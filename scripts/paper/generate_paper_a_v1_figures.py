#!/usr/bin/env python3
"""Render the three current Paper A V1 publication figures.

This renderer is deliberately read-only with respect to scientific authorities:
it consumes frozen result artifacts, checks their identities and transcribes
registered values.  It performs no model execution, fitting, resampling, or
new statistical analysis.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

matplotlib.rcParams["svg.hashsalt"] = "paper-a-v1"


ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = ROOT / "docs" / "paper" / "figures"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)

EXP026 = ROOT / "experiments" / "exp026" / "results" / "exp026_results.json"
EXP027 = ROOT / "experiments" / "exp027" / "results" / "exp027_results.json"
METRIC_SPEC = ROOT / "experiments" / "exp026" / "EXP-026-MATRIX-METRIC-SPECIFICATION.md"
POSITIONING = ROOT / "docs" / "paper_a" / "PAPER-A-POSITIONING-FREEZE-V1.md"
MANUSCRIPT = ROOT / "docs" / "paper" / "PAPER-A-MANUSCRIPT-V1.1.md"
ARCHITECTURE = ROOT / "docs" / "paper" / "revision" / "PAPER-A-POST-AUDIT-MANUSCRIPT-ARCHITECTURE.md"

EXPECTED_RESULT_SHA256 = {
    "exp026": "9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551",
    "exp027": "1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d",
}

MODEL_INFO = {
    "Qwen": {"key": "Q", "layers": 28, "exp": "exp026", "label": "Qwen"},
    "OLMo": {"key": "O", "layers": 16, "exp": "exp026", "label": "OLMo"},
    "Llama": {"key": "L", "layers": 16, "exp": "exp027", "label": "Llama"},
}

COLORS = {"Qwen": "#0072B2", "OLMo": "#D55E00", "Llama": "#009E73"}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_equal(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-12) -> None:
    if not np.isclose(actual, expected, atol=tol, rtol=0):
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def load_authorities() -> tuple[dict[str, Any], dict[str, str]]:
    paths = {"exp026": EXP026, "exp027": EXP027}
    data = {name: load_json(path) for name, path in paths.items()}
    hashes = {name: sha256_file(path) for name, path in paths.items()}
    for name, expected in EXPECTED_RESULT_SHA256.items():
        assert_equal(hashes[name], expected, f"{name} result SHA-256")
    for path in (METRIC_SPEC, POSITIONING, MANUSCRIPT, ARCHITECTURE):
        if not path.exists():
            raise FileNotFoundError(path)

    q = data["exp026"]["model_profiles"]["Q"]
    o = data["exp026"]["model_profiles"]["O"]
    l = data["exp027"]["profile_archive"]
    assert_equal(q["num_layers"], 28, "Qwen layer count")
    assert_equal(o["num_layers"], 16, "OLMo layer count")
    assert_equal(l["num_layers"], 16, "Llama layer count")
    expected = {
        "Qwen": (q["point"], q["bootstrap"], q["support"]),
        "OLMo": (o["point"], o["bootstrap"], o["support"]),
        "Llama": (l["point"], l["bootstrap"], data["exp027"]["profile"]),
    }
    expected_values = {
        "Qwen": (0.7049462571528698, -0.17355352410373298, 0.00013923267534205524),
        "OLMo": (0.7519250367843754, 0.5249651786448143, 0.04785714308465166),
        "Llama": (0.6077483252598234, -0.41426422986393563, 0.0014030612453970375),
    }
    for name, (point, _bootstrap, _support) in expected.items():
        distance, sdi, low_d = expected_values[name]
        assert_close(float(point["distance_association"]), distance, f"{name} distance")
        assert_close(float(point["sdi"] if isinstance(point["sdi"], (float, int)) else point["sdi"]["sdi"]), sdi, f"{name} SDI")
        low_value = point["low_d_recovery"]
        if isinstance(low_value, dict):
            low_value = low_value["mean_recovery"]
        assert_close(float(low_value), low_d, f"{name} LOW-D")
    return data, hashes


def _save(fig: plt.Figure, stem: str) -> dict[str, str]:
    png = FIGURE_DIR / f"{stem}.png"
    svg = FIGURE_DIR / f"{stem}.svg"
    fig.savefig(png, dpi=180, bbox_inches="tight", facecolor="white", metadata={"Date": None})
    fig.savefig(svg, bbox_inches="tight", facecolor="white", metadata={"Date": None})
    plt.close(fig)
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")
    return {
        "png": str(png.relative_to(ROOT)),
        "svg": str(svg.relative_to(ROOT)),
        "png_sha256": sha256_file(png),
        "svg_sha256": sha256_file(svg),
    }


def _box(ax: plt.Axes, xy: tuple[float, float], width: float, height: float, text: str, *, fc: str = "#F5F5F5", ec: str = "#404040", fontsize: float = 10) -> None:
    x, y = xy
    patch = FancyBboxPatch((x, y), width, height, boxstyle="round,pad=0.025", facecolor=fc, edgecolor=ec, linewidth=1.2)
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=fontsize, wrap=True)


def figure_1() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(12.7, 6.0))
    ax.set_xlim(0, 13.1)
    ax.set_ylim(0, 8.4)
    ax.axis("off")
    ax.text(0.25, 8.05, "Paper A: operational measurement framework", fontsize=15, weight="bold", va="top")
    ax.text(0.25, 7.67, "Direct reuse and restricted FIT-only recovery are separate evaluation paths.", fontsize=10, color="#404040", va="top")
    ax.text(0.42, 7.17, "SOURCE PATH (FIT)", fontsize=10, weight="bold", color="#404040")
    _box(ax, (0.42, 6.05), 1.8, 0.85, "source depth s\npost-block residual", fontsize=9.5)
    _box(ax, (2.75, 6.05), 1.8, 0.85, "h_s\nFIT representation", fontsize=9.5)
    _box(ax, (5.08, 6.05), 2.1, 0.85, "fit q_s on FIT\nfixed source readout", fontsize=9.2)
    _box(ax, (7.75, 6.05), 2.0, 0.85, "C_self(s)\nsource self score", fc="#EAF2F8", ec="#0072B2", fontsize=9.5)
    for x0, x1 in ((2.22, 2.75), (4.55, 5.08), (7.18, 7.75)):
        ax.add_patch(FancyArrowPatch((x0, 6.475), (x1, 6.475), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#404040"))

    ax.text(0.42, 5.35, "TARGET PATH (EVAL)", fontsize=10, weight="bold", color="#404040")
    _box(ax, (0.42, 4.22), 1.8, 0.85, "target depth t\npost-block residual", fontsize=9.5)
    _box(ax, (2.75, 4.22), 1.8, 0.85, "h_t\nEVAL representation", fontsize=9.5)
    ax.add_patch(FancyArrowPatch((2.22, 4.645), (2.75, 4.645), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#404040"))

    ax.text(4.78, 5.15, "A. DIRECT REUSE", fontsize=9.8, weight="bold", color="#0072B2")
    _box(ax, (4.68, 4.22), 1.85, 0.85, "frozen q_s\nno retraining", fontsize=9.5)
    _box(ax, (6.95, 4.22), 1.75, 0.85, "C0(s,t)\ndirect", fc="#EAF2F8", ec="#0072B2", fontsize=9.5)
    _box(ax, (9.12, 4.22), 2.55, 0.85, "D(s,t) = C_self(s)\n− C0(s,t)", fc="#FDEDEC", ec="#D55E00", fontsize=9.0)
    for x0, x1 in ((4.55, 4.68), (6.53, 6.95), (8.70, 9.12)):
        ax.add_patch(FancyArrowPatch((x0, 4.645), (x1, 4.645), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#0072B2"))

    ax.text(4.78, 3.62, "B. RESTRICTED FIT-ONLY RECOVERY", fontsize=9.8, weight="bold", color="#009E73")
    _box(ax, (4.68, 2.68), 1.85, 0.85, "apply frozen restricted\ncalibration", fc="#E8F6F3", ec="#009E73", fontsize=8.8)
    _box(ax, (6.95, 2.68), 1.75, 0.85, "calibrated target\nevaluation", fc="#E8F6F3", ec="#009E73", fontsize=9.0)
    _box(ax, (9.12, 2.68), 1.75, 0.85, "C_cal(s,t)\ncalibrated", fc="#E8F6F3", ec="#009E73", fontsize=9.2)
    _box(ax, (11.15, 2.68), 1.45, 0.85, "R(s,t)\n= C_cal − C0", fc="#E8F6F3", ec="#009E73", fontsize=8.7)
    ax.text(10.55, 3.94, "FIT only: estimate + freeze parameters", fontsize=7.8, color="#007A61", ha="center", va="center", bbox={"boxstyle": "round,pad=0.10", "facecolor": "#FFFFFF", "edgecolor": "#009E73", "linestyle": "--", "linewidth": 0.9})
    ax.add_patch(FancyArrowPatch((3.65, 4.22), (4.68, 3.53), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#009E73"))
    for x0, x1 in ((6.53, 6.95), (8.70, 9.12), (10.87, 11.15)):
        ax.add_patch(FancyArrowPatch((x0, 3.105), (x1, 3.105), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#009E73"))
    ax.add_patch(FancyArrowPatch((3.65, 4.55), (4.68, 4.645), arrowstyle="-|>", mutation_scale=12, linewidth=1.1, color="#0072B2"))
    ax.add_patch(FancyBboxPatch((0.25, 0.48), 12.55, 6.88, boxstyle="round,pad=0.02", fill=False, linestyle="--", linewidth=1.0, edgecolor="#888888"))
    ax.text(0.5, 0.72, "Measured: readout-relative compatibility and restricted recovery", fontsize=8.8, color="#404040")
    ax.text(0.5, 0.51, "Not inferred: geometry, information flow, mechanism, or causality", fontsize=8.8, color="#404040")
    return fig


def _profile_data(data: dict[str, Any], name: str) -> tuple[float, list[float], float, list[float], float, list[float], str, str]:
    info = MODEL_INFO[name]
    if info["exp"] == "exp026":
        profile = data["exp026"]["model_profiles"][info["key"]]
        support = profile["support"]
    else:
        profile = data["exp027"]["profile_archive"]
        support = data["exp027"]["profile"]
    point = profile["point"]
    boot = profile["bootstrap"]
    low = point["low_d_recovery"]
    if isinstance(low, dict):
        low = low["mean_recovery"]
    sdi = point["sdi"] if isinstance(point["sdi"], (int, float)) else point["sdi"]["sdi"]
    return (
        float(point["distance_association"]), list(map(float, boot["distance_association_ci"])),
        float(sdi), list(map(float, boot["sdi_ci"])),
        float(low), list(map(float, boot["low_d_recovery_ci"])),
        support.get("distance_support", "POSITIVE_SUPPORTED") if isinstance(support, dict) else support["distance_association_status"],
        support.get("sdi_class", support.get("dominance_status", "")) if isinstance(support, dict) else support["dominance_status"],
    )


def figure_2(data: dict[str, Any]) -> plt.Figure:
    names = ["Qwen", "OLMo", "Llama"]
    profiles = {name: _profile_data(data, name) for name in names}
    fig = plt.figure(figsize=(12.6, 8.0))
    grid = fig.add_gridspec(2, 2, height_ratios=[1.15, 1.0], hspace=0.38, wspace=0.28)
    fig.suptitle("Three-model operational profiles", fontsize=16, weight="bold", y=0.98)
    x = np.arange(3)
    labels = ["Qwen", "OLMo", "Llama"]

    ax = fig.add_subplot(grid[0, 0])
    vals = [profiles[n][0] for n in names]
    lo = [vals[i] - profiles[names[i]][1][0] for i in range(3)]
    hi = [profiles[names[i]][1][1] - vals[i] for i in range(3)]
    ax.errorbar(x, vals, yerr=[lo, hi], fmt="o", color="#0072B2", ecolor="#0072B2", capsize=4)
    ax.set_title("A. Depth-distance association with degradation")
    ax.set_ylabel("Spearman association")
    ax.set_xticks(x, labels)
    ax.set_ylim(0.0, 0.82)
    ax.axhline(0, color="#888888", linewidth=0.8)
    ax.text(0.02, 0.04, "positive depth-distance association in all three tested models", transform=ax.transAxes, fontsize=8.2, color="#404040")

    ax = fig.add_subplot(grid[0, 1])
    vals = [profiles[n][2] for n in names]
    lo = [vals[i] - profiles[names[i]][3][0] for i in range(3)]
    hi = [profiles[names[i]][3][1] - vals[i] for i in range(3)]
    ax.errorbar(x, vals, yerr=[lo, hi], fmt="o", color="#D55E00", ecolor="#D55E00", capsize=4)
    ax.axhline(0, color="#404040", linewidth=1)
    ax.set_title("B. Source/target organization (SDI)")
    ax.set_ylabel("SDI")
    ax.set_xticks(x, labels)
    ax.set_ylim(-0.58, 0.68)
    ax.text(0.02, 0.04, "negative = TARGET_DOMINANT; positive = SOURCE_DOMINANT", transform=ax.transAxes, fontsize=8.0, color="#404040")

    ax = fig.add_subplot(grid[1, 0])
    vals = [profiles[n][4] for n in names]
    lo = [vals[i] - profiles[names[i]][5][0] for i in range(3)]
    hi = [profiles[names[i]][5][1] - vals[i] for i in range(3)]
    marker_faces = ["white", "#009E73", "#009E73"]
    ax.errorbar(x, vals, yerr=[lo, hi], fmt="none", ecolor="#009E73", capsize=4)
    for xi, value, face in zip(x, vals, marker_faces):
        ax.plot(xi, value, marker="o", markersize=8, markerfacecolor=face, markeredgecolor="#009E73", markeredgewidth=1.5, linestyle="none")
    ax.axhline(0, color="#888888", linewidth=0.8)
    ax.set_title("C. LOW-D restricted recovery")
    ax.set_ylabel("mean R")
    ax.set_xticks(x, labels)
    ax.set_ylim(-0.005, 0.060)
    ax.legend(handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor="#009E73", markeredgecolor="#009E73", markersize=7, label="filled = registered support"), Line2D([0], [0], marker="o", color="none", markerfacecolor="white", markeredgecolor="#009E73", markersize=7, label="open = not supported")], loc="upper left", frameon=False, fontsize=8)

    ax = fig.add_subplot(grid[1, 1])
    ax.set_xlim(-0.85, 2.0)
    ax.set_ylim(-0.72, 2.25)
    ax.axis("off")
    ax.text(0.58, 2.18, "D. Observed combinations of registered profile components", fontsize=9.2, weight="bold", ha="center")
    ax.text(0.58, 1.98, "SOURCE/TARGET organization", fontsize=8.5, weight="bold", ha="center")
    ax.text(0.5, 1.78, "TARGET_DOMINANT", fontsize=8.2, ha="center")
    ax.text(1.5, 1.78, "SOURCE_DOMINANT", fontsize=8.2, ha="center")
    ax.text(-0.05, 1.5, "SUPPORTED", fontsize=8.0, weight="bold", va="center", ha="right")
    ax.text(-0.05, 0.5, "NOT_SUPPORTED", fontsize=8.0, weight="bold", va="center", ha="right")
    ax.text(-0.64, 1.0, "LOW-D support", fontsize=8.0, rotation=90, va="center", ha="center")
    for cx in (0, 1):
        for cy in (0, 1):
            ax.add_patch(Rectangle((cx, cy), 1, 1, facecolor="#FAFAFA", edgecolor="#555555", linewidth=1.0))
    ax.text(0.5, 0.5, "Qwen", color=COLORS["Qwen"], weight="bold", fontsize=9.5, ha="center", va="center")
    ax.text(1.5, 1.5, "OLMo", color=COLORS["OLMo"], weight="bold", fontsize=9.5, ha="center", va="center")
    ax.text(0.5, 1.5, "Llama", color=COLORS["Llama"], weight="bold", fontsize=9.5, ha="center", va="center")
    ax.text(1.5, 0.5, "—", color="#777777", fontsize=13, ha="center", va="center")
    ax.text(0.5, -0.16, "Empty cell = not observed in this three-model panel.", fontsize=7.5, ha="center")
    ax.text(0.5, -0.38, "Llama routing: prospective.", fontsize=7.3, ha="center", color="#404040")
    ax.text(0.5, -0.54, "Mapping-break interpretation: bounded post-hoc synthesis.", fontsize=7.3, ha="center", color="#404040")
    return fig


def _matrix(data: dict[str, Any], name: str) -> np.ndarray:
    info = MODEL_INFO[name]
    if info["exp"] == "exp026":
        raw = data["exp026"]["model_profiles"][info["key"]]["matrices"]["dbar_eval"]["values"]
    else:
        raw = data["exp027"]["profile_archive"]["dbar_eval"]
    matrix = np.asarray(raw, dtype=float)
    assert_equal(tuple(matrix.shape), (info["layers"], info["layers"]), f"{name} Dbar shape")
    return matrix


def figure_3(data: dict[str, Any]) -> tuple[plt.Figure, dict[str, Any]]:
    matrices = {name: _matrix(data, name) for name in MODEL_INFO}
    vmax = max(float(np.max(np.abs(m))) for m in matrices.values())
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.9), constrained_layout=True)
    fig.suptitle("Full directed source-target matrices", fontsize=16, weight="bold", y=1.02)
    image = None
    for ax, (name, matrix) in zip(axes, matrices.items()):
        image = ax.imshow(matrix, cmap="RdBu_r", vmin=-vmax, vmax=vmax, interpolation="none", aspect="equal")
        n = matrix.shape[0]
        ticks = np.linspace(0, n - 1, min(n, 6), dtype=int)
        ax.set_xticks(ticks, [str(v) for v in ticks], fontsize=8)
        ax.set_yticks(ticks, [str(v) for v in ticks], fontsize=8)
        ax.set_xlabel("target layer t", fontsize=9)
        ax.set_ylabel("source layer s", fontsize=9)
        ax.set_title(f"{name} ({n}×{n})")
    cbar = fig.colorbar(image, ax=axes, shrink=0.82, pad=0.02)
    cbar.set_label("D̄: condition-pooled degradation", fontsize=9)
    return fig, {"matrix_quantity": "Dbar_eval", "direction_convention": "source rows → target columns", "common_scale": True, "interpolation": False, "common_abs_limit": vmax}


def write_captions(metadata: dict[str, Any]) -> Path:
    path = FIGURE_DIR / "PAPER-A-V1-FIGURE-CAPTIONS.md"
    text = """# Paper A V1 Figure Captions

