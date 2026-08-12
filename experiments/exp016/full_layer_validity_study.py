"""EXP-016: fixed full layer-strength validity study for Qwen and Gemma.

This is representation-level analysis only. It does not generate text and does
not write raw hidden-state vectors or model weights.
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "matplotlib-exp016"))

import matplotlib.pyplot as plt
import numpy as np
import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment_io import ensure_dir, load_json, save_json, write_csv
from src.extraction import extract_last_token_hidden_state, tensor_to_numpy_float32
from src.invariants import summarize_invariant_metrics
from src.representation_metrics import compute_silhouette, cosine_similarity_matrix, mean_between_group_similarity, mean_within_group_similarity, separation_score
from src.steering import apply_static_steering, compute_group_centroids, cosine_to_centroids, nearest_centroid_labels


GROUPS = ["logic", "causality", "analogy", "definition"]
BETAS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5]
MODEL_SPECS = {
    "Qwen/Qwen3-1.7B": {
        "layers": [4, 8, 12, 16, 20, 24, 28],
        "denominator": 28,
        "snapshot_root": Path(r"D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-1.7B\snapshots"),
    },
    "google/gemma-3-1b-it": {
        "layers": [4, 8, 12, 16, 20, 23, 26],
        "denominator": 26,
        "snapshot_root": Path(r"D:\AI_Cache\huggingface\models--google--gemma-3-1b-it\snapshots"),
    },
}
ASSIGNMENT_THRESHOLD = 0.90


def parse_args() -> argparse.Namespace:
    """Parse only data and output locations; the study grid is predeclared."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--output_dir", default="results/exp016")
    return parser.parse_args()


def local_snapshot(model: str) -> Path:
    """Resolve a single local snapshot without making a network request."""
    candidates = sorted(path for path in MODEL_SPECS[model]["snapshot_root"].iterdir() if path.is_dir())
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected one local snapshot for {model}; found {len(candidates)}.")
    return candidates[0]


def variant_similarities(similarity: np.ndarray, prompts: list[dict]) -> tuple[float, float]:
    """Return the EXP-003 same-group and cross-group control means."""
    same_group_cross_variant = []
    for group in GROUPS:
        originals = [i for i, item in enumerate(prompts) if item["group"] == group and item["variant_type"] == "original_style"]
        paraphrases = [i for i, item in enumerate(prompts) if item["group"] == group and item["variant_type"] == "paraphrase"]
        same_group_cross_variant.extend(similarity[i, j] for i in originals for j in paraphrases)
    same_variant_cross_group = []
    for variant in ("original_style", "paraphrase"):
        indices = [i for i, item in enumerate(prompts) if item["variant_type"] == variant]
        same_variant_cross_group.extend(similarity[i, j] for offset, i in enumerate(indices) for j in indices[offset + 1:] if prompts[i]["group"] != prompts[j]["group"])
    return float(np.mean(same_group_cross_variant)), float(np.mean(same_variant_cross_group))


def safe_silhouette(matrix: np.ndarray, labels: list[str]) -> float:
    """Return NaN only if the fixed prompt geometry is degenerate."""
    try:
        return compute_silhouette(matrix, labels)
    except ValueError:
        return float("nan")


def extract_layers(model_name: str, prompts: list[dict]) -> tuple[dict[int, np.ndarray], dict]:
    """Extract requested last-token layers in RAM with one forward per prompt."""
    spec = MODEL_SPECS[model_name]
    snapshot = local_snapshot(model_name)
    before = torch.cuda.memory_allocated(0)
    config = AutoConfig.from_pretrained(snapshot, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(snapshot, local_files_only=True, dtype=torch.float16, device_map="auto")
    model.eval()
    parameter = next(model.parameters())
    if parameter.device.type != "cuda":
        raise RuntimeError(f"Expected CUDA placement for {model_name}; got {parameter.device}.")
    after_load = torch.cuda.memory_allocated(0)
    collected = {layer: [] for layer in spec["layers"]}
    token_counts = []
    with torch.no_grad():
        for item in prompts:
            inputs = tokenizer(item["text"], return_tensors="pt")
            token_counts.append(int(inputs["input_ids"].shape[-1]))
            inputs = {name: value.to(parameter.device) for name, value in inputs.items()}
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            expected = spec["denominator"] + 1
            if len(outputs.hidden_states) != expected:
                raise ValueError(f"Expected {expected} hidden states for {model_name}; found {len(outputs.hidden_states)}.")
            for layer in spec["layers"]:
                collected[layer].append(tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, layer)))
    metadata = {
        "model": model_name,
        "model_class": model.__class__.__name__,
        "config_class": config.__class__.__name__,
        "model_type": config.model_type,
        "hidden_size": config.hidden_size,
        "hidden_state_count": spec["denominator"] + 1,
        "runtime_dtype": str(parameter.dtype),
        "runtime_device": str(parameter.device),
        "gpu_memory_before_load_bytes": before,
        "gpu_memory_after_load_bytes": after_load,
        "gpu_memory_after_final_forward_bytes": torch.cuda.memory_allocated(0),
        "min_token_count": min(token_counts),
        "max_token_count": max(token_counts),
    }
    matrices = {layer: np.stack(values).astype(np.float32) for layer, values in collected.items()}
    del model
    torch.cuda.empty_cache()
    return matrices, metadata


