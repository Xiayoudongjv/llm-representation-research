"""EXP-010: exploratory group-level links between representation metrics and accuracy."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


GROUPS = ["logic", "causality", "analogy", "definition"]
ROOT = Path(__file__).resolve().parents[2]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output_dir", default="results/exp010")
    return parser.parse_args()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def mean(rows: list[dict[str, str]], column: str) -> float:
    return float(np.mean([float(row[column]) for row in rows]))


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def pearson(values: list[float], accuracy: list[float]) -> float | None:
    if len(values) < 2 or np.std(values) == 0 or np.std(accuracy) == 0:
        return None
    return float(np.corrcoef(values, accuracy)[0, 1])


def min_max(values: list[float]) -> list[float]:
    low, high = min(values), max(values)
    if high == low:
        return [0.5 for _ in values]
    return [(value - low) / (high - low) for value in values]


def main() -> None:
    args = parse_args()
    output_dir = ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    behavior_rows = load_csv(ROOT / "results/exp009b/group_accuracy_comparison.csv")
    layer_group_rows = [row for row in load_csv(ROOT / "results/exp003/group_metrics.csv") if int(row["layer"]) == 16]
    layer_rows = [row for row in load_csv(ROOT / "results/exp003/layer_metrics.csv") if int(row["layer"]) == 16]
    pair_rows = load_csv(ROOT / "results/exp005/pair_summary.csv")
    invariant_rows = load_csv(ROOT / "results/exp006/invariant_pair_summary.csv")
    invariant_metric_rows = load_csv(ROOT / "results/exp006/invariant_metrics.csv")

    if len(layer_rows) != 1 or len(behavior_rows) != 4:
        raise ValueError("Expected one EXP-003 layer-16 row and four behavior groups.")
    layer = layer_rows[0]
    behavior_by_group = {row["group"]: row for row in behavior_rows}
    layer_by_group = {row["group"]: row for row in layer_group_rows}
    summary_rows = []
    for group in GROUPS:
        incoming = [row for row in pair_rows if row["target_group"] == group]
        outgoing = [row for row in pair_rows if row["source_group"] == group]
        # The checked-in EXP-006 pair summary has truncated final columns.
        # Use the complete invariant metrics at the final tested beta for these
        # aggregates, while still loading the pair summary as a required input.
        final_invariant_rows = []
        for source_group, target_group in {(row["source_group"], row["target_group"]) for row in invariant_metric_rows}:
            pair_metrics = [
                row for row in invariant_metric_rows
                if row["source_group"] == source_group and row["target_group"] == target_group
            ]
            final_invariant_rows.append(max(pair_metrics, key=lambda row: float(row["beta"])))
        invariant_incoming = [row for row in final_invariant_rows if row["target_group"] == group]
        invariant_outgoing = [row for row in final_invariant_rows if row["source_group"] == group]
        summary_rows.append({
            "group": group,
            "strict_accuracy": float(behavior_by_group[group]["strict_accuracy"]),
            "audited_upper_bound_accuracy": float(behavior_by_group[group]["audited_upper_bound_accuracy"]),
            "layer16_within_similarity": float(layer_by_group[group]["within_similarity"]),
            "layer16_separation_score": float(layer["separation_score"]),
            "layer16_silhouette_score": float(layer["silhouette_score"]),
            "layer16_paraphrase_retention_score": float(layer["paraphrase_retention_score"]),
            "mean_incoming_delta_norm": mean(incoming, "delta_norm"),
            "mean_outgoing_delta_norm": mean(outgoing, "delta_norm"),
            "mean_incoming_final_target_assignment_rate": mean(incoming, "final_target_assignment_rate"),
            "mean_outgoing_final_target_assignment_rate": mean(outgoing, "final_target_assignment_rate"),
            "mean_incoming_target_minus_source_similarity": mean(incoming, "final_target_minus_source_similarity"),
            "mean_outgoing_target_minus_source_similarity": mean(outgoing, "final_target_minus_source_similarity"),
            "mean_outgoing_final_ivs": mean(invariant_outgoing, "invariant_violation_score"),
            "mean_incoming_final_ivs": mean(invariant_incoming, "invariant_violation_score"),
            "mean_outgoing_final_rsm_pearson": mean(invariant_outgoing, "rsm_pearson"),
            "mean_incoming_final_rsm_pearson": mean(invariant_incoming, "rsm_pearson"),
            "mean_outgoing_final_relative_perturbation_norm": mean(invariant_outgoing, "mean_relative_perturbation_norm"),
            "mean_incoming_final_relative_perturbation_norm": mean(invariant_incoming, "mean_relative_perturbation_norm"),
        })

    summary_header = list(summary_rows[0])
    write_csv(output_dir / "group_behavior_representation_summary.csv", summary_header, [[row[column] for column in summary_header] for row in summary_rows])

    strict_accuracy = [row["strict_accuracy"] for row in summary_rows]
    audited_accuracy = [row["audited_upper_bound_accuracy"] for row in summary_rows]
    metric_columns = [column for column in summary_header if column not in {"group", "strict_accuracy", "audited_upper_bound_accuracy"}]
    correlations = []
    for metric in metric_columns:
        values = [row[metric] for row in summary_rows]
        correlations.append([
            metric,
            pearson(values, strict_accuracy),
            pearson(values, audited_accuracy),
            "n=4 groups; exploratory only; correlation is non-causal and underpowered",
        ])
    write_csv(output_dir / "exploratory_correlations.csv", ["metric", "pearson_r_with_strict_accuracy", "pearson_r_with_audited_accuracy", "note"], correlations)

    valid_correlations = [(row[0], row[1]) for row in correlations if row[1] is not None]
    strongest_positive = max(valid_correlations, key=lambda item: item[1])
    strongest_negative = min(valid_correlations, key=lambda item: item[1])
    summary = {
        "number_of_groups": len(summary_rows),
        "strict_accuracy_by_group": {row["group"]: row["strict_accuracy"] for row in summary_rows},
        "audited_accuracy_by_group": {row["group"]: row["audited_upper_bound_accuracy"] for row in summary_rows},
        "strongest_positive_correlation_metric": {"metric": strongest_positive[0], "pearson_r": strongest_positive[1]},
        "strongest_negative_correlation_metric": {"metric": strongest_negative[0], "pearson_r": strongest_negative[1]},
        "warning": "n=4 is too small for reliable inference.",
        "note": "Exploratory, non-causal group-level correlation analysis; representation metrics do not explain behavior by themselves.",
    }
    (output_dir / "representation_behavior_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    def scatter(x_key: str, filename: str, xlabel: str) -> None:
        figure, axis = plt.subplots(figsize=(7, 5))
        axis.scatter([row[x_key] for row in summary_rows], strict_accuracy)
        for row in summary_rows:
            axis.annotate(row["group"], (row[x_key], row["strict_accuracy"]))
        axis.set_xlabel(xlabel)
        axis.set_ylabel("Strict accuracy")
        axis.set_title("EXP-010 Accuracy vs Representation Metric")
        figure.tight_layout()
        figure.savefig(output_dir / filename)
        plt.close(figure)

    scatter("layer16_within_similarity", "accuracy_vs_layer16_within_similarity.png", "Layer 16 within similarity")
    scatter("mean_outgoing_final_ivs", "accuracy_vs_outgoing_ivs.png", "Mean outgoing final IVS")
    scatter("mean_outgoing_delta_norm", "accuracy_vs_delta_norm.png", "Mean outgoing delta norm")

    selected_metrics = {
        "strict_accuracy": strict_accuracy,
        "layer16_within_similarity": [row["layer16_within_similarity"] for row in summary_rows],
        "mean_outgoing_final_ivs": [row["mean_outgoing_final_ivs"] for row in summary_rows],
        "mean_outgoing_delta_norm": [row["mean_outgoing_delta_norm"] for row in summary_rows],
    }
    figure, axis = plt.subplots(figsize=(9, 5))
    x = np.arange(len(GROUPS))
    for name, values in selected_metrics.items():
        axis.plot(x, min_max(values), marker="o", label=name)
    axis.set_xticks(x, GROUPS)
    axis.set_xlabel("Group")
    axis.set_ylabel("Min-max normalized value")
    axis.set_title("EXP-010 Accuracy and Selected Representation Metrics")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "group_accuracy_with_rep_metrics.png")
    plt.close(figure)
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
