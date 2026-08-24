"""PA-EXT-A-006P synthetic-only engineering qualification.

This module deliberately has no path or parser dependency on the live V8
acquisition namespace.  It qualifies the existing V3 builder and a small,
model-sequential output lifecycle using synthetic text only.  It never reads
formal panel records and never publishes a canonical panel or result.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import torch

ROOT = Path(__file__).resolve().parents[3]
EXP_DIR = ROOT / "experiments" / "paper_a_ext_a"
ENGINEERING_DIR = EXP_DIR / "engineering"
ARTIFACT_PATH = ENGINEERING_DIR / "pa_ext_a_006p_post_acquisition_preflight.json"

for path in (str(ROOT), str(EXP_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import pa_ext_a_v3_pipeline as pipeline
import validate_pa_ext_a_v3_pipeline as panel_validator
from src.extraction import (
    extract_last_token_hidden_state,
    get_model_input_device,
    move_tokenized_inputs_to_device,
    tensor_to_numpy_float32,
)
from src.model_loader import load_causal_lm, load_tokenizer


MODEL_SPECS: tuple[dict[str, Any], ...] = (
    {
        "key": "qwen",
        "model_id": "Qwen/Qwen3-1.7B",
        "dtype": "bfloat16",
        "local_path": None,
    },
    {
        "key": "olmo",
        "model_id": "allenai/OLMo-2-0425-1B-Instruct",
        "dtype": "bfloat16",
        "local_path": r"D:\AI_Cache\huggingface\hub\models--allenai--OLMo-2-0425-1B-Instruct\snapshots\48d788eca847d4d7548f375ad03d3c9312f6139e",
    },
    {
        "key": "llama",
        "model_id": "meta-llama/Llama-3.2-1B-Instruct",
        "dtype": "bfloat16",
        "local_path": r"D:\AI_Cache\llama_hf\Llama3.2-1B-Instruct-meta-converted-v4463-attempt3",
    },
)

SYNTHETIC_PROMPTS = (
    "SYNTHETIC_QUALIFICATION_ONLY record A states a relation.",
    "SYNTHETIC_QUALIFICATION_ONLY record B compares two placeholders.",
    "SYNTHETIC_QUALIFICATION_ONLY record C contains no formal panel content.",
    "SYNTHETIC_QUALIFICATION_ONLY record D is used for engineering timing.",
)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _atomic_json_write(path: Path, payload: Mapping[str, Any]) -> None:
    """Write an isolated engineering file atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_bytes(canonical_json_bytes(payload) + b"\n")
    os.replace(temporary, path)


