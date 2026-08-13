"""Validate Task 081A's non-executable EXP-020 implementation specification.

This validator performs integrity and protocol checks only.  It does not load a
model, import a formal runner, or print formal prompt/source contents.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SPEC_PATH = Path(__file__).with_name("exp020_implementation_spec.json")
FROZEN_CONFIG_PATH = Path(__file__).with_name("exp020_frozen_config.json")
PREREGISTRATION_PATH = ROOT / "docs" / "experiments" / "EXP-020-PREREGISTRATION.md"
PREREGISTRATION_VALIDATOR_PATH = Path(__file__).with_name("validate_exp020_preregistration.py")
RESULT_FILENAMES = (
    "transition_metrics.csv", "probe_metrics.csv", "invariant_metrics.csv", "pair_summary.csv",
    "representation_summary.json", "validation_summary.json", "behavioral_outputs.csv",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _formal_result_paths(root: Path) -> list[Path]:
    roots = (root / "results" / "exp020", root / "experiments" / "exp020" / "results")
    return [directory / name for directory in roots for name in RESULT_FILENAMES if (directory / name).exists()]


def _git_clean_for_authority_files(root: Path) -> bool:
    files = [
        "experiments/exp020/exp020_frozen_config.json",
        "docs/experiments/EXP-020-PREREGISTRATION.md",
        "experiments/exp020/validate_exp020_preregistration.py",
    ]
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", *files], cwd=root, capture_output=True, text=True)
    unchanged = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *files], cwd=root, capture_output=True, text=True)
    return tracked.returncode == 0 and unchanged.returncode == 0


def _run_preregistration_validator(root: Path) -> tuple[bool, str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(PREREGISTRATION_VALIDATOR_PATH)],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0, (completed.stdout + completed.stderr).strip()


def matched_random_delta(task_delta, *, base_seed: int, model_index: int, block_index: int, split_index: int, source_group_index: int, target_group_index: int):
    """Recover EXP-018's deterministic matched-norm random control for synthetic tests."""
    import numpy as np

    task = np.asarray(task_delta, dtype=float)
    norm = float(np.linalg.norm(task))
    if norm < 1e-12:
        raise ValueError("Task delta must have non-zero norm.")
    seed = np.random.SeedSequence([base_seed, model_index, block_index, split_index, source_group_index, target_group_index])
    random = np.random.default_rng(seed).standard_normal(task.shape)
    return random * (norm / float(np.linalg.norm(random)))


def probability_column_index(classes, semantic_class_order: list[str], target_label: str) -> int:
    """Map fitted classifier classes to a frozen semantic label without assuming column order."""
    if target_label not in semantic_class_order:
        raise ValueError(f"Unknown semantic label: {target_label}")
    encoded_label = semantic_class_order.index(target_label)
    class_list = list(classes)
    if encoded_label not in class_list:
        raise ValueError(f"Classifier is missing encoded class {encoded_label} for {target_label!r}.")
    return class_list.index(encoded_label)


def paired_effects(baseline_target: float, task_target: float, random_target: float, opposite_target: float) -> dict[str, float]:
    """Compute the frozen paired effects using only synthetic scalar inputs."""
    task_effect = task_target - baseline_target
    random_effect = random_target - baseline_target
    opposite_effect = opposite_target - baseline_target
    return {
        "task_effect": task_effect,
        "random_effect": random_effect,
        "opposite_effect": opposite_effect,
        "D_random": task_effect - random_effect,
        "D_opposite": task_effect - opposite_effect,
    }


def primary_gate(*, task_mean: float, task_ci_low: float, random_contrast_mean: float, random_contrast_ci_low: float, opposite_contrast_mean: float, technical_invalid: bool = False, secondary_supported: bool = False) -> str:
    """Apply the frozen primary-only gate; secondary results cannot rescue it."""
    del secondary_supported
    if technical_invalid:
        return "REPRESENTATION_REPLICATION_INVALID"
    supported = (
        task_mean > 0
        and task_ci_low > 0
        and random_contrast_mean > 0
        and random_contrast_ci_low > 0
        and opposite_contrast_mean > 0
    )
    return "REPRESENTATION_REPLICATION_SUPPORTED" if supported else "REPRESENTATION_REPLICATION_NOT_SUPPORTED"


