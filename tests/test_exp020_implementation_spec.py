"""Synthetic-only tests for Task 081A implementation-spec helpers."""

from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path

import numpy as np
import pytest


MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "exp020" / "validate_exp020_implementation_spec.py"
SPEC = importlib.util.spec_from_file_location("exp020_spec_validator", MODULE_PATH)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def test_matched_random_is_deterministic_and_norm_matched() -> None:
    task = np.array([3.0, -4.0, 2.0])
    first = validator.matched_random_delta(task, base_seed=20260319, model_index=2, block_index=18, split_index=0, source_group_index=1, target_group_index=3)
    second = validator.matched_random_delta(task, base_seed=20260319, model_index=2, block_index=18, split_index=0, source_group_index=1, target_group_index=3)
    assert np.array_equal(first, second)
    assert np.linalg.norm(first) == pytest.approx(np.linalg.norm(task))


def test_matched_random_seed_scope_changes_with_transition_key() -> None:
    task = np.array([1.0, 2.0, 3.0])
    first = validator.matched_random_delta(task, base_seed=20260319, model_index=2, block_index=18, split_index=0, source_group_index=0, target_group_index=1)
    changed = validator.matched_random_delta(task, base_seed=20260319, model_index=2, block_index=18, split_index=0, source_group_index=1, target_group_index=0)
    assert not np.array_equal(first, changed)


def test_probability_mapping_does_not_assume_column_order() -> None:
    scientific = ["logic", "causality", "analogy", "definition"]
    classes = np.array([2, 0, 3, 1])
    assert validator.probability_column_index(classes, scientific, "logic") == 1
    assert validator.probability_column_index(classes, scientific, "definition") == 2


def test_probability_mapping_covers_all_classes_and_rejects_missing_or_unknown() -> None:
    scientific = ["logic", "causality", "analogy", "definition"]
    classes = np.array([3, 1, 0, 2])
    assert [validator.probability_column_index(classes, scientific, label) for label in scientific] == [2, 1, 3, 0]
    with pytest.raises(ValueError, match="missing"):
        validator.probability_column_index(np.array([0, 1, 2]), scientific, "definition")
    with pytest.raises(ValueError, match="Unknown"):
        validator.probability_column_index(classes, scientific, "unknown")


def test_paired_effects_use_same_item_baseline() -> None:
    effects = validator.paired_effects(0.10, 0.75, 0.30, 0.05)
    assert effects == pytest.approx({"task_effect": 0.65, "random_effect": 0.20, "opposite_effect": -0.05, "D_random": 0.45, "D_opposite": 0.70})


def test_primary_gate_supports_all_requirements_only() -> None:
    assert validator.primary_gate(task_mean=0.2, task_ci_low=0.01, random_contrast_mean=0.1, random_contrast_ci_low=0.01, opposite_contrast_mean=0.1) == "REPRESENTATION_REPLICATION_SUPPORTED"
    for changed in ("task_mean", "task_ci_low", "random_contrast_mean", "random_contrast_ci_low", "opposite_contrast_mean"):
        values = {"task_mean": 0.2, "task_ci_low": 0.01, "random_contrast_mean": 0.1, "random_contrast_ci_low": 0.01, "opposite_contrast_mean": 0.1}
        values[changed] = 0.0
        assert validator.primary_gate(**values) == "REPRESENTATION_REPLICATION_NOT_SUPPORTED"


def test_secondary_cannot_rescue_primary_failure() -> None:
    assert validator.primary_gate(task_mean=0.0, task_ci_low=0.1, random_contrast_mean=0.1, random_contrast_ci_low=0.1, opposite_contrast_mean=0.1, secondary_supported=True) == "REPRESENTATION_REPLICATION_NOT_SUPPORTED"


def test_technical_invalidity_is_distinct() -> None:
    assert validator.primary_gate(task_mean=1.0, task_ci_low=1.0, random_contrast_mean=1.0, random_contrast_ci_low=1.0, opposite_contrast_mean=1.0, technical_invalid=True) == "REPRESENTATION_REPLICATION_INVALID"


