"""EXP-014: Gemma calibrated centroid steering and RSM-preservation replication.

This experiment uses only local Gemma weights and raw plain-text prompts.  It
does not generate text or persist raw representation vectors.
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment_io import ensure_dir, load_json, read_csv, save_json, write_csv
from src.experiment_plots import save_line_plot
from src.extraction import extract_last_token_hidden_state, tensor_to_numpy_float32
from src.invariants import summarize_invariant_metrics
from src.steering import (
    apply_static_steering,
    compute_group_centroids,
    cosine_to_centroids,
    nearest_centroid_labels,
)


MODEL_ID = "google/gemma-3-1b-it"
LAYER = 26
GROUPS = ["logic", "causality", "analogy", "definition"]
BETAS = [-1.0, -0.5, 0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0]


def parse_args() -> argparse.Namespace:
    """Parse fixed replication paths without exposing analysis hyperparameters."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--output_dir", default="results/exp014")
    return parser.parse_args()


def local_snapshot_path() -> Path:
    """Resolve exactly one external Gemma snapshot without a network lookup."""
    cache_root = Path(os.environ.get("HF_HOME", r"D:\\AI_Cache\\huggingface"))
    snapshots = cache_root / "models--google--gemma-3-1b-it" / "snapshots"
    candidates = sorted(path for path in snapshots.iterdir() if path.is_dir()) if snapshots.exists() else []
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected one local Gemma snapshot under {snapshots}; found {len(candidates)}.")
    return candidates[0]


def first_beta(rows: list[dict[str, float]], key: str, predicate) -> float | None:
    """Return the first scheduled beta whose named metric meets a predicate."""
    for row in rows:
        if predicate(float(row[key])):
            return float(row["beta"])
    return None


def pearson_with_beta(rows: list[dict[str, float]], field: str) -> float:
    """Return a finite Pearson correlation over nonnegative scheduled betas."""
    selected = [row for row in rows if float(row["beta"]) >= 0]
    values = np.asarray([float(row[field]) for row in selected], dtype=float)
    betas = np.asarray([float(row["beta"]) for row in selected], dtype=float)
    if np.std(values) < 1e-12:
        return 0.0
    return float(np.corrcoef(betas, values)[0, 1])


def qwen_aggregates() -> list[dict[str, float]]:
    """Read complete Qwen EXP-006 transition metrics for descriptive comparison."""
    rows = read_csv(ROOT / "results/exp006/invariant_metrics.csv")
    fields = [
        "target_assignment_rate",
        "target_minus_source_similarity",
        "mean_relative_perturbation_norm",
        "invariant_violation_score",
        "rsm_pearson",
    ]
    result = []
    for beta in sorted({float(row["beta"]) for row in rows}):
        selected = [row for row in rows if float(row["beta"]) == beta]
        if len(selected) != 12:
            raise ValueError(f"Qwen EXP-006 has incomplete rows at beta {beta}.")
        means = {field: float(np.mean([float(row[field]) for row in selected])) for field in fields}
        result.append({
            "beta": beta,
            "mean_target_assignment_rate": means["target_assignment_rate"],
            "mean_target_minus_source_similarity": means["target_minus_source_similarity"],
            "mean_relative_perturbation_norm": means["mean_relative_perturbation_norm"],
            "mean_ivs": means["invariant_violation_score"],
            "mean_rsm_pearson": means["rsm_pearson"],
        })
    return result


def comparison_plot(qwen_rows, gemma_rows, field: str, output_path: Path, ylabel: str, title: str) -> None:
    """Plot Qwen and Gemma points at their observed beta schedules."""
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.plot([row["beta"] for row in qwen_rows], [row[field] for row in qwen_rows], marker="o", label="Qwen3-1.7B")
    axis.plot([row["beta"] for row in gemma_rows], [row[field] for row in gemma_rows], marker="o", label="Gemma-3-1B-IT")
    axis.set_xlabel("Beta")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def select_exploratory_beta(aggregate_rows: list[dict[str, float]]) -> tuple[float, str]:
    """Apply the predeclared assignment-first, IVS-second operating-point rule."""
    eligible = [row for row in aggregate_rows if row["mean_target_assignment_rate"] >= 0.9]
    if eligible:
        chosen = min(eligible, key=lambda row: row["mean_ivs"])
        return float(chosen["beta"]), "lowest mean IVS among betas with mean assignment >= 0.9"
    chosen = max(aggregate_rows, key=lambda row: row["mean_target_assignment_rate"] - row["mean_ivs"])
    return float(chosen["beta"]), "highest mean assignment minus mean IVS because no beta reached mean assignment >= 0.9"


