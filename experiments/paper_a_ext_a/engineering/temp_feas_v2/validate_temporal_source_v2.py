"""Validate the frozen TEMPORAL_SOURCE_V2 protocol without network or data access."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[4]
PROTOCOL_PATH = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
V8_AUTHORITY = ROOT / "experiments" / "paper_a_ext_a" / "paper_a_ext_a_temporal_asset_source_v8.json"
V8_CHECKPOINT = ROOT / "experiments" / "paper_a_ext_a" / "data" / "raw" / "wikidata_v8" / "acquisition_checkpoint.json"
OLD_REPORT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_002r" / "temp_feas_002r_report.json"

EXPECTED_HEAD = "878ef6aabf57af061ff86a81e456347c1461690c"
EXPECTED_V8_AUTHORITY_SHA = "47a2ce443fe097b32fc391b910d97860593093ec19c9e362ec7019d5f3984ca7"
EXPECTED_V8_CHECKPOINT_SHA = "a6f21f6bdf2267d14c36f26231a61d8279ed1bbe66ce0265e25c6fde61a59b38"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def base_authority_is_bound(ref: str) -> bool:
    if git_value("rev-parse", ref) == EXPECTED_HEAD:
        return True
    try:
        target = git_value("rev-parse", ref)
        return subprocess.run(
            ["git", "merge-base", "--is-ancestor", EXPECTED_HEAD, target],
            cwd=ROOT,
            check=False,
        ).returncode == 0
    except subprocess.CalledProcessError:
        return False


def validate_protocol(protocol: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if protocol.get("protocol_status") != "FROZEN_BEFORE_FRESH_ACQUISITION":
        errors.append("protocol is not frozen before acquisition")
    evidence = protocol.get("prior_source_evidence", {})
    expected_evidence = {
        "confirmation_total": 2840,
        "event_root_valid": 2840,
        "date_valid_after_root": 2840,
        "dedup_valid": 2840,
        "surface_leakage_pass": 3,
        "surface_leakage_reject": 2837,
        "final_eligible_events": 3,
        "temporal_families_possible": 1,
    }
    for key, expected in expected_evidence.items():
        if evidence.get(key) != expected:
            errors.append(f"prior evidence mismatch: {key}")
    if protocol.get("event_criterion", {}).get("allowed_roots") != ["Q1190554", "Q1656682"]:
        errors.append("event roots changed")
    if protocol.get("canonical_time", {}).get("priority") != ["P580_start_time", "P585_point_in_time"]:
        errors.append("canonical time priority changed")
    if protocol.get("canonical_time", {}).get("validity", {}).get("calendar_qid") != "Q1985727":
        errors.append("calendar requirement changed")
    if protocol.get("canonical_time", {}).get("validity", {}).get("minimum_time_precision") != 11:
        errors.append("precision requirement changed")
    surface = protocol.get("surface_leakage_rule", {})
    if surface.get("frozen_before_acquisition") is not True or surface.get("manual_redaction") is not False:
        errors.append("surface rule is not pre-frozen or permits redaction")
    if set(surface.get("patterns", [])) != {"four_digit_year", "complete_numeric_date", "month_year", "month_day_year", "explicit_bce_ce_year"}:
        errors.append("surface pattern set changed")
    freshness = protocol.get("freshness", {})
    if freshness.get("exclude_prior_date_valid_pool") is not True or freshness.get("exclude_prior_v8_candidate_universe") is not True:
        errors.append("freshness exclusion is incomplete")
    diversity = protocol.get("diversity_control", {})
    if diversity.get("maximum_single_coarse_class_events") != 44 or diversity.get("threshold_tuning_after_observation") is not False:
        errors.append("diversity rule changed")
    if protocol.get("selection_and_ordering", {}).get("acquisition_order_by_event_date") is not False:
        errors.append("acquisition is date ordered")
    backend = protocol.get("acquisition_backend", {})
    if backend.get("primary", {}).get("name") != "QLever":
        errors.append("primary backend changed")
    if backend.get("fallback_policy", {}).get("mode") != "FAIL_CLOSED_NO_ACQUISITION":
        errors.append("fallback is not fail-closed")
    stopping = protocol.get("stopping_rule", {})
    if stopping.get("stop_at_eligible_events") != 600:
        errors.append("stopping reserve changed")
    if protocol.get("required_flags") != {
        "TEMPORAL_SOURCE_V2_FROZEN": True,
        "TEMPORAL_SOURCE_V2_DATA_ACCESSED": False,
        "OLD_CONFIRMATION_REUSED": False,
        "FORMAL_MODEL_INFERENCE_PERFORMED": False,
        "FORMAL_SCIENTIFIC_OUTCOME_CREATED": False,
    }:
        errors.append("required flags are not frozen")
    return errors


def validate() -> dict[str, Any]:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    errors = validate_protocol(protocol)
    errors.extend(
        [
            "HEAD/base-parent mismatch" if not base_authority_is_bound("HEAD") else "",
            "origin/base-parent mismatch" if not base_authority_is_bound("origin/main") else "",
            "V8 authority changed" if sha256_file(V8_AUTHORITY) != EXPECTED_V8_AUTHORITY_SHA else "",
            "V8 checkpoint changed" if sha256_file(V8_CHECKPOINT) != EXPECTED_V8_CHECKPOINT_SHA else "",
            "old confirmation report changed" if sha256_file(OLD_REPORT) != protocol["prior_source_evidence"]["old_confirmation_report_sha256"] else "",
        ]
    )
    errors = [error for error in errors if error]
    result = {
        "protocol": "TEMPORAL_SOURCE_V2",
        "valid": not errors,
        "errors": errors,
        "network_accessed": False,
        "data_accessed": False,
        "model_inference_performed": False,
    }
    if errors:
        raise RuntimeError("TEMPORAL_SOURCE_V2_VALIDATION_FAILED:" + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    result = validate()
    print("TEMPORAL_SOURCE_V2_VALIDATION=PASS")
    print("TEMPORAL_SOURCE_V2_DATA_ACCESSED=false")
    print("NETWORK_ACCESSED=false")
    print("MODEL_INFERENCE=false")
