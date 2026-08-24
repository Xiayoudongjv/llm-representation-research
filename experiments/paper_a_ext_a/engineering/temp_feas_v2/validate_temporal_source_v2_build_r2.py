"""Validate the R2 freshness-authority repair without network or acquisition."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
RUNNER_PATH = ROOT / "experiments" / "paper_a_ext_a" / "acquire_temporal_source_v2.py"
PROTOCOL = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_protocol.json"
AMENDMENT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temporal_source_v2_wdqs_backend_amendment.json"
EVIDENCE = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "temp_v2_build_r2_engineering.json"
EXPECTED_PROTOCOL_SHA = "5018718739045b25514c8e94ede7e7ba6a99faa56b43c2156d27fbb97cfe2b6b"
EXPECTED_AMENDMENT_SHA = "326e2e3312ffd8a8877197d51d6bd4685f30c8a8efbe048bc243128911bf7413"


def _load_runner():
    spec = importlib.util.spec_from_file_location("temp_v2_runner_r2_validator", RUNNER_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def validate() -> dict[str, object]:
    runner = _load_runner()
    protocol_sha = hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()
    amendment_payload = json.loads(AMENDMENT.read_text(encoding="utf-8"))
    amendment_sha = hashlib.sha256(AMENDMENT.read_bytes()).hexdigest()
    amendment_logical_sha = runner.historical_content_hash(amendment_payload, "amendment_sha256")
    evidence = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    info = runner.load_freshness_exclusion_authority()
    if protocol_sha != EXPECTED_PROTOCOL_SHA or amendment_logical_sha != EXPECTED_AMENDMENT_SHA:
        raise RuntimeError("TEMPORAL_SOURCE_V2_BUILD_R2_FROZEN_AUTHORITY_CHANGED")
    if info["logical_manifest_sha256"] != runner.EXPECTED_DATE_POOL_MANIFEST_SHA256:
        raise RuntimeError("TEMPORAL_SOURCE_V2_BUILD_R2_LOGICAL_MANIFEST_AUTHORITY_FAILED")
    if info["date_pool_count"] != 3550 or info["v8_page_count"] != 67 or info["v8_qid_count"] != 6695 or info["union_count"] != 6695:
        raise RuntimeError("TEMPORAL_SOURCE_V2_BUILD_R2_EXCLUSION_COUNTS_FAILED")
    if evidence.get("task_id") != "PA-EXT-A-TEMP-V2-BUILD-R2" or evidence.get("engineering_only") is not True:
        raise RuntimeError("TEMPORAL_SOURCE_V2_BUILD_R2_EVIDENCE_IDENTITY_FAILED")
    for flag in (
        "TEMPORAL_SOURCE_V2_BUILD_R2_COMPLETE",
        "TEMPORAL_SOURCE_V2_FRESHNESS_AUTHORITY_BINDING_REPAIRED",
        "TEMPORAL_SOURCE_V2_HISTORICAL_MANIFEST_AUTHORITY_PRESERVED",
        "TEMPORAL_SOURCE_V2_V8_EXCLUSION_UNIVERSE_QUALIFIED",
        "TEMPORAL_SOURCE_V2_ZERO_DATA_RESTART_QUALIFIED",
        "TEMPORAL_SOURCE_V2_LONG_RUN_READY",
    ):
        if evidence.get(flag) is not True:
            raise RuntimeError(f"TEMPORAL_SOURCE_V2_BUILD_R2_FLAG_FAILED:{flag}")
    result = {
        "valid": True,
        "base_protocol_sha256": protocol_sha,
        "wdqs_amendment_sha256": amendment_logical_sha,
        "wdqs_amendment_raw_sha256": amendment_sha,
        "raw_manifest_sha256": info["raw_manifest_sha256"],
        "logical_manifest_sha256": info["logical_manifest_sha256"],
        "date_pool_qid_count": info["date_pool_count"],
        "v8_candidate_page_count": info["v8_page_count"],
        "v8_unique_qid_count": info["v8_qid_count"],
        "union_exclusion_count": info["union_count"],
        "full_acquisition_performed": False,
        "canonical_220_created": False,
        "model_inference_performed": False,
        "scientific_logic_changed": False,
    }
    return result


if __name__ == "__main__":
    print(json.dumps(validate(), ensure_ascii=False, sort_keys=True))
    print("TEMPORAL_SOURCE_V2_BUILD_R2_VALIDATION=PASS")
