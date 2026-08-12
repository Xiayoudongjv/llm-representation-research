"""EXP-015: fixed layer-validity pilot across cached Qwen and Gemma models.

The experiment is representation-level only. It uses raw plain-text prompts,
never generates text, and writes aggregate metrics only.
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", r"D:\AI_Cache\matplotlib")

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
from src.representation_metrics import (
    compute_silhouette,
    cosine_similarity_matrix,
    mean_between_group_similarity,
    mean_within_group_similarity,
    separation_score,
)
from src.steering import apply_static_steering, compute_group_centroids, cosine_to_centroids, nearest_centroid_labels


GROUPS = ["logic", "causality", "analogy", "definition"]
BETAS = [0.5, 0.75, 1.0]
MODEL_SPECS = {
    "Qwen/Qwen3-1.7B": {"layers": [8, 16, 28], "denominator": 28, "cache": Path(r"D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-1.7B\snapshots")},
    "google/gemma-3-1b-it": {"layers": [8, 16, 26], "denominator": 26, "cache": Path(r"D:\AI_Cache\huggingface\models--google--gemma-3-1b-it\snapshots")},
}
MATERIAL_ASSIGNMENT_RANGE = 0.20
MATERIAL_IVS_RANGE = 0.01


def parse_args() -> argparse.Namespace:
    """Parse only input and output locations; layers and betas are fixed."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prompts_path", default="experiments/exp003/prompts_controlled.json")
    parser.add_argument("--output_dir", default="results/exp015")
    return parser.parse_args()


def snapshot_path(model: str) -> Path:
    """Resolve exactly one local snapshot for a fixed model without networking."""
    candidates = sorted(path for path in MODEL_SPECS[model]["cache"].iterdir() if path.is_dir())
    if len(candidates) != 1:
        raise FileNotFoundError(f"Expected one local snapshot for {model}; found {len(candidates)}.")
    return candidates[0]


def variant_similarities(similarity: np.ndarray, prompts: list[dict]) -> tuple[float, float]:
    """Compute EXP-003's cross-variant and cross-group comparison means."""
    same_group_cross_variant = []
    for group in GROUPS:
        originals = [index for index, item in enumerate(prompts) if item["group"] == group and item["variant_type"] == "original_style"]
        paraphrases = [index for index, item in enumerate(prompts) if item["group"] == group and item["variant_type"] == "paraphrase"]
        same_group_cross_variant.extend(similarity[i, j] for i in originals for j in paraphrases)
    same_variant_cross_group = []
    for variant in ("original_style", "paraphrase"):
        indices = [index for index, item in enumerate(prompts) if item["variant_type"] == variant]
        same_variant_cross_group.extend(similarity[i, j] for position, i in enumerate(indices) for j in indices[position + 1:] if prompts[i]["group"] != prompts[j]["group"])
    return float(np.mean(same_group_cross_variant)), float(np.mean(same_variant_cross_group))


def safe_silhouette(matrix: np.ndarray, labels: list[str]) -> float:
    """Return NaN only for a degenerate silhouette input."""
    try:
        return compute_silhouette(matrix, labels)
    except ValueError:
        return float("nan")


