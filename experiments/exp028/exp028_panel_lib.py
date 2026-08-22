#!/usr/bin/env python3
"""Shared EXP-028 fresh-panel validation and freeze-identity machinery.

This module is synthetic/engineering-only. It never loads a language model and
never constructs a real EXP-028 scientific panel.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path
from typing import Any, Mapping, Sequence

PANEL_SCHEMA_VERSION = "1.0.0"
FORMAL_PANEL_CLASSIFICATION = "EXP028_FRESH_SCIENTIFIC_PANEL"
SYNTHETIC_PANEL_CLASSIFICATION = "SYNTHETIC_NON_SCIENTIFIC_NOT_FOR_FORMAL_RUN"
INDEX_CLASSIFICATION = "EXP028_HISTORICAL_EXCLUSION_INDEX"

CONDITIONS = [
    "c01_lexical_relex",
    "c02_syntactic_restructure",
    "c03_controlled_compression",
    "c04_controlled_elaboration",
    "c05_relation_explicit",
    "c06_relation_implicit",
    "c07_register_formal",
    "c08_register_informal",
    "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
]
CLASSES = ["logic", "causality", "analogy", "definition"]
SPLITS = ["FIT", "DIAGNOSTIC", "EVAL"]
ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}
EXPECTED_TOTAL_ITEMS = len(CONDITIONS) * len(CLASSES) * sum(ALLOCATION.values())


def sha256_file(path: Path | str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path | str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = text.strip()
    return " ".join(text.split())


def normalized_text_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest()


def _item_str(item: Mapping[str, Any], *names: str) -> str | None:
    for name in names:
        value = item.get(name)
        if isinstance(value, str) and value:
            return value
    return None


def _has_classification(panel: Mapping[str, Any], expected: str) -> bool:
    return panel.get("classification") == expected or panel.get("panel_kind") == expected


def load_exclusion_index(path: Path | str) -> dict[str, Any]:
    index = read_json(path)
    if index.get("classification") != INDEX_CLASSIFICATION:
        raise ValueError("EXP028_EXCLUSION_INDEX_CLASSIFICATION_INVALID")
    return index


def panel_statistics(panel: Mapping[str, Any]) -> dict[str, Any]:
    items = panel.get("items", [])
    split_counts = {split: 0 for split in SPLITS}
    condition_counts = {condition: 0 for condition in CONDITIONS}
    class_counts = {cls: 0 for cls in CLASSES}
    cell_counts: dict[tuple[str, str, str], int] = {}
    for item in items:
        split = _item_str(item, "split")
        condition = _item_str(item, "condition_id", "condition")
        semantic_class = _item_str(item, "semantic_class")
        if split in split_counts:
            split_counts[split] += 1
        if condition in condition_counts:
            condition_counts[condition] += 1
        if semantic_class in class_counts:
            class_counts[semantic_class] += 1
        if condition and semantic_class and split:
            key = (condition, semantic_class, split)
            cell_counts[key] = cell_counts.get(key, 0) + 1
    return {
        "item_count": len(items),
        "split_counts": split_counts,
        "condition_counts": condition_counts,
        "class_counts": class_counts,
        "cell_counts": {f"{c}|{s}|{p}": n for (c, s, p), n in sorted(cell_counts.items())},
    }


def validate_panel(
    panel: Mapping[str, Any],
    exclusion_index: Mapping[str, Any] | None = None,
    *,
    formal: bool = True,
) -> list[str]:
    """Validate a candidate EXP-028 panel against the frozen contract.

    `formal=True` enforces production formal-run requirements and rejects
    synthetic panels. `formal=False` validates synthetic fixtures without
    requiring a production freeze identity.
    """
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    if not isinstance(panel, Mapping):
        return ["panel_not_mapping"]

    if formal:
        check(_has_classification(panel, FORMAL_PANEL_CLASSIFICATION), "panel_classification_not_formal")
        check(not _has_classification(panel, SYNTHETIC_PANEL_CLASSIFICATION), "panel_is_synthetic_not_formal")
    else:
        check(_has_classification(panel, SYNTHETIC_PANEL_CLASSIFICATION), "synthetic_panel_classification")

    check(panel.get("schema_version") == PANEL_SCHEMA_VERSION, "panel_schema_version")
    check(panel.get("experiment") == "EXP-028", "panel_experiment")
    check(panel.get("frozen") is True, "panel_not_frozen")

    if formal:
        provenance = panel.get("provenance")
        check(isinstance(provenance, Mapping) and provenance.get("generator_task"), "panel_provenance_generator_task")
    else:
        check(isinstance(panel.get("provenance"), Mapping), "synthetic_panel_provenance")

    items = panel.get("items", [])
    check(isinstance(items, list) and len(items) == EXPECTED_TOTAL_ITEMS, "panel_item_count_exact_880")
    if not isinstance(items, list):
        return errors

    seen_item_ids: set[str] = set()
    seen_hashes: set[str] = set()
    seen_source_families: set[str] = set()
    seen_paraphrase_families: set[str] = set()

    for idx, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"item_{idx}_not_mapping")
            continue

        item_id = _item_str(item, "item_id")
        check(bool(item_id), f"item_{idx}_missing_item_id")
        if item_id:
            if item_id in seen_item_ids:
                errors.append(f"duplicate_item_id_{idx}")
            seen_item_ids.add(item_id)

        raw = item.get("raw_text")
        check(isinstance(raw, str) and bool(raw), f"item_{idx}_raw_text")
        if isinstance(raw, str):
            text_hash = normalized_text_hash(raw)
            declared_hash = item.get("normalized_raw_text_sha256")
            check(not declared_hash or declared_hash == text_hash, f"item_{idx}_normalized_hash_mismatch")
            if text_hash in seen_hashes:
                errors.append(f"duplicate_normalized_raw_text_{idx}")
            seen_hashes.add(text_hash)

        source_family = _item_str(item, "source_family_id")
        check(bool(source_family), f"item_{idx}_source_family_id")
        if source_family:
            if source_family in seen_source_families:
                errors.append(f"duplicate_source_family_id_{idx}")
            seen_source_families.add(source_family)

        paraphrase_family = _item_str(item, "paraphrase_family_id")
        if paraphrase_family:
            if paraphrase_family in seen_paraphrase_families:
                errors.append(f"duplicate_paraphrase_family_id_{idx}")
            seen_paraphrase_families.add(paraphrase_family)

        condition = _item_str(item, "condition_id", "condition")
        check(condition in CONDITIONS, f"item_{idx}_condition")
        semantic_class = _item_str(item, "semantic_class")
        check(semantic_class in CLASSES, f"item_{idx}_semantic_class")
        split = _item_str(item, "split")
        check(split in SPLITS, f"item_{idx}_split")

    # Exact allocation: one cell per condition x class x split.
    for condition in CONDITIONS:
        for semantic_class in CLASSES:
            for split in SPLITS:
                count = sum(
                    1
                    for item in items
                    if isinstance(item, Mapping)
                    and _item_str(item, "condition_id", "condition") == condition
                    and _item_str(item, "semantic_class") == semantic_class
                    and _item_str(item, "split") == split
                )
                check(count == ALLOCATION[split], f"panel_allocation_{condition}_{semantic_class}_{split}_{count}_vs_{ALLOCATION[split]}")

    if exclusion_index is not None:
        if exclusion_index.get("classification") != INDEX_CLASSIFICATION:
            errors.append("exclusion_index_classification")
        else:
            prior_hashes = set(exclusion_index.get("normalized_raw_text_sha256", []))
            prior_source_families = set(exclusion_index.get("source_family_ids", []))
            prior_paraphrase_families = set(exclusion_index.get("paraphrase_family_ids", []))
            for idx, item in enumerate(items):
                if not isinstance(item, Mapping):
                    continue
                raw = item.get("raw_text")
                if isinstance(raw, str):
                    text_hash = normalized_text_hash(raw)
                    if text_hash in prior_hashes:
                        errors.append(f"prior_panel_collision_{idx}")
                source_family = _item_str(item, "source_family_id")
                if source_family and source_family in prior_source_families:
                    errors.append(f"prior_source_family_reuse_{idx}")
                paraphrase_family = _item_str(item, "paraphrase_family_id")
                if paraphrase_family and paraphrase_family in prior_paraphrase_families:
                    errors.append(f"prior_paraphrase_family_reuse_{idx}")

    return errors


def panel_freeze_identity(
    *,
    panel_sha256: str,
    config_sha256: str,
    generator_sha256: str,
    validator_sha256: str,
    exclusion_index_sha256: str,
    statistics: Mapping[str, Any],
    generation_seed: int | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": PANEL_SCHEMA_VERSION,
        "experiment": "EXP-028",
        "panel_sha256": panel_sha256,
        "generator_identity": {
            "name": "generate_exp028_panel.py",
            "sha256": generator_sha256,
        },
        "validator_identity": {
            "name": "validate_exp028_panel.py",
            "sha256": validator_sha256,
        },
        "exclusion_index_sha256": exclusion_index_sha256,
        "scientific_config_sha256": config_sha256,
        "generation_seed": generation_seed,
        "item_count": int(statistics.get("item_count", 0)),
        "split_counts": {
            split: int(statistics.get("split_counts", {}).get(split, 0))
            for split in SPLITS
        },
    }
