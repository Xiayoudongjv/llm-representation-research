#!/usr/bin/env python3
"""EXP-028 formal result schema validator.

This module is used by the EXP-028 production runner before atomic publication.
It does not access real FIT/DIAG/EVAL content.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np

EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]
CONFIG_PATH = EXP_DIR / "exp028_frozen_config.json"
BINDING_PATH = EXP_DIR / "exp028_authority_binding.json"

VALID_MODEL_NAMES = ("Qwen", "OLMo", "Llama")
VALID_MODEL_STATES = {
    "JOINT_ALIGNMENT_CONTRIBUTION",
    "REPRESENTATION_ONLY",
    "READOUT_ONLY_ARTIFACT_RISK",
    "NO_PAIRED_COORDINATE_CONTRIBUTION",
}
VALID_THREE_MODEL_ROUTES = {
    "THREE_MODEL_JOINT_COORDINATEWISE_COMPONENT",
    "THREE_MODEL_COMMON_STATE",
    "MODEL_DEPENDENT_ALIGNMENT_STATE",
    "NOT_FULLY_ADJUDICATED",
}
VALID_SUPPORT_SEMANTICS = "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND"
VALID_DESCRIPTIVE_INTERVAL = "CENTRAL_90_PERCENT_PERCENTILE_INTERVAL"


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _classify_state(rm_supported: bool, ro_supported: bool) -> str:
    if rm_supported and ro_supported:
        return "JOINT_ALIGNMENT_CONTRIBUTION"
    if rm_supported and not ro_supported:
        return "REPRESENTATION_ONLY"
    if not rm_supported and ro_supported:
        return "READOUT_ONLY_ARTIFACT_RISK"
    return "NO_PAIRED_COORDINATE_CONTRIBUTION"


def validate_config_surface(config: Mapping[str, Any]) -> list[str]:
    """Validate static result-facing config fields without scientific data."""
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    check(config.get("experiment_id") == "EXP-028", "experiment_id")
    check(config.get("working_name") == "PAIRED_INFORMATION_BEYOND_MARGINAL_RECALIBRATION", "working_name")
    check(config.get("design_status") == "FROZEN_DESIGN_NOT_RUN", "design_status")
    models = config.get("models", {})
    check(set(models) == set(VALID_MODEL_NAMES), "model_set")
    bootstrap = config.get("bootstrap", {})
    support = bootstrap.get("primary_support_ci", {})
    check(support.get("name") == VALID_SUPPORT_SEMANTICS, "bootstrap_support_semantics")
    desc = bootstrap.get("descriptive_central_interval", {})
    check(desc.get("name") == VALID_DESCRIPTIVE_INTERVAL, "bootstrap_descriptive_interval")
    check(bootstrap.get("two_sided_95_percent_ci_used") is False, "bootstrap_two_sided_95_ci_used")
    return errors


def validate_result_payload(payload: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    if not isinstance(payload, Mapping):
        return ["result_payload_not_mapping"]

    check(payload.get("schema_version") == "1.0.0", "schema_version")
    check(payload.get("classification") == "EXP028_SCIENTIFIC_RESULT", "classification")
    check(payload.get("experiment") == "EXP-028", "experiment")
    check(payload.get("working_name") == "PAIRED_INFORMATION_BEYOND_MARGINAL_RECALIBRATION", "working_name")
    check(isinstance(payload.get("created_at_utc"), str) and bool(payload.get("created_at_utc")), "created_at_utc")
    check(isinstance(payload.get("attempt_id"), str) and bool(payload.get("attempt_id")), "attempt_id")
    check(payload.get("model_name") in VALID_MODEL_NAMES, "model_name")
    check(isinstance(payload.get("technical_validity"), bool), "technical_validity")

    endpoints = payload.get("primary_endpoints", {})
    if not isinstance(endpoints, Mapping):
        errors.append("primary_endpoints_mapping")
    else:
        for field in ("DELTA_RM", "DELTA_RO"):
            value = endpoints.get(field)
            check(isinstance(value, (int, float)) and np.isfinite(float(value)), f"primary_endpoints_{field}_nonfinite")

    bootstrap = payload.get("bootstrap", {})
    if not isinstance(bootstrap, Mapping):
        errors.append("bootstrap_mapping")
    else:
        for field in ("DELTA_RM", "DELTA_RO"):
            bound = bootstrap.get(field, {})
            check(isinstance(bound, Mapping), f"bootstrap_{field}_mapping")
            check(bound.get("primary_support_semantics") == VALID_SUPPORT_SEMANTICS, f"bootstrap_{field}_support_semantics")
            check(bound.get("descriptive_central_interval") == VALID_DESCRIPTIVE_INTERVAL, f"bootstrap_{field}_descriptive_interval")
            check(isinstance(bound.get("support"), bool), f"bootstrap_{field}_support_bool")

    model_state = payload.get("model_state")
    check(model_state in VALID_MODEL_STATES, "model_state")
    route = payload.get("three_model_route")
    check(route in VALID_THREE_MODEL_ROUTES, "three_model_route")

    if isinstance(bootstrap, Mapping):
        rm_bound = bootstrap.get("DELTA_RM", {})
        ro_bound = bootstrap.get("DELTA_RO", {})
        if isinstance(rm_bound.get("support"), bool) and isinstance(ro_bound.get("support"), bool):
            expected_state = _classify_state(bool(rm_bound.get("support")), bool(ro_bound.get("support")))
            check(model_state == expected_state, "support_class_mismatch")

    claim = payload.get("claim_firewall", {})
    if not isinstance(claim, Mapping):
        errors.append("claim_firewall_mapping")
    else:
        for key in ("TRANSPORT_TEST", "INVARIANT_TEST", "FUNCTIONAL_BINDING_TEST", "FULL_RESIDUAL_FLOW_TEST", "FULL_MSA_TEST"):
            check(claim.get(key) is False, f"claim_firewall_{key}")

    for forbidden in (
        "transport_claim",
        "invariant_claim",
        "functional_binding_claim",
        "residual_flow_confirmation",
        "msa_confirmation",
    ):
        if forbidden in payload:
            errors.append(f"forbidden_claim_{forbidden}")

    binding = payload.get("execution_binding", {})
    if not isinstance(binding, Mapping) or not binding.get("runner_sha256") or not binding.get("frozen_config_sha256"):
        errors.append("execution_binding")

    panel = payload.get("panel_identity", {})
    if not isinstance(panel, Mapping):
        errors.append("panel_identity_mapping")
    else:
        check(panel.get("experiment") == "EXP-028", "panel_identity_experiment")
        check(isinstance(panel.get("panel_sha256"), str) and bool(panel.get("panel_sha256")), "panel_identity_sha256")

    authorization = payload.get("authorization_identity", {})
    if not isinstance(authorization, Mapping):
        errors.append("authorization_identity_mapping")
    else:
        for field in ("authorization_id", "authorization_sha256", "run_attempt_id"):
            check(isinstance(authorization.get(field), str) and bool(authorization.get(field)), f"authorization_identity_{field}")

    if "raw_hidden_tensors" in payload:
        errors.append("raw_hidden_tensors_forbidden")

    return errors


def is_valid_result_payload(payload: Mapping[str, Any]) -> bool:
    return validate_result_payload(payload) == []
