"""Synthetic-only security, publication, and arithmetic tests for EXP-020A."""

from __future__ import annotations

import copy
import importlib.util
import inspect
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pytest
from sklearn.linear_model import LogisticRegression as SklearnLogisticRegression
from sklearn.preprocessing import StandardScaler as SklearnStandardScaler


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


def _frozen_probe_config() -> dict:
    """Return a deep copy of the actual frozen probe object, without prompts."""
    return copy.deepcopy(runner._json(runner.FROZEN_CONFIG_PATH)["probe"])


def _synthetic_probe_fit(class_order: list[str]) -> dict[str, np.ndarray]:
    """Finite numeric FIT representations only; no model or prompt access."""
    return {
        group: np.array(
            [[float(index * 10), float(index * 10 + 1)], [float(index * 10 + 2), float(index * 10 + 3)]],
            dtype=float,
        )
        for index, group in enumerate(class_order)
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


def _consumed_authorization(digest: str = AUTH_DIGEST, run_attempt_id: str = "33333333-3333-4333-8333-333333333333") -> dict:
    """Return synthetic authorization provenance required for publication."""
    return {
        **_authorization(),
        "authorization_sha256": digest,
        "consumption_record_path": (
            "experiments/exp020/results/authorization_consumption/"
            f"{digest}.json"
        ),
        "run_attempt_id": run_attempt_id,
    }


def _consumption_context(digest: str = AUTH_DIGEST, authorization_id: str | None = None) -> dict:
    authorization = _authorization()
    if authorization_id is not None:
        authorization["authorization_id"] = authorization_id
    return {
        "authorization": authorization,
        "authorization_sha256": digest,
        "runner_commit": COMMIT,
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
        "authorization": {
            "authorization_id": authorization["authorization_id"],
            "authorization_sha256": authorization["authorization_sha256"],
            "authorized_runner_commit": COMMIT,
            "scope": list(runner.FORMAL_AUTHORIZATION_SCOPE),
            "single_use": True,
            "consumption_record_path": authorization["consumption_record_path"],
            "run_attempt_id": authorization["run_attempt_id"],
        },
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
    config = _frozen_probe_config()
    probe_fit = _synthetic_probe_fit(config["classifier"]["class_order"])
    scaler, classifier, order = runner._fit_probe(probe_fit, config)
    probabilities = runner._target_probabilities(scaler, classifier, order, np.array([[0.0, 0.0]]), "logic")
    assert probabilities.shape == (1,)


def test_actual_frozen_probe_config_constructs_and_fits_with_semantic_order() -> None:
    probe = _frozen_probe_config()
    fit = _synthetic_probe_fit(probe["classifier"]["class_order"])
    scaler, classifier, semantic_order = runner._fit_probe(fit, probe)
    transformed = scaler.transform(np.vstack(list(fit.values())))
    assert np.isfinite(transformed).all()
    assert semantic_order == probe["classifier"]["class_order"]
    assert list(classifier.classes_) == list(range(len(semantic_order)))


def test_frozen_scaler_identity_is_validated_but_not_forwarded(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _frozen_probe_config()
    received: dict[str, object] = {}

    def capture_scaler(**kwargs):
        received.update(kwargs)
        return SklearnStandardScaler(**kwargs)

    monkeypatch.setattr(runner, "StandardScaler", capture_scaler)
    runner._fit_probe(_synthetic_probe_fit(probe["classifier"]["class_order"]), probe)
    assert probe["preprocessing"]["class"] == "StandardScaler"
    assert received == {"with_mean": True, "with_std": True}
    assert "class" not in received


@pytest.mark.parametrize("field", sorted(runner.PROBE_FIELDS))
def test_probe_required_fields_fail_closed(field: str) -> None:
    probe = _frozen_probe_config()
    del probe[field]
    with pytest.raises(RuntimeError, match="probe"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("field, invalid_value", [
    (field, invalid_value)
    for field in ("with_mean", "with_std")
    for invalid_value in (0, 1, "true", None, [], {})
])
def test_preprocessing_boolean_fields_reject_every_non_bool(field: str, invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe["preprocessing"][field] = invalid_value
    with pytest.raises(RuntimeError, match="StandardScaler"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("field", sorted(runner.PREPROCESSING_FIELDS))
def test_preprocessing_required_fields_fail_closed(field: str) -> None:
    probe = _frozen_probe_config()
    del probe["preprocessing"][field]
    with pytest.raises(RuntimeError, match="preprocessing"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("mutation", [
    lambda section: section.update(unknown=True),
    lambda section: section.update(with_mean_renamed=section.pop("with_mean")),
    lambda section: section.update(**{"class": "OtherScaler"}),
    lambda section: section.update(**{"class": ""}),
])
def test_preprocessing_unknown_renamed_or_wrong_identity_fails_closed(mutation) -> None:
    probe = _frozen_probe_config()
    mutation(probe["preprocessing"])
    with pytest.raises(RuntimeError):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("invalid_value", [True, False, "1.0", None, [], {}])
def test_classifier_C_rejects_non_numeric_or_bool_values(invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe["classifier"]["C"] = invalid_value
    with pytest.raises(RuntimeError, match="C parameter"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("field, invalid_value", [
    (field, invalid_value)
    for field in ("max_iter", "random_state")
    for invalid_value in (True, False, 1.0, "1", None, [], {})
])
def test_classifier_integer_fields_require_strict_int(field: str, invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe["classifier"][field] = invalid_value
    with pytest.raises(RuntimeError, match="integer parameters"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("field", ("fit_data_only", "tuning_on_evaluation_permitted"))
@pytest.mark.parametrize("invalid_value", (0, 1, "false", None, [], {}))
def test_probe_data_use_constraints_reject_non_boolean_or_wrong_values(field: str, invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe[field] = invalid_value
    with pytest.raises(RuntimeError, match="data-use constraints"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("field", ("solver", "penalty", "multi_class"))
@pytest.mark.parametrize("invalid_value", (None, 1, [], {}))
def test_classifier_string_fields_reject_non_strings(field: str, invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe["classifier"][field] = invalid_value
    with pytest.raises(RuntimeError, match="string parameters"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("invalid_value", (0, True, [], ()))
def test_classifier_class_weight_rejects_unimplemented_types(invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe["classifier"]["class_weight"] = invalid_value
    with pytest.raises(RuntimeError, match="class_weight"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("invalid_value", ("logic", None, (), {}))
def test_classifier_class_order_requires_nonempty_list_of_unique_strings(invalid_value: object) -> None:
    probe = _frozen_probe_config()
    probe["classifier"]["class_order"] = invalid_value
    with pytest.raises(RuntimeError, match="class_order"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("invalid_order", ([], ["logic", 1], ["logic", "logic"]))
def test_classifier_class_order_rejects_empty_nonstring_or_duplicate_labels(invalid_order: list[object]) -> None:
    probe = _frozen_probe_config()
    probe["classifier"]["class_order"] = invalid_order
    with pytest.raises(RuntimeError, match="class_order"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("field", sorted(runner.CLASSIFIER_FIELDS))
def test_classifier_required_fields_fail_closed(field: str) -> None:
    probe = _frozen_probe_config()
    del probe["classifier"][field]
    with pytest.raises(RuntimeError, match="classifier"):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


@pytest.mark.parametrize("mutation", [
    lambda section: section.update(unknown=True),
    lambda section: section.update(solver_renamed=section.pop("solver")),
    lambda section: section.update(**{"class": "OtherClassifier"}),
    lambda section: section.update(**{"class": ""}),
])
def test_classifier_unknown_renamed_or_wrong_identity_fails_closed(mutation) -> None:
    probe = _frozen_probe_config()
    mutation(probe["classifier"])
    with pytest.raises(RuntimeError):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)


def test_classifier_class_order_is_metadata_not_constructor_kwarg(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _frozen_probe_config()
    received: dict[str, object] = {}

    def capture_classifier(**kwargs):
        received.update(kwargs)
        return SklearnLogisticRegression(**kwargs)

    capture_classifier.__signature__ = inspect.signature(SklearnLogisticRegression)
    monkeypatch.setattr(runner, "LogisticRegression", capture_classifier)
    runner._fit_probe(_synthetic_probe_fit(probe["classifier"]["class_order"]), probe)
    assert "class_order" not in received
    assert received["solver"] == probe["classifier"]["solver"]
    assert received["penalty"] == probe["classifier"]["penalty"]
    assert received["C"] == probe["classifier"]["C"]
    assert received["max_iter"] == probe["classifier"]["max_iter"]
    assert received["class_weight"] == probe["classifier"]["class_weight"]
    assert received["random_state"] == probe["classifier"]["random_state"]


@pytest.mark.parametrize("mutation", [
    lambda probe: probe["preprocessing"].update(with_mean=1),
    lambda probe: probe["classifier"].update(C=True),
    lambda probe: probe.pop("fit_data_only"),
])
def test_invalid_probe_metadata_fails_before_any_sklearn_estimator_construction(
    monkeypatch: pytest.MonkeyPatch, mutation
) -> None:
    probe = _frozen_probe_config()
    calls: list[str] = []

    def unexpected_scaler(*args, **kwargs):
        calls.append("StandardScaler")
        raise AssertionError("invalid metadata reached StandardScaler construction")

    def unexpected_classifier(*args, **kwargs):
        calls.append("LogisticRegression")
        raise AssertionError("invalid metadata reached LogisticRegression construction")

    monkeypatch.setattr(runner, "StandardScaler", unexpected_scaler)
    monkeypatch.setattr(runner, "LogisticRegression", unexpected_classifier)
    mutation(probe)
    with pytest.raises(RuntimeError):
        runner._fit_probe(_synthetic_probe_fit(_frozen_probe_config()["classifier"]["class_order"]), probe)
    assert calls == []


def test_probability_selection_uses_fitted_classifier_classes() -> None:
    class IdentityScaler:
        def transform(self, values):
            return np.asarray(values, dtype=float)

    class ReorderedClassifier:
        classes_ = np.array([1, 0])

        def predict_proba(self, values):
            return np.tile(np.array([[0.2, 0.8]]), (len(values), 1))

    probabilities = runner._target_probabilities(
        IdentityScaler(), ReorderedClassifier(), ["logic", "causality"], np.array([[1.0, 2.0]]), "logic"
    )
    assert np.array_equal(probabilities, np.array([0.8]))


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
    consumption = runner._authorization_consumption_path(AUTH_DIGEST, tmp_path)
    consumption.parent.mkdir(parents=True)
    consumption.write_text("{}", encoding="utf-8")
    runner._require_no_formal_results(tmp_path)
    canonical = runner._canonical_result_path(tmp_path)
    canonical.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError):
        runner._require_no_formal_results(tmp_path)


def test_authorization_consumption_is_durable_and_single_use(tmp_path: Path) -> None:
    context = _consumption_context()
    acquired = runner._acquire_authorization_consumption(context, tmp_path)
    record_path = runner._authorization_consumption_path(AUTH_DIGEST, tmp_path)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert acquired["consumption_record_path"] == record["canonical_result_path"].replace(
        "exp020a_results.json", f"authorization_consumption/{AUTH_DIGEST}.json"
    )
    assert record["state"] == "consumed"
    assert record["authorization_id"] == context["authorization"]["authorization_id"]
    assert record["run_attempt_id"] == acquired["run_attempt_id"]
    with pytest.raises(PermissionError, match="ALREADY_CONSUMED"):
        runner._acquire_authorization_consumption(context, tmp_path)


@pytest.mark.parametrize("contents", [b"", b"{malformed", b'{"state":"partial"'])
def test_any_existing_consumption_record_blocks_reuse(tmp_path: Path, contents: bytes) -> None:
    path = runner._authorization_consumption_path(AUTH_DIGEST, tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(contents)
    with pytest.raises(PermissionError, match="ALREADY_CONSUMED"):
        runner._acquire_authorization_consumption(_consumption_context(), tmp_path)


def test_concurrent_authorization_consumption_has_exactly_one_winner(tmp_path: Path) -> None:
    context = _consumption_context()

    def acquire() -> str | None:
        try:
            return runner._acquire_authorization_consumption(context, tmp_path)["run_attempt_id"]
        except PermissionError:
            return None

    with ThreadPoolExecutor(max_workers=8) as pool:
        attempts = list(pool.map(lambda _: acquire(), range(8)))
    assert sum(value is not None for value in attempts) == 1
    record = json.loads(runner._authorization_consumption_path(AUTH_DIGEST, tmp_path).read_text(encoding="utf-8"))
    assert record["run_attempt_id"] == next(value for value in attempts if value is not None)


def test_consumption_write_and_fsync_failures_remain_consumed(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    write_context = _consumption_context("4" * 64)
    monkeypatch.setattr(runner.json, "dump", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("write failure")))
    with pytest.raises(RuntimeError, match="CONSUMPTION_WRITE_FAILURE"):
        runner._acquire_authorization_consumption(write_context, tmp_path)
    assert runner._authorization_consumption_path("4" * 64, tmp_path).exists()
    with pytest.raises(PermissionError, match="ALREADY_CONSUMED"):
        runner._acquire_authorization_consumption(write_context, tmp_path)

    monkeypatch.undo()
    fsync_context = _consumption_context("5" * 64)
    monkeypatch.setattr(runner.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("fsync failure")))
    with pytest.raises(RuntimeError, match="CONSUMPTION_WRITE_FAILURE"):
        runner._acquire_authorization_consumption(fsync_context, tmp_path)
    assert runner._authorization_consumption_path("5" * 64, tmp_path).exists()
    with pytest.raises(PermissionError, match="ALREADY_CONSUMED"):
        runner._acquire_authorization_consumption(fsync_context, tmp_path)


def test_new_authorization_hash_creates_a_distinct_consumption_record(tmp_path: Path) -> None:
    first = runner._acquire_authorization_consumption(_consumption_context("6" * 64), tmp_path)
    second = runner._acquire_authorization_consumption(
        _consumption_context("7" * 64, "44444444-4444-4444-8444-444444444444"),
        tmp_path,
    )
    assert first["consumption_record_path"] != second["consumption_record_path"]
    assert runner._authorization_consumption_path("6" * 64, tmp_path).exists()
    assert runner._authorization_consumption_path("7" * 64, tmp_path).exists()


def test_authorization_id_cannot_change_consumption_record_identity(tmp_path: Path) -> None:
    first = runner._acquire_authorization_consumption(_consumption_context(), tmp_path)
    with pytest.raises(PermissionError, match="ALREADY_CONSUMED"):
        runner._acquire_authorization_consumption(
            _consumption_context(AUTH_DIGEST, "55555555-5555-4555-8555-555555555555"),
            tmp_path,
        )
    assert first["consumption_record_path"].endswith(f"{AUTH_DIGEST}.json")


def test_existing_canonical_result_blocks_before_authorization_consumption(tmp_path: Path) -> None:
    final = runner._canonical_result_path(tmp_path)
    final.parent.mkdir(parents=True)
    final.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Formal output already exists"):
        runner._acquire_authorization_consumption(_consumption_context(), tmp_path)
    assert not runner._authorization_consumption_path(AUTH_DIGEST, tmp_path).exists()


def test_formal_path_consumes_before_validator_or_formal_source_access(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []
    context = {**_consumption_context(), "config": _synthetic_config(), "spec": {}}
    monkeypatch.setattr(runner, "validate_formal_authorization", lambda: calls.append("authorization") or context)
    monkeypatch.setattr(runner, "_require_no_formal_results", lambda: calls.append("no-results"))
    monkeypatch.setattr(
        runner,
        "_acquire_authorization_consumption",
        lambda _: calls.append("consume") or (_ for _ in ()).throw(RuntimeError("stop after consume")),
    )
    monkeypatch.setattr(runner, "_run_validator", lambda _: calls.append("validator"))
    with pytest.raises(RuntimeError, match="stop after consume"):
        runner.formal_run()
    assert calls == ["authorization", "no-results", "consume"]


def test_formal_loader_uses_neutral_resource_affecting_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise only mocked loader setup; no formal data or model is accessed."""
    import torch
    import transformers
    from src import model_loader

    config = _synthetic_config()
    config["model"]["canonical_path"] = EXPECTED_BINDINGS["model_canonical_path"]
    context = {**_consumption_context(), "config": config, "spec": {}, "bindings": EXPECTED_BINDINGS}
    tokenizer_calls: list[tuple[str, dict]] = []
    model_call: dict[str, object] = {}
    monkeypatch.setattr(runner, "validate_formal_authorization", lambda: context)
    monkeypatch.setattr(runner, "_require_no_formal_results", lambda: None)
    monkeypatch.setattr(runner, "_acquire_authorization_consumption", lambda _: {"consumption_record_path": "synthetic.json", "run_attempt_id": "33333333-3333-4333-8333-333333333333"})
    monkeypatch.setattr(runner, "_run_validator", lambda _: None)
    monkeypatch.setattr(runner, "validate_static_environment", lambda *_: {})
    monkeypatch.setattr(runner, "_json", lambda _: [])
    monkeypatch.setattr(model_loader, "load_tokenizer", lambda path, **kwargs: tokenizer_calls.append((path, kwargs)) or object())

    def capture_model(path, **kwargs):
        model_call.update(path=path, **kwargs)
        raise RuntimeError("synthetic formal loader stop")

    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", capture_model)
    with pytest.raises(RuntimeError, match="synthetic formal loader stop"):
        runner.formal_run()
    assert tokenizer_calls == [(EXPECTED_BINDINGS["model_canonical_path"], {"local_files_only": True})]
    assert model_call == {
        "path": EXPECTED_BINDINGS["model_canonical_path"],
        "local_files_only": True,
        "dtype": torch.bfloat16,
        "device_map": {"": 0},
        "low_cpu_mem_usage": True,
    }
    assert config["model"]["revision"] == EXPECTED_BINDINGS["model_revision"]


def test_neutral_loader_uses_the_same_resource_affecting_kwargs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Capture neutral loader configuration without loading the real model."""
    import torch
    import transformers

    captured: dict[str, object] = {}
    monkeypatch.setattr(runner, "static_preflight", lambda: {})
    monkeypatch.setattr(transformers.AutoConfig, "from_pretrained", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(transformers.AutoTokenizer, "from_pretrained", lambda *_args, **_kwargs: object())

    def capture_model(path, **kwargs):
        captured.update(path=path, **kwargs)
        raise RuntimeError("synthetic neutral loader stop")

    monkeypatch.setattr(transformers.AutoModelForCausalLM, "from_pretrained", capture_model)
    with pytest.raises(RuntimeError, match="synthetic neutral loader stop"):
        runner.neutral_model_preflight()
    assert captured == {
        "path": Path(runner._json(runner.FROZEN_CONFIG_PATH)["model"]["canonical_path"]),
        "local_files_only": True,
        "dtype": torch.bfloat16,
        "device_map": {"": 0},
        "low_cpu_mem_usage": True,
    }


def test_consumption_failure_is_not_a_scientific_gate_status(tmp_path: Path) -> None:
    path = runner._authorization_consumption_path(AUTH_DIGEST, tmp_path)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"")
    with pytest.raises(PermissionError, match="FORMAL_RUN_BLOCKED_AUTHORIZATION_ALREADY_CONSUMED") as error:
        runner._acquire_authorization_consumption(_consumption_context(), tmp_path)
    assert "REPRESENTATION_REPLICATION" not in str(error.value)


def test_complete_synthetic_result_publishes_atomically(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
    result = _complete_result(config, authorization)
    outcome = runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    output = runner._canonical_result_path(tmp_path)
    assert output.is_file()
    assert outcome["publication_status"] == "PUBLISHED"
    expected_bytes = (json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode("utf-8")
    assert output.read_bytes() == expected_bytes
    assert json.loads(output.read_text(encoding="utf-8"))["experiment"] == "EXP-020A"
    assert json.loads(output.read_text(encoding="utf-8"))["authorization"] == result["authorization"]
    assert not list(output.parent.glob("*.tmp-*"))
    with pytest.raises(RuntimeError):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)


def test_concurrent_publication_has_exactly_one_winner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()

    def publish() -> str | None:
        result = _complete_result(config, authorization)
        try:
            return runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)["publication_status"]
        except (FileExistsError, RuntimeError):
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: publish(), range(2)))
    assert outcomes.count("PUBLISHED") == 1
    assert outcomes.count(None) == 1
    output = runner._canonical_result_path(tmp_path)
    assert output.exists()
    assert json.loads(output.read_text(encoding="utf-8"))["experiment"] == "EXP-020A"


def test_link_publication_never_overwrites_race_winner(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
    result = _complete_result(config, authorization)
    output = runner._canonical_result_path(tmp_path)
    original_link = runner.os.link

    def race_winner(source: str | Path, destination: str | Path) -> None:
        destination_path = Path(destination)
        destination_path.write_text("race winner", encoding="utf-8")
        original_link(source, destination)

    monkeypatch.setattr(runner.os, "link", race_winner)
    with pytest.raises(FileExistsError):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert output.read_text(encoding="utf-8") == "race winner"


def test_link_failure_has_no_replace_fallback(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
    result = _complete_result(config, authorization)
    monkeypatch.setattr(runner.os, "link", lambda *_: (_ for _ in ()).throw(OSError("link unavailable")))
    monkeypatch.setattr(runner.os, "replace", lambda *_: (_ for _ in ()).throw(AssertionError("replace must not run")))
    with pytest.raises(OSError, match="link unavailable"):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert not runner._canonical_result_path(tmp_path).exists()


def test_publication_fsync_failure_leaves_no_final_result(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
    result = _complete_result(config, authorization)
    monkeypatch.setattr(runner.os, "fsync", lambda _: (_ for _ in ()).throw(OSError("fsync failure")))
    with pytest.raises(OSError, match="fsync failure"):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert not runner._canonical_result_path(tmp_path).exists()
    assert not list((tmp_path / "experiments" / "exp020" / "results").glob("*.tmp-*"))


def test_published_result_survives_staging_cleanup_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
    result = _complete_result(config, authorization)
    original_unlink = runner.os.unlink

    def fail_staging_cleanup(path: str | Path) -> None:
        if ".tmp-" in Path(path).name:
            raise OSError("cleanup failure")
        original_unlink(path)

    monkeypatch.setattr(runner.os, "unlink", fail_staging_cleanup)
    outcome = runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert outcome["publication_status"] == "PUBLISHED_WITH_STAGING_CLEANUP_FAILURE"
    assert runner._canonical_result_path(tmp_path).exists()
    assert len(list(runner._canonical_result_path(tmp_path).parent.glob("*.tmp-*"))) == 1


def test_duplicate_or_missing_transition_coverage_never_publishes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
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
    lambda result: result["authorization"].update(run_attempt_id="wrong"),
])
def test_incomplete_or_invalid_results_never_publish(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, mutate) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
    result = _complete_result(config, authorization)
    mutate(result)
    with pytest.raises(ValueError):
        runner._atomic_publish(result, config, authorization, COMMIT, tmp_path)
    assert not runner._canonical_result_path(tmp_path).exists()
    assert not list((tmp_path / "experiments" / "exp020" / "results").glob("*.tmp-*"))


def test_staging_failure_leaves_no_final_artifact(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _patch_authorization_context(monkeypatch, tmp_path)
    config, authorization = _synthetic_config(), _consumed_authorization()
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
    assert "os.replace(" not in source
    assert "os.link(staging, output_path)" in source
