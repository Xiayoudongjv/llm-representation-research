import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP027_ENG = ROOT / "experiments" / "exp027" / "engineering"
if str(EXP027_ENG) not in sys.path:
    sys.path.insert(0, str(EXP027_ENG))

import exp027_progress as progress


FORBIDDEN_TERMS = ["rho", "sdi", "low_d", "low-d", "ci", "support", "route", "condition", "model_comparison"]


def test_report_and_state_are_outcome_blind(tmp_path, capsys):
    helper = progress.OutcomeBlindProgress(state_path=tmp_path / "state.json")
    helper.report(
        "BOOTSTRAP",
        completed=1200,
        total=5000,
        eta_seconds=42.0,
        heartbeat=True,
        publication_status="PENDING",
    )
    out = capsys.readouterr().out.lower()
    assert "stage=bootstrap" in out
    assert "completed=1200" in out
    assert "total=5000" in out
    assert "percent=24.0" in out
    assert "publication_status=pending" in out
    for term in FORBIDDEN_TERMS:
        assert term not in out

    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert set(state).issubset(progress.ALLOWED_STATE_KEYS)
    assert state["completed"] == 1200
    assert state["total"] == 5000
    assert state["percent"] == 24.0
    for term in FORBIDDEN_TERMS:
        assert term not in json.dumps(state).lower()


def test_percent_is_calculated_when_not_supplied(tmp_path, capsys):
    helper = progress.OutcomeBlindProgress(state_path=tmp_path / "state.json")
    helper.report("BOOTSTRAP", completed=2500, total=5000)
    out = capsys.readouterr().out
    assert "percent=50.0" in out
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert state["percent"] == 50.0


def test_state_file_replaces_atomically_without_tmp_leftover(tmp_path):
    helper = progress.OutcomeBlindProgress(state_path=tmp_path / "state.json")
    helper.write_state("PREPARE", completed=1, total=10)
    helper.write_state("BOOTSTRAP", completed=200, total=5000)
    assert list(tmp_path.glob("state.json*")) == [tmp_path / "state.json"]


def test_progress_state_rejects_disallowed_keys(tmp_path):
    helper = progress.OutcomeBlindProgress(state_path=tmp_path / "state.json")
    try:
        helper.write_state("BAD", completed=1, total=10)
        state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
        state["rho"] = 0.5
        progress._atomic_write_json(tmp_path / "bad.json", state)
        helper._validate_state(state)
    except ValueError:
        return
    raise AssertionError("expected forbidden progress field to be rejected")
