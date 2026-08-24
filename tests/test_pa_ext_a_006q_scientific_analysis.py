from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments.paper_a_ext_a.engineering import pa_ext_a_006q_scientific_analysis_preflight as preflight


def test_all_synthetic_component_fixtures_match_expected_profiles() -> None:
    results = preflight.qualify_fixtures()
    assert len(results) == 6
    assert all(value["status"] == "PASS" for value in results.values())
    assert results["CASE_1_TARGET_LOW_D_SUPPORTED"]["organization_label"] == "TARGET_DOMINANT"
    assert results["CASE_3_SOURCE_LOW_D_SUPPORTED"]["organization_label"] == "SOURCE_DOMINANT"
    assert results["CASE_5_NULL"]["distance_status"] == "NOT_EVALUABLE"


def test_source_target_orientation_cannot_be_silently_reversed() -> None:
    target = preflight.synthetic_component_matrices(structure="positive", organization="TARGET", low_d="SUPPORTED")
    source = preflight.synthetic_component_matrices(structure="positive", organization="SOURCE", low_d="SUPPORTED")
    assert preflight.analyze_component_profile(*target)["organization_label"] == "TARGET_DOMINANT"
    assert preflight.analyze_component_profile(*source)["organization_label"] == "SOURCE_DOMINANT"


@pytest.mark.parametrize("route", ["A1", "A2", "A3", "A4", "A5", "A6"])
def test_every_a1_a6_route_is_reachable(route: str) -> None:
    result = preflight.qualify_routes()
    assert result[route]["route"] == route


def test_invalid_route_is_rejected() -> None:
    with pytest.raises(preflight.QualificationError):
        preflight.route_a1_a6({"Qwen": preflight.HISTORICAL_PROFILES["Qwen"]})


def test_input_guards_fail_closed() -> None:
    checks = preflight.qualify_input_guards()
    assert len(checks) == 9
    assert all(value == "PASS" for value in checks.values())


def test_publication_guards_reject_synthetic_partial_and_canonical() -> None:
    checks = preflight.qualify_publication_guards()
    assert checks == {
        "synthetic_rejection": "PASS",
        "partial_model_rejection": "PASS",
        "canonical_path_rejection": "PASS",
    }


def test_deterministic_fixture_results_and_temp_output_only(tmp_path: Path) -> None:
    first = preflight.qualify_fixtures()
    second = preflight.qualify_fixtures()
    assert json.dumps(first, sort_keys=True, allow_nan=True) == json.dumps(second, sort_keys=True, allow_nan=True)
    output = tmp_path / "engineering" / "preflight.json"
    artifact = preflight.write_artifact(output)
    assert output.is_file()
    assert artifact["formal_panel_consumed"] is False
    assert artifact["formal_inference_performed"] is False
    assert artifact["scientific_outcome_computed"] is False
    assert not (preflight.ROOT / "experiments" / "paper_a_ext_a" / "results").exists()


def test_no_live_v8_path_is_used_or_written() -> None:
    source = preflight.Path(preflight.__file__).read_text(encoding="utf-8")
    assert "raw/wikidata_v8" not in source
    assert "acquisition_checkpoint.json" not in source
    assert preflight.ARTIFACT_PATH.parent.name == "engineering"
