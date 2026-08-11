"""EXP-006: evaluate relational structure during calibrated steering."""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.invariants import summarize_invariant_metrics
from src.model_loader import load_causal_lm, load_tokenizer, print_model_info
from src.steering import apply_static_steering, compute_group_centroids, cosine_to_centroids, nearest_centroid_labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument("--groups", default="logic,causality,analogy,definition")
    parser.add_argument("--betas", default="0,0.25,0.5,0.75,1,1.5,2")
    parser.add_argument("--output_dir", default="results/exp006")
    return parser.parse_args()


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _first_beta(rows, betas, predicate):
    for row, beta in zip(rows, betas):
        if predicate(row):
            return beta
    return None


def _plot_scatter(x, y, output_path: Path, xlabel: str, ylabel: str, title: str) -> None:
    figure, axis = plt.subplots(figsize=(9, 6))
    axis.scatter(x, y)
    axis.set_xlabel(xlabel)
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def _plot_beta_means(betas, values, output_path: Path, ylabel: str, title: str) -> None:
    figure, axis = plt.subplots(figsize=(9, 6))
    axis.plot(betas, values, marker="o")
    axis.set_xlabel("Beta")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.set_xticks(betas)
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    groups = [value.strip() for value in args.groups.split(",") if value.strip()]
    betas = [float(value.strip()) for value in args.betas.split(",") if value.strip()]
    prompts_path = PROJECT_ROOT / args.prompts_path
    output_dir = PROJECT_ROOT / args.output_dir
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    prompt_ids = [item["id"] for item in prompts]
    prompt_groups = [item["group"] for item in prompts]

    print(f"Loading model: {args.model_name}")
    tokenizer = load_tokenizer(args.model_name)
    model = load_causal_lm(args.model_name, dtype=args.dtype)
    print_model_info(model)
    device = next(model.parameters()).device
    representations = []
    with torch.no_grad():
        for item in prompts:
            inputs = tokenizer(item["text"], return_tensors="pt")
            inputs = {name: value.to(device) for name, value in inputs.items()}
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            hidden_states = outputs.hidden_states
            if not 0 <= args.layer < len(hidden_states):
                raise ValueError(f"Layer {args.layer} is out of range for hidden-state indices 0..{len(hidden_states) - 1}.")
            representations.append(hidden_states[args.layer][0, -1, :].detach().cpu().float().numpy())

    matrix = np.stack(representations).astype(np.float32)
    centroids = compute_group_centroids(matrix, prompt_groups)
    missing = [group for group in groups if group not in centroids]
    if missing:
        raise ValueError(f"Requested groups are missing from prompts: {missing}")

    invariant_rows = []
    tradeoff_rows = []
    pair_records = {}
    all_scatter_x = []
    all_scatter_y = []
    for source_group, target_group in itertools.permutations(groups, 2):
        source_indices = [index for index, group in enumerate(prompt_groups) if group == source_group]
        source_matrix = matrix[source_indices]
        source_ids = [prompt_ids[index] for index in source_indices]
        source_norms = np.linalg.norm(source_matrix, axis=1)
        delta = centroids[target_group] - centroids[source_group]
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm < 1e-12:
            raise ValueError(f"Centroid delta for {source_group}->{target_group} is near zero.")
        centroid_pair = {source_group: centroids[source_group], target_group: centroids[target_group]}
        before_rsm_reps = source_matrix
        pair_records[(source_group, target_group)] = []
        for beta in betas:
            perturbation = beta * delta
            steered = apply_static_steering(source_matrix, delta, beta)
            similarities = cosine_to_centroids(steered, centroid_pair)
            nearest_labels, _ = nearest_centroid_labels(steered, centroids)
            source_similarities = similarities[source_group]
            target_similarities = similarities[target_group]
            relative_norms = float(np.linalg.norm(perturbation)) / np.maximum(source_norms, 1e-12)
            invariant = summarize_invariant_metrics(before_rsm_reps, steered)
            target_rate = float(np.mean([label == target_group for label in nearest_labels]))
            record = {
                "beta": beta,
                "target_rate": target_rate,
                "target_minus_source": float(np.mean(target_similarities) - np.mean(source_similarities)),
                "relative_norm": float(np.mean(relative_norms)),
                **invariant,
            }
            pair_records[(source_group, target_group)].append(record)
            invariant_rows.append([source_group, target_group, beta, np.mean(source_similarities), np.mean(target_similarities), record["target_minus_source"], target_rate, record["relative_norm"], invariant["rsm_pearson"], invariant["rsm_spearman"], invariant["invariant_violation_score"], invariant["rsm_frobenius_distance"]])
            tradeoff_rows.append([source_group, target_group, beta, target_rate, record["target_minus_source"], invariant["invariant_violation_score"], invariant["rsm_pearson"], record["relative_norm"]])
            all_scatter_x.append(target_rate)
            all_scatter_y.append(invariant["invariant_violation_score"])

    pair_summary_rows = []
    for source_group, target_group in itertools.permutations(groups, 2):
        rows = pair_records[(source_group, target_group)]
        min_half = _first_beta(rows, betas, lambda row: row["target_rate"] >= 0.5)
        min_one = _first_beta(rows, betas, lambda row: row["target_rate"] >= 1.0)
        half_row = next((row for row in rows if row["beta"] == min_half), None)
        one_row = next((row for row in rows if row["beta"] == min_one), None)
        final = rows[-1]
        pair_summary_rows.append([source_group, target_group, min_half, min_one, half_row["invariant_violation_score"] if half_row else None, one_row["invariant_violation_score"] if one_row else None, final["beta"], final["target_rate"], final["invariant_violation_score"], final["rsm_pearson"], final["relative_norm"]])

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "invariant_metrics.csv", ["source_group", "target_group", "beta", "mean_similarity_to_source", "mean_similarity_to_target", "target_minus_source_similarity", "target_assignment_rate", "mean_relative_perturbation_norm", "rsm_pearson", "rsm_spearman", "invariant_violation_score", "rsm_frobenius_distance"], invariant_rows)
    _write_csv(output_dir / "invariant_pair_summary.csv", ["source_group", "target_group", "min_beta_assignment_ge_0_5", "min_beta_assignment_eq_1", "invariant_violation_at_min_beta_ge_0_5", "invariant_violation_at_min_beta_eq_1", "rsm_pearson_at_min_beta_ge_0_5", "rsm_pearson_at_min_beta_eq_1", "final_beta", "final_target_assignment_rate", "final_invariant_violation_score", "final_rsm_pearson", "final_relative_perturbation_norm"], pair_summary_rows)
    _write_csv(output_dir / "transition_invariant_tradeoff.csv", ["source_group", "target_group", "beta", "target_assignment_rate", "target_minus_source_similarity", "invariant_violation_score", "rsm_pearson", "mean_relative_perturbation_norm"], tradeoff_rows)
    metadata = {
        "model_name": args.model_name,
        "layer": args.layer,
        "groups": groups,
        "betas": betas,
        "prompt_count": len(prompts),
        "hidden_size": int(matrix.shape[1]),
        "number_of_pairs": len(list(itertools.permutations(groups, 2))),
        "invariant_definition": "IVS = 1 - Pearson correlation between upper-triangle source RSM values before and after steering.",
        "note_rsm_correlation": "RSM correlation is only a proxy for relational invariance.",
        "note_analysis_scope": "This is representation-level analysis, not generation-time reasoning evaluation.",
    }
    (output_dir / "invariant_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    means_by_beta = []
    assignment_means = []
    pearson_means = []
    for beta in betas:
        rows_at_beta = [row for pair_rows in pair_records.values() for row in pair_rows if row["beta"] == beta]
        means_by_beta.append(float(np.mean([row["invariant_violation_score"] for row in rows_at_beta])))
        assignment_means.append(float(np.mean([row["target_rate"] for row in rows_at_beta])))
        pearson_means.append(float(np.mean([row["rsm_pearson"] for row in rows_at_beta])))
    _plot_scatter(all_scatter_x, all_scatter_y, output_dir / "assignment_vs_invariant_violation.png", "Target assignment rate", "Invariant violation score", "EXP-006 Assignment vs Invariant Violation")
    _plot_beta_means(betas, means_by_beta, output_dir / "beta_vs_invariant_violation.png", "Mean invariant violation score", "EXP-006 Beta vs Invariant Violation")
    _plot_beta_means(betas, assignment_means, output_dir / "beta_vs_assignment_rate.png", "Mean target assignment rate", "EXP-006 Beta vs Assignment Rate")
    _plot_beta_means(betas, pearson_means, output_dir / "beta_vs_rsm_pearson.png", "Mean RSM Pearson correlation", "EXP-006 Beta vs RSM Pearson")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
