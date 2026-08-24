"""Synthetic-only qualification for the PA-EXT-A scientific analysis path.

This module deliberately does not load a real panel or a model.  It imports
the already-frozen EXP-026 measurement primitives and applies the frozen
PA-EXT-A A1--A6 routing rules to deterministic synthetic component profiles.
The resulting artifact is engineering evidence only; it is not a scientific
result and cannot be published to a canonical result path.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
ENGINEERING_DIR = ROOT / "experiments" / "paper_a_ext_a" / "engineering"
ARTIFACT_PATH = ENGINEERING_DIR / "pa_ext_a_006q_scientific_analysis_preflight.json"
EXP026_PATH = ROOT / "experiments" / "exp026" / "run_exp026.py"
CONFIG_PATH = ROOT / "experiments" / "paper_a_ext_a" / "paper_a_ext_a_frozen_config.json"
ROUTING_PATH = ROOT / "docs" / "paper" / "extension" / "PAPER-A-CROSS-TASK-OUTCOME-ROUTING.md"

EXPECTED_ROUTE_NAMES = {
    "A1": "THREE_MODEL_PROFILE_STABILITY",
    "A2": "PARTIAL_PROFILE_STABILITY",
    "A3": "TASK_CONDITIONAL_ORGANIZATION",
    "A4": "TASK_CONDITIONAL_RECALIBRATABILITY",
    "A5": "BROAD_TASK_CONDITIONAL_PROFILE",
    "A6": "NOT_FULLY_ADJUDICATED",
}
MODEL_KEYS = ("Qwen", "OLMo", "Llama")
HISTORICAL_PROFILES = {
    "Qwen": ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED"),
    "OLMo": ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED"),
    "Llama": ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED"),
}


class QualificationError(RuntimeError):
    """Raised when a synthetic qualification input fails closed."""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_exp026() -> Any:
    module_name = "_pa_ext_a_006q_exp026_reference"
    spec = importlib.util.spec_from_file_location(module_name, EXP026_PATH)
    if spec is None or spec.loader is None:
        raise QualificationError("EXP026_REFERENCE_IMPORT_FAILED")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


EXP026 = _load_exp026()


@dataclass(frozen=True)
class SyntheticFixture:
    """A deterministic component matrix with a declared expected profile."""

    name: str
    structure: str
    organization: str
    low_d: str
    expected: tuple[str, str, str]


def _off_diagonal_matrix(value: float, num_layers: int) -> np.ndarray:
    matrix = np.full((num_layers, num_layers), value, dtype=np.float32)
    np.fill_diagonal(matrix, 0.0)
    return matrix


def _finite_or_none(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None


def synthetic_component_matrices(
    *, structure: str, organization: str, low_d: str, num_layers: int = 4
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Build d-bar, diagnostic d-bar, and r-bar synthetic matrices.

    The distance term is an integer layer gap, matching the production
    ``normalized_pair_distance`` ordering.  Organization terms are attached
    to the target or source axis respectively, so the orientation is
    independently observable through the production SDI calculation.
    """

    if structure == "positive":
        dbar = np.zeros((num_layers, num_layers), dtype=np.float32)
        for source in range(num_layers):
            for target in range(num_layers):
                if source == target:
                    continue
                value = float(abs(source - target))
                if organization == "TARGET":
                    value += 0.5 * target
                elif organization == "SOURCE":
                    value += 0.5 * source
                elif organization not in {"NONE", "BOUNDARY"}:
                    raise QualificationError("UNKNOWN_SYNTHETIC_ORGANIZATION")
                dbar[source, target] = value
    elif structure == "null":
        dbar = _off_diagonal_matrix(1.0, num_layers)
    else:
        raise QualificationError("UNKNOWN_SYNTHETIC_STRUCTURE")

    diagnostic = _off_diagonal_matrix(-1.0, num_layers)
    if low_d == "SUPPORTED":
        rbar = _off_diagonal_matrix(1.0, num_layers)
    elif low_d == "NOT_SUPPORTED":
        rbar = _off_diagonal_matrix(-1.0, num_layers)
    else:
        raise QualificationError("UNKNOWN_SYNTHETIC_LOW_D_STATE")
    return dbar, diagnostic, rbar


