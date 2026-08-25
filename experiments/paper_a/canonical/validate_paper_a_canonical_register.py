"""Read-only integrity validator for the Paper A canonical registers."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SSOT = ROOT / "experiments/paper_a/canonical/paper_a_scientific_results.json"
CLAIMS = ROOT / "experiments/paper_a/canonical/paper_a_claim_register.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def get(data, path: str):
    for part in path.split("."):
        data = data[part]
    return data


def resolve_field(data, field_path: str):
    """Resolve the compact provenance paths used by this register."""
    current = data
    for part in field_path.split("."):
        if part.endswith(".length"):
            raise AssertionError("length must be a terminal path component")
        match = re.fullmatch(r"([^\[]+)(?:\[(\d+)\])?", part)
        if not match:
            raise AssertionError(f"unsupported provenance path component: {part}")
        current = current[match.group(1)]
        if match.group(2) is not None:
            current = current[int(match.group(2))]
    if field_path.endswith(".length"):
        raise AssertionError("length provenance paths are handled by the caller")
    return current


def check_numeric_nodes(node, sources, location="root"):
    if isinstance(node, bool) or node is None:
        return
    if isinstance(node, (int, float)):
        raise AssertionError(f"unprovenanced numeric value at {location}")
    if isinstance(node, list):
        for index, item in enumerate(node):
            check_numeric_nodes(item, f"{location}[{index}]")
    elif isinstance(node, dict):
        if set(node) >= {"value", "provenance"} and isinstance(node["value"], (int, float)) and not isinstance(node["value"], bool):
            provenance = node["provenance"]
            required = {"experiment", "canonical_path", "canonical_sha256", "field_path"}
            if set(provenance) != required:
                raise AssertionError(f"bad provenance at {location}")
            source = sources[provenance["canonical_path"]]
            assert sha256(ROOT / provenance["canonical_path"]) == provenance["canonical_sha256"], location
            field_path = provenance["field_path"]
            if field_path.endswith(".length"):
                source_value = resolve_field(source, field_path[:-len(".length")].rstrip("."))
                source_value = len(source_value)
            else:
                source_value = resolve_field(source, field_path)
            assert node["value"] == source_value, f"value mismatch at {location}: {node['value']} != {source_value}"
            return
        for key, value in node.items():
            check_numeric_nodes(value, sources, f"{location}.{key}")


def main() -> None:
    ssot = json.loads(SSOT.read_text(encoding="utf-8"))
    claims = json.loads(CLAIMS.read_text(encoding="utf-8"))
    assert ssot["status"] == "READY_FOR_PAPER_A_SCIENCE_FREEZE"
    assert claims["status"] == ssot["status"]
    assert [item["claim_id"] for item in claims["claims"]] == [f"C{i}" for i in range(1, 11)]
    source_data = {}
    for experiment, source in ssot["canonical_sources"].items():
        path = ROOT / source["path"]
        assert path.is_file(), f"missing canonical source for {experiment}: {path}"
        assert sha256(path) == source["sha256"], f"canonical hash mismatch for {experiment}"
        source_data[source["path"]] = json.loads(path.read_text(encoding="utf-8"))
    check_numeric_nodes(ssot, source_data)

    expected = {
        "EXP-023": "f30591ad942e82a322e594695ce1d5023586261fd7b8bccaa208b0d46f388000",
        "EXP-024": "50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69",
        "EXP-025": "bbac2f03b24bdf2ec93485c201d3c0cf50588ed51659e607bb97b231181765a9",
        "EXP-026": "9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551",
        "EXP-027": "1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d",
    }
    assert {k: v["sha256"] for k, v in ssot["canonical_sources"].items() if k in expected} == expected
    profiles = ssot["core_profiles"]
    assert {name: profile["distance_related_degradation"]["support"] for name, profile in profiles.items()} == {
        "Qwen3-1.7B": "POSITIVE_SUPPORTED",
        "OLMo-2-1B": "POSITIVE_SUPPORTED",
        "Meta-Llama-3.2-1B-Instruct": "POSITIVE_SUPPORTED",
    }
    assert profiles["Qwen3-1.7B"]["sdi"]["classification"] == "TARGET_DOMINANT"
    assert profiles["OLMo-2-1B"]["sdi"]["classification"] == "SOURCE_DOMINANT"
    assert profiles["Meta-Llama-3.2-1B-Instruct"]["sdi"]["classification"] == "TARGET_DOMINANT"
    assert profiles["Qwen3-1.7B"]["restricted_low_d_recovery"]["support"] == "NOT_SUPPORTED"
    assert profiles["OLMo-2-1B"]["restricted_low_d_recovery"]["support"] == "SUPPORTED"
    assert profiles["Meta-Llama-3.2-1B-Instruct"]["restricted_low_d_recovery"]["support"] == "SUPPORTED"
    assert ssot["limitations"]["exp021_status"] == "ENGINEERING_ONLY"
    assert ssot["directionality"]["status"] == "CLOSED_NO_FURTHER_MATRIX_MINING"
    assert ssot["limitations"]["cross_task_status"] == "NOT_ESTABLISHED"
    print("PAPER_A_CANONICAL_REGISTER_VALIDATION_PASS")
    print("PAPER_A_ASSET_REGISTER_COMPLETE = true")
    print("PAPER_A_CLAIM_REGISTER_COMPLETE = true")
    print("PAPER_A_RESULT_SSOT_COMPLETE = true")


if __name__ == "__main__":
    main()
