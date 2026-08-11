"""Apply approved EXP-011C answer-vocabulary patches and rescore offline."""

from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.answer_scoring import normalize_answer, score_answer
from src.experiment_io import load_json, read_csv, save_json, write_csv


GROUPS = ["logic", "causality", "analogy", "definition"]
Z_95 = 1.959963984540054
DATASET_PATH = ROOT / "experiments/exp011/expanded_answer_prompts.json"
AUDIT_PATH = ROOT / "results/exp011c/audited_answer_results.csv"
SOURCE_PATH = ROOT / "results/exp011b/answer_eval_results.csv"
AUDIT_SUMMARY_PATH = ROOT / "results/exp011c/audit_summary.json"
OUTPUT_DIR = ROOT / "results/exp011d"


def wilson(correct: int, total: int) -> tuple[float, float]:
    """Return a descriptive two-sided 95% Wilson confidence interval."""
    p = correct / total
    denominator = 1 + Z_95**2 / total
    center = (p + Z_95**2 / (2 * total)) / denominator
    margin = Z_95 * math.sqrt((p * (1 - p) + Z_95**2 / (4 * total)) / total) / denominator
    return center - margin, center + margin


def approved_patches(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Select only non-empty additions explicitly approved by the audit."""
    return [
        row for row in rows
        if row["audit_label"] == "likely_correct_scoring_miss"
        and row["recommend_dataset_update"].lower() == "true"
        and row["candidate_new_acceptable_answer"].strip()
    ]


def save_plot(group_rows: list[dict[str, object]]) -> None:
    """Save a compact default-style final group-accuracy plot."""
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar([row["group"] for row in group_rows], [row["accuracy"] for row in group_rows])
    axis.set_ylim(0, 1)
    axis.set_xlabel("Group")
    axis.set_ylabel("Accuracy")
    axis.set_title("EXP-011D Final Rescored Group Accuracy")
    figure.tight_layout()
    figure.savefig(OUTPUT_DIR / "group_accuracy.png")
    plt.close(figure)


def main() -> None:
    """Patch the frozen dataset vocabulary and rescore existing model answers."""
    dataset = load_json(DATASET_PATH)
    audit_rows = read_csv(AUDIT_PATH)
    source_rows = read_csv(SOURCE_PATH)
    by_id = {item["id"]: item for item in dataset}
    patch_log: list[dict[str, str]] = []
    for audit in approved_patches(audit_rows):
        item = by_id[audit["id"]]
        candidate = normalize_answer(audit["candidate_new_acceptable_answer"])
        existing_normalized = {normalize_answer(answer) for answer in item["acceptable_answers"]}
        if candidate and candidate not in existing_normalized:
            item["acceptable_answers"].append(candidate)
            patch_log.append({
                "id": item["id"], "group": item["group"], "expected_answer": item["expected_answer"],
                "added_acceptable_answer": candidate, "audit_reason": audit["audit_reason"],
            })
    save_json(dataset, DATASET_PATH)
    write_csv(OUTPUT_DIR / "patch_log.csv", ["id", "group", "expected_answer", "added_acceptable_answer", "audit_reason"], patch_log)

    rescored: list[dict[str, object]] = []
    for source in source_rows:
        item = by_id[source["id"]]
        final_correct = score_answer(source["model_answer"], item["acceptable_answers"], item["scoring_rule"])
        original_correct = source["is_correct"].lower() == "true"
        rescored.append({
            "id": item["id"], "group": item["group"], "question": item["question"],
            "expected_answer": item["expected_answer"], "acceptable_answers": str(item["acceptable_answers"]),
            "model_answer": source["model_answer"], "normalized_model_answer": normalize_answer(source["model_answer"]),
            "original_is_correct": original_correct, "final_is_correct": final_correct,
            "changed_after_patch": not original_correct and final_correct,
        })
    write_csv(OUTPUT_DIR / "rescored_answer_results.csv", list(rescored[0]), rescored)

    group_rows: list[dict[str, object]] = []
    for group in GROUPS:
        subset = [row for row in rescored if row["group"] == group]
        correct = sum(row["final_is_correct"] for row in subset)
        low, high = wilson(correct, len(subset))
        group_rows.append({"group": group, "total": len(subset), "correct": correct, "accuracy": correct / len(subset), "ci95_low": low, "ci95_high": high})
    write_csv(OUTPUT_DIR / "group_accuracy.csv", list(group_rows[0]), group_rows)
    save_plot(group_rows)
    final_correct = sum(row["final_is_correct"] for row in rescored)
    original_correct = sum(row["original_is_correct"] for row in rescored)
    audit_summary = load_json(AUDIT_SUMMARY_PATH)
    final_accuracy = final_correct / len(rescored)
    ranking = [row["group"] for row in sorted(group_rows, key=lambda row: row["accuracy"], reverse=True)]
    summary = {
        "original_exp011b_accuracy": original_correct / len(rescored),
        "conservative_exp011c_accuracy": audit_summary["conservative_audited_accuracy"],
        "final_rescored_accuracy": final_accuracy,
        "number_of_patches": len(patch_log),
        "number_of_items_changed_from_incorrect_to_correct": sum(row["changed_after_patch"] for row in rescored),
        "group_accuracy": {row["group"]: row for row in group_rows},
        "group_ranking": ranking,
        "final_rescored_accuracy_equals_conservative_audit_accuracy": final_accuracy == audit_summary["conservative_audited_accuracy"],
        "warnings": ["Existing EXP-011B model answers were rescored offline; no model generation occurred.", "Acceptable-answer sets remain finite and this patch does not promote partial or ambiguous answers."],
    }
    save_json(summary, OUTPUT_DIR / "final_behavior_summary.json")
    print(summary)


if __name__ == "__main__":
    main()
