"""EXP-020A runner with explicit formal-run authorization and non-formal preflight.

The formal path is implemented but intentionally inaccessible without a future,
separately created authorization artifact. Importing this module has no I/O.
"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import os
import platform
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXP_DIR = Path(__file__).resolve().parent
FROZEN_CONFIG_PATH = EXP_DIR / "exp020_frozen_config.json"
SPEC_PATH = EXP_DIR / "exp020_implementation_spec.json"
PREREGISTRATION_PATH = ROOT / "docs" / "experiments" / "EXP-020-PREREGISTRATION.md"
AUTHORIZATION_PATH = EXP_DIR / "exp020_formal_run_authorization.json"
CANONICAL_RESULT_PATH = EXP_DIR / "results" / "exp020a_results.json"
PREFLIGHT_OUTPUT_PATH = EXP_DIR / "results" / "runner_preflight.json"
PROMPT_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
NEUTRAL_TEXT = "This is a neutral hardware diagnostic."
AUTHORIZATION_SCHEMA_VERSION = "1.0.0"
RESULT_SCHEMA_VERSION = "1.0.0"
FORMAL_AUTHORIZATION_SCOPE = ["formal_fit_eval_inference", "atomic_scientific_result_publication"]
LEGACY_FORMAL_RESULT_FILENAMES = (
    "transition_metrics.csv", "probe_metrics.csv", "invariant_metrics.csv", "pair_summary.csv",
    "representation_summary.json", "validation_summary.json", "behavioral_outputs.csv",
    "effect_rows.json", "probe_rows.json", "transition_rows.json", "pair_rows.json",
)
AUTHORIZATION_FIELDS = frozenset({
    "schema_version", "experiment", "formal_run_authorized", "scope", "single_use",
    "runner_commit", "frozen_config_path", "frozen_config_sha256",
    "preregistration_path", "preregistration_sha256", "prompt_file", "prompt_file_sha256",
    "source_conditions_file", "source_conditions_sha256", "split_transition_manifest_path",
    "split_transition_manifest_sha256", "model_id", "model_revision", "model_canonical_path",
    "model_config_path", "model_config_sha256", "tokenizer_identity", "tokenizer_revision",
    "created_at", "authorization_id",
})


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _canonical_result_path(root: Path = ROOT) -> Path:
    return root / "experiments" / "exp020" / "results" / "exp020a_results.json"


def _ambiguous_formal_result_paths(root: Path = ROOT) -> list[Path]:
    """Return legacy paths that could be mistaken for a formal scientific result."""
    paths: list[Path] = []
    legacy_output_dir = root / "results" / "exp020"
    if legacy_output_dir.exists():
        paths.append(legacy_output_dir)
    engineering_results = root / "experiments" / "exp020" / "results"
    for name in LEGACY_FORMAL_RESULT_FILENAMES:
        candidate = engineering_results / name
        if candidate.exists():
            paths.append(candidate)
    return paths


def _require_no_formal_results(root: Path = ROOT) -> None:
    canonical = _canonical_result_path(root)
    if canonical.exists():
        raise RuntimeError(f"Formal output already exists: {canonical}")
    if paths := _ambiguous_formal_result_paths(root):
        raise RuntimeError(f"Ambiguous formal output already exists: {paths[0]}")


def _current_commit(root: Path = ROOT) -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def _relative_path(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _tracked_worktree_clean(root: Path = ROOT) -> bool:
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return not completed.stdout.strip()


def _strict_authorization_json(path: Path) -> dict[str, Any]:
    def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
            value[key] = item
        return value

    try:
        parsed = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, PermissionError) as exc:
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED") from exc
    if not isinstance(parsed, dict) or set(parsed) != AUTHORIZATION_FIELDS:
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    return parsed


def _derive_frozen_bindings(root: Path = ROOT) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Derive current LEVEL-1 authority bindings without opening prompt text."""
    config_path = root / _relative_path(FROZEN_CONFIG_PATH, ROOT)
    spec_path = root / _relative_path(SPEC_PATH, ROOT)
    preregistration_path = root / _relative_path(PREREGISTRATION_PATH, ROOT)
    config, spec = _json(config_path), _json(spec_path)
    authority = spec["authority_references"]
    dataset, model = config["dataset"], config["model"]
    prompt_path = root / dataset["prompt_file"]
    source_path = root / dataset["source_conditions_file"]
    model_config_path = Path(model["canonical_path"]) / "config.json"
    try:
        source = _json(source_path)
        split_manifest_hash = hashlib.sha256(
            _canonical_json({"splits": source["splits"], "ordered_transitions": source["ordered_transitions"], "groups": source["groups"]}).encode("utf-8")
        ).hexdigest()
        observed = {
            "frozen_config_path": _relative_path(config_path, root),
            "frozen_config_sha256": _sha256(config_path),
            "preregistration_path": _relative_path(preregistration_path, root),
            "preregistration_sha256": _sha256(preregistration_path),
            "prompt_file": dataset["prompt_file"],
            "prompt_file_sha256": _sha256(prompt_path),
            "source_conditions_file": dataset["source_conditions_file"],
            "source_conditions_sha256": _sha256(source_path),
            "split_transition_manifest_path": dataset["source_conditions_file"],
            "split_transition_manifest_sha256": split_manifest_hash,
            "model_id": model["model_id"],
            "model_revision": model["revision"],
            "model_canonical_path": model["canonical_path"],
            "model_config_path": str(model_config_path),
            "model_config_sha256": _sha256(model_config_path),
            "tokenizer_identity": spec["semantic_rules"]["tokenizer_effective_defaults"]["value"]["tokenizer_class"],
            "tokenizer_revision": spec["semantic_rules"]["tokenizer_effective_defaults"]["value"]["revision"],
        }
    except (KeyError, OSError, TypeError, ValueError) as exc:
        raise PermissionError("FORMAL_RUN_BLOCKED_INTEGRITY_MISMATCH") from exc
    expected = {
        "frozen_config_path": authority["frozen_config_path"],
        "frozen_config_sha256": authority["frozen_config_sha256"],
        "preregistration_path": authority["preregistration_path"],
        "preregistration_sha256": authority["preregistration_sha256"],
        "prompt_file": dataset["prompt_file"],
        "prompt_file_sha256": dataset["prompt_file_sha256"],
        "source_conditions_file": dataset["source_conditions_file"],
        "source_conditions_sha256": dataset["source_conditions_sha256"],
        "split_transition_manifest_path": dataset["source_conditions_file"],
        "split_transition_manifest_sha256": dataset["split_transition_manifest_sha256"],
        "model_id": spec["fixed_protocol"]["model_id"],
        "model_revision": spec["fixed_protocol"]["revision"],
        "model_canonical_path": spec["fixed_protocol"]["canonical_path"],
        "model_config_path": str(model_config_path),
        "model_config_sha256": spec["fixed_protocol"]["config_sha256"],
        "tokenizer_identity": spec["semantic_rules"]["tokenizer_effective_defaults"]["value"]["tokenizer_class"],
        "tokenizer_revision": spec["semantic_rules"]["tokenizer_effective_defaults"]["value"]["revision"],
    }
    if observed != expected:
        raise PermissionError("FORMAL_RUN_BLOCKED_INTEGRITY_MISMATCH")
    return expected, config, spec


