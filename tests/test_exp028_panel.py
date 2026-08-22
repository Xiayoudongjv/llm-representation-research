"""EXP-028 fresh-panel generation, validation, and freeze-identity tests.

These tests use synthetic/non-scientific dummy text only. They never load a
language model, never access real FIT/DIAG/EVAL data, never create a final
scientific panel, and never create a formal authorization.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP028_DIR = ROOT / "experiments" / "exp028"
for path in (str(ROOT), str(EXP028_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import build_exp028_exclusion_index as exclusion_builder
import exp028_panel_lib as panel_lib
import generate_exp028_panel as panel_generator
import run_exp028 as r
import validate_exp028_panel as panel_validator


def _candidate_items(prefix: str = "test") -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    n = 0
    for condition in panel_lib.CONDITIONS:
        for semantic_class in panel_lib.CLASSES:
            for split in panel_lib.SPLITS:
                for _ in range(panel_lib.ALLOCATION[split]):
                    n += 1
                    raw_text = f"{prefix} {condition} {semantic_class} {split} {n:04d}"
                    items.append({
                        "item_id": f"item-{prefix}-{n:04d}",
                        "condition_id": condition,
                        "semantic_class": semantic_class,
                        "split": split,
                        "source_family_id": f"sf-{prefix}-{n:04d}",
                        "paraphrase_family_id": f"pf-{prefix}-{n:04d}",
                        "raw_text": raw_text,
                        "normalized_raw_text_sha256": panel_lib.normalized_text_hash(raw_text),
                    })
    return items


def _formal_panel(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "classification": panel_lib.FORMAL_PANEL_CLASSIFICATION,
        "experiment": "EXP-028",
        "frozen": True,
        "provenance": {"generator_task": "TEST_ONLY_NON_SCIENTIFIC"},
        "items": items if items is not None else _candidate_items(),
    }


def _synthetic_panel(items: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "classification": panel_lib.SYNTHETIC_PANEL_CLASSIFICATION,
        "experiment": "EXP-028",
        "frozen": True,
        "provenance": {"generator_task": "TEST_ONLY_SYNTHETIC"},
        "items": items if items is not None else _candidate_items("synthetic"),
    }


def _empty_exclusion_index() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "classification": panel_lib.INDEX_CLASSIFICATION,
        "normalized_raw_text_sha256": [],
        "source_family_ids": [],
        "paraphrase_family_ids": [],
        "records": [],
    }


def _write_json(path: Path, payload: Any) -> str:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return panel_lib.sha256_file(path)


def test_valid_formal_panel_accepted():
    assert panel_lib.validate_panel(_formal_panel(), _empty_exclusion_index(), formal=True) == []


def test_synthetic_fixture_accepted_in_synthetic_mode():
    assert panel_lib.validate_panel(_synthetic_panel(), formal=False) == []


def test_fit_count_exact():
    items = _candidate_items()
    items = [item for item in items if not (item["split"] == "FIT" and item["condition_id"] == "c01_lexical_relex" and item["semantic_class"] == "logic")][:-1]
    # Above filtering is intentionally covered below by a simpler count break.
    items = _candidate_items()
    items = items[:-1]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("panel_item_count_exact_880" in e for e in errors)
    assert any("panel_allocation" in e for e in errors)


def test_diag_count_exact():
    items = _candidate_items()
    items = [item for item in items if not (item["split"] == "DIAGNOSTIC" and item["condition_id"] == "c01_lexical_relex" and item["semantic_class"] == "logic")]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("panel_allocation" in e for e in errors)


def test_eval_count_exact():
    items = _candidate_items()
    items = [item for item in items if not (item["split"] == "EVAL" and item["condition_id"] == "c01_lexical_relex" and item["semantic_class"] == "logic")]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("panel_allocation" in e for e in errors)


def test_condition_count_exact():
    items = [item for item in _candidate_items() if item["condition_id"] != "c01_lexical_relex"]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("panel_allocation_c01_lexical_relex" in e for e in errors)


def test_class_count_exact():
    items = [item for item in _candidate_items() if item["semantic_class"] != "logic"]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("panel_allocation" in e and "_logic_" in e for e in errors)


def test_raw_text_collision_rejected():
    items = _candidate_items()
    items[1]["raw_text"] = items[0]["raw_text"]
    items[1]["normalized_raw_text_sha256"] = items[0]["normalized_raw_text_sha256"]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("duplicate_normalized_raw_text" in e for e in errors)


def test_normalized_collision_rejected():
    items = _candidate_items()
    items[0]["raw_text"] = "A  B"
    items[0]["normalized_raw_text_sha256"] = panel_lib.normalized_text_hash("A B")
    items[1]["raw_text"] = "A B"
    items[1]["normalized_raw_text_sha256"] = panel_lib.normalized_text_hash("A B")
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("duplicate_normalized_raw_text" in e for e in errors)


def test_source_family_collision_rejected():
    items = _candidate_items()
    items[0]["source_family_id"] = "sf_historical"
    index = _empty_exclusion_index()
    index["source_family_ids"] = ["sf_historical"]
    errors = panel_lib.validate_panel(_formal_panel(items), index, formal=True)
    assert any("prior_source_family_reuse" in e for e in errors)


def test_paraphrase_family_collision_rejected():
    items = _candidate_items()
    items[0]["paraphrase_family_id"] = "pf_historical"
    index = _empty_exclusion_index()
    index["paraphrase_family_ids"] = ["pf_historical"]
    errors = panel_lib.validate_panel(_formal_panel(items), index, formal=True)
    assert any("prior_paraphrase_family_reuse" in e for e in errors)


def test_cross_split_leakage_rejected():
    items = _candidate_items()
    items[1]["source_family_id"] = items[0]["source_family_id"]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("duplicate_source_family_id" in e for e in errors)


def test_wrong_split_rejected():
    items = _candidate_items()
    items[0]["split"] = "BAD_SPLIT"
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("item_0_split" in e for e in errors)


def test_duplicate_item_id_rejected():
    items = _candidate_items()
    items[1]["item_id"] = items[0]["item_id"]
    errors = panel_lib.validate_panel(_formal_panel(items), _empty_exclusion_index(), formal=True)
    assert any("duplicate_item_id" in e for e in errors)


def test_unknown_historical_metadata_handled_explicitly():
    index = exclusion_builder.build_index(ROOT)
    assert index["metadata_policy"] == "missing_historical_fields_marked_unavailable_and_not_invented"
    assert any(record["paraphrase_family_id"] == "UNAVAILABLE" for record in index["records"])


def test_post_freeze_mutation_detectable(tmp_path):
    panel = _formal_panel()
    path = tmp_path / "panel.json"
    expected = _write_json(path, panel)
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ValueError, match="PANEL_SHA256_MISMATCH"):
        panel_validator.validate_panel_file(path, expected_sha256=expected)


def test_panel_freeze_identity_binds_counts_and_hashes():
    panel = _formal_panel()
    stats = panel_lib.panel_statistics(panel)
    identity = panel_lib.panel_freeze_identity(
        panel_sha256="a" * 64,
        config_sha256="b" * 64,
        generator_sha256="c" * 64,
        validator_sha256="d" * 64,
        exclusion_index_sha256="e" * 64,
        statistics=stats,
        generation_seed=None,
    )
    assert identity["item_count"] == 880
    assert identity["split_counts"] == {"FIT": 240, "DIAGNOSTIC": 320, "EVAL": 320}
    assert identity["generation_seed"] is None


def test_formal_run_rejects_synthetic_panel(tmp_path):
    panel = _synthetic_panel()
    path = tmp_path / "synthetic_panel.json"
    _write_json(path, panel)
    index_path = tmp_path / "index.json"
    _write_json(index_path, _empty_exclusion_index())
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="FORMAL_RUN_PANEL_INVALID"):
        r.load_and_validate_formal_panel(path, index_path)


def test_formal_run_rejects_missing_panel(tmp_path):
    missing = tmp_path / "missing_panel.json"
    index = tmp_path / "index.json"
    _write_json(index, _empty_exclusion_index())
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="FORMAL_RUN_PANEL_MISSING"):
        r.run_formal_run(
            ROOT,
            authorization_file=None,
            panel_manifest=str(missing),
            exclusion_index=str(index),
        )


def test_formal_run_rejects_unfrozen_panel(tmp_path):
    panel = _formal_panel()
    panel["frozen"] = False
    path = tmp_path / "unfrozen_panel.json"
    _write_json(path, panel)
    index = tmp_path / "index.json"
    _write_json(index, _empty_exclusion_index())
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="FORMAL_RUN_PANEL_INVALID"):
        r.load_and_validate_formal_panel(path, index)


def test_formal_run_rejects_wrong_panel_sha(tmp_path):
    path = tmp_path / "panel.json"
    _write_json(path, _formal_panel())
    index = tmp_path / "index.json"
    _write_json(index, _empty_exclusion_index())
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="FORMAL_RUN_PANEL_SHA256_MISMATCH"):
        r.load_and_validate_formal_panel(path, index, expected_panel_sha256="0" * 64)


def test_formal_run_rejects_freshness_collision(tmp_path):
    items = _candidate_items()
    items[0]["source_family_id"] = "sf_historical"
    panel_path = tmp_path / "panel.json"
    _write_json(panel_path, _formal_panel(items))
    index = _empty_exclusion_index()
    index["source_family_ids"] = ["sf_historical"]
    index_path = tmp_path / "index.json"
    _write_json(index_path, index)
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="FORMAL_RUN_PANEL_INVALID"):
        r.load_and_validate_formal_panel(panel_path, index_path)


def test_generator_builds_valid_formal_panel(tmp_path):
    panel, stats = panel_generator.build_panel(
        _candidate_items(),
        exclusion_index=_empty_exclusion_index(),
        generator_sha256="f" * 64,
    )
    assert stats["item_count"] == 880
    assert panel_lib.validate_panel(panel, _empty_exclusion_index(), formal=True) == []


def test_generator_rejects_invalid_allocation(tmp_path):
    items = _candidate_items()[:-1]
    with pytest.raises(ValueError, match="EXP028_PANEL_VALIDATION_FAILED"):
        panel_generator.build_panel(
            items,
            exclusion_index=_empty_exclusion_index(),
            generator_sha256="f" * 64,
        )


def test_generator_does_not_import_torch():
    source = Path(panel_generator.__file__).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "from torch" not in source
