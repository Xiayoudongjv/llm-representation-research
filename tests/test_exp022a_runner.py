"""Synthetic-only EXP-022A runner and preflight tests."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from sklearn.linear_model import LogisticRegression


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "experiments"
    / "exp022a"
    / "run_exp022a.py"
)
SPEC = importlib.util.spec_from_file_location("exp022a_runner", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
sys.modules["exp022a_runner"] = runner
SPEC.loader.exec_module(runner)


def _synthetic_split(seed: int = 1) -> runner.SplitDataset:
    return runner.make_synthetic_split("A_original_fit_paraphrase_eval", seed)


def _synthetic_balanced_labels() -> tuple[list[str], list[str]]:
    y_true = []
    y_pred = []
    for cls in runner.CLASS_UNIVERSE:
        y_true.extend([cls] * 3)
        y_pred.extend([cls] * 3)
    return y_true, y_pred


def _tracked_analysis(monkeypatch: pytest.MonkeyPatch):
    """Run a synthetic split while recording fit object reuse and call roles."""
    original_fit_scaler = runner.fit_scaler
    original_fit_classifier = runner.fit_classifier
    original_build_rows = runner._build_prediction_rows
    scaler_objects = []
    classifier_objects = []
    build_calls = []

    def tracked_fit_scaler(X):
        scaler = original_fit_scaler(X)
        scaler_objects.append(scaler)
        return scaler

    def tracked_fit_classifier(X, y):
        classifier, warning_messages = original_fit_classifier(X, y)
        classifier_objects.append((classifier, list(y)))
        return classifier, warning_messages

    def tracked_build_rows(dataset, checkpoint, readout, scaler, classifier):
        build_calls.append((checkpoint, readout, scaler, classifier))
        return original_build_rows(dataset, checkpoint, readout, scaler, classifier)

    monkeypatch.setattr(runner, "fit_scaler", tracked_fit_scaler)
    monkeypatch.setattr(runner, "fit_classifier", tracked_fit_classifier)
    monkeypatch.setattr(runner, "_build_prediction_rows", tracked_build_rows)
    analysis = runner.run_split_analysis(_synthetic_split())
    return analysis, scaler_objects, classifier_objects, build_calls


AUTH_REPO_COMMIT = "a" * 40
AUTH_RUNNER_SHA = "b" * 64


def _synthetic_records(*, include_text: bool = True) -> list[dict[str, object]]:
    records = []
    for cls in runner.CLASS_UNIVERSE:
        for index in range(1, 4):
            for variant in ("original", "paraphrase"):
                record = {
                    "id": f"{cls}_{'orig' if variant == 'original' else 'para'}_{index:02d}",
                    "group": cls,
                    "variant_type": variant,
                }
                if include_text:
                    record["text"] = f"synthetic {cls} {variant} {index}"
                records.append(record)
    return records


def _base_authorization() -> dict[str, object]:
    return {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "experiment": runner.EXPERIMENT,
        "authorization_id": "synthetic-authorization",
        "single_use": True,
        "authorized_repository_commit": AUTH_REPO_COMMIT,
        "authorized_runner_sha256": AUTH_RUNNER_SHA,
        "frozen_preregistration_sha256": runner.FROZEN_PREREGISTRATION_SHA256,
        "formal_dataset_sha256": runner.PROMPT_FILE_SHA256,
        "model_name": runner.FORMAL_MODEL_NAME,
        "model_snapshot_identity": runner.FORMAL_MODEL_SNAPSHOT,
        "model_hook_qualification_sha256": runner.FORMAL_MODEL_HOOK_QUALIFICATION_SHA256,
        "canonical_result_path": "experiments/exp022a/results/exp022a_results.json",
        "authorization_created_at_utc": "2026-08-17T00:00:00Z",
    }


def _write_authorization(tmp_path: Path, authorization: dict[str, object]) -> Path:
    path = tmp_path / "formal_authorization.json"
    path.write_text(
        json.dumps(authorization, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return path


def _monkeypatch_authorization_identity(
    monkeypatch: pytest.MonkeyPatch,
    *,
    repository_commit: str = AUTH_REPO_COMMIT,
    runner_sha: str = AUTH_RUNNER_SHA,
) -> None:
    monkeypatch.setattr(runner, "_repository_commit", lambda root=runner.ROOT: repository_commit)
    monkeypatch.setattr(runner, "_runner_sha256", lambda: runner_sha)


def _monkeypatch_formal_preflight(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    repository_commit: str = AUTH_REPO_COMMIT,
    runner_sha: str = AUTH_RUNNER_SHA,
) -> None:
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(runner, "FORMAL_MODEL_SNAPSHOT_PATH", snapshot_dir)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=runner.ROOT: repository_commit)
    monkeypatch.setattr(runner, "_runner_sha256", lambda: runner_sha)
    monkeypatch.setattr(runner, "_tracked_tree_clean", lambda root: True)
    monkeypatch.setattr(runner, "_staging_empty", lambda root: True)
    monkeypatch.setattr(runner, "verify_frozen_authority", lambda root: {"status": "FROZEN"})
    monkeypatch.setattr(
        runner,
        "_verify_model_hook_qualification_artifact",
        lambda root: {"path": "synthetic", "sha256": runner.FORMAL_MODEL_HOOK_QUALIFICATION_SHA256},
    )
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root: None)


class _MockDecoderBlock(torch.nn.Module):
    def __init__(self, tuple_output: bool = False):
        super().__init__()
        self.tuple_output = tuple_output

    def forward(self, x):
        output = x * 2.0 + 1.0
        if self.tuple_output:
            return (output,)
        return output


class _RaisingDecoderBlock(torch.nn.Module):
    def forward(self, x):
        raise RuntimeError("synthetic forward failure")


def test_exact_binomial_tail_known_cases() -> None:
    assert runner.exact_binomial_tail(4, 0) == pytest.approx(0.0625)
    assert runner.exact_binomial_tail(5, 0) == pytest.approx(0.03125)
    assert runner.exact_binomial_tail(0, 0) == pytest.approx(1.0)
    assert runner.exact_binomial_tail(3, 1) == pytest.approx(0.3125)
    assert runner.exact_binomial_tail(0, 5) == pytest.approx(1.0)


def test_primary_support_rules() -> None:
    assert runner.d_fixed_support(-5 / 12, 0.03125)
    assert not runner.d_fixed_support(-4 / 12, 0.0625)
    assert not runner.d_fixed_support(0.0, 0.001)
    assert not runner.g_refit_support(False, 0.5, 0.001)
    assert runner.g_refit_support(True, 0.5, 0.03125)
    assert not runner.g_refit_support(True, 0.0, 0.001)


def test_balanced_accuracy_equals_accuracy_on_balanced_data() -> None:
    y_true, y_pred = _synthetic_balanced_labels()
    assert runner.balanced_accuracy(y_true, y_pred) == pytest.approx(
        runner.accuracy(y_true, y_pred)
    )
    assert runner.balanced_accuracy(y_true, y_pred) == pytest.approx(1.0)


def test_balanced_accuracy_differs_on_unbalanced_data() -> None:
    y_true = ["logic", "logic", "logic", "causality"]
    y_pred = ["logic", "logic", "logic", "logic"]
    assert runner.accuracy(y_true, y_pred) == pytest.approx(0.75)
    assert runner.balanced_accuracy(y_true, y_pred, ["logic", "causality"]) == pytest.approx(
        0.5
    )


def test_cross_split_categories_include_partial_concordance_zero_case() -> None:
    assert (
        runner.cross_split_category(True, True, -1.0, -0.5, favorable_sign=-1)
        == "CROSS_SPLIT_SUPPORTED"
    )
    assert (
        runner.cross_split_category(True, False, -1.0, 0.0, favorable_sign=-1)
        == "PARTIAL_CONCORDANCE"
    )
    assert (
        runner.cross_split_category(True, False, -1.0, -0.2, favorable_sign=-1)
        == "PARTIAL_CONCORDANCE"
    )
    assert (
        runner.cross_split_category(True, False, -1.0, 0.3, favorable_sign=-1)
        == "SPLIT_HETEROGENEOUS"
    )
    assert (
        runner.cross_split_category(False, False, -0.1, -0.2, favorable_sign=-1)
        == "NOT_SUPPORTED"
    )
    assert (
        runner.cross_split_category(False, False, -0.1, 0.2, favorable_sign=-1)
        == "SPLIT_HETEROGENEOUS"
    )


def test_class_probability_reordering() -> None:
    probabilities = np.array(
        [[0.1, 0.2, 0.3, 0.4], [0.4, 0.3, 0.2, 0.1]],
        dtype=float,
    )
    classifier_classes = ["analogy", "causality", "definition", "logic"]
    reordered = runner.reorder_probabilities(probabilities, classifier_classes)
    assert reordered.shape == (2, 4)
    assert reordered[0].tolist() == pytest.approx([0.4, 0.2, 0.1, 0.3])
    assert reordered[1].tolist() == pytest.approx([0.1, 0.3, 0.4, 0.2])


def test_class_probability_mapping_rejects_missing_class() -> None:
    probabilities = np.ones((1, 4)) / 4
    with pytest.raises(runner.TechnicalInvalidError):
        runner.reorder_probabilities(probabilities, ["logic", "causality", "analogy", "other"])


def test_fit_classifier_raises_technical_invalid_on_exception(monkeypatch) -> None:
    def raise_fit(self, X, y):
        raise RuntimeError("synthetic fit failure")

    monkeypatch.setattr(LogisticRegression, "fit", raise_fit)
    with pytest.raises(runner.TechnicalInvalidError):
        runner.fit_classifier(np.eye(4), list(runner.CLASS_UNIVERSE))


def test_predict_probabilities_rejects_nonfinite(monkeypatch) -> None:
    class FakeClassifier:
        def predict_proba(self, X):
            return np.array([[np.nan, 0, 0, 0]])

    with pytest.raises(runner.TechnicalInvalidError):
        runner.predict_probabilities(FakeClassifier(), runner.fit_scaler(np.eye(4)), np.eye(4))


def test_bootstrap_is_deterministic_for_same_fixture() -> None:
    correct_a = {cls: [1, 0, 1] for cls in runner.CLASS_UNIVERSE}
    correct_b = {cls: [1, 1, 0] for cls in runner.CLASS_UNIVERSE}
    first = runner.bootstrap_contrast(correct_a, correct_b, resamples=50)
    second = runner.bootstrap_contrast(correct_a, correct_b, resamples=50)
    assert first["lower"] == pytest.approx(second["lower"])
    assert first["upper"] == pytest.approx(second["upper"])
    assert first["distribution"] == pytest.approx(second["distribution"])


def test_synthetic_split_pipeline_produces_supported_primary_gates() -> None:
    analysis = runner.run_split_analysis(_synthetic_split())
    summary = analysis["summary"]
    assert analysis["technical_validity"] in {"VALID", "VALID_WITH_WARNING"}
    assert summary["primary"]["D_fixed"]["supported"] is True
    assert summary["primary"]["G_refit"]["supported"] is True
    assert summary["primary"]["G_refit"]["serial_gate"] == "OPEN"


def test_post_final_checkpoint_is_secondary_only() -> None:
    primary = runner.CHECKPOINT_BY_NAME[runner.PRIMARY_ENDPOINT_CHECKPOINT]
    post = runner.CHECKPOINT_BY_NAME[runner.POST_FINAL_CHECKPOINT]
    assert primary.representation_role == "PRE_FINAL_RMSNORM_HOOK"
    assert post.representation_role == "POST_FINAL_RMSNORM"
    assert primary.block_index == 27 and primary.hidden_states_index is None
    assert post.block_index == 27 and post.hidden_states_index == 28


def test_validate_split_dataset_rejects_missing_fit_class() -> None:
    dataset = _synthetic_split()
    dataset.fit_records.pop("logic")
    dataset.fit_records["other"] = ("other_1", "other_2", "other_3")
    with pytest.raises(runner.TechnicalInvalidError):
        runner.validate_split_dataset(dataset)


def test_validate_split_dataset_rejects_nonfinite_representation() -> None:
    dataset = _synthetic_split()
    record_id = dataset.eval_records["logic"][0]
    dataset.representations[record_id][runner.PRIMARY_ENDPOINT_CHECKPOINT] = np.array(
        [np.nan] * 8, dtype=np.float32
    )
    with pytest.raises(runner.TechnicalInvalidError):
        runner.validate_split_dataset(dataset)


def test_synthetic_preflight_reports_pass_and_does_not_access_real_data() -> None:
    report = runner.synthetic_preflight()
    assert report["status"] == "EXP022A_SYNTHETIC_PREFLIGHT_PASS"
    assert report["cross_split_synthesis"]["D_fixed"] == "CROSS_SPLIT_SUPPORTED"
    assert report["cross_split_synthesis"]["G_refit"] == "CROSS_SPLIT_SUPPORTED"
    assert report["model_loaded"] is False
    assert report["tokenizer_loaded"] is False
    assert report["controlled_prompt_text_accessed"] is False
    assert report["formal_eval_accessed"] is False
    assert report["scientific_result_created"] is False


def test_static_preflight_passes_and_has_engineering_classification() -> None:
    report = runner.static_preflight()
    assert report["status"] == "EXP022A_STATIC_PREFLIGHT_PASS"
    assert report["classification"] == "ENGINEERING_STATIC_PREFLIGHT_ONLY"
    assert report["frozen_preregistration_sha256"] == runner.FROZEN_PREREGISTRATION_SHA256
    assert report["formal_run_authorized"] is False


def test_frozen_authority_mismatch_is_hard_failure(monkeypatch) -> None:
    monkeypatch.setattr(runner, "_sha256", lambda path: "0" * 64)
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.verify_frozen_authority()


def test_formal_run_fails_before_forbidden_loader_calls(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden loader called")

    monkeypatch.setattr(runner, "load_production_dataset", forbidden)
    monkeypatch.setattr(runner, "select_last_valid_token", forbidden)
    monkeypatch.setattr(runner, "block27_pre_final_rmsnorm_hook", forbidden)
    with pytest.raises(PermissionError, match="FORMAL_RUN_NOT_AUTHORIZED"):
        runner.run_formal()


def test_no_mode_fails_closed() -> None:
    with pytest.raises(SystemExit) as exc_info:
        runner.main([])
    assert exc_info.value.code != 0


def test_production_record_validation_requires_nonempty_text() -> None:
    records = _synthetic_records(include_text=True)
    split_definitions = runner.load_split_definitions()
    metas = runner.validate_production_records(records, split_definitions)
    assert len(metas) == 24


def test_production_record_validation_rejects_missing_text() -> None:
    records = _synthetic_records(include_text=False)
    split_definitions = runner.load_split_definitions()
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_RECORD_MISSING_TEXT"):
        runner.validate_production_records(records, split_definitions)


def test_last_valid_token_indices() -> None:
    assert runner.last_valid_token_indices(np.array([1, 1, 1, 0, 0])) == [2]
    assert runner.last_valid_token_indices(
        np.array([[1, 1, 0, 0], [1, 1, 1, 0]])
    ) == [1, 2]


def test_atomic_write_json_is_complete(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "result.json"
    runner.atomic_write_json(target, {"a": 1})
    assert target.exists()
    assert runner._read_json(target) == {"a": 1}
    assert not target.with_name(target.name + ".staging").exists()


def test_staging_path_has_single_source() -> None:
    assert runner.STAGING_RESULT_PATH == runner.staging_path_for(
        runner.CANONICAL_RESULT_PATH
    )
    assert runner.STAGING_RESULT_PATH.name == "exp022a_results.json.staging"
    assert "exp022a_results.json.tmp" not in str(runner.STAGING_RESULT_PATH)


def test_collision_checker_rejects_actual_staging_path(tmp_path: Path) -> None:
    canonical = tmp_path / runner.CANONICAL_RESULT_PATH.relative_to(runner.ROOT)
    staging = runner.staging_path_for(canonical)
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.write_text("KEEP", encoding="utf-8")
    with pytest.raises(runner.ProtocolIntegrityError, match="STAGING_RESULT_ALREADY_EXISTS"):
        runner.verify_no_result_collision(tmp_path)
    assert staging.read_text(encoding="utf-8") == "KEEP"


def test_atomic_write_preserves_existing_staging(tmp_path: Path) -> None:
    target = tmp_path / "result.json"
    staging = runner.staging_path_for(target)
    staging.write_text("KEEP", encoding="utf-8")
    with pytest.raises(FileExistsError):
        runner.atomic_write_json(target, {"x": 1})
    assert staging.read_text(encoding="utf-8") == "KEEP"
    assert not target.exists()


def test_atomic_write_never_overwrites_canonical(tmp_path: Path) -> None:
    target = tmp_path / "result.json"
    target.write_text("KEEP", encoding="utf-8")
    with pytest.raises(FileExistsError):
        runner.atomic_write_json(target, {"x": 1})
    assert target.read_text(encoding="utf-8") == "KEEP"


def test_successful_atomic_publication_is_no_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "result.json"
    outcome = runner.atomic_write_json(target, {"a": 1})
    assert outcome["publication_status"] == "PUBLISHED"
    assert runner._read_json(target) == {"a": 1}
    assert not runner.staging_path_for(target).exists()
    with pytest.raises(FileExistsError):
        runner.atomic_write_json(target, {"a": 2})
    assert runner._read_json(target) == {"a": 1}


def test_publication_link_failure_leaves_no_canonical(tmp_path: Path, monkeypatch) -> None:
    target = tmp_path / "result.json"

    def fail_link(source, destination):
        raise OSError("synthetic link failure")

    monkeypatch.setattr(runner.os, "link", fail_link)
    with pytest.raises(OSError, match="synthetic link failure"):
        runner.atomic_write_json(target, {"a": 1})
    assert not target.exists()
    assert not runner.staging_path_for(target).exists()


def test_formal_result_validation_blocks_publication(tmp_path: Path, monkeypatch) -> None:
    events = []
    monkeypatch.setattr(
        runner,
        "verify_no_result_collision",
        lambda root: events.append("collision"),
    )
    monkeypatch.setattr(
        runner,
        "atomic_publish_validated_result",
        lambda result, root=runner.ROOT: events.append("publish"),
    )
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.finalize_formal_result({"schema_version": "1.0.0"}, tmp_path)
    assert events == []
    assert not runner.staging_path_for(tmp_path / "result.json").exists()


def test_formal_finalization_order_validate_collision_publish(
    tmp_path: Path, monkeypatch
) -> None:
    events = []
    monkeypatch.setattr(
        runner,
        "validate_result_schema",
        lambda result, formal=True: events.append("validate"),
    )
    monkeypatch.setattr(
        runner,
        "verify_no_result_collision",
        lambda root: events.append("collision"),
    )
    monkeypatch.setattr(
        runner,
        "atomic_publish_validated_result",
        lambda result, root=runner.ROOT: events.append("publish"),
    )
    runner.finalize_formal_result({}, tmp_path)
    assert events == ["validate", "collision", "publish"]


def test_formal_run_calls_frozen_authority_before_authorization_gate(
    monkeypatch,
) -> None:
    events = []
    monkeypatch.setattr(
        runner,
        "verify_frozen_authority",
        lambda root: events.append("authority"),
    )

    def fail_authorization(root):
        events.append("gate")
        raise PermissionError("FORMAL_RUN_NOT_AUTHORIZED")

    monkeypatch.setattr(runner, "_require_formal_authorization", fail_authorization)
    with pytest.raises(PermissionError, match="FORMAL_RUN_NOT_AUTHORIZED"):
        runner.run_formal()
    assert events == ["authority", "gate"]


def test_a0_reuses_reference_objects_downstream(monkeypatch) -> None:
    _, scaler_objects, classifier_objects, build_calls = _tracked_analysis(monkeypatch)
    reference_scaler = scaler_objects[0]
    reference_classifier = classifier_objects[0][0]
    a0_calls = [call for call in build_calls if call[1] == "A0"]
    assert len(a0_calls) == len(runner.CHECKPOINT_NAMES)
    assert all(
        call[2] is reference_scaler and call[3] is reference_classifier
        for call in a0_calls
    )


def test_a1_reuses_reference_classifier_and_refits_scaler(monkeypatch) -> None:
    _, _, classifier_objects, build_calls = _tracked_analysis(monkeypatch)
    reference_classifier = classifier_objects[0][0]
    a1_calls = [call for call in build_calls if call[1] == "A1"]
    assert len(a1_calls) == len(runner.CHECKPOINT_NAMES)
    assert all(call[3] is reference_classifier for call in a1_calls)
    assert len({id(call[2]) for call in a1_calls}) == len(runner.CHECKPOINT_NAMES)


def test_a2_uses_layer_specific_fit_only_components(monkeypatch) -> None:
    _, _, classifier_objects, build_calls = _tracked_analysis(monkeypatch)
    a2_calls = [call for call in build_calls if call[1] == "A2"]
    assert len(a2_calls) == len(runner.CHECKPOINT_NAMES)
    assert len({id(call[2]) for call in a2_calls}) == len(runner.CHECKPOINT_NAMES)
    assert len({id(call[3]) for call in a2_calls}) == len(runner.CHECKPOINT_NAMES)


def test_eval_records_never_enter_fit_calls(monkeypatch) -> None:
    dataset = _synthetic_split()
    rng = np.random.default_rng(20260817)
    for cls in runner.CLASS_UNIVERSE:
        for record_id in dataset.eval_records[cls]:
            for checkpoint in dataset.representations[record_id]:
                dataset.representations[record_id][checkpoint] = np.asarray(
                    dataset.representations[record_id][checkpoint], dtype=np.float32
                ) + rng.normal(scale=0.5, size=8).astype(np.float32)

    fit_ids = {
        record_id
        for cls in runner.CLASS_UNIVERSE
        for record_id in dataset.fit_records[cls]
    }
    eval_ids = {
        record_id
        for cls in runner.CLASS_UNIVERSE
        for record_id in dataset.eval_records[cls]
    }
    calls = []
    original_stack_records = runner._stack_records

    def tracked_stack_records(dataset, record_map, checkpoint):
        ids = {
            record_id
            for cls in runner.CLASS_UNIVERSE
            for record_id in record_map[cls]
        }
        calls.append((checkpoint, ids))
        return original_stack_records(dataset, record_map, checkpoint)

    monkeypatch.setattr(runner, "_stack_records", tracked_stack_records)
    analysis = runner.run_split_analysis(dataset)
    assert analysis["technical_validity"] in {"VALID", "VALID_WITH_WARNING"}
    for _, ids in calls:
        assert ids in (fit_ids, eval_ids)
    assert sum(1 for _, ids in calls if ids == fit_ids) == 14
    assert sum(1 for _, ids in calls if ids == eval_ids) == 39


def test_last_valid_token_indices_torch_cpu() -> None:
    mask_1d = torch.tensor([1, 1, 1, 0, 0], dtype=torch.long)
    indices_1d = runner.last_valid_token_indices(mask_1d)
    assert torch.is_tensor(indices_1d)
    assert indices_1d.dtype == torch.long
    assert indices_1d.device.type == "cpu"
    assert indices_1d.tolist() == [2]

    mask_2d = torch.tensor(
        [[1, 1, 0, 0], [1, 1, 1, 0]], dtype=torch.long
    )
    indices_2d = runner.last_valid_token_indices(mask_2d)
    assert torch.is_tensor(indices_2d)
    assert indices_2d.dtype == torch.long
    assert indices_2d.tolist() == [1, 2]


def test_last_valid_token_indices_torch_rejects_invalid_masks() -> None:
    with pytest.raises(ValueError, match="no valid token"):
        runner.last_valid_token_indices(torch.zeros(2, 3, dtype=torch.long))
    with pytest.raises(ValueError, match="one- or two-dimensional"):
        runner.last_valid_token_indices(torch.ones(1, 2, 3, dtype=torch.long))
    with pytest.raises(ValueError, match="negative"):
        runner.last_valid_token_indices(torch.tensor([1, -1], dtype=torch.long))


def test_select_last_valid_token_torch_batch_and_two_dimensional() -> None:
    states = torch.arange(2 * 4 * 3, dtype=torch.float32).reshape(2, 4, 3)
    mask = torch.tensor([[1, 1, 0, 0], [1, 1, 1, 0]], dtype=torch.long)
    selected = runner.select_last_valid_token(states, mask)
    assert torch.is_tensor(selected)
    assert selected.shape == (2, 3)
    assert selected.device == states.device
    assert torch.equal(
        selected,
        torch.stack([states[0, 1, :], states[1, 2, :]]),
    )

    states_2d = torch.arange(5 * 3, dtype=torch.float32).reshape(5, 3)
    selected_2d = runner.select_last_valid_token(
        states_2d, torch.tensor([1, 1, 1, 0, 0], dtype=torch.long)
    )
    assert torch.is_tensor(selected_2d)
    assert selected_2d.shape == (3,)
    assert torch.equal(selected_2d, states_2d[2, :])


def test_select_last_valid_token_numpy_preserves_existing_behavior() -> None:
    states = np.arange(2 * 4 * 3, dtype=np.float32).reshape(2, 4, 3)
    mask = np.array([[1, 1, 0, 0], [1, 1, 1, 0]])
    selected = runner.select_last_valid_token(states, mask)
    assert isinstance(selected, np.ndarray)
    assert selected.shape == (2, 3)
    assert np.array_equal(selected, np.stack([states[0, 1, :], states[1, 2, :]]))


def test_to_float32_analysis_array_torch_detach_cpu_float32() -> None:
    tensor = torch.tensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
    array = runner.to_float32_analysis_array(tensor)
    assert isinstance(array, np.ndarray)
    assert array.dtype == np.float32
    assert array.tolist() == [[1.0, 2.0], [3.0, 4.0]]


def test_to_float32_analysis_array_rejects_nonfinite() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        runner.to_float32_analysis_array(torch.tensor([1.0, float("nan")]))
    with pytest.raises(ValueError, match="non-finite"):
        runner.to_float32_analysis_array(np.array([1.0, np.inf], dtype=np.float32))


def test_to_float32_analysis_array_validates_expected_dimension() -> None:
    with pytest.raises(ValueError, match="dimension"):
        runner.to_float32_analysis_array(np.ones((2, 3), dtype=np.float32), expected_ndim=1)
    array = runner.to_float32_analysis_array(torch.ones(2, 3), expected_ndim=2)
    assert array.shape == (2, 3)


def test_extract_block_hidden_state_supports_tensor_tuple_and_list() -> None:
    tensor = torch.ones(2, 3)
    assert runner.extract_block_hidden_state(tensor) is tensor
    assert torch.equal(runner.extract_block_hidden_state((tensor, "meta")), tensor)
    assert torch.equal(runner.extract_block_hidden_state([tensor]), tensor)
    with pytest.raises(TypeError, match="UNSUPPORTED"):
        runner.extract_block_hidden_state({"hidden": tensor})
    with pytest.raises(TypeError, match="UNSUPPORTED"):
        runner.extract_block_hidden_state(())


def test_forward_hook_capture_records_output_without_replacement() -> None:
    module = _MockDecoderBlock()
    x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
    capture = runner.ForwardHookCapture()
    with runner.block_output_hook_capture(module, capture) as active:
        output = module(x)
        assert active is capture
        assert torch.equal(capture.value, output)
    assert torch.equal(output, x * 2.0 + 1.0)


def test_hook_cleanup_after_success_and_subsequent_forward() -> None:
    module = _MockDecoderBlock()
    capture = runner.ForwardHookCapture()
    x = torch.tensor([1.0, 2.0, 3.0])
    with runner.block_output_hook_capture(module, capture):
        first = module(x)
        captured = capture.value
    assert len(module._forward_hooks) == 0
    second = module(x + 10.0)
    assert torch.equal(capture.value, captured)
    assert torch.equal(first, x * 2.0 + 1.0)
    assert not torch.equal(captured, second)


def test_hook_cleanup_after_exception() -> None:
    module = _RaisingDecoderBlock()
    capture = runner.ForwardHookCapture()
    with pytest.raises(RuntimeError, match="synthetic forward failure"):
        with runner.block_output_hook_capture(module, capture):
            module(torch.tensor([1.0]))
    assert len(module._forward_hooks) == 0


def test_hook_capture_rejects_missing_and_multiple_capture() -> None:
    capture = runner.ForwardHookCapture()
    with pytest.raises(RuntimeError, match="MISSING"):
        _ = capture.value
    capture.record(torch.ones(2, 3))
    with pytest.raises(RuntimeError, match="MULTIPLE"):
        capture.record(torch.ones(2, 3))


def test_mock_decoder_tuple_output_hook_captures_first_component() -> None:
    module = _MockDecoderBlock(tuple_output=True)
    x = torch.tensor([[1.0, 2.0]])
    capture = runner.ForwardHookCapture()
    with runner.block_output_hook_capture(module, capture):
        output = module(x)
    assert isinstance(output, tuple)
    assert len(output) == 1
    assert torch.equal(output[0], x * 2.0 + 1.0)
    assert torch.equal(capture.value, output[0])


def test_zero_perturbation_unit_with_mock_hook() -> None:
    module = _MockDecoderBlock()
    x = torch.tensor([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    reference = module(x)
    capture = runner.ForwardHookCapture()
    with runner.block_output_hook_capture(module, capture):
        observed = module(x)
    assert torch.equal(observed, reference)
    assert torch.equal(capture.value, reference)


def test_checkpoint_extraction_maps_hidden_states_and_block27_hook() -> None:
    hidden_states = [torch.zeros(2, 4, 3) for _ in range(29)]
    for index in range(17, 29):
        hidden_states[index] = torch.full((2, 4, 3), float(index))
    block27_pre = torch.full((2, 4, 3), 270.0)
    checkpoints = runner.extract_checkpoint_tensors(hidden_states, block27_pre)
    assert set(checkpoints) == set(runner.CHECKPOINT_NAMES)
    assert torch.equal(
        checkpoints["block16_pre_final_rmsnorm"], hidden_states[17]
    )
    assert torch.equal(
        checkpoints["block26_pre_final_rmsnorm"], hidden_states[27]
    )
    assert torch.equal(checkpoints["block27_pre_final_rmsnorm"], block27_pre)
    assert torch.equal(
        checkpoints["block27_post_final_rmsnorm"], hidden_states[28]
    )


def test_checkpoint_extraction_rejects_missing_hidden_states() -> None:
    with pytest.raises(runner.ProtocolIntegrityError, match="MISSING_HIDDEN_STATE"):
        runner.extract_checkpoint_tensors(
            [torch.zeros(2, 4, 3) for _ in range(10)],
            torch.zeros(2, 4, 3),
        )


def test_last_token_extraction_uses_same_index_across_checkpoints() -> None:
    checkpoint_tensors = {
        name: torch.arange(2 * 5 * 3, dtype=torch.float32).reshape(2, 5, 3)
        for name in runner.CHECKPOINT_NAMES
    }
    mask = torch.tensor([[1, 1, 0, 0, 0], [1, 1, 1, 0, 0]], dtype=torch.long)
    selected = runner.extract_last_token_representations(checkpoint_tensors, mask)
    assert set(selected) == set(runner.CHECKPOINT_NAMES)
    for name, tensor in selected.items():
        assert torch.is_tensor(tensor)
        assert tensor.shape == (2, 3)
        assert torch.equal(tensor[0], checkpoint_tensors[name][0, 1, :])
        assert torch.equal(tensor[1], checkpoint_tensors[name][1, 2, :])


def test_build_parser_accepts_explicit_authorization_file() -> None:
    args = runner.build_parser().parse_args(
        ["--formal-run", "--authorization-file", "auth.json"]
    )
    assert args.formal_run is True
    assert args.authorization_file == "auth.json"


def test_formal_run_with_missing_authorization_file_fails_closed() -> None:
    with pytest.raises(
        runner.ProtocolIntegrityError, match="FORMAL_AUTHORIZATION_FILE_MISSING"
    ):
        runner.run_formal(runner.ROOT, Path("missing-authorization.json"))


def test_authorization_validation_accepts_exact_valid_authorization(monkeypatch) -> None:
    _monkeypatch_authorization_identity(monkeypatch)
    authorization = _base_authorization()
    assert runner._validate_formal_authorization(authorization, runner.ROOT) == authorization


def test_authorization_validation_rejects_invalid_schema_and_bindings(monkeypatch) -> None:
    _monkeypatch_authorization_identity(monkeypatch)
    base = _base_authorization()
    invalid = []

    missing = copy.deepcopy(base)
    missing.pop("authorization_created_at_utc")
    invalid.append(("missing-field", missing))

    extra = copy.deepcopy(base)
    extra["unexpected"] = True
    invalid.append(("extra-field", extra))

    wrong_experiment = copy.deepcopy(base)
    wrong_experiment["experiment"] = "EXP-021"
    invalid.append(("wrong-experiment", wrong_experiment))

    not_single_use = copy.deepcopy(base)
    not_single_use["single_use"] = False
    invalid.append(("not-single-use", not_single_use))

    wrong_repo = copy.deepcopy(base)
    wrong_repo["authorized_repository_commit"] = "1" * 40
    invalid.append(("wrong-repo", wrong_repo))

    wrong_runner = copy.deepcopy(base)
    wrong_runner["authorized_runner_sha256"] = "1" * 64
    invalid.append(("wrong-runner", wrong_runner))

    wrong_prereg = copy.deepcopy(base)
    wrong_prereg["frozen_preregistration_sha256"] = "1" * 64
    invalid.append(("wrong-prereg", wrong_prereg))

    wrong_dataset = copy.deepcopy(base)
    wrong_dataset["formal_dataset_sha256"] = "1" * 64
    invalid.append(("wrong-dataset", wrong_dataset))

    wrong_model = copy.deepcopy(base)
    wrong_model["model_name"] = "other/model"
    invalid.append(("wrong-model", wrong_model))

    wrong_snapshot = copy.deepcopy(base)
    wrong_snapshot["model_snapshot_identity"] = "1" * 64
    invalid.append(("wrong-snapshot", wrong_snapshot))

    wrong_qualification = copy.deepcopy(base)
    wrong_qualification["model_hook_qualification_sha256"] = "1" * 64
    invalid.append(("wrong-qualification", wrong_qualification))

    wrong_result_path = copy.deepcopy(base)
    wrong_result_path["canonical_result_path"] = "wrong/result.json"
    invalid.append(("wrong-result-path", wrong_result_path))

    for label, authorization in invalid:
        with pytest.raises(runner.ProtocolIntegrityError):
            runner._validate_formal_authorization(authorization, runner.ROOT)

    with pytest.raises(runner.ProtocolIntegrityError, match="NOT_OBJECT"):
        runner._validate_formal_authorization([], runner.ROOT)


def test_authorization_consumption_is_exclusive_and_single_use(tmp_path: Path) -> None:
    authorization = _base_authorization()
    auth_path = _write_authorization(tmp_path, authorization)
    first = runner._consume_formal_authorization(
        tmp_path, authorization, auth_path, "attempt-one"
    )
    record_path = Path(first["consumption_record_path"])
    assert record_path.exists()
    assert first["authorization_sha256"] == runner._sha256(auth_path)

    with pytest.raises(runner.ProtocolIntegrityError, match="AUTHORIZATION_ALREADY_CONSUMED"):
        runner._consume_formal_authorization(
            tmp_path, authorization, auth_path, "attempt-two"
        )


def test_run_formal_consumes_before_scientific_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authorization = _base_authorization()
    auth_path = _write_authorization(tmp_path, authorization)
    _monkeypatch_formal_preflight(monkeypatch, tmp_path)
    events = []

    monkeypatch.setattr(
        runner,
        "_pre_consumption_static_checks",
        lambda root, auth, path: events.append("static"),
    )
    monkeypatch.setattr(
        runner,
        "_consume_formal_authorization",
        lambda root, auth, path, attempt: events.append("consume")
        or {
            "authorization_sha256": runner._sha256(path),
            "consumption_record_path": "synthetic",
            "consumption_record_sha256": "0" * 64,
            "run_attempt_id": attempt,
        },
    )
    monkeypatch.setattr(
        runner,
        "_execute_formal_after_consumption",
        lambda root, auth, consumption, attempt: events.append("execute")
        or {"result": "synthetic"},
    )
    monkeypatch.setattr(
        runner,
        "finalize_formal_result",
        lambda result, root=runner.ROOT: events.append("finalize")
        or {"publication_status": "SYNTHETIC"},
    )

    runner.run_formal(tmp_path, auth_path)
    assert events == ["static", "consume", "execute", "finalize"]


def test_execute_formal_after_consumption_reaches_splits_and_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = []
    authorization = _base_authorization()
    consumption = {
        "authorization_sha256": "c" * 64,
        "consumption_record_path": "synthetic-consumption.json",
        "consumption_record_sha256": "d" * 64,
        "run_attempt_id": "attempt-split",
    }

    monkeypatch.setattr(
        runner,
        "_verify_formal_dataset_identity",
        lambda root: events.append("dataset") or {"path": "p", "sha256": "e" * 64},
    )
    monkeypatch.setattr(
        runner,
        "_load_formal_records",
        lambda root: events.append("records") or ([], []),
    )
    monkeypatch.setattr(
        runner,
        "_load_formal_runtime",
        lambda root: events.append("runtime")
        or (object(), object(), torch.device("cpu")),
    )
    monkeypatch.setattr(
        runner,
        "_extract_formal_representations",
        lambda root, tokenizer, model, device, records: events.append("extract")
        or {},
    )

    def fake_build(root, records, metas, representations):
        events.append("build")
        return {
            "A_original_fit_paraphrase_eval": "split-a",
            "B_paraphrase_fit_original_eval": "split-b",
        }

    monkeypatch.setattr(runner, "_build_formal_split_datasets", fake_build)

    def fake_analysis(dataset):
        events.append(f"analysis:{dataset}")
        return {
            "summary": {"primary": {}, "secondary": {}, "bootstrap": {}},
            "technical_validity": "VALID",
            "warnings": [],
        }

    monkeypatch.setattr(runner, "run_split_analysis", fake_analysis)
    monkeypatch.setattr(
        runner,
        "_build_formal_result",
        lambda *args, **kwargs: events.append("result") or {"result": "built"},
    )

    result = runner._execute_formal_after_consumption(
        runner.ROOT, authorization, consumption, "attempt-split"
    )
    assert result == {"result": "built"}
    assert events == [
        "dataset",
        "records",
        "runtime",
        "extract",
        "build",
        "analysis:split-a",
        "analysis:split-b",
        "result",
    ]


def test_failure_after_consumption_preserves_evidence_and_no_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    authorization = _base_authorization()
    auth_path = _write_authorization(tmp_path, authorization)
    _monkeypatch_formal_preflight(monkeypatch, tmp_path)
    events = []

    def fail_execution(root, authorization, consumption, run_attempt_id):
        raise RuntimeError("synthetic post-consumption failure")

    monkeypatch.setattr(runner, "_execute_formal_after_consumption", fail_execution)
    monkeypatch.setattr(
        runner,
        "finalize_formal_result",
        lambda result, root=runner.ROOT: events.append("finalize"),
    )

    with pytest.raises(RuntimeError, match="synthetic post-consumption failure"):
        runner.run_formal(tmp_path, auth_path)

    authorization_sha = runner._sha256(auth_path)
    consumption_path = runner._consumption_path_for(tmp_path, authorization_sha)
    assert consumption_path.exists()
    evidence_dir = (
        tmp_path
        / runner.TECHNICAL_FAILURE_EVIDENCE_DIR.relative_to(runner.ROOT)
    )
    evidence_files = list(evidence_dir.glob("*.json"))
    assert len(evidence_files) == 1
    assert "finalize" not in events
    canonical = tmp_path / runner.CANONICAL_RESULT_PATH.relative_to(runner.ROOT)
    assert not canonical.exists()
    assert not runner.staging_path_for(canonical).exists()


def test_production_record_validation_rejects_malformed_records() -> None:
    split_definitions = runner.load_split_definitions()
    valid = _synthetic_records(include_text=True)

    wrong_count = valid[:-1]
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_RECORD_COUNT_MISMATCH"):
        runner.validate_production_records(wrong_count, split_definitions)

    duplicate_id = copy.deepcopy(valid)
    duplicate_id[1]["id"] = duplicate_id[0]["id"]
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_RECORD_ID_DUPLICATE"):
        runner.validate_production_records(duplicate_id, split_definitions)

    unexpected_group = copy.deepcopy(valid)
    unexpected_group[0]["group"] = "mathematics"
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_CLASS_UNIVERSE_MISMATCH"):
        runner.validate_production_records(unexpected_group, split_definitions)

    unexpected_variant = copy.deepcopy(valid)
    unexpected_variant[0]["variant_type"] = "augmented"
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_VARIANT_ROLE_MISMATCH"):
        runner.validate_production_records(unexpected_variant, split_definitions)

    class_imbalance = copy.deepcopy(valid)
    class_imbalance[0]["group"] = "causality"
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_VARIANT_CLASS_COUNT_MISMATCH"):
        runner.validate_production_records(class_imbalance, split_definitions)

    missing_group = copy.deepcopy(valid)
    missing_group[0].pop("group")
    with pytest.raises(runner.ProtocolIntegrityError, match="PRODUCTION_RECORD_MISSING_GROUP"):
        runner.validate_production_records(missing_group, split_definitions)


def test_formal_extraction_integration_uses_qualified_runtime_helpers() -> None:
    class _Namespace:
        pass

    class _MockBlock(torch.nn.Module):
        def forward(self, hidden):
            return hidden * 2.0 + 1.0

    class _MockModel:
        def __init__(self):
            self.model = _Namespace()
            self.model.layers = [torch.nn.Identity() for _ in range(28)]
            self.model.layers[27] = _MockBlock()

        def __call__(self, input_ids, attention_mask, use_cache, output_hidden_states):
            batch, length = input_ids.shape
            hidden = torch.arange(
                batch * length * 4, dtype=torch.float32
            ).reshape(batch, length, 4)
            _ = self.model.layers[27](hidden)
            hidden_states = tuple(hidden + float(index) for index in range(29))
            output = _Namespace()
            output.hidden_states = hidden_states
            return output

    tokenizer = lambda text, return_tensors, padding, truncation, add_special_tokens: {
        "input_ids": torch.tensor([[7, 8, 9]], dtype=torch.long),
        "attention_mask": torch.tensor([[1, 1, 1]], dtype=torch.long),
    }
    model = _MockModel()
    device = torch.device("cpu")
    records = [{"id": "logic_orig_01", "text": "synthetic prompt"}]

    representations = runner._extract_formal_representations(
        runner.ROOT, tokenizer, model, device, records
    )
    assert set(representations) == {"logic_orig_01"}
    assert set(representations["logic_orig_01"]) == set(runner.CHECKPOINT_NAMES)
    for checkpoint, value in representations["logic_orig_01"].items():
        assert isinstance(value, np.ndarray)
        assert value.dtype == np.float32
        assert value.shape == (4,)
        assert np.isfinite(value).all()


def test_formal_model_architecture_validation_rejects_mismatch() -> None:
    class _Config:
        model_type = "qwen3"
        hidden_size = 2048
        num_hidden_layers = 28

    class _WrongClass:
        config = _Config()
        model = type("Model", (), {"layers": list(range(28))})()

    with pytest.raises(runner.ProtocolIntegrityError, match="FORMAL_MODEL_CLASS_MISMATCH"):
        runner._validate_formal_model_architecture(_WrongClass())

    class _WrongLayers:
        pass

    _WrongLayers.__name__ = "Qwen3ForCausalLM"
    _WrongLayers.config = _Config()
    _WrongLayers.model = type("Model", (), {"layers": list(range(27))})()
    with pytest.raises(runner.ProtocolIntegrityError, match="FORMAL_MODEL_TRANSFORMER_BLOCKS_MISMATCH"):
        runner._validate_formal_model_architecture(_WrongLayers())


def test_formal_gate_still_blocks_new_runtime_helpers(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("forbidden runtime helper called")

    monkeypatch.setattr(runner, "extract_checkpoint_tensors", forbidden)
    monkeypatch.setattr(runner, "block_output_hook_capture", forbidden)
    monkeypatch.setattr(runner, "make_block_output_hook", forbidden)
    with pytest.raises(PermissionError, match="FORMAL_RUN_NOT_AUTHORIZED"):
        runner.run_formal()


@pytest.mark.skipif(
    not torch.cuda.is_available(),
    reason="optional CUDA tensor smoke requires a CUDA device",
)
def test_optional_cuda_tensor_runtime_path_smoke() -> None:
    device = torch.device("cuda")
    mask = torch.tensor(
        [[1, 1, 0], [1, 1, 1]], dtype=torch.long, device=device
    )
    indices = runner.last_valid_token_indices(mask)
    assert torch.is_tensor(indices)
    assert indices.device.type == "cuda"

    states = torch.arange(2 * 3 * 3, dtype=torch.float32, device=device).reshape(
        2, 3, 3
    )
    selected = runner.select_last_valid_token(states, mask)
    assert torch.is_tensor(selected)
    assert selected.device.type == "cuda"

    analysis = runner.to_float32_analysis_array(selected)
    assert isinstance(analysis, np.ndarray)
    assert analysis.dtype == np.float32
