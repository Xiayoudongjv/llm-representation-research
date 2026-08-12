"""Validate the 100-card external-material pilot without writing responses."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
CARDS_PATH = DATA_DIR / "source_cards_100_simple.csv"
FIELDS = ["source_card_id", "task_class", "topic_group", "source_material", "source_reference", "human_response", "status"]
CLASSES = ("logic", "causality", "analogy", "definition")
EXPECTED_GROUPS = {
    "logic": {"category_inference", "conditional_inference", "exclusion_or_contradiction", "comparison_or_transitivity", "simple_rule_application"},
    "causality": {"physics", "biology", "earth_environment", "everyday_processes", "technology_mechanisms"},
    "analogy": {"tool_function", "part_whole", "support_structure", "location_or_container", "functional_correspondence"},
    "definition": {"science_concepts", "mathematics_concepts", "everyday_objects", "technology_concepts", "general_education_concepts"},
}
FORBIDDEN = ("NO_INTERVENTION", "TASK_REAL", "MATCHED_RANDOM", "OPPOSITE", "hidden_state", "steering_vector", "intervention_condition")


def load_rows() -> list[dict[str, str]]:
    """Load cards and enforce the simple frozen header."""
    with CARDS_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"unexpected header: {reader.fieldnames}")
        return list(reader)


def validate(rows: list[dict[str, str]]) -> None:
    """Validate quotas, content presence, metadata safety, and concentration."""
    if len(rows) != 100:
        raise ValueError(f"expected 100 rows, got {len(rows)}")
    if Counter(row["task_class"] for row in rows) != Counter({c: 25 for c in CLASSES}):
        raise ValueError("class quota failure")
    ids = [row["source_card_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate source_card_id")
    materials = [row["source_material"] for row in rows]
    if len(materials) != len(set(materials)):
        raise ValueError("duplicate source_material")
    for cls in CLASSES:
        subset = [row for row in rows if row["task_class"] == cls]
        groups = Counter(row["topic_group"] for row in subset)
        if set(groups) != EXPECTED_GROUPS[cls] or any(count != 5 for count in groups.values()):
            raise ValueError(f"topic quota failure: {cls} {dict(groups)}")
    if any(not row["source_material"].strip() or not row["source_reference"].strip() for row in rows):
        raise ValueError("empty source material or source reference")
    if any(row["human_response"] or row["status"] != "pending" for row in rows):
        raise ValueError("human_response must be blank and status must be pending")
    values = " ".join(" ".join(row.values()) for row in rows).casefold()
    if any(term.casefold() in values for term in FORBIDDEN):
        raise ValueError("forbidden intervention metadata")
    resources = Counter(row["source_reference"] for row in rows)
    print(f"source_resource_counts={dict(resources)}")
    if max(resources.values()) > 15:
        raise ValueError("source resource exceeds 15 cards")
    print(f"source_cards_validation=passed rows={len(rows)}")


def main() -> None:
    """Run the 100-card validation."""
    validate(load_rows())


if __name__ == "__main__":
    main()
