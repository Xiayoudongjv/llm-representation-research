"""Run neutral, local-only Qwen3-4B hardware qualification in frozen mode order."""

from __future__ import annotations

import gc
import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

import torch
import transformers
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


MODEL_ID = "Qwen/Qwen3-4B"
CANONICAL_MODEL_PATH = Path(r"D:\Qwen3-4B-transfer")
RESULT = Path(__file__).resolve().parent / "results" / "qwen3_4b_hardware_qualification.json"
PROMPT = "This is a neutral hardware diagnostic."
MODE_ORDER = ["MODE_A_NATIVE", "MODE_B_CPU_OFFLOAD", "MODE_C_4BIT"]
MAX_MODE_B_SECONDS = 120.0


def json_value(value: object) -> str:
    if isinstance(value, (Path, torch.dtype, torch.device)):
        return str(value)
    raise TypeError(f"Not JSON serializable: {type(value).__name__}")


def cleanup(model: object | None = None) -> None:
    del model
    gc.collect()
    if torch.cuda.is_available():
        # A CUDA OOM can leave the allocator unable to perform an additional
        # IPC cleanup. Cleanup must never mask the recorded loading failure.
        try:
            torch.cuda.empty_cache()
        except RuntimeError:
            pass
        try:
            torch.cuda.ipc_collect()
        except RuntimeError:
            pass


def memory_gib() -> dict[str, float | None]:
    if not torch.cuda.is_available():
        return {"allocated_gib": None, "reserved_gib": None, "peak_allocated_gib": None}
    scale = 1024**3
    return {
        "allocated_gib": round(torch.cuda.memory_allocated() / scale, 4),
        "reserved_gib": round(torch.cuda.memory_reserved() / scale, 4),
        "peak_allocated_gib": round(torch.cuda.max_memory_allocated() / scale, 4),
    }


def is_oom(exc: Exception) -> bool:
    message = f"{type(exc).__name__}: {exc}".casefold()
    return any(token in message for token in ("out of memory", "cuda oom", "cuda error: out of memory"))


def selected_layers(num_blocks: int) -> dict[str, int]:
    return {"primary_depth_0_50": round(0.50 * (num_blocks - 1)), "secondary_depth_0_75": round(0.75 * (num_blocks - 1))}


def input_device(model) -> torch.device:
    device = model.get_input_embeddings().weight.device
    return torch.device("cuda:0") if device.type == "meta" and torch.cuda.is_available() else device


def zero_hook_equivalence(model, inputs: dict[str, torch.Tensor], layer: torch.nn.Module) -> dict[str, object]:
    with torch.inference_mode():
        baseline = model(**inputs, return_dict=True).logits.detach()

    def zero_intervention(_module, _args, output):
        if isinstance(output, tuple):
            return (output[0] + torch.zeros_like(output[0]), *output[1:])
        return output + torch.zeros_like(output)

    handle = layer.register_forward_hook(zero_intervention)
    try:
        with torch.inference_mode():
            hooked = model(**inputs, return_dict=True).logits.detach()
    finally:
        handle.remove()
    difference = (baseline - hooked).abs()
    return {
        "status": "ZERO_HOOK_EQUIVALENCE_PASS" if torch.allclose(baseline, hooked, rtol=1e-3, atol=1e-3) else "ZERO_HOOK_EQUIVALENCE_FAIL",
        "rtol": 1e-3,
        "atol": 1e-3,
        "max_abs_logit_difference": float(difference.max().item()),
    }


def run_diagnostics(model, tokenizer, mode: str, dtype: torch.dtype, quantization: dict[str, object] | None, after_load_memory: dict[str, float | None]) -> dict[str, object]:
    model.eval()
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None:
        raise RuntimeError("Expected model.model.layers for hook diagnostics.")
    layer_count = len(layers)
    frozen_layers = selected_layers(layer_count)
    if not all(0 <= index < layer_count and isinstance(layers[index], torch.nn.Module) for index in frozen_layers.values()):
        raise RuntimeError("Frozen normalized-depth hook positions are inaccessible.")
    device = input_device(model)
    inputs = {name: value.to(device) for name, value in tokenizer(PROMPT, return_tensors="pt").items()}
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    started = time.perf_counter()
    with torch.inference_mode():
        outputs = model(**inputs, output_hidden_states=True, return_dict=True)
    forward_seconds = time.perf_counter() - started
    hidden = outputs.hidden_states
    hidden_ok = len(hidden) == layer_count + 1 and hidden[-1].ndim == 3 and hidden[-1].shape[-1] == model.config.hidden_size
    hidden_shape = list(hidden[-1].shape) if hidden_ok else None
    del outputs, hidden
    forward_memory = memory_gib()
    torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
    started = time.perf_counter()
    with torch.inference_mode():
        generated = model.generate(**inputs, max_new_tokens=2, do_sample=False, use_cache=True)
    generation_seconds = time.perf_counter() - started
    generated_tokens = int(generated.shape[-1] - inputs["input_ids"].shape[-1])
    del generated
    generation_memory = memory_gib()
    zero_hook = zero_hook_equivalence(model, inputs, layers[frozen_layers["primary_depth_0_50"]])
    del inputs
    return {
        "mode": mode,
        "dtype": str(dtype),
        "quantization": quantization or {"enabled": False},
        "device_map": getattr(model, "hf_device_map", {"": str(device)}),
        "gpu_memory_after_load": after_load_memory,
        "forward_seconds": round(forward_seconds, 4),
        "generation_seconds": round(generation_seconds, 4),
        "forward_peak_gpu_memory": forward_memory,
        "generation_peak_gpu_memory": generation_memory,
        "hidden_state_extraction_success": bool(hidden_ok),
        "hidden_state_tensor_count": layer_count + 1,
        "hidden_state_shape": hidden_shape,
        "selected_block_hooks_accessible": True,
        "selected_layers": frozen_layers,
        "short_generation_success": generated_tokens == 2,
        "generated_token_count": generated_tokens,
        "zero_hook_equivalence": zero_hook,
        "practical_runtime": mode != "MODE_B_CPU_OFFLOAD" or max(forward_seconds, generation_seconds) <= MAX_MODE_B_SECONDS,
    }


