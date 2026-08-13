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
SEMANTIC_RULE_SCHEMA_VERSION = "1.0.0"
REQUIRED_SEMANTIC_RULES = (
    "input_rendering", "tokenizer_invocation", "tokenizer_effective_defaults", "representation",
    "layer_mapping", "direction", "intervention", "matched_random", "opposite", "probe",
    "probability_mapping", "effects", "statistics_bootstrap", "secondary_direction",
)
REQUIRED_RULE_CLASSIFICATIONS = {
    "input_rendering": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "tokenizer_invocation": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "tokenizer_effective_defaults": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_FROZEN_RUNTIME"),
    "representation": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "layer_mapping": ("AUTHORITATIVE_RECOVERED_VALUE", "ALREADY_FROZEN_EXP020"),
    "direction": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "intervention": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "matched_random": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "opposite": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
    "probe": ("AUTHORITATIVE_RECOVERED_VALUE", "ALREADY_FROZEN_EXP020"),
    "probability_mapping": ("IMPLEMENTATION_CORRECTNESS_REQUIREMENT", "IMPLEMENTATION_CORRECTNESS_REQUIREMENT"),
    "effects": ("AUTHORITATIVE_RECOVERED_VALUE", "ALREADY_FROZEN_EXP020"),
    "statistics_bootstrap": ("USER_APPROVED_PRE_OUTCOME_IMPLEMENTATION_SPEC", "USER_APPROVED_PRE_OUTCOME_IMPLEMENTATION_SPEC"),
    "secondary_direction": ("AUTHORITATIVE_RECOVERED_VALUE", "RECOVERED_FROM_EXP018"),
}
CANONICAL_ORDER_SOURCE = {
    "authority": "experiments/exp020/exp020_frozen_config.json",
    "split_order": "dataset.splits sorted by split_index ascending",
    "cluster_order": "dataset.groups order then evaluation_ids[group] list order",
    "row_order": "dataset.ordered_transitions order filtered by source_group",
}


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


def validate_semantic_rule_registry(spec: dict[str, Any]) -> list[str]:
    """Require the versioned completeness registry and exact per-rule provenance."""
    errors: list[str] = []
    registry = spec.get("semantic_rule_registry", {})
    serialized = registry.get("required_rules")
    if registry.get("schema_version") != SEMANTIC_RULE_SCHEMA_VERSION:
        errors.append("semantic-rule registry schema version mismatch")
    if not isinstance(serialized, list) or tuple(serialized) != REQUIRED_SEMANTIC_RULES:
        errors.append("semantic-rule registry does not match canonical ordered registry")
    if isinstance(serialized, list) and len(serialized) != len(set(serialized)):
        errors.append("semantic-rule registry contains duplicate entries")
    rules = spec.get("semantic_rules", {})
    if set(rules) != set(REQUIRED_SEMANTIC_RULES):
        errors.append("semantic-rule keys do not exactly match required registry")
    for name in REQUIRED_SEMANTIC_RULES:
        rule = rules.get(name)
        if not isinstance(rule, dict):
            errors.append(f"required semantic rule missing: {name}")
            continue
        if rule.get("value") in (None, "", [], {}):
            errors.append(f"required semantic rule has empty value: {name}")
        if rule.get("status") != "RESOLVED":
            errors.append(f"required semantic rule is not resolved: {name}")
        expected_classification, expected_tag = REQUIRED_RULE_CLASSIFICATIONS[name]
        if rule.get("value_classification") != expected_classification or rule.get("provenance_tag") != expected_tag:
            errors.append(f"required semantic rule classification/provenance mismatch: {name}")
    return errors


def _validate_bootstrap_schema(bootstrap: dict[str, Any], dataset: dict[str, Any]) -> list[str]:
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
    if bootstrap.get("canonical_order_source") != CANONICAL_ORDER_SOURCE:
        errors.append("bootstrap schema mismatch: canonical ordering source")
    try:
        canonical_manifest(dataset)
    except ValueError as exc:
        errors.append(f"frozen dataset manifest cannot derive canonical ordering: {exc}")
    return errors


