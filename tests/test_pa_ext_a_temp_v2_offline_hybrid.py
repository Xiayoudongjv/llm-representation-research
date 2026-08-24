"""Synthetic qualification for the final TEMP-V2 offline-hybrid path."""

from __future__ import annotations

import bz2
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2_offline.py"
SPEC = importlib.util.spec_from_file_location("temp_v2_offline_hybrid", MODULE_PATH)
OFFLINE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(OFFLINE)


def _uri(qid: str) -> str:
    return f"<http://www.wikidata.org/entity/{qid}>"


def _triple(subject: str, predicate: str, obj: str, *, literal: bool = False, language: str | None = None) -> str:
    value = json.dumps(obj, ensure_ascii=False) + (f"@{language}" if language else "") if literal else _uri(obj)
    return f"{_uri(subject)} <{predicate}> {value} .\n"


def _dump(tmp_path: Path) -> Path:
    lines = [
        _triple("Q100", OFFLINE.P279_URI, "Q1190554"),
        _triple("Q101", OFFLINE.P279_URI, "Q100"),
        _triple("Q102", OFFLINE.P279_URI, "Q1190554"),
        _triple("Q102", OFFLINE.P279_URI, "Q1656682"),
        _triple("Q200", OFFLINE.P279_URI, "Q201"),
        _triple("Q201", OFFLINE.P279_URI, "Q200"),
        _triple("Q300", OFFLINE.P279_URI, "Q301"),
        _triple("Q1", OFFLINE.P31_URI, "Q100"),
        _triple("Q2", OFFLINE.P31_URI, "Q101"),
        _triple("Q3", OFFLINE.P31_URI, "Q102"),
        _triple("Q4", OFFLINE.P31_URI, "Q101"),
        _triple("Q5", OFFLINE.P31_URI, "Q101"),
        _triple("Q2", OFFLINE.RDFS_LABEL_URI, "Safe event", literal=True, language="en"),
        _triple("Q3", OFFLINE.RDFS_LABEL_URI, "Bilingual event", literal=True, language="en"),
        _triple("Q5", OFFLINE.RDFS_LABEL_URI, "非英文", literal=True, language="zh"),
    ]
    path = tmp_path / "mini-wikidata.nt.bz2"
    with bz2.open(path, "wb") as handle:
        handle.write("".join(lines).encode("utf-8"))
    return path


def _time_claim(property_name: str, time_value: str, precision: int = 11, calendar: str = "Q1985727") -> dict:
    return {
        property_name: [{
            "mainsnak": {
                "snaktype": "value",
                "datavalue": {"value": {"time": time_value, "precision": precision, "calendarmodel": _uri(calendar)[1:-1]}},
            }
        }]
    }


def _entity(qid: str, label: str, claims: dict) -> dict:
    return {"id": qid, "labels": {"en": {"language": "en", "value": label}}, "claims": claims}


def _normalized_time(property_name: str, time_value: str = "+2000-01-01T00:00:00Z", precision: int = 11, calendar: str = "Q1985727") -> dict:
    return {"property": property_name, "time_value": time_value, "precision": precision, "calendar": calendar}


def test_streaming_bz2_reader_is_linewise_and_reports_bounded_progress(tmp_path: Path) -> None:
    path = _dump(tmp_path)
    counters = OFFLINE.ProgressCounters(path.stat().st_size)
    triples = list(OFFLINE.iter_nt_triples(path, counters))
    assert len(triples) == 15
    assert counters.compressed_file_size_bytes == path.stat().st_size
    assert counters.compressed_file_position_bytes is None
    assert counters.triples_scanned == 15
    with pytest.raises(FileNotFoundError):
        list(OFFLINE.iter_nt_triples(tmp_path / "missing.nt.bz2"))


def test_root_closure_handles_direct_multihop_cycle_disconnected_and_both_roots(tmp_path: Path) -> None:
    path = _dump(tmp_path)
    parents, compatible, _ = OFFLINE.scan_p279_closure(path)
    assert parents["Q100"] == {"Q1190554"}
    assert {"Q1190554", "Q100", "Q101", "Q102", "Q1656682"} <= compatible
    assert "Q200" not in compatible
    assert "Q300" not in compatible


def test_structural_pass_filters_prior_ids_before_hydration(tmp_path: Path) -> None:
    path = _dump(tmp_path)
    parents, compatible, _ = OFFLINE.scan_p279_closure(path)
    candidates, _ = OFFLINE.scan_p31_candidates(path, compatible)
    assert set(candidates) == {"Q1", "Q2", "Q3", "Q4", "Q5"}
    labels, _ = OFFLINE.scan_labels(path, set(candidates) - {"Q1"})
    assert labels == {"Q2": "Safe event", "Q3": "Bilingual event"}
    snapshot = OFFLINE.build_structural_snapshot(path, tmp_path / "work", exclusions={"Q1"})
    assert snapshot["counts"] == {
        "structural_candidates_total": 5,
        "prior_identity_rejects": 1,
        "fresh_structural_candidates": 4,
        "labels_collected": 2,
    }
    assert all(row["qid"] != "Q1" for row in snapshot["candidates"])


