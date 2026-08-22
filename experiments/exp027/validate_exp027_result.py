"""EXP-027 formal result schema validator.

This module is used by the EXP-027 production runner before atomic publication.
It validates synthetic and future formal result payloads. It does not access
real FIT/DIAG/EVAL content.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parent))

import validate_exp027_preregistration as design_validator


EXPECTED_PROFILE_FIELDS = (
    "distance_association_status",
    "dominance_status",
    "low_d_recovery_status",
)

REQUIRED_AUTHORIZATION_FIELDS = (
    "authorization_id",
    "authorization_sha256",
    "consumption_record_sha256",
    "run_attempt_id",
)

REQUIRED_BINDING_FIELDS = (
    "repository_commit",
    "runner_sha256",
    "frozen_design_sha256",
    "preregistration_sha256",
    "model_identity",
    "dataset_hashes",
)


def route_from_profile(
    profile: Mapping[str, str],
    *,
    technical_valid: bool,
    measurement_valid: bool,
) -> tuple[str, str]:
    return design_validator.route_profile(
        dict(profile),
        technical_valid=technical_valid,
        measurement_valid=measurement_valid,
    )


def validate_result_payload(payload: Mapping[str, Any]) -> list[str]:
    """Return a list of schema/contract errors; an empty list means valid."""
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    if not isinstance(payload, Mapping):
        return ["result_payload_not_mapping"]

    check(payload.get("schema_version") == "1.0.0", "schema_version")
    check(payload.get("classification") == "EXP027_SCIENTIFIC_RESULT", "classification")
    check(payload.get("experiment") == "EXP-027", "experiment")
    check(isinstance(payload.get("created_at_utc"), str) and bool(payload.get("created_at_utc")), "created_at_utc")
    check(payload.get("attempt_status") in {"COMPLETED", "FAILED", "CRASHED"}, "attempt_status")
    check(payload.get("result_status") in {
        "VALID_REGISTERED_RESULT",
        "UNOBSERVED_OR_INVALID",
    }, "result_status")
    check(payload.get("scientific_status") in {"OBSERVED", "NOT_OBSERVED"}, "scientific_status")

    profile = payload.get("profile", {})
    if not isinstance(profile, Mapping) or set(profile) != set(EXPECTED_PROFILE_FIELDS):
        errors.append("profile_schema")
    else:
        for field in EXPECTED_PROFILE_FIELDS:
            if not isinstance(profile.get(field), str):
                errors.append(f"profile_field_{field}")

    technical_valid = payload.get("technical_validity")
    measurement_valid = payload.get("measurement_validity")
    check(isinstance(technical_valid, bool), "technical_validity")
    check(isinstance(measurement_valid, bool), "measurement_validity")

    route = payload.get("route")
    result_status = payload.get("result_status")
    if isinstance(profile, Mapping) and set(profile) == set(EXPECTED_PROFILE_FIELDS):
        expected_route, expected_result_status = route_from_profile(
            profile,
            technical_valid=bool(technical_valid),
            measurement_valid=bool(measurement_valid),
        )
        check(route == expected_route, "profile_route_mismatch")
        check(result_status == expected_result_status, "result_status_route_mismatch")

    authorization = payload.get("authorization_identity", {})
    if not isinstance(authorization, Mapping) or any(field not in authorization for field in REQUIRED_AUTHORIZATION_FIELDS):
        errors.append("authorization_identity")
    else:
        if not authorization.get("authorization_id") or not authorization.get("authorization_sha256"):
            errors.append("authorization_identity_values")
        if not authorization.get("consumption_record_sha256") or not authorization.get("run_attempt_id"):
            errors.append("authorization_consumption_identity")

    binding = payload.get("execution_binding", {})
    if not isinstance(binding, Mapping) or any(field not in binding for field in REQUIRED_BINDING_FIELDS):
        errors.append("execution_binding")
    else:
        if not binding.get("repository_commit") or not binding.get("runner_sha256"):
            errors.append("execution_binding_values")

    environment = payload.get("execution_environment", {})
    if not isinstance(environment, Mapping):
        errors.append("execution_environment")
    else:
        for field in ("python_version", "numpy_version"):
            if not isinstance(environment.get(field), str) or not environment.get(field):
                errors.append(f"execution_environment_{field}")

    if "raw_hidden_tensors" in payload:
        errors.append("raw_hidden_tensors_forbidden")

    return errors


def is_valid_result_payload(payload: Mapping[str, Any]) -> bool:
    return validate_result_payload(payload) == []