"""Formal-pipeline qualification tests for EXP-027 (Task 102D).

These tests are synthetic/static only. They never load the real Llama model,
never access real FIT/DIAG/EVAL scientific content, and never create a formal
authorization or canonical scientific result.
"""

from __future__ import annotations

import ast
import copy
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP026_DIR = ROOT / "experiments" / "exp026"
EXP027_DIR = ROOT / "experiments" / "exp027"
EXP027_ENG = EXP027_DIR / "engineering"
for path in (str(ROOT), str(EXP026_DIR), str(EXP027_DIR), str(EXP027_ENG)):
    if path not in sys.path:
        sys.path.insert(0, path)

import run_exp027 as r
import validate_exp027_result as result_validator
import exp027_progress as progress
import run_exp026 as ref


RUNNER_PATH = EXP027_DIR / "run_exp027.py"
RESULT_VALIDATOR_PATH = EXP027_DIR / "validate_exp027_result.py"


def _read_source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _frozen_config() -> dict[str, Any]:
    return json.loads((EXP027_DIR / "exp027_frozen_design.json").read_text(encoding="utf-8"))


def _profile(distance: str, dominance: str, low_d: str) -> dict[str, str]:
    return {
        "distance_association_status": distance,
        "dominance_status": dominance,
        "low_d_recovery_status": low_d,
    }


def _valid_auth_payload() -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "classification": "EXP027_FORMAL_AUTHORIZATION",
        "experiment": "EXP-027",
        "purpose": "SINGLE_USE_FORMAL_RUN",
        "single_use": True,
        "authorized_execution_count": 1,
        "formal_mode": "--formal-run",
        "authorization_id": "102d-test-auth",
        "created_at_utc": "2026-08-22T00:00:00+00:00",
        "execution_binding": r.verify_exp027_authorities(r.ROOT),
    }


