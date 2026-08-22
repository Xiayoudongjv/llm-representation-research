#!/usr/bin/env python3
"""Generate and freeze an EXP-028 panel from already-created candidate items.

This module is engineering machinery. It does not create scientific raw text,
does not load language-model weights, and does not introduce a random seed.
The final scientific panel is intentionally NOT generated in Task 103E.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import exp028_panel_lib as panel_lib

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = EXP_DIR / "exp028_frozen_config.json"
DEFAULT_INDEX_PATH = EXP_DIR / "engineering" / "exp028_historical_exclusion_index.json"
SYNTHETIC_FIXTURE_PATH = EXP_DIR / "engineering" / "exp028_synthetic_panel_fixture.json"


def _config() -> dict[str, Any]:
    return panel_lib.read_json(CONFIG_PATH)


def _generator_sha256() -> str:
    return panel_lib.sha256_file(Path(__file__))


def _candidate_items(path: Path) -> list[dict[str, Any]]:
    data = panel_lib.read_json(path)
    if not isinstance(data, list) or not data:
        raise ValueError("EXP028_PANEL_CANDIDATE_ITEMS_MUST_BE_NONEMPTY_LIST")
    return [dict(item) for item in data]


def _item_value(item: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in item and item[name] is not None:
            return item[name]
    return default


def build_panel(
    candidate_items: Sequence[Mapping[str, Any]],
    *,
    exclusion_index: Mapping[str, Any] | None = None,
    generator_sha256: str,
) -> dict[str, Any]:
    """Build and validate a frozen EXP-028 panel from candidate raw-text items."""
    cell_counter: dict[tuple[str, str, str], int] = {}
    items: list[dict[str, Any]] = []
    for item in candidate_items:
        if not isinstance(item, Mapping):
            raise ValueError("EXP028_PANEL_ITEM_NOT_MAPPING")
        condition = str(_item_value(item, "condition_id", "condition"))
        semantic_class = str(_item_value(item, "semantic_class"))
        split = str(_item_value(item, "split"))
        raw_text = str(_item_value(item, "raw_text", default=""))
        source_family_id = _item_value(item, "source_family_id")
        paraphrase_family_id = _item_value(item, "paraphrase_family_id")
        key = (condition, semantic_class, split)
        cell_counter[key] = cell_counter.get(key, 0) + 1
        index_in_cell = cell_counter[key]
        item_id = str(_item_value(item, "item_id", default=f"exp028_{condition}_{split}_{semantic_class}_{index_in_cell:04d}"))
        normalized_hash = panel_lib.normalized_text_hash(raw_text)
        items.append({
            "item_id": item_id,
            "condition_id": condition,
            "semantic_class": semantic_class,
            "split": split,
            "source_family_id": source_family_id,
            "paraphrase_family_id": paraphrase_family_id,
            "raw_text": raw_text,
            "normalized_raw_text_sha256": normalized_hash,
        })

    panel = {
        "schema_version": panel_lib.PANEL_SCHEMA_VERSION,
        "classification": panel_lib.FORMAL_PANEL_CLASSIFICATION,
        "experiment": "EXP-028",
        "frozen": True,
        "provenance": {
            "generator_task": "103E_EXP028_FRESH_PANEL_GENERATION_QUALIFICATION",
            "generator_name": "generate_exp028_panel.py",
            "generator_sha256": generator_sha256,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "purpose": "EXP028_FRESH_SCIENTIFIC_PANEL",
        },
        "generation_identity": {
            "generator_name": "generate_exp028_panel.py",
            "generator_sha256": generator_sha256,
            "scientific_config_sha256": panel_lib.sha256_file(CONFIG_PATH),
        },
        "items": items,
    }

    errors = panel_lib.validate_panel(panel, exclusion_index=exclusion_index, formal=True)
    if errors:
        raise ValueError(f"EXP028_PANEL_VALIDATION_FAILED_{errors}")

    stats = panel_lib.panel_statistics(panel)
    return panel, stats


def write_panel(panel: Mapping[str, Any], output_path: Path) -> str:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(panel, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return panel_lib.sha256_file(output_path)


def build_synthetic_fixture(generator_sha256: str) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    n = 0
    for condition in panel_lib.CONDITIONS:
        for semantic_class in panel_lib.CLASSES:
            for split in panel_lib.SPLITS:
                for _ in range(panel_lib.ALLOCATION[split]):
                    n += 1
                    raw_text = (
                        "SYNTHETIC_NON_SCIENTIFIC_NOT_FOR_FORMAL_RUN "
                        f"{condition} {semantic_class} {split} {n:04d}"
                    )
                    items.append({
                        "item_id": f"exp028_synthetic_{condition}_{split}_{semantic_class}_{n:04d}",
                        "condition_id": condition,
                        "semantic_class": semantic_class,
                        "split": split,
                        "source_family_id": f"sf_synthetic_{condition}_{split}_{semantic_class}_{n:04d}",
                        "paraphrase_family_id": f"pf_synthetic_{condition}_{split}_{semantic_class}_{n:04d}",
                        "raw_text": raw_text,
                        "normalized_raw_text_sha256": panel_lib.normalized_text_hash(raw_text),
                    })
    panel = {
        "schema_version": panel_lib.PANEL_SCHEMA_VERSION,
        "classification": panel_lib.SYNTHETIC_PANEL_CLASSIFICATION,
        "experiment": "EXP-028",
        "frozen": True,
        "provenance": {
            "generator_task": "103E_SYNTHETIC_QUALIFICATION",
            "generator_name": "generate_exp028_panel.py",
            "generator_sha256": generator_sha256,
            "purpose": "SYNTHETIC_NON_SCIENTIFIC_NOT_FOR_FORMAL_RUN",
        },
        "items": items,
    }
    errors = panel_lib.validate_panel(panel, formal=False)
    if errors:
        raise ValueError(f"EXP028_SYNTHETIC_PANEL_VALIDATION_FAILED_{errors}")
    return panel


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--exclusion-index", default=str(DEFAULT_INDEX_PATH))
    parser.add_argument("--synthetic-fixture", action="store_true")
    args = parser.parse_args(argv)

    generator_sha = _generator_sha256()
    if args.synthetic_fixture:
        panel = build_synthetic_fixture(generator_sha)
        write_panel(panel, SYNTHETIC_FIXTURE_PATH)
        print("EXP028_SYNTHETIC_PANEL_FIXTURE=PASS")
        print(f"SHA256={panel_lib.sha256_file(SYNTHETIC_FIXTURE_PATH)}")
        return 0

    if not args.input or not args.output:
        parser.error("--input and --output are required unless --synthetic-fixture is used")
    input_path = Path(args.input)
    output_path = Path(args.output)
    exclusion_path = Path(args.exclusion_index)
    if not exclusion_path.exists():
        raise ValueError("EXP028_EXCLUSION_INDEX_MISSING")
    exclusion_index = panel_lib.load_exclusion_index(exclusion_path)
    candidate_items = _candidate_items(input_path)
    panel, stats = build_panel(
        candidate_items,
        exclusion_index=exclusion_index,
        generator_sha256=generator_sha,
    )
    panel_sha = write_panel(panel, output_path)
    freeze_path = output_path.with_name(output_path.name + ".freeze_identity.json")
    freeze_identity = panel_lib.panel_freeze_identity(
        panel_sha256=panel_sha,
        config_sha256=panel_lib.sha256_file(CONFIG_PATH),
        generator_sha256=generator_sha,
        validator_sha256=panel_lib.sha256_file(EXP_DIR / "validate_exp028_panel.py"),
        exclusion_index_sha256=panel_lib.sha256_file(exclusion_path),
        statistics=stats,
        generation_seed=None,
    )
    freeze_path.write_text(
        json.dumps(freeze_identity, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("EXP028_PANEL_GENERATION=PASS")
    print(f"OUTPUT={output_path}")
    print(f"FREEZE_IDENTITY={freeze_path}")
    print(f"ITEMS={len(panel['items'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
