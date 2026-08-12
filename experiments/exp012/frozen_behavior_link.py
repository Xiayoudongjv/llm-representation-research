"""EXP-012: reanalyze group-level representation links with frozen behavior."""

from __future__ import annotations

import argparse
import math
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment_io import load_json, read_csv, save_json, write_csv


GROUPS = ["logic", "causality", "analogy", "definition"]
NOTE = "n=4 groups; exploratory only; no inferential claim"


def parse_args() -> argparse.Namespace:
    """Parse the output location for the offline reanalysis."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", default="results/exp012")
    return parser.parse_args()


def mean(rows: list[dict[str, str]], column: str) -> float:
    """Return a numeric mean for a non-empty CSV subset."""
    return float(np.mean([float(row[column]) for row in rows]))


def correlation(x: list[float], y: list[float]) -> float:
    """Return Pearson r or NaN when a correlation is undefined."""
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def average_ranks(values: list[float]) -> list[float]:
    """Return average ranks with deterministic tie handling."""
    order = sorted(range(len(values)), key=lambda index: values[index])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        rank = (position + end + 2) / 2
        for item_index in range(position, end + 1):
            ranks[order[item_index]] = rank
        position = end + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float:
    """Return Spearman rho via average ranks, or NaN for constant inputs."""
    return correlation(average_ranks(x), average_ranks(y))


def final_invariant_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Select the largest-beta complete EXP-006 metrics row for each transition."""
    grouped: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[(row["source_group"], row["target_group"])].append(row)
    return [max(pair_rows, key=lambda row: float(row["beta"])) for pair_rows in grouped.values()]


