from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.paper_a import generate_paper_assets as generator
from experiments.paper_a import validate_paper_a_paper_assets as validator


def test_generator_consumes_ssot_and_profile_matches(tmp_path: Path) -> None:
    generator.generate(tmp_path)
    profile = json.loads((tmp_path / "data/figure_02_profile_data.json").read_text(encoding="utf-8"))
    ssot = json.loads(generator.SSOT_PATH.read_text(encoding="utf-8"))
    assert profile["profiles"] == ssot["core_profiles"]


def test_matrix_orientation_and_all_metrics(tmp_path: Path) -> None:
    generator.generate(tmp_path)
    data = json.loads((tmp_path / "data/figure_03_matrix_data.json").read_text(encoding="utf-8"))
    assert data["axis"] == {"row": "source readout/scaler layer", "column": "target representation layer"}
    assert data["presentation_transformations"]["matrix_transposed_for_display"] is False
    assert set(data["metric_order"]) == {"c0_eval", "d_eval", "r_eval"}


def test_directionality_is_archived_exploratory(tmp_path: Path) -> None:
    generator.generate(tmp_path)
    data = json.loads((tmp_path / "data/figure_04_directionality_data.json").read_text(encoding="utf-8"))
    assert data["status_label"] == "POST-HOC EXPLORATORY"
    assert data["presentation_transformations"]["new_inference"] is False


def test_boundaries_exclude_engineering_assets(tmp_path: Path) -> None:
    generator.generate(tmp_path)
    validator.main.__module__  # ensure validator is importable without side effects
    ssot = json.loads(generator.SSOT_PATH.read_text(encoding="utf-8"))
    assert ssot["limitations"]["exp021_status"] == "ENGINEERING_ONLY"
    assert ssot["limitations"]["exp020a_boundary"].startswith("ENGINEERING_ONLY")
    assert ssot["limitations"]["ext_b_status"] == "TERMINATED_PRE_MODEL_INFERENCE_AT_FROZEN_DATASET_GATE"


def test_all_generated_scientific_exports_have_source_metadata(tmp_path: Path) -> None:
    generator.generate(tmp_path)
    for path in (tmp_path / "data").glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        assert "figure_id" in data
    manifest = json.loads((tmp_path / "manifests/paper_asset_manifest.json").read_text(encoding="utf-8"))
    assert manifest["canonical_ssot"]["sha256"]


def test_generator_fails_on_canonical_hash_mismatch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    altered = tmp_path / "altered_ssot.json"
    data = json.loads(generator.SSOT_PATH.read_text(encoding="utf-8"))
    data["canonical_sources"]["EXP-026"]["sha256"] = "0" * 64
    altered.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr(generator, "SSOT_PATH", altered)
    with pytest.raises(AssertionError):
        generator.generate(tmp_path / "out")