def _validate_authorization_types(authorization: dict[str, Any]) -> None:
    expected_scalars = {
        "schema_version": AUTHORIZATION_SCHEMA_VERSION,
        "experiment": "EXP-020A",
        "formal_run_authorized": True,
        "single_use": True,
    }
    for key, expected in expected_scalars.items():
        if authorization.get(key) != expected or type(authorization[key]) is not type(expected):
            raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    if authorization["scope"] != FORMAL_AUTHORIZATION_SCOPE or not all(isinstance(item, str) for item in authorization["scope"]):
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    for key in AUTHORIZATION_FIELDS - {"schema_version", "experiment", "formal_run_authorized", "scope", "single_use", "created_at", "authorization_id"}:
        if not isinstance(authorization[key], str) or not authorization[key]:
            raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    try:
        timestamp = authorization["created_at"].replace("Z", "+00:00")
        datetime.fromisoformat(timestamp)
        uuid.UUID(authorization["authorization_id"])
    except (AttributeError, ValueError) as exc:
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED") from exc


def validate_formal_authorization(root: Path = ROOT) -> dict[str, Any]:
    """Fail closed before formal source, model, output, or RNG access."""
    path = AUTHORIZATION_PATH if AUTHORIZATION_PATH.is_absolute() else root / AUTHORIZATION_PATH
    if not path.is_file():
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    authorization = _strict_authorization_json(path)
    _validate_authorization_types(authorization)
    if not _tracked_worktree_clean(root):
        raise PermissionError("FORMAL_RUN_BLOCKED_DIRTY_TRACKED_WORKTREE")
    expected, config, spec = _derive_frozen_bindings(root)
    current_commit = _current_commit(root)
    if authorization["runner_commit"] != current_commit:
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    for key, value in expected.items():
        if authorization[key] != value:
            raise PermissionError("FORMAL_RUN_BLOCKED_INTEGRITY_MISMATCH")
    return {
        "authorization": authorization,
        "authorization_path": str(path),
        "authorization_sha256": _sha256(path),
        "bindings": expected,
        "config": config,
        "spec": spec,
        "runner_commit": current_commit,
    }