def test_formal_output_guard_is_scoped_to_temporary_root(tmp_path: Path) -> None:
    result = tmp_path / "results" / "exp020" / "probe_metrics.csv"
    result.parent.mkdir(parents=True)
    result.write_text("synthetic only", encoding="utf-8")
    assert validator._formal_result_paths(tmp_path) == [result]


def _spec_with_semantics(semantics: dict, *, primary: bool, secondary: bool, full: bool, unresolved_primary: list[str], unresolved_secondary: list[str]) -> dict:
    return {
        "semantic_rules": semantics,
        "unresolved_primary_critical": unresolved_primary,
        "unresolved_secondary": unresolved_secondary,
        "PRIMARY_READY": primary,
        "SECONDARY_READY": secondary,
        "FULL_READY": full,
    }


def test_fail_open_regression_rejects_tag_omitted_from_top_level_list() -> None:
    spec = _spec_with_semantics({"tokenizer": {"value": None, "provenance_tag": "UNRESOLVED_PRIMARY_CRITICAL"}}, primary=False, secondary=True, full=False, unresolved_primary=[], unresolved_secondary=[])
    assert validator.validate_readiness_fields(spec)


def test_fail_open_regression_rejects_orphan_top_level_unresolved_key() -> None:
    spec = _spec_with_semantics({}, primary=False, secondary=True, full=False, unresolved_primary=["ghost"], unresolved_secondary=[])
    assert validator.validate_readiness_fields(spec)


def test_fail_open_regression_rejects_manual_primary_ready_with_unresolved_tag() -> None:
    spec = _spec_with_semantics({"bootstrap": {"value": None, "provenance_tag": "UNRESOLVED_PRIMARY_CRITICAL"}}, primary=True, secondary=True, full=True, unresolved_primary=["bootstrap"], unresolved_secondary=[])
    assert validator.validate_readiness_fields(spec)


def test_fail_open_regression_rejects_removed_list_when_component_tag_remains() -> None:
    spec = _spec_with_semantics({"statistics": {"value": None, "provenance_tag": "UNRESOLVED_PRIMARY_CRITICAL", "unresolved_components": ["ci_method"]}}, primary=False, secondary=True, full=False, unresolved_primary=[], unresolved_secondary=[])
    assert validator.validate_readiness_fields(spec)


def test_fail_open_regression_rejects_inconsistent_ready_combination() -> None:
    spec = _spec_with_semantics({}, primary=True, secondary=False, full=True, unresolved_primary=[], unresolved_secondary=[])
    assert validator.validate_readiness_fields(spec)


def _synthetic_manifest() -> dict:
    groups = ["logic", "causality", "analogy", "definition"]
    transitions = [[source, target] for source in groups for target in groups if source != target]
    return {
        "groups": groups,
        "ordered_transitions": transitions,
        "splits": [
            {"id": "split_a", "split_index": 0, "evaluation_ids": {group: [f"a_{group}_{index}" for index in range(3)] for group in groups}},
            {"id": "split_b", "split_index": 1, "evaluation_ids": {group: [f"b_{group}_{index}" for index in range(3)] for group in groups}},
        ],
    }


def _synthetic_clusters(manifest: dict | None = None, *, reverse_splits: bool = False, shuffle_rows: bool = False) -> dict:
    manifest = manifest or _synthetic_manifest()
    canonical = validator.canonical_manifest(manifest)
    result: dict = {}
    for item in canonical:
        result.setdefault(item["split_id"], {})[item["held_out_source_item_id"]] = [
            {
                "split_id": item["split_id"], "held_out_source_item_id": item["held_out_source_item_id"],
                "source_group": item["source_group"], "target_group": target,
                "task_effect": float(item["split_index"] + target_index + len(item["held_out_source_item_id"])),
                "D_random": float(target_index - item["split_index"]), "D_opposite": float(2 - target_index),
            }
            for target_index, target in enumerate(item["target_groups"])
        ]
    if shuffle_rows:
        for split in result.values():
            for rows in split.values():
                rows.reverse()
    if reverse_splits:
        return dict(reversed(list(result.items())))
    return result


