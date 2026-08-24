"""Synthetic-only PA-EXT-A-006P engineering qualification tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP_DIR = ROOT / "experiments" / "paper_a_ext_a"
for path in (str(ROOT), str(EXP_DIR), str(EXP_DIR / "engineering")):
    if path not in sys.path:
        sys.path.insert(0, path)

import pa_ext_a_v3_pipeline as pipeline
from pa_ext_a_006p_preflight import (
    MODEL_SPECS,
    SyntheticOutputStore,
    build_synthetic_panel_qualification,
)


@pytest.fixture(scope="module")
def design():
    return pipeline.load_frozen_design()


def test_full_synthetic_panel_counts_and_repeatability():
    result = build_synthetic_panel_qualification()
    assert result["total_families"] == 880
    assert result["total_records"] == 1760
    assert result["task_family_counts"] == {
        "exta_tf_spatial": 220,
        "exta_tf_temporal": 220,
        "exta_tf_quantitative": 220,
        "exta_tf_mereological": 220,
    }
    assert result["partition_family_counts"] == {"FIT": 240, "DIAG": 320, "EVAL": 320}
    assert result["partition_record_counts"] == {"FIT": 480, "DIAG": 640, "EVAL": 640}
    assert result["record_roles_per_family"] == [("realization", "reference")]
    assert result["family_split_isolated"] is True
    assert result["family_ids_unique"] is True
    assert result["record_ids_unique"] is True
    assert result["deterministic_repeatability"] is True
    assert result["build_1_sha256"] == result["build_2_sha256"]


def test_synthetic_fixture_rejected_in_production_mode(design):
    panel = pipeline.compose_panel(
        pipeline.build_synthetic_asset_bank(design), design, mode="synthetic"
    )
    errors = pipeline.validate_asset_bank(
        pipeline.build_synthetic_asset_bank(design), design, mode="production"
    )
    assert any("production_asset_must_not_be_synthetic" in error for error in errors)
    assert panel["formal_panel_allowed"] is False


def test_wrong_family_size_and_duplicate_ids_are_rejected(design):
    assets = pipeline.build_synthetic_asset_bank(design)
    assert len(assets) > 1
    duplicate = json.loads(json.dumps(assets[1]))
    duplicate["asset_id"] = assets[0]["asset_id"]
    errors = pipeline.validate_asset_bank([assets[0], duplicate], design, mode="synthetic")
    assert any("duplicate_id" in error for error in errors)
    with pytest.raises(pipeline.PaperAExtAPipelineError):
        pipeline.compose_panel(assets[:-1], design, mode="synthetic")


def test_missing_provenance_is_rejected(design):
    asset = json.loads(json.dumps(pipeline.build_synthetic_asset_bank(design)[0]))
    asset.pop("provenance")
    errors = pipeline.validate_asset_bank([asset], design, mode="synthetic")
    assert any("missing_provenance" in error for error in errors)


def test_sequential_output_namespaces_and_partial_guard(tmp_path: Path):
    store = SyntheticOutputStore(tmp_path)
    required = [spec["key"] for spec in MODEL_SPECS]
    store.write_model_output("qwen", {"model_key": "qwen", "synthetic": True})
    assert store.is_complete(required) is False
    with pytest.raises(RuntimeError, match="PARTIAL_SYNTHETIC_RUN_NOT_PUBLISHABLE"):
        store.write_completion_manifest(required)
    with pytest.raises(ValueError, match="MODEL_OUTPUT_NAMESPACE_MISMATCH"):
        store.write_model_output("olmo", {"model_key": "qwen"})
    store.write_model_output("olmo", {"model_key": "olmo", "synthetic": True})
    store.write_model_output("llama", {"model_key": "llama", "synthetic": True})
    store.write_completion_manifest(required)
    assert store.is_complete(required) is True
    assert (tmp_path / "qwen" / "synthetic_output.json").exists()
    assert (tmp_path / "olmo" / "synthetic_output.json").exists()
    assert (tmp_path / "llama" / "synthetic_output.json").exists()


def test_no_live_v8_path_is_written_by_synthetic_helpers(tmp_path: Path):
    result = build_synthetic_panel_qualification()
    assert result["synthetic_classification"] == pipeline.SYNTHETIC_PANEL_CLASSIFICATION
    assert not (EXP_DIR / "data" / "raw" / "wikidata_v8" / "pa_ext_a_006p").exists()
    store = SyntheticOutputStore(tmp_path / "isolated")
    store.write_model_output("qwen", {"model_key": "qwen"})
    assert not (EXP_DIR / "data" / "raw" / "wikidata_v8" / "completion_manifest.json").exists()