def _run_validator(path: Path) -> None:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run([sys.executable, str(path)], cwd=ROOT, env=environment, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(f"Validator failed: {path.name}")


def validate_static_environment(config: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    """Check frozen identity, versions, local config hash, and no-network prerequisites."""
    import torch
    import transformers

    model = config["model"]
    fixed = spec["fixed_protocol"]
    expected = {
        "model_id": "Qwen/Qwen3-4B", "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
        "canonical_path": r"D:\Qwen3-4B-transfer", "local_files_only": True, "dtype": "bfloat16",
        "device": "cuda:0", "architecture": "Qwen3ForCausalLM", "model_type": "qwen3",
        "num_transformer_blocks": 36, "hidden_size": 2560, "vocab_size": 151936,
        "execution_mode": "MODE_A_NATIVE",
    }
    if {key: model.get(key) for key in expected} != expected:
        raise RuntimeError("RUNNER_PREFLIGHT_INVALID_ENVIRONMENT")
    if fixed["config_sha256"] != model["config_sha256"]:
        raise RuntimeError("RUNNER_PREFLIGHT_INVALID_ENVIRONMENT")
    model_path = Path(model["canonical_path"])
    config_path = model_path / "config.json"
    if not config_path.is_file() or _sha256(config_path) != model["config_sha256"]:
        raise RuntimeError("RUNNER_PREFLIGHT_INVALID_ENVIRONMENT")
    if transformers.__version__ != "5.14.1" or torch.__version__ != "2.12.1+cu130":
        raise RuntimeError("RUNNER_PREFLIGHT_INVALID_ENVIRONMENT")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        raise RuntimeError("RUNNER_PREFLIGHT_INVALID_ENVIRONMENT")
    return {"model_config_present": True, "config_sha256_match": True, "transformers": transformers.__version__, "torch": torch.__version__, "cuda_available": True, "bf16_supported": True}


def static_preflight() -> dict[str, Any]:
    """Perform metadata-only checks without opening formal prompt content or weights."""
    _run_validator(EXP_DIR / "validate_exp020_preregistration.py")
    _run_validator(EXP_DIR / "validate_exp020_implementation_spec.py")
    config, spec = _json(FROZEN_CONFIG_PATH), _json(SPEC_PATH)
    environment = validate_static_environment(config, spec)
    _require_no_formal_results()
    if AUTHORIZATION_PATH.exists():
        raise RuntimeError("RUNNER_PREFLIGHT_FAILED")
    return {
        "status": "STATIC_PREFLIGHT_PASS", "formal_scientific_execution": "NOT_RUN",
        "formal_fit_eval_inference": False, "formal_scientific_results": False,
        "authorization_artifact_present": False, "formal_result_present": False,
        "model": {"id": config["model"]["model_id"], "revision": config["model"]["revision"], "config_sha256": config["model"]["config_sha256"]},
        "environment": environment, "planned": {"primary": spec["fixed_protocol"]["primary"], "secondary": spec["fixed_protocol"]["secondary"]},
    }


def neutral_model_preflight() -> dict[str, Any]:
    """Run one local-only neutral forward and discard all transient tensors immediately."""
    report = static_preflight()
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer
    from src.extraction import extract_last_token_hidden_state, move_tokenized_inputs_to_device, tensor_to_numpy_float32

    config = _json(FROZEN_CONFIG_PATH)
    model_info = config["model"]
    path = Path(model_info["canonical_path"])
    started = time.perf_counter()
    model_config = AutoConfig.from_pretrained(path, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(path, local_files_only=True, dtype=torch.bfloat16, device_map={"": 0}, low_cpu_mem_usage=True)
    model.eval()
    tokenized = tokenizer(NEUTRAL_TEXT, return_tensors="pt")
    inputs = move_tokenized_inputs_to_device(tokenized, torch.device("cuda:0"))
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, return_dict=True)
    primary = tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, 19))
    secondary = tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, 27))
    valid = (
        model.__class__.__name__ == "Qwen3ForCausalLM" and model_config.model_type == "qwen3"
        and len(model.model.layers) == 36 and model_config.hidden_size == 2560 and model_config.vocab_size == 151936
        and len(outputs.hidden_states) == 37 and primary.shape == (2560,) and secondary.shape == (2560,)
        and np.isfinite(primary).all() and np.isfinite(secondary).all()
    )
    result = {"status": "NEUTRAL_MODEL_PREFLIGHT_PASS" if valid else "RUNNER_PREFLIGHT_INVALID_ENVIRONMENT", "neutral_sentence_only": True, "model_class": model.__class__.__name__, "tokenizer_class": tokenizer.__class__.__name__, "hidden_state_count": len(outputs.hidden_states), "primary_shape": list(primary.shape), "secondary_shape": list(secondary.shape), "dtype": str(next(model.parameters()).dtype), "device": str(next(model.parameters()).device), "elapsed_seconds": round(time.perf_counter() - started, 4)}
    del primary, secondary, outputs, inputs, tokenized, model
    torch.cuda.empty_cache()
    if not valid:
        raise RuntimeError("RUNNER_PREFLIGHT_INVALID_ENVIRONMENT")
    report["neutral_model_preflight"] = result
    return report


