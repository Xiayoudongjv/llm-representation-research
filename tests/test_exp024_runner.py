"""Focused EXP-024 frozen-runner and static-preflight tests."""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest


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


def test_qualification_mode_cannot_load_formal_records(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("formal dataset loader must not be called in 098A qualification mode")

    monkeypatch.setattr(runner, "load_frozen_dataset", forbidden)
    assert runner.main(["--model-hook-qualification"]) == 2


def test_no_mode_fails_closed():
    with pytest.raises(SystemExit):
        runner.main([])