def _write_auth(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _minimal_result_payload() -> dict[str, Any]:
    profile = _profile("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED")
    route, status = result_validator.route_from_profile(
        profile,
        technical_valid=True,
        measurement_valid=True,
    )
    return {
        "schema_version": "1.0.0",
        "classification": "EXP027_SCIENTIFIC_RESULT",
        "experiment": "EXP-027",
        "created_at_utc": "2026-08-22T00:00:00+00:00",
        "attempt_status": "COMPLETED",
        "result_status": status,
        "scientific_status": "OBSERVED" if status == "VALID_REGISTERED_RESULT" else "NOT_OBSERVED",
        "profile": profile,
        "route": route,
        "technical_validity": True,
        "measurement_validity": True,
        "authorization_identity": {
            "authorization_id": "auth-id",
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
            "run_attempt_id": "attempt-id",
        },
        "execution_binding": {
            "repository_commit": "c" * 40,
            "runner_sha256": "d" * 64,
            "frozen_design_sha256": "e" * 64,
            "preregistration_sha256": "f" * 64,
            "model_identity": {"converted_model_hash": "g" * 64},
            "dataset_hashes": {"dataset_sha256": "h" * 64},
        },
        "execution_environment": {
            "python_version": "3.11",
            "numpy_version": "1.26",
            "torch_version": "2.0",
            "cuda_available": True,
            "gpu_name": "test-gpu",
        },
        "profile_archive": {},
    }


# ---------------------------------------------------------------------------
# Static, synthetic, neutral
# ---------------------------------------------------------------------------

def test_static_preflight_passes_without_model_or_formal_data():
    artifact = r.run_static_preflight(publish=False)
    assert artifact["status"] == "PASS"
    assert artifact["no_formal_result"] is True
    assert artifact["no_authorization"] is True
    assert artifact["no_authorization_consumption"] is True


def test_synthetic_preflight_exercises_integrated_graph():
    artifact = r.run_synthetic_preflight(publish=False)
    assert artifact["status"] == "PASS"
    assert artifact["reference_optimized_ci_equivalent"] is True
    assert artifact["formal_data_accessed"] is False
    assert artifact["scientific_result_created"] is False


def test_neutral_preflight_is_justified_without_rerunning_model():
    artifact = r.run_neutral_model_preflight(publish=False)
    assert artifact["status"] == "NOT_REQUIRED_WITH_JUSTIFICATION"
    assert artifact["real_panel_accessed"] is False


# ---------------------------------------------------------------------------
# Authorization fail-closed and single-use semantics
# ---------------------------------------------------------------------------

def test_formal_run_rejects_missing_authorization(monkeypatch):
    monkeypatch.setattr(r, "verify_exp027_authorities", lambda root: {})
    monkeypatch.setattr(r, "verify_no_result_collision", lambda root: None)
    monkeypatch.setattr(r, "_authorization_path_for", lambda root, auth_file: None)
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_RUN_REQUIRES_AUTHORIZATION"):
        r.run_formal_run(r.ROOT)


@pytest.mark.parametrize(
    "mutator,message",
    [
        (lambda a: a.update({"experiment": "EXP-026"}), "EXPERIMENT"),
        (lambda a: a.update({"purpose": "RESCUE_RUN"}), "PURPOSE"),
        (lambda a: a.update({"single_use": False}), "NOT_SINGLE_USE"),
        (lambda a: a.update({"authorized_execution_count": 2}), "EXECUTION_COUNT"),
        (lambda a: a.update({"formal_mode": "--engineering-qualification"}), "MODE"),
        (lambda a: a["execution_binding"].update({"repository_commit": "0" * 40}), "BINDING"),
        (lambda a: a["execution_binding"].update({"runner_sha256": "0" * 64}), "BINDING"),
        (lambda a: a["execution_binding"].update({"frozen_design_sha256": "0" * 64}), "BINDING"),
        (lambda a: a["execution_binding"].update({"preregistration_sha256": "0" * 64}), "BINDING"),
        (lambda a: a["execution_binding"]["model_identity"].update({"converted_model_hash": "0" * 64}), "BINDING"),
        (lambda a: a["execution_binding"]["dataset_hashes"].update({"dataset_sha256": "0" * 64}), "BINDING"),
    ],
)
def test_authorization_rejects_malformed_or_mismatched_binding(tmp_path, mutator, message):
    payload = _valid_auth_payload()
    mutator(payload)
    path = _write_auth(tmp_path, payload)
    with pytest.raises(r.Exp027ProtocolIntegrityError, match=message):
        r.validate_exp027_authorization(r.ROOT, path)


def test_authorization_consumption_is_atomic_and_single_use(tmp_path):
    payload = _valid_auth_payload()
    path = _write_auth(tmp_path, payload)
    authorization, authorization_sha = r.validate_exp027_authorization(r.ROOT, path)
    consumption_dir = tmp_path / "consumption"
    record, record_sha = r.consume_exp027_authorization(
        r.ROOT,
        authorization,
        authorization_sha,
        consumption_dir=consumption_dir,
    )
    assert record_sha
    assert (consumption_dir / f"{payload['authorization_id']}.json").exists()
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_AUTHORIZATION_ALREADY_CONSUMED"):
        r.consume_exp027_authorization(
            r.ROOT,
            authorization,
            authorization_sha,
            consumption_dir=consumption_dir,
        )


def test_crash_after_consumption_does_not_reach_scientific_extraction(tmp_path, monkeypatch, capsys):
    payload = _valid_auth_payload()
    path = _write_auth(tmp_path, payload)
    authorization, authorization_sha = r.validate_exp027_authorization(r.ROOT, path)
    consumption_dir = tmp_path / "consumption"
    r.consume_exp027_authorization(
        r.ROOT,
        authorization,
        authorization_sha,
        consumption_dir=consumption_dir,
    )

    monkeypatch.setattr(r, "verify_exp027_authorities", lambda root: {})
    monkeypatch.setattr(r, "verify_no_result_collision", lambda root: None)
    monkeypatch.setattr(r, "_authorization_path_for", lambda root, auth_file: path)
    monkeypatch.setattr(r, "validate_exp027_authorization", lambda root, auth_path: (authorization, authorization_sha))
    monkeypatch.setattr(r, "consume_exp027_authorization", lambda *args, **kwargs: (_ for _ in ()).throw(r.Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_ALREADY_CONSUMED")))
    monkeypatch.setattr(r, "load_exp027_observations", lambda root: pytest.fail("scientific extraction must not run"))

    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_AUTHORIZATION_ALREADY_CONSUMED"):
        r.run_formal_run(r.ROOT, authorization_file=str(path))


# ---------------------------------------------------------------------------
# Progress and CLI contract
# ---------------------------------------------------------------------------

def test_formal_progress_is_outcome_blind_and_stage_level(tmp_path, monkeypatch, capsys):
    payload = _valid_auth_payload()
    auth_path = tmp_path / "auth.json"
    auth_path.write_text(json.dumps(payload), encoding="utf-8")
    authorization = payload
    authorization_sha = "a" * 64

    fake_consumption = {
        "authorization_id": payload["authorization_id"],
        "run_attempt_id": "attempt-1",
        "consumed_at_utc": "2026-08-22T00:00:00+00:00",
    }

    monkeypatch.setattr(r, "verify_exp027_authorities", lambda root: {})
    monkeypatch.setattr(r, "verify_no_result_collision", lambda root: None)
    monkeypatch.setattr(r, "_authorization_path_for", lambda root, auth_file: auth_path)
    monkeypatch.setattr(r, "validate_exp027_authorization", lambda root, auth_path: (authorization, authorization_sha))
    monkeypatch.setattr(r, "consume_exp027_authorization", lambda *args, **kwargs: (fake_consumption, "b" * 64))
    monkeypatch.setattr(r, "load_exp027_observations", lambda root: [])
    monkeypatch.setattr(r, "execute_exp027_scientific_executor", lambda **kwargs: {"payload": {}, "profile": {}, "result_sha256": "c" * 64, "route": "THIRD_REGISTERED_PROFILE"})

    r.run_formal_run(r.ROOT, authorization_file=str(auth_path), progress_state_path=tmp_path / "progress.json")
    out = capsys.readouterr().out.lower()
    assert out.count("stage=") == 5
    for term in ("rho", "sdi", "low_d", "low-d", "ci", "support", "route", "condition", "profile"):
        assert term not in out

    state = json.loads((tmp_path / "progress.json").read_text(encoding="utf-8"))
    assert set(state).issubset(progress.ALLOWED_STATE_KEYS)


def test_cli_has_no_scientific_override_surfaces():
    parser = r.build_parser()
    allowed_destinations = {
        "help",
        "static_preflight",
        "synthetic_preflight",
        "neutral_model_preflight",
        "formal_run",
        "repo_root",
        "authorization_file",
    }
    assert {action.dest for action in parser._actions} == allowed_destinations

    source = _read_source(RUNNER_PATH)
    for line in source.splitlines():
        if "os.environ" in line:
            assert "HF_HUB_OFFLINE" in line or "TRANSFORMERS_OFFLINE" in line


# ---------------------------------------------------------------------------
# Frozen carrier, class mapping, routing, LOW-D firewall
# ---------------------------------------------------------------------------

def test_block15_final_norm_trap_is_preserved():
    config = _frozen_config()
    carrier = config["carrier_semantics"]
    assert carrier["block_15_hook_output"] == "post_decoder_block_residual_before_model_final_RMSNorm"
    assert carrier["forbidden_carrier"] == "outputs.hidden_states[-1]"

    source = _read_source(RUNNER_PATH)
    assert "outputs.hidden_states[-1]" not in source
    assert "register_forward_hook" in source


def test_class_mapping_and_profile_routing_are_frozen():
    assert ref.CLASS_ORDER == ("logic", "causality", "analogy", "definition")
    qwen = _profile("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED")
    route, status = result_validator.route_from_profile(qwen, technical_valid=True, measurement_valid=True)
    assert route == "EXP026_PROFILE_MATCH_QWEN"
    assert status == "VALID_REGISTERED_RESULT"

    invalid_route, invalid_status = result_validator.route_from_profile(qwen, technical_valid=False, measurement_valid=True)
    assert invalid_route == "NOT_ASSIGNED"
    assert invalid_status == "UNOBSERVED_OR_INVALID"


def test_integrated_runner_uses_frozen_exp026_computation():
    source = _read_source(RUNNER_PATH)
    assert "compute_matrix_profile" in source
    assert "optimized_matrix_bootstrap" in source
    assert "ref.CONDITION_ORDER" in source
    assert "ref._support_classes" in source


def test_no_qwen_or_olmo_rerun_path_exists():
    source = _read_source(RUNNER_PATH)
    assert "Qwen/Qwen3-1.7B" not in source
    assert "OLMo-2-0425-1B-Instruct" not in source
    assert "MODEL_REGISTRY" not in source
    assert "ref.load_runtime(" not in source


# ---------------------------------------------------------------------------
# Publication and result schema
# ---------------------------------------------------------------------------

def test_exclusive_publication_rejects_collision(tmp_path):
    target = tmp_path / "result.json"
    target.write_text("existing", encoding="utf-8")
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="CANONICAL_RESULT_ALREADY_EXISTS"):
        r._atomic_write_json_exclusive(target, {"status": "COMPLETED"})


def test_atomic_write_leaves_no_partial_or_tmp_file(tmp_path):
    target = tmp_path / "result.json"
    payload = {"status": "COMPLETED", "route": "THIRD_REGISTERED_PROFILE"}
    sha = r._atomic_write_json(target, payload)
    assert sha
    assert json.loads(target.read_text(encoding="utf-8")) == payload
    assert list(tmp_path.glob("result.json*")) == [target]


def test_result_schema_accepts_valid_synthetic_payload():
    payload = _minimal_result_payload()
    assert result_validator.validate_result_payload(payload) == []
    assert result_validator.is_valid_result_payload(payload) is True


@pytest.mark.parametrize(
    "mutator,expected",
    [
        (lambda p: p.update({"classification": "WRONG"}), "classification"),
        (lambda p: p.update({"experiment": "EXP-026"}), "experiment"),
        (lambda p: p.update({"created_at_utc": ""}), "created_at_utc"),
        (lambda p: p.update({"technical_validity": False}), "result_status_route_mismatch"),
        (lambda p: p.pop("authorization_identity"), "authorization_identity"),
        (lambda p: p.pop("execution_binding"), "execution_binding"),
        (lambda p: p.pop("execution_environment"), "execution_environment_python_version"),
        (lambda p: p.update({"raw_hidden_tensors": []}), "raw_hidden_tensors_forbidden"),
    ],
)
def test_result_schema_fails_closed_on_mutation(mutator, expected):
    payload = _minimal_result_payload()
    mutator(payload)
    errors = result_validator.validate_result_payload(payload)
    assert expected in errors


# ---------------------------------------------------------------------------
# Failure injection: no canonical result and no automatic retry
# ---------------------------------------------------------------------------

def test_result_validation_failure_does_not_publish(tmp_path, monkeypatch):
    payload = _minimal_result_payload()
    payload["route"] = "NOT_ASSIGNED"
    result_path = tmp_path / "exp027_results.json"

    monkeypatch.setattr(r, "compute_exp027_profile", lambda *args, **kwargs: {"source_qualification": {"source_coverage_evaluable": True}, "support": {}})
    monkeypatch.setattr(r, "verify_exp027_authorities", lambda root: {})
    monkeypatch.setattr(r, "build_exp027_result_payload", lambda **kwargs: payload)

    with pytest.raises(r.Exp027ProtocolIntegrityError, match="RESULT_SCHEMA_INVALID"):
        r.execute_exp027_scientific_executor(
            root=r.ROOT,
            observations=[],
            result_path=result_path,
            authorization_identity={},
            bootstrap_replicates=1,
        )
    assert not result_path.exists()


def test_publication_failure_does_not_leave_canonical_result(tmp_path, monkeypatch):
    payload = _minimal_result_payload()
    result_path = tmp_path / "exp027_results.json"

    monkeypatch.setattr(r, "compute_exp027_profile", lambda *args, **kwargs: {"source_qualification": {"source_coverage_evaluable": True}, "support": {}})
    monkeypatch.setattr(r, "verify_exp027_authorities", lambda root: {})
    monkeypatch.setattr(r, "build_exp027_result_payload", lambda **kwargs: payload)
    monkeypatch.setattr(result_validator, "validate_result_payload", lambda payload: [])

    def fail_publication(path, value):
        raise r.Exp027ProtocolIntegrityError("PUBLICATION_FAILURE_INJECTED")

    monkeypatch.setattr(r, "_atomic_write_json_exclusive", fail_publication)

    with pytest.raises(r.Exp027ProtocolIntegrityError, match="PUBLICATION_FAILURE_INJECTED"):
        r.execute_exp027_scientific_executor(
            root=r.ROOT,
            observations=[],
            result_path=result_path,
            authorization_identity={},
            bootstrap_replicates=1,
        )
    assert not result_path.exists()


def test_runner_has_no_automatic_retry_loop():
    source = _read_source(RUNNER_PATH)
    for forbidden in ("while True", "for attempt in range", "watchdog", "restart", "retry"):
        assert forbidden not in source


# ---------------------------------------------------------------------------
# Lifecycle state-machine repair regression tests
# ---------------------------------------------------------------------------

def test_lifecycle_state_classification(tmp_path):
    auth = tmp_path / "auth.json"
    consumption = tmp_path / "consumption"
    result = tmp_path / "result.json"

    assert r.classify_exp027_lifecycle(None, consumption, result) == "S0_PRISTINE_UNAUTHORIZED"

    auth.write_text("{}", encoding="utf-8")
    assert r.classify_exp027_lifecycle(auth, consumption, result) == "S1_AUTHORIZED_UNUSED"

    consumption.mkdir()
    (consumption / "102d-test-auth.json").write_text("{}", encoding="utf-8")
    assert r.classify_exp027_lifecycle(auth, consumption, result) == "S2_CONSUMED_IN_PROGRESS"

    result.write_text("{}", encoding="utf-8")
    assert r.classify_exp027_lifecycle(auth, consumption, result) == "S3_PUBLISHED"

    auth.unlink()
    assert r.classify_exp027_lifecycle(None, consumption, result) == "SX_INVALID_STATE"


def test_lifecycle_validator_accepts_s1_and_rejects_consumed_states():
    assert r.validate_formal_lifecycle("S1_AUTHORIZED_UNUSED") == "S1_AUTHORIZED_UNUSED"
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_AUTHORIZATION_ALREADY_CONSUMED"):
        r.validate_formal_lifecycle("S2_CONSUMED_IN_PROGRESS")

    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_RUN_REQUIRES_AUTHORIZATION"):
        r.validate_formal_lifecycle("S0_PRISTINE_UNAUTHORIZED")
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="CANONICAL_RESULT_ALREADY_EXISTS"):
        r.validate_formal_lifecycle("S3_PUBLISHED")
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_LIFECYCLE_INVALID_STATE"):
        r.validate_formal_lifecycle("SX_INVALID_STATE")


def test_s1_authorized_state_does_not_invalidate_immutable_authorities(tmp_path):
    auth = tmp_path / "auth.json"
    auth.write_text("{}", encoding="utf-8")
    consumption = tmp_path / "consumption"
    result = tmp_path / "result.json"

    assert r.classify_exp027_lifecycle(auth, consumption, result) == "S1_AUTHORIZED_UNUSED"
    # The immutable authority binding must remain available after an authorization exists.
    binding = r.verify_exp027_authorities(r.ROOT)
    assert binding["runner_sha256"] == r.sha256_file(r.RUNNER_PATH if hasattr(r, "RUNNER_PATH") else Path(__file__).parents[1] / "experiments" / "exp027" / "run_exp027.py")


def test_s2_consumed_state_keeps_authorities_and_rejects_second_launch(tmp_path):
    payload = _valid_auth_payload()
    auth_path = _write_auth(tmp_path, payload)
    authorization, authorization_sha = r.validate_exp027_authorization(r.ROOT, auth_path)

    consumption = tmp_path / "consumption"
    consumption.mkdir()
    (consumption / f"{payload['authorization_id']}.json").write_text("{}", encoding="utf-8")
    result = tmp_path / "result.json"

    assert r.classify_exp027_lifecycle(auth_path, consumption, result) == "S2_CONSUMED_IN_PROGRESS"
    assert r.verify_exp027_authorities(r.ROOT)

    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_AUTHORIZATION_ALREADY_CONSUMED"):
        r.consume_exp027_authorization(
            r.ROOT,
            authorization,
            authorization_sha,
            consumption_dir=consumption,
        )


def test_s3_published_collision_is_rejected_before_inference(tmp_path, monkeypatch):
    auth = tmp_path / "auth.json"
    auth.write_text("{}", encoding="utf-8")
    consumption = tmp_path / "consumption"
    consumption.mkdir()
    (consumption / "one.json").write_text("{}", encoding="utf-8")
    result = tmp_path / "result.json"
    result.write_text("{}", encoding="utf-8")

    assert r.classify_exp027_lifecycle(auth, consumption, result) == "S3_PUBLISHED"
    with pytest.raises(r.Exp027ProtocolIntegrityError, match="CANONICAL_RESULT_ALREADY_EXISTS"):
        r.validate_formal_lifecycle("S3_PUBLISHED")


def test_invalid_lifecycle_fails_closed(tmp_path):
    auth = tmp_path / "auth.json"
    consumption = tmp_path / "consumption"
    result = tmp_path / "result.json"

    # consumption without authorization
    consumption.mkdir()
    (consumption / "orphan.json").write_text("{}", encoding="utf-8")
    assert r.classify_exp027_lifecycle(None, consumption, result) == "SX_INVALID_STATE"

    # multiple consumption records
    auth.write_text("{}", encoding="utf-8")
    (consumption / "second.json").write_text("{}", encoding="utf-8")
    assert r.classify_exp027_lifecycle(auth, consumption, result) == "SX_INVALID_STATE"

    # canonical result without valid lifecycle provenance
    auth.unlink()
    result.write_text("{}", encoding="utf-8")
    assert r.classify_exp027_lifecycle(None, consumption, result) == "SX_INVALID_STATE"

    with pytest.raises(r.Exp027ProtocolIntegrityError, match="FORMAL_LIFECYCLE_INVALID_STATE"):
        r.validate_formal_lifecycle("SX_INVALID_STATE")
