"""Conservatively audit existing EXP-011B answer scoring without model use."""

from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.experiment_io import read_csv, save_json, write_csv


GROUPS = ["logic", "causality", "analogy", "definition"]
LABELS = ["strict_correct", "likely_correct_scoring_miss", "partially_correct", "ambiguous", "likely_wrong"]
Z_95 = 1.959963984540054
INPUT_PATH = ROOT / "results/exp011b/answer_eval_results.csv"
OUTPUT_DIR = ROOT / "results/exp011c"

# Each override is a conservative manual decision for an existing strict failure.
OVERRIDES = {
    "exp011_logic_002": ("likely_correct_scoring_miss", "The response directly states the required negative conclusion.", "not a mammal"),
    "exp011_logic_003": ("partially_correct", "It states the derived property instead of the requested yes/no answer.", ""),
    "exp011_logic_005": ("likely_wrong", "It gives the opposite of the required conclusion.", ""),
    "exp011_logic_009": ("likely_wrong", "It gives the opposite of the required conclusion.", ""),
    "exp011_logic_014": ("likely_wrong", "It repeats the antecedent rather than answering the negative conclusion.", ""),
    "exp011_logic_020": ("likely_wrong", "It gives the opposite of the required conclusion.", ""),
    "exp011_causality_003": ("likely_correct_scoring_miss", "'melts' is a direct inflectional variant of the accepted effect.", "melts"),
    "exp011_causality_004": ("likely_correct_scoring_miss", "The response expresses the same lamp-on effect with harmless word-order variation.", "turn the lamp on"),
    "exp011_causality_005": ("likely_correct_scoring_miss", "The response states the same computer-shutdown effect with an infinitive form.", "computer to shut down"),
    "exp011_causality_006": ("likely_wrong", "It names the process rather than the stated cause, sunlight.", ""),
    "exp011_causality_007": ("likely_correct_scoring_miss", "'freezes' is a direct inflectional variant of the accepted effect.", "freezes"),
    "exp011_causality_008": ("likely_correct_scoring_miss", "The pronoun refers directly to the glass in the explicit question.", "it breaks"),
    "exp011_causality_017": ("likely_correct_scoring_miss", "It expresses the same explicitly stated wet-soil effect.", "make it wet"),
    "exp011_causality_019": ("likely_correct_scoring_miss", "It expresses the same water-flow-stopping effect.", "stop the water flow"),
    "exp011_analogy_003": ("partially_correct", "Shelter is related to a kennel but does not provide the intended specific relation.", ""),
    "exp011_analogy_004": ("ambiguous", "Shoe is a defensible foot covering, although it differs from the intended glove-to-sock relation.", ""),
    "exp011_analogy_006": ("likely_wrong", "It supplies an object instead of the requested activity.", ""),
    "exp011_analogy_009": ("likely_wrong", "Patient is not the analogous workplace answer.", ""),
    "exp011_analogy_010": ("partially_correct", "A refrigerator stores items, but that is not the intended appliance function.", ""),
    "exp011_analogy_012": ("ambiguous", "An access code is related to a password but is not clearly interchangeable here.", ""),
    "exp011_analogy_016": ("likely_wrong", "Cut is not the analogous needle function.", ""),
    "exp011_analogy_017": ("partially_correct", "It recognizes an animal-group relation but gives the wrong group term.", ""),
    "exp011_analogy_018": ("likely_wrong", "Performer is not the analogous creator-product answer.", ""),
    "exp011_analogy_019": ("partially_correct", "A unit relates to measurement but does not name the measured quantity.", ""),
    "exp011_analogy_020": ("partially_correct", "Aircraft is related to a pilot but is not the intended workplace.", ""),
    "exp011_definition_005": ("partially_correct", "Builder is related but is not conventionally equivalent to architect.", ""),
    "exp011_definition_018": ("likely_wrong", "Knife is a different paper-cutting tool.", ""),
    "exp011_definition_020": ("ambiguous", "Froglet can describe a young frog, though it differs from the intended developmental term.", ""),
}


def wilson(correct: int, total: int) -> tuple[float, float]:
    """Return a descriptive 95% Wilson interval."""
    p = correct / total
    denominator = 1 + Z_95**2 / total
    center = (p + Z_95**2 / (2 * total)) / denominator
    margin = Z_95 * math.sqrt((p * (1 - p) + Z_95**2 / (4 * total)) / total) / denominator
    return center - margin, center + margin


def audit_row(row: dict[str, str]) -> dict[str, object]:
    """Apply the documented conservative audit label to one result row."""
    strict = row["is_correct"].lower() == "true"
    if strict:
        label, reason, candidate = "strict_correct", "Accepted by the existing boundary-aware scoring rule.", ""
    else:
        label, reason, candidate = OVERRIDES[row["id"]]
    return {
        "id": row["id"], "group": row["group"], "question": row["question"],
        "expected_answer": row["expected_answer"], "acceptable_answers": row["acceptable_answers"],
        "model_answer": row["model_answer"], "normalized_model_answer": row["normalized_model_answer"],
        "strict_is_correct": strict, "audit_label": label, "audit_reason": reason,
        "candidate_new_acceptable_answer": candidate,
        "recommend_dataset_update": label == "likely_correct_scoring_miss",
    }


