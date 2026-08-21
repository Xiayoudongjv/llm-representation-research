"""Neutral TinyLlama engineering qualification for prospective EXP-027 fallback.

This script loads the exact local TinyLlama snapshot and verifies model/tokenizer/
carrier/hidden-state boundaries using neutral engineering text only. It must not
access any EXP-024/026/027 FIT/DIAG/EVAL record or run the scientific panel.
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

TINYLLAMA_MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
TINYLLAMA_REVISION = "fe8a4ea1ffedaf415f4da2f062534de366a451e6"
SNAPSHOT_PATH = Path(
    "D:/AI_Cache/huggingface/hub/models--TinyLlama--TinyLlama-1.1B-Chat-v1.0/snapshots/"
    "fe8a4ea1ffedaf415f4da2f062534de366a451e6"
)

NEUTRAL_TEXT = "The local snapshot is loaded offline for neutral engineering checks only."


def _set_offline_env() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def run_qualification(output_path: Path | None = None) -> dict[str, Any]:
    _set_offline_env()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    started_at = datetime.now(timezone.utc).isoformat()
    torch.cuda.reset_peak_memory_stats()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

    tokenizer = AutoTokenizer.from_pretrained(str(SNAPSHOT_PATH), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(SNAPSHOT_PATH),
        dtype=torch.bfloat16,
        local_files_only=True,
        use_cache=False,
    )
    model.eval()
    model.to(device)

    encoded = tokenizer(NEUTRAL_TEXT, return_tensors="pt", padding=False, truncation=False)
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    backbone = model.model
    layers = list(backbone.layers)
    carrier_forbidden = {id(backbone.embed_tokens), id(backbone.norm)}
    captures: list[Any] = [None] * len(layers)
    handles = []
    with torch.inference_mode():
        for index, module in enumerate(layers):
            def make_hook(index: int):
                def hook(_module, _args, output):
                    if isinstance(output, (tuple, list)):
                        value = output[0]
                    else:
                        value = output
                    captures[index] = value
                return hook
            handles.append(module.register_forward_hook(make_hook(index)))
        try:
            model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                use_cache=False,
            )
        finally:
            for handle in handles:
                handle.remove()

    selected_arrays = []
    for index, value in enumerate(captures):
        if value is None:
            raise RuntimeError(f"MISSING_CAPTURE_{index}")
        if torch.is_tensor(value):
            selected = value[0, attention_mask[0].sum() - 1]
            arr = selected.detach().cpu().to(torch.float32).numpy()
        else:
            raise TypeError(f"UNEXPECTED_CAPTURE_TYPE_{index}")
        selected_arrays.append(arr)

    hidden_size = model.config.hidden_size
    num_layers = model.config.num_hidden_layers
    layer_count_ok = len(layers) == num_layers == 22
    carrier_identity_ok = (
        len({id(module) for module in layers}) == len(layers)
        and not any(id(module) in carrier_forbidden for module in layers)
    )
    shape_ok = all(arr.shape == (hidden_size,) for arr in selected_arrays)
    finite_ok = all(np.isfinite(arr).all() for arr in selected_arrays)

    if device.type == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        vram_peak_reserved = int(torch.cuda.max_memory_reserved(0))
        vram_peak_allocated = int(torch.cuda.max_memory_allocated(0))
    else:
        gpu_name = "CPU_ONLY"
        vram_peak_reserved = None
        vram_peak_allocated = None

    result = {
        "schema_version": "1.0.0",
        "qualification_classification": "NEUTRAL_ENGINEERING_MODEL_QUALIFICATION_ONLY",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_id": TINYLLAMA_MODEL_ID,
        "model_revision": TINYLLAMA_REVISION,
        "snapshot_path": str(SNAPSHOT_PATH),
        "model_class": type(model).__name__,
        "model_type": model.config.model_type,
        "hidden_size": int(hidden_size),
        "num_hidden_layers": int(num_layers),
        "runtime_dtype": str(model.dtype),
        "device": str(device),
        "gpu_name": gpu_name,
        "tokenizer_class": type(tokenizer).__name__,
        "bos_token": tokenizer.bos_token,
        "eos_token": tokenizer.eos_token,
        "pad_token": tokenizer.pad_token,
        "unk_token": tokenizer.unk_token,
        "chat_template_available": bool(getattr(tokenizer, "chat_template", None)),
        "add_special_tokens_observed": bool(tokenizer.add_special_tokens),
        "input_ids_shape": list(input_ids.shape),
        "last_valid_token_index": int(attention_mask[0].sum() - 1),
        "layer_count_ok": bool(layer_count_ok),
        "carrier_identity_ok": bool(carrier_identity_ok),
        "carrier_excludes_embedding_and_norm": bool(carrier_identity_ok),
        "last_token_extraction_ok": bool(shape_ok and finite_ok),
        "captured_layer_shapes": [list(arr.shape) for arr in selected_arrays],
        "all_selected_finite": bool(finite_ok),
        "vram_peak_reserved_bytes": vram_peak_reserved,
        "vram_peak_allocated_bytes": vram_peak_allocated,
        "real_panel_accessed": False,
        "formal_run_authorized": False,
    }
    result = _json_safe(result)

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run_qualification(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())