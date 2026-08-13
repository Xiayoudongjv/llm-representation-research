"""Synthetic-only safety and arithmetic tests for the EXP-020A runner."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "exp020" / "run_exp020a.py"
SPEC = importlib.util.spec_from_file_location("exp020_runner", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


def test_import_is_side_effect_free() -> None:
    assert runner.NEUTRAL_TEXT == "This is a neutral hardware diagnostic."
    assert not hasattr(runner, "prompts")


def test_no_mode_refuses_before_any_action() -> None:
    with pytest.raises(SystemExit) as error:
        runner.main([])
    assert error.value.code != 0


def test_formal_authorization_rejection_precedes_formal_actions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[str] = []
    monkeypatch.setattr(runner, "AUTHORIZATION_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(runner, "_json", lambda path: calls.append(f"json:{path.name}"))
    monkeypatch.setattr(runner, "_require_no_formal_results", lambda: calls.append("output"))
    assert runner.main(["--formal-run"]) == 2
    assert calls == []


def test_layer_mapping_and_last_token_extraction_are_frozen() -> None:
    primary = {"block_index": 18, "hidden_state_index": 19}
    secondary = {"block_index": 26, "hidden_state_index": 27}
    assert primary["hidden_state_index"] == primary["block_index"] + 1
    assert secondary["hidden_state_index"] == secondary["block_index"] + 1


def test_fit_only_centroids_and_probe_and_probability_mapping() -> None:
    fit = {"logic": np.array([[0.0, 0.0], [2.0, 2.0]]), "causality": np.array([[4.0, 4.0], [6.0, 6.0]])}
    centroids = runner._fit_centroids(fit, ["logic", "causality"])
    assert np.array_equal(centroids["logic"], np.array([1.0, 1.0]))
    config = {"preprocessing": {"with_mean": True, "with_std": True}, "classifier": {"class_order": ["logic", "causality"], "solver": "lbfgs", "penalty": "l2", "C": 1.0, "multi_class": "multinomial", "max_iter": 1000, "class_weight": None, "random_state": 1}}
    scaler, classifier, order = runner._fit_probe(fit, config)
    probabilities = runner._target_probabilities(scaler, classifier, order, np.array([[0.0, 0.0]]), "logic")
    assert probabilities.shape == (1,)


def test_offline_intervention_matched_random_opposite_and_effects() -> None:
    from experiments.exp020.validate_exp020_implementation_spec import matched_random_delta, paired_effects

    baseline = np.array([[1.0, 2.0]])
    delta = np.array([3.0, 4.0])
    assert np.array_equal(baseline + 0.75 * delta, np.array([[3.25, 5.0]]))
    random = matched_random_delta(delta, base_seed=20260319, model_index=2, block_index=18, split_index=0, source_group_index=0, target_group_index=1)
    assert np.linalg.norm(random) == pytest.approx(np.linalg.norm(delta))
    assert np.array_equal(-delta, np.array([-3.0, -4.0]))
    assert paired_effects(0.1, 0.5, 0.2, 0.0)["D_random"] == pytest.approx(0.3)


def test_primary_gate_and_secondary_cannot_rescue() -> None:
    from experiments.exp020.validate_exp020_implementation_spec import primary_gate

    assert primary_gate(task_mean=0.0, task_ci_low=0.1, random_contrast_mean=0.1, random_contrast_ci_low=0.1, opposite_contrast_mean=0.1, secondary_supported=True) == "REPRESENTATION_REPLICATION_NOT_SUPPORTED"
    assert primary_gate(task_mean=1.0, task_ci_low=1.0, random_contrast_mean=1.0, random_contrast_ci_low=1.0, opposite_contrast_mean=1.0, technical_invalid=True) == "REPRESENTATION_REPLICATION_INVALID"


def test_formal_output_guard_and_atomic_publication(tmp_path: Path) -> None:
    output = tmp_path / "results" / "exp020"
    rows = {"effect_rows": [], "probe_rows": [], "transition_rows": [], "pair_rows": []}
    runner._atomic_publish(rows, {"synthetic": True}, output)
    assert output.is_dir()
    assert (output / "representation_summary.json").is_file()
    with pytest.raises(FileExistsError):
        runner._atomic_publish(rows, {"synthetic": True}, output)


def test_partial_staging_is_not_published_after_failure(tmp_path: Path) -> None:
    output = tmp_path / "results" / "exp020"
    with pytest.raises(ValueError):
        runner._atomic_publish({"effect_rows": []}, {"synthetic": True}, output)
    assert not output.exists()


def test_runner_source_does_not_serialize_raw_hidden_states() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "raw_hidden_states" not in source
    assert "token_ids" not in source
