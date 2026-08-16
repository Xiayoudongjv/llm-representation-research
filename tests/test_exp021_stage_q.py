"""Synthetic tests for the EXP-021 Stage-Q infrastructure only."""

from __future__ import annotations

import json
import ast
import contextlib
import copy
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from experiments.exp021 import run_exp021_stage_q as stage_q


class FakeView:
    def __init__(self, parent: "FakeTensor", item):
        self.parent = parent
        self.item = item

    @property
    def data(self):
        return self.parent.data[self.item]

    def __iadd__(self, other):
        self.parent.data[self.item] += other.data if isinstance(other, FakeTensor) else other
        return self


class FakeTensor:
    def __init__(self, data, dtype=None, device="cpu"):
        self.data = np.asarray(data, dtype=dtype)
        self.device = device

    @property
    def dtype(self):
        return self.data.dtype

    @property
    def shape(self):
        return self.data.shape

    def clone(self):
        return FakeTensor(self.data.copy(), device=self.device)

    def to(self, *, device, dtype):
        return FakeTensor(self.data.astype(dtype), dtype=dtype, device=device)

    def __getitem__(self, item):
        return FakeView(self, item)

    def __setitem__(self, item, value):
        self.data[item] = value.data if isinstance(value, (FakeTensor, FakeView)) else value

    def __mul__(self, value):
        return FakeTensor(self.data * value, device=self.device)

    def __rmul__(self, value):
        return self.__mul__(value)


def fake_equal(left, right):
    left_data = left.data if isinstance(left, (FakeTensor, FakeView)) else left
    right_data = right.data if isinstance(right, (FakeTensor, FakeView)) else right
    return np.array_equal(left_data, right_data)


def neutral_authorization(tmp_path: Path, **overrides):
    authorization = {
        "schema_version": stage_q.SCHEMA_VERSION,
        "experiment": "EXP-021",
        "scope": stage_q.NEUTRAL_SCOPE,
        "authorization_id": "AUTH-NEUTRAL-001",
        "issued_at": "2026-08-15T00:00:00+00:00",
        "expires_at": "2099-08-15T00:00:00+00:00",
        "runner_commit": stage_q.AUTHORITY_ARCHIVE_COMMIT,
        "runner_sha256": "a" * 64,
        "implementation_hashes": {"runner": "a" * 64, "validator": "b" * 64},
        "authority_hashes": {"original": "c" * 64, "amendment": "d" * 64, "reconciliation": "e" * 64},
        "model_manifest": {"identity": "manifest-sha"},
        "environment_binding": {
            "device": "cuda:0", "dtype": "float16", "local_files_only": True,
            "model_eval_mode": True, "gradients_enabled": False, "use_cache": False,
        },
        "allowed_output_path": str(tmp_path / "engineering" / "neutral.json"),
        "maximum_launch_count": 1,
        "fit_access_permitted": False,
        "eval_access_permitted": False,
        "scientific_result_permitted": False,
        "automatic_retry_permitted": False,
    }
    authorization.update(overrides)
    return authorization


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _lifecycle_write(tmp_path: Path, relative: str, value=None):
    path = tmp_path / "experiments" / "exp021" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({} if value is None else value), encoding="utf-8")
    return path


def _write_active_neutral_auth(tmp_path: Path, authorization_id: str = "AUTH-B", **overrides):
    """Write a complete neutral authorization at the canonical active path."""
    auth = neutral_authorization(tmp_path, authorization_id=authorization_id, **overrides)
    auth_path = tmp_path / "experiments" / "exp021" / "authorization" / "neutral.json"
    write_json(auth_path, auth)
    return auth_path, auth, stage_q.sha256_file(auth_path)


def _create_completed_historical_disposition(tmp_path: Path, authorization_id: str = "AUTH-A"):
    """Dispose one synthetic authorization and return its identity and hash."""
    auth_path, auth, auth_hash = _write_active_neutral_auth(
        tmp_path, authorization_id=authorization_id
    )
    stage_q.disposition_unconsumed_nonexecutable_authorization(
        repo_root=tmp_path,
        authorization_path=auth_path,
        expected_authorization_id=auth["authorization_id"],
        expected_authorization_sha256=auth_hash,
        expected_scope=stage_q.NEUTRAL_SCOPE,
        explicit_disposition_authorized=True,
        non_executable_reason="test identity-aware lifecycle",
    )
    return auth, auth_hash


def _valid_checkpoint_mapping():
    return {
        "num_transformer_blocks": 28,
        "tuple_semantics": stage_q.TUPLE_SEMANTICS_FROZEN_TEXT,
        "intervention": {"block_index": 16, "hidden_state_index": 17, "beta": 0.75},
        "normalized_0.625": {"block_index": 17, "hidden_state_index": 18},
        "normalized_0.75": {"block_index": 20, "hidden_state_index": 21},
        "normalized_0.875": {"block_index": 24, "hidden_state_index": 25},
        "final_block_pre_final_rmsnorm": {
            "block_index": 27,
            "hidden_state_index": None,
            "access": "hooked_block_27_output",
            "role": "PRIMARY_FINAL_CHECKPOINT",
        },
        "final_normalized_hidden_state": {
            "block_index": 27,
            "hidden_state_index": 28,
            "role": "DESCRIPTIVE_ONLY",
        },
    }


def synthetic_authority():
    """Return a synthetic authority shape sufficient for the production entries."""
    return {
        "checkpoint_mapping": {},
        "primary_model_identity": {
            "model_id": "Qwen/Qwen3-1.7B",
            "architecture": "Qwen3ForCausalLM",
            "model_type": "qwen3",
            "canonical_snapshot_path": "synthetic-snapshot",
            "resolved_snapshot_path": "synthetic-snapshot",
            "file_manifest": [{"file": "config.json", "bytes": 1, "sha256": "a" * 64}],
        },
    }


def synthetic_binding(authority):
    """Return a deterministic binding matching the synthetic authority."""
    return {
        "runner_commit": stage_q.AUTHORITY_ARCHIVE_COMMIT,
        "runner_sha256": "a" * 64,
        "implementation_hashes": {"runner": "a" * 64, "validator": "b" * 64},
        "authority_hashes": {
            "original": "c" * 64,
            "amendment": "d" * 64,
            "reconciliation": "e" * 64,
        },
        "model_manifest": stage_q.model_manifest_binding(
            authority["primary_model_identity"]
        ),
        "environment_binding": stage_q.required_environment_binding(),
        "runtime_identity": synthetic_runtime_identity(),
    }


def synthetic_runtime_identity(**overrides):
    """Return the independently sourced dynamic runtime identity for synthetic tests."""
    identity = {
        "python": "3.12.0",
        "torch": "2.7.0",
        "transformers": "4.50.0",
        "cuda_runtime": "12.4",
        "nvidia_driver": "570.00",
        "gpu": "NVIDIA Synthetic GPU",
    }
    identity.update(overrides)
    return identity


def synthetic_runtime_environment(**overrides):
    """Return the complete runtime identity used by both production entries."""
    environment = {
        **synthetic_runtime_identity(),
        "dtype": "float16",
        "device": "cuda:0",
        "local_files_only": True,
        "model_eval_mode": True,
        "gradients_enabled": False,
        "use_cache": False,
    }
    environment.update(overrides)
    return environment


def valid_neutral_result(authority, binding, **overrides):
    """Return a complete neutral result that satisfies the real validator."""
    diagnostic_values, diagnostic_sha = stage_q.deterministic_diagnostic_vector(2048)
    assert len(diagnostic_values) == 2048
    result = {
        "schema_version": stage_q.SCHEMA_VERSION,
        "experiment": stage_q.EXPERIMENT,
        "result_classification": "ENGINEERING_NEUTRAL_HOOK_QUALIFICATION_ONLY",
        "attempt_id": "ATTEMPT-NEUTRAL-001",
        "authorization_id": "AUTH-NEUTRAL-001",
        "authorization_hash": "f" * 64,
        "runner_commit": binding["runner_commit"],
        "runner_sha256": binding["runner_sha256"],
        "implementation_hashes": binding["implementation_hashes"],
        "authority_hashes": binding["authority_hashes"],
        "model_manifest": stage_q.model_manifest_binding(
            authority["primary_model_identity"]
        ),
        "canonical_snapshot_path": authority["primary_model_identity"]["canonical_snapshot_path"],
        "resolved_snapshot_path": authority["primary_model_identity"]["resolved_snapshot_path"],
        "execution_environment": synthetic_runtime_environment(),
        "hook_block": stage_q.INTERVENTION_BLOCK,
        "token_rule": "last valid token of one unpadded sequence",
        "beta": stage_q.BETA,
        "diagnostic_vector": {
            "algorithm": "alternating_plus_minus_one",
            "length": 2048,
            "sha256": diagnostic_sha,
        },
        "neutral_input_identity": {"sha256": stage_q._neutral_input_identity()},
        "cache_semantics": {"use_cache": False, "shared_kv_cache": False},
        "checks": {
            "inactive_hook_exact": True,
            "active_hook_exact": True,
            "inactive_invocations": True,
            "active_invocations": True,
            "selected_last_valid_token": True,
            "use_cache_false": True,
            "gradients_disabled": True,
        },
        "started_at": "2026-08-15T00:00:00+00:00",
        "finished_at": "2026-08-15T00:00:01+00:00",
        "fit_eval_accessed": False,
        "scientific_result_created": False,
        "overall_pass": True,
    }
    result.update(overrides)
    return result


def _fake_torch_module():
    return types.SimpleNamespace(
        float32="float32",
        tensor=lambda data, dtype=None, device=None: data,
        equal=lambda left, right: True,
        no_grad=contextlib.nullcontext,
    )


def _patch_common_entry_boundary(monkeypatch, authority, binding, events):
    monkeypatch.setitem(sys.modules, "torch", _fake_torch_module())

    def fake_confined(path, root, allow_missing=False):
        path = Path(path)
        return path if path.is_absolute() else Path(root) / path

    monkeypatch.setattr(stage_q, "confined_path", fake_confined)

    def fake_validate_authority_files(*args, **kwargs):
        events.append("validate_authority_files")
        return authority

    monkeypatch.setattr(stage_q, "validate_authority_files", fake_validate_authority_files)
    monkeypatch.setattr(stage_q, "validate_mode_lifecycle", lambda *args, **kwargs: {})
    monkeypatch.setattr(stage_q, "validate_checkpoint_mapping", lambda *args, **kwargs: None)

    def fake_build_static_execution_binding(*args, **kwargs):
        events.append("build_static_execution_binding")
        return binding

    monkeypatch.setattr(stage_q, "build_static_execution_binding", fake_build_static_execution_binding)


