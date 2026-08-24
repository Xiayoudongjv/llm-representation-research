"""Offline validator for the frozen TEMPORAL_SOURCE_V2 WDQS amendment."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
AMENDMENT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_wdqs_backend_amendment.json"
ENGINEERING = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temp_v2_wdqs_backend_engineering.json"
RUNNER = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
EXPECTED_BASE_PROTOCOL_SHA = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"
EXPECTED_AMENDMENT_SHA = "326e2e3312ffd8a8877197d51d6bd4685f30c8a8efbe048bc243128911bf7413"
EXPECTED_ENDPOINT = "https://query.wikidata.org/sparql"
EXPECTED_BACKEND = "WIKIDATA_QUERY_SERVICE_OFFICIAL_MAIN_GRAPH"
EXPECTED_ENGINEERING_SHA = "9152a49757de214ca1a1f5a0dc1492c1176fded1a2f7ec00503730105d174f6b"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_without_hash(payload: dict) -> str:
    copy = dict(payload)
    copy.pop("amendment_sha256", None)
    return sha256_bytes(json.dumps(copy, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def engineering_authority_sha256(payload: dict) -> str:
    copy = dict(payload)
    copy.pop("artifact_sha256", None)
    return sha256_bytes(json.dumps(copy, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def validate() -> dict:
    errors: list[str] = []
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    amendment = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    engineering = json.loads(ENGINEERING.read_text(encoding="utf-8"))
    runner_source = RUNNER.read_text(encoding="utf-8")
    runner_tree = ast.parse(runner_source)
    classes = {node.name for node in ast.walk(runner_tree) if isinstance(node, ast.ClassDef)}
    functions = {node.name for node in ast.walk(runner_tree) if isinstance(node, ast.FunctionDef)}

    if sha256_file(PROTOCOL) != EXPECTED_BASE_PROTOCOL_SHA:
        errors.append("base_protocol_changed")
    if amendment.get("base_protocol_sha256") != EXPECTED_BASE_PROTOCOL_SHA:
        errors.append("amendment_base_protocol_mismatch")
    if amendment.get("amendment_type") != "BACKEND_ONLY":
        errors.append("amendment_type_changed")
    if amendment.get("status") != "FROZEN_BEFORE_WDQS_ACQUISITION":
        errors.append("amendment_not_frozen")
    if amendment.get("amendment_sha256") != EXPECTED_AMENDMENT_SHA or canonical_without_hash(amendment) != EXPECTED_AMENDMENT_SHA:
        errors.append("amendment_sha_mismatch")
    if engineering.get("artifact_sha256") != EXPECTED_ENGINEERING_SHA or engineering_authority_sha256(engineering) != EXPECTED_ENGINEERING_SHA:
        errors.append("engineering_record_sha_mismatch")
    if engineering.get("base_protocol_sha256") != EXPECTED_BASE_PROTOCOL_SHA or engineering.get("backend_amendment_sha256") != EXPECTED_AMENDMENT_SHA:
        errors.append("engineering_authority_mismatch")
    target = amendment.get("to_backend", {})
    if target.get("name") != EXPECTED_BACKEND or target.get("endpoint") != EXPECTED_ENDPOINT:
        errors.append("wdqs_identity_mismatch")
    if target.get("failure_policy") != "FAIL_CLOSED_NO_ACQUISITION":
        errors.append("failure_policy_changed")
    for field in ("scientific_protocol_changed", "source_selection_semantics_changed", "pairing_semantics_changed"):
        if amendment.get(field) is not False:
            errors.append(f"{field}_not_false")
    if protocol.get("required_flags", {}).get("TEMPORAL_SOURCE_V2_DATA_ACCESSED") is not False:
        errors.append("base_protocol_data_accessed")
    if "WikidataQueryServiceClient" not in classes or "run_production" not in functions:
        errors.append("wdqs_runner_entry_missing")
    for token in ("WDQS_ENDPOINT", "WDQS_AMENDMENT_SHA256", "TEMPORAL_SOURCE_V2_WDQS_ONTOLOGY_VISIBILITY_FAILED"):
        if token not in runner_source:
            errors.append(f"runner_missing_{token}")
    if (ROOT / "experiments" / "paper_a_ext_a" / "data" / "wikidata_temporal_source_v2").exists():
        errors.append("canonical_output_exists")
    result = {
        "valid": not errors,
        "errors": errors,
        "base_protocol_sha256": EXPECTED_BASE_PROTOCOL_SHA,
        "amendment_sha256": EXPECTED_AMENDMENT_SHA,
        "network_accessed": False,
        "full_acquisition_performed": False,
        "model_inference_performed": False,
    }
    if errors:
        raise RuntimeError("TEMPORAL_SOURCE_V2_WDQS_AMENDMENT_VALIDATION_FAILED:" + json.dumps(result, sort_keys=True))
    return result


if __name__ == "__main__":
    validate()
    print("TEMPORAL_SOURCE_V2_WDQS_AMENDMENT_VALIDATION=PASS")
    print("TEMPORAL_SOURCE_V2_FULL_ACQUISITION_PERFORMED=false")
    print("NETWORK_ACCESSED=false")
    print("MODEL_INFERENCE=false")
