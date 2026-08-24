"""Static/offline validator for the TEMPORAL_SOURCE_V2 production runner."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RUNNER = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
MONITOR = ROOT / "experiments" / "paper_a_ext_a" / "monitor_temporal_source_v2.py"
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
V8_AUTHORITY = ROOT / "experiments" / "paper_a_ext_a" / "paper_a_ext_a_temporal_asset_source_v8.json"
V8_CHECKPOINT = ROOT / "experiments" / "paper_a_ext_a" / "data" / "raw" / "wikidata_v8" / "acquisition_checkpoint.json"
OLD_REPORT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_002r" / "temp_feas_002r_report.json"
EXPECTED_PROTOCOL_SHA = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"
EXPECTED_V8_AUTHORITY_SHA = "47a2ce443fe097b32fc391b910d97860593093ec19c9e362ec7019d5f3984ca7"
EXPECTED_V8_CHECKPOINT_SHA = "a6f21f6bdf2267d14c36f26231a61d8279ed1bbe66ce0265e25c6fde61a59b38"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> dict:
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    source = RUNNER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    functions = {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    required = {"initial_checkpoint", "write_checkpoint", "load_checkpoint", "resolve_canonical_time", "select_events", "pair_events", "publish_canonical", "stopping_state"}
    errors = []
    if sha256_file(PROTOCOL) != EXPECTED_PROTOCOL_SHA:
        errors.append("protocol_sha_mismatch")
    if not required <= functions:
        errors.append("runner_function_missing")
    if not MONITOR.exists():
        errors.append("monitor_missing")
    if protocol.get("required_flags", {}).get("TEMPORAL_SOURCE_V2_DATA_ACCESSED") is not False:
        errors.append("protocol_data_accessed")
    if sha256_file(V8_AUTHORITY) != EXPECTED_V8_AUTHORITY_SHA:
        errors.append("v8_authority_changed")
    if sha256_file(V8_CHECKPOINT) != EXPECTED_V8_CHECKPOINT_SHA:
        errors.append("v8_checkpoint_changed")
    if sha256_file(OLD_REPORT) != protocol["prior_source_evidence"]["old_confirmation_report_sha256"]:
        errors.append("old_negative_result_changed")
    if (ROOT / "experiments" / "paper_a_ext_a" / "data" / "wikidata_temporal_source_v2").exists():
        errors.append("canonical_output_already_exists")
    if "transformers" in source or "torch" in source:
        errors.append("model_dependency_present")
    result = {"valid": not errors, "errors": errors, "network_accessed": False, "full_acquisition_performed": False}
    if errors:
        raise RuntimeError("TEMPORAL_SOURCE_V2_RUNNER_VALIDATION_FAILED:" + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    validate()
    print("TEMPORAL_SOURCE_V2_RUNNER_VALIDATION=PASS")
