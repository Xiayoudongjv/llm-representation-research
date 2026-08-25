"""Offline qualification for TEMP-V2 WDQS ID-first discovery and hydration."""

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
SPEC = importlib.util.spec_from_file_location("temp_v2_runner_r4", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def _binding(value: str, *, language: str | None = None) -> dict[str, str]:
    result = {"type": "uri", "value": value}
    if language is not None:
        result["type"] = "literal"
        result["xml:lang"] = language
    return result


def _row(item: str, clazz: str, label: str | None = None, *, language: str | None = None) -> dict[str, object]:
    row: dict[str, object] = {"item": _binding(f"http://www.wikidata.org/entity/{item}"), "class": _binding(f"http://www.wikidata.org/entity/{clazz}")}
    if label is not None:
        row["label"] = _binding(label, language=language)
    return row


def _normalized(records: list[dict[str, object]]) -> list[tuple[str, tuple[str, ...], str]]:
    return [(row["qid"], tuple(row["direct_p31_qids"]), row["label"]) for row in records]


def test_structural_query_does_not_project_label() -> None:
    query = RUNNER.wdqs_event_page_query(100, 0)
    assert "SELECT DISTINCT ?item ?class WHERE" in query
    assert "SELECT DISTINCT ?item ?class ?label WHERE" not in query


def test_structural_query_keeps_english_label_existence_guard() -> None:
    query = RUNNER.wdqs_event_page_query(100, 0)
    assert "FILTER EXISTS" in query
    assert "?item rdfs:label ?label" in query
    assert 'FILTER(lang(?label)="en")' in query


def test_inverse_roots_and_main_view_filter_are_preserved() -> None:
    query = RUNNER.wdqs_event_page_query(100, 0)
    assert "VALUES ?root { wd:Q1190554 wd:Q1656682 }" in query
    assert "?root ^wdt:P279* ?class ." in query
    assert "?class ^wdt:P31 ?item ." in query
    assert RUNNER.main_view_filter() in query


def test_structural_distinct_order_limit_and_offset_are_preserved() -> None:
    query = RUNNER.wdqs_event_page_query(100, 1700)
    assert "SELECT DISTINCT ?item ?class WHERE" in query
    assert "ORDER BY ASC(?item) ASC(?class)" in query
    assert "LIMIT 100" in query
    assert "OFFSET 1700" in query
    assert RUNNER.PAGE_SIZE == 100


def test_label_hydration_is_bounded_to_selected_page_qids() -> None:
    query = RUNNER.wdqs_label_hydration_query(["Q2", "Q1"])
    assert "VALUES ?item { wd:Q1 wd:Q2 }" in query
    assert "wd:Q999" not in query
    assert "SELECT DISTINCT ?item ?label WHERE" in query
    assert 'FILTER(lang(?label)="en")' in query


def test_wdqs_fetch_runs_structural_then_hydration_only_for_page() -> None:
    calls: list[str] = []
    structural = {"results": {"bindings": [_row("Q1", "Q10"), _row("Q2", "Q11")]}}
    labels = {"results": {"bindings": [_row("Q1", "Q0", "Alpha", language="en"), _row("Q2", "Q0", "Beta", language="en")]}}

    def request(query: str):
        calls.append(query)
        return 200, structural if len(calls) == 1 else labels

    client = RUNNER.WikidataQueryServiceClient(request=request, sleep=lambda _: None)
    result = client.fetch_event_page(100, 300)
    assert _normalized(RUNNER._parse_event_page(result)) == [("Q1", ("Q10",), "Alpha"), ("Q2", ("Q11",), "Beta")]
    assert len(calls) == 2
    assert "wd:Q1" in calls[1] and "wd:Q2" in calls[1]
    assert "wd:Q999" not in calls[1]


def test_old_and_new_fixture_contracts_are_identical() -> None:
    structural_rows = [_row(f"Q{100 + i}", f"Q{1000 + i % 4}") for i in range(98)]
    structural_rows.extend([_row("Q198", "Q1001"), _row("Q198", "Q1002")])
    labels = {f"Q{100 + i}": f"Event {i}" for i in range(99)}
    structural = {"results": {"bindings": structural_rows}}
    label_rows = [_row(qid, "Q1000", text, language="en") for qid, text in labels.items()]
    hydrated = RUNNER.hydrate_wdqs_event_page(structural, {"results": {"bindings": label_rows}})
    old_rows = [dict(row, label={"type": "literal", "xml:lang": "en", "value": labels[RUNNER._qid(row["item"]["value"])]}) for row in structural_rows]
    old_rows.append(dict(old_rows[0]))  # duplicate graph path, removed by the historical parser grouping
    old = RUNNER._parse_event_page({"results": {"bindings": old_rows}})
    new = RUNNER._parse_event_page(hydrated)
    assert _normalized(old) == _normalized(new)
    assert len(new) == 99
    assert len(new[-1]["direct_p31_qids"]) == 2


def test_unlabeled_item_cannot_enter() -> None:
    with pytest.raises(RuntimeError, match="MEMBERSHIP_DRIFT"):
        RUNNER.hydrate_wdqs_event_page({"results": {"bindings": [_row("Q1", "Q10")]}}, {"results": {"bindings": []}})


def test_non_english_only_item_cannot_enter() -> None:
    with pytest.raises(RuntimeError, match="LABEL_HYDRATION_INVALID"):
        RUNNER.hydrate_wdqs_event_page(
            {"results": {"bindings": [_row("Q1", "Q10")]}},
            {"results": {"bindings": [_row("Q1", "Q0", "非英文", language="zh")]}}
        )


def test_multiple_english_labels_fail_closed_under_historical_parser_contract() -> None:
    with pytest.raises(RuntimeError, match="MEMBERSHIP_DRIFT"):
        RUNNER.hydrate_wdqs_event_page(
            {"results": {"bindings": [_row("Q1", "Q10")]}},
            {"results": {"bindings": [_row("Q1", "Q0", "Alpha", language="en"), _row("Q1", "Q0", "A", language="en")]}}
        )


def test_pagination_boundary_and_nonzero_offset_are_unchanged() -> None:
    first = RUNNER.wdqs_event_page_query(100, 0)
    second = RUNNER.wdqs_event_page_query(100, 100)
    assert "LIMIT 100\nOFFSET 0" in first
    assert "LIMIT 100\nOFFSET 100" in second


def test_qlever_query_path_is_unchanged() -> None:
    query = RUNNER.event_page_query(100, 0)
    assert "?item wdt:P31 ?class ." in query
    assert "?class wdt:P279* ?root ." in query
    assert "SELECT DISTINCT ?item ?class ?label WHERE" in query


def test_authorities_freshness_resume_and_downstream_path_unchanged() -> None:
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == RUNNER.PROTOCOL_SHA256
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    assert RUNNER.historical_content_hash(amendment, "amendment_sha256") == RUNNER.WDQS_AMENDMENT_SHA256
    info = RUNNER.load_freshness_exclusion_authority()
    assert info["union_count"] == 6695
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({"status": "PRODUCTION_CORE_FAILED", "current_state": "TERMINAL"})
    assert RUNNER.prepare_checkpoint_for_resume(checkpoint)["resume_reason"] == "ZERO_DATA_FAILED_ATTEMPT_RESTART"
    events = [
        {"qid": f"Q{i:06d}", "canonical_identity": f"Q{i:06d}|P585|{1900 + i}-01-01", "canonical_time": f"{1900 + i:04d}-01-01T00:00:00Z", "coarse_class": f"QCLASS{i % 10}"}
        for i in range(440)
    ]
    assert len(RUNNER.pair_events(RUNNER.select_events(events, target=440, class_cap=44), target_families=220)) == 220
