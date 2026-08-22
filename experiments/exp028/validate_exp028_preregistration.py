#!/usr/bin/env python3
"""EXP-028 frozen preregistration validator.

This validator is read-only. It checks the EXP-028 frozen design JSON against
inherited model, panel, probe, moment-recalibration, and bootstrap authorities.
It does not load a model, access real FIT/DIAG/EVAL content, or create results.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]
CONFIG_PATH = EXP_DIR / "exp028_frozen_config.json"

EXPECTED_EXPERIMENT = "EXP-028"
EXPECTED_WORKING_NAME = "PAIRED_INFORMATION_BEYOND_MARGINAL_RECALIBRATION"
EXPECTED_TASK_ID = "103B_EXP028_AUTHORITY_BINDING_AND_PREREGISTRATION_DRAFT"
EXPECTED_DESIGN_STATUS = "FROZEN_DESIGN_NOT_RUN"
EXPECTED_ORIGIN_CLASS = "RESULT_CONDITIONED_ASSET_DERIVED_CANDIDATE"
EXPECTED_HEAD = "86c120f56ee615540ecff15bb62f8d05eaca7700"
EXPECTED_AUTHORITY_BINDING_PATH = "experiments/exp028/exp028_authority_binding.json"
EXPECTED_AUTHORITY_BINDING_SHA256 = "72fd5e1f52c5be19bc5fd8cb4558b3e6e9eea5b2e6b615ef7e568d23ef627727"

EXPECTED_MODELS = {
    "Qwen": {
        "model_id": "Qwen/Qwen3-1.7B",
        "model_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "model_class": "Qwen3ForCausalLM",
        "model_type": "qwen3",
        "hidden_size": 2048,
        "num_hidden_layers": 28,
        "first_layer_index": 0,
        "last_layer_index": 27,
        "tokenizer_class": "Qwen2Tokenizer",
    },
    "OLMo": {
        "model_id": "allenai/OLMo-2-0425-1B-Instruct",
        "model_revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
        "model_class": "Olmo2ForCausalLM",
        "model_type": "olmo2",
        "hidden_size": 2048,
        "num_hidden_layers": 16,
        "first_layer_index": 0,
        "last_layer_index": 15,
        "tokenizer_class": "GPT2Tokenizer",
    },
    "Llama": {
        "model_id": "Meta-Llama-3.2-1B-Instruct",
        "model_class": "LlamaForCausalLM",
        "model_type": "llama",
        "hidden_size": 2048,
        "num_hidden_layers": 16,
        "first_layer_index": 0,
        "last_layer_index": 15,
        "tokenizer_class": "TokenizersBackend",
    },
}

EXPECTED_CLASS_ORDER = ["logic", "causality", "analogy", "definition"]
EXPECTED_CONDITIONS = [
    "c01_lexical_relex",
    "c02_syntactic_restructure",
    "c03_controlled_compression",
    "c04_controlled_elaboration",
    "c05_relation_explicit",
    "c06_relation_implicit",
    "c07_register_formal",
    "c08_register_informal",
    "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
]
EXPECTED_ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}

PRIOR_PANEL_FILES = {
    "exp023_dataset": (
        "experiments/exp023/data/exp023_independent_controlled.json",
        "9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a",
    ),
    "exp024_dataset": (
        "experiments/exp024/data/exp024_condition_panel_frozen.json",
        "46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404",
    ),
    "exp024_condition_panel_spec": (
        "experiments/exp024/condition_panel_spec.json",
        "a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954",
    ),
    "exp024_data_schema": (
        "experiments/exp024/data_schema.json",
        "e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec",
    ),
    "exp024_frozen_manifest": (
        "experiments/exp024/exp024_frozen_manifest.json",
        "1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59",
    ),
}

EXPECTED_PROHIBITED_FAMILIES = [
    "dense_affine_matrix",
    "low_rank_cross_coordinate_map",
    "orthogonal_Procrustes",
    "MLP",
    "KAN",
    "spline_adapter",
    "attention_adapter",
    "learned_residual_network",
]

FORBIDDEN_EXP028_PATHS = [
    EXP_DIR / "results",
    EXP_DIR / "exp028_formal_run_authorization.json",
    EXP_DIR / "exp028_results.json",
    EXP_DIR / "formal_authorization",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(config.get("schema_version") == "1.0.0", "schema_version mismatch")
    check(config.get("experiment_id") == EXPECTED_EXPERIMENT, "experiment_id mismatch")
    check(config.get("working_name") == EXPECTED_WORKING_NAME, "working_name mismatch")
    check(config.get("task_id") == EXPECTED_TASK_ID, "task_id mismatch")
    check(config.get("design_status") == EXPECTED_DESIGN_STATUS, "design_status mismatch")
    check(config.get("authority_commit") == EXPECTED_HEAD, "authority_commit mismatch")
    check(config.get("freeze_commit") == EXPECTED_HEAD, "freeze_commit mismatch")
    check(config.get("origin_class") == EXPECTED_ORIGIN_CLASS, "origin_class mismatch")

    scope = config.get("explicit_scope", {})
    for key in (
        "FULL_RESIDUAL_FLOW_TEST",
        "FULL_MSA_TEST",
        "TRANSPORT_TEST",
        "INVARIANT_TEST",
        "FUNCTIONAL_BINDING_TEST",
    ):
        check(scope.get(key) is False, f"scope flag must be false: {key}")

    binding = config.get("authority_binding", {})
    check(binding.get("path") == EXPECTED_AUTHORITY_BINDING_PATH, "authority binding path mismatch")
    check(str(binding.get("sha256", "")).casefold() == EXPECTED_AUTHORITY_BINDING_SHA256.casefold(), "authority binding hash mismatch")
    binding_path = ROOT / EXPECTED_AUTHORITY_BINDING_PATH
    if not binding_path.exists():
        errors.append("authority binding file missing")
    elif sha256_file(binding_path).casefold() != EXPECTED_AUTHORITY_BINDING_SHA256.casefold():
        errors.append("authority binding file hash drift")

    models = config.get("models", {})
    for name, expected in EXPECTED_MODELS.items():
        model = models.get(name, {})
        check(model.get("model_id") == expected["model_id"], f"{name} model_id mismatch")
        if name == "Llama":
            check(model.get("model_family") == "Llama-3.2", "Llama model_family mismatch")
        else:
            check(model.get("model_revision") == expected.get("model_revision"), f"{name} model_revision mismatch")
        check(model.get("model_class") == expected["model_class"], f"{name} model_class mismatch")
        check(model.get("model_type") == expected["model_type"], f"{name} model_type mismatch")
        check(model.get("hidden_size") == expected["hidden_size"], f"{name} hidden_size mismatch")
        check(model.get("num_hidden_layers") == expected["num_hidden_layers"], f"{name} num_hidden_layers mismatch")
        check(model.get("first_layer_index") == expected["first_layer_index"], f"{name} first_layer_index mismatch")
        check(model.get("last_layer_index") == expected["last_layer_index"], f"{name} last_layer_index mismatch")
        check(model.get("tokenizer_class") == expected["tokenizer_class"], f"{name} tokenizer_class mismatch")

    layer = config.get("layer_domain", {})
    check(layer.get("ordering_rule") == "j > i", "layer ordering mismatch")
    check(layer.get("all_ordered_forward_pairs") is True, "layer pairs must include all ordered forward pairs")
    check(layer.get("equal_weight_layer_pairs") is True, "layer pairs must be equal weight")
    check(layer.get("layer_subset_shopping") is False, "layer subset shopping must be false")
    check(layer.get("distance_weighting") == "none", "layer distance weighting must be none")
    check(layer.get("profile_weighting") == "none", "profile weighting must be none")
    check(layer.get("low_d_subset_selection") == "none", "LOW-D subset selection must be none")

    carrier = config.get("carrier_semantics", {})
    check(carrier.get("api") == "FORWARD_HOOK_DECODER_BLOCK_OUTPUT", "carrier API mismatch")
    check(carrier.get("logical_layer_module_path") == "model.model.layers[l]", "carrier module path mismatch")
    check(carrier.get("hook_output") == "post_decoder_block_residual_before_next_block_and_before_model_final_norm", "carrier semantics mismatch")
    check(carrier.get("forbidden_carrier") == "outputs.hidden_states[-1]", "forbidden carrier mismatch")

    tokenizer = config.get("tokenizer_contract", {})
    check(tokenizer.get("add_special_tokens") is True, "tokenizer add_special_tokens mismatch")
    check(tokenizer.get("return_tensors") == "pt", "tokenizer return_tensors mismatch")
    check(tokenizer.get("padding") is False, "tokenizer padding mismatch")
    check(tokenizer.get("truncation") is False, "tokenizer truncation mismatch")
    check(tokenizer.get("last_valid_token_rule") == "attention_mask_sum_minus_one", "last-valid-token rule mismatch")
    check(tokenizer.get("analysis_dtype") == "float32", "analysis dtype mismatch")

    probe = config.get("probe_contract", {})
    check(probe.get("classifier") == "LogisticRegression", "probe classifier mismatch")
    check(probe.get("solver") == "lbfgs", "probe solver mismatch")
    check(probe.get("penalty") == "L2", "probe penalty mismatch")
    check(probe.get("C") == 1.0, "probe C mismatch")
    check(probe.get("max_iter") == 1000, "probe max_iter mismatch")
    check(probe.get("class_weight") is None, "probe class_weight mismatch")
    check(probe.get("class_order") == EXPECTED_CLASS_ORDER, "probe class order mismatch")
    check(probe.get("probability_mapping") == "classifier.classes_", "probe probability mapping mismatch")
    check(probe.get("fit_only_rule") == "FIT_condition_realization_only", "probe FIT-only rule mismatch")

    moment = config.get("moment_recalibration", {})
    check(moment.get("name") == "A_mu_sigma", "moment name mismatch")
    check("T_mu_sigma(h_j)_k" in moment.get("definition", ""), "moment definition mismatch")
    check(moment.get("orientation") == "target_representation_to_source_measurement_frame", "moment orientation mismatch")
    check(moment.get("variance_convention") == "population_variance_ddof_0", "moment variance convention mismatch")

    operators = config.get("operator_families", {})
    check(operators.get("primary_comparator") == "T_pair_diag_vs_T_mu_sigma", "primary comparator mismatch")
    check(operators.get("primary_comparator_baseline") == "T1_MOMENT_RECALIBRATION", "primary comparator baseline mismatch")
    check(operators.get("primary_contrast") == "T2_MINUS_T1", "primary contrast mismatch")
    check(operators.get("coordinatewise_only") is True, "operator must be coordinatewise only")
    check(operators.get("T2", {}).get("label_free") is True, "T_pair_diag must be label-free")
    check(operators.get("T2", {}).get("fit_only") is True, "T_pair_diag must be FIT-only")
    check(operators.get("T2", {}).get("cross_coordinate_mixing") is False, "T_pair_diag must not mix coordinates")
    check(operators.get("T2", {}).get("hyperparameter_search") is False, "T_pair_diag hyperparameter search must be false")
    check(operators.get("T2", {}).get("task_loss_optimization") is False, "T_pair_diag task-loss optimization must be false")
    check(operators.get("prohibited_families") == EXPECTED_PROHIBITED_FAMILIES, "prohibited operator families mismatch")

    numerical = config.get("numerical_edge_rules", {})
    check(numerical.get("epsilon") == 0.0, "epsilon mismatch")
    check(numerical.get("no_tunable_epsilon") is True, "tunable epsilon forbidden")
    check(numerical.get("zero_variance_action") == "TECHNICALLY_INVALID_MODEL", "zero variance action mismatch")
    check(numerical.get("nonfinite_variance_action") == "TECHNICALLY_INVALID_MODEL", "nonfinite variance action mismatch")
    check(numerical.get("nonfinite_fitted_coefficient_action") == "TECHNICALLY_INVALID_MODEL", "nonfinite coefficient action mismatch")

    endpoints = config.get("primary_endpoints", {})
    rep = endpoints.get("representation_endpoint", {})
    read = endpoints.get("readout_endpoint", {})
    check(rep.get("name") == "DELTA_RM", "representation endpoint name mismatch")
    check(rep.get("definition") == "DELTA_RM = E(T_mu_sigma) - E(T_pair_diag)", "DELTA_RM definition mismatch")
    check("DELTA_RM = E(T_mu_sigma) - E(T_pair_diag)" in rep.get("sign_convention", ""), "DELTA_RM sign convention mismatch")
    check(read.get("name") == "DELTA_RO", "readout endpoint name mismatch")
    check(read.get("definition") == "DELTA_RO = C_pair - C_mu_sigma", "DELTA_RO definition mismatch")
    check("DELTA_RO = C_pair - C_mu_sigma" in read.get("sign_convention", ""), "DELTA_RO sign convention mismatch")
    check(endpoints.get("balanced_accuracy") == "macro_average_per_class_recall_over_logic_causality_analogy_definition", "balanced accuracy mismatch")
    check(endpoints.get("probe_fitting") == "FIT_only", "probe fitting firewall mismatch")
    check(endpoints.get("operator_fitting") == "label_free_FIT_only", "operator fitting firewall mismatch")
    check(endpoints.get("no_optimize_T_pair_diag_against_DELTA_RO") is True, "endpoint optimization firewall mismatch")

    model_routing = config.get("model_state_routing", {})
    check(model_routing.get("RM_SUPPORTED_rule") == "lower_bound_of_registered_bootstrap_CI_for_DELTA_RM_gt_0", "RM support rule mismatch")
    check(model_routing.get("support_decision_uses") == "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND", "model support decision source mismatch")
    check(model_routing.get("RO_SUPPORTED_rule") == "lower_bound_of_registered_bootstrap_CI_for_DELTA_RO_gt_0", "RO support rule mismatch")
    states = model_routing.get("states", {})
    check(states.get("(RM+, RO+)") == "JOINT_ALIGNMENT_CONTRIBUTION", "state routing mismatch")
    check(states.get("(RM+, RO-)") == "REPRESENTATION_ONLY", "state routing mismatch")
    check(states.get("(RM-, RO+)") == "READOUT_ONLY_ARTIFACT_RISK", "state routing mismatch")
    check(states.get("(RM-, RO-)") == "NO_PAIRED_COORDINATE_CONTRIBUTION", "state routing mismatch")
    check(model_routing.get("READOUT_ONLY_ARTIFACT_RISK_interpretation") == "cautionary_registered_interpretation_not_alignment_success", "RO-only risk interpretation mismatch")

    three_model = config.get("three_model_routing", {})
    check(three_model.get("no_majority_vote") is True, "majority vote forbidden")
    check(three_model.get("no_endpoint_voting") is True, "endpoint voting forbidden")
    check(three_model.get("no_nearest_profile_routing") is True, "nearest-profile routing forbidden")
    check(three_model.get("no_post_hoc_grouping") is True, "post-hoc grouping forbidden")
    rules = three_model.get("rules", [])
    check("if_any_model_technically_invalid_then_NOT_FULLY_ADJUDICATED" in rules, "invalid-model routing missing")

    bootstrap = config.get("bootstrap", {})
    check(bootstrap.get("design") == "condition_stratified_source_family_cluster_bootstrap", "bootstrap design mismatch")
    check(bootstrap.get("resampling_unit") == "source_family", "bootstrap resampling unit mismatch")
    check(bootstrap.get("statistical_unit") == "source_family_cluster", "bootstrap statistical unit mismatch")
    check(bootstrap.get("strata") == "condition", "bootstrap strata mismatch")
    check(bootstrap.get("bit_generator") == "numpy.random.PCG64", "bootstrap bit generator mismatch")
    check(bootstrap.get("seed") == 20260819, "bootstrap seed mismatch")
    check(bootstrap.get("replicates") == 5000, "bootstrap replicates mismatch")
    check("ci_level" not in bootstrap, "ambiguous legacy ci_level must be removed")
    support_ci = bootstrap.get("primary_support_ci", {})
    check(support_ci.get("name") == "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND", "primary support bound mismatch")
    check(support_ci.get("level") == 0.95, "primary support level mismatch")
    check(support_ci.get("side") == "lower", "primary support side mismatch")
    check(support_ci.get("percentile") == 5, "primary support percentile mismatch")
    desc = bootstrap.get("descriptive_central_interval", {})
    check(desc.get("name") == "CENTRAL_90_PERCENT_PERCENTILE_INTERVAL", "descriptive interval name mismatch")
    check(desc.get("level") == 0.90, "descriptive interval level mismatch")
    check(desc.get("lower_percentile") == 5 and desc.get("upper_percentile") == 95, "descriptive interval percentiles mismatch")
    check(bootstrap.get("two_sided_95_percent_ci_used") is False, "two-sided 95 CI must not be used")
    check(bootstrap.get("support_decision_uses") == "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND", "support decision source mismatch")
    check(bootstrap.get("ci_method") == "percentile", "bootstrap CI method mismatch")
    check(bootstrap.get("quantile_method") == "numpy.percentile_method_linear", "bootstrap quantile method mismatch")
    check(bootstrap.get("one_sided_positive_lower_bound") == 5, "bootstrap lower bound mismatch")
    check(bootstrap.get("one_sided_negative_upper_bound") == 95, "bootstrap upper bound mismatch")
    check(bootstrap.get("no_operator_refit_inside_EVAL_bootstrap") is True, "operator refit inside bootstrap forbidden")
    check(bootstrap.get("no_probe_refit_inside_EVAL_bootstrap") is True, "probe refit inside bootstrap forbidden")
    check(bootstrap.get("bootstrap_shopping") is False, "bootstrap shopping forbidden")

    aggregation = config.get("aggregation_order", {})
    check(aggregation.get("source_family") == "mean_over_fresh_EVAL_source_families_equal_weight", "source-family aggregation mismatch")
    check(aggregation.get("condition") == "arithmetic_mean_over_all_10_conditions_equal_weight", "condition aggregation mismatch")
    check(aggregation.get("layer_pair") == "arithmetic_mean_over_all_preregistered_ordered_forward_pairs_j_gt_i_equal_weight", "layer-pair aggregation mismatch")
    check("token_count" in aggregation.get("forbidden_weighting", []), "token-count weighting must be forbidden")
    check("layer_distance" in aggregation.get("forbidden_weighting", []), "layer-distance weighting must be forbidden")
    check("LOW_D_subset_selection" in aggregation.get("forbidden_weighting", []), "LOW-D weighting must be forbidden")

    diag = config.get("diag_role", {})
    check(diag.get("role") == "TECHNICAL_ONLY", "DIAG role must be technical only")
    check("select_favorable_layer_pairs" in diag.get("must_not", []), "DIAG layer-pair selection forbidden")
    check("determine_whether_EVAL_is_worth_running" in diag.get("must_not", []), "DIAG EVAL gating forbidden")
    check(diag.get("source_technical_floor") == 0.75, "DIAG source floor mismatch")

    pair_break = config.get("pair_break_control", {})
    check(pair_break.get("status") == "SECONDARY_ONLY", "pair-break control must be secondary")
    check(pair_break.get("cannot_rescue_primary_failure") is True, "pair-break control must not rescue primary")
    check(pair_break.get("procedure") == "within_FIT_sort_source_family_ids_lexicographically_and_assign_target_sequence_by_cyclic_shift_of_one", "pair-break procedure mismatch")
    check(pair_break.get("scope") == "within_FIT_per_condition_per_layer_pair", "pair-break scope mismatch")
    check(pair_break.get("ordering") == "lexicographic_source_family_id", "pair-break ordering mismatch")
    check(pair_break.get("condition_handling") == "independent_per_condition", "pair-break condition handling mismatch")
    check(pair_break.get("source_family_handling") == "preserve_source_family_count_and_marginals", "pair-break source-family handling mismatch")

    capacity = config.get("operator_capacity_firewall", {})
    check(capacity.get("EXP028_remains_coordinatewise") is True, "EXP-028 must remain coordinatewise")
    check(capacity.get("prohibited_post_hoc_rescue_families") == EXPECTED_PROHIBITED_FAMILIES, "capacity firewall family mismatch")

    check("paired item-level coordinate information contributes" in config.get("claim_ceiling", ""), "claim ceiling mismatch")
    not_established = config.get("not_established", [])
    for term in ("transport", "invariant_preservation", "Functional_Binding", "Residual-Flow_confirmation", "MSA_confirmation"):
        check(term in not_established, f"claim ceiling missing {term}")

    fresh = config.get("fresh_data_firewall", {})
    check(fresh.get("no_prior_scientific_items_in_EXP028") is True, "fresh-data firewall missing")
    check(isinstance(fresh.get("prior_panel_authorities"), list) and len(fresh.get("prior_panel_authorities", [])) >= 2, "prior panel authorities not enumerated")
    check(fresh.get("fresh_panel_generation_deferred_to_103C_or_later") is True, "fresh panel generation must be deferred")
    check(fresh.get("duplicate_normalization") == "unicodedata.normalize_NFKC_then_strip_then_collapse_each_maximal_Unicode_whitespace_run_to_single_ASCII_space", "duplicate normalization mismatch")
    check(fresh.get("duplicate_hash") == "sha256_of_utf8_normalized_text", "duplicate hash mismatch")
    check("no_normalized_raw_text_sha256_collision_with_prior_scientific_panels" in fresh.get("required_freshness_checks", []), "freshness hash check missing")
    check("no_prior_source_family_reuse_where_source_family_identity_exists" in fresh.get("required_freshness_checks", []), "freshness family check missing")

    formal = config.get("formal_run_policy", {})
    for key in ("formal_authorization_created", "scientific_result_created", "real_FIT_accessed", "real_DIAG_accessed", "real_EVAL_accessed", "scientific_inference_performed"):
        check(formal.get(key) is False, f"formal firewall flag must be false: {key}")

    for name, (rel_path, expected_hash) in PRIOR_PANEL_FILES.items():
        actual_path = ROOT / rel_path
        if not actual_path.exists():
            errors.append(f"prior panel authority missing: {rel_path}")
        elif sha256_file(actual_path).casefold() != expected_hash.casefold():
            errors.append(f"prior panel authority hash drift: {rel_path}")

    for forbidden in FORBIDDEN_EXP028_PATHS:
        if forbidden.exists():
            errors.append(f"forbidden EXP-028 artifact present: {forbidden}")

    return errors


def main() -> int:
    if not CONFIG_PATH.exists():
        print("MISSING_CONFIG", CONFIG_PATH)
        return 2
    config = read_json(CONFIG_PATH)
    errors = validate(config)
    if errors:
        print("EXP028_PREREGISTRATION_VALIDATOR=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("EXP028_PREREGISTRATION_VALIDATOR=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
