"""Adversarial engineering review tests for EXP-027 frozen design (Task 102C).

Synthetic/static only. No real Llama model load, no real FIT/DIAG/EVAL access,
and no scientific outcome computation. The accepted EXP-026 implementation is
the semantic oracle.
"""

from __future__ import annotations

import ast
import copy
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP026_DIR = ROOT / "experiments" / "exp026"
EXP027_DIR = ROOT / "experiments" / "exp027"
EXP027_ENG = EXP027_DIR / "engineering"
for path in (str(ROOT), str(EXP026_DIR), str(EXP027_DIR), str(EXP027_ENG)):
    if path not in sys.path:
        sys.path.insert(0, path)

import run_exp026 as ref
import validate_exp027_preregistration as val
import exp027_progress as progress

CONFIG_PATH = EXP027_DIR / "exp027_frozen_design.json"
QWEN_TUPLE = ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED")
OLMO_TUPLE = ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED")


def _config():
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def _profile(distance, dominance, low_d):
    return {
        "distance_association_status": distance,
        "dominance_status": dominance,
        "low_d_recovery_status": low_d,
    }


def _all_profiles():
    for distance in ("POSITIVE_SUPPORTED", "NOT_SUPPORTED"):
        for dominance in ("SOURCE_DOMINANT", "TARGET_DOMINANT", "NO_DOMINANCE", "NO_ROW_OR_COLUMN_VARIATION"):
            for low_d in ("SUPPORTED", "NOT_SUPPORTED", "NOT_EVALUABLE"):
                yield _profile(distance, dominance, low_d)


def _source_qualification_fixture(num_layers):
    observations = []
    for condition in ref.CONDITION_ORDER:
        for class_index, semantic_class in enumerate(ref.CLASS_ORDER):
            vectors = np.stack(
                [np.asarray([float(class_index), 0.0], dtype=np.float32) for _ in range(num_layers)],
                axis=0,
            )
            observations.append(
                ref.ExtractedObservation(
                    record_id=f"102c_{condition}_{semantic_class}",
                    partition="DIAGNOSTIC",
                    condition_id=condition,
                    semantic_class=semantic_class,
                    source_family_id=f"102c_{condition}_{semantic_class}",
                    vectors=vectors,
                )
            )
    return observations


class _EncoderFakeModel:
    def __init__(self, good_classes):
        self.good_classes = set(good_classes)

    def predict(self, X):
        out = []
        for row in X:
            cls_index = int(row[0])
            cls = ref.CLASS_ORDER[cls_index]
            out.append(cls if cls in self.good_classes else ref.CLASS_ORDER[(cls_index + 1) % len(ref.CLASS_ORDER)])
        return out


class _PermutedClassesModel:
    def __init__(self):
        self.classes_ = np.asarray(["causality", "logic", "analogy", "definition"])


