"""Focused offline qualification for TEMPORAL_SOURCE_V2 CLI wiring R1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).parents[1]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
PROTOCOL_PATH = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
SPEC = importlib.util.spec_from_file_location("temp_v2_runner_r1", RUNNER_PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(RUNNER)


class FakeClient:
    def __init__(self, *, failure: Exception | None = None):
        self.failure = failure
        self.preflight_calls = 0

    def preflight(self):
        self.preflight_calls += 1
        if self.failure is not None:
            raise self.failure
        return {"status": 200, "endpoint": RUNNER.QLEVER_ENDPOINT, "graph_scope": "UNIFIED"}


def test_preflight_mode_does_not_call_production_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden():
        raise AssertionError("preflight must not call run_production")

    monkeypatch.setattr(RUNNER, "run_production", forbidden)
    assert RUNNER.main(["--preflight"]) == 0


def test_run_mode_calls_production_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []

    def fake_run():
        calls.append(True)
        return {"status": "MOCK_TERMINAL"}

    monkeypatch.setattr(RUNNER, "run_production", fake_run)
    assert RUNNER.main(["--run"]) == 0
    assert calls == [True]


def test_backend_health_failure_is_persisted_fail_closed(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.json"
    result = RUNNER.run_production(
        client=FakeClient(failure=RuntimeError("synthetic backend unavailable")),
        checkpoint_path=checkpoint_path,
        production_core=lambda *_: pytest.fail("core must not run after gate failure"),
    )
    assert result["status"] == "BACKEND_PREFLIGHT_FAILED"
    persisted = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    assert persisted["status"] == "BACKEND_PREFLIGHT_FAILED"
    assert persisted["current_state"] == "TERMINAL"


def test_run_resume_passes_authoritative_checkpoint_to_core(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint = RUNNER.initial_checkpoint(timestamp="2026-08-24T00:00:00+00:00")
    checkpoint.update({"status": "RUNNING", "current_acquisition_offset": 700})
    RUNNER.write_checkpoint(checkpoint_path, checkpoint)
    seen = []

    def fake_core(_client, resumed):
        seen.append(resumed["current_acquisition_offset"])
        return {"status": "SOURCE_EXHAUSTED", "full_acquisition_performed": False}

    result = RUNNER.run_production(client=FakeClient(), checkpoint_path=checkpoint_path, production_core=fake_core)
    assert result["status"] == "SOURCE_EXHAUSTED"
    assert seen == [700]


def test_run_does_not_bypass_checkpoint_authority(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint = RUNNER.initial_checkpoint()
    checkpoint["protocol_sha256"] = "wrong"
    RUNNER.write_checkpoint(checkpoint_path, checkpoint)
    with pytest.raises(RuntimeError, match="AUTHORITY_MISMATCH_protocol_sha256"):
        RUNNER.run_production(client=FakeClient(), checkpoint_path=checkpoint_path)


def test_run_does_not_bypass_publication_guard(tmp_path: Path) -> None:
    checkpoint_path = tmp_path / "checkpoint.json"

    def forbidden_publication(_bundle):
        RUNNER.publish_canonical({"synthetic.json": {}}, tmp_path / "out", synthetic=True)

    result = RUNNER.run_production(client=FakeClient(), checkpoint_path=checkpoint_path, production_core=forbidden_publication)
    assert result["status"] == "PRODUCTION_CORE_FAILED"
    assert not (tmp_path / "out").exists()


def test_protocol_sha_is_unchanged() -> None:
    assert hashlib.sha256(PROTOCOL_PATH.read_bytes()).hexdigest() == RUNNER.PROTOCOL_SHA256
    assert RUNNER.PROTOCOL_SHA256 == "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"


def test_deterministic_selection_remains_unchanged() -> None:
    events = [
        {"qid": f"Q{i}", "canonical_identity": f"Q{i}|P585|2000-{i:02d}", "coarse_class": f"QCLASS{i % 3}", "canonical_time": f"2000-01-{i:02d}T00:00:00Z"}
        for i in range(1, 10)
    ]
    assert RUNNER.select_events(events, target=6, class_cap=3) == RUNNER.select_events(events, target=6, class_cap=3)
