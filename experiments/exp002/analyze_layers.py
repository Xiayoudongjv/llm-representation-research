"""EXP-002: analyze representation geometry across Transformer layers."""

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
from src.plotting import plot_layer_metric, plot_pca_2d
from src.representation_metrics import (
    compute_silhouette,
    cosine_similarity_matrix,
    group_centroid_distances,
    mean_between_group_similarity,
    mean_within_group_similarity,
    pca_2d,
    separation_score,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--prompts_path", default="experiments/exp001/prompts.json")
    parser.add_argument("--layers", default="0,4,8,12,16,20,24,28")
    parser.add_argument("--output_dir", default="results/exp002")
    return parser.parse_args()


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _pearson_correlation(x, y) -> float:
    x_array = np.asarray(x, dtype=float)
    y_array = np.asarray(y, dtype=float)
    if np.std(x_array) == 0 or np.std(y_array) == 0:
        return float("nan")
    return float(np.corrcoef(x_array, y_array)[0, 1])


def main() -> None:
    args = parse_args()
    layers = [int(value.strip()) for value in args.layers.split(",") if value.strip()]
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
    representations_by_layer = {layer: [] for layer in layers}
    token_counts = []
    final_norms = []

    with torch.no_grad():
        for item in prompts:
            inputs = tokenizer(item["text"], return_tensors="pt")
            token_counts.append(int(inputs["input_ids"].shape[-1]))
            inputs = {name: value.to(device) for name, value in inputs.items()}
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            hidden_states = outputs.hidden_states
            if any(layer < 0 or layer >= len(hidden_states) for layer in layers):
                raise ValueError(f"Requested layers {layers} exceed available hidden-state indices 0..{len(hidden_states) - 1}.")
            final_norms.append(float(torch.linalg.vector_norm(hidden_states[-1][0, -1, :]).item()))
            for layer in layers:
                representation = hidden_states[layer][0, -1, :].detach().cpu().float().numpy()
                representations_by_layer[layer].append(representation)

    output_dir.mkdir(parents=True, exist_ok=True)
    layer_rows = []
    group_rows = []
    centroid_results = {}
    for layer in layers:
        matrix = np.stack(representations_by_layer[layer]).astype(np.float32)
        similarity = cosine_similarity_matrix(matrix)
        coords, explained = pca_2d(matrix)
        within_mean, per_group = mean_within_group_similarity(similarity, groups)
        between_mean = mean_between_group_similarity(similarity, groups)
        separation = separation_score(within_mean, between_mean)
        silhouette = compute_silhouette(matrix, groups)
        centroid_results[str(layer)] = group_centroid_distances(matrix, groups)
        layer_rows.append([
            layer,
            within_mean,
            between_mean,
            separation,
            silhouette,
            explained[0],
            explained[1],
            float(np.sum(explained)),
        ])
        group_rows.extend([[layer, group, value] for group, value in per_group.items()])
        plot_pca_2d(coords, prompt_ids, str(output_dir / f"pca_layer_{layer:02d}.png"), f"EXP-002 PCA: layer {layer}")

    _write_csv(
        output_dir / "layer_metrics.csv",
        ["layer", "within_similarity", "between_similarity", "separation_score", "silhouette_score", "pca_pc1_variance", "pca_pc2_variance", "pca_2d_total_variance"],
        layer_rows,
    )
    _write_csv(output_dir / "group_metrics.csv", ["layer", "group", "within_similarity"], group_rows)
    _write_csv(output_dir / "prompt_token_counts.csv", ["id", "group", "token_count"], [[item["id"], item["group"], count] for item, count in zip(prompts, token_counts)])
    (output_dir / "centroid_distances.json").write_text(json.dumps(centroid_results, indent=2) + "\n", encoding="utf-8")
    mean_by_group = {}
    for group in dict.fromkeys(groups):
        values = [count for item, count in zip(prompts, token_counts) if item["group"] == group]
        mean_by_group[group] = float(np.mean(values))
    diagnostics = {
        "token_count_final_representation_norm_pearson_r": _pearson_correlation(token_counts, final_norms),
        "mean_token_count_by_group": mean_by_group,
        "min_token_count": min(token_counts),
        "max_token_count": max(token_counts),
        "note": "This is a preliminary diagnostic and does not eliminate lexical or template confounds.",
    }
    (output_dir / "diagnostics.json").write_text(json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")

    layers_for_plot = [row[0] for row in layer_rows]
    plot_layer_metric(layers_for_plot, [row[3] for row in layer_rows], str(output_dir / "layer_separation.png"), "Separation score", "EXP-002 Layer-wise Separation")
    plot_layer_metric(layers_for_plot, [row[4] for row in layer_rows], str(output_dir / "layer_silhouette.png"), "Silhouette score", "EXP-002 Layer-wise Silhouette")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
