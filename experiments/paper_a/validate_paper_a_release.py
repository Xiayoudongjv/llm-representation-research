"""Fail-closed release validator for the frozen Paper A science package.

This validator checks provenance, manuscript-facing asset integrity, and the
claim/interpretation boundaries.  It does not run a model or compute a new
statistic.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SSOT_PATH = ROOT / "experiments/paper_a/canonical/paper_a_scientific_results.json"
CLAIMS_PATH = ROOT / "experiments/paper_a/canonical/paper_a_claim_register.json"
ASSET_ROOT = ROOT / "experiments/paper_a/paper_assets"

EXPECTED_MODELS = ["Qwen3-1.7B", "OLMo-2-1B", "Meta-Llama-3.2-1B-Instruct"]
EXPECTED_DATA = {
    "data/figure_01_framework_spec.json",
    "data/figure_02_profile_data.json",
    "data/figure_03_matrix_data.json",
    "data/figure_04_directionality_data.json",
    "data/figure_05_heterogeneity_data.json",
}
EXPECTED_TABLES = {
    "tables/table_01_model_profile.json",
    "tables/table_02_claim_summary.json",
    "tables/table_s1_registered_negative_heterogeneity.json",
    "tables/table_s2_directionality_descriptives.json",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_numeric_node(node: Any, location: str) -> None:
    require(isinstance(node, dict), f"missing numeric node at {location}")
    require(isinstance(node.get("value"), (int, float)) and not isinstance(node["value"], bool), location)
    provenance = node.get("provenance")
    require(isinstance(provenance, dict), f"missing provenance at {location}")
    require(
        set(provenance) == {"experiment", "canonical_path", "canonical_sha256", "field_path"},
        f"incomplete provenance at {location}",
    )


def check_profile(profile: dict[str, Any], model: str) -> None:
    distance = profile["distance_related_degradation"]
    require(distance["support"] in {"POSITIVE_SUPPORTED", "NOT_SUPPORTED"}, f"distance class: {model}")
    require_numeric_node(distance["statistic"], f"{model}.distance.statistic")
    require_numeric_node(distance["confidence_interval"]["lower"], f"{model}.distance.ci.lower")
    require_numeric_node(distance["confidence_interval"]["upper"], f"{model}.distance.ci.upper")

    sdi = profile["sdi"]
    require(sdi["classification"] in {"SOURCE_DOMINANT", "TARGET_DOMINANT", "BALANCED"}, f"SDI class: {model}")
    require_numeric_node(sdi["statistic"], f"{model}.sdi.statistic")
    require_numeric_node(sdi["confidence_interval"]["lower"], f"{model}.sdi.ci.lower")
    require_numeric_node(sdi["confidence_interval"]["upper"], f"{model}.sdi.ci.upper")

    recovery = profile["restricted_low_d_recovery"]
    require(recovery["support"] in {"SUPPORTED", "NOT_SUPPORTED"}, f"LOW-D class: {model}")
    require_numeric_node(recovery["mean_recovery"], f"{model}.low_d.mean")
    require_numeric_node(recovery["confidence_interval"]["lower"], f"{model}.low_d.ci.lower")
    require_numeric_node(recovery["confidence_interval"]["upper"], f"{model}.low_d.ci.upper")


def check_claim_boundaries(ssot: dict[str, Any], claims: dict[str, Any]) -> None:
    require([claim["claim_id"] for claim in claims["claims"]] == [f"C{i}" for i in range(1, 11)], "claim IDs")
    for claim in claims["claims"]:
        evidence = claim.get("primary_evidence", []) + claim.get("secondary_evidence", [])
        require("EXP-020A" not in evidence, "EXP-020A entered compatibility evidence")
    by_id = {claim["claim_id"]: claim for claim in claims["claims"]}
    require("operational" in by_id["C3"]["allowed_wording"].lower(), "C3 lacks operational qualification")
    require("statistically independent" in by_id["C3"]["prohibited_wording"], "C3 independence ceiling")
    require("three tested models" in by_id["C5"]["allowed_wording"], "C5 model scope")
    require("all architectures" in by_id["C5"]["prohibited_wording"], "C5 architecture ceiling")
    require(by_id["C8"]["confirmatory_or_exploratory"] == "EXPLORATORY", "C8 exploratory status")
    require("universal" in by_id["C8"]["prohibited_wording"], "C8 universal ceiling")
    require(by_id["C9"]["evidence_status"] == "NOT_ESTABLISHED", "C9 cross-task boundary")
    require(by_id["C10"]["evidence_status"] == "NOT_ESTABLISHED", "C10 construct boundary")
    limits = ssot["limitations"]
    require(limits["cross_task_status"] == "NOT_ESTABLISHED", "cross-task status")
    require(limits["exp021_status"] == "ENGINEERING_ONLY", "EXP-021 boundary")
    require(limits["exp020a_boundary"].startswith("ENGINEERING_ONLY"), "EXP-020A boundary")
    require(limits["cka_status"].startswith("NO_GO"), "CKA boundary")
    require(limits["svcca_status"] == "DO_NOT_ADD", "SVCCA boundary")
    require(limits["ext_b_status"] == "TERMINATED_PRE_MODEL_INFERENCE_AT_FROZEN_DATASET_GATE", "EXT-B boundary")
    require(ssot["directionality"]["status"] == "CLOSED_NO_FURTHER_MATRIX_MINING", "directionality closure")
    require(ssot["directionality"]["inference_class"] == "POST_HOC_EXPLORATORY_DESCRIPTIVE", "directionality inference class")
    require(ssot["future_candidates"]["fourth_model"] == "FUTURE_CANDIDATE_LAB_RESOURCE_DEPENDENT", "fourth-model policy")


def validate(output_dir: Path = ASSET_ROOT) -> dict[str, Any]:
    ssot = load(SSOT_PATH)
    claims = load(CLAIMS_PATH)
    require(ssot["status"] == "READY_FOR_PAPER_A_SCIENCE_FREEZE", "SSOT status")
    require(claims["status"] == ssot["status"], "claim/SSOT status")

    source_hashes = {}
    for source in ssot["canonical_sources"].values():
        path = ROOT / source["path"]
        require(path.is_file(), f"missing canonical source: {path}")
        require(sha256(path) == source["sha256"], f"canonical hash mismatch: {path}")
        source_hashes[source["path"]] = source["sha256"]

    check_claim_boundaries(ssot, claims)
    manifest = load(output_dir / "manifests/paper_asset_manifest.json")
    require(manifest["canonical_ssot"]["sha256"] == sha256(SSOT_PATH), "manifest SSOT hash")
    require(manifest["claim_register"]["sha256"] == sha256(CLAIMS_PATH), "manifest claim hash")
    require(manifest["scientific_content_deterministic"] is True, "scientific determinism flag")
    require(manifest["rendered_file_bytes_deterministic"] is True, "render determinism flag")
    require(set(manifest["figure_ids"]) == {f"FIGURE-0{i}" for i in range(1, 6)}, "figure inventory")
    require(set(manifest["table_ids"]) == {"TABLE-01", "TABLE-02", "TABLE-S1", "TABLE-S2"}, "table inventory")
    for item in manifest["output_files"]:
        path = output_dir / item["path"]
        require(path.is_file(), f"missing asset: {path}")
        require(sha256(path) == item["sha256"], f"asset hash mismatch: {path}")

    profile_data = load(output_dir / "data/figure_02_profile_data.json")
    require(profile_data["model_order"] == EXPECTED_MODELS, "profile model order")
    require(profile_data["profiles"] == ssot["core_profiles"], "profile data differs from SSOT")
    for model in EXPECTED_MODELS:
        check_profile(profile_data["profiles"][model], model)

    table_profile = load(output_dir / "tables/table_01_model_profile.json")
    require([row["model"] for row in table_profile["rows"]] == EXPECTED_MODELS, "Table 1 model order")
    for row in table_profile["rows"]:
        check_profile(
            {
                "distance_related_degradation": {"support": row["distance_classification"], "statistic": row["distance_statistic"], "confidence_interval": row["distance_ci"]},
                "sdi": {"classification": row["sdi_classification"], "statistic": row["sdi"], "confidence_interval": row["sdi_ci"]},
                "restricted_low_d_recovery": {"support": row["low_d_classification"], "mean_recovery": row["low_d_recovery"], "confidence_interval": row["low_d_ci"]},
            },
            row["model"],
        )

    directionality = load(output_dir / "data/figure_04_directionality_data.json")
    require(directionality["status_label"] == "POST-HOC EXPLORATORY", "directionality label")
    require(directionality["values"] == ssot["directionality"]["models"], "directionality values")
    require(directionality["presentation_transformations"]["new_inference"] is False, "directionality new inference")
    facts = (output_dir / "facts/figure_02_model_profiles.md").read_text(encoding="utf-8")
    require("three tested models" in facts, "profile fact-sheet scope")
    require("no architecture causality" in facts, "profile fact-sheet architecture ceiling")

    require("EXP-021" not in " ".join(manifest["figure_ids"] + manifest["table_ids"]), "engineering asset in manifest")
    require("EXP-020A" not in json.dumps(profile_data), "EXP-020A in profile data")
    return {
        "canonical_sources": len(source_hashes),
        "profile_models": len(EXPECTED_MODELS),
        "output_files": len(manifest["output_files"]),
        "figures": len(manifest["figure_ids"]),
        "tables": len(manifest["table_ids"]),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=ASSET_ROOT)
    args = parser.parse_args()
    summary = validate(args.output_dir.resolve())
    print("PAPER_A_RELEASE_VALID = true")
    print("PAPER_A_CONTINUOUS_MAGNITUDE_HARDENING_PASS = true")
    print("PAPER_A_CONSTRUCT_VALIDITY_HARDENING_PASS = true")
    print("PAPER_A_RECOVERABILITY_CLAIM_HARDENING_PASS = true")
    print("PAPER_A_MULTI_AXIS_CLAIM_HARDENING_PASS = true")
    print("PAPER_A_MODEL_SCOPE_HARDENING_PASS = true")
    print("PAPER_A_DIRECTIONALITY_HARDENING_PASS = true")
    print("PAPER_A_EXTERNAL_VALIDITY_BOUNDARY_PASS = true")
    print(f"PAPER_A_RELEASE_ASSET_COUNT = {summary['output_files']}")


if __name__ == "__main__":
    main()
