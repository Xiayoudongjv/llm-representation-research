"""Structural validation only for the independent EXP-019 dataset."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path


DATA_DIR = Path(__file__).with_name("data")
FIELDS = ["example_id", "content_family_id", "task_class", "response_text", "split", "provenance", "length_tokens", "length_band", "template_family", "paraphrase_family_id", "lexical_challenge", "notes"]
CLASSES = ("logic", "causality", "analogy", "definition")
SPLIT_COUNTS = {"train": 120, "validation": 30, "test": 40}
ALLOWED_PROVENANCE = {"manual_procedural", "manual_authored", "rule_composed", "ai_assisted_draft"}
ALLOWED_BANDS = {"short": range(1, 6), "medium": range(6, 13), "limited_long": range(13, 21)}
FORBIDDEN = ("TASK_REAL", "MATCHED_RANDOM", "OPPOSITE", "NO_INTERVENTION", "hidden_state", "steering_vector")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"Unexpected dataset schema: {reader.fieldnames}")
        return list(reader)


def validate(rows: list[dict[str, str]]) -> dict:
    if len(rows) != 760:
        raise ValueError(f"Expected 760 primary rows, found {len(rows)}.")
    if Counter(row["task_class"] for row in rows) != Counter({task: 190 for task in CLASSES}):
        raise ValueError("Expected exactly 190 rows per task class.")
    for task in CLASSES:
        counts = Counter(row["split"] for row in rows if row["task_class"] == task)
        if counts != Counter(SPLIT_COUNTS):
            raise ValueError(f"Split counts for {task} are {counts}, not {SPLIT_COUNTS}.")
    family_splits, paraphrase_splits = defaultdict(set), defaultdict(set)
    for row in rows:
        if not row["response_text"].strip():
            raise ValueError("Empty response text is not allowed.")
        if row["task_class"] not in CLASSES or row["split"] not in SPLIT_COUNTS:
            raise ValueError("Found an unsupported task class or split.")
        if row["provenance"] not in ALLOWED_PROVENANCE:
            raise ValueError(f"Unsupported provenance: {row['provenance']}")
        if row["length_band"] not in ALLOWED_BANDS or int(row["length_tokens"]) not in ALLOWED_BANDS[row["length_band"]]:
            raise ValueError(f"Invalid length metadata for {row['example_id']}")
        if "label_quality=clear" not in row["notes"]:
            raise ValueError(f"Primary row lacks clear label quality: {row['example_id']}")
        if any(token.lower() in " ".join(row.values()).lower() for token in FORBIDDEN):
            raise ValueError(f"Forbidden intervention/internal token in {row['example_id']}")
        family_splits[row["content_family_id"]].add(row["split"])
        paraphrase_splits[row["paraphrase_family_id"]].add(row["split"])
    if any(len(splits) != 1 for splits in family_splits.values()) or any(len(splits) != 1 for splits in paraphrase_splits.values()):
        raise ValueError("Content or paraphrase families cross splits.")
    texts = [row["response_text"] for row in rows]
    if len(texts) != len(set(texts)):
        raise ValueError("Exact duplicate response text found.")
    normalized = [" ".join(text.lower().split()) for text in texts]
    if len(normalized) != len(set(normalized)):
        raise ValueError("Normalized duplicate response text found.")
    challenge = Counter(row["task_class"] for row in rows if row["lexical_challenge"] == "true")
    if any(challenge[task] < 20 for task in CLASSES):
        raise ValueError(f"Lexical challenge counts below 20 per class: {challenge}")
    return {"rows": len(rows), "families": len(family_splits), "challenge": dict(challenge)}


def main() -> None:
    result = validate(load_rows(DATA_DIR / "behavioral_targetness_dataset.csv"))
    print(f"dataset_validation=passed rows={result['rows']} families={result['families']} challenge={result['challenge']}")


if __name__ == "__main__":
    main()
