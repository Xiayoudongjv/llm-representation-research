#!/usr/bin/env python3
"""Governance validator for the Innovation Candidate Registry v1.0.

This validator checks epistemic separation and structural integrity only.
It is not a scientific validator and does not interpret experiment results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


THEORY_DIR = Path(__file__).resolve().parent
REGISTRY_MD = THEORY_DIR / "INNOVATION-CANDIDATE-REGISTRY.md"
REGISTRY_JSON = THEORY_DIR / "innovation_candidate_registry.json"

ALLOWED_ORIGIN_METHODS = {
    "SCAMPER",
    "TRIZ",
    "REVERSE_THINKING",
    "COMBINATION_INNOVATION",
    "CROSS_ASSET_SYNTHESIS",
    "RESULT_CONDITIONED_SYNTHESIS",
    "MATHEMATICAL_INTUITION_REFORMULATION",
    "EXTERNAL_PRIOR_ART_CONTRAST",
}
ALLOWED_ORIGINATOR_CLASSES = {
    "USER_ORIGINATED",
    "AI_SYNTHESIS",
    "USER_AI_CO_SYNTHESIS",
    "LITERATURE_DERIVED",
    "RESULT_CONDITIONED_SYNTHESIS",
    "UNKNOWN",
}
ALLOWED_CURRENT_STATUSES = {
    "PROSPECTIVE_CONSTRUCT",
    "PROSPECTIVE_HYPOTHESIS_SOURCE",
    "PROSPECTIVE_FRAMEWORK",
    "PROSPECTIVE_MECHANISM_TEST",
    "PROSPECTIVE_PREDICTION_FRAMEWORK",
    "EXPLORATORY_PROSPECTIVE",
    "SPECULATIVE_PROSPECTIVE",
    "LONG_TERM_PROSPECTIVE",
    "LONG_TERM_SYSTEMS_ASSET",
}
ALLOWED_ACTIVATION_STATES = {
    "ACTIVE",
    "ELIGIBLE_NOT_ACTIVATED",
    "DEPENDENCY_BLOCKED",
    "DEFERRED",
    "SPECULATIVE",
    "CLOSED",
}
REQUIRED_FIELDS = {
    "ic_id",
    "name",
    "origin_class",
    "origin_method",
    "originator_class",
    "origin_assets",
    "core_question",
    "scientific_construct",
    "candidate_formalization",
    "current_status",
    "activation_state",
    "evidence_dependencies",
    "blocking_dependencies",
    "falsification_route",
    "novelty_status",
    "novelty_risk",
    "scientific_value",
    "engineering_value",
    "claim_ceiling",
    "forbidden_inference",
    "target_paper",
    "possible_independent_paper",
    "promotion_target",
    "promotion_gate",
    "source_anchors",
    "notes",
    "supported_by_existing_results",
    "scientific_authority",
}


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def validate() -> list[str]:
    errors: list[str] = []

    if not REGISTRY_MD.exists():
        errors.append("registry markdown missing")
    if not REGISTRY_JSON.exists():
        errors.append("registry JSON missing")

    payload = load_json(REGISTRY_JSON)

    if payload.get("registry_version") != "1.0":
        errors.append("registry_version mismatch")
    if payload.get("asset_class") != "INNOVATION_CANDIDATE":
        errors.append("asset_class mismatch")
    if payload.get("auto_promotion_allowed") is not False:
        errors.append("AUTO_PROMOTION_ALLOWED must be false")
    if payload.get("scientific_authority") != "NONE_BY_DEFAULT":
        errors.append("scientific authority must be NONE_BY_DEFAULT")
    if "promotion_requirements" not in payload:
        errors.append("promotion pipeline missing")

    firewall = payload.get("current_activation_firewall", {})
    if firewall.get("innovation_registry_does_not_control_current_experiment_state") is not True:
        errors.append("registry experiment-state firewall missing")
    if firewall.get("current_experiment_state_must_be_resolved_from_repository_authority") is not True:
        errors.append("repository-authority firewall missing")
    if firewall.get("chat_state_import_allowed_for_current_execution_state") is not False:
        errors.append("chat-state authority firewall missing")

    routing = payload.get("paper_routing", {})
    paper_a = routing.get("Paper_A", {})
    if paper_a.get("forced_activation") is not False:
        errors.append("Paper A must not force innovation-candidate activation")

    candidates = payload.get("candidates", [])
    ids = [candidate.get("ic_id") for candidate in candidates]
    if len(ids) != 12:
        errors.append("candidate count must be 12")
    if len(set(ids)) != len(ids):
        errors.append("IC_ID values must be unique")
    expected_ids = [f"IC-{i:03d}" for i in range(1, 13)]
    if ids != expected_ids:
        errors.append("IC_ID sequence mismatch")

    by_id = {candidate.get("ic_id"): candidate for candidate in candidates}

    for candidate in candidates:
        ic_id = candidate.get("ic_id")
        missing = REQUIRED_FIELDS - set(candidate.keys())
        if missing:
            errors.append(f"{ic_id}: missing fields {sorted(missing)}")

        if candidate.get("origin_class") != "INNOVATION_CANDIDATE":
            errors.append(f"{ic_id}: origin_class mismatch")
        methods = candidate.get("origin_method", [])
        if not isinstance(methods, list) or not methods or any(m not in ALLOWED_ORIGIN_METHODS for m in methods):
            errors.append(f"{ic_id}: invalid origin_method")
        if candidate.get("originator_class") not in ALLOWED_ORIGINATOR_CLASSES:
            errors.append(f"{ic_id}: invalid originator_class")
        if candidate.get("current_status") not in ALLOWED_CURRENT_STATUSES:
            errors.append(f"{ic_id}: invalid current_status")
        if candidate.get("activation_state") not in ALLOWED_ACTIVATION_STATES:
            errors.append(f"{ic_id}: invalid activation_state")
        if candidate.get("activation_state") == "ACTIVE":
            errors.append(f"{ic_id}: candidate must not be ACTIVE")
        if candidate.get("supported_by_existing_results") is not False:
            errors.append(f"{ic_id}: candidate must not be marked supported by existing results")
        if candidate.get("scientific_authority") != "NONE_BY_DEFAULT":
            errors.append(f"{ic_id}: scientific authority must be NONE_BY_DEFAULT")
        if candidate.get("activation_state") == "DEPENDENCY_BLOCKED" and not candidate.get("blocking_dependencies"):
            errors.append(f"{ic_id}: dependency-blocked candidate missing blocking dependency")
        if not candidate.get("target_paper"):
            errors.append(f"{ic_id}: target paper missing")

    ic003 = by_id.get("IC-003", {})
    if ic003.get("matched_recovery_ne_invariant") is not True:
        errors.append("IC-003: matched recovery != invariant firewall missing")

    ic008 = by_id.get("IC-008", {})
    if ic008.get("kakaya_theorem_claim") is not False:
        errors.append("IC-008: Kakeya theorem claim firewall missing")

    ic009 = by_id.get("IC-009", {})
    if ic009.get("234_status") != "USER_ORIGINATED_INTUITION_ONLY":
        errors.append("IC-009: 234 status firewall missing")

    ic011 = by_id.get("IC-011", {})
    if ic011.get("patent_status") != "NOT_ASSESSED":
        errors.append("IC-011: patent status firewall missing")

    ic012 = by_id.get("IC-012", {})
    if ic012.get("discriminating_statistic_ne_invariant") is not True:
        errors.append("IC-012: discriminating statistic != invariant firewall missing")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        print("INNOVATION_CANDIDATE_REGISTRY_VALIDATOR=FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("INNOVATION_CANDIDATE_REGISTRY_VALIDATOR=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
