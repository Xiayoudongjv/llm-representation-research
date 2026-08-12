"""EXP-013: Gemma replication of EXP-003 controlled geometry metrics."""

from __future__ import annotations

import argparse
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
from src.extraction import extract_last_token_hidden_state, tensor_to_numpy_float32
from src.representation_metrics import (
    compute_silhouette,
    cosine_similarity_matrix,
    mean_between_group_similarity,
    mean_within_group_similarity,
    pca_2d,
    separation_score,
)


MODEL_ID = "google/gemma-3-1b-it"
LAYERS = [0, 4, 8, 12, 16, 20, 23, 26]
GROUPS = ["logic", "causality", "analogy", "definition"]


def parse_args() -> argparse.Namespace:
    """Parse fixed local-replication inputs and output location."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--output_dir", default="results/exp013")
    return parser.parse_args()


def local_snapshot_path() -> Path:
    """Resolve the manually cached Gemma snapshot without any network lookup."""
    cache_root = Path(os.environ.get("HF_HOME", r"D:\AI_Cache\huggingface"))
    snapshots = cache_root / "models--google--gemma-3-1b-it" / "snapshots"
    candidates = sorted(path for path in snapshots.iterdir() if path.is_dir()) if snapshots.exists() else []
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected one local Gemma snapshot under {snapshots}; found {len(candidates)}.")
    return candidates[0]


def variant_similarities(similarity: np.ndarray, prompts: list[dict]) -> tuple[float, float]:
    """Match EXP-003's cross-variant within- versus cross-group similarities."""
    same_group_cross_variant = []
    for group in dict.fromkeys(item["group"] for item in prompts):
        originals = [index for index, item in enumerate(prompts) if item["group"] == group and item["variant_type"] == "original_style"]
        paraphrases = [index for index, item in enumerate(prompts) if item["group"] == group and item["variant_type"] == "paraphrase"]
        same_group_cross_variant.extend(similarity[i, j] for i in originals for j in paraphrases)
    same_variant_cross_group = []
    for variant in ("original_style", "paraphrase"):
        indices = [index for index, item in enumerate(prompts) if item["variant_type"] == variant]
        same_variant_cross_group.extend(
            similarity[i, j] for position, i in enumerate(indices) for j in indices[position + 1:] if prompts[i]["group"] != prompts[j]["group"]
        )
    return float(np.mean(same_group_cross_variant)), float(np.mean(same_variant_cross_group))


def safe_silhouette(matrix: np.ndarray, groups: list[str]) -> float:
    """Return NaN rather than fail the replication on degenerate input."""
    try:
        return compute_silhouette(matrix, groups)
    except ValueError:
        return float("nan")


def line_plot(depths, values, output: Path, ylabel: str, title: str) -> None:
    """Save a simple normalized-depth metric curve."""
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.plot(depths, values, marker="o")
    axis.set_xlabel("Normalized hidden-state depth")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def comparison_plot(qwen_rows, gemma_rows, metric: str, output: Path, title: str) -> None:
    """Plot actual Qwen and Gemma normalized-depth points without interpolation."""
    figure, axis = plt.subplots(figsize=(7, 5))
    axis.plot([float(row["layer"]) / 28 for row in qwen_rows], [float(row[metric]) for row in qwen_rows], marker="o", label="Qwen3-1.7B")
    axis.plot([float(row["normalized_depth"]) for row in gemma_rows], [float(row[metric]) for row in gemma_rows], marker="o", label="Gemma-3-1B-IT")
    axis.set_xlabel("Normalized hidden-state depth")
    axis.set_ylabel(metric.replace("_", " "))
    axis.set_title(title)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def classify(rows: list[dict[str, object]]) -> dict[str, str]:
    """Apply conservative, result-dependent replication criteria."""
    non_embedding = [row for row in rows if int(row["layer"]) != 0]
    positive_geometry = [row for row in non_embedding if float(row["separation_score"]) > 0 and float(row["silhouette_score"]) > 0]
    positive_retention = [row for row in non_embedding if float(row["paraphrase_retention_score"]) > 0]
    separation = [float(row["separation_score"]) for row in rows]
    silhouette = [float(row["silhouette_score"]) for row in rows]
    rises_then_declines = (max(separation[1:-1], default=float("-inf")) > separation[-1]) or (max(silhouette[1:-1], default=float("-inf")) > silhouette[-1])
    best = max(non_embedding, key=lambda row: float(row["separation_score"]))
    best_depth = float(best["normalized_depth"])
    return {
        "task_associated_geometry": "replicated" if len(positive_geometry) >= 2 else ("partially_replicated" if positive_geometry else "not_replicated"),
        "paraphrase_controlled_signal": "replicated" if positive_retention else "not_replicated",
        "non_monotonic_layerwise_geometry": "replicated" if rises_then_declines else "not_replicated",
        "mid_or_middeep_peak": "replicated" if 0.3 <= best_depth <= 0.8 else ("partially_replicated" if 0.15 <= best_depth < 0.9 else "not_replicated"),
    }


