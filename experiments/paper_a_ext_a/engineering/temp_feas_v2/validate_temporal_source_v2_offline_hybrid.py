"""Offline-only validator for the final TEMP-V2 hybrid architecture."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
RUNNER = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2_offline.py"
MONITOR = ROOT / "experiments" / "paper_a_ext_a" / "monitor_temporal_source_v2_offline.py"
RECORD = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temp_v2_offline_hybrid_build_engineering.json"
EXPECTED_PROTOCOL_SHA = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"


def validate() -> dict[str, object]:
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != EXPECTED_PROTOCOL_SHA:
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_PROTOCOL_CHANGED")
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    required = {
        "_unquote_literal", "_decode_iri_ref", "_validate_blank_node_label", "_read_term", "parse_nt_line", "iter_nt_triples", "scan_p279_closure", "scan_p31_candidates", "scan_labels",
        "build_structural_snapshot", "compute_root_compatible_classes", "entity_to_candidate",
        "finalize_hydrated_candidates", "preflight", "main",
    }
    missing = sorted(required - functions)
    if missing or "transformers" in source or "torch" in source or "json.loads(quoted)" in source:
        raise RuntimeError(f"TEMPORAL_SOURCE_V2_OFFLINE_HYBRID_VALIDATION_FAILED:{missing}")
    for marker in ('"t": "\\t"', '"u"', '"U"', "invalid Unicode scalar value", "blank_node"):
        if marker not in source:
            raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_NTRIPLES_DECODER_MISSING")
    if not MONITOR.exists() or "read_status" not in MONITOR.read_text(encoding="utf-8"):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_MONITOR_MISSING")
    record = json.loads(RECORD.read_text(encoding="utf-8"))
    required_flags = record.get("required_flags", {})
    expected_true = {
        "TEMPORAL_SOURCE_V2_OFFLINE_HYBRID_BUILD_COMPLETE",
        "TEMPORAL_SOURCE_V2_STREAMING_BZ2_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_P279_CLOSURE_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_P31_DISCOVERY_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_FRESHNESS_EXCLUSION_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_LABEL_HANDLING_QUALIFIED",
        "TEMPORAL_SOURCE_V2_FULL_ENTITY_HYDRATION_LAYER_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_CHECKPOINT_RESUME_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_PROGRESS_MONITOR_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_ONLINE_NORMALIZED_CONTRACT_EQUIVALENT",
        "TEMPORAL_SOURCE_V2_OFFLINE_R5_COMPLETE",
        "TEMPORAL_SOURCE_V2_NTRIPLES_LITERAL_PARSER_REPAIRED",
        "TEMPORAL_SOURCE_V2_NTRIPLES_ECHAR_QUALIFIED",
        "TEMPORAL_SOURCE_V2_NTRIPLES_UCHAR_QUALIFIED",
        "TEMPORAL_SOURCE_V2_REALISTIC_BZ2_FIXTURE_QUALIFIED",
        "TEMPORAL_SOURCE_V2_OFFLINE_R5_CORRECTION_COMPLETE",
        "TEMPORAL_SOURCE_V2_NTRIPLES_BLANK_NODE_SUPPORT_QUALIFIED",
        "TEMPORAL_SOURCE_V2_NTRIPLES_SUBJECT_GRAMMAR_COMPLETE",
        "TEMPORAL_SOURCE_V2_NTRIPLES_OBJECT_GRAMMAR_COMPLETE",
        "TEMPORAL_SOURCE_V2_OFFLINE_LONG_RUN_READY",
    }
    if any(required_flags.get(flag) is not True for flag in expected_true):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_REQUIRED_QUALIFICATION_FLAG_MISSING")
    expected_false = {
        "TEMPORAL_SOURCE_V2_BASE_PROTOCOL_CHANGED",
        "TEMPORAL_SOURCE_V2_SCIENTIFIC_SEMANTICS_CHANGED",
        "TEMPORAL_SOURCE_V2_SCIENTIFIC_LOGIC_CHANGED",
        "TEMPORAL_SOURCE_V2_FRESHNESS_AUTHORITY_CHANGED",
        "TEMPORAL_SOURCE_V2_FRESHNESS_RULE_CHANGED",
        "TEMPORAL_SOURCE_V2_SELECTION_CHANGED",
        "TEMPORAL_SOURCE_V2_PAIRING_CHANGED",
        "TEMPORAL_SOURCE_V2_REAL_DUMP_DOWNLOADED",
        "TEMPORAL_SOURCE_V2_REAL_DUMP_SCANNED",
        "REAL_WIKIDATA_DUMP_SCANNED_BY_CODEX",
        "TEMPORAL_SOURCE_V2_ENTITY_HYDRATION_PERFORMED",
        "REAL_WIKIDATA_ENTITY_HYDRATION_PERFORMED",
        "TEMPORAL_SOURCE_V2_FULL_ACQUISITION_PERFORMED",
        "TEMPORAL_SOURCE_V2_CANONICAL_220_CREATED",
        "FORMAL_MODEL_INFERENCE_PERFORMED",
        "FORMAL_SCIENTIFIC_OUTCOME_CREATED",
    }
    if any(required_flags.get(flag) is not False for flag in expected_false):
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_PRODUCTION_ACTION_FLAG_SET")
    if "bz2.BZ2File" not in source or "ENTITY_API_BATCH_SIZE" not in source:
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_STREAM_OR_HYDRATION_MISSING")
    if "load_freshness_exclusion_authority" not in source or "prepare_candidate" not in source:
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_FROZEN_LOGIC_REUSE_MISSING")
    if (ROOT / "experiments" / "paper_a_ext_a" / "data" / "wikidata_temporal_source_v2").exists():
        raise RuntimeError("TEMPORAL_SOURCE_V2_OFFLINE_CANONICAL_OUTPUT_EXISTS")
    result = {
        "valid": True,
        "protocol_sha256": EXPECTED_PROTOCOL_SHA,
        "network_acquisition_performed": False,
        "real_dump_scanned": False,
        "entity_hydration_performed": False,
        "canonical_220_created": False,
        "model_inference_performed": False,
        "formal_scientific_outcome_created": False,
    }
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
    print("TEMPORAL_SOURCE_V2_OFFLINE_HYBRID_VALIDATION=PASS")
