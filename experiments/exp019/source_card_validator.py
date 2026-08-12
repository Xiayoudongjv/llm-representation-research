"""Validate independent EXP-019 source cards without creating responses."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
TEMPLATE_PATH = DATA_DIR / "source_card_template.csv"
FIELDS = [
    "source_card_id", "target_task_class", "source_family", "source_title",
    "source_reference", "retrieval_date", "fact_or_relation_1",
    "fact_or_relation_2", "relation_type", "candidate_concept", "notes",
    "status",
]
CLASSES = {"logic", "causality", "analogy", "definition"}
SOURCE_FAMILIES = {
    "basic_science", "biology", "physics", "earth_science", "mathematics",
    "general_reference", "language_reference", "reasoning_education",
    "technology", "everyday_knowledge",
}
FORBIDDEN_FIELDS = {"response_text", "final_response", "primary_response"}
FORBIDDEN_METADATA = {
    "NO_INTERVENTION", "TASK_REAL", "MATCHED_RANDOM", "OPPOSITE",
    "hidden_state", "steering_vector", "intervention_condition",
}


def load_cards(path: Path = TEMPLATE_PATH) -> list[dict[str, str]]:
    """Load source cards and enforce the header without making network calls."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"unexpected source-card header: {reader.fieldnames}")
        return list(reader)


def validate_cards(cards: list[dict[str, str]]) -> None:
    """Validate populated source cards and permit an empty template."""
    if FORBIDDEN_FIELDS.intersection(FIELDS):
        raise ValueError("source-card schema contains final response field")
    seen: set[str] = set()
    for card in cards:
        card_id = card["source_card_id"]
        if not card_id or card_id in seen:
            raise ValueError("source_card_id must be present and unique")
        seen.add(card_id)
        if card["target_task_class"] not in CLASSES:
            raise ValueError("invalid target_task_class")
        if card["source_family"] and card["source_family"] not in SOURCE_FAMILIES:
            raise ValueError("unapproved source_family")
        if not card["source_reference"]:
            raise ValueError("source_reference is required")
        if not card["relation_type"]:
            raise ValueError("relation_type is required")
        content = " ".join(
            card[key] for key in ("fact_or_relation_1", "fact_or_relation_2", "candidate_concept")
        ).strip()
        if not content:
            raise ValueError("factual or relation content is required")
        values = " ".join(card.values()).casefold()
        if any(term.casefold() in values for term in FORBIDDEN_METADATA):
            raise ValueError("forbidden intervention metadata")


def main() -> None:
    """Validate the source-card template or a supplied CSV path."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=TEMPLATE_PATH)
    args = parser.parse_args()
    cards = load_cards(args.path)
    validate_cards(cards)
    print(f"source_card_validation=passed rows={len(cards)}")


if __name__ == "__main__":
    main()
