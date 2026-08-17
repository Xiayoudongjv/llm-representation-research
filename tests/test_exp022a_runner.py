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