def scatter(rows: list[dict[str, object]], x_key: str, output: Path, xlabel: str) -> None:
    """Save an annotated group-level frozen-accuracy scatter plot."""
    figure, axis = plt.subplots(figsize=(7, 5))
    x_values = [float(row[x_key]) for row in rows]
    y_values = [float(row["exp011d_frozen_accuracy"]) for row in rows]
    axis.scatter(x_values, y_values)
    for row, x_value, y_value in zip(rows, x_values, y_values):
        axis.annotate(str(row["group"]), (x_value, y_value))
    axis.set_xlabel(xlabel)
    axis.set_ylabel("EXP-011D frozen accuracy")
    axis.set_title("EXP-012 Frozen Behavior vs Representation Metric")
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def main() -> None:
    """Build frozen-behavior tables, descriptive correlations, and sensitivity."""
    args = parse_args()
    output_dir = ROOT / args.output_dir
    frozen_rows = read_csv(ROOT / "results/exp011d/group_accuracy.csv")
    frozen_accuracy = {row["group"]: float(row["accuracy"]) for row in frozen_rows}
    old_summary = read_csv(ROOT / "results/exp010/group_behavior_representation_summary.csv")
    old_accuracy = {row["group"]: float(row["strict_accuracy"]) for row in old_summary}
    layer_groups = [row for row in read_csv(ROOT / "results/exp003/group_metrics.csv") if int(row["layer"]) == 16]
    pair_rows = read_csv(ROOT / "results/exp005/pair_summary.csv")
    invariant_rows = final_invariant_rows(read_csv(ROOT / "results/exp006/invariant_metrics.csv"))
    layer_by_group = {row["group"]: row for row in layer_groups}

    summary_rows: list[dict[str, object]] = []
    for group in GROUPS:
        incoming_pairs = [row for row in pair_rows if row["target_group"] == group]
        outgoing_pairs = [row for row in pair_rows if row["source_group"] == group]
        incoming_invariants = [row for row in invariant_rows if row["target_group"] == group]
        outgoing_invariants = [row for row in invariant_rows if row["source_group"] == group]
        summary_rows.append({
            "group": group,
            "exp009_old_accuracy": old_accuracy[group],
            "exp011d_frozen_accuracy": frozen_accuracy[group],
            "accuracy_change": frozen_accuracy[group] - old_accuracy[group],
            "layer16_within_similarity": float(layer_by_group[group]["within_similarity"]),
            "mean_incoming_delta_norm": mean(incoming_pairs, "delta_norm"),
            "mean_outgoing_delta_norm": mean(outgoing_pairs, "delta_norm"),
            "mean_incoming_target_minus_source_similarity": mean(incoming_pairs, "final_target_minus_source_similarity"),
            "mean_outgoing_target_minus_source_similarity": mean(outgoing_pairs, "final_target_minus_source_similarity"),
            "mean_incoming_final_ivs": mean(incoming_invariants, "invariant_violation_score"),
            "mean_outgoing_final_ivs": mean(outgoing_invariants, "invariant_violation_score"),
            "mean_incoming_final_rsm_pearson": mean(incoming_invariants, "rsm_pearson"),
            "mean_outgoing_final_rsm_pearson": mean(outgoing_invariants, "rsm_pearson"),
            "mean_incoming_final_relative_perturbation_norm": mean(incoming_invariants, "mean_relative_perturbation_norm"),
            "mean_outgoing_final_relative_perturbation_norm": mean(outgoing_invariants, "mean_relative_perturbation_norm"),
        })
    write_csv(output_dir / "group_behavior_representation_summary.csv", list(summary_rows[0]), summary_rows)

    metrics = [key for key in summary_rows[0] if key not in {"group", "exp009_old_accuracy", "exp011d_frozen_accuracy", "accuracy_change"}]
    frozen_values = [float(row["exp011d_frozen_accuracy"]) for row in summary_rows]
    correlation_rows: list[dict[str, object]] = []
    for metric in metrics:
        values = [float(row[metric]) for row in summary_rows]
        loo = [correlation([value for index, value in enumerate(values) if index != omit], [value for index, value in enumerate(frozen_values) if index != omit]) for omit in range(len(GROUPS))]
        finite_loo = [value for value in loo if not math.isnan(value)]
        signs = {math.copysign(1, value) for value in finite_loo if value != 0}
        correlation_rows.append({
            "metric": metric, "pearson_r": correlation(values, frozen_values), "spearman_rho": spearman(values, frozen_values),
            "n_groups": 4, "loo_min_r": min(finite_loo) if finite_loo else float("nan"),
            "loo_max_r": max(finite_loo) if finite_loo else float("nan"),
            "loo_sign_consistent": len(finite_loo) == 4 and len(signs) <= 1,
            "note": NOTE if np.std(values) != 0 else f"{NOTE}; constant metric",
        })
    write_csv(output_dir / "correlations_frozen_behavior.csv", list(correlation_rows[0]), correlation_rows)

    old_correlations = {row["metric"]: row for row in read_csv(ROOT / "results/exp010/exploratory_correlations.csv")}
    comparison_rows: list[dict[str, object]] = []
    for row in correlation_rows:
        old_value = float(old_correlations[row["metric"]]["pearson_r_with_strict_accuracy"]) if old_correlations[row["metric"]]["pearson_r_with_strict_accuracy"] else float("nan")
        new_value = float(row["pearson_r"])
        changed = not math.isnan(old_value) and not math.isnan(new_value) and old_value * new_value < 0
        delta = abs(new_value - old_value) if not math.isnan(old_value) and not math.isnan(new_value) else float("nan")
        note = "constant or undefined correlation" if math.isnan(delta) else ("sign reversal; benchmark-sensitive descriptive association" if changed else ("large descriptive change" if delta >= 0.30 else "directionally similar only if signs match"))
        comparison_rows.append({"metric": row["metric"], "exp010_pearson_r_old_behavior": old_value, "exp012_pearson_r_frozen_behavior": new_value, "absolute_change": delta, "sign_changed": changed, "ranking_or_interpretation_note": note})
    write_csv(output_dir / "correlation_comparison_exp010_vs_exp012.csv", list(comparison_rows[0]), comparison_rows)

    scatter(summary_rows, "layer16_within_similarity", output_dir / "accuracy_vs_layer16_within_similarity.png", "Layer 16 within similarity")
    scatter(summary_rows, "mean_outgoing_final_ivs", output_dir / "accuracy_vs_outgoing_ivs.png", "Mean outgoing final IVS")
    scatter(summary_rows, "mean_outgoing_delta_norm", output_dir / "accuracy_vs_delta_norm.png", "Mean outgoing delta norm")
    shared = [row for row in comparison_rows if not math.isnan(float(row["absolute_change"]))]
    figure, axis = plt.subplots(figsize=(10, 5))
    x_positions = np.arange(len(shared))
    axis.plot(x_positions, [row["exp010_pearson_r_old_behavior"] for row in shared], marker="o", label="EXP-010 old behavior")
    axis.plot(x_positions, [row["exp012_pearson_r_frozen_behavior"] for row in shared], marker="o", label="EXP-012 frozen behavior")
    axis.set_xticks(x_positions, [row["metric"] for row in shared], rotation=75, ha="right")
    axis.set_ylabel("Pearson r")
    axis.set_title("EXP-010 vs EXP-012 Descriptive Correlations")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "old_vs_frozen_correlations.png")
    plt.close(figure)

    valid = [row for row in correlation_rows if not math.isnan(float(row["pearson_r"]))]
    strongest_positive = max(valid, key=lambda row: float(row["pearson_r"]))
    strongest_negative = min(valid, key=lambda row: float(row["pearson_r"]))
    sign_changes = [row["metric"] for row in comparison_rows if row["sign_changed"]]
    largest_change = max((row for row in comparison_rows if not math.isnan(float(row["absolute_change"]))), key=lambda row: float(row["absolute_change"]))
    summary = {
        "number_of_groups": 4,
        "old_behavior_accuracy_by_group": old_accuracy,
        "frozen_behavior_accuracy_by_group": frozen_accuracy,
        "old_group_ranking": [group for group, _ in sorted(old_accuracy.items(), key=lambda item: item[1], reverse=True)],
        "frozen_group_ranking": [group for group, _ in sorted(frozen_accuracy.items(), key=lambda item: item[1], reverse=True)],
        "strongest_positive_pearson_metric": {"metric": strongest_positive["metric"], "pearson_r": strongest_positive["pearson_r"], "spearman_rho": strongest_positive["spearman_rho"]},
        "strongest_negative_pearson_metric": {"metric": strongest_negative["metric"], "pearson_r": strongest_negative["pearson_r"], "spearman_rho": strongest_negative["spearman_rho"]},
        "metrics_with_sign_change_vs_exp010": sign_changes,
        "largest_absolute_correlation_change": largest_change,
        "metrics_with_loo_sign_consistency": [row["metric"] for row in correlation_rows if row["loo_sign_consistent"]],
        "warning": "n=4 groups is too small for reliable representation-behavior inference.",
        "interpretation": "EXP-010 descriptive correlations are benchmark-sensitive when behavior is replaced with EXP-011D. Any apparent association remains descriptive only; representation metrics do not explain behavior by themselves.",
    }
    save_json(summary, output_dir / "frozen_behavior_link_summary.json")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
