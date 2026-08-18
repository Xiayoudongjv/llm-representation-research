
#!/usr/bin/env python3
"""Deterministically generate Paper-A figures and table artifacts from canonical results.

This script performs no new inferential tests. It reads canonical JSON result
artifacts, verifies expected scientific identities, and renders publication
previews plus vector figures. It also writes the two main evidence tables.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = ROOT / "docs" / "paper" / "figures"
TABLE_DIR = ROOT / "docs" / "paper" / "tables"
FIGURE_DIR.mkdir(parents=True, exist_ok=True)
TABLE_DIR.mkdir(parents=True, exist_ok=True)

SOURCES = {
    "exp024": ROOT / "experiments" / "exp024" / "results" / "exp024_results.json",
    "exp023": ROOT / "experiments" / "exp023" / "results" / "exp023_results.json",
    "exp022a": ROOT / "experiments" / "exp022a" / "results" / "exp022a_results.json",
    "exp021": ROOT / "experiments" / "exp021" / "engineering" / "stage_q_result.json",
    "exp020a": ROOT / "experiments" / "exp020" / "results" / "exp020a_results.json",
}

EXPECTED_SHA256 = {
    "exp024": "50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69",
    "exp020a": "c603b763c5b5723b002d67ce71a073beba9668bf8bc49e0a215cc54d5f82e26a",
}

# Okabe-Ito-ish colorblind-safe palette.
COLOR_FIXED = "#404040"
COLOR_RECAL = "#0072B2"
COLOR_BOUNDARY = "#D55E00"
COLOR_SPLIT_A = "#0072B2"
COLOR_SPLIT_B = "#D55E00"
COLOR_POSITIVE = "#0072B2"
COLOR_NEGATIVE = "#D55E00"

SHORT_CONDITION = {
    "c01_lexical_relex": "c01 lexical relex",
    "c02_syntactic_restructure": "c02 syntactic restructure",
    "c03_controlled_compression": "c03 controlled compression",
    "c04_controlled_elaboration": "c04 controlled elaboration",
    "c05_relation_explicit": "c05 relation explicit",
    "c06_relation_implicit": "c06 relation implicit",
    "c07_register_formal": "c07 register formal",
    "c08_register_informal": "c08 register informal",
    "c09_neutral_distractor_prefix": "c09 neutral distractor prefix",
    "c10_anaphoric_reference": "c10 anaphoric reference",
}

CHECKPOINT_LABELS = {
    "intervention": "reference\n(intervention)",
    "normalized_0.625": "0.625",
    "normalized_0.75": "0.75",
    "normalized_0.875": "0.875",
    "final_block_pre_final_rmsnorm": "final block\npre-RMSNorm",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_eq(actual: Any, expected: Any, label: str) -> None:
    if actual != expected:
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def assert_close(actual: float, expected: float, label: str, tol: float = 1e-12) -> None:
    if not math.isclose(actual, expected, rel_tol=0.0, abs_tol=tol):
        raise AssertionError(f"{label}: expected {expected!r}, got {actual!r}")


def load_authorities() -> Tuple[Dict[str, Any], Dict[str, str]]:
    data: Dict[str, Any] = {}
    hashes: Dict[str, str] = {}
    for key, path in SOURCES.items():
        if not path.exists():
            raise FileNotFoundError(path)
        hashes[key] = sha256_file(path)
        data[key] = load_json(path)

    for key, expected in EXPECTED_SHA256.items():
        assert_eq(hashes[key], expected, f"{key} SHA-256")

    exp024 = data["exp024"]
    primary = exp024["primary"]
    assert_close(float(primary["rho"]), 0.28401877872187725, "EXP-024 primary rho")
    assert_close(float(primary["exact_one_sided_p"]), 0.2115079365079365, "EXP-024 primary p")
    assert_eq(bool(primary["supported"]), False, "EXP-024 primary supported")
    assert_eq(primary["outcome"], "G_eval(c)", "EXP-024 primary outcome")
    assert_eq(primary["diagnostic"], "S_diag(c)", "EXP-024 primary diagnostic")
    condition_order = exp024["condition_level"]["condition_order"]
    assert_eq(len(condition_order), 10, "EXP-024 condition count")
    assert_eq(condition_order, list(SHORT_CONDITION.keys()), "EXP-024 condition order")

    exp023 = data["exp023"]
    assert_eq(exp023["cross_split_synthesis"]["G_cal"], "NO_REPLICATION", "EXP-023 G_cal synthesis")
    assert_eq(set(exp023["splits"].keys()), {"A", "B"}, "EXP-023 split identity")

    exp022a = data["exp022a"]
    assert_eq(exp022a["cross_split_synthesis"]["D_fixed"], "PARTIAL_CONCORDANCE", "EXP-022A D_fixed")
    assert_eq(exp022a["cross_split_synthesis"]["G_refit"], "SPLIT_HETEROGENEOUS", "EXP-022A G_refit")

    exp021 = data["exp021"]
    assert_eq(exp021["result_classification"], "ENGINEERING_MEASUREMENT_QUALIFICATION_ONLY", "EXP-021 classification")
    assert_eq(bool(exp021["global_pass"]), False, "EXP-021 global_pass")
    assert_eq(exp021["checkpoint_mapping"]["final_block_pre_final_rmsnorm"]["role"], "PRIMARY_FINAL_CHECKPOINT", "EXP-021 primary role")
    assert_eq(exp021["checkpoint_mapping"]["final_normalized_hidden_state"]["role"], "DESCRIPTIVE_ONLY", "EXP-021 descriptive role")

    exp020a = data["exp020a"]
    assert_eq(exp020a["primary"]["gate_outcome"], "REPRESENTATION_REPLICATION_SUPPORTED", "EXP-020A gate outcome")

    return data, hashes


def save_figure(fig: plt.Figure, stem: str) -> Dict[str, str]:
    png_path = FIGURE_DIR / f"{stem}.png"
    svg_path = FIGURE_DIR / f"{stem}.svg"
    fig.savefig(png_path, dpi=150, bbox_inches="tight", facecolor="white")
    fig.savefig(svg_path, bbox_inches="tight", facecolor="white")
    plt.close(fig)

    # Matplotlib SVG output may contain trailing spaces at line boundaries.
    # Strip them so the committed vector files satisfy `git diff --check`.
    svg_text = svg_path.read_text(encoding="utf-8")
    svg_path.write_text("\n".join(line.rstrip() for line in svg_text.splitlines()) + "\n", encoding="utf-8")

    return {
        "stem": stem,
        "png": str(png_path.relative_to(ROOT)),
        "svg": str(svg_path.relative_to(ROOT)),
        "png_sha256": sha256_file(png_path),
        "svg_sha256": sha256_file(svg_path),
    }


def _style_ax(ax: plt.Axes) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8)
    ax.grid(axis="y", linestyle=":", linewidth=0.6, alpha=0.4)


def fig01_framework() -> plt.Figure:
    fig, ax = plt.subplots(figsize=(6.5, 5.0))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 11)
    ax.axis("off")

    nodes = [
        (1, "Fixed semantic readout", "TESTED"),
        (2, "Cross-depth compatibility", "TESTED"),
        (3, "FIT-only featurewise\nrecalibration", "TESTED"),
        (4, "Held-out recovery", "TESTED"),
        (5, "Replication / heterogeneity", "TESTED"),
        (6, "Independent susceptibility test", "TESTED"),
    ]
    positions = [(5.0, 10.4 - i * 1.52) for i in range(len(nodes))]
    for (y, label, status), (x, ypos) in zip(nodes, positions):
        width = 5.4 if len(label.split("\n")[0]) <= 18 else 5.8
        box = FancyBboxPatch((x - width / 2, ypos - 0.38), width, 0.76,
                             boxstyle="round,pad=0.02", linewidth=1.2,
                             edgecolor=COLOR_FIXED, facecolor="#F5F5F5")
        ax.add_patch(box)
        ax.text(x, ypos, label, ha="center", va="center", fontsize=8.5, color=COLOR_FIXED, linespacing=1.15)
        if y < 6:
            ax.annotate("", xy=(x, ypos - 0.40), xytext=(x, ypos - 0.78),
                        arrowprops=dict(arrowstyle="-", color=COLOR_FIXED, lw=1.0))

    boundary_label = ("BOUNDARY / NOT ESTABLISHED:\n"
                      "behavioral control, functional binding,\ncoordinate transport")
    box = FancyBboxPatch((1.4, 0.45), 7.2, 1.15, boxstyle="round,pad=0.03",
                         linewidth=1.4, linestyle="--", edgecolor=COLOR_BOUNDARY,
                         facecolor="none")
    ax.add_patch(box)
    ax.text(5.0, 1.02, boundary_label, ha="center", va="center", fontsize=8.5,
            color=COLOR_BOUNDARY, linespacing=1.25)

    return fig


def fig02_manipulability(exp020a: Dict[str, Any]) -> plt.Figure:
    summary = exp020a["primary"]["summary"]["observed"]
    bootstrap = exp020a["primary"]["summary"]["bootstrap_ci"]
    labels = ["task_effect", "D_random", "D_opposite"]
    pretty = ["Task effect", "Matched-random\ncontrast", "Opposite-direction\ncontrast"]
    values = [summary[k]["mean"] for k in labels]
    lower = [bootstrap[k][0] for k in labels]
    upper = [bootstrap[k][1] for k in labels]
    yerr = [[v - lo for v, lo in zip(values, lower)], [hi - v for v, hi in zip(values, upper)]]

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    x = list(range(len(labels)))
    bars = ax.bar(x, values, yerr=yerr, capsize=4, width=0.58,
                  color=[COLOR_RECAL, COLOR_FIXED, COLOR_FIXED], edgecolor="black", linewidth=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels(pretty, fontsize=8)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Observed mean (bootstrap 95% CI)", fontsize=8)
    _style_ax(ax)
    for xi, v in zip(x, values):
        ax.text(xi, v + 0.03, f"{v:.3f}", ha="center", fontsize=7.5)
    ax.text(0.02, 1.02, "EXP-020A gate: REPRESENTATION_REPLICATION_SUPPORTED",
            transform=ax.transAxes, fontsize=7.2, va="bottom", color=COLOR_RECAL)
    ax.text(0.02, 0.965, "EXP-018 probe: task > matched-random 216/216; task > opposite 216/216",
            transform=ax.transAxes, fontsize=6.8, va="bottom", color=COLOR_FIXED)
    fig.tight_layout()
    return fig


def fig03_fixed_readout(exp021: Dict[str, Any]) -> plt.Figure:
    summaries = exp021["checkpoint_summaries"]
    split_keys = ["A_original_fit_paraphrase_eval", "B_paraphrase_fit_original_eval"]
    checkpoints = ["intervention", "normalized_0.625", "normalized_0.75",
                   "normalized_0.875", "final_block_pre_final_rmsnorm"]

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    for split, color, marker, label in [
        (split_keys[0], COLOR_SPLIT_A, "o", "Split A"),
        (split_keys[1], COLOR_SPLIT_B, "s", "Split B"),
    ]:
        vals = [summaries[split][ck]["accuracy"] for ck in checkpoints]
        pass_flags = [bool(summaries[split][ck]["pass"]) for ck in checkpoints]
        x = list(range(len(checkpoints)))
        ax.plot(x, vals, color=color, marker=marker, linewidth=1.2, markersize=4.5, label=label)
        for xi, v, ok in zip(x, vals, pass_flags):
            if not ok:
                ax.scatter(xi, v, s=45, facecolors="none", edgecolors=COLOR_BOUNDARY,
                           linewidths=1.3, zorder=4)
    ax.set_xticks(range(len(checkpoints)))
    ax.set_xticklabels([CHECKPOINT_LABELS[c] for c in checkpoints], fontsize=6.6)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Fixed-readout accuracy", fontsize=8)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    _style_ax(ax)
    ax.text(0.02, 1.02, "EXP-021 engineering measurement qualification; global_pass = false",
            transform=ax.transAxes, fontsize=6.8, va="bottom", color=COLOR_FIXED)
    ax.text(0.02, 0.965, "Open circles mark checkpoint-level predicted-class coverage failures",
            transform=ax.transAxes, fontsize=6.5, va="bottom", color=COLOR_BOUNDARY)
    fig.tight_layout()
    return fig


def fig04_exp023(exp023: Dict[str, Any]) -> plt.Figure:
    splits = exp023["splits"]
    metrics = {k: v["metrics"] for k, v in splits.items()}
    variants = ["A0", "A_mu", "A_sigma", "A_mu_sigma"]
    split_labels = ["Split A", "Split B"]
    block27 = "block27_pre_final_rmsnorm"
    values = {sk: [metrics[sk][block27][v]["balanced_accuracy"] for v in variants] for sk in splits}
    bootstrap = {sk: splits[sk]["bootstrap"]["G_cal"] for sk in splits}
    primary = {sk: splits[sk]["primary"]["G_cal"] for sk in splits}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0))
    ax0, ax1 = axes

    x = list(range(len(variants)))
    width = 0.36
    for offset, (sk, color, label) in enumerate([
        ("A", COLOR_SPLIT_A, "Split A"),
        ("B", COLOR_SPLIT_B, "Split B"),
    ]):
        ax0.bar([xi + offset * width - width / 2 for xi in x], values[sk], width=width,
                color=color, edgecolor="black", linewidth=0.5, label=label)
    ax0.set_xticks(x)
    ax0.set_xticklabels(["A0", "A_mu", "A_sigma", "A_mu_sigma"], fontsize=7)
    ax0.set_ylim(0, 1.0)
    ax0.set_ylabel("Final-block balanced accuracy", fontsize=7.5)
    ax0.set_xlabel("Readout variant", fontsize=7.5)
    ax0.legend(fontsize=6.8, frameon=False, loc="lower right")
    _style_ax(ax0)
    ax0.set_title("(a) Final-block readout performance", fontsize=8)

    xb = [0, 1]
    est = [primary["A"]["estimate"], primary["B"]["estimate"]]
    lo = [bootstrap["A"]["lower"], bootstrap["B"]["lower"]]
    hi = [bootstrap["A"]["upper"], bootstrap["B"]["upper"]]
    ax1.errorbar(xb, est, yerr=[[est[i] - lo[i] for i in range(2)], [hi[i] - est[i] for i in range(2)]],
                 fmt="o", capsize=4, color=COLOR_FIXED, markersize=5)
    ax1.axhline(0, color="black", linewidth=0.8)
    ax1.set_xticks(xb)
    ax1.set_xticklabels(split_labels, fontsize=7.5)
    ax1.set_ylim(-0.18, 0.48)
    ax1.set_ylabel("G_cal estimate (bootstrap CI)", fontsize=7.5)
    _style_ax(ax1)
    ax1.set_title("(b) Calibration recovery", fontsize=8)
    ax1.text(0.5, 0.12, "Registered cross-split outcome:\nNO_REPLICATION",
             transform=ax1.transAxes, ha="center", va="center", fontsize=7.6,
             color=COLOR_BOUNDARY, bbox=dict(boxstyle="round,pad=0.25", fc="#FFF4EC",
                                             ec=COLOR_BOUNDARY, lw=1.0))

    fig.tight_layout()
    return fig


def fig05_exp024_primary(exp024: Dict[str, Any]) -> plt.Figure:
    cl = exp024["condition_level"]
    order = cl["condition_order"]
    s_diag = [cl["s_diag"][k] for k in order]
    g_eval = [cl["g_eval"][k] for k in order]
    primary = exp024["primary"]

    fig, ax = plt.subplots(figsize=(6.2, 3.4))
    ax.scatter(s_diag, g_eval, s=24, color=COLOR_RECAL, edgecolor="black", linewidth=0.5, zorder=3)
    for i, key in enumerate(order):
        short = key.split("_", 1)[0]
        ax.annotate(short, (s_diag[i], g_eval[i]), textcoords="offset points",
                    xytext=(4, 3), fontsize=6.4, color=COLOR_FIXED)
    ax.set_xlim(0.24, 0.56)
    ax.set_ylim(0.26, 0.56)
    ax.set_xlabel("S_diag(c)", fontsize=8)
    ax.set_ylabel("G_eval(c)", fontsize=8)
    ax.set_xticks([0.30, 0.35, 0.40, 0.45, 0.50])
    ax.set_yticks([0.30, 0.35, 0.40, 0.45, 0.50])
    _style_ax(ax)
    text = (
        "n = 10 conditions\n"
        f"Spearman rho = {primary['rho']}\n"
        f"exact one-sided p = {primary['exact_one_sided_p']}\n"
        "registered support = NOT_SUPPORTED"
    )
    ax.text(0.985, 0.035, text, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=6.6, linespacing=1.25,
            bbox=dict(boxstyle="round,pad=0.35", fc="white", ec=COLOR_BOUNDARY, lw=0.8))
    fig.tight_layout()
    return fig


def fig06_exp024_broad(exp024: Dict[str, Any]) -> plt.Figure:
    cl = exp024["condition_level"]
    order = cl["condition_order"]
    s_diag = [cl["s_diag"][k] for k in order]
    g_eval = [cl["g_eval"][k] for k in order]
    x = list(range(len(order)))

    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    ax.plot(x, s_diag, marker="o", linewidth=0.9, markersize=4.2,
            color=COLOR_RECAL, label="S_diag(c)")
    ax.plot(x, g_eval, marker="s", linewidth=0.9, markersize=4.2,
            color=COLOR_BOUNDARY, label="G_eval(c)")
    for xi in x:
        ax.plot([xi, xi], [s_diag[xi], g_eval[xi]], color="#999999", linewidth=0.5,
                linestyle=":")
    ax.set_xticks(x)
    ax.set_xticklabels([k.split("_", 1)[0] for k in order], fontsize=6.4)
    ax.set_ylim(0, 0.60)
    ax.set_xlabel("Condition (frozen order)", fontsize=8)
    ax.set_ylabel("Condition-level value", fontsize=8)
    ax.legend(fontsize=7, frameon=False, loc="upper right")
    _style_ax(ax)
    ax.text(0.02, 0.96, "10/10 S_diag > 0; 10/10 G_eval > 0",
            transform=ax.transAxes, fontsize=7.2, va="top", color=COLOR_FIXED)
    ax.text(0.02, 0.90, "Descriptive panel observation only; not a confirmatory positivity test",
            transform=ax.transAxes, fontsize=6.6, va="top", color=COLOR_BOUNDARY)
    fig.tight_layout()
    return fig


def generate_figures(data: Dict[str, Any]) -> List[Dict[str, str]]:
    figs = [
        ("fig01_framework", fig01_framework()),
        ("fig02_manipulability", fig02_manipulability(data["exp020a"])),
        ("fig03_fixed_readout_degradation", fig03_fixed_readout(data["exp021"])),
        ("fig04_exp023_heterogeneity", fig04_exp023(data["exp023"])),
        ("fig05_exp024_primary_scatter", fig05_exp024_primary(data["exp024"])),
        ("fig06_exp024_broad_benefit", fig06_exp024_broad(data["exp024"])),
    ]
    out = []
    for stem, fig in figs:
        out.append(save_figure(fig, stem))
    return out


def _fmt_num(value: Any) -> str:
    f = float(value)
    if f == int(f):
        return str(int(f))
    return repr(f)


def write_evidence_table() -> Dict[str, str]:
    rows = [
        ("EXP-018", "Can task-associated representations be locally manipulated under held-out controls?",
         "Frozen task-vs-matched-random/opposite representation movement; independent fit-only probe",
         "Task exceeded matched-random in 216/216 conditions; task exceeded opposite in 216/216 conditions",
         "Local representational manipulability supported at the representation/readout level",
         "No behavioral control or general task conversion"),
        ("EXP-017", "Does representation manipulation produce task-specific behavioral advantage?",
         "Matched-control behavioral endpoint",
         "No demonstrated behavioral control from representation manipulation",
         "Representation manipulability does not automatically imply behavioral control",
         "Behavioral control remains unsupported"),
        ("EXP-019", "Can a general behavioral evaluator detect the expected task-specific effect?",
         "Behavioral evaluator frozen on independent held-out conditions",
         "Evaluator generalization limitation; behavioral endpoint interpretation limited",
         "Behavioral endpoint evidence remains bounded",
         "No general behavioral-control inference"),
        ("EXP-020A", "Does the local manipulability result replicate in a same-family larger model?",
         "Same-family frozen replication gate",
         "`REPRESENTATION_REPLICATION_SUPPORTED`",
         "Same-family larger-model representation replication supported",
         "Not cross-model or cross-task universality"),
        ("EXP-021", "Does a fixed semantic readout lose compatibility at deeper clean checkpoints?",
         "Frozen Stage-Q measurement qualification across checkpoints/splits",
         "Checkpoint-level pass/fail heterogeneity; engineering qualification only",
         "Fixed-readout compatibility is depth/split/condition dependent",
         "Not a universal representation-quality or functional claim"),
        ("EXP-022A", "Can FIT-only featurewise recalibration recover a degraded fixed readout in the discovery experiment?",
         "Discovery split design; fixed readout plus recalibrated variants",
         "`D_fixed = PARTIAL_CONCORDANCE`; `G_refit = SPLIT_HETEROGENEOUS`",
         "Featurewise recalibration is a candidate recovery mechanism in the discovery experiment",
         "Exploratory origin; not an independent confirmatory result"),
        ("EXP-023", "Does featurewise calibration rescue replicate across independent complementary splits?",
         "Independent preregistered replication with Split A and Split B",
         "Cross-split synthesis `G_cal = NO_REPLICATION`",
         "Strong rescue in Split A and null rescue in Split B; no general cross-split calibration claim",
         "Do not pool A/B or relabel as partial replication"),
        ("EXP-024", "Does independent S_diag(c) predict independent G_eval(c) across the 10-condition panel?",
         "Frozen 10-condition independent DIAGNOSTIC/EVAL design; exact permutation test",
         "Primary `NOT_SUPPORTED`; `rho = 0.28401877872187725`, exact one-sided `p = 0.2115079365079365`",
         "Simple independent degradation-magnitude predictor is not supported",
         "10/10 positive S_diag and G_eval are descriptive only"),
    ]
    lines = [
        "# Paper-A Evidence Summary Table",
        "",
        "Canonical source: `experiments/exp018`, `experiments/exp017`, `experiments/exp019`, "
        "`experiments/exp020/results/exp020a_results.json`, `experiments/exp021/engineering/stage_q_result.json`, "
        "`experiments/exp022a/results/exp022a_results.json`, `experiments/exp023/results/exp023_results.json`, "
        "`experiments/exp024/results/exp024_results.json`.",
        "",
        "| Experiment | Scientific Question | Design | Primary Outcome | Interpretation | Boundary |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for exp, q, design, outcome, interp, boundary in rows:
        lines.append(f"| {exp} | {q} | {design} | {outcome} | {interp} | {boundary} |")
    path = TABLE_DIR / "paper_a_evidence_summary.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)}


def write_exp024_condition_table(exp024: Dict[str, Any]) -> Dict[str, str]:
    cl = exp024["condition_level"]
    order = cl["condition_order"]
    primary = exp024["primary"]
    lines = [
        "# EXP-024 Condition Outcomes",
        "",
        "Canonical source: `experiments/exp024/results/exp024_results.json`.",
        "",
        "| Condition ID | Condition | S_diag(c) | G_eval(c) | A0 block16 diagnostic BA | A0 block27 diagnostic BA |",
        "| --- | --- | ---: | ---: | ---: | ---: |",
    ]
    for key in order:
        dba = cl["diagnostic_balanced_accuracy"][key]
        lines.append(
            f"| {key} | {SHORT_CONDITION[key]} | {_fmt_num(cl['s_diag'][key])} | {_fmt_num(cl['g_eval'][key])} | "
            f"{_fmt_num(dba['A0_block16'])} | {_fmt_num(dba['A0_block27'])} |"
        )
    lines.extend([
        "",
        "| Primary summary | Value |",
        "| --- | --- |",
        f"| Spearman rho | {primary['rho']} |",
        f"| Exact one-sided p | {primary['exact_one_sided_p']} |",
        f"| Registered support | {'NOT_SUPPORTED' if not primary['supported'] else 'SUPPORTED'} |",
        "| Scientific unit | condition |",
        "| Condition count | 10 |",
        "",
        "Descriptive panel observation: `S_diag(c) > 0` in 10/10 conditions and "
        "`G_eval(c) > 0` in 10/10 conditions. This is descriptive only; it is not a new "
        "confirmatory positivity test.",
    ])
    md_path = TABLE_DIR / "exp024_condition_outcomes.md"
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    csv_path = TABLE_DIR / "exp024_condition_outcomes.csv"
    csv_lines = ["condition,s_diag,g_eval,A0_block16_diagnostic_BA,A0_block27_diagnostic_BA"]
    for key in order:
        dba = cl["diagnostic_balanced_accuracy"][key]
        csv_lines.append(f"{key},{cl['s_diag'][key]},{cl['g_eval'][key]},"
                         f"{dba['A0_block16']},{dba['A0_block27']}")
    csv_path.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    return {
        "markdown_path": str(md_path.relative_to(ROOT)),
        "markdown_sha256": sha256_file(md_path),
        "csv_path": str(csv_path.relative_to(ROOT)),
        "csv_sha256": sha256_file(csv_path),
    }


def write_manifest(data: Dict[str, Any], hashes: Dict[str, str], figures: List[Dict[str, str]],
                   table1: Dict[str, str], table2: Dict[str, str]) -> Path:
    manifest = {
        "schema_version": "1.0",
        "generated_by": "scripts/paper/generate_paper_a_figures.py",
        "source_files": {key: str(SOURCES[key].relative_to(ROOT)) for key in SOURCES},
        "source_sha256": hashes,
        "figures": figures,
        "tables": [table1, table2],
        "no_new_inferential_tests": True,
    }
    path = FIGURE_DIR / "figure_source_manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> None:
    data, hashes = load_authorities()
    figures = generate_figures(data)
    table1 = write_evidence_table()
    table2 = write_exp024_condition_table(data["exp024"])
    manifest_path = write_manifest(data, hashes, figures, table1, table2)
    print(json.dumps({
        "manifest": str(manifest_path.relative_to(ROOT)),
        "manifest_sha256": sha256_file(manifest_path),
        "figures": [f["stem"] for f in figures],
        "tables": [table1["path"], table2["markdown_path"]],
    }, indent=2))


if __name__ == "__main__":
    main()