def _semantic_errors(config):
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    check(config.get("experiment_id") == "EXP-027", "experiment_id")
    check(config.get("design_status") == "FROZEN_DESIGN_NOT_RUN", "design_status")

    model = config.get("third_model_identity", {})
    check(model.get("model_id") == "Meta-Llama-3.2-1B-Instruct", "third model id")
    check(model.get("model_class") == "LlamaForCausalLM", "third model class")
    check(model.get("model_type") == "llama", "third model type")
    check(model.get("hidden_size") == 2048, "third model hidden size")
    check(model.get("logical_decoder_blocks") == 16, "third model layer count")
    check(str(model.get("converted_model_hash", "")).casefold() == val.EXPECTED_CONVERTED_HASH.casefold(), "converted model hash")
    check(model.get("runtime_dtype") == "torch.bfloat16", "runtime dtype")

    check(config.get("logical_decoder_blocks") == 16, "logical decoder blocks")
    check(config.get("carrier_api") == "FORWARD_HOOK_DECODER_BLOCK_OUTPUT", "carrier api")
    carrier = config.get("carrier_semantics", {})
    check(carrier.get("logical_layer_l_module_path") == "model.model.layers[l]", "carrier module path")
    check(carrier.get("block_0_to_14_hook_output") == "post_decoder_block_residual_before_next_block", "block 0-14 carrier")
    check(carrier.get("block_15_hook_output") == "post_decoder_block_residual_before_model_final_RMSNorm", "block 15 carrier")
    check(carrier.get("final_hidden_state_semantics") == "POST_FINAL_NORM_CONFIRMED", "final state semantics")
    check(carrier.get("forbidden_carrier") == "outputs.hidden_states[-1]", "final-norm trap")
    check(carrier.get("output_hidden_states_use") == "oracle_verification_only", "output_hidden_states role")

    tokenizer = config.get("tokenizer_identity", {})
    check(tokenizer.get("vocab_size") == 128256, "tokenizer vocab")
    check(tokenizer.get("bos_token_id") == 128000, "tokenizer BOS")
    check(tokenizer.get("eos_token_id") == 128001, "tokenizer EOS")
    check(tokenizer.get("eot_token_id") == 128009, "tokenizer EOT")
    check(tokenizer.get("chat_template_used") is False, "chat template policy")

    invocation = config.get("tokenizer_invocation", {})
    check(invocation.get("raw_text_field") == "text", "raw text field")
    check(invocation.get("add_special_tokens") is True, "add special tokens")
    check(invocation.get("padding") is False, "padding")
    check(invocation.get("truncation") is False, "truncation")
    check(invocation.get("last_valid_token_rule") == "attention_mask_sum_minus_one", "last-valid-token rule")

    domain = config.get("source_target_domain", {})
    check(domain.get("source_indices") == list(range(16)), "source domain")
    check(domain.get("target_indices") == list(range(16)), "target domain")
    check(domain.get("ordered_pair_semantics") == "source_layer_i_classifier_evaluated_on_target_layer_j", "ordered-pair semantics")
    check(domain.get("matrix_orientation") == "rows_source_layers_columns_target_layers", "matrix orientation")
    check(domain.get("layer_subset_shopping") is False, "layer subset shopping")

    split = config.get("split_identity", {})
    check(split.get("partitions") == ["FIT", "DIAGNOSTIC", "EVAL"], "partition identity")
    check(split.get("allocation") == {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}, "allocation")
    check(split.get("new_split_created") is False, "new split")
    check(split.get("item_filtering_allowed") is False, "item filtering")

    hashes = config.get("dataset_hashes", {})
    hash_key = {
        "dataset": "dataset_sha256",
        "condition_panel": "condition_panel_sha256",
        "data_schema": "data_schema_sha256",
        "frozen_manifest": "frozen_manifest_sha256",
        "exp024_preregistration": "exp024_preregistration_sha256",
    }
    for name, (_rel_path, expected_hash) in val.EXPECTED_DATASET_FILES.items():
        check(str(hashes.get(hash_key[name], "")).casefold() == expected_hash.casefold(), f"dataset hash {name}")

    check(config.get("class_order") == list(ref.CLASS_ORDER), "class order")
    check(config.get("condition_order") == list(ref.CONDITION_ORDER), "condition order")

    distance = config.get("distance_definition", {})
    check(distance.get("normalized_depth") == "layer_index/(num_layers-1)", "normalized depth formula")
    check(distance.get("pair_distance") == "abs(source_layer-target_layer)/(num_layers-1)", "pair distance formula")
    check(distance.get("num_layers") == 16, "distance num layers")

    association = config.get("distance_association", {})
    check(association.get("dependent_quantity") == "Dbar_m(i,j)", "distance dependent quantity")
    check(association.get("independent_quantity") == "abs(d(i)-d(j))", "distance independent quantity")
    check(association.get("statistic") == "Spearman_rho", "distance statistic")
    check(association.get("tie_handling") == "average_ranks", "distance tie handling")
    check(association.get("implementation_identity") == "custom_average_rank_spearman", "distance implementation identity")
    check(association.get("p_value_used") is False, "distance p-value policy")

    sdi = config.get("sdi", {})
    check(sdi.get("formula") == "SDI=(SOURCE_VARIANCE-TARGET_VARIANCE)/(SOURCE_VARIANCE+TARGET_VARIANCE)", "SDI formula")
    check(sdi.get("variance_convention") == "numpy.var(ddof=0)", "SDI variance convention")
    check(sdi.get("zero_denominator") == "SDI=0_status=NO_ROW_OR_COLUMN_VARIATION", "SDI zero denominator")
    check(sdi.get("support_rule") == "SOURCE_DOMINANT_if_SDI_gt_0_and_lower_gt_0; TARGET_DOMINANT_if_SDI_lt_0_and_upper_lt_0", "SDI support rule")

    low_d = config.get("low_d", {})
    check(low_d.get("mask_definition") == "DIAGNOSTIC_Dbar_m(i,j)<=0_for_eligible_off_diagonal_pairs", "LOW-D mask")
    check(low_d.get("mask_frozen_across_bootstrap") is True, "LOW-D mask frozen")
    check(low_d.get("estimand") == "mean_Rbar_eval_m(i,j)_over_frozen_DIAGNOSTIC_selected_pair_set", "LOW-D estimand")
    check(low_d.get("effective_n_zero") == "NOT_EVALUABLE", "LOW-D n=0")
    check(low_d.get("support_rule") == "SUPPORTED_if_point_estimate_gt_0_and_one_sided_95_percent_lower_bound_gt_0_else_NOT_SUPPORTED", "LOW-D support rule")

    bootstrap = config.get("bootstrap", {})
    check(bootstrap.get("design") == "condition_stratified_source_family_cluster_bootstrap", "bootstrap design")
    check(bootstrap.get("resampling_unit") == "source_family", "bootstrap resampling unit")
    check(bootstrap.get("statistical_unit") == "source_family_cluster", "bootstrap statistical unit")
    check(bootstrap.get("strata") == "condition", "bootstrap strata")
    check(bootstrap.get("bit_generator") == "numpy.random.PCG64", "bootstrap RNG")
    check(bootstrap.get("seed") == 20260819, "bootstrap seed")
    check(bootstrap.get("rng_construction") == "numpy.random.Generator(numpy.random.PCG64(20260819))", "bootstrap RNG construction")
    check(bootstrap.get("replicates") == 5000, "bootstrap replicates")
    check(bootstrap.get("ci_level") == 0.95, "bootstrap CI level")
    check(bootstrap.get("ci_method") == "percentile", "bootstrap CI method")
    check(bootstrap.get("quantile_method") == "numpy.percentile_method_linear", "bootstrap quantile method")
    check(bootstrap.get("one_sided_positive_lower_bound") == 5, "bootstrap lower bound")
    check(bootstrap.get("one_sided_negative_upper_bound") == 95, "bootstrap upper bound")
    check(bootstrap.get("invalid_replicate_handling") == "skip_replicates_that_do_not_preserve_all_four_classes", "bootstrap invalid replicate handling")

    technical = config.get("technical_validity", {})
    check(technical.get("source_technical_floor") == 0.75, "technical floor")
    check(technical.get("source_technical_floor_evaluated_on") == "DIAGNOSTIC", "technical floor partition")
    check(technical.get("source_coverage_min_count") == 8, "coverage min count")
    check(technical.get("source_coverage_min_fraction") == 0.5, "coverage fraction")
    check(technical.get("source_coverage_min_normalized_depth_span") == 0.5, "coverage span")
    check(technical.get("carrier_capture_exactly_once") is True, "carrier exactly once")
    check(technical.get("last_valid_token_must_be_mask_derived") is True, "last token mask derived")
    check(technical.get("analysis_dtype") == "float32", "analysis dtype")

    profiles = config.get("reference_profiles", {})
    check(profiles == val.EXPECTED_REFERENCE_PROFILES, "reference profiles")

    routing = config.get("profile_routing", {})
    check(routing.get("method") == "EXACT_MATCH_ONLY", "routing method")
    check(routing.get("no_continuous_similarity") is True, "no continuous similarity")
    check(routing.get("rules") == [
        "if_technical_or_measurement_invalid_then_RESULT_STATUS_UNOBSERVED_OR_INVALID_and_SCIENTIFIC_PROFILE_ROUTE_NOT_ASSIGNED",
        "if_llama_profile_exactly_equals_QWEN_REFERENCE_PROFILE_then_EXP026_PROFILE_MATCH_QWEN",
        "if_llama_profile_exactly_equals_OLMO_REFERENCE_PROFILE_then_EXP026_PROFILE_MATCH_OLMO",
        "else_THIRD_REGISTERED_PROFILE",
    ], "routing rules")

    outcome = config.get("outcome_blind_progress_policy", {})
    check(outcome.get("atomic_state_file") is True, "atomic state file")
    check(outcome.get("no_hidden_preview") is True, "no hidden preview")
    check(outcome.get("no_console_preview") is True, "no console preview")
    check(outcome.get("no_automatic_retry") is True, "no automatic retry")
    check(outcome.get("allowed") == ["timestamp", "stage", "completed", "total", "percentage", "elapsed", "eta", "heartbeat", "publication_status"], "outcome allowed fields")

    formal = config.get("formal_run_policy", {})
    check(formal.get("formal_authorization_created") is False, "authorization flag")
    check(formal.get("formal_run_performed") is False, "formal run flag")
    check(formal.get("scientific_result_created") is False, "scientific result flag")
    check(formal.get("next_task") == "102C_EXP027_ENGINEERING_AND_ADVERSARIAL_REVIEW", "next task")

    check(config.get("formal_authorization_created") is False, "top-level authorization")
    check(config.get("formal_run_status") == "NOT_PERFORMED", "formal run status")
    check(config.get("scientific_result_status") == "NOT_CREATED", "scientific result status")
    return errors

# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def test_statistical_contract_matches_exp026_source():
    config = _config()
    bootstrap = config["bootstrap"]
    assert bootstrap["replicates"] == ref.BOOTSTRAP_REPLICATES == 5000
    assert bootstrap["seed"] == ref.BOOTSTRAP_SEED == 20260819
    assert bootstrap["bit_generator"] == "numpy.random.PCG64"
    assert isinstance(np.random.PCG64(ref.BOOTSTRAP_SEED), np.random.PCG64)
    assert bootstrap["quantile_method"] == "numpy.percentile_method_linear"
    assert ref.BOOTSTRAP_QUANTILE_METHOD == "linear"
    assert bootstrap["ci_level"] == ref.BOOTSTRAP_CI_LEVEL == 0.95
    assert bootstrap["ci_method"] == "percentile"
    assert bootstrap["one_sided_positive_lower_bound"] == 5
    assert bootstrap["one_sided_negative_upper_bound"] == 95
    assert config["sdi"]["variance_convention"] == "numpy.var(ddof=0)"


def test_average_rank_uses_ties():
    assert ref.average_rank([3.0, 1.0, 1.0]) == [3.0, 1.5, 1.5]
    assert ref.average_rank([1.0, 1.0, 1.0]) == [2.0, 2.0, 2.0]