def derive_unresolved_fields(spec: dict[str, Any], provenance_tag: str) -> set[str]:
    """Derive unresolved keys from semantic-rule tags, never from a hand-maintained list."""
    derived: set[str] = set()
    for name, rule in spec.get("semantic_rules", {}).items():
        if rule.get("provenance_tag") != provenance_tag:
            continue
        components = rule.get("unresolved_components")
        if components:
            derived.update(f"{name}.{component}" for component in components)
        else:
            derived.add(name)
    return derived


def validate_readiness_fields(spec: dict[str, Any]) -> list[str]:
    """Reject any readiness claim inconsistent with semantic-rule provenance."""
    errors: list[str] = []
    primary = derive_unresolved_fields(spec, "UNRESOLVED_PRIMARY_CRITICAL")
    secondary = derive_unresolved_fields(spec, "UNRESOLVED_SECONDARY")
    serialized_primary = set(spec.get("unresolved_primary_critical", []))
    serialized_secondary = set(spec.get("unresolved_secondary", []))
    if serialized_primary != primary:
        errors.append("unresolved_primary_critical does not exactly match semantic-rule tags")
    if serialized_secondary != secondary:
        errors.append("unresolved_secondary does not exactly match semantic-rule tags")
    for name, rule in spec.get("semantic_rules", {}).items():
        if rule.get("provenance_tag") == "UNRESOLVED_PRIMARY_CRITICAL" and rule.get("value") is not None:
            errors.append(f"unresolved primary rule has an executable value: {name}")
        if rule.get("value_classification") in {"CANDIDATE_INTERPRETATION", "RECOMMENDED_OPTION"} and rule.get("value") is not None:
            errors.append(f"candidate/recommendation serialized as executable value: {name}")
    derived_primary_ready = not primary
    derived_secondary_ready = not secondary
    derived_full_ready = derived_primary_ready and derived_secondary_ready
    if spec.get("PRIMARY_READY") != derived_primary_ready:
        errors.append("PRIMARY_READY does not equal derived primary readiness")
    if spec.get("SECONDARY_READY") != derived_secondary_ready:
        errors.append("SECONDARY_READY does not equal derived secondary readiness")
    if spec.get("FULL_READY") != derived_full_ready:
        errors.append("FULL_READY does not equal derived full readiness")
    return errors


def _validate_bootstrap_schema(bootstrap: dict[str, Any]) -> list[str]:
    """Validate every user-approved cluster-bootstrap semantic without running data."""
    errors: list[str] = []
    expected = {
        "value_classification": "USER_APPROVED_PRE_OUTCOME_IMPLEMENTATION_SPEC",
        "cluster_key_fields": ["split_id", "held_out_source_item_id"],
        "split_strata": 2,
        "clusters_per_split": 12,
        "transition_rows_per_cluster": 3,
        "transition_rows_per_replicate": 72,
        "shared_resample_plan": ["task_effect", "D_random", "D_opposite"],
        "statistic": "arithmetic mean over 72 resampled transition-item values",
    }
    for key, value in expected.items():
        if bootstrap.get(key) != value:
            errors.append(f"bootstrap schema mismatch: {key}")
    if bootstrap.get("rng") != {"constructor": "np.random.Generator(np.random.PCG64(20260812))", "bit_generator": "PCG64"}:
        errors.append("bootstrap schema mismatch: explicit PCG64 RNG")
    if bootstrap.get("ci") != {"method": "percentile bootstrap", "quantiles": [0.025, 0.975], "numpy_method": "linear"}:
        errors.append("bootstrap schema mismatch: percentile CI")
    if bootstrap.get("descriptive") != {"mean": "arithmetic mean", "median": "np.median", "standard_deviation_ddof": 1, "proportion_positive": "mean(value > 0)"}:
        errors.append("bootstrap schema mismatch: descriptive statistics")
    behavior = bootstrap.get("degenerate_behavior", {})
    required_invalidity = {"nonfinite observed value", "nonfinite bootstrap statistic", "fewer than two distinct source-item clusters in either split", "not exactly 12 clusters per split", "not exactly 3 transition rows per cluster"}
    if behavior.get("retain_degenerate_replicates") is not True or behavior.get("all_identical_ci") != "[c, c]" or behavior.get("zero_is_positive") is not False or set(behavior.get("technical_invalidity", [])) != required_invalidity:
        errors.append("bootstrap schema mismatch: degenerate/technical-invalidity policy")
    if "not 72 independent prompts" not in bootstrap.get("interpretation_boundary", ""):
        errors.append("bootstrap schema mismatch: interpretation boundary")
    return errors