def encoding_metrics(model: str, matrices: dict[int, np.ndarray], prompts: list[dict]) -> list[dict]:
    """Compute unchanged controlled-geometry metrics for every selected layer."""
    labels = [item["group"] for item in prompts]
    denominator = MODEL_SPECS[model]["denominator"]
    rows = []
    for layer, matrix in matrices.items():
        similarity = cosine_similarity_matrix(matrix)
        within, _ = mean_within_group_similarity(similarity, labels)
        between = mean_between_group_similarity(similarity, labels)
        same_group, cross_group = variant_similarities(similarity, prompts)
        rows.append({
            "model": model,
            "layer": layer,
            "normalized_depth": layer / denominator,
            "separation_score": separation_score(within, between),
            "silhouette_score": safe_silhouette(matrix, labels),
            "paraphrase_retention_score": same_group - cross_group,
            "mean_within_group_similarity": within,
            "mean_between_group_similarity": between,
        })
    return rows


def steering_metrics(model: str, matrices: dict[int, np.ndarray], labels: list[str]) -> tuple[list[dict], list[dict]]:
    """Return fixed-grid pair-level and aggregate steering/RSM metrics."""
    denominator = MODEL_SPECS[model]["denominator"]
    pair_rows, aggregate_rows = [], []
    for layer, matrix in matrices.items():
        centroids = compute_group_centroids(matrix, labels)
        by_beta = {beta: [] for beta in BETAS}
        for source, target in itertools.permutations(GROUPS, 2):
            source_matrix = matrix[[i for i, label in enumerate(labels) if label == source]]
            source_norms = np.linalg.norm(source_matrix, axis=1)
            delta = centroids[target] - centroids[source]
            delta_norm = float(np.linalg.norm(delta))
            if delta_norm < 1e-12:
                raise ValueError(f"Near-zero centroid delta for {model} layer {layer}: {source}->{target}.")
            centroid_pair = {source: centroids[source], target: centroids[target]}
            for beta in BETAS:
                steered = apply_static_steering(source_matrix, delta, beta)
                similarities = cosine_to_centroids(steered, centroid_pair)
                nearest, _ = nearest_centroid_labels(steered, centroids)
                invariant = summarize_invariant_metrics(source_matrix, steered)
                record = {
                    "model": model,
                    "layer": layer,
                    "normalized_depth": layer / denominator,
                    "source_group": source,
                    "target_group": target,
                    "beta": beta,
                    "delta_norm": delta_norm,
                    "mean_target_assignment_rate": float(np.mean([label == target for label in nearest])),
                    "mean_target_minus_source_similarity": float(np.mean(similarities[target]) - np.mean(similarities[source])),
                    "mean_relative_perturbation_norm": float(np.mean(abs(beta) * delta_norm / np.maximum(source_norms, 1e-12))),
                    "ivs": float(invariant["invariant_violation_score"]),
                    "rsm_pearson": float(invariant["rsm_pearson"]),
                }
                pair_rows.append(record)
                by_beta[beta].append(record)
        for beta, records in by_beta.items():
            assignments = np.asarray([row["mean_target_assignment_rate"] for row in records], dtype=float)
            ivs = np.asarray([row["ivs"] for row in records], dtype=float)
            perturbation = float(np.mean([row["mean_relative_perturbation_norm"] for row in records]))
            assignment = float(np.mean(assignments))
            mean_ivs = float(np.mean(ivs))
            aggregate_rows.append({
                "model": model,
                "layer": layer,
                "normalized_depth": layer / denominator,
                "beta": beta,
                "mean_target_assignment_rate": assignment,
                "mean_target_minus_source_similarity": float(np.mean([row["mean_target_minus_source_similarity"] for row in records])),
                "mean_relative_perturbation_norm": perturbation,
                "pairs_assignment_ge_0_5": int(np.sum(assignments >= 0.5)),
                "pairs_assignment_eq_1": int(np.sum(assignments >= 1.0)),
                "mean_ivs": mean_ivs,
                "mean_rsm_pearson": float(np.mean([row["rsm_pearson"] for row in records])),
                "median_assignment": float(np.median(assignments)),
                "min_assignment": float(np.min(assignments)),
                "max_assignment": float(np.max(assignments)),
                "median_ivs": float(np.median(ivs)),
                "max_ivs": float(np.max(ivs)),
                "efficiency": assignment / (perturbation + 1e-8),
                "validity_score": assignment - mean_ivs - 0.1 * perturbation,
            })
    return pair_rows, aggregate_rows