def test_spearman_degenerate_and_nonfinite_handling():
    assert ref.spearman_rho([1], [2]) == 0.0
    assert math.isnan(ref.spearman_rho([1, 1, 1], [1, 2, 3]))
    assert math.isnan(ref.spearman_rho([1, 2, 3], [1.0, float("nan"), 3.0]))


def test_population_variance_ddof_zero_and_nan():
    assert ref.population_variance([1, 2, 3]) == pytest.approx(np.var([1, 2, 3], ddof=0))
    assert math.isnan(ref.population_variance([]))
    assert math.isnan(ref.population_variance([1.0, float("nan")]))


# ---------------------------------------------------------------------------
# Depth normalization
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("num_layers", [3, 4, 16, 28])
def test_normalized_depth_contract_is_scale_free(num_layers):
    for layer in range(num_layers):
        assert ref.normalized_depth(layer, num_layers) == layer / (num_layers - 1)
        assert ref.normalized_pair_distance(layer, layer, num_layers) == 0.0
    assert ref.normalized_pair_distance(0, num_layers - 1, num_layers) == 1.0
    assert ref.normalized_pair_distance(num_layers - 1, 0, num_layers) == 1.0
    with pytest.raises(ValueError):
        ref.normalized_pair_distance(-1, 0, num_layers)
    with pytest.raises(ValueError):
        ref.normalized_pair_distance(0, num_layers, num_layers)


# ---------------------------------------------------------------------------
# Matrix orientation
# ---------------------------------------------------------------------------

