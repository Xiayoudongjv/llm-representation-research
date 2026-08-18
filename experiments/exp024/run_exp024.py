#!/usr/bin/env python3
"""EXP-024 frozen-protocol runner and static preflight.

This module implements the frozen EXP-024 production surface. Importing it does
not load a model, tokenizer, formal dataset for inference, or compute a
scientific outcome. Static preflight is the only mode authorized in Task 098A.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


EXPERIMENT = "EXP-024"
RESULT_SCHEMA_VERSION = "1.0.0"

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent

FROZEN_MANIFEST_PATH = EXP_DIR / "exp024_frozen_manifest.json"
FROZEN_MANIFEST_SHA256 = (
    "1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59"
)
FROZEN_DATASET_PATH = EXP_DIR / "data" / "exp024_condition_panel_frozen.json"
FROZEN_DATASET_SHA256 = (
    "46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404"
)
FINAL_PREREGISTRATION_PATH = ROOT / "docs" / "experiments" / "EXP-024-PREREGISTRATION.md"
FINAL_PREREGISTRATION_SHA256 = (
    "55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810"
)
CONDITION_PANEL_PATH = EXP_DIR / "condition_panel_spec.json"
CONDITION_PANEL_SHA256 = (
    "a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954"
)
DATA_SCHEMA_PATH = EXP_DIR / "data_schema.json"
DATA_SCHEMA_SHA256 = (
    "e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec"
)

CANONICAL_RESULT_PATH = EXP_DIR / "results" / "exp024_results.json"
PREFLIGHT_PATH = EXP_DIR / "results" / "runner_preflight.json"
RESULT_SCHEMA_PATH = EXP_DIR / "exp024_result_schema.json"
AUTHORIZATION_SCHEMA_PATH = EXP_DIR / "exp024_formal_run_authorization.schema.json"
AUTHORIZATION_CONSUMPTION_DIR = EXP_DIR / "results" / "authorization_consumption"
TECHNICAL_FAILURE_EVIDENCE_DIR = EXP_DIR / "results" / "technical_failure_evidence"
MODEL_HOOK_QUALIFICATION_PATH = EXP_DIR / "engineering" / "model_hook_qualification.json"

FORMAL_MODEL_NAME = "Qwen/Qwen3-1.7B"
FORMAL_MODEL_SNAPSHOT = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
FORMAL_MODEL_SNAPSHOT_PATH = (
    Path("D:/AI_Cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots")
    / FORMAL_MODEL_SNAPSHOT
)

CLASS_ORDER = ("logic", "causality", "analogy", "definition")
CLASS_UNIVERSE = frozenset(CLASS_ORDER)
PARTITIONS = ("FIT", "DIAGNOSTIC", "EVAL")
RECORD_ROLES = ("reference_form", "condition_realization")
ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}
N_CONDITIONS = 10
PERMUTATION_COUNT = math.factorial(N_CONDITIONS)
SUPPORT_RULE = "rho>0_and_p<=0.05"

PRIMARY_CHECKPOINT_SPECS = {
    "block16_pre_final_rmsnorm": {"hidden_states_index": 17, "role": "reference"},
    "block27_pre_final_rmsnorm": {"hidden_states_index": None, "role": "primary_final"},
}
SECONDARY_CHECKPOINT_NAMES = ("block27_post_final_rmsnorm",)

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

FORMAL_AUTHORIZATION_REQUIRED_FIELDS = {
    "schema_version",
    "experiment",
    "authorization_id",
    "single_use",
    "authorized_repository_commit",
    "authorized_runner_sha256",
    "frozen_manifest_sha256",
    "frozen_dataset_sha256",
    "preregistration_sha256",
    "model_name",
    "model_snapshot_identity",
    "model_hook_qualification_sha256",
    "canonical_result_path",
    "authorization_created_at_utc",
}


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


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")


def atomic_write_json(path: Path, data: Any) -> dict[str, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_name(path.name + ".staging")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if staging.exists():
        raise ProtocolIntegrityError("STAGING_FILE_ALREADY_EXISTS")
    staging.write_text(payload, encoding="utf-8", newline="\n")
    try:
        if path.exists():
            raise ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")
        os.link(str(staging), str(path))
    finally:
        if staging.exists():
            staging.unlink()
    return {"path": str(path), "sha256": sha256_file(path)}


def _repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


def _runner_sha256() -> str:
    return sha256_file(Path(__file__))


def _tracked_tree_clean(root: Path = ROOT) -> bool:
    completed = subprocess.run(
        ["git", "diff", "--quiet"], cwd=root, text=True, capture_output=True
    )
    if completed.returncode not in (0, 1):
        raise ProtocolIntegrityError("FORMAL_GIT_TRACKED_TREE_STATUS_UNAVAILABLE")
    return completed.returncode == 0


def _staging_empty(root: Path = ROOT) -> bool:
    completed = subprocess.run(
        ["git", "diff", "--cached", "--quiet"], cwd=root, text=True, capture_output=True
    )
    if completed.returncode not in (0, 1):
        raise ProtocolIntegrityError("FORMAL_GIT_STAGING_STATUS_UNAVAILABLE")
    return completed.returncode == 0


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_git_commit(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def load_freeze_manifest(root: Path = ROOT) -> dict[str, Any]:
    path = root / FROZEN_MANIFEST_PATH.relative_to(ROOT)
    if sha256_file(path) != FROZEN_MANIFEST_SHA256:
        raise ProtocolIntegrityError("FROZEN_MANIFEST_SHA_MISMATCH")
    manifest = read_json(path)
    if manifest.get("freeze_status") != "FROZEN_NOT_RUN":
        raise ProtocolIntegrityError("FROZEN_MANIFEST_STATUS_NOT_FROZEN")
    return manifest


def verify_frozen_authority(root: Path = ROOT) -> dict[str, Any]:
    dataset_path = root / FROZEN_DATASET_PATH.relative_to(ROOT)
    prereg_path = root / FINAL_PREREGISTRATION_PATH.relative_to(ROOT)
    condition_path = root / CONDITION_PANEL_PATH.relative_to(ROOT)
    schema_path = root / DATA_SCHEMA_PATH.relative_to(ROOT)
    identities = {
        "dataset": (dataset_path, FROZEN_DATASET_SHA256),
        "preregistration": (prereg_path, FINAL_PREREGISTRATION_SHA256),
        "manifest": (root / FROZEN_MANIFEST_PATH.relative_to(ROOT), FROZEN_MANIFEST_SHA256),
        "condition_panel": (condition_path, CONDITION_PANEL_SHA256),
        "data_schema": (schema_path, DATA_SCHEMA_SHA256),
    }
    for name, (path, expected) in identities.items():
        actual = sha256_file(path)
        if actual != expected:
            raise ProtocolIntegrityError(f"FROZEN_AUTHORITY_SHA_MISMATCH_{name.upper()}")
    manifest = load_freeze_manifest(root)
    if manifest.get("model_revision") != FORMAL_MODEL_SNAPSHOT:
        raise ProtocolIntegrityError("FROZEN_MODEL_REVISION_MISMATCH")
    if manifest.get("primary_scientific_unit") != "condition":
        raise ProtocolIntegrityError("FROZEN_PRIMARY_UNIT_MISMATCH")
    return {
        "dataset": {"path": str(dataset_path.relative_to(ROOT)), "sha256": FROZEN_DATASET_SHA256},
        "preregistration": {"path": str(prereg_path.relative_to(ROOT)), "sha256": FINAL_PREREGISTRATION_SHA256},
        "manifest": {"path": str(FROZEN_MANIFEST_PATH.relative_to(ROOT)), "sha256": FROZEN_MANIFEST_SHA256},
        "condition_panel": {"path": str(condition_path.relative_to(ROOT)), "sha256": CONDITION_PANEL_SHA256},
        "data_schema": {"path": str(schema_path.relative_to(ROOT)), "sha256": DATA_SCHEMA_SHA256},
    }


def verify_no_result_collision(root: Path = ROOT) -> None:
    canonical = root / CANONICAL_RESULT_PATH.relative_to(ROOT)
    if canonical.exists():
        raise ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")
    if canonical.with_name(canonical.name + ".staging").exists():
        raise ProtocolIntegrityError("RESULT_STAGING_ALREADY_EXISTS")


def _validate_frozen_dataset_structure(
    records: Sequence[Mapping[str, Any]],
    condition_panel: Mapping[str, Any],
    data_schema: Mapping[str, Any],
) -> list[RecordMeta]:
    if not isinstance(records, list):
        raise ProtocolIntegrityError("DATASET_TOP_LEVEL_NOT_ARRAY")
    required_fields = set(data_schema.get("record_required_fields", []))
    condition_ids = {item["condition_id"] for item in condition_panel["conditions"]}
    if len(condition_ids) != N_CONDITIONS:
        raise ProtocolIntegrityError("CONDITION_PANEL_COUNT_MISMATCH")

    metas: list[RecordMeta] = []
    family_records: dict[str, list[Mapping[str, Any]]] = {}
    for record in records:
        missing = required_fields - set(record)
        if missing:
            raise ProtocolIntegrityError(f"RECORD_MISSING_FIELDS: {sorted(missing)}")
        if record.get("semantic_class") not in CLASS_UNIVERSE:
            raise ProtocolIntegrityError("RECORD_INVALID_SEMANTIC_CLASS")
        if record.get("partition") not in PARTITIONS:
            raise ProtocolIntegrityError("RECORD_INVALID_PARTITION")
        if record.get("record_role") not in RECORD_ROLES:
            raise ProtocolIntegrityError("RECORD_INVALID_ROLE")
        if record.get("condition_id") not in condition_ids:
            raise ProtocolIntegrityError("RECORD_UNKNOWN_CONDITION")
        if record.get("transformation_rule_id") != record.get("condition_id"):
            raise ProtocolIntegrityError("RECORD_TRANSFORMATION_RULE_MISMATCH")
        if not isinstance(record.get("text"), str) or not record["text"].strip():
            raise ProtocolIntegrityError("RECORD_TEXT_EMPTY")
        family_records.setdefault(record["source_family_id"], []).append(record)
        metas.append(
            RecordMeta(
                record_id=record["record_id"],
                source_family_id=record["source_family_id"],
                semantic_class=record["semantic_class"],
                condition_id=record["condition_id"],
                partition=record["partition"],
                record_role=record["record_role"],
                text=record["text"],
            )
        )

    if len(metas) != 1760:
        raise ProtocolIntegrityError("DATASET_RECORD_COUNT_MISMATCH")
    if len(family_records) != 880:
        raise ProtocolIntegrityError("DATASET_FAMILY_COUNT_MISMATCH")

    for family_id, family in family_records.items():
        if len(family) != 2:
            raise ProtocolIntegrityError("FAMILY_RECORD_COUNT_NOT_TWO")
        roles = {record["record_role"] for record in family}
        if roles != set(RECORD_ROLES):
            raise ProtocolIntegrityError("FAMILY_ROLE_PAIR_MISMATCH")
        first = family[0]
        for record in family[1:]:
            for field in ("source_family_id", "semantic_class", "condition_id", "partition"):
                if record.get(field) != first.get(field):
                    raise ProtocolIntegrityError("FAMILY_METADATA_INCONSISTENT")

    partitions = {partition: [] for partition in PARTITIONS}
    for meta in metas:
        partitions[meta.partition].append(meta)
    for partition in PARTITIONS:
        family_count = len({meta.source_family_id for meta in partitions[partition]})
        expected_families = ALLOCATION[partition] * N_CONDITIONS * len(CLASS_ORDER)
        if family_count != expected_families:
            raise ProtocolIntegrityError(f"PARTITION_FAMILY_COUNT_MISMATCH_{partition}")

    condition_partition_family_ids: dict[tuple[str, str], set[str]] = {}
    for meta in metas:
        condition_partition_family_ids.setdefault((meta.condition_id, meta.partition), set()).add(meta.source_family_id)
    for (condition_id, partition), family_ids in condition_partition_family_ids.items():
        expected = ALLOCATION[partition] * len(CLASS_ORDER)
        if len(family_ids) != expected:
            raise ProtocolIntegrityError("CELL_FAMILY_COUNT_MISMATCH")

    base_to_condition: dict[str, set[str]] = {}
    for meta in metas:
        record = next(r for r in records if r["record_id"] == meta.record_id)
        base_to_condition.setdefault(record["base_content_identity"], set()).add(meta.condition_id)
    for base, conditions in base_to_condition.items():
        if len(conditions) != 1:
            raise ProtocolIntegrityError("CROSS_CONDITION_FAMILY_REUSE")

    family_partitions: dict[str, set[str]] = {}
    for meta in metas:
        family_partitions.setdefault(meta.source_family_id, set()).add(meta.partition)
    for family_id, parts in family_partitions.items():
        if len(parts) != 1:
            raise ProtocolIntegrityError("CROSS_PARTITION_FAMILY_OVERLAP")

    return metas


def load_frozen_dataset(root: Path = ROOT) -> tuple[list[Mapping[str, Any]], list[RecordMeta]]:
    verify_frozen_authority(root)
    dataset_path = root / FROZEN_DATASET_PATH.relative_to(ROOT)
    records = read_json(dataset_path)
    condition_panel = read_json(root / CONDITION_PANEL_PATH.relative_to(ROOT))
    data_schema = read_json(root / DATA_SCHEMA_PATH.relative_to(ROOT))
    metas = _validate_frozen_dataset_structure(records, condition_panel, data_schema)
    return records, metas


def partition_records(records: Sequence[Mapping[str, Any]]) -> dict[str, list[Mapping[str, Any]]]:
    partitions = {partition: [] for partition in PARTITIONS}
    for record in records:
        partitions[record["partition"]].append(record)
    return partitions


def average_rank(data: Sequence[float]) -> list[float]:
    array = np.asarray(data, dtype=float)
    order = np.argsort(array, kind="mergesort")
    sorted_values = array[order]
    ranks = np.empty(len(array), dtype=float)
    index = 0
    while index < len(array):
        j = index + 1
        while j < len(array) and sorted_values[j] == sorted_values[index]:
            j += 1
        rank = (index + 1 + j) / 2.0
        for k in range(index, j):
            ranks[order[k]] = rank
        index = j
    return [float(value) for value in ranks]


def spearman_rho(x: Sequence[float], y: Sequence[float]) -> float:
    if len(x) != len(y) or len(x) == 0:
        raise ValueError("Spearman inputs must be nonempty and equal length.")
    if len(x) == 1:
        return 0.0
    x_rank = np.asarray(average_rank(x), dtype=float)
    y_rank = np.asarray(average_rank(y), dtype=float)
    x_rank -= x_rank.mean()
    y_rank -= y_rank.mean()
    denominator = float(np.sqrt((x_rank @ x_rank) * (y_rank @ y_rank)))
    if denominator == 0.0:
        return 0.0
    return float((x_rank @ y_rank) / denominator)


def exact_one_sided_permutation_p(
    x: Sequence[float],
    y: Sequence[float],
    alternative: str = "greater",
) -> dict[str, float | int]:
    if len(x) != len(y):
        raise ValueError("Permutation inputs must be equal length.")
    n = len(x)
    if n > N_CONDITIONS:
        raise ValueError("Production exact test supports at most ten condition units.")
    observed = spearman_rho(x, y)
    y_rank = np.asarray(average_rank(y), dtype=float)
    y_rank -= y_rank.mean()
    x_rank = np.asarray(average_rank(x), dtype=float)
    x_rank -= x_rank.mean()
    denominator = float(np.sqrt((x_rank @ x_rank) * (y_rank @ y_rank)))
    count = 0
    for perm in itertools.permutations(range(n)):
        permuted = y_rank[list(perm)]
        numerator = float(x_rank @ permuted)
        rho = (numerator / denominator) if denominator else 0.0
        if rho >= observed:
            count += 1
    total = math.factorial(n)
    return {"rho": observed, "p": count / total, "count_ge": count, "total": total}


def primary_support_rule(rho: float, p: float, alpha: float = 0.05) -> bool:
    return bool(rho > 0 and p <= alpha)


def balanced_accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError("Balanced-accuracy inputs must be equal length.")
    classes = sorted(set(y_true))
    if not classes:
        return 0.0
    recalls = []
    for cls in classes:
        positives = [i for i, value in enumerate(y_true) if value == cls]
        if not positives:
            continue
        correct = sum(1 for i in positives if y_pred[i] == cls)
        recalls.append(correct / len(positives))
    return float(np.mean(recalls)) if recalls else 0.0


def fit_scaler(X: np.ndarray) -> StandardScaler:
    scaler = StandardScaler(**SCALER_KWARGS)
    scaler.fit(X)
    return scaler


def fit_classifier(X: np.ndarray, y: Sequence[str]) -> tuple[LogisticRegression, list[str]]:
    model = LogisticRegression(**CLASSIFIER_KWARGS)
    model.fit(X, list(y))
    labels = [str(value) for value in model.classes_]
    return model, labels


def transform_with_stats(X: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    mean = np.asarray(mean, dtype=float)
    scale = np.asarray(scale, dtype=float)
    return (X - mean) / scale


def predict_with_classifier(model: Any, X: np.ndarray) -> list[str]:
    return [str(value) for value in model.predict(X)]


def classifier_class_mapping(model: Any) -> list[str]:
    return [str(value) for value in model.classes_]


def calibration_condition_predictions(
    X: np.ndarray,
    reference_mean: np.ndarray,
    reference_scale: np.ndarray,
    condition_mean: np.ndarray,
    condition_scale: np.ndarray,
    classifier: Any,
) -> dict[str, list[str]]:
    a0 = transform_with_stats(X, reference_mean, reference_scale)
    a_mu = transform_with_stats(X, condition_mean, reference_scale)
    a_sigma = transform_with_stats(X, reference_mean, condition_scale)
    a_mu_sigma = transform_with_stats(X, condition_mean, condition_scale)
    return {
        "A0": predict_with_classifier(classifier, a0),
        "A_mu": predict_with_classifier(classifier, a_mu),
        "A_sigma": predict_with_classifier(classifier, a_sigma),
        "A_mu_sigma": predict_with_classifier(classifier, a_mu_sigma),
    }


def compute_s_diag(
    a0_reference_diag: Mapping[str, float],
    a0_final_diag: Mapping[str, float],
) -> dict[str, float]:
    return {
        condition: a0_reference_diag[condition] - a0_final_diag[condition]
        for condition in a0_reference_diag
    }


def compute_g_eval(
    a_mu_sigma_eval: Mapping[str, float],
    a0_final_eval: Mapping[str, float],
) -> dict[str, float]:
    return {
        condition: a_mu_sigma_eval[condition] - a0_final_eval[condition]
        for condition in a_mu_sigma_eval
    }


def validate_result_schema(result: Mapping[str, Any], *, formal: bool = False) -> None:
    if not isinstance(result, Mapping):
        raise ProtocolIntegrityError("RESULT_NOT_OBJECT")
    required = {
        "schema_version",
        "experiment",
        "runner",
        "model",
        "dataset",
        "classes",
        "primary",
        "technical_validity",
        "attempt_status",
        "result_status",
        "scientific_status",
        "provenance",
    }
    missing = required - set(result)
    if missing:
        raise ProtocolIntegrityError(f"RESULT_MISSING_FIELDS: {sorted(missing)}")
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ProtocolIntegrityError("RESULT_SCHEMA_VERSION_MISMATCH")
    if result["experiment"] != EXPERIMENT:
        raise ProtocolIntegrityError("RESULT_EXPERIMENT_MISMATCH")
    if result.get("hidden_states_included", True) is True:
        raise ProtocolIntegrityError("RESULT_MUST_NOT_INCLUDE_RAW_HIDDEN_STATES")
    if formal and result.get("result_status") != "FORMAL_RESULT":
        raise ProtocolIntegrityError("FORMAL_RESULT_STATUS_INVALID")
    if formal and result.get("scientific_status") != "FORMAL_ANALYSIS_COMPLETED":
        raise ProtocolIntegrityError("FORMAL_SCIENTIFIC_STATUS_INVALID")


def atomic_publish_validated_result(result: Mapping[str, Any], root: Path = ROOT) -> dict[str, str]:
    validate_result_schema(result, formal=True)
    verify_no_result_collision(root)
    canonical = root / CANONICAL_RESULT_PATH.relative_to(ROOT)
    return atomic_write_json(canonical, result)


def finalize_formal_result(result: Mapping[str, Any], root: Path = ROOT) -> dict[str, str]:
    return atomic_publish_validated_result(result, root)


def _require_formal_authorization(root: Path = ROOT) -> None:
    raise ProtocolIntegrityError("FORMAL_RUN_NOT_AUTHORIZED")


def _pre_consumption_static_checks(
    root: Path,
    authorization: Mapping[str, Any],
    auth_path: Path,
) -> None:
    verify_frozen_authority(root)
    verify_no_result_collision(root)
    _validate_formal_authorization(authorization, root)
    if not _tracked_tree_clean(root):
        raise ProtocolIntegrityError("FORMAL_TRACKED_TREE_NOT_CLEAN")
    if not _staging_empty(root):
        raise ProtocolIntegrityError("FORMAL_STAGING_NOT_EMPTY")
    if not _is_sha256(sha256_file(auth_path)):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_SHA_INVALID")


def _consumption_path_for(root: Path, authorization_sha256: str) -> Path:
    return (
        root
        / AUTHORIZATION_CONSUMPTION_DIR.relative_to(ROOT)
        / f"{authorization_sha256}.json"
    )


def _consume_formal_authorization(
    root: Path,
    authorization: Mapping[str, Any],
    auth_path: Path,
    run_attempt_id: str,
) -> dict[str, Any]:
    authorization_sha = sha256_file(auth_path)
    record_path = _consumption_path_for(root, authorization_sha)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": authorization_sha,
        "run_attempt_id": run_attempt_id,
        "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": authorization["authorized_repository_commit"],
        "runner_sha256": authorization["authorized_runner_sha256"],
        "frozen_manifest_sha256": authorization["frozen_manifest_sha256"],
        "frozen_dataset_sha256": authorization["frozen_dataset_sha256"],
        "preregistration_sha256": authorization["preregistration_sha256"],
        "model_name": authorization["model_name"],
        "model_snapshot_identity": authorization["model_snapshot_identity"],
        "model_hook_qualification_sha256": authorization["model_hook_qualification_sha256"],
        "canonical_result_path": authorization["canonical_result_path"],
    }
    payload = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    try:
        fd = os.open(str(record_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise ProtocolIntegrityError("AUTHORIZATION_ALREADY_CONSUMED") from exc
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return {
        "authorization_sha256": authorization_sha,
        "consumption_record_path": str(record_path),
        "consumption_record_sha256": sha256_file(record_path),
        "run_attempt_id": run_attempt_id,
    }


def _validate_formal_authorization(
    authorization: Mapping[str, Any], root: Path = ROOT
) -> Mapping[str, Any]:
    if not isinstance(authorization, Mapping):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_NOT_OBJECT")
    if set(authorization) != FORMAL_AUTHORIZATION_REQUIRED_FIELDS:
        missing = sorted(FORMAL_AUTHORIZATION_REQUIRED_FIELDS - set(authorization))
        extra = sorted(set(authorization) - FORMAL_AUTHORIZATION_REQUIRED_FIELDS)
        raise ProtocolIntegrityError(
            f"FORMAL_AUTHORIZATION_FIELDS_INVALID missing={missing} extra={extra}"
        )
    if authorization["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_SCHEMA_VERSION_MISMATCH")
    if authorization["experiment"] != EXPERIMENT:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXPERIMENT_MISMATCH")
    if authorization["single_use"] is not True:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_NOT_SINGLE_USE")
    if not isinstance(authorization["authorization_id"], str) or not authorization["authorization_id"].strip():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_ID_INVALID")
    if not _is_git_commit(authorization["authorized_repository_commit"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_REPOSITORY_COMMIT_INVALID")
    if not _is_sha256(authorization["authorized_runner_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_RUNNER_SHA_INVALID")
    if not _is_sha256(authorization["frozen_manifest_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_MANIFEST_SHA_INVALID")
    if not _is_sha256(authorization["frozen_dataset_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_DATASET_SHA_INVALID")
    if not _is_sha256(authorization["preregistration_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_PREREGISTRATION_SHA_INVALID")
    if not _is_sha256(authorization["model_hook_qualification_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_QUALIFICATION_SHA_INVALID")
    if not isinstance(authorization["authorization_created_at_utc"], str) or not authorization["authorization_created_at_utc"]:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_CREATED_AT_INVALID")

    bindings = {
        "authorized_repository_commit": _repository_commit(root),
        "authorized_runner_sha256": _runner_sha256(),
        "frozen_manifest_sha256": FROZEN_MANIFEST_SHA256,
        "frozen_dataset_sha256": FROZEN_DATASET_SHA256,
        "preregistration_sha256": FINAL_PREREGISTRATION_SHA256,
        "model_name": FORMAL_MODEL_NAME,
        "model_snapshot_identity": FORMAL_MODEL_SNAPSHOT,
        "canonical_result_path": CANONICAL_RESULT_PATH.relative_to(ROOT).as_posix(),
    }
    for field, expected in bindings.items():
        if authorization[field] != expected:
            raise ProtocolIntegrityError(
                f"FORMAL_AUTHORIZATION_BINDING_MISMATCH_{field.upper()}"
            )
    qualification = _verify_model_hook_qualification_artifact(root)
    if authorization["model_hook_qualification_sha256"] != qualification["sha256"]:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_QUALIFICATION_SHA_BINDING_MISMATCH")
    _verify_model_hook_qualification_current(qualification["artifact"])
    return authorization


def _verify_model_hook_qualification_artifact(root: Path = ROOT) -> dict[str, Any]:
    path = root / MODEL_HOOK_QUALIFICATION_PATH.relative_to(ROOT)
    if not path.is_file():
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_ARTIFACT_MISSING")
    artifact = read_json(path)
    if artifact.get("experiment") != EXPERIMENT:
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_EXPERIMENT_MISMATCH")
    if artifact.get("status") != "QUALIFIED":
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_NOT_QUALIFIED")
    if artifact.get("model_name") != FORMAL_MODEL_NAME:
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_MODEL_MISMATCH")
    if artifact.get("model_snapshot") != FORMAL_MODEL_SNAPSHOT:
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_SNAPSHOT_MISMATCH")
    return {
        "path": MODEL_HOOK_QUALIFICATION_PATH.relative_to(ROOT).as_posix(),
        "sha256": sha256_file(path),
        "artifact": artifact,
    }


def _verify_model_hook_qualification_current(artifact: Mapping[str, Any]) -> None:
    if artifact.get("runner_sha256") != _runner_sha256():
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_RUNNER_STALE")
    if artifact.get("frozen_manifest_sha256") != FROZEN_MANIFEST_SHA256:
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_MANIFEST_STALE")
    if artifact.get("frozen_dataset_sha256") != FROZEN_DATASET_SHA256:
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_DATASET_STALE")
    if artifact.get("preregistration_sha256") != FINAL_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("EXP024_MODEL_HOOK_QUALIFICATION_PREREGISTRATION_STALE")


def _execute_formal_after_consumption(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
) -> dict[str, Any]:
    raise TechnicalInvalidError("EXP024_FORMAL_RUNTIME_NOT_QUALIFIED_IN_098A")


def run_formal(
    root: Path = ROOT,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    if authorization_path is None:
        verify_frozen_authority(root)
        _require_formal_authorization(root)
    auth_path = Path(authorization_path)
    if not auth_path.is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_FILE_MISSING")
    authorization = read_json(auth_path)
    _pre_consumption_static_checks(root, authorization, auth_path)

    run_attempt_id = str(uuid.uuid4())
    consumption = _consume_formal_authorization(
        root, authorization, auth_path, run_attempt_id
    )
    result = _execute_formal_after_consumption(
        root, authorization, consumption, run_attempt_id
    )
    return finalize_formal_result(result, root)


def static_preflight(root: Path = ROOT) -> dict[str, Any]:
    authorities = verify_frozen_authority(root)
    records, metas = load_frozen_dataset(root)
    verify_no_result_collision(root)
    result_schema = read_json(root / RESULT_SCHEMA_PATH.relative_to(ROOT))
    auth_schema = read_json(root / AUTHORIZATION_SCHEMA_PATH.relative_to(ROOT))
    if result_schema.get("title") != "EXP-024 formal result schema":
        raise ProtocolIntegrityError("RESULT_SCHEMA_TITLE_MISMATCH")
    if auth_schema.get("title") != "EXP-024 formal-run authorization schema":
        raise ProtocolIntegrityError("AUTHORIZATION_SCHEMA_TITLE_MISMATCH")

    partition_families = {
        partition: len({meta.source_family_id for meta in metas if meta.partition == partition})
        for partition in PARTITIONS
    }
    output = {
        "status": "PASS",
        "classification": "ENGINEERING_STATIC_PREFLIGHT_ONLY",
        "experiment": EXPERIMENT,
        "runner": {
            "path": Path(__file__).relative_to(ROOT).as_posix(),
            "sha256": _runner_sha256(),
        },
        "frozen_authorities": authorities,
        "dataset": {
            "record_count": len(records),
            "source_family_count": len({meta.source_family_id for meta in metas}),
            "condition_count": len({meta.condition_id for meta in metas}),
            "semantic_class_count": len({meta.semantic_class for meta in metas}),
            "partition_families": partition_families,
        },
        "primary_scientific_unit": "condition",
        "primary_diagnostic": "S_diag(c)",
        "primary_outcome": "G_eval(c)",
        "primary_statistic": "Spearman_rho",
        "exact_permutation_count": PERMUTATION_COUNT,
        "support_rule": SUPPORT_RULE,
        "formal_result_present": False,
        "model_access": False,
        "scientific_outcome_access": False,
    }
    write_json(root / PREFLIGHT_PATH.relative_to(ROOT), output)
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static-preflight", action="store_true")
    modes.add_argument("--model-hook-qualification", action="store_true")
    modes.add_argument("--formal-run", action="store_true")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--authorization-file", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else ROOT
    try:
        if args.static_preflight:
            print(json.dumps(static_preflight(root), ensure_ascii=False, indent=2, sort_keys=True))
        elif args.model_hook_qualification:
            raise PermissionError("EXP024_MODEL_HOOK_QUALIFICATION_NOT_AUTHORIZED_IN_098A")
        elif args.formal_run:
            authorization_path = (
                Path(args.authorization_file).resolve()
                if args.authorization_file
                else None
            )
            run_formal(root, authorization_path)
        else:
            raise SystemExit("A mode is required.")
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (ProtocolIntegrityError, TechnicalInvalidError) as exc:
        print(f"EXP024_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
