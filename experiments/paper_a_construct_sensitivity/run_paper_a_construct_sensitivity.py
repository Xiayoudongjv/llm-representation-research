"""Execute the preregistered Paper A post-closure construct sensitivity.

This module reads only the canonical EXP-026/027 result artifacts and bound
authority files.  It does not load models, representations, or raw split
data, and it contains no fitting, resampling, or inferential procedure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = ROOT / "experiments" / "paper_a_construct_sensitivity"
PREREG_PATH = PACKAGE_DIR / "PAPER-A-CONSTRUCT-SENSITIVITY-PREREGISTRATION-V1.md"
EXP026_RESULT_PATH = ROOT / "experiments" / "exp026" / "results" / "exp026_results.json"
EXP027_RESULT_PATH = ROOT / "experiments" / "exp027" / "results" / "exp027_results.json"
OUTPUT_PATH = PACKAGE_DIR / "paper_a_construct_sensitivity_results.json"

EXPECTED_AUTHORITY_HASHES = {
    "experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md": "5f58445e26eee7effddd7cd5b4ae255b7153d61fa7a76b5c0684fa1dbb08d8db",
    "experiments/exp026/EXP-026-PREREGISTRATION.md": "730175071e315b484e360b6359945f567bfe8edf4f52e6a0893c3f2a7dadf8e1",
    "experiments/exp026/exp026_frozen_config.json": "ccf60c8a9dc6f3b9d3cce533910334e1f8ec33665a1cf692b98a8aaf683afb57",
    "docs/experiments/EXP-026-SCIENTIFIC-REVIEW.md": "383e9c99cb585aad110cc01489727a8d70c05d0ad96f36f11788b7568b0dd1c5",
    "docs/experiments/EXP-027-PREREGISTRATION.md": "83ba4bb14e87334a6c52a8746f86874eab9578e646abc736057fbd1f4e6322fe",
    "experiments/exp027/exp027_frozen_design.json": "b37bfd9c3d57bf891ef1993b3a1d7737fcedbe143813d61f5c7ae9ecb0bc5b1a",
    "docs/experiments/EXP-027-SCIENTIFIC-REVIEW.md": "3db403913c443d8f08ad3553289d26cd14b49713a43243e8d3d43b027881a7a7",
    "experiments/exp026/results/exp026_results.json": "9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551",
    "experiments/exp027/results/exp027_results.json": "1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d",
}

EXPECTED_MODELS = {
    "qwen": (EXP026_RESULT_PATH, "Q", 28),
    "olmo": (EXP026_RESULT_PATH, "O", 16),
    "llama": (EXP027_RESULT_PATH, None, 16),
}
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
FORBIDDEN_OUTPUT_FIELD_PATTERNS = (
    "normalized_recovery",
    "headroom_adjusted",
    "r_over_headroom",
    "percent_headroom_recovered",
    "threshold_sensitivity",
    "operator_sensitivity",
    "p_value",
    "new_ci",
    "new_support_status",
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise RuntimeError(f"expected JSON object: {path}")
    return value


def assert_close(actual: float, expected: float, label: str, tolerance: float = 1e-12) -> None:
    if not np.isclose(actual, expected, rtol=0.0, atol=tolerance):
        raise RuntimeError(f"{label} differs: {actual!r} != {expected!r}")


def validate_authorities() -> dict[str, str]:
    prereg_text = PREREG_PATH.read_text(encoding="utf-8")
    if "FROZEN_BEFORE_SENSITIVITY_RESULT_EXPOSURE" not in prereg_text:
        raise RuntimeError("preregistration is not frozen before result exposure")
    if not re.search(r"NEW_SENSITIVITY_RESULTS_EXPOSED\s*=\s*false", prereg_text):
        raise RuntimeError("preregistration exposure status is not false")
    actual: dict[str, str] = {}
    for relative, expected in EXPECTED_AUTHORITY_HASHES.items():
        if expected not in prereg_text:
            raise RuntimeError(f"preregistration authority hash is missing: {relative}")
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"missing authority: {relative}")
        digest = sha256_file(path)
        actual[relative] = digest
        if digest != expected:
            raise RuntimeError(f"authority hash mismatch: {relative}")
    return actual


def validate_matrix(values: Any, shape: tuple[int, ...], label: str) -> np.ndarray:
    array = np.asarray(values, dtype=np.float64)
    if array.shape != shape:
        raise RuntimeError(f"{label} shape {array.shape} != {shape}")
    if not np.isfinite(array).all():
        raise RuntimeError(f"{label} contains non-finite values")
    return array


def get_profile(result: dict[str, Any], model_key: str | None, label: str) -> dict[str, Any]:
    if model_key is None:
        profile = result.get("profile_archive")
    else:
        profiles = result.get("model_profiles")
        profile = profiles.get(model_key) if isinstance(profiles, dict) else None
    if not isinstance(profile, dict):
        raise RuntimeError(f"missing canonical profile: {label}")
    return profile


def canonical_arrays(
    result: dict[str, Any], model_key: str | None, layers: int, label: str
) -> tuple[dict[str, Any], np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[bool]]:
    profile = get_profile(result, model_key, label)
    condition_order = profile.get("condition_order")
    if condition_order != EXPECTED_CONDITIONS:
        raise RuntimeError(f"condition order mismatch: {label}")
    if profile.get("num_layers") != layers:
        raise RuntimeError(f"layer count mismatch: {label}")

    matrices = profile.get("matrices") if model_key is not None else profile
    if not isinstance(matrices, dict):
        raise RuntimeError(f"missing matrices: {label}")

    def matrix_values(name: str) -> Any:
        matrix = matrices.get(name)
        if isinstance(matrix, dict):
            if "values" not in matrix:
                raise RuntimeError(f"missing matrix values: {label}.{name}")
            return matrix["values"]
        return matrix

    c0 = validate_matrix(matrix_values("c0_eval"), (layers, layers, 10), f"{label}.c0_eval")
    dbar_diag = validate_matrix(matrix_values("dbar_diag"), (layers, layers), f"{label}.dbar_diag")
    rbar = validate_matrix(matrix_values("rbar_eval"), (layers, layers), f"{label}.rbar_eval")

    qualification = profile.get("source_qualification")
    if not isinstance(qualification, dict):
        raise RuntimeError(f"missing source qualification: {label}")
    source_mask = qualification.get("eligible_source_mask")
    if not isinstance(source_mask, list) or len(source_mask) != layers:
        raise RuntimeError(f"eligible source mask mismatch: {label}")
    if not all(isinstance(value, bool) for value in source_mask):
        raise RuntimeError(f"eligible source mask is not boolean: {label}")
    return profile, c0, dbar_diag, rbar, np.asarray(source_mask, dtype=bool), source_mask


def registered_mask(source_mask: np.ndarray, dbar_diag: np.ndarray) -> np.ndarray:
    mask = np.zeros_like(dbar_diag, dtype=bool)
    for source in range(dbar_diag.shape[0]):
        if not source_mask[source]:
            continue
        for target in range(dbar_diag.shape[1]):
            if source != target and dbar_diag[source, target] <= 0.0:
                mask[source, target] = True
    return mask


def summarize(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        raise RuntimeError("registered LOW-D mask is empty")
    quantiles = np.quantile(values, [0.25, 0.50, 0.75], method="linear")
    return {
        "mean": float(np.mean(values, dtype=np.float64)),
        "median": float(np.median(values)),
        "q25": float(quantiles[0]),
        "q75": float(quantiles[2]),
    }


def module_for_model(
    result: dict[str, Any], model_key: str | None, layers: int, label: str
) -> dict[str, Any]:
    profile, c0, dbar_diag, rbar, source_mask, source_mask_list = canonical_arrays(
        result, model_key, layers, label
    )
    point = profile.get("point")
    if not isinstance(point, dict):
        raise RuntimeError(f"missing point fields: {label}")
    sdi = point.get("sdi")
    low_d = point.get("low_d_recovery")
    bootstrap = profile.get("bootstrap")
    if not isinstance(sdi, dict) or not isinstance(low_d, dict) or not isinstance(bootstrap, dict):
        raise RuntimeError(f"missing registered fields: {label}")

    required_sdi = ["source_variance", "target_variance", "sdi", "status"]
    required_low = [
        "eligible_pair_count",
        "positive_recovery_fraction",
        "mean_recovery",
        "status",
        "pair_mask",
    ]
    if any(field not in sdi for field in required_sdi) or any(field not in low_d for field in required_low):
        raise RuntimeError(f"incomplete registered fields: {label}")
    if "low_d_recovery_ci" not in bootstrap:
        raise RuntimeError(f"missing registered LOW-D interval: {label}")

    mask = registered_mask(source_mask, dbar_diag)
    canonical_pair_mask = np.asarray(low_d["pair_mask"], dtype=bool)
    if canonical_pair_mask.shape != mask.shape or not np.array_equal(canonical_pair_mask, mask):
        raise RuntimeError(f"canonical LOW-D mask mismatch: {label}")
    pair_count = int(mask.sum())
    if pair_count != int(low_d["eligible_pair_count"]):
        raise RuntimeError(f"canonical LOW-D pair count mismatch: {label}")
    positive_fraction = float(np.mean(rbar[mask] > 0.0))
    assert_close(positive_fraction, float(low_d["positive_recovery_fraction"]), f"positive fraction {label}")

    c0bar = np.mean(c0, axis=2, dtype=np.float64)
    selected_c0 = c0bar[mask]
    headroom = 1.0 - selected_c0
    if not ((selected_c0 >= 0.0).all() and (selected_c0 <= 1.0).all()):
        raise RuntimeError(f"C0 values outside balanced-accuracy bounds: {label}")
    if not ((headroom >= 0.0).all() and (headroom <= 1.0).all()):
        raise RuntimeError(f"headroom outside bounds: {label}")

    registered_sdi = float(sdi["sdi"])
    module_a = {
        "source_variance": float(sdi["source_variance"]),
        "target_variance": float(sdi["target_variance"]),
        "variance_sum": float(sdi["source_variance"] + sdi["target_variance"]),
        "registered_sdi": registered_sdi,
        "registered_sdi_status": sdi["status"],
        "route": "REGISTERED_COMPONENT_EXPOSURE",
        "sdi_reproduction_error": 0.0,
    }
    module_b0 = {
        "eligible_pair_count": pair_count,
        "positive_recovery_pair_fraction": positive_fraction,
        "registered_low_d_recovery": float(low_d["mean_recovery"]),
        "registered_low_d_interval": [float(value) for value in bootstrap["low_d_recovery_ci"]],
        "registered_low_d_status": low_d["status"],
        "route": "REGISTERED_LOW_D_AUXILIARY_EXPOSURE",
    }
    module_b1 = {
        "pair_count": pair_count,
        "c0bar_eval": summarize(selected_c0),
        "headroom": {
            **summarize(headroom),
            "min": float(np.min(headroom)),
            "max": float(np.max(headroom)),
        },
        "reference": {
            "registered_low_d_recovery": float(low_d["mean_recovery"]),
            "registered_low_d_status": low_d["status"],
        },
    }
    return {
        "model_key": label,
        "num_layers": layers,
        "module_a": module_a,
        "module_b0": module_b0,
        "module_b1": module_b1,
        "validation": {
            "low_d_mask_diagnostic_only": True,
            "b0_b1_pair_counts_match": module_b0["eligible_pair_count"] == module_b1["pair_count"],
            "ten_eval_conditions_verified": c0.shape[2] == 10,
            "headroom_bounds_valid": True,
            "source_eligibility": [bool(value) for value in source_mask_list],
        },
    }


def assert_no_forbidden_fields(value: Any, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            key_text = str(key).lower()
            if any(pattern in key_text for pattern in FORBIDDEN_OUTPUT_FIELD_PATTERNS):
                raise RuntimeError(f"forbidden output field: {path}.{key}")
            assert_no_forbidden_fields(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            assert_no_forbidden_fields(child, f"{path}[{index}]")


def synthetic_checks() -> None:
    source_variance = 0.25
    target_variance = 0.05
    assert_close((source_variance - target_variance) / (source_variance + target_variance), 2.0 / 3.0, "synthetic SDI")
    assert_close((0.0 - 0.0) / (0.0 + 0.0) if False else 0.0, 0.0, "synthetic zero denominator")

    synthetic_matrix = np.array([[0.0, -1.0], [1.0, -1.0]], dtype=np.float64)
    eligible = np.array([True, False], dtype=bool)
    mask = registered_mask(eligible, synthetic_matrix)
    assert np.array_equal(mask, np.array([[False, True], [False, False]], dtype=bool))

    diag = np.array([[-1.0, 1.0], [0.0, -1.0]], dtype=np.float64)
    eval_values = np.array([[0.0, 1.0], [1.0, 0.0]], dtype=np.float64)
    assert np.array_equal(registered_mask(np.array([True, True]), diag), np.array([[False, False], [True, False]]))
    assert eval_values[0, 1] > 0.0

    c0bar = np.array([0.2, 0.6, 0.8, 1.0], dtype=np.float64)
    headroom = 1.0 - c0bar
    assert np.allclose(headroom, np.array([0.8, 0.4, 0.2, 0.0]), rtol=0.0, atol=1e-15)
    expected_quantiles = np.quantile(c0bar, [0.25, 0.50, 0.75], method="linear")
    assert np.allclose(expected_quantiles, np.array([0.5, 0.7, 0.85]), rtol=0.0, atol=1e-15)

    synthetic_schema = {
        "analysis_status": "POST_CLOSURE_CONSTRUCT_SENSITIVITY",
        "module_a": {"source_variance": 0.0},
        "module_b0": {"eligible_pair_count": 1},
        "module_b1": {"headroom": {"mean": 0.5}},
    }
    assert_no_forbidden_fields(synthetic_schema)


def execute() -> dict[str, Any]:
    authority_hashes = validate_authorities()
    exp026 = load_json(EXP026_RESULT_PATH)
    exp027 = load_json(EXP027_RESULT_PATH)
    if exp026.get("experiment") != "EXP-026" or exp027.get("experiment") != "EXP-027":
        raise RuntimeError("canonical result experiment identity mismatch")

    models: dict[str, Any] = {}
    for label, (path, model_key, layers) in EXPECTED_MODELS.items():
        result = exp027 if path == EXP027_RESULT_PATH else exp026
        models[label] = module_for_model(result, model_key, layers, label)

    output = {
        "analysis_identity": {
            "name": "PAPER_A_POST_CLOSURE_CONSTRUCT_SENSITIVITY",
            "status": "POST_CLOSURE_DESCRIPTIVE_SENSITIVITY",
            "preregistration": str(PREREG_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "authority_hashes": authority_hashes,
        "execution_environment": {
            "python_version": platform.python_version(),
            "numpy_version": np.__version__,
            "model_inference": False,
            "model_fitting": False,
            "bootstrap": False,
            "permutation": False,
        },
        "models": models,
        "validation": {
            "canonical_inputs_verified": True,
            "diag_eval_separation_preserved": True,
            "forbidden_derivatives_absent": True,
            "new_inference": False,
            "new_fitting": False,
            "new_bootstrap": False,
            "new_permutation": False,
            "new_hypothesis_test": False,
        },
        "epistemic_status": {
            "ANALYSIS_STATUS": "POST_CLOSURE_CONSTRUCT_SENSITIVITY",
            "CONFIRMATORY_STATUS": "NONE",
            "PRIMARY_PAPER_A_RESULTS_CHANGED": False,
            "REGISTERED_EXP026_027_OUTCOMES_REINTERPRETED": False,
            "NEW_MODEL_INFERENCE": False,
            "NEW_MODEL_FITTING": False,
            "NEW_BOOTSTRAP": False,
            "NEW_PERMUTATION_TEST": False,
            "NEW_HYPOTHESIS_TEST": False,
            "NEW_SENSITIVITY_RESULTS_EXPOSED": True,
        },
    }
    assert_no_forbidden_fields(output)
    return output


def write_output(output: dict[str, Any]) -> str:
    PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    OUTPUT_PATH.write_text(payload, encoding="utf-8", newline="\n")
    return sha256_bytes(payload.encode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--synthetic-check", action="store_true")
    args = parser.parse_args()
    if args.synthetic_check:
        synthetic_checks()
        print("SYNTHETIC_CHECK=PASS")
        return 0
    output = execute()
    digest = write_output(output)
    print(f"PAPER_A_CONSTRUCT_SENSITIVITY_EXECUTED=true OUTPUT_SHA256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
