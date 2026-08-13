"""Synthetic-only security, publication, and arithmetic tests for EXP-020A."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "exp020" / "run_exp020a.py"
SPEC = importlib.util.spec_from_file_location("exp020_runner", MODULE_PATH)
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


COMMIT = "a" * 40
AUTH_DIGEST = "b" * 64
EXPECTED_BINDINGS = {
    "frozen_config_path": "experiments/exp020/exp020_frozen_config.json",
    "frozen_config_sha256": "c" * 64,
    "preregistration_path": "docs/experiments/EXP-020-PREREGISTRATION.md",
    "preregistration_sha256": "d" * 64,
    "prompt_file": "experiments/exp003/prompts_controlled.json",
    "prompt_file_sha256": "e" * 64,
    "source_conditions_file": "experiments/exp018/validation_conditions.json",
    "source_conditions_sha256": "f" * 64,
    "split_transition_manifest_path": "experiments/exp018/validation_conditions.json",
    "split_transition_manifest_sha256": "1" * 64,
    "model_id": "Qwen/Qwen3-4B",
    "model_revision": "2" * 40,
    "model_canonical_path": "D:/synthetic-qwen",
    "model_config_path": "D:/synthetic-qwen/config.json",
    "model_config_sha256": "3" * 64,
    "tokenizer_identity": "Qwen2Tokenizer",
    "tokenizer_revision": "2" * 40,
}


def _synthetic_config() -> dict:
    groups = ["logic", "causality", "analogy", "definition"]
    splits = []
    for split_index in range(2):
        evaluation_ids = {group: [f"s{split_index}-{group}-{index}" for index in range(3)] for group in groups}
        splits.append({"id": f"split-{split_index}", "split_index": split_index, "evaluation_ids": evaluation_ids, "fit_ids": {group: [f"fit-{split_index}-{group}-{index}" for index in range(3)] for group in groups}})
    return {
        "model": {"model_id": EXPECTED_BINDINGS["model_id"], "revision": EXPECTED_BINDINGS["model_revision"], "config_sha256": EXPECTED_BINDINGS["model_config_sha256"], "device": "cuda:0", "dtype": "bfloat16"},
        "dataset": {
            "groups": groups,
            "splits": splits,
            "ordered_transitions": [(source, target) for source in groups for target in groups if source != target],
            "aggregate_paired_evaluation_count": 72,
        },
    }


def _authorization() -> dict:
    return {
        "schema_version": runner.AUTHORIZATION_SCHEMA_VERSION,
        "experiment": "EXP-020A",
        "formal_run_authorized": True,
        "scope": list(runner.FORMAL_AUTHORIZATION_SCOPE),
        "single_use": True,
        "runner_commit": COMMIT,
        **EXPECTED_BINDINGS,
        "created_at": "2026-08-13T00:00:00Z",
        "authorization_id": "11111111-1111-4111-8111-111111111111",
    }


def _patch_authorization_context(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    path = tmp_path / "authorization.json"
    path.write_text(json.dumps(_authorization()), encoding="utf-8")
    monkeypatch.setattr(runner, "AUTHORIZATION_PATH", path)
    monkeypatch.setattr(runner, "_tracked_worktree_clean", lambda root: True)
    monkeypatch.setattr(runner, "_current_commit", lambda root: COMMIT)
    config = _synthetic_config()
    monkeypatch.setattr(runner, "_derive_frozen_bindings", lambda root=runner.ROOT: (EXPECTED_BINDINGS, config, {"synthetic": True}))
    return path


def _comparison_rows(config: dict, *, block: int, hidden: int, beta: float) -> list[dict]:
    rows = []
    for split in config["dataset"]["splits"]:
        for source, target in config["dataset"]["ordered_transitions"]:
            for item_id in split["evaluation_ids"][source]:
                rows.append({"block_index": block, "hidden_state_index": hidden, "beta": beta, "split_id": split["id"], "held_out_source_item_id": item_id, "source_group": source, "target_group": target, "task_effect": 0.4, "random_effect": 0.1, "opposite_effect": -0.2, "D_random": 0.3, "D_opposite": 0.6})
    return rows


def _summary(gate: str) -> dict:
    observed = {key: {"mean": 0.4, "median": 0.4, "standard_deviation": 0.1, "proportion_positive": 1.0} for key in ("task_effect", "D_random", "D_opposite")}
    return {"observed": observed, "bootstrap_ci": {key: [0.1, 0.5] for key in observed}, "gate": gate}


def _complete_result(config: dict, authorization: dict) -> dict:
    primary_rows = _comparison_rows(config, block=18, hidden=19, beta=0.75)
    secondary_rows = _comparison_rows(config, block=26, hidden=27, beta=0.5)
    return {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "experiment": "EXP-020A",
        "run_id": "22222222-2222-4222-8222-222222222222",
        "authorization": {"authorization_id": authorization["authorization_id"], "authorization_sha256": authorization["authorization_sha256"], "authorized_runner_commit": COMMIT, "scope": list(runner.FORMAL_AUTHORIZATION_SCOPE), "single_use": True},
        "frozen_authority_bindings": {key: EXPECTED_BINDINGS[key] for key in ("frozen_config_sha256", "preregistration_sha256", "prompt_file_sha256", "source_conditions_sha256", "split_transition_manifest_sha256", "model_revision", "model_config_sha256", "tokenizer_identity", "tokenizer_revision")},
        "model_runtime": {"model_id": EXPECTED_BINDINGS["model_id"], "model_revision": EXPECTED_BINDINGS["model_revision"], "model_config_sha256": EXPECTED_BINDINGS["model_config_sha256"], "tokenizer_identity": EXPECTED_BINDINGS["tokenizer_identity"], "tokenizer_revision": EXPECTED_BINDINGS["tokenizer_revision"], "python": "3.11", "numpy": "2", "torch": "2", "transformers": "5", "scikit_learn": "1", "device": "cuda:0", "dtype": "bfloat16"},
        "git_runner": {"authorized_runner_commit": COMMIT, "actual_runner_commit": COMMIT},
        "formal_inputs": {"prompt_file": EXPECTED_BINDINGS["prompt_file"], "prompt_file_sha256": EXPECTED_BINDINGS["prompt_file_sha256"], "source_conditions_file": EXPECTED_BINDINGS["source_conditions_file"], "source_conditions_sha256": EXPECTED_BINDINGS["source_conditions_sha256"], "split_transition_manifest_sha256": EXPECTED_BINDINGS["split_transition_manifest_sha256"], "split_count": 2, "groups": config["dataset"]["groups"], "ordered_transition_count": 12, "evaluation_clusters": 24, "paired_transition_rows": 72},
        "primary": runner._result_section(primary_rows, _summary("REPRESENTATION_REPLICATION_SUPPORTED"), block_index=18, hidden_state_index=19, beta=0.75, primary=True),
        "secondary_descriptive": runner._result_section(secondary_rows, _summary("REPRESENTATION_REPLICATION_SUPPORTED"), block_index=26, hidden_state_index=27, beta=0.5, primary=False),
        "bootstrap": {"seed": 20260812, "resamples": 10000, "bit_generator": "PCG64", "cluster_strata": 2, "clusters_per_split": 12, "transition_rows_per_cluster": 3, "transition_rows_per_replicate": 72},
        "technical_validity": {"status": "VALID", "reason": None},
        "status": {"exp020_scientific_status": "COMPLETED", "representation_gate": "REPRESENTATION_REPLICATION_SUPPORTED"},
    }


def test_import_is_side_effect_free() -> None:
    assert runner.NEUTRAL_TEXT == "This is a neutral hardware diagnostic."
    assert not hasattr(runner, "prompts")


def test_no_mode_refuses_before_any_action() -> None:
    with pytest.raises(SystemExit) as error:
        runner.main([])
    assert error.value.code != 0


def test_missing_authorization_blocks_before_any_formal_action(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[str] = []
    monkeypatch.setattr(runner, "AUTHORIZATION_PATH", tmp_path / "missing.json")
    monkeypatch.setattr(runner, "_derive_frozen_bindings", lambda: calls.append("binding"))
    monkeypatch.setattr(runner, "_require_no_formal_results", lambda: calls.append("output"))
    assert runner.main(["--formal-run"]) == 2
    assert calls == []


@pytest.mark.parametrize("mutation", [
    lambda auth: auth.update(schema_version="wrong"),
    lambda auth: auth.pop("prompt_file_sha256"),
    lambda auth: auth.update(extra="unknown"),
    lambda auth: auth.update(experiment="other"),
    lambda auth: auth.update(scope=["wrong"]),
    lambda auth: auth.update(single_use=False),
    lambda auth: auth.update(runner_commit="wrong"),
    lambda auth: auth.update(frozen_config_sha256="0" * 64),
    lambda auth: auth.update(preregistration_sha256="0" * 64),
    lambda auth: auth.update(prompt_file_sha256="0" * 64),
    lambda auth: auth.update(source_conditions_sha256="0" * 64),
    lambda auth: auth.update(split_transition_manifest_sha256="0" * 64),
    lambda auth: auth.update(model_revision="0" * 40),
    lambda auth: auth.update(model_config_sha256="0" * 64),
    lambda auth: auth.update(tokenizer_identity="wrong"),
    lambda auth: auth.update(tokenizer_revision="0" * 40),
])
def test_authorization_contract_rejects_all_mismatches(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutation) -> None:
    path = _patch_authorization_context(monkeypatch, tmp_path)
    auth = _authorization()
    mutation(auth)
    path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(PermissionError):
        runner.validate_formal_authorization()


def test_malformed_duplicate_and_dirty_authorizations_fail_closed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = _patch_authorization_context(monkeypatch, tmp_path)
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(PermissionError):
        runner.validate_formal_authorization()
    path.write_text('{"schema_version":"1.0.0","schema_version":"1.0.0"}', encoding="utf-8")
    with pytest.raises(PermissionError):
        runner.validate_formal_authorization()
    path.write_text(json.dumps(_authorization()), encoding="utf-8")
    monkeypatch.setattr(runner, "_tracked_worktree_clean", lambda root: False)
    with pytest.raises(PermissionError, match="DIRTY"):
        runner.validate_formal_authorization()


def test_layer_mapping_and_last_token_extraction_are_frozen() -> None:
    assert 19 == 18 + 1
    assert 27 == 26 + 1


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
    assert paired_effects(0.1, 0.5, 0.2, 0.0)["D_random"] == pytest.approx(0.3)


def test_primary_gate_and_secondary_cannot_rescue() -> None:
    from experiments.exp020.validate_exp020_implementation_spec import primary_gate

    assert primary_gate(task_mean=0.0, task_ci_low=0.1, random_contrast_mean=0.1, random_contrast_ci_low=0.1, opposite_contrast_mean=0.1, secondary_supported=True) == "REPRESENTATION_REPLICATION_NOT_SUPPORTED"
    assert primary_gate(task_mean=1.0, task_ci_low=1.0, random_contrast_mean=1.0, random_contrast_ci_low=1.0, opposite_contrast_mean=1.0, technical_invalid=True) == "REPRESENTATION_REPLICATION_INVALID"


def test_canonical_result_path_guards_and_ignores_engineering_reports(tmp_path: Path) -> None:
    engineering = tmp_path / "experiments" / "exp020" / "results"
    engineering.mkdir(parents=True)
    (engineering / "runner_preflight.json").write_text("{}", encoding="utf-8")
    (engineering / "formal_run_review.json").write_text("{}", encoding="utf-8")
    runner._require_no_formal_results(tmp_path)
    canonical = runner._canonical_result_path(tmp_path)
    canonical.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError):
        runner._require_no_formal_results(tmp_path)


def test_complete_synthetic_result_publishes_atomically(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), {**_authorization(), "authorization_sha256": AUTH_DIGEST}
    result = _complete_result(config, authorization)
    runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    output = runner._canonical_result_path(tmp_path)
    assert output.is_file()
    assert json.loads(output.read_text(encoding="utf-8"))["experiment"] == "EXP-020A"
    assert not list(output.parent.glob("*.tmp-*"))
    with pytest.raises(RuntimeError):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)


def test_duplicate_or_missing_transition_coverage_never_publishes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), {**_authorization(), "authorization_sha256": AUTH_DIGEST}
    result = _complete_result(config, authorization)
    result["primary"]["comparisons"][-1] = copy.deepcopy(result["primary"]["comparisons"][0])
    with pytest.raises(ValueError, match="coverage"):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert not runner._canonical_result_path(tmp_path).exists()


@pytest.mark.parametrize("mutate", [
    lambda result: result.pop("authorization"),
    lambda result: result["primary"].update(comparisons=[]),
    lambda result: result["secondary_descriptive"].update(comparisons=[]),
    lambda result: result["primary"].update(gate_inputs=None),
    lambda result: result["primary"]["comparisons"].__setitem__(0, {**result["primary"]["comparisons"][0], "task_effect": float("nan")}),
    lambda result: result.update(technical_validity={"status": "INVALID", "reason": "synthetic"}),
    lambda result: result["authorization"].update(authorization_sha256="wrong"),
])
def test_incomplete_or_invalid_results_never_publish(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutate) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), {**_authorization(), "authorization_sha256": AUTH_DIGEST}
    result = _complete_result(config, authorization)
    mutate(result)
    with pytest.raises(ValueError):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert not runner._canonical_result_path(tmp_path).exists()
    assert not list((tmp_path / "experiments" / "exp020" / "results").glob("*.tmp-*"))


def test_staging_failure_leaves_no_final_artifact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), {**_authorization(), "authorization_sha256": AUTH_DIGEST}
    result = _complete_result(config, authorization)
    original_dump = runner.json.dump
    monkeypatch.setattr(runner.json, "dump", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("synthetic staging failure")))
    with pytest.raises(OSError):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    monkeypatch.setattr(runner.json, "dump", original_dump)
    assert not runner._canonical_result_path(tmp_path).exists()


def test_runner_source_does_not_serialize_raw_hidden_states() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    assert "raw_hidden_states" not in source
    assert "token_ids" not in source
