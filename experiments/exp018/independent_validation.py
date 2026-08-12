"""EXP-018 held-out centroid-steering validation runner.

The frozen design is read only from ``validation_conditions.json``. Running
with ``--dry-run`` validates the plan without importing or loading model code.
``--run`` is intentionally explicit because it performs the official model
forwards and writes the preregistered result schemas.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment_io import load_json, save_json, write_csv
from src.invariants import summarize_invariant_metrics


CONFIG_PATH = Path(__file__).with_name("validation_conditions.json")
PROMPTS_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
OUTPUT_DIR = ROOT / "results" / "exp018"

TRANSITION_FIELDS = [
    "model", "layer", "split", "source_group", "target_group", "beta",
    "intervention_type", "eval_item_id", "target_assignment_rate", "source_assignment_rate",
    "target_minus_source_similarity",
]
PROBE_FIELDS = [
    "model", "layer", "split", "source_group", "target_group", "beta",
    "intervention_type", "eval_item_id", "target_probability", "source_probability",
    "target_minus_source_probability", "target_prediction_rate",
    "source_prediction_rate",
]
INVARIANT_FIELDS = [
    "model", "layer", "split", "source_group", "target_group", "beta",
    "intervention_type", "rsm_pearson", "invariant_violation_score",
    "rsm_frobenius_distance", "ivs_advantage_vs_random",
]
PAIR_SUMMARY_FIELDS = [
    "model", "layer", "split", "source_group", "target_group",
    "fit_item_count", "eval_item_count", "probe_training_sample_count",
    "probe_training_accuracy", "probe_class_counts",
    "baseline_target_assignment_rate", "baseline_source_assignment_rate",
    "baseline_target_minus_source_similarity", "baseline_target_probability",
    "baseline_source_probability", "baseline_target_minus_source_probability",
    "baseline_target_prediction_rate", "baseline_source_prediction_rate",
]


@dataclass
class ProbeBundle:
    """Fit-only preprocessing, classifier, and training diagnostics."""

    scaler: StandardScaler
    classifier: LogisticRegression
    class_order: list[str]
    training_sample_count: int
    class_counts: dict[str, int]
    training_accuracy: float


def parse_args() -> argparse.Namespace:
    """Parse explicit dry-run versus official-execution mode."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Validate configuration only; do not load a model.")
    mode.add_argument("--run", action="store_true", help="Run the official model-forward validation.")
    parser.add_argument("--dtype", default="float16", help="Runtime model dtype for --run only.")
    return parser.parse_args()