def analyze_component_profile(
    dbar: np.ndarray,
    diagnostic_dbar: np.ndarray,
    rbar: np.ndarray,
    *,
    eligible_mask: Sequence[bool] | None = None,
) -> dict[str, Any]:
    """Run the frozen EXP-026 profile primitives on synthetic matrices."""

    dbar = np.asarray(dbar, dtype=np.float32)
    diagnostic_dbar = np.asarray(diagnostic_dbar, dtype=np.float32)
    rbar = np.asarray(rbar, dtype=np.float32)
    if dbar.ndim != 2 or dbar.shape[0] != dbar.shape[1]:
        raise QualificationError("SYNTHETIC_MATRIX_SHAPE_INVALID")
    if diagnostic_dbar.shape != dbar.shape or rbar.shape != dbar.shape:
        raise QualificationError("SYNTHETIC_MATRIX_SHAPE_MISMATCH")
    num_layers = dbar.shape[0]
    mask = list(eligible_mask or [True] * num_layers)
    if len(mask) != num_layers:
        raise QualificationError("SYNTHETIC_ELIGIBILITY_SHAPE_INVALID")
    point = EXP026._summarize_point_profile(
        dbar, rbar, mask, num_layers, diagnostic_dbar
    )
    distance = point["distance_association"]
    sdi = point["sdi"]["sdi"]
    low_d = point["low_d_recovery"]
    bootstrap = {
        "distance_association_ci": (
            [float(distance - 0.1), float(distance + 0.1)]
            if math.isfinite(distance)
            else [float("nan"), float("nan")]
        ),
        "sdi_ci": [float(sdi - 0.1), float(sdi + 0.1)] if math.isfinite(sdi) else [float("nan"), float("nan")],
        "low_d_recovery_ci": (
            [float(low_d["mean_recovery"] - 0.1), float(low_d["mean_recovery"] + 0.1)]
            if low_d.get("mean_recovery") is not None
            else [float("nan"), float("nan")]
        ),
    }
    support = EXP026._support_classes(point, bootstrap)
    return {
        "distance_statistic": distance,
        "distance_status": support["distance_support"],
        "source_target_statistic": sdi,
        "source_target_status": support["sdi_class"],
        "organization_label": support["sdi_class"],
        "low_d_status": support["low_d_support"],
        "point": point,
        "support": support,
        "bootstrap_fixture_ci": bootstrap,
    }


