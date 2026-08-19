#!/usr/bin/env python3
"""EXP-026 frozen design validator.

This validator is read-only and checks the frozen EXP-026 design authority.
It does not run a model, access scientific outcomes, or create scientific
results.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


EXP_DIR = Path(__file__).resolve().parent
ROOT = EXP_DIR.parents[1]
CONFIG_PATH = EXP_DIR / "exp026_frozen_config.json"

EXPECTED_FREEZE_COMMIT = "6dfccb10f5b907667f621ae307df9f3b0893e46e"
EXPECTED_MODELS = {
    "Q": {
        "model_id": "Qwen/Qwen3-1.7B",
        "model_revision": "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e",
        "num_hidden_layers": 28,
        "hidden_size": 2048,
        "eligible_count": 28,
    },
    "O": {
        "model_id": "allenai/OLMo-2-0425-1B-Instruct",
        "model_revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
        "num_hidden_layers": 16,
        "hidden_size": 2048,
        "eligible_count": 16,
    },
}
EXPECTED_DATASET_HASH = "46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404"
EXPECTED_PANEL_HASH = "a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954"
EXPECTED_SCHEMA_HASH = "e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec"
EXPECTED_MANIFEST_HASH = "1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59"
EXPECTED_PREREG_HASH = "55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810"
EXPECTED_CLASSES = ["logic", "causality", "analogy", "definition"]
EXPECTED_CONDITIONS = [
    "c01_lexical_relex",
    "c02_syntactic_restructure",
    "c03_controlled_compression",
    "c04_controlled_elaboration",
    "c05_relation_explicit",
    "c06_relation_implicit",
    "c07_register_formal",
    "c08_register_informal",
    "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
]
EXPECTED_ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}
EXPECTED_SUMMARIES = {
    "primary_1": "DISTANCE_ASSOCIATION",
    "primary_2": "SOURCE_DOMINANCE_INDEX",
    "secondary_confirmatory": "LOW_D_RECOVERY",
    "localization_status": "DESCRIPTIVE",
    "cross_model_matrix_similarity_status": "DESCRIPTIVE",
}
FORBIDDEN_CLAIM_TERMS = [
    "architecture causality",
    "family causality",
    "universal latent geometry",
    "functional binding",
    "invariant preservation",
    "behavioral causality",
]
NO_RUNNER_PATHS = [
    EXP_DIR / "run_exp026.py",
    EXP_DIR / "results",
    EXP_DIR / "exp026_results.json",
    EXP_DIR / "exp026_formal_result.json",
    EXP_DIR / "exp026_formal_run_authorization.json",
    EXP_DIR / "formal_authorization",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def fail(message: str) -> None:
    print(f"FAIL: {message}")
    raise SystemExit(1)


def main() -> int:
    if not CONFIG_PATH.exists():
        fail("missing exp026_frozen_config.json")

    config = read_json(CONFIG_PATH)

    if config.get("experiment") != "EXP-026":
        fail("config experiment is not EXP-026")
    if config.get("design_status") != "FROZEN_DESIGN_NOT_RUN":
        fail("design_status is not FROZEN_DESIGN_NOT_RUN")
    if config.get("design_selected") != "FULL_SOURCE_TARGET_COMPATIBILITY_MATRIX":
        fail("design_selected mismatch")
    if config.get("model_scope") != "TWO_MODEL_COMPARATIVE_PROFILE":
        fail("model_scope mismatch")
    if config.get("freeze_commit") != EXPECTED_FREEZE_COMMIT:
        fail("freeze_commit mismatch")
    if config.get("specification_gaps") != 0:
        fail("specification_gaps is not zero")

    models = config.get("models")
    if not isinstance(models, dict) or set(models) != {"Q", "O"}:
        fail("models must be exactly Q and O")
    for key, expected in EXPECTED_MODELS.items():
        model = models.get(key)
        if not isinstance(model, dict):
            fail(f"missing model {key}")
        for field in ("model_id", "model_revision", "num_hidden_layers", "hidden_size"):
            if model.get(field) != expected[field]:
                fail(f"model {key} {field} mismatch")
        blocks = model.get("eligible_blocks")
        if not isinstance(blocks, dict):
            fail(f"model {key} eligible_blocks missing")
        if blocks.get("count") != expected["eligible_count"]:
            fail(f"model {key} eligible block count mismatch")
        if blocks.get("first_index") != 0:
            fail(f"model {key} first block index mismatch")
        if blocks.get("last_index") != expected["num_hidden_layers"] - 1:
            fail(f"model {key} last block index mismatch")

    if config.get("llama_included") is not False:
        fail("llama_included must be false")
    if config.get("fallback_model") != "NONE":
        fail("fallback_model must be NONE")
    if config.get("dataset_reused") is not True:
        fail("dataset_reused must be true")

    inherited = config.get("inherited_authorities", {})
    dataset_path = ROOT / inherited.get("dataset_path", "")
    panel_path = ROOT / inherited.get("condition_panel_path", "")
    schema_path = ROOT / inherited.get("data_schema_path", "")
    manifest_path = ROOT / inherited.get("frozen_manifest_path", "")
    exp024_prereg_path = ROOT / inherited.get("exp024_preregistration_path", "")
    if not dataset_path.exists():
        fail("inherited dataset path missing")
    if not panel_path.exists():
        fail("inherited panel path missing")
    if not schema_path.exists():
        fail("inherited data schema path missing")
    if not manifest_path.exists():
        fail("inherited manifest path missing")
    if not exp024_prereg_path.exists():
        fail("inherited EXP-024 preregistration path missing")
    if sha256_file(dataset_path) != EXPECTED_DATASET_HASH:
        fail("inherited dataset hash mismatch")
    if inherited.get("dataset_sha256") != EXPECTED_DATASET_HASH:
        fail("config dataset hash mismatch")
    if sha256_file(panel_path) != EXPECTED_PANEL_HASH:
        fail("inherited panel hash mismatch")
    if inherited.get("condition_panel_sha256") != EXPECTED_PANEL_HASH:
        fail("config panel hash mismatch")
    if sha256_file(schema_path) != EXPECTED_SCHEMA_HASH:
        fail("inherited data schema hash mismatch")
    if inherited.get("data_schema_sha256") != EXPECTED_SCHEMA_HASH:
        fail("config data schema hash mismatch")
    if sha256_file(manifest_path) != EXPECTED_MANIFEST_HASH:
        fail("inherited manifest hash mismatch")
    if inherited.get("frozen_manifest_sha256") != EXPECTED_MANIFEST_HASH:
        fail("config manifest hash mismatch")
    if sha256_file(exp024_prereg_path) != EXPECTED_PREREG_HASH:
        fail("inherited EXP-024 preregistration hash mismatch")
    if inherited.get("exp024_preregistration_sha256") != EXPECTED_PREREG_HASH:
        fail("config EXP-024 preregistration hash mismatch")

    panel = config.get("panel", {})
    if panel.get("n_conditions") != 10:
        fail("panel n_conditions mismatch")
    if panel.get("semantic_classes") != EXPECTED_CLASSES:
        fail("panel semantic classes mismatch")
    if panel.get("condition_order") != EXPECTED_CONDITIONS:
        fail("panel condition order mismatch")
    if panel.get("allocation") != EXPECTED_ALLOCATION:
        fail("panel allocation mismatch")

    firewall = config.get("firewall", {})
    if "source_layer_classifier_parameters" not in firewall.get("fit_roles", []):
        fail("FIT firewall missing classifier role")
    if "pairwise_fit_only_recalibration_parameters" not in firewall.get("fit_roles", []):
        fail("FIT firewall missing recalibration role")
    if "source_layer_technical_eligibility" not in firewall.get("diagnostic_roles", []):
        fail("DIAGNOSTIC firewall missing eligibility role")
    if "confirmatory_compatibility_and_recovery_summaries" not in firewall.get("eval_roles", []):
        fail("EVAL firewall missing confirmatory role")
    if "source_layers" not in firewall.get("eval_forbidden_selection", []):
        fail("EVAL forbidden selection missing source_layers")

    layer = config.get("layer_carrier", {})
    if layer.get("normalized_depth_formula") != "layer_index/(num_layers-1)":
        fail("normalized depth formula mismatch")
    if layer.get("full_layer_extraction_feasible") is not True:
        fail("full layer extraction feasibility must be true")

    metrics = config.get("metrics", {})
    if metrics.get("source_technical_floor") != 0.75:
        fail("source technical floor mismatch")
    if metrics.get("c0_definition") is None:
        fail("C0 definition missing")
    if metrics.get("d_definition") != "Cself-C0":
        fail("D definition mismatch")
    if metrics.get("primary_recalibration") != "A_mu_sigma":
        fail("primary recalibration mismatch")
    if metrics.get("r_definition") != "Ccal-C0":
        fail("R definition mismatch")
    if metrics.get("source_coverage_min_fraction") != 0.5:
        fail("source coverage fraction mismatch")
    if metrics.get("source_coverage_min_normalized_depth_span") != 0.5:
        fail("source coverage span mismatch")

    summaries = config.get("summaries", {})
    for key, value in EXPECTED_SUMMARIES.items():
        if summaries.get(key) != value:
            fail(f"summary {key} mismatch")

    stats = config.get("statistics", {})
    if stats.get("statistical_unit") != "source_family_cluster":
        fail("statistical unit mismatch")
    if stats.get("resampling_unit") != "source_family":
        fail("resampling unit mismatch")
    if stats.get("bootstrap_design") != "condition_stratified_source_family_cluster_bootstrap":
        fail("bootstrap design mismatch")
    if stats.get("bootstrap_replicates") != 5000:
        fail("bootstrap replicates mismatch")
    if stats.get("seed") != 20260819:
        fail("bootstrap seed mismatch")
    if stats.get("sdi_variance_convention") != "population_variance_ddof_0":
        fail("SDI variance convention mismatch")
    if stats.get("low_d_recovery_effective_n_zero") != "NOT_EVALUABLE":
        fail("LOW_D_RECOVERY n=0 semantics mismatch")

    routing = config.get("routing", {})
    if routing.get("frozen") is not True:
        fail("routing rules must be frozen")
    if routing.get("conflict_resolution") != "P3 > P1 > P2 > P4 > P5":
        fail("routing conflict resolution mismatch")

    claim = config.get("claim_ceiling", "")
    if "reproducible differences" not in claim or "FIT-only featurewise recalibratability" not in claim:
        fail("claim ceiling mismatch")
    if config.get("model_dependent_language_enforced") is not True:
        fail("model-dependent language must be enforced")
    if config.get("family_causal_claim_prohibited") is not True:
        fail("family causal claim must be prohibited")
    if config.get("llama_future_gate_defined") is not True:
        fail("Llama future gate must be defined")

    design_files = config.get("design_files", {})
    for key in (
        "preregistration_path",
        "model_selection_path",
        "layer_carrier_mapping_path",
        "matrix_metric_specification_path",
        "routing_rules_path",
    ):
        path_key = key.replace("_path", "_sha256")
        path = design_files.get(key)
        expected_hash = design_files.get(path_key)
        if not path or not expected_hash:
            fail(f"design file path/hash missing for {key}")
        full_path = ROOT / path
        if not full_path.exists():
            fail(f"design file missing: {path}")
        actual_hash = sha256_file(full_path)
        if actual_hash != expected_hash:
            fail(f"design file hash mismatch: {path}")

    for path in NO_RUNNER_PATHS:
        if path.exists():
            fail(f"forbidden runner/result/authorization path exists: {path}")
    for child in EXP_DIR.glob("*formal_run_authorization*.json"):
        fail(f"forbidden authorization file exists: {child.name}")
    for child in EXP_DIR.glob("*results*.json"):
        fail(f"forbidden result file exists: {child.name}")

    flags = config.get("flags", {})
    for flag in (
        "runner_created",
        "gpu_run_executed",
        "formal_authorization_created",
        "scientific_result_created",
    ):
        if flags.get(flag) is not False:
            fail(f"flag {flag} must be false")

    if config.get("next_task") != "101C_EXP026_RUNNER_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION":
        fail("next_task mismatch")

    print("EXP026_DESIGN_VALIDATION = PASS")
    print("EXP026_SPECIFICATION_GAPS = 0")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:  # pragma: no cover
        print(f"FAIL: validator exception: {exc}")
        sys.exit(1)
