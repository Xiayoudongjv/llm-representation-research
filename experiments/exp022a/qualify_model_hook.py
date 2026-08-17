"""Engineering-only EXP-022A model/tokenizer/hook qualification runner.

This script is intentionally separate from the scientific runner. It loads the
exact local Qwen3-1.7B snapshot and exercises the production runtime helpers on
neutral engineering-only inputs. It does not access formal data, run EXP-022A,
or create a scientific result.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import numpy as np
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from experiments.exp022a import run_exp022a as runner  # noqa: E402


EXPERIMENT = "EXP-022A"
MODEL_NAME = "Qwen/Qwen3-1.7B"
EXPECTED_SNAPSHOT = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
SNAPSHOT_PATH = (
    Path("D:/AI_Cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots")
    / EXPECTED_SNAPSHOT
)
ARTIFACT_PATH = (
    REPO_ROOT
    / "experiments"
    / "exp022a"
    / "engineering"
    / "model_hook_qualification.json"
)

NEUTRAL_TEXTS = (
    "Morning sunlight crossed the empty room.",
    "A paper boat rested beside the window.",
)

TOKENIZER_KWARGS = {
    "return_tensors": "pt",
    "padding": False,
    "truncation": False,
    "add_special_tokens": True,
}

BLOCK_ORACLE_RTOL = 1e-3
BLOCK_ORACLE_ATOL = 1e-5
FINAL_NORM_RTOL = 1e-3
FINAL_NORM_ATOL = 1e-5
DISTINCTION_MIN_ABS = 1e-4
ZERO_PERTURBATION_RTOL = 1e-3
ZERO_PERTURBATION_ATOL = 1e-5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_commit() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()


def _tensor_close(left: torch.Tensor, right: torch.Tensor, rtol: float, atol: float) -> bool:
    return bool(torch.allclose(left, right, rtol=rtol, atol=atol))


def _max_abs_diff(left: torch.Tensor, right: torch.Tensor) -> float:
    return float((left - right).abs().max().item())


def _prepare_inputs(tokenizer: Any, text: str, device: torch.device) -> dict[str, torch.Tensor]:
    encoded = tokenizer(text, **TOKENIZER_KWARGS)
    return {
        "input_ids": encoded["input_ids"].to(device),
        "attention_mask": encoded["attention_mask"].to(device),
    }


def _forward(model: Any, inputs: dict[str, torch.Tensor]) -> Any:
    return model(
        input_ids=inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        use_cache=False,
        output_hidden_states=True,
    )


def _hooked_forward(
    model: Any,
    inputs: dict[str, torch.Tensor],
) -> dict[str, Any]:
    """Run one forward with block16/block26/block27 production observation hooks."""
    block16 = model.model.layers[16]
    block26 = model.model.layers[26]
    block27 = model.model.layers[27]
    capture16 = runner.ForwardHookCapture()
    capture26 = runner.ForwardHookCapture()
    capture27 = runner.ForwardHookCapture()

    baseline_counts = {
        16: len(block16._forward_hooks),
        26: len(block26._forward_hooks),
        27: len(block27._forward_hooks),
    }

    with torch.inference_mode():
        with runner.block_output_hook_capture(block16, capture16):
            with runner.block_output_hook_capture(block26, capture26):
                handle27 = block27.register_forward_hook(
                    runner.block27_pre_final_rmsnorm_hook(capture27)
                )
                try:
                    outputs = _forward(model, inputs)
                finally:
                    handle27.remove()

    after_counts = {
        16: len(block16._forward_hooks),
        26: len(block26._forward_hooks),
        27: len(block27._forward_hooks),
    }
    cleanup_ok = (
        after_counts[16] == baseline_counts[16]
        and after_counts[26] == baseline_counts[26]
        and after_counts[27] == baseline_counts[27]
    )
    return {
        "outputs": outputs,
        "capture16": capture16,
        "capture26": capture26,
        "capture27": capture27,
        "hook_cleanup_ok": cleanup_ok,
    }


def _tokenizer_metadata(tokenizer: Any) -> dict[str, Any]:
    return {
        "class": type(tokenizer).__name__,
        "vocab_size": int(len(tokenizer)),
        "padding_side": str(tokenizer.padding_side),
        "bos_token": tokenizer.bos_token,
        "eos_token": tokenizer.eos_token,
        "pad_token": tokenizer.pad_token,
        "additional_special_tokens_count": int(
            len(getattr(tokenizer, "additional_special_tokens", []) or [])
        ),
        "add_special_tokens_contract": TOKENIZER_KWARGS["add_special_tokens"],
        "padding_contract": TOKENIZER_KWARGS["padding"],
        "truncation_contract": TOKENIZER_KWARGS["truncation"],
        "return_tensors_contract": TOKENIZER_KWARGS["return_tensors"],
    }


def _checkpoint_shape_statuses(
    checkpoints: dict[str, torch.Tensor],
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for name, tensor in checkpoints.items():
        if tensor.ndim != 3 or tensor.shape[-1] != 2048:
            statuses[name] = "FAIL"
        else:
            statuses[name] = "PASS"
    return statuses


def _last_valid_token_status(
    checkpoints: dict[str, torch.Tensor],
    attention_mask: torch.Tensor,
) -> tuple[str, dict[str, Any]]:
    try:
        indices = runner.last_valid_token_indices(attention_mask)
        expected_indices = attention_mask.sum(dim=-1) - 1
        if not torch.equal(indices.reshape(-1), expected_indices.reshape(-1)):
            return "FAIL", {}
        selected = runner.extract_last_token_representations(checkpoints, attention_mask)
        for name, checkpoint in checkpoints.items():
            for batch_index, token_index in enumerate(expected_indices.tolist()):
                if not torch.equal(
                    selected[name][batch_index],
                    checkpoint[batch_index, int(token_index)],
                ):
                    return "FAIL", {}
        return "PASS", {"selected_checkpoint_count": len(selected)}
    except Exception:
        return "FAIL", {}


def _float32_boundary_status(
    selected: dict[str, torch.Tensor],
) -> tuple[str, dict[str, Any]]:
    try:
        for name, tensor in selected.items():
            for record_index in range(tensor.shape[0]):
                array = runner.to_float32_analysis_array(
                    tensor[record_index], expected_ndim=1
                )
                if array.dtype != np.float32 or array.shape != (2048,):
                    return "FAIL", {}
                if not np.isfinite(array).all():
                    return "FAIL", {}
        return "PASS", {"converted_checkpoint_count": len(selected)}
    except Exception:
        return "FAIL", {}


def _block_oracle_status(
    capture: runner.ForwardHookCapture,
    reference: torch.Tensor,
) -> dict[str, Any]:
    captured = capture.value
    exact = torch.equal(captured, reference)
    close = _tensor_close(
        captured, reference, BLOCK_ORACLE_RTOL, BLOCK_ORACLE_ATOL
    )
    max_diff = _max_abs_diff(captured.float(), reference.float())
    return {
        "status": "PASS" if close else "FAIL",
        "exact": bool(exact),
        "tolerance_pass": close,
        "max_abs_diff": max_diff,
    }


def _final_rmsnorm_status(
    model: Any,
    h_pre: torch.Tensor,
    h_post: torch.Tensor,
) -> dict[str, Any]:
    with torch.inference_mode():
        recomputed_post = model.model.norm(h_pre)
    relationship = _tensor_close(
        recomputed_post, h_post, FINAL_NORM_RTOL, FINAL_NORM_ATOL
    )
    pre_post_diff = _max_abs_diff(h_pre.float(), h_post.float())
    distinction = pre_post_diff > DISTINCTION_MIN_ABS and not torch.equal(
        h_pre, h_post
    )
    return {
        "status": "PASS" if relationship else "FAIL",
        "relationship_tolerance_pass": relationship,
        "pre_post_distinction_pass": bool(distinction),
        "pre_post_max_abs_diff": pre_post_diff,
    }


def _hook_zero_perturbation_status(
    baseline_logits: torch.Tensor,
    hooked_logits: torch.Tensor,
) -> dict[str, Any]:
    exact = torch.equal(baseline_logits, hooked_logits)
    close = _tensor_close(
        baseline_logits.float(),
        hooked_logits.float(),
        ZERO_PERTURBATION_RTOL,
        ZERO_PERTURBATION_ATOL,
    )
    max_diff = _max_abs_diff(baseline_logits.float(), hooked_logits.float())
    return {
        "status": "PASS" if (exact or close) else "FAIL",
        "exact": bool(exact),
        "tolerance_pass": close,
        "max_abs_diff": max_diff,
    }


def main() -> int:
    captured_warnings: list[str] = []
    with warnings.catch_warnings(record=True) as warning_records:
        warnings.simplefilter("always")
        result = _run_qualification()
        captured_warnings = [
            f"{record.category.__name__}: {record.message}" for record in warning_records
        ]

    result["warnings"] = list(dict.fromkeys(captured_warnings))
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["overall_qualification_status"] == "MODEL_HOOK_ENGINEERING_QUALIFIED" else 1


def _run_qualification() -> dict[str, Any]:
    repository_commit = _repo_commit()
    frozen_sha = _sha256_file(REPO_ROOT / "docs/experiments/EXP-022A-PREREGISTRATION.md")
    if frozen_sha != runner.FROZEN_PREREGISTRATION_SHA256:
        raise RuntimeError("FROZEN_PREREGISTRATION_SHA_MISMATCH")

    def _forbidden_formal_data(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("FORMAL_DATASET_LOADER_FORBIDDEN")

    runner.load_production_dataset = _forbidden_formal_data
    runner.validate_production_records = _forbidden_formal_data

    snapshot_identity_pass = SNAPSHOT_PATH.is_dir() and str(SNAPSHOT_PATH.name) == EXPECTED_SNAPSHOT
    if not snapshot_identity_pass:
        raise RuntimeError("MODEL_SNAPSHOT_UNAVAILABLE")

    tokenizer = AutoTokenizer.from_pretrained(
        str(SNAPSHOT_PATH),
        local_files_only=True,
    )
    tokenizer_metadata = _tokenizer_metadata(tokenizer)
    tokenizer_identity_pass = (
        tokenizer_metadata["class"] == "Qwen2Tokenizer"
        and tokenizer_metadata["vocab_size"] > 0
        and tokenizer_metadata["padding_side"] in {"left", "right"}
        and tokenizer_metadata["eos_token"] is not None
        and tokenizer_metadata["pad_token"] is not None
    )

    device = torch.device("cuda:0")
    model = AutoModelForCausalLM.from_pretrained(
        str(SNAPSHOT_PATH),
        dtype=torch.float16,
        local_files_only=True,
    )
    model.to(device)
    model.eval()
    torch.set_grad_enabled(False)

    config = model.config
    architecture_pass = (
        getattr(config, "model_type", None) == "qwen3"
        and int(getattr(config, "hidden_size", -1)) == 2048
        and int(getattr(config, "num_hidden_layers", -1)) == 28
        and int(getattr(config, "vocab_size", -1)) == 151936
        and type(model).__name__ == "Qwen3ForCausalLM"
        and len(model.model.layers) == 28
    )
    if not architecture_pass:
        raise RuntimeError("MODEL_RUNTIME_ARCHITECTURE_MISMATCH")

    warm_inputs = _prepare_inputs(tokenizer, NEUTRAL_TEXTS[0], device)
    with torch.inference_mode():
        _forward(model, warm_inputs)

    neutral_hashes = [_sha256_text(text) for text in NEUTRAL_TEXTS]
    per_record: list[dict[str, Any]] = []
    all_hidden_length_pass = True
    all_block16_pass = True
    all_block26_pass = True
    all_block27_pass = True
    all_final_norm_pass = True
    all_pre_post_distinction_pass = True
    all_last_valid_pass = True
    all_float32_pass = True
    all_checkpoint_shapes_pass = True
    all_hook_cleanup_pass = True
    all_zero_perturbation_pass = True

    for text in NEUTRAL_TEXTS:
        inputs = _prepare_inputs(tokenizer, text, device)
        hooked = _hooked_forward(model, inputs)
        outputs = hooked["outputs"]
        hidden_states = outputs.hidden_states
        hidden_length = len(hidden_states)
        hidden_length_pass = hidden_length == 29

        capture16 = hooked["capture16"]
        capture26 = hooked["capture26"]
        capture27 = hooked["capture27"]
        block16_status = _block_oracle_status(capture16, hidden_states[17])
        block26_status = _block_oracle_status(capture26, hidden_states[27])

        h_pre = capture27.value
        h_post = hidden_states[28]
        block27_status = {
            "status": "PASS"
            if (h_pre.ndim == 3 and h_pre.shape[-1] == 2048)
            else "FAIL",
            "shape": list(h_pre.shape),
            "captured_output_not_input": bool(
                not torch.equal(h_pre, hidden_states[27])
            ),
            "captured_pre_not_post": bool(
                not torch.equal(h_pre, h_post)
            ),
        }
        final_norm_status = _final_rmsnorm_status(model, h_pre, h_post)
        checkpoint_tensors = runner.extract_checkpoint_tensors(
            hidden_states, h_pre
        )
        checkpoint_shapes = _checkpoint_shape_statuses(checkpoint_tensors)
        selected = runner.extract_last_token_representations(
            checkpoint_tensors, inputs["attention_mask"]
        )
        last_valid_status, last_valid_meta = _last_valid_token_status(
            checkpoint_tensors, inputs["attention_mask"]
        )
        float32_status, float32_meta = _float32_boundary_status(selected)

        with torch.inference_mode():
            baseline_outputs = _forward(model, inputs)
        zero_status = _hook_zero_perturbation_status(
            baseline_outputs.logits,
            outputs.logits,
        )

        hook_cleanup_pass = bool(hooked["hook_cleanup_ok"])
        captured27_before_clean = capture27.value
        with torch.inference_mode():
            _forward(model, inputs)
        stale_hook_triggered = capture27.value is not captured27_before_clean
        hook_cleanup_pass = hook_cleanup_pass and not stale_hook_triggered

        record = {
            "neutral_input_sha256": _sha256_text(text),
            "hidden_state_tuple_length": hidden_length,
            "hidden_state_tuple_length_pass": bool(hidden_length_pass),
            "block16_oracle": block16_status,
            "block26_oracle": block26_status,
            "block27_pre_final_hook": block27_status,
            "final_rmsnorm_relationship": final_norm_status,
            "checkpoint_shape_statuses": checkpoint_shapes,
            "last_valid_token": last_valid_status,
            "last_valid_token_meta": last_valid_meta,
            "float32_analysis_boundary": float32_status,
            "float32_analysis_boundary_meta": float32_meta,
            "hook_cleanup": "PASS" if hook_cleanup_pass else "FAIL",
            "hook_zero_perturbation": zero_status,
        }
        per_record.append(record)

        all_hidden_length_pass = all_hidden_length_pass and hidden_length_pass
        all_block16_pass = all_block16_pass and block16_status["status"] == "PASS"
        all_block26_pass = all_block26_pass and block26_status["status"] == "PASS"
        all_block27_pass = all_block27_pass and block27_status["status"] == "PASS"
        all_final_norm_pass = (
            all_final_norm_pass and final_norm_status["status"] == "PASS"
        )
        all_pre_post_distinction_pass = (
            all_pre_post_distinction_pass
            and final_norm_status["pre_post_distinction_pass"]
        )
        all_last_valid_pass = all_last_valid_pass and last_valid_status == "PASS"
        all_float32_pass = all_float32_pass and float32_status == "PASS"
        all_checkpoint_shapes_pass = (
            all_checkpoint_shapes_pass
            and all(status == "PASS" for status in checkpoint_shapes.values())
        )
        all_hook_cleanup_pass = all_hook_cleanup_pass and hook_cleanup_pass
        all_zero_perturbation_pass = (
            all_zero_perturbation_pass
            and zero_status["status"] == "PASS"
        )

    special_contract_pass = tokenizer_identity_pass
    overall_pass = all(
        [
            snapshot_identity_pass,
            tokenizer_identity_pass,
            architecture_pass,
            all_hidden_length_pass,
            all_block16_pass,
            all_block26_pass,
            all_block27_pass,
            all_final_norm_pass,
            all_pre_post_distinction_pass,
            all_zero_perturbation_pass,
            all_hook_cleanup_pass,
            all_last_valid_pass,
            special_contract_pass,
            all_float32_pass,
            all_checkpoint_shapes_pass,
        ]
    )

    return {
        "schema_version": "1.0.0",
        "experiment": EXPERIMENT,
        "classification": "ENGINEERING_MODEL_HOOK_QUALIFICATION_ONLY",
        "timestamp_utc": _utc_now(),
        "repository_commit": repository_commit,
        "frozen_preregistration_sha256": frozen_sha,
        "model": {
            "name": MODEL_NAME,
            "snapshot_identity": EXPECTED_SNAPSHOT,
            "snapshot_identity_status": "PASS" if snapshot_identity_pass else "FAIL",
            "class": type(model).__name__,
            "model_type": getattr(config, "model_type", None),
            "hidden_size": int(getattr(config, "hidden_size", -1)),
            "num_hidden_layers": int(getattr(config, "num_hidden_layers", -1)),
            "transformer_blocks": len(model.model.layers),
            "vocab_size": int(getattr(config, "vocab_size", -1)),
            "runtime_dtype": "float16",
            "model_runtime_architecture": "PASS" if architecture_pass else "FAIL",
        },
        "tokenizer": {
            "metadata": tokenizer_metadata,
            "runtime_identity": "PASS" if tokenizer_identity_pass else "FAIL",
            "special_token_runtime_contract": "PASS" if special_contract_pass else "FAIL",
        },
        "runtime_versions": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "numpy": np.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_runtime": torch.version.cuda,
            "gpu_name": torch.cuda.get_device_name(0),
        },
        "neutral_input_hashes": neutral_hashes,
        "hidden_state_tuple_length_required": 29,
        "hidden_state_tuple_length_status": "PASS" if all_hidden_length_pass else "FAIL",
        "block16_oracle": "PASS" if all_block16_pass else "FAIL",
        "block26_oracle": "PASS" if all_block26_pass else "FAIL",
        "block27_pre_final_hook_runtime": "PASS" if all_block27_pass else "FAIL",
        "final_rmsnorm_relationship": "PASS" if all_final_norm_pass else "FAIL",
        "primary_pre_post_distinction": "PASS" if all_pre_post_distinction_pass else "FAIL",
        "hook_zero_perturbation": "PASS" if all_zero_perturbation_pass else "FAIL",
        "hook_cleanup": "PASS" if all_hook_cleanup_pass else "FAIL",
        "last_valid_token_runtime": "PASS" if all_last_valid_pass else "FAIL",
        "float32_analysis_boundary_runtime": "PASS" if all_float32_pass else "FAIL",
        "checkpoint_runtime_shapes": "PASS" if all_checkpoint_shapes_pass else "FAIL",
        "technical_validity": "VALID" if overall_pass else "INVALID",
        "overall_qualification_status": (
            "MODEL_HOOK_ENGINEERING_QUALIFIED"
            if overall_pass
            else "MODEL_HOOK_ENGINEERING_QUALIFICATION_FAILED"
        ),
        "formal_data_accessed": False,
        "controlled_prompt_text_accessed": False,
        "formal_fit_data_accessed": False,
        "formal_eval_data_accessed": False,
        "scientific_measurement_performed": False,
        "scientific_result_created": False,
        "formal_run_authorized": False,
        "result_status": "NOT_RUN",
        "per_record_evidence": per_record,
    }


if __name__ == "__main__":
    raise SystemExit(main())