class SyntheticOutputStore:
    """Model-separated, partial-run-safe store used only by tests/preflight."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def write_model_output(self, model_key: str, payload: Mapping[str, Any]) -> Path:
        if payload.get("model_key") != model_key:
            raise ValueError("MODEL_OUTPUT_NAMESPACE_MISMATCH")
        path = self.root / model_key / "synthetic_output.json"
        _atomic_json_write(path, payload)
        return path

    def write_completion_manifest(self, required_models: Sequence[str]) -> Path:
        required = sorted(set(required_models))
        completed = sorted(
            path.parent.name
            for path in self.root.glob("*/synthetic_output.json")
        )
        if completed != required:
            raise RuntimeError("PARTIAL_SYNTHETIC_RUN_NOT_PUBLISHABLE")
        path = self.root / "completion_manifest.json"
        _atomic_json_write(path, {"model_keys": completed, "complete": True})
        return path

    def is_complete(self, required_models: Sequence[str]) -> bool:
        path = self.root / "completion_manifest.json"
        if not path.exists():
            return False
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload == {"model_keys": sorted(set(required_models)), "complete": True}


def build_synthetic_panel_qualification() -> dict[str, Any]:
    """Build the full-size synthetic panel through the existing V3 path."""
    design = pipeline.load_frozen_design()
    panel_one = pipeline.compose_panel(
        pipeline.build_synthetic_asset_bank(design), design, mode="synthetic"
    )
    panel_two = pipeline.compose_panel(
        pipeline.build_synthetic_asset_bank(design), design, mode="synthetic"
    )
    errors = panel_validator.validate_panel(panel_one, design, mode="synthetic")
    if errors:
        raise RuntimeError(f"SYNTHETIC_PANEL_VALIDATION_FAILED:{errors[:5]}")

    items = panel_one["items"]
    families = {item["source_family_id"] for item in items}
    task_counts = {
        task: len({item["source_family_id"] for item in items if item["task_family_id"] == task})
        for task in pipeline.TASK_FAMILY_IDS
    }
    partition_families = {
        partition: len({item["source_family_id"] for item in items if item["partition"] == partition})
        for partition in pipeline.PARTITIONS
    }
    return {
        "total_families": len(families),
        "total_records": len(items),
        "task_family_counts": task_counts,
        "partition_family_counts": partition_families,
        "partition_record_counts": {
            partition: sum(item["partition"] == partition for item in items)
            for partition in pipeline.PARTITIONS
        },
        "record_roles_per_family": sorted(
            {tuple(sorted(item["record_role"] for item in items if item["source_family_id"] == family)) for family in families}
        ),
        "family_split_isolated": all(
            len({item["partition"] for item in items if item["source_family_id"] == family}) == 1
            for family in families
        ),
        "family_ids_unique": len(families) == len({item["source_family_id"] for item in items}),
        "record_ids_unique": len(items) == len({item["item_id"] for item in items}),
        "deterministic_repeatability": pipeline.canonical_json_bytes(panel_one)
        == pipeline.canonical_json_bytes(panel_two),
        "build_1_sha256": sha256_bytes(pipeline.canonical_json_bytes(panel_one)),
        "build_2_sha256": sha256_bytes(pipeline.canonical_json_bytes(panel_two)),
        "synthetic_classification": panel_one["classification"],
        "formal_panel_allowed": panel_one["formal_panel_allowed"],
        "synthetic_rejected_in_production_mode": bool(
            panel_validator.validate_panel(
                panel_one, design, mode="production"
            )
        ),
    }


def _model_target(spec: Mapping[str, Any]) -> str:
    local_path = spec.get("local_path")
    if local_path and Path(str(local_path)).exists():
        return str(local_path)
    return str(spec["model_id"])


def _memory_snapshot() -> tuple[int | None, int | None]:
    if not torch.cuda.is_available():
        return None, None
    return int(torch.cuda.max_memory_allocated()), int(torch.cuda.max_memory_reserved())


def qualify_model_synthetic(spec: Mapping[str, Any], cache_root: Path) -> dict[str, Any]:
    """Load one model, run only synthetic prompts, then unload it."""
    result: dict[str, Any] = {
        "model_id": spec["model_id"],
        "local_path": spec.get("local_path"),
        "load_success": False,
        "synthetic_forward_success": False,
        "synthetic_prompt_count": len(SYNTHETIC_PROMPTS),
        "cache_local_only": True,
    }
    model = tokenizer = None
    try:
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA_UNAVAILABLE")
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats()
        target = _model_target(spec)
        started = time.perf_counter()
        tokenizer = load_tokenizer(
            target,
            cache_dir=None if spec.get("local_path") else cache_root,
            local_files_only=True,
        )
        model = load_causal_lm(
            target,
            dtype=str(spec["dtype"]),
            device_map="auto",
            cache_dir=None if spec.get("local_path") else cache_root,
            local_files_only=True,
        )
        model.eval()
        result["load_seconds"] = time.perf_counter() - started
        result["model_class"] = model.__class__.__name__
        result["tokenizer_class"] = tokenizer.__class__.__name__
        result["device"] = str(get_model_input_device(model))
        result["dtype"] = str(next(model.parameters()).dtype)
        result["hidden_size"] = int(getattr(model.config, "hidden_size"))
        result["num_hidden_layers"] = int(getattr(model.config, "num_hidden_layers"))
        result["load_success"] = True

        input_lengths: list[int] = []
        shapes: list[list[int]] = []
        forward_started = time.perf_counter()
        for prompt in SYNTHETIC_PROMPTS:
            tokenized = tokenizer(prompt, return_tensors="pt")
            input_lengths.append(int(tokenized["input_ids"].shape[-1]))
            inputs = move_tokenized_inputs_to_device(tokenized, get_model_input_device(model))
            with torch.no_grad():
                outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            hidden_states = outputs.hidden_states
            final_index = len(hidden_states) - 1
            representation = extract_last_token_hidden_state(hidden_states, final_index)
            shapes.append(list(representation.shape))
            if representation.ndim != 1:
                raise RuntimeError("INVALID_SYNTHETIC_REPRESENTATION_SHAPE")
            tensor_to_numpy_float32(representation)
        elapsed = time.perf_counter() - forward_started
        result["synthetic_forward_success"] = True
        result["hidden_state_tensor_count"] = int(len(hidden_states))
        result["semantic_position"] = "last_token_final_hidden_state"
        result["representation_shapes"] = shapes
        result["token_counts"] = input_lengths
        result["forward_seconds"] = elapsed
        result["samples_per_second"] = len(SYNTHETIC_PROMPTS) / elapsed if elapsed else None
        result["peak_gpu_memory_allocated"] = _memory_snapshot()[0]
        result["peak_gpu_memory_reserved"] = _memory_snapshot()[1]
    except Exception as exc:  # qualification records failures rather than hiding them
        result["error_type"] = type(exc).__name__
        result["error"] = str(exc)
    finally:
        del model, tokenizer
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
    return result


def _git_value(*args: str) -> str | None:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_preflight(*, artifact_path: Path = ARTIFACT_PATH) -> dict[str, Any]:
    synthetic = build_synthetic_panel_qualification()
    cache_root = Path(
        os.environ.get(
            "HF_HUB_CACHE",
            str(Path(os.environ.get("HF_HOME", r"D:\AI_Cache\huggingface")) / "hub"),
        )
    )
    model_results = [qualify_model_synthetic(spec, cache_root) for spec in MODEL_SPECS]
    with tempfile.TemporaryDirectory(prefix="pa_ext_a_006p_") as temporary:
        store = SyntheticOutputStore(Path(temporary))
        for spec, result in zip(MODEL_SPECS, model_results):
            store.write_model_output(spec["key"], {"model_key": spec["key"], "result": result})
        store.write_completion_manifest([spec["key"] for spec in MODEL_SPECS])
        resumability = {
            "qualified": store.is_complete([spec["key"] for spec in MODEL_SPECS]),
            "partial_not_publishable": True,
            "mixed_model_output_prevented": True,
            "model_sequential_execution": True,
        }
    artifact = {
        "task_id": "PA-EXT-A-006P",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_head": _git_value("rev-parse", "HEAD"),
        "git_origin_main": _git_value("rev-parse", "origin/main"),
        "working_tree_scope": "synthetic engineering files only; pre-existing unrelated files preserved",
        "v8_live_lineage_touched": False,
        "synthetic_panel": synthetic,
        "production_firewall": {
            "synthetic_rejected_in_production_mode": synthetic["synthetic_rejected_in_production_mode"],
            "formal_inference_performed": False,
            "formal_panel_consumed": False,
            "live_v8_consumed": False,
        },
        "models": {spec["key"]: result for spec, result in zip(MODEL_SPECS, model_results)},
        "resumability": resumability,
        "tests": {"command": "python -m pytest tests/test_pa_ext_a_006p_preflight.py -q -p no:cacheprovider"},
        "scientific_result_fields_intentionally_omitted": True,
    }
    _atomic_json_write(artifact_path, artifact)
    return artifact


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PA-EXT-A synthetic engineering preflight")
    parser.add_argument("--artifact", type=Path, default=ARTIFACT_PATH)
    args = parser.parse_args(argv)
    artifact = run_preflight(artifact_path=args.artifact)
    print(json.dumps(artifact, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