def main() -> None:
    """Run fixed-prompt Gemma geometry replication without saving representations."""
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
    gpu_after_load = torch.cuda.memory_allocated(0)
    if parameter.device.type != "cuda":
        raise RuntimeError(f"Expected CUDA model placement; got {parameter.device}.")

    by_layer = {layer: [] for layer in LAYERS}
    token_counts = []
    groups = [item["group"] for item in prompts]
    for item in prompts:
        inputs = tokenizer(item["text"], return_tensors="pt")
        token_counts.append(int(inputs["input_ids"].shape[-1]))
        inputs = {name: value.to(parameter.device) for name, value in inputs.items()}
        with torch.no_grad():
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
        if len(outputs.hidden_states) != 27:
            raise ValueError(f"Expected 27 Gemma hidden states; found {len(outputs.hidden_states)}.")
        for layer in LAYERS:
            by_layer[layer].append(tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, layer)))

    layer_rows: list[dict[str, object]] = []
    group_rows: list[dict[str, object]] = []
    zero_variance_layers = []
    for layer in LAYERS:
        matrix = np.stack(by_layer[layer]).astype(np.float32)
        if np.allclose(np.var(matrix, axis=0), 0.0):
            zero_variance_layers.append(layer)
        similarity = cosine_similarity_matrix(matrix)
        within, per_group = mean_within_group_similarity(similarity, groups)
        between = mean_between_group_similarity(similarity, groups)
        same_group_cross_variant, same_variant_cross_group = variant_similarities(similarity, prompts)
        _, explained = pca_2d(matrix)
        row = {
            "layer": layer, "normalized_depth": layer / 26, "within_similarity": within,
            "between_similarity": between, "separation_score": separation_score(within, between),
            "silhouette_score": safe_silhouette(matrix, groups),
            "same_group_cross_variant_similarity": same_group_cross_variant,
            "same_variant_cross_group_similarity": same_variant_cross_group,
            "paraphrase_retention_score": same_group_cross_variant - same_variant_cross_group,
            "pca_pc1_variance": float(explained[0]), "pca_pc2_variance": float(explained[1]),
            "pca_2d_total_variance": float(np.sum(explained)),
        }
        layer_rows.append(row)
        group_rows.extend({"layer": layer, "normalized_depth": layer / 26, "group": group, "within_similarity": value} for group, value in per_group.items())
    write_csv(output_dir / "layer_metrics.csv", list(layer_rows[0]), layer_rows)
    write_csv(output_dir / "group_metrics.csv", list(group_rows[0]), group_rows)

    qwen_rows = read_csv(ROOT / "results/exp003/layer_metrics.csv")
    best_separation = max(layer_rows, key=lambda row: float(row["separation_score"]))
    best_silhouette = max(layer_rows, key=lambda row: float(row["silhouette_score"]))
    best_retention = max(layer_rows, key=lambda row: float(row["paraphrase_retention_score"]))
    qwen_best = max(qwen_rows, key=lambda row: float(row["separation_score"]))
    assessment = classify(layer_rows)
    gate = "PROCEED_TO_STEERING" if assessment["task_associated_geometry"] in {"replicated", "partially_replicated"} and assessment["paraphrase_controlled_signal"] in {"replicated", "partially_replicated"} else "PAUSE_STEERING"
    summary = {
        "model": MODEL_ID, "number_of_prompts": len(prompts), "number_of_groups": len(GROUPS),
        "layers": LAYERS, "normalized_depths": [layer / 26 for layer in LAYERS],
        "best_separation_layer": best_separation["layer"], "best_separation_normalized_depth": best_separation["normalized_depth"], "best_separation_score": best_separation["separation_score"],
        "best_silhouette_layer": best_silhouette["layer"], "best_silhouette_score": best_silhouette["silhouette_score"],
        "best_paraphrase_retention_layer": best_retention["layer"], "best_paraphrase_retention_score": best_retention["paraphrase_retention_score"],
        "positive_separation_layers": [row["layer"] for row in layer_rows if float(row["separation_score"]) > 0],
        "positive_silhouette_layers": [row["layer"] for row in layer_rows if float(row["silhouette_score"]) > 0],
        "positive_paraphrase_retention_layers": [row["layer"] for row in layer_rows if float(row["paraphrase_retention_score"]) > 0],
        "qwen_best_controlled_layer": int(qwen_best["layer"]), "qwen_best_separation_score": float(qwen_best["separation_score"]),
        "qwen_best_paraphrase_retention_score": max(float(row["paraphrase_retention_score"]) for row in qwen_rows),
        "replication_assessment": assessment, "gate_decision": gate,
        "warning": "Two models and 24 hand-designed prompts do not establish universal geometry or behavioral relevance.",
    }
    save_json(summary, output_dir / "replication_summary.json")
    metadata = {
        "model": MODEL_ID, "model_class": model.__class__.__name__, "config_class": config.__class__.__name__,
        "tokenizer_class": tokenizer.__class__.__name__, "model_type": config.model_type,
        "parameter_count": sum(parameter_.numel() for parameter_ in model.parameters()),
        "num_hidden_layers": config.num_hidden_layers, "hidden_size": config.hidden_size,
        "declared_torch_dtype": str(config.torch_dtype), "runtime_dtype": str(parameter.dtype), "runtime_device": str(parameter.device),
        "hidden_state_count": 27, "selected_layers": LAYERS, "prompt_format": "raw_plain_text_no_chat_template",
        "batch_size": 1, "min_token_count": min(token_counts), "max_token_count": max(token_counts),
        "gpu_memory_before_load_bytes": gpu_before, "gpu_memory_after_load_bytes": gpu_after_load,
        "gpu_memory_after_final_forward_bytes": torch.cuda.memory_allocated(0), "zero_variance_layers": zero_variance_layers,
    }
    save_json(metadata, output_dir / "model_metadata.json")
    depths = [float(row["normalized_depth"]) for row in layer_rows]
    line_plot(depths, [float(row["separation_score"]) for row in layer_rows], output_dir / "separation_by_depth.png", "Separation score", "EXP-013 Gemma Separation by Depth")
    line_plot(depths, [float(row["silhouette_score"]) for row in layer_rows], output_dir / "silhouette_by_depth.png", "Silhouette score", "EXP-013 Gemma Silhouette by Depth")
    line_plot(depths, [float(row["paraphrase_retention_score"]) for row in layer_rows], output_dir / "paraphrase_retention_by_depth.png", "Paraphrase retention score", "EXP-013 Gemma Paraphrase Retention by Depth")
    comparison_plot(qwen_rows, layer_rows, "separation_score", output_dir / "qwen_vs_gemma_separation.png", "Qwen vs Gemma Separation")
    comparison_plot(qwen_rows, layer_rows, "silhouette_score", output_dir / "qwen_vs_gemma_silhouette.png", "Qwen vs Gemma Silhouette")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
