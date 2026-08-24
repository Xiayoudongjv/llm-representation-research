"""Focused fail-closed tests for TEMP-FEAS-002."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_002"


def _read(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def _hash_without_artifact(value: dict) -> str:
    body = dict(value)
    body.pop("artifact_sha256", None)
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def test_entry_gate_hashes_and_block_status_are_frozen() -> None:
    result = _read("temp_feas_002_confirmation_result.json")
    assert result["artifact_sha256"] == _hash_without_artifact(result)
    assert result["status"] == "TEMP_FEAS_002_BLOCKED_INSUFFICIENT_ONTOLOGY_CLOSURE"
    assert result["proposal_sha256"] == "5ac334a8e788b6c491cf9af375c4926c1db8bda6fd71b53e16ff3dd68b22a9be"
    assert result["confirmation_manifest_sha256"] == "3a278b4602aadc361a998eff0910571daae292255beae536c37249efa09843ec"
    assert result["entry_gate"]["v8_authority_unchanged"] is True
    assert result["entry_gate"]["v8_checkpoint_unchanged"] is True


def test_structural_closure_failure_prevents_confirmation_exposure() -> None:
    result = _read("temp_feas_002_confirmation_result.json")
    assert result["ontology_closure_sufficiency"]["sufficient"] is False
    assert result["confirmation_exposure"]["confirmation_semantic_fields_loaded"] is False
    assert result["confirmation_exposure"]["confirmation_funnel_evaluated"] is False
    assert result["required_flags"]["PA_EXT_A_FINAL_ELIGIBLE_EVENTS"] == "NOT_COMPUTED"
    assert result["required_flags"]["PA_EXT_A_TEMPORAL_FAMILIES_POSSIBLE"] == "NOT_COMPUTED"


def test_funnel_is_fail_closed_and_bottleneck_is_ontology_root() -> None:
    funnel = _read("temp_feas_002_funnel.json")
    assert funnel["artifact_sha256"] == _hash_without_artifact(funnel)
    assert funnel["dominant_bottleneck"] == "ONTOLOGY_ROOT"
    assert all(value == "NOT_COMPUTED" for value in funnel["counts"].values())
    assert funnel["leakage_survival_rate"] == "NOT_COMPUTED"


def test_no_formal_or_network_execution_flags() -> None:
    report = _read("temp_feas_002_report.json")
    assert report["artifact_sha256"] == _hash_without_artifact(report)
    assert report["confirmation_exposure"] is False
    assert report["network_accessed"] is False
    assert report["formal_panel_accessed"] is False
    assert report["formal_inference_performed"] is False
    assert report["v8_lineage_modified"] is False
    assert report["required_flags"]["PA_EXT_A_TEMP_RULE_CONFIRMED"] is False
