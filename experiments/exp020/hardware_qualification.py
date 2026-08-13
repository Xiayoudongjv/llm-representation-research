"""Neutral, frozen-order hardware qualification for Qwen/Qwen3-4B.

This is not an EXP-020 scientific run: it uses only neutral diagnostic text,
saves scalar/config diagnostics, and never opens formal prompt or EXP-017 data.
"""

from __future__ import annotations

import gc
import json
import os
import platform
import shutil
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import torch
import transformers
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


MODEL_ID = "Qwen/Qwen3-4B"
EXP_DIR = Path(__file__).resolve().parent
RESULT = EXP_DIR / "results" / "hardware_qualification.json"
CACHE_DIR = Path(os.environ.get("HF_HOME", r"D:\AI_Cache\huggingface"))
PROMPT = "This is a neutral hardware diagnostic."
MAX_MODE_B_SECONDS = 120.0


def json_value(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.dtype):
        return str(value)
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")


def cleanup(model=None) -> None:
    if model is not None:
        del model
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()


def memory_gib() -> dict[str, float | None]:
    if not torch.cuda.is_available():
        return {"allocated_gib": None, "reserved_gib": None, "peak_allocated_gib": None}
    scale = 1024 ** 3
    return {
        "allocated_gib": round(torch.cuda.memory_allocated() / scale, 4),
        "reserved_gib": round(torch.cuda.memory_reserved() / scale, 4),
        "peak_allocated_gib": round(torch.cuda.max_memory_allocated() / scale, 4),
    }


def error_record(exc: Exception) -> dict[str, str | bool]:
    message = f"{type(exc).__name__}: {exc}"
    lowered = message.casefold()
    return {"error": message, "oom": any(token in lowered for token in ("out of memory", "cuda oom", "cuda error: out of memory"))}


def metadata(config, tokenizer) -> dict[str, object]:
    token_keys = ("model_max_length", "padding_side", "truncation_side", "chat_template", "bos_token", "eos_token", "pad_token")
    config_keys = ("model_type", "architectures", "num_hidden_layers", "hidden_size", "torch_dtype", "vocab_size", "max_position_embeddings")
    return {
        "model_id": MODEL_ID,
        "revision": getattr(config, "_commit_hash", None),
        "tokenizer_class": tokenizer.__class__.__name__,
        "tokenizer_config": {key: getattr(tokenizer, key, None) for key in token_keys},
        "model_config": {key: getattr(config, key, None) for key in config_keys},
        "num_transformer_blocks": getattr(config, "num_hidden_layers", None),
        "hidden_size": getattr(config, "hidden_size", None),
        "transformers_version": transformers.__version__,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
    }


def select_layers(num_blocks: int) -> dict[str, int]:
    if not isinstance(num_blocks, int) or num_blocks < 2:
        raise RuntimeError(f"Invalid transformer block count: {num_blocks}")
    return {"primary_depth_0_50": round(0.50 * (num_blocks - 1)), "secondary_depth_0_75": round(0.75 * (num_blocks - 1))}


def run_loaded_diagnostics(model, tokenizer, mode: str, dtype: torch.dtype, quantization: dict[str, object] | None) -> dict[str, object]:
    model.eval()
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None:
        raise RuntimeError("Expected model.model.layers is inaccessible for hook diagnostics.")
    num_blocks = len(layers)
    selected = select_layers(num_blocks)
    hooks_accessible = all(0 <= index < num_blocks and isinstance(layers[index], torch.nn.Module) for index in selected.values())
    if not hooks_accessible:
        raise RuntimeError("Frozen normalized-depth hook positions are inaccessible.")
    input_device = next(model.parameters()).device
    inputs = tokenizer(PROMPT, return_tensors="pt")
    inputs = {key: value.to(input_device) for key, value in inputs.items()}
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    forward_start = time.perf_counter()
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, return_dict=True)
    forward_seconds = time.perf_counter() - forward_start
    hidden_states = outputs.hidden_states
    hidden_ok = len(hidden_states) == num_blocks + 1 and hidden_states[-1].ndim == 3 and hidden_states[-1].shape[-1] == model.config.hidden_size
    del outputs, hidden_states
    forward_memory = memory_gib()
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    generation_start = time.perf_counter()
    with torch.no_grad():
        generated = model.generate(**inputs, max_new_tokens=2, do_sample=False, use_cache=True)
    generation_seconds = time.perf_counter() - generation_start
    generation_memory = memory_gib()
    del generated, inputs
    return {
        "mode": mode,
        "dtype": str(dtype),
        "quantization": quantization or {"enabled": False},
        "input_device": str(input_device),
        "device_map": getattr(model, "hf_device_map", {"": str(input_device)}),
        "idle_memory_after_load": forward_memory,
        "forward_seconds": round(forward_seconds, 4),
        "generation_seconds": round(generation_seconds, 4),
        "forward_peak_memory": forward_memory,
        "generation_peak_memory": generation_memory,
        "hidden_state_tensor_count": len(layers) + 1,
        "hidden_state_extraction_success": bool(hidden_ok),
        "selected_block_hooks_accessible": True,
        "selected_layers": selected,
        "short_generation_success": True,
        "practical_runtime": bool(mode != "MODE_B_CPU_OFFLOAD" or max(forward_seconds, generation_seconds) <= MAX_MODE_B_SECONDS),
    }


