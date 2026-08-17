"""Synthetic-only EXP-022A runner and preflight tests."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
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


def test_production_record_validation_does_not_require_prompt_text(tmp_path: Path) -> None:
    records = []
    for cls in runner.CLASS_UNIVERSE:
        for index in range(1, 4):
            for variant in ("original", "paraphrase"):
                records.append(
                    {
                        "id": f"{cls}_{'orig' if variant == 'original' else 'para'}_{index:02d}",
                        "group": cls,
                        "variant_type": variant,
                    }
                )
    split_definitions = runner.load_split_definitions()
    metas = runner.validate_production_records(records, split_definitions)
    assert len(metas) == 24


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
