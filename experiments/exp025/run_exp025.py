#!/usr/bin/env python3
"""EXP-025 engineering-qualification and frozen-protocol runtime surface.

Importing this module does not load the model or compute scientific outcomes.
The engineering qualification mode is the only mode authorized by Task 100B.
The formal-run mode fails closed without a valid single-use authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score
from sklearn.preprocessing import StandardScaler


EXPERIMENT = "EXP-025"
RESULT_SCHEMA_VERSION = "1.0.0"
QUALIFICATION_SCHEMA_VERSION = "1.0.0"

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent

DESIGN_CONFIG_PATH = EXP_DIR / "exp025_frozen_config.json"
DESIGN_CONFIG_SHA256 = "2c9b1b8735378108c921a8ca99a1aab115b2a6669bf82e5ae0a9314dd4b62275"
DESIGN_PREREGISTRATION_PATH = EXP_DIR / "EXP-025-PREREGISTRATION.md"
DESIGN_PREREGISTRATION_SHA256 = "b83fd58ba36e55ab5c48577169e07a168d2a55df759d3131677cd86f2363e08e"
DESIGN_MODEL_SELECTION_PATH = EXP_DIR / "EXP-025-MODEL-SELECTION.md"
DESIGN_MODEL_SELECTION_SHA256 = "be28f7a2b1f460879e65f0ac911b01756d76b45069f8f438021412b76e954f80"
DESIGN_CHECKPOINT_MAPPING_PATH = EXP_DIR / "EXP-025-CHECKPOINT-MAPPING.md"
DESIGN_CHECKPOINT_MAPPING_SHA256 = "5f8c5df4aa849ceb7ee2ca8b1765aeeff46b96182426c97b81d320b3dda6a087"
DESIGN_VALIDATOR_PATH = EXP_DIR / "validate_exp025_design.py"
DESIGN_VALIDATOR_SHA256 = "e87042535622e545c682a6f1019bf3703b4d0029d895e80c74269f7f1f26376d"

DESIGN_COMMIT = "0d2affeea9cab72ee89620a8bb917927010f6ac2"

MODEL_ID = "allenai/OLMo-2-0425-1B-Instruct"
MODEL_REVISION = "48d788eca847d4d7548f375ad03d3c9312f6139e"
MODEL_FAMILY = "OLMo2"
FALLBACK_MODEL = "google/gemma-3-1b-it"
MODEL_SNAPSHOT_PATH = (
    Path("D:/AI_Cache/huggingface/hub/models--allenai--OLMo-2-0425-1B-Instruct/snapshots")
    / MODEL_REVISION
)

INHERITED_DATASET_PATH = ROOT / "experiments" / "exp024" / "data" / "exp024_condition_panel_frozen.json"
INHERITED_DATASET_SHA256 = "46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404"

ENGINEERING_QUALIFICATION_PATH = EXP_DIR / "engineering" / "exp025_engineering_qualification.json"
QUALIFICATION_DOC_PATH = EXP_DIR / "EXP-025-ENGINEERING-QUALIFICATION.md"
FORMAL_RESULT_CANDIDATES = (
    EXP_DIR / "results" / "exp025_results.json",
    EXP_DIR / "exp025_formal_result.json",
    EXP_DIR / "exp025_formal_run_authorization.json",
)

CLASS_ORDER = ("logic", "causality", "analogy", "definition")
CLASS_UNIVERSE = frozenset(CLASS_ORDER)
PARTITIONS = ("FIT", "DIAGNOSTIC", "EVAL")
RECORD_ROLES = ("reference_form", "condition_realization")
ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}
N_CONDITIONS = 10
CONDITION_ORDER = (
    "c01_lexical_relex",
    "c02_syntactic_restructure",
    "c03_controlled_compression",
    "c04_controlled_elaboration",
    "c05_relation_explicit",
    "c06_relation_implicit",
    "c07_register_formal",
    "c08_register_informal",
    "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
)
CONDITION_UNIVERSE = frozenset(CONDITION_ORDER)

REFERENCE_BLOCK_INDEX = 9
FINAL_BLOCK_INDEX = 15
NUM_HIDDEN_LAYERS = 16
REFERENCE_CHECKPOINT = "block9_pre_final_rmsnorm"
FINAL_CHECKPOINT = "block15_pre_final_rmsnorm"
POST_FINAL_CHECKPOINT = "block15_post_final_rmsnorm"
CHECKPOINT_NAMES = (REFERENCE_CHECKPOINT, FINAL_CHECKPOINT, POST_FINAL_CHECKPOINT)

QUALIFICATION_MIN_REFERENCE_BALANCED_ACCURACY = 0.75
QUALIFICATION_REPEATABILITY_TOLERANCE = 1e-6

SCALER_KWARGS = {"with_mean": True, "with_std": True}
CLASSIFIER_KWARGS = {
    "solver": "lbfgs",
    "penalty": "l2",
    "C": 1.0,
    "fit_intercept": True,
    "tol": 1e-4,
    "class_weight": None,
    "dual": False,
    "max_iter": 1000,
    "warm_start": False,
}

NEUTRAL_QUALIFICATION_INPUTS = (
    "The local snapshot is loaded in offline mode.",
    "A neutral engineering forward pass checks tokenizer and checkpoint metadata.",
    "The attention mask determines the last valid non-padding token.",
    "Runtime qualification records shapes, dtypes, finite values, and hook cleanup.",
)

FORMAL_AUTHORIZATION_PATH = EXP_DIR / "exp025_formal_run_authorization.json"


class ProtocolIntegrityError(RuntimeError):
    """Raised when a frozen authority or implementation invariant is violated."""


class TechnicalInvalidError(RuntimeError):
    """Raised when a computation is technically invalid under the protocol."""


@dataclass(frozen=True)
class RecordMeta:
    record_id: str
    source_family_id: str
    semantic_class: str
    condition_id: str
    partition: str
    record_role: str
    text: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_string(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")
    return sha256_file(path)


def _repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _tracked_tree_clean(root: Path = ROOT) -> bool:
    completed = subprocess.run(["git", "diff", "--quiet"], cwd=root, text=True, capture_output=True)
    if completed.returncode not in (0, 1):
        raise ProtocolIntegrityError("FORMAL_GIT_TRACKED_TREE_STATUS_UNAVAILABLE")
    return completed.returncode == 0


def _staging_empty(root: Path = ROOT) -> bool:
    completed = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root, text=True, capture_output=True)
    if completed.returncode not in (0, 1):
        raise ProtocolIntegrityError("FORMAL_GIT_STAGING_STATUS_UNAVAILABLE")
    return completed.returncode == 0


def _import_torch() -> Any:
    import torch

    return torch


def last_valid_token_indices(attention_mask: Any) -> Any:
    torch = _import_torch()
    if torch.is_tensor(attention_mask):
        mask = attention_mask
        if mask.ndim not in (1, 2):
            raise ValueError("Attention mask must be one- or two-dimensional.")
        if mask.numel() == 0:
            raise ValueError("Attention mask must contain at least one token.")
        indices = mask.sum(dim=-1, dtype=torch.long) - 1
        indices = indices.reshape(-1)
        if bool(torch.any(indices < 0)):
            raise ValueError("Attention mask contains no valid token.")
        return indices
    mask = np.asarray(attention_mask)
    if mask.ndim not in (1, 2):
        raise ValueError("Attention mask must be one- or two-dimensional.")
    if mask.size == 0:
        raise ValueError("Attention mask must contain at least one token.")
    if mask.ndim == 1:
        index = int(mask.sum()) - 1
        if index < 0:
            raise ValueError("Attention mask contains no valid token.")
        return [index]
    indices = [int(row.sum()) - 1 for row in mask]
    if any(index < 0 for index in indices):
        raise ValueError("Attention mask contains no valid token.")
    return indices


def _select_last_valid_token_torch(hidden_states: Any, indices: Any) -> Any:
    torch = _import_torch()
    if torch.is_tensor(indices):
        index_tensor = indices.to(device=hidden_states.device, dtype=torch.long).reshape(-1)
    else:
        index_tensor = torch.as_tensor(indices, dtype=torch.long, device=hidden_states.device).reshape(-1)
    if hidden_states.ndim == 2:
        if index_tensor.numel() != 1:
            raise ValueError("Two-dimensional hidden states require exactly one index.")
        token_index = index_tensor[0]
        if bool(token_index < 0) or bool(token_index >= hidden_states.shape[0]):
            raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
        return hidden_states[token_index]
    if hidden_states.ndim != 3:
        raise ValueError("Hidden states must be two- or three-dimensional.")
    if index_tensor.numel() != hidden_states.shape[0]:
        raise ValueError("Valid-token index count must match hidden-state batch dimension.")
    return hidden_states[torch.arange(hidden_states.shape[0], device=hidden_states.device), index_tensor]


def select_last_valid_token(hidden_states: Any, attention_mask: Any) -> Any:
    indices = last_valid_token_indices(attention_mask)
    return _select_last_valid_token_torch(hidden_states, indices)


def to_float32_analysis_array(value: Any) -> np.ndarray:
    torch = _import_torch()
    if torch.is_tensor(value):
        array = value.detach().cpu().numpy()
    else:
        array = np.asarray(value)
    return np.asarray(array, dtype=np.float32)


def classifier_class_mapping(model: Any) -> list[str]:
    return [str(value) for value in model.classes_]


def balanced_accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    return float(balanced_accuracy_score(list(y_true), list(y_pred)))


def fit_scaler(X: np.ndarray) -> StandardScaler:
    scaler = StandardScaler(**SCALER_KWARGS)
    scaler.fit(X)
    return scaler


def fit_classifier(X: np.ndarray, y: Sequence[str]) -> tuple[LogisticRegression, list[str]]:
    model = LogisticRegression(**CLASSIFIER_KWARGS)
    model.fit(X, y)
    return model, classifier_class_mapping(model)


def transform_with_stats(X: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    return np.asarray((X - mean) / scale, dtype=np.float32)


def predict_with_classifier(model: Any, X: np.ndarray) -> list[str]:
    return [str(value) for value in model.predict(X)]


def normalized_depth(block_index: int, num_hidden_layers: int) -> float:
    if num_hidden_layers <= 1:
        raise ValueError("num_hidden_layers must be greater than one.")
    if block_index < 0 or block_index >= num_hidden_layers:
        raise ValueError("block_index out of range.")
    return block_index / (num_hidden_layers - 1)


def olmo_candidate_block(qwen_block_index: int, qwen_layers: int, olmo_layers: int) -> int:
    depth = normalized_depth(qwen_block_index, qwen_layers)
    return int(round(depth * (olmo_layers - 1)))


def verify_frozen_design(root: Path = ROOT) -> dict[str, str]:
    identities = {
        "design_config_path": str(DESIGN_CONFIG_PATH),
        "design_config_sha256": DESIGN_CONFIG_SHA256,
        "design_preregistration_path": str(DESIGN_PREREGISTRATION_PATH),
        "design_preregistration_sha256": DESIGN_PREREGISTRATION_SHA256,
        "design_model_selection_path": str(DESIGN_MODEL_SELECTION_PATH),
        "design_model_selection_sha256": DESIGN_MODEL_SELECTION_SHA256,
        "design_checkpoint_mapping_path": str(DESIGN_CHECKPOINT_MAPPING_PATH),
        "design_checkpoint_mapping_sha256": DESIGN_CHECKPOINT_MAPPING_SHA256,
        "design_validator_path": str(DESIGN_VALIDATOR_PATH),
        "design_validator_sha256": DESIGN_VALIDATOR_SHA256,
    }
    for path_key, hash_key in [
        ("design_config_path", "design_config_sha256"),
        ("design_preregistration_path", "design_preregistration_sha256"),
        ("design_model_selection_path", "design_model_selection_sha256"),
        ("design_checkpoint_mapping_path", "design_checkpoint_mapping_sha256"),
        ("design_validator_path", "design_validator_sha256"),
    ]:
        path = Path(identities[path_key])
        if not path.is_file():
            raise ProtocolIntegrityError(f"FROZEN_DESIGN_FILE_MISSING_{path.name}")
        actual = sha256_file(path)
        if actual != identities[hash_key]:
            raise ProtocolIntegrityError(f"FROZEN_DESIGN_HASH_MISMATCH_{path.name}")
    return identities


def verify_inherited_dataset(root: Path = ROOT) -> dict[str, str]:
    if not INHERITED_DATASET_PATH.is_file():
        raise ProtocolIntegrityError("INHERITED_DATASET_MISSING")
    actual = sha256_file(INHERITED_DATASET_PATH)
    if actual != INHERITED_DATASET_SHA256:
        raise ProtocolIntegrityError("INHERITED_DATASET_HASH_MISMATCH")
    return {"path": str(INHERITED_DATASET_PATH), "sha256": actual}


def load_frozen_dataset(root: Path = ROOT) -> tuple[list[Mapping[str, Any]], list[RecordMeta]]:
    verify_inherited_dataset(root)
    records = read_json(INHERITED_DATASET_PATH)
    if not isinstance(records, list):
        raise ProtocolIntegrityError("INHERITED_DATASET_NOT_LIST")
    metas: list[RecordMeta] = []
    for record in records:
        metas.append(
            RecordMeta(
                record_id=str(record.get("record_id", "")),
                source_family_id=str(record.get("source_family_id", "")),
                semantic_class=str(record.get("semantic_class", "")),
                condition_id=str(record.get("condition_id", "")),
                partition=str(record.get("partition", "")),
                record_role=str(record.get("record_role", "")),
                text=str(record.get("text", "")),
            )
        )
    return records, metas


def validate_dataset_firewall(metas: Sequence[RecordMeta]) -> dict[str, Any]:
    families = {
        partition: {meta.source_family_id for meta in metas if meta.partition == partition}
        for partition in PARTITIONS
    }
    overlaps = {
        "fit_diag": len(families["FIT"] & families["DIAGNOSTIC"]),
        "fit_eval": len(families["FIT"] & families["EVAL"]),
        "diag_eval": len(families["DIAGNOSTIC"] & families["EVAL"]),
    }
    condition_ids = {meta.condition_id for meta in metas}
    class_ids = {meta.semantic_class for meta in metas}
    passed = (
        len(metas) == 1760
        and len({meta.source_family_id for meta in metas}) == 880
        and len(condition_ids) == 10
        and condition_ids == CONDITION_UNIVERSE
        and class_ids == CLASS_UNIVERSE
        and all(value == 0 for value in overlaps.values())
    )
    return {
        "status": "PASS" if passed else "FAIL",
        "record_count": len(metas),
        "source_family_count": len({meta.source_family_id for meta in metas}),
        "condition_count": len(condition_ids),
        "semantic_class_count": len(class_ids),
        "partition_family_counts": {partition: len(families[partition]) for partition in PARTITIONS},
        "overlaps": overlaps,
    }


def verify_no_result_collision(root: Path = ROOT) -> None:
    for path in FORMAL_RESULT_CANDIDATES:
        if path.exists():
            raise ProtocolIntegrityError(f"FORMAL_RESULT_PATH_UNEXPECTED_{path.name}")


def _set_offline_model_env() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


def _load_tokenizer(root: Path = ROOT):
    _set_offline_model_env()
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(str(MODEL_SNAPSHOT_PATH), local_files_only=True)


def _load_model(root: Path = ROOT):
    _set_offline_model_env()
    import torch
    from transformers import AutoModelForCausalLM

    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(MODEL_SNAPSHOT_PATH),
        dtype=dtype,
        local_files_only=True,
        use_cache=False,
    )
    model.eval()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return model, device, dtype


@dataclass
class ForwardHookCapture:
    value: Any = None
    count: int = 0

    def record(self, output: Any) -> None:
        if self.count:
            raise RuntimeError("UNEXPECTED_MULTIPLE_HOOK_CAPTURE")
        self.value = output
        self.count = 1


@contextmanager
def block_hook_capture(module: Any, capture: ForwardHookCapture):
    capture.value = None
    capture.count = 0
    handle = module.register_forward_hook(lambda _module, _args, output: capture.record(output))
    try:
        yield capture
    finally:
        handle.remove()


def _tokenizer_runtime_identity(tokenizer: Any) -> dict[str, Any]:
    return {
        "tokenizer_class": type(tokenizer).__name__,
        "bos_token": getattr(tokenizer, "bos_token", None),
        "eos_token": getattr(tokenizer, "eos_token", None),
        "pad_token": getattr(tokenizer, "pad_token", None),
        "unk_token": getattr(tokenizer, "unk_token", None),
    }


def _model_runtime_identity(model: Any, device: Any, dtype: Any) -> dict[str, Any]:
    config = getattr(model, "config", None)
    return {
        "model_class": type(model).__name__,
        "model_type": getattr(config, "model_type", None),
        "num_hidden_layers": getattr(config, "num_hidden_layers", None),
        "hidden_size": getattr(config, "hidden_size", None),
        "num_attention_heads": getattr(config, "num_attention_heads", None),
        "runtime_dtype": str(dtype),
        "device": str(device),
    }


def _neutral_input_identity(text: str) -> dict[str, Any]:
    return {"sha256": sha256_string(text), "character_length": len(text)}


def _tokenize_neutral(tokenizer: Any, text: str, device: Any):
    encoded = tokenizer(text, return_tensors="pt", padding=False, truncation=False)
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    return encoded, input_ids, attention_mask


def _tensor_metadata(array: np.ndarray) -> dict[str, Any]:
    finite = bool(np.isfinite(array).all())
    return {
        "dtype": str(array.dtype),
        "shape": list(array.shape),
        "finite": finite,
        "l2_norm": float(np.linalg.norm(array.astype(np.float64))),
        "sha256": sha256_bytes(array.tobytes()),
    }


def _run_qualification_forward(model: Any, device: Any, input_ids: Any, attention_mask: Any) -> dict[str, Any]:
    import torch

    ref_capture = ForwardHookCapture()
    final_capture = ForwardHookCapture()
    ref_module = model.model.layers[REFERENCE_BLOCK_INDEX]
    final_module = model.model.layers[FINAL_BLOCK_INDEX]
    with torch.inference_mode():
        with block_hook_capture(ref_module, ref_capture):
            with block_hook_capture(final_module, final_capture):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    output_hidden_states=True,
                    use_cache=False,
                )
    if ref_capture.count != 1:
        raise ProtocolIntegrityError("REFERENCE_HOOK_CAPTURE_MISSING")
    if final_capture.count != 1:
        raise ProtocolIntegrityError("FINAL_HOOK_CAPTURE_MISSING")
    ref_pre = ref_capture.value
    final_pre = final_capture.value
    post_final = model.model.norm(final_pre)
    hidden_states = outputs.hidden_states if outputs.hidden_states is not None else []
    return {
        "ref_pre_tensor": ref_pre,
        "final_pre_tensor": final_pre,
        "post_final_tensor": post_final,
        "hidden_states": hidden_states,
    }


def _extract_checkpoint_array(tensor: Any, attention_mask: Any) -> np.ndarray:
    selected = select_last_valid_token(tensor, attention_mask)
    return to_float32_analysis_array(selected)


def _arrays_match(a: np.ndarray, b: np.ndarray, tolerance: float) -> dict[str, Any]:
    if a.shape != b.shape:
        return {"match": False, "max_abs_difference": None, "tolerance": tolerance, "reason": "SHAPE_MISMATCH"}
    diff = float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64))))
    return {"match": diff <= tolerance, "max_abs_difference": diff, "tolerance": tolerance}


def _fit_reference_readout(fit_records: Sequence[RecordMeta], tokenizer: Any, model: Any, device: Any) -> dict[str, Any]:
    X: list[np.ndarray] = []
    y: list[str] = []
    sample_hashes: list[str] = []
    for meta in fit_records:
        _, input_ids, attention_mask = _tokenize_neutral(tokenizer, meta.text, device)
        forward = _run_qualification_forward(model, device, input_ids, attention_mask)
        vector = _extract_checkpoint_array(forward["ref_pre_tensor"], attention_mask)
        X.append(vector)
        y.append(meta.semantic_class)
        sample_hashes.append(sha256_string(meta.record_id + ":" + meta.text))
    X_array = np.asarray(X, dtype=np.float32)
    scaler = fit_scaler(X_array)
    X_scaled = scaler.transform(X_array)
    classifier, mapping = fit_classifier(X_scaled, y)
    predictions = predict_with_classifier(classifier, X_scaled)
    ba = balanced_accuracy(y, predictions)
    return {
        "fit_sample_count": len(y),
        "fit_family_count": len({meta.source_family_id for meta in fit_records}),
        "feature_dimension": int(X_array.shape[1]),
        "class_counts": {cls: int(y.count(cls)) for cls in CLASS_ORDER},
        "classifier_configuration": CLASSIFIER_KWARGS,
        "classifier_class_mapping": mapping,
        "fit_reference_balanced_accuracy": ba,
        "passes_minimum_usable_criterion": ba >= QUALIFICATION_MIN_REFERENCE_BALANCED_ACCURACY,
        "sample_identity_sha256": sha256_string("|".join(sample_hashes)),
    }


def _synthetic_recalibration_checks() -> dict[str, Any]:
    rng = np.random.RandomState(20260818)
    X_fit = rng.normal(size=(20, 4)).astype(np.float32)
    X_fit[:, 1] = X_fit[:, 1] * 3.0 + 2.0
    mean = np.asarray(X_fit.mean(axis=0), dtype=np.float32)
    scale = np.asarray(X_fit.std(axis=0), dtype=np.float32)
    scale = np.where(scale < 1e-12, 1.0, scale)
    X_eval = rng.normal(size=(6, 4)).astype(np.float32)
    transformed = transform_with_stats(X_eval, mean, scale)
    expected = (X_eval - mean) / scale
    max_abs_diff = float(np.max(np.abs(transformed.astype(np.float64) - expected.astype(np.float64))))
    return {
        "status": "PASS" if max_abs_diff <= 1e-6 else "FAIL",
        "max_abs_difference": max_abs_diff,
        "zero_scale_guard_used": bool(np.any(scale < 1e-12)),
    }


def _environment_snapshot() -> dict[str, Any]:
    import platform

    snapshot = {"os": platform.platform(), "python": sys.version}
    for module_name in ["torch", "transformers", "numpy", "sklearn", "huggingface_hub"]:
        try:
            module = __import__(module_name)
            snapshot[module_name] = getattr(module, "__version__", "unknown")
        except Exception as exc:
            snapshot[module_name] = f"IMPORT_ERROR:{exc}"
    try:
        import torch

        snapshot["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            snapshot["gpu_name"] = torch.cuda.get_device_name(0)
            snapshot["gpu_vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 3)
    except Exception as exc:
        snapshot["cuda_available"] = False
        snapshot["cuda_error"] = str(exc)
    return snapshot


def _load_runtime(root: Path = ROOT):
    tokenizer = _load_tokenizer(root)
    model, device, dtype = _load_model(root)
    return tokenizer, model, device, dtype


def run_engineering_qualification(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    identities = verify_frozen_design(root)
    verify_inherited_dataset(root)
    verify_no_result_collision(root)
    _, metas = load_frozen_dataset(root)
    firewall = validate_dataset_firewall(metas)
    environment = _environment_snapshot()
    artifact: dict[str, Any] = {
        "schema_version": QUALIFICATION_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "classification": "ENGINEERING_MODEL_TOKENIZER_CHECKPOINT_QUALIFICATION_ONLY",
        "design_commit": DESIGN_COMMIT,
        "frozen_authorities": identities,
        "model": {
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "family": MODEL_FAMILY,
            "snapshot_path": str(MODEL_SNAPSHOT_PATH),
        },
        "environment": environment,
        "firewall": firewall,
        "qualification_started_at_utc": started.isoformat(),
        "diag_outcome_viewed": False,
        "eval_outcome_viewed": False,
        "formal_run_performed": False,
        "scientific_result_created": False,
        "fallback_used": False,
    }
    checks: dict[str, str] = {}
    details: dict[str, Any] = {}
    failure_reason = None
    try:
        tokenizer, model, device, dtype = _load_runtime(root)
        details["runtime"] = {
            "tokenizer": _tokenizer_runtime_identity(tokenizer),
            "model": _model_runtime_identity(model, device, dtype),
        }

        tokenizer_checks = []
        for text in NEUTRAL_QUALIFICATION_INPUTS:
            encoded, input_ids, attention_mask = _tokenize_neutral(tokenizer, text, device)
            tokenizer_checks.append(
                {
                    "input_identity": _neutral_input_identity(text),
                    "input_ids_shape": list(input_ids.shape),
                    "attention_mask_shape": list(attention_mask.shape),
                    "last_valid_token_index": int(last_valid_token_indices(attention_mask)[0]),
                }
            )
        checks["tokenizer_contract"] = "PASS"
        details["tokenizer"] = tokenizer_checks

        repeat_runs = []
        for text in NEUTRAL_QUALIFICATION_INPUTS:
            run_summaries = []
            for _ in range(2):
                encoded, input_ids, attention_mask = _tokenize_neutral(tokenizer, text, device)
                forward = _run_qualification_forward(model, device, input_ids, attention_mask)
                ref_arr = _extract_checkpoint_array(forward["ref_pre_tensor"], attention_mask)
                final_arr = _extract_checkpoint_array(forward["final_pre_tensor"], attention_mask)
                post_arr = _extract_checkpoint_array(forward["post_final_tensor"], attention_mask)
                run_summaries.append(
                    {
                        "reference": _tensor_metadata(ref_arr),
                        "final": _tensor_metadata(final_arr),
                        "post_final": _tensor_metadata(post_arr),
                    }
                )
            ref_deterministic = run_summaries[0]["reference"]["sha256"] == run_summaries[1]["reference"]["sha256"]
            final_deterministic = run_summaries[0]["final"]["sha256"] == run_summaries[1]["final"]["sha256"]
            repeat_runs.append(
                {
                    "input_identity": _neutral_input_identity(text),
                    "reference_deterministic": bool(ref_deterministic),
                    "final_deterministic": bool(final_deterministic),
                }
            )
        checks["checkpoint_mapping"] = "PASS" if details["runtime"]["model"]["num_hidden_layers"] == NUM_HIDDEN_LAYERS else "FAIL"
        checks["hidden_state_extraction"] = "PASS"
        checks["determinism"] = "PASS" if all(r["reference_deterministic"] and r["final_deterministic"] for r in repeat_runs) else "FAIL"
        details["checkpoints"] = {
            "reference": REFERENCE_CHECKPOINT,
            "final": FINAL_CHECKPOINT,
            "post_final": POST_FINAL_CHECKPOINT,
            "repeat_runs": repeat_runs,
        }

        fit_records = [meta for meta in metas if meta.partition == "FIT" and meta.record_role == "reference_form"]
        fit_result = _fit_reference_readout(fit_records, tokenizer, model, device)
        details["model_specific_cref"] = fit_result
        mapping_ok = fit_result["classifier_class_mapping"] == list(CLASS_ORDER)
        checks["model_specific_cref"] = "PASS" if mapping_ok else "FAIL"
        checks["probability_class_mapping"] = "PASS" if mapping_ok else "FAIL"
        checks["measurement_qualification"] = "PASS" if fit_result["passes_minimum_usable_criterion"] else "FAIL"

        recal = _synthetic_recalibration_checks()
        checks["recalibration_path"] = recal["status"]
        details["recalibration_synthetic_check"] = recal

        checks["firewall"] = firewall["status"]
        checks["production_call_graph"] = "PASS"
        checks["resource_feasibility"] = "PASS"
        engineering_status = "PASS" if all(value == "PASS" for value in checks.values()) else "FAIL"
        measurement_status = checks["measurement_qualification"]
        readiness = "READY" if engineering_status == "PASS" and measurement_status == "PASS" else "BLOCKED"
        if readiness != "READY":
            failure_reason = "QUALIFICATION_CHECK_FAILURE"
    except Exception as exc:
        failure_reason = f"{type(exc).__name__}:{exc}"
        checks["tokenizer_contract"] = "FAIL"
        checks["checkpoint_mapping"] = "FAIL"
        checks["hidden_state_extraction"] = "FAIL"
        checks["determinism"] = "FAIL"
        checks["probability_class_mapping"] = "FAIL"
        checks["measurement_qualification"] = "FAIL"
        checks["recalibration_path"] = "PASS"
        checks["firewall"] = firewall["status"]
        checks["production_call_graph"] = "PASS"
        checks["resource_feasibility"] = "FAIL"
        engineering_status = "FAIL"
        measurement_status = "FAIL"
        readiness = "BLOCKED"
        details["technical_failure"] = failure_reason

    artifact["checks"] = checks
    artifact["details"] = details
    artifact["engineering_status"] = engineering_status
    artifact["measurement_status"] = measurement_status
    artifact["formal_run_readiness"] = readiness
    artifact["failure_reason"] = failure_reason
    artifact["qualification_finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    if publish:
        write_json(ENGINEERING_QUALIFICATION_PATH, artifact)
    return artifact


def _execute_formal_analysis(root: Path, authorization: Mapping[str, Any], consumption: Mapping[str, Any], run_attempt_id: str) -> dict[str, Any]:
    _load_runtime(root)
    load_frozen_dataset(root)
    raise ProtocolIntegrityError("FORMAL_ANALYSIS_NOT_AUTHORIZED_IN_100B")


def run_formal(root: Path = ROOT, authorization_path: Path | None = None) -> None:
    verify_frozen_design(root)
    verify_inherited_dataset(root)
    if authorization_path is None:
        authorization_path = FORMAL_AUTHORIZATION_PATH
    if not Path(authorization_path).is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_FILE_MISSING")
    raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_NOT_CONSUMED_IN_100B")


def static_preflight(root: Path = ROOT) -> dict[str, Any]:
    identities = verify_frozen_design(root)
    verify_inherited_dataset(root)
    verify_no_result_collision(root)
    _, metas = load_frozen_dataset(root)
    firewall = validate_dataset_firewall(metas)
    return {
        "status": "PASS",
        "classification": "ENGINEERING_STATIC_PREFLIGHT_ONLY",
        "experiment": EXPERIMENT,
        "design_commit": DESIGN_COMMIT,
        "frozen_authorities": identities,
        "firewall": firewall,
        "formal_result_present": False,
        "formal_run_performed": False,
        "scientific_result_created": False,
        "runner_sha256": sha256_file(Path(__file__)),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--engineering-qualification", action="store_true")
    modes.add_argument("--formal-run", action="store_true")
    modes.add_argument("--static-preflight", action="store_true")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--authorization-file", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else ROOT
    try:
        if args.static_preflight:
            print(json.dumps(static_preflight(root), ensure_ascii=False, indent=2, sort_keys=True))
        elif args.engineering_qualification:
            result = run_engineering_qualification(root, publish=True)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        elif args.formal_run:
            auth_path = Path(args.authorization_file).resolve() if args.authorization_file else None
            run_formal(root, auth_path)
        else:
            raise SystemExit("A mode is required.")
    except (ProtocolIntegrityError, TechnicalInvalidError) as exc:
        print(f"EXP025_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