def test_sdi_detects_source_target_transpose():
    num_layers = 3
    dbar = np.asarray(
        [
            [0.0, 10.0, -5.0],
            [2.0, 0.0, 3.0],
            [-1.0, 4.0, 0.0],
        ],
        dtype=np.float32,
    )
    mask = [True, True, True]
    original = ref._sdi_point(dbar, mask, num_layers)
    transposed = ref._sdi_point(dbar.T.copy(), mask, num_layers)
    assert original["sdi"] != transposed["sdi"]
    assert np.sign(original["sdi"]) == -np.sign(transposed["sdi"])


# ---------------------------------------------------------------------------
# Condition pooling
# ---------------------------------------------------------------------------

def test_condition_pool_equal_weight_arithmetic_mean():
    slices = [np.full((2, 2), float(i), dtype=np.float32) for i in range(10)]
    matrix = np.stack(slices, axis=2)
    pooled = ref._condition_pool(matrix)
    assert np.allclose(pooled, np.full((2, 2), 4.5, dtype=np.float32))


def test_condition_pool_rejects_wrong_condition_axis_and_nonfinite():
    with pytest.raises(ref.ProtocolIntegrityError):
        ref._condition_pool(np.zeros((3, 3, 9), dtype=np.float32))
    with pytest.raises(ref.TechnicalInvalidError):
        ref._condition_pool(np.full((3, 3, 10), np.nan, dtype=np.float32))


@pytest.mark.parametrize(
    "mutated_order",
    [
        list(reversed(ref.CONDITION_ORDER)),
        list(ref.CONDITION_ORDER[:-1]) + ["c_missing"],
        [ref.CONDITION_ORDER[0]] * 10,
    ],
)
def test_compute_matrix_profile_rejects_mutated_condition_order(mutated_order):
    observations = ref._hardcoded_synthetic_observations()["A"]
    with pytest.raises(ref.ProtocolIntegrityError):
        ref.compute_matrix_profile(
            observations,
            num_layers=4,
            condition_order=tuple(mutated_order),
            bootstrap_replicates=0,
        )


# ---------------------------------------------------------------------------
# LOW-D leakage firewall
# ---------------------------------------------------------------------------

def test_low_d_mask_is_derived_from_diag_dbar_only():
    num_layers = 4
    eligible = [True] * num_layers
    diag_dbar = np.full((num_layers, num_layers), 1.0, dtype=np.float32)
    diag_dbar[0, 2] = -1.0
    rbar = np.zeros_like(diag_dbar)
    rbar[0, 2] = 7.0
    rbar[0, 1] = 99.0

    mask, pairs = ref._low_d_pair_mask(diag_dbar, eligible, num_layers)
    assert mask[0, 2]
    assert not mask[0, 1]
    assert pairs == [(0, 2)]

    point = ref._summarize_point_profile(
        np.zeros_like(diag_dbar),
        rbar,
        eligible,
        num_layers,
        diag_dbar,
    )
    assert point["low_d_recovery"]["eligible_pair_count"] == 1
    assert point["low_d_recovery"]["mean_recovery"] == pytest.approx(7.0)


def _reject_low_d_contract(mask_source, partitions, uses_eval_r, recomputed):
    if mask_source != "DIAGNOSTIC_Dbar":
        raise ValueError("wrong mask source")
    if partitions != ["DIAGNOSTIC"]:
        raise ValueError("wrong partitions")
    if uses_eval_r:
        raise ValueError("EVAL R used for selection")
    if recomputed:
        raise ValueError("mask recomputed after EVAL")


@pytest.mark.parametrize(
    "fixture",
    [
        ("EVAL_Dbar", ["DIAGNOSTIC"], False, False),
        ("DIAGNOSTIC_Dbar", ["DIAGNOSTIC", "EVAL"], False, False),
        ("DIAGNOSTIC_Dbar", ["DIAGNOSTIC"], True, False),
        ("DIAGNOSTIC_Dbar", ["DIAGNOSTIC"], False, True),
    ],
)
def test_low_d_leak_fixtures_are_rejected(fixture):
    with pytest.raises(ValueError):
        _reject_low_d_contract(*fixture)


