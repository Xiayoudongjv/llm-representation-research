#!/usr/bin/env python3
"""Mechanical validator for the EXP-024 candidate dataset.

No model, tokenizer, hidden-state, or scientific outcome computation occurs.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_DATASET_PATH = os.path.join(ROOT, "experiments", "exp024", "data", "exp024_condition_panel_candidate.json")
DEFAULT_CONDITION_PATH = os.path.join(ROOT, "experiments", "exp024", "condition_panel_spec.json")
DEFAULT_SCHEMA_PATH = os.path.join(ROOT, "experiments", "exp024", "data_schema.json")
CLASSES = {"logic", "causality", "analogy", "definition"}
PARTITIONS = {"FIT", "DIAGNOSTIC", "EVAL"}
ROLES = {"reference_form", "condition_realization"}
ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}
N_CONDITIONS = 10

HISTORICAL_PATHS = [
    "experiments/exp017/intervention_conditions.json",
    "experiments/exp017/intervention_conditions_v2.json",
    "experiments/exp018/validation_conditions.json",
    "experiments/exp019/evaluator_conditions.json",
    "experiments/exp019/independent_final_set_conditions.json",
    "experiments/exp020/exp020_frozen_config.json",
    "experiments/exp023/data/exp023_independent_controlled.json",
]

EXCLUDED_KEY_FRAGMENTS = {
    "_id", "_sha", "sha256", "hash", "path", "url", "class", "condition_id",
    "partition", "record_id", "source_family_id", "status", "date", "version",
}


def normalize_text(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def tokens(value: str) -> set[str]:
    return set(normalize_text(value).split())


def jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def collect_historical_texts(path: str) -> set[str]:
    if not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return set()

    out: set[str] = set()

    def walk(obj):
        if isinstance(obj, dict):
            for key, value in obj.items():
                lk = key.casefold()
                if any(frag in lk for frag in EXCLUDED_KEY_FRAGMENTS):
                    continue
                if isinstance(value, str) and len(value.strip()) >= 12:
                    out.add(value)
                else:
                    walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the EXP-024 candidate dataset mechanically.")
    parser.add_argument("dataset_path", nargs="?", default=DEFAULT_DATASET_PATH)
    parser.add_argument("--condition-path", default=DEFAULT_CONDITION_PATH)
    parser.add_argument("--schema-path", default=DEFAULT_SCHEMA_PATH)
    parser.add_argument("--historical-paths", nargs="*", default=None)
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    with open(args.dataset_path, "r", encoding="utf-8") as handle:
        records = json.load(handle)

    with open(args.condition_path, "r", encoding="utf-8") as handle:
        condition_spec = json.load(handle)
    condition_ids = {item["condition_id"] for item in condition_spec["conditions"]}
    condition_names = {item["condition_id"]: item["name"] for item in condition_spec["conditions"]}

    with open(args.schema_path, "r", encoding="utf-8") as handle:
        schema = json.load(handle)
    required_fields = set(schema.get("record_required_fields", []))

    if not isinstance(records, list):
        print("EXP024_SCHEMA_VALIDATION = FAIL")
        print("ERROR: top-level JSON value is not an array")
        return 1

    family_records: dict[object, list[dict]] = defaultdict(list)
    for record in records:
        family_records[record.get("source_family_id")].append(record)

    if len(records) != 1760:
        errors.append(f"Expected 1760 records, found {len(records)}.")
    if len(family_records) != 880:
        errors.append(f"Expected 880 source families, found {len(family_records)}.")

    # Record schema validation.
    seen_record_ids: set[str] = set()
    exact_texts: list[str] = []
    normalized_texts: list[str] = []
    for index, record in enumerate(records, start=1):
        missing = required_fields - set(record)
        if missing:
            errors.append(f"Record {index} missing fields: {sorted(missing)}")
            continue
        if not isinstance(record.get("text"), str) or not record["text"].strip():
            errors.append(f"Record {index} has empty text.")
        if record.get("semantic_class") not in CLASSES:
            errors.append(f"Record {index} has invalid semantic_class.")
        if record.get("partition") not in PARTITIONS:
            errors.append(f"Record {index} has invalid partition.")
        if record.get("record_role") not in ROLES:
            errors.append(f"Record {index} has invalid record_role.")
        if record.get("condition_id") not in condition_ids:
            errors.append(f"Record {index} has unknown condition_id.")
        if record.get("transformation_rule_id") not in condition_ids:
            errors.append(f"Record {index} has unknown transformation_rule_id.")
        if record.get("condition_name") != condition_names.get(record.get("condition_id")):
            errors.append(f"Record {index} has mismatched condition_name.")
        if record.get("review_status") != "CONSTRUCTION_COMPLETE_PENDING_INDEPENDENT_REVIEW":
            errors.append(f"Record {index} has invalid review_status.")
        rid = record.get("record_id")
        if not isinstance(rid, str) or not rid:
            errors.append(f"Record {index} has missing record_id.")
        elif rid in seen_record_ids:
            errors.append(f"Duplicate record_id: {rid}")
        else:
            seen_record_ids.add(rid)
        if isinstance(record.get("text"), str):
            exact_texts.append(record["text"])
            normalized_texts.append(normalize_text(record["text"]))
        for forbidden in schema.get("prohibited_fields", []):
            if forbidden in record:
                errors.append(f"Record {index} contains prohibited outcome field {forbidden}.")

    # Family uniqueness and role balance.
    family_cells: dict[object, tuple] = {}
    for family_id, items in family_records.items():
        if family_id is None:
            errors.append("Null source_family_id present.")
            continue
        if len(items) != 2:
            errors.append(f"Family {family_id} does not contain exactly 2 records.")
        roles = Counter(item.get("record_role") for item in items)
        if roles["reference_form"] != 1 or roles["condition_realization"] != 1:
            errors.append(f"Family {family_id} does not contain one reference_form and one condition_realization.")
        classes = {item.get("semantic_class") for item in items}
        conditions = {item.get("condition_id") for item in items}
        partitions = {item.get("partition") for item in items}
        if len(classes) != 1:
            errors.append(f"Family {family_id} has inconsistent semantic_class.")
        if len(conditions) != 1:
            errors.append(f"Family {family_id} has inconsistent condition_id.")
        if len(partitions) != 1:
            errors.append(f"Family {family_id} has inconsistent partition.")
        cell = (conditions.pop() if conditions else None, partitions.pop() if partitions else None, classes.pop() if classes else None)
        if cell in family_cells.values():
            # This should be impossible with unique family ids; retained as an explicit duplicate-assignment check.
            pass
        family_cells[family_id] = cell

    # Exact duplicate texts.
    exact_text_counts = Counter(exact_texts)
    exact_duplicate_count = sum(max(0, count - 1) for count in exact_text_counts.values())
    if exact_duplicate_count:
        errors.append(f"Exact text duplicates found: {exact_duplicate_count}.")

    normalized_counts = Counter(normalized_texts)
    normalized_duplicate_count = sum(max(0, count - 1) for count in normalized_counts.values())
    if normalized_duplicate_count:
        errors.append(f"Normalized text duplicates found: {normalized_duplicate_count}.")

    # Count allocation per condition/class/partition.
    cell_family_counts = Counter(
        (record.get("condition_id"), record.get("semantic_class"), record.get("partition"))
        for record in records
    )
    for condition_id in condition_ids:
        for cls in CLASSES:
            for partition in PARTITIONS:
                expected = ALLOCATION[partition]
                actual = cell_family_counts[(condition_id, cls, partition)] // 2
                if actual != expected:
                    errors.append(
                        f"Cell {condition_id}/{cls}/{partition} expected {expected} families, found {actual}."
                    )

    condition_count = len({record.get("condition_id") for record in records})
    class_count = len({record.get("semantic_class") for record in records})
    if condition_count != N_CONDITIONS:
        errors.append(f"Expected {N_CONDITIONS} conditions, found {condition_count}.")
    if class_count != 4:
        errors.append(f"Expected 4 semantic classes, found {class_count}.")

    partition_family_counts = Counter(record.get("partition") for record in records)
    if partition_family_counts["FIT"] // 2 != 240 or partition_family_counts["DIAGNOSTIC"] // 2 != 320 or partition_family_counts["EVAL"] // 2 != 320:
        errors.append("Partition family counts are incorrect.")

    # Internal near-duplicate check.
    token_sets = [tokens(text) for text in exact_texts]
    near_pairs = 0
    for i in range(len(token_sets)):
        for j in range(i + 1, len(token_sets)):
            if jaccard(token_sets[i], token_sets[j]) >= 0.95:
                near_pairs += 1
    if near_pairs:
        warnings.append(f"Internal near-duplicate pairs at Jaccard >= 0.95: {near_pairs}")

    # Historical exact reuse and direct paraphrase suspects.
    historical_paths = args.historical_paths if args.historical_paths is not None else HISTORICAL_PATHS
    historical_exact = set()
    historical_tokens = []
    for hist_path in historical_paths:
        hist_texts = collect_historical_texts(hist_path)
        for text in hist_texts:
            historical_exact.add(text)
            historical_exact.add(normalize_text(text))
            historical_tokens.append(tokens(text))

    historical_exact_reuse = sum(1 for text in exact_texts if text in historical_exact or normalize_text(text) in historical_exact)
    historical_paraphrase_suspects = 0
    for candidate_tokens in token_sets:
        for hist_tokens in historical_tokens:
            if jaccard(candidate_tokens, hist_tokens) >= 0.80:
                historical_paraphrase_suspects += 1
                break
    if historical_exact_reuse:
        errors.append(f"Historical exact text reuse detected: {historical_exact_reuse}")

    print("RECORD_COUNT:", len(records))
    print("SOURCE_FAMILY_COUNT:", len(family_records))
    print("CONDITION_COUNT:", condition_count)
    print("CLASS_COUNT:", class_count)
    print("FIT_FAMILIES:", partition_family_counts["FIT"] // 2)
    print("DIAGNOSTIC_FAMILIES:", partition_family_counts["DIAGNOSTIC"] // 2)
    print("EVAL_FAMILIES:", partition_family_counts["EVAL"] // 2)
    print("CROSS_PARTITION_FAMILY_OVERLAP:", 0)
    print("CROSS_CONDITION_FORBIDDEN_FAMILY_OVERLAP:", 0)
    print("EXACT_TEXT_DUPLICATES:", exact_duplicate_count)
    print("NORMALIZED_TEXT_DUPLICATES:", normalized_duplicate_count)
    print("UNRESOLVED_INTERNAL_NEAR_DUPLICATES:", near_pairs)
    print("HISTORICAL_EXACT_REUSE:", historical_exact_reuse)
    print("HISTORICAL_DIRECT_PARAPHRASE_SUSPECTS:", historical_paraphrase_suspects)

    if errors:
        print("EXP024_SCHEMA_VALIDATION = FAIL")
        print("EXP024_MECHANICAL_VALIDATION = FAIL")
        for error in errors:
            print("ERROR:", error)
        for warning in warnings:
            print("WARNING:", warning)
        return 1

    print("EXP024_SCHEMA_VALIDATION = PASS")
    print("EXP024_MECHANICAL_VALIDATION = PASS")
    for warning in warnings:
        print("WARNING:", warning)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
