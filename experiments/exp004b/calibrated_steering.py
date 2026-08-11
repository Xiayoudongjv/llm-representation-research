"""EXP-004B: evaluate calibrated centroid-difference steering."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.model_loader import load_causal_lm, load_tokenizer, print_model_info
from src.plotting import plot_line_series
from src.steering import apply_static_steering, compute_group_centroids, cosine_to_centroids, nearest_centroid_labels


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument("--source_group", default="logic")
    parser.add_argument("--target_group", default="causality")
    parser.add_argument("--betas", default="-1,-0.5,0,0.25,0.5,0.75,1,1.5,2")
    parser.add_argument("--output_dir", default="results/exp004b")
    return parser.parse_args()


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    betas = [float(value.strip()) for value in args.betas.split(",") if value.strip()]
    prompts_path = PROJECT_ROOT / args.prompts_path
    output_dir = PROJECT_ROOT / args.output_dir
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    prompt_ids = [item["id"] for item in prompts]
    groups = [item["group"] for item in prompts]

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
    centroids = compute_group_centroids(matrix, groups)
    if args.source_group not in centroids or args.target_group not in centroids:
        raise ValueError(f"Both source and target groups must exist. Available groups: {sorted(centroids)}")
    delta = centroids[args.target_group] - centroids[args.source_group]
    delta_norm = float(np.linalg.norm(delta))
    if delta_norm < 1e-12:
        raise ValueError("The source-target centroid delta is too small to calibrate.")
    source_indices = [index for index, group in enumerate(groups) if group == args.source_group]
    source_matrix = matrix[source_indices]
    source_ids = [prompt_ids[index] for index in source_indices]
    source_norms = np.linalg.norm(source_matrix, axis=1)
    centroid_pair = {args.source_group: centroids[args.source_group], args.target_group: centroids[args.target_group]}

    metric_rows = []
    assignment_rows = []
    curve_source = []
    curve_target = []
    target_rates = []
    relative_perturbations = []
    for beta in betas:
        perturbation = beta * delta
        steered = apply_static_steering(source_matrix, delta, beta)
        similarities = cosine_to_centroids(steered, centroid_pair)
        nearest_labels, nearest_scores = nearest_centroid_labels(steered, centroids)
        source_similarities = similarities[args.source_group]
        target_similarities = similarities[args.target_group]
        perturbation_norm = float(np.linalg.norm(perturbation))
        relative_norms = perturbation_norm / np.maximum(source_norms, 1e-12)
        mean_source = float(np.mean(source_similarities))
        mean_target = float(np.mean(target_similarities))
        target_rate = float(np.mean([label == args.target_group for label in nearest_labels]))
        mean_relative = float(np.mean(relative_norms))
        metric_rows.append([beta, mean_source, mean_target, mean_target - mean_source, target_rate, perturbation_norm, mean_relative])
        curve_source.append(mean_source)
        curve_target.append(mean_target)
        target_rates.append(target_rate)
        relative_perturbations.append(mean_relative)
        for prompt_id, nearest, score, source_similarity, target_similarity, relative_norm in zip(source_ids, nearest_labels, nearest_scores, source_similarities, target_similarities, relative_norms):
            assignment_rows.append([beta, prompt_id, args.source_group, nearest, score, source_similarity, target_similarity, perturbation_norm, relative_norm])

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "calibrated_steering_metrics.csv", ["beta", "mean_similarity_to_source", "mean_similarity_to_target", "target_minus_source_similarity", "target_assignment_rate", "mean_perturbation_norm", "mean_relative_perturbation_norm"], metric_rows)
    _write_csv(output_dir / "calibrated_steering_assignments.csv", ["beta", "prompt_id", "original_group", "nearest_group", "nearest_score", "similarity_to_source", "similarity_to_target", "perturbation_norm", "relative_perturbation_norm"], assignment_rows)
    metadata = {
        "model_name": args.model_name,
        "layer": args.layer,
        "source_group": args.source_group,
        "target_group": args.target_group,
        "hidden_size": int(matrix.shape[1]),
        "delta_norm": delta_norm,
        "betas": betas,
        "prompt_count": len(prompts),
        "source_prompt_count": len(source_indices),
        "note": "This is representation-level calibrated centroid steering, not generation-time intervention.",
    }
    (output_dir / "calibrated_steering_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    plot_line_series(betas, {"source centroid similarity": curve_source, "target centroid similarity": curve_target}, str(output_dir / "calibrated_steering_curve.png"), "Beta", "Mean cosine similarity", "EXP-004B Calibrated Steering Curve")
    plot_line_series(betas, {"target assignment rate": target_rates}, str(output_dir / "calibrated_target_assignment_rate.png"), "Beta", "Target assignment rate", "EXP-004B Target Assignment Rate")
    plot_line_series(betas, {"mean relative perturbation norm": relative_perturbations}, str(output_dir / "relative_perturbation_norm.png"), "Beta", "Mean relative perturbation norm", "EXP-004B Relative Perturbation")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
