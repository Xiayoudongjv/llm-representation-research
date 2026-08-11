"""EXP-007: analyze the transition-validity frontier from EXP-006 results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tradeoff_path", default="results/exp006/transition_invariant_tradeoff.csv")
    parser.add_argument("--pair_summary_path", default="results/exp006/invariant_pair_summary.csv")
    parser.add_argument("--output_dir", default="results/exp007")
    parser.add_argument("--lambda_values", default="0,1,5,10,20,50,100")
    return parser.parse_args()


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def _fmt(value):
    return "" if value is None else value


def _plot_line(x, series: dict[str, list[float]], path: Path, ylabel: str, title: str) -> None:
    figure, axis = plt.subplots(figsize=(9, 6))
    for label, values in series.items():
        axis.plot(x, values, marker="o", label=label)
    axis.set_xlabel("Beta")
    axis.set_ylabel(ylabel)
    axis.set_title(title)
    axis.set_xticks(x)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path)
    plt.close(figure)


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    tradeoff_rows = _load_csv(Path(args.tradeoff_path))
    pair_summary_rows = _load_csv(Path(args.pair_summary_path))
    lambda_values = [float(value.strip()) for value in args.lambda_values.split(",") if value.strip()]
    groups_by_pair = {}
    for row in tradeoff_rows:
        pair = (row["source_group"], row["target_group"])
        record = {
            "source_group": pair[0],
            "target_group": pair[1],
            "beta": float(row["beta"]),
            "target_assignment_rate": float(row["target_assignment_rate"]),
            "target_minus_source_similarity": float(row["target_minus_source_similarity"]),
            "invariant_violation_score": float(row["invariant_violation_score"]),
            "rsm_pearson": float(row["rsm_pearson"]),
            "mean_relative_perturbation_norm": float(row["mean_relative_perturbation_norm"]),
        }
        record["success_minus_violation"] = record["target_assignment_rate"] - record["invariant_violation_score"]
        record["success_minus_perturbation"] = record["target_assignment_rate"] - record["mean_relative_perturbation_norm"]
        record["balanced_validity_score"] = record["target_assignment_rate"] - record["invariant_violation_score"] - 0.1 * record["mean_relative_perturbation_norm"]
        for lambda_value in lambda_values:
            record[f"validity_score_lambda_{lambda_value:g}"] = record["target_assignment_rate"] - lambda_value * record["invariant_violation_score"]
        groups_by_pair.setdefault(pair, []).append(record)

    score_header = ["source_group", "target_group", "beta", "target_assignment_rate", "target_minus_source_similarity", "invariant_violation_score", "rsm_pearson", "mean_relative_perturbation_norm", "success_minus_violation", "success_minus_perturbation", "balanced_validity_score"] + [f"validity_score_lambda_{lambda_value:g}" for lambda_value in lambda_values]
    score_rows = []
    for row in tradeoff_rows:
        pair = (row["source_group"], row["target_group"])
        record = next(item for item in groups_by_pair[pair] if item["beta"] == float(row["beta"]))
        score_rows.append([record[column] for column in score_header])

    frontier_header = ["source_group", "target_group", "minimal_beta_assignment_ge_0_5", "minimal_beta_assignment_ge_1", "beta_max_success_minus_violation", "beta_max_balanced_validity", "beta_min_ivs_given_assignment_1", "beta_min_perturbation_given_assignment_1", "recommended_beta", "recommended_reason", "assignment_at_recommended_beta", "ivs_at_recommended_beta", "rsm_pearson_at_recommended_beta", "relative_perturbation_at_recommended_beta"]
    frontier_rows = []
    recommended_records = []
    for pair, records in groups_by_pair.items():
        records = sorted(records, key=lambda item: item["beta"])
        assignment_half = [row for row in records if row["target_assignment_rate"] >= 0.5]
        assignment_one = [row for row in records if row["target_assignment_rate"] >= 1.0 - 1e-12]
        min_half = min(assignment_half, key=lambda row: row["beta"]) if assignment_half else None
        min_one = min(assignment_one, key=lambda row: row["beta"]) if assignment_one else None
        max_success = max(records, key=lambda row: row["success_minus_violation"])
        max_balanced = max(records, key=lambda row: row["balanced_validity_score"])
        min_ivs = min(assignment_one, key=lambda row: (row["invariant_violation_score"], row["beta"])) if assignment_one else None
        min_perturbation = min(assignment_one, key=lambda row: (row["mean_relative_perturbation_norm"], row["beta"])) if assignment_one else None
        if min_ivs is not None:
            recommended = min_ivs
            reason = "minimum IVS among beta values with assignment rate 1.0"
        elif min_half is not None:
            recommended = min_half
            reason = "minimum beta with assignment rate at least 0.5"
        else:
            recommended = max_balanced
            reason = "maximum balanced validity because assignment rate 0.5 was not reached"
        recommended_records.append(recommended)
        frontier_rows.append([pair[0], pair[1], min_half["beta"] if min_half else None, min_one["beta"] if min_one else None, max_success["beta"], max_balanced["beta"], min_ivs["beta"] if min_ivs else None, min_perturbation["beta"] if min_perturbation else None, recommended["beta"], reason, recommended["target_assignment_rate"], recommended["invariant_violation_score"], recommended["rsm_pearson"], recommended["mean_relative_perturbation_norm"]])

    output_dir.mkdir(parents=True, exist_ok=True)
    _write_csv(output_dir / "validity_scores.csv", score_header, score_rows)
    _write_csv(output_dir / "frontier_summary.csv", frontier_header, frontier_rows)

    recommended_betas = [record["beta"] for record in recommended_records]
    beta_counter = Counter(str(beta).rstrip("0").rstrip(".") if beta % 1 else str(int(beta)) for beta in recommended_betas)
    most_common_beta, _ = beta_counter.most_common(1)[0]
    aggregate = {
        "number_of_pairs": len(pair_summary_rows),
        "beta_counts_for_recommended_beta": dict(beta_counter),
        "mean_recommended_beta": float(np.mean(recommended_betas)),
        "mean_assignment_at_recommended_beta": float(np.mean([record["target_assignment_rate"] for record in recommended_records])),
        "mean_ivs_at_recommended_beta": float(np.mean([record["invariant_violation_score"] for record in recommended_records])),
        "mean_rsm_pearson_at_recommended_beta": float(np.mean([record["rsm_pearson"] for record in recommended_records])),
        "mean_relative_perturbation_at_recommended_beta": float(np.mean([record["mean_relative_perturbation_norm"] for record in recommended_records])),
        "most_common_recommended_beta": float(most_common_beta),
        "note": "This is an exploratory frontier analysis; the scalar validity scores are not final theoretical definitions.",
    }
    (output_dir / "aggregate_validity_summary.json").write_text(json.dumps(aggregate, indent=2) + "\n", encoding="utf-8")

    all_records = [record for records in groups_by_pair.values() for record in records]
    _plot_line(
        sorted({record["beta"] for record in all_records}),
        {
            "target assignment rate": [np.mean([record["target_assignment_rate"] for record in all_records if record["beta"] == beta]) for beta in sorted({record["beta"] for record in all_records})],
            "success minus violation": [np.mean([record["success_minus_violation"] for record in all_records if record["beta"] == beta]) for beta in sorted({record["beta"] for record in all_records})],
            "balanced validity score": [np.mean([record["balanced_validity_score"] for record in all_records if record["beta"] == beta]) for beta in sorted({record["beta"] for record in all_records})],
        }, output_dir / "mean_validity_by_beta.png", "Mean score", "EXP-007 Mean Validity by Beta",
    )
    betas = sorted({record["beta"] for record in all_records})
    _plot_line(betas, {
        "invariant violation score": [np.mean([record["invariant_violation_score"] for record in all_records if record["beta"] == beta]) for beta in betas],
        "relative perturbation norm": [np.mean([record["mean_relative_perturbation_norm"] for record in all_records if record["beta"] == beta]) for beta in betas],
    }, output_dir / "mean_ivs_and_perturbation_by_beta.png", "Mean value", "EXP-007 IVS and Perturbation by Beta")

    figure, axis = plt.subplots(figsize=(9, 6))
    axis.scatter([record["invariant_violation_score"] for record in all_records], [record["target_assignment_rate"] for record in all_records])
    axis.set_xlabel("Invariant violation score")
    axis.set_ylabel("Target assignment rate")
    axis.set_title("EXP-007 Validity Frontier")
    figure.tight_layout()
    figure.savefig(output_dir / "validity_frontier_scatter.png")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 6))
    axis.hist(recommended_betas, bins=np.arange(min(recommended_betas) - 0.125, max(recommended_betas) + 0.376, 0.25))
    axis.set_xlabel("Recommended beta")
    axis.set_ylabel("Number of pairs")
    axis.set_title("EXP-007 Recommended Beta")
    figure.tight_layout()
    figure.savefig(output_dir / "beta_recommendation_histogram.png")
    plt.close(figure)
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
