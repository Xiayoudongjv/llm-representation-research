#!/usr/bin/env python3
"""EXP-028 paired-information runner.

This module implements the frozen EXP-028 scientific contract as an
engineering surface. Importing or running the synthetic/static modes does not
load a real model and does not access real FIT/DIAG/EVAL content.

Modes:

--static-preflight
--synthetic-qualification
--formal-run

Formal-run mode is authorization-gated and must not be invoked by Task 103D.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
ENGINEERING_DIR = EXP_DIR / "engineering"
CONFIG_PATH = EXP_DIR / "exp028_frozen_config.json"
BINDING_PATH = EXP_DIR / "exp028_authority_binding.json"
RESULT_PATH = EXP_DIR / "results" / "exp028_results.json"
AUTHORIZATION_PATH = EXP_DIR / "exp028_formal_run_authorization.json"
CONSUMPTION_DIR = EXP_DIR / "results" / "authorization_consumption"
QUALIFICATION_PATH = ENGINEERING_DIR / "exp028_runner_synthetic_qualification.json"
BOOTSTRAP_SEED = 20260819
BOOTSTRAP_REPLICATES = 5000

_STATIC_FLAG = "--static-preflight"
_SYNTHETIC_FLAG = "--synthetic-qualification"
_FORMAL_FLAG = "--formal-run"
_REPO_ROOT_FLAG = "--repo-root"
_AUTHORIZATION_FILE_FLAG = "--authorization-file"

if str(EXP_DIR) not in sys.path:
    sys.path.insert(0, str(EXP_DIR))

import validate_exp028_preregistration as design_validator
import validate_exp028_result as result_validator


class Exp028ProtocolIntegrityError(RuntimeError):
    """Raised when an EXP-028 frozen authority or lifecycle invariant fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def json_safe(value: Any) -> Any:
    """Convert nested NumPy/tuple/path values to JSON-safe primitives."""
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    return value


def atomic_write_json(path: Path, payload: Any) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(json_safe(payload), handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return sha256_file(path)


def atomic_write_json_exclusive(path: Path, payload: Any) -> str:
    path = Path(path)
    if path.exists():
        raise Exp028ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")
    return atomic_write_json(path, payload)


def repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def frozen_config(root: Path = ROOT) -> dict[str, Any]:
    return read_json(root / CONFIG_PATH)


def authority_binding(root: Path = ROOT) -> dict[str, Any]:
    return read_json(root / BINDING_PATH)


def _load_frozen_authorities(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any]]:
    config = frozen_config(root)
    errors = design_validator.validate(config)
    if errors:
        raise Exp028ProtocolIntegrityError(f"EXP028_PREREGISTRATION_INVALID_{errors}")
    binding = authority_binding(root)
    expected_binding_hash = (config.get("authority_binding") or {}).get("sha256")
    actual_binding_hash = sha256_file(root / BINDING_PATH)
    if expected_binding_hash and expected_binding_hash.casefold() != actual_binding_hash.casefold():
        raise Exp028ProtocolIntegrityError("EXP028_AUTHORITY_BINDING_HASH_DRIFT")
    return config, binding


def _model_authority_fields(model: Mapping[str, Any]) -> tuple[str, ...]:
    return (
        "model_id",
        "model_family",
        "model_class",
        "model_type",
        "hidden_size",
        "num_hidden_layers",
    )


