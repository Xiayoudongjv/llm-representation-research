#!/usr/bin/env python3
"""Validate the EXP-025 preoutcome specification clarification authority.

This is a non-scientific governance validator. It does not import torch,
sklearn, or any model/runtime dependency, does not open the formal dataset, and
does not access DIAGNOSTIC/EVAL outcome data.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = ROOT / "experiments" / "exp025"

CLARIFICATION_MD = EXP_DIR / "EXP-025-PREOUTCOME-SPECIFICATION-CLARIFICATION-001.md"
CLARIFICATION_JSON = EXP_DIR / "exp025_preoutcome_specification_clarification_001.json"

PRIMARY_FROZEN_AUTHORITIES = {
    EXP_DIR / "EXP-025-PREREGISTRATION.md": "b83fd58ba36e55ab5c48577169e07a168d2a55df759d3131677cd86f2363e08e",
    EXP_DIR / "exp025_frozen_config.json": "2c9b1b8735378108c921a8ca99a1aab115b2a6669bf82e5ae0a9314dd4b62275",
    EXP_DIR / "EXP-025-MODEL-SELECTION.md": "be28f7a2b1f460879e65f0ac911b01756d76b45069f8f438021412b76e954f80",
    EXP_DIR / "EXP-025-CHECKPOINT-MAPPING.md": "5f8c5df4aa849ceb7ee2ca8b1765aeeff46b96182426c97b81d320b3dda6a087",
    EXP_DIR / "validate_exp025_design.py": "e87042535622e545c682a6f1019bf3703b4d0029d895e80c74269f7f1f26376d",
}

INHERITED_FROZEN_AUTHORITIES = {
    ROOT / "docs" / "experiments" / "EXP-024-PREREGISTRATION.md": "55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810",
}

EXPECTED_GAPS = ("GAP-001", "GAP-002", "GAP-004", "GAP-005", "GAP-006")
VALID_STATUSES = {
    "PREEXISTING_AUTHORITY_RESOLUTION",
    "PROSPECTIVE_PREOUTCOME_CLARIFICATION",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(reasons: list[str], message: str) -> None:
    reasons.append(message)


def validate() -> dict[str, Any]:
    reasons: list[str] = []
    validation_errors: list[str] = []

    if not CLARIFICATION_MD.is_file():
        fail(reasons, "CLARIFICATION_MARKDOWN_MISSING")
    if not CLARIFICATION_JSON.is_file():
        fail(reasons, "CLARIFICATION_JSON_MISSING")

    for path, expected_sha in {**PRIMARY_FROZEN_AUTHORITIES, **INHERITED_FROZEN_AUTHORITIES}.items():
        if not path.is_file():
            fail(reasons, f"FROZEN_AUTHORITY_MISSING_{path.name}")
            continue
        actual = sha256_file(path)
        if actual.lower() != expected_sha.lower():
            fail(reasons, f"FROZEN_AUTHORITY_HASH_MISMATCH_{path.name}")
            validation_errors.append(f"{path.name}: expected {expected_sha}, actual {actual}")

    result_candidates = (
        EXP_DIR / "results" / "exp025_results.json",
        EXP_DIR / "exp025_formal_result.json",
    )
    for path in result_candidates:
        if path.exists():
            fail(reasons, f"UNEXPECTED_RESULT_PATH_PRESENT_{path.name}")

    clarification = read_json(CLARIFICATION_JSON)

    if clarification.get("schema_version") != "1.0.0":
        fail(reasons, "CLARIFICATION_SCHEMA_VERSION_INVALID")
    if clarification.get("experiment") != "EXP-025":
        fail(reasons, "CLARIFICATION_EXPERIMENT_INVALID")
    if clarification.get("classification") != "PROSPECTIVE_PREOUTCOME_SPECIFICATION_CLARIFICATION":
        fail(reasons, "CLARIFICATION_CLASSIFICATION_INVALID")
    if clarification.get("prior_scientific_outcome_exposure") is not False:
        fail(reasons, "PRIOR_SCIENTIFIC_OUTCOME_EXPOSURE_MUST_BE_FALSE")
    if clarification.get("prior_diag_access") is not False:
        fail(reasons, "PRIOR_DIAG_ACCESS_MUST_BE_FALSE")
    if clarification.get("prior_eval_access") is not False:
        fail(reasons, "PRIOR_EVAL_ACCESS_MUST_BE_FALSE")
    if clarification.get("original_preregistration_changed") is not False:
        fail(reasons, "ORIGINAL_PREREGISTRATION_CHANGED_MUST_BE_FALSE")
    if clarification.get("preoutcome_protocol_clarification_added") is not True:
        fail(reasons, "PREOUTCOME_PROTOCOL_CLARIFICATION_ADDED_MUST_BE_TRUE")

    gap_resolutions = clarification.get("gap_resolutions")
    if not isinstance(gap_resolutions, dict):
        fail(reasons, "GAP_RESOLUTIONS_MISSING")
        gap_resolutions = {}

    for gap_id in EXPECTED_GAPS:
        entry = gap_resolutions.get(gap_id)
        if not isinstance(entry, dict):
            fail(reasons, f"MISSING_GAP_{gap_id}")
            continue
        status = entry.get("status")
        if status not in VALID_STATUSES:
            fail(reasons, f"UNRESOLVED_OR_INVALID_STATUS_{gap_id}")
        if not entry.get("authority"):
            fail(reasons, f"MISSING_AUTHORITY_{gap_id}")
        if not entry.get("exact_rule"):
            fail(reasons, f"MISSING_EXACT_RULE_{gap_id}")
        if not entry.get("scientific_quantities_affected"):
            fail(reasons, f"MISSING_QUANTITIES_{gap_id}")

    md_text = CLARIFICATION_MD.read_text(encoding="utf-8")
    expected_markers = {
        "GAP-001": ["average ranks", "Pearson correlation", "standard Spearman"],
        "GAP-002": ["rho_perm >= rho_obs", "3,628,800", "NOT_EVALUABLE"],
        "GAP-004": ["sigma_source,j == 0", "z_j = 0", "no epsilon"],
        "GAP-005": ["effective_n == 0", "NOT_EVALUABLE", "NO SCIENTIFIC ROUTING"],
        "GAP-006": ["BA = (1 / 4)", "TP_c / N_c", "STOP_AND_REPORT_PROTOCOL_INTEGRITY_ERROR"],
    }
    for gap_id, markers in expected_markers.items():
        for marker in markers:
            if marker.lower() not in md_text.lower():
                fail(reasons, f"MISSING_EXACT_SEMANTIC_{gap_id}_{marker}")

    md_sha = sha256_file(CLARIFICATION_MD)
    json_sha = sha256_file(CLARIFICATION_JSON)
    validator_sha = sha256_file(Path(__file__))

    passed = not reasons
    return {
        "validation_status": "PASS" if passed else "FAIL",
        "validation_errors": reasons,
        "validation_error_details": validation_errors,
        "clarification_md_sha256": md_sha,
        "clarification_json_sha256": json_sha,
        "clarification_validator_sha256": validator_sha,
        "all_five_gaps_present": all(
            gap_id in gap_resolutions for gap_id in EXPECTED_GAPS
        ),
        "no_unresolved_gap": all(
            gap_resolutions.get(gap_id, {}).get("status") in VALID_STATUSES
            for gap_id in EXPECTED_GAPS
        ),
        "original_frozen_authority_hashes_unchanged": not any(
            "FROZEN_AUTHORITY_HASH_MISMATCH" in reason for reason in reasons
        ),
        "diag_or_eval_or_result_accessed": False,
        "diag_data_accessed": False,
        "eval_data_accessed": False,
        "valid_scientific_result_count": 0,
    }


def main() -> int:
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    print("EXP025_PREOUTCOME_CLARIFICATION_VALIDATION = " + result["validation_status"])
    return 0 if result["validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
