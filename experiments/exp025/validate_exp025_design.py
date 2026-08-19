#!/usr/bin/env python3
"""Deterministic design validator for the frozen EXP-025 design assets.

This validator checks frozen model identity, inherited EXP-024 authority
identities, frozen checkpoint mapping, firewall flags, and absence of formal
scientific artifacts. It does not import or load any model or tokenizer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections import Counter


ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXP025_DIR = os.path.join(ROOT, "experiments", "exp025")
DEFAULT_CONFIG = os.path.join(EXP025_DIR, "exp025_frozen_config.json")

EXPECTED_MODEL_REVISION = "48d788eca847d4d7548f375ad03d3c9312f6139e"
EXPECTED_MODEL_ID = "allenai/OLMo-2-0425-1B-Instruct"
EXPECTED_MODEL_FAMILY = "OLMo2"
EXPECTED_ROLE = "CROSS_MODEL_ROUTING_EXPERIMENT"
EXPECTED_CALIBRATION_VARIANTS = ["A0", "A_mu", "A_sigma", "A_mu_sigma"]

RESULT_CANDIDATES = [
    os.path.join(EXP025_DIR, "results", "exp025_results.json"),
    os.path.join(EXP025_DIR, "exp025_formal_result.json"),
    os.path.join(EXP025_DIR, "exp025_formal_run_authorization.json"),
]

FORBIDDEN_PREREGISTRATION_TOKENS = [
    "TBD",
    "TODO",
    "PLACEHOLDER",
    "DRAFT_NOT_FROZEN",
    "ACTIVE_PROSPECTIVE_NOT_TESTED",
    "PROTOCOL_DRAFTED_NOT_FROZEN",
    "EXP025_FORMAL_RUN_PERFORMED = true",
    "EXP025_SCIENTIFIC_RESULT_CREATED = true",
]


def sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate frozen EXP-025 design assets.")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    args = parser.parse_args()

    errors: list[str] = []

    if not os.path.exists(args.config):
        print("EXP025_DESIGN_VALIDATION = FAIL")
        print(f"ERROR: config not found: {args.config}")
        return 1

    try:
        with open(args.config, "r", encoding="utf-8") as handle:
            config = json.load(handle)
    except Exception as exc:
        print("EXP025_DESIGN_VALIDATION = FAIL")
        print(f"ERROR: config does not parse: {exc}")
        return 1

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    def config_path(key: str) -> str:
        value = config.get(key)
        if not isinstance(value, str):
            raise ValueError(f"Config field {key!r} is missing or not a string.")
        return os.path.join(ROOT, value)

    # Core config fields.
    require(config.get("schema_version") == "1.0.0", "Config schema_version is not 1.0.0.")
    require(config.get("experiment") == "EXP-025", "Config experiment is not EXP-025.")
    require(config.get("design_status") == "FROZEN_DESIGN_NOT_RUN", "Design status is not FROZEN_DESIGN_NOT_RUN.")
    require(config.get("role") == EXPECTED_ROLE, "EXP-025 role is not CROSS_MODEL_ROUTING_EXPERIMENT.")
    require(config.get("primary_model") == EXPECTED_MODEL_ID, "Primary model is not the frozen OLMo Instruct model.")
    require(config.get("model_revision") == EXPECTED_MODEL_REVISION, "Model revision is not frozen.")
    require(config.get("model_family") == EXPECTED_MODEL_FAMILY, "Model family is not OLMo2.")
    require(config.get("model_locked") is True, "Model locked flag is not true.")
    require(config.get("model_shopping_prohibited") is True, "Model-shopping prohibition is not true.")
    require(config.get("qwen_readout_reused") is False, "Qwen readout reuse flag must be false.")
    require(config.get("dataset_reused_from_exp024") is True, "Dataset reuse flag must be true.")
    require(config.get("fit_diag_eval_firewall") is True, "FIT/DIAG/EVAL firewall flag must be true.")
    require(config.get("layer_sweep_allowed") is False, "Layer sweep must be false.")
    require(config.get("checkpoint_mapping_frozen") is True, "Checkpoint mapping must be frozen.")
    require(config.get("formal_run_performed") is False, "Formal run must not be performed.")
    require(config.get("scientific_result_created") is False, "Scientific result must not be created.")
    require(config.get("ready_for_engineering_qualification") is True, "Design is not marked ready for engineering qualification.")

    require(config.get("primary_rq1") == "FIXED_READOUT_DEGRADATION_CROSS_MODEL", "Primary RQ1 mismatch.")
    require(config.get("primary_rq2") == "FIT_ONLY_RECALIBRATION_RECOVERY_CROSS_MODEL", "Primary RQ2 mismatch.")
    require(config.get("susceptibility_rq") == "SECONDARY", "Susceptibility RQ is not secondary.")
    require(config.get("global_routing_table_frozen") is True, "Global routing table must be frozen.")

    require(config.get("kan_operator_included") is False, "KAN operator must not be included.")
    require(config.get("invariant_included") is False, "Invariant must not be included.")
    require(config.get("functional_binding_included") is False, "Functional binding must not be included.")

    calibration_variants = config.get("calibration_variants")
    require(isinstance(calibration_variants, list), "Calibration variants must be a list.")
    if isinstance(calibration_variants, list):
        require(calibration_variants == EXPECTED_CALIBRATION_VARIANTS, "Calibration variants are not exactly A0/A_mu/A_sigma/A_mu_sigma.")

    # Inherited EXP-024 authorities.
    authority_checks = [
        ("inherited_dataset_path", "inherited_dataset_sha256", "Inherited dataset"),
        ("condition_panel_path", "condition_panel_sha256", "Condition panel"),
        ("data_schema_path", "data_schema_sha256", "Data schema"),
        ("frozen_manifest_path", "frozen_manifest_sha256", "Frozen manifest"),
        ("preregistration_path", "preregistration_sha256", "EXP-024 preregistration"),
    ]
    for path_key, hash_key, label in authority_checks:
        path = config_path(path_key)
        expected_hash = config.get(hash_key)
        require(os.path.exists(path), f"{label} does not exist: {path}")
        if os.path.exists(path):
            require(sha256_file(path) == expected_hash, f"{label} SHA mismatch with config.")

    # EXP-025 design files.
    exp025_prereg_path = config_path("exp025_preregistration_path")
    model_selection_path = config_path("model_selection_path")
    checkpoint_mapping_path = config_path("checkpoint_mapping_path")
    for path, label in [
        (exp025_prereg_path, "EXP-025 preregistration"),
        (model_selection_path, "Model selection"),
        (checkpoint_mapping_path, "Checkpoint mapping"),
    ]:
        require(os.path.exists(path), f"{label} does not exist: {path}")

    prereg_text = read_text(exp025_prereg_path) if os.path.exists(exp025_prereg_path) else ""
    require("FROZEN_DESIGN_NOT_RUN" in prereg_text, "Preregistration is not frozen-design-not-run.")
    require(EXPECTED_MODEL_REVISION in prereg_text, "Preregistration does not record exact model revision.")
    require("CROSS_MODEL_ROUTING_EXPERIMENT" in prereg_text, "Preregistration does not record experiment role.")
    require("S_diag(c)" in prereg_text, "Preregistration does not define S_diag(c).")
    require("G_eval(c)" in prereg_text, "Preregistration does not define G_eval(c).")
    require("block9_pre_final_rmsnorm" in prereg_text, "Preregistration does not freeze OLMo reference checkpoint.")
    require("block15_pre_final_rmsnorm" in prereg_text, "Preregistration does not freeze OLMo final checkpoint.")
    require("block15_post_final_rmsnorm" in prereg_text, "Preregistration does not freeze post-final descriptive checkpoint.")
    require("FIXED_READOUT_DEGRADATION_CROSS_MODEL" in prereg_text, "Preregistration does not record primary RQ1.")
    require("FIT_ONLY_RECALIBRATION_RECOVERY_CROSS_MODEL" in prereg_text, "Preregistration does not record primary RQ2.")
    require("SECONDARY" in prereg_text, "Preregistration does not mark susceptibility RQ secondary.")
    require("STRENGTHENED" in prereg_text and "MODEL-DEPENDENT OPERATOR SUFFICIENCY" in prereg_text, "Preregistration does not freeze the routing table.")
    require("0.75" in prereg_text, "Preregistration does not record measurement qualification usability threshold.")
    require("EXP025_FORMAL_RUN_PERFORMED = false" in prereg_text, "Preregistration access audit does not mark formal run false.")
    require("EXP025_SCIENTIFIC_RESULT_CREATED = false" in prereg_text, "Preregistration access audit does not mark scientific result false.")
    for token in FORBIDDEN_PREREGISTRATION_TOKENS:
        require(token not in prereg_text, f"Forbidden placeholder/draft token remains: {token}")

    if os.path.exists(model_selection_path):
        selection_text = read_text(model_selection_path)
        require(EXPECTED_MODEL_REVISION in selection_text, "Model-selection document does not record exact revision.")
        require("google/gemma-3-1b-it" in selection_text, "Model-selection document does not record fallback.")
        require("MODEL_LOCKED = true" in selection_text, "Model-selection document does not record model lock.")
        require("no Llama" in selection_text, "Model-selection document does not prohibit model shopping.")

    if os.path.exists(checkpoint_mapping_path):
        mapping_text = read_text(checkpoint_mapping_path)
        require("block9_pre_final_rmsnorm" in mapping_text, "Checkpoint mapping does not freeze reference checkpoint.")
        require("block15_pre_final_rmsnorm" in mapping_text, "Checkpoint mapping does not freeze final checkpoint.")
        require("0.5925925926" in mapping_text, "Checkpoint mapping does not record normalized depth derivation.")
        require("NO LAYER SWEEP" in mapping_text or "layer sweep" in mapping_text, "Checkpoint mapping does not prohibit layer sweep.")

    # Validator identity is recorded in the config and matches this file.
    actual_validator_hash = sha256_file(os.path.abspath(__file__))
    require(actual_validator_hash == config.get("design_validator_sha256"), "Design validator identity is not recorded correctly in config.")

    # No formal result or authorization may exist.
    for result_path in RESULT_CANDIDATES:
        require(not os.path.exists(result_path), f"Formal result path unexpectedly exists: {result_path}")

    if errors:
        print("EXP025_DESIGN_VALIDATION = FAIL")
        for error in errors:
            print("ERROR:", error)
        return 1

    print("EXP025_DESIGN_VALIDATION = PASS")
    print("EXP025_DESIGN_CREATED = true")
    print("EXP025_MODEL_LOCKED = true")
    print("EXP025_CHECKPOINT_MAPPING_FROZEN = true")
    print("EXP025_FORMAL_RUN_PERFORMED = false")
    print("EXP025_SCIENTIFIC_RESULT_CREATED = false")
    print("EXP025_READY_FOR_ENGINEERING_QUALIFICATION = true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
