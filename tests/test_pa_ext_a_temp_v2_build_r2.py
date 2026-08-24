"""Offline qualification for TEMP-V2 freshness authority binding R2."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
MANIFEST = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_001" / "date_valid_pool_manifest.json"
SPEC = importlib.util.spec_from_file_location("temp_v2_runner_r2", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


def _manifest_copy(tmp_path: Path, **changes: object) -> Path:
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    payload.update(changes)
    path = tmp_path / "date_valid_pool_manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def test_unchanged_manifest_uses_historical_logical_authority() -> None:
    info = RUNNER.load_freshness_exclusion_authority()
    assert info["date_pool_count"] == 3550
    assert info["logical_manifest_sha256"] == RUNNER.EXPECTED_DATE_POOL_MANIFEST_SHA256


def test_raw_file_sha_is_not_the_scientific_authority() -> None:
    raw_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert raw_sha != RUNNER.EXPECTED_DATE_POOL_MANIFEST_SHA256
    assert RUNNER.historical_content_hash(json.loads(MANIFEST.read_text(encoding="utf-8")), "manifest_sha256") == RUNNER.EXPECTED_DATE_POOL_MANIFEST_SHA256


def test_altered_manifest_content_fails(tmp_path: Path) -> None:
    altered = _manifest_copy(tmp_path, status="ALTERED")
    with pytest.raises(RuntimeError, match="MANIFEST_AUTHORITY_MISMATCH"):
        RUNNER.load_freshness_exclusion_authority(manifest_path=altered)


def test_total_count_drift_fails(tmp_path: Path) -> None:
    altered = _manifest_copy(tmp_path, total_count=3549)
    with pytest.raises(RuntimeError, match="MANIFEST_AUTHORITY_MISMATCH"):
        RUNNER.load_freshness_exclusion_authority(manifest_path=altered)


def test_v8_authority_drift_fails(tmp_path: Path) -> None:
    altered = tmp_path / "v8_authority.json"
    altered.write_bytes((ROOT / "experiments" / "paper_a_ext_a" / "paper_a_ext_a_temporal_asset_source_v8.json").read_bytes() + b" ")
    with pytest.raises(RuntimeError, match="V8_AUTHORITY_MISMATCH"):
        RUNNER.load_freshness_exclusion_authority(v8_authority_path=altered)


def test_all_historical_date_pool_qids_load() -> None:
    info = RUNNER.load_freshness_exclusion_authority()
    assert info["date_pool_count"] == 3550
    assert len(info["date_pool_qids"]) == 3550


def test_v8_response_pages_load() -> None:
    info = RUNNER.load_freshness_exclusion_authority()
    assert info["v8_page_count"] == 67
    assert info["v8_qid_count"] == 6695


def test_metadata_sidecars_are_not_response_pages() -> None:
    raw_dir = ROOT / "experiments" / "paper_a_ext_a" / "data" / "raw" / "wikidata_v8"
    response_paths = RUNNER._frozen_v8_candidate_response_paths(raw_dir)
    assert len(response_paths) == 67
    assert all(not path.name.endswith(".meta.json") for path in response_paths)


def test_exclusion_union_is_deterministic() -> None:
    first = RUNNER.load_freshness_exclusion_authority()["excluded_qids"]
    second = RUNNER.load_freshness_exclusion_authority()["excluded_qids"]
    assert first == second
    assert len(first) == 6695


def test_old_identity_is_rejected_and_fresh_identity_passes() -> None:
    excluded = RUNNER.load_freshness_exclusion_authority()["excluded_qids"]
    old_qid = next(iter(excluded))
    rejected, reason = RUNNER.prepare_candidate(
        {"qid": old_qid, "direct_p31_qids": ["Q1190554"], "label": "A safe event", "times": []},
        excluded,
        {},
    )
    assert rejected is None and reason == "PRIOR_IDENTITY_REJECT"
    fresh, reason = RUNNER.prepare_candidate(
        {"qid": "Q999999999", "direct_p31_qids": ["Q1190554"], "label": "A safe event", "times": [{"property": "P585", "time_value": "+2001-01-01T00:00:00Z", "precision": 11, "calendar": "Q1985727"}]},
        excluded,
        {},
    )
    assert fresh is not None and reason == "ELIGIBLE"


def test_zero_data_terminal_checkpoint_can_resume() -> None:
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({"status": "PRODUCTION_CORE_FAILED", "current_state": "TERMINAL", "error": "freshness failure"})
    resumed = RUNNER.prepare_checkpoint_for_resume(checkpoint)
    assert resumed["status"] == "RESUMING"
    assert resumed["resume_reason"] == "ZERO_DATA_FAILED_ATTEMPT_RESTART"
    assert resumed["previous_terminal_error"] == "freshness failure"


def test_run_production_resumes_zero_data_checkpoint_without_network(tmp_path: Path) -> None:
    class OfflineClient:
        backend_name = "QLever"
        endpoint = RUNNER.QLEVER_ENDPOINT
        graph_scope = RUNNER.GRAPH_SCOPE
        backend_amendment_sha256 = None

        def preflight(self):
            return {"status": 200, "offline_fixture": True}

    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({"status": "PRODUCTION_CORE_FAILED", "current_state": "TERMINAL", "error": "freshness failure"})
    RUNNER.write_checkpoint(checkpoint_path, checkpoint)

    def fake_core(_client, resumed):
        assert resumed["resume_reason"] == "ZERO_DATA_FAILED_ATTEMPT_RESTART"
        return {"status": "SOURCE_EXHAUSTED", "full_acquisition_performed": False}

    result = RUNNER.run_production(client=OfflineClient(), checkpoint_path=checkpoint_path, production_core=fake_core)
    assert result["status"] == "SOURCE_EXHAUSTED"
    persisted = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert persisted["previous_terminal_status"] == "PRODUCTION_CORE_FAILED"


def test_nonzero_terminal_checkpoint_cannot_be_silently_reset() -> None:
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint.update({"status": "PRODUCTION_CORE_FAILED", "current_state": "TERMINAL", "fresh_candidates_discovered": 1})
    with pytest.raises(RuntimeError, match="NONZERO_TERMINAL"):
        RUNNER.prepare_checkpoint_for_resume(checkpoint)


def test_base_protocol_and_backend_amendment_are_unchanged() -> None:
    protocol = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
    amendment = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_wdqs_backend_amendment.json"
    assert hashlib.sha256(protocol.read_bytes()).hexdigest() == RUNNER.PROTOCOL_SHA256
    amendment_payload = json.loads(amendment.read_text(encoding="utf-8"))
    assert RUNNER.historical_content_hash(amendment_payload, "amendment_sha256") == RUNNER.WDQS_AMENDMENT_SHA256


def test_440_to_220_path_remains_unchanged() -> None:
    events = [
        {"qid": f"Q{i:06d}", "canonical_identity": f"Q{i:06d}|P585|{1900 + i}-01-01", "canonical_time": f"{1900 + i:04d}-01-01T00:00:00Z", "coarse_class": f"QCLASS{i % 10}"}
        for i in range(440)
    ]
    selected = RUNNER.select_events(events, target=440, class_cap=44)
    pairs = RUNNER.pair_events(selected, target_families=220)
    assert len(selected) == 440
    assert len(pairs) == 220
