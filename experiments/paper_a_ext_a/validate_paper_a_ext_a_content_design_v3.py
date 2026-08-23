#!/usr/bin/env python3
"""Static V3 content-design validator for Paper-A EXT-A.

Read-only. Verifies the V1 protocol is unchanged, V2 history is preserved,
and V3 content-production authority is hash-bound with no real panel data.
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
V2_DESIGN_PATH = EXP_DIR / "paper_a_ext_a_panel_content_design.json"
V3_DESIGN_PATH = EXP_DIR / "paper_a_ext_a_panel_content_design_v3.json"
V3_BINDING_PATH = EXP_DIR / "paper_a_ext_a_content_design_v3_binding.json"

EXPECTED_PROTOCOL_SHA256 = "78e58c43c7fabfafaa03084ef17f9c5ff4c02665d242aa57b9f70a9d3b793e5d"
EXPECTED_V2_SHA256 = "82dd8d944691c49d5586defdf999d0afdb70f95bd5b4f568ffa5c72642829ce6"
EXPECTED_V3_SHA256 = "205376bbd8704862de2cafeb1fd09719b498688532e6c54aec3a2326b71f0462"

EXPECTED_TASK_FAMILIES = [
    "exta_tf_spatial",
    "exta_tf_temporal",
    "exta_tf_quantitative",
    "exta_tf_mereological",
]
EXPECTED_RELATIONS = [
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
    EXP_DIR / "real_semantic_asset_bank.json",
    EXP_DIR / "semantic_asset_bank.json",
    EXP_DIR / "real_source_bank.json",
    EXP_DIR / "source_bank.json",
    EXP_DIR / "real_panel.json",
    EXP_DIR / "candidate_items.json",
    EXP_DIR / "fit_data.json",
    EXP_DIR / "diag_data.json",
    EXP_DIR / "eval_data.json",
    EXP_DIR / "results",
    EXP_DIR / "formal_authorization",
    EXP_DIR / "formal_run_authorization.json",
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

    for path, expected, label in [
        (PROTOCOL_PATH, EXPECTED_PROTOCOL_SHA256, "protocol"),
        (V2_DESIGN_PATH, EXPECTED_V2_SHA256, "V2 content design"),
        (V3_DESIGN_PATH, EXPECTED_V3_SHA256, "V3 content design"),
    ]:
        if not path.exists():
            errors.append(f"missing {label} file: {path}")
            continue
        actual = sha256_file(path)
        check(actual == expected, f"{label} SHA mismatch: {actual}", errors)

    if not V3_BINDING_PATH.exists():
        errors.append("missing V3 binding file")
        return errors

    try:
        binding = read_json(V3_BINDING_PATH)
        protocol = read_json(PROTOCOL_PATH)
        v3 = read_json(V3_DESIGN_PATH)
    except Exception as exc:
        return [f"JSON parse failure: {exc}"]

    check(binding.get("protocol_sha256") == EXPECTED_PROTOCOL_SHA256, "binding protocol hash mismatch", errors)
    check(binding.get("panel_content_design_sha256") == EXPECTED_V3_SHA256, "binding V3 design hash mismatch", errors)
    check(binding.get("predecessor_content_design_sha256") == EXPECTED_V2_SHA256, "binding predecessor V2 hash mismatch", errors)
    check(binding.get("protocol_authority_unchanged") is True, "protocol authority must be unchanged", errors)
    for key in [
        "measurement_contract_modified",
        "statistical_contract_modified",
        "outcome_routing_modified",
        "model_contract_modified",
        "carrier_contract_modified",
        "task_family_set_modified",
        "semantic_relation_set_modified",
        "dataset_shape_modified",
    ]:
        check(binding.get(key) is False, f"{key} must be false", errors)

    check(protocol.get("protocol_status") == "FINAL_FROZEN_PRE_DATA_PROTOCOL", "protocol status mismatch", errors)
    check(protocol.get("carrier_rules_frozen") is True, "carrier rules not frozen", errors)
    check(protocol.get("measurement_contract_frozen") is True, "measurement contract not frozen", errors)
    check(protocol.get("statistical_contract_frozen") is True, "statistical contract not frozen", errors)
    check(protocol.get("outcome_routing_frozen") is True, "outcome routing not frozen", errors)

    check(v3.get("status") == "FINAL_FROZEN_PRE_DATA_V3_CONTENT_PRODUCTION_SIMPLIFICATION", "V3 status mismatch", errors)
    check(v3.get("panel_content_status") == "PANEL_CONTENT_NOT_YET_CREATED", "V3 panel status mismatch", errors)
    check(v3.get("panel_authority_route") == "STRUCTURED_SEMANTIC_ASSET_BANK_PLUS_DETERMINISTIC_COMPOSITION_RENDERING", "V3 panel route mismatch", errors)
    check(v3.get("predecessor_content_design_sha256") == EXPECTED_V2_SHA256, "V3 predecessor hash mismatch", errors)
    check(v3.get("protocol_sha256") == EXPECTED_PROTOCOL_SHA256, "V3 protocol hash mismatch", errors)

    task_families = [item.get("task_family_id") for item in v3.get("task_families", [])]
    check(task_families == EXPECTED_TASK_FAMILIES, "V3 task family set mismatch", errors)
    relations = [item.get("relation_id") for item in v3.get("semantic_relations", [])]
    check(relations == EXPECTED_RELATIONS, "V3 relation set mismatch", errors)
    check(v3.get("conditions") == EXPECTED_CONDITIONS, "V3 condition set mismatch", errors)

    panel = v3.get("panel_structure", {})
    check(panel.get("source_bank_size") == 880, "source bank size mismatch", errors)
    check(panel.get("final_panel_size") == 1760, "final panel size mismatch", errors)
    check(panel.get("fit_source_families") == 240, "FIT source families mismatch", errors)
    check(panel.get("diag_source_families") == 320, "DIAG source families mismatch", errors)
    check(panel.get("eval_source_families") == 320, "EVAL source families mismatch", errors)

    flags = v3.get("hard_flags", {})
    for name in [
        "REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED",
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

    check(v3.get("next_task") == "PA-EXT-A-003_GENERATOR_VALIDATOR_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION", "next task mismatch", errors)

    for path in FORBIDDEN_PATHS:
        if path.exists():
            errors.append(f"forbidden panel/result/authorization path exists: {path}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("PAPER_A_EXT_A_CONTENT_DESIGN_V3_VALIDATION = FAIL")
        return 1
    print("PAPER_A_EXT_A_CONTENT_DESIGN_V3_VALIDATION = PASS")
    print("PAPER_A_EXT_A_PREREGISTRATION_STATE = FINAL_FROZEN_PRE_DATA_V3_CONTENT_PRODUCTION_SIMPLIFICATION")
    print("PAPER_A_EXT_A_PANEL_CONTENT_STATUS = PANEL_CONTENT_NOT_YET_CREATED")
    print("PAPER_A_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false")
    print("PAPER_A_EXT_A_SOURCE_BANK_CREATED = false")
    print("PAPER_A_EXT_A_PANEL_CREATED = false")
    print("PAPER_A_EXT_A_MODEL_INFERENCE_PERFORMED = false")
    print("PAPER_A_EXT_A_RESULTS_CREATED = false")
    print("PAPER_A_EXT_A_AUTHORIZATION_CREATED = false")
    print("PAPER_A_MANUSCRIPT_MODIFIED = false")
    print("EXP028_MODIFIED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())