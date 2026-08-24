"""Focused offline tests for TEMP-FEAS-002E ontology traversal."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_002e" / "build_ontology_snapshot.py"


def _module():
    spec = importlib.util.spec_from_file_location("temp_feas_002e_builder", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_truthy_p279_prefers_preferred_and_excludes_deprecated() -> None:
    module = _module()
    entity = {
        "claims": {
            "P279": [
                {"rank": "normal", "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q2"}}}},
                {"rank": "preferred", "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q1"}}}},
                {"rank": "deprecated", "mainsnak": {"snaktype": "value", "datavalue": {"value": {"id": "Q3"}}}},
            ]
        }
    }
    assert module.truthy_p279(entity) == ["Q1"]


def test_redirect_preserves_requested_qid_and_records_resolved_entity() -> None:
    module = _module()
    entity = {
        "id": "Q2",
        "lastrevid": 7,
        "claims": {},
        "redirects": {"from": "Q1", "to": "Q2"},
    }
    record = module._entity_record(entity, "Q1", "batch_0000", "a" * 64, "2026-01-01T00:00:00+00:00")
    assert record["qid"] == "Q1"
    assert record["resolved_qid"] == "Q2"
    assert record["direct_p279_qids"] == []


def test_recursive_traversal_classifies_roots_and_terminal_nodes() -> None:
    module = _module()
    edges = {"Q10": {"Q20"}, "Q20": {"Q1656682"}, "Q30": set()}
    assert module.classify_seed("Q10", edges) == "REACHES_Q1656682"
    assert module.classify_seed("Q30", edges) == "TERMINAL_NO_ROOT"


def test_cycle_without_root_and_unresolved_are_distinguished() -> None:
    module = _module()
    assert module.classify_seed("Q40", {"Q40": {"Q41"}, "Q41": {"Q40"}}) == "CYCLE_NO_ROOT"
    assert module.classify_seed("Q50", {}) == "UNRESOLVED"


def test_both_root_reachability_and_determinism() -> None:
    module = _module()
    edges = {"Q60": {"Q1656682", "Q1190554"}}
    assert module.classify_seed("Q60", edges) == "REACHES_BOTH"
    assert module.closure_status(["Q60"], edges) == module.closure_status(["Q60"], edges)


def test_builder_has_ontology_only_firewall() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert '"labels"' not in source
    assert '"descriptions"' not in source
    assert "P585" not in source
    assert "qlever" not in source.lower()
    assert "TEMPORAL_EVENT_LIKE_V1" not in source
    assert "data/raw/wikidata_v8" not in source.replace("\\", "/")


def test_persisted_batches_are_minimized_to_direct_p279_only() -> None:
    module = _module()
    batch_dir = module.OUTPUT_DIR / "entity_api_batches"
    batch_files = [path for path in batch_dir.glob("*.json") if not path.name.endswith(".meta.json")]
    assert batch_files
    allowed = {"qid", "resolved_qid", "lastrevid", "direct_p279_qids", "redirects", "missing"}
    for path in batch_files:
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert "P585" not in path.read_text(encoding="utf-8")
        for entity in payload["entities"].values():
            assert set(entity) <= allowed
