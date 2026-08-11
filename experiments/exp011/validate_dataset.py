"""Validate the EXP-011 dataset without loading a model."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "experiments/exp011/expanded_answer_prompts.json"
SUMMARY_PATH = ROOT / "results/exp011_dataset_validation.json"
GROUPS = {"logic", "causality", "analogy", "definition"}
REQUIRED_FIELDS = {
    "id", "group", "question", "expected_answer", "acceptable_answers",
    "answer_type", "scoring_rule", "notes",
}


def validate_dataset(items: object) -> dict:
    """Validate dataset structure and return a small JSON-serializable summary."""
    if not isinstance(items, list):
        raise ValueError("Top-level dataset value must be a JSON list.")
    if len(items) != 80:
        raise ValueError(f"Expected exactly 80 items; found {len(items)}.")
    ids: list[str] = []
    questions: list[str] = []
    group_counts: Counter[str] = Counter()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item {index} must be an object.")
        missing = REQUIRED_FIELDS - set(item)
        if missing:
            raise ValueError(f"Item {index} is missing fields: {sorted(missing)}.")
        for field in REQUIRED_FIELDS - {"acceptable_answers"}:
            if not isinstance(item[field], str) or not item[field].strip():
                raise ValueError(f"Item {index} has an empty or invalid {field!r} field.")
        answers = item["acceptable_answers"]
        if not isinstance(answers, list) or not answers or any(not isinstance(answer, str) or not answer for answer in answers):
            raise ValueError(f"Item {index} must have a non-empty acceptable_answers list of strings.")
        if item["group"] not in GROUPS:
            raise ValueError(f"Item {index} has invalid group {item['group']!r}.")
        if item["expected_answer"] not in answers:
            raise ValueError(f"Item {index} expected_answer must appear in acceptable_answers.")
        if any(answer != answer.lower() for answer in answers):
            raise ValueError(f"Item {index} acceptable_answers must be lowercase.")
        if item["answer_type"] != "short_answer":
            raise ValueError(f"Item {index} answer_type must be 'short_answer'.")
        if item["scoring_rule"] != "case_insensitive_contains":
            raise ValueError(f"Item {index} scoring_rule must be 'case_insensitive_contains'.")
        ids.append(item["id"])
        questions.append(item["question"])
        group_counts[item["group"]] += 1
    if len(ids) != len(set(ids)):
        raise ValueError("Dataset IDs must be unique.")
    if len(questions) != len(set(questions)):
        raise ValueError("Dataset questions must be unique.")
    if set(group_counts) != GROUPS or any(group_counts[group] != 20 for group in GROUPS):
        raise ValueError(f"Expected exactly 20 items per group; found {dict(group_counts)}.")
    return {
        "total_items": len(items),
        "group_counts": dict(sorted(group_counts.items())),
        "validation_passed": True,
        "warnings": [],
    }


def main() -> None:
    """Load, validate, save, and print the compact validation summary."""
    with DATASET_PATH.open(encoding="utf-8") as handle:
        items = json.load(handle)
    summary = validate_dataset(items)
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
