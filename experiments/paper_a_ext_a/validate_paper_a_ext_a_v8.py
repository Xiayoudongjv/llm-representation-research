"""Offline validator for the PA-EXT-A V8 literal-date amendment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from qlever_v7_main_view import main_view_filter
from qlever_v8_literal_main_view import (
    V7_HISTORICAL_NEXT_OFFSET,
    V8_FORMAL_START_OFFSET,
    candidate_query,
    validate_initial_offset,
)


EXP_DIR = Path(__file__).resolve().parent
AUTHORITY_PATH = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v8.json"
V7_PATH = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v7.json"
V6_PATH = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v6.json"
RULE_PATH = EXP_DIR / "v7_main_view_rule.json"
IMPLEMENTATION_PATH = EXP_DIR / "qlever_v8_literal_main_view.py"
QUALIFICATION_PATH = EXP_DIR / "engineering" / "qlever_v8_literal_binding_qualification.json"
V7_SHA256 = "0766e5a315a0a6c1784beef8c0e2af45364f22ec7d9af164741628f323b65fb3"
V6_SHA256 = "6df26d9d2940bfabb25058f561229070c59ca3e8a288cf2f543656b770a9acbe"
RULE_SHA256 = "ece32b16462f6abc42d6cba0b4a5a433fbfdacf51278ea46d7bf1f8d22adec05"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for path in (AUTHORITY_PATH, V7_PATH, V6_PATH, RULE_PATH, IMPLEMENTATION_PATH, QUALIFICATION_PATH):
        check(path.exists(), f"missing:{path}")
    if errors:
        return errors

    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    qualification = json.loads(QUALIFICATION_PATH.read_text(encoding="utf-8"))
    query = candidate_query(limit=100, offset=0)
    check(sha256_file(V7_PATH) == V7_SHA256, "v7_changed")
    check(sha256_file(V6_PATH) == V6_SHA256, "v6_changed")
    check(sha256_file(RULE_PATH) == RULE_SHA256, "rule_changed")
    check(authority.get("status") == "FROZEN", "v8_not_frozen")
    check(authority.get("amendment_scope") == "CANDIDATE_RESPONSE_SCHEMA_LITERAL_BINDING_ONLY", "scope")
    check(authority.get("formal_backend") == "QLEVER", "backend")
    check(authority.get("raw_graph_scope") == "UNIFIED", "graph_scope")
    check(authority.get("candidate_response_schema_corrected") is True, "literal_correction_missing")
    check(authority.get("temporal_eligibility_definition_changed") is False, "semantic_drift")
    check(authority.get("frozen_temporal_semantics_changed") is False, "frozen_semantics_changed")
    check(authority.get("v7_raw_lineage_consumed_by_v8") is False, "v7_consumed")
    check(authority.get("v8_formal_start_offset") == 0, "start_offset")
    check(authority.get("v8_candidate_pages_verified") == 0, "pages_created")
    check(authority.get("formal_acquisition_performed") is False, "formal_acquisition")
    check(authority.get("temporal_families_created") == 0, "families_created")
    check(authority.get("model_inference_performed") is False, "inference")
    blocker = authority.get("v7_formal_blocker", {})
    check(blocker.get("formal_acquisition_started") is True, "v7_blocker_started")
    check(blocker.get("candidate_pages_verified") == 10, "v7_blocker_pages")
    check(blocker.get("next_offset") == 1000, "v7_blocker_offset")
    check(blocker.get("eligible_events") == 0, "v7_blocker_events")
    check(blocker.get("temporal_families") == 0, "v7_blocker_families")
    check(blocker.get("canonical_temporal_output_created") is False, "v7_blocker_output")
    check(blocker.get("model_inference_performed") is False, "v7_blocker_inference")
    check("FILTER(ISLITERAL(?date))" in query, "literal_filter_missing")
    check(query.index("FILTER(ISLITERAL(?date))") < query.index("ORDER BY") < query.index("LIMIT") < query.index("OFFSET"), "filter_order")
    check("P279" not in main_view_filter(), "graph_rule_p279")
    check(authority.get("query_sha256") == hashlib.sha256(query.encode("utf-8")).hexdigest(), "query_hash")
    check(authority.get("implementation_sha256") == sha256_file(IMPLEMENTATION_PATH), "implementation_hash")
    check(authority.get("main_view_rule_sha256") == RULE_SHA256, "authority_rule_hash")
    check(qualification.get("status") == "PASS", "qualification_status")
    check(qualification.get("candidate_literal_binding_rate") == "100/100", "literal_binding_rate")
    check(qualification.get("positive_time_metadata_path") is True, "positive_metadata_path")
    check(qualification.get("p31_retrieval") is True, "p31")
    check(qualification.get("p279_retrieval") is True, "p279")
    check(qualification.get("main_view_filter") is True, "main_view_filter")
    check(qualification.get("temporal_families_created") == 0, "qualification_families")
    check(qualification.get("formal_v8_acquisition_performed") is False, "qualification_formal")
    check(qualification.get("model_inference_performed") is False, "qualification_inference")
    check(authority.get("qualification_report_sha256") == sha256_file(QUALIFICATION_PATH), "qualification_hash")
    try:
        validate_initial_offset(V8_FORMAL_START_OFFSET)
    except ValueError as exc:
        errors.append(f"zero_offset_rejected:{exc}")
    try:
        validate_initial_offset(V7_HISTORICAL_NEXT_OFFSET)
        errors.append("v7_offset_accepted")
    except ValueError:
        pass
    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("PA_EXT_A_V8_AUTHORITY_VALIDATION = FAIL")
        return 1
    authority = json.loads(AUTHORITY_PATH.read_text(encoding="utf-8"))
    print("PA_EXT_A_V8_AUTHORITY_VALIDATION = PASS")
    print(f"V8_SHA256 = {sha256_file(AUTHORITY_PATH)}")
    print(f"V8_QUERY_SHA256 = {authority['query_sha256']}")
    print(f"IMPLEMENTATION_SHA256 = {authority['implementation_sha256']}")
    print("FORMAL_V8_ACQUISITION_PERFORMED = false")
    print("TEMPORAL_FAMILIES_CREATED = 0")
    print("MODEL_INFERENCE_PERFORMED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
