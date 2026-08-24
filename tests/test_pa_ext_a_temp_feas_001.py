"""Focused offline guards for PA-EXT-A-TEMP-FEAS-001."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_001"
HELPER = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_001.py"


def _read(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def _content_hash(value: dict, field: str) -> str:
    body = dict(value)
    body.pop(field, None)
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_exact_3550_pool_and_manifest_repeatability() -> None:
    manifest = _read("date_valid_pool_manifest.json")
    identities = [row["canonical_identity"] for row in manifest["records"]]
    assert manifest["total_count"] == 3550
    assert len(identities) == 3550
    assert len(set(identities)) == 3550
    assert manifest["duplicate_identity_check"] is True
    assert manifest["manifest_sha256"] == _content_hash(manifest, "manifest_sha256")


def test_deterministic_design_confirmation_split_has_no_overlap() -> None:
    design = _read("source_design_manifest.json")
    confirmation = _read("source_confirmation_manifest.json")
    design_ids = {row["canonical_identity"] for row in design["records"]}
    confirmation_ids = {row["canonical_identity"] for row in confirmation["records"]}
    assert design["split"] == "SOURCE_DESIGN"
    assert confirmation["split"] == "SOURCE_CONFIRMATION"
    assert design["total_count"] == 710
    assert confirmation["total_count"] == 2840
    assert not design_ids & confirmation_ids
    assert len(design_ids | confirmation_ids) == 3550
    assert design["manifest_sha256"] == _content_hash(design, "manifest_sha256")
    assert confirmation["manifest_sha256"] == _content_hash(confirmation, "manifest_sha256")


def test_confirmation_manifest_is_identity_only() -> None:
    confirmation = _read("source_confirmation_manifest.json")
    forbidden = {
        "english_label",
        "direct_p31_classes",
        "cached_p279_parents_by_p31_class",
        "direct_Q1190554_membership",
        "cached_ancestry_to_Q1190554",
        "provisional_ontology_category",
    }
    assert confirmation["identity_only"] is True
    assert confirmation["semantic_fields_exposed"] is False
    assert all(set(row) == {"canonical_identity", "identity_sha256", "split"} for row in confirmation["records"])
    assert not any(forbidden & set(row) for row in confirmation["records"])


def test_design_only_audit_and_single_proposal() -> None:
    design = _read("source_design_manifest.json")
    audit = _read("design_ontology_audit.json")
    sample = _read("design_human_review_sample.json")
    proposal = _read("temp_feas_001_proposed_rule.json")
    report = _read("temp_feas_001_report.json")
    assert audit["design_count"] == 710
    assert len(design["records"]) == 710
    assert len(sample["records"]) == 40
    assert all("direct_p31_classes" in row for row in sample["records"])
    assert audit["direct_Q1190554_membership_count"] == 0
    assert proposal["status"] == "PROPOSED_NOT_CONFIRMED"
    assert proposal["proposal_sha256"] == _content_hash(proposal, "proposal_sha256")
    assert report["required_flags"]["PA_EXT_A_PROSPECTIVE_TEMPORAL_RULE_CONFIRMED"] is False


def test_no_network_access_and_no_v8_mutation_surface() -> None:
    source = HELPER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "urlopen" not in source
    assert "import requests" not in source
    assert "urlopen" not in called_names
    assert "RAW_DIR / \"acquisition_checkpoint.json\"" in source
    report = _read("temp_feas_001_report.json")
    assert report["network_accessed"] is False
    assert report["v8_lineage_modified"] is False
    assert report["formal_panel_accessed"] is False
    assert report["formal_inference_performed"] is False
    assert report["scientific_outcome_created"] is False


def test_proposal_freezes_lineage_before_confirmation() -> None:
    proposal = _read("temp_feas_001_proposed_rule.json")
    assert proposal["design_only"] is True
    assert proposal["confirmation_semantics_accessed"] is False
    assert proposal["target_temporal_families"] == 220
    assert proposal["theoretical_hard_minimum_eligible_events"] == 440
    assert proposal["operational_reserve_target_eligible_events"] == 500
    assert "event-first" in proposal["acquisition_ordering"].lower()