def load_frozen_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the single frozen EXP-018 configuration source."""
    return load_json(path)


def _flatten_ids(ids_by_group: dict[str, list[str]]) -> list[str]:
    return [item_id for group_ids in ids_by_group.values() for item_id in group_ids]


def validate_split_disjointness(split: dict[str, Any], groups: list[str]) -> None:
    """Reject duplicate, missing, or overlapping fit/evaluation IDs per group."""
    if set(split["fit_ids"]) != set(groups) or set(split["evaluation_ids"]) != set(groups):
        raise ValueError(f"Split {split.get('id', '<unknown>')} must provide fit and evaluation IDs for every group.")
    for group in groups:
        fit_ids = list(split["fit_ids"][group])
        eval_ids = list(split["evaluation_ids"][group])
        if len(fit_ids) != len(set(fit_ids)) or len(eval_ids) != len(set(eval_ids)):
            raise ValueError(f"Split {split['id']} has duplicate IDs in group {group!r}.")
        overlap = sorted(set(fit_ids) & set(eval_ids))
        if overlap:
            raise ValueError(f"Split {split['id']} leaks group {group!r} IDs between fit and evaluation: {overlap}")


def validate_config(config: dict[str, Any], prompts: list[dict[str, Any]]) -> None:
    """Validate frozen structure and prompt provenance without loading models."""
    groups = list(config["groups"])
    if len(groups) != len(set(groups)) or not groups:
        raise ValueError("Configuration groups must be non-empty and unique.")
    prompt_ids = [item["id"] for item in prompts]
    if len(prompt_ids) != len(set(prompt_ids)):
        raise ValueError("Prompt IDs must be unique.")
    prompt_group_by_id = {item["id"]: item["group"] for item in prompts}
    if set(prompt_group_by_id.values()) != set(groups):
        raise ValueError("Prompt groups do not match the frozen configuration groups.")
    for split in config["splits"]:
        validate_split_disjointness(split, groups)
        all_ids = _flatten_ids(split["fit_ids"]) + _flatten_ids(split["evaluation_ids"])
        unknown = sorted(set(all_ids) - set(prompt_ids))
        if unknown:
            raise ValueError(f"Split {split['id']} references unknown prompt IDs: {unknown}")
        if len(all_ids) != len(set(all_ids)):
            raise ValueError(f"Split {split['id']} has cross-group duplicate IDs.")
        for group in groups:
            for item_id in split["fit_ids"][group] + split["evaluation_ids"][group]:
                if prompt_group_by_id[item_id] != group:
                    raise ValueError(f"Prompt {item_id!r} is assigned to {group!r}, but belongs to {prompt_group_by_id[item_id]!r}.")
    if not config["betas"] or any(not isinstance(beta, (int, float)) for beta in config["betas"]):
        raise ValueError("Frozen beta grid must contain numeric values.")
    for model in config["models"]:
        if not model["name"] or any(not isinstance(layer, int) or layer < 0 for layer in model["primary_layers"] + model["secondary_layers"]):
            raise ValueError(f"Invalid frozen model/layer configuration: {model}")
    if len(config["ordered_transitions"]) != len(groups) * (len(groups) - 1):
        raise ValueError("Ordered transitions must cover every non-self group pair.")


def route_split_items(prompts: list[dict[str, Any]], split: dict[str, Any], groups: list[str]) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    """Route prompt records into disjoint group-keyed fit and evaluation sets."""
    validate_split_disjointness(split, groups)
    by_id = {item["id"]: item for item in prompts}
    fit = {group: [by_id[item_id] for item_id in split["fit_ids"][group]] for group in groups}
    evaluation = {group: [by_id[item_id] for item_id in split["evaluation_ids"][group]] for group in groups}
    return fit, evaluation


def fit_group_centroids(fit_representations: dict[str, np.ndarray], groups: list[str]) -> dict[str, np.ndarray]:
    """Fit one centroid per group using fit arrays only."""
    if set(fit_representations) != set(groups):
        raise ValueError("Centroid fitting requires exactly one fit-only array per configured group.")
    centroids: dict[str, np.ndarray] = {}
    for group in groups:
        matrix = np.asarray(fit_representations[group], dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] == 0:
            raise ValueError(f"Fit representations for {group!r} must have shape [n, d] with n > 0.")
        centroids[group] = matrix.mean(axis=0)
    return centroids


def construct_task_delta(fit_centroids: dict[str, np.ndarray], source_group: str, target_group: str) -> np.ndarray:
    """Construct the raw target-minus-source delta from fit-only centroids."""
    if source_group not in fit_centroids or target_group not in fit_centroids:
        raise ValueError("Both source and target centroids must be fit centroids.")
    return np.asarray(fit_centroids[target_group], dtype=float) - np.asarray(fit_centroids[source_group], dtype=float)


def matched_random_delta(task_delta: np.ndarray, config: dict[str, Any], model_index: int, layer: int, split_index: int, source_group: str, target_group: str) -> np.ndarray:
    """Return a deterministic, matched-norm random vector for one transition key."""
    task = np.asarray(task_delta, dtype=float)
    norm = float(np.linalg.norm(task))
    if norm < 1e-12:
        raise ValueError("Cannot construct a matched random vector for a near-zero task delta.")
    group_index = config["group_index"]
    seed = np.random.SeedSequence([
        config["random_control"]["base_seed"], model_index, layer, split_index,
        group_index[source_group], group_index[target_group],
    ])
    random = np.random.default_rng(seed).standard_normal(task.shape)
    random_norm = float(np.linalg.norm(random))
    if random_norm < 1e-12:
        raise RuntimeError("Random-direction generation produced a near-zero vector.")
    return random * (norm / random_norm)


def opposite_delta(task_delta: np.ndarray) -> np.ndarray:
    """Return the exact opposite of a previously fit task delta."""
    return -np.asarray(task_delta, dtype=float)


def apply_steering(held_out_representations: np.ndarray, delta: np.ndarray, beta: float) -> np.ndarray:
    """Return a new steered held-out array without mutating the input."""
    representations = np.asarray(held_out_representations, dtype=float)
    return representations.copy() + float(beta) * np.asarray(delta, dtype=float)


def _cosine_matrix(representations: np.ndarray, centroids: dict[str, np.ndarray], groups: list[str]) -> np.ndarray:
    matrix = np.asarray(representations, dtype=float)
    normalized_reps = matrix / np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-12)
    normalized_centroids = np.stack([np.asarray(centroids[group], dtype=float) for group in groups])
    normalized_centroids /= np.maximum(np.linalg.norm(normalized_centroids, axis=1, keepdims=True), 1e-12)
    return normalized_reps @ normalized_centroids.T


def evaluate_held_out_centroids(held_out_representations: np.ndarray, fit_centroids: dict[str, np.ndarray], groups: list[str], source_group: str, target_group: str) -> dict[str, float]:
    """Evaluate held-out arrays against fit-only centroids by cosine similarity."""
    item_metrics = evaluate_held_out_centroid_items(held_out_representations, fit_centroids, groups, source_group, target_group)
    return aggregate_mean_metrics(item_metrics)


def evaluate_held_out_centroid_items(held_out_representations: np.ndarray, fit_centroids: dict[str, np.ndarray], groups: list[str], source_group: str, target_group: str) -> list[dict[str, float]]:
    """Return one held-out cosine-centroid record per representation.

    Assignment-rate fields are 0.0/1.0 per item; their mean is the group rate.
    """
    if source_group not in groups or target_group not in groups:
        raise ValueError("Source and target must be configured groups.")
    similarities = _cosine_matrix(held_out_representations, fit_centroids, groups)
    predicted_indices = np.argmax(similarities, axis=1)
    source_index, target_index = groups.index(source_group), groups.index(target_group)
    return [
        {
            "target_assignment_rate": float(predicted == target_index),
            "source_assignment_rate": float(predicted == source_index),
            "target_minus_source_similarity": float(similarity[target_index] - similarity[source_index]),
        }
        for predicted, similarity in zip(predicted_indices, similarities)
    ]


def fit_linear_probe(fit_representations: dict[str, np.ndarray], config: dict[str, Any]) -> ProbeBundle:
    """Fit the frozen scaler and multinomial probe using fit arrays only."""
    class_order = list(config["linear_probe"]["classifier"]["class_order"])
    if set(fit_representations) != set(class_order):
        raise ValueError("Probe fitting requires fit-only arrays for exactly the configured classes.")
    matrices = [np.asarray(fit_representations[group], dtype=float) for group in class_order]
    if any(matrix.ndim != 2 or matrix.shape[0] == 0 for matrix in matrices):
        raise ValueError("Each probe fit array must be a non-empty [n, d] matrix.")
    features = np.concatenate(matrices, axis=0)
    labels = np.concatenate([np.full(matrix.shape[0], index, dtype=int) for index, matrix in enumerate(matrices)])
    preprocessing = config["linear_probe"]["preprocessing"]
    classifier_config = config["linear_probe"]["classifier"]
    scaler = StandardScaler(with_mean=preprocessing["with_mean"], with_std=preprocessing["with_std"])
    transformed = scaler.fit_transform(features)
    classifier_kwargs = {
        "solver": classifier_config["solver"], "penalty": classifier_config["penalty"], "C": classifier_config["C"],
        "max_iter": classifier_config["max_iter"], "class_weight": classifier_config["class_weight"],
        "random_state": classifier_config["random_state"],
    }
    if "multi_class" in inspect.signature(LogisticRegression).parameters:
        classifier_kwargs["multi_class"] = classifier_config["multi_class"]
    elif classifier_config["multi_class"] != "multinomial":
        raise RuntimeError("Installed scikit-learn removed multi_class; frozen configuration must require multinomial behavior.")
    classifier = LogisticRegression(**classifier_kwargs)
    classifier.fit(transformed, labels)
    predictions = classifier.predict(transformed)
    counts = Counter(labels.tolist())
    return ProbeBundle(
        scaler=scaler,
        classifier=classifier,
        class_order=class_order,
        training_sample_count=int(features.shape[0]),
        class_counts={group: int(counts[index]) for index, group in enumerate(class_order)},
        training_accuracy=float(np.mean(predictions == labels)),
    )


def evaluate_probe(probe: ProbeBundle, held_out_representations: np.ndarray, source_group: str, target_group: str) -> dict[str, float]:
    """Evaluate held-out representations with an already fit frozen probe."""
    return aggregate_mean_metrics(evaluate_probe_items(probe, held_out_representations, source_group, target_group))


def evaluate_probe_items(probe: ProbeBundle, held_out_representations: np.ndarray, source_group: str, target_group: str) -> list[dict[str, float]]:
    """Return one held-out frozen-probe record per representation."""
    if source_group not in probe.class_order or target_group not in probe.class_order:
        raise ValueError("Source and target must be probe classes.")
    transformed = probe.scaler.transform(np.asarray(held_out_representations, dtype=float))
    probabilities = probe.classifier.predict_proba(transformed)
    predictions = probe.classifier.predict(transformed)
    source_index, target_index = probe.class_order.index(source_group), probe.class_order.index(target_group)
    return [
        {
            "target_probability": float(probability[target_index]),
            "source_probability": float(probability[source_index]),
            "target_minus_source_probability": float(probability[target_index] - probability[source_index]),
            "target_prediction_rate": float(prediction == target_index),
            "source_prediction_rate": float(prediction == source_index),
        }
        for probability, prediction in zip(probabilities, predictions)
    ]


def compare_rsm_conditions(baseline: np.ndarray, task: np.ndarray, random: np.ndarray, opposite: np.ndarray) -> dict[str, float]:
    """Compare held-out RSM/IVS values using the existing invariant implementation."""
    task_metrics = summarize_invariant_metrics(baseline, task)
    random_metrics = summarize_invariant_metrics(baseline, random)
    opposite_metrics = summarize_invariant_metrics(baseline, opposite)
    return {
        "rsm_pearson_task": task_metrics["rsm_pearson"],
        "rsm_pearson_random": random_metrics["rsm_pearson"],
        "rsm_pearson_opposite": opposite_metrics["rsm_pearson"],
        "ivs_task": task_metrics["invariant_violation_score"],
        "ivs_random": random_metrics["invariant_violation_score"],
        "ivs_opposite": opposite_metrics["invariant_violation_score"],
        "ivs_advantage_vs_random": random_metrics["invariant_violation_score"] - task_metrics["invariant_violation_score"],
        "rsm_frobenius_task": task_metrics["rsm_frobenius_distance"],
        "rsm_frobenius_random": random_metrics["rsm_frobenius_distance"],
        "rsm_frobenius_opposite": opposite_metrics["rsm_frobenius_distance"],
    }


def expected_condition_counts(config: dict[str, Any]) -> dict[str, int]:
    """Derive all dry-run counts from the frozen configuration."""
    model_layers = sum(len(model["primary_layers"]) + len(model["secondary_layers"]) for model in config["models"])
    splits = len(config["splits"])
    transitions = len(config["ordered_transitions"])
    betas = len(config["betas"])
    interventions = len(config["conditions"])
    eval_per_source = len(next(iter(config["splits"][0]["evaluation_ids"].values())))
    condition_evaluations = model_layers * splits * transitions * betas * interventions
    return {
        "model_layer_configurations": model_layers,
        "splits": splits,
        "ordered_transitions": transitions,
        "betas": betas,
        "intervention_types": interventions,
        "held_out_source_items_per_transition": eval_per_source,
        "condition_evaluations": condition_evaluations,
        "per_item_transition_rows": condition_evaluations * eval_per_source,
        "per_item_probe_rows": condition_evaluations * eval_per_source,
        "invariant_rows": condition_evaluations,
        "pair_summary_rows": model_layers * splits * transitions,
    }


def aggregate_result_rows(fieldnames: list[str], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate the stable output schema before any future CSV write."""
    expected = set(fieldnames)
    for index, row in enumerate(rows):
        if set(row) != expected:
            raise ValueError(f"Result row {index} does not match the frozen schema.")
    return rows