def replication_status(pair_rows, aggregate_rows, qwen_rows, exploratory_beta: float) -> dict[str, str]:
    """Classify the fixed replication questions from aggregate, not prompt-tuned, evidence."""
    pairs_half = sum(first_beta(rows, "target_assignment_rate", lambda value: value >= 0.5) is not None for rows in pair_rows.values())
    pairs_one = sum(first_beta(rows, "target_assignment_rate", lambda value: value >= 1.0) is not None for rows in pair_rows.values())
    positive_movement = sum(rows[-1]["mean_target_minus_source_similarity"] > rows[0]["mean_target_minus_source_similarity"] for rows in pair_rows.values())
    movement_r = pearson_with_beta(aggregate_rows, "mean_target_minus_source_similarity")
    perturbation_r = pearson_with_beta(aggregate_rows, "mean_relative_perturbation_norm")
    ivs_r = pearson_with_beta(aggregate_rows, "mean_ivs")
    rsm_r = pearson_with_beta(aggregate_rows, "mean_rsm_pearson")
    gemma_075 = next(row for row in aggregate_rows if row["beta"] == 0.75)
    qwen_075 = next((row for row in qwen_rows if row["beta"] == 0.75), None)
    if gemma_075["mean_target_assignment_rate"] >= 0.9 and exploratory_beta == 0.75:
        beta_status = "replicated"
    elif gemma_075["mean_target_assignment_rate"] >= 0.75:
        beta_status = "partially_replicated"
    else:
        beta_status = "not_replicated"
    return {
        "calibrated_transition_success": "replicated" if pairs_half >= 3 and positive_movement >= 3 else "not_replicated",
        "multi_pair_transition_success": "replicated" if pairs_one >= 9 else ("partially_replicated" if pairs_half >= 9 else "not_replicated"),
        "transition_perturbation_tradeoff": "replicated" if movement_r > 0.8 and perturbation_r > 0.8 else "not_replicated",
        "relational_preservation_tradeoff": "replicated" if ivs_r > 0.8 and rsm_r < -0.8 else "not_replicated",
        "qwen_beta_075_frontier": beta_status,
        "diagnostic_correlations_nonnegative_betas": {
            "target_movement_vs_beta": movement_r,
            "relative_perturbation_vs_beta": perturbation_r,
            "ivs_vs_beta": ivs_r,
            "rsm_pearson_vs_beta": rsm_r,
        },
        "qwen_mean_assignment_at_beta_0_75": qwen_075["mean_target_assignment_rate"] if qwen_075 else None,
        "qwen_mean_ivs_at_beta_0_75": qwen_075["mean_ivs"] if qwen_075 else None,
    }


