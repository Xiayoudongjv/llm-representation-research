"""Focused tests for the pre-acquisition TEMPORAL_SOURCE_V2 freeze."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).parents[1]
MODULE_PATH = ROOT / "experiments" / "paper_a_ext_a" / "engineering" / "temp_feas_v2" / "validate_temporal_source_v2.py"
PROTOCOL_PATH = MODULE_PATH.with_name("temporal_source_v2_protocol.json")
SPEC = importlib.util.spec_from_file_location("temp_v2_validator", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def protocol() -> dict:
    return json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))


def test_frozen_protocol_validates() -> None:
    assert MODULE.validate_protocol(protocol()) == []


def test_prior_negative_evidence_is_preserved() -> None:
    evidence = protocol()["prior_source_evidence"]
    assert evidence["surface_leakage_pass"] == 3
    assert evidence["surface_leakage_reject"] == 2837
    assert evidence["temporal_families_possible"] == 1


def test_freshness_and_fail_closed_backend_are_frozen() -> None:
    value = protocol()
    assert value["freshness"]["exclude_prior_v8_candidate_universe"] is True
    assert value["acquisition_backend"]["fallback_policy"]["mode"] == "FAIL_CLOSED_NO_ACQUISITION"


def test_no_data_or_model_access_flags() -> None:
    value = protocol()
    assert value["required_flags"] == {
        "TEMPORAL_SOURCE_V2_FROZEN": True,
        "TEMPORAL_SOURCE_V2_DATA_ACCESSED": False,
        "OLD_CONFIRMATION_REUSED": False,
        "FORMAL_MODEL_INFERENCE_PERFORMED": False,
        "FORMAL_SCIENTIFIC_OUTCOME_CREATED": False,
    }
