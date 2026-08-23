#!/usr/bin/env python3
"""Independent final-panel validator for the PA-EXT-A V3 pipeline."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Mapping

import pa_ext_a_v3_pipeline as pipe

REQUIRED_ITEM_FIELDS = [
    "item_id",
    "task_family_id",
    "semantic_relation_id",
    "class_id",
    "condition_id",
    "source_item_id",
    "source_family_id",
    "transformation_id",
    "transformation_family_id",
    "raw_text",
    "normalized_text",
    "partition",
    "authoring_provenance",
    "review_status",
    "rejection_history",
    "content_design_sha256",
    "record_role",
    "semantic_instance_id",
    "render_provenance",
]


def _has_classification(panel: Mapping[str, Any], expected: str) -> bool:
    return panel.get("classification") == expected


def _rendered_text(item: Mapping[str, Any]) -> str | None:
    provenance = item.get("render_provenance")
    if not isinstance(provenance, Mapping):
        return None
    if provenance.get("render_function") != "deterministic_frozen_template":
        return None
    template = provenance.get("template")
    placeholders = provenance.get("placeholders")
    if not isinstance(template, str) or not isinstance(placeholders, Mapping):
        return None
    try:
        return pipe._clean_rendered_text(template.format(**{str(k): str(v) for k, v in placeholders.items()}))
    except Exception:
        return None


def validate_panel(
    panel: Mapping[str, Any],
    design: Mapping[str, Any] | None = None,
    *,
    mode: str = "synthetic",
    exclusion_index: Mapping[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    if not isinstance(panel, Mapping):
        return ["panel_not_mapping"]

    if design is None:
        design = pipe.load_frozen_design()

    if mode == "synthetic":
        check(_has_classification(panel, pipe.SYNTHETIC_PANEL_CLASSIFICATION), "panel_classification_not_synthetic")
        check(panel.get("synthetic") is True, "panel_synthetic_flag")
        check(panel.get("scientific_use_allowed") is False, "panel_scientific_use_allowed")
        check(panel.get("formal_panel_allowed") is False, "panel_formal_panel_allowed")
    else:
        check(_has_classification(panel, pipe.FORMAL_PANEL_CLASSIFICATION), "panel_classification_not_formal")
        check(panel.get("synthetic") is False, "panel_synthetic_flag")
        check(panel.get("scientific_use_allowed") is True, "panel_scientific_use_allowed")
        check(panel.get("formal_panel_allowed") is True, "panel_formal_panel_allowed")

    check(panel.get("schema_version") == pipe.PANEL_SCHEMA_VERSION, "panel_schema_version")
    check(panel.get("experiment") == "PAPER-A-EXT-A", "panel_experiment")
    check(panel.get("pipeline_route") == pipe.PIPELINE_ROUTE, "panel_pipeline_route")
    check(panel.get("frozen") is True, "panel_not_frozen")
    check(panel.get("content_design_sha256") == pipe.EXPECTED_V3_SHA256, "panel_content_design_sha256")
    check(panel.get("protocol_sha256") == pipe.EXPECTED_PROTOCOL_SHA256, "panel_protocol_sha256")
    check(panel.get("generated_by") == "pa_ext_a_v3_pipeline.py", "panel_generated_by")

    items = panel.get("items")
    check(isinstance(items, list), "panel_items_not_list")
    if not isinstance(items, list):
        return errors

    check(len(items) == 1760, f"panel_item_count_exact_1760_{len(items)}")

    seen_item_ids: set[str] = set()
    seen_source_families: set[str] = set()
    seen_hashes: set[str] = set()
    family_records: dict[str, list[Mapping[str, Any]]] = {}

    for idx, item in enumerate(items):
        if not isinstance(item, Mapping):
            errors.append(f"item_{idx}_not_mapping")
            continue

        for field in REQUIRED_ITEM_FIELDS:
            check(field in item, f"item_{idx}_missing_{field}")

        item_id = item.get("item_id")
        check(isinstance(item_id, str) and bool(item_id), f"item_{idx}_item_id")
        if isinstance(item_id, str):
            check(item_id not in seen_item_ids, f"duplicate_item_id_{idx}")
            seen_item_ids.add(item_id)

        source_family_id = item.get("source_family_id")
        check(isinstance(source_family_id, str) and bool(source_family_id), f"item_{idx}_source_family_id")
        if isinstance(source_family_id, str):
            seen_source_families.add(source_family_id)
            family_records.setdefault(source_family_id, []).append(item)

        task_family_id = item.get("task_family_id")
        relation_id = item.get("semantic_relation_id")
        class_id = item.get("class_id")
        condition_id = item.get("condition_id")
        partition = item.get("partition")
        record_role = item.get("record_role")

        check(task_family_id in pipe.TASK_FAMILY_IDS, f"item_{idx}_task_family")
        check(relation_id in pipe.RELATION_IDS, f"item_{idx}_semantic_relation")
        check(class_id in pipe.CLASS_BY_TASK.values(), f"item_{idx}_class")
        check(condition_id in pipe.CONDITIONS, f"item_{idx}_condition")
        check(partition in pipe.PARTITIONS, f"item_{idx}_partition")
        check(record_role in pipe.RECORD_ROLES, f"item_{idx}_record_role")

        check(pipe.RELATION_BY_TASK.get(task_family_id) == relation_id, f"item_{idx}_relation_task_mapping")
        check(pipe.CLASS_BY_TASK.get(task_family_id) == class_id, f"item_{idx}_class_task_mapping")

        raw_text = item.get("raw_text")
        check(isinstance(raw_text, str) and bool(raw_text), f"item_{idx}_raw_text")
        normalized = item.get("normalized_text")
        if isinstance(raw_text, str):
            check(normalized == pipe.normalize_text(raw_text), f"item_{idx}_normalized_text_mismatch")
            text_hash = pipe.normalized_text_hash(raw_text)
            check(text_hash not in seen_hashes, f"duplicate_normalized_text_{idx}")
            seen_hashes.add(text_hash)
            token_count = len(pipe.normalize_text(raw_text).split())
            check(8 <= token_count <= 28, f"item_{idx}_surface_token_count_{token_count}")

        check(item.get("content_design_sha256") == pipe.EXPECTED_V3_SHA256, f"item_{idx}_content_design_sha256")

        if source_family_id and condition_id and partition and task_family_id and record_role:
            parsed = _parse_source_family_id(str(source_family_id))
            check(parsed is not None, f"item_{idx}_source_family_pattern")
            if parsed is not None:
                expected_sf = pipe.make_source_family_id(
                    str(task_family_id),
                    str(condition_id),
                    str(partition),
                    parsed["index"],
                )
                check(expected_sf == source_family_id, f"item_{idx}_source_family_identity")
            check(item.get("item_id") == pipe.make_final_item_id(str(source_family_id), str(record_role)), f"item_{idx}_item_identity")
            check(item.get("source_item_id") == pipe.make_source_item_id(str(source_family_id)), f"item_{idx}_source_item_identity")
            check(item.get("transformation_id") == pipe.make_transformation_id(str(condition_id)), f"item_{idx}_transformation_identity")
            check(item.get("transformation_family_id") == pipe.make_transformation_family_id(str(source_family_id)), f"item_{idx}_transformation_family_identity")

        expected_rendered = _rendered_text(item)
        check(expected_rendered is not None, f"item_{idx}_render_provenance_invalid")
        if expected_rendered is not None:
            check(expected_rendered == raw_text, f"item_{idx}_free_form_or_mismatched_rendered_text")
            check(item.get("render_provenance", {}).get("rendered_text") == raw_text, f"item_{idx}_rendered_text_field_mismatch")

    check(len(seen_source_families) == 880, f"panel_source_family_count_{len(seen_source_families)}")
    for family, family_items in family_records.items():
        check(len(family_items) == 2, f"family_{family}_record_count_{len(family_items)}")
        roles = {item.get("record_role") for item in family_items}
        check(roles == set(pipe.RECORD_ROLES), f"family_{family}_roles_{sorted(roles)}")
        check(len({item.get("partition") for item in family_items}) == 1, f"family_{family}_partition_leak")
        check(len({item.get("task_family_id") for item in family_items}) == 1, f"family_{family}_task_leak")
        check(len({item.get("semantic_relation_id") for item in family_items}) == 1, f"family_{family}_relation_leak")
        check(len({item.get("class_id") for item in family_items}) == 1, f"family_{family}_class_leak")
        check(len({item.get("condition_id") for item in family_items}) == 1, f"family_{family}_condition_leak")

    for partition in pipe.PARTITIONS:
        family_count = sum(1 for family_items in family_records.values() if family_items[0].get("partition") == partition)
        record_count = sum(1 for item in items if isinstance(item, Mapping) and item.get("partition") == partition)
        expected_families = {"FIT": 240, "DIAG": 320, "EVAL": 320}[partition]
        expected_records = {"FIT": 480, "DIAG": 640, "EVAL": 640}[partition]
        check(family_count == expected_families, f"partition_{partition}_family_count_{family_count}")
        check(record_count == expected_records, f"partition_{partition}_record_count_{record_count}")

    for task_family_id in pipe.TASK_FAMILY_IDS:
        for condition_id in pipe.CONDITIONS:
            for partition in pipe.PARTITIONS:
                expected_records = pipe.PARTITION_COUNTS[partition] * 2
                count = sum(
                    1
                    for item in items
                    if isinstance(item, Mapping)
                    and item.get("task_family_id") == task_family_id
                    and item.get("condition_id") == condition_id
                    and item.get("partition") == partition
                )
                check(count == expected_records, f"cell_{task_family_id}_{condition_id}_{partition}_{count}_vs_{expected_records}")

    if exclusion_index is not None:
        check(
            exclusion_index.get("classification") == pipe.HISTORICAL_INDEX_CLASSIFICATION,
            "exclusion_index_classification",
        )
        prior_hashes = set(exclusion_index.get("normalized_text_hashes", []))
        prior_families = set(exclusion_index.get("source_family_ids", []))
        prior_items = set(exclusion_index.get("source_item_ids", []))
        for idx, item in enumerate(items):
            if not isinstance(item, Mapping):
                continue
            raw = item.get("raw_text")
            if isinstance(raw, str) and pipe.normalized_text_hash(raw) in prior_hashes:
                errors.append(f"prior_panel_text_collision_{idx}")
            sf = item.get("source_family_id")
            if sf in prior_families:
                errors.append(f"prior_source_family_collision_{idx}")
            source_item = item.get("source_item_id")
            if source_item in prior_items:
                errors.append(f"prior_source_item_collision_{idx}")

    return errors

SOURCE_FAMILY_RE = re.compile(
    r"^exta_sf_(?P<condition>xa\d\d_[a-z_]+?)_"
    r"(?P<partition>FIT|DIAG|EVAL)_"
    r"(?P<task>exta_tf_[a-z_]+)_"
    r"(?P<index>\d{4})$"
)


def _parse_source_family_id(source_family_id: str) -> dict[str, Any] | None:
    match = SOURCE_FAMILY_RE.match(source_family_id)
    if not match:
        return None
    return {
        "condition": match.group("condition"),
        "partition": match.group("partition"),
        "task": match.group("task"),
        "index": int(match.group("index")),
    }


def validate_panel_file(
    path: Path | str,
    *,
    mode: str = "synthetic",
    expected_sha256: str | None = None,
    exclusion_index: Mapping[str, Any] | None = None,
) -> list[str]:
    panel_path = Path(path)
    if expected_sha256 is not None:
        actual = pipe.sha256_file(panel_path)
        if actual != expected_sha256:
            raise pipe.PaperAExtAPipelineError("PANEL_SHA256_MISMATCH")
    panel = pipe.read_json(panel_path)
    return validate_panel(panel, mode=mode, exclusion_index=exclusion_index)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a PA-EXT-A V3 pipeline panel")
    parser.add_argument("panel", type=Path)
    parser.add_argument("--mode", choices=["synthetic", "production"], default="synthetic")
    parser.add_argument("--expected-sha256")
    args = parser.parse_args(argv)

    errors = validate_panel_file(args.panel, mode=args.mode, expected_sha256=args.expected_sha256)
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("PAPER_A_EXT_A_V3_PIPELINE_VALIDATION = FAIL")
        return 1

    print("PAPER_A_EXT_A_V3_PIPELINE_VALIDATION = PASS")
    print("PAPER_A_EXT_A_PANEL_MODE = " + args.mode)
    print("PAPER_A_EXT_A_PANEL_IS_SYNTHETIC_QUALIFICATION_ONLY = true" if args.mode == "synthetic" else "PAPER_A_EXT_A_PANEL_IS_FORMAL = true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
