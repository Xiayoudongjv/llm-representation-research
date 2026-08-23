"""PA-EXT-A V3 pipeline synthetic-qualification tests.

Synthetic/static only. These tests never load a language model, never create a
real semantic asset bank, panel, result, or authorization.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "experiments" / "paper_a_ext_a"
for path in (str(ROOT), str(EXP_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import pa_ext_a_v3_pipeline as p
import validate_pa_ext_a_v3_pipeline as v


@pytest.fixture(scope="module")
def design() -> dict[str, Any]:
    return p.load_frozen_design()


@pytest.fixture(scope="module")
def full_panel(design: dict[str, Any]) -> dict[str, Any]:
    return p.compose_panel(p.build_synthetic_asset_bank(design), design, mode="synthetic")


def _copy(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, sort_keys=True))


def test_v3_design_hash_mismatch_rejected(tmp_path: Path):
    design = p.read_json(p.V3_DESIGN_PATH)
    path = tmp_path / "v3_design_mutated.json"
    path.write_text(json.dumps(design, indent=2), encoding="utf-8")
    with pytest.raises(p.PaperAExtAPipelineError, match="V3_DESIGN_SHA256_MISMATCH"):
        p.load_frozen_design(path, expected_sha256=p.EXPECTED_V3_SHA256)


def test_unknown_asset_rejected(design: dict[str, Any]):
    asset = p.build_synthetic_asset_bank(design)[0]
    asset["asset_type"] = "UNKNOWN_ASSET_TYPE"
    errors = p.validate_asset_bank([asset], design, mode="synthetic")
    assert any("asset_unknown_type" in error for error in errors)


def test_invalid_relation_asset_combination_rejected(design: dict[str, Any]):
    asset = p.build_synthetic_asset_bank(design)[0]
    asset["allowed_relations"] = [p.RELATION_BY_TASK["exta_tf_temporal"]]
    errors = p.validate_asset_bank([asset], design, mode="synthetic")
    assert any("asset_relation_task_incompatible" in error for error in errors)


def test_deterministic_repeated_generation_identical(design: dict[str, Any]):
    panel_a = p.compose_panel(p.build_synthetic_asset_bank(design), design, mode="synthetic")
    panel_b = p.compose_panel(p.build_synthetic_asset_bank(design), design, mode="synthetic")
    assert p.canonical_json_bytes(panel_a) == p.canonical_json_bytes(panel_b)


def test_exact_880_1760_structure(full_panel: dict[str, Any]):
    families = {item["source_family_id"] for item in full_panel["items"]}
    assert len(families) == 880
    assert len(full_panel["items"]) == 1760
    assert sum(1 for item in full_panel["items"] if item["partition"] == "FIT") == 480
    assert sum(1 for item in full_panel["items"] if item["partition"] == "DIAG") == 640
    assert sum(1 for item in full_panel["items"] if item["partition"] == "EVAL") == 640


def test_partition_isolation(full_panel: dict[str, Any]):
    by_family: dict[str, set[str]] = {}
    for item in full_panel["items"]:
        by_family.setdefault(item["source_family_id"], set()).add(item["partition"])
    assert all(len(partitions) == 1 for partitions in by_family.values())
    assert sum(1 for partitions in by_family.values() if next(iter(partitions)) == "FIT") == 240
    assert sum(1 for partitions in by_family.values() if next(iter(partitions)) == "DIAG") == 320
    assert sum(1 for partitions in by_family.values() if next(iter(partitions)) == "EVAL") == 320


def test_deterministic_ids(full_panel: dict[str, Any]):
    for item in full_panel["items"]:
        assert item["source_family_id"].startswith("exta_sf_")
        assert item["item_id"] == f"{item['source_family_id']}_{item['record_role']}"
        assert item["source_item_id"] == f"{item['source_family_id']}_source"
        assert item["transformation_id"] == f"exta_xform_{item['condition_id']}"
        assert item["transformation_family_id"] == f"{item['source_family_id']}_xform"
    assert len({item["item_id"] for item in full_panel["items"]}) == 1760


def test_free_form_final_text_rejected(full_panel: dict[str, Any], design: dict[str, Any]):
    panel = _copy(full_panel)
    panel["items"][0]["raw_text"] = "arbitrary free-form text injected after rendering"
    errors = v.validate_panel(panel, design, mode="synthetic")
    assert any("free_form" in error for error in errors)


def test_runtime_scientific_override_rejected(full_panel: dict[str, Any], design: dict[str, Any]):
    panel = _copy(full_panel)
    panel["synthetic"] = False
    panel["scientific_use_allowed"] = True
    panel["formal_panel_allowed"] = True
    errors = v.validate_panel(panel, design, mode="synthetic")
    assert any("panel_synthetic_flag" in error or "panel_scientific_use_allowed" in error for error in errors)


def test_historical_collision_rejected(full_panel: dict[str, Any], design: dict[str, Any]):
    item = full_panel["items"][0]
    exclusion = {
        "schema_version": p.PANEL_SCHEMA_VERSION,
        "classification": p.HISTORICAL_INDEX_CLASSIFICATION,
        "old_dataset_path": "test-only",
        "normalized_text_hashes": [p.normalized_text_hash(item["raw_text"])],
        "source_family_ids": [item["source_family_id"]],
        "source_item_ids": [item["source_item_id"]],
        "base_content_ids": [],
        "record_count": 1,
    }
    errors = v.validate_panel(full_panel, design, mode="synthetic", exclusion_index=exclusion)
    assert any("prior_panel_text_collision" in error or "prior_source_family_collision" in error for error in errors)


def test_synthetic_panel_rejected_by_production_mode(full_panel: dict[str, Any], design: dict[str, Any]):
    errors = v.validate_panel(full_panel, design, mode="production")
    assert any("panel_classification_not_formal" in error or "panel_synthetic_flag" in error for error in errors)


def test_json_serialization_safe(full_panel: dict[str, Any]):
    text = json.dumps(full_panel, sort_keys=True)
    decoded = json.loads(text)
    assert decoded["items"][0]["item_id"] == full_panel["items"][0]["item_id"]


def test_existing_validators_still_pass():
    scripts = [
        EXP_DIR / "validate_paper_a_ext_a_preregistration.py",
        EXP_DIR / "validate_paper_a_ext_a_content_design.py",
        EXP_DIR / "validate_paper_a_ext_a_content_design_v3.py",
    ]
    for script in scripts:
        result = subprocess.run(
            [sys.executable, "-B", str(script)],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_no_real_scientific_asset_or_panel_created():
    forbidden = [
        EXP_DIR / "real_semantic_asset_bank.json",
        EXP_DIR / "semantic_asset_bank.json",
        EXP_DIR / "real_source_bank.json",
        EXP_DIR / "source_bank.json",
        EXP_DIR / "real_panel.json",
        EXP_DIR / "candidate_items.json",
        EXP_DIR / "fit_data.json",
        EXP_DIR / "diag_data.json",
        EXP_DIR / "eval_data.json",
        EXP_DIR / "results.json",
        EXP_DIR / "formal_run_authorization.json",
    ]
    assert not any(path.exists() for path in forbidden)


def test_no_model_inference_result_auth_created():
    source = Path(p.__file__).read_text(encoding="utf-8")
    assert "import torch" not in source
    assert "from torch" not in source
    qualification = p.run_synthetic_qualification(publish=False)
    assert qualification["real_data_flags"]["REAL_EXT_A_MODEL_INFERENCE_PERFORMED"] is False
    assert qualification["real_data_flags"]["REAL_EXT_A_RESULTS_CREATED"] is False
    assert qualification["real_data_flags"]["REAL_EXT_A_AUTHORIZATION_CREATED"] is False