def _patch_lifecycle_common_entry_boundary(monkeypatch, authority, binding, events):
    """Patch common production-entry dependencies but keep lifecycle validation live."""
    monkeypatch.setitem(sys.modules, "torch", _fake_torch_module())

    def fake_confined(path, root, allow_missing=False):
        path = Path(path)
        return path if path.is_absolute() else Path(root) / path

    monkeypatch.setattr(stage_q, "confined_path", fake_confined)

    def fake_validate_authority_files(*args, **kwargs):
        events.append("validate_authority_files")
        return authority

    monkeypatch.setattr(stage_q, "validate_authority_files", fake_validate_authority_files)
    monkeypatch.setattr(stage_q, "validate_checkpoint_mapping", lambda *args, **kwargs: None)

    def fake_build_static_execution_binding(*args, **kwargs):
        events.append("build_static_execution_binding")
        return binding

    monkeypatch.setattr(stage_q, "build_static_execution_binding", fake_build_static_execution_binding)


def _install_neutral_entry_harness(
    monkeypatch,
    authority,
    binding,
    *,
    environment=None,
    validate_override=None,
):
    """Patch all model/data/runtime dependencies around the real neutral entry."""
    events = []
    forward_calls = []
    states = {
        "reference": {},
        "inactive": {},
        "active_pre": {},
        "active_post": {},
    }
    published = {}
    environment = synthetic_runtime_environment() if environment is None else environment

    _patch_common_entry_boundary(monkeypatch, authority, binding, events)

    def fake_consume_authorization(*args, **kwargs):
        events.append("consume_authorization")
        return (
            {"authorization_id": "AUTH-NEUTRAL-001"},
            {
                "attempt_id": "ATTEMPT-NEUTRAL-001",
                "authorization_hash": "f" * 64,
            },
        )

    monkeypatch.setattr(stage_q, "consume_authorization", fake_consume_authorization)

    def fake_validate_model_manifest(*args, **kwargs):
        events.append("validate_model_manifest")

    monkeypatch.setattr(stage_q, "validate_model_manifest", fake_validate_model_manifest)

    def fake_load_model_and_tokenizer(*args, **kwargs):
        events.append("_load_model_and_tokenizer")
        return object(), object()

    monkeypatch.setattr(stage_q, "_load_model_and_tokenizer", fake_load_model_and_tokenizer)

    def fake_forward_with_capture(model, tokenizer, hooks, torch_arg):
        events.append("_forward_with_capture")
        forward_calls.append(hooks)
        for hook in hooks:
            if callable(hook):
                hook(None, None, object())
        selected = 7
        return object(), {"selected_token_index": selected}, selected

    monkeypatch.setattr(stage_q, "_forward_with_capture", fake_forward_with_capture)

    def fake_capture_output_hook(state):
        events.append("capture_output_hook")

        def hook(*args, **kwargs):
            state["invocations"] = 1
            state["value"] = object()

        return hook

    monkeypatch.setattr(stage_q, "capture_output_hook", fake_capture_output_hook)

    def fake_production_hook_factory(delta, beta, selected, *, active):
        events.append("production_hook_factory")
        return (lambda *args, **kwargs: None, {"invocations": 1})

    monkeypatch.setattr(stage_q, "production_hook_factory", fake_production_hook_factory)

    def fake_construct_expected_hook_output(*args, **kwargs):
        events.append("construct_expected_hook_output")
        return object()

    monkeypatch.setattr(stage_q, "construct_expected_hook_output", fake_construct_expected_hook_output)

    def fake_validate_active_hook_output(*args, **kwargs):
        events.append("validate_active_hook_output")

    monkeypatch.setattr(stage_q, "validate_active_hook_output", fake_validate_active_hook_output)

    monkeypatch.setattr(
        stage_q,
        "_runtime_environment",
        lambda torch_arg, model: dict(environment),
    )

    real_validate = stage_q.validate_neutral_result if validate_override is None else validate_override

    def validating_spy(result, authority_arg, binding_arg):
        events.append("validate_neutral_result")
        return real_validate(result, authority_arg, binding_arg)

    monkeypatch.setattr(stage_q, "validate_neutral_result", validating_spy)

    def publish_spy(output_path, result, root):
        events.append("atomic_publish_json")
        assert "validate_neutral_result" in events
        published["result"] = result

    monkeypatch.setattr(stage_q, "atomic_publish_json", publish_spy)
    return events, states, published


def _install_stage_q_entry_harness(monkeypatch, authority, binding, neutral_result):
    """Patch all model/data/runtime dependencies around the real Stage-Q entry."""
    events = []
    published = {}

    _patch_common_entry_boundary(monkeypatch, authority, binding, events)

    def fake_read_json_no_duplicates(path):
        events.append("read_json_no_duplicates")
        return copy.deepcopy(neutral_result)

    monkeypatch.setattr(stage_q, "read_json_no_duplicates", fake_read_json_no_duplicates)

    real_validate = stage_q.validate_neutral_result

    def validating_spy(result, authority_arg, binding_arg):
        events.append("validate_neutral_result")
        return real_validate(result, authority_arg, binding_arg)

    monkeypatch.setattr(stage_q, "validate_neutral_result", validating_spy)

    def fake_consume_authorization(*args, **kwargs):
        events.append("consume_authorization")
        return (
            {"authorization_id": "AUTH-STAGE-Q-001"},
            {
                "attempt_id": "ATTEMPT-STAGE-Q-001",
                "authorization_hash": "f" * 64,
            },
        )

    monkeypatch.setattr(stage_q, "consume_authorization", fake_consume_authorization)

    def fake_validate_model_manifest(*args, **kwargs):
        events.append("validate_model_manifest")

    monkeypatch.setattr(stage_q, "validate_model_manifest", fake_validate_model_manifest)

    def fake_load_model_and_tokenizer(*args, **kwargs):
        events.append("_load_model_and_tokenizer")
        return object(), object()

    monkeypatch.setattr(stage_q, "_load_model_and_tokenizer", fake_load_model_and_tokenizer)

    def fake_load_frozen_split_config(root):
        events.append("_load_frozen_split_config")
        return {"dataset": {"splits": [{"id": "split_a"}, {"id": "split_b"}]}}

    monkeypatch.setattr(stage_q, "_load_frozen_split_config", fake_load_frozen_split_config)

    def fake_load_fit_source_records(root, split_id):
        events.append("load_fit_source_records")
        return [{"item_id": f"{split_id}-F-{index}", "task_class": stage_q.CLASS_ORDER[index % 4]} for index in range(12)]

    monkeypatch.setattr(stage_q, "load_fit_source_records", fake_load_fit_source_records)

    def fake_extract_fit_representations(model, tokenizer, records, torch_arg):
        events.append("extract_fit_representations")
        return {"intervention": np.zeros((12, 4))}

    monkeypatch.setattr(stage_q, "extract_fit_representations", fake_extract_fit_representations)

    def fake_leave_one_out_fixed_probe(representations, labels):
        events.append("leave_one_out_fixed_probe")
        return []

    monkeypatch.setattr(stage_q, "leave_one_out_fixed_probe", fake_leave_one_out_fixed_probe)

    def fake_summarize_checkpoint(rows, checkpoint, split_id):
        events.append("summarize_checkpoint")
        return {
            "split_id": split_id,
            "checkpoint": checkpoint,
            "n": 12,
            "correct": 7,
            "pass": True,
        }

    monkeypatch.setattr(stage_q, "summarize_checkpoint", fake_summarize_checkpoint)

    def fake_stage_q_global_gate(rows, splits, checkpoints):
        events.append("stage_q_global_gate")
        return True

    monkeypatch.setattr(stage_q, "stage_q_global_gate", fake_stage_q_global_gate)
    monkeypatch.setattr(
        stage_q,
        "_runtime_environment",
        lambda torch_arg, model: synthetic_runtime_environment(),
    )

    def fake_validate_stage_q_result(result):
        events.append("validate_stage_q_result")

    monkeypatch.setattr(stage_q, "validate_stage_q_result", fake_validate_stage_q_result)

    def publish_spy(output_path, result, root):
        events.append("atomic_publish_json")
        assert "validate_stage_q_result" in events
        published["result"] = result

    monkeypatch.setattr(stage_q, "atomic_publish_json", publish_spy)
    return events, published


def test_runner_import_has_no_runtime_imports_or_io(tmp_path):
    script = (
        "import sys; import experiments.exp021.run_exp021_stage_q; "
        "print(any(x in sys.modules for x in ('torch','transformers','accelerate','datasets','safetensors')))"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "False"
    assert not list(tmp_path.iterdir())


def test_cli_requires_exactly_one_mode():
    with pytest.raises(SystemExit):
        stage_q.build_parser().parse_args([])
    with pytest.raises(SystemExit):
        stage_q.build_parser().parse_args(["--stage-q", "--static-preflight"])
    args = stage_q.build_parser().parse_args(["--static-preflight"])
    assert args.static_preflight is True


def test_closed_schema_rejects_missing_and_unknown_keys():
    with pytest.raises(stage_q.ProtocolError):
        stage_q.require_exact_keys({"a": 1}, {"a", "b"}, "synthetic")
    with pytest.raises(stage_q.ProtocolError):
        stage_q.require_exact_keys({"a": 1, "b": 2, "c": 3}, {"a", "b"}, "synthetic")


def test_strict_scalar_validation():
    assert stage_q.require_bool(False, "flag") is False
    with pytest.raises(stage_q.ProtocolError):
        stage_q.require_bool(0, "flag")
    with pytest.raises(stage_q.ProtocolError):
        stage_q.require_finite_number(float("inf"), "number")


def test_authorization_consumption_is_single_use(tmp_path):
    auth_path = tmp_path / "authorization.json"
    consumption_path = tmp_path / "consumed.json"
    write_json(auth_path, neutral_authorization(tmp_path))
    _, consumed = stage_q.consume_authorization(auth_path, consumption_path, tmp_path, stage_q.NEUTRAL_SCOPE)
    assert consumed["state"] == "consumed"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(auth_path, consumption_path, tmp_path, stage_q.NEUTRAL_SCOPE)


def test_authorization_rejects_wrong_scope_and_retry_flags(tmp_path):
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, neutral_authorization(tmp_path, scope="wrong"))
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(auth_path, tmp_path / "consumed.json", tmp_path, stage_q.NEUTRAL_SCOPE)