def _fit_centroids(fit: dict[str, np.ndarray], groups: list[str]) -> dict[str, np.ndarray]:
    return {group: np.asarray(fit[group], dtype=float).mean(axis=0) for group in groups}


def _fit_probe(fit: dict[str, np.ndarray], probe_config: dict[str, Any]) -> tuple[StandardScaler, LogisticRegression, list[str]]:
    classes = list(probe_config["classifier"]["class_order"])
    features = np.concatenate([np.asarray(fit[group], dtype=float) for group in classes], axis=0)
    labels = np.concatenate([np.full(len(fit[group]), index, dtype=int) for index, group in enumerate(classes)])
    scaler = StandardScaler(**probe_config["preprocessing"])
    transformed = scaler.fit_transform(features)
    kwargs = {key: probe_config["classifier"][key] for key in ("solver", "penalty", "C", "max_iter", "class_weight", "random_state")}
    if "multi_class" in inspect.signature(LogisticRegression).parameters:
        kwargs["multi_class"] = probe_config["classifier"]["multi_class"]
    elif probe_config["classifier"]["multi_class"] != "multinomial":
        raise RuntimeError("Frozen multinomial probe is incompatible with this scikit-learn version.")
    classifier = LogisticRegression(**kwargs)
    classifier.fit(transformed, labels)
    return scaler, classifier, classes


def _target_probabilities(scaler: StandardScaler, classifier: LogisticRegression, semantic_order: list[str], representations: np.ndarray, target: str) -> np.ndarray:
    encoded = semantic_order.index(target)
    classes = list(classifier.classes_)
    if encoded not in classes:
        raise ValueError("Fitted classifier lacks a frozen semantic class.")
    return classifier.predict_proba(scaler.transform(np.asarray(representations, dtype=float)))[:, classes.index(encoded)]


def _route_items(prompts: list[dict[str, Any]], split: dict[str, Any], groups: list[str], representations: dict[str, np.ndarray]) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, list[str]]]:
    """Route frozen IDs into disjoint FIT/EVAL arrays without using outcomes."""
    by_id = {item["id"]: item for item in prompts}
    fit, evaluation, evaluation_ids = {}, {}, {}
    for group in groups:
        fit_ids, eval_ids = split["fit_ids"][group], split["evaluation_ids"][group]
        if set(fit_ids) & set(eval_ids) or any(by_id[item_id]["group"] != group for item_id in fit_ids + eval_ids):
            raise ValueError("Frozen FIT/EVAL ID routing is invalid.")
        fit[group] = np.stack([representations[item_id] for item_id in fit_ids]).astype(float)
        evaluation[group] = np.stack([representations[item_id] for item_id in eval_ids]).astype(float)
        evaluation_ids[group] = list(eval_ids)
    return fit, evaluation, evaluation_ids


def _summarize_effects(effect_rows: list[dict[str, Any]], config: dict[str, Any]) -> dict[str, Any]:
    """Apply the reviewed source-item cluster bootstrap and primary-only gate."""
    from experiments.exp020.validate_exp020_implementation_spec import bootstrap_cluster_statistics, descriptive_statistics, primary_gate

    bootstrap = _json(SPEC_PATH)["fixed_protocol"]["bootstrap"]
    clusters: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for row in effect_rows:
        clusters.setdefault(row["split_id"], {}).setdefault(row["held_out_source_item_id"], []).append(row)
    output = bootstrap_cluster_statistics(clusters, config["dataset"], seed=bootstrap["seed"], resamples=bootstrap["resamples"])
    observed = {outcome: descriptive_statistics([row[outcome] for row in effect_rows]) for outcome in ("task_effect", "D_random", "D_opposite")}
    return {"observed": observed, "bootstrap_ci": {key: values.tolist() for key, values in output["ci"].items()}, "gate": primary_gate(task_mean=observed["task_effect"]["mean"], task_ci_low=float(output["ci"]["task_effect"][0]), random_contrast_mean=observed["D_random"]["mean"], random_contrast_ci_low=float(output["ci"]["D_random"][0]), opposite_contrast_mean=observed["D_opposite"]["mean"])}


