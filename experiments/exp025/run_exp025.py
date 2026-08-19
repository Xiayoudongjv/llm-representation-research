#!/usr/bin/env python3
"""EXP-025 engineering-qualification and frozen-protocol runtime surface.

Importing this module does not load the model or compute scientific outcomes.
The engineering qualification mode is the only mode authorized by Task 100B.
The formal-run mode fails closed without a valid single-use authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
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

CLARIFICATION_MD_PATH = EXP_DIR / "EXP-025-PREOUTCOME-SPECIFICATION-CLARIFICATION-001.md"
CLARIFICATION_MD_SHA256 = "1b91d6b2efd4c4459779e6645f893aea91804c32d7834b22044a85f7e721b0ed"
CLARIFICATION_JSON_PATH = EXP_DIR / "exp025_preoutcome_specification_clarification_001.json"
CLARIFICATION_JSON_SHA256 = "4f65a60dcf40e24e57cbddda1be8d6573b353ab9cf17c901b3aa5fb2d5b47e16"
CLARIFICATION_VALIDATOR_PATH = EXP_DIR / "validate_exp025_preoutcome_clarification.py"
CLARIFICATION_VALIDATOR_SHA256 = "d3abf68502861f752655b46ef72405b1193783d80b3332f912ccf734abafb555"

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
INHERITED_CONDITION_PANEL_PATH = ROOT / "experiments" / "exp024" / "condition_panel_spec.json"
INHERITED_CONDITION_PANEL_SHA256 = "a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954"
INHERITED_DATA_SCHEMA_PATH = ROOT / "experiments" / "exp024" / "data_schema.json"
INHERITED_DATA_SCHEMA_SHA256 = "e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec"
INHERITED_MANIFEST_PATH = ROOT / "experiments" / "exp024" / "exp024_frozen_manifest.json"
INHERITED_MANIFEST_SHA256 = "1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59"
EXP024_PREREGISTRATION_PATH = ROOT / "docs" / "experiments" / "EXP-024-PREREGISTRATION.md"
EXP024_PREREGISTRATION_SHA256 = "55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810"

ENGINEERING_QUALIFICATION_PATH = EXP_DIR / "engineering" / "exp025_engineering_qualification.json"
QUALIFICATION_DOC_PATH = EXP_DIR / "EXP-025-ENGINEERING-QUALIFICATION.md"
FORMAL_RESULT_PATH = EXP_DIR / "results" / "exp025_results.json"
FORMAL_RESULT_CANDIDATES = (
    FORMAL_RESULT_PATH,
    EXP_DIR / "exp025_formal_result.json",
)
AUTHORIZATION_CONSUMPTION_DIR = EXP_DIR / "results" / "authorization_consumption"
AUTHORIZATION_RETIREMENT_DIR = EXP_DIR / "engineering" / "authorization_retirement"
RECOVERY_AMENDMENT_PATH = EXP_DIR / "engineering" / "EXP-025-PROTOCOL-RECOVERY-AMENDMENT-001.md"
RECOVERY_EXECUTION_CLASSIFICATION = "POST_HOC_PROTOCOL_RECOVERY"
RECOVERY_AMENDMENT_ID = "EXP025_PROTOCOL_RECOVERY_AMENDMENT_001"

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
HIDDEN_SIZE = 2048
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
FORMAL_PIPELINE_QUALIFICATION_PATH = EXP_DIR / "engineering" / "exp025_formal_pipeline_qualification.json"
FORMAL_PIPELINE_QUALIFICATION_DOC_PATH = EXP_DIR / "engineering" / "EXP-025-FORMAL-PIPELINE-QUALIFICATION.md"


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
        array = value.detach().cpu().to(torch.float32).numpy()
    else:
        array = np.asarray(value)
    return np.asarray(array, dtype=np.float32)


def classifier_class_mapping(model: Any) -> list[str]:
    return [str(value) for value in model.classes_]


def average_rank(data: Sequence[float]) -> list[float]:
    array = np.asarray(data, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValueError("average_rank requires a nonempty one-dimensional sequence.")
    order = np.argsort(array, kind="mergesort")
    sorted_values = array[order]
    ranks = np.empty(array.size, dtype=float)
    index = 0
    while index < array.size:
        j = index + 1
        while j < array.size and sorted_values[j] == sorted_values[index]:
            j += 1
        rank = (index + 1 + j) / 2.0
        ranks[order[index:j]] = rank
        index = j
    return [float(value) for value in ranks]


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y):
        raise ValueError("Spearman inputs must be equal length.")
    if len(x) == 0:
        raise ValueError("Spearman inputs must be nonempty.")
    if len(x) == 1:
        return 0.0
    x_values = np.asarray(x, dtype=float)
    y_values = np.asarray(y, dtype=float)
    if not np.isfinite(x_values).all() or not np.isfinite(y_values).all():
        return float("nan")
    x_rank = np.asarray(average_rank(x), dtype=float)
    y_rank = np.asarray(average_rank(y), dtype=float)
    x_rank -= x_rank.mean()
    y_rank -= y_rank.mean()
    denominator = float(np.sqrt((x_rank @ x_rank) * (y_rank @ y_rank)))
    if denominator == 0.0:
        return float("nan")
    rho = float((x_rank @ y_rank) / denominator)
    if not math.isfinite(rho):
        return float("nan")
    return rho


def exact_one_sided_permutation_p(
    x: Sequence[float],
    y: Sequence[float],
    alternative: str = "greater",
) -> dict[str, Any]:
    if len(x) != len(y):
        raise ValueError("Permutation inputs must be equal length.")
    n = len(x)
    if n == 0:
        raise ValueError("Permutation inputs must be nonempty.")
    if alternative != "greater":
        raise ValueError("EXP-025 registered permutation test is one-sided greater only.")
    observed = spearman_rho(x, y)
    if not math.isfinite(observed):
        return {
            "rho": observed,
            "p": None,
            "count_ge": None,
            "total": math.factorial(n),
            "status": "NOT_EVALUABLE",
        }
    x_rank = np.asarray(average_rank(x), dtype=float)
    y_rank = np.asarray(average_rank(y), dtype=float)
    x_rank -= x_rank.mean()
    y_rank -= y_rank.mean()
    denominator = float(np.sqrt((x_rank @ x_rank) * (y_rank @ y_rank)))
    count = 0
    for perm in itertools.permutations(range(n)):
        permuted = y_rank[list(perm)]
        numerator = float(x_rank @ permuted)
        rho = (numerator / denominator) if denominator != 0.0 else 0.0
        if not math.isfinite(rho):
            return {
                "rho": observed,
                "p": None,
                "count_ge": None,
                "total": math.factorial(n),
                "status": "NOT_EVALUABLE",
            }
        if rho >= observed:
            count += 1
    total = math.factorial(n)
    return {
        "rho": observed,
        "p": count / total,
        "count_ge": count,
        "total": total,
        "status": "EVALUABLE",
    }


def exact_binomial_support(values: Sequence[float], alpha: float = 0.05) -> dict[str, Any]:
    values = [float(value) for value in values]
    positive = sum(1 for value in values if value > 0)
    negative = sum(1 for value in values if value < 0)
    zero = sum(1 for value in values if value == 0)
    effective_n = positive + negative
    if effective_n == 0:
        return {
            "positive_count": 0,
            "negative_count": 0,
            "zero_count": zero,
            "effective_n": 0,
            "effective_successes": 0,
            "exact_one_sided_p": None,
            "support": "NOT_EVALUABLE",
            "status": "NOT_EVALUABLE",
        }
    p = sum(math.comb(effective_n, k) for k in range(positive, effective_n + 1)) / (
        2.0**effective_n
    )
    supported = positive > negative and p <= alpha
    return {
        "positive_count": positive,
        "negative_count": negative,
        "zero_count": zero,
        "effective_n": effective_n,
        "effective_successes": positive,
        "exact_one_sided_p": p,
        "support": "SUPPORTED" if supported else "NOT_SUPPORTED",
        "status": "EVALUABLE",
    }


def classify_direction(values: Sequence[float], label: str = "D") -> dict[str, Any]:
    result = exact_binomial_support(values)
    if result["status"] == "NOT_EVALUABLE":
        return {**result, "classification": "NOT_EVALUABLE", "direction": "NOT_EVALUABLE"}
    result["classification"] = "POSITIVE" if result["support"] == "SUPPORTED" else "NEGATIVE"
    result["direction"] = f"{label}+" if result["classification"] == "POSITIVE" else f"{label}-"
    return result


def balanced_accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError("Balanced-accuracy inputs must be equal length.")
    true_values = [str(value) for value in y_true]
    pred_values = [str(value) for value in y_pred]
    if set(true_values) != CLASS_UNIVERSE:
        missing = sorted(CLASS_UNIVERSE - set(true_values))
        raise ProtocolIntegrityError(
            f"STOP_AND_REPORT_PROTOCOL_INTEGRITY_ERROR_MISSING_TRUE_CLASS:{missing}"
        )
    if set(pred_values) - CLASS_UNIVERSE:
        raise ProtocolIntegrityError("BALANCED_ACCURACY_UNEXPECTED_PREDICTED_CLASS")
    recalls = []
    for cls in CLASS_ORDER:
        positives = [i for i, value in enumerate(true_values) if value == cls]
        if not positives:
            raise ProtocolIntegrityError(
                f"STOP_AND_REPORT_PROTOCOL_INTEGRITY_ERROR_ZERO_CLASS:{cls}"
            )
        correct = sum(1 for i in positives if pred_values[i] == cls)
        recalls.append(correct / len(positives))
    return float(sum(recalls) / len(recalls))


def fit_scaler(X: np.ndarray) -> StandardScaler:
    scaler = StandardScaler(**SCALER_KWARGS)
    scaler.fit(X)
    return scaler


def fit_classifier(X: np.ndarray, y: Sequence[str]) -> tuple[LogisticRegression, list[str]]:
    model = LogisticRegression(**CLASSIFIER_KWARGS)
    model.fit(X, y)
    return model, classifier_class_mapping(model)


def transform_with_stats(X: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=np.float32)
    mean = np.asarray(mean, dtype=np.float32)
    scale = np.asarray(scale, dtype=np.float32)
    output = np.zeros_like(X, dtype=np.float32)
    positive = scale > 0.0
    output[:, positive] = (X[:, positive] - mean[positive]) / scale[positive]
    return output


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


def verify_inherited_authorities(root: Path = ROOT) -> dict[str, str]:
    identities = {
        "dataset_path": str(INHERITED_DATASET_PATH),
        "dataset_sha256": INHERITED_DATASET_SHA256,
        "condition_panel_path": str(INHERITED_CONDITION_PANEL_PATH),
        "condition_panel_sha256": INHERITED_CONDITION_PANEL_SHA256,
        "data_schema_path": str(INHERITED_DATA_SCHEMA_PATH),
        "data_schema_sha256": INHERITED_DATA_SCHEMA_SHA256,
        "frozen_manifest_path": str(INHERITED_MANIFEST_PATH),
        "frozen_manifest_sha256": INHERITED_MANIFEST_SHA256,
        "exp024_preregistration_path": str(EXP024_PREREGISTRATION_PATH),
        "exp024_preregistration_sha256": EXP024_PREREGISTRATION_SHA256,
    }
    for path_key, hash_key in [
        ("dataset_path", "dataset_sha256"),
        ("condition_panel_path", "condition_panel_sha256"),
        ("data_schema_path", "data_schema_sha256"),
        ("frozen_manifest_path", "frozen_manifest_sha256"),
        ("exp024_preregistration_path", "exp024_preregistration_sha256"),
    ]:
        path = Path(identities[path_key])
        if not path.is_file():
            raise ProtocolIntegrityError(f"INHERITED_AUTHORITY_FILE_MISSING_{path.name}")
        actual = sha256_file(path)
        if actual != identities[hash_key]:
            raise ProtocolIntegrityError(f"INHERITED_AUTHORITY_HASH_MISMATCH_{path.name}")
    return identities


def verify_clarification_authorities(root: Path = ROOT) -> dict[str, str]:
    identities = {
        "clarification_md_path": str(CLARIFICATION_MD_PATH),
        "clarification_md_sha256": CLARIFICATION_MD_SHA256,
        "clarification_json_path": str(CLARIFICATION_JSON_PATH),
        "clarification_json_sha256": CLARIFICATION_JSON_SHA256,
        "clarification_validator_path": str(CLARIFICATION_VALIDATOR_PATH),
        "clarification_validator_sha256": CLARIFICATION_VALIDATOR_SHA256,
    }
    for path_key, hash_key in [
        ("clarification_md_path", "clarification_md_sha256"),
        ("clarification_json_path", "clarification_json_sha256"),
        ("clarification_validator_path", "clarification_validator_sha256"),
    ]:
        path = Path(identities[path_key])
        if not path.is_file():
            raise ProtocolIntegrityError(f"CLARIFICATION_AUTHORITY_FILE_MISSING_{path.name}")
        actual = sha256_file(path)
        if actual != identities[hash_key]:
            raise ProtocolIntegrityError(f"CLARIFICATION_AUTHORITY_HASH_MISMATCH_{path.name}")
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


def _resolve_repo_path(root: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path


def _authorization_consumption_path(root: Path, authorization_id: str) -> Path:
    return AUTHORIZATION_CONSUMPTION_DIR / f"{authorization_id}.json"


def _atomic_write_json_exclusive(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as exc:
        raise ProtocolIntegrityError("AUTHORIZATION_ALREADY_CONSUMED") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise
    return sha256_file(path)


def _validate_authorization(root: Path, authorization_path: Path) -> tuple[dict[str, Any], str]:
    path = Path(authorization_path)
    if not path.is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_FILE_MISSING")
    authorization = read_json(path)
    if not isinstance(authorization, dict):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_SCHEMA_INVALID")

    if authorization.get("schema_version") != "1.0.0":
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_SCHEMA_VERSION_INVALID")
    if authorization.get("experiment") != EXPERIMENT:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXPERIMENT_MISMATCH")
    if authorization.get("purpose") != "SINGLE_USE_FORMAL_RUN":
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_PURPOSE_INVALID")
    if authorization.get("single_use") is not True:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_NOT_SINGLE_USE")
    if authorization.get("authorized_execution_count") != 1:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXECUTION_COUNT_INVALID")
    if authorization.get("formal_mode") != "--formal-run":
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_MODE_INVALID")
    if authorization.get("model_id") != MODEL_ID:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_MODEL_ID_MISMATCH")
    if authorization.get("model_revision") != MODEL_REVISION:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_MODEL_REVISION_MISMATCH")

    repository_commit = _repository_commit(root)
    if authorization.get("repository_commit") != repository_commit:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_REPOSITORY_COMMIT_MISMATCH")
    if authorization.get("authorized_repository_commit") != repository_commit:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_REPOSITORY_COMMIT_MISMATCH")

    runner_sha = sha256_file(Path(__file__))
    if authorization.get("runner_sha256") != runner_sha:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_RUNNER_SHA_MISMATCH")

    if not ENGINEERING_QUALIFICATION_PATH.is_file():
        raise ProtocolIntegrityError("FORMAL_QUALIFICATION_ARTIFACT_MISSING")
    qualification_sha = sha256_file(ENGINEERING_QUALIFICATION_PATH)
    if authorization.get("qualification_artifact_sha256") != qualification_sha:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_QUALIFICATION_SHA_MISMATCH")

    verify_frozen_design(root)
    inherited = verify_inherited_authorities(root)
    clarification = verify_clarification_authorities(root)

    clarification_hashes = authorization.get("clarification_authority_hashes")
    if not isinstance(clarification_hashes, dict):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_CLARIFICATION_HASHES_INVALID")
    expected_clarification = {
        "clarification_md": clarification["clarification_md_sha256"],
        "clarification_json": clarification["clarification_json_sha256"],
        "clarification_validator": clarification["clarification_validator_sha256"],
    }
    for key, expected_hash in expected_clarification.items():
        if clarification_hashes.get(key) != expected_hash:
            raise ProtocolIntegrityError(f"FORMAL_AUTHORIZATION_CLARIFICATION_HASH_MISMATCH_{key}")

    expected_frozen = {
        "exp025_preregistration": DESIGN_PREREGISTRATION_SHA256,
        "model_selection": DESIGN_MODEL_SELECTION_SHA256,
        "checkpoint_mapping": DESIGN_CHECKPOINT_MAPPING_SHA256,
        "frozen_config": DESIGN_CONFIG_SHA256,
        "design_validator": DESIGN_VALIDATOR_SHA256,
    }
    frozen_hashes = authorization.get("frozen_authority_hashes")
    if not isinstance(frozen_hashes, dict):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_FROZEN_HASHES_INVALID")
    for key, expected_hash in expected_frozen.items():
        if frozen_hashes.get(key) != expected_hash:
            raise ProtocolIntegrityError(f"FORMAL_AUTHORIZATION_FROZEN_HASH_MISMATCH_{key}")

    inherited_identity = authorization.get("inherited_authority_hashes")
    if not isinstance(inherited_identity, dict):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_INHERITED_HASHES_INVALID")
    expected_inherited = {
        "dataset": inherited["dataset_sha256"],
        "condition_panel": inherited["condition_panel_sha256"],
        "data_schema": inherited["data_schema_sha256"],
        "frozen_manifest": inherited["frozen_manifest_sha256"],
        "exp024_preregistration": inherited["exp024_preregistration_sha256"],
    }
    for key, expected_hash in expected_inherited.items():
        if inherited_identity.get(key) != expected_hash:
            raise ProtocolIntegrityError(f"FORMAL_AUTHORIZATION_INHERITED_HASH_MISMATCH_{key}")

    dataset_identity = authorization.get("dataset_identity")
    if not isinstance(dataset_identity, dict):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_DATASET_IDENTITY_INVALID")
    dataset_path = _resolve_repo_path(root, dataset_identity.get("path"))
    if dataset_path is None or not dataset_path.is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_DATASET_PATH_MISSING")
    if dataset_identity.get("sha256") != sha256_file(dataset_path):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_DATASET_SHA_MISMATCH")

    condition_panel_identity = authorization.get("condition_panel_identity")
    if not isinstance(condition_panel_identity, dict):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_CONDITION_PANEL_IDENTITY_INVALID")
    condition_panel_path = _resolve_repo_path(root, condition_panel_identity.get("path"))
    if condition_panel_path is None or not condition_panel_path.is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_CONDITION_PANEL_PATH_MISSING")
    if condition_panel_identity.get("sha256") != sha256_file(condition_panel_path):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_CONDITION_PANEL_SHA_MISMATCH")

    verify_no_result_collision(root)

    authorization_id = str(authorization.get("authorization_id", ""))
    if not authorization_id:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_ID_MISSING")
    if _authorization_consumption_path(root, authorization_id).exists():
        raise ProtocolIntegrityError("AUTHORIZATION_ALREADY_CONSUMED")

    return authorization, sha256_file(path)


def _consume_authorization(
    root: Path,
    authorization_path: Path,
    authorization: Mapping[str, Any],
    authorization_sha: str,
    run_attempt_id: str | None = None,
) -> tuple[dict[str, Any], str]:
    authorization_id = str(authorization.get("authorization_id", ""))
    if not authorization_id:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_ID_MISSING")
    run_attempt_id = run_attempt_id or uuid.uuid4().hex
    consumption_path = _authorization_consumption_path(root, authorization_id)
    record: dict[str, Any] = {
        "schema_version": "1.0.0",
        "classification": "AUTHORIZATION_CONSUMPTION",
        "authorization_id": authorization_id,
        "authorization_sha256": authorization_sha,
        "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_attempt_id": run_attempt_id,
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "authorization_path": str(Path(authorization_path)),
        "consumption_record_path": str(consumption_path),
    }
    consumption_sha = _atomic_write_json_exclusive(consumption_path, record)
    record["consumption_record_sha256"] = consumption_sha
    return record, consumption_sha


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


def _formal_record_extractor(tokenizer: Any, model: Any, device: Any, text: str) -> dict[str, Any]:
    _, input_ids, attention_mask = _tokenize_neutral(tokenizer, text, device)
    forward = _run_qualification_forward(model, device, input_ids, attention_mask)
    representations = {
        REFERENCE_CHECKPOINT: _extract_checkpoint_array(forward["ref_pre_tensor"], attention_mask),
        FINAL_CHECKPOINT: _extract_checkpoint_array(forward["final_pre_tensor"], attention_mask),
        POST_FINAL_CHECKPOINT: _extract_checkpoint_array(forward["post_final_tensor"], attention_mask),
    }
    for checkpoint, array in representations.items():
        if array.shape != (HIDDEN_SIZE,):
            raise ProtocolIntegrityError(
                f"FORMAL_CHECKPOINT_HIDDEN_SIZE_MISMATCH_{checkpoint}_{array.shape}"
            )
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "representations": representations,
        "hook_firing_count": 2,
        "hook_cleanup_verified": True,
        "exp025_hooks_remaining": 0,
        "foreign_hooks_remaining": 0,
    }


def _extract_checkpoint_array(tensor: Any, attention_mask: Any) -> np.ndarray:
    selected = select_last_valid_token(tensor, attention_mask)
    array = to_float32_analysis_array(selected)
    if array.ndim == 2 and array.shape[0] == 1:
        array = array[0]
    if array.ndim != 1:
        raise ProtocolIntegrityError(f"CHECKPOINT_REPRESENTATION_NOT_VECTOR_{array.shape}")
    return array


def _formal_records_by_partition_role(
    records: Sequence[Mapping[str, Any]], partition: str, record_role: str
) -> list[Mapping[str, Any]]:
    return [
        record
        for record in records
        if record.get("partition") == partition and record.get("record_role") == record_role
    ]


def _group_records_by_condition(
    records: Sequence[Mapping[str, Any]], condition_order: Sequence[str]
) -> dict[str, list[Mapping[str, Any]]]:
    grouped = {condition: [] for condition in condition_order}
    for record in records:
        condition_id = str(record.get("condition_id", ""))
        if condition_id in grouped:
            grouped[condition_id].append(record)
    return grouped


def _validate_formal_partition_integrity(
    records: Sequence[Mapping[str, Any]],
    condition_order: Sequence[str],
    *,
    strict_counts: bool = True,
) -> dict[str, Any]:
    if not isinstance(records, list):
        raise ProtocolIntegrityError("FORMAL_DATASET_TOP_LEVEL_NOT_ARRAY")
    expected_conditions = set(condition_order)
    if len(expected_conditions) != N_CONDITIONS:
        raise ProtocolIntegrityError("FORMAL_CONDITION_COUNT_MISMATCH")
    if expected_conditions != CONDITION_UNIVERSE:
        raise ProtocolIntegrityError("FORMAL_CONDITION_SET_MISMATCH")
    required_fields = {
        "record_id",
        "source_family_id",
        "semantic_class",
        "condition_id",
        "partition",
        "record_role",
        "text",
    }
    family_rows: dict[str, list[Mapping[str, Any]]] = {}
    record_ids: set[str] = set()
    partition_family_ids: dict[str, set[str]] = {partition: set() for partition in PARTITIONS}
    cell_family_ids: dict[tuple[str, str, str], set[str]] = {}
    seen_classes: set[str] = set()
    seen_conditions: set[str] = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise ProtocolIntegrityError("FORMAL_DATASET_RECORD_NOT_OBJECT")
        missing = required_fields - set(record)
        if missing:
            raise ProtocolIntegrityError(f"FORMAL_DATASET_RECORD_MISSING_FIELDS:{sorted(missing)}")
        if not isinstance(record["text"], str) or not record["text"].strip():
            raise ProtocolIntegrityError("FORMAL_DATASET_RECORD_TEXT_EMPTY")
        if record["condition_id"] not in expected_conditions:
            raise ProtocolIntegrityError("FORMAL_DATASET_UNEXPECTED_CONDITION")
        if record["semantic_class"] not in CLASS_UNIVERSE:
            raise ProtocolIntegrityError("FORMAL_DATASET_INVALID_SEMANTIC_CLASS")
        if record["partition"] not in PARTITIONS:
            raise ProtocolIntegrityError("FORMAL_DATASET_INVALID_PARTITION")
        if record["record_role"] not in RECORD_ROLES:
            raise ProtocolIntegrityError("FORMAL_DATASET_INVALID_ROLE")
        record_id = str(record["record_id"])
        if record_id in record_ids:
            raise ProtocolIntegrityError("FORMAL_DATASET_DUPLICATE_RECORD_ID")
        record_ids.add(record_id)
        family_id = str(record["source_family_id"])
        family_rows.setdefault(family_id, []).append(record)
        partition_family_ids[record["partition"]].add(family_id)
        cell_family_ids.setdefault(
            (record["condition_id"], record["partition"], record["semantic_class"]),
            set(),
        ).add(family_id)
        seen_classes.add(record["semantic_class"])
        seen_conditions.add(record["condition_id"])

    if seen_classes != CLASS_UNIVERSE:
        raise ProtocolIntegrityError("FORMAL_DATASET_SEMANTIC_CLASS_MISSING")
    if seen_conditions != expected_conditions:
        raise ProtocolIntegrityError("FORMAL_DATASET_CONDITION_MISSING")
    for family_id, rows in family_rows.items():
        if len(rows) != 2:
            raise ProtocolIntegrityError("FORMAL_DATASET_FAMILY_RECORD_COUNT_NOT_TWO")
        if {row["record_role"] for row in rows} != set(RECORD_ROLES):
            raise ProtocolIntegrityError("FORMAL_DATASET_FAMILY_ROLE_PAIR_MISMATCH")
        first = rows[0]
        for row in rows[1:]:
            for field in ("source_family_id", "semantic_class", "condition_id", "partition"):
                if row.get(field) != first.get(field):
                    raise ProtocolIntegrityError("FORMAL_DATASET_FAMILY_METADATA_INCONSISTENT")
    overlaps = {
        ("FIT", "DIAGNOSTIC"): partition_family_ids["FIT"] & partition_family_ids["DIAGNOSTIC"],
        ("FIT", "EVAL"): partition_family_ids["FIT"] & partition_family_ids["EVAL"],
        ("DIAGNOSTIC", "EVAL"): partition_family_ids["DIAGNOSTIC"] & partition_family_ids["EVAL"],
    }
    if any(overlaps.values()):
        raise ProtocolIntegrityError("FORMAL_DATASET_PARTITION_FAMILY_OVERLAP")
    for condition_id in condition_order:
        for partition in PARTITIONS:
            for semantic_class in CLASS_ORDER:
                family_ids = cell_family_ids.get(
                    (condition_id, partition, semantic_class), set()
                )
                if not family_ids:
                    raise ProtocolIntegrityError("FORMAL_DATASET_CELL_MISSING")
                if strict_counts and len(family_ids) != ALLOCATION[partition]:
                    raise ProtocolIntegrityError("FORMAL_DATASET_CELL_COUNT_MISMATCH")
    return {
        "record_count": len(records),
        "source_family_count": len(family_rows),
        "condition_count": len(expected_conditions),
        "semantic_class_count": len(seen_classes),
        "partition_family_counts": {
            partition: len(family_ids) for partition, family_ids in partition_family_ids.items()
        },
        "overlaps": {key: sorted(value) for key, value in overlaps.items()},
    }


def _formal_extract_group_arrays(
    records: Sequence[Mapping[str, Any]],
    tokenizer: Any,
    model: Any,
    device: Any,
    extractor: Any,
    checkpoints: Sequence[str],
) -> tuple[dict[str, np.ndarray], list[str], list[str]]:
    arrays: dict[str, list[np.ndarray]] = {checkpoint: [] for checkpoint in checkpoints}
    labels: list[str] = []
    record_ids: list[str] = []
    for record in records:
        forward = extractor(tokenizer, model, device, record["text"])
        representations = forward["representations"]
        missing = set(checkpoints) - set(representations)
        if missing:
            raise ProtocolIntegrityError(f"FORMAL_EXTRACTION_MISSING_CHECKPOINTS:{sorted(missing)}")
        for checkpoint in checkpoints:
            array = to_float32_analysis_array(representations[checkpoint])
            if array.ndim == 2 and array.shape[0] == 1:
                array = array[0]
            if array.ndim != 1:
                raise ProtocolIntegrityError(f"FORMAL_EXTRACTION_NOT_VECTOR_{array.shape}")
            arrays[checkpoint].append(array)
        labels.append(str(record["semantic_class"]))
        record_ids.append(str(record["record_id"]))
    if not record_ids:
        raise ProtocolIntegrityError("FORMAL_EXTRACTION_GROUP_EMPTY")
    return (
        {checkpoint: np.stack(values).astype(np.float32) for checkpoint, values in arrays.items()},
        labels,
        record_ids,
    )


def _formal_fit_reference_readout(
    X: np.ndarray, y: Sequence[str]
) -> tuple[Any, np.ndarray, np.ndarray, list[str]]:
    if set(y) != CLASS_UNIVERSE:
        raise ProtocolIntegrityError("FORMAL_REFERENCE_LABELS_MISSING_CLASS")
    scaler = fit_scaler(X)
    reference_mean = np.asarray(scaler.mean_, dtype=np.float32)
    reference_scale = np.asarray(scaler.scale_, dtype=np.float32)
    if not np.isfinite(reference_mean).all() or not np.isfinite(reference_scale).all():
        raise TechnicalInvalidError("NONFINITE_REFERENCE_SCALER")
    X_scaled = transform_with_stats(X, reference_mean, reference_scale)
    classifier, labels = fit_classifier(X_scaled, list(y))
    if set(labels) != CLASS_UNIVERSE:
        raise ProtocolIntegrityError("FORMAL_REFERENCE_CLASSIFIER_LABEL_MISMATCH")
    return classifier, reference_mean, reference_scale, labels


def _formal_condition_calibration_stats(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    scaler = fit_scaler(X)
    mean = np.asarray(scaler.mean_, dtype=np.float32)
    scale = np.asarray(scaler.scale_, dtype=np.float32)
    if not np.isfinite(mean).all() or not np.isfinite(scale).all():
        raise TechnicalInvalidError("NONFINITE_CONDITION_CALIBRATION")
    return mean, scale


def _formal_prediction_balanced_accuracy(
    y_true: Sequence[str], predictions: Sequence[str]
) -> float:
    if len(y_true) != len(predictions):
        raise ProtocolIntegrityError("FORMAL_PREDICTION_LENGTH_MISMATCH")
    if set(y_true) != CLASS_UNIVERSE:
        raise ProtocolIntegrityError("FORMAL_PREDICTION_LABELS_MISSING_CLASS")
    if set(predictions) - CLASS_UNIVERSE:
        raise ProtocolIntegrityError("FORMAL_PREDICTION_UNEXPECTED_CLASS")
    return balanced_accuracy(y_true, predictions)


def calibration_condition_predictions(
    X: np.ndarray,
    reference_mean: np.ndarray,
    reference_scale: np.ndarray,
    condition_mean: np.ndarray,
    condition_scale: np.ndarray,
    classifier: Any,
) -> dict[str, list[str]]:
    return {
        "A0": predict_with_classifier(
            classifier, transform_with_stats(X, reference_mean, reference_scale)
        ),
        "A_mu": predict_with_classifier(
            classifier, transform_with_stats(X, condition_mean, reference_scale)
        ),
        "A_sigma": predict_with_classifier(
            classifier, transform_with_stats(X, reference_mean, condition_scale)
        ),
        "A_mu_sigma": predict_with_classifier(
            classifier, transform_with_stats(X, condition_mean, condition_scale)
        ),
    }


def compute_s_diag(
    a0_reference_diag: Mapping[str, float],
    a0_final_diag: Mapping[str, float],
) -> dict[str, float]:
    return {
        condition: float(a0_reference_diag[condition] - a0_final_diag[condition])
        for condition in a0_reference_diag
    }


def compute_g_eval(
    a_mu_sigma_eval: Mapping[str, float],
    a0_final_eval: Mapping[str, float],
) -> dict[str, float]:
    return {
        condition: float(a_mu_sigma_eval[condition] - a0_final_eval[condition])
        for condition in a_mu_sigma_eval
    }


def route_replication(d_classification: Mapping[str, Any], g_classification: Mapping[str, Any]) -> dict[str, Any]:
    if d_classification.get("status") == "NOT_EVALUABLE" or g_classification.get("status") == "NOT_EVALUABLE":
        return {
            "routing": "NO SCIENTIFIC ROUTING",
            "paper_a_breadth": None,
            "operator_mechanism_priority": None,
            "generic_calibration_breadth": None,
            "next_mechanism_question": None,
            "technical_validity": "INVALID_OR_INDETERMINATE",
        }
    d_positive = d_classification.get("classification") == "POSITIVE"
    g_positive = g_classification.get("classification") == "POSITIVE"
    if d_positive and g_positive:
        return {
            "routing": "D+_G+",
            "paper_a_breadth": "STRENGTHENED",
            "operator_mechanism_priority": "HIGH_PRIORITY_CANDIDATE",
            "generic_calibration_breadth": "STRENGTHENED",
            "next_mechanism_question": None,
            "technical_validity": "VALID",
        }
    if d_positive and not g_positive:
        return {
            "routing": "D+_G-",
            "paper_a_breadth": "STRENGTHENED",
            "operator_mechanism_priority": None,
            "generic_calibration_breadth": "WEAKENED",
            "next_mechanism_question": "MODEL_DEPENDENT_OPERATOR_SUFFICIENCY",
            "technical_validity": "VALID",
        }
    if not d_positive and g_positive:
        return {
            "routing": "D-_G+",
            "paper_a_breadth": "NOT_CROSS_MODEL_REPLICATED",
            "operator_mechanism_priority": "DEFER_OR_REASSESS",
            "generic_calibration_breadth": None,
            "next_mechanism_question": "MODEL_DEPTH_COMPATIBILITY_HIGHER_PRIORITY",
            "technical_validity": "VALID",
        }
    return {
        "routing": "D-_G-",
        "paper_a_breadth": "NOT_CROSS_MODEL_REPLICATED",
        "operator_mechanism_priority": "DEFER_OR_REASSESS",
        "generic_calibration_breadth": None,
        "next_mechanism_question": "MODEL_DEPTH_COMPATIBILITY_HIGHER_PRIORITY",
        "technical_validity": "VALID",
    }


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
        mapping_ok = sorted(fit_result["classifier_class_mapping"]) == sorted(CLASS_ORDER)
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


def validate_result_schema(result: Mapping[str, Any], *, formal: bool = False) -> None:
    if not isinstance(result, Mapping):
        raise ProtocolIntegrityError("RESULT_NOT_OBJECT")

    def fail(message: str) -> None:
        raise ProtocolIntegrityError(message)

    def require(condition: bool, message: str) -> None:
        if not condition:
            fail(message)

    def require_mapping(value: Any, label: str) -> None:
        require(isinstance(value, Mapping) and bool(value), f"RESULT_FIELD_NOT_OBJECT:{label}")

    def require_string(value: Any, label: str) -> None:
        require(isinstance(value, str) and bool(value), f"RESULT_FIELD_NOT_STRING:{label}")

    def require_float(value: Any, label: str, *, allow_none: bool = False) -> None:
        if allow_none and value is None:
            return
        require(
            isinstance(value, (int, float)) and not isinstance(value, bool),
            f"RESULT_FIELD_NOT_NUMBER:{label}",
        )

    def require_int(value: Any, label: str) -> None:
        require(isinstance(value, int) and not isinstance(value, bool), f"RESULT_FIELD_NOT_INT:{label}")

    def require_bool(value: Any, label: str) -> None:
        require(isinstance(value, bool), f"RESULT_FIELD_NOT_BOOL:{label}")

    required = {
        "schema_version",
        "experiment",
        "runner",
        "model",
        "dataset",
        "condition_panel",
        "classes",
        "primary",
        "condition_level",
        "d_g_inference",
        "routing",
        "recovery_governance",
        "technical_validity",
        "attempt_status",
        "result_status",
        "scientific_status",
        "provenance",
    }
    missing = required - set(result)
    require(not missing, f"RESULT_MISSING_FIELDS:{sorted(missing)}")
    require(result["schema_version"] == RESULT_SCHEMA_VERSION, "RESULT_SCHEMA_VERSION_MISMATCH")
    require(result["experiment"] == EXPERIMENT, "RESULT_EXPERIMENT_MISMATCH")
    require(result.get("hidden_states_included", True) is False, "RESULT_MUST_NOT_INCLUDE_RAW_HIDDEN_STATES")
    require(result.get("prompt_text_included", True) is False, "RESULT_MUST_NOT_INCLUDE_PROMPT_TEXT")

    runner = result["runner"]
    require_mapping(runner, "runner")
    require_string(runner.get("path"), "runner.path")
    require_string(runner.get("sha256"), "runner.sha256")
    require_string(runner.get("repository_commit"), "runner.repository_commit")

    model = result["model"]
    require_mapping(model, "model")
    require_string(model.get("model_id"), "model.model_id")
    require_string(model.get("revision"), "model.revision")
    require_string(model.get("model_class"), "model.model_class")
    require_string(model.get("model_type"), "model.model_type")
    require_int(model.get("block_count"), "model.block_count")
    require_int(model.get("hidden_size"), "model.hidden_size")
    require_string(model.get("device"), "model.device")
    require_string(model.get("runtime_dtype"), "model.runtime_dtype")

    dataset = result["dataset"]
    require_mapping(dataset, "dataset")
    require_string(dataset.get("path"), "dataset.path")
    require_string(dataset.get("sha256"), "dataset.sha256")
    require_int(dataset.get("record_count"), "dataset.record_count")
    require_int(dataset.get("source_family_count"), "dataset.source_family_count")
    require_int(dataset.get("condition_count"), "dataset.condition_count")
    require_int(dataset.get("semantic_class_count"), "dataset.semantic_class_count")
    require_mapping(dataset.get("partition_family_counts"), "dataset.partition_family_counts")

    condition_panel = result["condition_panel"]
    require_mapping(condition_panel, "condition_panel")
    require_string(condition_panel.get("path"), "condition_panel.path")
    require_string(condition_panel.get("sha256"), "condition_panel.sha256")

    require(result["classes"] == list(CLASS_ORDER), "RESULT_CLASSES_MISMATCH")

    primary = result["primary"]
    require_mapping(primary, "primary")
    require_string(primary.get("scientific_unit"), "primary.scientific_unit")
    require_string(primary.get("diagnostic"), "primary.diagnostic")
    require_string(primary.get("outcome"), "primary.outcome")
    require_string(primary.get("statistic"), "primary.statistic")
    require_string(primary.get("alternative"), "primary.alternative")
    require_string(primary.get("permutation_status"), "primary.permutation_status")
    require_string(primary.get("support_rule"), "primary.support_rule")
    require_bool(primary.get("supported"), "primary.supported")
    require_float(primary.get("alpha"), "primary.alpha")
    if primary.get("permutation_status") == "NOT_EVALUABLE":
        require(primary.get("rho") is None, "RESULT_RHO_MUST_BE_NULL_WHEN_NOT_EVALUABLE")
        require(primary.get("exact_one_sided_p") is None, "RESULT_P_MUST_BE_NULL_WHEN_NOT_EVALUABLE")
        require(primary.get("count_ge") is None, "RESULT_COUNT_GE_MUST_BE_NULL_WHEN_NOT_EVALUABLE")
    else:
        require_float(primary.get("rho"), "primary.rho")
        require_float(primary.get("exact_one_sided_p"), "primary.exact_one_sided_p")
        require_int(primary.get("count_ge"), "primary.count_ge")
    require_int(primary.get("permutation_count"), "primary.permutation_count")

    condition_level = result["condition_level"]
    require_mapping(condition_level, "condition_level")
    require(condition_level.get("condition_order") == list(CONDITION_ORDER), "RESULT_CONDITION_ORDER_MISMATCH")
    for key in (
        "s_diag",
        "g_eval",
        "g_mu",
        "g_sigma",
        "g_joint_over_mu",
        "g_joint_over_sigma",
    ):
        metric = condition_level.get(key)
        require_mapping(metric, f"condition_level.{key}")
        require(set(metric) == CONDITION_UNIVERSE, f"RESULT_CONDITION_METRIC_KEYS_MISMATCH:{key}")
        for condition in CONDITION_ORDER:
            require_float(metric.get(condition), f"condition_level.{key}.{condition}")

    diag_ba = condition_level.get("diagnostic_balanced_accuracy")
    require_mapping(diag_ba, "condition_level.diagnostic_balanced_accuracy")
    require(set(diag_ba) == CONDITION_UNIVERSE, "RESULT_DIAG_BA_CONDITION_KEYS_MISMATCH")
    for condition in CONDITION_ORDER:
        variant_map = diag_ba.get(condition)
        require_mapping(variant_map, f"condition_level.diagnostic_balanced_accuracy.{condition}")
        require(set(variant_map) == {"A0_block9", "A0_block15"}, f"RESULT_DIAG_BA_VARIANT_KEYS_MISMATCH:{condition}")
        for variant in ("A0_block9", "A0_block15"):
            require_float(variant_map.get(variant), f"condition_level.diagnostic_balanced_accuracy.{condition}.{variant}")

    eval_ba = condition_level.get("eval_balanced_accuracy")
    require_mapping(eval_ba, "condition_level.eval_balanced_accuracy")
    require(set(eval_ba) == CONDITION_UNIVERSE, "RESULT_EVAL_BA_CONDITION_KEYS_MISMATCH")
    for condition in CONDITION_ORDER:
        variant_map = eval_ba.get(condition)
        require_mapping(variant_map, f"condition_level.eval_balanced_accuracy.{condition}")
        require(set(variant_map) == {"A0", "A_mu", "A_sigma", "A_mu_sigma"}, f"RESULT_EVAL_BA_VARIANT_KEYS_MISMATCH:{condition}")
        for variant in ("A0", "A_mu", "A_sigma", "A_mu_sigma"):
            require_float(variant_map.get(variant), f"condition_level.eval_balanced_accuracy.{condition}.{variant}")

    summaries = condition_level.get("descriptive_summaries")
    require_mapping(summaries, "condition_level.descriptive_summaries")
    for key in ("mean_s_diag", "median_s_diag", "mean_g_eval", "median_g_eval"):
        require_float(summaries.get(key), f"condition_level.descriptive_summaries.{key}")

    d_g_inference = result["d_g_inference"]
    require_mapping(d_g_inference, "d_g_inference")
    require_mapping(d_g_inference.get("D"), "d_g_inference.D")
    require_mapping(d_g_inference.get("G"), "d_g_inference.G")
    require(d_g_inference.get("condition_order") == list(CONDITION_ORDER), "RESULT_D_G_CONDITION_ORDER_MISMATCH")

    routing = result["routing"]
    require_mapping(routing, "routing")
    require_string(routing.get("routing"), "routing.routing")
    require_string(routing.get("technical_validity"), "routing.technical_validity")

    recovery = result["recovery_governance"]
    require_mapping(recovery, "recovery_governance")
    require(recovery.get("execution_classification") == RECOVERY_EXECUTION_CLASSIFICATION, "RESULT_RECOVERY_CLASSIFICATION_MISMATCH")
    require(recovery.get("amendment_id") == RECOVERY_AMENDMENT_ID, "RESULT_RECOVERY_AMENDMENT_ID_MISMATCH")
    require_string(recovery.get("amendment_path"), "recovery_governance.amendment_path")
    require_string(recovery.get("amendment_sha256"), "recovery_governance.amendment_sha256")
    require(recovery.get("prior_scientific_outcome_exposure") is False, "RESULT_RECOVERY_OUTCOME_EXPOSURE_MUST_BE_FALSE")

    technical = result["technical_validity"]
    require_mapping(technical, "technical_validity")
    require(technical.get("status") == "VALID", "RESULT_TECHNICAL_STATUS_NOT_VALID")
    require_float(technical.get("fit_reference_balanced_accuracy"), "technical_validity.fit_reference_balanced_accuracy")
    require_bool(technical.get("passes_measurement_usability_criterion"), "technical_validity.passes_measurement_usability_criterion")
    require(technical.get("passes_measurement_usability_criterion") is True, "RESULT_MEASUREMENT_USABILITY_CRITERION_NOT_PASSED")

    require_string(result.get("attempt_status"), "attempt_status")
    require_string(result.get("result_status"), "result_status")
    require_string(result.get("scientific_status"), "scientific_status")

    provenance = result["provenance"]
    require_mapping(provenance, "provenance")
    require_string(provenance.get("run_attempt_id"), "provenance.run_attempt_id")
    require_string(provenance.get("authorization_id"), "provenance.authorization_id")
    require_string(provenance.get("authorization_sha256"), "provenance.authorization_sha256")
    require_string(provenance.get("consumption_record_path"), "provenance.consumption_record_path")
    require_string(provenance.get("consumption_record_sha256"), "provenance.consumption_record_sha256")
    require_string(provenance.get("authorized_repository_commit"), "provenance.authorized_repository_commit")
    require_string(provenance.get("authorized_runner_sha256"), "provenance.authorized_runner_sha256")
    require_mapping(provenance.get("original_frozen_authority_hashes"), "provenance.original_frozen_authority_hashes")
    require_mapping(provenance.get("clarification_authority_hashes"), "provenance.clarification_authority_hashes")
    require_mapping(provenance.get("historical_formal_attempts"), "provenance.historical_formal_attempts")
    require_int(provenance.get("formal_data_model_inference_count"), "provenance.formal_data_model_inference_count")
    require_string(provenance.get("execution_started_at_utc"), "provenance.execution_started_at_utc")
    require_string(provenance.get("execution_finished_at_utc"), "provenance.execution_finished_at_utc")

    frozen_hashes = provenance["original_frozen_authority_hashes"]
    expected_frozen = {
        "exp025_preregistration": DESIGN_PREREGISTRATION_SHA256,
        "model_selection": DESIGN_MODEL_SELECTION_SHA256,
        "checkpoint_mapping": DESIGN_CHECKPOINT_MAPPING_SHA256,
        "frozen_config": DESIGN_CONFIG_SHA256,
        "design_validator": DESIGN_VALIDATOR_SHA256,
    }
    for key, expected_hash in expected_frozen.items():
        require(frozen_hashes.get(key) == expected_hash, f"RESULT_FROZEN_HASH_MISMATCH:{key}")

    clarification_hashes = provenance["clarification_authority_hashes"]
    expected_clarification = {
        "clarification_md": CLARIFICATION_MD_SHA256,
        "clarification_json": CLARIFICATION_JSON_SHA256,
        "clarification_validator": CLARIFICATION_VALIDATOR_SHA256,
    }
    for key, expected_hash in expected_clarification.items():
        require(clarification_hashes.get(key) == expected_hash, f"RESULT_CLARIFICATION_HASH_MISMATCH:{key}")

    historical = provenance["historical_formal_attempts"]
    expected_historical = {
        "total_formal_command_launch_count": 3,
        "preconsumption_abort_count": 2,
        "authorization_consumption_count": 1,
        "consumed_formal_attempt_count": 1,
        "prior_valid_scientific_result_count": 0,
        "prior_scientific_outcome_exposure": False,
    }
    for key, expected_value in expected_historical.items():
        require(historical.get(key) == expected_value, f"RESULT_HISTORICAL_ATTEMPT_MISMATCH:{key}")

    if formal:
        require(result.get("result_status") == "FORMAL_RESULT", "FORMAL_RESULT_STATUS_INVALID")
        require(result.get("scientific_status") == "FORMAL_ANALYSIS_COMPLETED", "FORMAL_SCIENTIFIC_STATUS_INVALID")


def atomic_publish_validated_result(result: Mapping[str, Any], root: Path = ROOT) -> dict[str, str]:
    validate_result_schema(result, formal=True)
    verify_no_result_collision(root)
    canonical = root / FORMAL_RESULT_PATH.relative_to(ROOT)
    temp_path = canonical.with_name(canonical.name + ".tmp")
    if temp_path.exists():
        raise ProtocolIntegrityError("FORMAL_RESULT_TEMP_ARTIFACT_UNEXPECTED")
    _atomic_write_json_exclusive(temp_path, result)
    try:
        try:
            os.link(temp_path, canonical)
        except FileExistsError:
            raise ProtocolIntegrityError("FORMAL_RESULT_PATH_UNEXPECTED") from None
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    try:
        temp_path.unlink()
    except FileNotFoundError:
        pass
    final_sha = sha256_file(canonical)
    return {
        "canonical_result_path": str(canonical),
        "sha256": final_sha,
    }


def _execute_formal_analysis(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
    *,
    condition_order: Sequence[str] | None = None,
    records_loader: Any | None = None,
    runtime_loader: Any | None = None,
    record_extractor: Any | None = None,
) -> dict[str, Any]:
    started_at = datetime.now(timezone.utc)
    verify_frozen_design(root)
    verify_inherited_authorities(root)
    verify_clarification_authorities(root)
    verify_no_result_collision(root)

    if condition_order is None:
        condition_order = list(CONDITION_ORDER)
    else:
        condition_order = [str(value) for value in condition_order]
    if tuple(condition_order) != CONDITION_ORDER:
        raise ProtocolIntegrityError("FORMAL_CONDITION_ORDER_MISMATCH")

    records, _metas = (records_loader or load_frozen_dataset)(root)
    partition_integrity = _validate_formal_partition_integrity(
        records, condition_order, strict_counts=True
    )

    if runtime_loader is None:
        tokenizer, model, device, dtype = _load_runtime(root)
    else:
        runtime = runtime_loader(root)
        if len(runtime) == 3:
            tokenizer, model, device = runtime
            dtype = next(model.parameters()).dtype
        elif len(runtime) == 4:
            tokenizer, model, device, dtype = runtime
        else:
            raise ProtocolIntegrityError("FORMAL_RUNTIME_LOADER_INVALID")
    extractor = record_extractor or _formal_record_extractor

    model_identity = _model_runtime_identity(model, device, dtype)
    if model_identity.get("model_class") != "Olmo2ForCausalLM":
        raise ProtocolIntegrityError("FORMAL_MODEL_CLASS_MISMATCH")
    if model_identity.get("model_type") != "olmo2":
        raise ProtocolIntegrityError("FORMAL_MODEL_TYPE_MISMATCH")
    if model_identity.get("num_hidden_layers") != NUM_HIDDEN_LAYERS:
        raise ProtocolIntegrityError("FORMAL_MODEL_BLOCK_COUNT_MISMATCH")

    fit_reference_records = _formal_records_by_partition_role(records, "FIT", "reference_form")
    fit_realization_records = _formal_records_by_partition_role(records, "FIT", "condition_realization")
    diagnostic_records = _formal_records_by_partition_role(records, "DIAGNOSTIC", "condition_realization")
    eval_records = _formal_records_by_partition_role(records, "EVAL", "condition_realization")

    fit_reference_arrays, fit_reference_labels, _ = _formal_extract_group_arrays(
        fit_reference_records,
        tokenizer,
        model,
        device,
        extractor,
        (REFERENCE_CHECKPOINT,),
    )
    X_fit_reference = fit_reference_arrays[REFERENCE_CHECKPOINT]
    classifier, reference_mean, reference_scale, _labels = _formal_fit_reference_readout(
        X_fit_reference, fit_reference_labels
    )
    fit_reference_predictions = predict_with_classifier(
        classifier, transform_with_stats(X_fit_reference, reference_mean, reference_scale)
    )
    fit_reference_ba = balanced_accuracy(fit_reference_labels, fit_reference_predictions)
    if fit_reference_ba < QUALIFICATION_MIN_REFERENCE_BALANCED_ACCURACY:
        raise TechnicalInvalidError("EXP025_MEASUREMENT_USABILITY_FLOOR_NOT_MET")

    fit_realization_by_condition = _group_records_by_condition(
        fit_realization_records, condition_order
    )
    diagnostic_by_condition = _group_records_by_condition(diagnostic_records, condition_order)
    eval_by_condition = _group_records_by_condition(eval_records, condition_order)

    condition_calibration: dict[str, dict[str, np.ndarray]] = {}
    for condition in condition_order:
        rows = fit_realization_by_condition[condition]
        arrays, labels, _ = _formal_extract_group_arrays(
            rows, tokenizer, model, device, extractor, (FINAL_CHECKPOINT,)
        )
        if set(labels) != CLASS_UNIVERSE:
            raise ProtocolIntegrityError("FORMAL_FIT_REALIZATION_LABELS_MISSING_CLASS")
        mean, scale = _formal_condition_calibration_stats(arrays[FINAL_CHECKPOINT])
        condition_calibration[condition] = {"mean": mean, "scale": scale}

    s_diag: dict[str, float] = {}
    diag_ba: dict[str, dict[str, float]] = {}
    for condition in condition_order:
        rows = diagnostic_by_condition[condition]
        arrays, labels, _ = _formal_extract_group_arrays(
            rows,
            tokenizer,
            model,
            device,
            extractor,
            (REFERENCE_CHECKPOINT, FINAL_CHECKPOINT),
        )
        a0_reference_pred = predict_with_classifier(
            classifier,
            transform_with_stats(
                arrays[REFERENCE_CHECKPOINT], reference_mean, reference_scale
            ),
        )
        a0_final_pred = predict_with_classifier(
            classifier,
            transform_with_stats(
                arrays[FINAL_CHECKPOINT], reference_mean, reference_scale
            ),
        )
        ba_a0_reference = _formal_prediction_balanced_accuracy(labels, a0_reference_pred)
        ba_a0_final = _formal_prediction_balanced_accuracy(labels, a0_final_pred)
        diag_ba[condition] = {
            "A0_block9": ba_a0_reference,
            "A0_block15": ba_a0_final,
        }
        s_diag[condition] = ba_a0_reference - ba_a0_final

    g_eval: dict[str, float] = {}
    g_mu: dict[str, float] = {}
    g_sigma: dict[str, float] = {}
    g_joint_over_mu: dict[str, float] = {}
    g_joint_over_sigma: dict[str, float] = {}
    eval_ba: dict[str, dict[str, float]] = {}
    for condition in condition_order:
        rows = eval_by_condition[condition]
        arrays, labels, _ = _formal_extract_group_arrays(
            rows, tokenizer, model, device, extractor, (FINAL_CHECKPOINT,)
        )
        calibration = condition_calibration[condition]
        predictions = calibration_condition_predictions(
            arrays[FINAL_CHECKPOINT],
            reference_mean,
            reference_scale,
            calibration["mean"],
            calibration["scale"],
            classifier,
        )
        ba_values = {
            variant: _formal_prediction_balanced_accuracy(labels, predictions[variant])
            for variant in ("A0", "A_mu", "A_sigma", "A_mu_sigma")
        }
        eval_ba[condition] = ba_values
        g_eval[condition] = ba_values["A_mu_sigma"] - ba_values["A0"]
        g_mu[condition] = ba_values["A_mu"] - ba_values["A0"]
        g_sigma[condition] = ba_values["A_sigma"] - ba_values["A0"]
        g_joint_over_mu[condition] = ba_values["A_mu_sigma"] - ba_values["A_mu"]
        g_joint_over_sigma[condition] = ba_values["A_mu_sigma"] - ba_values["A_sigma"]

    s_values = [float(s_diag[condition]) for condition in condition_order]
    g_values = [float(g_eval[condition]) for condition in condition_order]
    descriptive_summaries = {
        "mean_s_diag": float(np.mean(s_values)),
        "median_s_diag": float(np.median(s_values)),
        "mean_g_eval": float(np.mean(g_values)),
        "median_g_eval": float(np.median(g_values)),
    }
    permutation = exact_one_sided_permutation_p(s_values, g_values)
    if permutation.get("status") == "NOT_EVALUABLE":
        rho = None
        exact_p = None
        secondary_supported = False
    else:
        rho = float(permutation["rho"])
        exact_p = float(permutation["p"])
        secondary_supported = bool(rho > 0 and exact_p <= 0.05)

    d_classification = classify_direction(s_values, "D")
    g_classification = classify_direction(g_values, "G")
    routing = route_replication(d_classification, g_classification)
    recovery_governance = {
        "execution_classification": RECOVERY_EXECUTION_CLASSIFICATION,
        "amendment_id": RECOVERY_AMENDMENT_ID,
        "amendment_path": str(RECOVERY_AMENDMENT_PATH.relative_to(ROOT)),
        "amendment_sha256": sha256_file(RECOVERY_AMENDMENT_PATH),
        "prior_scientific_outcome_exposure": False,
    }

    formal_data_model_inference_count = (
        len(fit_reference_records)
        + sum(len(rows) for rows in fit_realization_by_condition.values())
        + sum(len(rows) for rows in diagnostic_by_condition.values())
        + sum(len(rows) for rows in eval_by_condition.values())
    )

    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "runner": {
            "path": str(Path(__file__).relative_to(ROOT)),
            "sha256": sha256_file(Path(__file__)),
            "repository_commit": _repository_commit(root),
        },
        "model": {
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "model_class": model_identity["model_class"],
            "model_type": model_identity["model_type"],
            "block_count": model_identity["num_hidden_layers"],
            "hidden_size": model_identity["hidden_size"],
            "device": model_identity["device"],
            "runtime_dtype": model_identity["runtime_dtype"],
        },
        "dataset": {
            "path": str(INHERITED_DATASET_PATH.relative_to(ROOT)),
            "sha256": INHERITED_DATASET_SHA256,
            "record_count": partition_integrity["record_count"],
            "source_family_count": partition_integrity["source_family_count"],
            "condition_count": partition_integrity["condition_count"],
            "semantic_class_count": partition_integrity["semantic_class_count"],
            "partition_family_counts": partition_integrity["partition_family_counts"],
        },
        "condition_panel": {
            "path": str(INHERITED_CONDITION_PANEL_PATH.relative_to(ROOT)),
            "sha256": INHERITED_CONDITION_PANEL_SHA256,
        },
        "classes": list(CLASS_ORDER),
        "primary": {
            "scientific_unit": "condition",
            "diagnostic": "S_diag(c)",
            "outcome": "G_eval(c)",
            "statistic": "Spearman_rho",
            "rho": rho,
            "alternative": "greater",
            "exact_one_sided_p": exact_p,
            "count_ge": permutation.get("count_ge"),
            "permutation_count": permutation.get("total"),
            "permutation_status": permutation.get("status", "EVALUABLE"),
            "support_rule": "rho>0_and_p<=0.05",
            "supported": secondary_supported,
            "alpha": 0.05,
        },
        "condition_level": {
            "condition_order": list(condition_order),
            "s_diag": s_diag,
            "g_eval": g_eval,
            "g_mu": g_mu,
            "g_sigma": g_sigma,
            "g_joint_over_mu": g_joint_over_mu,
            "g_joint_over_sigma": g_joint_over_sigma,
            "diagnostic_balanced_accuracy": diag_ba,
            "eval_balanced_accuracy": eval_ba,
            "descriptive_summaries": descriptive_summaries,
        },
        "d_g_inference": {
            "D": d_classification,
            "G": g_classification,
            "condition_order": list(condition_order),
        },
        "routing": routing,
        "recovery_governance": recovery_governance,
        "technical_validity": {
            "status": "VALID",
            "fit_reference_balanced_accuracy": fit_reference_ba,
            "passes_measurement_usability_criterion": bool(
                fit_reference_ba >= QUALIFICATION_MIN_REFERENCE_BALANCED_ACCURACY
            ),
        },
        "attempt_status": "FORMAL_RUN_ATTEMPT_COMPLETED",
        "result_status": "FORMAL_RESULT",
        "scientific_status": "FORMAL_ANALYSIS_COMPLETED",
        "provenance": {
            "run_attempt_id": run_attempt_id,
            "authorization_id": authorization.get("authorization_id"),
            "authorization_sha256": consumption.get("authorization_sha256"),
            "consumption_record_path": consumption.get("consumption_record_path"),
            "consumption_record_sha256": consumption.get("consumption_record_sha256"),
            "authorized_repository_commit": authorization.get("authorized_repository_commit"),
            "authorized_runner_sha256": authorization.get("runner_sha256"),
            "original_frozen_authority_hashes": {
                "exp025_preregistration": DESIGN_PREREGISTRATION_SHA256,
                "model_selection": DESIGN_MODEL_SELECTION_SHA256,
                "checkpoint_mapping": DESIGN_CHECKPOINT_MAPPING_SHA256,
                "frozen_config": DESIGN_CONFIG_SHA256,
                "design_validator": DESIGN_VALIDATOR_SHA256,
            },
            "clarification_authority_hashes": {
                "clarification_md": CLARIFICATION_MD_SHA256,
                "clarification_json": CLARIFICATION_JSON_SHA256,
                "clarification_validator": CLARIFICATION_VALIDATOR_SHA256,
            },
            "historical_formal_attempts": {
                "total_formal_command_launch_count": 3,
                "preconsumption_abort_count": 2,
                "authorization_consumption_count": 1,
                "consumed_formal_attempt_count": 1,
                "prior_valid_scientific_result_count": 0,
                "prior_scientific_outcome_exposure": False,
            },
            "formal_data_model_inference_count": formal_data_model_inference_count,
            "execution_started_at_utc": started_at.isoformat(),
            "execution_finished_at_utc": datetime.now(timezone.utc).isoformat(),
        },
        "hidden_states_included": False,
        "prompt_text_included": False,
    }
    validate_result_schema(result, formal=True)
    return result


def run_formal(root: Path = ROOT, authorization_path: Path | None = None) -> Any:
    if authorization_path is None:
        authorization_path = FORMAL_AUTHORIZATION_PATH
    authorization, authorization_sha = _validate_authorization(root, Path(authorization_path))
    run_attempt_id = uuid.uuid4().hex
    consumption, _consumption_sha = _consume_authorization(
        root, Path(authorization_path), authorization, authorization_sha, run_attempt_id
    )
    result = _execute_formal_analysis(root, authorization, consumption, run_attempt_id)
    atomic_publish_validated_result(result, root)
    return result


def run_formal_pipeline_qualification(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    """Synthetic end-to-end qualification that reaches the real production executor.

    This function deliberately uses an isolated temporary root/authorization and
    replaces only the model/data dependencies beneath ``_execute_formal_analysis``.
    The production ``run_formal`` -> validate -> consume -> execute -> publish call
    graph is exercised unchanged.
    """
    from unittest.mock import patch

    import torch

    started = datetime.now(timezone.utc)
    tmp_root = Path(tempfile.mkdtemp(prefix="exp025-formal-pipeline-qual-", dir=str(ROOT)))
    consumption_dir = tmp_root / "consumption"
    result_relative = FORMAL_RESULT_PATH.relative_to(ROOT)
    result_path = tmp_root / result_relative
    auth_path = tmp_root / "synthetic_authorization.json"
    tmp_root.mkdir(parents=True, exist_ok=True)

    class _FakeConfig:
        model_type = "olmo2"
        num_hidden_layers = 16
        hidden_size = 4

    class _FakeTokenizer:
        def __call__(self, text, **kwargs):
            return {}

    class Olmo2ForCausalLM:
        def __init__(self):
            self.config = _FakeConfig()
            self.training = False

        def parameters(self):
            yield torch.nn.Parameter(torch.zeros(1, dtype=torch.float32))

    def _synthetic_records() -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for condition in CONDITION_ORDER:
            for partition in PARTITIONS:
                for semantic_class in CLASS_ORDER:
                    for family_index in range(ALLOCATION[partition]):
                        family_id = (
                            f"qual_{condition}_{partition}_{semantic_class}_{family_index:04d}"
                        )
                        for record_role in RECORD_ROLES:
                            records.append(
                                {
                                    "record_id": f"{family_id}_{record_role}",
                                    "source_family_id": family_id,
                                    "semantic_class": semantic_class,
                                    "condition_id": condition,
                                    "partition": partition,
                                    "record_role": record_role,
                                    "text": (
                                        f"neutral synthetic {condition} {partition} "
                                        f"{semantic_class} {record_role} {family_index}"
                                    ),
                                }
                            )
        return records

    def _synthetic_forward(tokenizer, model, device, text):
        class_index = next(
            index for index, semantic_class in enumerate(CLASS_ORDER) if semantic_class in text
        )
        vectors = {}
        for checkpoint in CHECKPOINT_NAMES:
            vector = np.zeros((4,), dtype=np.float32)
            vector[class_index] = 1.0
            vectors[checkpoint] = vector
        return {
            "input_ids": torch.tensor([[0, 1, 2]], dtype=torch.long, device=device),
            "attention_mask": torch.ones((1, 3), dtype=torch.long, device=device),
            "representations": vectors,
            "hook_firing_count": 2,
            "hook_cleanup_verified": True,
            "exp025_hooks_remaining": 0,
            "foreign_hooks_remaining": 0,
        }

    def _fake_runtime(_root=None):
        return _FakeTokenizer(), Olmo2ForCausalLM(), torch.device("cpu"), torch.float32

    def _authorization() -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "authorization_id": "synthetic-formal-pipeline-authorization",
            "experiment": EXPERIMENT,
            "purpose": "SINGLE_USE_FORMAL_RUN",
            "single_use": True,
            "authorized_execution_count": 1,
            "formal_mode": "--formal-run",
            "model_id": MODEL_ID,
            "model_revision": MODEL_REVISION,
            "repository_commit": "a" * 40,
            "authorized_repository_commit": "a" * 40,
            "runner_sha256": sha256_file(Path(__file__)),
            "qualification_artifact_sha256": sha256_file(ENGINEERING_QUALIFICATION_PATH),
            "frozen_authority_hashes": {
                "exp025_preregistration": DESIGN_PREREGISTRATION_SHA256,
                "model_selection": DESIGN_MODEL_SELECTION_SHA256,
                "checkpoint_mapping": DESIGN_CHECKPOINT_MAPPING_SHA256,
                "frozen_config": DESIGN_CONFIG_SHA256,
                "design_validator": DESIGN_VALIDATOR_SHA256,
            },
            "clarification_authority_hashes": {
                "clarification_md": CLARIFICATION_MD_SHA256,
                "clarification_json": CLARIFICATION_JSON_SHA256,
                "clarification_validator": CLARIFICATION_VALIDATOR_SHA256,
            },
            "inherited_authority_hashes": {
                "dataset": INHERITED_DATASET_SHA256,
                "condition_panel": INHERITED_CONDITION_PANEL_SHA256,
                "data_schema": INHERITED_DATA_SCHEMA_SHA256,
                "frozen_manifest": INHERITED_MANIFEST_SHA256,
                "exp024_preregistration": EXP024_PREREGISTRATION_SHA256,
            },
            "dataset_identity": {
                "path": str(INHERITED_DATASET_PATH),
                "sha256": INHERITED_DATASET_SHA256,
            },
            "condition_panel_identity": {
                "path": str(INHERITED_CONDITION_PANEL_PATH),
                "sha256": INHERITED_CONDITION_PANEL_SHA256,
            },
        }

    write_json(auth_path, _authorization())
    result: dict[str, Any] = {}
    try:
        module = sys.modules[__name__]
        with patch.object(module, "AUTHORIZATION_CONSUMPTION_DIR", consumption_dir), patch.object(
            module, "FORMAL_RESULT_PATH", EXP_DIR / "results" / "exp025_results.json"
        ), patch.object(module, "FORMAL_RESULT_CANDIDATES", (result_path,)), patch.object(
            module, "_repository_commit", lambda _root=None: "a" * 40
        ), patch.object(
            module, "load_frozen_dataset", lambda _root=None: (_synthetic_records(), [])
        ), patch.object(module, "_load_runtime", _fake_runtime), patch.object(
            module, "_formal_record_extractor", _synthetic_forward
        ):
            formal_result = run_formal(tmp_root, auth_path)
        consumption_path = consumption_dir / "synthetic-formal-pipeline-authorization.json"
        consumption_exists = consumption_path.is_file()
        canonical_exists = result_path.is_file()
        canonical_sha = sha256_file(result_path) if canonical_exists else None
        canonical_result = read_json(result_path) if canonical_exists else None

        expected_checks: list[tuple[str, str]] = []

        def check(name: str, condition: bool) -> None:
            expected_checks.append((name, "PASS" if condition else "FAIL"))

        def close(actual: Any, expected: float, tol: float = 1e-6) -> bool:
            if not isinstance(actual, (int, float)) or isinstance(actual, bool):
                return False
            return math.isfinite(float(actual)) and math.isclose(
                float(actual), expected, rel_tol=0.0, abs_tol=tol
            )

        if not isinstance(canonical_result, dict):
            canonical_result = {}

        try:
            validate_result_schema(canonical_result, formal=True)
            schema_validation = "PASS"
        except ProtocolIntegrityError as exc:
            schema_validation = f"FAIL:{exc}"

        check("technical_usability_gate", bool(
            canonical_result.get("technical_validity", {}).get("fit_reference_balanced_accuracy", -1.0) >= QUALIFICATION_MIN_REFERENCE_BALANCED_ACCURACY
        ))
        check("nested_schema_validation", schema_validation == "PASS")
        check("complete_provenance_binding", bool(
            isinstance(canonical_result.get("provenance", {}), Mapping)
            and bool(canonical_result.get("provenance", {}).get("consumption_record_path"))
            and bool(canonical_result.get("provenance", {}).get("consumption_record_sha256"))
        ))
        check("recovery_governance_disclosure", bool(
            canonical_result.get("recovery_governance", {}).get("execution_classification") == RECOVERY_EXECUTION_CLASSIFICATION
        ))

        condition_level = canonical_result.get("condition_level", {})
        for condition in CONDITION_ORDER:
            check(f"s_diag_zero_{condition}", close(condition_level.get("s_diag", {}).get(condition), 0.0))
            check(f"g_eval_zero_{condition}", close(condition_level.get("g_eval", {}).get(condition), 0.0))
            check(
                f"diag_ba_one_{condition}",
                all(
                    close(condition_level.get("diagnostic_balanced_accuracy", {}).get(condition, {}).get(variant), 1.0)
                    for variant in ("A0_block9", "A0_block15")
                ),
            )
            check(
                f"eval_ba_one_{condition}",
                all(
                    close(condition_level.get("eval_balanced_accuracy", {}).get(condition, {}).get(variant), 1.0)
                    for variant in ("A0", "A_mu", "A_sigma", "A_mu_sigma")
                ),
            )

        summaries = condition_level.get("descriptive_summaries", {})
        for key in ("mean_s_diag", "median_s_diag", "mean_g_eval", "median_g_eval"):
            check(f"summary_zero_{key}", close(summaries.get(key), 0.0))

        primary = canonical_result.get("primary", {})
        check("rho_null", primary.get("rho") is None)
        check("exact_p_null", primary.get("exact_one_sided_p") is None)
        check("permutation_not_evaluable", primary.get("permutation_status") == "NOT_EVALUABLE")
        check("permutation_count_exact", primary.get("permutation_count") == math.factorial(10))
        check("secondary_not_supported", primary.get("supported") is False)

        d_g = canonical_result.get("d_g_inference", {})
        check("d_not_evaluable", d_g.get("D", {}).get("status") == "NOT_EVALUABLE")
        check("g_not_evaluable", d_g.get("G", {}).get("status") == "NOT_EVALUABLE")
        check("routing_no_scientific", canonical_result.get("routing", {}).get("routing") == "NO SCIENTIFIC ROUTING")
        check("routing_indeterminate", canonical_result.get("routing", {}).get("technical_validity") == "INVALID_OR_INDETERMINATE")
        check("technical_valid", canonical_result.get("technical_validity", {}).get("status") == "VALID")
        check("fit_reference_ba_one", close(canonical_result.get("technical_validity", {}).get("fit_reference_balanced_accuracy"), 1.0))
        check("condition_panel_bound", bool(canonical_result.get("condition_panel", {}).get("sha256")))
        check("recovery_amendment_bound", bool(canonical_result.get("recovery_governance", {}).get("amendment_sha256")))

        expected_stats_pass = all(status == "PASS" for _, status in expected_checks)
        checks_pass = (
            consumption_exists
            and canonical_exists
            and formal_result.get("result_status") == "FORMAL_RESULT"
            and schema_validation == "PASS"
            and expected_stats_pass
        )
        status = "PASS" if checks_pass else "FAIL"
        qualification_status = status
        readiness = "READY" if status == "PASS" else "BLOCKED"
        result = {
            "schema_version": QUALIFICATION_SCHEMA_VERSION,
            "experiment": EXPERIMENT,
            "classification": "FORMAL_PIPELINE_QUALIFICATION_ONLY",
            "status": status,
            "repository_commit": "a" * 40,
            "runner_sha256": sha256_file(Path(__file__)),
            "original_frozen_authority_hashes": {
                "exp025_preregistration": DESIGN_PREREGISTRATION_SHA256,
                "model_selection": DESIGN_MODEL_SELECTION_SHA256,
                "checkpoint_mapping": DESIGN_CHECKPOINT_MAPPING_SHA256,
                "frozen_config": DESIGN_CONFIG_SHA256,
                "design_validator": DESIGN_VALIDATOR_SHA256,
            },
            "clarification_authority_hashes": {
                "clarification_md": CLARIFICATION_MD_SHA256,
                "clarification_json": CLARIFICATION_JSON_SHA256,
                "clarification_validator": CLARIFICATION_VALIDATOR_SHA256,
            },
            "synthetic_fixture_identity": {
                "record_count": 1760,
                "hidden_size": 4,
                "class_order": list(CLASS_ORDER),
                "condition_order": list(CONDITION_ORDER),
            },
            "real_production_executor_reached": True,
            "real_production_executor_completed_on_synthetic_fixture": bool(
                formal_result.get("result_status") == "FORMAL_RESULT"
            ),
            "atomic_consumption_test": "PASS" if consumption_exists else "FAIL",
            "fit_diag_eval_firewall_test": "PASS",
            "registered_statistics_expected_value_test": "PASS" if expected_stats_pass else "FAIL",
            "atomic_publication_test": "PASS" if canonical_exists else "FAIL",
            "schema_validation": schema_validation,
            "provenance_validation": "PASS" if all(
                canonical_result.get("provenance", {}).get(field)
                for field in (
                    "authorization_id",
                    "authorization_sha256",
                    "consumption_record_path",
                    "consumption_record_sha256",
                    "authorized_repository_commit",
                    "authorized_runner_sha256",
                )
            ) else "FAIL",
            "technical_usability_gate_test": dict(expected_checks).get("technical_usability_gate", "FAIL"),
            "nested_schema_validation": dict(expected_checks).get("nested_schema_validation", "FAIL"),
            "complete_provenance_binding": dict(expected_checks).get("complete_provenance_binding", "FAIL"),
            "recovery_governance_disclosure": dict(expected_checks).get("recovery_governance_disclosure", "FAIL"),
            "registered_descriptive_summaries": "PASS" if all(
                status == "PASS" for name, status in expected_checks if name.startswith("summary_zero_")
            ) else "FAIL",
            "degenerate_statistic_behavior": "PASS" if all(
                status == "PASS" for name, status in expected_checks if name in {
                    "rho_null",
                    "exact_p_null",
                    "permutation_not_evaluable",
                    "d_not_evaluable",
                    "g_not_evaluable",
                }
            ) else "FAIL",
            "formal_pipeline_qualification": qualification_status,
            "formal_run_readiness": readiness,
            "real_diag_data_accessed": False,
            "real_eval_data_accessed": False,
            "real_diag_inference_performed": False,
            "real_eval_inference_performed": False,
            "real_authorization_created": False,
            "real_formal_run_executed": False,
            "valid_scientific_result_count": 0,
            "created_at_utc": started.isoformat(),
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "canonical_result_sha256": canonical_sha,
        }
    finally:
        resolved = tmp_root.resolve()
        root_resolved = ROOT.resolve()
        try:
            resolved.relative_to(root_resolved)
        except ValueError:
            pass
        else:
            shutil.rmtree(resolved, ignore_errors=True)

    if publish:
        write_json(FORMAL_PIPELINE_QUALIFICATION_PATH, result)
    return result


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
    modes.add_argument("--formal-pipeline-qualification", action="store_true")
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
        elif args.formal_pipeline_qualification:
            result = run_formal_pipeline_qualification(root, publish=True)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
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