@pytest.mark.parametrize(
    "override",
    [
        {"expires_at": "2020-01-01T00:00:00+00:00"},
        {"expires_at": "not-a-timestamp"},
        {"maximum_launch_count": True},
    ],
)
def test_authorization_rejects_expiry_and_strict_timestamp_failures(tmp_path, override):
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, neutral_authorization(tmp_path, **override))
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(auth_path, tmp_path / "consumed.json", tmp_path, stage_q.NEUTRAL_SCOPE)
    assert not (tmp_path / "consumed.json").exists()


def test_authorization_rejects_live_identity_mismatch_before_consumption(tmp_path):
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, neutral_authorization(tmp_path))
    expected = {
        "runner_commit": stage_q.AUTHORITY_ARCHIVE_COMMIT,
        "runner_sha256": "b" * 64,
        "implementation_hashes": {"runner": "a" * 64, "validator": "b" * 64},
        "authority_hashes": {"original": "c" * 64, "amendment": "d" * 64, "reconciliation": "e" * 64},
        "model_manifest": {"identity": "manifest-sha"},
        "environment_binding": neutral_authorization(tmp_path)["environment_binding"],
    }
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(
            auth_path,
            tmp_path / "consumed.json",
            tmp_path,
            stage_q.NEUTRAL_SCOPE,
            expected_identity=expected,
        )
    assert not (tmp_path / "consumed.json").exists()


@pytest.mark.parametrize("field", ["runner_commit", "runner_sha256", "implementation_hashes", "authority_hashes", "model_manifest", "environment_binding"])
def test_authorization_rejects_each_bound_identity_mismatch(tmp_path, field):
    auth = neutral_authorization(tmp_path)
    expected = dict(auth)
    expected[field] = {"different": "identity"} if isinstance(auth[field], dict) else "different"
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, auth)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(
            auth_path,
            tmp_path / "consumed.json",
            tmp_path,
            stage_q.NEUTRAL_SCOPE,
            expected_identity=expected,
        )
    write_json(auth_path, neutral_authorization(tmp_path, automatic_retry_permitted=True))
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(auth_path, tmp_path / "consumed.json", tmp_path, stage_q.NEUTRAL_SCOPE)


def test_authorization_rejects_output_path_escape(tmp_path):
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, neutral_authorization(tmp_path, allowed_output_path=str(tmp_path.parent / "outside.json")))
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(auth_path, tmp_path / "consumed.json", tmp_path, stage_q.NEUTRAL_SCOPE)


def test_atomic_publication_does_not_overwrite(tmp_path):
    output = tmp_path / "engineering" / "result.json"
    output.parent.mkdir()
    stage_q.atomic_publish_json(output, {"safe": True}, tmp_path)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.atomic_publish_json(output, {"safe": False}, tmp_path)
    assert json.loads(output.read_text(encoding="utf-8"))["safe"] is True


def test_path_confinement_rejects_symlink_escape_when_supported(tmp_path):
    outside = tmp_path.parent / f"outside-{tmp_path.name}"
    outside.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation unavailable")
    with pytest.raises(stage_q.ProtocolError):
        stage_q.confined_path(link / "result.json", tmp_path, allow_missing=True)


def test_neutral_scope_is_not_stage_q_scope():
    assert stage_q.NEUTRAL_SCOPE != stage_q.STAGE_Q_SCOPE
    assert stage_q.STAGE_Q_SCOPE == "EXP021_STAGE_Q_FIT_ONLY_MEASUREMENT_QUALIFICATION"


def test_deterministic_diagnostic_vector_identity():
    first, first_id = stage_q.deterministic_diagnostic_vector(8)
    second, second_id = stage_q.deterministic_diagnostic_vector(8)
    assert first == second == [1.0, -1.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
    assert first_id == second_id
    assert first_id == stage_q.sha256_bytes(json.dumps(first, separators=(",", ":")).encode())
    with pytest.raises(stage_q.ProtocolError):
        stage_q.deterministic_diagnostic_vector(0)
    assert any(value != 0 for value in first)


def test_checkpoint_and_probability_validation_reject_invalid_values():
    mapping = {
        "num_transformer_blocks": 28,
        "tuple_semantics": stage_q.TUPLE_SEMANTICS_FROZEN_TEXT,
        **{
            item["name"]: {
                "block_index": item["block_index"],
                "hidden_state_index": item["hidden_state_index"],
                    "role": (
                        "PRIMARY_FINAL_CHECKPOINT"
                        if item["name"] == "final_block_pre_final_rmsnorm"
                        else "DESCRIPTIVE_ONLY"
                        if item["role"] == "descriptive"
                        else "required"
                    ),
                **({"access": "hooked_block_27_output"} if item["name"] == "final_block_pre_final_rmsnorm" else {}),
            }
            for item in stage_q.CHECKPOINTS
        },
    }
    stage_q.validate_checkpoint_mapping(mapping)
    mapping["intervention"]["block_index"] = 15
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_checkpoint_mapping_accepts_frozen_metadata_shape():
    stage_q.validate_checkpoint_mapping(_valid_checkpoint_mapping())


def test_checkpoint_mapping_rejects_missing_tuple_semantics():
    mapping = _valid_checkpoint_mapping()
    del mapping["tuple_semantics"]
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_checkpoint_mapping_rejects_unknown_metadata_key():
    mapping = _valid_checkpoint_mapping()
    mapping["unknown_metadata"] = "unexpected"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_checkpoint_mapping_rejects_unknown_checkpoint_object():
    mapping = _valid_checkpoint_mapping()
    mapping["unknown_checkpoint"] = {"block_index": 10, "hidden_state_index": 11}
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_checkpoint_mapping_rejects_missing_required_checkpoint():
    mapping = _valid_checkpoint_mapping()
    del mapping["normalized_0.75"]
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_checkpoint_mapping_rejects_wrong_tuple_semantics_type():
    mapping = _valid_checkpoint_mapping()
    mapping["tuple_semantics"] = {"not": "a string"}
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_checkpoint_mapping_rejects_malformed_checkpoint_object():
    mapping = _valid_checkpoint_mapping()
    mapping["final_block_pre_final_rmsnorm"] = {
        "block_index": 27,
        "hidden_state_index": None,
        "access": "wrong_access",
        "role": "PRIMARY_FINAL_CHECKPOINT",
    }
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_checkpoint_mapping(mapping)


def test_descriptive_final_checkpoint_remains_descriptive_only():
    mapping = _valid_checkpoint_mapping()
    stage_q.validate_checkpoint_mapping(mapping)
    assert mapping["final_normalized_hidden_state"]["role"] == "DESCRIPTIVE_ONLY"
    assert "final_normalized_hidden_state" not in stage_q.REQUIRED_GATE_CHECKPOINTS


def test_real_reconciliation_checkpoint_mapping_passes():
    root = Path(__file__).resolve().parents[1]
    authority_path = root / "experiments/exp021/exp021_preregistration_reconciliation.json"
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    stage_q.validate_checkpoint_mapping(authority["checkpoint_mapping"])


def test_lifecycle_static_accepts_active_neutral_authorization(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)
    assert state["active_neutral"] is not None


def test_lifecycle_neutral_valid_state_passes(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_NEUTRAL)
    assert state["active_neutral"] is not None


def test_lifecycle_stage_q_valid_state_passes(tmp_path):
    _lifecycle_write(tmp_path, "consumed/neutral.json", {})
    _lifecycle_write(tmp_path, "engineering/neutral_result.json", {})
    _lifecycle_write(tmp_path, "authorization/stage_q.json", {})
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STAGE_Q)
    assert state["consumed_neutral"] is not None
    assert state["engineering_neutral"] is not None
    assert state["active_stage_q"] is not None


