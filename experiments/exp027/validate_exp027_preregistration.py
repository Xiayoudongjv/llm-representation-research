#!/usr/bin/env python3
"""EXP-027 frozen preregistration validator.

This validator is read-only. It checks the EXP-027 frozen design JSON against
the inherited EXP-026 authority and the qualified Llama provenance. It does not
load a model, access formal FIT/DIAG/EVAL content, or create scientific results.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]
CONFIG_PATH = EXP_DIR / "exp027_frozen_design.json"

EXPECTED_TASK_ID = "102B_EXP027_PREREGISTRATION_AND_FROZEN_DESIGN"
EXPECTED_DESIGN_STATUS = "FROZEN_DESIGN_NOT_RUN"
EXPECTED_COMMIT = "e2c846554192b67d27aab2bdacd30b43970ac6b3"
EXPECTED_MODEL_ID = "Meta-Llama-3.2-1B-Instruct"
EXPECTED_MODEL_SOURCE = "META_OFFICIAL_NATIVE_DISTRIBUTION"
EXPECTED_MODEL_CLASS = "LlamaForCausalLM"
EXPECTED_MODEL_TYPE = "llama"
EXPECTED_CONVERTED_HASH = "1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f"
EXPECTED_LOGICAL_BLOCKS = 16
EXPECTED_HIDDEN_SIZE = 2048
EXPECTED_CARRIER_API = "FORWARD_HOOK_DECODER_BLOCK_OUTPUT"
EXPECTED_CLASSES = ["logic", "causality", "analogy", "definition"]
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
EXPECTED_REFERENCE_MODELS = {
    "Qwen": {
        "model_id": "Qwen/Qwen3-1.7B",
        "model_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "num_hidden_layers": 28,
        "hidden_size": 2048,
    },
    "OLMo": {
        "model_id": "allenai/OLMo-2-0425-1B-Instruct",
        "model_revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
        "num_hidden_layers": 16,
        "hidden_size": 2048,
    },
}
EXPECTED_REFERENCE_PROFILES = {
    "QWEN_REFERENCE_PROFILE": {
        "distance_association_status": "POSITIVE_SUPPORTED",
        "dominance_status": "TARGET_DOMINANT",
        "low_d_recovery_status": "NOT_SUPPORTED",
    },
    "OLMO_REFERENCE_PROFILE": {
        "distance_association_status": "POSITIVE_SUPPORTED",
        "dominance_status": "SOURCE_DOMINANT",
        "low_d_recovery_status": "SUPPORTED",
    },
}
EXPECTED_NATIVE_HASHES = {
    "checklist.chk": "efefc79fc47ecce1c3e06a6ae77a4cddc7e6078f822efba22e4fc7f9da02400e",
    "consolidated.00.pth": "fc17d497df5e4175b3a8acb4f5865b26f7fc1b009b25bef814b95fde10e8a1f3",
    "params.json": "1d616a44f3cdac29b9288cf14718b76eb1bed56ed38be1f7e39b06ed139e3733",
    "tokenizer.model": "82e9d31979e92ab929cd544440f129d9ecd797b69e327f80f17e1c50d5551b55",
}
EXPECTED_DATASET_FILES = {
    "dataset": (
        "experiments/exp024/data/exp024_condition_panel_frozen.json",
        "46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404",
    ),
    "condition_panel": (
        "experiments/exp024/condition_panel_spec.json",
        "a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954",
    ),
    "data_schema": (
        "experiments/exp024/data_schema.json",
        "e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec",
    ),
    "frozen_manifest": (
        "experiments/exp024/exp024_frozen_manifest.json",
        "1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59",
    ),
    "exp024_preregistration": (
        "docs/experiments/EXP-024-PREREGISTRATION.md",
        "55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810",
    ),
}
FORBIDDEN_RESULT_PATHS = [
    EXP_DIR / "results",
    EXP_DIR / "exp027_results.json",
    EXP_DIR / "exp027_formal_result.json",
    EXP_DIR / "exp027_formal_run_authorization.json",
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


def route_profile(
    profile: dict[str, str],
    *,
    technical_valid: bool = True,
    measurement_valid: bool = True,
) -> tuple[str, str]:
    """Return (profile_route, result_status) using exact-match routing only."""
    if not technical_valid or not measurement_valid:
        return "NOT_ASSIGNED", "UNOBSERVED_OR_INVALID"
    tuple_value = (
        profile.get("distance_association_status"),
        profile.get("dominance_status"),
        profile.get("low_d_recovery_status"),
    )
    qwen_tuple = tuple(EXPECTED_REFERENCE_PROFILES["QWEN_REFERENCE_PROFILE"].values())
    olmo_tuple = tuple(EXPECTED_REFERENCE_PROFILES["OLMO_REFERENCE_PROFILE"].values())
    if tuple_value == qwen_tuple:
        return "EXP026_PROFILE_MATCH_QWEN", "VALID_REGISTERED_RESULT"
    if tuple_value == olmo_tuple:
        return "EXP026_PROFILE_MATCH_OLMO", "VALID_REGISTERED_RESULT"
    return "THIRD_REGISTERED_PROFILE", "VALID_REGISTERED_RESULT"


def validate(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(config.get("schema_version") == "1.0.0", "schema_version mismatch")
    check(config.get("experiment_id") == "EXP-027", "experiment_id mismatch")
    check(config.get("task_id") == EXPECTED_TASK_ID, "task_id mismatch")
    check(config.get("design_status") == EXPECTED_DESIGN_STATUS, "design_status mismatch")
    check(config.get("authority_commit") == EXPECTED_COMMIT, "authority_commit mismatch")
    check(config.get("freeze_commit") == EXPECTED_COMMIT, "freeze_commit mismatch")

    refs = config.get("reference_models", {})
    check(set(refs) == {"Qwen", "OLMo"}, "reference model set mismatch")
    for key, expected in EXPECTED_REFERENCE_MODELS.items():
        model = refs.get(key, {})
        for field, value in expected.items():
            check(model.get(field) == value, f"reference model {key} {field} mismatch")

    profiles = config.get("reference_profiles", {})
    check(profiles == EXPECTED_REFERENCE_PROFILES, "EXP-026 reference profiles mismatch")

    model = config.get("third_model_identity", {})
    check(model.get("model_id") == EXPECTED_MODEL_ID, "third model id mismatch")
    check(model.get("model_source") == EXPECTED_MODEL_SOURCE, "third model source mismatch")
    check(model.get("model_class") == EXPECTED_MODEL_CLASS, "third model class mismatch")
    check(model.get("model_type") == EXPECTED_MODEL_TYPE, "third model type mismatch")
    check(model.get("hidden_size") == EXPECTED_HIDDEN_SIZE, "third model hidden size mismatch")
    check(model.get("logical_decoder_blocks") == EXPECTED_LOGICAL_BLOCKS, "third model layer count mismatch")
    check(str(model.get("converted_model_hash", "")).casefold() == EXPECTED_CONVERTED_HASH.casefold(), "converted model hash mismatch")
    check(model.get("runtime_dtype") == "torch.bfloat16", "runtime dtype mismatch")

    check(config.get("logical_decoder_blocks") == EXPECTED_LOGICAL_BLOCKS, "logical decoder block count mismatch")
    check(config.get("carrier_api") == EXPECTED_CARRIER_API, "carrier API mismatch")

    carrier = config.get("carrier_semantics", {})
    check(carrier.get("final_hidden_state_semantics") == "POST_FINAL_NORM_CONFIRMED", "final hidden-state semantics mismatch")
    check(carrier.get("forbidden_carrier") == "outputs.hidden_states[-1]", "final-layer carrier boundary mismatch")
    check(carrier.get("logical_layer_l_module_path") == "model.model.layers[l]", "carrier module mapping mismatch")

    tokenizer = config.get("tokenizer_identity", {})
    check(tokenizer.get("vocab_size") == 128256, "tokenizer vocab mismatch")
    check(tokenizer.get("bos_token_id") == 128000, "tokenizer BOS mismatch")
    check(tokenizer.get("eos_token_id") == 128001, "tokenizer EOS mismatch")
    check(tokenizer.get("eot_token_id") == 128009, "tokenizer EOT mismatch")
    check(tokenizer.get("chat_template_used") is False, "chat template policy mismatch")

    invocation = config.get("tokenizer_invocation", {})
    check(invocation.get("add_special_tokens") is True, "tokenizer add_special_tokens mismatch")
    check(invocation.get("padding") is False, "tokenizer padding mismatch")
    check(invocation.get("truncation") is False, "tokenizer truncation mismatch")
    check(invocation.get("last_valid_token_rule") == "attention_mask_sum_minus_one", "last-valid-token rule mismatch")

    domain = config.get("source_target_domain", {})
    block_ids = list(range(EXPECTED_LOGICAL_BLOCKS))
    check(domain.get("source_indices") == block_ids, "source layer domain mismatch")
    check(domain.get("target_indices") == block_ids, "target layer domain mismatch")
    check(domain.get("layer_subset_shopping") is False, "layer subset shopping must be false")

    check(config.get("class_order") == EXPECTED_CLASSES, "class order mismatch")
    check(config.get("condition_order") == EXPECTED_CONDITIONS, "condition order mismatch")
    split = config.get("split_identity", {})
    check(split.get("partitions") == ["FIT", "DIAGNOSTIC", "EVAL"], "partition identity mismatch")
    check(split.get("allocation") == EXPECTED_ALLOCATION, "allocation mismatch")
    check(split.get("new_split_created") is False, "new split created must be false")
    check(split.get("item_filtering_allowed") is False, "item filtering must be false")

    hashes = config.get("dataset_hashes", {})
    for name, (rel_path, expected_hash) in EXPECTED_DATASET_FILES.items():
        key = {
            "dataset": "dataset_sha256",
            "condition_panel": "condition_panel_sha256",
            "data_schema": "data_schema_sha256",
            "frozen_manifest": "frozen_manifest_sha256",
            "exp024_preregistration": "exp024_preregistration_sha256",
        }[name]
        check(hashes.get(key) == expected_hash, f"dataset hash field mismatch: {key}")
        actual_path = ROOT / rel_path
        if not actual_path.exists():
            errors.append(f"dataset authority file missing: {rel_path}")
        elif sha256_file(actual_path) != expected_hash:
            errors.append(f"dataset authority file hash drift: {rel_path}")

    native_hashes = config.get("native_model_hashes", {})
    for name, expected_hash in EXPECTED_NATIVE_HASHES.items():
        item = native_hashes.get(name, {})
        check(str(item.get("sha256", "")).casefold() == expected_hash.casefold(), f"native model hash mismatch: {name}")
    check(config.get("native_md5_verified") is True, "native MD5 verification flag mismatch")

    readout = config.get("readout_semantics", {})
    check(readout.get("classifier") == "LogisticRegression", "classifier identity mismatch")
    check(readout.get("penalty") == "L2", "classifier penalty mismatch")
    check(readout.get("C") == 1.0, "classifier C mismatch")
    check(readout.get("max_iter") == 1000, "classifier max_iter mismatch")
    check(readout.get("recalibration_variant") == "A_mu_sigma", "recalibration variant mismatch")

    matrix = config.get("matrix_semantics", {})
    check(matrix.get("c0_definition"), "C0 definition missing")
    check(matrix.get("d_definition") == "Cself-C0", "D definition mismatch")
    check(matrix.get("r_definition") == "Ccal-C0", "R definition mismatch")
    check(matrix.get("condition_pooling") == "arithmetic_mean_over_all_10_conditions_equal_weight", "condition pooling mismatch")

    distance = config.get("distance_definition", {})
    check(distance.get("normalized_depth") == "layer_index/(num_layers-1)", "normalized depth formula mismatch")
    check(distance.get("pair_distance") == "abs(source_layer-target_layer)/(num_layers-1)", "pair distance formula mismatch")

    assoc = config.get("distance_association", {})
    check(assoc.get("statistic") == "Spearman_rho", "distance statistic mismatch")
    check(assoc.get("tie_handling") == "average_ranks", "distance tie handling mismatch")
    check(assoc.get("p_value_used") is False, "distance p-value policy mismatch")

    sdi = config.get("sdi", {})
    check(sdi.get("variance_convention") == "numpy.var(ddof=0)", "SDI variance convention mismatch")
    check(sdi.get("zero_denominator") == "SDI=0_status=NO_ROW_OR_COLUMN_VARIATION", "SDI zero-denominator rule mismatch")

    low_d = config.get("low_d", {})
    check(low_d.get("mask_definition") == "DIAGNOSTIC_Dbar_m(i,j)<=0_for_eligible_off_diagonal_pairs", "LOW-D mask definition mismatch")
    check(low_d.get("mask_frozen_across_bootstrap") is True, "LOW-D mask freeze mismatch")
    check(low_d.get("effective_n_zero") == "NOT_EVALUABLE", "LOW-D n=0 semantics mismatch")

    bootstrap = config.get("bootstrap", {})
    check(bootstrap.get("resampling_unit") == "source_family", "bootstrap resampling unit mismatch")
    check(bootstrap.get("statistical_unit") == "source_family_cluster", "bootstrap statistical unit mismatch")
    check(bootstrap.get("strata") == "condition", "bootstrap strata mismatch")
    check(bootstrap.get("bit_generator") == "numpy.random.PCG64", "bootstrap RNG mismatch")
    check(bootstrap.get("seed") == 20260819, "bootstrap seed mismatch")
    check(bootstrap.get("replicates") == 5000, "bootstrap replicate count mismatch")
    check(bootstrap.get("quantile_method") == "numpy.percentile_method_linear", "bootstrap quantile method mismatch")

    technical = config.get("technical_validity", {})
    check(technical.get("source_technical_floor") == 0.75, "source technical floor mismatch")
    check(technical.get("source_coverage_min_count") == 8, "source coverage min count mismatch")
    check(technical.get("source_coverage_min_fraction") == 0.5, "source coverage fraction mismatch")
    check(technical.get("source_coverage_min_normalized_depth_span") == 0.5, "source coverage span mismatch")

    measurement = config.get("measurement_validity", {})
    check(measurement.get("invalid_result_status") == "UNOBSERVED_OR_INVALID", "invalidity result status mismatch")
    check(measurement.get("invalid_profile_route") == "NOT_ASSIGNED", "invalidity profile route mismatch")
    check(measurement.get("measurement_failure_does_not_imply_absence") is True, "measurement failure boundary mismatch")

    routing = config.get("profile_routing", {})
    check(routing.get("method") == "EXACT_MATCH_ONLY", "profile routing method mismatch")
    check(routing.get("no_continuous_similarity") is True, "continuous similarity must be false")
    expected_rules = [
        "if_technical_or_measurement_invalid_then_RESULT_STATUS_UNOBSERVED_OR_INVALID_and_SCIENTIFIC_PROFILE_ROUTE_NOT_ASSIGNED",
        "if_llama_profile_exactly_equals_QWEN_REFERENCE_PROFILE_then_EXP026_PROFILE_MATCH_QWEN",
        "if_llama_profile_exactly_equals_OLMO_REFERENCE_PROFILE_then_EXP026_PROFILE_MATCH_OLMO",
        "else_THIRD_REGISTERED_PROFILE",
    ]
    check(routing.get("rules") == expected_rules, "profile routing rules mismatch")

    outcome = config.get("outcome_blind_progress_policy", {})
    for field in ("no_hidden_preview", "no_console_preview", "no_automatic_retry", "atomic_state_file"):
        check(outcome.get(field) is True, f"outcome-blind policy mismatch: {field}")

    formal = config.get("formal_run_policy", {})
    check(formal.get("formal_authorization_created") is False, "formal authorization flag must be false")
    check(formal.get("formal_run_performed") is False, "formal run flag must be false")
    check(formal.get("scientific_result_created") is False, "scientific result flag must be false")
    check(formal.get("next_task") == "102C_EXP027_ENGINEERING_AND_ADVERSARIAL_REVIEW", "next task mismatch")

    check(config.get("formal_authorization_created") is False, "top-level authorization flag must be false")
    check(config.get("formal_run_status") == "NOT_PERFORMED", "formal run status mismatch")
    check(config.get("scientific_result_status") == "NOT_CREATED", "scientific result status mismatch")
    check(config.get("unresolved_primary_critical_fields") == [], "unresolved primary critical fields must be empty")

    return errors


def validate_immutable_content(config_path: Path = CONFIG_PATH) -> list[str]:
    """Validate only the frozen preregistration/design content and expected hashes.

    This is the content-only authority check used by the formal runner after a
    valid authorization may exist. It intentionally does not check the pristine
    run-state absence enforced by :func:`validate_file`.
    """
    if not config_path.exists():
        return ["missing exp027_frozen_design.json"]
    try:
        config = read_json(config_path)
    except Exception as exc:  # pragma: no cover
        return [f"config parse failure: {exc}"]
    return validate(config)


def validate_file(config_path: Path = CONFIG_PATH, root: Path = ROOT) -> list[str]:
    errors = validate_immutable_content(config_path)
    for path in FORBIDDEN_RESULT_PATHS:
        if path.exists():
            errors.append(f"forbidden result/authorization path exists: {path}")
    return errors


def main() -> int:
    errors = validate_file()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("EXP027_PREREGISTRATION_VALIDATION = FAIL")
        return 1
    print("EXP027_PREREGISTRATION_VALIDATION = PASS")
    print("EXP027_102B_PREREGISTRATION_FROZEN = true")
    print("EXP027_FROZEN_DESIGN_VALIDATED = true")
    print("EXP027_FORMAL_AUTHORIZED = false")
    print("EXP027_FORMAL_RUN_PERFORMED = false")
    print("EXP027_SCIENTIFIC_RESULT_CREATED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