def _valid_semantic_spec() -> dict:
    rules = {
        name: {"value": "synthetic", "status": "RESOLVED", "value_classification": classification, "provenance_tag": tag}
        for name, (classification, tag) in validator.REQUIRED_RULE_CLASSIFICATIONS.items()
    }
    return {
        "semantic_rule_registry": {"schema_version": validator.SEMANTIC_RULE_SCHEMA_VERSION, "required_rules": list(validator.REQUIRED_SEMANTIC_RULES)},
        "semantic_rules": rules,
    }


@pytest.mark.parametrize("rule_name", validator.REQUIRED_SEMANTIC_RULES)
def test_required_rule_deletion_is_rejected(rule_name: str) -> None:
    spec = _valid_semantic_spec()
    del spec["semantic_rules"][rule_name]
    assert validator.validate_semantic_rule_registry(spec)


def test_registry_rejects_unknown_renamed_version_and_order_errors() -> None:
    spec = _valid_semantic_spec()
    spec["semantic_rules"]["unknown"] = {"value": "x", "status": "RESOLVED"}
    assert validator.validate_semantic_rule_registry(spec)
    spec = _valid_semantic_spec()
    spec["semantic_rule_registry"]["schema_version"] = "2.0.0"
    assert validator.validate_semantic_rule_registry(spec)
    spec = _valid_semantic_spec()
    spec["semantic_rule_registry"]["required_rules"].reverse()
    assert validator.validate_semantic_rule_registry(spec)
    spec = _valid_semantic_spec()
    spec["semantic_rule_registry"]["required_rules"].pop()
    assert validator.validate_semantic_rule_registry(spec)


def test_registry_rejects_empty_unresolved_or_bad_provenance_rule() -> None:
    for mutation in ("empty", "status", "classification", "provenance"):
        spec = _valid_semantic_spec()
        rule = spec["semantic_rules"]["representation"]
        if mutation == "empty":
            rule["value"] = ""
        elif mutation == "status":
            rule["status"] = "UNRESOLVED"
        elif mutation == "classification":
            rule["value_classification"] = "WRONG"
        else:
            rule["provenance_tag"] = "WRONG"
        assert validator.validate_semantic_rule_registry(spec)


def test_cluster_plan_preserves_clusters_strata_and_shared_outcome_plan() -> None:
    manifest = _synthetic_manifest()
    clusters = _synthetic_clusters(manifest)
    plan = validator.cluster_resample_plan(clusters, manifest, seed=20260812, resamples=1)[0]
    assert list(plan) == ["split_a", "split_b"]
    assert all(len(indices) == 12 for indices in plan.values())
    rows = validator.sampled_transition_rows(clusters, manifest, plan)
    assert len(rows) == 72
    for split_id, indices in plan.items():
        for index in set(indices):
            expected = 3 * indices.count(index)
            source_id = validator.canonical_manifest(manifest)[index if split_id == "split_a" else 12 + index]["held_out_source_item_id"]
            observed = sum(row["held_out_source_item_id"] == source_id for row in rows)
            assert observed == expected
    output = validator.bootstrap_cluster_statistics(clusters, manifest, seed=20260812, resamples=2)
    assert len(output["plan"]) == 2
    assert set(output["means"]) == {"task_effect", "D_random", "D_opposite"}


def test_cluster_bootstrap_is_explicit_pcg64_deterministic_and_linear_percentile() -> None:
    manifest = _synthetic_manifest()
    clusters = _synthetic_clusters(manifest)
    first = validator.bootstrap_cluster_statistics(clusters, manifest, seed=20260812, resamples=9)
    second = validator.bootstrap_cluster_statistics(clusters, manifest, seed=20260812, resamples=9)
    assert first["plan"] == second["plan"]
    assert np.array_equal(first["means"]["task_effect"], second["means"]["task_effect"])
    assert np.array_equal(first["ci"]["task_effect"], np.quantile(first["means"]["task_effect"], [0.025, 0.975], method="linear"))
    source = inspect.getsource(validator.cluster_resample_plan)
    assert "PCG64" in source
    source = inspect.getsource(validator.bootstrap_cluster_statistics)
    assert 'method="linear"' in source


