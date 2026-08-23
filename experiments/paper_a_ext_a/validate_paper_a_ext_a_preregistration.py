#!/usr/bin/env python3
"""Static preregistration validator for Paper-A EXT-A.

Read-only. Verifies the frozen pre-data protocol config and the absence of
real panel/result/authorization artifacts. It does not load models, access
scientific data, or create results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]
CONFIG_PATH = EXP_DIR / "paper_a_ext_a_frozen_config.json"

EXPECTED_EXPERIMENT_ID = "PAPER-A-EXT-A"
EXPECTED_TASK_ID = "PA-EXT-A-001"
EXPECTED_PROTOCOL_STATUS = "FINAL_FROZEN_PRE_DATA_PROTOCOL"
EXPECTED_PANEL_STATUS = "PANEL_CONTENT_NOT_YET_CREATED"
EXPECTED_AUTHORITY_COMMIT = "85c1012164dbcef3b34c699bebd11f06a462a960"
EXPECTED_INDEPENDENCE = "NEW_TASK_FAMILIES_AND_NEW_SEMANTIC_RELATIONS"
EXPECTED_PANEL_ROUTE = "HUMAN_AUTHORED_SOURCE_BANK_DETERMINISTIC_TRANSFORMATION"

EXPECTED_MODELS = {
    "Qwen": {
        "model_id": "Qwen/Qwen3-1.7B",
        "model_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "num_hidden_layers": 28,
    },
    "OLMo": {
        "model_id": "allenai/OLMo-2-0425-1B-Instruct",
        "model_revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
        "num_hidden_layers": 16,
    },
    "Llama": {
        "model_id": "Meta-Llama-3.2-1B-Instruct",
        "converted_model_hash": "1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f",
        "logical_decoder_blocks": 16,
        "final_hidden_state_semantics": "POST_FINAL_NORM_CONFIRMED",
        "forbidden_carrier": "outputs.hidden_states[-1]",
    },
}

EXPECTED_REFERENCE_PROFILES = {
    "Qwen": {
        "distance_association_status": "POSITIVE_SUPPORTED",
        "dominance_status": "TARGET_DOMINANT",
        "low_d_recovery_status": "NOT_SUPPORTED",
    },
    "OLMo": {
        "distance_association_status": "POSITIVE_SUPPORTED",
        "dominance_status": "SOURCE_DOMINANT",
        "low_d_recovery_status": "SUPPORTED",
    },
    "Llama": {
        "distance_association_status": "POSITIVE_SUPPORTED",
        "dominance_status": "TARGET_DOMINANT",
        "low_d_recovery_status": "SUPPORTED",
    },
}

FORBIDDEN_PATHS = [
    EXP_DIR / "results",
    EXP_DIR / "real_panel.json",
    EXP_DIR / "candidate_items.json",
    EXP_DIR / "fit_data.json",
    EXP_DIR / "diag_data.json",
    EXP_DIR / "eval_data.json",
    EXP_DIR / "formal_authorization",
    EXP_DIR / "formal_run_authorization.json",
    EXP_DIR / "results.json",
]


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    check(config.get("schema_version") == "1.0.0", "schema_version mismatch", errors)
    check(config.get("experiment_id") == EXPECTED_EXPERIMENT_ID, "experiment_id mismatch", errors)
    check(config.get("task_id") == EXPECTED_TASK_ID, "task_id mismatch", errors)
    check(config.get("protocol_status") == EXPECTED_PROTOCOL_STATUS, "protocol_status mismatch", errors)
    check(config.get("panel_content_status") == EXPECTED_PANEL_STATUS, "panel_content_status mismatch", errors)
    check(config.get("authority_commit") == EXPECTED_AUTHORITY_COMMIT, "authority_commit mismatch", errors)
    check(config.get("cross_task_independence_level") == EXPECTED_INDEPENDENCE, "cross_task_independence_level mismatch", errors)
    check(config.get("original_model_count") == 3, "original_model_count mismatch", errors)
    check(config.get("new_model_added") is False, "new_model_added must be false", errors)
    check(config.get("model_set_rule") == "THREE_MODELS_ONLY_NO_FOURTH_MODEL", "model_set_rule mismatch", errors)

    models = config.get("models", {})
    for key, expected in EXPECTED_MODELS.items():
        model = models.get(key, {})
        for field, value in expected.items():
            check(model.get(field) == value, f"{key} model {field} mismatch", errors)

    profiles = config.get("reference_profiles", {})
    check(profiles == EXPECTED_REFERENCE_PROFILES, "reference_profiles mismatch", errors)

    check(config.get("carrier_rules_frozen") is True, "carrier_rules_frozen must be true", errors)
    check(config.get("measurement_contract_frozen") is True, "measurement_contract_frozen must be true", errors)
    check(config.get("statistical_contract_frozen") is True, "statistical_contract_frozen must be true", errors)
    check(config.get("outcome_routing_frozen") is True, "outcome_routing_frozen must be true", errors)
    check(config.get("one_extension_stopping_rule") is True, "one_extension_stopping_rule must be true", errors)
    check(config.get("new_panel_authority_route") == EXPECTED_PANEL_ROUTE, "panel authority route mismatch", errors)

    stats = config.get("statistical_contract", {})
    check(stats.get("distance_statistic") == "Spearman_rho", "distance statistic mismatch", errors)
    check(stats.get("sdi_variance_convention") == "numpy.var(ddof=0)", "SDI variance convention mismatch", errors)
    check(stats.get("bootstrap_design") == "condition_stratified_source_family_cluster_bootstrap", "bootstrap design mismatch", errors)
    check(stats.get("resampling_unit") == "source_family", "resampling unit mismatch", errors)
    check(stats.get("statistical_unit") == "source_family_cluster", "statistical unit mismatch", errors)
    check(stats.get("bit_generator") == "numpy.random.PCG64", "RNG mismatch", errors)
    check(stats.get("seed") == 20260819, "bootstrap seed mismatch", errors)
    check(stats.get("replicates") == 5000, "bootstrap replicates mismatch", errors)
    check(stats.get("quantile_method") == "numpy.percentile_method_linear", "quantile method mismatch", errors)

    routing = config.get("outcome_routing", {})
    check(routing.get("method") == "EXACT_COMPONENT_MATCH", "outcome routing method mismatch", errors)
    check(routing.get("continuous_profile_similarity") is False, "continuous profile similarity must be false", errors)
    check(routing.get("no_majority_vote") is True, "majority vote must be false", errors)
    check(routing.get("no_two_thirds_rescue") is True, "two-thirds rescue must be false", errors)
    check(routing.get("no_model_drop") is True, "model drop must be false", errors)
    check(routing.get("no_replication_success_only") is True, "replication success-only must be false", errors)

    firewalls = config.get("firewalls", {})
    check(firewalls.get("exp024_anti_rescue_firewall") is True, "EXP-024 firewall must be true", errors)
    check(firewalls.get("exp024_remains_negative_result") is True, "EXP-024 must remain negative result", errors)
    check(firewalls.get("exp028_firewall") is True, "EXP-028 firewall must be true", errors)
    check(firewalls.get("exp028_modified") is False, "EXP-028 modified must be false", errors)
    check(firewalls.get("paper_a_manuscript_modified") is False, "Paper-A manuscript modified must be false", errors)

    flags = config.get("hard_flags", {})
    for name in [
        "REAL_EXT_A_PANEL_CREATED",
        "REAL_EXT_A_CANDIDATE_ITEMS_CREATED",
        "REAL_EXT_A_FIT_DATA_CREATED",
        "REAL_EXT_A_DIAG_DATA_CREATED",
        "REAL_EXT_A_EVAL_DATA_CREATED",
        "REAL_EXT_A_MODEL_INFERENCE_PERFORMED",
        "REAL_EXT_A_HIDDEN_STATES_ACCESSED",
        "REAL_EXT_A_RESULTS_CREATED",
        "REAL_EXT_A_AUTHORIZATION_CREATED",
        "PAPER_A_MANUSCRIPT_MODIFIED",
        "EXP028_MODIFIED",
    ]:
        check(flags.get(name) is False, f"hard flag {name} must be false", errors)

    check(config.get("next_task") == "PA-EXT-A-002_PANEL_CONTENT_DESIGN_AND_FREEZE", "next task mismatch", errors)
    return errors


def validate_file() -> list[str]:
    if not CONFIG_PATH.exists():
        return ["missing paper_a_ext_a_frozen_config.json"]
    try:
        config = read_json(CONFIG_PATH)
    except Exception as exc:
        return [f"config parse failure: {exc}"]
    errors = validate(config)
    for path in FORBIDDEN_PATHS:
        if path.exists():
            errors.append(f"forbidden panel/result/authorization path exists: {path}")
    return errors


def main() -> int:
    errors = validate_file()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("PAPER_A_EXT_A_PREREGISTRATION_VALIDATION = FAIL")
        return 1
    print("PAPER_A_EXT_A_PREREGISTRATION_VALIDATION = PASS")
    print("PAPER_A_EXT_A_PROTOCOL_STATE = FINAL_FROZEN_PRE_DATA_PROTOCOL")
    print("PAPER_A_EXT_A_PANEL_CONTENT_STATUS = PANEL_CONTENT_NOT_YET_CREATED")
    print("PAPER_A_EXT_A_REAL_PANEL_CREATED = false")
    print("PAPER_A_EXT_A_MODEL_INFERENCE_PERFORMED = false")
    print("PAPER_A_EXT_A_RESULTS_CREATED = false")
    print("PAPER_A_EXT_A_AUTHORIZATION_CREATED = false")
    print("PAPER_A_MANUSCRIPT_MODIFIED = false")
    print("EXP028_MODIFIED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())