def attempt_mode(mode: str, config, tokenizer, dtype: torch.dtype) -> dict[str, object]:
    model = None
    started = time.perf_counter()
    try:
        torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
        kwargs: dict[str, object] = {"cache_dir": str(CACHE_DIR), "dtype": dtype, "low_cpu_mem_usage": True}
        quantization = None
        if mode == "MODE_A_NATIVE":
            kwargs["device_map"] = {"": 0}
        elif mode == "MODE_B_CPU_OFFLOAD":
            kwargs["device_map"] = "auto"
            kwargs["max_memory"] = {0: "6GiB", "cpu": "32GiB"}
        elif mode == "MODE_C_4BIT":
            try:
                from transformers import BitsAndBytesConfig
            except ImportError as exc:
                raise RuntimeError("bitsandbytes/4-bit configuration is unavailable.") from exc
            quantization = {
                "enabled": True,
                "method": "bitsandbytes_4bit",
                "quantization_type": "nf4",
                "compute_dtype": str(dtype),
                "double_quantization": True,
            }
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_compute_dtype=dtype,
                bnb_4bit_use_double_quant=True,
            )
            kwargs["device_map"] = "auto"
        else:
            raise ValueError(f"Unknown qualification mode: {mode}")
        model = AutoModelForCausalLM.from_pretrained(MODEL_ID, **kwargs)
        diagnostics = run_loaded_diagnostics(model, tokenizer, mode, dtype, quantization)
        diagnostics.update({"success": True, "load_seconds": round(time.perf_counter() - started, 4)})
        return diagnostics
    except Exception as exc:
        return {"mode": mode, "success": False, "load_or_diagnostic_seconds": round(time.perf_counter() - started, 4), **error_record(exc), "traceback_tail": traceback.format_exc().splitlines()[-1]}
    finally:
        cleanup(model)


def main() -> None:
    if RESULT.exists():
        prior = json.loads(RESULT.read_text(encoding="utf-8"))
        if not (prior.get("qualification_status") == "HARDWARE_INFEASIBLE" and "access_error" in prior and not prior.get("attempts")):
            raise RuntimeError("Qualification record already exists; refusing to replace the frozen qualification decision.")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA GPU unavailable; cannot qualify the required hardware path.")
    if CACHE_DIR.drive.upper() != "D:":
        raise RuntimeError(f"Cache directory must remain on D:, found {CACHE_DIR}")
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    base = {
        "requested_model_id": MODEL_ID,
        "qualification_status": "HARDWARE_INFEASIBLE",
        "hardware_feasibility": "UNTESTED",
        "model_access_status": "BLOCKED",
        "qualification_stage_reached": "BEFORE_MODEL_CONFIG_LOAD",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "diagnostic_prompt": PROMPT,
        "cache_dir": str(CACHE_DIR),
        "cache_configuration": {
            "HF_HOME": os.environ.get("HF_HOME"),
            "HF_HUB_CACHE": os.environ.get("HF_HUB_CACHE"),
            "TRANSFORMERS_CACHE": os.environ.get("TRANSFORMERS_CACHE"),
            "planned_download_cache_dir": str(CACHE_DIR),
            "free_disk_gib": round(shutil.disk_usage(CACHE_DIR.drive + "\\").free / 1024 ** 3, 2),
        },
        "gpu": {"name": torch.cuda.get_device_name(0), "total_memory_gib": round(torch.cuda.get_device_properties(0).total_memory / 1024 ** 3, 4), "bf16_supported": torch.cuda.is_bf16_supported()},
        "mode_order": ["MODE_A_NATIVE", "MODE_B_CPU_OFFLOAD", "MODE_C_4BIT"],
        "formal_exp020_results_created": False,
        "exp017_accessed": False,
        "attempts": [],
    }
    try:
        config = AutoConfig.from_pretrained(MODEL_ID, cache_dir=str(CACHE_DIR))
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, cache_dir=str(CACHE_DIR))
        base["model_metadata"] = metadata(config, tokenizer)
    except Exception as exc:
        base["access_error"] = error_record(exc)
        base["stop_reason"] = "Model configuration was unavailable from both the D: cache and Hugging Face access; no hardware inference mode was attempted."
        RESULT.write_text(json.dumps(base, ensure_ascii=False, indent=2, default=json_value) + "\n", encoding="utf-8")
        print("HARDWARE_INFEASIBLE")
        return
    native = attempt_mode("MODE_A_NATIVE", config, tokenizer, dtype)
    base["hardware_feasibility"] = "TESTED"
    base["model_access_status"] = "AVAILABLE"
    base["qualification_stage_reached"] = "MODEL_MODE_DIAGNOSTICS"
    base["attempts"].append(native)
    selected = native if native.get("success") else None
    if selected is None and native.get("oom"):
        offload = attempt_mode("MODE_B_CPU_OFFLOAD", config, tokenizer, dtype)
        base["attempts"].append(offload)
        selected = offload if offload.get("success") and offload.get("practical_runtime") else None
        if selected is None:
            four_bit = attempt_mode("MODE_C_4BIT", config, tokenizer, dtype)
            base["attempts"].append(four_bit)
            selected = four_bit if four_bit.get("success") else None
    if selected is not None:
        base["qualification_status"] = "QUALIFIED"
        base["frozen_execution_mode"] = selected["mode"]
        base["selected_mode"] = selected
        base["quantization_claim_boundary"] = (
            "higher-parameter quantized replication; parameter count and numerical precision differ from Qwen3-1.7B"
            if selected["quantization"].get("enabled") else "higher-parameter non-quantized replication"
        )
    else:
        base["stop_reason"] = "No frozen-order mode completed load, hidden-state extraction, and short generation without OOM at practical runtime."
    RESULT.write_text(json.dumps(base, ensure_ascii=False, indent=2, default=json_value) + "\n", encoding="utf-8")
    print(base["qualification_status"])
    print("attempted_modes:", ",".join(item["mode"] for item in base["attempts"]))
    print("frozen_execution_mode:", base.get("frozen_execution_mode"))


if __name__ == "__main__":
    main()
