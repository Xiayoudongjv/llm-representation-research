"""Validate generated Paper A paper assets against frozen authorities."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = ROOT / "experiments/paper_a/paper_assets"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    output = args.output_dir.resolve()
    ssot_path = ROOT / "experiments/paper_a/canonical/paper_a_scientific_results.json"
    claims_path = ROOT / "experiments/paper_a/canonical/paper_a_claim_register.json"
    ssot = load(ssot_path)
    claims = load(claims_path)
    assert ssot["status"] == "READY_FOR_PAPER_A_SCIENCE_FREEZE"
    assert claims["status"] == ssot["status"]
    manifest = load(output / "manifests/paper_asset_manifest.json")
    assert manifest["canonical_ssot"]["sha256"] == sha256(ssot_path)
    assert manifest["claim_register"]["sha256"] == sha256(claims_path)
    assert manifest["scientific_content_deterministic"] is True
    for item in manifest["output_files"]:
        path = output / item["path"]
        assert path.is_file(), path
        assert sha256(path) == item["sha256"], path

    profile = load(output / "data/figure_02_profile_data.json")
    assert profile["model_order"] == ["Qwen3-1.7B", "OLMo-2-1B", "Meta-Llama-3.2-1B-Instruct"]
    assert profile["profiles"] == ssot["core_profiles"]
    matrices = load(output / "data/figure_03_matrix_data.json")
    assert matrices["presentation_transformations"]["matrix_transposed_for_display"] is False
    for model in matrices["model_order"]:
        for metric in matrices["metric_order"]:
            item = matrices["matrices"][model][metric]
            assert item["shape"][0] == len(item["values"])
            assert item["shape"][1] == len(item["values"][0])
            assert item["source_field_path"]
    directionality = load(output / "data/figure_04_directionality_data.json")
    assert directionality["status_label"] == "POST-HOC EXPLORATORY"
    assert directionality["values"] == ssot["directionality"]["models"]
    heterogeneity = load(output / "data/figure_05_heterogeneity_data.json")
    assert heterogeneity["values"]["EXP-024"] == ssot["registered_negative_results"]["EXP-024_predictor"]
    assert ssot["limitations"]["exp021_status"] == "ENGINEERING_ONLY"
    assert "EXP-021" not in " ".join(manifest["figure_ids"] + manifest["table_ids"])
    assert ssot["limitations"]["exp020a_boundary"].startswith("ENGINEERING_ONLY")
    assert ssot["limitations"]["ext_b_status"] == "TERMINATED_PRE_MODEL_INFERENCE_AT_FROZEN_DATASET_GATE"
    expected_data = {"figure_01_framework_spec.json", "figure_02_profile_data.json", "figure_03_matrix_data.json", "figure_04_directionality_data.json", "figure_05_heterogeneity_data.json"}
    assert expected_data <= {p.name for p in (output / "data").glob("*.json")}
    print("PAPER_A_PAPER_ASSET_VALIDATION_PASS")
    print("PAPER_A_FIGURE_DATA_PROVENANCE_COMPLETE = true")
    print("PAPER_A_TABLE_DATA_PROVENANCE_COMPLETE = true")
    print("PAPER_A_DIRECTIONALITY_EXPLORATORY_LABEL_PRESERVED = true")
    print("PAPER_A_EXT_B_BOUNDARY_PRESERVED = true")


if __name__ == "__main__":
    main()
