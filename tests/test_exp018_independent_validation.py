"""Synthetic leakage and control tests for the EXP-018 runner."""

from __future__ import annotations

import copy

import numpy as np
import pytest

from experiments.exp018.independent_validation import (
    INVARIANT_FIELDS,
    PAIR_SUMMARY_FIELDS,
    PROBE_FIELDS,
    TRANSITION_FIELDS,
    aggregate_result_rows,
    apply_steering,
    construct_task_delta,
    evaluate_probe,
    fit_group_centroids,
    fit_linear_probe,
    load_frozen_config,
    matched_random_delta,
    opposite_delta,
    validate_split_disjointness,
)


@pytest.fixture
def config():
    return load_frozen_config()


@pytest.fixture
def fit_representations(config):
    rng = np.random.default_rng(7)
    return {
        group: rng.normal(loc=index * 4.0, scale=0.2, size=(3, 4))
        for index, group in enumerate(config["groups"])
    }


def test_fit_eval_overlap_raises(config):
    split = copy.deepcopy(config["splits"][0])
    split["evaluation_ids"]["logic"][0] = split["fit_ids"]["logic"][0]
    with pytest.raises(ValueError, match="leaks"):
        validate_split_disjointness(split, config["groups"])


def test_scaler_sees_fit_data_only(config, fit_representations):
    probe = fit_linear_probe(fit_representations, config)
    fit_matrix = np.concatenate([fit_representations[group] for group in config["groups"]])
    assert np.allclose(probe.scaler.mean_, fit_matrix.mean(axis=0))
    assert not np.allclose(probe.scaler.mean_, np.full(4, 999.0))


def test_probe_sees_fit_labels_only(config, fit_representations):
    probe = fit_linear_probe(fit_representations, config)
    assert probe.training_sample_count == 12
    assert probe.class_counts == {group: 3 for group in config["groups"]}


def test_centroids_use_fit_arrays_only(config, fit_representations):
    centroids = fit_group_centroids(fit_representations, config["groups"])
    assert np.allclose(centroids["logic"], fit_representations["logic"].mean(axis=0))
    assert not np.allclose(centroids["logic"], np.full(4, 999.0))


def test_task_delta_equals_target_minus_source_centroid(config, fit_representations):
    centroids = fit_group_centroids(fit_representations, config["groups"])
    delta = construct_task_delta(centroids, "logic", "causality")
    assert np.array_equal(delta, centroids["causality"] - centroids["logic"])


def test_opposite_delta_is_exact_negative():
    task = np.array([1.0, -2.0, 3.0])
    assert np.array_equal(opposite_delta(task), -task)


def test_random_delta_norm_matches_task_delta(config, fit_representations):
    centroids = fit_group_centroids(fit_representations, config["groups"])
    task = construct_task_delta(centroids, "logic", "causality")
    random = matched_random_delta(task, config, 0, 16, 0, "logic", "causality")
    assert np.isclose(np.linalg.norm(random), np.linalg.norm(task))


def test_random_direction_reused_across_betas(config, fit_representations):
    centroids = fit_group_centroids(fit_representations, config["groups"])
    task = construct_task_delta(centroids, "logic", "causality")
    first = matched_random_delta(task, config, 0, 16, 0, "logic", "causality")
    second = matched_random_delta(task, config, 0, 16, 0, "logic", "causality")
    assert np.array_equal(first, second)


def test_random_direction_changes_deterministically_by_transition_key(config, fit_representations):
    centroids = fit_group_centroids(fit_representations, config["groups"])
    task = construct_task_delta(centroids, "logic", "causality")
    first = matched_random_delta(task, config, 0, 16, 0, "logic", "causality")
    second = matched_random_delta(task, config, 0, 16, 0, "causality", "logic")
    assert not np.array_equal(first, second)


def test_held_out_arrays_are_not_mutated_in_place():
    held_out = np.arange(12.0).reshape(3, 4)
    original = held_out.copy()
    steered = apply_steering(held_out, np.ones(4), 0.75)
    assert np.array_equal(held_out, original)
    assert not np.shares_memory(held_out, steered)


def test_probe_is_fit_once_and_reused_after_steering(config, fit_representations):
    probe = fit_linear_probe(fit_representations, config)
    classifier_id = id(probe.classifier)
    held_out = fit_representations["logic"] + 0.5
    baseline = evaluate_probe(probe, held_out, "logic", "causality")
    steered = evaluate_probe(probe, apply_steering(held_out, np.ones(4), 0.5), "logic", "causality")
    assert id(probe.classifier) == classifier_id
    assert set(baseline) == set(PROBE_FIELDS[8:])
    assert set(steered) == set(PROBE_FIELDS[8:])


def test_output_metric_schemas_are_stable():
    for fields in (TRANSITION_FIELDS, PROBE_FIELDS, INVARIANT_FIELDS, PAIR_SUMMARY_FIELDS):
        row = {field: 0 for field in fields}
        assert aggregate_result_rows(fields, [row]) == [row]
        bad = dict(row)
        bad.pop(fields[-1])
        with pytest.raises(ValueError, match="schema"):
            aggregate_result_rows(fields, [bad])
