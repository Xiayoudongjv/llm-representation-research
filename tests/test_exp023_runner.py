"""Focused EXP-023 frozen-runner and synthetic-preflight tests."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from sklearn.preprocessing import StandardScaler


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "exp023"
    / "run_exp023.py"
)
SPEC = importlib.util.spec_from_file_location("exp023_runner", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
import sys as _sys
_sys.modules["exp023_runner"] = runner
SPEC.loader.exec_module(runner)


def _synthetic_split(split_id: str = "A", seed: int = 1) -> runner.SplitDataset:
    return runner.make_synthetic_split(split_id, seed)


def _failure_auth() -> dict[str, object]:
    return {
        "authorization_id": "auth-failure",
        "authorized_repository_commit": "a" * 40,
        "authorized_runner_sha256": "b" * 64,
        "frozen_preregistration_sha256": runner.FROZEN_PREREGISTRATION_SHA256,
        "frozen_dataset_sha256": runner.DATASET_SHA256,
        "model_name": runner.FORMAL_MODEL_NAME,
        "model_snapshot_identity": runner.FORMAL_MODEL_SNAPSHOT,
        "model_hook_qualification_sha256": "c" * 64,
        "canonical_result_path": "experiments/exp023/results/exp023_results.json",
    }


def _write_consumption_record(tmp_path: Path, content: str = "consumption") -> Path:
    path = tmp_path / "consumption.json"
    path.write_text(content, encoding="utf-8")
    return path


def _make_records(*, valid: bool = True) -> list[dict[str, object]]:
    records = []
    for cls in runner.CLASS_UNIVERSE:
        for family_index in range(1, 9):
            family_id = f"{cls}_{family_index:02d}"
            for raw_variant, canonical_variant in (
                ("original_style", "original"),
                ("paraphrase", "paraphrase"),
            ):
                record: dict[str, object] = {
                    "record_id": f"{family_id}_{raw_variant}",
                    "source_family_id": family_id,
                    "SOURCE_SEMANTIC_CLASS": cls,
                    "variant_type": raw_variant,
                }
                if valid:
                    record["text"] = f"synthetic {cls} {raw_variant} {family_index}"
                records.append(record)
    return records


def test_frozen_preregistration_sha_matches_constant():
    actual = runner._sha256(
        runner.ROOT / runner.PREREGISTRATION_PATH.relative_to(runner.ROOT)
    )
    assert actual == runner.FROZEN_PREREGISTRATION_SHA256


def test_frozen_dataset_sha_matches_constant():
    actual = runner._sha256(
        runner.ROOT / runner.DATASET_PATH.relative_to(runner.ROOT)
    )
    assert actual == runner.DATASET_SHA256


def test_frozen_authority_verifies_actual_repo():
    result = runner.verify_frozen_authority()
    assert result["preregistration"]["status"] == "FROZEN"
    assert result["dataset"]["status"] == "FROZEN"


def test_raw_variant_strictness_rejects_canonical_original():
    records = _make_records()
    records[0]["variant_type"] = "original"
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.validate_dataset_records(records)


def test_raw_and_canonical_variant_are_separated():
    metas = runner.validate_dataset_records(_make_records())
    assert {meta.raw_variant_type for meta in metas} == {"original_style", "paraphrase"}
    assert {meta.canonical_variant for meta in metas} == {"original", "paraphrase"}
    assert sum(meta.raw_variant_type == "original_style" for meta in metas) == 32
    assert sum(meta.canonical_variant == "paraphrase" for meta in metas) == 32


def test_frozen_dataset_loader_counts():
    records, metas = runner.load_frozen_dataset()
    assert len(records) == 64
    assert len(metas) == 64
    assert len({meta.source_family_id for meta in metas}) == 32


def test_checkpoint_registry_matches_protocol():
    assert runner.CHECKPOINT_NAMES == (
        "block16_pre_final_rmsnorm",
        "block17_pre_final_rmsnorm",
        "block18_pre_final_rmsnorm",
        "block19_pre_final_rmsnorm",
        "block20_pre_final_rmsnorm",
        "block21_pre_final_rmsnorm",
        "block22_pre_final_rmsnorm",
        "block23_pre_final_rmsnorm",
        "block24_pre_final_rmsnorm",
        "block25_pre_final_rmsnorm",
        "block26_pre_final_rmsnorm",
        "block27_pre_final_rmsnorm",
        "block27_post_final_rmsnorm",
    )
    assert runner.READOUT_CONDITIONS == ("A0", "A_mu", "A_sigma", "A_mu_sigma")


def test_synthetic_split_construction_exact():
    dataset = _synthetic_split("A", 1)
    for cls in runner.CLASS_UNIVERSE:
        assert len(dataset.fit_records[cls]) == 8
        assert len(dataset.eval_records[cls]) == 8
    assert set(dataset.fit_records) == set(runner.CLASS_UNIVERSE)
    assert set(dataset.eval_records) == set(runner.CLASS_UNIVERSE)
    assert set(dataset.source_families.values())


def test_synthetic_split_preserves_source_family_metadata():
    dataset = _synthetic_split("B", 2)
    for record_id, family_id in dataset.source_families.items():
        assert record_id.startswith(family_id)
    assert len({family for family in dataset.source_families.values()}) == 32


def test_fit_eval_separation_and_class_balance():
    dataset = _synthetic_split("A", 3)
    fit_ids = [rid for ids in dataset.fit_records.values() for rid in ids]
    eval_ids = [rid for ids in dataset.eval_records.values() for rid in ids]
    assert len(fit_ids) == 32
    assert len(eval_ids) == 32
    assert set(fit_ids).isdisjoint(eval_ids)


def test_no_eval_scaler_leakage():
    dataset = _synthetic_split("A", 1)
    for record_id in dataset.fit_records:
        for rid in dataset.fit_records[record_id]:
            dataset.representations[rid][runner.PRIMARY_REFERENCE_CHECKPOINT] = (
                dataset.representations[rid][runner.PRIMARY_REFERENCE_CHECKPOINT] + 10.0
            )
    X_fit, _, _ = runner._stack_records(
        dataset, dataset.fit_records, runner.PRIMARY_REFERENCE_CHECKPOINT
    )
    X_eval, _, _ = runner._stack_records(
        dataset, dataset.eval_records, runner.PRIMARY_REFERENCE_CHECKPOINT
    )
    scaler = runner.fit_scaler(X_fit)
    assert np.allclose(scaler.mean_, X_fit.mean(axis=0))
    assert not np.allclose(scaler.mean_, X_eval.mean(axis=0))


def test_a0_formula_matches_reference_scaler():
    dataset = _synthetic_split("A", 2)
    X, _, _ = runner._stack_records(
        dataset, dataset.fit_records, runner.PRIMARY_REFERENCE_CHECKPOINT
    )
    scaler = runner.fit_scaler(X)
    other, _, _ = runner._stack_records(
        dataset, dataset.eval_records, runner.PRIMARY_REFERENCE_CHECKPOINT
    )
    np.testing.assert_allclose(
        runner._transform_with_stats(other, scaler.mean_, scaler.scale_),
        scaler.transform(other),
        rtol=1e-5,
        atol=1e-5,
    )


def test_a_mu_formula_uses_layer_mean_and_reference_scale():
    rng = np.random.default_rng(4)
    X = rng.normal(size=(32, 5)).astype(np.float32)
    mu_l = X.mean(axis=0)
    sigma_ref = np.array([1.5, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    expected = (X - mu_l) / sigma_ref
    np.testing.assert_allclose(
        runner._transform_with_stats(X, mu_l, sigma_ref), expected
    )


def test_a_sigma_formula_uses_reference_mean_and_layer_scale():
    rng = np.random.default_rng(5)
    X = rng.normal(size=(32, 5)).astype(np.float32)
    mu_ref = np.array([0.1, -0.2, 0.3, -0.4, 0.5], dtype=np.float32)
    sigma_l = X.std(axis=0).astype(np.float32)
    expected = (X - mu_ref) / sigma_l
    np.testing.assert_allclose(
        runner._transform_with_stats(X, mu_ref, sigma_l), expected
    )


def test_zero_variance_semantics_are_deterministic_unit_scale():
    X = np.zeros((8, 4), dtype=np.float32)
    scaler = runner.fit_scaler(X)
    assert np.allclose(scaler.mean_, 0)
    assert np.allclose(scaler.scale_, 1)
    transformed = runner._transform_with_stats(X, scaler.mean_, scaler.scale_)
    assert np.isfinite(transformed).all()


def test_a_mu_sigma_algebraic_equivalence():
    rng = np.random.default_rng(6)
    X = rng.normal(size=(32, 5)).astype(np.float32)
    mu_l = X.mean(axis=0)
    sigma_l = X.std(axis=0)
    mu_l[2] = 0.0
    sigma_l[2] = 1.0
    transformed = (X - mu_l) / sigma_l
    mu_ref = np.array([0.1, 0.2, 0.3, 0.4, 0.5], dtype=np.float32)
    sigma_ref = np.array([1.2, 1.4, 1.6, 1.8, 2.0], dtype=np.float32)
    transported = mu_ref + sigma_ref * transformed
    back_transformed = (transported - mu_ref) / sigma_ref
    np.testing.assert_allclose(back_transformed, transformed, atol=1e-6)


@pytest.mark.parametrize(
    ("favorable", "unfavorable", "expected"),
    [
        (0, 0, 1.0),
        (1, 0, 0.5),
        (4, 0, 0.0625),
        (5, 0, 0.03125),
        (6, 0, 0.015625),
        (1, 1, 0.75),
    ],
)
def test_exact_binomial_edge_cases(favorable, unfavorable, expected):
    assert runner.exact_binomial_tail(favorable, unfavorable) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("supported_a", "supported_b", "effect_a", "effect_b", "expected"),
    [
        (True, True, 0.1, 0.2, "FULL_REPLICATION"),
        (True, False, 0.1, 0.05, "PARTIAL_REPLICATION"),
        (False, True, 0.05, 0.2, "PARTIAL_REPLICATION"),
        (True, False, 0.1, -0.05, "SPLIT_HETEROGENEOUS"),
        (False, False, 0.1, -0.1, "SPLIT_HETEROGENEOUS"),
        (False, False, 0.1, 0.2, "NO_REPLICATION"),
        (True, False, 0.1, 0.0, "NO_REPLICATION"),
    ],
)
def test_cross_split_classification(supported_a, supported_b, effect_a, effect_b, expected):
    assert runner.cross_split_category(supported_a, supported_b, effect_a, effect_b) == expected


def test_d_fixed_is_contextual_not_gate():
    analysis = runner.run_split_analysis(_synthetic_split("A", 1))
    primary = analysis["summary"]["primary"]
    assert primary["D_fixed"]["serial_gate"] == "CONTEXTUAL_NOT_GATE"
    assert "G_cal" in primary


def test_secondary_estimands_present_and_descriptive_only():
    analysis = runner.run_split_analysis(_synthetic_split("B", 2))
    secondary = analysis["summary"]["secondary"]
    assert set(secondary) == {
        "G_mu",
        "G_sigma",
        "G_joint_over_mu",
        "G_joint_over_sigma",
    }
    assert "significance" not in secondary


def test_bootstrap_determinism():
    correct_a = {cls: [True, False, True, False, True, False, True, False] for cls in runner.CLASS_UNIVERSE}
    correct_b = {cls: [False, True, True, False, True, False, True, False] for cls in runner.CLASS_UNIVERSE}
    first = runner.bootstrap_contrast(correct_a, correct_b)
    second = runner.bootstrap_contrast(correct_a, correct_b)
    assert first == second
    assert first["seed"] == runner.BOOTSTRAP_SEED


def test_bootstrap_rejects_wrong_class_count():
    correct_a = {cls: [True] * 7 for cls in runner.CLASS_UNIVERSE}
    correct_b = {cls: [True] * 7 for cls in runner.CLASS_UNIVERSE}
    with pytest.raises(ValueError):
        runner.bootstrap_contrast(correct_a, correct_b)


def test_bootstrap_intervals_cover_all_required_contrasts():
    dataset = _synthetic_split("A", 3)
    analysis = runner.run_split_analysis(dataset)
    intervals = analysis["summary"]["bootstrap"]
    assert set(intervals) == {
        "G_cal",
        "D_fixed",
        "G_mu",
        "G_sigma",
        "G_joint_over_mu",
        "G_joint_over_sigma",
    }


def test_full_depth_trajectories_descriptive_only():
    analysis = runner.run_split_analysis(_synthetic_split("B", 4))
    trajectories = analysis["summary"]["trajectories"]
    assert set(trajectories) == set(runner.READOUT_CONDITIONS)
    for values in trajectories.values():
        assert set(values) == set(runner.CHECKPOINT_NAMES)
    assert "best_layer" not in analysis["summary"]
    assert "max_over_layer" not in analysis["summary"]


def test_post_final_delta_descriptive_only():
    analysis = runner.run_split_analysis(_synthetic_split("A", 5))
    deltas = analysis["summary"]["post_final_delta"]
    assert set(deltas) == set(runner.READOUT_CONDITIONS)
    assert "significance" not in deltas


def test_static_preflight_passes_and_writes_expected_file():
    result = runner.static_preflight()
    assert result["status"] == "EXP023_STATIC_PREFLIGHT_PASS"
    preflight = runner._read_json(runner.PREFLIGHT_PATH)
    assert preflight["static_preflight"]["status"] == "EXP023_STATIC_PREFLIGHT_PASS"
    assert preflight["experiment"] == "EXP-023"


def test_synthetic_preflight_passes_and_is_not_scientific():
    result = runner.synthetic_preflight()
    assert result["status"] == "EXP023_SYNTHETIC_PREFLIGHT_PASS"
    assert result["scientific_result_created"] is False
    assert result["model_loaded"] is False
    assert result["tokenizer_loaded"] is False
    preflight = runner._read_json(runner.PREFLIGHT_PATH)
    assert preflight["synthetic_preflight"]["status"] == "EXP023_SYNTHETIC_PREFLIGHT_PASS"


def test_prediction_row_redacts_text():
    dataset = _synthetic_split("A", 1)
    analysis = runner.run_split_analysis(dataset)
    rows = analysis["evaluation_rows"]
    assert rows
    assert "text" not in rows[0]
    assert "prompt" not in rows[0]


def test_result_validator_requires_required_keys():
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.validate_result_schema({})


def test_result_validator_accepts_synthetic_result_via_preflight():
    runner.synthetic_preflight()
    # The preflight internally validates a synthetic result; reaching here is success.
    assert True


def test_atomic_publication_no_overwrite(tmp_path):
    result = {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "experiment": runner.EXPERIMENT,
        "classification": "TEST",
        "preregistration": {
            "path": str(runner.PREREGISTRATION_PATH.relative_to(runner.ROOT)),
            "sha256": runner.FROZEN_PREREGISTRATION_SHA256,
            "status": "FROZEN",
        },
        "runner": {"path": "runner.py", "sha256": "a" * 64},
        "execution_mode": "synthetic-preflight",
        "model": {"model_id": runner.FORMAL_MODEL_NAME, "snapshot": runner.FORMAL_MODEL_SNAPSHOT},
        "dataset": {"path": str(runner.DATASET_PATH.relative_to(runner.ROOT)), "sha256": runner.DATASET_SHA256},
        "classes": list(runner.CLASS_UNIVERSE),
        "checkpoints": runner.CHECKPOINT_NAMES,
        "readout_definitions": {},
        "splits": {},
        "cross_split_synthesis": {},
        "technical_validity": {"status": "VALID"},
        "attempt_status": "TEST",
        "result_status": "TEST",
        "scientific_status": "NOT_RUN",
        "warnings": [],
        "prompt_text_included": False,
        "hidden_states_included": False,
    }
    canonical = tmp_path / "result.json"
    first = runner.atomic_write_json(canonical, result)
    assert first["publication_status"] == "PUBLISHED"
    assert canonical.exists()
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.atomic_write_json(canonical, result)


def test_verify_no_result_collision(tmp_path, monkeypatch):
    relative = runner.CANONICAL_RESULT_PATH.relative_to(runner.ROOT)
    canonical = tmp_path / relative
    canonical.parent.mkdir(parents=True, exist_ok=True)
    canonical.write_text("{}", encoding="utf-8")
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.verify_no_result_collision(tmp_path)


def test_exclusive_consumption_rejects_second_use(tmp_path):
    auth_path = tmp_path / "authorization.json"
    auth_path.write_text(
        json.dumps({"authorization_id": "auth-1"}), encoding="utf-8"
    )
    auth = {
        "authorization_id": "auth-1",
        "authorized_repository_commit": "a" * 40,
        "authorized_runner_sha256": "b" * 64,
        "frozen_preregistration_sha256": runner.FROZEN_PREREGISTRATION_SHA256,
        "frozen_dataset_sha256": runner.DATASET_SHA256,
        "model_name": runner.FORMAL_MODEL_NAME,
        "model_snapshot_identity": runner.FORMAL_MODEL_SNAPSHOT,
        "model_hook_qualification_sha256": "c" * 64,
        "canonical_result_path": "experiments/exp023/results/exp023_results.json",
    }
    first = runner._consume_formal_authorization(
        tmp_path, auth, auth_path, "attempt-1"
    )
    assert first["run_attempt_id"] == "attempt-1"
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._consume_formal_authorization(
            tmp_path, auth, auth_path, "attempt-2"
        )


def test_technical_failure_evidence_exclusive(tmp_path):
    auth = _failure_auth()
    consumption_path = _write_consumption_record(tmp_path)
    consumption = {
        "authorization_sha256": "a" * 64,
        "consumption_record_path": str(consumption_path),
        "consumption_record_sha256": "wrong-original-sha",
    }
    runner._preserve_technical_failure_after_consumption(
        tmp_path, auth, consumption, "attempt-fail", "MODEL_LOAD", RuntimeError("boom")
    )
    path = runner._technical_failure_evidence_path_for(tmp_path, "attempt-fail")
    assert path.exists()
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._preserve_technical_failure_after_consumption(
            tmp_path,
            auth,
            consumption,
            "attempt-fail",
            "MODEL_LOAD",
            RuntimeError("boom"),
        )


def test_technical_failure_evidence_binds_all_direct_fields(tmp_path):
    auth = _failure_auth()
    consumption_path = _write_consumption_record(tmp_path, "consumption-bytes")
    consumption = {
        "authorization_sha256": "a" * 64,
        "consumption_record_path": str(consumption_path),
        "consumption_record_sha256": "wrong-original-sha",
    }
    runner._preserve_technical_failure_after_consumption(
        tmp_path,
        auth,
        consumption,
        "attempt-direct",
        "MODEL_LOAD",
        RuntimeError("boom"),
    )
    path = runner._technical_failure_evidence_path_for(tmp_path, "attempt-direct")
    data = runner._read_json(path)
    expected_consumption_sha = runner._sha256(consumption_path)
    assert data["authorization_id"] == "auth-failure"
    assert data["authorization_sha256"] == "a" * 64
    assert data["consumption_record_path"] == str(consumption_path)
    assert data["consumption_record_sha256"] == expected_consumption_sha
    assert data["repository_commit"] == "a" * 40
    assert data["runner_sha256"] == "b" * 64
    assert data["frozen_preregistration_sha256"] == runner.FROZEN_PREREGISTRATION_SHA256
    assert data["frozen_dataset_sha256"] == runner.DATASET_SHA256
    assert data["model_hook_qualification_sha256"] == "c" * 64
    assert data["model_name"] == runner.FORMAL_MODEL_NAME
    assert data["model_snapshot_identity"] == runner.FORMAL_MODEL_SNAPSHOT
    assert data["failure_stage"] == "MODEL_LOAD"
    assert data["failure_class"] == "RUNTIME"
    assert data["sanitized_exception_type"] == "RuntimeError"
    assert data["sanitized_exception_message"] == "post_consumption_failure at MODEL_LOAD"
    assert data["prompt_text_included"] is False
    assert data["hidden_states_included"] is False


def test_technical_failure_evidence_consumption_sha_tracks_bytes(tmp_path):
    auth = _failure_auth()
    first_path = tmp_path / "first" / "consumption.json"
    first_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("first-consumption", encoding="utf-8")
    second_path = tmp_path / "second" / "consumption.json"
    second_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.write_text("second-consumption", encoding="utf-8")

    first_consumption = {
        "authorization_sha256": "a" * 64,
        "consumption_record_path": str(first_path),
    }
    second_consumption = {
        "authorization_sha256": "a" * 64,
        "consumption_record_path": str(second_path),
    }
    runner._preserve_technical_failure_after_consumption(
        tmp_path, auth, first_consumption, "attempt-a", "MODEL_LOAD", RuntimeError("a")
    )
    runner._preserve_technical_failure_after_consumption(
        tmp_path, auth, second_consumption, "attempt-b", "MODEL_LOAD", RuntimeError("b")
    )
    first_data = runner._read_json(
        runner._technical_failure_evidence_path_for(tmp_path, "attempt-a")
    )
    second_data = runner._read_json(
        runner._technical_failure_evidence_path_for(tmp_path, "attempt-b")
    )
    assert first_data["consumption_record_sha256"] == runner._sha256(first_path)
    assert second_data["consumption_record_sha256"] == runner._sha256(second_path)
    assert first_data["consumption_record_sha256"] != second_data["consumption_record_sha256"]


def test_failure_stage_propagation_model_load(tmp_path, monkeypatch):
    context = runner.FormalFailureContext()
    monkeypatch.setattr(
        runner,
        "_verify_formal_dataset_identity",
        lambda root: {"path": "x", "sha256": runner.DATASET_SHA256},
    )
    monkeypatch.setattr(runner, "_load_formal_records", lambda root: ([], []))

    def fail_runtime(root, failure_context=None):
        if failure_context is not None:
            failure_context.stage = "MODEL_LOAD"
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "_load_formal_runtime", fail_runtime)
    with pytest.raises(RuntimeError):
        runner._execute_formal_after_consumption(
            tmp_path, {}, {}, "attempt-model", context
        )
    assert context.stage == "MODEL_LOAD"


def test_failure_stage_propagation_representation_extraction(tmp_path, monkeypatch):
    context = runner.FormalFailureContext()
    monkeypatch.setattr(
        runner,
        "_verify_formal_dataset_identity",
        lambda root: {"path": "x", "sha256": runner.DATASET_SHA256},
    )
    monkeypatch.setattr(runner, "_load_formal_records", lambda root: ([], []))
    monkeypatch.setattr(runner, "_load_formal_runtime", lambda root, failure_context=None: ("tokenizer", "model", "cuda:0"))

    def fail_extract(root, tokenizer, model, device, records):
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "_extract_formal_representations", fail_extract)
    with pytest.raises(RuntimeError):
        runner._execute_formal_after_consumption(
            tmp_path, {}, {}, "attempt-extract", context
        )
    assert context.stage == "REPRESENTATION_EXTRACTION"


def test_failure_stage_propagation_result_validation(tmp_path, monkeypatch):
    context = runner.FormalFailureContext()

    def fail_validation(result, formal=False):
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "validate_result_schema", fail_validation)
    with pytest.raises(RuntimeError):
        runner.finalize_formal_result({}, tmp_path, context)
    assert context.stage == "RESULT_VALIDATION"


def test_consumption_before_model_load_ordering(tmp_path, monkeypatch):
    auth_path = tmp_path / "auth.json"
    auth_path.write_text("{}", encoding="utf-8")
    calls = []
    monkeypatch.setattr(runner, "_pre_consumption_static_checks", lambda root, auth, path: calls.append("pre"))
    monkeypatch.setattr(runner, "_consume_formal_authorization", lambda root, auth, path, attempt: calls.append("consume") or {
        "authorization_sha256": "a" * 64,
        "consumption_record_path": str(tmp_path / "consumption.json"),
        "consumption_record_sha256": "b" * 64,
        "run_attempt_id": attempt,
    })
    monkeypatch.setattr(runner, "_execute_formal_after_consumption", lambda root, auth, consumption, attempt, failure_context: calls.append("execute") or {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "experiment": runner.EXPERIMENT,
        "classification": "TEST",
        "preregistration": {"path": "x", "sha256": runner.FROZEN_PREREGISTRATION_SHA256, "status": "FROZEN"},
        "runner": {"path": "x", "sha256": "a" * 64},
        "execution_mode": "formal-run",
        "model": {"model_id": runner.FORMAL_MODEL_NAME, "snapshot": runner.FORMAL_MODEL_SNAPSHOT},
        "dataset": {"path": "x", "sha256": runner.DATASET_SHA256},
        "classes": list(runner.CLASS_UNIVERSE),
        "checkpoints": runner.CHECKPOINT_NAMES,
        "readout_definitions": {},
        "splits": {},
        "cross_split_synthesis": {},
        "technical_validity": {"status": "VALID"},
        "attempt_status": "TEST",
        "result_status": "FORMAL_RESULT",
        "scientific_status": "FORMAL_ANALYSIS_COMPLETED",
        "warnings": [],
        "prompt_text_included": False,
        "hidden_states_included": False,
    })
    monkeypatch.setattr(runner, "finalize_formal_result", lambda result, root, failure_context=None: calls.append("finalize") or {"publication_status": "PUBLISHED"})
    runner.run_formal(tmp_path, auth_path)
    assert calls == ["pre", "consume", "execute", "finalize"]


def test_authorization_required_fields_match_contract():
    assert "single_use" in runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS
    assert "frozen_dataset_sha256" in runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS
    assert "model_hook_qualification_sha256" in runner.FORMAL_AUTHORIZATION_REQUIRED_FIELDS


def test_last_valid_token_indices_numpy_and_torch():
    mask = np.array([[1, 1, 1, 0], [1, 1, 0, 0]])
    assert runner.last_valid_token_indices(mask) == [2, 1]
    torch_mask = __import__("torch").tensor(mask)
    assert [int(v) for v in runner.last_valid_token_indices(torch_mask)] == [2, 1]


def test_extract_checkpoint_tensors_mapping_complete():
    import torch
    hidden = [torch.zeros(1, 4) for _ in range(29)]
    block27_pre = torch.zeros(1, 4)
    tensors = runner.extract_checkpoint_tensors(hidden, block27_pre)
    assert set(tensors) == set(runner.CHECKPOINT_NAMES)