def verify_model_authorities(root: Path = ROOT) -> dict[str, Any]:
    """Fail closed on model identity or carrier authority drift."""
    config, binding = _load_frozen_authorities(root)
    models = binding.get("models", {})
    expected_names = ["Qwen", "OLMo", "Llama"]
    if set(models) != set(expected_names):
        raise Exp028ProtocolIntegrityError("EXP028_MODEL_SET_MISMATCH")
    verified = {}
    for name in expected_names:
        frozen_model = config["models"].get(name)
        binding_model = models.get(name)
        if not frozen_model or not binding_model:
            raise Exp028ProtocolIntegrityError(f"EXP028_MISSING_MODEL_{name}")
        for field in _model_authority_fields(frozen_model):
            if frozen_model.get(field) != binding_model.get(field):
                raise Exp028ProtocolIntegrityError(f"EXP028_MODEL_AUTHORITY_MISMATCH_{name}_{field}")
        for field in ("layer_indices", "tokenizer_class", "runtime_dtype"):
            if binding_model.get(field) is None:
                raise Exp028ProtocolIntegrityError(f"EXP028_MISSING_BINDING_FIELD_{name}_{field}")
        verified[name] = {
            "model_id": binding_model.get("model_id"),
            "model_source": binding_model.get("model_source") or binding_model.get("model_revision"),
            "model_class": binding_model.get("model_class"),
            "hidden_size": binding_model.get("hidden_size"),
            "num_hidden_layers": binding_model.get("num_hidden_layers"),
            "layer_indices": binding_model.get("layer_indices"),
        }
    carrier = binding.get("carrier_semantics", {})
    if carrier.get("api") != "FORWARD_HOOK_DECODER_BLOCK_OUTPUT":
        raise Exp028ProtocolIntegrityError("EXP028_CARRIER_API_MISMATCH")
    if carrier.get("forbidden_carrier") != "outputs.hidden_states[-1]":
        raise Exp028ProtocolIntegrityError("EXP028_CARRIER_FORBIDDEN_MISMATCH")
    for name in expected_names:
        primary = carrier.get(f"{name}_primary_deep_checkpoint")
        if not isinstance(primary, str) or not primary:
            raise Exp028ProtocolIntegrityError(f"EXP028_CARRIER_CHECKPOINT_MISSING_{name}")
    return {
        "models": verified,
        "carrier_semantics": carrier,
        "authority_binding_sha256": sha256_file(root / BINDING_PATH),
        "frozen_config_sha256": sha256_file(root / CONFIG_PATH),
    }


def verify_exp028_authorities(root: Path = ROOT) -> dict[str, Any]:
    model_authority = verify_model_authorities(root)
    config = frozen_config(root)
    formal = config.get("formal_run_policy", {})
    if formal.get("formal_authorization_created") is not False:
        raise Exp028ProtocolIntegrityError("EXP028_FORMAL_POLICY_STATE_UNEXPECTED")
    for forbidden in (EXP_DIR / "results", EXP_DIR / "exp028_formal_run_authorization.json", EXP_DIR / "exp028_results.json"):
        if forbidden.exists():
            raise Exp028ProtocolIntegrityError(f"EXP028_FORBIDDEN_ARTIFACT_PRESENT_{forbidden.name}")
    return {
        "repository_commit": repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "frozen_config_sha256": model_authority["frozen_config_sha256"],
        "authority_binding_sha256": model_authority["authority_binding_sha256"],
        "models": model_authority["models"],
        "carrier_semantics": model_authority["carrier_semantics"],
    }


def verify_no_result_collision(result_path: Path = RESULT_PATH) -> None:
    if result_path.exists():
        raise Exp028ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")


# ---------------------------------------------------------------------------
# Fresh panel interface
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKC", text)
    text = text.strip()
    parts = text.split()
    return " ".join(parts)


def normalized_text_hash(text: str) -> str:
    return sha256_string(normalize_text(text))


def validate_fresh_panel(
    panel: Mapping[str, Any],
    prior_authorities: Sequence[Mapping[str, str]] | None = None,
) -> list[str]:
    """Validate a fresh EXP-028 panel without using real scientific items."""
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    prior_authorities = list(prior_authorities or [])
    check(panel.get("schema_version") == "1.0.0", "panel_schema_version")
    check(panel.get("experiment") == "EXP-028", "panel_experiment")
    items = panel.get("items", [])
    check(isinstance(items, list) and items, "panel_items")
    if not isinstance(items, list):
        return errors

    seen_hashes: set[str] = set()
    seen_family_ids: set[str] = set()
    expected_classes = {"logic", "causality", "analogy", "definition"}
    expected_conditions = {
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
    }
    splits = {"FIT", "DIAGNOSTIC", "EVAL"}
    seen_conditions: set[str] = set()
    seen_splits: set[str] = set()
    prior_hashes = {auth.get("sha256") for auth in prior_authorities if auth.get("sha256")}
    prior_family_ids = {auth.get("source_family_id") for auth in prior_authorities if auth.get("source_family_id")}

    for idx, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"item_{idx}_not_mapping")
            continue
        raw = item.get("raw_text")
        check(isinstance(raw, str) and bool(raw), f"item_{idx}_raw_text")
        if isinstance(raw, str):
            text_hash = normalized_text_hash(raw)
            if text_hash in seen_hashes:
                errors.append(f"duplicate_normalized_raw_text_{idx}")
            seen_hashes.add(text_hash)
            if text_hash in prior_hashes:
                errors.append(f"prior_panel_collision_{idx}")
        family_id = item.get("source_family_id")
        if family_id is not None:
            if family_id in seen_family_ids:
                errors.append(f"duplicate_source_family_id_{idx}")
            seen_family_ids.add(family_id)
            if family_id in prior_family_ids:
                errors.append(f"prior_source_family_reuse_{idx}")
        condition = item.get("condition")
        check(condition in expected_conditions, f"item_{idx}_condition")
        if condition in expected_conditions:
            seen_conditions.add(condition)
        semantic_class = item.get("semantic_class")
        check(semantic_class in expected_classes, f"item_{idx}_semantic_class")
        split = item.get("split")
        check(split in splits, f"item_{idx}_split")
        if split in splits:
            seen_splits.add(split)

    check(seen_conditions == expected_conditions, "panel_condition_coverage")
    check(seen_splits == splits, "panel_split_coverage")
    for cls in expected_classes:
        for split in splits:
            count = sum(
                1
                for item in items
                if item.get("semantic_class") == cls and item.get("split") == split
            )
            check(count >= 1, f"panel_allocation_missing_{cls}_{split}")
    check(panel.get("frozen") is True, "panel_not_frozen")
    return errors


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

