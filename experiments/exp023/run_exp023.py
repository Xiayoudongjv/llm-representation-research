"""EXP-023 frozen runner and engineering preflight.

Task 096A implements the frozen EXP-023 protocol on synthetic/static evidence
only.  The formal-run path is complete but fail-closed until an EXP-023
single-use authorization and EXP-023 runtime/model-hook qualification artifact
are supplied.  Importing this module does not load a model, tokenizer, formal
prompt text, or hidden-state data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import uuid
import warnings
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


EXPERIMENT = "EXP-023"
EXPERIMENT_NAME = (
    "Independent Featurewise Calibration Replication and Mean/Scale Decomposition"
)
RESULT_SCHEMA_VERSION = "1.0.0"
FROZEN_PREREGISTRATION_SHA256 = (
    "11bfa984d436ba06f7f3d1b0db24b90439742e9d9a87d124880834b437749f0b"
)
ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
PREREGISTRATION_PATH = ROOT / "docs" / "experiments" / "EXP-023-PREREGISTRATION.md"
FREEZE_MANIFEST_PATH = ROOT / "docs" / "experiments" / "EXP-023-FREEZE-MANIFEST.json"
DATASET_PATH = EXP_DIR / "data" / "exp023_independent_controlled.json"
DATASET_SHA256 = (
    "9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a"
)
HISTORICAL_EXCLUSION_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
HISTORICAL_EXCLUSION_SHA256 = (
    "72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472"
)
CANONICAL_RESULT_PATH = EXP_DIR / "results" / "exp023_results.json"
PREFLIGHT_PATH = EXP_DIR / "engineering" / "runner_preflight.json"
MODEL_HOOK_QUALIFICATION_PATH = (
    EXP_DIR / "engineering" / "model_hook_qualification_post_patch.json"
)
FORMAL_MODEL_NAME = "Qwen/Qwen3-1.7B"
FORMAL_MODEL_SNAPSHOT = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
FORMAL_MODEL_SNAPSHOT_PATH = (
    Path("D:/AI_Cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots")
    / FORMAL_MODEL_SNAPSHOT
)
AUTHORIZATION_CONSUMPTION_DIR = EXP_DIR / "results" / "authorization_consumption"
TECHNICAL_FAILURE_EVIDENCE_DIR = EXP_DIR / "results" / "technical_failure_evidence"
FORMAL_AUTHORIZATION_REQUIRED_FIELDS = {
    "schema_version",
    "experiment",
    "authorization_id",
    "single_use",
    "authorized_repository_commit",
    "authorized_runner_sha256",
    "frozen_preregistration_sha256",
    "frozen_dataset_sha256",
    "model_name",
    "model_snapshot_identity",
    "model_hook_qualification_sha256",
    "canonical_result_path",
    "authorization_created_at_utc",
}
CLASS_UNIVERSE = ("logic", "causality", "analogy", "definition")
RAW_VARIANT_TO_CANONICAL_ROLE = {
    "original_style": "original",
    "paraphrase": "paraphrase",
}
RAW_VARIANT_UNIVERSE = frozenset(RAW_VARIANT_TO_CANONICAL_ROLE)
CANONICAL_VARIANT_ROLES = tuple(dict.fromkeys(RAW_VARIANT_TO_CANONICAL_ROLE.values()))
READOUT_CONDITIONS = ("A0", "A_mu", "A_sigma", "A_mu_sigma")
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
BOOTSTRAP_SEED = 20260818
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_QUANTILES = (0.025, 0.975)


def staging_path_for(canonical_path: Path) -> Path:
    return canonical_path.with_name(canonical_path.name + ".staging")


STAGING_RESULT_PATH = staging_path_for(CANONICAL_RESULT_PATH)


class ProtocolIntegrityError(RuntimeError):
    """Raised when a frozen authority or implementation invariant is violated."""


class TechnicalInvalidError(RuntimeError):
    """Raised when a computation is technically invalid under the protocol."""


@dataclass
class FormalFailureContext:
    """Tracks the current post-consumption production stage for failure evidence."""

    stage: str = "DATASET_LOAD"


@dataclass(frozen=True)
class CheckpointSpec:
    name: str
    block_index: int
    hidden_states_index: int | None
    representation_role: str


CHECKPOINT_SPECS = (
    CheckpointSpec("block16_pre_final_rmsnorm", 16, 17, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block17_pre_final_rmsnorm", 17, 18, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block18_pre_final_rmsnorm", 18, 19, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block19_pre_final_rmsnorm", 19, 20, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block20_pre_final_rmsnorm", 20, 21, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block21_pre_final_rmsnorm", 21, 22, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block22_pre_final_rmsnorm", 22, 23, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block23_pre_final_rmsnorm", 23, 24, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block24_pre_final_rmsnorm", 24, 25, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block25_pre_final_rmsnorm", 25, 26, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block26_pre_final_rmsnorm", 26, 27, "PRE_FINAL_RMSNORM"),
    CheckpointSpec("block27_pre_final_rmsnorm", 27, None, "PRE_FINAL_RMSNORM_HOOK"),
    CheckpointSpec("block27_post_final_rmsnorm", 27, 28, "POST_FINAL_RMSNORM"),
)
CHECKPOINT_NAMES = tuple(cp.name for cp in CHECKPOINT_SPECS)
CHECKPOINT_BY_NAME = {cp.name: cp for cp in CHECKPOINT_SPECS}
PRIMARY_REFERENCE_CHECKPOINT = "block16_pre_final_rmsnorm"
PRIMARY_ENDPOINT_CHECKPOINT = "block27_pre_final_rmsnorm"
POST_FINAL_CHECKPOINT = "block27_post_final_rmsnorm"


@dataclass(frozen=True)
class RecordMeta:
    record_id: str
    source_family_id: str
    source_semantic_class: str
    raw_variant_type: str
    canonical_variant: str


@dataclass
class SplitDataset:
    split_id: str
    fit_records: dict[str, tuple[str, ...]]
    eval_records: dict[str, tuple[str, ...]]
    labels: dict[str, str]
    source_families: dict[str, str]
    representations: dict[str, dict[str, np.ndarray]]


@dataclass(frozen=True)
class PredictionRow:
    split_id: str
    eval_record_id: str
    source_family_id: str
    source_semantic_class: str
    checkpoint: str
    readout_condition: str
    true_class: str
    predicted_class: str
    probability_vector: tuple[float, float, float, float]
    correct: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "split_id": self.split_id,
            "eval_record_id": self.eval_record_id,
            "source_family_id": self.source_family_id,
            "source_semantic_class": self.source_semantic_class,
            "checkpoint": self.checkpoint,
            "readout_condition": self.readout_condition,
            "true_class": self.true_class,
            "predicted_class": self.predicted_class,
            "probability_logic": self.probability_vector[0],
            "probability_causality": self.probability_vector[1],
            "probability_analogy": self.probability_vector[2],
            "probability_definition": self.probability_vector[3],
            "correct": self.correct,
        }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def atomic_write_json(path: Path, data: Any) -> dict[str, str]:
    """Publish JSON through an exclusive staging file without overwriting."""
    if path.exists():
        raise ProtocolIntegrityError(f"Canonical result already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = staging_path_for(path)
    payload = json.dumps(
        data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    staging_created = False
    try:
        with staging.open("x", encoding="utf-8", newline="\n") as handle:
            staging_created = True
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.link(staging, path)
    except Exception:
        if staging_created and staging.exists():
            staging.unlink()
        raise
    try:
        staging.unlink()
    except OSError:
        return {
            "publication_status": "PUBLISHED_WITH_STAGING_CLEANUP_FAILURE",
            "canonical_result_path": str(path),
        }
    return {
        "publication_status": "PUBLISHED",
        "canonical_result_path": str(path),
    }


def verify_frozen_authority(root: Path = ROOT) -> dict[str, Any]:
    prereg_path = root / PREREGISTRATION_PATH.relative_to(ROOT)
    actual = _sha256(prereg_path)
    if actual != FROZEN_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("FROZEN_PREREGISTRATION_SHA_MISMATCH")
    manifest = load_freeze_manifest(root)
    dataset_actual = _sha256(root / DATASET_PATH.relative_to(ROOT))
    if dataset_actual != DATASET_SHA256:
        raise ProtocolIntegrityError("FROZEN_DATASET_SHA_MISMATCH")
    historical_actual = _sha256(root / HISTORICAL_EXCLUSION_PATH.relative_to(ROOT))
    if historical_actual != HISTORICAL_EXCLUSION_SHA256:
        raise ProtocolIntegrityError("HISTORICAL_EXCLUSION_DATASET_SHA_MISMATCH")
    return {
        "preregistration": {
            "path": str(PREREGISTRATION_PATH.relative_to(ROOT)),
            "sha256": actual,
            "status": "FROZEN",
        },
        "dataset": {
            "path": str(DATASET_PATH.relative_to(ROOT)),
            "sha256": dataset_actual,
            "status": "FROZEN",
        },
        "historical_exclusion_dataset": {
            "path": str(HISTORICAL_EXCLUSION_PATH.relative_to(ROOT)),
            "sha256": historical_actual,
        },
        "freeze_manifest": manifest,
    }


def load_freeze_manifest(root: Path = ROOT) -> dict[str, Any]:
    path = root / FREEZE_MANIFEST_PATH.relative_to(ROOT)
    manifest = _read_json(path)
    if manifest.get("experiment") != EXPERIMENT:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_EXPERIMENT_MISMATCH")
    if manifest.get("status") != "FROZEN_PROTOCOL_NOT_RUN":
        raise ProtocolIntegrityError("FREEZE_MANIFEST_STATUS_MISMATCH")
    if manifest.get("preregistration_sha256") != FROZEN_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_PREREGISTRATION_SHA_MISMATCH")
    if manifest.get("dataset_sha256") != DATASET_SHA256:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_DATASET_SHA_MISMATCH")
    if manifest.get("model_name") != FORMAL_MODEL_NAME:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_MODEL_NAME_MISMATCH")
    if manifest.get("model_snapshot") != FORMAL_MODEL_SNAPSHOT:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_MODEL_SNAPSHOT_MISMATCH")
    if manifest.get("formal_run_authorized") is not False:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_FORMAL_RUN_AUTHORIZED_INVALID")
    return manifest


def verify_no_result_collision(root: Path = ROOT) -> None:
    canonical = root / CANONICAL_RESULT_PATH.relative_to(ROOT)
    staging = staging_path_for(canonical)
    if canonical.exists():
        raise ProtocolIntegrityError("EXP023_CANONICAL_RESULT_ALREADY_EXISTS")
    if staging.exists():
        raise ProtocolIntegrityError("EXP023_STAGING_RESULT_ALREADY_EXISTS")


def _installed_api_versions() -> dict[str, str]:
    import sklearn

    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
    }


def _validate_frozen_dataset_structure(root: Path = ROOT) -> dict[str, Any]:
    path = root / DATASET_PATH.relative_to(ROOT)
    actual = _sha256(path)
    if actual != DATASET_SHA256:
        raise ProtocolIntegrityError("FROZEN_DATASET_SHA_MISMATCH")
    records = _read_json(path)
    if not isinstance(records, list) or len(records) != 64:
        raise ProtocolIntegrityError("DATASET_RECORD_COUNT_MISMATCH")
    required_fields = {
        "record_id",
        "source_family_id",
        "SOURCE_SEMANTIC_CLASS",
        "variant_type",
        "text",
    }
    seen_records = set()
    seen_families = {}
    variant_counts = {variant: 0 for variant in RAW_VARIANT_UNIVERSE}
    class_counts = {cls: 0 for cls in CLASS_UNIVERSE}
    class_variant_counts = {
        cls: {variant: 0 for variant in RAW_VARIANT_UNIVERSE} for cls in CLASS_UNIVERSE
    }
    for record in records:
        if not isinstance(record, Mapping):
            raise ProtocolIntegrityError("DATASET_RECORD_NOT_OBJECT")
        if set(record) != required_fields:
            raise ProtocolIntegrityError("DATASET_RECORD_FIELDS_INVALID")
        record_id = str(record["record_id"])
        family_id = str(record["source_family_id"])
        cls = str(record["SOURCE_SEMANTIC_CLASS"])
        variant = str(record["variant_type"])
        text = record["text"]
        if not record_id.strip() or not family_id.strip() or not isinstance(text, str) or not text.strip():
            raise ProtocolIntegrityError("DATASET_RECORD_CONTENT_INVALID")
        if cls not in CLASS_UNIVERSE:
            raise ProtocolIntegrityError("DATASET_CLASS_UNIVERSE_MISMATCH")
        if variant not in RAW_VARIANT_UNIVERSE:
            raise ProtocolIntegrityError("DATASET_RAW_VARIANT_UNIVERSE_MISMATCH")
        if record_id in seen_records:
            raise ProtocolIntegrityError("DATASET_DUPLICATE_RECORD_ID")
        seen_records.add(record_id)
        seen_families.setdefault(family_id, []).append((variant, cls))
        variant_counts[variant] += 1
        class_counts[cls] += 1
        class_variant_counts[cls][variant] += 1
    if len(seen_records) != 64:
        raise ProtocolIntegrityError("DATASET_RECORD_ID_UNIQUENESS_VIOLATION")
    if len(seen_families) != 32:
        raise ProtocolIntegrityError("DATASET_SOURCE_FAMILY_COUNT_MISMATCH")
    for family_id, members in seen_families.items():
        if len(members) != 2:
            raise ProtocolIntegrityError("DATASET_FAMILY_MEMBER_COUNT_MISMATCH")
        variants = {variant for variant, _ in members}
        classes = {cls for _, cls in members}
        if variants != RAW_VARIANT_UNIVERSE or len(classes) != 1:
            raise ProtocolIntegrityError("DATASET_FAMILY_PAIR_INVALID")
    if variant_counts != {"original_style": 32, "paraphrase": 32}:
        raise ProtocolIntegrityError("DATASET_RAW_VARIANT_COUNT_MISMATCH")
    if class_counts != {cls: 16 for cls in CLASS_UNIVERSE}:
        raise ProtocolIntegrityError("DATASET_CLASS_COUNT_MISMATCH")
    for cls in CLASS_UNIVERSE:
        if class_variant_counts[cls] != {
            "original_style": 8,
            "paraphrase": 8,
        }:
            raise ProtocolIntegrityError("DATASET_CLASS_VARIANT_COUNT_MISMATCH")
    return {
        "path": str(DATASET_PATH.relative_to(ROOT)),
        "sha256": actual,
        "record_count": 64,
        "source_family_count": 32,
        "families_per_class": 8,
        "original_style_count": 32,
        "paraphrase_count": 32,
    }


def validate_dataset_records(records: Sequence[Mapping[str, Any]]) -> list[RecordMeta]:
    if len(records) != 64:
        raise ProtocolIntegrityError("DATASET_RECORD_COUNT_MISMATCH")
    metas = []
    for record in records:
        if not isinstance(record, Mapping):
            raise ProtocolIntegrityError("DATASET_RECORD_NOT_OBJECT")
        for field in ("record_id", "source_family_id", "SOURCE_SEMANTIC_CLASS", "variant_type", "text"):
            if field not in record:
                raise ProtocolIntegrityError(f"DATASET_RECORD_MISSING_{field.upper()}")
        record_id = str(record["record_id"])
        family_id = str(record["source_family_id"])
        cls = str(record["SOURCE_SEMANTIC_CLASS"])
        raw_variant = str(record["variant_type"])
        text = record["text"]
        if not record_id.strip() or not family_id.strip():
            raise ProtocolIntegrityError("DATASET_RECORD_ID_INVALID")
        if cls not in CLASS_UNIVERSE:
            raise ProtocolIntegrityError("DATASET_CLASS_UNIVERSE_MISMATCH")
        if raw_variant not in RAW_VARIANT_UNIVERSE:
            raise ProtocolIntegrityError("DATASET_RAW_VARIANT_UNIVERSE_MISMATCH")
        if not isinstance(text, str) or not text.strip():
            raise ProtocolIntegrityError("DATASET_RECORD_MISSING_TEXT")
        metas.append(
            RecordMeta(
                record_id=record_id,
                source_family_id=family_id,
                source_semantic_class=cls,
                raw_variant_type=raw_variant,
                canonical_variant=RAW_VARIANT_TO_CANONICAL_ROLE[raw_variant],
            )
        )
    ids = [meta.record_id for meta in metas]
    if len(set(ids)) != 64:
        raise ProtocolIntegrityError("DATASET_RECORD_ID_DUPLICATE")
    if {meta.source_semantic_class for meta in metas} != set(CLASS_UNIVERSE):
        raise ProtocolIntegrityError("DATASET_CLASS_UNIVERSE_MISMATCH")
    if {meta.raw_variant_type for meta in metas} != RAW_VARIANT_UNIVERSE:
        raise ProtocolIntegrityError("DATASET_RAW_VARIANT_UNIVERSE_MISMATCH")
    raw_counts = {
        variant: sum(1 for meta in metas if meta.raw_variant_type == variant)
        for variant in RAW_VARIANT_UNIVERSE
    }
    if raw_counts != {"original_style": 32, "paraphrase": 32}:
        raise ProtocolIntegrityError("DATASET_RAW_VARIANT_COUNT_MISMATCH")
    family_by_id = {}
    for meta in metas:
        family_by_id.setdefault(meta.source_family_id, []).append(meta)
    if len(family_by_id) != 32:
        raise ProtocolIntegrityError("DATASET_SOURCE_FAMILY_COUNT_MISMATCH")
    for family_id, family_metas in family_by_id.items():
        if len(family_metas) != 2:
            raise ProtocolIntegrityError("DATASET_FAMILY_MEMBER_COUNT_MISMATCH")
        variants = {meta.raw_variant_type for meta in family_metas}
        classes = {meta.source_semantic_class for meta in family_metas}
        if variants != RAW_VARIANT_UNIVERSE or len(classes) != 1:
            raise ProtocolIntegrityError("DATASET_FAMILY_PAIR_INVALID")
    return metas


def load_frozen_dataset(root: Path = ROOT) -> tuple[list[Mapping[str, Any]], list[RecordMeta]]:
    _validate_frozen_dataset_structure(root)
    records = _read_json(root / DATASET_PATH.relative_to(ROOT))
    return records, validate_dataset_records(records)


def build_split_datasets(
    records: Sequence[Mapping[str, Any]],
    metas: Sequence[RecordMeta],
    representations: Mapping[str, Mapping[str, np.ndarray]],
) -> dict[str, SplitDataset]:
    meta_by_id = {meta.record_id: meta for meta in metas}
    split_ids = ("A", "B")
    datasets = {}
    for split_id in split_ids:
        fit_raw = "original_style" if split_id == "A" else "paraphrase"
        eval_raw = "paraphrase" if split_id == "A" else "original_style"
        fit_ids = [
            meta.record_id for meta in metas if meta.raw_variant_type == fit_raw
        ]
        eval_ids = [
            meta.record_id for meta in metas if meta.raw_variant_type == eval_raw
        ]
        fit_records = {
            cls: tuple(
                rid for rid in fit_ids if meta_by_id[rid].source_semantic_class == cls
            )
            for cls in CLASS_UNIVERSE
        }
        eval_records = {
            cls: tuple(
                rid for rid in eval_ids if meta_by_id[rid].source_semantic_class == cls
            )
            for cls in CLASS_UNIVERSE
        }
        labels = {meta.record_id: meta.source_semantic_class for meta in metas}
        source_families = {meta.record_id: meta.source_family_id for meta in metas}
        datasets[split_id] = SplitDataset(
            split_id=split_id,
            fit_records=fit_records,
            eval_records=eval_records,
            labels=labels,
            source_families=source_families,
            representations=dict(representations),
        )
    return datasets


def exact_binomial_tail(favorable: int, unfavorable: int) -> float:
    if favorable < 0 or unfavorable < 0:
        raise ValueError("Discordance counts must be nonnegative.")
    m = favorable + unfavorable
    if m == 0:
        return 1.0
    denominator = 2**m
    numerator = sum(math.comb(m, k) for k in range(favorable, m + 1))
    return numerator / denominator


def balanced_accuracy(
    y_true: Sequence[str],
    y_pred: Sequence[str],
    classes: Sequence[str] = CLASS_UNIVERSE,
) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError("Label length mismatch.")
    recalls = []
    for cls in classes:
        indices = [i for i, label in enumerate(y_true) if label == cls]
        if not indices:
            raise ValueError(f"Class has no observations: {cls}")
        recalls.append(sum(y_pred[i] == cls for i in indices) / len(indices))
    return float(np.mean(recalls))


def accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if not y_true:
        return 0.0
    return float(np.mean([a == b for a, b in zip(y_true, y_pred)]))


def g_cal_support(estimate: float, exact_p: float, alpha: float = 0.05) -> bool:
    return estimate > 0 and exact_p <= alpha


def d_fixed_support(estimate: float, exact_p: float, alpha: float = 0.05) -> bool:
    return estimate < 0 and exact_p <= alpha


def _sign(value: float) -> int:
    if value == 0:
        return 0
    return 1 if value > 0 else -1


def cross_split_category(
    supported_a: bool,
    supported_b: bool,
    effect_a: float,
    effect_b: float,
) -> str:
    """Classify EXP-023 G_cal replication without pooling splits."""
    if supported_a and supported_b:
        return "FULL_REPLICATION"
    if supported_a != supported_b:
        unsupported_effect = effect_b if supported_a else effect_a
        if unsupported_effect > 0:
            return "PARTIAL_REPLICATION"
        if unsupported_effect < 0:
            return "SPLIT_HETEROGENEOUS"
        return "NO_REPLICATION"
    if (effect_a > 0 and effect_b < 0) or (effect_a < 0 and effect_b > 0):
        return "SPLIT_HETEROGENEOUS"
    return "NO_REPLICATION"


def _as_vector(value: Any, label: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float32)
    if array.ndim != 1:
        array = array.reshape(-1)
    if not np.isfinite(array).all():
        raise TechnicalInvalidError(f"NONFINITE_REPRESENTATION_{label}")
    return array


def validate_split_dataset(dataset: SplitDataset) -> None:
    if set(dataset.fit_records) != set(CLASS_UNIVERSE):
        raise TechnicalInvalidError("FIT_CLASS_UNIVERSE_MISMATCH")
    if set(dataset.eval_records) != set(CLASS_UNIVERSE):
        raise TechnicalInvalidError("EVAL_CLASS_UNIVERSE_MISMATCH")
    all_fit_ids = []
    all_eval_ids = []
    for cls in CLASS_UNIVERSE:
        fit_ids = dataset.fit_records[cls]
        eval_ids = dataset.eval_records[cls]
        if len(fit_ids) != 8 or len(eval_ids) != 8:
            raise TechnicalInvalidError("FROZEN_SPLIT_COUNT_MISMATCH")
        if len(set(fit_ids)) != 8 or len(set(eval_ids)) != 8:
            raise TechnicalInvalidError("DUPLICATE_RECORD_ID")
        if set(fit_ids) & set(eval_ids):
            raise TechnicalInvalidError("FIT_EVAL_OVERLAP")
        all_fit_ids.extend(fit_ids)
        all_eval_ids.extend(eval_ids)
    if len(set(all_fit_ids + all_eval_ids)) != 64:
        raise TechnicalInvalidError("RECORD_ID_UNIQUENESS_VIOLATION")
    for record_id, cls in dataset.labels.items():
        if cls not in CLASS_UNIVERSE:
            raise TechnicalInvalidError("UNEXPECTED_SOURCE_CLASS")
        if record_id not in dataset.representations:
            raise TechnicalInvalidError("MISSING_REPRESENTATIONS")
        if record_id not in dataset.source_families:
            raise TechnicalInvalidError("MISSING_SOURCE_FAMILY")
    expected_shape = None
    for record_id, checkpoints in dataset.representations.items():
        if record_id not in dataset.labels:
            raise TechnicalInvalidError("MISSING_LABEL")
        if set(checkpoints) != set(CHECKPOINT_NAMES):
            raise TechnicalInvalidError("CHECKPOINT_SET_MISMATCH")
        for cp, value in checkpoints.items():
            vector = _as_vector(value, f"{record_id}:{cp}")
            if expected_shape is None:
                expected_shape = vector.shape
            elif vector.shape != expected_shape:
                raise TechnicalInvalidError("REPRESENTATION_SHAPE_MISMATCH")


def _stack_records(
    dataset: SplitDataset,
    record_map: Mapping[str, Sequence[str]],
    checkpoint: str,
) -> tuple[np.ndarray, list[str], list[str]]:
    arrays = []
    ids = []
    labels = []
    for cls in CLASS_UNIVERSE:
        for record_id in record_map[cls]:
            arrays.append(_as_vector(dataset.representations[record_id][checkpoint], record_id))
            ids.append(record_id)
            labels.append(dataset.labels[record_id])
    if not arrays:
        raise TechnicalInvalidError("EMPTY_RECORD_BATCH")
    return np.stack(arrays), ids, labels


def fit_scaler(X: np.ndarray) -> StandardScaler:
    try:
        scaler = StandardScaler(**SCALER_KWARGS)
        return scaler.fit(X)
    except Exception as exc:
        raise TechnicalInvalidError("STANDARD_SCALER_FIT_EXCEPTION") from exc


def fit_classifier(X: np.ndarray, y: Sequence[str]) -> tuple[LogisticRegression, list[str]]:
    warning_messages = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            classifier = LogisticRegression(**CLASSIFIER_KWARGS)
            classifier.fit(X, y)
            warning_messages = [
                str(warning.message)
                for warning in caught
                if issubclass(warning.category, ConvergenceWarning)
            ]
    except Exception as exc:
        raise TechnicalInvalidError("CLASSIFIER_FIT_EXCEPTION") from exc
    if not np.isfinite(classifier.coef_).all() or not np.isfinite(classifier.intercept_).all():
        raise TechnicalInvalidError("NONFINITE_CLASSIFIER_COEFFICIENTS")
    return classifier, warning_messages


def _transform_with_stats(X: np.ndarray, mean: np.ndarray, scale: np.ndarray) -> np.ndarray:
    try:
        transformed = (X - mean) / scale
    except Exception as exc:
        raise TechnicalInvalidError("CONDITION_TRANSFORM_EXCEPTION") from exc
    if not np.isfinite(transformed).all():
        raise TechnicalInvalidError("NONFINITE_CONDITION_TRANSFORM")
    return transformed


def _predict_with_classifier(
    classifier: LogisticRegression,
    X: np.ndarray,
) -> tuple[np.ndarray, list[str]]:
    try:
        probabilities = classifier.predict_proba(X)
    except Exception as exc:
        raise TechnicalInvalidError("CLASSIFIER_PREDICTION_EXCEPTION") from exc
    if not np.isfinite(probabilities).all():
        raise TechnicalInvalidError("NONFINITE_PROBABILITIES")
    if probabilities.shape[1] != len(CLASS_UNIVERSE):
        raise TechnicalInvalidError("INVALID_PROBABILITY_WIDTH")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6):
        raise TechnicalInvalidError("INVALID_PROBABILITY_NORMALIZATION")
    classes = [str(cls) for cls in classifier.classes_]
    if set(classes) != set(CLASS_UNIVERSE):
        raise TechnicalInvalidError("CLASSIFIER_CLASS_MAP_MISMATCH")
    indices = [classes.index(cls) for cls in CLASS_UNIVERSE]
    probabilities = probabilities[:, indices]
    predicted = [CLASS_UNIVERSE[int(np.argmax(row))] for row in probabilities]
    return probabilities, predicted


def _build_prediction_rows(
    dataset: SplitDataset,
    checkpoint: str,
    readout_condition: str,
    classifier: LogisticRegression,
    transformed_eval: np.ndarray,
    eval_ids: Sequence[str],
    true_classes: Sequence[str],
) -> list[PredictionRow]:
    probabilities, predicted = _predict_with_classifier(classifier, transformed_eval)
    rows = []
    for row_index, record_id in enumerate(eval_ids):
        rows.append(
            PredictionRow(
                split_id=dataset.split_id,
                eval_record_id=record_id,
                source_family_id=dataset.source_families[record_id],
                source_semantic_class=dataset.labels[record_id],
                checkpoint=checkpoint,
                readout_condition=readout_condition,
                true_class=true_classes[row_index],
                predicted_class=predicted[row_index],
                probability_vector=tuple(float(v) for v in probabilities[row_index]),
                correct=predicted[row_index] == true_classes[row_index],
            )
        )
    return rows


def _condition_rows(
    rows: Sequence[PredictionRow],
    checkpoint: str,
    readout_condition: str,
) -> list[PredictionRow]:
    return [
        row
        for row in rows
        if row.checkpoint == checkpoint and row.readout_condition == readout_condition
    ]


def _condition_metrics(rows: Sequence[PredictionRow]) -> dict[str, Any]:
    if len(rows) != 32:
        raise TechnicalInvalidError("EXPECTED_THIRTY_TWO_EVAL_ROWS")
    true_classes = [row.true_class for row in rows]
    predicted_classes = [row.predicted_class for row in rows]
    recalls = {}
    for cls in CLASS_UNIVERSE:
        indices = [i for i, label in enumerate(true_classes) if label == cls]
        if len(indices) != 8:
            raise TechnicalInvalidError("EVAL_CLASS_BALANCE_MISMATCH")
        recalls[cls] = sum(predicted_classes[i] == cls for i in indices) / 8
    return {
        "balanced_accuracy": float(np.mean(list(recalls.values()))),
        "accuracy": accuracy(true_classes, predicted_classes),
        "per_class_recall": {cls: float(recalls[cls]) for cls in CLASS_UNIVERSE},
    }


def _metrics_for_rows(rows: Sequence[PredictionRow]) -> dict[str, dict[str, dict[str, Any]]]:
    metrics = {}
    for checkpoint in CHECKPOINT_NAMES:
        metrics[checkpoint] = {}
        for readout in READOUT_CONDITIONS:
            metrics[checkpoint][readout] = _condition_metrics(
                _condition_rows(rows, checkpoint, readout)
            )
    return metrics


def _metric_ba(
    metrics: Mapping[str, Mapping[str, Mapping[str, Any]]],
    checkpoint: str,
    readout: str,
) -> float:
    return float(metrics[checkpoint][readout]["balanced_accuracy"])


def correctness_by_class(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
    checkpoint: str,
    readout_condition: str,
) -> dict[str, list[bool]]:
    selected = _condition_rows(rows, checkpoint, readout_condition)
    by_record = {row.eval_record_id: row.correct for row in selected}
    return {
        cls: [by_record[record_id] for record_id in dataset.eval_records[cls]]
        for cls in CLASS_UNIVERSE
    }


def _discordance_counts(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
    cond_a: tuple[str, str],
    cond_b: tuple[str, str],
    *,
    favorable_a_correct_b_incorrect: bool,
) -> tuple[int, int]:
    map_a = correctness_by_class(dataset, rows, *cond_a)
    map_b = correctness_by_class(dataset, rows, *cond_b)
    favorable = 0
    unfavorable = 0
    for cls in CLASS_UNIVERSE:
        for record_index in range(8):
            a_correct = map_a[cls][record_index]
            b_correct = map_b[cls][record_index]
            if a_correct and not b_correct:
                if favorable_a_correct_b_incorrect:
                    favorable += 1
                else:
                    unfavorable += 1
            elif not a_correct and b_correct:
                if favorable_a_correct_b_incorrect:
                    unfavorable += 1
                else:
                    favorable += 1
    return favorable, unfavorable


BOOTSTRAP_CONTRASTS = (
    {
        "name": "G_cal",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A_mu_sigma",
    },
    {
        "name": "D_fixed",
        "a_checkpoint": PRIMARY_REFERENCE_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A0",
    },
    {
        "name": "G_mu",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A_mu",
    },
    {
        "name": "G_sigma",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A_sigma",
    },
    {
        "name": "G_joint_over_mu",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A_mu",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A_mu_sigma",
    },
    {
        "name": "G_joint_over_sigma",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A_sigma",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A_mu_sigma",
    },
)


def _balanced_accuracy_from_class_correct(
    correct_by_class: Mapping[str, Sequence[bool]],
) -> float:
    return float(np.mean([np.mean(list(values)) for values in correct_by_class.values()]))


def bootstrap_contrast(
    correct_a: Mapping[str, Sequence[bool]],
    correct_b: Mapping[str, Sequence[bool]],
    *,
    seed: int = BOOTSTRAP_SEED,
    resamples: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    if set(correct_a) != set(CLASS_UNIVERSE) or set(correct_b) != set(CLASS_UNIVERSE):
        raise ValueError("Bootstrap correctness class universe mismatch.")
    for cls in CLASS_UNIVERSE:
        if len(correct_a[cls]) != 8 or len(correct_b[cls]) != 8:
            raise ValueError("Frozen bootstrap requires exactly eight EVAL records per class.")
    rng = np.random.default_rng(np.random.PCG64(seed))
    class_means_a = np.zeros(resamples, dtype=np.float64)
    class_means_b = np.zeros(resamples, dtype=np.float64)
    for cls in CLASS_UNIVERSE:
        values_a = np.asarray(correct_a[cls], dtype=bool)
        values_b = np.asarray(correct_b[cls], dtype=bool)
        indices = rng.integers(0, 8, size=(resamples, 8))
        class_means_a += values_a[indices].mean(axis=1)
        class_means_b += values_b[indices].mean(axis=1)
    balanced_a = class_means_a / len(CLASS_UNIVERSE)
    balanced_b = class_means_b / len(CLASS_UNIVERSE)
    distribution = balanced_b - balanced_a
    lower, upper = np.quantile(distribution, BOOTSTRAP_QUANTILES, method="linear")
    return {
        "lower": float(lower),
        "upper": float(upper),
        "resamples": resamples,
        "seed": seed,
    }


def _bootstrap_intervals(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
    failure_context: FormalFailureContext | None = None,
) -> dict[str, dict[str, Any]]:
    if failure_context is not None:
        failure_context.stage = "BOOTSTRAP"
    output = {}
    for contrast in BOOTSTRAP_CONTRASTS:
        correct_a = correctness_by_class(
            dataset, rows, contrast["a_checkpoint"], contrast["a_readout"]
        )
        correct_b = correctness_by_class(
            dataset, rows, contrast["b_checkpoint"], contrast["b_readout"]
        )
        interval = bootstrap_contrast(correct_a, correct_b)
        output[contrast["name"]] = {
            "lower": interval["lower"],
            "upper": interval["upper"],
            "resamples": interval["resamples"],
            "seed": interval["seed"],
        }
    return output


def _build_split_summary(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
    technical_validity: str,
    warnings_list: Sequence[str],
    failure_context: FormalFailureContext | None = None,
) -> dict[str, Any]:
    metrics = _metrics_for_rows(rows)
    primary_ba = {
        readout: _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, readout)
        for readout in READOUT_CONDITIONS
    }
    reference_ba = _metric_ba(metrics, PRIMARY_REFERENCE_CHECKPOINT, "A0")
    g_cal = primary_ba["A_mu_sigma"] - primary_ba["A0"]
    g_favorable, g_unfavorable = _discordance_counts(
        dataset,
        rows,
        (PRIMARY_ENDPOINT_CHECKPOINT, "A0"),
        (PRIMARY_ENDPOINT_CHECKPOINT, "A_mu_sigma"),
        favorable_a_correct_b_incorrect=False,
    )
    g_p = exact_binomial_tail(g_favorable, g_unfavorable)
    g_supported = g_cal_support(g_cal, g_p)

    d_fixed = primary_ba["A0"] - reference_ba
    d_favorable, d_unfavorable = _discordance_counts(
        dataset,
        rows,
        (PRIMARY_REFERENCE_CHECKPOINT, "A0"),
        (PRIMARY_ENDPOINT_CHECKPOINT, "A0"),
        favorable_a_correct_b_incorrect=True,
    )
    d_p = exact_binomial_tail(d_favorable, d_unfavorable)
    d_supported = d_fixed_support(d_fixed, d_p)

    secondary = {
        "G_mu": primary_ba["A_mu"] - primary_ba["A0"],
        "G_sigma": primary_ba["A_sigma"] - primary_ba["A0"],
        "G_joint_over_mu": primary_ba["A_mu_sigma"] - primary_ba["A_mu"],
        "G_joint_over_sigma": primary_ba["A_mu_sigma"] - primary_ba["A_sigma"],
    }
    trajectories = {
        readout: {
            checkpoint: _metric_ba(metrics, checkpoint, readout)
            for checkpoint in CHECKPOINT_NAMES
        }
        for readout in READOUT_CONDITIONS
    }
    post_final_delta = {
        readout: _metric_ba(metrics, POST_FINAL_CHECKPOINT, readout)
        - _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, readout)
        for readout in READOUT_CONDITIONS
    }
    return {
        "split_id": dataset.split_id,
        "metrics": metrics,
        "primary": {
            "G_cal": {
                "estimate": g_cal,
                "favorable": g_favorable,
                "unfavorable": g_unfavorable,
                "exact_p": g_p,
                "supported": g_supported,
            },
            "D_fixed": {
                "estimate": d_fixed,
                "favorable": d_favorable,
                "unfavorable": d_unfavorable,
                "exact_p": d_p,
                "supported": d_supported,
                "serial_gate": "CONTEXTUAL_NOT_GATE",
            },
            "interpretation": {
                "g_cal_supported": g_supported,
                "d_fixed_supported": d_supported,
                "degradation_rescue_language_eligible": bool(g_supported and d_supported),
                "calibration_improvement_language_eligible": bool(g_supported),
            },
        },
        "secondary": secondary,
        "trajectories": trajectories,
        "post_final_delta": post_final_delta,
        "bootstrap": _bootstrap_intervals(dataset, rows, failure_context),
        "technical_validity": {"status": technical_validity},
        "warnings": list(warnings_list),
    }


def run_split_analysis(
    dataset: SplitDataset,
    failure_context: FormalFailureContext | None = None,
) -> dict[str, Any]:
    if failure_context is not None:
        failure_context.stage = "SPLIT_ANALYSIS"
    validate_split_dataset(dataset)
    X_ref_fit, _, y_ref_fit = _stack_records(
        dataset, dataset.fit_records, PRIMARY_REFERENCE_CHECKPOINT
    )
    scaler_ref = fit_scaler(X_ref_fit)
    X_ref_fit_scaled = scaler_ref.transform(X_ref_fit)
    if failure_context is not None:
        failure_context.stage = "CLASSIFIER_FIT"
    classifier_ref, warning_messages = fit_classifier(X_ref_fit_scaled, y_ref_fit)
    warnings_list = list(warning_messages)

    rows: list[PredictionRow] = []
    for checkpoint in CHECKPOINT_NAMES:
        X_fit_checkpoint, _, _ = _stack_records(
            dataset, dataset.fit_records, checkpoint
        )
        X_eval, eval_ids, true_classes = _stack_records(
            dataset, dataset.eval_records, checkpoint
        )
        scaler_l = fit_scaler(X_fit_checkpoint)
        stats = {
            "A0": (scaler_ref.mean_, scaler_ref.scale_),
            "A_mu": (scaler_l.mean_, scaler_ref.scale_),
            "A_sigma": (scaler_ref.mean_, scaler_l.scale_),
            "A_mu_sigma": (scaler_l.mean_, scaler_l.scale_),
        }
        for readout in READOUT_CONDITIONS:
            mean, scale = stats[readout]
            transformed_eval = _transform_with_stats(X_eval, mean, scale)
            rows.extend(
                _build_prediction_rows(
                    dataset,
                    checkpoint,
                    readout,
                    classifier_ref,
                    transformed_eval,
                    eval_ids,
                    true_classes,
                )
            )

    technical_validity = "VALID_WITH_WARNING" if warnings_list else "VALID"
    if failure_context is not None:
        failure_context.stage = "STATISTICS"
    summary = _build_split_summary(
        dataset,
        rows,
        technical_validity,
        warnings_list,
        failure_context,
    )
    return {
        "split_id": dataset.split_id,
        "summary": summary,
        "evaluation_rows": [row.to_dict() for row in rows],
        "technical_validity": technical_validity,
        "warnings": warnings_list,
    }


def make_synthetic_split(split_id: str, seed: int) -> SplitDataset:
    rng = np.random.default_rng(seed)
    dimension = 8
    reference_means = {cls: rng.normal(size=dimension) * 1.5 for cls in CLASS_UNIVERSE}
    final_means = {cls: rng.normal(size=dimension) * 2.5 for cls in CLASS_UNIVERSE}

    labels = {}
    source_families = {}
    representations = {}
    fit_records = {cls: [] for cls in CLASS_UNIVERSE}
    eval_records = {cls: [] for cls in CLASS_UNIVERSE}
    fit_raw, eval_raw = (
        ("original_style", "paraphrase")
        if split_id == "A"
        else ("paraphrase", "original_style")
    )

    for cls_index, cls in enumerate(CLASS_UNIVERSE):
        for item_index in range(1, 9):
            family_id = f"synthetic_{cls}_{item_index:02d}"
            fit_id = f"{family_id}_{fit_raw}"
            eval_id = f"{family_id}_{eval_raw}"
            fit_records[cls].append(fit_id)
            eval_records[cls].append(eval_id)
            labels[fit_id] = cls
            labels[eval_id] = cls
            source_families[fit_id] = family_id
            source_families[eval_id] = family_id

            ref_vector = reference_means[cls] + rng.normal(scale=0.04, size=dimension)
            final_vector = final_means[cls] + rng.normal(scale=0.04, size=dimension)
            checkpoint_vectors = {}
            for checkpoint in CHECKPOINT_NAMES:
                if checkpoint == PRIMARY_REFERENCE_CHECKPOINT:
                    checkpoint_vectors[checkpoint] = ref_vector.astype(np.float32)
                else:
                    checkpoint_vectors[checkpoint] = final_vector.astype(np.float32)
            representations[fit_id] = {
                cp: value.copy() for cp, value in checkpoint_vectors.items()
            }
            representations[eval_id] = {
                cp: value.copy() for cp, value in checkpoint_vectors.items()
            }

    return SplitDataset(
        split_id=split_id,
        fit_records={cls: tuple(fit_records[cls]) for cls in CLASS_UNIVERSE},
        eval_records={cls: tuple(eval_records[cls]) for cls in CLASS_UNIVERSE},
        labels=labels,
        source_families=source_families,
        representations=representations,
    )


def _static_result_schema_is_complete() -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "checkpoint_registry": CHECKPOINT_NAMES,
        "readout_registry": READOUT_CONDITIONS,
        "classifier_contract": CLASSIFIER_KWARGS,
        "bootstrap_contract": {
            "replicates": BOOTSTRAP_REPLICATES,
            "seed": BOOTSTRAP_SEED,
            "rng": "PCG64(20260818)",
            "quantiles": list(BOOTSTRAP_QUANTILES),
            "resampling": "class_stratified_eval_paired",
        },
        "authorization_required": True,
        "exclusive_consumption": True,
        "consumption_before_model_load": True,
        "atomic_no_overwrite_publication": True,
        "technical_failure_evidence": True,
        "model_hook_qualification_required": True,
        "formal_call_graph_placeholders": False,
    }


def _write_preflight_json(root: Path, key: str, value: dict[str, Any]) -> None:
    path = root / PREFLIGHT_PATH.relative_to(ROOT)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = _read_json(path)
    else:
        existing = {}
    existing[key] = value
    existing["experiment"] = EXPERIMENT
    existing["schema_version"] = RESULT_SCHEMA_VERSION
    _write_json(path, existing)


def static_preflight(root: Path = ROOT) -> dict[str, Any]:
    authority = verify_frozen_authority(root)
    verify_no_result_collision(root)
    _validate_frozen_dataset_structure(root)
    validator = subprocess.run(
        [
            sys.executable,
            str(root / "experiments" / "exp023" / "validate_exp023_dataset.py"),
        ],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if validator.returncode != 0 or "STRUCTURAL_VALIDATION = PASS" not in validator.stdout:
        raise ProtocolIntegrityError("STATIC_PREFLIGHT_DATASET_VALIDATOR_FAIL")
    versions = _installed_api_versions()
    result = {
        "status": "EXP023_STATIC_PREFLIGHT_PASS",
        "classification": "ENGINEERING_STATIC_PREFLIGHT_ONLY",
        "frozen_authority": authority,
        "dataset_structural_validation": "PASS",
        "result_schema": _static_result_schema_is_complete(),
        "versions": versions,
        "runner_path": str(Path(__file__).relative_to(ROOT)),
        "runner_sha256": _sha256(Path(__file__)),
        "formal_run_authorized": False,
        "model_hook_engineering_qualified": False,
        "canonical_result_present": (root / CANONICAL_RESULT_PATH.relative_to(ROOT)).exists(),
        "staging_result_present": staging_path_for(root / CANONICAL_RESULT_PATH.relative_to(ROOT)).exists(),
        "model_loaded": False,
        "tokenizer_loaded": False,
        "formal_prompt_text_accessed": False,
        "scientific_result_created": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_preflight_json(root, "static_preflight", result)
    return result


REQUIRED_RESULT_KEYS = {
    "schema_version",
    "experiment",
    "classification",
    "preregistration",
    "runner",
    "execution_mode",
    "model",
    "dataset",
    "classes",
    "checkpoints",
    "readout_definitions",
    "splits",
    "cross_split_synthesis",
    "technical_validity",
    "attempt_status",
    "result_status",
    "scientific_status",
    "warnings",
}


def validate_result_schema(result: Mapping[str, Any], *, formal: bool = False) -> None:
    if set(result) < REQUIRED_RESULT_KEYS:
        missing = sorted(REQUIRED_RESULT_KEYS - set(result))
        raise ProtocolIntegrityError(f"RESULT_SCHEMA_MISSING_KEYS: {missing}")
    if result["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ProtocolIntegrityError("RESULT_SCHEMA_VERSION_MISMATCH")
    if result["experiment"] != EXPERIMENT:
        raise ProtocolIntegrityError("RESULT_EXPERIMENT_MISMATCH")
    if result["preregistration"]["sha256"] != FROZEN_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("RESULT_PREREGISTRATION_SHA_MISMATCH")
    if result["dataset"]["sha256"] != DATASET_SHA256:
        raise ProtocolIntegrityError("RESULT_DATASET_SHA_MISMATCH")
    if formal:
        if result.get("execution_mode") != "formal-run":
            raise ProtocolIntegrityError("FORMAL_RESULT_EXECUTION_MODE_INVALID")
        if result["scientific_status"] == "NOT_RUN":
            raise ProtocolIntegrityError("FORMAL_RESULT_CLAIMS_NOT_RUN_VIOLATION")
    else:
        if result.get("execution_mode") != "synthetic-preflight":
            raise ProtocolIntegrityError("SYNTHETIC_RESULT_EXECUTION_MODE_INVALID")
        if result["scientific_status"] != "NOT_RUN":
            raise ProtocolIntegrityError("SYNTHETIC_RESULT_CLAIMS_NOT_RUN_VIOLATION")
    if result.get("prompt_text_included", True) or result.get("hidden_states_included", True):
        raise ProtocolIntegrityError("RESULT_CONTAINS_PROHIBITED_CONTENT")
    for split in result["splits"].values():
        if split["technical_validity"]["status"] not in {
            "VALID",
            "VALID_WITH_WARNING",
            "TECHNICALLY_INVALID",
        }:
            raise ProtocolIntegrityError("RESULT_TECHNICAL_VALIDITY_INVALID")


def atomic_publish_validated_result(result: Mapping[str, Any], root: Path = ROOT) -> dict[str, str]:
    canonical = root / CANONICAL_RESULT_PATH.relative_to(ROOT)
    return atomic_write_json(canonical, result)


def finalize_formal_result(
    result: Mapping[str, Any],
    root: Path = ROOT,
    failure_context: FormalFailureContext | None = None,
) -> dict[str, str]:
    if failure_context is not None:
        failure_context.stage = "RESULT_VALIDATION"
    validate_result_schema(result, formal=True)
    if failure_context is not None:
        failure_context.stage = "PUBLICATION"
    verify_no_result_collision(root)
    return atomic_publish_validated_result(result, root)


def synthetic_preflight(root: Path = ROOT) -> dict[str, Any]:
    verify_frozen_authority(root)
    load_freeze_manifest(root)
    verify_no_result_collision(root)
    analyses = {}
    for split_id, seed in (("A", 1), ("B", 2)):
        dataset = make_synthetic_split(split_id, seed)
        analyses[split_id] = run_split_analysis(dataset)

    split_a = analyses["A"]["summary"]
    split_b = analyses["B"]["summary"]
    cross_split = {
        "G_cal": cross_split_category(
            split_a["primary"]["G_cal"]["supported"],
            split_b["primary"]["G_cal"]["supported"],
            split_a["primary"]["G_cal"]["estimate"],
            split_b["primary"]["G_cal"]["estimate"],
        )
    }
    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "classification": "SYNTHETIC_PREFLIGHT_SCHEMA_VALIDATION",
        "preregistration": {
            "path": str(PREREGISTRATION_PATH.relative_to(ROOT)),
            "sha256": FROZEN_PREREGISTRATION_SHA256,
            "status": "FROZEN",
        },
        "runner": {
            "path": str(Path(__file__).relative_to(ROOT)),
            "sha256": _sha256(Path(__file__)),
        },
        "execution_mode": "synthetic-preflight",
        "model": {
            "model_id": FORMAL_MODEL_NAME,
            "snapshot": FORMAL_MODEL_SNAPSHOT,
            "local_files_only": True,
            "architecture": "Qwen3ForCausalLM",
            "model_type": "qwen3",
            "blocks": 28,
            "hidden_size": 2048,
            "vocab_size": 151936,
        },
        "dataset": {
            "path": str(DATASET_PATH.relative_to(ROOT)),
            "sha256": DATASET_SHA256,
            "record_count": 64,
            "source_family_count": 32,
            "fit_count_per_split": 32,
            "evaluation_count_per_split": 32,
            "records_per_class_per_split": 8,
        },
        "classes": list(CLASS_UNIVERSE),
        "checkpoints": CHECKPOINT_NAMES,
        "readout_definitions": {
            "A0": "fixed reference scaler and reference classifier",
            "A_mu": "FIT-only layer mean with reference scale; reference classifier retained",
            "A_sigma": "FIT-only layer scale with reference mean; reference classifier retained",
            "A_mu_sigma": "FIT-only layer mean and scale; reference classifier retained",
        },
        "splits": {
            "A": split_a,
            "B": split_b,
        },
        "cross_split_synthesis": cross_split,
        "technical_validity": {
            "status": "VALID"
            if all(a["technical_validity"] == "VALID" for a in analyses.values())
            else "VALID_WITH_WARNING"
        },
        "attempt_status": "SYNTHETIC_PREFLIGHT_COMPLETED",
        "result_status": "SYNTHETIC_ONLY",
        "scientific_status": "NOT_RUN",
        "warnings": [w for a in analyses.values() for w in a["warnings"]],
        "prompt_text_included": False,
        "hidden_states_included": False,
    }
    validate_result_schema(result)
    output = {
        "status": "EXP023_SYNTHETIC_PREFLIGHT_PASS",
        "classification": "ENGINEERING_SYNTHETIC_PREFLIGHT_ONLY",
        "experiment": EXPERIMENT,
        "frozen_preregistration_sha256": FROZEN_PREREGISTRATION_SHA256,
        "split_a": {
            "technical_validity": analyses["A"]["technical_validity"],
            "G_cal_supported": split_a["primary"]["G_cal"]["supported"],
            "D_fixed_supported": split_a["primary"]["D_fixed"]["supported"],
        },
        "split_b": {
            "technical_validity": analyses["B"]["technical_validity"],
            "G_cal_supported": split_b["primary"]["G_cal"]["supported"],
            "D_fixed_supported": split_b["primary"]["D_fixed"]["supported"],
        },
        "cross_split_synthesis": cross_split,
        "result_schema_validated": True,
        "model_loaded": False,
        "tokenizer_loaded": False,
        "formal_prompt_text_accessed": False,
        "scientific_result_created": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    _write_preflight_json(root, "synthetic_preflight", output)
    return output


def _require_formal_authorization(root: Path) -> None:
    raise PermissionError("FORMAL_RUN_NOT_AUTHORIZED")


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
    authorization = _read_json(auth_path)
    _pre_consumption_static_checks(root, authorization, auth_path)

    run_attempt_id = str(uuid.uuid4())
    failure_context = FormalFailureContext()
    consumption = _consume_formal_authorization(
        root, authorization, auth_path, run_attempt_id
    )
    try:
        result = _execute_formal_after_consumption(
            root,
            authorization,
            consumption,
            run_attempt_id,
            failure_context,
        )
        failure_context.stage = "RESULT_VALIDATION"
        return finalize_formal_result(result, root, failure_context)
    except Exception as exc:
        _preserve_technical_failure_after_consumption(
            root,
            authorization,
            consumption,
            run_attempt_id,
            failure_context.stage,
            exc,
        )
        raise


def _runner_sha256() -> str:
    return _sha256(Path(__file__))


def _repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()


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
    if not _is_sha256(authorization["frozen_preregistration_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_PREREGISTRATION_SHA_INVALID")
    if not _is_sha256(authorization["frozen_dataset_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_DATASET_SHA_INVALID")
    if not _is_sha256(authorization["model_hook_qualification_sha256"]):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_QUALIFICATION_SHA_INVALID")
    if not isinstance(authorization["authorization_created_at_utc"], str) or not authorization["authorization_created_at_utc"]:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_CREATED_AT_INVALID")

    canonical_path = CANONICAL_RESULT_PATH.relative_to(ROOT).as_posix()
    bindings = {
        "authorized_repository_commit": _repository_commit(root),
        "authorized_runner_sha256": _runner_sha256(),
        "frozen_preregistration_sha256": FROZEN_PREREGISTRATION_SHA256,
        "frozen_dataset_sha256": DATASET_SHA256,
        "model_name": FORMAL_MODEL_NAME,
        "model_snapshot_identity": FORMAL_MODEL_SNAPSHOT,
        "canonical_result_path": canonical_path,
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
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_ARTIFACT_MISSING")
    artifact = _read_json(path)
    if artifact.get("experiment") != EXPERIMENT:
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_EXPERIMENT_MISMATCH")
    if artifact.get("status") != "QUALIFIED":
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_NOT_QUALIFIED")
    if artifact.get("model_name") != FORMAL_MODEL_NAME:
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_MODEL_MISMATCH")
    if artifact.get("model_snapshot") != FORMAL_MODEL_SNAPSHOT:
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_SNAPSHOT_MISMATCH")
    return {
        "path": MODEL_HOOK_QUALIFICATION_PATH.relative_to(ROOT).as_posix(),
        "sha256": _sha256(path),
        "artifact": artifact,
    }


def _verify_model_hook_qualification_current(artifact: Mapping[str, Any]) -> None:
    if artifact.get("runner_sha256") != _runner_sha256():
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_RUNNER_STALE")
    if artifact.get("frozen_preregistration_sha256") != FROZEN_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_PREREGISTRATION_STALE")
    if artifact.get("frozen_dataset_sha256") != DATASET_SHA256:
        raise ProtocolIntegrityError("EXP023_MODEL_HOOK_QUALIFICATION_DATASET_STALE")


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
    authorization_sha = _sha256(auth_path)
    if not _is_sha256(authorization_sha):
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
    authorization_sha = _sha256(auth_path)
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
        "frozen_preregistration_sha256": authorization["frozen_preregistration_sha256"],
        "frozen_dataset_sha256": authorization["frozen_dataset_sha256"],
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
        "consumption_record_sha256": _sha256(record_path),
        "run_attempt_id": run_attempt_id,
    }


def _technical_failure_evidence_path_for(root: Path, run_attempt_id: str) -> Path:
    return (
        root
        / TECHNICAL_FAILURE_EVIDENCE_DIR.relative_to(ROOT)
        / f"{run_attempt_id}.json"
    )


def _failure_class(exc: Exception) -> str:
    if isinstance(exc, ProtocolIntegrityError):
        return "PROTOCOL_INTEGRITY"
    if isinstance(exc, TechnicalInvalidError):
        return "TECHNICAL_INVALID"
    return "RUNTIME"


def _sanitized_exception_type(exc: Exception) -> str:
    return type(exc).__name__


def _sanitized_exception_message(exc: Exception, failure_stage: str) -> str:
    return f"post_consumption_failure at {failure_stage}"


def _preserve_technical_failure_after_consumption(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
    failure_stage: str,
    exc: Exception,
) -> None:
    record_path = _technical_failure_evidence_path_for(root, run_attempt_id)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    consumption_record_path = Path(consumption["consumption_record_path"])
    if not consumption_record_path.is_file():
        raise ProtocolIntegrityError("CONSUMPTION_RECORD_MISSING_FOR_FAILURE_EVIDENCE")
    try:
        consumption_record_sha256 = _sha256(consumption_record_path)
    except OSError as exc2:
        raise ProtocolIntegrityError(
            "CONSUMPTION_RECORD_SHA_UNAVAILABLE_FOR_FAILURE_EVIDENCE"
        ) from exc2
    record = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "classification": "FORMAL_RUN_TECHNICAL_FAILURE_EVIDENCE",
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": consumption["authorization_sha256"],
        "consumption_record_path": str(consumption_record_path),
        "consumption_record_sha256": consumption_record_sha256,
        "run_attempt_id": run_attempt_id,
        "repository_commit": authorization["authorized_repository_commit"],
        "runner_sha256": authorization["authorized_runner_sha256"],
        "frozen_preregistration_sha256": authorization["frozen_preregistration_sha256"],
        "frozen_dataset_sha256": authorization["frozen_dataset_sha256"],
        "model_hook_qualification_sha256": authorization["model_hook_qualification_sha256"],
        "model_name": authorization["model_name"],
        "model_snapshot_identity": authorization["model_snapshot_identity"],
        "canonical_result_path": authorization["canonical_result_path"],
        "failure_stage": failure_stage,
        "failure_class": _failure_class(exc),
        "sanitized_exception_type": _sanitized_exception_type(exc),
        "sanitized_exception_message": _sanitized_exception_message(
            exc, failure_stage
        ),
        "attempt_status": "TECHNICALLY_INVALID",
        "result_status": "NO_SCIENTIFIC_RESULT",
        "scientific_status": "NOT_OBSERVED",
        "technical_validity": {"status": "TECHNICALLY_INVALID"},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "prompt_text_included": False,
        "hidden_states_included": False,
    }
    payload = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    try:
        fd = os.open(str(record_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc2:
        raise ProtocolIntegrityError("TECHNICAL_FAILURE_EVIDENCE_ALREADY_EXISTS") from exc2
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _verify_formal_dataset_identity(root: Path = ROOT) -> dict[str, Any]:
    path = root / DATASET_PATH.relative_to(ROOT)
    actual = _sha256(path)
    if actual != DATASET_SHA256:
        raise ProtocolIntegrityError("FORMAL_DATASET_SHA_MISMATCH")
    return {"path": str(DATASET_PATH.relative_to(ROOT)), "sha256": actual}


def _load_formal_records(root: Path = ROOT) -> tuple[list[Mapping[str, Any]], list[RecordMeta]]:
    return load_frozen_dataset(root)


def _load_formal_runtime(
    root: Path = ROOT,
    failure_context: FormalFailureContext | None = None,
) -> tuple[Any, Any, torch.device]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if failure_context is not None:
        failure_context.stage = "TOKENIZER_LOAD"
    tokenizer = AutoTokenizer.from_pretrained(
        str(FORMAL_MODEL_SNAPSHOT_PATH), local_files_only=True
    )
    if failure_context is not None:
        failure_context.stage = "MODEL_LOAD"
    model = AutoModelForCausalLM.from_pretrained(
        str(FORMAL_MODEL_SNAPSHOT_PATH), dtype=torch.float16, local_files_only=True
    )
    _validate_formal_model_architecture(model)
    device = torch.device("cuda:0")
    model.to(device)
    model.eval()
    torch.set_grad_enabled(False)
    return tokenizer, model, device


def _validate_formal_model_architecture(model: Any) -> None:
    if type(model).__name__ != "Qwen3ForCausalLM":
        raise ProtocolIntegrityError("FORMAL_MODEL_CLASS_MISMATCH")
    config = getattr(model, "config", None)
    if config is None:
        raise ProtocolIntegrityError("FORMAL_MODEL_CONFIG_MISSING")
    if getattr(config, "model_type", None) != "qwen3":
        raise ProtocolIntegrityError("FORMAL_MODEL_TYPE_MISMATCH")
    if int(getattr(config, "hidden_size", -1)) != 2048:
        raise ProtocolIntegrityError("FORMAL_MODEL_HIDDEN_SIZE_MISMATCH")
    if int(getattr(config, "num_hidden_layers", -1)) != 28:
        raise ProtocolIntegrityError("FORMAL_MODEL_LAYER_COUNT_MISMATCH")
    if not hasattr(model, "model") or len(model.model.layers) != 28:
        raise ProtocolIntegrityError("FORMAL_MODEL_TRANSFORMER_BLOCKS_MISMATCH")


def _tokenize_formal_record(tokenizer: Any, text: str, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    encoded = tokenizer(
        text,
        return_tensors="pt",
        padding=False,
        truncation=False,
        add_special_tokens=True,
    )
    return encoded["input_ids"].to(device), encoded["attention_mask"].to(device)


def _extract_formal_representations(
    root: Path,
    tokenizer: Any,
    model: Any,
    device: torch.device,
    records: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, np.ndarray]]:
    representations: dict[str, dict[str, np.ndarray]] = {}
    block27 = model.model.layers[27]
    for record in records:
        record_id = str(record["record_id"])
        input_ids, attention_mask = _tokenize_formal_record(
            tokenizer, str(record["text"]), device
        )
        capture = ForwardHookCapture()
        with torch.inference_mode():
            with block_output_hook_capture(block27, capture):
                outputs = model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    use_cache=False,
                    output_hidden_states=True,
                )
        checkpoints = extract_checkpoint_tensors(outputs.hidden_states, capture.value)
        selected = extract_last_token_representations(checkpoints, attention_mask)
        representations[record_id] = {
            name: to_float32_analysis_array(selected[name][0], expected_ndim=1)
            for name in CHECKPOINT_NAMES
        }
    return representations


def _build_formal_split_datasets(
    root: Path,
    records: Sequence[Mapping[str, Any]],
    metas: Sequence[RecordMeta],
    representations: Mapping[str, Mapping[str, np.ndarray]],
) -> dict[str, SplitDataset]:
    return build_split_datasets(records, metas, representations)


def _build_formal_result(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
    dataset_identity: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    metas: Sequence[RecordMeta],
    analyses: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    split_a = analyses["A"]["summary"]
    split_b = analyses["B"]["summary"]
    cross_split = {
        "G_cal": cross_split_category(
            split_a["primary"]["G_cal"]["supported"],
            split_b["primary"]["G_cal"]["supported"],
            split_a["primary"]["G_cal"]["estimate"],
            split_b["primary"]["G_cal"]["estimate"],
        )
    }
    analysis_warnings = [w for analysis in analyses.values() for w in analysis["warnings"]]
    validity_values = [analysis["technical_validity"] for analysis in analyses.values()]
    if all(value == "VALID" for value in validity_values):
        technical_validity = "VALID"
    elif all(value in {"VALID", "VALID_WITH_WARNING"} for value in validity_values):
        technical_validity = "VALID_WITH_WARNING"
    else:
        technical_validity = "TECHNICALLY_INVALID"
    if technical_validity == "TECHNICALLY_INVALID":
        raise TechnicalInvalidError("FORMAL_SPLIT_TECHNICALLY_INVALID")

    result = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "classification": "FORMAL_SCIENTIFIC_RESULT",
        "preregistration": {
            "path": str(PREREGISTRATION_PATH.relative_to(ROOT)),
            "sha256": FROZEN_PREREGISTRATION_SHA256,
            "status": "FROZEN",
        },
        "runner": {
            "path": str(Path(__file__).relative_to(ROOT)),
            "sha256": _runner_sha256(),
        },
        "execution_mode": "formal-run",
        "model": {
            "model_id": FORMAL_MODEL_NAME,
            "snapshot": FORMAL_MODEL_SNAPSHOT,
            "local_files_only": True,
            "architecture": "Qwen3ForCausalLM",
            "model_type": "qwen3",
            "blocks": 28,
            "hidden_size": 2048,
            "vocab_size": 151936,
        },
        "dataset": {
            "path": str(DATASET_PATH.relative_to(ROOT)),
            "sha256": dataset_identity["sha256"],
            "record_count": 64,
            "source_family_count": 32,
            "fit_count_per_split": 32,
            "evaluation_count_per_split": 32,
            "records_per_class_per_split": 8,
        },
        "classes": list(CLASS_UNIVERSE),
        "checkpoints": CHECKPOINT_NAMES,
        "readout_definitions": {
            "A0": "fixed reference scaler and reference classifier",
            "A_mu": "FIT-only layer mean with reference scale; reference classifier retained",
            "A_sigma": "FIT-only layer scale with reference mean; reference classifier retained",
            "A_mu_sigma": "FIT-only layer mean and scale; reference classifier retained",
        },
        "splits": {
            "A": split_a,
            "B": split_b,
        },
        "cross_split_synthesis": cross_split,
        "technical_validity": {"status": technical_validity},
        "attempt_status": "FORMAL_RUN_ATTEMPT_COMPLETED",
        "result_status": "FORMAL_RESULT",
        "scientific_status": "FORMAL_ANALYSIS_COMPLETED",
        "warnings": analysis_warnings,
        "prompt_text_included": False,
        "hidden_states_included": False,
        "provenance": {
            "repository_commit": _repository_commit(root),
            "authorization": {
                "authorization_id": authorization["authorization_id"],
                "authorization_sha256": consumption["authorization_sha256"],
            },
            "consumption_record": {
                "path": consumption["consumption_record_path"],
                "sha256": consumption["consumption_record_sha256"],
            },
            "run_attempt_id": run_attempt_id,
            "formal_dataset": dataset_identity,
            "model": {
                "name": FORMAL_MODEL_NAME,
                "snapshot": FORMAL_MODEL_SNAPSHOT,
            },
            "model_hook_qualification_sha256": authorization["model_hook_qualification_sha256"],
            "runtime_versions": _installed_api_versions(),
        },
    }
    validate_result_schema(result, formal=True)
    return result


def _execute_formal_after_consumption(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
    failure_context: FormalFailureContext | None = None,
) -> dict[str, Any]:
    if failure_context is None:
        failure_context = FormalFailureContext()
    failure_context.stage = "DATASET_LOAD"
    dataset_identity = _verify_formal_dataset_identity(root)
    records, metas = _load_formal_records(root)
    tokenizer, model, device = _load_formal_runtime(root, failure_context)
    failure_context.stage = "REPRESENTATION_EXTRACTION"
    representations = _extract_formal_representations(
        root, tokenizer, model, device, records
    )
    failure_context.stage = "SPLIT_ANALYSIS"
    datasets = _build_formal_split_datasets(root, records, metas, representations)
    analyses = {
        split_id: run_split_analysis(dataset, failure_context)
        for split_id, dataset in datasets.items()
    }
    failure_context.stage = "RESULT_CONSTRUCTION"
    return _build_formal_result(
        root,
        authorization,
        consumption,
        run_attempt_id,
        dataset_identity,
        records,
        metas,
        analyses,
    )


def last_valid_token_indices(attention_mask: Any) -> Any:
    if torch.is_tensor(attention_mask):
        mask = attention_mask
        if mask.ndim not in (1, 2):
            raise ValueError("Attention mask must be one- or two-dimensional.")
        if mask.numel() == 0:
            raise ValueError("Attention mask must contain at least one token.")
        if mask.dtype.is_complex:
            raise TypeError("Complex attention masks are not supported.")
        if torch.is_floating_point(mask) and not bool(torch.isfinite(mask).all()):
            raise ValueError("Attention mask contains non-finite values.")
        if bool(torch.any(mask < 0)):
            raise ValueError("Attention mask contains negative values.")
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
    if np.iscomplexobj(mask):
        raise TypeError("Complex attention masks are not supported.")
    if not np.isfinite(mask).all():
        raise ValueError("Attention mask contains non-finite values.")
    if np.any(mask < 0):
        raise ValueError("Attention mask contains negative values.")
    if mask.ndim == 1:
        index = int(mask.sum()) - 1
        if index < 0:
            raise ValueError("Attention mask contains no valid token.")
        return [index]
    indices = [int(row.sum()) - 1 for row in mask]
    if any(index < 0 for index in indices):
        raise ValueError("Attention mask contains no valid token.")
    return indices


def _indices_to_python_list(indices: Any) -> list[int]:
    if torch.is_tensor(indices):
        return [int(value) for value in indices.detach().cpu().tolist()]
    return [int(value) for value in indices]


def _select_last_valid_token_torch(hidden_states: Any, indices: Any) -> Any:
    if hidden_states.ndim not in (2, 3):
        raise ValueError("Hidden states must be two- or three-dimensional.")
    if torch.is_tensor(indices):
        index_tensor = indices.to(device=hidden_states.device, dtype=torch.long).reshape(-1)
    else:
        index_tensor = torch.as_tensor(
            indices, dtype=torch.long, device=hidden_states.device
        ).reshape(-1)
    if hidden_states.ndim == 2:
        if index_tensor.numel() != 1:
            raise ValueError("Two-dimensional hidden states require exactly one valid-token index.")
        if hidden_states.shape[0] == 0:
            raise ValueError("Hidden-state sequence dimension must be nonempty.")
        token_index = index_tensor[0]
        if bool(token_index < 0) or bool(token_index >= hidden_states.shape[0]):
            raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
        return hidden_states[token_index]
    if hidden_states.shape[0] == 0:
        raise ValueError("Hidden-state batch dimension must be nonempty.")
    if index_tensor.numel() != hidden_states.shape[0]:
        raise ValueError("Valid-token index count must match hidden-state batch dimension.")
    return hidden_states[torch.arange(hidden_states.shape[0], device=hidden_states.device), index_tensor]


def _select_last_valid_token_numpy(hidden_states: Any, indices: Any) -> np.ndarray:
    array = np.asarray(hidden_states)
    if array.ndim not in (2, 3):
        raise ValueError("Hidden states must be two- or three-dimensional.")
    index_list = _indices_to_python_list(indices)
    if array.ndim == 2:
        if len(index_list) != 1:
            raise ValueError("Two-dimensional hidden states require exactly one valid-token index.")
        if array.shape[0] == 0:
            raise ValueError("Hidden-state sequence dimension must be nonempty.")
        index = index_list[0]
        if index < 0 or index >= array.shape[0]:
            raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
        return array[index]
    if array.shape[0] == 0:
        raise ValueError("Hidden-state batch dimension must be nonempty.")
    if len(index_list) != array.shape[0]:
        raise ValueError("Valid-token index count must match hidden-state batch dimension.")
    return array[np.arange(array.shape[0]), index_list]


def select_last_valid_token_at_indices(hidden_states: Any, indices: Any) -> Any:
    if torch.is_tensor(hidden_states):
        return _select_last_valid_token_torch(hidden_states, indices)
    return _select_last_valid_token_numpy(hidden_states, indices)


def select_last_valid_token(hidden_states: Any, attention_mask: Any) -> Any:
    return select_last_valid_token_at_indices(
        hidden_states, last_valid_token_indices(attention_mask)
    )


def to_float32_analysis_array(value: Any, expected_ndim: int | None = None) -> np.ndarray:
    if torch.is_tensor(value):
        array = value.detach().cpu().numpy()
    else:
        array = np.asarray(value)
    array = np.asarray(array, dtype=np.float32)
    if expected_ndim is not None and array.ndim != expected_ndim:
        if array.ndim == expected_ndim + 1 and array.shape[0] == 1:
            array = array[0]
        else:
            raise ValueError("Unexpected analysis array dimensionality.")
    if not np.isfinite(array).all():
        raise TechnicalInvalidError("NONFINITE_ANALYSIS_ARRAY")
    return array


def extract_block_hidden_state(output: Any) -> Any:
    if torch.is_tensor(output):
        return output
    if isinstance(output, (tuple, list)):
        if len(output) == 0:
            raise TypeError("UNSUPPORTED_BLOCK_OUTPUT_STRUCTURE_EMPTY")
        return extract_block_hidden_state(output[0])
    raise TypeError("UNSUPPORTED_BLOCK_OUTPUT_STRUCTURE")


@dataclass
class ForwardHookCapture:
    _captured: Any = None
    _capture_count: int = 0

    def record(self, output: Any) -> None:
        if self._capture_count:
            raise RuntimeError("UNEXPECTED_MULTIPLE_HOOK_CAPTURE")
        self._captured = extract_block_hidden_state(output)
        self._capture_count = 1

    @property
    def value(self) -> Any:
        if self._capture_count == 0:
            raise RuntimeError("HOOK_CAPTURE_MISSING")
        if self._capture_count != 1:
            raise RuntimeError("UNEXPECTED_MULTIPLE_HOOK_CAPTURE")
        return self._captured

    def clear(self) -> None:
        self._captured = None
        self._capture_count = 0


def make_block_output_hook(capture: ForwardHookCapture):
    def hook(module: Any, args: Any, output: Any) -> None:
        capture.record(output)
        return None
    return hook


def block27_pre_final_rmsnorm_hook(capture: ForwardHookCapture):
    return make_block_output_hook(capture)


@contextmanager
def block_output_hook_capture(module: Any, capture: ForwardHookCapture | None = None):
    capture = capture if capture is not None else ForwardHookCapture()
    capture.clear()
    hook = make_block_output_hook(capture)
    handle = module.register_forward_hook(hook)
    try:
        yield capture
    finally:
        handle.remove()


def extract_checkpoint_tensors(
    hidden_states: Sequence[Any],
    block27_pre_final_output: Any,
) -> dict[str, Any]:
    if not isinstance(hidden_states, (tuple, list)):
        raise TypeError("HIDDEN_STATES_SEQUENCE_REQUIRED")
    checkpoint_tensors = {}
    for checkpoint in CHECKPOINT_SPECS:
        if checkpoint.hidden_states_index is None:
            tensor = extract_block_hidden_state(block27_pre_final_output)
        else:
            index = checkpoint.hidden_states_index
            if index >= len(hidden_states):
                raise ProtocolIntegrityError(f"MISSING_HIDDEN_STATE_{checkpoint.name}_{index}")
            tensor = hidden_states[index]
            if not torch.is_tensor(tensor):
                raise TypeError(f"CHECKPOINT_{checkpoint.name}_NOT_TORCH_TENSOR")
        checkpoint_tensors[checkpoint.name] = tensor
    if set(checkpoint_tensors) != set(CHECKPOINT_NAMES):
        raise ProtocolIntegrityError("CHECKPOINT_EXTRACTION_MAPPING_MISMATCH")
    return checkpoint_tensors


def extract_last_token_representations(
    checkpoint_tensors: Mapping[str, Any],
    attention_mask: Any,
) -> dict[str, Any]:
    if set(checkpoint_tensors) != set(CHECKPOINT_NAMES):
        raise ProtocolIntegrityError("CHECKPOINT_TENSOR_SET_MISMATCH")
    indices = last_valid_token_indices(attention_mask)
    return {
        name: select_last_valid_token_at_indices(tensor, indices)
        for name, tensor in checkpoint_tensors.items()
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static-preflight", action="store_true")
    modes.add_argument("--synthetic-preflight", action="store_true")
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
        elif args.synthetic_preflight:
            print(json.dumps(synthetic_preflight(root), ensure_ascii=False, indent=2, sort_keys=True))
        elif args.model_hook_qualification:
            raise PermissionError("EXP023_MODEL_HOOK_QUALIFICATION_NOT_AUTHORIZED_IN_096A")
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
        print(f"EXP023_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