## Figure 1 — Operational measurement framework

**What is shown.** A readout fit at source depth `s` is evaluated on the source self representation and then directly reused on target depth `t`. The target representation branches into direct reuse through frozen `q_s` and a separate restricted calibration path whose parameters are estimated on FIT only, frozen, and then applied to EVAL, yielding `C0`, `D`, `C_cal`, and `R` as parallel operational quantities.

**Main observation.** These are distinct operational measurements of the same source-target protocol.

**Not implied.** The diagram does not represent latent geometry, information flow, mechanism, causality, or semantic equivalence.

## Figure 2 — Three-model operational profiles

**What is shown.** Registered continuous values and one-sided 95% cluster-bootstrap intervals for depth-distance association with degradation, SDI, and LOW-D restricted recovery. Panel D is a discrete 2×2 display of the observed combinations of registered profile components.

**Main observation.** Positive distance-associated structure is supported in all three tested models; organization and LOW-D recovery classifications differ by model. The third registered profile adds a target-dominant plus supported LOW-D combination absent from the initial two-model pairing.

**Not implied.** Categorical profiles are not a learned embedding, latent coordinate space, clustering, taxonomy, independence test, or causal explanation. The empty cell means not observed in this three-model panel. Llama routing was prospective; the mapping-break interpretation is bounded post-hoc synthesis.