def group_metrics(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    """Aggregate strict and audited metrics with Wilson intervals by group."""
    metrics = []
    for group in GROUPS:
        subset = [row for row in rows if row["group"] == group]
        counts = Counter(row["audit_label"] for row in subset)
        strict = counts["strict_correct"]
        audited = strict + counts["likely_correct_scoring_miss"]
        low_strict, high_strict = wilson(strict, len(subset))
        low_audited, high_audited = wilson(audited, len(subset))
        metrics.append({
            "group": group, "total": len(subset), **{label: counts[label] for label in LABELS},
            "strict_accuracy": strict / len(subset), "conservative_audited_accuracy": audited / len(subset),
            "review_ceiling": (audited + counts["partially_correct"] + counts["ambiguous"]) / len(subset),
            "strict_ci95_low": low_strict, "strict_ci95_high": high_strict,
            "audited_ci95_low": low_audited, "audited_ci95_high": high_audited,
        })
    return metrics


def save_plot(metrics: list[dict[str, object]]) -> None:
    """Save default-style side-by-side strict and audited group accuracy bars."""
    positions = list(range(len(metrics)))
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.bar([value - 0.2 for value in positions], [row["strict_accuracy"] for row in metrics], width=0.4, label="Strict")
    axis.bar([value + 0.2 for value in positions], [row["conservative_audited_accuracy"] for row in metrics], width=0.4, label="Conservative audited")
    axis.set_xticks(positions, [row["group"] for row in metrics])
    axis.set_ylim(0, 1)
    axis.set_ylabel("Accuracy")
    axis.set_title("EXP-011C Strict and Conservative Audited Accuracy")
    axis.legend()
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "group_accuracy_audit.png")
    plt.close(figure)


def main() -> None:
    """Write the conservative per-item audit and compact aggregate outputs."""
    input_rows = read_csv(INPUT_PATH)
    if len(input_rows) != 80:
        raise ValueError(f"Expected 80 EXP-011B results; found {len(input_rows)}.")
    audited = [audit_row(row) for row in input_rows]
    if Counter(row["audit_label"] for row in audited).total() != 80:
        raise ValueError("Every input result must receive exactly one audit label.")
    write_csv(OUTPUT_DIR / "audited_answer_results.csv", list(audited[0]), audited)
    metrics = group_metrics(audited)
    write_csv(OUTPUT_DIR / "group_accuracy_audit.csv", list(metrics[0]), metrics)
    counts = Counter(row["audit_label"] for row in audited)
    label_rows = [{"audit_label": label, "count": counts[label]} for label in LABELS]
    write_csv(OUTPUT_DIR / "audit_label_counts.csv", ["audit_label", "count"], label_rows)
    save_plot(metrics)
    strict = counts["strict_correct"]
    audited_correct = strict + counts["likely_correct_scoring_miss"]
    ceiling = audited_correct + counts["partially_correct"] + counts["ambiguous"]
    strict_ranking = [row["group"] for row in sorted(metrics, key=lambda row: row["strict_accuracy"], reverse=True)]
    audited_ranking = [row["group"] for row in sorted(metrics, key=lambda row: row["conservative_audited_accuracy"], reverse=True)]
    additions = [{"id": row["id"], "answer": row["candidate_new_acceptable_answer"]} for row in audited if row["recommend_dataset_update"]]
    materially_brittle = (audited_correct - strict) / 80 >= 0.05 or any(row["conservative_audited_accuracy"] - row["strict_accuracy"] >= 0.10 for row in metrics)
    summary = {
        "total_items": 80, "strict_correct_count": strict,
        "likely_correct_scoring_miss_count": counts["likely_correct_scoring_miss"],
        "partially_correct_count": counts["partially_correct"], "ambiguous_count": counts["ambiguous"],
        "likely_wrong_count": counts["likely_wrong"], "strict_accuracy": strict / 80,
        "conservative_audited_accuracy": audited_correct / 80, "review_ceiling": ceiling / 80,
        "group_metrics": {row["group"]: row for row in metrics},
        "recommended_acceptable_answer_additions": additions,
        "number_of_recommended_dataset_updates": len(additions),
        "warnings": ["Review ceiling is an uncertainty ceiling, not accuracy or final correctness.", "This rule-based manual audit has no independent human annotator or semantic judge."],
        "strict_scoring_appears_materially_brittle": materially_brittle,
        "behavioral_group_ranking_strict": strict_ranking,
        "behavioral_group_ranking_audited": audited_ranking,
        "ranking_changes_after_conservative_audit": strict_ranking != audited_ranking,
    }
    save_json(summary, OUTPUT_DIR / "audit_summary.json")
    print(summary)


if __name__ == "__main__":
    main()