def main() -> None:
    """Extract Gemma layer-26 states once, then evaluate all fixed transitions."""
    args = parse_args()
    prompts = load_json(ROOT / args.prompts_path)
    if len(prompts) != 24 or {item["group"] for item in prompts} != set(GROUPS):
        raise ValueError("Expected the unchanged 24-prompt EXP-003 controlled dataset.")
    output_dir = ensure_dir(ROOT / args.output_dir)
    snapshot = local_snapshot_path()
    gpu_before = torch.cuda.memory_allocated(0)
    config = AutoConfig.from_pretrained(snapshot, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(snapshot, local_files_only=True, dtype=torch.float16, device_map="auto")
    model.eval()
    parameter = next(model.parameters())
    if parameter.device.type != "cuda":
        raise RuntimeError(f"Expected CUDA model placement; got {parameter.device}.")
    gpu_after_load = torch.cuda.memory_allocated(0)

    representations = []
    token_counts = []
    with torch.no_grad():
        for item in prompts:
            inputs = tokenizer(item["text"], return_tensors="pt")
            token_counts.append(int(inputs["input_ids"].shape[-1]))
            inputs = {name: value.to(parameter.device) for name, value in inputs.items()}
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            if len(outputs.hidden_states) != 27:
                raise ValueError(f"Expected 27 Gemma hidden states; found {len(outputs.hidden_states)}.")
            representations.append(tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, LAYER)))

    matrix = np.stack(representations).astype(np.float32)
    labels = [item["group"] for item in prompts]
    centroids = compute_group_centroids(matrix, labels)
    pair_rows: dict[tuple[str, str], list[dict[str, float]]] = {}
    invariant_rows: list[dict[str, float | str]] = []
    steering_rows: list[dict[str, float | str]] = []

    for source_group, target_group in itertools.permutations(GROUPS, 2):
        source_indices = [index for index, group in enumerate(labels) if group == source_group]
        source_matrix = matrix[source_indices]
        source_norms = np.linalg.norm(source_matrix, axis=1)
        delta = centroids[target_group] - centroids[source_group]
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm < 1e-12:
            raise ValueError(f"Centroid delta for {source_group}->{target_group} is near zero.")
        pair_key = (source_group, target_group)
        pair_rows[pair_key] = []
        centroid_pair = {source_group: centroids[source_group], target_group: centroids[target_group]}

        for beta in BETAS:
            steered = apply_static_steering(source_matrix, delta, beta)
            similarities = cosine_to_centroids(steered, centroid_pair)
            nearest_labels, _ = nearest_centroid_labels(steered, centroids)
            invariant = summarize_invariant_metrics(source_matrix, steered)
            perturbation_norm = float(abs(beta) * delta_norm)
            record = {
                "source_group": source_group,
                "target_group": target_group,
                "beta": beta,
                "delta_norm": delta_norm,
                "mean_source_similarity": float(np.mean(similarities[source_group])),
                "mean_target_similarity": float(np.mean(similarities[target_group])),
                "mean_target_minus_source_similarity": float(np.mean(similarities[target_group]) - np.mean(similarities[source_group])),
                "target_assignment_rate": float(np.mean([label == target_group for label in nearest_labels])),
                "relative_perturbation_norm": float(np.mean(perturbation_norm / np.maximum(source_norms, 1e-12))),
                "rsm_pearson": float(invariant["rsm_pearson"]),
                "invariant_violation_score": float(invariant["invariant_violation_score"]),
                "rsm_frobenius_distance": float(invariant["rsm_frobenius_distance"]),
            }
            steering_rows.append({key: record[key] for key in ["source_group", "target_group", "beta", "delta_norm", "mean_source_similarity", "mean_target_similarity", "mean_target_minus_source_similarity", "target_assignment_rate", "relative_perturbation_norm"]})
            invariant_rows.append({key: record[key] for key in ["source_group", "target_group", "beta", "rsm_pearson", "invariant_violation_score", "rsm_frobenius_distance"]})
            pair_rows[pair_key].append(record)

    aggregate_rows = []
    for beta in BETAS:
        rows = [row for pair in pair_rows.values() for row in pair if row["beta"] == beta]
        aggregate_rows.append({
            "beta": beta,
            "mean_target_assignment_rate": float(np.mean([row["target_assignment_rate"] for row in rows])),
            "mean_target_minus_source_similarity": float(np.mean([row["mean_target_minus_source_similarity"] for row in rows])),
            "mean_relative_perturbation_norm": float(np.mean([row["relative_perturbation_norm"] for row in rows])),
            "mean_ivs": float(np.mean([row["invariant_violation_score"] for row in rows])),
            "mean_rsm_pearson": float(np.mean([row["rsm_pearson"] for row in rows])),
        })

    summary_rows = []
    for source_group, target_group in itertools.permutations(GROUPS, 2):
        rows = pair_rows[(source_group, target_group)]
        final = rows[-1]
        summary_rows.append({
            "source_group": source_group,
            "target_group": target_group,
            "delta_norm": rows[0]["delta_norm"],
            "first_beta_target_gt_source": first_beta(rows, "mean_target_minus_source_similarity", lambda value: value > 0),
            "first_beta_assignment_ge_0_5": first_beta(rows, "target_assignment_rate", lambda value: value >= 0.5),
            "first_beta_assignment_eq_1": first_beta(rows, "target_assignment_rate", lambda value: value >= 1.0),
            "final_target_minus_source_similarity": final["mean_target_minus_source_similarity"],
            "final_relative_perturbation_norm": final["relative_perturbation_norm"],
            "final_ivs": final["invariant_violation_score"],
            "final_rsm_pearson": final["rsm_pearson"],
        })

    qwen_rows = qwen_aggregates()
    best_beta, best_rule = select_exploratory_beta(aggregate_rows)
    statuses = replication_status(pair_rows, aggregate_rows, qwen_rows, best_beta)
    pairs_half = sum(row["first_beta_assignment_ge_0_5"] is not None for row in summary_rows)
    pairs_one = sum(row["first_beta_assignment_eq_1"] is not None for row in summary_rows)
    summary = {
        "model": MODEL_ID,
        "layer": LAYER,
        "number_of_pairs": len(summary_rows),
        "betas": BETAS,
        "pairs_reaching_assignment_ge_0_5": pairs_half,
        "pairs_reaching_assignment_eq_1": pairs_one,
        "mean_assignment_by_beta": {str(row["beta"]): row["mean_target_assignment_rate"] for row in aggregate_rows},
        "mean_ivs_by_beta": {str(row["beta"]): row["mean_ivs"] for row in aggregate_rows},
        "mean_rsm_pearson_by_beta": {str(row["beta"]): row["mean_rsm_pearson"] for row in aggregate_rows},
        "mean_relative_perturbation_by_beta": {str(row["beta"]): row["mean_relative_perturbation_norm"] for row in aggregate_rows},
        "median_first_beta_assignment_ge_0_5": float(np.median([row["first_beta_assignment_ge_0_5"] for row in summary_rows if row["first_beta_assignment_ge_0_5"] is not None])) if pairs_half else None,
        "median_first_beta_assignment_eq_1": float(np.median([row["first_beta_assignment_eq_1"] for row in summary_rows if row["first_beta_assignment_eq_1"] is not None])) if pairs_one else None,
        "best_exploratory_beta_by_rule": {"beta": best_beta, "rule": best_rule},
        "replication_status": statuses,
        "warning": "Representation-level centroid steering and RSM preservation do not establish reasoning improvement or logical invariance.",
    }
    metadata = {
        "model": MODEL_ID,
        "model_class": model.__class__.__name__,
        "config_class": config.__class__.__name__,
        "model_type": config.model_type,
        "runtime_dtype": str(parameter.dtype),
        "runtime_device": str(parameter.device),
        "hidden_state_count": 27,
        "hidden_size": config.hidden_size,
        "layer": LAYER,
        "prompt_format": "raw_plain_text_no_chat_template",
        "batch_size": 1,
        "min_token_count": min(token_counts),
        "max_token_count": max(token_counts),
        "gpu_memory_before_load_bytes": gpu_before,
        "gpu_memory_after_load_bytes": gpu_after_load,
        "gpu_memory_after_final_forward_bytes": torch.cuda.memory_allocated(0),
        "note": "Only in-memory float32 last-token representations were used; no representations were saved.",
    }
    write_csv(output_dir / "steering_metrics.csv", list(steering_rows[0]), steering_rows)
    write_csv(output_dir / "invariant_metrics.csv", list(invariant_rows[0]), invariant_rows)
    write_csv(output_dir / "pair_summary.csv", list(summary_rows[0]), summary_rows)
    write_csv(output_dir / "aggregate_by_beta.csv", list(aggregate_rows[0]), aggregate_rows)
    save_json(summary, output_dir / "replication_summary.json")
    save_json(metadata, output_dir / "model_metadata.json")
    save_line_plot(BETAS, {"Gemma mean target assignment rate": [row["mean_target_assignment_rate"] for row in aggregate_rows]}, output_dir / "assignment_by_beta.png", title="EXP-014 Gemma Assignment by Beta", xlabel="Beta", ylabel="Mean target assignment rate")
    save_line_plot(BETAS, {"Gemma mean invariant violation score": [row["mean_ivs"] for row in aggregate_rows]}, output_dir / "ivs_by_beta.png", title="EXP-014 Gemma IVS by Beta", xlabel="Beta", ylabel="Mean IVS")
    save_line_plot(BETAS, {"Gemma mean relative perturbation norm": [row["mean_relative_perturbation_norm"] for row in aggregate_rows]}, output_dir / "perturbation_by_beta.png", title="EXP-014 Gemma Perturbation by Beta", xlabel="Beta", ylabel="Mean relative perturbation norm")
    comparison_plot(qwen_rows, aggregate_rows, "mean_target_assignment_rate", output_dir / "qwen_vs_gemma_assignment.png", "Mean target assignment rate", "Qwen vs Gemma Assignment")
    comparison_plot(qwen_rows, aggregate_rows, "mean_ivs", output_dir / "qwen_vs_gemma_ivs.png", "Mean IVS", "Qwen vs Gemma IVS")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