## Figure 3 — Full directed source-target matrices

**What is shown.** Native-resolution condition-pooled degradation matrices `Dbar_eval`, with source-readout layers on rows and target-representation layers on columns. Qwen uses 28 layers; OLMo and Llama use 16 layers. Panels retain native layer indices. A common symmetric color scale is used only for visual comparison, with no interpolation or resampling. Cross-model distance analysis uses registered normalized depth. `D = 0` means no degradation relative to the source self condition; positive `D` means worse direct fixed-readout compatibility relative to self.

**Main observation.** The registered operational matrix retains source-target orientation and permits descriptive comparison of depth-dependent degradation.

**Not implied.** Matrix orientation is operational; it does not establish geometry, information flow, causal direction, or a mechanism. The heatmaps do not replace the separate `C0`, `D`, and `R` definitions.
"""
    path.write_text(text, encoding="utf-8")
    return path


def write_manifest(data_hashes: dict[str, str], figures: dict[str, dict[str, str]], matrix_meta: dict[str, Any]) -> Path:
    source_paths = {
        "exp026_results": EXP026,
        "exp027_results": EXP027,
        "matrix_metric_specification": METRIC_SPEC,
        "positioning_freeze": POSITIONING,
        "manuscript_v1_1": MANUSCRIPT,
        "post_audit_architecture": ARCHITECTURE,
    }
    source_records = {name: {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)} for name, path in source_paths.items()}
    renderer = "scripts/paper/generate_paper_a_v1_figures.py"
    manifest = {
        "schema_version": "1.0",
        "generated_by": renderer,
        "no_new_inference": True,
        "no_model_inference": True,
        "canonical_values_transcribed": True,
        "sources": source_records,
        "canonical_result_hashes_verified": data_hashes,
        "figures": {
            "figure_1": {"png": figures["figure_1"]["png"], "svg": figures["figure_1"]["svg"], "png_sha256": figures["figure_1"]["png_sha256"], "svg_sha256": figures["figure_1"]["svg_sha256"], "renderer": renderer, "source_files": {key: source_records[key] for key in ("positioning_freeze", "manuscript_v1_1")}, "panel_type": "CONCEPTUAL", "exact_quantities": ["C0", "D", "C_cal", "R"], "fit_eval_boundary": "parameters estimated on FIT only, frozen before EVAL application", "no_new_inference": True},
            "figure_2": {"png": figures["figure_2"]["png"], "svg": figures["figure_2"]["svg"], "png_sha256": figures["figure_2"]["png_sha256"], "svg_sha256": figures["figure_2"]["svg_sha256"], "renderer": renderer, "source_files": {key: source_records[key] for key in ("exp026_results", "exp027_results", "manuscript_v1_1", "post_audit_architecture")}, "panel_type": "CANONICAL_NUMERIC_PLUS_FROZEN_CATEGORICAL_SYNTHESIS", "exact_quantities": ["distance_association", "SDI", "LOW_D_RECOVERY", "registered profile statuses"], "categorical_panel_layout": "2x2 discrete grid", "continuous_values_visible": True, "no_new_inference": True},
            "figure_3": {"png": figures["figure_3"]["png"], "svg": figures["figure_3"]["svg"], "png_sha256": figures["figure_3"]["png_sha256"], "svg_sha256": figures["figure_3"]["svg_sha256"], "renderer": renderer, "source_files": {key: source_records[key] for key in ("exp026_results", "exp027_results", "matrix_metric_specification", "manuscript_v1_1")}, "panel_type": "CANONICAL_NUMERIC", "exact_quantities": ["Dbar_eval"], "matrix_metadata": matrix_meta, "data_unchanged_from_previous_v1": True, "no_new_inference": True},
        },
        "historical_figure_dispositions": {
            "fig01_framework": "SUPPLEMENT_REUSE_WITH_CAPTION_UPDATE",
            "fig02_manipulability": "STALE_FOR_CURRENT_PAPER",
            "fig03_fixed_readout_degradation": "SUPPLEMENT_REUSE_WITH_CAPTION_UPDATE",
            "fig04_exp023_heterogeneity": "SUPPLEMENT_REUSE_WITH_CAPTION_UPDATE",
            "fig05_exp024_primary_scatter": "SUPPLEMENT_REUSE_WITH_CAPTION_UPDATE",
            "fig06_exp024_broad_benefit": "STALE_FOR_CURRENT_PAPER",
        },
    }
    path = FIGURE_DIR / "paper_a_v1_figure_source_manifest.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def main() -> None:
    data, hashes = load_authorities()
    outputs: dict[str, dict[str, str]] = {}
    outputs["figure_1"] = _save(figure_1(), "paper_a_v1_fig01_measurement_framework")
    outputs["figure_2"] = _save(figure_2(data), "paper_a_v1_fig02_three_model_synthesis")
    fig3, matrix_meta = figure_3(data)
    outputs["figure_3"] = _save(fig3, "paper_a_v1_fig03_directed_matrices")
    captions = write_captions(matrix_meta)
    manifest = write_manifest(hashes, outputs, matrix_meta)
    print(json.dumps({"figures": outputs, "manifest": str(manifest.relative_to(ROOT)), "captions": str(captions.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