def test_low_d_valid_contract_passes():
    _reject_low_d_contract("DIAGNOSTIC_Dbar", ["DIAGNOSTIC"], False, False)

# ---------------------------------------------------------------------------
# Technical validity boundaries
# ---------------------------------------------------------------------------

def test_source_technical_floor_boundary_is_inclusive():
    observations = _source_qualification_fixture(4)
    three_good = {"logic", "causality", "analogy"}
    two_good = {"logic", "causality"}

    eligible_models = [_EncoderFakeModel(three_good) for _ in range(4)]
    eligible = ref._source_qualification(observations, 4, eligible_models, ref.CONDITION_ORDER)
    assert all(eligible["eligible_source_mask"])
    assert eligible["source_coverage_evaluable"] is True

    ineligible_models = [_EncoderFakeModel(two_good) for _ in range(4)]
    ineligible = ref._source_qualification(observations, 4, ineligible_models, ref.CONDITION_ORDER)
    assert not any(ineligible["eligible_source_mask"])
    assert ineligible["source_coverage_evaluable"] is False


def test_source_technical_floor_rejects_below_inclusive_boundary(monkeypatch):
    observations = _source_qualification_fixture(4)
    models = [_EncoderFakeModel(set(ref.CLASS_ORDER)) for _ in range(4)]
    monkeypatch.setattr(ref, "balanced_accuracy", lambda y_true, y_pred: 0.749999999)
    qual = ref._source_qualification(observations, 4, models, ref.CONDITION_ORDER)
    assert not any(qual["eligible_source_mask"])
    monkeypatch.setattr(ref, "balanced_accuracy", lambda y_true, y_pred: 0.75)
    qual = ref._source_qualification(observations, 4, models, ref.CONDITION_ORDER)
    assert all(qual["eligible_source_mask"])


def _coverage_models(num_layers, eligible_indices):
    three_good = {"logic", "causality", "analogy"}
    two_good = {"logic", "causality"}
    return [
        _EncoderFakeModel(three_good if index in eligible_indices else two_good)
        for index in range(num_layers)
    ]


def test_source_coverage_count_and_span_boundaries():
    observations = _source_qualification_fixture(8)

    count_and_span_ok = _coverage_models(8, {0, 1, 6, 7})
    qual = ref._source_qualification(observations, 8, count_and_span_ok, ref.CONDITION_ORDER)
    assert qual["eligible_source_count"] == 4
    assert qual["eligible_depth_span"] == pytest.approx(1.0)
    assert qual["source_coverage_evaluable"] is True

    count_fail = _coverage_models(8, {0, 1, 2})
    qual = ref._source_qualification(observations, 8, count_fail, ref.CONDITION_ORDER)
    assert qual["eligible_source_count"] == 3
    assert qual["source_coverage_evaluable"] is False

    span_fail = _coverage_models(8, {0, 1, 2, 3})
    qual = ref._source_qualification(observations, 8, span_fail, ref.CONDITION_ORDER)
    assert qual["eligible_source_count"] == 4
    assert qual["eligible_depth_span"] == pytest.approx(3 / 7)
    assert qual["source_coverage_evaluable"] is False


# ---------------------------------------------------------------------------
# Profile routing and invalidity order
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("profile", list(_all_profiles()))
def test_exact_profile_routing_space(profile):
    route, status = val.route_profile(profile)
    assert status == "VALID_REGISTERED_RESULT"
    profile_tuple = tuple(profile.values())
    if profile_tuple == QWEN_TUPLE:
        assert route == "EXP026_PROFILE_MATCH_QWEN"
    elif profile_tuple == OLMO_TUPLE:
        assert route == "EXP026_PROFILE_MATCH_OLMO"
    else:
        assert route == "THIRD_REGISTERED_PROFILE"


@pytest.mark.parametrize("profile", list(_all_profiles()))
def test_invalidity_precedes_routing_for_every_profile(profile):
    for technical_valid, measurement_valid in [(False, True), (True, False), (False, False)]:
        route, status = val.route_profile(
            profile,
            technical_valid=technical_valid,
            measurement_valid=measurement_valid,
        )
        assert route == "NOT_ASSIGNED"
        assert status == "UNOBSERVED_OR_INVALID"


