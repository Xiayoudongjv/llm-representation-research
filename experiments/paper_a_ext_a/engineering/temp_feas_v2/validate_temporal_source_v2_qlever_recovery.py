"""Offline validator for the TEMP-V2 QLever recovery repair."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
EVIDENCE = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temp_v2_qlever_recovery_engineering.json"
QLEVER_CHECKPOINT = ROOT / "experiments" / "paper_a_ext_a" / "data" / "temporal_source_v2_runtime" / "checkpoint.json"
WDQS_CHECKPOINT = ROOT / "experiments" / "paper_a_ext_a" / "data" / "temporal_source_v2_runtime" / "wdqs_checkpoint.json"
EXPECTED_PROTOCOL_SHA = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"


def validate() -> dict[str, object]:
    errors: list[str] = []
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    record = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    flags = record.get("required_flags", {})
    if hashlib.sha256(PROTOCOL.read_bytes()).hexdigest() != EXPECTED_PROTOCOL_SHA:
        errors.append("base_protocol_changed")
    if not {"event_page_query", "_qid", "run_production", "prepare_checkpoint_for_resume"} <= functions:
        errors.append("runner_function_missing")
    for marker in (
        "PREFIX p: <http://www.wikidata.org/prop/>",
        "PREFIX ps: <http://www.wikidata.org/prop/statement/>",
        "PREFIX wikibase: <http://wikiba.se/ontology#>",
        "QID_URI_SPARQL_PATTERN",
        "FILTER(REGEX(STR(?item)",
        "active_client = client or QLeverClient()",
    ):
        if marker not in source:
            errors.append(f"runner_missing_{marker}")
    true_flags = {
        "TEMPORAL_SOURCE_V2_QLEVER_RECOVERY_COMPLETE",
        "TEMPORAL_SOURCE_V2_QLEVER_BACKEND_RESTORED",
        "TEMPORAL_SOURCE_V2_QLEVER_PREFIX_COMPLETION_QUALIFIED",
        "TEMPORAL_SOURCE_V2_QUERY_SIDE_QID_GATE_QUALIFIED",
        "TEMPORAL_SOURCE_V2_QID_GATE_PAGINATION_EQUIVALENT",
        "TEMPORAL_SOURCE_V2_FALSE_SOURCE_EXHAUSTION_REPAIRED",
        "TEMPORAL_SOURCE_V2_QLEVER_FRESH_RUN_STATE_QUALIFIED",
        "TEMPORAL_SOURCE_V2_QLEVER_LONG_RUN_READY",
    }
    false_flags = {
        "TEMPORAL_SOURCE_V2_BASE_PROTOCOL_CHANGED",
        "TEMPORAL_SOURCE_V2_SCIENTIFIC_LOGIC_CHANGED",
        "TEMPORAL_SOURCE_V2_FRESHNESS_RULE_CHANGED",
        "TEMPORAL_SOURCE_V2_SELECTION_CHANGED",
        "TEMPORAL_SOURCE_V2_PAIRING_CHANGED",
        "REAL_QLEVER_FULL_ACQUISITION_PERFORMED",
        "TEMPORAL_SOURCE_V2_CANONICAL_220_CREATED",
        "FORMAL_MODEL_INFERENCE_PERFORMED",
        "FORMAL_SCIENTIFIC_OUTCOME_CREATED",
    }
    if any(flags.get(name) is not True for name in true_flags):
        errors.append("required_true_flag_missing")
    if any(flags.get(name) is not False for name in false_flags):
        errors.append("required_false_flag_set")
    if QLEVER_CHECKPOINT.exists():
        checkpoint = json.loads(QLEVER_CHECKPOINT.read_text(encoding="utf-8"))
        zero_fields = {
            "current_acquisition_offset": 0,
            "fresh_candidates_discovered": 0,
            "artifact_chunk_count": 0,
            "final_eligible_events": 0,
            "canonical_events_count": 0,
            "families_count": 0,
        }
        if checkpoint.get("backend") != "QLever" or checkpoint.get("endpoint") != "https://qlever.dev/api/wikidata":
            errors.append("qlever_checkpoint_identity_mismatch")
        if any(checkpoint.get(key) != value for key, value in zero_fields.items()):
            errors.append("qlever_checkpoint_not_zero_data")
    if not WDQS_CHECKPOINT.exists():
        errors.append("historical_wdqs_checkpoint_missing")
    if (ROOT / "experiments" / "paper_a_ext_a" / "data" / "wikidata_temporal_source_v2").exists():
        errors.append("canonical_output_exists")
    result = {
        "valid": not errors,
        "errors": errors,
        "base_protocol_sha256": EXPECTED_PROTOCOL_SHA,
        "network_accessed": False,
        "full_acquisition_performed": False,
        "canonical_220_created": False,
        "model_inference_performed": False,
    }
    if errors:
        raise RuntimeError("TEMPORAL_SOURCE_V2_QLEVER_RECOVERY_VALIDATION_FAILED:" + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), sort_keys=True))
    print("TEMPORAL_SOURCE_V2_QLEVER_RECOVERY_VALIDATION=PASS")
