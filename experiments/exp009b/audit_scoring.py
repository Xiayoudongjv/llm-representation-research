"""EXP-009B: conservatively audit EXP-009 answer scoring."""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt


GROUPS = ["logic", "causality", "analogy", "definition"]
AUDIT_LABELS = [
    "strict_correct",
    "likely_correct_scoring_miss",
    "partially_correct",
    "likely_wrong",
    "ambiguous",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results_path", default="results/exp009/answer_eval_results.csv")
    parser.add_argument("--prompts_path", default="experiments/exp009/reasoning_eval_prompts.json")
    parser.add_argument("--output_dir", default="results/exp009b")
    return parser.parse_args()


def normalize_answer(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"^(the answer is|answer:|it is)\s*", "", text)
    text = re.sub(r"[\s.!?,;:]+$", "", text)
    return re.sub(r"\s+", " ", text)


def contains_standalone(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(normalize_answer(phrase))}(?!\w)", text) is not None


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_prompts(path: Path) -> dict[str, dict]:
    with path.open(encoding="utf-8") as handle:
        return {item["id"]: item for item in json.load(handle)}


def audit_row(row: dict[str, str], prompt: dict) -> dict[str, str]:
    strict_is_correct = row["is_correct"].strip().lower() == "true"
    model_answer = normalize_answer(row["model_answer"])
    expected_answer = normalize_answer(row["expected_answer"])
    acceptable_answers = [normalize_answer(value) for value in prompt["acceptable_answers"]]
    if strict_is_correct:
        label = "strict_correct"
        reason = "Original EXP-009 strict rule marked the answer correct."
    elif any(contains_standalone(model_answer, acceptable) for acceptable in acceptable_answers):
        label = "likely_correct_scoring_miss"
        reason = "A listed acceptable answer appears after conservative normalization."
    elif row["group"] == "analogy":
        if row["id"] in {"analogy_eval_03", "analogy_eval_04"}:
            label = "partially_correct"
            reason = "The answer gives a related association but does not match the requested target exactly."
        else:
            label = "likely_wrong"
            reason = "The answer does not match the expected analogy target or option."
    elif row["id"] == "logic_eval_04":
        label = "likely_wrong"
        reason = "The numerical answer does not match the deterministic sequence target."
    elif row["id"] == "definition_eval_06":
        label = "ambiguous"
        reason = "The answer describes a related aspect of democracy without the exact conservative target phrase."
    elif row["id"] == "definition_eval_05":
        label = "ambiguous"
        reason = "The answer is a clear paraphrase, but the audit does not infer semantic equivalence automatically."
    elif row["id"] == "causality_eval_06":
        label = "ambiguous"
        reason = "The answer gives a plausible mechanism but lacks the listed string-level match."
    elif row["id"] == "causality_eval_03":
        label = "ambiguous"
        reason = "The answer uses a semantically adjacent photosynthesis expression without the exact listed phrase."
    else:
        label = "likely_wrong"
        reason = "No conservative acceptable-answer string match was found."
    return {
        "id": row["id"],
        "group": row["group"],
        "question": row["question"],
        "expected_answer": row["expected_answer"],
        "acceptable_answers": "; ".join(prompt["acceptable_answers"]),
        "model_answer": row["model_answer"],
        "strict_is_correct": str(strict_is_correct),
        "normalized_model_answer": model_answer,
        "normalized_expected_answer": expected_answer,
        "audit_label": label,
        "audit_reason": reason,
    }


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    result_rows = load_csv(Path(args.results_path))
    prompts = load_prompts(Path(args.prompts_path))
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audited = [audit_row(row, prompts[row["id"]]) for row in result_rows]
    counts = Counter(row["audit_label"] for row in audited)
    strict_accuracy = sum(row["strict_is_correct"] == "True" for row in audited) / len(audited)
    upper_bound_accuracy = (counts["strict_correct"] + counts["likely_correct_scoring_miss"]) / len(audited)

    group_strict = {}
    group_upper = {}
    comparison_rows = []
    for group in GROUPS:
        group_rows = [row for row in audited if row["group"] == group]
        strict = sum(row["strict_is_correct"] == "True" for row in group_rows) / len(group_rows)
        upper = sum(row["audit_label"] in {"strict_correct", "likely_correct_scoring_miss"} for row in group_rows) / len(group_rows)
        group_strict[group] = strict
        group_upper[group] = upper
        comparison_rows.append([group, strict, upper, len(group_rows)])

    output_header = ["id", "group", "question", "expected_answer", "model_answer", "strict_is_correct", "audit_label", "audit_reason"]
    write_csv(output_dir / "audited_answer_results.csv", output_header, [[row[column] for column in output_header] for row in audited])
    write_csv(output_dir / "group_accuracy_comparison.csv", ["group", "strict_accuracy", "audited_upper_bound_accuracy", "num_items"], comparison_rows)
    summary = {
        "strict_accuracy": strict_accuracy,
        "audited_upper_bound_accuracy": upper_bound_accuracy,
        "counts_by_audit_label": {label: counts[label] for label in AUDIT_LABELS},
        "group_strict_accuracy": group_strict,
        "group_audited_upper_bound_accuracy": group_upper,
        "note": "Conservative heuristic auditing only; this is not human evaluation and does not use an LLM judge.",
    }
    (output_dir / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axis = plt.subplots(figsize=(8, 5))
    positions = range(len(GROUPS))
    width = 0.35
    axis.bar([position - width / 2 for position in positions], [group_strict[group] for group in GROUPS], width, label="strict")
    axis.bar([position + width / 2 for position in positions], [group_upper[group] for group in GROUPS], width, label="audited upper bound")
    axis.set_xticks(list(positions), GROUPS)
    axis.set_xlabel("Group")
    axis.set_ylabel("Accuracy")
    axis.set_ylim(0, 1.0)
    axis.set_title("EXP-009B Strict vs Audited Accuracy")
    axis.legend()
    figure.tight_layout()
    figure.savefig(output_dir / "group_accuracy_comparison.png")
    plt.close(figure)
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