def extract_model_layers(model_name: str, prompts: list[dict]) -> tuple[dict[int, np.ndarray], dict]:
    """Run one no-grad forward per prompt and retain only requested layer vectors in RAM."""
    spec = MODEL_SPECS[model_name]
    snapshot = snapshot_path(model_name)
    gpu_before = torch.cuda.memory_allocated(0)
    config = AutoConfig.from_pretrained(snapshot, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(snapshot, local_files_only=True, dtype=torch.float16, device_map="auto")
    model.eval()
    parameter = next(model.parameters())
    if parameter.device.type != "cuda":
        raise RuntimeError(f"Expected CUDA placement for {model_name}; got {parameter.device}.")
    gpu_after_load = torch.cuda.memory_allocated(0)
    representations = {layer: [] for layer in spec["layers"]}
    token_counts = []
    with torch.no_grad():
        for item in prompts:
            inputs = tokenizer(item["text"], return_tensors="pt")
            token_counts.append(int(inputs["input_ids"].shape[-1]))
            outputs = model(**{name: value.to(parameter.device) for name, value in inputs.items()}, output_hidden_states=True, return_dict=True)
            expected_states = spec["denominator"] + 1
            if len(outputs.hidden_states) != expected_states:
                raise ValueError(f"Expected {expected_states} hidden states for {model_name}; found {len(outputs.hidden_states)}.")
            for layer in spec["layers"]:
                representations[layer].append(tensor_to_numpy_float32(extract_last_token_hidden_state(outputs.hidden_states, layer)))
    metadata = {
        "model": model_name,
        "model_class": model.__class__.__name__,
        "config_class": config.__class__.__name__,
        "model_type": config.model_type,
        "hidden_size": config.hidden_size,
        "hidden_state_count": spec["denominator"] + 1,
        "runtime_dtype": str(parameter.dtype),
        "runtime_device": str(parameter.device),
        "gpu_memory_before_load_bytes": gpu_before,
        "gpu_memory_after_load_bytes": gpu_after_load,
        "gpu_memory_after_final_forward_bytes": torch.cuda.memory_allocated(0),
        "min_token_count": min(token_counts),
        "max_token_count": max(token_counts),
    }
    matrices = {layer: np.stack(rows).astype(np.float32) for layer, rows in representations.items()}
    del model
    torch.cuda.empty_cache()
    return matrices, metadata


def encoding_rows(model: str, matrices: dict[int, np.ndarray], prompts: list[dict]) -> list[dict]:
    """Compute unchanged EXP-003/EXP-013 geometry definitions for fixed layers."""
    labels = [item["group"] for item in prompts]
    denominator = MODEL_SPECS[model]["denominator"]
    rows = []
    for layer, matrix in matrices.items():
        similarity = cosine_similarity_matrix(matrix)
        within, _ = mean_within_group_similarity(similarity, labels)
        between = mean_between_group_similarity(similarity, labels)
        same_group, same_variant_cross_group = variant_similarities(similarity, prompts)
        rows.append({
            "model": model,
            "layer": layer,
            "normalized_depth": layer / denominator,
            "mean_within_group_similarity": within,
            "mean_between_group_similarity": between,
            "separation_score": separation_score(within, between),
            "silhouette_score": safe_silhouette(matrix, labels),
            "paraphrase_retention_score": same_group - same_variant_cross_group,
        })
    return rows


def layer_beta_rows(model: str, matrices: dict[int, np.ndarray], prompts: list[dict]) -> list[dict]:
    """Aggregate fixed centroid steering and RSM metrics over all ordered pairs."""
    labels = [item["group"] for item in prompts]
    denominator = MODEL_SPECS[model]["denominator"]
    rows = []
    for layer, matrix in matrices.items():
        centroids = compute_group_centroids(matrix, labels)
        records_by_beta = {beta: [] for beta in BETAS}
        for source, target in itertools.permutations(GROUPS, 2):
            source_matrix = matrix[[index for index, group in enumerate(labels) if group == source]]
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
                records_by_beta[beta].append({
                    "assignment": float(np.mean([label == target for label in nearest])),
                    "movement": float(np.mean(similarities[target]) - np.mean(similarities[source])),
                    "relative_perturbation": float(np.mean(abs(beta) * delta_norm / np.maximum(source_norms, 1e-12))),
                    "ivs": float(invariant["invariant_violation_score"]),
                    "rsm_pearson": float(invariant["rsm_pearson"]),
                })
        for beta, records in records_by_beta.items():
            assignment = float(np.mean([record["assignment"] for record in records]))
            perturbation = float(np.mean([record["relative_perturbation"] for record in records]))
            ivs = float(np.mean([record["ivs"] for record in records]))
            rows.append({
                "model": model,
                "layer": layer,
                "normalized_depth": layer / denominator,
                "beta": beta,
                "mean_target_assignment_rate": assignment,
                "mean_target_minus_source_similarity": float(np.mean([record["movement"] for record in records])),
                "mean_relative_perturbation_norm": perturbation,
                "pairs_assignment_ge_0_5": sum(record["assignment"] >= 0.5 for record in records),
                "pairs_assignment_eq_1": sum(record["assignment"] >= 1.0 for record in records),
                "mean_ivs": ivs,
                "mean_rsm_pearson": float(np.mean([record["rsm_pearson"] for record in records])),
                "transition_efficiency": assignment / (perturbation + 1e-8),
                "validity_score": assignment - ivs - 0.1 * perturbation,
            })
    return rows


def select_roles(model: str, encoding: list[dict], layer_beta: list[dict]) -> tuple[dict, list[dict]]:
    """Apply all predeclared role definitions before examining any role label."""
    model_encoding = [row for row in encoding if row["model"] == model]
    model_beta = [row for row in layer_beta if row["model"] == model]
    encoding = max(model_encoding, key=lambda row: (row["separation_score"], row["paraphrase_retention_score"], row["silhouette_score"]))
    beta_075 = [row for row in model_beta if row["beta"] == 0.75]
    control = max(beta_075, key=lambda row: (row["mean_target_assignment_rate"], row["mean_target_minus_source_similarity"]))
    eligible = [row for row in model_beta if row["mean_target_assignment_rate"] >= 0.80]
    fallback = not eligible
    if eligible:
        safe = min(eligible, key=lambda row: (row["mean_ivs"], -row["mean_target_assignment_rate"], row["mean_relative_perturbation_norm"], row["layer"]))
    else:
        safe = max(model_beta, key=lambda row: (row["mean_target_assignment_rate"] - row["mean_ivs"], -row["mean_relative_perturbation_norm"], -row["layer"]))
    efficiency = max(model_beta, key=lambda row: (row["transition_efficiency"], row["validity_score"]))
    assignment_range = max(row["mean_target_assignment_rate"] for row in beta_075) - min(row["mean_target_assignment_rate"] for row in beta_075)
    ivs_range = max(row["mean_ivs"] for row in beta_075) - min(row["mean_ivs"] for row in beta_075)
    role_summary = {
        "model": model,
        "encoding_layer": encoding["layer"],
        "encoding_separation": encoding["separation_score"],
        "control_layer_beta_075": control["layer"],
        "control_assignment_beta_075": control["mean_target_assignment_rate"],
        "safe_control_layer": safe["layer"],
        "safe_control_beta": safe["beta"],
        "safe_control_assignment": safe["mean_target_assignment_rate"],
        "safe_control_ivs": safe["mean_ivs"],
        "safe_control_relative_perturbation": safe["mean_relative_perturbation_norm"],
        "safe_control_used_fallback": fallback,
        "best_efficiency_layer_beta": f"layer_{efficiency['layer']}_beta_{efficiency['beta']}",
        "encoding_equals_control": encoding["layer"] == control["layer"],
        "encoding_equals_safe_control": encoding["layer"] == safe["layer"],
        "control_equals_safe_control": control["layer"] == safe["layer"],
        "beta_075_assignment_range": assignment_range,
        "beta_075_ivs_range": ivs_range,
        "material_layer_effect_predeclared": assignment_range >= MATERIAL_ASSIGNMENT_RANGE or ivs_range >= MATERIAL_IVS_RANGE,
    }
    layer_summary = []
    for geometry in model_encoding:
        beta_row = next(row for row in beta_075 if row["layer"] == geometry["layer"])
        layer_summary.append({
            "model": model,
            "layer": geometry["layer"],
            "normalized_depth": geometry["normalized_depth"],
            "separation_score": geometry["separation_score"],
            "silhouette_score": geometry["silhouette_score"],
            "paraphrase_retention_score": geometry["paraphrase_retention_score"],
            "assignment_beta_075": beta_row["mean_target_assignment_rate"],
            "ivs_beta_075": beta_row["mean_ivs"],
            "relative_perturbation_beta_075": beta_row["mean_relative_perturbation_norm"],
            "is_encoding_layer": geometry["layer"] == encoding["layer"],
            "is_control_layer_beta_075": geometry["layer"] == control["layer"],
            "is_safe_control_layer": geometry["layer"] == safe["layer"],
        })
    return role_summary, layer_summary


def save_model_plot(model: str, rows: list[dict], output_path: Path) -> None:
    """Plot fixed beta curves for assignment and IVS at each tested layer."""
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    for layer in MODEL_SPECS[model]["layers"]:
        selected = [row for row in rows if row["model"] == model and row["layer"] == layer]
        axes[0].plot(BETAS, [row["mean_target_assignment_rate"] for row in selected], marker="o", label=f"layer {layer}")
        axes[1].plot(BETAS, [row["mean_ivs"] for row in selected], marker="o", label=f"layer {layer}")
    axes[0].set(title=f"{model} assignment", xlabel="Beta", ylabel="Mean target assignment")
    axes[1].set(title=f"{model} IVS", xlabel="Beta", ylabel="Mean IVS")
    axes[1].legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def save_scatter(rows: list[dict], y_field: str, ylabel: str, output_path: Path) -> None:
    """Save an exploratory three-layer-per-model geometry comparison."""
    figure, axis = plt.subplots(figsize=(7, 5))
    for model in MODEL_SPECS:
        selected = [row for row in rows if row["model"] == model]
        axis.scatter([row["separation_score"] for row in selected], [row[y_field] for row in selected], label=model)
        for row in selected:
            axis.annotate(f"{model.split('/')[-1]} L{row['layer']}", (row["separation_score"], row[y_field]))
    axis.set_xlabel("Separation score")
    axis.set_ylabel(ylabel)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def main() -> None:
    """Run all fixed layers and betas for both models without saving raw states."""
    args = parse_args()
    prompts = load_json(ROOT / args.prompts_path)
    if len(prompts) != 24 or {item["group"] for item in prompts} != set(GROUPS):
        raise ValueError("Expected the unchanged 24-prompt EXP-003 controlled dataset.")
    output_dir = ensure_dir(ROOT / args.output_dir)
    all_encoding, all_beta, model_metadata = [], [], {}
    for model in MODEL_SPECS:
        matrices, metadata = extract_model_layers(model, prompts)
        model_metadata[model] = metadata
        all_encoding.extend(encoding_rows(model, matrices, prompts))
        all_beta.extend(layer_beta_rows(model, matrices, prompts))
    role_summaries, layer_summaries = [], []
    for model in MODEL_SPECS:
        role, layer_summary = select_roles(model, all_encoding, all_beta)
        role_summaries.append(role)
        layer_summaries.extend(layer_summary)
    differentiated = [not (row["encoding_equals_control"] and row["encoding_equals_safe_control"] and row["control_equals_safe_control"]) or row["material_layer_effect_predeclared"] for row in role_summaries]
    support = True if all(differentiated) else ("mixed" if any(differentiated) else False)
    if support is True or support == "mixed":
        gate = "EXPAND_LAYER_VALIDITY_STUDY"
        reason = "At least one model showed predeclared role separation or a material beta-0.75 layer effect."
    else:
        gate = "PROCEED_TO_GENERATION_INTERVENTION"
        reason = "No tested model showed predeclared role separation or a material beta-0.75 layer effect."
    summary = {
        "models": role_summaries,
        "model_metadata": model_metadata,
        "tested_betas": BETAS,
        "predeclared_materiality": {"assignment_range_at_beta_075": MATERIAL_ASSIGNMENT_RANGE, "ivs_range_at_beta_075": MATERIAL_IVS_RANGE},
        "pilot_supports_layer_role_separation": support,
        "reason": reason,
        "gate_decision": gate,
        "warning": "This three-layer, three-beta representation-level pilot does not identify causal functional layer roles or generation-time effects.",
    }
    encoding_fields = list(all_encoding[0])
    beta_fields = list(all_beta[0])
    layer_summary_fields = list(layer_summaries[0])
    write_csv(output_dir / "encoding_metrics.csv", encoding_fields, all_encoding)
    write_csv(output_dir / "layer_beta_metrics.csv", beta_fields, all_beta)
    write_csv(output_dir / "model_layer_summary.csv", layer_summary_fields, layer_summaries)
    save_json(summary, output_dir / "layer_validity_summary.json")
    save_model_plot("Qwen/Qwen3-1.7B", all_beta, output_dir / "qwen_layer_validity.png")
    save_model_plot("google/gemma-3-1b-it", all_beta, output_dir / "gemma_layer_validity.png")
    save_scatter(layer_summaries, "assignment_beta_075", "Mean target assignment at beta 0.75", output_dir / "geometry_vs_assignment.png")
    save_scatter(layer_summaries, "ivs_beta_075", "Mean IVS at beta 0.75", output_dir / "geometry_vs_ivs.png")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
