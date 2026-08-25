"""Offline qualification for the TEMPORAL_SOURCE_V2 WDQS backend amendment."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
SPEC = importlib.util.spec_from_file_location("temp_v2_wdqs_runner", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def binding(**values: str) -> dict:
    return {key: {"type": "uri", "value": value} for key, value in values.items()}


def test_wdqs_health_and_ontology_preflight_pass() -> None:
    responses = [
        (200, {"head": {"vars": ["health"]}, "results": {"bindings": []}}),
        (200, {"head": {"vars": ["parent"]}, "results": {"bindings": [binding(parent="http://www.wikidata.org/entity/Q1914636")]}}),
    ]
    client = RUNNER.WikidataQueryServiceClient(request=lambda _query: responses.pop(0), sleep=lambda _delay: None)
    result = client.preflight()
    assert result["endpoint"] == RUNNER.WDQS_ENDPOINT
    assert result["backend"] == RUNNER.WDQS_BACKEND_NAME
    assert result["backend_amendment_sha256"] == RUNNER.WDQS_AMENDMENT_SHA256


def test_wdqs_response_parsing_preserves_query_fields() -> None:
    page = {
        "results": {
            "bindings": [
                binding(item="http://www.wikidata.org/entity/Q1", **{"class": "http://www.wikidata.org/entity/Q100", "label": "An event"}),
                binding(item="http://www.wikidata.org/entity/Q1", **{"class": "http://www.wikidata.org/entity/Q101", "label": "An event"}),
            ]
        }
    }
    parsed = RUNNER._parse_event_page(page)
    assert parsed == [{"qid": "Q1", "direct_p31_qids": ["Q100", "Q101"], "label": "An event"}]
    times = RUNNER._parse_time_metadata(
        {"results": {"bindings": [binding(item="http://www.wikidata.org/entity/Q1", property="P585", timeValue="+2000-01-01T00:00:00Z", precision="11", calendar="http://www.wikidata.org/entity/Q1985727")]}}
    )
    assert times["Q1"][0]["property"] == "P585"
    parents = RUNNER._parse_parent_metadata(
        {"results": {"bindings": [binding(**{"class": "http://www.wikidata.org/entity/Q100", "parent": "http://www.wikidata.org/entity/Q1190554"})]}}
    )
    assert parents == {"Q100": {"Q1190554"}}


def test_wdqs_health_failure_is_bounded_and_fail_closed() -> None:
    sleeps: list[float] = []
    client = RUNNER.WikidataQueryServiceClient(request=lambda _query: (503, {}), sleep=sleeps.append)
    with pytest.raises(RuntimeError, match="WDQS_REQUEST_FAILED"):
        client.preflight()
    assert len(sleeps) == RUNNER.MAX_RETRIES - 1


def test_wdqs_endpoint_identity_guard() -> None:
    client = RUNNER.WikidataQueryServiceClient(
        request=lambda _query: (200, {"results": {"bindings": [{"health": {"value": "1"}}]}}),
        sleep=lambda _delay: None,
    )
    client.endpoint = "https://mirror.example/sparql"
    with pytest.raises(RuntimeError, match="ENDPOINT_IDENTITY_FAILED"):
        client.preflight()


def test_wdqs_ontology_visibility_guard() -> None:
    responses = [
        (200, {"results": {"bindings": []}}),
        (200, {"results": {"bindings": []}}),
    ]
    client = RUNNER.WikidataQueryServiceClient(request=lambda _query: responses.pop(0), sleep=lambda _delay: None)
    with pytest.raises(RuntimeError, match="ONTOLOGY_VISIBILITY_FAILED"):
        client.preflight()


def test_wdqs_retry_reaches_success_without_parallelism() -> None:
    responses = [(502, {}), (503, {}), (200, {"ok": True})]
    sleeps: list[float] = []
    client = RUNNER.WikidataQueryServiceClient(request=lambda _query: responses.pop(0), sleep=sleeps.append)
    assert client.request("SELECT 1") == (200, {"ok": True})
    assert sleeps == [1.0, 2.0]


def test_wdqs_checkpoint_binds_base_and_amendment_authority(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    checkpoint = RUNNER.initial_checkpoint(
        backend=RUNNER.WDQS_BACKEND_NAME,
        endpoint=RUNNER.WDQS_ENDPOINT,
        graph_scope="OFFICIAL_MAIN_GRAPH",
        backend_amendment_sha256=RUNNER.WDQS_AMENDMENT_SHA256,
    )
    RUNNER.write_checkpoint(path, checkpoint)
    loaded = RUNNER.load_checkpoint(
        path,
        expected_backend=RUNNER.WDQS_BACKEND_NAME,
        expected_endpoint=RUNNER.WDQS_ENDPOINT,
        expected_graph_scope="OFFICIAL_MAIN_GRAPH",
        expected_backend_amendment_sha256=RUNNER.WDQS_AMENDMENT_SHA256,
    )
    assert loaded["protocol_sha256"] == RUNNER.PROTOCOL_SHA256
    assert loaded["backend_amendment_sha256"] == RUNNER.WDQS_AMENDMENT_SHA256


def test_wdqs_checkpoint_amendment_mismatch_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "checkpoint.json"
    checkpoint = RUNNER.initial_checkpoint(
        backend=RUNNER.WDQS_BACKEND_NAME,
        endpoint=RUNNER.WDQS_ENDPOINT,
        graph_scope="OFFICIAL_MAIN_GRAPH",
        backend_amendment_sha256="wrong",
    )
    RUNNER.write_checkpoint(path, checkpoint)
    with pytest.raises(RuntimeError, match="AUTHORITY_MISMATCH_backend_amendment_sha256"):
        RUNNER.load_checkpoint(
            path,
            expected_backend=RUNNER.WDQS_BACKEND_NAME,
            expected_endpoint=RUNNER.WDQS_ENDPOINT,
            expected_graph_scope="OFFICIAL_MAIN_GRAPH",
            expected_backend_amendment_sha256=RUNNER.WDQS_AMENDMENT_SHA256,
        )


def test_wdqs_run_fail_closed_before_acquisition(tmp_path: Path) -> None:
    class FailingWDQS:
        backend_name = RUNNER.WDQS_BACKEND_NAME
        endpoint = RUNNER.WDQS_ENDPOINT
        graph_scope = "OFFICIAL_MAIN_GRAPH"
        backend_amendment_sha256 = RUNNER.WDQS_AMENDMENT_SHA256

        def preflight(self):
            raise RuntimeError("synthetic WDQS outage")

    checkpoint_path = tmp_path / "checkpoint.json"
    result = RUNNER.run_production(
        client=FailingWDQS(),
        checkpoint_path=checkpoint_path,
        production_core=lambda *_: pytest.fail("acquisition must not start after WDQS preflight failure"),
    )
    assert result["status"] == "BACKEND_PREFLIGHT_FAILED"
    persisted = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert persisted["backend"] == RUNNER.WDQS_BACKEND_NAME
    assert persisted["current_state"] == "TERMINAL"


def test_existing_deterministic_440_to_220_primitives_are_reused() -> None:
    events = [
        {"qid": f"Q{i}", "canonical_identity": f"Q{i}", "canonical_time": f"2000-01-{i:03d}T00:00:00Z", "coarse_class": f"QCLASS{i // 40}"}
        for i in range(440)
    ]
    selected = RUNNER.select_events(events, target=440, class_cap=44)
    assert len(RUNNER.pair_events(selected, target_families=220)) == 220
