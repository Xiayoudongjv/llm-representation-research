"""EXP-005: test calibrated centroid steering across ordered group pairs."""

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
    parser.add_argument("--output_dir", default="results/exp005")
    return parser.parse_args()


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _first_beta(values, betas, predicate):
    for value, beta in zip(values, betas):
        if predicate(value):
            return beta
    return None


def _heatmap(matrix, groups, output_path: Path, title: str, colorbar_label: str) -> None:
    figure, axis = plt.subplots(figsize=(8, 7))
    image = axis.imshow(matrix, cmap="viridis")
    axis.set_xticks(range(len(groups)), groups, rotation=45, ha="right")
    axis.set_yticks(range(len(groups)), groups)
    axis.set_xlabel("Target group")
    axis.set_ylabel("Source group")
    axis.set_title(title)
    figure.colorbar(image, ax=axis, label=colorbar_label)
    for row in range(len(groups)):
        for column in range(len(groups)):
            value = matrix[row, column]
            if np.isfinite(value):
                axis.text(column, row, f"{value:.2f}", ha="center", va="center", color="white")
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
    pair_list = [(source, target) for source, target in itertools.permutations(groups, 2)]
    metric_rows = []
    assignment_rows = []
    pair_records = {}

    for source_group, target_group in pair_list:
        source_indices = [index for index, group in enumerate(prompt_groups) if group == source_group]
        source_matrix = matrix[source_indices]
        source_ids = [prompt_ids[index] for index in source_indices]
        source_norms = np.linalg.norm(source_matrix, axis=1)
        delta = centroids[target_group] - centroids[source_group]
        delta_norm = float(np.linalg.norm(delta))
        if delta_norm < 1e-12:
            raise ValueError(f"Centroid delta for {source_group}->{target_group} is near zero.")
        centroid_pair = {source_group: centroids[source_group], target_group: centroids[target_group]}
        pair_records[(source_group, target_group)] = {"delta_norm": delta_norm, "rows": []}

        for beta in betas:
            perturbation = beta * delta
            steered = apply_static_steering(source_matrix, delta, beta)
            similarities = cosine_to_centroids(steered, centroid_pair)
            nearest_labels, nearest_scores = nearest_centroid_labels(steered, centroids)
            source_similarities = similarities[source_group]
            target_similarities = similarities[target_group]
            perturbation_norm = float(np.linalg.norm(perturbation))
            relative_norms = perturbation_norm / np.maximum(source_norms, 1e-12)
            mean_source = float(np.mean(source_similarities))
            mean_target = float(np.mean(target_similarities))
            target_rate = float(np.mean([label == target_group for label in nearest_labels]))
            row = [source_group, target_group, beta, mean_source, mean_target, mean_target - mean_source, target_rate, perturbation_norm, float(np.mean(relative_norms))]
            metric_rows.append(row)
            pair_records[(source_group, target_group)]["rows"].append({"beta": beta, "target_similarity": mean_target, "source_similarity": mean_source, "target_rate": target_rate, "target_minus_source": mean_target - mean_source, "relative_norm": float(np.mean(relative_norms))})
            for prompt_id, nearest, score, source_similarity, target_similarity, relative_norm in zip(source_ids, nearest_labels, nearest_scores, source_similarities, target_similarities, relative_norms):
                assignment_rows.append([source_group, target_group, beta, prompt_id, source_group, nearest, score, source_similarity, target_similarity, perturbation_norm, relative_norm])

    pair_summary_rows = []
    final_assignment = np.full((len(groups), len(groups)), np.nan)
    min_assignment = np.full((len(groups), len(groups)), np.nan)
    final_target_minus_source = np.full((len(groups), len(groups)), np.nan)
    delta_matrix = np.full((len(groups), len(groups)), np.nan)
    for source_group, target_group in pair_list:
        record = pair_records[(source_group, target_group)]
        rows = record["rows"]
        target_similarities = [row["target_similarity"] for row in rows]
        source_similarities = [row["source_similarity"] for row in rows]
        target_rates = [row["target_rate"] for row in rows]
        final = rows[-1]
        min_target_exceeds = _first_beta([target > source for target, source in zip(target_similarities, source_similarities)], betas, bool)
        min_assignment_half = _first_beta(target_rates, betas, lambda value: value >= 0.5)
        min_assignment_one = _first_beta(target_rates, betas, lambda value: value >= 1.0)
        pair_summary_rows.append([source_group, target_group, record["delta_norm"], min_target_exceeds, min_assignment_half, min_assignment_one, final["beta"], final["target_rate"], final["target_minus_source"], final["relative_norm"]])
        source_index = groups.index(source_group)
        target_index = groups.index(target_group)
        final_assignment[source_index, target_index] = final["target_rate"]
        min_assignment[source_index, target_index] = min_assignment_half if min_assignment_half is not None else np.nan
        final_target_minus_source[source_index, target_index] = final["target_minus_source"]
        delta_matrix[source_index, target_index] = record["delta_norm"]

    asymmetry_rows = []
    for position, group_a in enumerate(groups):
        for group_b in groups[position + 1:]:
            forward = pair_records[(group_a, group_b)]["rows"]
            reverse = pair_records[(group_b, group_a)]["rows"]
            forward_half = _first_beta([row["target_rate"] for row in forward], betas, lambda value: value >= 0.5)
            reverse_half = _first_beta([row["target_rate"] for row in reverse], betas, lambda value: value >= 0.5)
            forward_final = forward[-1]["target_rate"]
            reverse_final = reverse[-1]["target_rate"]
            asymmetry = abs(forward_final - reverse_final)
            asymmetry_rows.append([group_a, group_b, forward_half, reverse_half, forward_final, reverse_final, asymmetry])

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "multipair_steering_metrics.csv", ["source_group", "target_group", "beta", "mean_similarity_to_source", "mean_similarity_to_target", "target_minus_source_similarity", "target_assignment_rate", "mean_perturbation_norm", "mean_relative_perturbation_norm"], metric_rows)
    _write_csv(output_dir / "multipair_steering_assignments.csv", ["source_group", "target_group", "beta", "prompt_id", "original_group", "nearest_group", "nearest_score", "similarity_to_source", "similarity_to_target", "perturbation_norm", "relative_perturbation_norm"], assignment_rows)
    _write_csv(output_dir / "pair_summary.csv", ["source_group", "target_group", "delta_norm", "min_beta_target_similarity_exceeds_source", "min_beta_target_assignment_rate_ge_0_5", "min_beta_target_assignment_rate_eq_1", "final_beta", "final_target_assignment_rate", "final_target_minus_source_similarity", "final_relative_perturbation_norm"], pair_summary_rows)
    _write_csv(output_dir / "asymmetry_summary.csv", ["group_a", "group_b", "a_to_b_min_beta_assignment_ge_0_5", "b_to_a_min_beta_assignment_ge_0_5", "a_to_b_final_assignment_rate", "b_to_a_final_assignment_rate", "asymmetry_score"], asymmetry_rows)
    metadata = {
        "model_name": args.model_name,
        "layer": args.layer,
        "groups": groups,
        "betas": betas,
        "prompt_count": len(prompts),
        "hidden_size": int(matrix.shape[1]),
        "number_of_pairs": len(pair_list),
        "note": "This is representation-level calibrated centroid steering, not generation-time intervention.",
    }
    (output_dir / "multipair_steering_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    _heatmap(final_assignment, groups, output_dir / "final_assignment_heatmap.png", "EXP-005 Final Target Assignment Rate", "Final assignment rate")
    _heatmap(min_assignment, groups, output_dir / "min_beta_heatmap.png", "EXP-005 Minimum Beta for Assignment Rate >= 0.5", "Minimum beta")
    _heatmap(final_target_minus_source, groups, output_dir / "final_target_minus_source_heatmap.png", "EXP-005 Final Target Minus Source Similarity", "Target minus source")
    _heatmap(delta_matrix, groups, output_dir / "delta_norm_heatmap.png", "EXP-005 Centroid Delta Norm", "Delta norm")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