def validate_cluster_structure(clusters_by_split: dict[str, list[list[dict[str, float]]]]) -> None:
    """Validate the approved two-stratum, twelve-cluster, three-row design on synthetic data."""
    import numpy as np

    if len(clusters_by_split) != 2:
        raise ValueError("Bootstrap requires exactly two split strata.")
    for split_id, clusters in clusters_by_split.items():
        if len(clusters) != 12:
            raise ValueError(f"Split {split_id!r} must contain exactly 12 clusters.")
        source_ids = {cluster[0]["held_out_source_item_id"] for cluster in clusters if cluster}
        if len(source_ids) < 2:
            raise ValueError(f"Split {split_id!r} has fewer than two distinct source-item clusters.")
        for cluster in clusters:
            if len(cluster) != 3:
                raise ValueError("Each cluster must contain exactly three transition rows.")
            source_id = cluster[0]["held_out_source_item_id"]
            split_value = cluster[0]["split_id"]
            for row in cluster:
                if row["held_out_source_item_id"] != source_id or row["split_id"] != split_value:
                    raise ValueError("A source-item cluster cannot mix source IDs or split IDs.")
                for outcome in ("task_effect", "D_random", "D_opposite"):
                    if not np.isfinite(row[outcome]):
                        raise ValueError("Nonfinite observed value is technical invalidity.")


def cluster_resample_plan(clusters_by_split: dict[str, list[list[dict[str, float]]]], *, seed: int, resamples: int) -> list[dict[str, list[int]]]:
    """Create the approved shared PCG64 plan, preserving supplied split/cluster order."""
    import numpy as np

    validate_cluster_structure(clusters_by_split)
    split_ids = list(clusters_by_split)
    rng = np.random.Generator(np.random.PCG64(seed))
    return [{split_id: rng.integers(0, 12, size=12).tolist() for split_id in split_ids} for _ in range(resamples)]


def sampled_transition_rows(clusters_by_split: dict[str, list[list[dict[str, float]]]], replicate: dict[str, list[int]]) -> list[dict[str, float]]:
    """Expand one shared cluster plan without separating any three-row cluster."""
    rows: list[dict[str, float]] = []
    for split_id, indices in replicate.items():
        for index in indices:
            rows.extend(clusters_by_split[split_id][index])
    if len(rows) != 72:
        raise ValueError("Each bootstrap replicate must contain exactly 72 transition-item rows.")
    return rows


def bootstrap_cluster_statistics(clusters_by_split: dict[str, list[list[dict[str, float]]]], *, seed: int = 20260812, resamples: int = 10000) -> dict[str, Any]:
    """Compute synthetic-only approved cluster-bootstrap means and percentile CIs."""
    import numpy as np

    plan = cluster_resample_plan(clusters_by_split, seed=seed, resamples=resamples)
    outcomes = ("task_effect", "D_random", "D_opposite")
    means = {outcome: [] for outcome in outcomes}
    for replicate in plan:
        values = {outcome: [] for outcome in outcomes}
        for row in sampled_transition_rows(clusters_by_split, replicate):
            for outcome in outcomes:
                values[outcome].append(row[outcome])
        for outcome in outcomes:
            statistic = float(np.mean(values[outcome]))
            if not np.isfinite(statistic):
                raise ValueError("Nonfinite bootstrap statistic is technical invalidity.")
            means[outcome].append(statistic)
    return {
        "plan": plan,
        "means": {outcome: np.asarray(values, dtype=float) for outcome, values in means.items()},
        "ci": {outcome: np.quantile(values, [0.025, 0.975], method="linear") for outcome, values in means.items()},
    }


