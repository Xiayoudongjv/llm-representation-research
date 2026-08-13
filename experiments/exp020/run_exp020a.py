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
import subprocess
import sys
import time
import uuid
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
AUTHORIZATION_PATH = EXP_DIR / "exp020_formal_run_authorization.json"
FORMAL_OUTPUT_DIR = ROOT / "results" / "exp020"
PREFLIGHT_OUTPUT_PATH = EXP_DIR / "results" / "runner_preflight.json"
PROMPT_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
NEUTRAL_TEXT = "This is a neutral hardware diagnostic."
FORMAL_RESULT_FILENAMES = (
    "transition_metrics.csv", "probe_metrics.csv", "invariant_metrics.csv", "pair_summary.csv",
    "representation_summary.json", "validation_summary.json", "behavioral_outputs.csv",
)
EXPECTED_AUTHORIZATION = {
    "experiment": "EXP-020A",
    "formal_run_authorized": True,
    "protocol_commit": "ea85fa5bfb17d8c684da619fe6cd74418c2312be",
    "implementation_spec_commit": "18579a1074d2c5f7a3873f2890f223b3653a94e9",
}


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _formal_result_paths(root: Path = ROOT) -> list[Path]:
    roots = (root / "results" / "exp020", root / "experiments" / "exp020" / "results")
    return [directory / name for directory in roots for name in FORMAL_RESULT_FILENAMES if (directory / name).exists()]


def _require_no_formal_results(root: Path = ROOT) -> None:
    if paths := _formal_result_paths(root):
        raise RuntimeError(f"Formal output already exists: {paths[0]}")


def _current_commit(root: Path = ROOT) -> str:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def validate_formal_authorization(root: Path = ROOT) -> dict[str, Any]:
    """Validate authorization before formal prompt/source, model, or output access."""
    path = AUTHORIZATION_PATH if AUTHORIZATION_PATH.is_absolute() else root / AUTHORIZATION_PATH
    if not path.is_file():
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    authorization = _json(path)
    for key, expected in EXPECTED_AUTHORIZATION.items():
        if authorization.get(key) != expected:
            raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    if authorization.get("runner_commit") != _current_commit(root):
        raise PermissionError("FORMAL_RUN_BLOCKED_NOT_AUTHORIZED")
    return authorization


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


def _atomic_publish(rows: dict[str, list[dict[str, Any]]], summary: dict[str, Any], output_dir: Path = FORMAL_OUTPUT_DIR) -> None:
    """Future formal output publication: validate in memory then atomically rename one complete set."""
    if output_dir.exists() or _formal_result_paths():
        raise FileExistsError("Formal output path already exists.")
    staging = output_dir.with_name(f"{output_dir.name}_tmp_{uuid.uuid4().hex}")
    try:
        staging.mkdir(parents=True)
        required = {"effect_rows", "probe_rows", "transition_rows", "pair_rows"}
        if set(rows) != required or any(not isinstance(value, list) for value in rows.values()):
            raise ValueError("Formal output schema is incomplete.")
        for name, value in rows.items():
            (staging / f"{name}.json").write_text(json.dumps(value, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        (staging / "representation_summary.json").write_text(json.dumps(summary, ensure_ascii=False, allow_nan=False), encoding="utf-8")
        staging.replace(output_dir)
    except Exception:
        # A future execution may leave a staging directory for forensic inspection; it is never published.
        raise


def formal_run() -> None:
    """Future authorized computation path; never called by Task 082A."""
    validate_formal_authorization()  # Must remain first: no formal data/model/output access before this line.
    _require_no_formal_results()
    config, spec = _json(FROZEN_CONFIG_PATH), _json(SPEC_PATH)
    validate_static_environment(config, spec)
    prompts = _json(PROMPT_PATH)  # Formal source access begins only after authorization.
    from src.extraction import extract_last_token_hidden_state, move_tokenized_inputs_to_device, tensor_to_numpy_float32
    from src.model_loader import load_causal_lm, load_tokenizer
    from experiments.exp020.validate_exp020_implementation_spec import bootstrap_cluster_statistics, canonical_manifest
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
    _atomic_publish(
        {"effect_rows": primary_rows + secondary_rows, "probe_rows": [], "transition_rows": [], "pair_rows": []},
        {"primary": primary_summary, "secondary_descriptive": secondary_summary, "primary_gate_controls_status": "secondary_cannot_rescue_primary"},
    )
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
