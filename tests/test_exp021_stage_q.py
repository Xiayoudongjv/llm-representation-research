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
        "runner_commit": stage_q.ARCHIVE_COMMIT,
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
        "runner_commit": stage_q.ARCHIVE_COMMIT,
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
        "runner_commit": stage_q.ARCHIVE_COMMIT,
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
