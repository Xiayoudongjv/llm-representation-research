"""Synthetic qualification of the TEMP-V2 engineering path."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
SPEC = importlib.util.spec_from_file_location("temp_v2_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def event(qid: str, cls: str = "QCLASS", date: str = "2000-01-01T00:00:00Z", label: str = "A documented event", prop: str = "P585") -> dict:
    return {"qid": qid, "direct_p31_qids": [cls], "label": label, "times": [{"property": prop, "time_value": date, "precision": 11, "calendar": "Q1985727"}]}


def test_backend_gate_pass_and_fail_closed() -> None:
    calls = []
    client = RUNNER.QLeverClient(request=lambda query: (200, {"head": {}, "results": {}}))
    result = client.preflight()
    assert result["status"] == 200
    assert result["graph_scope"] == "UNIFIED"
    failing = RUNNER.QLeverClient(request=lambda query: (503, {}))
    with pytest.raises(RuntimeError, match="HEALTH_FAILED"):
        failing.preflight()


def test_backend_endpoint_identity_fail_closed() -> None:
    client = RUNNER.QLeverClient(endpoint="https://wrong.example/wikidata", request=lambda query: (200, {}))
    with pytest.raises(RuntimeError, match="ENDPOINT_IDENTITY_FAILED"):
        client.preflight()


def test_fresh_qid_exclusion_and_root_validity() -> None:
    parents = {"QCLASS": {"Q1190554"}, "QBAD": {"QUNRELATED"}}
    eligible, reason = RUNNER.prepare_candidate(event("Q1"), {"Q1"}, parents)
    assert eligible is None and reason == "PRIOR_IDENTITY_REJECT"
    eligible, reason = RUNNER.prepare_candidate(event("Q2"), set(), parents)
    assert eligible and reason == "ELIGIBLE"
    eligible, reason = RUNNER.prepare_candidate(event("Q3", cls="QBAD"), set(), parents)
    assert eligible is None and reason == "EVENT_ROOT_INVALID"


def test_p580_precedence_p585_fallback_and_ambiguous_rejection() -> None:
    candidate = event("Q1", prop="P585")
    candidate["times"].insert(0, {"property": "P580", "time_value": "1999-01-01T00:00:00Z", "precision": 11, "calendar": "Q1985727"})
    resolved, source = RUNNER.resolve_canonical_time(candidate)
    assert resolved and resolved["canonical_property"] == "P580" and source == "p580"
    ambiguous = event("Q2")
    ambiguous["times"].append({"property": "P585", "time_value": "2001-01-01T00:00:00Z", "precision": 11, "calendar": "Q1985727"})
    resolved, reason = RUNNER.resolve_canonical_time(ambiguous)
    assert resolved is None and reason == "AMBIGUOUS_CANONICAL_TIME"


def test_invalid_time_calendar_and_precision_are_rejected() -> None:
    assert RUNNER.resolve_canonical_time({"times": [{"property": "P585", "time_value": "2000-01-01T00:00:00Z", "precision": 10, "calendar": "Q1985727"}]})[0] is None
    assert RUNNER.resolve_canonical_time({"times": [{"property": "P585", "time_value": "2000-01-01T00:00:00Z", "precision": 11, "calendar": "Q1"}]})[0] is None


def test_leakage_rejection_and_dedup_identity() -> None:
    assert not RUNNER.surface_is_safe("Event in 1999")
    assert not RUNNER.surface_is_safe("March 4, 1999")
    assert RUNNER.surface_is_safe("A documented event")
    parents = {"QCLASS": {"Q1190554"}}
    first, _ = RUNNER.prepare_candidate(event("Q1"), set(), parents)
    second, _ = RUNNER.prepare_candidate(event("Q1"), set(), parents)
    assert first and second and first["canonical_identity"] == second["canonical_identity"]


def test_diversity_cap_and_hash_ordering() -> None:
    events = [{"qid": f"Q{i}", "canonical_identity": f"Q{i}|P585|{i}", "coarse_class": "QCLASS" if i < 50 else f"QCLASS{i}", "canonical_time": f"2000-01-{(i % 28) + 1:02d}T00:00:00Z"} for i in range(100)]
    selected = RUNNER.select_events(events, target=10, class_cap=2)
    assert len(selected) == 10
    assert max(__import__("collections").Counter(row["coarse_class"] for row in selected).values()) <= 2
    assert RUNNER.select_events(events, target=10, class_cap=2) == selected


def test_query_is_event_first_and_not_date_ordered() -> None:
    query = RUNNER.event_page_query(100, 0)
    assert "wdt:P31" in query and "wdt:P279*" in query
    assert "ORDER BY ASC(?item)" in query
    assert "?date" not in query


def test_duplicate_selection_identity_fails_closed() -> None:
    duplicate = {"qid": "Q1", "canonical_identity": "Q1|P585|x", "coarse_class": "Q1", "canonical_time": "x"}
    with pytest.raises(RuntimeError, match="DUPLICATE_CANONICAL"):
        RUNNER.select_events([duplicate, dict(duplicate)], target=2, class_cap=2)


def test_checkpoint_resume_and_authority_guard(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint = RUNNER.initial_checkpoint(timestamp="2026-01-01T00:00:00+00:00")
    checkpoint["status"] = "RUNNING"
    checkpoint["current_acquisition_offset"] = 100
    RUNNER.write_checkpoint(checkpoint_path, checkpoint)
    assert RUNNER.load_checkpoint(checkpoint_path)["current_acquisition_offset"] == 100
    checkpoint["protocol_sha256"] = "wrong"
    RUNNER.write_checkpoint(checkpoint_path, checkpoint)
    with pytest.raises(RuntimeError, match="AUTHORITY_MISMATCH"):
        RUNNER.load_checkpoint(checkpoint_path)


def test_stopping_paths() -> None:
    assert RUNNER.stopping_state(600, False) == "STOP_AT_RESERVE_AND_SELECT"
    assert RUNNER.stopping_state(450, True) == "READY_TO_PAIR"
    assert RUNNER.stopping_state(439, True) == "INSUFFICIENT_FRESH_SOURCE"
    assert RUNNER.stopping_state(100, False) == "CONTINUE_ACQUISITION"


def test_full_440_to_220_synthetic_path() -> None:
    events = [
        {"qid": f"Q{i}", "canonical_identity": f"Q{i}", "canonical_time": f"2000-01-{i:03d}T00:00:00Z", "coarse_class": f"QCLASS{i // 40}"}
        for i in range(440)
    ]
    selected = RUNNER.select_events(events, target=440, class_cap=44)
    assert len(selected) == 440
    pairs = RUNNER.pair_events(selected, target_families=220)
    assert len(pairs) == 220


def test_progress_monitor_is_read_only_and_complete() -> None:
    monitor_path = ROOT / "experiments" / "paper_a_ext_a" / "monitor_temporal_source_v2.py"
    spec = importlib.util.spec_from_file_location("temp_v2_monitor", monitor_path)
    monitor = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(monitor)
    output = monitor.render({"retrieval_timestamp": "2026-01-01T00:00:00+00:00", "fresh_candidates_discovered": 4, "event_root_valid": 3, "time_valid": 2, "surface_leakage_pass": 1, "final_eligible_events": 1, "p580_used": 1, "p585_fallback_used": 0, "families_count": 0, "status": "RUNNING"})
    assert "Candidates=4" in output and "P580=1" in output and "Status=RUNNING" in output


def test_pairing_invariants_and_insufficient_pairable() -> None:
    events = [{"qid": f"Q{i}", "canonical_identity": f"Q{i}", "canonical_time": f"2000-01-{i:02d}T00:00:00Z"} for i in range(1, 9)]
    pairs = RUNNER.pair_events(events, target_families=4)
    assert len(pairs) == 4
    ids = [item["canonical_identity"] for pair in pairs for item in (pair["event_a"], pair["event_b"])]
    assert len(ids) == len(set(ids))
    assert {pair["direction"] for pair in pairs} == {"EARLIER_TO_LATER", "LATER_TO_EARLIER"}
    same_date = [{"qid": f"Q{i}", "canonical_identity": f"Q{i}", "canonical_time": "2000-01-01T00:00:00Z"} for i in range(4)]
    with pytest.raises(RuntimeError, match="INSUFFICIENT_PAIRABLE"):
        RUNNER.pair_events(same_date, target_families=1)


def test_publication_guards(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="SYNTHETIC_CANONICAL"):
        RUNNER.publish_canonical({"a.json": {}}, tmp_path / "canonical", synthetic=True)
    target = tmp_path / "canonical"
    target.mkdir()
    with pytest.raises(RuntimeError, match="ALREADY_EXISTS"):
        RUNNER.publish_canonical({"a.json": {}}, target)


def test_atomic_publication_to_new_noncanonical_fixture(tmp_path: Path) -> None:
    target = tmp_path / "published"
    RUNNER.publish_canonical({"eligible.json": {"count": 440}, "families.json": {"count": 220}}, target)
    assert (target / "eligible.json").exists()
    assert not list(tmp_path.glob(".*published.*"))


def test_preflight_mode_does_not_start_run() -> None:
    assert RUNNER.main(["--preflight"]) == 0