def descriptive_statistics(values) -> dict[str, float]:
    """Return the approved observed-row summaries, retaining zero and degenerate values."""
    import numpy as np

    array = np.asarray(values, dtype=float)
    if array.size == 0 or not np.isfinite(array).all():
        raise ValueError("Observed values must be nonempty and finite.")
    return {"mean": float(np.mean(array)), "median": float(np.median(array)), "standard_deviation": float(np.std(array, ddof=1)), "proportion_positive": float(np.mean(array > 0))}


def validate_spec(root: Path = ROOT) -> tuple[bool, list[str], dict[str, Any]]:
    """Return integrity validity, human-readable errors, and the parsed specification."""
    errors: list[str] = []
    spec = _load_json(root / SPEC_PATH.relative_to(ROOT))
    config = _load_json(root / FROZEN_CONFIG_PATH.relative_to(ROOT))
    authority = spec.get("authority_references", {})
    for path, key in ((FROZEN_CONFIG_PATH, "frozen_config_sha256"), (PREREGISTRATION_PATH, "preregistration_sha256"), (PREREGISTRATION_VALIDATOR_PATH, "preregistration_validator_sha256")):
        if _sha256(root / path.relative_to(ROOT)) != authority.get(key):
            errors.append(f"authority hash mismatch: {path.relative_to(ROOT)}")
    if not _git_clean_for_authority_files(root):
        errors.append("frozen authority files are untracked or modified relative to HEAD")
    if _formal_result_paths(root):
        errors.append("formal EXP-020 result file exists")
    expected_status = {
        "EXP020_FORMAL_RUN_AUTHORIZED": False,
        "EXP020_SCIENTIFIC_STATUS": "NOT_STARTED",
        "FORMAL_FIT_EVAL_INFERENCE_PERFORMED": False,
        "FORMAL_SCIENTIFIC_RESULTS_CREATED": False,
    }
    for key, expected in expected_status.items():
        if spec.get(key) != expected:
            errors.append(f"specification status mismatch: {key}")
    model = config.get("model", {})
    fixed = spec.get("fixed_protocol", {})
    expected_fixed = {
        "model_id": model.get("model_id"), "revision": model.get("revision"), "canonical_path": model.get("canonical_path"),
        "local_files_only": model.get("local_files_only"), "execution_mode": model.get("execution_mode"),
        "dtype": model.get("dtype"), "device": model.get("device"), "config_sha256": model.get("config_sha256"),
    }
    for key, expected in expected_fixed.items():
        if fixed.get(key) != expected:
            errors.append(f"frozen model mismatch: {key}")
    primary = config.get("layer_indexing", {}).get("primary", {})
    secondary = config.get("layer_indexing", {}).get("secondary_descriptive", {})
    beta = config.get("beta", {})
    if fixed.get("primary") != {"block_index": primary.get("block_index"), "hidden_state_index": primary.get("hidden_states_index"), "beta": beta.get("primary")}:
        errors.append("primary block/index/beta mismatch")
    secondary_betas = beta.get("secondary_descriptive", [])
    secondary_beta = secondary_betas[0] if isinstance(secondary_betas, list) and len(secondary_betas) == 1 else None
    if fixed.get("secondary") != {"block_index": secondary.get("block_index"), "hidden_state_index": secondary.get("hidden_states_index"), "beta": secondary_beta, "descriptive_only": True}:
        errors.append("secondary block/index/beta mismatch")
    if fixed.get("conditions") != config.get("conditions"):
        errors.append("conditions mismatch")
    random = fixed.get("random_control", {})
    frozen_random = config.get("direction_construction", {}).get("random_control", {})
    if random.get("base_seed") != frozen_random.get("base_seed") or random.get("model_index") != frozen_random.get("model_index"):
        errors.append("matched-random frozen seed mismatch")
    bootstrap = fixed.get("bootstrap", {})
    statistics = config.get("statistics", {})
    if bootstrap.get("seed") != statistics.get("bootstrap_seed") or bootstrap.get("resamples") != statistics.get("bootstrap_resamples"):
        errors.append("bootstrap seed/resample mismatch")
    errors.extend(_validate_bootstrap_schema(bootstrap))
    semantics = spec.get("semantic_rules", {})
    extraction = semantics.get("representation", {})
    if extraction.get("status") != "RESOLVED" or extraction.get("value_classification") != "AUTHORITATIVE_RECOVERED_VALUE" or extraction.get("provenance_tag") != "RECOVERED_FROM_EXP018":
        errors.append("historical extraction provenance is not fully recovered")
    tokenizer = semantics.get("tokenizer_effective_defaults", {})
    if tokenizer.get("status") != "RESOLVED" or tokenizer.get("value_classification") != "AUTHORITATIVE_RECOVERED_VALUE" or tokenizer.get("provenance_tag") != "RECOVERED_FROM_FROZEN_RUNTIME":
        errors.append("effective tokenizer defaults are not recovered from frozen runtime")
    probability = semantics.get("probability_mapping", {})
    if probability.get("value_classification") != "IMPLEMENTATION_CORRECTNESS_REQUIREMENT" or probability.get("provenance_tag") != "IMPLEMENTATION_CORRECTNESS_REQUIREMENT":
        errors.append("probability mapping classification is incorrect")
    bootstrap_rule = semantics.get("statistics_bootstrap", {})
    if bootstrap_rule.get("value_classification") != "USER_APPROVED_PRE_OUTCOME_IMPLEMENTATION_SPEC" or bootstrap_rule.get("provenance_tag") != "USER_APPROVED_PRE_OUTCOME_IMPLEMENTATION_SPEC":
        errors.append("bootstrap provenance tag is incorrect")
    errors.extend(validate_readiness_fields(spec))
    prereg_ok, _ = _run_preregistration_validator(root)
    if not prereg_ok:
        errors.append("frozen preregistration validator failed")
    return not errors, errors, spec