def aggregate_mean_metrics(records: list[dict[str, float]]) -> dict[str, float]:
    """Aggregate identically keyed numerical held-out records without refitting."""
    if not records:
        raise ValueError("Cannot aggregate an empty record sequence.")
    fields = set(records[0])
    if any(set(record) != fields for record in records):
        raise ValueError("All metric records must have the same schema before aggregation.")
    return {field: float(np.mean([record[field] for record in records])) for field in fields}


def _collect_model_representations(model_name: str, layers: list[int], prompts: list[dict[str, Any]], dtype: str) -> dict[int, dict[str, np.ndarray]]:
    """Load a model only during explicit --run and collect no persisted raw states."""
    import torch

    from src.extraction import extract_last_token_hidden_state, get_model_input_device, move_tokenized_inputs_to_device, tensor_to_numpy_float32
    from src.model_loader import check_cuda_or_raise, load_causal_lm, load_tokenizer

    check_cuda_or_raise()
    tokenizer = load_tokenizer(model_name)
    model = load_causal_lm(model_name, dtype=dtype)
    device = get_model_input_device(model)
    collected = {layer: {} for layer in layers}
    model.eval()
    for prompt in prompts:
        tokenized = tokenizer(prompt["text"], return_tensors="pt")
        inputs = move_tokenized_inputs_to_device(tokenized, device)
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
        for layer in layers:
            collected[layer][prompt["id"]] = tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, layer))
    del model
    torch.cuda.empty_cache()
    return collected


