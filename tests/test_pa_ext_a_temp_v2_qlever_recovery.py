"""Offline qualification for the TEMP-V2 QLever recovery repair."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
SPEC = importlib.util.spec_from_file_location("temp_v2_qlever_recovery", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def test_event_page_query_completes_main_view_prefixes_and_qid_gate() -> None:
    query = RUNNER.event_page_query(100, 0)
    for prefix in (
        "PREFIX p: <http://www.wikidata.org/prop/>",
        "PREFIX ps: <http://www.wikidata.org/prop/statement/>",
        "PREFIX wikibase: <http://wikiba.se/ontology#>",
    ):
        assert prefix in query
    assert f'FILTER(REGEX(STR(?item), "{RUNNER.QID_URI_SPARQL_PATTERN}"))' in query
    assert "SELECT DISTINCT ?item ?class ?label WHERE" in query
    assert "ORDER BY ASC(?item) ASC(?class)" in query
    assert "LIMIT 100\nOFFSET 0" in query


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("http://www.wikidata.org/entity/Q1", "Q1"),
        ("http://www.wikidata.org/entity/Q42", "Q42"),
        ("http://www.wikidata.org/entity/Q10000008", "Q10000008"),
        ("http://www.wikidata.org/entity/L1000775", None),
        ("http://www.wikidata.org/entity/L1001291-S2", None),
        ("http://www.wikidata.org/entity/P31", None),
        ("http://www.wikidata.org/entity/Q0", None),
        ("http://www.wikidata.org/entity/Qabc", None),
        ("http://example.org/entity/Q42", None),
        ("Q42", None),
    ],
)
def test_qid_gate_matches_frozen_parser_identity_domain(value: str, expected: str | None) -> None:
    assert RUNNER._qid(value) == expected
    assert bool(RUNNER.QID_URI_RE.fullmatch(value)) is (expected is not None)


def test_lexeme_rows_are_outside_query_page_identity_domain() -> None:
    query = RUNNER.event_page_query(RUNNER.PAGE_SIZE, 0)
    assert RUNNER.QID_URI_SPARQL_PATTERN in query
    assert RUNNER._qid("http://www.wikidata.org/entity/L1000775") is None
    assert RUNNER._qid("http://www.wikidata.org/entity/Q1") == "Q1"


def test_qlever_client_endpoint_and_default_production_transport(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    created: list[str] = []

    class FakeQLever:
        backend_name = "QLever"
        endpoint = RUNNER.QLEVER_ENDPOINT
        graph_scope = RUNNER.GRAPH_SCOPE
        backend_amendment_sha256 = None

        def __init__(self) -> None:
            created.append("qlever")

        def preflight(self) -> dict[str, object]:
            return {"status": 200, "endpoint": self.endpoint}

    class ForbiddenWDQS:
        def __init__(self) -> None:
            created.append("wdqs")
            raise AssertionError("WDQS must not be the default transport")

    monkeypatch.setattr(RUNNER, "QLeverClient", FakeQLever)
    monkeypatch.setattr(RUNNER, "WikidataQueryServiceClient", ForbiddenWDQS)

    def fake_core(client: object, checkpoint: dict[str, object]) -> dict[str, object]:
        assert isinstance(client, FakeQLever)
        return {"status": "TEST_TERMINAL", "full_acquisition_performed": False}

    result = RUNNER.run_production(checkpoint_path=tmp_path / "checkpoint.json", production_core=fake_core)
    assert result["status"] == "TEST_TERMINAL"
    assert created == ["qlever"]


def test_injected_client_remains_supported(tmp_path: Path) -> None:
    class Injected:
        backend_name = "QLever"
        endpoint = RUNNER.QLEVER_ENDPOINT
        graph_scope = RUNNER.GRAPH_SCOPE
        backend_amendment_sha256 = None

        def preflight(self) -> dict[str, object]:
            return {"status": 200}

    result = RUNNER.run_production(
        client=Injected(),
        checkpoint_path=tmp_path / "checkpoint.json",
        production_core=lambda _client, _checkpoint: {"status": "INJECTED", "full_acquisition_performed": False},
    )
    assert result["status"] == "INJECTED"


def test_zero_data_qlever_checkpoint_resumes_without_erasing_evidence() -> None:
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({
        "status": "BACKEND_PREFLIGHT_FAILED",
        "current_state": "TERMINAL",
        "error": "historical qlever outage",
    })
    resumed = RUNNER.prepare_checkpoint_for_resume(checkpoint)
    assert resumed["resume_reason"] == "ZERO_DATA_FAILED_ATTEMPT_RESTART"
    assert resumed["previous_terminal_status"] == "BACKEND_PREFLIGHT_FAILED"
    assert resumed["previous_terminal_error"] == "historical qlever outage"
    assert resumed["current_acquisition_offset"] == 0
    assert resumed["artifact_chunk_count"] == 0


def test_nonzero_qlever_checkpoint_cannot_be_silently_reset() -> None:
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({
        "status": "PRODUCTION_CORE_FAILED",
        "current_state": "TERMINAL",
        "current_acquisition_offset": 100,
        "fresh_candidates_discovered": 1,
        "artifact_chunk_count": 1,
    })
    with pytest.raises(RuntimeError, match="NONZERO_TERMINAL_CHECKPOINT"):
        RUNNER.prepare_checkpoint_for_resume(checkpoint)


def test_protocol_and_downstream_authorities_unchanged() -> None:
    assert hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() == RUNNER.PROTOCOL_SHA256
    assert RUNNER.PAGE_SIZE == 100
    assert RUNNER.TARGET_EVENTS == 440
    assert RUNNER.RESERVE_EVENTS == 600
    assert RUNNER.TARGET_FAMILIES == 220
    events = [
        {
            "qid": f"Q{i:06d}",
            "canonical_identity": f"Q{i:06d}|P585|{1900 + i}-01-01",
            "canonical_time": f"{1900 + i:04d}-01-01T00:00:00Z",
            "coarse_class": f"QCLASS{i % 10}",
        }
        for i in range(440)
    ]
    selected = RUNNER.select_events(events, target=440, class_cap=44)
    assert len(RUNNER.pair_events(selected, target_families=220)) == 220
