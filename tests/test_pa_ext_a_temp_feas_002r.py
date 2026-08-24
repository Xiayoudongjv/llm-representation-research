"""Focused offline tests for PA-EXT-A TEMP-FEAS-002R."""

from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).parents[1] / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_002r" / "confirm_temp_feas_002r.py"
SPEC = importlib.util.spec_from_file_location("temp_feas_002r", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_parse_confirmation_identity() -> None:
    value = "Q1|-0500-01-02T00:00:00Z|-0500-01-02T00:00:00Z|precision=11|calendar=Q1985727"
    parsed = MODULE.parse_confirmation_identity(value)
    assert parsed["wikidata_item_id"] == "Q1"
    assert parsed["date_precision"] == 11
    assert parsed["calendar_model"] == "Q1985727"


def test_root_reachability_handles_both_roots() -> None:
    adjacency = {"Q10": {"Q1656682", "Q1190554"}}
    memo = {}
    assert MODULE.root_status({"Q10"}, adjacency, memo, {"Q10": "REACHES_BOTH"}) == "REACHES_BOTH"


def test_root_reachability_handles_cycle_without_root() -> None:
    adjacency = {"Q10": {"Q11"}, "Q11": {"Q10"}}
    assert MODULE.root_status({"Q10"}, adjacency, {}, {"Q10": "CYCLE_NO_ROOT", "Q11": "CYCLE_NO_ROOT"}) == "TERMINAL_NO_ROOT"


def test_surface_filter_matches_frozen_leakage_rule() -> None:
    assert MODULE.passes_surface_filter("A documented event")
    assert not MODULE.passes_surface_filter("Event in 2020")
    assert not MODULE.passes_surface_filter("March event")


def test_pairing_does_not_reuse_events() -> None:
    events = [
        {"wikidata_item_id": "Q1", "p585_point_in_time_value": "2000-01-01T00:00:00Z"},
        {"wikidata_item_id": "Q2", "p585_point_in_time_value": "2000-01-01T00:00:00Z"},
        {"wikidata_item_id": "Q3", "p585_point_in_time_value": "2001-01-01T00:00:00Z"},
        {"wikidata_item_id": "Q4", "p585_point_in_time_value": "2002-01-01T00:00:00Z"},
    ]
    assert MODULE.pair_events(events) == [("Q1", "Q3"), ("Q2", "Q4")]


def test_no_network_or_model_imports() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "urllib" not in source
    assert "torch" not in source
    assert "transformers" not in source
