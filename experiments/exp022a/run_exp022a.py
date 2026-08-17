"""EXP-022A Clean-State Layerwise Readout Transport Diagnosis runner.

Task 094B implements a protocol-faithful runner plus static and synthetic
preflight.  The formal-run path is intentionally fail-closed until a future
authorization artifact is supplied.  This module is import-safe: importing it
does not load a model, tokenizer, controlled prompt text, or hidden-state data.
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
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import torch
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


EXPERIMENT = "EXP-022A"
EXPERIMENT_NAME = "Clean-State Layerwise Readout Transport Diagnosis"
RESULT_SCHEMA_VERSION = "1.0.0"
FROZEN_PREREGISTRATION_SHA256 = (
    "609aab2b3cc96f4ea316b45741b2ae427e682c72c7546c8a9520201f94547698"
)
ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
PREREGISTRATION_PATH = ROOT / "docs" / "experiments" / "EXP-022A-PREREGISTRATION.md"
FREEZE_MANIFEST_PATH = ROOT / "docs" / "experiments" / "EXP-022A-FREEZE-MANIFEST.json"
CANONICAL_RESULT_PATH = EXP_DIR / "results" / "exp022a_results.json"
STATIC_PREFLIGHT_PATH = EXP_DIR / "results" / "runner_static_preflight.json"
FORMAL_AUTHORIZATION_PATH = EXP_DIR / "exp022a_formal_run_authorization.json"
PROMPT_FILE_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
PROMPT_FILE_SHA256 = (
    "72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472"
)
FORMAL_MODEL_NAME = "Qwen/Qwen3-1.7B"
FORMAL_MODEL_SNAPSHOT = "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
FORMAL_MODEL_SNAPSHOT_PATH = (
    Path("D:/AI_Cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots")
    / FORMAL_MODEL_SNAPSHOT
)
FORMAL_MODEL_HOOK_QUALIFICATION_SHA256 = (
    "5f2e82180ccb1381626513758209b060f43e3f70431d08c15a1e74af0fe4ffe2"
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
    "formal_dataset_sha256",
    "model_name",
    "model_snapshot_identity",
    "model_hook_qualification_sha256",
    "canonical_result_path",
    "authorization_created_at_utc",
}
EXP020_FROZEN_CONFIG_PATH = ROOT / "experiments" / "exp020" / "exp020_frozen_config.json"
CLASS_UNIVERSE = ("logic", "causality", "analogy", "definition")
READOUT_CONDITIONS = ("A0", "A1", "A2")
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
    "random_state": 20260812,
}
BOOTSTRAP_SEED = 20260817
BOOTSTRAP_REPLICATES = 10_000


def staging_path_for(canonical_path: Path) -> Path:
    """Return the single staging-path authority for a canonical result path."""
    return canonical_path.with_name(canonical_path.name + ".staging")


STAGING_RESULT_PATH = staging_path_for(CANONICAL_RESULT_PATH)


class ProtocolIntegrityError(RuntimeError):
    """Raised when a frozen authority or implementation invariant is violated."""


class TechnicalInvalidError(RuntimeError):
    """Raised when a computation is technically invalid under the protocol."""


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
    source_semantic_class: str
    variant: str


@dataclass
class SplitDataset:
    """Analysis-ready, text-free split representation."""

    split_id: str
    fit_records: dict[str, tuple[str, ...]]
    eval_records: dict[str, tuple[str, ...]]
    labels: dict[str, str]
    representations: dict[str, dict[str, np.ndarray]]


@dataclass(frozen=True)
class PredictionRow:
    split_id: str
    eval_record_id: str
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
    """Publish JSON through an exclusive staging file without replacing a result.

    The staging path is derived only from ``staging_path_for``.  The final
    canonical file is created with ``os.link``, which atomically fails if the
    destination already exists instead of silently replacing it.
    """
    if path.exists():
        raise FileExistsError(f"Canonical result already exists: {path}")
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
    """Hard-fail if the frozen preregistration has drifted."""
    path = root / PREREGISTRATION_PATH.relative_to(ROOT)
    actual = _sha256(path)
    if actual != FROZEN_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("FROZEN_PREREGISTRATION_SHA_MISMATCH")
    return {
        "path": str(PREREGISTRATION_PATH.relative_to(ROOT)),
        "sha256": actual,
        "status": "FROZEN",
    }


def load_freeze_manifest(root: Path = ROOT) -> dict[str, Any]:
    path = root / FREEZE_MANIFEST_PATH.relative_to(ROOT)
    manifest = _read_json(path)
    if manifest.get("experiment") != EXPERIMENT:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_EXPERIMENT_MISMATCH")
    if manifest.get("status") != "FROZEN":
        raise ProtocolIntegrityError("FREEZE_MANIFEST_NOT_FROZEN")
    if manifest.get("preregistration_sha256") != FROZEN_PREREGISTRATION_SHA256:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_SHA_MISMATCH")
    if manifest.get("implementation_authorized") is not False:
        raise ProtocolIntegrityError("FREEZE_MANIFEST_IMPLEMENTATION_AUTHORIZED_INVALID")
    return manifest


def verify_no_result_collision(root: Path = ROOT) -> None:
    canonical = root / CANONICAL_RESULT_PATH.relative_to(ROOT)
    staging = staging_path_for(canonical)
    if canonical.exists():
        raise ProtocolIntegrityError("EXP022A_CANONICAL_RESULT_ALREADY_EXISTS")
    if staging.exists():
        raise ProtocolIntegrityError("EXP022A_STAGING_RESULT_ALREADY_EXISTS")


def _installed_api_versions() -> dict[str, str]:
    import sklearn

    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "scikit_learn": sklearn.__version__,
    }


def static_preflight(root: Path = ROOT) -> dict[str, Any]:
    """Metadata-only preflight without prompt, model, tokenizer, or tensor access."""
    authority = verify_frozen_authority(root)
    manifest = load_freeze_manifest(root)
    verify_no_result_collision(root)
    if (root / FORMAL_AUTHORIZATION_PATH.relative_to(ROOT)).exists():
        raise ProtocolIntegrityError("EXP022A_FORMAL_AUTHORIZATION_UNEXPECTED")
    versions = _installed_api_versions()
    if versions["scikit_learn"] != "1.9.0":
        raise ProtocolIntegrityError("EXP022A_STATIC_PREFLIGHT_SCIKIT_LEARN_VERSION_MISMATCH")
    runner_sha = _sha256(Path(__file__))
    return {
        "status": "EXP022A_STATIC_PREFLIGHT_PASS",
        "classification": "ENGINEERING_STATIC_PREFLIGHT_ONLY",
        "experiment": EXPERIMENT,
        "frozen_preregistration_sha256": FROZEN_PREREGISTRATION_SHA256,
        "frozen_authority_verified": True,
        "freeze_manifest_verified": True,
        "freeze_manifest": manifest,
        "runner_path": str(Path(__file__).relative_to(ROOT)),
        "runner_sha256": runner_sha,
        "versions": versions,
        "formal_run_authorized": False,
        "canonical_result_present": False,
        "staging_result_present": False,
        "model_loaded": False,
        "tokenizer_loaded": False,
        "controlled_prompt_text_accessed": False,
        "formal_eval_accessed": False,
        "scientific_result_created": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _require_formal_authorization(root: Path) -> None:
    """Fail closed until a future authorization mechanism is implemented."""
    raise PermissionError("FORMAL_RUN_NOT_AUTHORIZED")


def run_formal(
    root: Path = ROOT,
    authorization_path: Path | None = None,
) -> dict[str, Any]:
    """Run the formal production path only when an explicit single-use authorization is supplied."""
    if authorization_path is None:
        verify_frozen_authority(root)
        _require_formal_authorization(root)

    auth_path = Path(authorization_path)
    if not auth_path.is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_FILE_MISSING")
    authorization = _read_json(auth_path)
    _pre_consumption_static_checks(root, authorization, auth_path)

    run_attempt_id = str(uuid.uuid4())
    consumption = _consume_formal_authorization(
        root, authorization, auth_path, run_attempt_id
    )
    try:
        result = _execute_formal_after_consumption(
            root, authorization, consumption, run_attempt_id
        )
        return finalize_formal_result(result, root)
    except Exception as exc:
        _preserve_technical_failure_after_consumption(
            root, authorization, consumption, run_attempt_id, exc
        )
        raise


def exact_binomial_tail(favorable: int, unfavorable: int) -> float:
    """Return P[Binomial(m, 0.5) >= favorable] for paired discordances."""
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


def d_fixed_support(estimate: float, exact_p: float, alpha: float = 0.05) -> bool:
    return estimate < 0 and exact_p <= alpha


def g_refit_support(
    d_fixed_supported: bool,
    estimate: float,
    exact_p: float,
    alpha: float = 0.05,
) -> bool:
    return d_fixed_supported and estimate > 0 and exact_p <= alpha


def cross_split_category(
    supported_a: bool,
    supported_b: bool,
    effect_a: float,
    effect_b: float,
    favorable_sign: int,
) -> str:
    """Classify a primary directional contrast without pooling splits."""
    if supported_a and supported_b:
        return "CROSS_SPLIT_SUPPORTED"

    def sign(value: float) -> int:
        if value == 0:
            return 0
        return 1 if value > 0 else -1

    if supported_a != supported_b:
        unsupported_effect = effect_b if supported_a else effect_a
        unsupported_sign = sign(unsupported_effect)
        if unsupported_sign == favorable_sign or unsupported_sign == 0:
            return "PARTIAL_CONCORDANCE"
        return "SPLIT_HETEROGENEOUS"

    sign_a = sign(effect_a)
    sign_b = sign(effect_b)
    if sign_a != sign_b:
        return "SPLIT_HETEROGENEOUS"
    return "NOT_SUPPORTED"


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
        if len(fit_ids) != 3 or len(eval_ids) != 3:
            raise TechnicalInvalidError("FROZEN_SPLIT_COUNT_MISMATCH")
        if len(set(fit_ids)) != 3 or len(set(eval_ids)) != 3:
            raise TechnicalInvalidError("DUPLICATE_RECORD_ID")
        if set(fit_ids) & set(eval_ids):
            raise TechnicalInvalidError("FIT_EVAL_OVERLAP")
        all_fit_ids.extend(fit_ids)
        all_eval_ids.extend(eval_ids)

    if len(set(all_fit_ids + all_eval_ids)) != 24:
        raise TechnicalInvalidError("RECORD_ID_UNIQUENESS_VIOLATION")

    for record_id, cls in dataset.labels.items():
        if cls not in CLASS_UNIVERSE:
            raise TechnicalInvalidError("UNEXPECTED_SOURCE_CLASS")
        if record_id not in dataset.representations:
            raise TechnicalInvalidError("MISSING_REPRESENTATIONS")

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


def predict_probabilities(
    classifier: LogisticRegression,
    scaler: StandardScaler,
    X: np.ndarray,
) -> np.ndarray:
    try:
        transformed = scaler.transform(X)
        probabilities = classifier.predict_proba(transformed)
    except Exception as exc:
        raise TechnicalInvalidError("CLASSIFIER_PREDICTION_EXCEPTION") from exc
    if not np.isfinite(probabilities).all():
        raise TechnicalInvalidError("NONFINITE_PROBABILITIES")
    if probabilities.shape[1] != len(CLASS_UNIVERSE):
        raise TechnicalInvalidError("INVALID_PROBABILITY_WIDTH")
    if not np.allclose(probabilities.sum(axis=1), 1.0, atol=1e-6):
        raise TechnicalInvalidError("INVALID_PROBABILITY_NORMALIZATION")
    return probabilities


def reorder_probabilities(
    probabilities: np.ndarray,
    classifier_classes: Sequence[Any],
) -> np.ndarray:
    classes = [str(cls) for cls in classifier_classes]
    if set(classes) != set(CLASS_UNIVERSE):
        raise TechnicalInvalidError("CLASSIFIER_CLASS_MAP_MISMATCH")
    indices = [classes.index(cls) for cls in CLASS_UNIVERSE]
    return probabilities[:, indices]


def _build_prediction_rows(
    dataset: SplitDataset,
    checkpoint: str,
    readout_condition: str,
    scaler: StandardScaler,
    classifier: LogisticRegression,
) -> list[PredictionRow]:
    X_eval, eval_ids, true_classes = _stack_records(
        dataset, dataset.eval_records, checkpoint
    )
    probabilities = reorder_probabilities(
        predict_probabilities(classifier, scaler, X_eval),
        list(classifier.classes_),
    )
    rows = []
    for row_index, record_id in enumerate(eval_ids):
        predicted_index = int(np.argmax(probabilities[row_index]))
        predicted_class = CLASS_UNIVERSE[predicted_index]
        rows.append(
            PredictionRow(
                split_id=dataset.split_id,
                eval_record_id=record_id,
                source_semantic_class=dataset.labels[record_id],
                checkpoint=checkpoint,
                readout_condition=readout_condition,
                true_class=true_classes[row_index],
                predicted_class=predicted_class,
                probability_vector=tuple(float(v) for v in probabilities[row_index]),
                correct=predicted_class == true_classes[row_index],
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
    if len(rows) != 12:
        raise TechnicalInvalidError("EXPECTED_TWELVE_EVAL_ROWS")
    true_classes = [row.true_class for row in rows]
    predicted_classes = [row.predicted_class for row in rows]
    recalls = {}
    for cls in CLASS_UNIVERSE:
        class_indices = [i for i, label in enumerate(true_classes) if label == cls]
        if len(class_indices) != 3:
            raise TechnicalInvalidError("EVAL_CLASS_BALANCE_MISMATCH")
        recalls[cls] = sum(predicted_classes[i] == cls for i in class_indices) / 3
    return {
        "balanced_accuracy": float(np.mean(list(recalls.values()))),
        "accuracy": accuracy(true_classes, predicted_classes),
        "per_class_recall": {cls: float(value) for cls, value in recalls.items()},
    }


def correctness_by_class(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
    checkpoint: str,
    readout_condition: str,
) -> dict[str, list[int]]:
    row_map = {
        (row.eval_record_id, row.checkpoint, row.readout_condition): row.correct
        for row in rows
    }
    output = {}
    for cls in CLASS_UNIVERSE:
        values = []
        for record_id in dataset.eval_records[cls]:
            values.append(int(row_map[(record_id, checkpoint, readout_condition)]))
        output[cls] = values
    return output


def bootstrap_contrast(
    correct_a_by_class: Mapping[str, Sequence[int]],
    correct_b_by_class: Mapping[str, Sequence[int]],
    *,
    seed: int = BOOTSTRAP_SEED,
    resamples: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    """Class-stratified held-out record resampling, with one fresh fixed stream."""
    rng = np.random.Generator(np.random.PCG64(seed))
    class_means_a = np.zeros(resamples, dtype=np.float64)
    class_means_b = np.zeros(resamples, dtype=np.float64)
    for cls in CLASS_UNIVERSE:
        values_a = np.asarray(correct_a_by_class[cls], dtype=np.float64)
        values_b = np.asarray(correct_b_by_class[cls], dtype=np.float64)
        if values_a.shape[0] != 3 or values_b.shape[0] != 3:
            raise ValueError("Frozen bootstrap requires exactly three EVAL records per class.")
        indices = rng.integers(0, 3, size=(resamples, 3))
        class_means_a += values_a[indices].mean(axis=1)
        class_means_b += values_b[indices].mean(axis=1)
    balanced_a = class_means_a / len(CLASS_UNIVERSE)
    balanced_b = class_means_b / len(CLASS_UNIVERSE)
    distribution = balanced_b - balanced_a
    lower, upper = np.quantile(distribution, [0.025, 0.975], method="linear")
    return {
        "lower": float(lower),
        "upper": float(upper),
        "distribution": distribution.astype(float).tolist(),
        "resamples": resamples,
        "seed": seed,
    }


CONTRASTS = (
    {
        "name": "D_fixed",
        "a_checkpoint": PRIMARY_REFERENCE_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A0",
    },
    {
        "name": "G_refit",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A2",
    },
    {
        "name": "G_scale",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A0",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A1",
    },
    {
        "name": "G_noncal",
        "a_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "a_readout": "A1",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A2",
    },
    {
        "name": "R_refit",
        "a_checkpoint": PRIMARY_REFERENCE_CHECKPOINT,
        "a_readout": "A2",
        "b_checkpoint": PRIMARY_ENDPOINT_CHECKPOINT,
        "b_readout": "A2",
    },
)


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
        for record_index, record_id in enumerate(dataset.eval_records[cls]):
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


def _bootstrap_intervals(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
) -> dict[str, dict[str, Any]]:
    output = {}
    for contrast in CONTRASTS:
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


def _build_split_summary(
    dataset: SplitDataset,
    rows: Sequence[PredictionRow],
    technical_validity: str,
    warnings_list: Sequence[str],
) -> dict[str, Any]:
    metrics = _metrics_for_rows(rows)
    d_estimate = _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A0") - _metric_ba(
        metrics, PRIMARY_REFERENCE_CHECKPOINT, "A0"
    )
    d_favorable, d_unfavorable = _discordance_counts(
        dataset,
        rows,
        (PRIMARY_REFERENCE_CHECKPOINT, "A0"),
        (PRIMARY_ENDPOINT_CHECKPOINT, "A0"),
        favorable_a_correct_b_incorrect=True,
    )
    d_p = exact_binomial_tail(d_favorable, d_unfavorable)
    d_supported = d_fixed_support(d_estimate, d_p)

    g_estimate = _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A2") - _metric_ba(
        metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A0"
    )
    g_favorable, g_unfavorable = _discordance_counts(
        dataset,
        rows,
        (PRIMARY_ENDPOINT_CHECKPOINT, "A0"),
        (PRIMARY_ENDPOINT_CHECKPOINT, "A2"),
        favorable_a_correct_b_incorrect=False,
    )
    g_p = exact_binomial_tail(g_favorable, g_unfavorable)
    g_supported = g_refit_support(d_supported, g_estimate, g_p)

    secondary = {
        "G_scale": _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A1")
        - _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A0"),
        "G_noncal": _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A2")
        - _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A1"),
        "R_refit": _metric_ba(metrics, PRIMARY_ENDPOINT_CHECKPOINT, "A2")
        - _metric_ba(metrics, PRIMARY_REFERENCE_CHECKPOINT, "A2"),
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
            "D_fixed": {
                "estimate": d_estimate,
                "favorable": d_favorable,
                "unfavorable": d_unfavorable,
                "exact_p": d_p,
                "supported": d_supported,
            },
            "G_refit": {
                "estimate": g_estimate,
                "favorable": g_favorable,
                "unfavorable": g_unfavorable,
                "exact_p": g_p,
                "serial_gate": "OPEN" if d_supported else "CLOSED_D_FIXED_NOT_SUPPORTED",
                "supported": g_supported,
            },
        },
        "secondary": {
            "G_scale": secondary["G_scale"],
            "G_noncal": secondary["G_noncal"],
            "R_refit": secondary["R_refit"],
            "post_final_delta": post_final_delta,
        },
        "bootstrap": _bootstrap_intervals(dataset, rows),
        "technical_validity": {"status": technical_validity},
        "warnings": list(warnings_list),
    }


def run_split_analysis(dataset: SplitDataset) -> dict[str, Any]:
    validate_split_dataset(dataset)
    X_ref_fit, _, y_ref_fit = _stack_records(
        dataset, dataset.fit_records, PRIMARY_REFERENCE_CHECKPOINT
    )
    scaler_ref = fit_scaler(X_ref_fit)
    X_ref_fit_scaled = scaler_ref.transform(X_ref_fit)
    classifier_ref, warning_messages = fit_classifier(X_ref_fit_scaled, y_ref_fit)
    warnings_list = list(warning_messages)

    rows: list[PredictionRow] = []
    for checkpoint in CHECKPOINT_NAMES:
        X_fit_checkpoint, _, y_fit_checkpoint = _stack_records(
            dataset, dataset.fit_records, checkpoint
        )
        scaler_a1 = fit_scaler(X_fit_checkpoint)
        X_fit_checkpoint_scaled_a1 = scaler_a1.transform(X_fit_checkpoint)
        classifier_a2, a2_warnings = fit_classifier(
            X_fit_checkpoint_scaled_a1, y_fit_checkpoint
        )
        warnings_list.extend(a2_warnings)

        rows.extend(
            _build_prediction_rows(dataset, checkpoint, "A0", scaler_ref, classifier_ref)
        )
        rows.extend(
            _build_prediction_rows(dataset, checkpoint, "A1", scaler_a1, classifier_ref)
        )
        rows.extend(
            _build_prediction_rows(dataset, checkpoint, "A2", scaler_a1, classifier_a2)
        )

    technical_validity = "VALID_WITH_WARNING" if warnings_list else "VALID"
    summary = _build_split_summary(dataset, rows, technical_validity, warnings_list)
    return {
        "split_id": dataset.split_id,
        "summary": summary,
        "evaluation_rows": [row.to_dict() for row in rows],
        "technical_validity": technical_validity,
        "warnings": warnings_list,
    }


def make_synthetic_split(split_id: str, seed: int) -> SplitDataset:
    """Create deterministic, text-free synthetic arrays for preflight."""
    rng = np.random.default_rng(seed)
    dimension = 8
    reference_means = {cls: rng.normal(size=dimension) * 1.5 for cls in CLASS_UNIVERSE}
    final_means = {cls: rng.normal(size=dimension) * 2.5 for cls in CLASS_UNIVERSE}

    labels = {}
    representations = {}
    fit_records = {cls: [] for cls in CLASS_UNIVERSE}
    eval_records = {cls: [] for cls in CLASS_UNIVERSE}
    fit_variant, eval_variant = (
        ("original", "paraphrase")
        if split_id.startswith("A_")
        else ("paraphrase", "original")
    )

    for cls in CLASS_UNIVERSE:
        for item_index in range(1, 4):
            fit_id = f"{cls}_{fit_variant}_{item_index:02d}"
            eval_id = f"{cls}_{eval_variant}_{item_index:02d}"
            fit_records[cls].append(fit_id)
            eval_records[cls].append(eval_id)
            labels[fit_id] = cls
            labels[eval_id] = cls

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
        representations=representations,
    )


def synthetic_preflight(root: Path = ROOT) -> dict[str, Any]:
    verify_frozen_authority(root)
    load_freeze_manifest(root)
    verify_no_result_collision(root)
    analyses = {}
    for split_id, seed in (
        ("A_original_fit_paraphrase_eval", 1),
        ("B_paraphrase_fit_original_eval", 2),
    ):
        dataset = make_synthetic_split(split_id, seed)
        analyses[split_id] = run_split_analysis(dataset)

    split_a = analyses["A_original_fit_paraphrase_eval"]["summary"]
    split_b = analyses["B_paraphrase_fit_original_eval"]["summary"]
    cross_split = {
        "D_fixed": cross_split_category(
            split_a["primary"]["D_fixed"]["supported"],
            split_b["primary"]["D_fixed"]["supported"],
            split_a["primary"]["D_fixed"]["estimate"],
            split_b["primary"]["D_fixed"]["estimate"],
            favorable_sign=-1,
        ),
        "G_refit": cross_split_category(
            split_a["primary"]["G_refit"]["supported"],
            split_b["primary"]["G_refit"]["supported"],
            split_a["primary"]["G_refit"]["estimate"],
            split_b["primary"]["G_refit"]["estimate"],
            favorable_sign=1,
        ),
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
            "model_id": "Qwen/Qwen3-1.7B",
            "snapshot": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
            "local_files_only": True,
            "architecture": "Qwen3ForCausalLM",
            "model_type": "qwen3",
            "blocks": 28,
            "hidden_size": 2048,
            "vocab_size": 151936,
        },
        "dataset": {
            "prompt_file_path": str(PROMPT_FILE_PATH.relative_to(ROOT)),
            "prompt_file_sha256": PROMPT_FILE_SHA256,
            "split_count": 2,
            "fit_count_per_split": 12,
            "evaluation_count_per_split": 12,
            "records_per_class_per_split": 3,
        },
        "classes": list(CLASS_UNIVERSE),
        "checkpoints": CHECKPOINT_NAMES,
        "readout_definitions": {
            "A0": "fixed full-FIT reference scaler and reference classifier",
            "A1": "layerwise FIT featurewise scaler recalibration; reference classifier retained",
            "A2": "layerwise FIT scaler and same-family linear classifier refit",
        },
        "splits": {
            "A_original_fit_paraphrase_eval": split_a,
            "B_paraphrase_fit_original_eval": split_b,
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
        "warnings": [
            warning for analysis in analyses.values() for warning in analysis["warnings"]
        ],
        "prompt_text_included": False,
        "hidden_states_included": False,
    }
    validate_result_schema(result)
    return {
        "status": "EXP022A_SYNTHETIC_PREFLIGHT_PASS",
        "experiment": EXPERIMENT,
        "frozen_preregistration_sha256": FROZEN_PREREGISTRATION_SHA256,
        "split_a": {
            "technical_validity": analyses["A_original_fit_paraphrase_eval"][
                "technical_validity"
            ],
            "D_fixed_supported": split_a["primary"]["D_fixed"]["supported"],
            "G_refit_supported": split_a["primary"]["G_refit"]["supported"],
        },
        "split_b": {
            "technical_validity": analyses["B_paraphrase_fit_original_eval"][
                "technical_validity"
            ],
            "D_fixed_supported": split_b["primary"]["D_fixed"]["supported"],
            "G_refit_supported": split_b["primary"]["G_refit"]["supported"],
        },
        "cross_split_synthesis": cross_split,
        "result_schema_validated": True,
        "model_loaded": False,
        "tokenizer_loaded": False,
        "controlled_prompt_text_accessed": False,
        "formal_eval_accessed": False,
        "scientific_result_created": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


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
    if formal:
        if result.get("execution_mode") != "formal-run":
            raise ProtocolIntegrityError("FORMAL_RESULT_EXECUTION_MODE_INVALID")
        if not isinstance(result.get("scientific_status"), str) or not result["scientific_status"]:
            raise ProtocolIntegrityError("FORMAL_RESULT_SCIENTIFIC_STATUS_INVALID")
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
    """Publish an already validated result to the canonical no-overwrite path."""
    canonical = root / CANONICAL_RESULT_PATH.relative_to(ROOT)
    return atomic_write_json(canonical, result)


def finalize_formal_result(result: Mapping[str, Any], root: Path = ROOT) -> dict[str, str]:
    """Run the production formal-result finalization pipeline in fixed order."""
    validate_result_schema(result, formal=True)
    verify_no_result_collision(root)
    return atomic_publish_validated_result(result, root)


def load_split_definitions(root: Path = ROOT) -> list[dict[str, Any]]:
    config = _read_json(root / EXP020_FROZEN_CONFIG_PATH.relative_to(ROOT))
    return config["dataset"]["splits"]


def validate_production_records(
    records: Sequence[Mapping[str, Any]],
    split_definitions: Sequence[Mapping[str, Any]],
) -> list[RecordMeta]:
    if len(records) != 24:
        raise ProtocolIntegrityError("PRODUCTION_RECORD_COUNT_MISMATCH")
    for record in records:
        for field in ("id", "group", "variant_type", "text"):
            if field not in record:
                raise ProtocolIntegrityError(f"PRODUCTION_RECORD_MISSING_{field.upper()}")
        if not isinstance(record["id"], str) or not record["id"].strip():
            raise ProtocolIntegrityError("PRODUCTION_RECORD_ID_INVALID")
        if not isinstance(record["group"], str) or not record["group"].strip():
            raise ProtocolIntegrityError("PRODUCTION_RECORD_GROUP_INVALID")
        if not isinstance(record["variant_type"], str) or not record["variant_type"].strip():
            raise ProtocolIntegrityError("PRODUCTION_RECORD_VARIANT_INVALID")
        if not isinstance(record["text"], str) or not record["text"].strip():
            raise ProtocolIntegrityError("PRODUCTION_RECORD_MISSING_TEXT")
    metas = [
        RecordMeta(
            record_id=str(record["id"]),
            source_semantic_class=str(record["group"]),
            variant=str(record["variant_type"]),
        )
        for record in records
    ]
    ids = [meta.record_id for meta in metas]
    if len(set(ids)) != 24:
        raise ProtocolIntegrityError("PRODUCTION_RECORD_ID_DUPLICATE")
    if {meta.source_semantic_class for meta in metas} != set(CLASS_UNIVERSE):
        raise ProtocolIntegrityError("PRODUCTION_CLASS_UNIVERSE_MISMATCH")
    if {meta.variant for meta in metas} != {"original", "paraphrase"}:
        raise ProtocolIntegrityError("PRODUCTION_VARIANT_ROLE_MISMATCH")

    for cls in CLASS_UNIVERSE:
        for variant in ("original", "paraphrase"):
            count = sum(
                1
                for meta in metas
                if meta.source_semantic_class == cls and meta.variant == variant
            )
            if count != 3:
                raise ProtocolIntegrityError("PRODUCTION_VARIANT_CLASS_COUNT_MISMATCH")

    for split in split_definitions:
        fit_ids = [
            record_id
            for class_ids in split["fit_ids"].values()
            for record_id in class_ids
        ]
        eval_ids = [
            record_id
            for class_ids in split["evaluation_ids"].values()
            for record_id in class_ids
        ]
        if len(fit_ids) != 12 or len(eval_ids) != 12:
            raise ProtocolIntegrityError("PRODUCTION_SPLIT_COUNT_MISMATCH")
        if set(fit_ids) & set(eval_ids):
            raise ProtocolIntegrityError("PRODUCTION_SPLIT_OVERLAP")
        expected_fit_variant = "original" if split["id"].startswith("A_") else "paraphrase"
        expected_eval_variant = "paraphrase" if split["id"].startswith("A_") else "original"
        for record_id in fit_ids:
            meta = next(meta for meta in metas if meta.record_id == record_id)
            if meta.variant != expected_fit_variant:
                raise ProtocolIntegrityError("PRODUCTION_FIT_VARIANT_MISMATCH")
        for record_id in eval_ids:
            meta = next(meta for meta in metas if meta.record_id == record_id)
            if meta.variant != expected_eval_variant:
                raise ProtocolIntegrityError("PRODUCTION_EVAL_VARIANT_MISMATCH")
    return metas


def load_production_dataset(
    prompt_path: Path,
    split_definitions: Sequence[Mapping[str, Any]],
) -> list[RecordMeta]:
    records = _read_json(prompt_path)
    return validate_production_records(records, split_definitions)


def _runner_sha256() -> str:
    return _sha256(Path(__file__))


def _repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        text=True,
    ).strip()


def _tracked_tree_clean(root: Path = ROOT) -> bool:
    completed = subprocess.run(
        ["git", "diff", "--quiet"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if completed.returncode not in (0, 1):
        raise ProtocolIntegrityError("FORMAL_GIT_TRACKED_TREE_STATUS_UNAVAILABLE")
    return completed.returncode == 0


def _staging_empty(root: Path = ROOT) -> bool:
    completed = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=root,
        text=True,
        capture_output=True,
    )
    if completed.returncode not in (0, 1):
        raise ProtocolIntegrityError("FORMAL_GIT_STAGING_STATUS_UNAVAILABLE")
    return completed.returncode == 0


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _is_git_commit(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{40}", value) is not None


def _validate_formal_authorization(
    authorization: Mapping[str, Any],
    root: Path = ROOT,
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
    if not _is_sha256(authorization["formal_dataset_sha256"]):
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
        "formal_dataset_sha256": PROMPT_FILE_SHA256,
        "model_name": FORMAL_MODEL_NAME,
        "model_snapshot_identity": FORMAL_MODEL_SNAPSHOT,
        "model_hook_qualification_sha256": FORMAL_MODEL_HOOK_QUALIFICATION_SHA256,
        "canonical_result_path": canonical_path,
    }
    for field, expected in bindings.items():
        if authorization[field] != expected:
            raise ProtocolIntegrityError(
                f"FORMAL_AUTHORIZATION_BINDING_MISMATCH_{field.upper()}"
            )
    return authorization


def _verify_model_hook_qualification_artifact(root: Path = ROOT) -> dict[str, Any]:
    path = root / "experiments" / "exp022a" / "engineering" / "model_hook_qualification.json"
    actual = _sha256(path)
    if actual != FORMAL_MODEL_HOOK_QUALIFICATION_SHA256:
        raise ProtocolIntegrityError("MODEL_HOOK_QUALIFICATION_SHA_MISMATCH")
    return {
        "path": str(path.relative_to(ROOT)),
        "sha256": actual,
    }


def _pre_consumption_static_checks(
    root: Path,
    authorization: Mapping[str, Any],
    authorization_path: Path,
) -> None:
    _validate_formal_authorization(authorization, root)
    if not _tracked_tree_clean(root):
        raise ProtocolIntegrityError("FORMAL_REPOSITORY_TRACKED_TREE_DIRTY")
    if not _staging_empty(root):
        raise ProtocolIntegrityError("FORMAL_REPOSITORY_STAGING_NOT_EMPTY")
    verify_frozen_authority(root)
    _verify_model_hook_qualification_artifact(root)
    verify_no_result_collision(root)
    if not FORMAL_MODEL_SNAPSHOT_PATH.is_dir():
        raise ProtocolIntegrityError("FORMAL_MODEL_SNAPSHOT_UNAVAILABLE")


def _consumption_path_for(root: Path, authorization_sha256: str) -> Path:
    return (
        root
        / AUTHORIZATION_CONSUMPTION_DIR.relative_to(ROOT)
        / f"{authorization_sha256}.json"
    )


def _consume_formal_authorization(
    root: Path,
    authorization: Mapping[str, Any],
    authorization_path: Path,
    run_attempt_id: str,
) -> dict[str, Any]:
    authorization_sha256 = _sha256(authorization_path)
    record_path = _consumption_path_for(root, authorization_sha256)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": authorization_sha256,
        "run_attempt_id": run_attempt_id,
        "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": authorization["authorized_repository_commit"],
        "runner_sha256": authorization["authorized_runner_sha256"],
        "frozen_preregistration_sha256": authorization["frozen_preregistration_sha256"],
        "formal_dataset_sha256": authorization["formal_dataset_sha256"],
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
        "authorization_sha256": authorization_sha256,
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


def _preserve_technical_failure_after_consumption(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
    exc: Exception,
) -> None:
    """Durably record a consumed formal attempt that ended before publication."""
    record_path = _technical_failure_evidence_path_for(root, run_attempt_id)
    record_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "classification": "FORMAL_RUN_TECHNICAL_FAILURE_EVIDENCE",
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": consumption["authorization_sha256"],
        "consumption_record_path": consumption["consumption_record_path"],
        "run_attempt_id": run_attempt_id,
        "attempt_status": "TECHNICALLY_INVALID",
        "result_status": "NO_SCIENTIFIC_RESULT",
        "scientific_status": "NOT_OBSERVED",
        "technical_validity": {"status": "TECHNICALLY_INVALID"},
        "failure": {
            "exception_type": type(exc).__name__,
            "message": str(exc),
        },
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "prompt_text_included": False,
        "hidden_states_included": False,
    }
    payload = json.dumps(
        record, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
    ) + "\n"
    try:
        fd = os.open(str(record_path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc2:
        raise ProtocolIntegrityError(
            "TECHNICAL_FAILURE_EVIDENCE_ALREADY_EXISTS"
        ) from exc2
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _verify_formal_dataset_identity(root: Path = ROOT) -> dict[str, Any]:
    path = root / PROMPT_FILE_PATH.relative_to(ROOT)
    actual = _sha256(path)
    if actual != PROMPT_FILE_SHA256:
        raise ProtocolIntegrityError("FORMAL_DATASET_SHA_MISMATCH")
    return {
        "path": str(PROMPT_FILE_PATH.relative_to(ROOT)),
        "sha256": actual,
    }


def _load_formal_records(root: Path = ROOT) -> tuple[list[Mapping[str, Any]], list[RecordMeta]]:
    path = root / PROMPT_FILE_PATH.relative_to(ROOT)
    records = _read_json(path)
    split_definitions = load_split_definitions(root)
    return records, validate_production_records(records, split_definitions)


def _load_formal_runtime(root: Path = ROOT) -> tuple[Any, Any, torch.device]:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(
        str(FORMAL_MODEL_SNAPSHOT_PATH),
        local_files_only=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(FORMAL_MODEL_SNAPSHOT_PATH),
        dtype=torch.float16,
        local_files_only=True,
    )
    _validate_formal_model_architecture(model)
    device = torch.device("cuda:0")
    model.to(device)
    model.eval()
    torch.set_grad_enabled(False)
    return tokenizer, model, device


def _validate_formal_model_architecture(model: Any) -> None:
    """Reject a runtime model that does not match the qualified EXP-022A identity."""
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


def _tokenize_formal_record(
    tokenizer: Any,
    text: str,
    device: torch.device,
) -> tuple[torch.Tensor, torch.Tensor]:
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
        record_id = str(record["id"])
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
    split_definitions = load_split_definitions(root)
    meta_by_id = {meta.record_id: meta for meta in metas}
    datasets: dict[str, SplitDataset] = {}
    for split in split_definitions:
        fit_ids = [
            record_id
            for class_ids in split["fit_ids"].values()
            for record_id in class_ids
        ]
        eval_ids = [
            record_id
            for class_ids in split["evaluation_ids"].values()
            for record_id in class_ids
        ]
        all_ids = fit_ids + eval_ids
        fit_records = {
            cls: tuple(rid for rid in fit_ids if meta_by_id[rid].source_semantic_class == cls)
            for cls in CLASS_UNIVERSE
        }
        eval_records = {
            cls: tuple(rid for rid in eval_ids if meta_by_id[rid].source_semantic_class == cls)
            for cls in CLASS_UNIVERSE
        }
        datasets[split["id"]] = SplitDataset(
            split_id=split["id"],
            fit_records=fit_records,
            eval_records=eval_records,
            labels={rid: meta_by_id[rid].source_semantic_class for rid in all_ids},
            representations={rid: dict(representations[rid]) for rid in all_ids},
        )
    return datasets


def _build_formal_result(
    root: Path,
    authorization: Mapping[str, Any],
    consumption: Mapping[str, Any],
    run_attempt_id: str,
    dataset_identity: Mapping[str, Any],
    records: Sequence[Mapping[str, Any]],
    metas: Sequence[RecordMeta],
    analyses: Mapping[str, dict[str, Any]],
) -> dict[str, Any]:
    split_a = analyses["A_original_fit_paraphrase_eval"]["summary"]
    split_b = analyses["B_paraphrase_fit_original_eval"]["summary"]
    cross_split = {
        "D_fixed": cross_split_category(
            split_a["primary"]["D_fixed"]["supported"],
            split_b["primary"]["D_fixed"]["supported"],
            split_a["primary"]["D_fixed"]["estimate"],
            split_b["primary"]["D_fixed"]["estimate"],
            favorable_sign=-1,
        ),
        "G_refit": cross_split_category(
            split_a["primary"]["G_refit"]["supported"],
            split_b["primary"]["G_refit"]["supported"],
            split_a["primary"]["G_refit"]["estimate"],
            split_b["primary"]["G_refit"]["estimate"],
            favorable_sign=1,
        ),
    }
    analysis_warnings = [
        warning for analysis in analyses.values() for warning in analysis["warnings"]
    ]
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
            "prompt_file_path": str(PROMPT_FILE_PATH.relative_to(ROOT)),
            "prompt_file_sha256": dataset_identity["sha256"],
            "split_count": 2,
            "fit_count_per_split": 12,
            "evaluation_count_per_split": 12,
            "records_per_class_per_split": 3,
        },
        "classes": list(CLASS_UNIVERSE),
        "checkpoints": CHECKPOINT_NAMES,
        "readout_definitions": {
            "A0": "fixed full-FIT reference scaler and reference classifier",
            "A1": "layerwise FIT featurewise scaler recalibration; reference classifier retained",
            "A2": "layerwise FIT scaler and same-family linear classifier refit",
        },
        "splits": {
            "A_original_fit_paraphrase_eval": split_a,
            "B_paraphrase_fit_original_eval": split_b,
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
            "model_hook_qualification_sha256": FORMAL_MODEL_HOOK_QUALIFICATION_SHA256,
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
) -> dict[str, Any]:
    dataset_identity = _verify_formal_dataset_identity(root)
    records, metas = _load_formal_records(root)
    tokenizer, model, device = _load_formal_runtime(root)
    representations = _extract_formal_representations(
        root, tokenizer, model, device, records
    )
    datasets = _build_formal_split_datasets(root, records, metas, representations)
    analyses = {
        split_id: run_split_analysis(dataset)
        for split_id, dataset in datasets.items()
    }
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
    """Return per-record last valid token indices.

    NumPy input returns ``list[int]``. Torch input remains on-device and
    returns a one-dimensional long tensor of indices.
    """
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
        index_tensor = indices.to(
            device=hidden_states.device, dtype=torch.long
        ).reshape(-1)
    else:
        index_tensor = torch.as_tensor(
            indices, dtype=torch.long, device=hidden_states.device
        ).reshape(-1)

    if hidden_states.ndim == 2:
        if index_tensor.numel() != 1:
            raise ValueError(
                "Two-dimensional hidden states require exactly one valid-token index."
            )
        if hidden_states.shape[0] == 0:
            raise ValueError("Hidden-state sequence dimension must be nonempty.")
        token_index = index_tensor[0]
        if bool(token_index < 0) or bool(token_index >= hidden_states.shape[0]):
            raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
        return hidden_states[token_index]

    if hidden_states.shape[0] == 0:
        raise ValueError("Hidden-state batch dimension must be nonempty.")
    if index_tensor.numel() != hidden_states.shape[0]:
        raise ValueError("Valid-token index count must match hidden-state batch size.")
    if bool(torch.any(index_tensor < 0)) or bool(
        torch.any(index_tensor >= hidden_states.shape[1])
    ):
        raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
    batch_indices = torch.arange(
        hidden_states.shape[0], dtype=torch.long, device=hidden_states.device
    )
    return hidden_states[batch_indices, index_tensor]


def _select_last_valid_token_numpy(hidden_states: Any, indices: Any) -> np.ndarray:
    states = np.asarray(hidden_states, dtype=np.float32)
    if states.ndim not in (2, 3):
        raise ValueError("Hidden states must be two- or three-dimensional.")
    index_list = _indices_to_python_list(indices)

    if states.ndim == 2:
        if len(index_list) != 1:
            raise ValueError(
                "Two-dimensional hidden states require exactly one valid-token index."
            )
        token_index = index_list[0]
        if token_index < 0 or token_index >= states.shape[0]:
            raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
        return states[token_index, :]

    if states.shape[0] != len(index_list):
        raise ValueError("Valid-token index count must match hidden-state batch size.")
    if states.shape[0] == 0:
        raise ValueError("Hidden-state batch dimension must be nonempty.")
    for token_index in index_list:
        if token_index < 0 or token_index >= states.shape[1]:
            raise ValueError("Valid-token index is outside hidden-state sequence bounds.")
    return np.stack(
        [
            states[batch_index, token_index, :]
            for batch_index, token_index in enumerate(index_list)
        ]
    )


def select_last_valid_token(hidden_states: Any, attention_mask: Any) -> Any:
    """Select each record's last valid token from hidden states.

    Torch selection stays in torch before any CPU conversion. NumPy input
    retains the original NumPy selection behavior.
    """
    indices = last_valid_token_indices(attention_mask)
    return select_last_valid_token_at_indices(hidden_states, indices)


def select_last_valid_token_at_indices(hidden_states: Any, indices: Any) -> Any:
    """Select hidden-state rows using already-derived valid-token indices."""
    if torch.is_tensor(hidden_states):
        return _select_last_valid_token_torch(hidden_states, indices)
    return _select_last_valid_token_numpy(hidden_states, indices)


def to_float32_analysis_array(value: Any, expected_ndim: int | None = None) -> np.ndarray:
    """Convert a torch tensor or NumPy-compatible value to finite float32 analysis data."""
    if torch.is_tensor(value):
        if value.dtype.is_complex:
            raise TypeError("Complex tensors are not valid analysis arrays.")
        array = np.asarray(value.detach().cpu().numpy(), dtype=np.float32)
    else:
        array = np.asarray(value, dtype=np.float32)
    if expected_ndim is not None and array.ndim != expected_ndim:
        raise ValueError(
            f"Analysis array has dimension {array.ndim}, expected {expected_ndim}."
        )
    if not np.isfinite(array).all():
        raise ValueError("Analysis array contains non-finite values.")
    return array


def extract_block_hidden_state(output: Any) -> Any:
    """Extract a decoder-block hidden-state tensor from a supported output shape."""
    if torch.is_tensor(output):
        return output
    if isinstance(output, (tuple, list)):
        if len(output) == 0:
            raise TypeError("UNSUPPORTED_BLOCK_OUTPUT_STRUCTURE_EMPTY")
        return extract_block_hidden_state(output[0])
    raise TypeError("UNSUPPORTED_BLOCK_OUTPUT_STRUCTURE")


@dataclass
class ForwardHookCapture:
    """Explicit per-forward capture container for decoder-block outputs."""

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
    """Return a non-mutating forward hook that records decoder-block output."""

    def hook(module: Any, args: Any, output: Any) -> None:
        capture.record(output)
        return None

    return hook


def block27_pre_final_rmsnorm_hook(capture: ForwardHookCapture):
    """Return the block27 pre-final-RMSNorm forward hook factory."""
    return make_block_output_hook(capture)


@contextmanager
def block_output_hook_capture(module: Any, capture: ForwardHookCapture | None = None):
    """Register, capture, and guaranteed-remove a forward hook."""
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
    """Map production model hidden states and the block27 hook output to checkpoint names."""
    if not isinstance(hidden_states, (tuple, list)):
        raise TypeError("HIDDEN_STATES_SEQUENCE_REQUIRED")

    checkpoint_tensors: dict[str, Any] = {}
    for checkpoint in CHECKPOINT_SPECS:
        if checkpoint.hidden_states_index is None:
            tensor = extract_block_hidden_state(block27_pre_final_output)
        else:
            index = checkpoint.hidden_states_index
            if index >= len(hidden_states):
                raise ProtocolIntegrityError(
                    f"MISSING_HIDDEN_STATE_{checkpoint.name}_{index}"
                )
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
    """Select each checkpoint tensor using the same per-record valid-token indices."""
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
        elif args.formal_run:
            authorization_path = (
                Path(args.authorization_file).resolve()
                if args.authorization_file
                else None
            )
            run_formal(root, authorization_path)
    except PermissionError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except (ProtocolIntegrityError, TechnicalInvalidError) as exc:
        print(f"EXP022A_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