def test_descriptive_statistics_use_sample_sd_and_strict_positive_rule() -> None:
    stats = validator.descriptive_statistics([0.0, 1.0, 2.0])
    assert stats["standard_deviation"] == pytest.approx(1.0)
    assert stats["proportion_positive"] == pytest.approx(2 / 3)
    identical = validator.descriptive_statistics([4.0, 4.0, 4.0])
    assert identical["standard_deviation"] == 0.0
    manifest = _synthetic_manifest()
    clusters = _synthetic_clusters(manifest)
    for split in clusters.values():
        for cluster in split.values():
            for row in cluster:
                row["task_effect"] = 4.0
    result = validator.bootstrap_cluster_statistics(clusters, manifest, resamples=3)
    assert np.array_equal(result["ci"]["task_effect"], np.array([4.0, 4.0]))


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_technical_invalidity_rejects_nonfinite_observations(bad: float) -> None:
    manifest = _synthetic_manifest()
    clusters = _synthetic_clusters(manifest)
    first_id = next(iter(clusters["split_a"]))
    clusters["split_a"][first_id][0]["task_effect"] = bad
    with pytest.raises(ValueError, match="Nonfinite"):
        validator.bootstrap_cluster_statistics(clusters, manifest, resamples=1)


def test_technical_invalidity_rejects_bad_cluster_structure() -> None:
    manifest = _synthetic_manifest()
    clusters = _synthetic_clusters(manifest)
    clusters["split_a"].pop(next(iter(clusters["split_a"])))
    with pytest.raises(ValueError, match="exactly match"):
        validator.cluster_resample_plan(clusters, manifest, seed=1, resamples=1)
    clusters = _synthetic_clusters(manifest)
    first_id = next(iter(clusters["split_a"]))
    clusters["split_a"][first_id].pop()
    with pytest.raises(ValueError, match="three transition"):
        validator.cluster_resample_plan(clusters, manifest, seed=1, resamples=1)
    clusters = _synthetic_clusters(manifest)
    for cluster in clusters["split_a"].values():
        for row in cluster:
            row["held_out_source_item_id"] = "same"
    with pytest.raises(ValueError, match="Cluster key"):
        validator.cluster_resample_plan(clusters, manifest, seed=1, resamples=1)


def test_bootstrap_is_invariant_to_reversed_and_shuffled_containers() -> None:
    manifest = _synthetic_manifest()
    canonical = _synthetic_clusters(manifest)
    reversed_containers = _synthetic_clusters(manifest, reverse_splits=True, shuffle_rows=True)
    first = validator.bootstrap_cluster_statistics(canonical, manifest, resamples=7)
    second = validator.bootstrap_cluster_statistics(reversed_containers, manifest, resamples=7)
    assert first["plan"] == second["plan"]
    for outcome in first["means"]:
        assert np.array_equal(first["means"][outcome], second["means"][outcome])
        assert np.array_equal(first["ci"][outcome], second["ci"][outcome])


def test_manifest_order_rejects_wrong_outer_split_extra_id_and_bad_transition() -> None:
    manifest = _synthetic_manifest()
    clusters = _synthetic_clusters(manifest)
    first_id = next(iter(clusters["split_a"]))
    clusters["split_a"][first_id][0]["split_id"] = "split_b"
    with pytest.raises(ValueError, match="Outer split"):
        validator.cluster_resample_plan(clusters, manifest, seed=1, resamples=1)
    clusters = _synthetic_clusters(manifest)
    rows = clusters["split_a"].pop(first_id)
    clusters["split_a"]["extra"] = rows
    for row in rows:
        row["held_out_source_item_id"] = "extra"
    with pytest.raises(ValueError, match="exactly match"):
        validator.cluster_resample_plan(clusters, manifest, seed=1, resamples=1)
    clusters = _synthetic_clusters(manifest)
    clusters["split_a"][first_id][0]["target_group"] = "logic"
    with pytest.raises(ValueError, match="target transitions"):
        validator.cluster_resample_plan(clusters, manifest, seed=1, resamples=1)
