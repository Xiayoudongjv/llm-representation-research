"""Generate Paper A figures, tables, facts, and data from frozen authorities.

This module is deliberately a projection layer: it validates the existing
Paper A registers, reads registered result matrices, and performs only
presentation transformations. It never loads a model or computes a statistic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
CANONICAL = ROOT / "experiments/paper_a/canonical"
SSOT_PATH = CANONICAL / "paper_a_scientific_results.json"
CLAIMS_PATH = CANONICAL / "paper_a_claim_register.json"
DEFAULT_OUTPUT = ROOT / "experiments/paper_a/paper_assets"

MODEL_ORDER = ["Qwen3-1.7B", "OLMo-2-1B", "Meta-Llama-3.2-1B-Instruct"]
MATRIX_MODEL_BINDINGS = {
    "Qwen3-1.7B": ("EXP-026", "Q", "model_profiles.Q.matrices"),
    "OLMo-2-1B": ("EXP-026", "O", "model_profiles.O.matrices"),
    "Meta-Llama-3.2-1B-Instruct": ("EXP-027", "Llama", "profile_archive"),
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_authorities() -> tuple[dict[str, Any], dict[str, Any]]:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from experiments.paper_a.canonical.validate_paper_a_canonical_register import main as validate_register

    validate_register()
    ssot = read_json(SSOT_PATH)
    for experiment, item in ssot["canonical_sources"].items():
        path = ROOT / item["path"]
        assert path.is_file(), f"missing canonical source: {experiment}"
        assert sha256(path) == item["sha256"], f"canonical source hash mismatch: {experiment}"
    return ssot, read_json(CLAIMS_PATH)


def source(ssot: dict[str, Any], experiment: str) -> dict[str, str]:
    item = ssot["canonical_sources"][experiment]
    return {"experiment": experiment, "canonical_path": item["path"], "canonical_sha256": item["sha256"]}


def field(data: dict[str, Any], path: str) -> Any:
    value: Any = data
    for part in path.split("."):
        value = value[part]
    return value


def profiled_value(profile: dict[str, Any], key: str) -> Any:
    item = profile[key]
    return item


def build_framework() -> dict[str, Any]:
    return {
        "figure_id": "FIGURE-01",
        "scientific_role": "SCHEMATIC_MEASUREMENT_FRAMEWORK",
        "labels": ["C0", "D", "Ccal", "R"],
        "definitions": {
            "C0": "direct source-readout reuse",
            "D": "direct-transfer degradation",
            "Ccal": "restricted FIT-only calibration",
            "R": "restricted recoverability",
        },
        "presentation_transformations": {"numeric_transformation": False},
    }


def build_profile_data(ssot: dict[str, Any]) -> dict[str, Any]:
    return {
        "figure_id": "FIGURE-02",
        "scientific_role": "CONFIRMATORY_THREE_MODEL_OPERATIONAL_PROFILE",
        "model_order": MODEL_ORDER,
        "source_assets": {name: source(ssot, "EXP-026" if name != MODEL_ORDER[2] else "EXP-027") for name in MODEL_ORDER},
        "profiles": {name: ssot["core_profiles"][name] for name in MODEL_ORDER},
        "labels": {
            "distance": "distance-related degradation statistic",
            "sdi": "SDI",
            "recovery": "restricted LOW-D recovery",
        },
        "presentation_transformations": {
            "distance_scale": "raw canonical statistic",
            "sdi_scale": "raw canonical statistic",
            "recovery_scale": "raw canonical statistic",
            "shared_y_axis": False,
        },
    }


def load_result(ssot: dict[str, Any], experiment: str) -> tuple[dict[str, Any], dict[str, str]]:
    src = source(ssot, experiment)
    return read_json(ROOT / src["canonical_path"]), src


def build_matrix_data(ssot: dict[str, Any]) -> dict[str, Any]:
    matrices: dict[str, Any] = {}
    for model in MODEL_ORDER:
        experiment, model_key, base_path = MATRIX_MODEL_BINDINGS[model]
        result, src = load_result(ssot, experiment)
        if experiment == "EXP-026":
            bundle = result["model_profiles"][model_key]["matrices"]
            field_prefix = f"{base_path}"
        else:
            bundle = result["profile_archive"]
            field_prefix = base_path
        matrices[model] = {}
        for metric in ("c0_eval", "d_eval", "r_eval"):
            matrix = bundle[metric]
            values = matrix["values"] if isinstance(matrix, dict) else matrix
            shape = matrix.get("shape") if isinstance(matrix, dict) else [len(values), len(values), len(values[0][0])]
            matrices[model][metric] = {
                "source_asset": src,
                "source_field_path": f"{field_prefix}.{metric}.values" if isinstance(matrix, dict) else f"{field_prefix}.{metric}",
                "shape": shape,
                "values": values,
            }
    return {
        "figure_id": "FIGURE-03",
        "scientific_role": "CONFIRMATORY_SOURCE_TARGET_OPERATIONAL_MATRICES",
        "model_order": MODEL_ORDER,
        "metric_order": ["c0_eval", "d_eval", "r_eval"],
        "axis": {"row": "source readout/scaler layer", "column": "target representation layer"},
        "matrices": matrices,
        "presentation_transformations": {
            "matrix_transposed_for_display": False,
            "matrix_resampled": False,
            "condition_aggregation": "none; all ten frozen condition slices retained",
        },
    }


def build_directionality_data(ssot: dict[str, Any]) -> dict[str, Any]:
    return {
        "figure_id": "FIGURE-04",
        "scientific_role": "EXPLORATORY_SECONDARY_MAIN_TEXT",
        "status_label": "POST-HOC EXPLORATORY",
        "source_asset": source(ssot, "DIRECTIONALITY_CLOSURE"),
        "model_order": ["Qwen", "OLMo", "Llama"],
        "values": {name: ssot["directionality"]["models"][name] for name in ["Qwen", "OLMo", "Llama"]},
        "available_display": ["mean_abs_A_C", "signed_shallow_deep_bias"],
        "unavailable_without_new_analysis": ["A_C_heatmap", "new_p_values", "new_confidence_intervals"],
        "presentation_transformations": {"new_inference": False, "significance_stars": False},
    }


def build_heterogeneity_data(ssot: dict[str, Any]) -> dict[str, Any]:
    return {
        "figure_id": "FIGURE-05",
        "scientific_role": "SUPPLEMENT_REGISTERED_NEGATIVE_AND_HETEROGENEITY",
        "source_assets": {name: source(ssot, name) for name in ["EXP-023", "EXP-024", "EXP-025"]},
        "values": {
            "EXP-023": ssot["split_heterogeneity"]["EXP-023"],
            "EXP-024": ssot["registered_negative_results"]["EXP-024_predictor"],
            "EXP-025": {
                "predictor": ssot["registered_negative_results"]["EXP-025_predictor"],
                "D": ssot["registered_negative_results"]["EXP-025_D"],
                "G": ssot["registered_negative_results"]["EXP-025_G"],
            },
        },
        "presentation_transformations": {"new_statistic": False, "new_inference": False},
    }


def build_tables(ssot: dict[str, Any], claims: dict[str, Any]) -> dict[str, Any]:
    profile_rows = []
    for name in MODEL_ORDER:
        profile = ssot["core_profiles"][name]
        profile_rows.append({
            "model": name,
            "matrix_shape": profile["matrix_shape"],
            "distance_statistic": profile["distance_related_degradation"]["statistic"],
            "distance_classification": profile["distance_related_degradation"]["support"],
            "distance_ci": profile["distance_related_degradation"]["confidence_interval"],
            "sdi": profile["sdi"]["statistic"],
            "sdi_classification": profile["sdi"]["classification"],
            "sdi_ci": profile["sdi"]["confidence_interval"],
            "low_d_recovery": profile["restricted_low_d_recovery"]["mean_recovery"],
            "low_d_classification": profile["restricted_low_d_recovery"]["support"],
            "low_d_ci": profile["restricted_low_d_recovery"]["confidence_interval"],
        })
    claim_rows = []
    for claim in claims["claims"]:
        claim_rows.append({key: claim[key] for key in ("claim_id", "evidence_status", "primary_evidence", "confirmatory_or_exploratory", "main_text_or_supplement")})
    return {
        "table_01_model_profile": {"table_id": "TABLE-01", "rows": profile_rows},
        "table_02_claim_summary": {"table_id": "TABLE-02", "rows": claim_rows},
        "table_s1_registered_negative_heterogeneity": {"table_id": "TABLE-S1", "data": build_heterogeneity_data(ssot)},
        "table_s2_directionality_descriptives": {"table_id": "TABLE-S2", "data": build_directionality_data(ssot)},
    }


def configure_plot() -> None:
    plt.rcParams.update({"font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9, "figure.dpi": 120, "savefig.dpi": 160, "svg.hashsalt": "paper_a_fixed"})


def save_figure(fig: Any, output: Path, stem: str) -> list[Path]:
    output.mkdir(parents=True, exist_ok=True)
    paths = [output / f"{stem}.svg", output / f"{stem}.png"]
    for path in paths:
        fig.savefig(path, metadata={"Date": None}, bbox_inches="tight")
        if path.suffix == ".svg":
            # Matplotlib emits indentation/path lines with trailing spaces;
            # normalize this presentation-only text so Git whitespace checks
            # and repeated renders agree without changing plotted values.
            lines = path.read_text(encoding="utf-8").splitlines()
            path.write_text("\n".join(line.rstrip() for line in lines) + "\n", encoding="utf-8")
    plt.close(fig)
    return paths


def render_figures(output: Path, framework: dict[str, Any], profile_data: dict[str, Any], matrix_data: dict[str, Any], directionality: dict[str, Any], heterogeneity: dict[str, Any]) -> list[Path]:
    configure_plot()
    paths: list[Path] = []
    fig, ax = plt.subplots(figsize=(8, 2.3))
    ax.axis("off")
    labels = [("C0", "direct source-readout reuse"), ("D", "direct-transfer degradation"), ("Ccal", "restricted FIT-only calibration"), ("R", "restricted recoverability")]
    for i, (label, text) in enumerate(labels):
        ax.text(i / 3.2, 0.55, label, ha="center", va="center", fontsize=15, weight="bold", bbox={"boxstyle": "round", "facecolor": "white", "edgecolor": "black"}, transform=ax.transAxes)
        ax.text(i / 3.2, 0.12, text, ha="center", va="center", fontsize=8, transform=ax.transAxes)
    paths += save_figure(fig, output, "figure_01_framework")

    fig, axes = plt.subplots(1, 3, figsize=(10, 3.2))
    names = profile_data["model_order"]
    for ax, metric, title in zip(axes, ("distance_related_degradation", "sdi", "restricted_low_d_recovery"), ("Distance degradation", "SDI", "Restricted LOW-D recovery")):
        vals = [profile_data["profiles"][n][metric]["statistic"]["value"] if metric != "restricted_low_d_recovery" else profile_data["profiles"][n][metric]["mean_recovery"]["value"] for n in names]
        ax.bar(range(len(names)), vals, color=["#4c78a8", "#f58518", "#54a24b"])
        ax.set_title(title); ax.set_xticks(range(len(names))); ax.set_xticklabels(["Qwen", "OLMo", "Llama"], rotation=25, ha="right"); ax.grid(axis="y", alpha=.25)
    fig.suptitle("Three-model operational profile (canonical summaries)")
    paths += save_figure(fig, output, "figure_02_model_profiles")

    fig, axes = plt.subplots(3, 3, figsize=(10, 10), constrained_layout=True)
    for row, model in enumerate(names):
        for col, metric in enumerate(matrix_data["metric_order"]):
            matrix = np.asarray(matrix_data["matrices"][model][metric]["values"], dtype=float)
            # The final axis is the frozen condition axis; display all ten slices
            # as a compact source-target mean only for presentation of the stored
            # values, without changing or reusing them scientifically.
            matrix_display = matrix.mean(axis=2)
            im = axes[row, col].imshow(matrix_display, origin="upper", aspect="auto", cmap="viridis")
            axes[row, col].set_title(f"{model.split('-')[0]} {metric.upper()}")
            axes[row, col].set_xlabel("target layer"); axes[row, col].set_ylabel("source layer")
            fig.colorbar(im, ax=axes[row, col], fraction=.046, pad=.04)
    fig.suptitle("Source-target operational matrices; display mean over ten frozen conditions")
    paths += save_figure(fig, output, "figure_03_matrices")

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
    d = directionality["values"]
    model_names = directionality["model_order"]
    axes[0].bar(model_names, [d[n]["mean_abs_A_C"]["value"] for n in model_names], color="#4c78a8")
    axes[0].set_title("mean |A_C|"); axes[0].tick_params(axis="x", rotation=25)
    axes[1].bar(model_names, [d[n]["signed_shallow_deep_bias"]["value"] for n in model_names], color="#f58518")
    axes[1].axhline(0, color="black", linewidth=.8); axes[1].set_title("signed shallow→deep bias"); axes[1].tick_params(axis="x", rotation=25)
    fig.suptitle("Directionality summary — POST-HOC EXPLORATORY")
    paths += save_figure(fig, output, "figure_04_directionality")

    fig, ax = plt.subplots(figsize=(8, 3.4))
    a = heterogeneity["values"]["EXP-023"]
    x = np.arange(2); width = .35
    d_vals = [a["split_A"]["D_fixed"]["estimate"]["value"], a["split_B"]["D_fixed"]["estimate"]["value"]]
    g_vals = [a["split_A"]["G_cal"]["estimate"]["value"], a["split_B"]["G_cal"]["estimate"]["value"]]
    ax.bar(x - width / 2, d_vals, width, label="D_fixed"); ax.bar(x + width / 2, g_vals, width, label="G_cal")
    ax.axhline(0, color="black", linewidth=.8); ax.set_xticks(x, ["Split A", "Split B"]); ax.set_title("EXP-023 split heterogeneity — registered values"); ax.legend()
    paths += save_figure(fig, output, "figure_05_heterogeneity")
    return paths


def write_facts(output: Path, ssot: dict[str, Any]) -> list[Path]:
    facts = {
        "figure_01_framework.md": ("Measurement framework", "What distinguishes C0, D, Ccal, and R?", "A schematic of registered operational definitions.", "CONFIRMATORY / REGISTERED", "Use only as an operational measurement distinction; no geometric or causal interpretation.", "Paper A claim register C1-C3"),
        "figure_02_model_profiles.md": ("Three-model profile", "Do the registered models share one operational profile?", "Canonical distance, SDI, and restricted recovery summaries.", "CONFIRMATORY / REGISTERED", "The three tested models have scoped different profiles; no architecture causality.", "EXP-026 and EXP-027 canonical results"),
        "figure_03_matrices.md": ("Directed matrices", "How are source-readout and target-representation layers operationally compared?", "C0, D, and R source-target matrices, displayed by source rows and target columns.", "CONFIRMATORY / REGISTERED", "Operational directed matrices only; no latent geometry or semantic equivalence.", "EXP-026 and EXP-027 canonical results"),
        "figure_04_directionality.md": ("Directional asymmetry", "Is signed operational asymmetry descriptively present in the tested profiles?", "Archived mean |A_C| and signed shallow-to-deep bias summaries.", "EXPLORATORY_SECONDARY / POST-HOC EXPLORATORY", "Scoped exploratory description only; no new inference, causal direction, or universal claim.", "Directionality closure"),
        "figure_05_heterogeneity.md": ("Registered heterogeneity", "How stable are registered outcomes across splits and conditions?", "EXP-023 split values and registered negative/heterogeneity evidence.", "CONFIRMATORY / REGISTERED", "Evidence is split/condition heterogeneous; do not select favorable subsets.", "EXP-022A, EXP-023, EXP-024, EXP-025"),
    }
    paths = []
    for filename, (question, scientific_question, shown, role, allowed, canonical) in facts.items():
        text = f"# {question}\n\n- FIGURE_ID: `{filename[:-3].upper()}`\n- SCIENTIFIC_QUESTION: {scientific_question}\n- WHAT_IS_SHOWN: {shown}\n- CONFIRMATORY_OR_EXPLORATORY: {role}\n- ALLOWED_INTERPRETATION: {allowed}\n- PROHIBITED_INTERPRETATION: No new scientific inference, causal mechanism, universal generalization, or representational-equivalence claim.\n- CANONICAL_SOURCE: {canonical}\n"
        path = output / "facts" / filename; path.parent.mkdir(parents=True, exist_ok=True); path.write_text(text, encoding="utf-8"); paths.append(path)
    return paths


def write_tables(output: Path, tables: dict[str, Any]) -> list[Path]:
    paths = []
    for name, table in tables.items():
        path = output / "tables" / f"{name}.json"; write_json(path, table); paths.append(path)
    return paths


def write_data(output: Path, data: dict[str, Any]) -> list[Path]:
    paths = []
    for name, payload in data.items():
        path = output / "data" / f"{name}.json"; write_json(path, payload); paths.append(path)
    return paths


def generate(output: Path = DEFAULT_OUTPUT) -> dict[str, Any]:
    ssot, claims = load_authorities()
    output.mkdir(parents=True, exist_ok=True)
    framework = build_framework()
    profile = build_profile_data(ssot)
    matrices = build_matrix_data(ssot)
    directionality = build_directionality_data(ssot)
    heterogeneity = build_heterogeneity_data(ssot)
    data_paths = write_data(output, {"figure_01_framework_spec": framework, "figure_02_profile_data": profile, "figure_03_matrix_data": matrices, "figure_04_directionality_data": directionality, "figure_05_heterogeneity_data": heterogeneity})
    table_paths = write_tables(output, build_tables(ssot, claims))
    fact_paths = write_facts(output, ssot)
    figure_paths = render_figures(output / "figures", framework, profile, matrices, directionality, heterogeneity)
    generator_path = Path(__file__).resolve()
    manifest = {
        "manifest_schema_version": "1.0.0",
        "generator": {"path": "experiments/paper_a/generate_paper_assets.py", "sha256": sha256(generator_path)},
        "canonical_ssot": {"path": "experiments/paper_a/canonical/paper_a_scientific_results.json", "sha256": sha256(SSOT_PATH)},
        "claim_register": {"path": "experiments/paper_a/canonical/paper_a_claim_register.json", "sha256": sha256(CLAIMS_PATH)},
        "input_canonical_result_hashes": {key: item["sha256"] for key, item in ssot["canonical_sources"].items()},
        "figure_ids": ["FIGURE-01", "FIGURE-02", "FIGURE-03", "FIGURE-04", "FIGURE-05"],
        "table_ids": ["TABLE-01", "TABLE-02", "TABLE-S1", "TABLE-S2"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"python": platform.python_version(), "matplotlib": matplotlib.__version__, "numpy": np.__version__},
        "scientific_content_deterministic": True,
        "rendered_file_bytes_deterministic": True,
    }
    all_outputs = data_paths + table_paths + fact_paths + figure_paths
    manifest["output_files"] = [{"path": str(path.relative_to(output)).replace("\\", "/"), "sha256": sha256(path)} for path in sorted(all_outputs)]
    write_json(output / "manifests/paper_asset_manifest.json", manifest)
    print(f"PAPER_A_ASSETS_GENERATED={output}")
    print(f"PAPER_A_OUTPUT_COUNT={len(all_outputs)}")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    generate(args.output_dir.resolve())


if __name__ == "__main__":
    main()