def _as_float_matrix(value: Any, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    if arr.ndim != 2:
        raise Exp028ProtocolIntegrityError(f"{name}_MUST_BE_2D")
    if not np.isfinite(arr).all():
        raise Exp028ProtocolIntegrityError(f"{name}_NONFINITE")
    return arr


def _column_mean(arr: np.ndarray) -> np.ndarray:
    return arr.mean(axis=0)


def _column_var_pop(arr: np.ndarray) -> np.ndarray:
    return np.mean((arr - _column_mean(arr)) ** 2, axis=0)


def _column_cov_pop(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    return np.mean((target - _column_mean(target)) * (source - _column_mean(source)), axis=0)


def apply_t0(target: Any) -> np.ndarray:
    return _as_float_matrix(target, "T0_TARGET")


def apply_t1_fit(source: Any, target: Any) -> tuple[np.ndarray, dict[str, Any]]:
    source = _as_float_matrix(source, "T1_SOURCE")
    target = _as_float_matrix(target, "T1_TARGET")
    if source.shape != target.shape:
        raise Exp028ProtocolIntegrityError("T1_SHAPE_MISMATCH")
    mu_s = _column_mean(source)
    sigma_s = np.sqrt(_column_var_pop(source))
    mu_t = _column_mean(target)
    sigma_t = np.sqrt(_column_var_pop(target))
    if not np.isfinite(mu_s).all() or not np.isfinite(mu_t).all():
        raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_NONFINITE_MOMENT")
    if np.any(sigma_s <= 0) or not np.isfinite(sigma_s).all():
        raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_SOURCE_SIGMA")
    if np.any(sigma_t <= 0) or not np.isfinite(sigma_t).all():
        raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_TARGET_SIGMA")
    transformed = ((target - mu_t) / sigma_t) * sigma_s + mu_s
    if not np.isfinite(transformed).all():
        raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_NONFINITE_T1")
    metadata = {
        "source_mean": mu_s,
        "source_std": sigma_s,
        "target_mean": mu_t,
        "target_std": sigma_t,
        "orientation": "target_representation_to_source_measurement_frame",
        "fit_only": True,
    }
    return transformed, metadata


def apply_t2_fit(source: Any, target: Any) -> tuple[np.ndarray, dict[str, Any]]:
    """Fit and apply coordinatewise affine OLS, target -> source frame."""
    source = _as_float_matrix(source, "T2_SOURCE")
    target = _as_float_matrix(target, "T2_TARGET")
    if source.shape != target.shape:
        raise Exp028ProtocolIntegrityError("T2_SHAPE_MISMATCH")
    n_coords = source.shape[1]
    a = np.zeros(n_coords, dtype=np.float64)
    b = np.zeros(n_coords, dtype=np.float64)
    for k in range(n_coords):
        src = source[:, k]
        tgt = target[:, k]
        var_t = float(np.mean((tgt - np.mean(tgt)) ** 2))
        if not np.isfinite(var_t) or var_t <= 0.0:
            raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_TARGET_VARIANCE")
        cov = float(np.mean((tgt - np.mean(tgt)) * (src - np.mean(src))))
        if not np.isfinite(cov):
            raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_NONFINITE_COVARIANCE")
        a_k = cov / var_t
        b_k = float(np.mean(src)) - a_k * float(np.mean(tgt))
        if not np.isfinite(a_k) or not np.isfinite(b_k):
            raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_NONFINITE_COEFFICIENT")
        a[k] = a_k
        b[k] = b_k
    transformed = target * a + b
    if not np.isfinite(transformed).all():
        raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_NONFINITE_T2")
    metadata = {
        "a": a,
        "b": b,
        "fit_only": True,
        "label_free": True,
        "cross_coordinate_mixing": False,
        "hyperparameter_search": False,
        "task_loss_optimization": False,
    }
    return transformed, metadata


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def rm_errors(source: np.ndarray, transformed: np.ndarray, source_std: np.ndarray) -> np.ndarray:
    if source.shape != transformed.shape:
        raise Exp028ProtocolIntegrityError("RM_SHAPE_MISMATCH")
    if np.any(source_std <= 0) or not np.isfinite(source_std).all():
        raise Exp028ProtocolIntegrityError("TECHNICALLY_INVALID_MODEL_SOURCE_SIGMA")
    residual = transformed - source
    normalized = residual / source_std
    return normalized * normalized


def _balanced_accuracy(y_true: Sequence[Any], y_pred: Sequence[Any]) -> float:
    from sklearn.metrics import balanced_accuracy_score
    return float(balanced_accuracy_score(y_true, y_pred))


def fit_frozen_probe(features: Any, labels: Sequence[Any]) -> dict[str, Any]:
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(labels)
    if x.ndim != 2 or len(y) != x.shape[0]:
        raise Exp028ProtocolIntegrityError("PROBE_SHAPE_MISMATCH")
    scaler = StandardScaler(with_mean=True, with_std=True)
    x_scaled = scaler.fit_transform(x)
    classifier = LogisticRegression(
        solver="lbfgs",
        penalty="l2",
        C=1.0,
        fit_intercept=True,
        tol=0.0001,
        class_weight=None,
        dual=False,
        max_iter=1000,
        warm_start=False,
    )
    classifier.fit(x_scaled, y)
    return {
        "scaler": scaler,
        "classifier": classifier,
        "class_order": [str(c) for c in classifier.classes_],
        "probability_mapping": "classifier.classes_",
        "fit_only_rule": "FIT_condition_realization_only",
    }


def probe_predict(probe: Mapping[str, Any], features: Any) -> np.ndarray:
    x = np.asarray(features, dtype=np.float64)
    return probe["classifier"].predict(probe["scaler"].transform(x))


def readout_accuracy(probe: Mapping[str, Any], features: Any, labels: Sequence[Any]) -> float:
    return _balanced_accuracy(labels, probe_predict(probe, features))


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate_equal_weight(records: Sequence[Mapping[str, Any]], value_key: str = "value") -> float:
    """Source-family mean -> condition mean -> layer-pair mean -> model mean."""
    if not records:
        raise Exp028ProtocolIntegrityError("AGGREGATION_EMPTY")
    by_group: dict[tuple[str, str, str], list[float]] = {}
    for record in records:
        key = (
            str(record.get("source_family", "unknown")),
            str(record.get("condition", "unknown")),
            str(record.get("layer_pair", "unknown")),
        )
        value = record.get(value_key)
        if not isinstance(value, (int, float, np.number)):
            raise Exp028ProtocolIntegrityError("AGGREGATION_NON_NUMERIC")
        by_group.setdefault(key, []).append(float(value))
    family_means: dict[tuple[str, str], list[float]] = {}
    for (family, condition, layer_pair), values in by_group.items():
        family_means.setdefault((condition, layer_pair), []).append(float(np.mean(values)))
    condition_means: dict[str, list[float]] = {}
    for (condition, layer_pair), values in family_means.items():
        condition_means.setdefault(layer_pair, []).append(float(np.mean(values)))
    layer_means = [float(np.mean(values)) for values in condition_means.values()]
    if not layer_means:
        raise Exp028ProtocolIntegrityError("AGGREGATION_NO_LAYER_PAIRS")
    return float(np.mean(layer_means))


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap_distribution(
    records: Sequence[Mapping[str, Any]],
    value_key: str = "value",
    seed: int = BOOTSTRAP_SEED,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> np.ndarray:
    """Condition-stratified source-family cluster bootstrap."""
    if replicates <= 0:
        raise Exp028ProtocolIntegrityError("BOOTSTRAP_REPLICATES_INVALID")
    by_condition: dict[str, dict[str, list[Mapping[str, Any]]]] = {}
    for record in records:
        condition = str(record.get("condition", "unknown"))
        family = str(record.get("source_family", "unknown"))
        by_condition.setdefault(condition, {}).setdefault(family, []).append(record)
    rng = np.random.Generator(np.random.PCG64(seed))
    draws = np.empty(replicates, dtype=np.float64)
    for draw_idx in range(replicates):
        sampled: list[Mapping[str, Any]] = []
        instance_id = 0
        for condition, family_rows in by_condition.items():
            families = list(family_rows.keys())
            if not families:
                continue
            chosen = rng.integers(0, len(families), size=len(families))
            for family_idx in chosen:
                family = families[int(family_idx)]
                for record in family_rows[family]:
                    sampled_record = dict(record)
                    sampled_record["source_family"] = f"__bootstrap_instance_{draw_idx}_{instance_id}__"
                    sampled.append(sampled_record)
                instance_id += 1
        if not sampled:
            draws[draw_idx] = np.nan
        else:
            draws[draw_idx] = aggregate_equal_weight(sampled, value_key)
    return draws


def bootstrap_support_bounds(
    records: Sequence[Mapping[str, Any]],
    value_key: str = "value",
    seed: int = BOOTSTRAP_SEED,
    replicates: int = BOOTSTRAP_REPLICATES,
) -> dict[str, Any]:
    draws = bootstrap_distribution(records, value_key=value_key, seed=seed, replicates=replicates)
    draws = draws[np.isfinite(draws)]
    if len(draws) == 0:
        raise Exp028ProtocolIntegrityError("BOOTSTRAP_NO_FINITE_DRAWS")
    lower = float(np.percentile(draws, 5, method="linear"))
    upper = float(np.percentile(draws, 95, method="linear"))
    return {
        "lower_percentile_5": lower,
        "upper_percentile_95": upper,
        "support": lower > 0.0,
        "primary_support_semantics": "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND",
        "descriptive_central_interval": "CENTRAL_90_PERCENT_PERCENTILE_INTERVAL",
        "replicates": int(replicates),
        "seed": int(seed),
    }


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def classify_model_state(rm_supported: bool, ro_supported: bool) -> str:
    if rm_supported and ro_supported:
        return "JOINT_ALIGNMENT_CONTRIBUTION"
    if rm_supported and not ro_supported:
        return "REPRESENTATION_ONLY"
    if not rm_supported and ro_supported:
        return "READOUT_ONLY_ARTIFACT_RISK"
    return "NO_PAIRED_COORDINATE_CONTRIBUTION"


def route_three_models(model_states: Sequence[tuple[str, bool]]) -> str:
    """model_states: list of (state, technical_valid)."""
    if len(model_states) != 3:
        raise Exp028ProtocolIntegrityError("THREE_MODEL_ROUTING_REQUIRES_THREE_MODELS")
    if any(not valid for _, valid in model_states):
        return "NOT_FULLY_ADJUDICATED"
    states = [state for state, _ in model_states]
    if states.count("JOINT_ALIGNMENT_CONTRIBUTION") == 3:
        return "THREE_MODEL_JOINT_COORDINATEWISE_COMPONENT"
    if len(set(states)) == 1:
        return "THREE_MODEL_COMMON_STATE"
    return "MODEL_DEPENDENT_ALIGNMENT_STATE"


# ---------------------------------------------------------------------------
# Pair-break control
# ---------------------------------------------------------------------------

def pair_break_mapping(source_family_ids: Sequence[str]) -> dict[str, str]:
    """Return deterministic cyclic shift of one over sorted source families."""
    unique = sorted(set(source_family_ids))
    if not unique:
        return {}
    return {family: unique[(idx + 1) % len(unique)] for idx, family in enumerate(unique)}


def pair_break_pairs(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Build broken source/target item pairs while preserving family marginals."""
    unique = sorted({str(record.get("source_family", "unknown")) for record in records})
    if len(unique) < 2:
        return list(records)
    mapping = {family: unique[(idx + 1) % len(unique)] for idx, family in enumerate(unique)}
    target_by_family: dict[str, list[Any]] = {}
    for record in records:
        target_by_family.setdefault(str(record.get("target_family", record.get("source_family", "unknown"))), []).append(record.get("target_id"))
    broken: list[dict[str, Any]] = []
    for record in records:
        source_family = str(record.get("source_family", "unknown"))
        target_family = mapping[source_family]
        target_ids = target_by_family.get(target_family, [])
        target_id = target_ids[len(broken) % len(target_ids)] if target_ids else None
        broken.append({
            "source_family": source_family,
            "target_family": target_family,
            "source_id": record.get("source_id"),
            "target_id": target_id,
        })
    return broken


# ---------------------------------------------------------------------------
# Progress reporting
# ---------------------------------------------------------------------------

class OutcomeBlindProgress:
    """Reports lifecycle progress without scientific outcome values."""

    def __init__(self, state_path: Path | str | None = None):
        self.state_path = Path(state_path) if state_path is not None else None

    def report(
        self,
        stage: str,
        *,
        completed: int = 0,
        total: int = 0,
        percent: float | None = None,
        elapsed_time: float | None = None,
        heartbeat: bool = False,
        technical_phase: str | None = None,
    ) -> None:
        percent = percent if percent is not None else (100.0 * completed / total if total else 0.0)
        payload = {
            "stage": stage,
            "completed": int(completed),
            "total": int(total),
            "percent": float(percent),
            "elapsed_time": elapsed_time,
            "heartbeat": bool(heartbeat),
            "technical_phase": technical_phase,
        }
        if self.state_path is not None:
            atomic_write_json(self.state_path, payload)
        else:
            print(json.dumps(json_safe(payload), sort_keys=True))


# ---------------------------------------------------------------------------
# Result payload and publication
# ---------------------------------------------------------------------------

def build_result_payload(
    *,
    model_name: str,
    technical_valid: bool,
    delta_rm: float,
    delta_ro: float,
    rm_support: dict[str, Any],
    ro_support: dict[str, Any],
    model_state: str,
    three_model_route: str,
    pair_break_secondary: dict[str, Any] | None = None,
    binding: Mapping[str, Any] | None = None,
    panel_identity: Mapping[str, Any] | None = None,
    authorization_identity: Mapping[str, Any] | None = None,
    attempt_id: str | None = None,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    payload: dict[str, Any] = {
        "schema_version": "1.0.0",
        "classification": "EXP028_SCIENTIFIC_RESULT",
        "experiment": "EXP-028",
        "working_name": "PAIRED_INFORMATION_BEYOND_MARGINAL_RECALIBRATION",
        "created_at_utc": now,
        "attempt_id": attempt_id or uuid.uuid4().hex,
        "model_name": model_name,
        "technical_validity": bool(technical_valid),
        "primary_endpoints": {
            "DELTA_RM": float(delta_rm),
            "DELTA_RO": float(delta_ro),
            "DELTA_RM_sign_convention": "DELTA_RM = E(T_mu_sigma) - E(T_pair_diag); positive means paired contribution improves direct representation matching",
            "DELTA_RO_sign_convention": "DELTA_RO = C_pair - C_mu_sigma; positive means paired contribution improves fixed-readout recovery",
        },
        "bootstrap": {
            "DELTA_RM": rm_support,
            "DELTA_RO": ro_support,
        },
        "model_state": model_state,
        "three_model_route": three_model_route,
        "pair_break_secondary": pair_break_secondary or {"status": "NOT_COMPUTED"},
        "execution_binding": binding or {},
        "panel_identity": panel_identity or {},
        "authorization_identity": authorization_identity or {},
        "claim_firewall": {
            "TRANSPORT_TEST": False,
            "INVARIANT_TEST": False,
            "FUNCTIONAL_BINDING_TEST": False,
            "FULL_RESIDUAL_FLOW_TEST": False,
            "FULL_MSA_TEST": False,
        },
    }
    return payload


def _runtime_environment() -> dict[str, Any]:
    try:
        import platform
        return {
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
        }
    except Exception:
        return {}


def publish_canonical_result(payload: Mapping[str, Any], result_path: Path = RESULT_PATH) -> str:
    errors = result_validator.validate_result_payload(payload)
    if errors:
        raise Exp028ProtocolIntegrityError(f"RESULT_SCHEMA_INVALID_{errors}")
    return atomic_write_json_exclusive(result_path, payload)


# ---------------------------------------------------------------------------
# Authorization lifecycle
# ---------------------------------------------------------------------------

def classify_authorization_lifecycle(
    authorization_path: Path | None,
    consumption_dir: Path,
    result_path: Path,
) -> str:
    if result_path.exists():
        return "CANONICAL_RESULT_EXISTS"
    if authorization_path is None or not authorization_path.exists():
        return "NO_AUTHORIZATION"
    consumption = consumption_dir / "consumption.json"
    if consumption.exists():
        record = read_json(consumption)
        if record.get("authorization_id") == read_json(authorization_path).get("authorization_id"):
            return "CONSUMED"
    return "AUTHORIZED_UNUSED"


def validate_authorization(authorization_path: Path, root: Path = ROOT) -> tuple[dict[str, Any], str]:
    authorization_path = Path(authorization_path)
    if not authorization_path.exists():
        raise Exp028ProtocolIntegrityError("FORMAL_RUN_REQUIRES_AUTHORIZATION")
    authorization = read_json(authorization_path)
    if authorization.get("classification") != "EXP028_FORMAL_AUTHORIZATION":
        raise Exp028ProtocolIntegrityError("AUTHORIZATION_CLASSIFICATION_INVALID")
    if authorization.get("experiment") != "EXP-028":
        raise Exp028ProtocolIntegrityError("AUTHORIZATION_EXPERIMENT_INVALID")
    if authorization.get("single_use") is not True:
        raise Exp028ProtocolIntegrityError("AUTHORIZATION_NOT_SINGLE_USE")
    if authorization.get("authorized_execution_count") != 1:
        raise Exp028ProtocolIntegrityError("AUTHORIZATION_EXECUTION_COUNT_INVALID")
    binding = authorization.get("execution_binding", {})
    if binding.get("runner_sha256") != sha256_file(Path(__file__)):
        raise Exp028ProtocolIntegrityError("AUTHORIZATION_RUNNER_SHA_MISMATCH")
    if not authorization.get("authorization_id") or not authorization.get("run_attempt_id"):
        raise Exp028ProtocolIntegrityError("AUTHORIZATION_IDENTITY_INCOMPLETE")
    return authorization, sha256_file(authorization_path)


def consume_authorization(
    authorization: Mapping[str, Any],
    authorization_sha: str,
    consumption_dir: Path = CONSUMPTION_DIR,
) -> tuple[dict[str, Any], str]:
    consumption_dir.mkdir(parents=True, exist_ok=True)
    consumption_path = consumption_dir / "consumption.json"
    if consumption_path.exists():
        raise Exp028ProtocolIntegrityError("FORMAL_AUTHORIZATION_ALREADY_CONSUMED")
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "schema_version": "1.0.0",
        "classification": "AUTHORIZATION_CONSUMPTION",
        "experiment": "EXP-028",
        "authorization_id": authorization.get("authorization_id"),
        "authorization_sha256": authorization_sha,
        "run_attempt_id": authorization.get("run_attempt_id"),
        "consumed_at_utc": now,
        "formal_launch_count": 1,
    }
    consumption_sha = atomic_write_json_exclusive(consumption_path, payload)
    return payload, consumption_sha


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------

def run_static_preflight(root: Path = ROOT, publish: bool = False) -> dict[str, Any]:
    binding = verify_exp028_authorities(root)
    config = frozen_config(root)
    errors = result_validator.validate_config_surface(config)
    if errors:
        raise Exp028ProtocolIntegrityError(f"STATIC_RESULT_CONFIG_INVALID_{errors}")
    no_auth = not (root / AUTHORIZATION_PATH).exists()
    no_result = not (root / RESULT_PATH).exists()
    if not no_auth or not no_result:
        raise Exp028ProtocolIntegrityError("STATIC_PREFLIGHT_LIFECYCLE_CONTAMINATED")
    try:
        run_formal_run(root, authorization_file=None)
    except Exp028ProtocolIntegrityError as exc:
        formal_gate = str(exc)
    else:
        raise Exp028ProtocolIntegrityError("STATIC_PREFLIGHT_FORMAL_GATE_NOT_ENFORCED")
    artifact = {
        "schema_version": "1.0.0",
        "classification": "EXP028_ENGINEERING_STATIC_PREFLIGHT",
        "status": "PASS",
        "formal_run_without_authorization_gate": formal_gate,
        "no_formal_result": no_result,
        "no_authorization": no_auth,
        "runner_sha256": binding["runner_sha256"],
        "frozen_config_sha256": binding["frozen_config_sha256"],
        "authority_binding_sha256": binding["authority_binding_sha256"],
        "synthetic_only": True,
        "real_model_inference_performed": False,
        "real_data_accessed": False,
        "authorization_created": False,
        "scientific_result_created": False,
    }
    if publish:
        atomic_write_json(ENGINEERING_DIR / "exp028_static_preflight.json", artifact)
    return artifact


def _synthetic_route_cases() -> list[dict[str, Any]]:
    cases = [
        {"states": [("JOINT_ALIGNMENT_CONTRIBUTION", True), ("JOINT_ALIGNMENT_CONTRIBUTION", True), ("JOINT_ALIGNMENT_CONTRIBUTION", True)], "expected": "THREE_MODEL_JOINT_COORDINATEWISE_COMPONENT"},
        {"states": [("REPRESENTATION_ONLY", True), ("REPRESENTATION_ONLY", True), ("REPRESENTATION_ONLY", True)], "expected": "THREE_MODEL_COMMON_STATE"},
        {"states": [("JOINT_ALIGNMENT_CONTRIBUTION", True), ("REPRESENTATION_ONLY", True), ("NO_PAIRED_COORDINATE_CONTRIBUTION", True)], "expected": "MODEL_DEPENDENT_ALIGNMENT_STATE"},
        {"states": [("JOINT_ALIGNMENT_CONTRIBUTION", True), ("JOINT_ALIGNMENT_CONTRIBUTION", True), ("JOINT_ALIGNMENT_CONTRIBUTION", False)], "expected": "NOT_FULLY_ADJUDICATED"},
    ]
    return cases


def run_synthetic_qualification(root: Path = ROOT, publish: bool = True) -> dict[str, Any]:
    binding = verify_exp028_authorities(root)
    scenario_results: list[dict[str, Any]] = []
    for case in _synthetic_route_cases():
        actual = route_three_models(case["states"])
        scenario_results.append({
            "case": case["expected"],
            "expected": case["expected"],
            "actual": actual,
            "pass": actual == case["expected"],
        })
    all_pass = all(item["pass"] for item in scenario_results)
    artifact = {
        "schema_version": "1.0.0",
        "classification": "EXP028_ENGINEERING_SYNTHETIC_QUALIFICATION",
        "status": "PASS" if all_pass else "FAIL",
        "runner_sha256": binding["runner_sha256"],
        "frozen_config_sha256": binding["frozen_config_sha256"],
        "authority_binding_sha256": binding["authority_binding_sha256"],
        "test_suite": "tests/test_exp028_runner.py",
        "scenario_count": len(scenario_results),
        "scenario_pass_count": sum(1 for item in scenario_results if item["pass"]),
        "scenarios": scenario_results,
        "synthetic_only": True,
        "real_model_inference_performed": False,
        "real_FIT_accessed": False,
        "real_DIAG_accessed": False,
        "real_EVAL_accessed": False,
        "authorization_created": False,
        "scientific_result_created": False,
    }
    if publish:
        artifact["artifact_sha256"] = atomic_write_json(QUALIFICATION_PATH, artifact)
    return artifact


def run_formal_run(root: Path = ROOT, authorization_file: str | None = None) -> dict[str, Any]:
    binding = verify_exp028_authorities(root)
    verify_no_result_collision(root / RESULT_PATH)
    progress = OutcomeBlindProgress()
    progress.report("AUTHORIZATION_VALIDATION", completed=0, total=1, heartbeat=True)
    auth_path = Path(authorization_file).resolve() if authorization_file else None
    lifecycle = classify_authorization_lifecycle(auth_path, root / CONSUMPTION_DIR, root / RESULT_PATH)
    if lifecycle != "AUTHORIZED_UNUSED":
        raise Exp028ProtocolIntegrityError(f"FORMAL_LIFECYCLE_{lifecycle}")
    authorization, authorization_sha = validate_authorization(auth_path, root)
    # Real scientific execution requires a frozen panel manifest and extracted
    # representation archive. Task 103D deliberately does not generate those.
    raise Exp028ProtocolIntegrityError("FORMAL_SCIENTIFIC_EXECUTION_REQUIRES_FROZEN_PANEL_AND_EXTRACTIONS")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument(_STATIC_FLAG, action="store_true")
    modes.add_argument(_SYNTHETIC_FLAG, action="store_true")
    modes.add_argument(_FORMAL_FLAG, action="store_true")
    parser.add_argument(_REPO_ROOT_FLAG, default=None)
    parser.add_argument(_AUTHORIZATION_FILE_FLAG, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else ROOT
    try:
        if args.static_preflight:
            result = run_static_preflight(root)
            print("EXP028_STATIC_PREFLIGHT = PASS")
            print(json.dumps(json_safe(result), indent=2, sort_keys=True))
            return 0
        if args.synthetic_qualification:
            result = run_synthetic_qualification(root, publish=True)
            print("EXP028_SYNTHETIC_QUALIFICATION = PASS" if result["status"] == "PASS" else "EXP028_SYNTHETIC_QUALIFICATION = FAIL")
            print(json.dumps(json_safe(result), indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
        if args.formal_run:
            run_formal_run(root, args.authorization_file)
            return 0
    except Exp028ProtocolIntegrityError as exc:
        print("EXP028_MODE = FAIL")
        print(f"EXP028_ERROR = {exc}")
        return 1
    except Exception as exc:
        print("EXP028_MODE = FAIL")
        print(f"EXP028_ERROR = {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