def build_fixtures() -> tuple[SyntheticFixture, ...]:
    """Return the six declared cases without outcome-based threshold tuning."""

    return (
        SyntheticFixture("CASE_1_TARGET_LOW_D_SUPPORTED", "positive", "TARGET", "SUPPORTED", ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED")),
        SyntheticFixture("CASE_2_TARGET_LOW_D_NOT_SUPPORTED", "positive", "TARGET", "NOT_SUPPORTED", ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED")),
        SyntheticFixture("CASE_3_SOURCE_LOW_D_SUPPORTED", "positive", "SOURCE", "SUPPORTED", ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED")),
        SyntheticFixture("CASE_4_SOURCE_LOW_D_NOT_SUPPORTED", "positive", "SOURCE", "NOT_SUPPORTED", ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "NOT_SUPPORTED")),
        SyntheticFixture("CASE_5_NULL", "null", "NONE", "NOT_SUPPORTED", ("NOT_EVALUABLE", "NO_ROW_OR_COLUMN_VARIATION", "NOT_SUPPORTED")),
        SyntheticFixture("CASE_6_BOUNDARY_ORGANIZATION", "positive", "BOUNDARY", "SUPPORTED", ("POSITIVE_SUPPORTED", "NO_DOMINANCE", "SUPPORTED")),
    )


def qualify_fixtures() -> dict[str, Any]:
    results: dict[str, Any] = {}
    for fixture in build_fixtures():
        matrices = synthetic_component_matrices(
            structure=fixture.structure,
            organization=fixture.organization,
            low_d=fixture.low_d,
        )
        observed = analyze_component_profile(*matrices)
        observed_tuple = (
            observed["distance_status"],
            observed["source_target_status"],
            observed["low_d_status"],
        )
        if observed_tuple != fixture.expected:
            raise QualificationError(f"FIXTURE_EXPECTATION_MISMATCH:{fixture.name}:{observed_tuple}")
        results[fixture.name] = {
            "expected_profile": list(fixture.expected),
            "observed_profile": list(observed_tuple),
            "distance_statistic": _finite_or_none(observed["distance_statistic"]),
            "distance_status": observed["distance_status"],
            "source_target_statistic": observed["source_target_statistic"],
            "source_target_status": observed["source_target_status"],
            "organization_label": observed["organization_label"],
            "low_d_status": observed["low_d_status"],
            "status": "PASS",
        }
    return results


def route_a1_a6(
    profiles: Mapping[str, Sequence[str]],
    *,
    technical_valid: Mapping[str, bool] | None = None,
) -> dict[str, Any]:
    """Apply the frozen PA-EXT-A A1--A6 exact-match routing rules."""

    if set(profiles) != set(MODEL_KEYS) or any(len(tuple(value)) != 3 for value in profiles.values()):
        raise QualificationError("PROFILE_MODEL_SET_OR_SHAPE_INVALID")
    validity = technical_valid or {key: True for key in MODEL_KEYS}
    if set(validity) != set(MODEL_KEYS):
        raise QualificationError("PROFILE_VALIDITY_MODEL_SET_INVALID")
    if not all(validity.values()):
        return {"route": "A6", "label": EXPECTED_ROUTE_NAMES["A6"], "status": "PASS"}
    tuples = {key: tuple(value) for key, value in profiles.items()}
    matching = [key for key in MODEL_KEYS if tuples[key] == HISTORICAL_PROFILES[key]]
    if len(matching) == len(MODEL_KEYS):
        route = "A1"
    elif matching:
        route = "A2"
    else:
        all_positive = all(value[0] == "POSITIVE_SUPPORTED" for value in tuples.values())
        organization_changed = any(
            tuples[key][1] != HISTORICAL_PROFILES[key][1] for key in MODEL_KEYS
        )
        low_d_changed = any(
            tuples[key][2] != HISTORICAL_PROFILES[key][2] for key in MODEL_KEYS
        )
        if all_positive and organization_changed and not low_d_changed:
            route = "A3"
        elif all_positive and not organization_changed and low_d_changed:
            route = "A4"
        else:
            route = "A5"
    return {
        "route": route,
        "label": EXPECTED_ROUTE_NAMES[route],
        "matching_models": matching,
        "status": "PASS",
    }


def qualify_routes() -> dict[str, Any]:
    cases = {
        "A1": HISTORICAL_PROFILES,
        "A2": {**HISTORICAL_PROFILES, "Llama": ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED")},
        "A3": {
            "Qwen": ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "NOT_SUPPORTED"),
            "OLMo": ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED"),
            "Llama": ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED"),
        },
        "A4": {
            "Qwen": ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED"),
            "OLMo": ("POSITIVE_SUPPORTED", "SOURCE_DOMINANT", "NOT_SUPPORTED"),
            "Llama": ("POSITIVE_SUPPORTED", "TARGET_DOMINANT", "NOT_SUPPORTED"),
        },
        "A5": {
            "Qwen": ("NOT_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED"),
            "OLMo": ("NOT_SUPPORTED", "SOURCE_DOMINANT", "SUPPORTED"),
            "Llama": ("NOT_SUPPORTED", "TARGET_DOMINANT", "SUPPORTED"),
        },
    }
    result = {name: route_a1_a6(profile) for name, profile in cases.items()}
    result["A6"] = route_a1_a6(HISTORICAL_PROFILES, technical_valid={key: key != "OLMo" for key in MODEL_KEYS})
    if any(value["route"] != name for name, value in result.items()):
        raise QualificationError("A1_A6_ROUTE_COVERAGE_FAILED")
    invalid = False
    try:
        route_a1_a6({"Qwen": HISTORICAL_PROFILES["Qwen"]})
    except QualificationError:
        invalid = True
    if not invalid:
        raise QualificationError("INVALID_ROUTE_NOT_REJECTED")
    return result | {"invalid_route_rejection": True, "mutually_exclusive": True}


def validate_synthetic_observations(
    records: Iterable[Mapping[str, Any]],
    *,
    expected_authority_hash: str,
    input_mode: str = "synthetic",
) -> None:
    """Validate the small synthetic observation boundary before analysis."""

    rows = list(records)
    if input_mode == "production" and any(row.get("provenance") == "synthetic" for row in rows):
        raise QualificationError("SYNTHETIC_INPUT_PRESENTED_AS_PRODUCTION")
    if expected_authority_hash != sha256_file(CONFIG_PATH):
        raise QualificationError("WRONG_AUTHORITY_HASH")
    if not rows:
        raise QualificationError("NO_SYNTHETIC_OBSERVATIONS")
    models = {str(row.get("model")) for row in rows}
    if models != set(MODEL_KEYS):
        raise QualificationError("MISSING_MODEL_OR_PARTIAL_MODEL_COMPLETION")
    required_partitions = {"FIT", "DIAGNOSTIC", "EVAL"}
    partitions_by_model: dict[str, set[str]] = {key: set() for key in MODEL_KEYS}
    identities: set[tuple[str, str, str]] = set()
    family_partitions: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        identity = (str(row.get("model")), str(row.get("partition")), str(row.get("record_id")))
        if identity in identities:
            raise QualificationError("DUPLICATE_OBSERVATION_IDENTITY")
        identities.add(identity)
        partitions_by_model[str(row.get("model"))].add(str(row.get("partition")))
        if not row.get("layer_complete", True):
            raise QualificationError("INCOMPLETE_REPRESENTATION_SET")
        vectors = np.asarray(row.get("vectors"))
        if vectors.ndim != 2 or vectors.shape[0] != int(row.get("num_layers", -1)):
            raise QualificationError("MISSING_LAYER_OR_WRONG_LAYER_SHAPE")
        if not np.isfinite(vectors).all():
            raise QualificationError("NONFINITE_SYNTHETIC_REPRESENTATION")
        family_key = (str(row.get("model")), str(row.get("family_id")))
        family_partitions.setdefault(family_key, set()).add(str(row.get("partition")))
    if any(len(parts) > 1 for parts in family_partitions.values()):
        raise QualificationError("FIT_DIAG_EVAL_SPLIT_CONTAMINATION")
    if any(parts != required_partitions for parts in partitions_by_model.values()):
        raise QualificationError("PARTIAL_MODEL_COMPLETION")


def _valid_synthetic_records() -> list[dict[str, Any]]:
    records = []
    for model in MODEL_KEYS:
        for partition in ("FIT", "DIAGNOSTIC", "EVAL"):
            records.append({
                "model": model,
                "partition": partition,
                "record_id": f"synthetic-{model}-{partition}",
                "family_id": f"family-{model}-{partition}",
                "vectors": np.zeros((4, 2), dtype=np.float32),
                "num_layers": 4,
                "layer_complete": True,
                "provenance": "synthetic",
            })
    return records


def qualify_input_guards() -> dict[str, str]:
    expected_hash = sha256_file(CONFIG_PATH)
    checks: dict[str, str] = {}
    validate_synthetic_observations(_valid_synthetic_records(), expected_authority_hash=expected_hash)
    checks["valid_synthetic_input"] = "PASS"
    mutations = {
        "missing_model": lambda rows: [row for row in rows if row["model"] != "Llama"],
        "missing_layer": lambda rows: [{**rows[0], "vectors": np.zeros((3, 2)), "num_layers": 4}],
        "duplicate_identity": lambda rows: rows + [dict(rows[0])],
        "split_contamination": lambda rows: rows + [{**rows[0], "record_id": "contaminant", "partition": "EVAL", "family_id": rows[0]["family_id"]}],
        "wrong_authority_hash": lambda rows: rows,
        "partial_model_completion": lambda rows: [row for row in rows if not (row["model"] == "Llama" and row["partition"] == "EVAL")],
        "incomplete_representation": lambda rows: [{**rows[0], "layer_complete": False}],
        "synthetic_as_production": lambda rows: rows,
    }
    for name, mutate in mutations.items():
        try:
            validate_synthetic_observations(
                mutate(_valid_synthetic_records()),
                expected_authority_hash="0" * 64 if name == "wrong_authority_hash" else expected_hash,
                input_mode="production" if name == "synthetic_as_production" else "synthetic",
            )
        except QualificationError:
            checks[name] = "PASS"
        else:
            raise QualificationError(f"INPUT_GUARD_NOT_FAIL_CLOSED:{name}")
    return checks


def publication_guard(*, output_path: Path, model_completion: Mapping[str, bool], synthetic: bool) -> None:
    """Reject all synthetic or incomplete publication attempts."""

    canonical_prefix = ROOT / "experiments" / "paper_a_ext_a" / "results"
    if synthetic:
        raise QualificationError("SYNTHETIC_PUBLICATION_REJECTED")
    if output_path.resolve().is_relative_to(canonical_prefix.resolve()):
        raise QualificationError("CANONICAL_PUBLICATION_REQUIRES_FORMAL_AUTHORITY")
    if set(model_completion) != set(MODEL_KEYS) or not all(model_completion.values()):
        raise QualificationError("PARTIAL_THREE_MODEL_PUBLICATION_REJECTED")


def qualify_publication_guards() -> dict[str, str]:
    checks: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="pa_ext_a_006q_") as tmp:
        temp_path = Path(tmp) / "synthetic.json"
        for name, kwargs in {
            "synthetic_rejection": {"output_path": temp_path, "model_completion": dict.fromkeys(MODEL_KEYS, True), "synthetic": True},
            "partial_model_rejection": {"output_path": temp_path, "model_completion": {"Qwen": True, "OLMo": True, "Llama": False}, "synthetic": False},
            "canonical_path_rejection": {"output_path": ROOT / "experiments" / "paper_a_ext_a" / "results" / "candidate.json", "model_completion": dict.fromkeys(MODEL_KEYS, True), "synthetic": False},
        }.items():
            try:
                publication_guard(**kwargs)
            except QualificationError:
                checks[name] = "PASS"
            else:
                raise QualificationError(f"PUBLICATION_GUARD_FAILED:{name}")
    return checks


def _canonical_payload(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def build_artifact(root: Path = ROOT) -> dict[str, Any]:
    if root.resolve() != ROOT.resolve():
        raise QualificationError("ROOT_OVERRIDE_NOT_ALLOWED")
    fixture_results = qualify_fixtures()
    route_results = qualify_routes()
    input_guards = qualify_input_guards()
    publication_guards = qualify_publication_guards()
    first = qualify_fixtures()
    second = qualify_fixtures()
    repeatability = _canonical_payload(first) == _canonical_payload(second)
    if not repeatability:
        raise QualificationError("SYNTHETIC_ANALYSIS_NOT_DETERMINISTIC")
    artifact: dict[str, Any] = {
        "task_id": "PA-EXT-A-006Q",
        "git_head": "6666b01e618e9a68c01fc0adfeb0680b6aabfc82",
        "authority_references": {
            "frozen_config": {"path": str(CONFIG_PATH.relative_to(ROOT)), "sha256": sha256_file(CONFIG_PATH)},
            "outcome_routing": {"path": str(ROUTING_PATH.relative_to(ROOT)), "sha256": sha256_file(ROUTING_PATH)},
            "exp026_analysis_runner": {"path": str(EXP026_PATH.relative_to(ROOT)), "sha256": sha256_file(EXP026_PATH)},
        },
        "authoritative_functions": [
            "experiments/exp026/run_exp026.py:_distance_association_point",
            "experiments/exp026/run_exp026.py:_summarize_point_profile",
            "experiments/exp026/run_exp026.py:_support_classes",
            "docs/paper/extension/PAPER-A-CROSS-TASK-OUTCOME-ROUTING.md: A1-A6",
        ],
        "synthetic_only": True,
        "formal_panel_consumed": False,
        "formal_inference_performed": False,
        "scientific_outcome_computed": False,
        "live_v8_touched": False,
        "fixture_results": fixture_results,
        "profile_routing": {"route_coverage": route_results, "orientation_guard": True},
        "input_fail_closed_guards": input_guards,
        "publication_guards": publication_guards,
        "determinism": {"repeatability": True, "fixture_hash": hashlib.sha256(_canonical_payload(fixture_results)).hexdigest()},
        "status": "PA_EXT_A_006Q_ENGINEERING_PASS",
    }
    artifact["artifact_content_sha256"] = hashlib.sha256(_canonical_payload(artifact)).hexdigest()
    return artifact


def write_artifact(path: Path = ARTIFACT_PATH) -> dict[str, Any]:
    artifact = build_artifact()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return artifact


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, default=ARTIFACT_PATH)
    args = parser.parse_args()
    artifact = write_artifact(args.artifact.resolve())
    print(json.dumps({"status": artifact["status"], "artifact": str(args.artifact), "artifact_content_sha256": artifact["artifact_content_sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
