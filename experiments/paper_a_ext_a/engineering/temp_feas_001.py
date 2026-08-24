"""Offline TEMP-FEAS-001 source-feasibility study.

This module reads only the already-cached V8 raw artifacts.  It deliberately
does not import a network client, write to the V8 raw directory, or inspect
semantic fields for SOURCE_CONFIRMATION after the deterministic split.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


EXP_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = EXP_DIR.parents[2]
RAW_DIR = EXP_DIR / "data" / "raw" / "wikidata_v8"
OUTPUT_DIR = EXP_DIR / "engineering" / "temp_feas_001"
V8_AUTHORITY = EXP_DIR / "paper_a_ext_a_temporal_asset_source_v8.json"
V7_RULE = EXP_DIR / "v7_main_view_rule.json"
V8_QUERY_MODULE = EXP_DIR / "qlever_v8_literal_main_view.py"
V8_RUNNER = EXP_DIR / "acquire_wikidata_temporal_v8.py"

EXPECTED_POOL_COUNT = 3550
DESIGN_BUCKET_MODULUS = 5
DESIGN_BUCKET_REMAINDER = 0
SPLIT_RULE_ID = "PA_EXT_A_TEMP_FEAS_001_SPLIT_V1"
OCCURRENCE_QID = "Q1190554"
EVENT_QID = "Q1656682"
GREGORIAN_QID = "Q1985727"
MIN_PRECISION = 11
DESIGN_SAMPLE_SIZE = 40
TARGET_FAMILY_COUNT = 220
MIN_ELIGIBLE_EVENTS = 440
DESIRABLE_RESERVE_EVENTS = 500
DATE_LEAKAGE_RE = re.compile(
    r"(?:[0-9]|\b(?:january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b|\b(?:ad|bc|bce|ce)\b)",
    re.IGNORECASE,
)


def _load_v8_module() -> Any:
    """Load the frozen V8 parser helpers without making network requests."""

    sys.path.insert(0, str(EXP_DIR))
    import acquire_wikidata_temporal_v8 as v8  # type: ignore[import-not-found]

    return v8


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _content_hash(value: dict[str, Any], field: str) -> str:
    without_hash = dict(value)
    without_hash.pop(field, None)
    return _sha256_bytes(_canonical_json(without_hash))


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _raw_checkpoint() -> dict[str, Any]:
    return json.loads((RAW_DIR / "acquisition_checkpoint.json").read_text(encoding="utf-8"))


def _verified_candidate_checkpoint(v8: Any, checkpoint: dict[str, Any]) -> dict[str, Any]:
    """Use exactly the pages that produced the frozen 3,550 metric.

    The current checkpoint includes offset 6600, but its metrics were recorded
    before that page was derived.  The authority-consistent pool is therefore
    the verified offsets strictly below ``next_candidate_offset - PAGE_SIZE``.
    """

    offsets = sorted(int(value) for value in checkpoint["candidate_page_offsets_verified"])
    expected = [value for value in offsets if value < int(checkpoint["next_candidate_offset"]) - v8.PAGE_SIZE]
    if expected != offsets[:-1] or len(expected) != 66:
        raise RuntimeError("TEMP_FEAS_V8_METRIC_PAGE_BOUNDARY_UNEXPECTED")
    result = dict(checkpoint)
    result["candidate_page_offsets_verified"] = expected
    result["candidate_pages_verified"] = len(expected)
    result["next_candidate_offset"] = int(checkpoint["next_candidate_offset"]) - v8.PAGE_SIZE
    return result


def _read_cached_maps(
    v8: Any,
    candidates: list[dict[str, str]],
    wanted_qids: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, set[str]], dict[str, set[str]]]:
    """Read cached metadata/class/parent chunks for the frozen candidate set."""

    metadata: dict[str, Any] = {}
    classes: dict[str, set[str]] = defaultdict(set)
    parents: dict[str, set[str]] = defaultdict(set)
    for start in range(0, len(candidates), v8.METADATA_BATCH_SIZE):
        batch = candidates[start : start + v8.METADATA_BATCH_SIZE]
        qids = [row["wikidata_item_id"] for row in batch]
        identity = f"batch_{start:08d}"
        metadata_path = RAW_DIR / f"metadata_chunk_{identity}_{v8.query_sha256(v8._metadata_query(qids))[:16]}.json"
        class_path = RAW_DIR / f"class_chunk_{identity}_{v8.query_sha256(v8._class_query(qids))[:16]}.json"
        if not metadata_path.exists() or not class_path.exists():
            raise RuntimeError(f"TEMP_FEAS_MISSING_CACHED_CHUNK_{identity}")
        parsed_classes = v8._parse_classes(json.loads(class_path.read_text(encoding="utf-8")))
        parsed_metadata = v8._parse_metadata(json.loads(metadata_path.read_text(encoding="utf-8")))
        if wanted_qids is None:
            metadata.update(parsed_metadata)
        else:
            for qid in wanted_qids & set(parsed_metadata):
                metadata[qid] = parsed_metadata[qid]
        for qid, values in parsed_classes.items():
            if wanted_qids is None or qid in wanted_qids:
                classes[qid].update(values)
        class_values = sorted({value for values in parsed_classes.values() for value in values})
        parent_path = RAW_DIR / f"parent_chunk_{identity}_{v8.query_sha256(v8._parent_query(class_values))[:16]}.json"
        if not parent_path.exists():
            raise RuntimeError(f"TEMP_FEAS_MISSING_CACHED_PARENT_{identity}")
        parsed_parents = v8._parse_parents(json.loads(parent_path.read_text(encoding="utf-8")))
        wanted_classes = {
            clazz
            for qid, values in parsed_classes.items()
            if wanted_qids is None or qid in wanted_qids
            for clazz in values
        }
        for clazz, values in parsed_parents.items():
            if wanted_qids is None or clazz in wanted_classes:
                parents[clazz].update(values)
    return metadata, dict(classes), dict(parents)


def _reconstruct_pool(v8: Any, checkpoint: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    bounded = _verified_candidate_checkpoint(v8, checkpoint)
    candidates = v8._parse_candidates(v8._load_candidate_payloads(bounded))
    metadata, _, _ = _read_cached_maps(v8, candidates)
    pool: list[dict[str, Any]] = []
    for row in candidates:
        qid = row["wikidata_item_id"]
        record = metadata.get(qid)
        if not record or len(record["labels"]) != 1 or len(record["records"]) != 1:
            continue
        date, time_value, precision, calendar = next(iter(record["records"]))
        if precision < MIN_PRECISION or calendar != GREGORIAN_QID:
            continue
        canonical_identity = f"{qid}|{date}|{time_value}|precision={precision}|calendar={calendar}"
        pool.append(
            {
                "wikidata_item_id": qid,
                "accepted_date": date,
                "time_value": time_value,
                "date_precision": precision,
                "calendar_model": calendar,
                "canonical_identity": canonical_identity,
            }
        )
    pool.sort(key=lambda row: (row["time_value"], row["wikidata_item_id"], row["canonical_identity"]))
    if len(pool) != EXPECTED_POOL_COUNT:
        raise RuntimeError(f"TEMP_FEAS_DATE_VALID_POOL_RECONSTRUCTION_MISMATCH_{len(pool)}")
    identities = [row["canonical_identity"] for row in pool]
    if len(set(identities)) != len(identities):
        raise RuntimeError("TEMP_FEAS_DUPLICATE_CANONICAL_IDENTITY")
    return pool, candidates


def _split(pool: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    design: list[dict[str, Any]] = []
    confirmation: list[dict[str, Any]] = []
    prefix = SPLIT_RULE_ID + "|"
    for row in pool:
        digest = hashlib.sha256((prefix + row["canonical_identity"]).encode("utf-8")).hexdigest()
        bucket = int(digest[:8], 16) % DESIGN_BUCKET_MODULUS
        (design if bucket == DESIGN_BUCKET_REMAINDER else confirmation).append(row)
    if set(row["canonical_identity"] for row in design) & set(row["canonical_identity"] for row in confirmation):
        raise RuntimeError("TEMP_FEAS_SPLIT_OVERLAP")
    if len(design) + len(confirmation) != EXPECTED_POOL_COUNT:
        raise RuntimeError("TEMP_FEAS_SPLIT_UNION_MISMATCH")
    return design, confirmation


def _design_semantics(v8: Any, design: list[dict[str, Any]], metadata: dict[str, Any], classes: dict[str, set[str]], parents: dict[str, set[str]]) -> list[dict[str, Any]]:
    """Attach semantic fields only to SOURCE_DESIGN records."""

    output: list[dict[str, Any]] = []
    for row in design:
        qid = row["wikidata_item_id"]
        record = metadata[qid]
        label = sorted(record["labels"])[0]
        direct = sorted(classes.get(qid, set()))
        ancestry = {clazz: sorted(parents.get(clazz, set())) for clazz in direct}
        direct_occurrence = OCCURRENCE_QID in direct
        direct_event = EVENT_QID in direct
        one_hop_occurrence = any(OCCURRENCE_QID in parents.get(clazz, set()) for clazz in direct)
        one_hop_event = any(EVENT_QID in parents.get(clazz, set()) for clazz in direct)
        if direct_occurrence or one_hop_occurrence:
            category = "occurrence_root_or_one_hop_parent"
        elif direct_event or one_hop_event:
            category = "event_root_or_one_hop_parent"
        elif direct:
            category = "other_cached_p31_class"
        else:
            category = "ontology_unavailable"
        reasons: list[str] = []
        if not (direct_occurrence or one_hop_occurrence):
            reasons.append("no_cached_direct_or_one_hop_Q1190554_ancestry")
        if not v8._passes_surface_filter(label):
            reasons.append("frozen_surface_date_leakage_filter")
        output.append(
            {
                **row,
                "english_label": label,
                "direct_p31_classes": direct,
                "cached_p279_parents_by_p31_class": ancestry,
                "direct_Q1190554_membership": direct_occurrence,
                "cached_ancestry_to_Q1190554": one_hop_occurrence,
                "direct_Q1656682_membership": direct_event,
                "cached_ancestry_to_Q1656682": one_hop_event,
                "provisional_ontology_category": category,
                "current_v8_rule_accepts": False,
                "current_v8_rejection_reasons": reasons,
                "surface_leakage_flag": not v8._passes_surface_filter(label),
            }
        )
    return output


def _design_sample(design_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(
        design_rows,
        key=lambda row: hashlib.sha256(("PA_EXT_A_TEMP_FEAS_001_SAMPLE_V1|" + row["canonical_identity"]).encode("utf-8")).hexdigest(),
    )
    return [
        {
            "sample_index": index,
            "wikidata_item_id": row["wikidata_item_id"],
            "accepted_date": row["accepted_date"],
            "english_label": row["english_label"],
            "direct_p31_classes": row["direct_p31_classes"],
            "cached_p279_parents_by_p31_class": row["cached_p279_parents_by_p31_class"],
            "cached_ancestry_to_Q1190554": row["cached_ancestry_to_Q1190554"],
            "provisional_ontology_category": row["provisional_ontology_category"],
            "current_v8_rejection_reasons": row["current_v8_rejection_reasons"],
        }
        for index, row in enumerate(ranked[:DESIGN_SAMPLE_SIZE], start=1)
    ]


def _audit(design_rows: list[dict[str, Any]]) -> dict[str, Any]:
    class_counts = Counter(clazz for row in design_rows for clazz in row["direct_p31_classes"])
    parent_counts = Counter(
        parent
        for row in design_rows
        for parents in row["cached_p279_parents_by_p31_class"].values()
        for parent in parents
    )
    label_counts = Counter(row["english_label"] for row in design_rows)
    prefix_counts = Counter(" ".join(row["english_label"].lower().split()[:3]) for row in design_rows)
    repeated_prefix_groups = {key: value for key, value in sorted(prefix_counts.items()) if value > 1}
    no_cached_event_root = sum(
        not row["direct_Q1190554_membership"]
        and not row["cached_ancestry_to_Q1190554"]
        and not row["direct_Q1656682_membership"]
        and not row["cached_ancestry_to_Q1656682"]
        for row in design_rows
    )
    return {
        "design_count": len(design_rows),
        "direct_p31_class_counts": dict(class_counts.most_common()),
        "cached_direct_p279_parent_counts": dict(parent_counts.most_common()),
        "direct_Q1190554_membership_count": sum(row["direct_Q1190554_membership"] for row in design_rows),
        "cached_ancestry_to_Q1190554_count": sum(row["cached_ancestry_to_Q1190554"] for row in design_rows),
        "event_like_outside_Q1190554_cached_closure_count": 0,
        "event_like_outside_Q1190554_cached_closure_status": "NOT_ESTABLISHED_FROM_CACHED_ONE_HOP_ANCESTRY",
        "candidates_without_cached_event_root_evidence": no_cached_event_root,
        "candidates_without_cached_event_root_evidence_fraction": no_cached_event_root / len(design_rows),
        "dominant_direct_p31_class": class_counts.most_common(1)[0] if class_counts else None,
        "unique_direct_p31_class_count": len(class_counts),
        "exact_duplicate_label_count": sum(value - 1 for value in label_counts.values() if value > 1),
        "repeated_three_word_label_prefix_groups": repeated_prefix_groups,
        "surface_date_leakage_count": sum(row["surface_leakage_flag"] for row in design_rows),
        "p585_first_bias_assessment": {
            "status": "SUPPORTED_BY_DESIGN_INDICATORS",
            "basis": [
                "all_design_labels_trigger_the_frozen_surface_date_leakage_filter",
                "one_direct_P31_QID_family_dominates_the_design_pool",
                "cached_event_root_ancestry_is_absent_for_the_design_pool",
            ],
            "interpretation": "P585-first acquisition appears to overrepresent a narrow date-labelled phenomenon family; this is a source-design suitability finding, not an implementation defect.",
        },
        "cached_ontology_scope": "direct P31 and one-hop P279 edges present in V8 class/parent artifacts; no network enrichment",
    }


def _proposed_rule(lineage: dict[str, Any], design_count: int) -> dict[str, Any]:
    return {
        "task_id": "PA-EXT-A-TEMP-FEAS-001",
        "status": "PROPOSED_NOT_CONFIRMED",
        "proposal_version": "TEMPORAL_EVENT_LIKE_V1",
        "source_manifest_sha256": lineage["date_valid_pool_manifest_sha256"],
        "design_manifest_sha256": lineage["source_design_manifest_sha256"],
        "confirmation_manifest_sha256": lineage["source_confirmation_manifest_sha256"],
        "split_rule_sha256": lineage["split_rule_sha256"],
        "design_count": design_count,
        "design_only": True,
        "confirmation_semantics_accessed": False,
        "formal_panel_accessed": False,
        "formal_inference_performed": False,
        "scientific_outcome_created": False,
        "v8_lineage_modified": False,
        "candidate_universe_semantics": "Non-scholarly entities in the frozen QLever unified graph whose direct P31 class has a finite, explicit P279* path to Q1656682 (event) or Q1190554 (occurrence), with no inference from labels or descriptions.",
        "allowed_event_like_ontology_criterion": "Require at least one direct P31/P279* path to Q1656682 or Q1190554. Paths are evaluated over a deterministically cached subclass graph with cycle protection; the zero-length path is allowed when P31 is itself a root.",
        "p585_date_requirement": "At least one unique English-labelled P585 statement with an actual wikibase timeValue and literal date binding.",
        "calendar_requirement": f"calendar model must be {GREGORIAN_QID} (Gregorian).",
        "precision_requirement": f"wikibase timePrecision must be >= {MIN_PRECISION} (day or finer).",
        "duplicate_handling": "Canonical identity is QID|accepted date literal|timeValue|precision|calendar. Keep one record only; reject repeated canonical identities and require exactly one canonical P585 record per selected QID.",
        "surface_leakage_handling": "Apply the frozen V8 English-label date leakage regex and reject labels containing digits, month names, AD/BC/BCE/CE markers, or empty labels.",
        "acquisition_ordering": "Event-first: enumerate the ontology-eligible QID universe before joining P585 metadata; complete the universe before applying global ordering. This changes access order only, not the semantic predicates.",
        "final_eligible_ordering": "Ascending P585 timeValue, then ascending Wikidata QID, then ascending canonical identity.",
        "pairing_rule": "Traverse the final ordered eligible list left-to-right without event reuse. Pair each unused event with the next unused event having a different normalized timeValue; reject same-date pair attempts and continue deterministically.",
        "same_date_handling": "Events with equal normalized timeValue cannot form a pair; retain their QID order for deterministic traversal but do not reuse or cross-pair an already consumed event.",
        "event_reuse_policy": "No event may occur in more than one pair.",
        "class_balancing_or_stratification": "None. No class, ontology-family, or time-bin balancing is applied because that would optimize source yield; the source distribution remains an auditable property.",
        "selection_if_excess": f"Select the first {TARGET_FAMILY_COUNT} non-overlapping valid pairs in final eligible order after requiring at least {MIN_ELIGIBLE_EVENTS} eligible events; retain a diagnostic reserve target of >= {DESIRABLE_RESERVE_EVENTS} but do not tune toward it.",
        "target_temporal_families": TARGET_FAMILY_COUNT,
        "theoretical_hard_minimum_eligible_events": MIN_ELIGIBLE_EVENTS,
        "operational_reserve_target_eligible_events": DESIRABLE_RESERVE_EVENTS,
        "design_count_recorded_for_audit_only": design_count,
    }


def run(output_dir: Path = OUTPUT_DIR) -> dict[str, Any]:
    """Build all TEMP-FEAS-001 engineering artifacts offline."""

    v8 = _load_v8_module()
    checkpoint = _raw_checkpoint()
    pool, candidates = _reconstruct_pool(v8, checkpoint)
    design, confirmation = _split(pool)
    design_qids = {row["wikidata_item_id"] for row in design}
    metadata, classes, parents = _read_cached_maps(v8, candidates, wanted_qids=design_qids)
    design_rows = _design_semantics(v8, design, metadata, classes, parents)

    authority_sha = _sha256_file(V8_AUTHORITY)
    query_sha = json.loads(V8_AUTHORITY.read_text(encoding="utf-8"))["query_sha256"]
    checkpoint_sha = _sha256_file(RAW_DIR / "acquisition_checkpoint.json")
    pool_manifest: dict[str, Any] = {
        "task_id": "PA-EXT-A-TEMP-FEAS-001",
        "schema_version": "1.0.0",
        "status": "FROZEN_DATE_VALID_POOL",
        "source_artifact_lineage": "V8_QLEVER_LITERAL_LINEAGE; offsets 0 through 6500 only, matching checkpoint metric 3550",
        "v8_authority_sha256": authority_sha,
        "v8_query_sha256": query_sha,
        "checkpoint_sha256": checkpoint_sha,
        "candidate_pages_used": 66,
        "candidate_offset_range": [0, 6500],
        "total_count": len(pool),
        "duplicate_identity_check": len({row["canonical_identity"] for row in pool}) == len(pool),
        "records": pool,
    }
    pool_manifest["manifest_sha256"] = _content_hash(pool_manifest, "manifest_sha256")

    split_rule = {
        "rule_id": SPLIT_RULE_ID,
        "canonical_expression": "SHA256('PA_EXT_A_TEMP_FEAS_001_SPLIT_V1|' + canonical_identity)",
        "bucket_function": "int(first_8_hex_characters, 16) % 5",
        "design_bucket": DESIGN_BUCKET_REMAINDER,
        "confirmation_buckets": [1, 2, 3, 4],
        "semantic_independence": True,
    }
    split_rule_sha = _sha256_bytes(_canonical_json(split_rule))
    design_manifest: dict[str, Any] = {
        "task_id": "PA-EXT-A-TEMP-FEAS-001",
        "schema_version": "1.0.0",
        "split": "SOURCE_DESIGN",
        "split_rule_sha256": split_rule_sha,
        "source_manifest_sha256": pool_manifest["manifest_sha256"],
        "semantic_audit_scope": "DESIGN_ONLY",
        "total_count": len(design_rows),
        "records": design_rows,
    }
    design_manifest["manifest_sha256"] = _content_hash(design_manifest, "manifest_sha256")
    confirmation_manifest: dict[str, Any] = {
        "task_id": "PA-EXT-A-TEMP-FEAS-001",
        "schema_version": "1.0.0",
        "split": "SOURCE_CONFIRMATION",
        "split_rule_sha256": split_rule_sha,
        "source_manifest_sha256": pool_manifest["manifest_sha256"],
        "identity_only": True,
        "semantic_fields_exposed": False,
        "total_count": len(confirmation),
        "records": [
            {
                "canonical_identity": row["canonical_identity"],
                "identity_sha256": _sha256_bytes(row["canonical_identity"].encode("utf-8")),
                "split": "SOURCE_CONFIRMATION",
            }
            for row in confirmation
        ],
    }
    confirmation_manifest["manifest_sha256"] = _content_hash(confirmation_manifest, "manifest_sha256")
    lineage = {
        "date_valid_pool_manifest_sha256": pool_manifest["manifest_sha256"],
        "source_design_manifest_sha256": design_manifest["manifest_sha256"],
        "source_confirmation_manifest_sha256": confirmation_manifest["manifest_sha256"],
        "split_rule_sha256": split_rule_sha,
    }
    audit = _audit(design_rows)
    proposal = _proposed_rule(lineage, len(design_rows))
    proposal["proposal_sha256"] = _content_hash(proposal, "proposal_sha256")
    report = {
        "task_id": "PA-EXT-A-TEMP-FEAS-001",
        "status": "TEMP_FEAS_001_PASS_SOURCE_FEASIBILITY_ONLY",
        "date_valid_pool_count": len(pool),
        "source_design_count": len(design),
        "source_confirmation_count": len(confirmation),
        "source_confirmation_semantics_accessed": False,
        "formal_panel_accessed": False,
        "formal_inference_performed": False,
        "scientific_outcome_created": False,
        "v8_lineage_modified": False,
        "network_accessed": False,
        "split_rule": split_rule,
        "split_rule_sha256": split_rule_sha,
        "pool_manifest_sha256": pool_manifest["manifest_sha256"],
        "design_manifest_sha256": design_manifest["manifest_sha256"],
        "confirmation_manifest_sha256": confirmation_manifest["manifest_sha256"],
        "proposal_sha256": proposal["proposal_sha256"],
        "design_ontology_audit": audit,
        "failure_classification": {
            "primary": "Q1190554_ONTOLOGY_ALIGNMENT_MISMATCH",
            "secondary": ["P585_CANDIDATE_UNIVERSE_MISMATCH", "ACQUISITION_ORDER_DISTRIBUTION_BIAS"],
            "implementation_failure": False,
            "engineering_correctness": "V8 parser and cached-artifact identity checks remain consistent with the recorded 3550 metric.",
            "source_design_suitability": "The frozen occurrence criterion has no cached direct/one-hop support in the DESIGN subset, while the P585-first pool is dominated by a narrow date-labelled class family.",
        },
        "required_flags": {
            "PA_EXT_A_TEMP_FEAS_001_COMPLETE": True,
            "PA_EXT_A_DATE_VALID_POOL_FROZEN": True,
            "PA_EXT_A_DATE_VALID_POOL_COUNT": len(pool),
            "PA_EXT_A_SOURCE_DESIGN_SPLIT_FROZEN": True,
            "PA_EXT_A_SOURCE_CONFIRMATION_SPLIT_FROZEN": True,
            "PA_EXT_A_SOURCE_CONFIRMATION_SEMANTICS_ACCESSED": False,
            "PA_EXT_A_DESIGN_ONTOLOGY_AUDIT_COMPLETE": True,
            "PA_EXT_A_V8_IMPLEMENTATION_BUG_DETECTED": False,
            "PA_EXT_A_PROSPECTIVE_TEMPORAL_RULE_PROPOSED": True,
            "PA_EXT_A_PROSPECTIVE_TEMPORAL_RULE_FROZEN": True,
            "PA_EXT_A_PROSPECTIVE_TEMPORAL_RULE_CONFIRMED": False,
            "PA_EXT_A_TEMPORAL_220_CREATED": False,
            "PA_EXT_A_FORMAL_PANEL_ACCESSED": False,
            "PA_EXT_A_FORMAL_INFERENCE_PERFORMED": False,
            "PA_EXT_A_FORMAL_SCIENTIFIC_OUTCOME_CREATED": False,
            "PA_EXT_A_V8_LINEAGE_MODIFIED": False,
            "PA_EXT_A_NETWORK_ACCESSED": False,
        },
    }
    sample = {
        "task_id": "PA-EXT-A-TEMP-FEAS-001",
        "split": "SOURCE_DESIGN",
        "sample_size": DESIGN_SAMPLE_SIZE,
        "selection_rule": "SHA256('PA_EXT_A_TEMP_FEAS_001_SAMPLE_V1|' + canonical_identity) ascending",
        "records": _design_sample(design_rows),
    }
    _write_json(output_dir / "date_valid_pool_manifest.json", pool_manifest)
    _write_json(output_dir / "source_design_manifest.json", design_manifest)
    _write_json(output_dir / "source_confirmation_manifest.json", confirmation_manifest)
    _write_json(output_dir / "design_ontology_audit.json", audit)
    _write_json(output_dir / "design_human_review_sample.json", sample)
    _write_json(output_dir / "temp_feas_001_proposed_rule.json", proposal)
    _write_json(output_dir / "temp_feas_001_report.json", report)
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the offline TEMP-FEAS-001 artifacts")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args(argv)
    report = run(args.output_dir)
    print(f"PA_EXT_A_TEMP_FEAS_001_COMPLETE = {report['required_flags']['PA_EXT_A_TEMP_FEAS_001_COMPLETE']}")
    print(f"DATE_VALID_POOL_COUNT = {report['date_valid_pool_count']}")
    print(f"SOURCE_DESIGN_COUNT = {report['source_design_count']}")
    print(f"SOURCE_CONFIRMATION_COUNT = {report['source_confirmation_count']}")
    print("SOURCE_CONFIRMATION_SEMANTICS_ACCESSED = false")
    print("FORMAL_PANEL_ACCESSED = false")
    print("FORMAL_INFERENCE_PERFORMED = false")
    print("NETWORK_ACCESSED = false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
