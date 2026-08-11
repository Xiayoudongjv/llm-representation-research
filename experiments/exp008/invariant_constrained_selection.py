"""EXP-008: select invariant-aware steering betas from existing metrics."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--invariant_metrics_path", default="results/exp006/invariant_metrics.csv")
    parser.add_argument("--frontier_summary_path", default="results/exp007/frontier_summary.csv")
    parser.add_argument("--output_dir", default="results/exp008")
    parser.add_argument("--lambda_values", default="1,5,10,20,50,100")
    parser.add_argument("--gamma_values", default="0,0.05,0.1,0.2")
    return parser.parse_args()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def parse_values(value: str) -> list[float]:
    return [float(item.strip()) for item in value.split(",") if item.strip()]


def fmt(value: float) -> str:
    return f"{value:g}"


def plot_lines(
    rows: list[dict[str, float]],
    lambdas: list[float],
    gammas: list[float],
    value_key: str,
    ylabel: str,
    title: str,
    output_path: Path,
) -> None:
    figure, axis = plt.subplots(figsize=(9, 6))
    for gamma in gammas:
        values = [
            float(np.mean([
                row[value_key]
                for row in rows
                if row["lambda"] == lambda_value and row["gamma"] == gamma
            ]))
            for lambda_value in lambdas
        ]
        axis.plot(lambdas, values, marker="o", label=f"gamma={fmt(gamma)}")
    axis.set_xlabel("Lambda")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.set_xticks(lambdas)
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    invariant_path = Path(args.invariant_metrics_path)
    frontier_path = Path(args.frontier_summary_path)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    lambda_values = parse_values(args.lambda_values)
    gamma_values = parse_values(args.gamma_values)

    metric_rows = load_csv(invariant_path)
    frontier_rows = load_csv(frontier_path)
    frontier_by_pair = {
        (row["source_group"], row["target_group"]): row for row in frontier_rows
    }
    records_by_pair: dict[tuple[str, str], list[dict[str, float | str]]] = {}
    for row in metric_rows:
        pair = (row["source_group"], row["target_group"])
        record: dict[str, float | str] = {
            "source_group": pair[0],
            "target_group": pair[1],
            "beta": float(row["beta"]),
            "target_assignment_rate": float(row["target_assignment_rate"]),
            "invariant_violation_score": float(row["invariant_violation_score"]),
            "rsm_pearson": float(row["rsm_pearson"]),
            "mean_relative_perturbation_norm": float(row["mean_relative_perturbation_norm"]),
        }
        records_by_pair.setdefault(pair, []).append(record)

    score_header = [
        "source_group", "target_group", "beta", "lambda", "gamma",
        "target_assignment_rate", "invariant_violation_score", "rsm_pearson",
        "mean_relative_perturbation_norm", "constraint_score",
    ]
    score_rows: list[list[object]] = []
    scored_rows: list[dict[str, float]] = []
    for pair, records in records_by_pair.items():
        for lambda_value in lambda_values:
            for gamma_value in gamma_values:
                for record in records:
                    score = (
                        float(record["target_assignment_rate"])
                        - lambda_value * float(record["invariant_violation_score"])
                        - gamma_value * float(record["mean_relative_perturbation_norm"])
                    )
                    scored = {
                        "source_group": pair[0], "target_group": pair[1],
                        "beta": float(record["beta"]), "lambda": lambda_value,
                        "gamma": gamma_value,
                        "target_assignment_rate": float(record["target_assignment_rate"]),
                        "invariant_violation_score": float(record["invariant_violation_score"]),
                        "rsm_pearson": float(record["rsm_pearson"]),
                        "mean_relative_perturbation_norm": float(record["mean_relative_perturbation_norm"]),
                        "constraint_score": score,
                    }
                    scored_rows.append(scored)
                    score_rows.append([scored[column] for column in score_header])
    write_csv(output_dir / "constrained_selection_scores.csv", score_header, score_rows)

    summary_header = [
        "source_group", "target_group", "lambda", "gamma", "selected_beta",
        "selected_assignment_rate", "selected_ivs", "selected_rsm_pearson",
        "selected_relative_perturbation", "baseline_frontier_beta",
        "baseline_assignment_rate", "baseline_ivs", "baseline_rsm_pearson",
        "baseline_relative_perturbation", "delta_ivs_vs_baseline",
        "delta_perturbation_vs_baseline", "delta_assignment_vs_baseline",
    ]
    pair_summary_rows: list[list[object]] = []
    selected_summary: list[dict[str, float]] = []
    for pair, records in records_by_pair.items():
        frontier = frontier_by_pair[pair]
        baseline_beta = float(frontier["recommended_beta"])
        baseline = min(records, key=lambda record: abs(float(record["beta"]) - baseline_beta))
        for lambda_value in lambda_values:
            for gamma_value in gamma_values:
                candidates = [
                    row for row in scored_rows
                    if row["source_group"] == pair[0]
                    and row["target_group"] == pair[1]
                    and row["lambda"] == lambda_value
                    and row["gamma"] == gamma_value
                ]
                selected = min(candidates, key=lambda row: (-row["constraint_score"], row["beta"]))
                summary = {
                    "source_group": pair[0], "target_group": pair[1],
                    "lambda": lambda_value, "gamma": gamma_value,
                    "selected_beta": selected["beta"],
                    "selected_assignment_rate": selected["target_assignment_rate"],
                    "selected_ivs": selected["invariant_violation_score"],
                    "selected_rsm_pearson": selected["rsm_pearson"],
                    "selected_relative_perturbation": selected["mean_relative_perturbation_norm"],
                    "baseline_frontier_beta": baseline_beta,
                    "baseline_assignment_rate": float(baseline["target_assignment_rate"]),
                    "baseline_ivs": float(baseline["invariant_violation_score"]),
                    "baseline_rsm_pearson": float(baseline["rsm_pearson"]),
                    "baseline_relative_perturbation": float(baseline["mean_relative_perturbation_norm"]),
                    "delta_ivs_vs_baseline": selected["invariant_violation_score"] - float(baseline["invariant_violation_score"]),
                    "delta_perturbation_vs_baseline": selected["mean_relative_perturbation_norm"] - float(baseline["mean_relative_perturbation_norm"]),
                    "delta_assignment_vs_baseline": selected["target_assignment_rate"] - float(baseline["target_assignment_rate"]),
                }
                selected_summary.append(summary)
                pair_summary_rows.append([summary[column] for column in summary_header])
    write_csv(output_dir / "constrained_pair_summary.csv", summary_header, pair_summary_rows)

    aggregate_header = [
        "lambda", "gamma", "mean_selected_beta", "mean_assignment_rate", "mean_ivs",
        "mean_rsm_pearson", "mean_relative_perturbation", "mean_delta_ivs_vs_baseline",
        "mean_delta_perturbation_vs_baseline", "mean_delta_assignment_vs_baseline",
        "num_pairs_assignment_1", "num_pairs_assignment_ge_0_5",
    ]
    aggregate_rows: list[list[object]] = []
    aggregate_records: list[dict[str, float]] = []
    for lambda_value in lambda_values:
        for gamma_value in gamma_values:
            rows = [row for row in selected_summary if row["lambda"] == lambda_value and row["gamma"] == gamma_value]
            aggregate = {
                "lambda": lambda_value, "gamma": gamma_value,
                "mean_selected_beta": float(np.mean([row["selected_beta"] for row in rows])),
                "mean_assignment_rate": float(np.mean([row["selected_assignment_rate"] for row in rows])),
                "mean_ivs": float(np.mean([row["selected_ivs"] for row in rows])),
                "mean_rsm_pearson": float(np.mean([row["selected_rsm_pearson"] for row in rows])),
                "mean_relative_perturbation": float(np.mean([row["selected_relative_perturbation"] for row in rows])),
                "mean_delta_ivs_vs_baseline": float(np.mean([row["delta_ivs_vs_baseline"] for row in rows])),
                "mean_delta_perturbation_vs_baseline": float(np.mean([row["delta_perturbation_vs_baseline"] for row in rows])),
                "mean_delta_assignment_vs_baseline": float(np.mean([row["delta_assignment_vs_baseline"] for row in rows])),
                "num_pairs_assignment_1": sum(row["selected_assignment_rate"] >= 1.0 - 1e-12 for row in rows),
                "num_pairs_assignment_ge_0_5": sum(row["selected_assignment_rate"] >= 0.5 for row in rows),
            }
            aggregate_records.append(aggregate)
            aggregate_rows.append([aggregate[column] for column in aggregate_header])
    write_csv(output_dir / "constrained_aggregate_summary.csv", aggregate_header, aggregate_rows)

    for value_key, ylabel, title, filename in [
        ("mean_ivs", "Mean IVS", "EXP-008 Mean IVS by Lambda and Gamma", "mean_ivs_by_lambda_gamma.png"),
        ("mean_assignment_rate", "Mean assignment rate", "EXP-008 Mean Assignment by Lambda and Gamma", "mean_assignment_by_lambda_gamma.png"),
        ("mean_relative_perturbation", "Mean relative perturbation", "EXP-008 Mean Perturbation by Lambda and Gamma", "mean_perturbation_by_lambda_gamma.png"),
    ]:
        plot_lines(aggregate_records, lambda_values, gamma_values, value_key, ylabel, title, output_dir / filename)

    matrix = np.array([
        [next(row["mean_selected_beta"] for row in aggregate_records if row["lambda"] == lambda_value and row["gamma"] == gamma_value) for lambda_value in lambda_values]
        for gamma_value in gamma_values
    ])
    figure, axis = plt.subplots(figsize=(9, 6))
    image = axis.imshow(matrix, aspect="auto")
    axis.set_xticks(range(len(lambda_values)), [fmt(value) for value in lambda_values])
    axis.set_yticks(range(len(gamma_values)), [fmt(value) for value in gamma_values])
    axis.set_xlabel("Lambda")
    axis.set_ylabel("Gamma")
    axis.set_title("EXP-008 Mean Selected Beta")
    figure.colorbar(image, ax=axis, label="Mean selected beta")
    figure.tight_layout()
    figure.savefig(output_dir / "beta_selection_heatmap_lambda_gamma.png")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 6))
    axis.scatter([row["selected_ivs"] for row in selected_summary], [row["selected_assignment_rate"] for row in selected_summary])
    axis.set_xlabel("Selected invariant violation score")
    axis.set_ylabel("Selected target assignment rate")
    axis.set_title("EXP-008 Constrained Assignment vs IVS")
    figure.tight_layout()
    figure.savefig(output_dir / "assignment_vs_ivs_constrained.png")
    plt.close(figure)

    metadata = {
        "input_files": {
            "invariant_metrics": str(invariant_path),
            "frontier_summary": str(frontier_path),
        },
        "lambda_values": lambda_values,
        "gamma_values": gamma_values,
        "number_of_pairs": len(records_by_pair),
        "note": "This is beta selection over discrete candidates, not learned steering.",
        "invariant_note": "RSM correlation is used only as a proxy invariant.",
        "analysis_note": "This is representation-level analysis only; it is not generation-time evaluation.",
    }
    (output_dir / "invariant_constrained_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