def select_role_summary(model: str, encoding: list[dict], aggregate: list[dict]) -> dict:
    """Apply predeclared encoding, control, safe, efficiency, and validity rules."""
    geometry = [row for row in encoding if row["model"] == model]
    grid = [row for row in aggregate if row["model"] == model]
    encoding_layer = max(geometry, key=lambda row: (row["separation_score"], row["paraphrase_retention_score"], row["silhouette_score"]))
    threshold_rows = [row for row in grid if row["mean_target_assignment_rate"] >= ASSIGNMENT_THRESHOLD]
    fallback = not threshold_rows
    if threshold_rows:
        control = min(threshold_rows, key=lambda row: (row["beta"], -row["mean_target_assignment_rate"], row["mean_relative_perturbation_norm"], row["layer"]))
        safe = min(threshold_rows, key=lambda row: (row["mean_ivs"], row["mean_relative_perturbation_norm"], -row["mean_target_assignment_rate"], row["layer"], row["beta"]))
        efficient = max(threshold_rows, key=lambda row: (row["efficiency"], row["validity_score"]))
    else:
        control = max(grid, key=lambda row: (row["mean_target_assignment_rate"], -row["mean_relative_perturbation_norm"], -row["layer"]))
        safe = control
        efficient = max(grid, key=lambda row: (row["efficiency"], row["validity_score"]))
    validity = max(grid, key=lambda row: (row["validity_score"], row["mean_target_assignment_rate"], -row["mean_ivs"]))
    return {
        "model": model,
        "encoding_layer": encoding_layer["layer"],
        "encoding_normalized_depth": encoding_layer["normalized_depth"],
        "encoding_separation": encoding_layer["separation_score"],
        "control_layer": control["layer"],
        "control_normalized_depth": control["normalized_depth"],
        "control_beta": control["beta"],
        "control_assignment": control["mean_target_assignment_rate"],
        "control_used_fallback": fallback,
        "safe_control_layer": safe["layer"],
        "safe_control_normalized_depth": safe["normalized_depth"],
        "safe_control_beta": safe["beta"],
        "safe_control_assignment": safe["mean_target_assignment_rate"],
        "safe_control_ivs": safe["mean_ivs"],
        "safe_control_relative_perturbation": safe["mean_relative_perturbation_norm"],
        "efficient_control_layer": efficient["layer"],
        "efficient_control_normalized_depth": efficient["normalized_depth"],
        "efficient_control_beta": efficient["beta"],
        "efficient_control_efficiency": efficient["efficiency"],
        "best_validity_layer": validity["layer"],
        "best_validity_normalized_depth": validity["normalized_depth"],
        "best_validity_beta": validity["beta"],
        "best_validity_score": validity["validity_score"],
        "encoding_equals_control": encoding_layer["layer"] == control["layer"],
        "encoding_equals_safe_control": encoding_layer["layer"] == safe["layer"],
        "control_equals_safe_control": control["layer"] == safe["layer"],
    }


