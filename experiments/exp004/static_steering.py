"""EXP-004: evaluate a static centroid-difference steering direction."""

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
from src.steering import (
    apply_static_steering,
    compute_group_centroids,
    compute_steering_vector,
    cosine_to_centroids,
    nearest_centroid_labels,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--layer", type=int, default=16)
    parser.add_argument("--source_group", default="logic")
    parser.add_argument("--target_group", default="causality")
    parser.add_argument("--alphas", default="-2,-1,-0.5,0,0.5,1,2")
    parser.add_argument("--output_dir", default="results/exp004")
    return parser.parse_args()


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    alphas = [float(value.strip()) for value in args.alphas.split(",") if value.strip()]
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
    raw_vector = centroids[args.target_group] - centroids[args.source_group]
    vector_norm = float(np.linalg.norm(raw_vector))
    steering_vector = compute_steering_vector(centroids[args.source_group], centroids[args.target_group], normalize=True)
    source_indices = [index for index, group in enumerate(groups) if group == args.source_group]
    source_matrix = matrix[source_indices]
    source_ids = [prompt_ids[index] for index in source_indices]
    centroid_pair = {args.source_group: centroids[args.source_group], args.target_group: centroids[args.target_group]}

    metric_rows = []
    assignment_rows = []
    curve_source = []
    curve_target = []
    target_rates = []
    for alpha in alphas:
        steered = apply_static_steering(source_matrix, steering_vector, alpha)
        similarities = cosine_to_centroids(steered, centroid_pair)
        nearest_labels, nearest_scores = nearest_centroid_labels(steered, centroids)
        source_similarities = similarities[args.source_group]
        target_similarities = similarities[args.target_group]
        target_rate = float(np.mean([label == args.target_group for label in nearest_labels]))
        mean_source = float(np.mean(source_similarities))
        mean_target = float(np.mean(target_similarities))
        metric_rows.append([alpha, mean_source, mean_target, mean_target - mean_source, target_rate])
        curve_source.append(mean_source)
        curve_target.append(mean_target)
        target_rates.append(target_rate)
        for prompt_id, nearest, score, source_similarity, target_similarity in zip(source_ids, nearest_labels, nearest_scores, source_similarities, target_similarities):
            assignment_rows.append([alpha, prompt_id, args.source_group, nearest, score, source_similarity, target_similarity])

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "steering_metrics.csv", ["alpha", "mean_similarity_to_source", "mean_similarity_to_target", "target_minus_source_similarity", "target_assignment_rate"], metric_rows)
    _write_csv(output_dir / "steering_assignments.csv", ["alpha", "prompt_id", "original_group", "nearest_group", "nearest_score", "similarity_to_source", "similarity_to_target"], assignment_rows)
    metadata = {
        "model_name": args.model_name,
        "layer": args.layer,
        "source_group": args.source_group,
        "target_group": args.target_group,
        "hidden_size": int(matrix.shape[1]),
        "vector_norm_before_normalization": vector_norm,
        "alphas": alphas,
        "prompt_count": len(prompts),
        "source_prompt_count": len(source_indices),
        "note": "This is representation-level steering, not generation-time intervention.",
    }
    (output_dir / "steering_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    plot_line_series(alphas, {"source centroid similarity": curve_source, "target centroid similarity": curve_target}, str(output_dir / "steering_curve.png"), "Alpha", "Mean cosine similarity", "EXP-004 Static Steering Curve")
    plot_line_series(alphas, {"target assignment rate": target_rates}, str(output_dir / "target_assignment_rate.png"), "Alpha", "Target assignment rate", "EXP-004 Target Assignment Rate")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