def attempt_mode(mode: str, config, tokenizer, dtype: torch.dtype) -> dict[str, object]:
    model = None
    started = time.perf_counter()
    try:
        torch.cuda.reset_peak_memory_stats() if torch.cuda.is_available() else None
        kwargs: dict[str, object] = {"local_files_only": True, "dtype": dtype, "low_cpu_mem_usage": True}
        quantization = None
        if mode == "MODE_A_NATIVE":
            kwargs["device_map"] = {"": 0}
        elif mode == "MODE_B_CPU_OFFLOAD":
            kwargs["device_map"] = "auto"
            kwargs["max_memory"] = {0: "6GiB", "cpu": "32GiB"}
        elif mode == "MODE_C_4BIT":
            from transformers import BitsAndBytesConfig

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
            raise ValueError(f"Unknown mode: {mode}")
        model = AutoModelForCausalLM.from_pretrained(CANONICAL_MODEL_PATH, **kwargs)
        after_load_memory = memory_gib()
        diagnostics = run_diagnostics(model, tokenizer, mode, dtype, quantization, after_load_memory)
        diagnostics["success"] = bool(diagnostics["hidden_state_extraction_success"] and diagnostics["short_generation_success"])
        diagnostics["load_seconds"] = round(time.perf_counter() - started - diagnostics["forward_seconds"] - diagnostics["generation_seconds"], 4)
        return diagnostics
    except Exception as exc:
        return {
            "mode": mode,
            "success": False,
            "oom": is_oom(exc),
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc().splitlines()[-1],
            "load_or_diagnostic_seconds": round(time.perf_counter() - started, 4),
        }
    finally:
        cleanup(model)


def main() -> None:
    if RESULT.exists():
        raise RuntimeError(f"Qualification result already exists; refusing to overwrite it: {RESULT}")
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; cannot perform the required qualification.")
    config = AutoConfig.from_pretrained(CANONICAL_MODEL_PATH, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(CANONICAL_MODEL_PATH, local_files_only=True)
    if config.model_type != "qwen3" or config.hidden_size != 2560 or config.num_hidden_layers != 36:
        raise RuntimeError("LOCAL_MODEL_IDENTITY_FAILED: local configuration does not match the preregistered Qwen3-4B identity.")
    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    result: dict[str, object] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "requested_model_id": MODEL_ID,
        "canonical_model_path": str(CANONICAL_MODEL_PATH),
        "local_files_only": True,
        "hardware_feasibility": "TESTED",
        "model_access_status": "LOCAL_SNAPSHOT_AVAILABLE",
        "qualification_stage_reached": "COMPLETE_NEUTRAL_DIAGNOSTICS",
        "diagnostic_prompt": PROMPT,
        "mode_order": MODE_ORDER,
        "model_metadata": {
            "config_class": config.__class__.__name__,
            "architectures": list(config.architectures or []),
            "model_type": config.model_type,
            "hidden_size": config.hidden_size,
            "num_transformer_blocks": config.num_hidden_layers,
            "vocab_size": config.vocab_size,
            "config_torch_dtype": str(config.torch_dtype),
            "tokenizer_class": tokenizer.__class__.__name__,
            "transformers_version": transformers.__version__,
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
        },
        "gpu": {"name": torch.cuda.get_device_name(0), "total_memory_gib": round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 4), "bf16_supported": torch.cuda.is_bf16_supported()},
        "exp020_scientific_results_created": False,
        "exp017_accessed": False,
        "exp019_accessed": False,
        "attempts": [],
    }
    native = attempt_mode("MODE_A_NATIVE", config, tokenizer, dtype)
    result["attempts"].append(native)
    selected = native if native.get("success") else None
    if selected is None and native.get("oom"):
        offload = attempt_mode("MODE_B_CPU_OFFLOAD", config, tokenizer, dtype)
        result["attempts"].append(offload)
        selected = offload if offload.get("success") and offload.get("practical_runtime") else None
        if selected is None:
            four_bit = attempt_mode("MODE_C_4BIT", config, tokenizer, dtype)
            result["attempts"].append(four_bit)
            selected = four_bit if four_bit.get("success") else None
    if selected is not None:
        result["selected_execution_mode"] = selected["mode"]
        result["zero_hook_status"] = selected["zero_hook_equivalence"]["status"]
        if result["zero_hook_status"] != "ZERO_HOOK_EQUIVALENCE_PASS":
            result["qualification_status"] = "ZERO_HOOK_VALIDATION_FAILED"
        elif selected["mode"] == "MODE_C_4BIT":
            result["qualification_status"] = "QUANTIZED_MODE_REQUIRED"
        else:
            result["qualification_status"] = "READY_FOR_EXP020_PREREGISTRATION_REVIEW"
    else:
        result["selected_execution_mode"] = None
        result["zero_hook_status"] = "NOT_RUN"
        result["qualification_status"] = "HARDWARE_INFEASIBLE" if len(result["attempts"]) == 3 else "NATIVE_GPU_OOM"
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=json_value) + "\n", encoding="utf-8")
    print(result["qualification_status"])
    print("selected_execution_mode:", result["selected_execution_mode"])


if __name__ == "__main__":
    main()