def main() -> int:
    valid, errors, spec = validate_spec()
    if not valid:
        print("IMPLEMENTATION_SPEC_INTEGRITY_FAILURE")
        for error in errors:
            print(f"- {error}")
        return 2
    derived_primary = derive_unresolved_fields(spec, "UNRESOLVED_PRIMARY_CRITICAL")
    derived_secondary = derive_unresolved_fields(spec, "UNRESOLVED_SECONDARY")
    if derived_primary:
        print("IMPLEMENTATION_SPEC_BLOCKED_PENDING_USER_DECISION")
        print("PRIMARY_READY = false")
        print(f"SECONDARY_READY = {str(spec['SECONDARY_READY']).lower()}")
        print(f"FULL_READY = {str(spec['FULL_READY']).lower()}")
        return 1
    if not spec["PRIMARY_READY"] and not derived_primary:
        print("IMPLEMENTATION_SPEC_INTEGRITY_FAILURE")
        return 2
    if spec["PRIMARY_READY"] and not spec["SECONDARY_READY"] and derived_secondary:
        print("PRIMARY_SPEC_READY_SECONDARY_UNRESOLVED")
        return 0
    if spec["PRIMARY_READY"] and spec["SECONDARY_READY"] and spec["FULL_READY"] and not derived_primary and not derived_secondary and not spec.get("protocol_conflicts"):
        print("READY_FOR_EXP020_RUNNER_IMPLEMENTATION")
        return 0
    print("IMPLEMENTATION_SPEC_INTEGRITY_FAILURE")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
