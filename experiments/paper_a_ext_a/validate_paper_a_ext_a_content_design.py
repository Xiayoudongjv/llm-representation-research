#!/usr/bin/env python3
"""Static content-design validator for Paper-A EXT-A.

Read-only. Verifies the V1 protocol authority is unchanged, the V2 content
design SHA binding is exact, and no real panel/result/authorization artifacts
exist. It does not load models, access scientific data, or create results.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]

PROTOCOL_PATH = EXP_DIR / "paper_a_ext_a_frozen_config.json"
DESIGN_PATH = EXP_DIR / "paper_a_ext_a_panel_content_design.json"
BINDING_PATH = EXP_DIR / "paper_a_ext_a_content_design_binding.json"

EXPECTED_PROTOCOL_SHA256 = "78e58c43c7fabfafaa03084ef17f9c5ff4c02665d242aa57b9f70a9d3b793e5d"
EXPECTED_DESIGN_SHA256 = "82dd8d944691c49d5586defdf999d0afdb70f95bd5b4f568ffa5c72642829ce6"

EXPECTED_TASK_FAMILIES = [
    "exta_tf_spatial",
    "exta_tf_temporal",
    "exta_tf_quantitative",
    "exta_tf_mereological",
]
EXPECTED_SEMANTIC_RELATIONS = [
    "exta_rel_spatial_configuration",
    "exta_rel_temporal_order",
    "exta_rel_quantitative_comparison",
    "exta_rel_part_whole",
]
EXPECTED_CONDITIONS = [
    "xa01_synonym_variant",
    "xa02_constituent_reorder",
    "xa03_redundancy_reduction",
    "xa04_explicative_elaboration",
    "xa05_overt_relation_marker",
    "xa06_implicit_relation_marker",
    "xa07_precise_register",
    "xa08_colloquial_register",
    "xa09_neutral_context_prefix",
    "xa10_coreference_shift",
]

FORBIDDEN_PATHS = [
    EXP_DIR / "real_panel.json",
    EXP_DIR / "source_bank.json",
    EXP_DIR / "candidate_items.json",
    EXP_DIR / "fit_data.json",
    EXP_DIR / "diag_data.json",
    EXP_DIR / "eval_data.json",
    EXP_DIR / "results",
    EXP_DIR / "formal_authorization",
    EXP_DIR / "formal_run_authorization.json",
    EXP_DIR / "scientific_result.json",
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


def check(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate() -> list[str]:
    errors: list[str] = []

    for path, expected_hash, label in [
        (PROTOCOL_PATH, EXPECTED_PROTOCOL_SHA256, "protocol"),
        (DESIGN_PATH, EXPECTED_DESIGN_SHA256, "content design"),
    ]:
        if not path.exists():
            errors.append(f"missing {label} file: {path}")
            continue
        actual = sha256_file(path)
        check(actual == expected_hash, f"{label} SHA mismatch: {actual}", errors)

    if not BINDING_PATH.exists():
        errors.append("missing content design binding file")
        return errors

    try:
        binding = read_json(BINDING_PATH)
    except Exception as exc:
        return [f"binding parse failure: {exc}"]

    check(binding.get("protocol_sha256") == EXPECTED_PROTOCOL_SHA256, "binding protocol hash mismatch", errors)
    check(binding.get("panel_content_design_sha256") == EXPECTED_DESIGN_SHA256, "binding design hash mismatch", errors)
    check(binding.get("protocol_authority_unchanged") is True, "protocol authority must be unchanged", errors)
    check(binding.get("measurement_contract_modified") is False, "measurement contract must be unmodified", errors)
    check(binding.get("statistical_contract_modified") is False, "statistical contract must be unmodified", errors)
    check(binding.get("outcome_routing_modified") is False, "outcome routing must be unmodified", errors)
    check(binding.get("model_contract_modified") is False, "model contract must be unmodified", errors)
    check(binding.get("carrier_contract_modified") is False, "carrier contract must be unmodified", errors)

    try:
        protocol = read_json(PROTOCOL_PATH)
        design = read_json(DESIGN_PATH)
    except Exception as exc:
        return [f"JSON parse failure: {exc}"]

    check(protocol.get("protocol_status") == "FINAL_FROZEN_PRE_DATA_PROTOCOL", "protocol status mismatch", errors)
    check(protocol.get("carrier_rules_frozen") is True, "carrier rules not frozen", errors)
    check(protocol.get("measurement_contract_frozen") is True, "measurement contract not frozen", errors)
    check(protocol.get("statistical_contract_frozen") is True, "statistical contract not frozen", errors)
    check(protocol.get("outcome_routing_frozen") is True, "outcome routing not frozen", errors)
    check(protocol.get("one_extension_stopping_rule") is True, "one-extension rule not frozen", errors)

    check(design.get("status") == "FINAL_FROZEN_PRE_DATA_V2_CONTENT_DESIGN", "content design status mismatch", errors)
    check(design.get("panel_content_status") == "PANEL_CONTENT_NOT_YET_CREATED", "panel content status mismatch", errors)
    check(design.get("protocol_sha256") == EXPECTED_PROTOCOL_SHA256, "design protocol hash binding mismatch", errors)
    check(design.get("cross_task_independence_level") == "NEW_TASK_FAMILIES_AND_NEW_SEMANTIC_RELATIONS", "independence level mismatch", errors)
    check(design.get("panel_authority_route") == "HUMAN_AUTHORED_SOURCE_BANK_DETERMINISTIC_TRANSFORMATION", "panel route mismatch", errors)

    task_families = [item.get("task_family_id") for item in design.get("task_families", [])]
    check(task_families == EXPECTED_TASK_FAMILIES, "task family set mismatch", errors)

    relations = [item.get("relation_id") for item in design.get("semantic_relations", [])]
    check(relations == EXPECTED_SEMANTIC_RELATIONS, "semantic relation set mismatch", errors)
    check(design.get("conditions") == EXPECTED_CONDITIONS, "condition set mismatch", errors)

    authoring = design.get("authoring_contract", {})
    check(authoring.get("authoring_scheme") == "FIXED_COUNT_DIRECT_AUTHORING", "authoring scheme mismatch", errors)
    check(authoring.get("surplus_policy") == "FIXED_COUNT_DIRECT_AUTHORING", "surplus policy mismatch", errors)

    panel = design.get("panel_structure", {})
    check(panel.get("source_bank_size") == 880, "source bank size mismatch", errors)
    check(panel.get("final_panel_size") == 1760, "final panel size mismatch", errors)
    check(panel.get("fit_source_families") == 240, "FIT source families mismatch", errors)
    check(panel.get("diag_source_families") == 320, "DIAG source families mismatch", errors)
    check(panel.get("eval_source_families") == 320, "EVAL source families mismatch", errors)

    flags = design.get("hard_flags", {})
    for name in [
        "REAL_EXT_A_SOURCE_BANK_CREATED",
        "REAL_EXT_A_PANEL_CREATED",
        "REAL_EXT_A_CANDIDATE_ITEMS_CREATED",
        "REAL_EXT_A_FIT_DATA_CREATED",
        "REAL_EXT_A_DIAG_DATA_CREATED",
        "REAL_EXT_A_EVAL_DATA_CREATED",
        "REAL_EXT_A_HIDDEN_STATES_ACCESSED",
        "REAL_EXT_A_MODEL_INFERENCE_PERFORMED",
        "REAL_EXT_A_RESULTS_CREATED",
        "REAL_EXT_A_AUTHORIZATION_CREATED",
        "PAPER_A_MANUSCRIPT_MODIFIED",
        "EXP028_MODIFIED",
    ]:
        check(flags.get(name) is False, f"hard flag {name} must be false", errors)

    check(design.get("llm_generation_firewall", {}).get("llm_generated_source_bank_allowed") is False, "LLM generation must be false", errors)
    check(design.get("embedding_selection_firewall", {}).get("embedding_selection_allowed") is False, "embedding selection must be false", errors)
    check(design.get("next_task") == "PA-EXT-A-003_GENERATOR_VALIDATOR_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION", "next task mismatch", errors)

    for path in FORBIDDEN_PATHS:
        if path.exists():
            errors.append(f"forbidden panel/result/authorization path exists: {path}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("PAPER_A_EXT_A_CONTENT_DESIGN_VALIDATION = FAIL")
        return 1
    print("PAPER_A_EXT_A_CONTENT_DESIGN_VALIDATION = PASS")
    print("PAPER_A_EXT_A_PREREGISTRATION_STATE = FINAL_FROZEN_PRE_DATA_V2_CONTENT_DESIGN")
    print("PAPER_A_EXT_A_PANEL_CONTENT_STATUS = PANEL_CONTENT_NOT_YET_CREATED")
    print("PAPER_A_EXT_A_REAL_PANEL_CREATED = false")
    print("PAPER_A_EXT_A_SOURCE_BANK_CREATED = false")
    print("PAPER_A_EXT_A_MODEL_INFERENCE_PERFORMED = false")
    print("PAPER_A_EXT_A_RESULTS_CREATED = false")
    print("PAPER_A_EXT_A_AUTHORIZATION_CREATED = false")
    print("PAPER_A_MANUSCRIPT_MODIFIED = false")
    print("EXP028_MODIFIED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())