# ---------------------------------------------------------------------------
# Carrier / token / class-mapping contracts
# ---------------------------------------------------------------------------

def test_carrier_final_norm_trap_is_explicit():
    config = _config()
    carrier = config["carrier_semantics"]
    assert carrier["block_15_hook_output"] == "post_decoder_block_residual_before_model_final_RMSNorm"
    assert carrier["final_hidden_state_semantics"] == "POST_FINAL_NORM_CONFIRMED"
    assert carrier["forbidden_carrier"] == "outputs.hidden_states[-1]"
    assert carrier["output_hidden_states_use"] == "oracle_verification_only"


def test_last_valid_token_indices_are_mask_derived():
    assert ref.last_valid_token_indices(np.asarray([1, 1, 1])) == [2]
    assert ref.last_valid_token_indices(np.asarray([1, 1, 1, 0, 0])) == [2]
    assert ref.last_valid_token_indices(np.asarray([[1, 1, 0], [1, 1, 1]])) == [1, 2]
    with pytest.raises(ValueError):
        ref.last_valid_token_indices(np.asarray([0, 0, 0]))


def test_select_last_valid_token_guards_right_padding():
    import torch

    hidden = torch.tensor(
        [[[10, 11], [20, 21], [30, 31], [40, 41], [50, 51]]],
        dtype=torch.float32,
    )
    mask = torch.tensor([[1, 1, 1, 0, 0]])
    selected = ref.select_last_valid_token(hidden, mask)
    assert torch.equal(selected, torch.tensor([[30, 31]], dtype=torch.float32))


def test_float32_analysis_boundary_from_bfloat16():
    import torch

    tensor = torch.tensor([1.5, 2.0], dtype=torch.bfloat16)
    array = ref.to_float32_analysis_array(tensor, expected_ndim=1)
    assert isinstance(array, np.ndarray)
    assert array.dtype == np.float32
    assert np.allclose(array, np.asarray([1.5, 2.0], dtype=np.float32))
    with pytest.raises(ref.TechnicalInvalidError):
        ref.to_float32_analysis_array(torch.tensor([np.inf], dtype=torch.float32))


def test_class_probability_mapping_uses_classifier_classes():
    model = _PermutedClassesModel()
    assert ref.classifier_class_mapping(model) == ["causality", "logic", "analogy", "definition"]
    assert ref.probability_column_index(model, "logic") == 1
    probabilities = np.asarray([[0.1, 0.7, 0.1, 0.1]], dtype=np.float32)
    assert ref.probability_for_class(probabilities, model, "logic")[0] == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# No hidden scientific CLI/environment freedom
# ---------------------------------------------------------------------------

def _argparse_option_strings(source):
    tree = ast.parse(source)
    options = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == "add_argument":
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        options.append(arg.value)
                for keyword in node.keywords:
                    if keyword.arg == "dest" and isinstance(keyword.value, ast.Constant):
                        options.append(keyword.value)
    return options


def test_no_scientific_cli_or_environment_override_surfaces():
    for path in EXP027_DIR.rglob("*.py"):
        source = path.read_text(encoding="utf-8").lstrip("\ufeff")
        for option in _argparse_option_strings(source):
            assert option == "--output", f"unexpected CLI option in {path}: {option}"
        for line in source.splitlines():
            if "os.environ" in line:
                assert "HF_HUB_OFFLINE" in line or "TRANSFORMERS_OFFLINE" in line


# ---------------------------------------------------------------------------
# Outcome-blind progress
# ---------------------------------------------------------------------------

def test_progress_rejects_forbidden_scientific_payload_keys():
    forbidden = [
        "rho",
        "sdi",
        "low_d",
        "ci",
        "p_value",
        "support",
        "profile_route",
        "route",
        "condition",
        "matrix_cells",
        "best_worst_layers",
    ]
    for key in forbidden:
        state = {
            "stage": "BOOTSTRAP",
            "completed": 1,
            "total": 10,
            "percent": 10.0,
            "elapsed": 0.0,
            "last_update": "2026-01-01T00:00:00+00:00",
            key: 0.0,
        }
        with pytest.raises(ValueError):
            progress.OutcomeBlindProgress._validate_state(state)