def _stack(items: list[dict[str, Any]], representations: dict[str, np.ndarray]) -> np.ndarray:
    return np.stack([representations[item["id"]] for item in items]).astype(float)


def run_validation(config: dict[str, Any], prompts: list[dict[str, Any]], dtype: str) -> None:
    """Run the official frozen validation and write only aggregate result files."""
    validate_config(config, prompts)
    transition_rows: list[dict[str, Any]] = []
    probe_rows: list[dict[str, Any]] = []
    invariant_rows: list[dict[str, Any]] = []
    pair_rows: list[dict[str, Any]] = []
    groups = list(config["groups"])
    for model_spec in config["models"]:
        layers = model_spec["primary_layers"] + model_spec["secondary_layers"]
        representations_by_layer = _collect_model_representations(model_spec["name"], layers, prompts, dtype)
        for layer in layers:
            representations = representations_by_layer[layer]
            for split in config["splits"]:
                fit_items, evaluation_items = route_split_items(prompts, split, groups)
                fit_reps = {group: _stack(fit_items[group], representations) for group in groups}
                eval_reps = {group: _stack(evaluation_items[group], representations) for group in groups}
                centroids = fit_group_centroids(fit_reps, groups)
                probe = fit_linear_probe(fit_reps, config)
                for source_group, target_group in config["ordered_transitions"]:
                    task_delta = construct_task_delta(centroids, source_group, target_group)
                    random_delta = matched_random_delta(task_delta, config, model_spec["model_index"], layer, split["split_index"], source_group, target_group)
                    deltas = {"task": task_delta, "matched_random": random_delta, "opposite": opposite_delta(task_delta)}
                    baseline = eval_reps[source_group]
                    baseline_centroid = evaluate_held_out_centroids(baseline, centroids, groups, source_group, target_group)
                    baseline_probe = evaluate_probe(probe, baseline, source_group, target_group)
                    pair_rows.append({
                        "model": model_spec["name"], "layer": layer, "split": split["id"], "source_group": source_group, "target_group": target_group,
                        "fit_item_count": int(sum(matrix.shape[0] for matrix in fit_reps.values()) / len(groups)), "eval_item_count": int(baseline.shape[0]),
                        "probe_training_sample_count": probe.training_sample_count, "probe_training_accuracy": probe.training_accuracy,
                        "probe_class_counts": str(probe.class_counts),
                        "baseline_target_assignment_rate": baseline_centroid["target_assignment_rate"],
                        "baseline_source_assignment_rate": baseline_centroid["source_assignment_rate"],
                        "baseline_target_minus_source_similarity": baseline_centroid["target_minus_source_similarity"],
                        "baseline_target_probability": baseline_probe["target_probability"],
                        "baseline_source_probability": baseline_probe["source_probability"],
                        "baseline_target_minus_source_probability": baseline_probe["target_minus_source_probability"],
                        "baseline_target_prediction_rate": baseline_probe["target_prediction_rate"],
                        "baseline_source_prediction_rate": baseline_probe["source_prediction_rate"],
                    })
                    by_condition: dict[str, np.ndarray] = {}
                    for beta in config["betas"]:
                        for intervention_type, delta in deltas.items():
                            steered = apply_steering(baseline, delta, beta)
                            by_condition[intervention_type] = steered
                            common = {"model": model_spec["name"], "layer": layer, "split": split["id"], "source_group": source_group, "target_group": target_group, "beta": beta, "intervention_type": intervention_type}
                            centroid_items = evaluate_held_out_centroid_items(steered, centroids, groups, source_group, target_group)
                            probe_items = evaluate_probe_items(probe, steered, source_group, target_group)
                            for item, centroid_item, probe_item in zip(evaluation_items[source_group], centroid_items, probe_items):
                                item_common = common | {"eval_item_id": item["id"]}
                                transition_rows.append(item_common | centroid_item)
                                probe_rows.append(item_common | probe_item)
                        rsm = compare_rsm_conditions(baseline, by_condition["task"], by_condition["matched_random"], by_condition["opposite"])
                        for intervention_type, key in (("task", "task"), ("matched_random", "random"), ("opposite", "opposite")):
                            invariant_rows.append({
                                "model": model_spec["name"], "layer": layer, "split": split["id"], "source_group": source_group, "target_group": target_group,
                                "beta": beta, "intervention_type": intervention_type,
                                "rsm_pearson": rsm[f"rsm_pearson_{key}"], "invariant_violation_score": rsm[f"ivs_{key}"],
                                "rsm_frobenius_distance": rsm[f"rsm_frobenius_{key}"], "ivs_advantage_vs_random": rsm["ivs_advantage_vs_random"],
                            })
    write_csv(OUTPUT_DIR / "transition_metrics.csv", TRANSITION_FIELDS, aggregate_result_rows(TRANSITION_FIELDS, transition_rows))
    write_csv(OUTPUT_DIR / "probe_metrics.csv", PROBE_FIELDS, aggregate_result_rows(PROBE_FIELDS, probe_rows))
    write_csv(OUTPUT_DIR / "invariant_metrics.csv", INVARIANT_FIELDS, aggregate_result_rows(INVARIANT_FIELDS, invariant_rows))
    write_csv(OUTPUT_DIR / "pair_summary.csv", PAIR_SUMMARY_FIELDS, aggregate_result_rows(PAIR_SUMMARY_FIELDS, pair_rows))
    save_json({"config_path": str(CONFIG_PATH.relative_to(ROOT)), "planned_counts": expected_condition_counts(config)}, OUTPUT_DIR / "validation_summary.json")
    save_json({"splits": config["splits"], "input_dataset": config["input_dataset"]}, OUTPUT_DIR / "split_metadata.json")


def main() -> None:
    """Validate the plan or run the explicit official validation."""
    args = parse_args()
    config = load_frozen_config()
    prompts = load_json(PROMPTS_PATH)
    validate_config(config, prompts)
    counts = expected_condition_counts(config)
    if args.dry_run:
        print("EXP-018 dry-run: configuration and prompt splits valid; no model loaded.")
        for name, count in counts.items():
            print(f"{name}: {count}")
        return
    run_validation(config, prompts, args.dtype)
    print(f"EXP-018 completed: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
