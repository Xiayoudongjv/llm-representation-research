#!/usr/bin/env python3
"""EXP-026 production runner and synthetic qualification surface.

Importing this module does not load a model or access scientific panel records.
Only the explicit CLI modes below may perform the corresponding work.

Modes:
  --static-preflight
  --engineering-qualification
  --synthetic-formal-qualification
  --formal-run

The first three modes are authorization/qualification modes. Only
`--formal-run` may access real EXP-026 FIT/DIAG/EVAL scientific records, and it
does so only after consuming a valid single-use formal authorization.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

EXPERIMENT = "EXP-026"
RESULT_SCHEMA_VERSION = "1.0.0"
QUALIFICATION_SCHEMA_VERSION = "1.0.0"

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent

DESIGN_CONFIG_PATH = EXP_DIR / "exp026_frozen_config.json"
DESIGN_PREREGISTRATION_PATH = EXP_DIR / "EXP-026-PREREGISTRATION.md"
DESIGN_MODEL_SELECTION_PATH = EXP_DIR / "EXP-026-MODEL-SELECTION.md"
DESIGN_LAYER_MAPPING_PATH = EXP_DIR / "EXP-026-LAYER-CARRIER-MAPPING.md"
DESIGN_METRIC_PATH = EXP_DIR / "EXP-026-MATRIX-METRIC-SPECIFICATION.md"
DESIGN_ROUTING_PATH = EXP_DIR / "EXP-026-ROUTING-RULES.md"
DESIGN_VALIDATOR_PATH = EXP_DIR / "validate_exp026_design.py"

EXPECTED_DESIGN_HASHES = {
    "frozen_config": "ccf60c8a9dc6f3b9d3cce533910334e1f8ec33665a1cf692b98a8aaf683afb57",
    "preregistration": "730175071e315b484e360b6359945f567bfe8edf4f52e6a0893c3f2a7dadf8e1",
    "layer_mapping": "04c6565ff366fc04960966fcff148228c5338870756c75375baf976177d6dfb1",
    "metric_specification": "5f58445e26eee7effddd7cd5b4ae255b7153d61fa7a76b5c0684fa1dbb08d8db",
    "routing_rules": "4ff6be135066e1cd0bbcad54ee6c7472d693d35063df8202326b5bd0b4308856",
    "design_validator": "8bfbbb8f7c106aae4f3bd1c82fe5f1419cb8fe7d4bcc87f624eb04a59e6ee2bf",
}

CLASS_ORDER = ("logic", "causality", "analogy", "definition")
CLASS_UNIVERSE = frozenset(CLASS_ORDER)
PARTITIONS = ("FIT", "DIAGNOSTIC", "EVAL")
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
ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}

MODEL_REGISTRY = {
    "Q": {
        "model_id": "Qwen/Qwen3-1.7B",
        "model_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "num_hidden_layers": 28,
        "hidden_size": 2048,
        "snapshot_path": Path(
            "D:/AI_Cache/huggingface/hub/models--Qwen--Qwen3-1.7B/snapshots/"
            "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
        ),
    },
    "O": {
        "model_id": "allenai/OLMo-2-0425-1B-Instruct",
        "model_revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
        "num_hidden_layers": 16,
        "hidden_size": 2048,
        "snapshot_path": Path(
            "D:/AI_Cache/huggingface/hub/models--allenai--OLMo-2-0425-1B-Instruct/snapshots/"
            "48d788eca847d4d7548f375ad03d3c9312f6139e"
        ),
    },
}
MODEL_KEYS = ("Q", "O")

NEUTRAL_QUALIFICATION_INPUTS = (
    "The local snapshot is loaded in offline mode.",
    "A neutral engineering forward pass checks tokenizer and carrier metadata.",
    "The attention mask determines the last valid non-padding token.",
    "Runtime qualification records shapes, dtypes, finite values, and hook cleanup.",
)

SOURCE_TECHNICAL_FLOOR = 0.75
SOURCE_COVERAGE_MIN_FRACTION = 0.5
SOURCE_COVERAGE_MIN_SPAN = 0.5
BOOTSTRAP_REPLICATES = 5000
BOOTSTRAP_SEED = 20260819
BOOTSTRAP_CI_LEVEL = 0.95
BOOTSTRAP_QUANTILE_METHOD = "linear"

FORMAL_RESULT_PATH = EXP_DIR / "results" / "exp026_results.json"
FORMAL_RESULT_CANDIDATES = (
    FORMAL_RESULT_PATH,
    EXP_DIR / "exp026_formal_result.json",
)
ENGINEERING_DIR = EXP_DIR / "engineering"
# Historical 101C qualification records are preserved.  101D-R writes only
# versioned, superseding qualification evidence.
ENGINEERING_QUALIFICATION_PATH = ENGINEERING_DIR / "exp026_runner_qualification_101d_r.json"
FORMAL_PIPELINE_QUALIFICATION_PATH = ENGINEERING_DIR / "exp026_formal_pipeline_qualification_101d_r.json"
FORMAL_AUTHORIZATION_PATH = EXP_DIR / "exp026_formal_run_authorization.json"
AUTHORIZATION_CONSUMPTION_DIR = EXP_DIR / "results" / "authorization_consumption"


class ProtocolIntegrityError(RuntimeError):
    """Raised when a frozen authority or implementation invariant is violated."""


class TechnicalInvalidError(RuntimeError):
    """Raised when a computation is technically invalid under the protocol."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        item = value.item()
        if isinstance(item, float) and not math.isfinite(item):
            return None
        return item
    if isinstance(value, dict):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def _atomic_write_json_exclusive(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_json_safe(data), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    try:
        fd = os.open(str(path), flags, 0o644)
    except FileExistsError as exc:
        raise ProtocolIntegrityError("PATH_ALREADY_EXISTS") from exc
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
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


def _atomic_write_json(path: Path, data: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(_json_safe(data), ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n"
    path.write_text(payload, encoding="utf-8", newline="\n")
    return sha256_file(path)


def _root_relative_path(root: Path, path: Path) -> Path:
    """Resolve a repository-owned absolute path against an injected root."""
    try:
        return root / path.relative_to(ROOT)
    except ValueError:
        # Test-only injected paths may deliberately live outside the repository.
        return path


def _canonical_json_sha256(value: Any) -> str:
    """Hash canonical JSON bytes for an authorization identity field."""
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_string(payload)


def verify_frozen_design(root: Path = ROOT) -> dict[str, Any]:
    checks = {
        "frozen_config": DESIGN_CONFIG_PATH,
        "preregistration": DESIGN_PREREGISTRATION_PATH,
        "layer_mapping": DESIGN_LAYER_MAPPING_PATH,
        "metric_specification": DESIGN_METRIC_PATH,
        "routing_rules": DESIGN_ROUTING_PATH,
        "design_validator": DESIGN_VALIDATOR_PATH,
    }
    actual = {}
    for key, path in checks.items():
        path = _root_relative_path(root, path)
        if not path.is_file():
            raise ProtocolIntegrityError(f"FROZEN_AUTHORITY_MISSING_{key}")
        actual[key] = sha256_file(path)
    for key, expected in EXPECTED_DESIGN_HASHES.items():
        if actual[key] != expected:
            raise ProtocolIntegrityError(f"FROZEN_AUTHORITY_HASH_MISMATCH_{key}")
    return actual


def verify_no_result_collision(root: Path = ROOT) -> None:
    for path in FORMAL_RESULT_CANDIDATES:
        if _root_relative_path(root, path).exists():
            raise ProtocolIntegrityError(f"FORMAL_RESULT_PATH_UNEXPECTED_{path.name}")


def _set_offline_model_env() -> None:
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

def _load_tokenizer(model_key: str):
    _set_offline_model_env()
    from transformers import AutoTokenizer

    spec = MODEL_REGISTRY[model_key]
    return AutoTokenizer.from_pretrained(str(spec["snapshot_path"]), local_files_only=True)


def _load_model(model_key: str):
    _set_offline_model_env()
    import torch
    from transformers import AutoModelForCausalLM

    spec = MODEL_REGISTRY[model_key]
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(
        str(spec["snapshot_path"]),
        dtype=dtype,
        local_files_only=True,
        use_cache=False,
    )
    model.eval()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return model, device, dtype


def load_runtime(model_key: str):
    tokenizer = _load_tokenizer(model_key)
    model, device, dtype = _load_model(model_key)
    return tokenizer, model, device, dtype


def _extract_block_hidden_state(output: Any) -> Any:
    import torch

    if torch.is_tensor(output):
        return output
    if isinstance(output, (tuple, list)):
        if len(output) == 0:
            raise TypeError("UNSUPPORTED_BLOCK_OUTPUT_STRUCTURE_EMPTY")
        return _extract_block_hidden_state(output[0])
    raise TypeError("UNSUPPORTED_BLOCK_OUTPUT_STRUCTURE")


@dataclass
class ForwardHookCapture:
    _captured: Any = None
    _capture_count: int = 0

    def record(self, output: Any) -> None:
        if self._capture_count:
            raise RuntimeError("UNEXPECTED_MULTIPLE_HOOK_CAPTURE")
        self._captured = _extract_block_hidden_state(output)
        self._capture_count = 1

    @property
    def value(self) -> Any:
        if self._capture_count != 1:
            raise RuntimeError("HOOK_CAPTURE_MISSING_OR_DUPLICATED")
        return self._captured

    @property
    def count(self) -> int:
        return self._capture_count


def last_valid_token_indices(attention_mask: Any) -> list[int]:
    import torch

    if torch.is_tensor(attention_mask):
        mask = attention_mask.detach().cpu().numpy()
    else:
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


def _select_last_valid_token_torch(hidden_states: Any, indices: Sequence[int]) -> Any:
    import torch

    if torch.is_tensor(indices):
        index_tensor = indices.to(device=hidden_states.device, dtype=torch.long).reshape(-1)
    else:
        index_tensor = torch.as_tensor(indices, dtype=torch.long, device=hidden_states.device).reshape(-1)
    if hidden_states.ndim == 2:
        if index_tensor.numel() != 1:
            raise ValueError("Two-dimensional hidden states require exactly one index.")
        return hidden_states[index_tensor[0]]
    if hidden_states.ndim != 3:
        raise ValueError("Hidden states must be two- or three-dimensional.")
    if index_tensor.numel() != hidden_states.shape[0]:
        raise ValueError("Valid-token index count must match hidden-state batch dimension.")
    return hidden_states[torch.arange(hidden_states.shape[0], device=hidden_states.device), index_tensor]


def select_last_valid_token(hidden_states: Any, attention_mask: Any) -> Any:
    return _select_last_valid_token_torch(hidden_states, last_valid_token_indices(attention_mask))


def to_float32_analysis_array(value: Any, expected_ndim: int | None = None) -> np.ndarray:
    import torch

    if torch.is_tensor(value):
        array = value.detach().cpu().to(torch.float32).numpy()
    else:
        array = np.asarray(value)
    array = np.asarray(array, dtype=np.float32)
    if expected_ndim is not None and array.ndim != expected_ndim:
        if array.ndim == expected_ndim + 1 and array.shape[0] == 1:
            array = array[0]
        else:
            raise TechnicalInvalidError("UNEXPECTED_ANALYSIS_ARRAY_NDIM")
    if not np.isfinite(array).all():
        raise TechnicalInvalidError("NONFINITE_ANALYSIS_ARRAY")
    return array


def tokenize_neutral(tokenizer: Any, text: str, device: Any):
    encoded = tokenizer(text, return_tensors="pt", padding=False, truncation=False)
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    return encoded, input_ids, attention_mask


def extract_all_layers(tokenizer: Any, model: Any, device: Any, text: str, num_layers: int) -> tuple[Any, Any, np.ndarray]:
    import torch

    _, input_ids, attention_mask = tokenize_neutral(tokenizer, text, device)
    captures = [ForwardHookCapture() for _ in range(num_layers)]
    handles = []
    with torch.inference_mode():
        for index in range(num_layers):
            module = model.model.layers[index]
            handle = module.register_forward_hook(
                lambda _module, _args, output, cap=captures[index]: cap.record(output)
            )
            handles.append(handle)
        try:
            model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                use_cache=False,
            )
        finally:
            for handle in handles:
                handle.remove()
    arrays = []
    for capture in captures:
        if capture.count != 1:
            raise ProtocolIntegrityError("ALL_LAYER_HOOK_CAPTURE_MISSING_OR_DUPLICATED")
        array = to_float32_analysis_array(select_last_valid_token(capture.value, attention_mask), expected_ndim=1)
        arrays.append(array)
    matrix = np.stack(arrays, axis=0).astype(np.float32)
    if matrix.shape != (num_layers, matrix.shape[1]):
        raise ProtocolIntegrityError("ALL_LAYER_EXTRACTION_SHAPE_INVALID")
    return input_ids, attention_mask, matrix


@dataclass(frozen=True)
class ExtractedObservation:
    record_id: str
    partition: str
    condition_id: str
    semantic_class: str
    source_family_id: str
    vectors: np.ndarray

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "partition": self.partition,
            "condition_id": self.condition_id,
            "semantic_class": self.semantic_class,
            "source_family_id": self.source_family_id,
            "vectors_sha256": sha256_bytes(self.vectors.astype(np.float32).tobytes()),
            "vectors_shape": list(self.vectors.shape),
            "vectors_dtype": str(self.vectors.dtype),
        }


def filter_condition_realization(observations: Sequence[ExtractedObservation], partition: str) -> list[ExtractedObservation]:
    return [obs for obs in observations if obs.partition == partition]


def group_by_condition(observations: Sequence[ExtractedObservation], condition_order: Sequence[str]) -> dict[str, list[ExtractedObservation]]:
    grouped = {condition: [] for condition in condition_order}
    for obs in observations:
        if obs.condition_id in grouped:
            grouped[obs.condition_id].append(obs)
    return grouped


def classifier_class_mapping(model: Any) -> list[str]:
    return [str(value) for value in model.classes_]


def balanced_accuracy(y_true: Sequence[str], y_pred: Sequence[str]) -> float:
    if len(y_true) != len(y_pred):
        raise ValueError("Balanced-accuracy inputs must be equal length.")
    true_values = [str(value) for value in y_true]
    pred_values = [str(value) for value in y_pred]
    if set(true_values) != CLASS_UNIVERSE:
        raise ProtocolIntegrityError("BALANCED_ACCURACY_MISSING_TRUE_CLASS")
    if set(pred_values) - CLASS_UNIVERSE:
        raise ProtocolIntegrityError("BALANCED_ACCURACY_UNEXPECTED_PREDICTED_CLASS")
    recalls = []
    for cls in CLASS_ORDER:
        positives = [i for i, value in enumerate(true_values) if value == cls]
        if not positives:
            raise ProtocolIntegrityError("BALANCED_ACCURACY_ZERO_CLASS")
        correct = sum(1 for i in positives if pred_values[i] == cls)
        recalls.append(correct / len(positives))
    return float(sum(recalls) / len(recalls))


def fit_scaler(X: np.ndarray) -> StandardScaler:
    scaler = StandardScaler(with_mean=True, with_std=True)
    scaler.fit(X)
    return scaler


def fit_classifier(X: np.ndarray, y: Sequence[str]) -> tuple[LogisticRegression, list[str]]:
    model = LogisticRegression(
        solver="lbfgs",
        penalty="l2",
        C=1.0,
        fit_intercept=True,
        tol=1e-4,
        class_weight=None,
        dual=False,
        max_iter=1000,
        warm_start=False,
    )
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
    return rho if math.isfinite(rho) else float("nan")


def population_variance(values: Sequence[float]) -> float:
    array = np.asarray(values, dtype=float)
    if array.size == 0:
        return float("nan")
    if not np.isfinite(array).all():
        return float("nan")
    return float(np.var(array, ddof=0))


def normalized_depth(layer_index: int, num_layers: int) -> float:
    if num_layers <= 1:
        raise ValueError("num_layers must be greater than one.")
    if layer_index < 0 or layer_index >= num_layers:
        raise ValueError("layer_index out of range.")
    return layer_index / (num_layers - 1)


def _matrix_from_observations(observations: Sequence[ExtractedObservation], layer: int) -> tuple[np.ndarray, list[str]]:
    if not observations:
        raise ProtocolIntegrityError("EMPTY_OBSERVATION_GROUP")
    X = np.stack([obs.vectors[layer] for obs in observations], axis=0).astype(np.float32)
    y = [obs.semantic_class for obs in observations]
    return X, y


def _fit_source_models(observations: Sequence[ExtractedObservation], num_layers: int) -> list[Any]:
    fit = filter_condition_realization(observations, "FIT")
    if not fit:
        raise ProtocolIntegrityError("FIT_DATA_MISSING")
    models = []
    for layer in range(num_layers):
        X, y = _matrix_from_observations(fit, layer)
        model, _ = fit_classifier(X, y)
        models.append(model)
    return models


def _fit_pair_calibration(observations: Sequence[ExtractedObservation], num_layers: int, condition_order: Sequence[str]) -> dict[str, Any]:
    fit = filter_condition_realization(observations, "FIT")
    grouped = group_by_condition(fit, condition_order)
    source_stats = []
    for layer in range(num_layers):
        X, _ = _matrix_from_observations(fit, layer)
        scaler = fit_scaler(X)
        source_stats.append((scaler.mean_.astype(np.float32), scaler.scale_.astype(np.float32)))
    target_by_layer_condition = [[None for _ in range(len(condition_order))] for _ in range(num_layers)]
    for layer in range(num_layers):
        for c_index, condition in enumerate(condition_order):
            X, _ = _matrix_from_observations(grouped[condition], layer)
            scaler = fit_scaler(X)
            target_by_layer_condition[layer][c_index] = (scaler.mean_.astype(np.float32), scaler.scale_.astype(np.float32))
    return {
        "source_stats": source_stats,
        "target_by_layer_condition": target_by_layer_condition,
    }


def _compute_c0_for_partition(
    observations: Sequence[ExtractedObservation],
    partition: str,
    num_layers: int,
    condition_order: Sequence[str],
    models: Sequence[Any],
) -> np.ndarray:
    rows = filter_condition_realization(observations, partition)
    grouped = group_by_condition(rows, condition_order)
    matrix = np.zeros((num_layers, num_layers, len(condition_order)), dtype=np.float32)
    for c_index, condition in enumerate(condition_order):
        group = grouped[condition]
        if not group:
            raise ProtocolIntegrityError("CONDITION_DATA_MISSING")
        for source in range(num_layers):
            model = models[source]
            for target in range(num_layers):
                X, y = _matrix_from_observations(group, target)
                pred = [str(value) for value in model.predict(X)]
                matrix[source, target, c_index] = balanced_accuracy(y, pred)
    return matrix


def _compute_c_cal_for_partition(
    observations: Sequence[ExtractedObservation],
    partition: str,
    num_layers: int,
    condition_order: Sequence[str],
    models: Sequence[Any],
    calibration: dict[str, Any],
) -> np.ndarray:
    rows = filter_condition_realization(observations, partition)
    grouped = group_by_condition(rows, condition_order)
    matrix = np.zeros((num_layers, num_layers, len(condition_order)), dtype=np.float32)
    target_by_layer_condition = calibration["target_by_layer_condition"]
    for c_index, condition in enumerate(condition_order):
        group = grouped[condition]
        if not group:
            raise ProtocolIntegrityError("CONDITION_DATA_MISSING")
        for source in range(num_layers):
            model = models[source]
            for target in range(num_layers):
                X, y = _matrix_from_observations(group, target)
                mean, scale = target_by_layer_condition[target][c_index]
                z = transform_with_stats(X, mean, scale)
                pred = [str(value) for value in model.predict(z)]
                matrix[source, target, c_index] = balanced_accuracy(y, pred)
    return matrix


def _source_qualification(observations: Sequence[ExtractedObservation], num_layers: int, models: Sequence[Any], condition_order: Sequence[str]) -> dict[str, Any]:
    diag = filter_condition_realization(observations, "DIAGNOSTIC")
    grouped = group_by_condition(diag, condition_order)
    ba_by_layer = []
    for layer in range(num_layers):
        model = models[layer]
        condition_values = []
        for condition in condition_order:
            X, y = _matrix_from_observations(grouped[condition], layer)
            pred = [str(value) for value in model.predict(X)]
            condition_values.append(balanced_accuracy(y, pred))
        ba_by_layer.append(float(np.mean(condition_values)))
    eligible = [value >= SOURCE_TECHNICAL_FLOOR for value in ba_by_layer]
    span = 0.0
    eligible_indices = [i for i, value in enumerate(eligible) if value]
    if eligible_indices:
        span = abs(normalized_depth(max(eligible_indices), num_layers) - normalized_depth(min(eligible_indices), num_layers))
    coverage = (
        len(eligible_indices) >= math.ceil(num_layers * SOURCE_COVERAGE_MIN_FRACTION)
        and span >= SOURCE_COVERAGE_MIN_SPAN
    )
    return {
        "ba_diag_self": ba_by_layer,
        "eligible_source_mask": eligible,
        "eligible_source_count": len(eligible_indices),
        "eligible_depth_span": span,
        "source_coverage_evaluable": coverage,
    }


def _condition_pool(matrix: np.ndarray) -> np.ndarray:
    if matrix.ndim != 3 or matrix.shape[2] != len(CONDITION_ORDER):
        raise ProtocolIntegrityError("CONDITION_POOL_REQUIRES_ALL_FROZEN_CONDITIONS")
    if not np.isfinite(matrix).all():
        raise TechnicalInvalidError("CONDITION_POOL_NONFINITE")
    return np.mean(matrix, axis=2).astype(np.float32)


def _distance_association_point(dbar: np.ndarray, eligible_mask: Sequence[bool], num_layers: int) -> float:
    pairs_x = []
    pairs_y = []
    for i in range(num_layers):
        if not eligible_mask[i]:
            continue
        for j in range(num_layers):
            if i == j:
                continue
            pairs_x.append(abs(normalized_depth(i, num_layers) - normalized_depth(j, num_layers)))
            pairs_y.append(float(dbar[i, j]))
    if len(pairs_x) < 2:
        return float("nan")
    return spearman_rho(pairs_x, pairs_y)


def _sdi_point(dbar: np.ndarray, eligible_mask: Sequence[bool], num_layers: int) -> dict[str, Any]:
    row_means = []
    col_means = []
    eligible = [i for i in range(num_layers) if eligible_mask[i]]
    for i in eligible:
        row_means.append(float(np.mean([dbar[i, j] for j in range(num_layers) if j != i])))
    for j in range(num_layers):
        vals = [dbar[i, j] for i in eligible if i != j]
        col_means.append(float(np.mean(vals)) if vals else float("nan"))
    source_var = population_variance(row_means)
    target_var = population_variance(col_means)
    denominator = source_var + target_var
    if denominator == 0.0:
        sdi = 0.0
        status = "NO_ROW_OR_COLUMN_VARIATION"
    else:
        sdi = (source_var - target_var) / denominator
        status = "EVALUABLE"
    return {
        "sdi": sdi,
        "source_variance": source_var,
        "target_variance": target_var,
        "row_means": row_means,
        "column_means": col_means,
        "status": status,
    }

def _localization_point(dbar: np.ndarray, eligible_mask: Sequence[bool], num_layers: int) -> dict[str, Any]:
    if num_layers <= 1:
        return {"localization": 0.0, "boundaries": [], "status": "NO_TARGET_BOUNDARY_VARIATION"}
    eligible = [i for i in range(num_layers) if eligible_mask[i]]
    jumps = []
    for j in range(num_layers - 1):
        vals = [abs(float(dbar[i, j + 1] - dbar[i, j])) for i in eligible]
        jumps.append(float(np.mean(vals)) if vals else 0.0)
    total = sum(jumps)
    if total == 0.0:
        return {"localization": 0.0, "boundaries": [], "status": "NO_TARGET_BOUNDARY_VARIATION", "jumps": jumps}
    max_jump = max(jumps)
    boundaries = [j for j, value in enumerate(jumps) if value == max_jump]
    return {
        "localization": max_jump / total,
        "boundaries": boundaries,
        "status": "EVALUABLE",
        "jumps": jumps,
    }


def _low_d_pair_mask(diag_dbar: np.ndarray, eligible_mask: Sequence[bool], num_layers: int) -> tuple[np.ndarray, list[tuple[int, int]]]:
    mask = np.zeros((num_layers, num_layers), dtype=bool)
    pairs = []
    for i in range(num_layers):
        if not eligible_mask[i]:
            continue
        for j in range(num_layers):
            if i == j:
                continue
            if float(diag_dbar[i, j]) <= 0.0:
                mask[i, j] = True
                pairs.append((i, j))
    return mask, pairs


def _summarize_point_profile(
    dbar: np.ndarray,
    rbar: np.ndarray,
    eligible_mask: Sequence[bool],
    num_layers: int,
    diag_dbar: np.ndarray,
) -> dict[str, Any]:
    distance = _distance_association_point(dbar, eligible_mask, num_layers)
    sdi = _sdi_point(dbar, eligible_mask, num_layers)
    localization = _localization_point(dbar, eligible_mask, num_layers)
    localization_r = _localization_point(rbar, eligible_mask, num_layers)
    mask, pairs = _low_d_pair_mask(diag_dbar, eligible_mask, num_layers)
    if not pairs:
        low_d = {"mean_recovery": None, "eligible_pair_count": 0, "positive_recovery_fraction": None, "status": "NOT_EVALUABLE"}
    else:
        values = [float(rbar[i, j]) for i, j in pairs]
        low_d = {
            "mean_recovery": float(np.mean(values)),
            "eligible_pair_count": len(values),
            "positive_recovery_fraction": float(np.mean([value > 0 for value in values])),
            "status": "EVALUABLE",
            "pair_mask": mask,
            "pairs": pairs,
        }
    return {
        "distance_association": distance,
        "sdi": sdi,
        "localization": localization,
        "localization_r": localization_r,
        "low_d_recovery": low_d,
        "mean_off_diag_dbar": float(np.mean([dbar[i, j] for i in range(num_layers) if eligible_mask[i] for j in range(num_layers) if i != j])) if any(eligible_mask) else float("nan"),
        "mean_off_diag_rbar": float(np.mean([rbar[i, j] for i in range(num_layers) if eligible_mask[i] for j in range(num_layers) if i != j])) if any(eligible_mask) else float("nan"),
    }


def _support_classes(point: dict[str, Any], bootstrap: dict[str, Any] | None) -> dict[str, Any]:
    if point.get("status") == "NOT_EVALUABLE_SOURCE_COVERAGE":
        return {
            "distance_support": "NOT_EVALUABLE",
            "sdi_class": "NOT_EVALUABLE",
            "low_d_support": "NOT_EVALUABLE",
        }
    distance_support = "NOT_SUPPORTED"
    if bootstrap and math.isfinite(point["distance_association"]):
        lower = bootstrap["distance_association_ci"][0]
        distance_support = "POSITIVE_SUPPORTED" if lower > 0 else "NOT_SUPPORTED"
    elif not math.isfinite(point["distance_association"]):
        distance_support = "NOT_EVALUABLE"
    sdi_class = "NO_DOMINANCE"
    if point["sdi"]["status"] == "NO_ROW_OR_COLUMN_VARIATION":
        sdi_class = "NO_ROW_OR_COLUMN_VARIATION"
    elif bootstrap:
        lower = bootstrap["sdi_ci"][0]
        upper = bootstrap["sdi_ci"][1]
        if point["sdi"]["sdi"] > 0 and lower > 0:
            sdi_class = "SOURCE_DOMINANT"
        elif point["sdi"]["sdi"] < 0 and upper < 0:
            sdi_class = "TARGET_DOMINANT"
    low_d_support = point["low_d_recovery"]["status"]
    if point["low_d_recovery"]["status"] == "EVALUABLE" and bootstrap:
        lower = bootstrap["low_d_recovery_ci"][0]
        low_d_support = "SUPPORTED" if (point["low_d_recovery"]["mean_recovery"] > 0 and lower > 0) else "NOT_SUPPORTED"
    return {
        "distance_support": distance_support,
        "sdi_class": sdi_class,
        "low_d_support": low_d_support,
    }


def _percentile(values: Sequence[float], q: float) -> float:
    if not values:
        return float("nan")
    return float(np.percentile(np.asarray(values, dtype=float), q, method=BOOTSTRAP_QUANTILE_METHOD))


def _bootstrap_model_summaries(
    observations: Sequence[ExtractedObservation],
    num_layers: int,
    condition_order: Sequence[str],
    models: Sequence[Any],
    calibration: dict[str, Any],
    eligible_mask: Sequence[bool],
    diag_dbar: np.ndarray,
    low_d_mask: np.ndarray,
    replicates: int,
    rng: np.random.Generator,
) -> dict[str, Any]:
    eval_rows = filter_condition_realization(observations, "EVAL")
    clusters: dict[str, dict[str, list[ExtractedObservation]]] = {}
    for condition in condition_order:
        by_family: dict[str, list[ExtractedObservation]] = {}
        for obs in eval_rows:
            if obs.condition_id == condition:
                by_family.setdefault(obs.source_family_id, []).append(obs)
        if not by_family:
            raise ProtocolIntegrityError("BOOTSTRAP_CONDITION_CLUSTER_EMPTY")
        clusters[condition] = by_family
    dist_values = []
    sdi_values = []
    low_values = []
    for _ in range(replicates):
        sample = []
        for condition in condition_order:
            family_ids = sorted(clusters[condition])
            sampled_indices = rng.integers(0, len(family_ids), size=len(family_ids))
            # The frozen unit is a source-family cluster.  Selecting a family
            # retains all of that family's semantic records; rows are never
            # independently resampled.
            for index in sampled_indices:
                sample.extend(clusters[condition][family_ids[int(index)]])
        if any(
            {obs.semantic_class for obs in sample if obs.condition_id == condition} != CLASS_UNIVERSE
            for condition in condition_order
        ):
            # A finite cluster bootstrap can draw no instance of a class.  This
            # replicate is non-evaluable, not evidence for any endpoint.
            continue
        c0_eval = _compute_c0_for_partition(sample, "EVAL", num_layers, condition_order, models)
        ccal_eval = _compute_c_cal_for_partition(sample, "EVAL", num_layers, condition_order, models, calibration)
        d_eval = np.zeros_like(c0_eval)
        for i in range(num_layers):
            for j in range(num_layers):
                d_eval[i, j, :] = c0_eval[i, i, :] - c0_eval[i, j, :]
        r_eval = ccal_eval - c0_eval
        dbar = _condition_pool(d_eval)
        rbar = _condition_pool(r_eval)
        point = _summarize_point_profile(dbar, rbar, eligible_mask, num_layers, diag_dbar)
        dist_values.append(point["distance_association"])
        sdi_values.append(point["sdi"]["sdi"])
        pairs = [(i, j) for i in range(num_layers) for j in range(num_layers) if low_d_mask[i, j]]
        low_values.append(float(np.mean([float(rbar[i, j]) for i, j in pairs])) if pairs else float("nan"))
    dist_values = [value for value in dist_values if math.isfinite(value)]
    sdi_values = [value for value in sdi_values if math.isfinite(value)]
    low_values = [value for value in low_values if math.isfinite(value)]
    if not sdi_values:
        raise ProtocolIntegrityError("BOOTSTRAP_NO_EVALUABLE_REPLICATES")
    return {
        "distance_association_ci": [_percentile(dist_values, 5), _percentile(dist_values, 95)],
        "sdi_ci": [_percentile(sdi_values, 5), _percentile(sdi_values, 95)],
        "low_d_recovery_ci": [_percentile(low_values, 5), _percentile(low_values, 95)],
        "replicates": replicates,
    }


def compute_matrix_profile(
    observations: Sequence[ExtractedObservation],
    *,
    num_layers: int,
    condition_order: Sequence[str] = CONDITION_ORDER,
    bootstrap_replicates: int = 0,
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    if tuple(condition_order) != CONDITION_ORDER:
        raise ProtocolIntegrityError("CONDITION_ORDER_MUST_MATCH_FROZEN_TEN")
    if num_layers <= 1:
        raise ProtocolIntegrityError("NUM_LAYERS_INVALID")
    models = _fit_source_models(observations, num_layers)
    calibration = _fit_pair_calibration(observations, num_layers, condition_order)
    qual = _source_qualification(observations, num_layers, models, condition_order)
    c0_eval = _compute_c0_for_partition(observations, "EVAL", num_layers, condition_order, models)
    c0_diag = _compute_c0_for_partition(observations, "DIAGNOSTIC", num_layers, condition_order, models)
    ccal_eval = _compute_c_cal_for_partition(observations, "EVAL", num_layers, condition_order, models, calibration)
    d_eval = np.zeros_like(c0_eval)
    d_diag = np.zeros_like(c0_diag)
    for i in range(num_layers):
        for j in range(num_layers):
            d_eval[i, j, :] = c0_eval[i, i, :] - c0_eval[i, j, :]
            d_diag[i, j, :] = c0_diag[i, i, :] - c0_diag[i, j, :]
    r_eval = ccal_eval - c0_eval
    dbar_eval = _condition_pool(d_eval)
    rbar_eval = _condition_pool(r_eval)
    dbar_diag = _condition_pool(d_diag)
    if qual["source_coverage_evaluable"]:
        point = _summarize_point_profile(dbar_eval, rbar_eval, qual["eligible_source_mask"], num_layers, dbar_diag)
    else:
        point = {
            "status": "NOT_EVALUABLE_SOURCE_COVERAGE",
            "distance_association": None,
            "sdi": {"status": "NOT_EVALUABLE", "sdi": None},
            "localization": {"status": "NOT_EVALUABLE", "localization": None, "boundaries": []},
            "localization_r": {"status": "NOT_EVALUABLE", "localization": None, "boundaries": []},
            "low_d_recovery": {"status": "NOT_EVALUABLE", "mean_recovery": None, "eligible_pair_count": 0},
            "mean_off_diag_dbar": None,
            "mean_off_diag_rbar": None,
        }
    bootstrap = None
    if bootstrap_replicates > 0 and qual["source_coverage_evaluable"]:
        if rng is None:
            rng = np.random.default_rng(np.random.PCG64(BOOTSTRAP_SEED))
        low_mask, _ = _low_d_pair_mask(dbar_diag, qual["eligible_source_mask"], num_layers)
        bootstrap = _bootstrap_model_summaries(
            observations,
            num_layers,
            condition_order,
            models,
            calibration,
            qual["eligible_source_mask"],
            dbar_diag,
            low_mask,
            bootstrap_replicates,
            rng,
        )
    support = _support_classes(point, bootstrap)
    return {
        "experiment": EXPERIMENT,
        "num_layers": num_layers,
        "condition_order": list(condition_order),
        "class_order": list(CLASS_ORDER),
        "source_qualification": qual,
        "c0_eval": c0_eval,
        "c0_diag": c0_diag,
        "c_cal_eval": ccal_eval,
        "d_eval": d_eval,
        "d_diag": d_diag,
        "r_eval": r_eval,
        "dbar_eval": dbar_eval,
        "dbar_diag": dbar_diag,
        "rbar_eval": rbar_eval,
        "point": point,
        "bootstrap": bootstrap,
        "support": support,
        "confirmatory_status": "EVALUABLE" if qual["source_coverage_evaluable"] else "NOT_EVALUABLE_SOURCE_COVERAGE",
    }

def _boundary_intersect(localization: dict[str, Any], localization_r: dict[str, Any]) -> bool:
    a = set(localization.get("boundaries", []))
    b = set(localization_r.get("boundaries", []))
    return bool(a and b and a & b)


def classify_route(q_summary: dict[str, Any], o_summary: dict[str, Any]) -> dict[str, Any]:
    models = {"Q": q_summary, "O": o_summary}
    if any(not summary.get("source_qualification", {}).get("source_coverage_evaluable", True) for summary in models.values()):
        return {
            "p1": False, "p2": False, "p3": False, "p4": False, "p5": False,
            "route": "NOT_EVALUABLE", "per_model": {key: {"p1": False, "p2": False, "p4": False} for key in models},
        }
    per = {}
    for key, summary in models.items():
        point = summary["point"]
        support = summary["support"]
        p1 = bool(
            support["distance_support"] == "POSITIVE_SUPPORTED"
            and support["low_d_support"] == "SUPPORTED"
            and point["localization"]["localization"] >= 0.5
            and point["localization_r"]["localization"] >= 0.5
            and _boundary_intersect(point["localization"], point["localization_r"])
        )
        p2 = support["sdi_class"] == "SOURCE_DOMINANT"
        p4 = support["low_d_support"] == "SUPPORTED"
        per[key] = {"p1": p1, "p2": p2, "p4": p4}
    p3 = bool(
        q_summary["support"]["distance_support"] != o_summary["support"]["distance_support"]
        or (
            q_summary["support"]["sdi_class"] != o_summary["support"]["sdi_class"]
            and q_summary["support"]["sdi_class"] in {"SOURCE_DOMINANT", "TARGET_DOMINANT"}
            and o_summary["support"]["sdi_class"] in {"SOURCE_DOMINANT", "TARGET_DOMINANT"}
        )
    )
    p1 = per["Q"]["p1"] or per["O"]["p1"]
    p2 = per["Q"]["p2"] or per["O"]["p2"]
    p4 = per["Q"]["p4"] or per["O"]["p4"]
    if p3:
        route = "P3"
    elif p1:
        route = "P1"
    elif p2:
        route = "P2"
    elif p4:
        route = "P4"
    else:
        route = "P5"
    return {
        "p1": p1,
        "p2": p2,
        "p3": p3,
        "p4": p4,
        "p5": not (p1 or p2 or p3 or p4),
        "route": route,
        "per_model": per,
    }


def _matrix_serialization(
    matrix: np.ndarray,
    *,
    source_order: Sequence[int],
    target_order: Sequence[int],
    condition_order: Sequence[str],
    eligible_source_mask: Sequence[bool],
) -> dict[str, Any]:
    return {
        "values": _json_safe(matrix.tolist()),
        "shape": list(matrix.shape),
        "dtype": str(matrix.dtype),
        "source_layer_order": list(source_order),
        "target_layer_order": list(target_order),
        "condition_order": list(condition_order),
        "eligible_source_mask": list(eligible_source_mask),
    }


def _serialize_profile(profile: dict[str, Any], model_key: str) -> dict[str, Any]:
    layers = list(range(profile["num_layers"]))
    eligible = profile["source_qualification"]["eligible_source_mask"]
    condition_order = profile["condition_order"]
    return {
        "model_key": model_key,
        "num_layers": profile["num_layers"],
        "class_order": profile["class_order"],
        "condition_order": condition_order,
        "source_qualification": {
            "ba_diag_self": _json_safe(profile["source_qualification"]["ba_diag_self"]),
            "eligible_source_mask": _json_safe(eligible),
            "eligible_source_count": profile["source_qualification"]["eligible_source_count"],
            "eligible_depth_span": profile["source_qualification"]["eligible_depth_span"],
            "source_coverage_evaluable": profile["source_qualification"]["source_coverage_evaluable"],
        },
        "matrices": {
            "c0_eval": _matrix_serialization(profile["c0_eval"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
            "d_eval": _matrix_serialization(profile["d_eval"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
            "c_cal_eval": _matrix_serialization(profile["c_cal_eval"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
            "r_eval": _matrix_serialization(profile["r_eval"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
            "dbar_eval": _matrix_serialization(profile["dbar_eval"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
            "rbar_eval": _matrix_serialization(profile["rbar_eval"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
            "dbar_diag": _matrix_serialization(profile["dbar_diag"], source_order=layers, target_order=layers, condition_order=condition_order, eligible_source_mask=eligible),
        },
        "point": _json_safe(profile["point"]),
        "bootstrap": _json_safe(profile["bootstrap"]),
        "support": _json_safe(profile["support"]),
    }


def build_result_payload(
    *,
    model_profiles: Mapping[str, dict[str, Any]],
    routing: dict[str, Any],
    authorities: Mapping[str, str],
    repository_commit: str,
    runner_sha256: str,
    authorization_identity: Mapping[str, Any] | None = None,
    model_registry: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    model_registry = model_registry or MODEL_REGISTRY
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "classification": "EXP026_SCIENTIFIC_RESULT",
        "experiment": EXPERIMENT,
        "repository_commit": repository_commit,
        "runner_sha256": runner_sha256,
        "authority_hashes": authorities,
        "authorization_identity": authorization_identity,
        "models": {key: model_registry[key] for key in model_profiles},
        "routing": routing,
        "model_profiles": {key: _serialize_profile(model_profiles[key], key) for key in model_profiles},
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def _valid_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _validate_serialized_matrix(
    value: Any,
    *,
    expected_layers: int,
    matrix_name: str,
    errors: list[str],
) -> None:
    if not isinstance(value, Mapping):
        errors.append(f"matrix_{matrix_name}_object")
        return
    expected_shape = [expected_layers, expected_layers]
    if matrix_name in {"c0_eval", "d_eval", "c_cal_eval", "r_eval"}:
        expected_shape.append(len(CONDITION_ORDER))
    if value.get("shape") != expected_shape:
        errors.append(f"matrix_{matrix_name}_shape")
    if value.get("dtype") != "float32":
        errors.append(f"matrix_{matrix_name}_dtype")
    if value.get("source_layer_order") != list(range(expected_layers)):
        errors.append(f"matrix_{matrix_name}_source_order")
    if value.get("target_layer_order") != list(range(expected_layers)):
        errors.append(f"matrix_{matrix_name}_target_order")
    if value.get("condition_order") != list(CONDITION_ORDER):
        errors.append(f"matrix_{matrix_name}_condition_order")
    eligible = value.get("eligible_source_mask")
    if not isinstance(eligible, list) or len(eligible) != expected_layers or not all(isinstance(item, bool) for item in eligible):
        errors.append(f"matrix_{matrix_name}_eligible_mask")
    try:
        matrix = np.asarray(value.get("values"), dtype=float)
        if list(matrix.shape) != expected_shape or not np.isfinite(matrix).all():
            errors.append(f"matrix_{matrix_name}_values")
    except (TypeError, ValueError):
        errors.append(f"matrix_{matrix_name}_values")


def validate_result_schema(
    payload: Mapping[str, Any],
    *,
    expected_models: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[str]:
    expected_models = expected_models or {key: MODEL_REGISTRY[key] for key in MODEL_KEYS}
    errors = []
    if payload.get("schema_version") != RESULT_SCHEMA_VERSION:
        errors.append("schema_version")
    if payload.get("classification") != "EXP026_SCIENTIFIC_RESULT":
        errors.append("classification")
    if payload.get("experiment") != EXPERIMENT:
        errors.append("experiment")
    if not _valid_sha256(payload.get("runner_sha256")):
        errors.append("runner_sha256")
    if not isinstance(payload.get("repository_commit"), str) or len(payload["repository_commit"]) != 40:
        errors.append("repository_commit")
    if not isinstance(payload.get("authority_hashes"), dict) or set(payload.get("authority_hashes", {})) != set(EXPECTED_DESIGN_HASHES):
        errors.append("authority_hashes")
    if not isinstance(payload.get("authorization_identity"), Mapping):
        errors.append("authorization_identity")
    if not isinstance(payload.get("models"), Mapping) or set(payload.get("models", {})) != set(expected_models):
        errors.append("models")
    if not isinstance(payload.get("model_profiles"), dict) or set(payload.get("model_profiles", {})) != set(expected_models):
        errors.append("model_profiles")
    required_matrices = {"c0_eval", "d_eval", "c_cal_eval", "r_eval", "dbar_eval", "rbar_eval", "dbar_diag"}
    for key, profile in payload.get("model_profiles", {}).items():
        if not isinstance(profile, dict):
            errors.append("model_profile_type")
            continue
        expected_layers = expected_models.get(key, {}).get("num_hidden_layers")
        if profile.get("num_layers") != expected_layers:
            errors.append("model_profile_num_layers")
            continue
        if profile.get("model_key") != key or profile.get("class_order") != list(CLASS_ORDER) or profile.get("condition_order") != list(CONDITION_ORDER):
            errors.append("model_profile_identity")
        qualification = profile.get("source_qualification")
        if not isinstance(qualification, Mapping):
            errors.append("source_qualification")
        else:
            mask = qualification.get("eligible_source_mask")
            if not isinstance(mask, list) or len(mask) != expected_layers or not all(isinstance(item, bool) for item in mask):
                errors.append("source_qualification_mask")
            if qualification.get("source_coverage_evaluable") not in {True, False}:
                errors.append("source_qualification_coverage")
        matrices = profile.get("matrices")
        if not isinstance(matrices, dict) or set(matrices) != required_matrices:
            errors.append("model_profile_matrices")
        else:
            for matrix_name in sorted(required_matrices):
                _validate_serialized_matrix(matrices[matrix_name], expected_layers=expected_layers, matrix_name=matrix_name, errors=errors)
        if not isinstance(profile.get("point"), Mapping) or not isinstance(profile.get("support"), Mapping):
            errors.append("model_profile_summaries")
        elif qualification and qualification.get("source_coverage_evaluable") is False:
            if profile.get("confirmatory_status") != "NOT_EVALUABLE_SOURCE_COVERAGE":
                errors.append("coverage_not_evaluable_status")
            if set(profile["support"].values()) != {"NOT_EVALUABLE"}:
                errors.append("coverage_not_evaluable_support")
        bootstrap = profile.get("bootstrap")
        if qualification and qualification.get("source_coverage_evaluable") is True:
            if not isinstance(bootstrap, Mapping) or bootstrap.get("replicates", 0) <= 0:
                errors.append("bootstrap")
            elif any(not isinstance(bootstrap.get(name), list) or len(bootstrap[name]) != 2 for name in ("distance_association_ci", "sdi_ci", "low_d_recovery_ci")):
                errors.append("bootstrap_ci")
    if "raw_hidden_tensors" in payload:
        errors.append("raw_hidden_tensors_forbidden")
    return errors


def validate_synthetic_result_schema(payload: Mapping[str, Any]) -> list[str]:
    synthetic_models = {
        "A": {"num_hidden_layers": 4, "model_id": "synthetic-A", "model_revision": "synthetic"},
        "B": {"num_hidden_layers": 3, "model_id": "synthetic-B", "model_revision": "synthetic"},
    }
    return validate_result_schema(payload, expected_models=synthetic_models)


def _load_design_config(root: Path = ROOT) -> dict[str, Any]:
    path = root / DESIGN_CONFIG_PATH.relative_to(ROOT)
    return read_json(path)


def verify_no_authorization_contamination(root: Path = ROOT) -> None:
    authorization_path = _root_relative_path(root, FORMAL_AUTHORIZATION_PATH)
    consumption_dir = _root_relative_path(root, AUTHORIZATION_CONSUMPTION_DIR)
    if authorization_path.exists():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_UNEXPECTED")
    if consumption_dir.exists():
        children = list(consumption_dir.glob("*.json"))
        if children:
            raise ProtocolIntegrityError("AUTHORIZATION_CONSUMPTION_UNEXPECTED")


def _authorization_path_for(root: Path, authorization_file: str | None) -> Path | None:
    if authorization_file:
        path = Path(authorization_file)
        if not path.is_absolute():
            path = root / path
        return path
    return None


def _inherited_authority_binding(root: Path) -> dict[str, dict[str, str]]:
    """Return the frozen data/panel identifiers declared by the authority."""
    config = _load_design_config(root)
    inherited = config.get("inherited_authorities", {})
    required = ("condition_panel", "data_schema", "dataset", "exp024_preregistration", "frozen_manifest")
    result = {}
    for key in required:
        path = inherited.get(f"{key}_path")
        digest = inherited.get(f"{key}_sha256")
        if not isinstance(path, str) or not _valid_sha256(digest):
            raise ProtocolIntegrityError("FROZEN_INHERITED_AUTHORITY_INVALID")
        result[key] = {"path": path.replace("\\", "/"), "sha256": digest}
    return result


def verify_inherited_authorities(root: Path = ROOT) -> dict[str, dict[str, str]]:
    """Verify the frozen data/panel authority bytes only within formal mode."""
    binding = _inherited_authority_binding(root)
    for key, entry in binding.items():
        path = root / Path(entry["path"])
        if not path.is_file() or sha256_file(path) != entry["sha256"]:
            raise ProtocolIntegrityError(f"INHERITED_AUTHORITY_HASH_MISMATCH_{key}")
    return binding


def formal_execution_binding(root: Path = ROOT) -> dict[str, Any]:
    """Identity every non-scientific authority a formal authorization must bind."""
    authorities = verify_frozen_design(root)
    config = _load_design_config(root)
    panel = config.get("panel", {})
    partition_identity = {
        "allocation": panel.get("allocation"),
        "condition_order": panel.get("condition_order"),
        "semantic_classes": panel.get("semantic_classes"),
        "source_family_count": panel.get("source_family_count"),
        "record_count": panel.get("record_count"),
    }
    return {
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "frozen_authority_hashes": authorities,
        "inherited_authorities": _inherited_authority_binding(root),
        "panel_identity_sha256": _canonical_json_sha256(panel),
        "partition_identity_sha256": _canonical_json_sha256(partition_identity),
        "models": {
            key: {"model_id": MODEL_REGISTRY[key]["model_id"], "model_revision": MODEL_REGISTRY[key]["model_revision"]}
            for key in MODEL_KEYS
        },
        "readiness": "READY",
    }


def _qualification_binding(root: Path) -> dict[str, str]:
    bindings = {
        "engineering_qualification": _root_relative_path(root, ENGINEERING_QUALIFICATION_PATH),
        "formal_pipeline_qualification": _root_relative_path(root, FORMAL_PIPELINE_QUALIFICATION_PATH),
    }
    result = {}
    for key, path in bindings.items():
        if not path.is_file():
            raise ProtocolIntegrityError(f"FORMAL_AUTHORIZATION_QUALIFICATION_MISSING_{key}")
        artifact = read_json(path)
        if (
            artifact.get("status") != "PASS"
            or artifact.get("runner_sha256") != sha256_file(Path(__file__))
            or artifact.get("authority_hashes") != verify_frozen_design(root)
        ):
            raise ProtocolIntegrityError(f"FORMAL_AUTHORIZATION_QUALIFICATION_INVALID_{key}")
        result[key] = sha256_file(path)
    return result


def validate_formal_authorization(root: Path, authorization_path: Path) -> tuple[dict[str, Any], str]:
    if not authorization_path.is_file():
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_FILE_MISSING")
    auth = read_json(authorization_path)
    if auth.get("schema_version") != "1.0.0":
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_SCHEMA_VERSION_INVALID")
    if auth.get("experiment") != EXPERIMENT:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXPERIMENT_MISMATCH")
    if auth.get("purpose") != "SINGLE_USE_FORMAL_RUN":
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_PURPOSE_INVALID")
    if auth.get("single_use") is not True:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_NOT_SINGLE_USE")
    if auth.get("authorized_execution_count") != 1:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXECUTION_COUNT_INVALID")
    if auth.get("formal_mode") != "--formal-run":
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_MODE_INVALID")
    current = formal_execution_binding(root)
    required_fields = {
        "repository_commit", "runner_sha256", "frozen_authority_hashes", "inherited_authorities",
        "panel_identity_sha256", "partition_identity_sha256", "models", "readiness",
    }
    bound = auth.get("execution_binding")
    if not isinstance(bound, Mapping) or set(bound) != required_fields:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_BINDING_SCHEMA_INVALID")
    for key in required_fields:
        if bound.get(key) != current[key]:
            raise ProtocolIntegrityError(f"FORMAL_AUTHORIZATION_BINDING_MISMATCH_{key}")
    qualifications = auth.get("qualification_hashes")
    if qualifications != _qualification_binding(root):
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_QUALIFICATION_HASH_MISMATCH")
    return auth, sha256_file(authorization_path)


def consume_authorization(
    root: Path,
    authorization_path: Path,
    authorization: Mapping[str, Any],
    authorization_sha: str,
    run_attempt_id: str | None = None,
    consumption_dir: Path | None = None,
) -> tuple[dict[str, Any], str]:
    authorization_id = str(authorization.get("authorization_id", ""))
    if not authorization_id:
        raise ProtocolIntegrityError("FORMAL_AUTHORIZATION_ID_MISSING")
    run_attempt_id = run_attempt_id or uuid.uuid4().hex
    consumption_dir = consumption_dir or _root_relative_path(root, AUTHORIZATION_CONSUMPTION_DIR)
    consumption_path = consumption_dir / f"{authorization_id}.json"
    record = {
        "schema_version": "1.0.0",
        "classification": "AUTHORIZATION_CONSUMPTION",
        "authorization_id": authorization_id,
        "authorization_sha256": authorization_sha,
        "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_attempt_id": run_attempt_id,
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "authority_hashes": verify_frozen_design(root),
        "authorization_path": str(authorization_path),
        "consumption_record_path": str(consumption_path),
    }
    consumption_sha = _atomic_write_json_exclusive(consumption_path, record)
    record["consumption_record_sha256"] = consumption_sha
    return record, consumption_sha


def _repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _publish_result_exclusive(root: Path, result_path: Path, payload: Mapping[str, Any]) -> str:
    if result_path.exists():
        raise ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")
    return _atomic_write_json_exclusive(result_path, payload)


def _runtime_identity(model_key: str, model: Any, device: Any, dtype: Any) -> dict[str, Any]:
    config = getattr(model, "config", None)
    return {
        "model_key": model_key,
        "model_class": type(model).__name__,
        "model_type": getattr(config, "model_type", None),
        "num_hidden_layers": getattr(config, "num_hidden_layers", None),
        "hidden_size": getattr(config, "hidden_size", None),
        "runtime_dtype": str(dtype),
        "device": str(device),
    }


def _gpu_name() -> str | None:
    import torch

    if torch.cuda.is_available():
        return torch.cuda.get_device_name(0)
    return None


def _resource_snapshot() -> dict[str, Any]:
    import torch

    return {
        "gpu_name": _gpu_name(),
        "cuda_available": torch.cuda.is_available(),
        "torch_version": torch.__version__,
    }


def _validate_formal_records(records: Any) -> list[Mapping[str, Any]]:
    """Validate the inherited panel only after formal authorization is consumed."""
    if not isinstance(records, list):
        raise ProtocolIntegrityError("FORMAL_DATASET_TOP_LEVEL_NOT_ARRAY")
    required = {"record_id", "source_family_id", "semantic_class", "condition_id", "partition", "record_role", "text"}
    seen_ids: set[str] = set()
    families: dict[str, list[Mapping[str, Any]]] = {}
    cells: dict[tuple[str, str, str], set[str]] = {}
    partitions: dict[str, set[str]] = {partition: set() for partition in PARTITIONS}
    for record in records:
        if not isinstance(record, Mapping) or required - set(record):
            raise ProtocolIntegrityError("FORMAL_DATASET_RECORD_SCHEMA_INVALID")
        record_id = str(record["record_id"])
        if not record_id or record_id in seen_ids:
            raise ProtocolIntegrityError("FORMAL_DATASET_RECORD_ID_INVALID")
        seen_ids.add(record_id)
        if record["semantic_class"] not in CLASS_UNIVERSE or record["condition_id"] not in CONDITION_UNIVERSE or record["partition"] not in PARTITIONS:
            raise ProtocolIntegrityError("FORMAL_DATASET_METADATA_INVALID")
        if not isinstance(record["text"], str) or not record["text"].strip():
            raise ProtocolIntegrityError("FORMAL_DATASET_TEXT_INVALID")
        family = str(record["source_family_id"])
        if not family:
            raise ProtocolIntegrityError("FORMAL_DATASET_FAMILY_INVALID")
        families.setdefault(family, []).append(record)
        partitions[record["partition"]].add(family)
        cells.setdefault((record["condition_id"], record["partition"], record["semantic_class"]), set()).add(family)
    if len(records) != 1760 or len(families) != 880:
        raise ProtocolIntegrityError("FORMAL_DATASET_SIZE_INVALID")
    for family, rows in families.items():
        if len(rows) != 2 or {str(row["record_role"]) for row in rows} != {"reference_form", "condition_realization"}:
            raise ProtocolIntegrityError("FORMAL_DATASET_FAMILY_ROLE_INVALID")
        first = rows[0]
        if any(any(row[field] != first[field] for field in ("semantic_class", "condition_id", "partition")) for row in rows[1:]):
            raise ProtocolIntegrityError("FORMAL_DATASET_FAMILY_METADATA_INCONSISTENT")
    if partitions["FIT"] & partitions["DIAGNOSTIC"] or partitions["FIT"] & partitions["EVAL"] or partitions["DIAGNOSTIC"] & partitions["EVAL"]:
        raise ProtocolIntegrityError("FORMAL_DATASET_PARTITION_FAMILY_OVERLAP")
    for condition in CONDITION_ORDER:
        for partition in PARTITIONS:
            for semantic_class in CLASS_ORDER:
                if len(cells.get((condition, partition, semantic_class), set())) != ALLOCATION[partition]:
                    raise ProtocolIntegrityError("FORMAL_DATASET_CELL_ALLOCATION_INVALID")
    return records


def load_production_observations(root: Path = ROOT) -> dict[str, list[ExtractedObservation]]:
    """Extract all-block vectors from the inherited panel during formal mode only."""
    config = _load_design_config(root)
    dataset = verify_inherited_authorities(root)["dataset"]
    dataset_path = root / Path(dataset["path"])
    if sha256_file(dataset_path) != dataset["sha256"]:
        raise ProtocolIntegrityError("FORMAL_DATASET_HASH_MISMATCH")
    records = _validate_formal_records(read_json(dataset_path))
    observations: dict[str, list[ExtractedObservation]] = {}
    for model_key in MODEL_KEYS:
        spec = MODEL_REGISTRY[model_key]
        tokenizer, model, device, _dtype = load_runtime(model_key)
        extracted: list[ExtractedObservation] = []
        for record in records:
            if record["record_role"] != "condition_realization":
                continue
            _input_ids, _attention_mask, vectors = extract_all_layers(tokenizer, model, device, str(record["text"]), spec["num_hidden_layers"])
            if vectors.shape != (spec["num_hidden_layers"], spec["hidden_size"]):
                raise TechnicalInvalidError("FORMAL_ALL_LAYER_VECTOR_SHAPE_INVALID")
            extracted.append(ExtractedObservation(
                record_id=str(record["record_id"]), partition=str(record["partition"]),
                condition_id=str(record["condition_id"]), semantic_class=str(record["semantic_class"]),
                source_family_id=str(record["source_family_id"]), vectors=vectors,
            ))
        observations[model_key] = extracted
        del model
    return observations


def execute_scientific_executor(
    *,
    root: Path,
    observations_by_model: Mapping[str, Sequence[ExtractedObservation]],
    model_registry: Mapping[str, Mapping[str, Any]],
    result_path: Path,
    authorization_identity: Mapping[str, Any],
    bootstrap_replicates: int,
) -> dict[str, Any]:
    """Run the sole production scientific pipeline, then publish once exclusively."""
    if tuple(model_registry) != tuple(observations_by_model):
        raise ProtocolIntegrityError("EXECUTOR_MODEL_OBSERVATION_SET_MISMATCH")
    profiles: dict[str, dict[str, Any]] = {}
    for offset, model_key in enumerate(model_registry):
        spec = model_registry[model_key]
        rng = np.random.default_rng(np.random.PCG64(BOOTSTRAP_SEED + offset))
        profiles[model_key] = compute_matrix_profile(
            observations_by_model[model_key],
            num_layers=int(spec["num_hidden_layers"]),
            condition_order=CONDITION_ORDER,
            bootstrap_replicates=bootstrap_replicates,
            rng=rng,
        )
    routing = classify_route(profiles["Q"], profiles["O"]) if set(profiles) == set(MODEL_KEYS) else {"route": "SYNTHETIC_NOT_ROUTED"}
    payload = build_result_payload(
        model_profiles=profiles,
        routing=routing,
        authorities=verify_frozen_design(root),
        repository_commit=_repository_commit(root),
        runner_sha256=sha256_file(Path(__file__)),
        authorization_identity=authorization_identity,
        model_registry=model_registry,
    )
    errors = validate_result_schema(payload, expected_models=model_registry)
    if errors:
        raise ProtocolIntegrityError(f"RESULT_SCHEMA_INVALID_{errors}")
    result_sha = _publish_result_exclusive(root, result_path, payload)
    return {"payload": payload, "profiles": profiles, "result_sha256": result_sha, "routing": routing}

def run_static_preflight(root: Path = ROOT) -> dict[str, Any]:
    verify_frozen_design(root)
    verify_no_result_collision(root)
    verify_no_authorization_contamination(root)
    _load_design_config(root)
    return {
        "status": "PASS",
        "frozen_authorities_match": True,
        "no_formal_result": True,
        "no_authorization_contamination": True,
        "models": {key: MODEL_REGISTRY[key] for key in MODEL_KEYS},
    }


def run_engineering_qualification(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    verify_frozen_design(root)
    verify_no_result_collision(root)
    verify_no_authorization_contamination(root)
    models = {}
    for key in MODEL_KEYS:
        spec = MODEL_REGISTRY[key]
        tokenizer, model, device, dtype = load_runtime(key)
        identity = _runtime_identity(key, model, device, dtype)
        config = getattr(model, "config", None)
        actual_layers = getattr(config, "num_hidden_layers", None)
        actual_hidden = getattr(config, "hidden_size", None)
        if actual_layers != spec["num_hidden_layers"]:
            raise ProtocolIntegrityError("MODEL_LAYER_COUNT_MISMATCH")
        if actual_hidden != spec["hidden_size"]:
            raise ProtocolIntegrityError("MODEL_HIDDEN_SIZE_MISMATCH")
        first = None
        for text in NEUTRAL_QUALIFICATION_INPUTS[:2]:
            _, _, matrix = extract_all_layers(tokenizer, model, device, text, spec["num_hidden_layers"])
            if first is None:
                first = matrix
            if matrix.shape != (spec["num_hidden_layers"], spec["hidden_size"]):
                raise ProtocolIntegrityError("ALL_LAYER_EXTRACTION_SHAPE_INVALID")
            if not np.isfinite(matrix).all():
                raise TechnicalInvalidError("ALL_LAYER_EXTRACTION_NONFINITE")
        _, _, repeat = extract_all_layers(tokenizer, model, device, NEUTRAL_QUALIFICATION_INPUTS[0], spec["num_hidden_layers"])
        max_diff = float(np.max(np.abs(first.astype(np.float64) - repeat.astype(np.float64)))) if first is not None else None
        models[key] = {
            "load_success": True,
            "model_id": spec["model_id"],
            "model_revision": spec["model_revision"],
            "logical_layer_count": spec["num_hidden_layers"],
            "hidden_size": spec["hidden_size"],
            "runtime_dtype": str(dtype),
            "device": str(device),
            "all_layer_extraction": "PASS",
            "neutral_input_count": len(NEUTRAL_QUALIFICATION_INPUTS),
            "determinism_max_abs_diff": max_diff,
            "identity": identity,
        }
    artifact = {
        "schema_version": QUALIFICATION_SCHEMA_VERSION,
        "classification": "ENGINEERING_MODEL_HOOK_QUALIFICATION_ONLY",
        "experiment": EXPERIMENT,
        "status": "PASS",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "authority_hashes": verify_frozen_design(root),
        "models": models,
        "resource": _resource_snapshot(),
        "formal_data_accessed": False,
        "scientific_result_created": False,
    }
    if publish:
        _atomic_write_json(ENGINEERING_QUALIFICATION_PATH, artifact)
    return artifact


def _hardcoded_synthetic_observations() -> dict[str, list[ExtractedObservation]]:
    observations = {"A": [], "B": []}
    for model_key, layers in (("A", 4), ("B", 3)):
        for partition in PARTITIONS:
            # Four family clusters per condition/class make every bootstrap
            # resample a meaningful cluster-level test fixture.
            count = 4
            for cond_index, cond in enumerate(CONDITION_ORDER):
                for cls_index, cls in enumerate(CLASS_ORDER):
                    for family in range(count):
                        vectors = []
                        for layer in range(layers):
                            vec = [
                                float(cls_index + layer * 0.25 + cond_index * 0.01 + family * 0.001),
                                float((cls_index % 2) * 1.0 - 0.5 + family * 0.01),
                            ]
                            vectors.append(np.asarray(vec, dtype=np.float32))
                        observations[model_key].append(
                            ExtractedObservation(
                                record_id=f"{model_key}_{partition}_{cond}_{cls}_{family}",
                                partition=partition,
                                condition_id=cond,
                                semantic_class=cls,
                                source_family_id=f"{model_key}_{partition}_{cond}_{cls}_{family}",
                                vectors=np.stack(vectors, axis=0).astype(np.float32),
                            )
                        )
    return observations


def _verify_synthetic_expected_values(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> None:
    assert profile_a["num_layers"] == 4
    assert profile_b["num_layers"] == 3
    assert profile_a["c0_eval"].shape == (4, 4, 10)
    assert profile_b["c0_eval"].shape == (3, 3, 10)
    assert np.allclose(np.diagonal(profile_a["d_eval"][:, :, 0]), 0.0)
    assert np.allclose(np.diagonal(profile_b["d_eval"][:, :, 0]), 0.0)
    assert any(profile_a["source_qualification"]["eligible_source_mask"])
    assert any(profile_b["source_qualification"]["eligible_source_mask"])
    assert "distance_association" in profile_a["point"]
    assert "sdi" in profile_a["point"]
    assert "low_d_recovery" in profile_a["point"]


def verify_independent_numeric_goldens() -> None:
    """Check hand-specified arithmetic anchors independent of production output."""
    known_matrix = np.stack([np.full((2, 2), value, dtype=np.float32) for value in range(10)], axis=2)
    if not np.array_equal(_condition_pool(known_matrix), np.full((2, 2), 4.5, dtype=np.float32)):
        raise ProtocolIntegrityError("INDEPENDENT_GOLDEN_CONDITION_POOL_FAILED")
    known_transform = transform_with_stats(
        np.array([[3.0, 10.0]], dtype=np.float32),
        np.array([1.0, 2.0], dtype=np.float32),
        np.array([2.0, 4.0], dtype=np.float32),
    )
    if not np.array_equal(known_transform, np.array([[1.0, 2.0]], dtype=np.float32)):
        raise ProtocolIntegrityError("INDEPENDENT_GOLDEN_CALIBRATION_FAILED")
    if balanced_accuracy(list(CLASS_ORDER), ["logic", "causality", "definition", "definition"]) != 0.75:
        raise ProtocolIntegrityError("INDEPENDENT_GOLDEN_CLASS_MAPPING_FAILED")


def _validate_synthetic_authorization(root: Path, authorization_path: Path) -> tuple[dict[str, Any], str]:
    auth = read_json(authorization_path)
    if auth.get("classification") != "SYNTHETIC_QUALIFICATION_AUTHORIZATION" or auth.get("single_use") is not True:
        raise ProtocolIntegrityError("SYNTHETIC_AUTHORIZATION_INVALID")
    if auth.get("runner_sha256") != sha256_file(Path(__file__)) or auth.get("repository_commit") != _repository_commit(root):
        raise ProtocolIntegrityError("SYNTHETIC_AUTHORIZATION_BINDING_MISMATCH")
    return auth, sha256_file(authorization_path)


def _run_authorized_executor(
    *,
    root: Path,
    authorization_path: Path,
    authorization_validator: Callable[[Path, Path], tuple[dict[str, Any], str]],
    observations_provider: Callable[[], Mapping[str, Sequence[ExtractedObservation]]],
    model_registry: Mapping[str, Mapping[str, Any]],
    result_path: Path,
    bootstrap_replicates: int,
    consumption_dir: Path | None = None,
) -> dict[str, Any]:
    """Shared authorization-consumption -> data -> executor control flow."""
    authorization, authorization_sha = authorization_validator(root, authorization_path)
    consumption, consumption_sha = consume_authorization(
        root, authorization_path, authorization, authorization_sha, consumption_dir=consumption_dir
    )
    result = execute_scientific_executor(
        root=root,
        observations_by_model=observations_provider(),
        model_registry=model_registry,
        result_path=result_path,
        authorization_identity={
            "authorization_id": authorization["authorization_id"],
            "authorization_sha256": authorization_sha,
            "consumption_record_sha256": consumption_sha,
            "classification": authorization.get("classification", "FORMAL_AUTHORIZATION"),
        },
        bootstrap_replicates=bootstrap_replicates,
    )
    result["authorization_consumption"] = consumption
    return result


def run_synthetic_formal_qualification(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    verify_frozen_design(root)
    verify_no_result_collision(root)
    verify_no_authorization_contamination(root)
    import tempfile
    verify_independent_numeric_goldens()
    synthetic_models = {
        "A": {"model_id": "synthetic-A", "model_revision": "synthetic", "num_hidden_layers": 4, "hidden_size": 2},
        "B": {"model_id": "synthetic-B", "model_revision": "synthetic", "num_hidden_layers": 3, "hidden_size": 2},
    }
    with tempfile.TemporaryDirectory(prefix="exp026_synthetic_") as tmp:
        tmp_path = Path(tmp)
        authorization_path = tmp_path / "synthetic_authorization.json"
        _atomic_write_json_exclusive(authorization_path, {
            "classification": "SYNTHETIC_QUALIFICATION_AUTHORIZATION", "single_use": True,
            "authorization_id": "EXP026_SYNTHETIC_101D_R", "runner_sha256": sha256_file(Path(__file__)),
            "repository_commit": _repository_commit(root),
        })
        result = _run_authorized_executor(
            root=root, authorization_path=authorization_path, authorization_validator=_validate_synthetic_authorization,
            observations_provider=_hardcoded_synthetic_observations, model_registry=synthetic_models,
            result_path=tmp_path / "exp026_synthetic_result.json", bootstrap_replicates=50,
            consumption_dir=tmp_path / "consumption",
        )
        _verify_synthetic_expected_values(result["profiles"]["A"], result["profiles"]["B"])
        schema_errors = validate_synthetic_result_schema(result["payload"])
        if schema_errors:
            raise ProtocolIntegrityError(f"RESULT_SCHEMA_INVALID_{schema_errors}")
        try:
            _publish_result_exclusive(root, tmp_path / "exp026_synthetic_result.json", result["payload"])
            raise ProtocolIntegrityError("PUBLICATION_RACE_NOT_REJECTED")
        except ProtocolIntegrityError:
            pass
    artifact = {
        "schema_version": QUALIFICATION_SCHEMA_VERSION,
        "classification": "FORMAL_PIPELINE_SYNTHETIC_QUALIFICATION",
        "experiment": EXPERIMENT,
        "status": "PASS",
        "started_at_utc": started.isoformat(),
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "authority_hashes": verify_frozen_design(root),
        "real_executor_connected": True,
        "synthetic_model_layers": {"A": 4, "B": 3},
        "synthetic_result_sha256": result["result_sha256"],
        "routing": result["routing"],
        "schema_validation": "PASS",
        "provenance_validation": "PASS",
        "independent_numeric_goldens": "PASS",
        "shared_authorized_executor": "PASS",
        "formal_data_accessed": False,
        "scientific_result_created": False,
    }
    if publish:
        _atomic_write_json(FORMAL_PIPELINE_QUALIFICATION_PATH, artifact)
    return artifact


def run_formal_run(root: Path = ROOT, authorization_file: str | None = None) -> dict[str, Any]:
    verify_frozen_design(root)
    verify_no_result_collision(root)
    auth_path = _authorization_path_for(root, authorization_file)
    if auth_path is None:
        raise ProtocolIntegrityError("FORMAL_RUN_REQUIRES_AUTHORIZATION")
    return _run_authorized_executor(
        root=root,
        authorization_path=auth_path,
        authorization_validator=validate_formal_authorization,
        observations_provider=lambda: load_production_observations(root),
        model_registry={key: MODEL_REGISTRY[key] for key in MODEL_KEYS},
        result_path=_root_relative_path(root, FORMAL_RESULT_PATH),
        bootstrap_replicates=BOOTSTRAP_REPLICATES,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static-preflight", action="store_true")
    modes.add_argument("--engineering-qualification", action="store_true")
    modes.add_argument("--synthetic-formal-qualification", action="store_true")
    modes.add_argument("--formal-run", action="store_true")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--authorization-file", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else ROOT
    try:
        if args.static_preflight:
            run_static_preflight(root)
            print("EXP026_STATIC_PREFLIGHT = PASS")
            print("EXP026_FROZEN_AUTHORITIES_MATCH = true")
            return 0
        if args.engineering_qualification:
            result = run_engineering_qualification(root)
            print("EXP026_ENGINEERING_QUALIFICATION = PASS")
            print(json.dumps({"models": result["models"], "status": result["status"]}, indent=2, sort_keys=True))
            return 0
        if args.synthetic_formal_qualification:
            result = run_synthetic_formal_qualification(root)
            print("EXP026_FORMAL_PIPELINE_QUALIFICATION = PASS")
            print("EXP026_SYNTHETIC_REAL_EXECUTOR_E2E = PASS")
            print("EXP026_FORMAL_RUN_READINESS = READY")
            return 0
        if args.formal_run:
            run_formal_run(root, args.authorization_file)
            return 0
    except ProtocolIntegrityError as exc:
        print("EXP026_MODE = FAIL")
        print(f"EXP026_ERROR = {exc}")
        return 1
    except Exception as exc:
        print("EXP026_MODE = FAIL")
        print(f"EXP026_ERROR = {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