def _compute_layer_effects(prompts: list[dict[str, Any]], representations: dict[str, np.ndarray], config: dict[str, Any], *, block_index: int, hidden_state_index: int, beta: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compute one frozen block/beta path in memory; no raw representation persistence."""
    from experiments.exp020.validate_exp020_implementation_spec import matched_random_delta

    dataset, groups = config["dataset"], config["dataset"]["groups"]
    rows: list[dict[str, Any]] = []
    for split in sorted(dataset["splits"], key=lambda item: item["split_index"]):
        fit, evaluation, eval_ids = _route_items(prompts, split, groups, representations)
        centroids = _fit_centroids(fit, groups)
        scaler, classifier, class_order = _fit_probe(fit, config["probe"])
        for source_group, target_group in dataset["ordered_transitions"]:
            delta = centroids[target_group] - centroids[source_group]
            random_delta = matched_random_delta(delta, base_seed=config["direction_construction"]["random_control"]["base_seed"], model_index=config["direction_construction"]["random_control"]["model_index"], block_index=block_index, split_index=split["split_index"], source_group_index=groups.index(source_group), target_group_index=groups.index(target_group))
            baseline = evaluation[source_group]
            baseline_p = _target_probabilities(scaler, classifier, class_order, baseline, target_group)
            task_p = _target_probabilities(scaler, classifier, class_order, baseline + beta * delta, target_group)
            random_p = _target_probabilities(scaler, classifier, class_order, baseline + beta * random_delta, target_group)
            opposite_p = _target_probabilities(scaler, classifier, class_order, baseline - beta * delta, target_group)
            for item_id, base, task, random, opposite in zip(eval_ids[source_group], baseline_p, task_p, random_p, opposite_p):
                task_effect, random_effect, opposite_effect = float(task - base), float(random - base), float(opposite - base)
                rows.append({"block_index": block_index, "hidden_state_index": hidden_state_index, "beta": beta, "split_id": split["id"], "held_out_source_item_id": item_id, "source_group": source_group, "target_group": target_group, "task_effect": task_effect, "random_effect": random_effect, "opposite_effect": opposite_effect, "D_random": task_effect - random_effect, "D_opposite": task_effect - opposite_effect})
    return rows, _summarize_effects(rows, config)


def _require_finite(value: Any, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value):
        raise ValueError(f"Result field is missing or nonfinite: {field}")


def _validate_formal_result(result: dict[str, Any], config: dict[str, Any], authorization: dict[str, Any], runner_commit: str) -> None:
    """Reject incomplete, ambiguous, or technically invalid publication objects."""
    required = {
        "schema_version", "experiment", "run_id", "authorization", "frozen_authority_bindings",
        "model_runtime", "git_runner", "formal_inputs", "primary", "secondary_descriptive",
        "bootstrap", "technical_validity", "status",
    }
    if not isinstance(result, dict) or set(result) != required:
        raise ValueError("Formal result schema is incomplete or has unknown fields.")
    if result["schema_version"] != RESULT_SCHEMA_VERSION or result["experiment"] != "EXP-020A":
        raise ValueError("Formal result identity is invalid.")
    try:
        uuid.UUID(result["run_id"])
    except (TypeError, ValueError) as exc:
        raise ValueError("Formal result run identity is invalid.") from exc

    auth = result["authorization"]
    required_auth = {"authorization_id", "authorization_sha256", "authorized_runner_commit", "scope", "single_use"}
    if not isinstance(auth, dict) or set(auth) != required_auth:
        raise ValueError("Formal result authorization provenance is incomplete.")
    if auth["authorization_id"] != authorization["authorization_id"] or auth["authorization_sha256"] != authorization["authorization_sha256"]:
        raise ValueError("Formal result authorization provenance disagrees with authorization artifact.")
    if auth["authorized_runner_commit"] != authorization["runner_commit"] or auth["scope"] != FORMAL_AUTHORIZATION_SCOPE or auth["single_use"] is not True:
        raise ValueError("Formal result authorization provenance is invalid.")

    bindings = result["frozen_authority_bindings"]
    required_bindings = {
        "frozen_config_sha256", "preregistration_sha256", "prompt_file_sha256", "source_conditions_sha256",
        "split_transition_manifest_sha256", "model_revision", "model_config_sha256", "tokenizer_identity", "tokenizer_revision",
    }
    if not isinstance(bindings, dict) or set(bindings) != required_bindings:
        raise ValueError("Formal result frozen-authority provenance is incomplete.")
    expected, _, _ = _derive_frozen_bindings()
    if bindings != {key: expected[key] for key in required_bindings}:
        raise ValueError("Formal result frozen-authority provenance disagrees with current bindings.")

    runtime = result["model_runtime"]
    required_runtime = {"model_id", "model_revision", "model_config_sha256", "tokenizer_identity", "tokenizer_revision", "python", "numpy", "torch", "transformers", "scikit_learn", "device", "dtype"}
    if not isinstance(runtime, dict) or set(runtime) != required_runtime:
        raise ValueError("Formal result runtime provenance is incomplete.")
    for key in ("model_id", "model_revision", "model_config_sha256", "tokenizer_identity", "tokenizer_revision", "device", "dtype"):
        expected_value = expected[key] if key in expected else config["model"][key]
        if runtime[key] != expected_value:
            raise ValueError("Formal result runtime provenance disagrees with frozen bindings.")
    if not all(isinstance(runtime[key], str) and runtime[key] for key in ("python", "numpy", "torch", "transformers", "scikit_learn")):
        raise ValueError("Formal result runtime versions are incomplete.")

    git_runner = result["git_runner"]
    if not isinstance(git_runner, dict) or git_runner != {"authorized_runner_commit": authorization["runner_commit"], "actual_runner_commit": runner_commit}:
        raise ValueError("Formal result Git/runner provenance is invalid.")

    inputs = result["formal_inputs"]
    required_inputs = {"prompt_file", "prompt_file_sha256", "source_conditions_file", "source_conditions_sha256", "split_transition_manifest_sha256", "split_count", "groups", "ordered_transition_count", "evaluation_clusters", "paired_transition_rows"}
    if not isinstance(inputs, dict) or set(inputs) != required_inputs:
        raise ValueError("Formal result input provenance is incomplete.")
    if inputs["prompt_file"] != expected["prompt_file"] or inputs["prompt_file_sha256"] != expected["prompt_file_sha256"] or inputs["source_conditions_file"] != expected["source_conditions_file"] or inputs["source_conditions_sha256"] != expected["source_conditions_sha256"] or inputs["split_transition_manifest_sha256"] != expected["split_transition_manifest_sha256"]:
        raise ValueError("Formal result input provenance is invalid.")
    expected_counts = {"split_count": 2, "groups": config["dataset"]["groups"], "ordered_transition_count": 12, "evaluation_clusters": 24, "paired_transition_rows": config["dataset"]["aggregate_paired_evaluation_count"]}
    if {key: inputs[key] for key in expected_counts} != expected_counts:
        raise ValueError("Formal result input counts are incomplete.")

    for section_name, block_index, hidden_state_index, beta, gate_required in (
        ("primary", 18, 19, 0.75, True),
        ("secondary_descriptive", 26, 27, 0.5, False),
    ):
        section = result[section_name]
        required_section = {"block_index", "hidden_state_index", "beta", "comparisons", "summary", "gate_inputs", "gate_outcome"}
        if not isinstance(section, dict) or set(section) != required_section:
            raise ValueError(f"Formal result {section_name} section is incomplete.")
        if section["block_index"] != block_index or section["hidden_state_index"] != hidden_state_index or section["beta"] != beta:
            raise ValueError(f"Formal result {section_name} layer or beta differs from the frozen protocol.")
        comparisons = section["comparisons"]
        if not isinstance(comparisons, list) or len(comparisons) != 72:
            raise ValueError(f"Formal result {section_name} comparisons are empty or incomplete.")
        required_row = {"block_index", "hidden_state_index", "beta", "split_id", "held_out_source_item_id", "source_group", "target_group", "task_effect", "random_effect", "opposite_effect", "D_random", "D_opposite"}
        for row in comparisons:
            if not isinstance(row, dict) or set(row) != required_row:
                raise ValueError(f"Formal result {section_name} comparison schema is invalid.")
            if row["block_index"] != block_index or row["hidden_state_index"] != hidden_state_index or row["beta"] != beta:
                raise ValueError(f"Formal result {section_name} comparison layer coverage is invalid.")
            for field in ("task_effect", "random_effect", "opposite_effect", "D_random", "D_opposite"):
                _require_finite(row[field], f"{section_name}.{field}")
        expected_coverage = {
            (split["id"], item_id, source_group, target_group)
            for split in config["dataset"]["splits"]
            for source_group, target_group in config["dataset"]["ordered_transitions"]
            for item_id in split["evaluation_ids"][source_group]
        }
        observed_coverage = {
            (row["split_id"], row["held_out_source_item_id"], row["source_group"], row["target_group"])
            for row in comparisons
        }
        if observed_coverage != expected_coverage or len(observed_coverage) != len(comparisons):
            raise ValueError(f"Formal result {section_name} split or transition coverage is incomplete.")
        summary = section["summary"]
        if not isinstance(summary, dict) or set(summary) != {"observed", "bootstrap_ci"}:
            raise ValueError(f"Formal result {section_name} summary is incomplete.")
        for outcome in ("task_effect", "D_random", "D_opposite"):
            stats = summary["observed"].get(outcome)
            ci = summary["bootstrap_ci"].get(outcome)
            if not isinstance(stats, dict) or set(stats) != {"mean", "median", "standard_deviation", "proportion_positive"}:
                raise ValueError(f"Formal result {section_name} observed statistics are incomplete.")
            if not isinstance(ci, list) or len(ci) != 2:
                raise ValueError(f"Formal result {section_name} bootstrap interval is incomplete.")
            for name, value in {**stats, "ci_low": ci[0], "ci_high": ci[1]}.items():
                _require_finite(value, f"{section_name}.{outcome}.{name}")
        if gate_required:
            required_gate_inputs = {"task_mean", "task_ci_low", "random_contrast_mean", "random_contrast_ci_low", "opposite_contrast_mean"}
            if not isinstance(section["gate_inputs"], dict) or set(section["gate_inputs"]) != required_gate_inputs:
                raise ValueError("Formal result primary gate inputs are absent.")
            for key, value in section["gate_inputs"].items():
                _require_finite(value, f"primary.gate_inputs.{key}")
            if section["gate_outcome"] not in {"REPRESENTATION_REPLICATION_SUPPORTED", "REPRESENTATION_REPLICATION_NOT_SUPPORTED"}:
                raise ValueError("Technical invalidity must not serialize as a scientific primary gate result.")
        elif section["gate_inputs"] is not None or section["gate_outcome"] != "DESCRIPTIVE_ONLY":
            raise ValueError("Secondary result must remain descriptive only.")

    bootstrap = result["bootstrap"]
    required_bootstrap = {"seed", "resamples", "bit_generator", "cluster_strata", "clusters_per_split", "transition_rows_per_cluster", "transition_rows_per_replicate"}
    if not isinstance(bootstrap, dict) or set(bootstrap) != required_bootstrap:
        raise ValueError("Formal result bootstrap metadata is incomplete.")
    if bootstrap != {"seed": 20260812, "resamples": 10000, "bit_generator": "PCG64", "cluster_strata": 2, "clusters_per_split": 12, "transition_rows_per_cluster": 3, "transition_rows_per_replicate": 72}:
        raise ValueError("Formal result bootstrap metadata differs from the frozen protocol.")
    if result["technical_validity"] != {"status": "VALID", "reason": None}:
        raise ValueError("Formal result technical validity status is invalid or ambiguous.")
    if result["status"] != {"exp020_scientific_status": "COMPLETED", "representation_gate": result["primary"]["gate_outcome"]}:
        raise ValueError("Formal result status is invalid.")


def _atomic_publish(result: dict[str, Any], config: dict[str, Any], authorization: dict[str, Any], runner_commit: str, root: Path = ROOT) -> None:
    """Validate one complete result and atomically publish it to the canonical path."""
    output_path = _canonical_result_path(root)
    _require_no_formal_results(root)
    _validate_formal_result(result, config, authorization, runner_commit)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError("Canonical formal result already exists.")
    staging = output_path.with_name(f"{output_path.name}.tmp-{uuid.uuid4().hex}")
    try:
        with staging.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(result, handle, ensure_ascii=False, allow_nan=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        if output_path.exists():
            raise FileExistsError("Canonical formal result already exists.")
        os.replace(staging, output_path)
    except Exception:
        if staging.exists():
            staging.unlink()
        raise


def _result_section(rows: list[dict[str, Any]], summary: dict[str, Any], *, block_index: int, hidden_state_index: int, beta: float, primary: bool) -> dict[str, Any]:
    """Package already-computed summaries without changing their scientific values."""
    observed, bootstrap_ci = summary["observed"], summary["bootstrap_ci"]
    if primary:
        gate_inputs = {
            "task_mean": observed["task_effect"]["mean"],
            "task_ci_low": bootstrap_ci["task_effect"][0],
            "random_contrast_mean": observed["D_random"]["mean"],
            "random_contrast_ci_low": bootstrap_ci["D_random"][0],
            "opposite_contrast_mean": observed["D_opposite"]["mean"],
        }
        gate_outcome = summary["gate"]
    else:
        gate_inputs, gate_outcome = None, "DESCRIPTIVE_ONLY"
    return {
        "block_index": block_index,
        "hidden_state_index": hidden_state_index,
        "beta": beta,
        "comparisons": rows,
        "summary": {"observed": observed, "bootstrap_ci": bootstrap_ci},
        "gate_inputs": gate_inputs,
        "gate_outcome": gate_outcome,
    }


def _build_formal_result(primary_rows: list[dict[str, Any]], primary_summary: dict[str, Any], secondary_rows: list[dict[str, Any]], secondary_summary: dict[str, Any], *, authorization_context: dict[str, Any], model: Any, tokenizer: Any) -> dict[str, Any]:
    """Create one complete provenance-bound result object after valid computation."""
    import sklearn
    import torch
    import transformers

    authorization = authorization_context["authorization"]
    bindings = authorization_context["bindings"]
    config = authorization_context["config"]
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "experiment": "EXP-020A",
        "run_id": str(uuid.uuid4()),
        "authorization": {
            "authorization_id": authorization["authorization_id"],
            "authorization_sha256": authorization_context["authorization_sha256"],
            "authorized_runner_commit": authorization["runner_commit"],
            "scope": FORMAL_AUTHORIZATION_SCOPE,
            "single_use": True,
        },
        "frozen_authority_bindings": {key: bindings[key] for key in ("frozen_config_sha256", "preregistration_sha256", "prompt_file_sha256", "source_conditions_sha256", "split_transition_manifest_sha256", "model_revision", "model_config_sha256", "tokenizer_identity", "tokenizer_revision")},
        "model_runtime": {
            "model_id": config["model"]["model_id"],
            "model_revision": config["model"]["revision"],
            "model_config_sha256": config["model"]["config_sha256"],
            "tokenizer_identity": tokenizer.__class__.__name__,
            "tokenizer_revision": bindings["tokenizer_revision"],
            "python": platform.python_version(),
            "numpy": np.__version__,
            "torch": torch.__version__,
            "transformers": transformers.__version__,
            "scikit_learn": sklearn.__version__,
            "device": str(next(model.parameters()).device),
            "dtype": str(next(model.parameters()).dtype).replace("torch.", ""),
        },
        "git_runner": {"authorized_runner_commit": authorization["runner_commit"], "actual_runner_commit": authorization_context["runner_commit"]},
        "formal_inputs": {
            "prompt_file": bindings["prompt_file"],
            "prompt_file_sha256": bindings["prompt_file_sha256"],
            "source_conditions_file": bindings["source_conditions_file"],
            "source_conditions_sha256": bindings["source_conditions_sha256"],
            "split_transition_manifest_sha256": bindings["split_transition_manifest_sha256"],
            "split_count": 2,
            "groups": config["dataset"]["groups"],
            "ordered_transition_count": 12,
            "evaluation_clusters": 24,
            "paired_transition_rows": config["dataset"]["aggregate_paired_evaluation_count"],
        },
        "primary": _result_section(primary_rows, primary_summary, block_index=18, hidden_state_index=19, beta=0.75, primary=True),
        "secondary_descriptive": _result_section(secondary_rows, secondary_summary, block_index=26, hidden_state_index=27, beta=0.5, primary=False),
        "bootstrap": {"seed": 20260812, "resamples": 10000, "bit_generator": "PCG64", "cluster_strata": 2, "clusters_per_split": 12, "transition_rows_per_cluster": 3, "transition_rows_per_replicate": 72},
        "technical_validity": {"status": "VALID", "reason": None},
        "status": {"exp020_scientific_status": "COMPLETED", "representation_gate": primary_summary["gate"]},
    }


def formal_run() -> None:
    """Future authorized computation path; prohibited during Task 082C."""
    authorization_context = validate_formal_authorization()  # Must remain first: no formal data/model/output access before this line.
    _run_validator(EXP_DIR / "validate_exp020_preregistration.py")
    _run_validator(EXP_DIR / "validate_exp020_implementation_spec.py")
    _require_no_formal_results()
    config, spec = authorization_context["config"], authorization_context["spec"]
    validate_static_environment(config, spec)
    prompts = _json(PROMPT_PATH)  # Formal source access begins only after authorization.
    from src.extraction import extract_last_token_hidden_state, move_tokenized_inputs_to_device, tensor_to_numpy_float32
    from src.model_loader import load_causal_lm, load_tokenizer
    import torch

    layers = [19, 27]
    tokenizer = load_tokenizer(config["model"]["canonical_path"], local_files_only=True)
    model = load_causal_lm(config["model"]["canonical_path"], dtype="bfloat16", device_map={"": 0}, local_files_only=True)
    model.eval()
    representations = {layer: {} for layer in layers}
    for prompt in prompts:
        tokenized = tokenizer(prompt["text"], return_tensors="pt")
        with torch.no_grad():
            output = model(**move_tokenized_inputs_to_device(tokenized, torch.device("cuda:0")), output_hidden_states=True, return_dict=True)
        for layer in layers:
            representations[layer][prompt["id"]] = tensor_to_numpy_float32(extract_last_token_hidden_state(output.hidden_states, layer))
    primary_rows, primary_summary = _compute_layer_effects(prompts, representations[19], config, block_index=18, hidden_state_index=19, beta=0.75)
    secondary_rows, secondary_summary = _compute_layer_effects(prompts, representations[27], config, block_index=26, hidden_state_index=27, beta=0.5)
    if len(primary_rows) != config["dataset"]["aggregate_paired_evaluation_count"]:
        raise RuntimeError("REPRESENTATION_REPLICATION_INVALID")
    result = _build_formal_result(primary_rows, primary_summary, secondary_rows, secondary_summary, authorization_context=authorization_context, model=model, tokenizer=tokenizer)
    _atomic_publish(result, config, {**authorization_context["authorization"], "authorization_sha256": authorization_context["authorization_sha256"]}, authorization_context["runner_commit"])
    del model
    torch.cuda.empty_cache()


def _write_preflight(report: dict[str, Any]) -> None:
    PREFLIGHT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.update({"EXP020_FORMAL_RUN_AUTHORIZED": False, "EXP020_SCIENTIFIC_STATUS": "NOT_STARTED", "FORMAL_FIT_EVAL_INFERENCE_PERFORMED": False, "FORMAL_SCIENTIFIC_RESULTS_CREATED": False})
    PREFLIGHT_OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--static-preflight", action="store_true")
    mode.add_argument("--neutral-model-preflight", action="store_true")
    mode.add_argument("--formal-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.static_preflight:
            _write_preflight(static_preflight())
            print("STATIC_PREFLIGHT_PASS")
            return 0
        if args.neutral_model_preflight:
            _write_preflight(neutral_model_preflight())
            print("NEUTRAL_MODEL_PREFLIGHT_PASS")
            return 0
        formal_run()
    except PermissionError as exc:
        print(str(exc))
        return 2
    except RuntimeError as exc:
        print(str(exc))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
