#!/usr/bin/env python3
"""Static structural validator for the EXP-023 candidate dataset.

No model access, tokenizer access, fitting, or scientific computation occurs.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATASET_PATH = os.path.join(ROOT, "experiments", "exp023", "data", "exp023_independent_controlled.json")
OLD_DATASET_PATH = os.path.join(ROOT, "experiments", "exp003", "prompts_controlled.json")
CLASSES = {"logic", "causality", "analogy", "definition"}
VARIANTS = {"original_style", "paraphrase"}


def normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate EXP-023 candidate dataset statically.")
    parser.add_argument("dataset_path", nargs="?", default=DEFAULT_DATASET_PATH)
    parser.add_argument("--historical-path", default=OLD_DATASET_PATH)
    args = parser.parse_args()

    errors: list[str] = []
    with open(args.dataset_path, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    if not isinstance(records, list):
        print("STRUCTURAL_VALIDATION = FAIL")
        print("ERROR: top-level JSON value is not an array")
        return 1

    families: dict[object, list[dict]] = defaultdict(list)
    for record in records:
        families[record.get("source_family_id")].append(record)

    if len(records) != 64:
        errors.append(f"Expected 64 records, found {len(records)}.")
    if len(families) != 32:
        errors.append(f"Expected 32 source families, found {len(families)}.")
    class_family_counts = Counter()
    for family_id, items in families.items():
        if len(items) != 2:
            errors.append(f"Family {family_id} does not contain exactly 2 records.")
        variants = Counter(item.get("variant_type") for item in items)
        if variants["original_style"] != 1 or variants["paraphrase"] != 1:
            errors.append(f"Family {family_id} does not contain one original_style and one paraphrase.")
        classes = {item.get("SOURCE_SEMANTIC_CLASS") for item in items}
        if len(classes) != 1:
            errors.append(f"Family {family_id} has inconsistent classes: {classes}")
        else:
            class_family_counts[classes.pop()] += 1

    if set(class_family_counts) != CLASSES:
        errors.append("Class universe mismatch.")
    for cls in CLASSES:
        if class_family_counts[cls] != 8:
            errors.append(f"Expected 8 {cls} families, found {class_family_counts[cls]}.")

    class_variant_counts = Counter(
        (record.get("SOURCE_SEMANTIC_CLASS"), record.get("variant_type"))
        for record in records
    )
    for cls in CLASSES:
        for variant in VARIANTS:
            if class_variant_counts[(cls, variant)] != 8:
                errors.append(f"Expected 8 {cls}/{variant} records, found {class_variant_counts[(cls, variant)]}.")

    record_ids = [record.get("record_id") for record in records]
    if len(record_ids) != len(set(record_ids)):
        errors.append("Duplicate record_id values present.")

    required_fields = {"record_id", "source_family_id", "SOURCE_SEMANTIC_CLASS", "variant_type", "text"}
    texts = []
    for index, record in enumerate(records, start=1):
        missing = required_fields - set(record)
        if missing:
            errors.append(f"Record {index} missing fields: {sorted(missing)}")
            continue
        if not isinstance(record["text"], str) or not record["text"].strip():
            errors.append(f"Record {index} has empty text.")
        if record["variant_type"] not in VARIANTS:
            errors.append(f"Record {index} has invalid variant_type.")
        if record["SOURCE_SEMANTIC_CLASS"] not in CLASSES:
            errors.append(f"Record {index} has invalid SOURCE_SEMANTIC_CLASS.")
        texts.append(record["text"])
    if len(set(texts)) != len(texts):
        errors.append("Duplicate exact scientific text present.")
    normalized = [normalize_text(text) for text in texts]
    if len(set(normalized)) != len(normalized):
        errors.append("Duplicate normalized scientific text present.")

    old_exact_count = 0
    old_normalized_count = 0
    if os.path.exists(args.historical_path):
        with open(args.historical_path, "r", encoding="utf-8") as handle:
            old_records = json.load(handle)
        old_exact = set()
        old_normalized = set()
        for old_record in old_records:
            old_text = old_record.get("text")
            if isinstance(old_text, str):
                old_exact.add(old_text)
                old_normalized.add(normalize_text(old_text))
        old_exact_count = sum(1 for text in texts if text in old_exact)
        old_normalized_count = sum(1 for text in normalized if text in old_normalized)
        if old_exact_count or old_normalized_count:
            errors.append("Historical text reuse detected.")

    print("RECORD_COUNT:", len(records))
    print("SOURCE_FAMILY_COUNT:", len(families))
    print("FAMILIES_PER_CLASS:", dict(sorted(class_family_counts.items())))
    print("OLD_RECORD_EXACT_REUSE_COUNT:", old_exact_count)
    print("OLD_RECORD_NORMALIZED_REUSE_COUNT:", old_normalized_count)

    if errors:
        print("STRUCTURAL_VALIDATION = FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1

    print("STRUCTURAL_VALIDATION = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
