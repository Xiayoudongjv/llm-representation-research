"""EXP-027 native-to-converted Llama checkpoint provenance audit.

This is read-only engineering evidence. It verifies that the local
Transformers safetensors checkpoint is the official Meta Llama converter's
deterministic transformation of the verified Meta-native consolidated
checkpoint. It does not access any EXP-024/026/027 FIT/DIAG/EVAL scientific
record and does not compute scientific outcomes.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import safetensors
import torch

NATIVE_DIR = Path("D:/AI_Cache/llama_home/.llama/checkpoints/Llama3.2-1B-Instruct")
CONVERTED_DIR = Path("D:/AI_Cache/llama_hf/Llama3.2-1B-Instruct-meta-converted-v4463-attempt3")

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


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().tolist()
    if isinstance(value, torch.dtype):
        return str(value)
    return value


def _permute(weight: torch.Tensor, n_heads: int, dim1: int, dim2: int) -> torch.Tensor:
    """Official Meta-to-HF Llama Q/K permutation used by the converter."""
    return weight.view(n_heads, dim1 // n_heads // 2, 2, dim2).transpose(1, 2).reshape(dim1, dim2)


def _compare(a: torch.Tensor, b: torch.Tensor) -> tuple[bool, float]:
    equal = bool(torch.equal(a, b))
    max_abs_diff = float((a.float() - b.float()).abs().max().item())
    return equal, max_abs_diff


def run_audit(output_path: Path | None = None) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc).isoformat()
    native = torch.load(
        NATIVE_DIR / "consolidated.00.pth",
        map_location="cpu",
        weights_only=True,
    )

    mismatch_reasons: list[str] = []
    exact_groups: dict[str, int] = {}
    max_diffs: dict[str, float] = {}
    q_diffs: list[float] = []
    k_diffs: list[float] = []

    def record_group(name: str, equal: bool, max_abs_diff: float, mismatch_detail: str) -> None:
        exact_groups[name] = exact_groups.get(name, 0) + (1 if equal else 0)
        max_diffs[name] = max(max_diffs.get(name, 0.0), max_abs_diff)
        if not equal:
            mismatch_reasons.append(mismatch_detail)

    embedding_equal, embedding_diff = _compare(
        native["tok_embeddings.weight"],
        safetensors.safe_open(
            str(CONVERTED_DIR / "model.safetensors"), framework="pt", device="cpu"
        ).get_tensor("model.embed_tokens.weight"),
    )
    record_group("embedding", embedding_equal, embedding_diff, "embedding mismatch")

    tied_equal, tied_diff = _compare(native["tok_embeddings.weight"], native["output.weight"])
    record_group("tied_output_embedding", tied_equal, tied_diff, "native output is not tied to embeddings")

    with safetensors.safe_open(str(CONVERTED_DIR / "model.safetensors"), framework="pt", device="cpu") as state:
        for layer_index in range(16):
            prefix = f"layers.{layer_index}"
            hf_prefix = f"model.layers.{layer_index}"

            q_native = native[f"{prefix}.attention.wq.weight"]
            q_converted = state.get_tensor(f"{hf_prefix}.self_attn.q_proj.weight")
            q_reconstructed = _permute(q_native, 32, 2048, 2048)
            q_equal, q_diff = _compare(q_reconstructed, q_converted)
            q_diffs.append(q_diff)
            record_group("q_proj_permute", q_equal, q_diff, f"{prefix} q_proj mismatch")

            k_native = native[f"{prefix}.attention.wk.weight"]
            k_converted = state.get_tensor(f"{hf_prefix}.self_attn.k_proj.weight")
            k_reconstructed = _permute(k_native, 8, 512, 2048)
            k_equal, k_diff = _compare(k_reconstructed, k_converted)
            k_diffs.append(k_diff)
            record_group("k_proj_permute", k_equal, k_diff, f"{prefix} k_proj mismatch")

            direct_groups = {
                "v_proj": (f"{prefix}.attention.wv.weight", f"{hf_prefix}.self_attn.v_proj.weight"),
                "o_proj": (f"{prefix}.attention.wo.weight", f"{hf_prefix}.self_attn.o_proj.weight"),
                "gate_proj": (f"{prefix}.feed_forward.w1.weight", f"{hf_prefix}.mlp.gate_proj.weight"),
                "up_proj": (f"{prefix}.feed_forward.w3.weight", f"{hf_prefix}.mlp.up_proj.weight"),
                "down_proj": (f"{prefix}.feed_forward.w2.weight", f"{hf_prefix}.mlp.down_proj.weight"),
                "input_layernorm": (f"{prefix}.attention_norm.weight", f"{hf_prefix}.input_layernorm.weight"),
                "post_attention_layernorm": (f"{prefix}.ffn_norm.weight", f"{hf_prefix}.post_attention_layernorm.weight"),
            }
            for group, (native_name, hf_name) in direct_groups.items():
                equal, diff = _compare(native[native_name], state.get_tensor(hf_name))
                record_group(group, equal, diff, f"{prefix} {group} mismatch")

        norm_equal, norm_diff = _compare(native["norm.weight"], state.get_tensor("model.norm.weight"))
        record_group("final_norm", norm_equal, norm_diff, "final norm mismatch")

    result = {
        "schema_version": "1.0.0",
        "qualification_classification": "NATIVE_CONVERTED_PROVENANCE_QUALIFICATION_ONLY",
        "started_at_utc": started_at,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "native_checkpoint_path": str(NATIVE_DIR),
        "converted_checkpoint_path": str(CONVERTED_DIR),
        "native_sha256": NATIVE_SHA256,
        "converted_sha256": CONVERTED_SHA256,
        "native_tensor_count": int(len(native)),
        "converted_tensor_count": int(sum(1 for _ in safetensors.safe_open(str(CONVERTED_DIR / "model.safetensors"), framework="pt", device="cpu").keys())),
        "q_proj_permutation": {
            "compared_tensors": 16,
            "exact_tensors": exact_groups.get("q_proj_permute", 0),
            "max_abs_diff": float(max(q_diffs, default=0.0)),
        },
        "k_proj_permutation": {
            "compared_tensors": 16,
            "exact_tensors": exact_groups.get("k_proj_permute", 0),
            "max_abs_diff": float(max(k_diffs, default=0.0)),
        },
        "direct_mapping_exact_tensors": exact_groups,
        "max_abs_diffs": max_diffs,
        "tied_output_embedding_exact": bool(tied_equal),
        "all_mapped_tensors_match": bool(not mismatch_reasons),
        "mismatch_reasons": mismatch_reasons,
        "provenance_status": "PASS" if not mismatch_reasons else "FAIL",
        "scientific_data_accessed": False,
        "scientific_outcome_computed": False,
    }

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    result = run_audit(args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