def canonical_manifest(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """Derive split, cluster, and row order solely from frozen-manifest metadata."""
    groups = manifest.get("groups")
    splits = manifest.get("splits")
    transitions = manifest.get("ordered_transitions")
    if not isinstance(groups, list) or not groups or len(groups) != len(set(groups)):
        raise ValueError("Manifest groups must be nonempty and unique.")
    if not isinstance(splits, list) or len(splits) != 2:
        raise ValueError("Manifest must contain exactly two split strata.")
    indices = [split.get("split_index") for split in splits]
    if sorted(indices) != [0, 1]:
        raise ValueError("Manifest split indices must be the unique frozen values 0 and 1.")
    if not isinstance(transitions, list):
        raise ValueError("Manifest ordered transitions are required.")
    result: list[dict[str, Any]] = []
    for split in sorted(splits, key=lambda item: item["split_index"]):
        evaluation_ids = split.get("evaluation_ids", {})
        if set(evaluation_ids) != set(groups):
            raise ValueError("Manifest evaluation IDs must cover exactly the frozen groups.")
        for source_group in groups:
            target_groups = [target for source, target in transitions if source == source_group]
            if len(target_groups) != 3 or len(set(target_groups)) != 3:
                raise ValueError("Each frozen source group must have exactly three ordered targets.")
            for source_id in evaluation_ids[source_group]:
                result.append({"split_id": split["id"], "split_index": split["split_index"], "source_group": source_group, "held_out_source_item_id": source_id, "target_groups": target_groups})
    if len(result) != 24 or any(sum(item["split_id"] == split["id"] for item in result) != 12 for split in splits):
        raise ValueError("Manifest must derive exactly 12 clusters per split and 24 total.")
    keys = [(item["split_id"], item["held_out_source_item_id"]) for item in result]
    if len(keys) != len(set(keys)):
        raise ValueError("Manifest contains duplicate canonical source-item cluster keys.")
    return result


def canonicalize_clusters(clusters_by_split: dict[str, dict[str, list[dict[str, Any]]]], manifest: dict[str, Any]) -> dict[str, list[list[dict[str, Any]]]]:
    """Validate and reorder arbitrary caller containers into frozen manifest order."""
    import numpy as np

    canonical = canonical_manifest(manifest)
    expected_by_split: dict[str, list[dict[str, Any]]] = {}
    for item in canonical:
        expected_by_split.setdefault(item["split_id"], []).append(item)
    if set(clusters_by_split) != set(expected_by_split):
        raise ValueError("Caller split keys do not exactly match canonical manifest splits.")
    result: dict[str, list[list[dict[str, Any]]]] = {}
    for split_id, expected_clusters in expected_by_split.items():
        caller_clusters = clusters_by_split[split_id]
        expected_ids = [item["held_out_source_item_id"] for item in expected_clusters]
        if set(caller_clusters) != set(expected_ids) or len(caller_clusters) != 12:
            raise ValueError("Caller cluster keys do not exactly match canonical manifest source IDs.")
        ordered_clusters: list[list[dict[str, Any]]] = []
        for expected in expected_clusters:
            source_id = expected["held_out_source_item_id"]
            rows = list(caller_clusters[source_id])
            if len(rows) != 3:
                raise ValueError("Each cluster must contain exactly three transition rows.")
            observed_targets: list[str] = []
            for row in rows:
                if row.get("split_id") != split_id:
                    raise ValueError("Outer split key must match every contained row split_id.")
                if row.get("held_out_source_item_id") != source_id:
                    raise ValueError("Cluster key must match every contained row source ID.")
                if row.get("source_group") != expected["source_group"]:
                    raise ValueError("Cluster row source group conflicts with frozen manifest.")
                observed_targets.append(row.get("target_group"))
                for outcome in ("task_effect", "D_random", "D_opposite"):
                    if not np.isfinite(row.get(outcome, np.nan)):
                        raise ValueError("Nonfinite observed value is technical invalidity.")
            if set(observed_targets) != set(expected["target_groups"]) or len(set(observed_targets)) != 3:
                raise ValueError("Cluster target transitions do not exactly match the frozen manifest.")
            by_target = {row["target_group"]: row for row in rows}
            ordered_clusters.append([by_target[target] for target in expected["target_groups"]])
        result[split_id] = ordered_clusters
    return result


def validate_cluster_structure(clusters_by_split: dict[str, dict[str, list[dict[str, Any]]]], manifest: dict[str, Any]) -> None:
    """Validate the approved two-stratum, twelve-cluster, three-row design."""
    canonicalize_clusters(clusters_by_split, manifest)


def cluster_resample_plan(clusters_by_split: dict[str, dict[str, list[dict[str, Any]]]], manifest: dict[str, Any], *, seed: int, resamples: int) -> list[dict[str, list[int]]]:
    """Create the approved shared PCG64 plan, preserving supplied split/cluster order."""
    import numpy as np

    canonical = canonicalize_clusters(clusters_by_split, manifest)
    split_ids = list(canonical)
    rng = np.random.Generator(np.random.PCG64(seed))
    return [{split_id: rng.integers(0, 12, size=12).tolist() for split_id in split_ids} for _ in range(resamples)]


def sampled_transition_rows(clusters_by_split: dict[str, dict[str, list[dict[str, Any]]]], manifest: dict[str, Any], replicate: dict[str, list[int]]) -> list[dict[str, Any]]:
    """Expand one shared cluster plan without separating any three-row cluster."""
    canonical = canonicalize_clusters(clusters_by_split, manifest)
    rows: list[dict[str, Any]] = []
    for split_id, indices in replicate.items():
        for index in indices:
            rows.extend(canonical[split_id][index])
    if len(rows) != 72:
        raise ValueError("Each bootstrap replicate must contain exactly 72 transition-item rows.")
    return rows


def bootstrap_cluster_statistics(clusters_by_split: dict[str, dict[str, list[dict[str, Any]]]], manifest: dict[str, Any], *, seed: int = 20260812, resamples: int = 10000) -> dict[str, Any]:
    """Compute synthetic-only approved cluster-bootstrap means and percentile CIs."""
    import numpy as np

    plan = cluster_resample_plan(clusters_by_split, manifest, seed=seed, resamples=resamples)
    outcomes = ("task_effect", "D_random", "D_opposite")
    means = {outcome: [] for outcome in outcomes}
    for replicate in plan:
        values = {outcome: [] for outcome in outcomes}
        for row in sampled_transition_rows(clusters_by_split, manifest, replicate):
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
    errors.extend(_validate_bootstrap_schema(bootstrap, config.get("dataset", {})))
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
    errors.extend(validate_semantic_rule_registry(spec))
    errors.extend(validate_readiness_fields(spec))
    if spec.get("protocol_conflicts") != []:
        errors.append("protocol conflicts must be empty for readiness")
    if spec.get("PRIMARY_READY") and spec.get("SECONDARY_READY") and spec.get("FULL_READY") and spec.get("final_task_status") != "READY_FOR_EXP020_RUNNER_IMPLEMENTATION":
        errors.append("final task status does not match fully resolved readiness")
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
