"""EXP-027 Llama-3.2 model-authority and neutral runtime qualification.

Read-only provenance and neutral runtime checks for the Meta-converted local
checkpoint. This script does not access any EXP-024/026/027 FIT/DIAG/EVAL
scientific record and does not compute scientific outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

NATIVE_DIR = Path("D:/AI_Cache/llama_home/.llama/checkpoints/Llama3.2-1B-Instruct")
CONVERTED_DIR = Path("D:/AI_Cache/llama_hf/Llama3.2-1B-Instruct-meta-converted-v4463-attempt3")
NEUTRAL_TEXT = "A neutral engineering sentence verifies local checkpoint identity and carrier semantics."

NATIVE_SHA256 = {
    "checklist.chk": "efefc79fc47ecce1c3e06a6ae77a4cddc7e6078f822efba22e4fc7f9da02400e",
    "consolidated.00.pth": "fc17d497df5e4175b3a8acb4f5865b26f7fc1b009b25bef814b95fde10e8a1f3",
    "params.json": "1d616a44f3cdac29b9288cf14718b76eb1bed56ed38be1f7e39b06ed139e3733",
    "tokenizer.model": "82e9d31979e92ab929cd544440f129d9ecd797b69e327f80f17e1c50d5551b55",
}

CONVERTED_SHA256 = {
    "config.json": "bd89aaf5151393a7ae25c5a1fbfb96c98a825d611c3a6e950db636ca2ee4b8d9",
    "generation_config.json": "82b9ac122eb7faddde243b84d8971c17323fd215a9ec5480c059f723bcd4577b",
    "model.safetensors": "1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f",
    "special_tokens_map.json": "ae9d6a4c878d14cc04cfdfa7483c92c46d04ce7675792522eda0bf5915d3435d",
    "tokenizer.json": "6b9e4e7fb171f92fd137b777cc2714bf87d11576700a1dcd7a399e7bbe39537b",
    "tokenizer_config.json": "c8ff00dfc90bf2c34c774beddbac0ca7c54f9256c260ff8ccd7985b535bdc89a",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _extract_hidden(output: Any) -> Any:
    import torch
    if torch.is_tensor(output):
        return output
    if isinstance(output, (tuple, list)) and output:
        return _extract_hidden(output[0])
    raise TypeError("UNSUPPORTED_BLOCK_OUTPUT")


def run_qualification(output_path: Path | None = None) -> dict[str, Any]:
    _set_offline_env()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    started_at = datetime.now(timezone.utc).isoformat()
    native_hashes = {name: _sha256(NATIVE_DIR / name) for name in NATIVE_SHA256}
    converted_hashes = {name: _sha256(CONVERTED_DIR / name) for name in CONVERTED_SHA256}
    native_hash_match = {name: native_hashes[name] == expected for name, expected in NATIVE_SHA256.items()}
    converted_hash_match = {name: converted_hashes[name] == expected for name, expected in CONVERTED_SHA256.items()}

    torch.cuda.reset_peak_memory_stats()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(str(CONVERTED_DIR), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(CONVERTED_DIR),
        dtype=torch.bfloat16,
        local_files_only=True,
        use_cache=False,
    )
    model.eval()
    model.to(device)

    encoded = tokenizer(NEUTRAL_TEXT, return_tensors="pt", padding=False, truncation=False)
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    layers = list(model.model.layers)
    captures: list[Any] = [None] * len(layers)
    handles = []
    with torch.inference_mode():
        for index, module in enumerate(layers):
            def hook_fn(_module, _args, output, index=index):
                captures[index] = _extract_hidden(output)
            handles.append(module.register_forward_hook(hook_fn))
        try:
            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                use_cache=False,
            )
        finally:
            for handle in handles:
                handle.remove()

    block_hidden = outputs.hidden_states
    last_index = attention_mask[0].sum() - 1
    selected = []
    for index, value in enumerate(captures):
        if value is None:
            raise RuntimeError(f"MISSING_HOOK_CAPTURE_{index}")
        selected.append(value[0, last_index, :].detach().cpu().to(torch.float32).numpy())

    diffs = []
    for index in range(len(layers) - 1):
        hook = captures[index][0, last_index, :].detach().cpu().to(torch.float32)
        hidden = block_hidden[index + 1][0, last_index, :].detach().cpu().to(torch.float32)
        diffs.append(float((hook - hidden).abs().max().item()))

    raw_final_full = captures[-1][0]
    final_normed_full = model.model.norm(raw_final_full)
    raw_final = raw_final_full[last_index, :]
    final_normed = final_normed_full[last_index, :]
    final_hidden = block_hidden[-1][0, last_index, :].detach().cpu().to(torch.float32)
    raw_vs_final_hidden_max = float((raw_final.detach().cpu().to(torch.float32) - final_hidden).abs().max().item())
    normed_vs_final_hidden_max = float((final_normed.detach().cpu().to(torch.float32) - final_hidden).abs().max().item())

    if device.type == "cuda":
        gpu_name = torch.cuda.get_device_name(0)
        peak_reserved = int(torch.cuda.max_memory_reserved(0))
    else:
        gpu_name = "CPU_ONLY"
        peak_reserved = 0

    result = {
        "schema_version": "1.0.0",
        "qualification_classification": "MODEL_AUTHORITY_AND_NEUTRAL_RUNTIME_QUALIFICATION_ONLY",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_source": "META_OFFICIAL_NATIVE_DISTRIBUTION",
        "selected_model": "Meta-Llama-3.2-1B-Instruct",
        "native_checkpoint_path": str(NATIVE_DIR),
        "converted_checkpoint_path": str(CONVERTED_DIR),
        "native_sha256": native_hashes,
        "native_sha256_match": native_hash_match,
        "converted_sha256": converted_hashes,
        "converted_sha256_match": converted_hash_match,
        "model_class": type(model).__name__,
        "model_type": model.config.model_type,
        "hidden_size": int(model.config.hidden_size),
        "num_hidden_layers": int(model.config.num_hidden_layers),
        "num_attention_heads": int(model.config.num_attention_heads),
        "num_key_value_heads": int(model.config.num_key_value_heads),
        "vocab_size": int(model.config.vocab_size),
        "intermediate_size": int(model.config.intermediate_size),
        "max_position_embeddings": int(model.config.max_position_embeddings),
        "rope_theta": float(model.config.to_dict().get("rope_theta", 500000.0)),
        "tie_word_embeddings": bool(model.config.tie_word_embeddings),
        "runtime_dtype": str(model.dtype),
        "device": str(device),
        "gpu_name": gpu_name,
        "tokenizer_class": type(tokenizer).__name__,
        "tokenizer_vocab": int(len(tokenizer)),
        "bos_token": tokenizer.bos_token,
        "bos_token_id": int(tokenizer.bos_token_id),
        "eos_token": tokenizer.eos_token,
        "eos_token_id": int(tokenizer.eos_token_id),
        "eot_token_id": int(tokenizer.convert_tokens_to_ids("<|eot_id|>")),
        "chat_template_available": bool(getattr(tokenizer, "chat_template", None)),
        "neutral_input_ids_shape": list(input_ids.shape),
        "logits_shape": list(outputs.logits.shape),
        "selected_carrier_shapes": [list(arr.shape) for arr in selected],
        "all_selected_finite": bool(all(np.isfinite(arr).all() for arr in selected)),
        "non_final_block_hook_hidden_max_abs_diff": diffs,
        "raw_final_vs_final_hidden_max_abs_diff": raw_vs_final_hidden_max,
        "normed_final_vs_final_hidden_max_abs_diff": normed_vs_final_hidden_max,
        "final_hidden_state_semantics": "POST_FINAL_NORM_CONFIRMED" if normed_vs_final_hidden_max == 0.0 else "UNEXPECTED",
        "carrier_api": "FORWARD_HOOK_DECODER_BLOCK_OUTPUT",
        "carrier_mapping_verified": len(layers) == 16 and all(np.isfinite(arr).all() for arr in selected),
        "peak_vram_reserved_bytes": peak_reserved,
        "real_panel_accessed": False,
        "formal_run_authorized": False,
        "scientific_matrix_computed": False,
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