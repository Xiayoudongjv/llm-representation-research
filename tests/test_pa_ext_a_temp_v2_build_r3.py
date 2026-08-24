"""Offline qualification for the WDQS-specific TEMP-V2 R3 query plan."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
AMENDMENT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_wdqs_backend_amendment.json"
SPEC = importlib.util.spec_from_file_location("temp_v2_runner_r3", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def test_wdqs_query_uses_inverse_root_traversal() -> None:
    query = RUNNER.wdqs_event_page_query(100, 0)
    assert "VALUES ?root { wd:Q1190554 wd:Q1656682 }" in query
    assert "?root ^wdt:P279* ?class ." in query
    assert "?class ^wdt:P31 ?item ." in query
    assert "?item wdt:P31 ?class" not in query
    assert "?class wdt:P279* ?root" not in query


def test_qlever_historical_query_is_unchanged_in_direction() -> None:
    query = RUNNER.event_page_query(100, 0)
    assert "?item wdt:P31 ?class ." in query
    assert "?class wdt:P279* ?root ." in query
    assert "?root ^wdt:P279* ?class" not in query


def test_wdqs_fetch_event_page_uses_wdqs_query_only() -> None:
    captured: list[str] = []

    def request(query: str):
        captured.append(query)
        return 200, {"results": {"bindings": []}}

    client = RUNNER.WikidataQueryServiceClient(request=request, sleep=lambda _: None)
    assert client.fetch_event_page(100, 300) == {"results": {"bindings": []}}
    assert captured == [RUNNER.wdqs_event_page_query(100, 300)]


def test_same_output_contract_and_english_label_requirement() -> None:
    query = RUNNER.wdqs_event_page_query(100, 300)
    assert "SELECT DISTINCT ?item ?class ?label WHERE" in query
    assert 'FILTER(lang(?label)="en")' in query
    assert RUNNER.main_view_filter() in query


def test_same_order_limit_and_offset() -> None:
    query = RUNNER.wdqs_event_page_query(100, 1700)
    assert "ORDER BY ASC(?item) ASC(?class)" in query
    assert "LIMIT 100" in query
    assert "OFFSET 1700" in query


def test_query_has_frozen_roots_once_and_balanced_syntax() -> None:
    query = RUNNER.wdqs_event_page_query(100, 0)
    assert query.count("wd:Q1190554") == 1
    assert query.count("wd:Q1656682") == 1
    assert query.count("{") == query.count("}")
    assert query.strip().endswith("OFFSET 0")


def test_query_parameter_guard_is_preserved() -> None:
    with pytest.raises(ValueError):
        RUNNER.wdqs_event_page_query(0, 0)
    with pytest.raises(ValueError):
        RUNNER.wdqs_event_page_query(100, -1)


def test_frozen_authorities_and_freshness_are_unchanged() -> None:
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == RUNNER.PROTOCOL_SHA256
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    assert RUNNER.historical_content_hash(amendment, "amendment_sha256") == RUNNER.WDQS_AMENDMENT_SHA256
    info = RUNNER.load_freshness_exclusion_authority()
    assert info["date_pool_count"] == 3550
    assert info["v8_qid_count"] == 6695
    assert info["union_count"] == 6695


def test_downstream_440_to_220_and_zero_data_resume_are_unchanged() -> None:
    events = [
        {"qid": f"Q{i:06d}", "canonical_identity": f"Q{i:06d}|P585|{1900 + i}-01-01", "canonical_time": f"{1900 + i:04d}-01-01T00:00:00Z", "coarse_class": f"QCLASS{i % 10}"}
        for i in range(440)
    ]
    assert len(RUNNER.pair_events(RUNNER.select_events(events, target=440, class_cap=44), target_families=220)) == 220
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({"status": "PRODUCTION_CORE_FAILED", "current_state": "TERMINAL"})
    resumed = RUNNER.prepare_checkpoint_for_resume(checkpoint)
    assert resumed["resume_reason"] == "ZERO_DATA_FAILED_ATTEMPT_RESTART"