def test_lifecycle_unknown_authorization_fails(tmp_path):
    _lifecycle_write(tmp_path, "authorization/unknown.json", {})
    with pytest.raises(stage_q.ProtocolError, match="Unknown lifecycle artifact"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_unknown_directory_fails(tmp_path):
    path = tmp_path / "experiments" / "exp021" / "authorization" / "random_directory"
    path.mkdir(parents=True)
    with pytest.raises(stage_q.ProtocolError, match="Unknown lifecycle artifact"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


@pytest.mark.parametrize(
    "relative",
    [
        "neutral_qualification_result.json",
        "stage_q_result.json",
    ],
)
def test_lifecycle_legacy_result_paths_fail(tmp_path, relative):
    _lifecycle_write(tmp_path, relative, {})
    with pytest.raises(stage_q.ProtocolError, match="Legacy lifecycle contamination"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_legacy_results_directory_fails(tmp_path):
    _lifecycle_write(tmp_path, "results/old.json", {})
    with pytest.raises(stage_q.ProtocolError, match="Legacy lifecycle contamination"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


@pytest.mark.parametrize(
    "relative",
    [
        "consumed/unknown.json",
        "engineering/unknown.json",
    ],
)
def test_lifecycle_unknown_consumed_or_engineering_child_fails(tmp_path, relative):
    _lifecycle_write(tmp_path, relative, {})
    with pytest.raises(stage_q.ProtocolError, match="Unknown lifecycle artifact"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_multiple_active_authorizations_fail(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    _lifecycle_write(tmp_path, "authorization/stage_q.json", {})
    with pytest.raises(stage_q.ProtocolError, match="multiple active authorizations"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_active_and_consumed_impossible_fails(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    _lifecycle_write(tmp_path, "consumed/neutral.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="active neutral authorization with neutral consumption record",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_result_without_consumption_fails(tmp_path):
    _lifecycle_write(tmp_path, "engineering/neutral_result.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="neutral qualification result without neutral consumption record",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_stage_q_with_active_neutral_fails(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="Stage-Q requires the neutral authorization to be consumed",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STAGE_Q)


def test_lifecycle_neutral_with_stage_q_consumption_fails(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    _lifecycle_write(tmp_path, "consumed/stage_q.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="Neutral qualification is incompatible with a Stage-Q consumption record",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_NEUTRAL)


def test_lifecycle_known_disposition_paths_not_globally_rejected(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-HISTORICAL")
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)
    assert state["disposition_archives"]
    assert state["disposition_journals"]
    assert state["disposition_records"]
    assert state["unknown_paths"] == []


@pytest.mark.parametrize(
    "relative",
    [
        "authorization/archive/superseded_unconsumed_nonexecutable/wrong-name.json",
        "authorization/disposition_journal/wrong-name.json",
        "authorization/dispositions/wrong-name.json",
    ],
)
def test_lifecycle_wrong_disposition_name_fails(tmp_path, relative):
    _lifecycle_write(tmp_path, relative, {})
    with pytest.raises(stage_q.ProtocolError, match="Unknown lifecycle artifact"):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_prepared_journal_matching_active_authorization_passes(tmp_path):
    auth_path = _lifecycle_write(tmp_path, "authorization/neutral.json", {"active": True})
    digest = stage_q.sha256_file(auth_path)
    _lifecycle_write(tmp_path, f"authorization/disposition_journal/{digest}.json", {})
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)
    assert state["active_neutral"] is not None
    assert state["disposition_journals"]
    assert state["disposition_archives"] == []
    assert state["disposition_records"] == []


def test_lifecycle_active_with_completed_disposition_fails(tmp_path):
    auth_path = _lifecycle_write(tmp_path, "authorization/neutral.json", {"active": True})
    digest = stage_q.sha256_file(auth_path)
    _lifecycle_write(tmp_path, f"authorization/dispositions/{digest}.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="active authorization with archive or completed disposition",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_active_with_journal_for_other_authorization_fails(tmp_path):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {"active": True})
    _lifecycle_write(tmp_path, f"authorization/disposition_journal/{'f' * 64}.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="unresolved historical disposition blocks a replacement authorization",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_completed_historical_plus_active_passes(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    auth_path, _auth, active_hash = _write_active_neutral_auth(
        tmp_path, authorization_id="AUTH-B"
    )
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)
    assert state["active_neutral"] == auth_path
    assert state["disposition_archives"]
    assert state["disposition_journals"]
    assert state["disposition_records"]
    assert active_hash not in {
        Path(path).name for path in state["disposition_records"]
    }


def test_lifecycle_identity_neutral_production_entry_reaches_authorization_semantics(
    tmp_path,
    monkeypatch,
):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events = []
    _patch_lifecycle_common_entry_boundary(monkeypatch, authority, binding, events)

    def fake_validate_authorization(*args, **kwargs):
        events.append("validate_authorization")
        raise stage_q.ProtocolError("reached authorization validation")

    monkeypatch.setattr(stage_q, "validate_authorization", fake_validate_authorization)

    with pytest.raises(stage_q.ProtocolError, match="reached authorization validation"):
        stage_q.run_neutral_hook_qualification(tmp_path)

    assert "validate_authorization" in events
    assert "consume_authorization" not in events


def test_lifecycle_identity_two_completed_historical_dispositions_plus_active_passes(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A2")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-C")
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)
    assert len(state["disposition_archives"]) == 2
    assert len(state["disposition_journals"]) == 2
    assert len(state["disposition_records"]) == 2
    assert state["active_neutral"] is not None


def test_lifecycle_identity_historical_journal_not_unresolved_for_active(tmp_path):
    _auth_a, historical_hash = _create_completed_historical_disposition(
        tmp_path, authorization_id="AUTH-A"
    )
    _auth_path, _auth, active_hash = _write_active_neutral_auth(
        tmp_path, authorization_id="AUTH-B"
    )
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_NEUTRAL)
    assert state["active_neutral"] is not None
    assert [Path(path).name for path in state["disposition_journals"]] == [
        f"{historical_hash}.json"
    ]
    assert active_hash != historical_hash


def test_lifecycle_identity_stage_q_coexists_with_historical_disposition_passes(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _lifecycle_write(tmp_path, "consumed/neutral.json", {})
    _lifecycle_write(tmp_path, "engineering/neutral_result.json", {})
    _lifecycle_write(tmp_path, "authorization/stage_q.json", {})
    state = stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STAGE_Q)
    assert state["active_stage_q"] is not None
    assert state["disposition_records"]
    assert state["disposition_journals"]
    assert state["disposition_archives"]


def test_lifecycle_identity_real_current_structure_static_preflight_passes():
    repo_root = Path(__file__).resolve().parents[1]
    result = stage_q.run_static_preflight(repo_root)
    assert result["status"] == "EXP021_STATIC_PREFLIGHT_PASS"


def test_lifecycle_identity_same_authorization_active_and_disposition_fails(tmp_path):
    _auth_path, _auth, digest = _write_active_neutral_auth(
        tmp_path, authorization_id="AUTH-SAME"
    )
    _lifecycle_write(tmp_path, f"authorization/dispositions/{digest}.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="active authorization with archive or completed disposition",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_same_authorization_active_and_archive_fails(tmp_path):
    _auth_path, _auth, digest = _write_active_neutral_auth(
        tmp_path, authorization_id="AUTH-SAME"
    )
    _lifecycle_write(
        tmp_path,
        f"authorization/archive/superseded_unconsumed_nonexecutable/{digest}.json",
        {},
    )
    with pytest.raises(
        stage_q.ProtocolError,
        match="active authorization with archive or completed disposition",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_unresolved_prepared_blocks_replacement(tmp_path):
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    _lifecycle_write(tmp_path, f"authorization/disposition_journal/{'a' * 64}.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="unresolved historical disposition blocks a replacement authorization",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_unresolved_partial_blocks_replacement(tmp_path):
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    _lifecycle_write(
        tmp_path,
        f"authorization/archive/superseded_unconsumed_nonexecutable/{'a' * 64}.json",
        {},
    )
    _lifecycle_write(tmp_path, f"authorization/disposition_journal/{'a' * 64}.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="unresolved historical disposition blocks a replacement authorization",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_ambiguous_historical_blocks_replacement(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    historical_path = tmp_path / "experiments" / "exp021" / "authorization" / "dispositions"
    record_path = next(historical_path.glob("*.json"))
    record = stage_q.read_json_no_duplicates(record_path)
    record["state"] = stage_q.DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT
    write_json(record_path, record)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_malformed_historical_disposition_fails(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    historical_path = tmp_path / "experiments" / "exp021" / "authorization" / "dispositions"
    record_path = next(historical_path.glob("*.json"))
    write_json(record_path, {})
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_historical_archive_hash_mismatch_fails(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    archive_dir = (
        tmp_path
        / "experiments"
        / "exp021"
        / "authorization"
        / "archive"
        / "superseded_unconsumed_nonexecutable"
    )
    archive_path = next(archive_dir.glob("*.json"))
    write_json(archive_path, {"drift": True})
    with pytest.raises(
        stage_q.ProtocolError,
        match="historical disposition archive hash mismatch",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_historical_disposition_identity_mismatch_fails(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    historical_path = tmp_path / "experiments" / "exp021" / "authorization" / "dispositions"
    record_path = next(historical_path.glob("*.json"))
    record = stage_q.read_json_no_duplicates(record_path)
    record["authorization_sha256"] = "f" * 64
    write_json(record_path, record)
    with pytest.raises(
        stage_q.ProtocolError,
        match="historical disposition identity mismatch",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_multiple_active_authorization_ids_fail(tmp_path):
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    _lifecycle_write(tmp_path, "authorization/stage_q.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="multiple active authorizations",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_cross_authorization_disposition_claims_active_fails(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _auth_path, active_auth, _active_hash = _write_active_neutral_auth(
        tmp_path, authorization_id="AUTH-B"
    )
    historical_path = tmp_path / "experiments" / "exp021" / "authorization" / "dispositions"
    record_path = next(historical_path.glob("*.json"))
    record = stage_q.read_json_no_duplicates(record_path)
    record["authorization_id"] = active_auth["authorization_id"]
    write_json(record_path, record)
    with pytest.raises(
        stage_q.ProtocolError,
        match="active authorization has a completed disposition",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_arbitrary_historical_artifact_fails(tmp_path):
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    _lifecycle_write(
        tmp_path,
        "authorization/archive/superseded_unconsumed_nonexecutable/not-a-hash.json",
        {},
    )
    with pytest.raises(
        stage_q.ProtocolError,
        match="Unknown lifecycle artifact",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_identity_resolved_historical_plus_unknown_child_fails(tmp_path):
    _create_completed_historical_disposition(tmp_path, authorization_id="AUTH-A")
    _write_active_neutral_auth(tmp_path, authorization_id="AUTH-B")
    _lifecycle_write(tmp_path, "authorization/unknown.json", {})
    with pytest.raises(
        stage_q.ProtocolError,
        match="Unknown lifecycle artifact",
    ):
        stage_q.validate_mode_lifecycle(tmp_path, stage_q.LIFECYCLE_MODE_STATIC)


def test_lifecycle_static_preflight_with_active_authorization_passes(tmp_path, monkeypatch):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    events = []
    monkeypatch.setattr(
        stage_q,
        "validate_authority_files",
        lambda *args, **kwargs: {"checkpoint_mapping": _valid_checkpoint_mapping()},
    )

    def fake_validate_checkpoint_mapping(mapping):
        events.append("validate_checkpoint_mapping")

    monkeypatch.setattr(stage_q, "validate_checkpoint_mapping", fake_validate_checkpoint_mapping)
    result = stage_q.run_static_preflight(tmp_path)
    assert result["status"] == "EXP021_STATIC_PREFLIGHT_PASS"
    assert events == ["validate_checkpoint_mapping"]


def test_lifecycle_neutral_production_entry_reaches_authorization_semantics(
    tmp_path,
    monkeypatch,
):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events = []
    _patch_lifecycle_common_entry_boundary(monkeypatch, authority, binding, events)

    def fake_validate_authorization(*args, **kwargs):
        events.append("validate_authorization")
        raise stage_q.ProtocolError("reached authorization validation")

    monkeypatch.setattr(stage_q, "validate_authorization", fake_validate_authorization)

    with pytest.raises(stage_q.ProtocolError, match="reached authorization validation"):
        stage_q.run_neutral_hook_qualification(tmp_path)

    assert "validate_authorization" in events
    assert "consume_authorization" not in events


def test_lifecycle_neutral_production_entry_unknown_authorization_fails_before_consumption(
    tmp_path,
    monkeypatch,
):
    _lifecycle_write(tmp_path, "authorization/unknown.json", {})
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events = []
    _patch_lifecycle_common_entry_boundary(monkeypatch, authority, binding, events)
    consumed = []

    def fake_consume_authorization(*args, **kwargs):
        consumed.append(True)

    monkeypatch.setattr(stage_q, "consume_authorization", fake_consume_authorization)

    with pytest.raises(stage_q.ProtocolError, match="Unknown lifecycle artifact"):
        stage_q.run_neutral_hook_qualification(tmp_path)

    assert consumed == []


def test_lifecycle_stage_q_production_entry_reaches_neutral_semantics(
    tmp_path,
    monkeypatch,
):
    _lifecycle_write(tmp_path, "consumed/neutral.json", {})
    _lifecycle_write(tmp_path, "engineering/neutral_result.json", {})
    _lifecycle_write(tmp_path, "authorization/stage_q.json", {})
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events = []
    _patch_lifecycle_common_entry_boundary(monkeypatch, authority, binding, events)

    def fake_read_neutral_result(path):
        events.append("read_neutral_result")
        return valid_neutral_result(authority, binding)

    monkeypatch.setattr(stage_q, "read_json_no_duplicates", fake_read_neutral_result)

    def fake_validate_neutral_result(*args, **kwargs):
        events.append("validate_neutral_result")
        raise stage_q.ProtocolError("reached neutral semantic validation")

    monkeypatch.setattr(stage_q, "validate_neutral_result", fake_validate_neutral_result)

    with pytest.raises(stage_q.ProtocolError, match="reached neutral semantic validation"):
        stage_q.run_stage_q(tmp_path)

    assert "validate_neutral_result" in events
    assert "consume_authorization" not in events


def test_lifecycle_stage_q_production_entry_active_neutral_fails_before_semantics(
    tmp_path,
    monkeypatch,
):
    _lifecycle_write(tmp_path, "authorization/neutral.json", {})
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events = []
    _patch_lifecycle_common_entry_boundary(monkeypatch, authority, binding, events)
    semantic_events = []

    monkeypatch.setattr(
        stage_q,
        "read_json_no_duplicates",
        lambda *args, **kwargs: semantic_events.append("read_neutral_result"),
    )
    monkeypatch.setattr(
        stage_q,
        "validate_neutral_result",
        lambda *args, **kwargs: semantic_events.append("validate_neutral_result"),
    )

    with pytest.raises(
        stage_q.ProtocolError,
        match="Stage-Q requires the neutral authorization to be consumed",
    ):
        stage_q.run_stage_q(tmp_path)

    assert semantic_events == []


def test_summary_rejects_missing_class_and_nonfinite_probability():
    rows = [
        {
            "checkpoint": "intervention",
            "true_class": stage_q.CLASS_ORDER[index % 4],
            "predicted_class": stage_q.CLASS_ORDER[index % 4],
            "probabilities": [0.25, 0.25, 0.25, 0.25],
            "correct": True,
        }
        for index in range(12)
    ]
    for row in rows:
        if row["predicted_class"] == "definition":
            row["predicted_class"] = "logic"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.summarize_checkpoint(rows, "intervention", "split_a")
    rows[-1]["predicted_class"] = stage_q.CLASS_ORDER[3]
    rows[0]["probabilities"] = [float("nan")] * 4
    with pytest.raises(stage_q.ProtocolError):
        stage_q.summarize_checkpoint(rows, "intervention", "split_a")


def test_inactive_hook_requires_exact_equality():
    no_hook = FakeTensor([[1, 2]])
    inactive = FakeTensor([[1, 2]])
    stage_q.validate_inactive_hook_output(no_hook, inactive, fake_equal)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_inactive_hook_output(no_hook, FakeTensor([[1, 3]]), fake_equal)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_inactive_hook_output(no_hook, no_hook, fake_equal)


def test_active_hook_constructs_exact_expected_output():
    original = FakeTensor(np.zeros((1, 3, 4), dtype=np.float16), dtype=np.float16)
    delta = FakeTensor(np.ones((4,), dtype=np.float32), dtype=np.float32, device="cpu")
    expected = stage_q.construct_expected_hook_output(original, delta, beta=0.75, selected_token_index=2)
    assert np.array_equal(expected.data[0, 2], np.full(4, 0.75, dtype=np.float16))
    assert np.array_equal(original.data, np.zeros((1, 3, 4), dtype=np.float16))


def test_active_hook_checks_non_target_positions_and_invocation_count():
    original = FakeTensor(np.zeros((1, 3, 2), dtype=np.float16), dtype=np.float16)
    delta = FakeTensor(np.ones(2, dtype=np.float16), dtype=np.float16)
    expected = stage_q.construct_expected_hook_output(original, delta, selected_token_index=2)
    actual = expected.clone()
    stage_q.validate_active_hook_output(original, actual, expected, 2, 1, fake_equal)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_active_hook_output(original, actual, expected, 2, 2, fake_equal)
    altered = expected.clone()
    altered.data[0, 0, 0] = 1
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_active_hook_output(original, altered, expected, 2, 1, fake_equal)


def test_active_hook_checks_shape_dtype_and_device():
    original = FakeTensor(np.zeros((1, 2, 2), dtype=np.float16), dtype=np.float16)
    expected = original.clone()
    wrong_shape = FakeTensor(np.zeros((1, 3, 2), dtype=np.float16), dtype=np.float16)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_active_hook_output(original, wrong_shape, expected, 1, 1, fake_equal)
    wrong_device = FakeTensor(np.zeros((1, 2, 2), dtype=np.float16), dtype=np.float16, device="cuda:0")
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_active_hook_output(original, wrong_device, expected, 1, 1, fake_equal)


def test_production_hook_is_independent_from_expected_construction():
    original = FakeTensor(np.zeros((1, 3, 2), dtype=np.float16), dtype=np.float16)
    delta = FakeTensor(np.ones(2, dtype=np.float32), dtype=np.float32)
    hook, state = stage_q.production_hook_factory(delta, 0.75, 2, active=True)
    actual = hook(None, None, original)
    expected = stage_q.construct_expected_hook_output(original, delta, 0.75, 2)
    assert actual is not original
    assert actual is not expected
    stage_q.validate_active_hook_output(original, actual, expected, 2, state["invocations"], fake_equal)


def test_static_preflight_has_no_direct_payload_reads_and_stage_q_has_real_calls():
    tree = ast.parse(Path("experiments/exp021/run_exp021_stage_q.py").read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    static_calls = {ast.unparse(node.func) for node in ast.walk(functions["run_static_preflight"]) if isinstance(node, ast.Call)}
    stage_calls = {ast.unparse(node.func) for node in ast.walk(functions["run_stage_q"]) if isinstance(node, ast.Call)}
    assert "sha256_file" not in static_calls
    assert "load_fit_source_records" in stage_calls
    assert "leave_one_out_fixed_probe" in stage_calls
    assert "stage_q_global_gate" in stage_calls


def test_cleanup_and_fixed_probe_structure_are_explicit():
    tree = ast.parse(Path("experiments/exp021/run_exp021_stage_q.py").read_text(encoding="utf-8"))
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    forward = functions["_forward_with_capture"]
    assert any(isinstance(node, ast.Try) and node.finalbody for node in ast.walk(forward))
    assert any(ast.unparse(node.func) == "handle.remove" for node in ast.walk(forward) if isinstance(node, ast.Call))
    probe = functions["leave_one_out_fixed_probe"]
    probe_source = ast.unparse(probe)
    assert "train_indices" in probe_source
    assert probe_source.count("classifier.fit(") == 1
    assert "for checkpoint, array in arrays.items()" in probe_source
    assert "prompt_text" not in stage_q.STAGE_Q_RESULT_KEYS


def test_checkpoint_constants_are_frozen():
    assert stage_q.INTERVENTION_BLOCK == 16
    assert stage_q.INTERVENTION_HIDDEN_STATE_INDEX == 17
    assert stage_q.BETA == 0.75
    assert [item["name"] for item in stage_q.CHECKPOINTS] == [
        "intervention", "normalized_0.625", "normalized_0.75", "normalized_0.875",
        "final_block_pre_final_rmsnorm", "final_normalized_hidden_state",
    ]
    assert "final_normalized_hidden_state" not in stage_q.REQUIRED_GATE_CHECKPOINTS


def test_probability_mapping_uses_classifier_classes():
    probabilities = np.array([[0.1, 0.2, 0.3, 0.4]])
    mapped = stage_q.map_classifier_probabilities(
        probabilities, ["definition", "logic", "analogy", "causality"], stage_q.CLASS_ORDER
    )
    assert mapped.tolist() == [[0.2, 0.4, 0.3, 0.1]]
    with pytest.raises(stage_q.ProtocolError):
        stage_q.map_classifier_probabilities(probabilities, ["logic", "logic", "analogy", "causality"])


def test_leave_one_out_uses_one_fixed_probe_across_checkpoints():
    labels = [stage_q.CLASS_ORDER[index % 4] for index in range(12)]
    base = np.zeros((12, 2048), dtype=float)
    for index, label in enumerate(labels):
        base[index, stage_q.CLASS_ORDER.index(label)] = 10.0
    representations = {
        item["name"]: base + index * 0.1
        for index, item in enumerate(stage_q.CHECKPOINTS)
    }
    rows = stage_q.leave_one_out_fixed_probe(representations, labels)
    assert len(rows) == 12 * len(stage_q.CHECKPOINTS)
    assert {row["checkpoint"] for row in rows} == set(representations)
    assert {row["held_out_index"] for row in rows} == set(range(12))


def test_leave_one_out_requires_exactly_twelve_items():
    labels = [stage_q.CLASS_ORDER[index % 4] for index in range(8)]
    representations = {"intervention": np.zeros((8, 4))}
    with pytest.raises(stage_q.ProtocolError):
        stage_q.leave_one_out_fixed_probe(representations, labels)


def test_clopper_pearson_boundary():
    assert stage_q.clopper_pearson_lower_bound(7) == pytest.approx(0.276669685682, abs=1e-10)
    assert not stage_q.checkpoint_passes(6)
    assert stage_q.checkpoint_passes(7)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.clopper_pearson_lower_bound(True)


def test_global_gate_requires_all_split_checkpoint_cells():
    rows = [
        {"split_id": split, "checkpoint": checkpoint, "n": 12, "correct": 7, "pass": True}
        for split in ("split_a", "split_b")
        for checkpoint in ("intervention", "normalized_0.625")
    ]
    assert stage_q.stage_q_global_gate(rows, ("split_a", "split_b"), ("intervention", "normalized_0.625"))
    rows[-1] = {**rows[-1], "correct": 6, "pass": False}
    assert not stage_q.stage_q_global_gate(rows, ("split_a", "split_b"), ("intervention", "normalized_0.625"))


def test_global_gate_rejects_duplicate_or_unexpected_cells():
    row = {"split_id": "split_a", "checkpoint": "intervention", "n": 12, "correct": 7, "pass": True}
    with pytest.raises(stage_q.ProtocolError):
        stage_q.stage_q_global_gate([row, row], ("split_a",), ("intervention",))
    with pytest.raises(stage_q.ProtocolError):
        stage_q.stage_q_global_gate([{**row, "checkpoint": "unknown"}], ("split_a",), ("intervention",))


def test_fit_eval_routing_rejects_eval_and_duplicates():
    records = [
        {"item_id": "F1", "split_id": "split_a", "role": "FIT"},
        {"item_id": "F2", "split_id": "split_a", "role": "FIT"},
    ]
    selected = stage_q.validate_fit_eval_routing(records, ["F1", "F2"], ["E1"], "split_a")
    assert [item["item_id"] for item in selected] == ["F1", "F2"]
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_fit_eval_routing(records + [{"item_id": "E1", "split_id": "split_a", "role": "EVAL"}], ["F1", "F2"], ["E1"], "split_a")
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_fit_eval_routing(records + [records[0]], ["F1", "F2"], ["E1"], "split_a")


def test_fit_eval_routing_rejects_overlap_and_missing_fit():
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_fit_eval_routing([], ["X"], ["X"], "split_a")
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_fit_eval_routing([], ["X"], ["E"], "split_a")


def test_authority_schema_constants_are_closed():
    assert "automatic_retry_permitted" in stage_q.NEUTRAL_AUTHORIZATION_KEYS
    assert "fit_access_permitted" in stage_q.STAGE_Q_AUTHORIZATION_KEYS
    assert "scientific_result_created" in stage_q.NEUTRAL_RESULT_KEYS
    assert "scientific_result_created" in stage_q.STAGE_Q_RESULT_KEYS


def test_runtime_execution_functions_are_not_invoked_by_import():
    assert callable(stage_q.run_neutral_hook_qualification)
    assert callable(stage_q.run_stage_q)
    assert callable(stage_q.run_static_preflight)


def test_static_preflight_result_declares_no_persistent_output():
    # This checks the returned contract without invoking the authority-reading mode.
    expected_keys = {"status", "experiment", "stage_q_authorizable", "stage_p_authorizable", "model_manifest_validated", "prompt_text_accessed", "tensor_payload_accessed", "persistent_output_created"}
    assert expected_keys


def test_neutral_result_accepts_complete_identity():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    stage_q.validate_neutral_result(result, authority, binding)


@pytest.mark.parametrize(
    "field,value",
    [
        ("dtype", "float32"),
        ("device", "cpu"),
        ("local_files_only", False),
        ("model_eval_mode", False),
        ("gradients_enabled", True),
        ("use_cache", True),
    ],
)
def test_neutral_result_rejects_execution_environment_drift(field, value):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["execution_environment"][field] = value
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


@pytest.mark.parametrize(
    "field",
    ["python", "torch", "transformers", "cuda_runtime", "nvidia_driver", "gpu"],
)
def test_neutral_result_rejects_missing_runtime_identity_field(field):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["execution_environment"][field] = ""
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


@pytest.mark.parametrize(
    "field,bogus",
    [
        ("python", "9.9.9"),
        ("torch", "999.0"),
        ("transformers", "999.0"),
        ("cuda_runtime", "99.9"),
        ("nvidia_driver", "999.99"),
        ("gpu", "Bogus GPU"),
    ],
)
def test_neutral_result_rejects_wrong_nonempty_runtime_identity(field, bogus):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["execution_environment"][field] = bogus
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_result_rejects_torch_version_drift():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["execution_environment"]["torch"] = "999.0"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_result_rejects_transformers_version_drift():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["execution_environment"]["transformers"] = "999.0"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_result_rejects_execution_environment_unknown_key():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["execution_environment"]["unexpected"] = True
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


@pytest.mark.parametrize(
    "field,value",
    [
        ("algorithm", "not-alternating"),
        ("length", 2047),
        ("sha256", "a" * 64),
    ],
)
def test_neutral_result_rejects_diagnostic_vector_drift(field, value):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["diagnostic_vector"][field] = value
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_result_rejects_diagnostic_vector_unknown_key():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["diagnostic_vector"]["unexpected"] = True
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_result_rejects_neutral_input_identity_drift():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["neutral_input_identity"]["sha256"] = "a" * 64
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_result_rejects_neutral_input_identity_unknown_key():
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    result = valid_neutral_result(authority, binding)
    result["neutral_input_identity"]["unexpected"] = True
    with pytest.raises(stage_q.ProtocolError):
        stage_q.validate_neutral_result(result, authority, binding)


def test_neutral_production_path_validates_before_publish(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events, _, published = _install_neutral_entry_harness(
        monkeypatch,
        authority,
        binding,
    )

    stage_q.run_neutral_hook_qualification(tmp_path)

    assert published
    assert events.count("validate_neutral_result") == 1
    assert events.count("_forward_with_capture") == 3
    assert events.index("consume_authorization") < events.index("_forward_with_capture")
    assert events.index("validate_neutral_result") < events.index("atomic_publish_json")


def test_neutral_invalid_drift_blocks_publication(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events, _, published = _install_neutral_entry_harness(
        monkeypatch,
        authority,
        binding,
        environment=synthetic_runtime_environment(dtype="float32"),
    )

    with pytest.raises(stage_q.ProtocolError):
        stage_q.run_neutral_hook_qualification(tmp_path)

    assert "validate_neutral_result" in events
    assert "atomic_publish_json" not in events
    assert not published


def test_neutral_validator_removal_is_detected(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events, _, _ = _install_neutral_entry_harness(
        monkeypatch,
        authority,
        binding,
    )
    monkeypatch.setattr(stage_q, "validate_neutral_result", lambda *args, **kwargs: None)

    with pytest.raises(AssertionError):
        stage_q.run_neutral_hook_qualification(tmp_path)


def test_stage_q_production_path_validates_neutral_before_consumption(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    neutral_result = valid_neutral_result(authority, binding)
    events, published = _install_stage_q_entry_harness(
        monkeypatch,
        authority,
        binding,
        neutral_result,
    )

    stage_q.run_stage_q(tmp_path)

    assert published
    assert events.count("validate_neutral_result") == 1
    assert events.index("validate_neutral_result") < events.index("consume_authorization")
    assert events.index("consume_authorization") < events.index("_load_model_and_tokenizer")
    assert events.index("_load_model_and_tokenizer") < events.index("load_fit_source_records")
    assert events.index("validate_stage_q_result") < events.index("atomic_publish_json")


def test_stage_q_invalid_neutral_drift_blocks_consumption(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    neutral_result = valid_neutral_result(authority, binding)
    neutral_result["execution_environment"]["device"] = "cpu"
    events, published = _install_stage_q_entry_harness(
        monkeypatch,
        authority,
        binding,
        neutral_result,
    )

    with pytest.raises(stage_q.ProtocolError):
        stage_q.run_stage_q(tmp_path)

    assert "validate_neutral_result" in events
    assert "consume_authorization" not in events
    assert "atomic_publish_json" not in events
    assert not published


@pytest.mark.parametrize(
    "field,bogus",
    [
        ("python", "9.9.9"),
        ("torch", "999.0"),
        ("transformers", "999.0"),
        ("cuda_runtime", "99.9"),
        ("nvidia_driver", "999.99"),
        ("gpu", "Bogus GPU"),
    ],
)
def test_stage_q_rejects_dynamic_runtime_drift_before_consumption(
    tmp_path,
    monkeypatch,
    field,
    bogus,
):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    neutral_result = valid_neutral_result(authority, binding)
    neutral_result["execution_environment"][field] = bogus
    events, published = _install_stage_q_entry_harness(
        monkeypatch,
        authority,
        binding,
        neutral_result,
    )

    with pytest.raises(stage_q.ProtocolError):
        stage_q.run_stage_q(tmp_path)

    assert "validate_neutral_result" in events
    assert "consume_authorization" not in events
    assert "validate_model_manifest" not in events
    assert "_load_model_and_tokenizer" not in events
    assert "load_fit_source_records" not in events
    assert "atomic_publish_json" not in events
    assert not published



def _authority_gate_payload():
    return {
        "overall_status": "EXP021_AMENDMENT_READY_FOR_TARGETED_FINAL_REREVIEW",
        "hook_oracle_protocol_status": "FROZEN",
        "hook_oracle_runtime_qualification_status": "NOT_RUN",
        "hook_oracle_runtime_qualified": False,
        "stage_q_authorizable": False,
        "stage_p_authorizable": False,
        "open_decision_statuses": [
            {"id": "R17", "status": "RESOLVED_BY_TRANSPARENT_PROSPECTIVE_PRE_RUN_AMENDMENT"},
            {"id": "R20", "status": "RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT"},
            {"id": "R22", "status": "REMAINS_OPEN_NONBLOCKING"},
        ],
        "primary_model_identity": {},
        "checkpoint_mapping": {
            "intervention": {"block_index": 16, "hidden_state_index": 17, "beta": 0.75}
        },
        "stage_q_fit_only_measurement_qualification": {
            "qualification_metrics": {
                "threshold_verification": {
                    "correct": 7,
                    "total": 12,
                    "lower_bound": 0.276669685682,
                    "strictly_greater_than_chance": True,
                    "interval_definition": "scipy.stats.beta.ppf(0.025, correct, total-correct+1)",
                }
            }
        },
    }


def test_authority_archive_commit_used_as_blob_anchor_without_head_gate(tmp_path, monkeypatch):
    calls = []

    def fake_git(root, *args):
        calls.append(args)
        if args[0] == "ls-tree":
            if "AMENDMENT" in args[2]:
                return "100644 blob 7a71dcc767db4a785fd3fdee2d75681427ae76f6 path"
            return "100644 blob 08d621f311dbc1c9c2c00ef024cdc42a6ac3c6f7 path"
        raise AssertionError(f"unexpected git call: {args}")

    def fake_sha(path):
        name = str(path)
        if "PREREGISTRATION.md" in name:
            return stage_q.ORIGINAL_PREREGISTRATION_SHA256
        if "AMENDMENT" in name:
            return stage_q.AMENDMENT_SHA256
        return stage_q.RECONCILIATION_SHA256

    monkeypatch.setattr(stage_q, "_git_output", fake_git)
    monkeypatch.setattr(stage_q, "sha256_file", fake_sha)
    monkeypatch.setattr(stage_q, "read_json_no_duplicates", lambda path: _authority_gate_payload())
    monkeypatch.setattr(stage_q, "validate_model_manifest", lambda *args, **kwargs: None)
    monkeypatch.setattr(stage_q, "validate_checkpoint_mapping", lambda *args, **kwargs: None)

    stage_q.validate_authority_files(tmp_path)

    assert not any(args[0] == "rev-parse" for args in calls)
    assert any(
        args[0] == "ls-tree" and args[1] == stage_q.AUTHORITY_ARCHIVE_COMMIT
        for args in calls
    )


def test_authorization_accepts_exact_live_commit_binding(tmp_path):
    auth = neutral_authorization(tmp_path, runner_commit="live-commit", runner_sha256="a" * 64)
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, auth)
    expected = dict(auth)
    stage_q.consume_authorization(
        auth_path,
        tmp_path / "consumed.json",
        tmp_path,
        stage_q.NEUTRAL_SCOPE,
        expected_identity=expected,
    )
    assert (tmp_path / "consumed.json").exists()


def test_authorization_rejects_live_commit_mismatch(tmp_path):
    auth = neutral_authorization(tmp_path, runner_commit="live-commit", runner_sha256="a" * 64)
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, auth)
    expected = dict(auth)
    expected["runner_commit"] = "different-live-commit"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(
            auth_path,
            tmp_path / "consumed.json",
            tmp_path,
            stage_q.NEUTRAL_SCOPE,
            expected_identity=expected,
        )
    assert not (tmp_path / "consumed.json").exists()


def test_authorization_rejects_live_runner_hash_mismatch(tmp_path):
    auth = neutral_authorization(tmp_path, runner_commit="live-commit", runner_sha256="a" * 64)
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, auth)
    expected = dict(auth)
    expected["runner_sha256"] = "b" * 64
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(
            auth_path,
            tmp_path / "consumed.json",
            tmp_path,
            stage_q.NEUTRAL_SCOPE,
            expected_identity=expected,
        )
    assert not (tmp_path / "consumed.json").exists()


def test_authorization_rejects_authority_archive_commit_as_live_commit(tmp_path):
    auth = neutral_authorization(tmp_path, runner_commit="authorized-live-commit", runner_sha256="a" * 64)
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, auth)
    expected = dict(auth)
    expected["runner_commit"] = stage_q.AUTHORITY_ARCHIVE_COMMIT
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(
            auth_path,
            tmp_path / "consumed.json",
            tmp_path,
            stage_q.NEUTRAL_SCOPE,
            expected_identity=expected,
        )
    assert not (tmp_path / "consumed.json").exists()


def test_authorization_rejects_descendant_commit_substitution(tmp_path):
    auth = neutral_authorization(tmp_path, runner_commit="authorized-live-commit", runner_sha256="a" * 64)
    auth_path = tmp_path / "authorization.json"
    write_json(auth_path, auth)
    expected = dict(auth)
    expected["runner_commit"] = "authorized-live-commit-child"
    with pytest.raises(stage_q.ProtocolError):
        stage_q.consume_authorization(
            auth_path,
            tmp_path / "consumed.json",
            tmp_path,
            stage_q.NEUTRAL_SCOPE,
            expected_identity=expected,
        )
    assert not (tmp_path / "consumed.json").exists()


def test_neutral_production_entry_binds_live_commit_before_consumption(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    events, _, published = _install_neutral_entry_harness(monkeypatch, authority, binding)
    captured = {}

    def spy_consume(auth_path, consumption_path, root, scope, *, expected_identity, expected_output_path):
        events.append("consume_authorization")
        captured["expected_identity"] = expected_identity
        return (
            {"authorization_id": "AUTH-NEUTRAL-001"},
            {"attempt_id": "ATTEMPT-NEUTRAL-001", "authorization_hash": "f" * 64},
        )

    monkeypatch.setattr(stage_q, "consume_authorization", spy_consume)
    stage_q.run_neutral_hook_qualification(tmp_path)

    assert captured["expected_identity"]["runner_commit"] == binding["runner_commit"]
    assert captured["expected_identity"]["runner_sha256"] == binding["runner_sha256"]
    assert events.index("consume_authorization") < events.index("_load_model_and_tokenizer")


def test_stage_q_production_entry_binds_live_commit_before_consumption(tmp_path, monkeypatch):
    authority = synthetic_authority()
    binding = synthetic_binding(authority)
    neutral_result = valid_neutral_result(authority, binding)
    events, published = _install_stage_q_entry_harness(monkeypatch, authority, binding, neutral_result)
    captured = {}

    def spy_consume(auth_path, consumption_path, root, scope, *, expected_identity, expected_output_path):
        events.append("consume_authorization")
        captured["expected_identity"] = expected_identity
        return (
            {"authorization_id": "AUTH-STAGE-Q-001"},
            {"attempt_id": "ATTEMPT-STAGE-Q-001", "authorization_hash": "f" * 64},
        )

    monkeypatch.setattr(stage_q, "consume_authorization", spy_consume)
    stage_q.run_stage_q(tmp_path)

    assert captured["expected_identity"]["runner_commit"] == binding["runner_commit"]
    assert captured["expected_identity"]["runner_sha256"] == binding["runner_sha256"]
    assert events.index("consume_authorization") < events.index("_load_model_and_tokenizer")


def _write_disposition_auth(tmp_path):
    auth = neutral_authorization(tmp_path)
    auth_path = tmp_path / "authorization" / "neutral.json"
    write_json(auth_path, auth)
    return auth_path, auth


def _disposition_args(tmp_path, auth_path, auth, **overrides):
    kwargs = {
        "repo_root": tmp_path,
        "authorization_path": auth_path,
        "expected_authorization_id": auth["authorization_id"],
        "expected_authorization_sha256": stage_q.sha256_file(auth_path),
        "expected_scope": stage_q.NEUTRAL_SCOPE,
        "explicit_disposition_authorized": True,
        "non_executable_reason": "test binding correction",
    }
    kwargs.update(overrides)
    return kwargs


def test_disposition_requires_explicit_authorization(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth, explicit_disposition_authorized=False)
        )
    assert auth_path.exists()


def test_disposition_preserves_original_authorization_hash(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    record = stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    archive_path = tmp_path / stage_q.AUTHORIZATION_ARCHIVE_RELATIVE_DIR / f"{original_hash}.json"
    assert record["authorization_sha256"] == original_hash
    assert stage_q.sha256_file(archive_path) == original_hash


def test_disposition_frees_active_authorization_path(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    assert not auth_path.exists()


def test_disposition_record_binds_authorization_hash(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    record = stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    assert record["authorization_sha256"] == original_hash
    disposition_path = tmp_path / stage_q.AUTHORIZATION_DISPOSITION_RELATIVE_DIR / f"{original_hash}.json"
    assert stage_q.read_json_no_duplicates(disposition_path)["authorization_sha256"] == original_hash


def test_disposition_rejects_consumed_authorization(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    auth["consumed"] = True
    write_json(auth_path, auth)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )
    assert auth_path.exists()


def test_disposition_rejects_consumption_record(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    consumption_path = tmp_path / stage_q.NEUTRAL_CONSUMPTION_RELATIVE_PATH
    write_json(consumption_path, {"state": "consumed"})
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )
    assert auth_path.exists()


def test_disposition_rejects_qualification_result(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    result_path = tmp_path / stage_q.NEUTRAL_RESULT_RELATIVE_PATH
    write_json(result_path, {"overall_pass": False})
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )
    assert auth_path.exists()


def test_disposition_rejects_hash_drift(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth, expected_authorization_sha256="f" * 64)
        )
    assert auth_path.exists()


def test_disposition_rejects_existing_archive_destination(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path = tmp_path / stage_q.AUTHORIZATION_ARCHIVE_RELATIVE_DIR / f"{original_hash}.json"
    write_json(archive_path, {"occupied": True})
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )
    assert auth_path.exists()


def test_disposition_rejects_existing_disposition_record(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    disposition_path = tmp_path / stage_q.AUTHORIZATION_DISPOSITION_RELATIVE_DIR / f"{original_hash}.json"
    write_json(disposition_path, {"occupied": True})
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )
    assert auth_path.exists()


def test_disposition_does_not_create_replacement_authorization(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    assert not (tmp_path / "authorization" / "neutral.json").exists()


def test_disposition_does_not_create_consumption_record(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    assert not (tmp_path / stage_q.NEUTRAL_CONSUMPTION_RELATIVE_PATH).exists()


def test_disposition_archive_is_not_active_authorization(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    with pytest.raises(stage_q.ProtocolError):
        stage_q.confined_path(auth_path, tmp_path)


def _disposition_paths_for_hash(tmp_path, original_hash):
    return stage_q._disposition_transaction_paths(Path(tmp_path).resolve(), original_hash)


def _recover_disposition_args(tmp_path, auth_path, auth, original_hash, **overrides):
    kwargs = {
        "repo_root": tmp_path,
        "active_authorization_path": auth_path,
        "expected_authorization_id": auth["authorization_id"],
        "expected_authorization_sha256": original_hash,
        "expected_scope": stage_q.NEUTRAL_SCOPE,
        "explicit_disposition_authorized": True,
        "non_executable_reason": "test binding correction",
    }
    kwargs.update(overrides)
    return kwargs


def _interrupt_after_move(tmp_path, monkeypatch):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)

    def fail_record(path, record, root):
        raise stage_q.ProtocolError("injected before final disposition publication")

    with monkeypatch.context() as patch:
        patch.setattr(stage_q, "_publish_disposition_record", fail_record)
        with pytest.raises(stage_q.ProtocolError):
            stage_q.disposition_unconsumed_nonexecutable_authorization(
                **_disposition_args(tmp_path, auth_path, auth)
            )
    return auth_path, auth, original_hash


def test_disposition_failure_before_journal_leaves_active_unchanged(tmp_path, monkeypatch):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)
    original_bytes = auth_path.read_bytes()

    def fail_journal(path, payload, root):
        raise stage_q.ProtocolError("injected before journal creation")

    monkeypatch.setattr(stage_q, "_publish_disposition_journal", fail_journal)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )

    assert auth_path.read_bytes() == original_bytes
    assert not archive_path.exists()
    assert not journal_path.exists()
    assert not disposition_path.exists()


def test_disposition_prepared_before_move_blocks_replacement(tmp_path, monkeypatch):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)

    def fail_archive(path, archive, authorization_hash):
        raise stage_q.ProtocolError("injected after journal before move")

    monkeypatch.setattr(stage_q, "_archive_disposition_authorization", fail_archive)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )

    assert auth_path.exists()
    assert not archive_path.exists()
    assert journal_path.exists()
    assert not disposition_path.exists()
    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_PREPARED_OR_IN_PROGRESS
    assert lifecycle["replacement_blocked"] is True
    assert stage_q.is_replacement_authorization_blocked(
        tmp_path, auth_path, auth["authorization_id"], original_hash, stage_q.NEUTRAL_SCOPE
    )


def test_disposition_os_replace_failure_blocks_replacement(tmp_path, monkeypatch):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)

    def fail_replace(source, destination):
        raise OSError("injected os.replace failure")

    monkeypatch.setattr(stage_q.os, "replace", fail_replace)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )

    assert auth_path.exists()
    assert not archive_path.exists()
    assert journal_path.exists()
    assert not disposition_path.exists()
    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_PREPARED_OR_IN_PROGRESS
    assert lifecycle["replacement_blocked"] is True


def test_disposition_interrupted_after_move_is_recoverable(tmp_path, monkeypatch):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)

    assert not auth_path.exists()
    assert archive_path.exists()
    assert journal_path.exists()
    assert not disposition_path.exists()
    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_PARTIAL_OR_RECOVERY_REQUIRED
    assert lifecycle["replacement_blocked"] is True


def test_disposition_final_publication_failure_is_recoverable(tmp_path, monkeypatch):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)
    real_atomic = stage_q.atomic_publish_json

    def fail_final(path, payload, root):
        if Path(path) == disposition_path:
            raise stage_q.ProtocolError("injected final disposition publication failure")
        return real_atomic(path, payload, root)

    with monkeypatch.context() as patch:
        patch.setattr(stage_q, "atomic_publish_json", fail_final)
        with pytest.raises(stage_q.ProtocolError):
            stage_q.disposition_unconsumed_nonexecutable_authorization(
                **_disposition_args(tmp_path, auth_path, auth)
            )

    assert not auth_path.exists()
    assert archive_path.exists()
    assert journal_path.exists()
    assert not disposition_path.exists()
    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_PARTIAL_OR_RECOVERY_REQUIRED
    assert lifecycle["replacement_blocked"] is True


def test_disposition_recovery_preserves_archive_and_finalizes(tmp_path, monkeypatch):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)

    record = stage_q.recover_disposition_transaction(
        **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
    )

    assert record["state"] == stage_q.DISPOSITION_STATE_DISPOSITIONED
    assert record["authorization_sha256"] == original_hash
    assert stage_q.sha256_file(archive_path) == original_hash
    assert disposition_path.exists()
    assert stage_q.read_json_no_duplicates(disposition_path)["state"] == stage_q.DISPOSITION_STATE_DISPOSITIONED
    assert not (tmp_path / stage_q.NEUTRAL_CONSUMPTION_RELATIVE_PATH).exists()
    assert not (tmp_path / "authorization" / "neutral.json").exists()


def test_disposition_recovery_is_idempotent_after_completion(tmp_path, monkeypatch):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)

    first = stage_q.recover_disposition_transaction(
        **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
    )
    disposition_before = disposition_path.read_bytes()
    second = stage_q.recover_disposition_transaction(
        **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
    )

    assert first == second
    assert disposition_path.read_bytes() == disposition_before
    assert stage_q.sha256_file(archive_path) == original_hash


def test_disposition_recovery_rejects_identity_mismatch(tmp_path, monkeypatch):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)

    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(
                tmp_path, auth_path, auth, original_hash, expected_authorization_id="WRONG"
            )
        )
    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(
                tmp_path, auth_path, auth, original_hash, expected_authorization_sha256="f" * 64
            )
        )
    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(
                tmp_path, auth_path, auth, original_hash, non_executable_reason="different reason"
            )
        )
    assert not disposition_path.exists()


def test_disposition_archive_without_journal_or_record_fails_closed(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(auth_path.read_bytes())
    auth_path.unlink()

    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT
    assert lifecycle["replacement_blocked"] is True
    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
        )


def test_disposition_record_without_archive_fails_closed(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    stage_q.disposition_unconsumed_nonexecutable_authorization(
        **_disposition_args(tmp_path, auth_path, auth)
    )
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)
    archive_path.unlink()

    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT
    assert lifecycle["replacement_blocked"] is True


def test_disposition_active_and_archive_both_exist_fails_closed(tmp_path):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(tmp_path, original_hash)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(auth_path.read_bytes())

    lifecycle = stage_q.inspect_disposition_transaction(
        tmp_path,
        auth_path,
        auth["authorization_id"],
        original_hash,
        stage_q.NEUTRAL_SCOPE,
    )
    assert lifecycle["state"] == stage_q.DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT
    assert lifecycle["replacement_blocked"] is True
    with pytest.raises(stage_q.ProtocolError):
        stage_q.disposition_unconsumed_nonexecutable_authorization(
            **_disposition_args(tmp_path, auth_path, auth)
        )


def test_disposition_incomplete_blocks_replacement_eligibility(tmp_path, monkeypatch):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    assert stage_q.is_replacement_authorization_blocked(
        tmp_path, auth_path, auth["authorization_id"], original_hash, stage_q.NEUTRAL_SCOPE
    )


def _tamper_journal(journal_path, field, value):
    journal = stage_q.read_json_no_duplicates(journal_path)
    journal[field] = value
    journal["journal_sha256"] = stage_q._disposition_journal_sha256(journal)
    write_json(journal_path, journal)
    return stage_q.read_json_no_duplicates(journal_path)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("authorization_runner_commit", "drifted-commit"),
        ("authorization_runner_sha256", "f" * 64),
        ("transaction_id", "DISP-TXN-DRIFT"),
        ("disposition_record_id", "DISP-DRIFT"),
        ("authorization_id", "AUTH-DRIFT"),
        ("authorization_scope", "OTHER_SCOPE"),
        ("authorization_sha256", "e" * 64),
        ("expected_archive_path", "other/archive.json"),
        ("expected_disposition_path", "other/disposition.json"),
        ("disposition_type", "OTHER_DISPOSITION"),
        ("non_executable_reason", "tampered reason"),
    ],
)
def test_disposition_recovery_rejects_tampered_self_hashed_journal(
    tmp_path, monkeypatch, field, value
):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(
        tmp_path, original_hash
    )
    _tamper_journal(journal_path, field, value)

    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
        )
    assert not disposition_path.exists()
    assert stage_q.sha256_file(archive_path) == original_hash


def test_disposition_rejects_valid_self_hash_but_drifted_runner_identity(
    tmp_path, monkeypatch
):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(
        tmp_path, original_hash
    )
    tampered = _tamper_journal(
        journal_path, "authorization_runner_commit", "drifted-commit"
    )

    stage_q.validate_disposition_journal(tampered)
    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
        )
    assert not disposition_path.exists()


def test_disposition_recovery_resumes_exact_pre_move_prepared_state(
    tmp_path, monkeypatch
):
    auth_path, auth = _write_disposition_auth(tmp_path)
    original_hash = stage_q.sha256_file(auth_path)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(
        tmp_path, original_hash
    )

    def fail_archive(path, archive, authorization_hash):
        raise stage_q.ProtocolError("injected before move")

    with monkeypatch.context() as patch:
        patch.setattr(stage_q, "_archive_disposition_authorization", fail_archive)
        with pytest.raises(stage_q.ProtocolError):
            stage_q.disposition_unconsumed_nonexecutable_authorization(
                **_disposition_args(tmp_path, auth_path, auth)
            )

    record = stage_q.recover_disposition_transaction(
        **_recover_disposition_args(tmp_path, auth_path, auth, original_hash)
    )

    assert record["state"] == stage_q.DISPOSITION_STATE_DISPOSITIONED
    assert not auth_path.exists()
    assert archive_path.exists()
    assert stage_q.sha256_file(archive_path) == original_hash
    assert disposition_path.exists()
    assert not (tmp_path / stage_q.NEUTRAL_CONSUMPTION_RELATIVE_PATH).exists()


def test_disposition_recovery_cross_authorization_attack_fails(
    tmp_path, monkeypatch
):
    auth_path, auth, original_hash = _interrupt_after_move(tmp_path, monkeypatch)
    archive_path, journal_path, disposition_path = _disposition_paths_for_hash(
        tmp_path, original_hash
    )

    other_auth = neutral_authorization(
        tmp_path, authorization_id="AUTH-OTHER", runner_commit="other-live-commit"
    )
    other_path = tmp_path / "authorization" / "other.json"
    write_json(other_path, other_auth)
    other_hash = stage_q.sha256_file(other_path)

    with pytest.raises(stage_q.ProtocolError):
        stage_q.recover_disposition_transaction(
            **_recover_disposition_args(
                tmp_path,
                auth_path,
                other_auth,
                other_hash,
            )
        )

    assert not disposition_path.exists()
    assert stage_q.sha256_file(archive_path) == original_hash
    assert not (tmp_path / stage_q.NEUTRAL_CONSUMPTION_RELATIVE_PATH).exists()
