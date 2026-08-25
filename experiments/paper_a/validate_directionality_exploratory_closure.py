"""Read-only validation of the archived Paper A directionality analysis."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CLOSURE = ROOT / "experiments/paper_a/directionality_exploratory_closure.json"
MANIFEST = ROOT / "experiments/paper_a/directionality_exploratory_manifest.json"

EXPECTED_HASHES = {
    "exp026_result": "9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551",
    "exp027_result": "1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d",
    "exp027_manifest": "0f5c7319d3b2cd2148b3a21c3afae218545b13cf987f4a7850579dfea45042d0",
}

EXPECTED = {
    "Qwen": {
        "mean_abs_A_C": 0.129067,
        "signed_shallow_deep_bias": -0.066567,
        "C0_SymErr": 0.236573,
        "mean_abs_A_D": 0.129191,
        "mean_abs_A_R": 0.133796,
        "A_C_A_R_spearman": -0.9512,
    },
    "OLMo": {
        "mean_abs_A_C": 0.137292,
        "signed_shallow_deep_bias": 0.123646,
        "C0_SymErr": 0.313139,
        "mean_abs_A_D": 0.155755,
        "mean_abs_A_R": 0.128359,
        "A_C_A_R_spearman": -0.4576,
    },
    "Llama": {
        "mean_abs_A_C": 0.167031,
        "signed_shallow_deep_bias": 0.072448,
        "C0_SymErr": 0.307183,
        "mean_abs_A_D": 0.171198,
        "mean_abs_A_R": 0.160234,
        "A_C_A_R_spearman": -0.8878,
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_matrix(result: dict, profile: str, name: str) -> tuple[list[list[list[float]]], dict]:
    obj = result
    for part in profile.split("."):
        obj = obj[part]
    matrices = obj.get("matrices", obj)
    matrix = matrices[name]
    if isinstance(matrix, dict):
        return matrix["values"], matrix
    return matrix, {}


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def rank(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    pos = 0
    while pos < len(order):
        end = pos + 1
        while end < len(order) and values[order[end]] == values[order[pos]]:
            end += 1
        value = (pos + 1 + end) / 2.0
        for index in order[pos:end]:
            ranks[index] = value
        pos = end
    return ranks


def pearson(left: list[float], right: list[float]) -> float:
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right))
    left_norm = math.sqrt(sum((a - left_mean) ** 2 for a in left))
    right_norm = math.sqrt(sum((b - right_mean) ** 2 for b in right))
    return numerator / (left_norm * right_norm)


def summarize(
    matrices: dict[str, list[list[list[float]]]],
    threshold: float | None = None,
) -> dict[str, float | int]:
    c0 = matrices["c0_eval"]
    n = len(c0)
    c0_mean = [[mean([c0[i][j][k] for k in range(len(c0[i][j]))]) for j in range(n)] for i in range(n)]
    d_mean = [[mean([matrices["d_eval"][i][j][k] for k in range(len(c0[i][j]))]) for j in range(n)] for i in range(n)]
    r_mean = [[mean([matrices["r_eval"][i][j][k] for k in range(len(c0[i][j]))]) for j in range(n)] for i in range(n)]
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    if threshold is not None:
        pairs = [(i, j) for i, j in pairs if abs(i - j) / (n - 1) >= threshold]

    def asym(matrix: list[list[float]]) -> list[float]:
        return [matrix[i][j] - matrix[j][i] for i, j in pairs]

    ac = asym(c0_mean)
    ad = asym(d_mean)
    ar = asym(r_mean)
    result: dict[str, float | int] = {
        "pair_count": len(pairs),
        "mean_abs_A_C": mean([abs(value) for value in ac]),
        "signed_A_C": mean(ac),
        "mean_abs_A_D": mean([abs(value) for value in ad]),
        "signed_A_D": mean(ad),
        "mean_abs_A_R": mean([abs(value) for value in ar]),
        "signed_A_R": mean(ar),
    }
    if threshold is None:
        result["C0_SymErr"] = math.sqrt(
            sum((c0_mean[i][j] - c0_mean[j][i]) ** 2 for i in range(n) for j in range(n))
            / sum(c0_mean[i][j] ** 2 for i in range(n) for j in range(n))
        )
        result["A_C_A_R_spearman"] = pearson(rank(ac), rank(ar))
    return result


def close(actual: float, expected: float, tolerance: float = 5e-6) -> bool:
    return abs(actual - expected) <= tolerance


def main() -> int:
    closure = json.loads(CLOSURE.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["analysis_artifact"]["sha256"] == sha256(CLOSURE)
    result_paths = {
        "exp026_result": ROOT / "experiments/exp026/results/exp026_results.json",
        "exp027_result": ROOT / "experiments/exp027/results/exp027_results.json",
        "exp027_manifest": ROOT / "docs/experiments/canonical/EXP-027-CANONICAL-RESULT-MANIFEST.json",
    }
    observed_hashes = {key: sha256(path) for key, path in result_paths.items()}
    assert observed_hashes == EXPECTED_HASHES, ("canonical hash mismatch", observed_hashes)
    assert manifest["canonical_inputs"]["exp027_manifest_sha256"] == EXPECTED_HASHES["exp027_manifest"]
    assert manifest["canonical_inputs"]["exp026_result_sha256"] == EXPECTED_HASHES["exp026_result"]
    assert manifest["canonical_inputs"]["exp027_result_sha256"] == EXPECTED_HASHES["exp027_result"]

    exp026 = json.loads(result_paths["exp026_result"].read_text(encoding="utf-8"))
    exp027 = json.loads(result_paths["exp027_result"].read_text(encoding="utf-8"))
    profiles = {
        "Qwen": (exp026, "model_profiles.Q"),
        "OLMo": (exp026, "model_profiles.O"),
        "Llama": (exp027, "profile_archive"),
    }
    recomputed = {}
    for model, (result, profile) in profiles.items():
        matrices = {}
        axis = None
        for metric in ("c0_eval", "d_eval", "r_eval"):
            values, metadata = load_matrix(result, profile, metric)
            matrices[metric] = values
            if metric == "c0_eval":
                axis = metadata.get("axis_binding")
        if model != "Llama":
            assert axis["source_axis_role"] == "source_probe_layer"
            assert axis["target_axis_role"] == "target_representation_layer"
            assert axis["source_layer_ids"] == [f"source_layer_{i}" for i in range(len(values))]
            assert axis["target_layer_ids"] == [f"target_layer_{i}" for i in range(len(values))]
        assert len(matrices["c0_eval"]) == len(matrices["d_eval"]) == len(matrices["r_eval"])
        recomputed[model] = {
            "all_pairs": summarize(matrices),
            "distance_025": summarize(matrices, 0.25),
            "distance_050": summarize(matrices, 0.50),
        }

    for model, expected in EXPECTED.items():
        observed = recomputed[model]["all_pairs"]
        for key in ("mean_abs_A_C", "C0_SymErr", "mean_abs_A_D", "mean_abs_A_R"):
            assert close(float(observed[key]), expected[key]), (model, key, observed[key], expected[key])
        assert close(float(observed["signed_A_C"]), expected["signed_shallow_deep_bias"])
        assert close(float(observed["A_C_A_R_spearman"]), expected["A_C_A_R_spearman"], 5e-4)
        recorded = closure["results"][model]
        for key in ("mean_abs_A_C", "distance_025", "distance_050"):
            if key == "mean_abs_A_C":
                assert close(float(recorded[key]), float(observed[key]))
            else:
                actual_distance = recomputed[model][key]
                assert recorded[key]["pair_count"] == actual_distance["pair_count"]
                assert close(float(recorded[key]["mean_abs_A_C"]), float(actual_distance["mean_abs_A_C"]))
                assert close(float(recorded[key]["signed_A_C"]), float(actual_distance["signed_A_C"]))

    assert closure["validation"]["C0_ORIENTATION_VALID"] is True
    assert closure["validation"]["A_C_RECOMPUTATION_MATCH"] is True
    assert closure["validation"]["A_D_RECOMPUTATION_MATCH"] is True
    assert closure["validation"]["A_R_RECOMPUTATION_MATCH"] is True
    assert closure["validation"]["DISTANCE_ROBUSTNESS_MATCH"] is True
    assert closure["flags"]["MODEL_INFERENCE_RUN"] is False
    print("PA_DIRECTIONALITY_CANONICAL_HASHES_VERIFIED = true")
    print("C0_ORIENTATION_VALID = true")
    print("A_C_RECOMPUTATION_MATCH = true")
    print("A_D_RECOMPUTATION_MATCH = true")
    print("A_R_RECOMPUTATION_MATCH = true")
    print("DISTANCE_ROBUSTNESS_MATCH = true")
    print("PA_DIRECTIONALITY_VALIDATION = PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
