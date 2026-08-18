"""Focused EXP-024 frozen-runner and static-preflight tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import torch


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "exp024"
    / "run_exp024.py"
)
MODULE_NAME = "exp024_runner"
SPEC = importlib.util.spec_from_file_location(MODULE_NAME, MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules[MODULE_NAME] = runner
SPEC.loader.exec_module(runner)


@pytest.fixture(scope="module")
def frozen_data():
    return runner.load_frozen_dataset()


def _valid_result() -> dict[str, object]:
    return {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "experiment": runner.EXPERIMENT,
        "runner": {"path": "x", "sha256": "a" * 64},
        "model": {
            "model_id": runner.FORMAL_MODEL_NAME,
            "snapshot": runner.FORMAL_MODEL_SNAPSHOT,
        },
        "dataset": {"path": "x", "sha256": runner.FROZEN_DATASET_SHA256},
        "classes": list(runner.CLASS_ORDER),
        "primary": {
            "statistic": "Spearman_rho",
            "permutation_count": runner.PERMUTATION_COUNT,
            "support_rule": runner.SUPPORT_RULE,
        },
        "technical_validity": {"status": "VALID"},
        "attempt_status": "FORMAL_RUN_ATTEMPT_COMPLETED",
        "result_status": "FORMAL_RESULT",
        "scientific_status": "FORMAL_ANALYSIS_COMPLETED",
        "provenance": {},
        "hidden_states_included": False,
        "prompt_text_included": False,
    }


def _authorization(
    *,
    runner_sha: str | None = None,
    qualification_sha: str = "b" * 64,
) -> dict[str, object]:
    return {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "experiment": runner.EXPERIMENT,
        "authorization_id": "test-auth",
        "single_use": True,
        "authorized_repository_commit": runner._repository_commit(),
        "authorized_runner_sha256": runner_sha or runner._runner_sha256(),
        "frozen_manifest_sha256": runner.FROZEN_MANIFEST_SHA256,
        "frozen_dataset_sha256": runner.FROZEN_DATASET_SHA256,
        "preregistration_sha256": runner.FINAL_PREREGISTRATION_SHA256,
        "model_name": runner.FORMAL_MODEL_NAME,
        "model_snapshot_identity": runner.FORMAL_MODEL_SNAPSHOT,
        "model_hook_qualification_sha256": qualification_sha,
        "canonical_result_path": runner.CANONICAL_RESULT_PATH.relative_to(runner.ROOT).as_posix(),
        "authorization_created_at_utc": "2026-08-18T00:00:00+00:00",
    }


def _mock_qualification(monkeypatch: pytest.MonkeyPatch, sha: str = "b" * 64) -> None:
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_artifact",
        lambda root=None: {"sha256": sha, "artifact": {}},
    )


class FakeConfig:
    model_type = "qwen3"
    hidden_size = 4
    num_hidden_layers = 28


class FakeLayer:
    pass


class FakeTransformer:
    def __init__(self):
        self.layers = [FakeLayer() for _ in range(28)]


class FakeModel:
    training = False

    def __init__(self):
        self.config = FakeConfig()
        self.model = FakeTransformer()

    def parameters(self):
        return iter([torch.tensor([0.0], dtype=torch.float32)])


class FakeTokenizer:
    all_special_ids = {1}

    def __call__(self, text, return_tensors=None, padding=False, truncation=False, add_special_tokens=True):
        return {
            "input_ids": torch.tensor([[0, 2, 1]], dtype=torch.long),
            "attention_mask": torch.ones((1, 3), dtype=torch.long),
        }


def _fake_forward(tokenizer, model, device, text):
    return {
        "input_ids": torch.tensor([[0, 2, 1]], dtype=torch.long, device=device),
        "attention_mask": torch.ones((1, 3), dtype=torch.long, device=device),
        "representations": {
            name: np.full((4,), index + 1, dtype=np.float32)
            for index, name in enumerate(runner.QUALIFICATION_CHECKPOINT_NAMES)
        },
        "hook_firing_count": 1,
        "hook_cleanup_verified": True,
        "exp024_hooks_remaining": 0,
        "foreign_hooks_remaining": 0,
    }
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_current",
        lambda artifact: None,
    )


def test_frozen_identity_validation_actual_repo():
    authorities = runner.verify_frozen_authority()
    assert authorities["dataset"]["sha256"] == runner.FROZEN_DATASET_SHA256
    assert authorities["preregistration"]["sha256"] == runner.FINAL_PREREGISTRATION_SHA256
    assert authorities["manifest"]["sha256"] == runner.FROZEN_MANIFEST_SHA256


def test_frozen_dataset_loader_uses_registered_path():
    assert runner.FROZEN_DATASET_PATH.name == "exp024_condition_panel_frozen.json"
    assert "candidate" not in runner.FROZEN_DATASET_PATH.name


def test_no_candidate_dataset_fallback(frozen_data, monkeypatch):
    calls: list[Path] = []
    original_read_json = runner.read_json

    def tracked_read_json(path: Path):
        calls.append(Path(path))
        return original_read_json(path)

    monkeypatch.setattr(runner, "read_json", tracked_read_json)
    records, metas = runner.load_frozen_dataset()
    dataset_calls = [path for path in calls if path.name == "exp024_condition_panel_frozen.json"]
    assert dataset_calls
    assert all("candidate" not in path.name for path in dataset_calls)
    assert len(records) == 1760
    assert len(metas) == 1760


def test_pairing_metadata_semantics(frozen_data):
    records, metas = frozen_data
    by_family: dict[str, list[dict[str, object]]] = {}
    for record in records:
        by_family.setdefault(record["source_family_id"], []).append(record)
    for family_id, family in by_family.items():
        roles = {record["record_role"] for record in family}
        assert roles == set(runner.RECORD_ROLES)


def test_deterministic_class_ordering_and_classifier_mapping():
    assert runner.CLASS_ORDER == ("logic", "causality", "analogy", "definition")
    X = np.array([[0.0], [1.0], [2.0], [3.0], [4.0], [5.0], [6.0], [7.0]])
    y = ["definition", "causality", "analogy", "logic", "definition", "causality", "analogy", "logic"]
    classifier, labels = runner.fit_classifier(X, y)
    assert labels == [str(value) for value in classifier.classes_]
    assert runner.classifier_class_mapping(classifier) == labels


def test_partitions_disjoint(frozen_data):
    records, _ = frozen_data
    partitions = runner.partition_records(records)
    family_sets = {
        partition: {record["source_family_id"] for record in rows}
        for partition, rows in partitions.items()
    }
    assert not (family_sets["FIT"] & family_sets["DIAGNOSTIC"])
    assert not (family_sets["FIT"] & family_sets["EVAL"])
    assert not (family_sets["DIAGNOSTIC"] & family_sets["EVAL"])


def test_reference_readout_uses_fit_reference_only(frozen_data):
    records, _ = frozen_data
    reference_fit = [
        record
        for record in records
        if record["partition"] == "FIT" and record["record_role"] == "reference_form"
    ]
    assert reference_fit
    assert all(record["partition"] == "FIT" for record in reference_fit)
    assert all(record["record_role"] == "reference_form" for record in reference_fit)


def test_no_diag_eval_leakage_into_cref(frozen_data):
    records, _ = frozen_data
    reference_fit_ids = {
        record["source_family_id"]
        for record in records
        if record["partition"] == "FIT" and record["record_role"] == "reference_form"
    }
    assert all(
        record["source_family_id"] in reference_fit_ids
        for record in records
        if record["partition"] == "FIT" and record["record_role"] == "reference_form"
    )
    leaked = {
        record["source_family_id"]
        for record in records
        if record["partition"] in {"DIAGNOSTIC", "EVAL"}
    } & reference_fit_ids
    assert not leaked


def test_condition_recalibration_uses_fit_only(frozen_data):
    records, _ = frozen_data
    fit_realizations = {
        record["source_family_id"]
        for record in records
        if record["partition"] == "FIT" and record["record_role"] == "condition_realization"
    }
    assert fit_realizations
    assert not any(
        record["partition"] != "FIT" and record["record_role"] == "condition_realization" and record["source_family_id"] in fit_realizations
        for record in records
    )


def test_sdiag_uses_diag_only():
    a0_reference = {"c1": 0.8, "c2": 0.7}
    a0_final = {"c1": 0.6, "c2": 0.7}
    scores = runner.compute_s_diag(a0_reference, a0_final)
    assert scores["c1"] == pytest.approx(0.2)
    assert scores["c2"] == pytest.approx(0.0)


def test_geval_uses_eval_only():
    a_mu_sigma = {"c1": 0.9, "c2": 0.8}
    a0_final = {"c1": 0.6, "c2": 0.7}
    scores = runner.compute_g_eval(a_mu_sigma, a0_final)
    assert scores["c1"] == pytest.approx(0.3)
    assert scores["c2"] == pytest.approx(0.1)


def test_balanced_accuracy_imbalanced():
    y_true = ["a", "a", "a", "a", "b"]
    y_pred = ["a", "a", "a", "a", "b"]
    assert runner.balanced_accuracy(y_true, y_pred) == 1.0
    y_pred = ["b", "b", "b", "b", "b"]
    assert runner.balanced_accuracy(y_true, y_pred) == pytest.approx(0.5)


def test_calibration_condition_predictions_wiring():
    rng = np.random.default_rng(0)
    X = rng.normal(size=(20, 4))
    y = ["a"] * 10 + ["b"] * 10
    classifier, _ = runner.fit_classifier(X, y)
    reference_mean = np.zeros(4)
    reference_scale = np.ones(4)
    condition_mean = np.ones(4)
    condition_scale = np.ones(4) * 2.0
    outputs = runner.calibration_condition_predictions(
        X, reference_mean, reference_scale, condition_mean, condition_scale, classifier
    )
    assert set(outputs) == {"A0", "A_mu", "A_sigma", "A_mu_sigma"}
    assert all(len(values) == len(X) for values in outputs.values())


def test_average_rank_ties():
    ranks = runner.average_rank([1.0, 2.0, 2.0, 4.0])
    assert ranks == [1.0, 2.5, 2.5, 4.0]


def test_spearman_helper():
    assert runner.spearman_rho([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert runner.spearman_rho([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)


def test_exact_permutation_bruteforce_equivalence():
    x = [1.0, 2.0, 3.0, 4.0]
    y = [1.0, 3.0, 2.0, 4.0]
    result = runner.exact_one_sided_permutation_p(x, y)
    assert result["rho"] == pytest.approx(runner.spearman_rho(x, y))
    assert result["total"] == math.factorial(len(x))
    assert 0.0 <= result["p"] <= 1.0


def test_exact_one_sided_ge_rule():
    x = [1, 2, 3, 4]
    y = [4, 3, 2, 1]
    result = runner.exact_one_sided_permutation_p(x, y)
    assert result["count_ge"] >= 1
    assert result["p"] == pytest.approx(result["count_ge"] / result["total"])


def test_exact_denominator():
    result = runner.exact_one_sided_permutation_p([1, 2, 3, 4], [1, 2, 3, 4])
    assert result["total"] == math.factorial(4)


def test_primary_support_rule():
    assert runner.primary_support_rule(0.5, 0.04) is True
    assert runner.primary_support_rule(0.5, 0.06) is False
    assert runner.primary_support_rule(0.0, 0.01) is False
    assert runner.primary_support_rule(-0.5, 0.01) is False


def test_secondary_cannot_replace_primary():
    assert runner.SUPPORT_RULE == "rho>0_and_p<=0.05"
    assert runner.PERMUTATION_COUNT == 3628800
    assert runner.PRIMARY_CHECKPOINT_SPECS["block27_pre_final_rmsnorm"]["role"] == "primary_final"
    assert runner.SECONDARY_CHECKPOINT_NAMES == ("block27_post_final_rmsnorm",)


def test_formal_mode_fails_without_authorization():
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.run_formal(runner.ROOT, None)


def test_stale_runner_binding_rejection(monkeypatch):
    auth = _authorization(runner_sha="c" * 64)
    monkeypatch.setattr(runner, "_verify_model_hook_qualification_artifact", lambda root=None: {"sha256": "b" * 64, "artifact": {}})
    monkeypatch.setattr(runner, "_verify_model_hook_qualification_current", lambda artifact: None)
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._validate_formal_authorization(auth, runner.ROOT)
    assert "RUNNER" in str(exc.value)


def test_stale_qualification_rejection(monkeypatch):
    auth = _authorization(qualification_sha="b" * 64)
    monkeypatch.setattr(runner, "_verify_model_hook_qualification_artifact", lambda root=None: {"sha256": "c" * 64, "artifact": {}})
    monkeypatch.setattr(runner, "_verify_model_hook_qualification_current", lambda artifact: None)
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._validate_formal_authorization(auth, runner.ROOT)
    assert "QUALIFICATION_SHA" in str(exc.value)


_DEFAULT_QUALIFICATION_MODEL = {
    "model_name": runner.FORMAL_MODEL_NAME,
    "model_snapshot": runner.FORMAL_MODEL_SNAPSHOT,
}
_UNSET_MODEL = object()


def _qualification_artifact(
    status: str = "QUALIFICATION_PASSED",
    model: object = _UNSET_MODEL,
    top_level_model: bool = False,
) -> dict[str, object]:
    artifact: dict[str, object] = {
        "experiment": runner.EXPERIMENT,
        "status": status,
    }
    if model is _UNSET_MODEL:
        artifact["model"] = _DEFAULT_QUALIFICATION_MODEL
    elif model is not None:
        artifact["model"] = model
    if top_level_model:
        artifact["model_name"] = runner.FORMAL_MODEL_NAME
        artifact["model_snapshot"] = runner.FORMAL_MODEL_SNAPSHOT
    return artifact


def _write_qualification_artifact(root: Path, status: str = "QUALIFICATION_PASSED", **kwargs: object) -> Path:
    artifact = _qualification_artifact(status=status, **kwargs)
    path = root / runner.MODEL_HOOK_QUALIFICATION_PATH.relative_to(runner.ROOT)
    runner.write_json(path, artifact)
    return path


def test_qualification_status_contract_accepts_canonical(tmp_path):
    path = _write_qualification_artifact(tmp_path, "QUALIFICATION_PASSED")
    verified = runner._verify_model_hook_qualification_artifact(tmp_path)
    assert verified["path"] == "experiments/exp024/engineering/model_hook_qualification.json"
    assert verified["sha256"] == runner.sha256_file(path)
    assert verified["artifact"]["status"] == "QUALIFICATION_PASSED"
    assert verified["artifact"]["model"]["model_name"] == runner.FORMAL_MODEL_NAME
    assert verified["artifact"]["model"]["model_snapshot"] == runner.FORMAL_MODEL_SNAPSHOT


@pytest.mark.parametrize(
    "status",
    ["QUALIFICATION_FAILED", "OPERATIONAL_FAILURE", "QUALIFIED", "ARBITRARY_STATUS"],
)
def test_qualification_status_contract_rejects_noncanonical(tmp_path, status):
    _write_qualification_artifact(tmp_path, status)
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._verify_model_hook_qualification_artifact(tmp_path)
    assert "NOT_PASSED" in str(exc.value)


@pytest.mark.parametrize(
    "model",
    [
        {"model_name": "wrong/model", "model_snapshot": runner.FORMAL_MODEL_SNAPSHOT},
        {"model_name": runner.FORMAL_MODEL_NAME, "model_snapshot": "wrong-snapshot"},
        {"model_name": runner.FORMAL_MODEL_NAME},
        {"model_snapshot": runner.FORMAL_MODEL_SNAPSHOT},
        "not-an-object",
    ],
)
def test_qualification_model_identity_contract_rejects_bad_nested(tmp_path, model):
    _write_qualification_artifact(tmp_path, model=model)
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._verify_model_hook_qualification_artifact(tmp_path)
    message = str(exc.value)
    assert any(
        token in message
        for token in (
            "MODEL_MISMATCH",
            "SNAPSHOT_MISMATCH",
            "MODEL_METADATA_MISSING",
        )
    )


def test_qualification_model_identity_rejects_top_level_fallback(tmp_path):
    _write_qualification_artifact(tmp_path, model=None, top_level_model=True)
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._verify_model_hook_qualification_artifact(tmp_path)
    assert "MODEL_METADATA_MISSING" in str(exc.value)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("frozen_manifest_sha256", "c" * 64),
        ("frozen_dataset_sha256", "d" * 64),
        ("preregistration_sha256", "e" * 64),
        ("model_name", "other/model"),
        ("model_snapshot_identity", "other-revision"),
    ],
)
def test_authorization_identity_binding_drift_rejected(monkeypatch, field, value):
    auth = _authorization()
    auth[field] = value
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_artifact",
        lambda root=None: {"sha256": "b" * 64, "artifact": {}},
    )
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_current",
        lambda artifact: None,
    )
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._validate_formal_authorization(auth, runner.ROOT)
    assert "BINDING_MISMATCH" in str(exc.value)


def test_authorization_schema_minimal_and_fail_closed():
    schema = runner.read_json(runner.AUTHORIZATION_SCHEMA_PATH)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS
    assert set(schema["properties"]) == runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS


def test_synthetic_authorization_uses_only_permitted_fields(monkeypatch):
    auth = _authorization()
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_artifact",
        lambda root=None: {"sha256": "b" * 64, "artifact": {}},
    )
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_current",
        lambda artifact: None,
    )
    assert runner._validate_formal_authorization(auth, runner.ROOT) == auth


def test_formal_authorization_path_uses_canonical_nested_model(monkeypatch, tmp_path):
    artifact = {
        "experiment": runner.EXPERIMENT,
        "status": "QUALIFICATION_PASSED",
        "model": {
            "model_name": runner.FORMAL_MODEL_NAME,
            "model_snapshot": runner.FORMAL_MODEL_SNAPSHOT,
        },
        "runner_sha256": runner._runner_sha256(),
        "frozen_manifest_sha256": runner.FROZEN_MANIFEST_SHA256,
        "frozen_dataset_sha256": runner.FROZEN_DATASET_SHA256,
        "preregistration_sha256": runner.FINAL_PREREGISTRATION_SHA256,
    }
    path = tmp_path / runner.MODEL_HOOK_QUALIFICATION_PATH.relative_to(runner.ROOT)
    runner.write_json(path, artifact)
    qualification_sha = runner.sha256_file(path)
    auth = _authorization(qualification_sha=qualification_sha)
    monkeypatch.setattr(
        runner,
        "_repository_commit",
        lambda root=None: auth["authorized_repository_commit"],
    )
    assert runner._validate_formal_authorization(auth, tmp_path) == auth


@pytest.mark.parametrize("field", sorted(runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS))
def test_authorization_required_field_missing_rejected(field):
    auth = _authorization()
    del auth[field]
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._validate_formal_authorization(auth, runner.ROOT)
    assert "FIELDS_INVALID" in str(exc.value)


def test_authorization_extra_field_rejected():
    auth = _authorization()
    auth["mode"] = "formal-run"
    with pytest.raises(runner.ProtocolIntegrityError) as exc:
        runner._validate_formal_authorization(auth, runner.ROOT)
    assert "extra" in str(exc.value)


@pytest.mark.parametrize(
    "field",
    ["mode", "qualification_storage_commit", "model_revision", "allowed_result_path"],
)
def test_task_illustrated_fields_not_required_by_production(field):
    schema = runner.read_json(runner.AUTHORIZATION_SCHEMA_PATH)
    assert field not in runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS
    assert field not in schema["properties"]


def test_authorization_consumption_is_single_use(tmp_path, monkeypatch):
    auth = _authorization()
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: auth["authorized_repository_commit"])
    monkeypatch.setattr(runner, "_runner_sha256", lambda: auth["authorized_runner_sha256"])
    monkeypatch.setattr(runner, "_verify_model_hook_qualification_artifact", lambda root=None: {"sha256": "b" * 64, "artifact": {}})
    monkeypatch.setattr(runner, "_verify_model_hook_qualification_current", lambda artifact: None)
    first = runner._consume_formal_authorization(tmp_path, auth, auth_path, "attempt-1")
    assert Path(first["consumption_record_path"]).is_file()
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._consume_formal_authorization(tmp_path, auth, auth_path, "attempt-2")


def test_consumption_before_model_data_scientific_work(tmp_path, monkeypatch):
    auth = _authorization()
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(json.dumps(auth), encoding="utf-8")
    calls: list[str] = []

    monkeypatch.setattr(runner, "verify_frozen_authority", lambda root=None: calls.append("verify") or {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: calls.append("no_collision"))
    monkeypatch.setattr(runner, "_validate_formal_authorization", lambda authorization, root=None: calls.append("validate_auth") or authorization)
    monkeypatch.setattr(runner, "_tracked_tree_clean", lambda root=None: True)
    monkeypatch.setattr(runner, "_staging_empty", lambda root=None: True)
    monkeypatch.setattr(runner, "_consume_formal_authorization", lambda root, auth, path, attempt: calls.append("consume") or {"authorization_sha256": "a" * 64})
    monkeypatch.setattr(runner, "_execute_formal_after_consumption", lambda root, auth, consumption, attempt: calls.append("execute") or _valid_result())
    monkeypatch.setattr(runner, "finalize_formal_result", lambda result, root=None: calls.append("publish") or {"publication_status": "PUBLISHED"})

    runner.run_formal(tmp_path, auth_path)
    assert calls == ["verify", "no_collision", "validate_auth", "consume", "execute", "publish"]


def test_canonical_result_no_clobber(tmp_path, monkeypatch):
    canonical = tmp_path / "experiments" / "exp024" / "results" / "exp024_results.json"
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("{}", encoding="utf-8")
    result = _valid_result()
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.atomic_publish_validated_result(result, tmp_path)


def test_production_result_validator_actually_called(tmp_path, monkeypatch):
    called = []
    monkeypatch.setattr(runner, "validate_result_schema", lambda result, formal=False: called.append(result))
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "atomic_write_json", lambda path, result: {"path": str(path)})
    result = _valid_result()
    runner.finalize_formal_result(result, tmp_path)
    assert len(called) == 1


def test_incomplete_result_cannot_publish(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "atomic_write_json", lambda path, result: (_ for _ in ()).throw(AssertionError("write should not happen")))
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.atomic_publish_validated_result({}, tmp_path)


def test_static_preflight_performs_no_model_access(monkeypatch):
    monkeypatch.setattr(runner, "write_json", lambda path, data: None)
    result = runner.static_preflight()
    assert result["model_access"] is False
    assert result["scientific_outcome_access"] is False
    assert result["formal_result_present"] is False


def test_qualification_cli_reaches_real_runtime(monkeypatch, capsys):
    monkeypatch.setattr(
        runner,
        "run_model_hook_qualification",
        lambda root=None: {"status": "QUALIFICATION_PASSED"},
    )
    assert runner.main(["--model-hook-qualification"]) == 0
    assert "QUALIFICATION_PASSED" in capsys.readouterr().out


def test_qualification_production_call_graph(monkeypatch, tmp_path):
    calls: list[str] = []

    monkeypatch.setattr(
        runner,
        "verify_frozen_authority",
        lambda root=None: calls.append("verify_authority") or {},
    )
    monkeypatch.setattr(
        runner,
        "_load_qualification_runtime",
        lambda root=None: calls.append("load_runtime") or (None, None, None),
    )
    monkeypatch.setattr(
        runner,
        "build_model_hook_qualification_result",
        lambda root, authorities, tokenizer, model, device: calls.append("build_result")
        or {"status": "QUALIFICATION_PASSED"},
    )
    monkeypatch.setattr(
        runner,
        "publish_model_hook_qualification",
        lambda result, root=None: calls.append("publish") or result,
    )

    result = runner.run_model_hook_qualification(tmp_path)
    assert result["status"] == "QUALIFICATION_PASSED"
    assert calls == ["verify_authority", "load_runtime", "build_result", "publish"]


def test_qualification_does_not_load_formal_dataset(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("formal dataset loader must not be called")

    monkeypatch.setattr(runner, "load_frozen_dataset", forbidden)
    monkeypatch.setattr(
        runner,
        "verify_frozen_authority",
        lambda root=None: {"frozen": "authority"},
    )
    monkeypatch.setattr(
        runner,
        "_load_qualification_runtime",
        lambda root=None: (FakeTokenizer(), FakeModel(), torch.device("cpu")),
    )
    monkeypatch.setattr(runner, "_run_qualification_forward", _fake_forward)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "publish_model_hook_qualification",
        lambda result, root=None: result,
    )

    result = runner.run_model_hook_qualification(tmp_path)
    assert result["status"] == "QUALIFICATION_PASSED"


def test_qualification_formal_science_firewall(monkeypatch, tmp_path):
    def forbidden(name):
        def _forbidden(*args, **kwargs):
            raise AssertionError(f"{name} must not be reached by qualification")

        return _forbidden

    for name in (
        "fit_classifier",
        "fit_scaler",
        "compute_s_diag",
        "compute_g_eval",
        "balanced_accuracy",
        "spearman_rho",
        "exact_one_sided_permutation_p",
        "finalize_formal_result",
    ):
        monkeypatch.setattr(runner, name, forbidden(name))

    monkeypatch.setattr(
        runner,
        "verify_frozen_authority",
        lambda root=None: {"frozen": "authority"},
    )
    monkeypatch.setattr(
        runner,
        "_load_qualification_runtime",
        lambda root=None: (FakeTokenizer(), FakeModel(), torch.device("cpu")),
    )
    monkeypatch.setattr(runner, "_run_qualification_forward", _fake_forward)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "publish_model_hook_qualification",
        lambda result, root=None: result,
    )

    result = runner.run_model_hook_qualification(tmp_path)
    assert result["status"] == "QUALIFICATION_PASSED"


def test_tokenizer_metadata_contract():
    tokenizer = FakeTokenizer()
    input_ids = torch.tensor([[0, 2, 1]], dtype=torch.long)
    attention_mask = torch.ones((1, 3), dtype=torch.long)
    metadata = runner._tokenization_metadata(tokenizer, input_ids, attention_mask)
    assert metadata["token_count"] == 3
    assert metadata["attention_mask_shape"] == [1, 3]
    assert metadata["last_token_id"] == 1
    assert metadata["last_token_is_special"] is True
    assert metadata["last_valid_token_index"] == 2


def test_invalid_extraction_position_rejected():
    with pytest.raises(ValueError):
        runner.last_valid_token_indices(torch.zeros((1, 3), dtype=torch.long))


class SyntheticBlock(torch.nn.Module):
    def forward(self, value):
        return value * 2


class ForeignCreatingBlock(torch.nn.Module):
    def forward(self, value):
        self.foreign_handle = self.register_forward_hook(lambda module, args, output: None)
        return value * 2


def test_block_hook_capture_and_cleanup():
    module = SyntheticBlock()
    capture = runner.ForwardHookCapture()
    with runner.block_output_hook_capture(module, capture):
        output = module(torch.ones(2, 3))
    assert capture.count == 1
    assert torch.equal(capture.value, output)
    assert runner._module_hook_count(module) == 0


def test_block_hook_cleanup_on_failure():
    module = SyntheticBlock()
    capture = runner.ForwardHookCapture()
    with pytest.raises(RuntimeError):
        with runner.block_output_hook_capture(module, capture):
            raise RuntimeError("boom")
    assert runner._module_hook_count(module) == 0


def test_foreign_preexisting_hook_is_preserved():
    module = SyntheticBlock()
    foreign_handle = module.register_forward_hook(lambda module, args, output: None)
    capture = runner.ForwardHookCapture()
    with runner.block_output_hook_capture(module, capture):
        module(torch.ones(2, 3))
    assert foreign_handle.id in module._forward_hooks
    assert capture.cleanup_verified is True
    assert capture.exp024_hooks_remaining == 0
    assert capture.foreign_hooks_after == 1
    foreign_handle.remove()


def test_foreign_runtime_hook_does_not_fail_cleanup():
    module = ForeignCreatingBlock()
    capture = runner.ForwardHookCapture()
    with runner.block_output_hook_capture(module, capture):
        module(torch.ones(2, 3))
    assert module.foreign_handle.id in module._forward_hooks
    assert runner._module_hook_count(module) == 1
    assert capture.cleanup_verified is True
    assert capture.exp024_hooks_remaining == 0
    module.foreign_handle.remove()


def test_owned_hook_leak_is_detected():
    module = SyntheticBlock()
    capture = runner.ForwardHookCapture()
    handle = module.register_forward_hook(runner.make_block_output_hook(capture))
    remaining = runner._exp024_owned_hooks_remaining(module, [handle.id])
    assert remaining == 1
    assert (remaining == 0) is False
    handle.remove()


def test_block_hook_cleanup_on_validation_failure():
    module = SyntheticBlock()
    capture = runner.ForwardHookCapture()
    with pytest.raises(ValueError):
        with runner.block_output_hook_capture(module, capture):
            module(torch.ones(2, 3))
            raise ValueError("activation validation failure")
    assert runner._module_hook_count(module) == 0
    assert capture.cleanup_verified is True
    assert capture.exp024_hooks_remaining == 0


def test_repeated_extraction_does_not_accumulate_owned_hooks():
    module = SyntheticBlock()
    for _ in range(2):
        capture = runner.ForwardHookCapture()
        with runner.block_output_hook_capture(module, capture):
            module(torch.ones(2, 3))
        assert capture.cleanup_verified is True
        assert runner._module_hook_count(module) == 0


def test_extraction_materializes_float32_finite():
    hidden_states = tuple(
        torch.ones((1, 5, 4), dtype=torch.float16) * (index + 1)
        for index in range(29)
    )
    block27_pre = torch.ones((1, 5, 4), dtype=torch.float16) * 30
    attention_mask = torch.ones((1, 5), dtype=torch.long)
    checkpoint_tensors = runner.extract_checkpoint_tensors(hidden_states, block27_pre)
    selected = runner.extract_last_token_representations(checkpoint_tensors, attention_mask)
    for name in runner.QUALIFICATION_CHECKPOINT_NAMES:
        array = runner.to_float32_analysis_array(selected[name][0], expected_ndim=1)
        assert array.dtype == np.float32
        assert array.shape == (4,)
        assert np.isfinite(array).all()


def test_materialization_rejects_nonfinite():
    with pytest.raises(runner.TechnicalInvalidError):
        runner.to_float32_analysis_array(
            torch.tensor([1.0, float("nan")], dtype=torch.float32), expected_ndim=1
        )


def test_repeatability_checker_pass_and_fail():
    left = {
        name: np.full((4,), index + 1, dtype=np.float32)
        for index, name in enumerate(runner.QUALIFICATION_CHECKPOINT_NAMES)
    }
    right = {name: value.copy() for name, value in left.items()}
    matched, details = runner._representations_match(left, right)
    assert matched is True
    assert all(details[name]["match"] for name in runner.QUALIFICATION_CHECKPOINT_NAMES)

    right["block16_pre_final_rmsnorm"] = np.full((4,), 99.0, dtype=np.float32)
    matched, details = runner._representations_match(left, right)
    assert matched is False
    assert details["block16_pre_final_rmsnorm"]["match"] is False


def test_qualification_validator_called_before_publication(tmp_path, monkeypatch):
    calls: list[str] = []

    def validator(result, root=None):
        calls.append("validator")
        return None

    def atomic(path, result):
        calls.append("atomic")
        return {"path": str(path)}

    monkeypatch.setattr(runner, "validate_model_hook_qualification", validator)
    monkeypatch.setattr(runner, "atomic_write_json", atomic)
    runner.publish_model_hook_qualification({}, tmp_path)
    assert calls == ["validator", "atomic"]


def test_qualification_validator_failure_prevents_publication(tmp_path, monkeypatch):
    def validator(result, root=None):
        raise runner.ProtocolIntegrityError("QUALIFICATION_INVALID")

    def atomic(path, result):
        raise AssertionError("publication must not happen")

    monkeypatch.setattr(runner, "validate_model_hook_qualification", validator)
    monkeypatch.setattr(runner, "atomic_write_json", atomic)
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.publish_model_hook_qualification({}, tmp_path)


def test_no_mode_fails_closed():
    with pytest.raises(SystemExit):
        runner.main([])


def _synthetic_formal_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for condition in runner.CONDITION_ORDER:
        for partition in runner.PARTITIONS:
            for semantic_class in runner.CLASS_ORDER:
                for family_index in range(runner.ALLOCATION[partition]):
                    family_id = (
                        f"syn_{condition}_{partition}_{semantic_class}_{family_index:04d}"
                    )
                    for record_role in runner.RECORD_ROLES:
                        records.append(
                            {
                                "record_id": f"{family_id}_{record_role}",
                                "source_family_id": family_id,
                                "semantic_class": semantic_class,
                                "condition_id": condition,
                                "partition": partition,
                                "record_role": record_role,
                                "text": (
                                    f"neutral synthetic {condition} {partition} "
                                    f"{semantic_class} {record_role} {family_index}"
                                ),
                                "base_content_identity": family_id,
                                "transformation_rule_id": condition,
                                "independence_group": family_id,
                                "review_status": "PASS",
                                "provenance": {},
                            }
                        )
    return records


def _synthetic_formal_forward(tokenizer, model, device, text):
    class_index = next(
        index
        for index, semantic_class in enumerate(runner.CLASS_ORDER)
        if semantic_class in text
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    noise_scale = 0.02
    arrays = {}
    for checkpoint_index, checkpoint in enumerate(runner.QUALIFICATION_CHECKPOINT_NAMES):
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big") + checkpoint_index)
        vector = np.zeros((4,), dtype=np.float32)
        vector[class_index] = 1.0
        vector += rng.normal(0.0, noise_scale, size=(4,)).astype(np.float32)
        arrays[checkpoint] = vector
    return {
        "input_ids": torch.tensor([[0, 2, 1]], dtype=torch.long, device=device),
        "attention_mask": torch.ones((1, 3), dtype=torch.long, device=device),
        "representations": arrays,
        "hook_firing_count": 1,
        "hook_cleanup_verified": True,
        "exp024_hooks_remaining": 0,
        "foreign_hooks_remaining": 0,
    }


def test_formal_runtime_synthetic_production_execution(tmp_path, monkeypatch):
    records = _synthetic_formal_records()
    monkeypatch.setattr(runner, "verify_frozen_authority", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "exact_one_sided_permutation_p",
        lambda x, y, alternative="greater": {
            "rho": 0.5,
            "p": 0.04,
            "count_ge": 1,
            "total": runner.PERMUTATION_COUNT,
        },
    )
    runtime = (FakeTokenizer(), FakeModel(), torch.device("cpu"))
    result = runner._execute_formal_analysis(
        tmp_path,
        {"authorization_id": "synthetic-auth"},
        {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
        },
        "synthetic-attempt",
        condition_order=runner.CONDITION_ORDER,
        records_loader=lambda root=None: (records, []),
        runtime_loader=lambda root=None: runtime,
        record_extractor=_synthetic_formal_forward,
    )
    runner.validate_result_schema(result, formal=True)
    assert result["result_status"] == "FORMAL_RESULT"
    assert result["scientific_status"] == "FORMAL_ANALYSIS_COMPLETED"
    assert result["primary"]["permutation_count"] == runner.PERMUTATION_COUNT
    assert result["primary"]["supported"] is True
    assert len(result["condition_level"]["s_diag"]) == 10
    assert len(result["condition_level"]["g_eval"]) == 10
    assert result["hidden_states_included"] is False
    assert result["prompt_text_included"] is False


def test_formal_runtime_call_graph_reaches_analysis_and_publication(tmp_path, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(
        runner,
        "_pre_consumption_static_checks",
        lambda *args, **kwargs: calls.append("pre_checks") or None,
    )
    monkeypatch.setattr(
        runner,
        "_consume_formal_authorization",
        lambda *args, **kwargs: calls.append("consume")
        or {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
        },
    )
    monkeypatch.setattr(
        runner,
        "_execute_formal_analysis",
        lambda *args, **kwargs: calls.append("execute") or _valid_result(),
    )
    monkeypatch.setattr(
        runner,
        "finalize_formal_result",
        lambda result, root=None: calls.append("finalize")
        or {"path": "x", "sha256": "c" * 64},
    )
    auth_path = tmp_path / "synthetic_auth.json"
    runner.write_json(auth_path, _authorization())
    runner.run_formal(tmp_path, auth_path)
    assert calls == ["pre_checks", "consume", "execute", "finalize"]


def test_formal_runtime_failure_does_not_publish_canonical_result(tmp_path, monkeypatch):
    monkeypatch.setattr(
        runner,
        "_pre_consumption_static_checks",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        runner,
        "_consume_formal_authorization",
        lambda *args, **kwargs: {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
        },
    )

    def fail_analysis(*args, **kwargs):
        raise runner.ProtocolIntegrityError("FORMAL_ANALYSIS_TEST_FAILURE")

    monkeypatch.setattr(runner, "_execute_formal_analysis", fail_analysis)
    auth_path = tmp_path / "synthetic_auth.json"
    runner.write_json(auth_path, _authorization())
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.run_formal(tmp_path, auth_path)
    canonical = tmp_path / runner.CANONICAL_RESULT_PATH.relative_to(runner.ROOT)
    assert not canonical.exists()


def test_formal_result_atomic_publication_uses_tmp_path(tmp_path, monkeypatch):
    records = _synthetic_formal_records()
    monkeypatch.setattr(runner, "verify_frozen_authority", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "exact_one_sided_permutation_p",
        lambda x, y, alternative="greater": {
            "rho": 0.5,
            "p": 0.04,
            "count_ge": 1,
            "total": runner.PERMUTATION_COUNT,
        },
    )
    runtime = (FakeTokenizer(), FakeModel(), torch.device("cpu"))
    result = runner._execute_formal_analysis(
        tmp_path,
        {"authorization_id": "synthetic-auth"},
        {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
        },
        "synthetic-attempt",
        condition_order=runner.CONDITION_ORDER,
        records_loader=lambda root=None: (records, []),
        runtime_loader=lambda root=None: runtime,
        record_extractor=_synthetic_formal_forward,
    )
    published = runner.atomic_publish_validated_result(result, tmp_path)
    assert published["sha256"]
    assert (tmp_path / runner.CANONICAL_RESULT_PATH.relative_to(runner.ROOT)).is_file()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda rows: _mutate_partition_family(rows, "FIT", "DIAGNOSTIC"),
        lambda rows: _mutate_partition_family(rows, "FIT", "EVAL"),
        lambda rows: _mutate_partition_family(rows, "DIAGNOSTIC", "EVAL"),
        lambda rows: _mutate_field(rows, "condition_id", "unexpected_condition"),
        lambda rows: _mutate_field(rows, "semantic_class", "invalid_class"),
        lambda rows: _duplicate_record_id(rows),
    ],
)
def test_formal_partition_integrity_fails_closed(mutator):
    records = _synthetic_formal_records()
    mutator(records)
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._validate_formal_partition_integrity(
            records, runner.CONDITION_ORDER, strict_counts=True
        )


def test_formal_partition_integrity_rejects_missing_semantic_class():
    records = [
        row
        for row in _synthetic_formal_records()
        if row["semantic_class"] != "definition"
    ]
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._validate_formal_partition_integrity(
            records, runner.CONDITION_ORDER, strict_counts=True
        )


def test_formal_partition_integrity_rejects_wrong_condition_count():
    records = _synthetic_formal_records()
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._validate_formal_partition_integrity(
            records, runner.CONDITION_ORDER[:-1], strict_counts=True
        )


def _mutate_partition_family(records, source_partition, target_partition):
    source = next(
        row
        for row in records
        if row["partition"] == source_partition
        and row["record_role"] == "reference_form"
    )
    target_rows = [
        row
        for row in records
        if row["partition"] == target_partition
        and row["record_role"] == "reference_form"
    ]
    for row in target_rows[:2]:
        row["source_family_id"] = source["source_family_id"]


def _mutate_field(records, field, value):
    records[0][field] = value


def _duplicate_record_id(records):
    records[1]["record_id"] = records[0]["record_id"]