def test_checkpoint_does_not_silently_restart_partial_scan(tmp_path: Path) -> None:
    path = _dump(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    checkpoint = work / "offline_checkpoint.json"
    checkpoint.write_text(json.dumps({"phase": "PASS1_P279_RUNNING", "status": "PASS1_P279_RUNNING"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="EXPLICIT_RESUME"):
        OFFLINE.build_structural_snapshot(path, work, exclusions=set(), checkpoint_path=checkpoint)


def test_entity_hydration_reuses_cache_and_reconstructs_full_time_metadata(tmp_path: Path) -> None:
    calls: list[list[str]] = []

    def request(qids: list[str]) -> dict:
        calls.append(qids)
        return {"entities": {qid: _entity(qid, f"Event {qid}", _time_claim("P585", "+2000-01-01T00:00:00Z")) for qid in qids}}

    candidates = [{"qid": "Q2", "direct_p31_qids": ["Q101"], "label": "Safe event"}]
    client = OFFLINE.WikidataEntityHydrationClient(cache_dir=tmp_path / "cache", request=request, batch_size=1, sleep=lambda _: None)
    first = client.hydrate(candidates, tmp_path / "hydration.json")
    second = client.hydrate(candidates, tmp_path / "hydration.json")
    assert calls == [["Q2"]]
    assert first == second
    assert first[0]["times"][0]["property"] == "P585"
    assert first[0]["times"][0]["calendar"] == "Q1985727"


def test_hydration_rejects_incomplete_or_malformed_entities(tmp_path: Path) -> None:
    client = OFFLINE.WikidataEntityHydrationClient(cache_dir=tmp_path / "cache", request=lambda _: {"entities": {}}, sleep=lambda _: None)
    with pytest.raises(RuntimeError, match="INCOMPLETE"):
        client.hydrate([{"qid": "Q2", "direct_p31_qids": ["Q101"]}], tmp_path / "hydration.json")


def test_full_entity_candidate_reuses_existing_scientific_rules(tmp_path: Path) -> None:
    candidate = {
        "qid": "Q2",
        "direct_p31_qids": ["Q101"],
        "label": "Safe event",
        "times": [_normalized_time("P580", "+2000-01-01T00:00:00Z"), _normalized_time("P585", "+1999-01-01T00:00:00Z")],
    }
    event, reason = OFFLINE.finalize_hydrated_candidates([candidate], {"Q101": {"Q100"}, "Q100": {"Q1190554"}}, set())
    assert reason == {"ELIGIBLE": 1}
    assert event[0]["canonical_property"] == "P580"


def test_invalid_calendar_precision_and_surface_are_rejected_by_frozen_logic() -> None:
    parents = {"Q101": {"Q1190554"}}
    base = {"qid": "Q2", "direct_p31_qids": ["Q101"], "label": "Safe event"}
    for time_record in (
        _time_claim("P585", "+2000-01-01T00:00:00Z", precision=10)["P585"],
        _time_claim("P585", "+2000-01-01T00:00:00Z", calendar="Q2")["P585"],
    ):
        normalized = _normalized_time("P585", precision=10) if time_record[0]["mainsnak"]["datavalue"]["value"]["precision"] == 10 else _normalized_time("P585", calendar="Q2")
        candidate = {**base, "times": [normalized]}
        events, reasons = OFFLINE.finalize_hydrated_candidates([candidate], parents, set())
        assert not events and list(reasons.values()) == [1]
    leaking = {**base, "label": "Event 2001", "times": [_normalized_time("P585")]}
    events, reasons = OFFLINE.finalize_hydrated_candidates([leaking], parents, set())
    assert not events and reasons == {"SURFACE_LEAKAGE_REJECT": 1}


def test_selection_and_pairing_match_frozen_440_to_220_path() -> None:
    events = [
        {"qid": f"Q{i:06d}", "canonical_identity": f"Q{i:06d}|P585|{1900 + i}-01-01", "canonical_time": f"{1900 + i:04d}-01-01T00:00:00Z", "coarse_class": f"QCLASS{i % 10}"}
        for i in range(440)
    ]
    selected = OFFLINE.RUNNER.select_events(events, target=440, class_cap=44)
    assert len(OFFLINE.RUNNER.pair_events(selected, target_families=220)) == 220


def test_preflight_is_local_and_reuses_frozen_exclusion_authority(tmp_path: Path) -> None:
    path = _dump(tmp_path)
    result = OFFLINE.preflight(path, work_dir=tmp_path / "work")
    assert result["valid"] is True
    assert result["freshness_union_count"] == 6695
    assert result["canonical_output_exists"] is False


def test_normalized_offline_candidate_matches_online_candidate_contract() -> None:
    candidate = {
        "qid": "Q2",
        "direct_p31_qids": ["Q101"],
        "label": "Safe event",
        "times": [_normalized_time("P585")],
    }
    parents = {"Q101": {"Q1190554"}}
    offline_event, _ = OFFLINE.finalize_hydrated_candidates([candidate], parents, set())
    online_event, _ = OFFLINE.RUNNER.prepare_candidate(candidate, set(), parents)
    assert offline_event == [online_event]
