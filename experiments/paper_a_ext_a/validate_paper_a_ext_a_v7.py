"""Read-only validator for the prospective PA-EXT-A V7 amendment."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from qlever_v7_main_view import (
    HISTORICAL_V6_CHECKPOINT_OFFSET,
    RULE_PATH,
    SCHOLARLY_P31_QIDS,
    V7_FORMAL_START_OFFSET,
    candidate_query,
    main_view_filter,
    validate_initial_offset,
)


EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]
AUTHORITY_PATH = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v7.json"
V6_PATH = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v6.json"
IMPLEMENTATION_PATH = EXP_DIR / "qlever_v7_main_view.py"
V6_PAYLOAD_PATH = EXP_DIR / "data" / "raw" / "wikidata_v6" / "candidate_page_offset_00000000_9c942ec12f340d3e.json"

EXPECTED_V6_SHA256 = "6df26d9d2940bfabb25058f561229070c59ca3e8a288cf2f543656b770a9acbe"
EXPECTED_V6_PAYLOAD_SHA256 = "19048051ee6837554f5f116c091bf43f2e8e1cd973cfe38b27be3cba4db8e859"
FORBIDDEN_OUTPUTS = [
    EXP_DIR / "data" / "wikidata_temporal_pairs.json",
    EXP_DIR / "data" / "paper_a_ext_a_semantic_asset_bank.json",
    EXP_DIR / "data" / "paper_a_ext_a_source_bank.json",
    EXP_DIR / "data" / "paper_a_ext_a_frozen_panel.json",
    EXP_DIR / "data" / "paper_a_ext_a_panel_manifest.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate() -> list[str]:
    errors: list[str] = []

    def check(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    for path in (AUTHORITY_PATH, RULE_PATH, IMPLEMENTATION_PATH, V6_PATH, V6_PAYLOAD_PATH):
        check(path.exists(), f"missing:{path}")
    if errors:
        return errors

    authority = read_json(AUTHORITY_PATH)
    rule = read_json(RULE_PATH)
    v6_lineage = authority.get("v6_lineage", {})

    check(sha256_file(V6_PATH) == EXPECTED_V6_SHA256, "v6_sha256_changed")
    check(sha256_file(V6_PAYLOAD_PATH) == EXPECTED_V6_PAYLOAD_SHA256, "v6_payload_sha256_changed")
    check(authority.get("status") == "FROZEN", "v7_status")
    check(authority.get("amendment_scope") == "ACCESS_BACKEND_PLUS_EXPLICIT_MAIN_VIEW_RECONSTRUCTION", "amendment_scope")
    check(authority.get("scientific_data_source") == "Wikidata", "scientific_data_source")
    check(authority.get("formal_backend") == "QLEVER", "formal_backend")
    check(authority.get("raw_graph_scope") == "UNIFIED", "raw_graph_scope")
    check(authority.get("main_view_filter") == "FROZEN_OFFICIAL_WDQS_SPLIT_RULE", "main_view_filter")
    check(authority.get("frozen_temporal_semantics_changed") is False, "semantic_drift")
    check(authority.get("global_backend_equivalence_claimed") is False, "global_equivalence_claim")
    check(authority.get("v6_historical_page_consumed_by_v7") is False, "v6_lineage_mixing")
    check(authority.get("v7_formal_start_offset") == 0, "v7_start_offset")
    check(authority.get("model_inference_performed") is False, "model_inference_flag")
    check(authority.get("formal_acquisition_performed") is False, "formal_acquisition_flag")
    check(v6_lineage.get("successful_candidate_pages") == 1, "v6_page_count")
    check(v6_lineage.get("temporal_pairs_created") == 0, "v6_pair_count")
    check(v6_lineage.get("v6_consumption_by_v7") is False, "v6_consumption_by_v7")

    v7_lineage = authority.get("v7_lineage", {})
    check(v7_lineage.get("main_view_filter_applied") is True, "v7_filter_required")
    check(v7_lineage.get("must_start_at_offset") == 0, "v7_lineage_start_offset")
    check(v7_lineage.get("must_not_resume_from_v6_offset") == 100, "v7_v6_checkpoint_boundary")
    check(v7_lineage.get("must_not_mix_v6_pages") is True, "v7_lineage_mixing_rule")

    scholarly = rule.get("scholarly_exclusion", {})
    check(scholarly.get("non_deprecated_p13046_statement") is True, "p13046_rule")
    check(scholarly.get("direct_non_deprecated_p31_in_list") is True, "p31_rule")
    check(scholarly.get("p279_ancestry_used") is False, "p279_graph_split_rule")
    check(len(scholarly.get("direct_p31_class_qids", [])) == 34, "scholarly_class_count")
    check(
        tuple(scholarly.get("direct_p31_class_qids", [])) == SCHOLARLY_P31_QIDS,
        "serialized_rule_implementation_class_list_mismatch",
    )

    generated = candidate_query(limit=100, offset=0)
    filter_position = generated.index("FILTER NOT EXISTS")
    order_position = generated.index("ORDER BY")
    limit_position = generated.index("LIMIT")
    offset_position = generated.index("OFFSET")
    check(filter_position < order_position < limit_position < offset_position, "filter_not_before_pagination")
    check("p:P13046" in main_view_filter(), "filter_missing_p13046")
    check("p:P31" in main_view_filter(), "filter_missing_p31")
    check("wikibase:DeprecatedRank" in main_view_filter(), "filter_missing_rank_guard")
    check("P279" not in main_view_filter(), "p279_used_in_graph_split")

    expected_query_sha = authority.get("query_sha256")
    expected_impl_sha = authority.get("implementation_sha256")
    check(expected_query_sha == hashlib.sha256(generated.encode("utf-8")).hexdigest(), "query_sha256")
    check(expected_impl_sha == sha256_file(IMPLEMENTATION_PATH), "implementation_sha256")
    check(authority.get("main_view_rule_sha256") == sha256_file(RULE_PATH), "rule_sha256")
    hard_flags = authority.get("hard_flags", {})
    check(hard_flags.get("RAW_UNIFIED_FORMAL_ACQUISITION_ALLOWED") is False, "raw_unified_formal_acquisition")
    check(hard_flags.get("V6_V7_PAGE_MIXING_ALLOWED") is False, "v6_v7_page_mixing")

    try:
        validate_initial_offset(V7_FORMAL_START_OFFSET)
    except ValueError as exc:
        errors.append(f"v7_zero_offset_rejected:{exc}")
    try:
        validate_initial_offset(HISTORICAL_V6_CHECKPOINT_OFFSET)
        errors.append("v6_checkpoint_accepted_as_v7_start")
    except ValueError:
        pass

    for path in FORBIDDEN_OUTPUTS:
        check(not path.exists(), f"forbidden_output_exists:{path}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        print("PA_EXT_A_V7_AUTHORITY_VALIDATION = FAIL")
        return 1
    print("PA_EXT_A_V7_AUTHORITY_VALIDATION = PASS")
    print(f"V7_SHA256 = {sha256_file(AUTHORITY_PATH)}")
    print(f"MAIN_VIEW_RULE_SHA256 = {sha256_file(RULE_PATH)}")
    print(f"QUERY_SHA256 = {hashlib.sha256(candidate_query(limit=100, offset=0).encode('utf-8')).hexdigest()}")
    print(f"IMPLEMENTATION_SHA256 = {sha256_file(IMPLEMENTATION_PATH)}")
    print("PA_EXT_A_TEMPORAL_V7_STATUS = FROZEN")
    print("MODEL_INFERENCE_PERFORMED = false")
    print("FORMAL_ACQUISITION_PERFORMED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