def test_progress_report_payload_has_no_scientific_preview(tmp_path, capsys):
    helper = progress.OutcomeBlindProgress(state_path=tmp_path / "state.json")
    helper.report("BOOTSTRAP", completed=2500, total=5000, eta_seconds=42.0)
    output = capsys.readouterr().out.lower()
    for term in ("rho", "sdi", "low_d", "ci", "support", "route", "condition"):
        assert term not in output
    state = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
    assert set(state).issubset(progress.ALLOWED_STATE_KEYS)


# ---------------------------------------------------------------------------
# Semantic mutation fail-closed oracle
# ---------------------------------------------------------------------------

def test_current_frozen_design_matches_independent_semantic_oracle():
    assert _semantic_errors(_config()) == []
    assert val.validate_file() == []


MUTATORS = [
    ("model hash", lambda c: c["third_model_identity"].update({"converted_model_hash": "0" * 64})),
    ("model class", lambda c: c["third_model_identity"].update({"model_class": "Olmo2ForCausalLM"})),
    ("tokenizer identity", lambda c: c["tokenizer_identity"].update({"vocab_size": 1})),
    ("layer count", lambda c: c.update({"logical_decoder_blocks": 15})),
    ("carrier API", lambda c: c.update({"carrier_api": "OUTPUTS_HIDDEN_STATES"})),
    ("block15 semantics", lambda c: c["carrier_semantics"].update({"block_15_hook_output": "POST_FINAL_NORM"})),
    ("dataset hash", lambda c: c["dataset_hashes"].update({"dataset_sha256": "0" * 64})),
    ("split identity", lambda c: c["split_identity"].update({"allocation": {"FIT": 10, "DIAGNOSTIC": 8, "EVAL": 8}})),
    ("condition order", lambda c: c.update({"condition_order": list(reversed(c["condition_order"]))})),
    ("source-target orientation", lambda c: c["source_target_domain"].update({"matrix_orientation": "rows_target_columns_source"})),
    ("distance definition", lambda c: c["distance_definition"].update({"normalized_depth": "layer_index/num_layers"})),
    ("Spearman ranking rule", lambda c: c["distance_association"].update({"tie_handling": "min_ranks"})),
    ("bootstrap seed", lambda c: c["bootstrap"].update({"seed": 1})),
    ("bootstrap n", lambda c: c["bootstrap"].update({"replicates": 10})),
    ("CI endpoints", lambda c: c["bootstrap"].update({"one_sided_positive_lower_bound": 50})),
    ("variance ddof", lambda c: c["sdi"].update({"variance_convention": "numpy.var(ddof=1)"})),
    ("LOW-D threshold", lambda c: c["low_d"].update({"mask_definition": "DIAGNOSTIC_Dbar_m(i,j)<0"})),
    ("technical floor", lambda c: c["technical_validity"].update({"source_technical_floor": 0.5})),
    ("coverage", lambda c: c["technical_validity"].update({"source_coverage_min_count": 1})),
    ("span", lambda c: c["technical_validity"].update({"source_coverage_min_normalized_depth_span": 0.1})),
    ("reference Qwen profile", lambda c: c["reference_profiles"]["QWEN_REFERENCE_PROFILE"].update({"dominance_status": "SOURCE_DOMINANT"})),
    ("reference OLMo profile", lambda c: c["reference_profiles"]["OLMO_REFERENCE_PROFILE"].update({"low_d_recovery_status": "NOT_SUPPORTED"})),
    ("routing rule", lambda c: c["profile_routing"].update({"method": "NEAREST_NEIGHBOR"})),
    ("authorization state", lambda c: c.update({"formal_authorization_created": True})),
    ("scientific-result state", lambda c: c.update({"scientific_result_status": "CREATED"})),
]


@pytest.mark.parametrize("name,mutator", MUTATORS, ids=[item[0] for item in MUTATORS])
def test_scientific_mutations_fail_independent_semantic_validation(name, mutator):
    config = copy.deepcopy(_config())
    mutator(config)
    assert _semantic_errors(config) != []
