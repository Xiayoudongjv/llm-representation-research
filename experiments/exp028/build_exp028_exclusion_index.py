#!/usr/bin/env python3
"""Build the EXP-028 historical exclusion index from frozen prior panels.

This script reads only enumerated frozen predecessor authorities. It does not
generate EXP-028 scientific items and does not load any language model.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import exp028_panel_lib as panel_lib

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = EXP_DIR / "exp028_frozen_config.json"
OUTPUT_PATH = EXP_DIR / "engineering" / "exp028_historical_exclusion_index.json"


def _load_config() -> dict[str, Any]:
    return panel_lib.read_json(CONFIG_PATH)


def _prior_authorities(config: dict[str, Any]) -> list[dict[str, str]]:
    firewall = config.get("fresh_data_firewall", {})
    authorities = firewall.get("prior_panel_authorities", [])
    if not authorities:
        raise ValueError("EXP028_PRIOR_PANEL_AUTHORITIES_MISSING")
    return [dict(a) for a in authorities]


def _verify_authority(root: Path, authority: dict[str, str]) -> None:
    path = root / authority["path"]
    if not path.exists():
        raise ValueError(f"EXP028_PRIOR_PANEL_MISSING_{authority['path']}")
    actual = panel_lib.sha256_file(path)
    if actual.casefold() != str(authority["sha256"]).casefold():
        raise ValueError(f"EXP028_PRIOR_PANEL_SHA_MISMATCH_{authority['path']}")


def _record(
    *,
    experiment_id: str,
    source_authority: str,
    source_authority_sha256: str,
    record_id: str | None,
    raw_text: str,
    source_family_id: str | None,
    paraphrase_family_id: str | None,
    split: str | None,
    semantic_class: str | None,
) -> dict[str, Any]:
    normalized = panel_lib.normalized_text_hash(raw_text)
    return {
        "experiment_id": experiment_id,
        "source_authority": source_authority,
        "source_authority_sha256": source_authority_sha256,
        "record_id": record_id or "UNAVAILABLE",
        "normalized_raw_text_sha256": normalized,
        "source_family_id": source_family_id or "UNAVAILABLE",
        "paraphrase_family_id": paraphrase_family_id or "UNAVAILABLE",
        "split": split or "UNAVAILABLE",
        "semantic_class": semantic_class or "UNAVAILABLE",
    }


def build_index(root: Path = ROOT) -> dict[str, Any]:
    config = _load_config()
    authorities = _prior_authorities(config)
    verified_authorities: list[dict[str, str]] = []
    records: list[dict[str, Any]] = []
    hash_set: set[str] = set()
    source_family_set: set[str] = set()
    paraphrase_family_set: set[str] = set()

    for authority in authorities:
        _verify_authority(root, authority)
        verified_authorities.append({
            "name": authority["name"],
            "path": authority["path"],
            "sha256": authority["sha256"],
            "verified": True,
        })
        path = root / authority["path"]
        data = panel_lib.read_json(path)

        if authority["name"] == "EXP-023 independent controlled panel" and isinstance(data, list):
            for item in data:
                rec = _record(
                    experiment_id="EXP-023",
                    source_authority=authority["name"],
                    source_authority_sha256=authority["sha256"],
                    record_id=item.get("record_id") if isinstance(item, dict) else None,
                    raw_text=item.get("text", "") if isinstance(item, dict) else "",
                    source_family_id=item.get("source_family_id") if isinstance(item, dict) else None,
                    paraphrase_family_id=None,
                    split=None,
                    semantic_class=item.get("SOURCE_SEMANTIC_CLASS") if isinstance(item, dict) else None,
                )
                records.append(rec)
                hash_set.add(rec["normalized_raw_text_sha256"])
                if rec["source_family_id"] != "UNAVAILABLE":
                    source_family_set.add(rec["source_family_id"])
        elif authority["name"] == "EXP-024 frozen condition panel dataset" and isinstance(data, list):
            for item in data:
                if not isinstance(item, dict):
                    continue
                rec = _record(
                    experiment_id="EXP-024",
                    source_authority=authority["name"],
                    source_authority_sha256=authority["sha256"],
                    record_id=item.get("record_id"),
                    raw_text=item.get("text", ""),
                    source_family_id=item.get("source_family_id"),
                    paraphrase_family_id=item.get("paraphrase_family_id"),
                    split=item.get("partition"),
                    semantic_class=item.get("semantic_class"),
                )
                records.append(rec)
                hash_set.add(rec["normalized_raw_text_sha256"])
                if rec["source_family_id"] != "UNAVAILABLE":
                    source_family_set.add(rec["source_family_id"])
                if rec["paraphrase_family_id"] != "UNAVAILABLE":
                    paraphrase_family_set.add(rec["paraphrase_family_id"])

    if not records:
        raise ValueError("EXP028_EXCLUSION_INDEX_EMPTY")

    return {
        "schema_version": panel_lib.PANEL_SCHEMA_VERSION,
        "classification": panel_lib.INDEX_CLASSIFICATION,
        "metadata_policy": "missing_historical_fields_marked_unavailable_and_not_invented",
        "source_authorities": verified_authorities,
        "normalized_raw_text_sha256": sorted(hash_set),
        "source_family_ids": sorted(source_family_set),
        "paraphrase_family_ids": sorted(paraphrase_family_set),
        "record_count": len(records),
        "records": records,
    }


def main() -> int:
    index = build_index(ROOT)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("EXP028_HISTORICAL_EXCLUSION_INDEX=PASS")
    print(f"RECORDS={len(index['records'])}")
    print(f"SHA256={panel_lib.sha256_file(OUTPUT_PATH)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