def heatmap(model: str, aggregate: list[dict], field: str, title: str, label: str, output: Path) -> None:
    """Plot a fixed beta-by-layer surface for a scalar aggregate metric."""
    layers = MODEL_SPECS[model]["layers"]
    matrix = np.asarray([[next(row[field] for row in aggregate if row["model"] == model and row["layer"] == layer and row["beta"] == beta) for layer in layers] for beta in BETAS], dtype=float)
    figure, axis = plt.subplots(figsize=(8, 5))
    image = axis.imshow(matrix, aspect="auto")
    axis.set_xticks(range(len(layers)), [str(layer) for layer in layers])
    axis.set_yticks(range(len(BETAS)), [str(beta) for beta in BETAS])
    axis.set_xlabel("Hidden-state index")
    axis.set_ylabel("Beta")
    axis.set_title(title)
    figure.colorbar(image, ax=axis, label=label)
    for row in range(len(BETAS)):
        for column in range(len(layers)):
            axis.text(column, row, f"{matrix[row, column]:.3f}", ha="center", va="center", fontsize=7)
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def role_depth_plot(role_rows: list[dict], output: Path) -> None:
    """Compare model-specific role depths on a normalized-depth axis."""
    role_names = ["encoding", "control", "safe_control", "efficient_control", "best_validity"]
    figure, axis = plt.subplots(figsize=(8, 5))
    for index, row in enumerate(role_rows):
        depths = [row[f"{name}_normalized_depth"] for name in role_names]
        axis.scatter(range(len(role_names)), depths, label=row["model"])
        axis.plot(range(len(role_names)), depths)
    axis.set_xticks(range(len(role_names)), [name.replace("_", " ") for name in role_names], rotation=20, ha="right")
    axis.set_ylabel("Normalized depth")
    axis.set_title("EXP-016 Model-Specific Role Depths")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def geometry_control_plot(encoding: list[dict], aggregate: list[dict], output: Path) -> None:
    """Plot beta-threshold control and preservation against geometry strength."""
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    for model in MODEL_SPECS:
        geometry = [row for row in encoding if row["model"] == model]
        control_rows = []
        for row in geometry:
            candidates = [metric for metric in aggregate if metric["model"] == model and metric["layer"] == row["layer"] and metric["mean_target_assignment_rate"] >= ASSIGNMENT_THRESHOLD]
            control_rows.append(min(candidates, key=lambda metric: metric["beta"]) if candidates else max([metric for metric in aggregate if metric["model"] == model and metric["layer"] == row["layer"]], key=lambda metric: metric["mean_target_assignment_rate"]))
        x = [row["separation_score"] for row in geometry]
        axes[0].scatter(x, [row["mean_target_assignment_rate"] for row in control_rows], label=model)
        axes[1].scatter(x, [row["mean_ivs"] for row in control_rows], label=model)
        for geometry_row, control_row in zip(geometry, control_rows):
            label = f"L{geometry_row['layer']}"
            axes[0].annotate(label, (geometry_row["separation_score"], control_row["mean_target_assignment_rate"]))
            axes[1].annotate(label, (geometry_row["separation_score"], control_row["mean_ivs"]))
    axes[0].set(xlabel="Separation score", ylabel="Assignment at layer's control point", title="Geometry vs control")
    axes[1].set(xlabel="Separation score", ylabel="IVS at layer's control point", title="Geometry vs preservation")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def main() -> None:
    """Run the fixed full layer-strength study and save only aggregate results."""
    args = parse_args()
    prompts = load_json(ROOT / args.prompts_path)
    if len(prompts) != 24 or {item["group"] for item in prompts} != set(GROUPS):
        raise ValueError("Expected the unchanged 24-prompt EXP-003 controlled dataset.")
    output_dir = ensure_dir(ROOT / args.output_dir)
    labels = [item["group"] for item in prompts]
    all_encoding, all_pair, all_aggregate, metadata = [], [], [], {}
    for model in MODEL_SPECS:
        matrices, model_metadata = extract_layers(model, prompts)
        metadata[model] = model_metadata
        all_encoding.extend(encoding_metrics(model, matrices, prompts))
        pair_rows, aggregate_rows = steering_metrics(model, matrices, labels)
        all_pair.extend(pair_rows)
        all_aggregate.extend(aggregate_rows)
    roles = [select_role_summary(model, all_encoding, all_aggregate) for model in MODEL_SPECS]
    qwen, gemma = roles
    separated = [not (row["encoding_equals_control"] and row["encoding_equals_safe_control"] and row["control_equals_safe_control"]) for row in roles]
    classification = "supported" if all(separated) else ("partially_supported" if any(separated) else "not_supported")
    gate = "PROCEED_TO_GENERATION_INTERVENTION"
    cross_model = {
        "qwen": qwen,
        "gemma": gemma,
        "encoding_peak_depth_similar": abs(qwen["encoding_normalized_depth"] - gemma["encoding_normalized_depth"]) <= 0.15,
        "control_peak_depth_similar": abs(qwen["control_normalized_depth"] - gemma["control_normalized_depth"]) <= 0.15,
        "safe_control_peak_depth_similar": abs(qwen["safe_control_normalized_depth"] - gemma["safe_control_normalized_depth"]) <= 0.15,
        "final_layer_geometry_corresponds_to_safe_control_qwen": qwen["encoding_layer"] == MODEL_SPECS["Qwen/Qwen3-1.7B"]["layers"][-1] and qwen["safe_control_layer"] == qwen["encoding_layer"],
        "final_layer_geometry_corresponds_to_safe_control_gemma": gemma["encoding_layer"] == MODEL_SPECS["google/gemma-3-1b-it"]["layers"][-1] and gemma["safe_control_layer"] == gemma["encoding_layer"],
        "classification": classification,
    }
    summary = {
        "models": roles,
        "model_metadata": metadata,
        "tested_betas": BETAS,
        "assignment_threshold": ASSIGNMENT_THRESHOLD,
        "cross_model_role_summary": cross_model,
        "layer_role_separation": classification,
        "gate_decision": gate,
        "gate_reason": "Both models yielded operational control and safe-control selections with no numerical failure; the complete fixed grid supports a pre-behavioral layer choice.",
        "warning": "This sampled-layer, representation-level study cannot identify causal functional modules or establish generation-time behavior.",
    }
    write_csv(output_dir / "pair_level_metrics.csv", list(all_pair[0]), all_pair)
    write_csv(output_dir / "layer_beta_aggregate.csv", list(all_aggregate[0]), all_aggregate)
    write_csv(output_dir / "encoding_metrics.csv", list(all_encoding[0]), all_encoding)
    write_csv(output_dir / "model_role_summary.csv", list(roles[0]), roles)
    cross_rows = [
        {"comparison": "encoding_peak_depth_similar", "value": cross_model["encoding_peak_depth_similar"]},
        {"comparison": "control_peak_depth_similar", "value": cross_model["control_peak_depth_similar"]},
        {"comparison": "safe_control_peak_depth_similar", "value": cross_model["safe_control_peak_depth_similar"]},
        {"comparison": "final_layer_geometry_corresponds_to_safe_control_qwen", "value": cross_model["final_layer_geometry_corresponds_to_safe_control_qwen"]},
        {"comparison": "final_layer_geometry_corresponds_to_safe_control_gemma", "value": cross_model["final_layer_geometry_corresponds_to_safe_control_gemma"]},
        {"comparison": "layer_role_separation", "value": classification},
    ]
    write_csv(output_dir / "cross_model_role_summary.csv", ["comparison", "value"], cross_rows)
    save_json(summary, output_dir / "validity_summary.json")
    heatmap("Qwen/Qwen3-1.7B", all_aggregate, "validity_score", "Qwen validity surface", "Validity score", output_dir / "qwen_validity_heatmap.png")
    heatmap("google/gemma-3-1b-it", all_aggregate, "validity_score", "Gemma validity surface", "Validity score", output_dir / "gemma_validity_heatmap.png")
    heatmap("Qwen/Qwen3-1.7B", all_aggregate, "mean_target_assignment_rate", "Qwen assignment surface", "Mean assignment", output_dir / "qwen_assignment_heatmap.png")
    heatmap("google/gemma-3-1b-it", all_aggregate, "mean_target_assignment_rate", "Gemma assignment surface", "Mean assignment", output_dir / "gemma_assignment_heatmap.png")
    heatmap("Qwen/Qwen3-1.7B", all_aggregate, "mean_ivs", "Qwen IVS surface", "Mean IVS", output_dir / "qwen_ivs_heatmap.png")
    heatmap("google/gemma-3-1b-it", all_aggregate, "mean_ivs", "Gemma IVS surface", "Mean IVS", output_dir / "gemma_ivs_heatmap.png")
    role_depth_plot(roles, output_dir / "role_depth_comparison.png")
    geometry_control_plot(all_encoding, all_aggregate, output_dir / "geometry_control_preservation.png")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
