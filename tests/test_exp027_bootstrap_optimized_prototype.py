import copy
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP026_DIR = ROOT / "experiments" / "exp026"
EXP027_ENG = ROOT / "experiments" / "exp027" / "engineering"
for path in (str(ROOT), str(EXP026_DIR), str(EXP027_ENG)):
    if path not in sys.path:
        sys.path.insert(0, path)

import run_exp026 as runner
import exp027_bootstrap_optimized_prototype as proto


def _new_rng(seed):
    return np.random.default_rng(np.random.PCG64(seed))


def _hardcoded_a():
    return runner._hardcoded_synthetic_observations()["A"]


def _hardcoded_b():
    return runner._hardcoded_synthetic_observations()["B"]


def _reference_bootstrap(observations, num_layers, replicates, seed):
    rng = _new_rng(seed)
    profile = runner.compute_matrix_profile(
        observations,
        num_layers=num_layers,
        condition_order=runner.CONDITION_ORDER,
        bootstrap_replicates=replicates,
        rng=rng,
    )
    return profile, rng


def _optimized_bootstrap(observations, num_layers, replicates, seed):
    rng = _new_rng(seed)
    bootstrap = proto.optimized_matrix_bootstrap(
        observations,
        num_layers,
        runner.CONDITION_ORDER,
        replicates,
        rng,
    )
    return bootstrap, rng


def _bootstrap_ci_equal(left, right):
    return (
        np.array_equal(left["distance_association_ci"], right["distance_association_ci"], equal_nan=True)
        and np.array_equal(left["sdi_ci"], right["sdi_ci"], equal_nan=True)
        and np.array_equal(left["low_d_recovery_ci"], right["low_d_recovery_ci"], equal_nan=True)
        and left["replicates"] == right["replicates"]
    )


@pytest.mark.parametrize("model_key,num_layers,seed,replicates", [
    ("A", 4, 20260819, 25),
    ("A", 4, 12345, 40),
    ("B", 3, 7, 30),
])
def test_registered_bootstrap_ci_equivalence(model_key, num_layers, seed, replicates):
    observations = runner._hardcoded_synthetic_observations()[model_key]
    reference, _ = _reference_bootstrap(observations, num_layers, replicates, seed)
    optimized, _ = _optimized_bootstrap(observations, num_layers, replicates, seed)
    assert reference["bootstrap"] is not None
    assert optimized is not None
    assert _bootstrap_ci_equal(reference["bootstrap"], optimized)


@pytest.mark.parametrize("model_key,num_layers,seed,replicates", [
    ("A", 4, 20260819, 25),
    ("B", 3, 99, 30),
])
def test_draw_sequence_rng_consumption_is_identical(model_key, num_layers, seed, replicates):
    observations = runner._hardcoded_synthetic_observations()[model_key]
    _, reference_rng = _reference_bootstrap(observations, num_layers, replicates, seed)
    _, optimized_rng = _optimized_bootstrap(observations, num_layers, replicates, seed)
    assert reference_rng.bit_generator.state == optimized_rng.bit_generator.state


@pytest.mark.parametrize("model_key,num_layers,seed,replicates", [
    ("A", 4, 20260819, 25),
    ("B", 3, 77, 30),
])
def test_support_classification_equivalence(model_key, num_layers, seed, replicates):
    observations = runner._hardcoded_synthetic_observations()[model_key]
    reference, _ = _reference_bootstrap(observations, num_layers, replicates, seed)
    optimized, _ = _optimized_bootstrap(observations, num_layers, replicates, seed)
    optimized_support = runner._support_classes(reference["point"], optimized)
    assert optimized_support == reference["support"]


def test_routing_equivalence_between_reference_and_optimized_bootstraps():
    seed = 20260819
    reps = 25
    ref_a, _ = _reference_bootstrap(_hardcoded_a(), 4, reps, seed)
    ref_b, _ = _reference_bootstrap(_hardcoded_b(), 3, reps, seed)
    opt_a = _optimized_bootstrap(_hardcoded_a(), 4, reps, seed)[0]
    opt_b = _optimized_bootstrap(_hardcoded_b(), 3, reps, seed)[0]

    ref_summary_a = copy.deepcopy(ref_a)
    ref_summary_b = copy.deepcopy(ref_b)
    opt_summary_a = copy.deepcopy(ref_a)
    opt_summary_b = copy.deepcopy(ref_b)
    opt_summary_a["support"] = runner._support_classes(opt_summary_a["point"], opt_a)
    opt_summary_b["support"] = runner._support_classes(opt_summary_b["point"], opt_b)

    ref_route = runner.classify_route(ref_summary_a, ref_summary_b)
    opt_route = runner.classify_route(opt_summary_a, opt_summary_b)
    assert opt_route == ref_route


def test_equivalence_with_ties_and_class_imbalance_fixture():
    base = _hardcoded_a()
    imbalanced = list(base)
    # Duplicate one family cluster to create class imbalance without removing any class.
    duplicated = [copy.deepcopy(obs) for obs in base if obs.source_family_id.endswith("_0") and obs.condition_id == runner.CONDITION_ORDER[0]]
    imbalanced.extend(duplicated)
    reference, _ = _reference_bootstrap(imbalanced, 4, 30, 424242)
    optimized, _ = _optimized_bootstrap(imbalanced, 4, 30, 424242)
    assert reference["bootstrap"] is not None
    assert optimized is not None
    assert _bootstrap_ci_equal(reference["bootstrap"], optimized)