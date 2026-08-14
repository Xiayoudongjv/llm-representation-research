"""Validate an EXP-020A cloud-migration manifest without loading a model.

The validator deliberately operates at file, JSON-schema, identifier, and count
levels.  It never prints or copies controlled prompt text, and it never imports
the formal EXP-020A runner.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0.0"
FORMAL_STATUS = "CLOUD_MIGRATION_SOURCE_PREFLIGHT_READY"
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "manifest_identity",
    "git_binding",
    "source_roots",
    "authority_artifacts",
    "execution_critical_repository_artifacts",
    "formal_input_artifacts",
    "model_snapshot",
    "prior_consumed_authorization",
    "intended_cloud_target",
    "target_bindings",
    "source_side_readiness",
    "target_side_readiness",
    "prohibited_operations",
}
ARTIFACT_FIELDS = {
    "logical_role",
    "relative_path",
    "sha256",
    "size_bytes",
    "required",
    "provenance_class",
    "content_access_level",
}
REPOSITORY_ARTIFACT_FIELDS = ARTIFACT_FIELDS | {"git_blob_sha256", "git_blob_size_bytes"}
FORMAL_FIELDS = ARTIFACT_FIELDS | {"schema_summary"}
MANIFEST_IDENTITY_FIELDS = {"experiment", "manifest_type", "schema_version"}
GIT_BINDING_FIELDS = {
    "schema_version", "execution_base_commit", "binding_policy", "allowed_migration_paths",
    "source_draft_requirements", "archived_checkout_requirements", "observed_checkout_commit_policy",
    "target_checkout_policy",
}
TARGET_CHECKOUT_POLICY_FIELDS = {
    "schema_version", "target_operating_system", "core_autocrlf", "core_eol",
    "configuration_applied_before_checkout", "checkout_mode", "floating_branch_prohibited",
}
SOURCE_DRAFT_REQUIREMENT_FIELDS = {
    "live_head_equals_execution_base", "migration_paths_untracked", "tracked_worktree_clean",
    "staging_empty", "no_unexpected_untracked_files",
}
ARCHIVED_REQUIREMENT_FIELDS = {
    "live_head_strict_descendant", "exact_committed_delta", "tracked_worktree_clean",
    "staging_empty", "no_unexpected_untracked_files",
}
SOURCE_ROOT_FIELDS = {"repository_root", "model_snapshot_root"}
TARGET_BINDING_FIELDS = {
    "repository_root", "model_snapshot_root", "persistent_root", "transfer_mode", "path_relocation_only"
}
CLOUD_TARGET_FIELDS = {"provider_class", "region", "hardware", "container"}
HARDWARE_FIELDS = {
    "node_count", "gpu_count", "requested_gpu", "requested_vram_gb", "requested_cpu_cores",
    "requested_host_memory_gb", "scaling_mode", "multi_container", "preemptible",
    "persistent_volume_gb", "persistent_mount", "provenance_class", "hardware_verified",
}
CONTAINER_FIELDS = {
    "image_repository", "image_tag", "expected_platform", "expected_image_manifest_digest",
    "provenance_class", "source_registry_resolution_verified", "actual_target_image_digest",
    "target_image_verified",
}
MODEL_SNAPSHOT_FIELDS = {"identity", "required_model_files", "required_tokenizer_files", "index_summary"}
MODEL_IDENTITY_FIELDS = {"model_id", "revision", "architecture", "model_type", "transformer_blocks", "hidden_size", "dtype"}
INDEX_SUMMARY_FIELDS = {"tensor_count", "raw_tensor_bytes", "index_sha256"}
AUTHORIZATION_FIELDS = {"authorization", "consumption_record", "single_use", "state", "reusable"}
SOURCE_READINESS_FIELDS = {"source_preflight_complete", "formal_run_authorized", "formal_results_created"}
TARGET_READINESS_FIELDS = {"transfer_verified", "cloud_runtime_verified", "cloud_target_qualified", "formal_run_authorized", "formal_results_created"}
PROHIBITED_OPERATION_FIELDS = {"cloud_created", "artifacts_uploaded", "model_loaded", "gpu_used", "formal_run_authorized", "formal_results_created"}
PROMPT_SCHEMA_FIELDS = {"top_level_type", "item_fields", "record_count", "id_count", "group_count"}
CONDITION_SCHEMA_FIELDS = {"top_level_type", "record_count", "id_count", "split_count", "split_membership_count", "transition_count", "condition_count", "beta_count"}
EXPECTED_EXECUTION_ROLES = (
    "frozen_config",
    "preregistration",
    "preregistration_validator",
    "implementation_specification",
    "implementation_spec_json",
    "implementation_spec_validator",
    "formal_runner",
    "runner_tests",
    "implementation_spec_tests",
    "extraction_utilities",
    "model_loader_utilities",
)
EXPECTED_FORMAL_ROLES = ("controlled_prompts", "validation_conditions")
EXPECTED_MODEL_ROLES = (
    "model_config",
    "generation_config",
    "model_index",
    "model_shard_1",
    "model_shard_2",
    "model_shard_3",
)
EXPECTED_TOKENIZER_ROLES = (
    "tokenizer_config",
    "tokenizer_json",
    "tokenizer_vocab",
    "tokenizer_merges",
)
EXPECTED_MIGRATION_PATHS = (
    ".gitignore",
    "experiments/exp020/archive/consumed_authorizations/exp020_formal_run_authorization.json",
    "experiments/exp020/cloud_migration_manifest.json",
    "experiments/exp020/exp020_formal_run_authorization.json",
    "experiments/exp020/prepare_cloud_runtime.py",
    "experiments/exp020/validate_cloud_migration_manifest.py",
    "tests/test_exp020_cloud_migration_manifest.py",
    "tests/test_exp020_cloud_runtime.py",
)
EXECUTION_BASE_COMMIT = "c830d0b6b8181d287306480317b1c66315ff13f9"
ARCHIVED_AUTHORIZATION_FIELDS = REPOSITORY_ARTIFACT_FIELDS | {
    "git_blob_relative_path",
    "original_operational_crlf_sha256",
    "original_operational_crlf_size_bytes",
}


class ManifestValidationError(ValueError):
    """Raised when a migration package is incomplete or inconsistent."""


def sha256_file(path: Path) -> str:
    """Return a streaming SHA-256 digest without loading a whole file in memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_keys(value: dict[str, Any], expected: set[str], name: str) -> None:
    if not isinstance(value, dict):
        raise ManifestValidationError(f"{name} must be an object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise ManifestValidationError(f"{name} fields mismatch; missing={missing}, unknown={unknown}")


def _require_non_empty_string(value: Any, name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ManifestValidationError(f"{name} must be a non-empty string")


def _require_exact_values(value: dict[str, Any], expected: dict[str, Any], name: str) -> None:
    _require_keys(value, set(expected), name)
    for key, wanted in expected.items():
        if value[key] != wanted:
            raise ManifestValidationError(f"{name}.{key} does not match the frozen value")


def _relative_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ManifestValidationError("artifact paths must be relative and may not traverse parents")
    candidate = root / path
    try:
        resolved_root = root.resolve(strict=True)
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise ManifestValidationError(f"required artifact is missing: {relative}") from error
    if not resolved.is_relative_to(resolved_root):
        raise ManifestValidationError("artifact path resolves outside its declared root")
    if not resolved.is_file():
        raise ManifestValidationError(f"artifact is not a regular file: {relative}")
    return resolved


def _validate_artifact_metadata(
    artifact: dict[str, Any], root: Path, *, formal: bool = False, repository: bool = False,
) -> Path:
    """Validate artifact metadata and resolve its path without comparing bytes."""
    expected = (REPOSITORY_ARTIFACT_FIELDS | {"schema_summary"}) if formal and repository else (
        REPOSITORY_ARTIFACT_FIELDS if repository else (FORMAL_FIELDS if formal else ARTIFACT_FIELDS)
    )
    _require_keys(artifact, expected, "repository artifact" if repository else "artifact")
    for field in ("logical_role", "relative_path", "sha256", "provenance_class", "content_access_level"):
        _require_non_empty_string(artifact[field], f"artifact.{field}")
    if len(artifact["sha256"]) != 64 or any(char not in "0123456789abcdef" for char in artifact["sha256"]):
        raise ManifestValidationError("artifact.sha256 must be a lowercase SHA-256 digest")
    if artifact["required"] is not True:
        raise ManifestValidationError("all migration artifacts must be marked required")
    if artifact["content_access_level"] not in {"LEVEL_0_FILE_IDENTITY", "LEVEL_1_SCHEMA_IDS_COUNTS"}:
        raise ManifestValidationError("unsupported content access level")
    if not isinstance(artifact["size_bytes"], int) or artifact["size_bytes"] < 0:
        raise ManifestValidationError("artifact size_bytes must be a non-negative integer")
    return _relative_path(root, artifact["relative_path"])


def _validate_artifact(
    artifact: dict[str, Any], root: Path, *, formal: bool = False
) -> Path:
    path = _validate_artifact_metadata(artifact, root, formal=formal)
    if path.stat().st_size != artifact["size_bytes"]:
        raise ManifestValidationError(f"artifact size mismatch: {artifact['relative_path']}")
    if sha256_file(path) != artifact["sha256"]:
        raise ManifestValidationError(f"artifact hash mismatch: {artifact['relative_path']}")
    return path


def _validate_repository_artifact(
    artifact: dict[str, Any], repo_root: Path, *, formal: bool = False,
    execution_base_commit: str, validate_source_worktree: bool = True,
    verify_target_worktree: bool = False, git_blob_relative_path: str | None = None,
) -> Path:
    """Validate source bytes and frozen Git-blob bytes without exposing contents."""
    path = _validate_artifact_metadata(artifact, repo_root, formal=formal, repository=True)
    _require_non_empty_string(artifact["git_blob_sha256"], "repository artifact.git_blob_sha256")
    if len(artifact["git_blob_sha256"]) != 64 or any(char not in "0123456789abcdef" for char in artifact["git_blob_sha256"]):
        raise ManifestValidationError("repository artifact.git_blob_sha256 must be a lowercase SHA-256 digest")
    if not isinstance(artifact["git_blob_size_bytes"], int) or artifact["git_blob_size_bytes"] < 0:
        raise ManifestValidationError("repository artifact.git_blob_size_bytes must be a non-negative integer")
    if validate_source_worktree:
        if path.stat().st_size != artifact["size_bytes"]:
            raise ManifestValidationError(f"artifact size mismatch: {artifact['relative_path']}")
        if sha256_file(path) != artifact["sha256"]:
            raise ManifestValidationError(f"artifact hash mismatch: {artifact['relative_path']}")
    blob_relative_path = git_blob_relative_path or artifact["relative_path"]
    if Path(blob_relative_path).is_absolute() or ".." in Path(blob_relative_path).parts:
        raise ManifestValidationError("repository artifact Git-blob path is not normalized")
    blob = subprocess.run(
        ["git", "show", f"{execution_base_commit}:{blob_relative_path}"],
        cwd=repo_root, capture_output=True, check=False,
    )
    if blob.returncode:
        raise ManifestValidationError("repository artifact is unavailable from execution-base Git object")
    if len(blob.stdout) != artifact["git_blob_size_bytes"]:
        raise ManifestValidationError(f"repository artifact Git-blob size mismatch: {artifact['relative_path']}")
    if hashlib.sha256(blob.stdout).hexdigest() != artifact["git_blob_sha256"]:
        raise ManifestValidationError(f"repository artifact Git-blob hash mismatch: {artifact['relative_path']}")
    if verify_target_worktree:
        data = path.read_bytes()
        if len(data) != artifact["git_blob_size_bytes"] or hashlib.sha256(data).hexdigest() != artifact["git_blob_sha256"]:
            raise ManifestValidationError(f"target checkout artifact bytes do not match execution-base Git blob: {artifact['relative_path']}")
    return path


def _validate_registry(
    entries: list[dict[str, Any]],
    root: Path,
    expected_roles: tuple[str, ...],
    name: str,
    *,
    formal: bool = False, repository: bool = False, execution_base_commit: str | None = None,
    validate_source_worktree: bool = True,
    verify_target_worktree: bool = False,
) -> list[Path]:
    if not isinstance(entries, list):
        raise ManifestValidationError(f"{name} must be a list")
    roles = [entry.get("logical_role") for entry in entries]
    if len(set(roles)) != len(roles):
        raise ManifestValidationError(f"{name} contains duplicate logical roles")
    if tuple(roles) != expected_roles:
        raise ManifestValidationError(f"{name} has an unexpected role set or ordering")
    paths = [entry.get("relative_path") for entry in entries]
    if len(set(paths)) != len(paths):
        raise ManifestValidationError(f"{name} contains duplicate artifact paths")
    lowered = [str(path).lower() for path in paths]
    if len(set(lowered)) != len(lowered):
        raise ManifestValidationError(f"{name} contains case-colliding paths")
    if repository:
        if execution_base_commit is None:
            raise ManifestValidationError("repository registry validation requires an execution-base commit")
        return [
            _validate_repository_artifact(
                entry, root, formal=formal, execution_base_commit=execution_base_commit,
                validate_source_worktree=validate_source_worktree,
                verify_target_worktree=verify_target_worktree,
            ) for entry in entries
        ]
    return [_validate_artifact(entry, root, formal=formal) for entry in entries]


def _validate_formal_inputs(
    entries: list[dict[str, Any]], root: Path, *, execution_base_commit: str,
    validate_source_worktree: bool, verify_target_worktree: bool,
) -> None:
    paths = _validate_registry(
        entries, root, EXPECTED_FORMAL_ROLES, "formal_input_artifacts", formal=True,
        repository=True, execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree,
        verify_target_worktree=verify_target_worktree,
    )
    prompts_path, conditions_path = paths
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    conditions = json.loads(conditions_path.read_text(encoding="utf-8"))
    prompts_summary = entries[0]["schema_summary"]
    conditions_summary = entries[1]["schema_summary"]
    _require_keys(prompts_summary, PROMPT_SCHEMA_FIELDS, "controlled prompt schema summary")
    _require_keys(conditions_summary, CONDITION_SCHEMA_FIELDS, "validation conditions schema summary")
    if not isinstance(prompts, list) or len(prompts) != prompts_summary["record_count"]:
        raise ManifestValidationError("controlled prompt record count does not match manifest")
    required_prompt_keys = {"id", "group", "text", "variant_type"}
    if any(set(row) != required_prompt_keys for row in prompts):
        raise ManifestValidationError("controlled prompt schema is incompatible")
    prompt_ids = [row["id"] for row in prompts]
    if len(set(prompt_ids)) != len(prompt_ids) or len(prompt_ids) != prompts_summary["id_count"]:
        raise ManifestValidationError("controlled prompt identifiers are not unique or counts disagree")
    if not isinstance(conditions, dict) or not isinstance(conditions.get("splits"), list):
        raise ManifestValidationError("validation conditions schema is incompatible")
    transitions = conditions.get("ordered_transitions")
    if not isinstance(transitions, list) or len(transitions) != conditions_summary["transition_count"]:
        raise ManifestValidationError("ordered transition count does not match manifest")
    split_count = 0
    split_memberships = 0
    for split in conditions["splits"]:
        if set(split) != {"id", "split_index", "fit_ids", "evaluation_ids"}:
            raise ManifestValidationError("split schema is incompatible")
        for key in ("fit_ids", "evaluation_ids"):
            group_mapping = split[key]
            if not isinstance(group_mapping, dict):
                raise ManifestValidationError("split ID groups must be mappings")
            values = [item for ids in group_mapping.values() for item in ids]
            if len(values) != len(set(values)):
                raise ManifestValidationError("split contains duplicate identifiers")
            split_memberships += len(values)
        split_count += 1
    if split_count != conditions_summary["split_count"]:
        raise ManifestValidationError("split count does not match manifest")
    if split_memberships != conditions_summary["split_membership_count"]:
        raise ManifestValidationError("split membership count does not match manifest")


def _validate_model_snapshot(snapshot: dict[str, Any], model_root: Path) -> None:
    _require_keys(snapshot, MODEL_SNAPSHOT_FIELDS, "model_snapshot")
    _require_exact_values(snapshot["identity"], {
        "model_id": "Qwen/Qwen3-4B",
        "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
        "architecture": "Qwen3ForCausalLM",
        "model_type": "qwen3",
        "transformer_blocks": 36,
        "hidden_size": 2560,
        "dtype": "bfloat16",
    }, "model_snapshot.identity")
    _validate_registry(snapshot["required_model_files"], model_root, EXPECTED_MODEL_ROLES, "required_model_files")
    _validate_registry(snapshot["required_tokenizer_files"], model_root, EXPECTED_TOKENIZER_ROLES, "required_tokenIZER_files")
    index_entry = snapshot["required_model_files"][2]
    index = json.loads(_relative_path(model_root, index_entry["relative_path"]).read_text(encoding="utf-8"))
    if set(index) != {"metadata", "weight_map"} or not isinstance(index["weight_map"], dict):
        raise ManifestValidationError("model index schema is incompatible")
    index_summary = snapshot["index_summary"]
    _require_keys(index_summary, INDEX_SUMMARY_FIELDS, "model_snapshot.index_summary")
    if len(index["weight_map"]) != index_summary["tensor_count"]:
        raise ManifestValidationError("model index tensor count does not match manifest")
    if index.get("metadata", {}).get("total_size") != index_summary["raw_tensor_bytes"]:
        raise ManifestValidationError("model index raw tensor size does not match manifest")
    shards = {entry["relative_path"] for entry in snapshot["required_model_files"][3:]}
    mapped = set(index["weight_map"].values())
    if not mapped.issubset(shards):
        raise ManifestValidationError("model index references an unregistered shard")
    if mapped != shards:
        raise ManifestValidationError("one or more registered model shards are unused by the index")


def _git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ManifestValidationError("repository git HEAD cannot be resolved")
    return result.stdout.strip()


def _git_output(repo_root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if result.returncode:
        raise ManifestValidationError("repository Git lifecycle check failed")
    return result.stdout.replace("\\", "/").strip()


def _validate_git_binding_schema(
    binding: dict[str, Any], *, expected_execution_base: str = EXECUTION_BASE_COMMIT
) -> None:
    """Validate the frozen base and exact, ordered migration-only path registry."""
    _require_exact_values(binding, {
        "schema_version": "1.0.0",
        "execution_base_commit": expected_execution_base,
        "binding_policy": "EXACT_TASK_085D_CORRECTION_ONLY_DESCENDANT",
        "allowed_migration_paths": list(EXPECTED_MIGRATION_PATHS),
        "source_draft_requirements": {
            "live_head_equals_execution_base": True,
            "migration_paths_untracked": True,
            "tracked_worktree_clean": True,
            "staging_empty": True,
            "no_unexpected_untracked_files": True,
        },
        "archived_checkout_requirements": {
            "live_head_strict_descendant": True,
            "exact_committed_delta": True,
            "tracked_worktree_clean": True,
            "staging_empty": True,
            "no_unexpected_untracked_files": True,
        },
        "observed_checkout_commit_policy": "OBSERVE_LIVE_HEAD_ONLY_NOT_SERIALIZED",
        "target_checkout_policy": {
            "schema_version": "1.0.0",
            "target_operating_system": "Linux",
            "core_autocrlf": False,
            "core_eol": "lf",
            "configuration_applied_before_checkout": True,
            "checkout_mode": "DETACHED_EXACT_COMMIT",
            "floating_branch_prohibited": True,
        },
    }, "git_binding")
    for relative in binding["allowed_migration_paths"]:
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise ManifestValidationError("git_binding allowed migration path is not normalized")


def _git_status_lines(repo_root: Path) -> list[str]:
    text = _git_output(repo_root, "status", "--porcelain=v1", "--untracked-files=all")
    return text.splitlines() if text else []


def _validate_target_checkout_environment(repo_root: Path, binding: dict[str, Any]) -> None:
    """Require the frozen Linux EOL configuration before target-side validation."""
    _require_exact_values(binding["target_checkout_policy"], {
        "schema_version": "1.0.0",
        "target_operating_system": "Linux",
        "core_autocrlf": False,
        "core_eol": "lf",
        "configuration_applied_before_checkout": True,
        "checkout_mode": "DETACHED_EXACT_COMMIT",
        "floating_branch_prohibited": True,
    }, "git_binding.target_checkout_policy")
    autocrlf = _git_output(repo_root, "config", "--local", "--get", "core.autocrlf")
    eol = _git_output(repo_root, "config", "--local", "--get", "core.eol")
    if autocrlf.lower() != "false" or eol.lower() != "lf":
        raise ManifestValidationError("target checkout Git EOL configuration does not match frozen policy")
    symbolic_head = subprocess.run(
        ["git", "symbolic-ref", "-q", "HEAD"], cwd=repo_root, capture_output=True, text=True, check=False
    )
    if symbolic_head.returncode == 0:
        raise ManifestValidationError("target checkout must use a detached exact commit")


def _validate_git_binding(
    binding: dict[str, Any], repo_root: Path, mode: str, *, check_git: bool,
    expected_execution_base: str = EXECUTION_BASE_COMMIT,
) -> str | None:
    """Validate the explicit source-draft or archived-checkout lifecycle mode."""
    _validate_git_binding_schema(binding, expected_execution_base=expected_execution_base)
    if mode not in {"source-draft", "archived-checkout"}:
        raise ManifestValidationError("validation mode must be source-draft or archived-checkout")
    if not check_git:
        return None
    base = binding["execution_base_commit"]
    head = _git_head(repo_root)
    status = _git_status_lines(repo_root)
    staged = [line for line in status if not line.startswith("?? ")]
    untracked = [line[3:] for line in status if line.startswith("?? ")]
    if staged:
        raise ManifestValidationError("repository has staged or tracked worktree changes")
    if mode == "source-draft":
        if head != base:
            raise ManifestValidationError("source-draft live HEAD does not equal execution base")
        if tuple(untracked) != tuple(binding["allowed_migration_paths"]):
            raise ManifestValidationError("source-draft untracked migration paths do not equal the frozen registry")
        return None
    if head == base:
        raise ManifestValidationError("archived-checkout HEAD must be a strict descendant of execution base")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", base, "HEAD"], cwd=repo_root, check=False
    )
    if ancestor.returncode:
        raise ManifestValidationError("execution base is not an ancestor of archived checkout HEAD")
    if untracked:
        raise ManifestValidationError("archived-checkout has unexpected untracked files")
    delta = _git_output(repo_root, "diff", "--no-renames", "--name-only", f"{base}..HEAD")
    delta_paths = tuple(line for line in delta.splitlines() if line)
    if delta_paths != tuple(binding["allowed_migration_paths"]):
        raise ManifestValidationError("archived-checkout committed delta does not equal the frozen migration registry")
    return head


def _validate_global_repository_registry_uniqueness(manifest: dict[str, Any]) -> None:
    """Reject ambiguous roles or paths across all repository-root registries."""
    entries = [
        *manifest["authority_artifacts"],
        *manifest["execution_critical_repository_artifacts"],
        *manifest["formal_input_artifacts"],
        manifest["prior_consumed_authorization"]["authorization"],
        manifest["prior_consumed_authorization"]["consumption_record"],
    ]
    roles = [entry["logical_role"] for entry in entries]
    paths = [entry["relative_path"] for entry in entries]
    if len(set(roles)) != len(roles):
        raise ManifestValidationError("repository registries contain duplicate logical roles")
    if len(set(paths)) != len(paths):
        raise ManifestValidationError("repository registries contain duplicate paths")
    if len({path.lower() for path in paths}) != len(paths):
        raise ManifestValidationError("repository registries contain case-colliding paths")


def _validate_no_formal_results(repo_root: Path) -> None:
    prohibited = [
        repo_root / "experiments/exp020/results/exp020a_results.json",
        repo_root / "results/exp020",
    ]
    engineering = repo_root / "experiments/exp020/results"
    legacy = (
        "transition_metrics.csv", "probe_metrics.csv", "invariant_metrics.csv", "pair_summary.csv",
        "representation_summary.json", "validation_summary.json", "behavioral_outputs.csv",
        "effect_rows.json", "probe_rows.json", "transition_rows.json", "pair_rows.json",
    )
    prohibited.extend(engineering / name for name in legacy)
    if any(path.exists() for path in prohibited):
        raise ManifestValidationError("canonical, staging, or legacy formal scientific result exists")
    if any(engineering.glob("exp020a_results.json.tmp-*")):
        raise ManifestValidationError("formal scientific result staging file exists")


def _validate_authorization(
    auth: dict[str, Any], repo_root: Path, *, execution_base_commit: str,
    validate_source_worktree: bool, verify_target_worktree: bool,
) -> None:
    """Verify only the non-reusable provenance of the prior authorization."""
    _require_keys(auth, AUTHORIZATION_FIELDS, "prior_consumed_authorization")
    archived = auth["authorization"]
    _require_keys(archived, ARCHIVED_AUTHORIZATION_FIELDS, "archived authorization artifact")
    for field in ("git_blob_relative_path", "original_operational_crlf_sha256"):
        _require_non_empty_string(archived[field], f"archived authorization artifact.{field}")
    if len(archived["original_operational_crlf_sha256"]) != 64 or any(
        char not in "0123456789abcdef" for char in archived["original_operational_crlf_sha256"]
    ):
        raise ManifestValidationError("archived authorization original CRLF hash must be a lowercase SHA-256 digest")
    if archived["git_blob_relative_path"] != "experiments/exp020/exp020_formal_run_authorization.json":
        raise ManifestValidationError("archived authorization must bind to the historical active-slot Git blob")
    if archived["original_operational_crlf_size_bytes"] != 1677:
        raise ManifestValidationError("archived authorization original CRLF size does not match the incident record")
    _validate_repository_artifact(
        {field: archived[field] for field in REPOSITORY_ARTIFACT_FIELDS},
        repo_root, execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree,
        verify_target_worktree=verify_target_worktree,
        git_blob_relative_path=archived["git_blob_relative_path"],
    )
    archived_bytes = _relative_path(repo_root, archived["relative_path"]).read_bytes()
    if archived_bytes.count(b"\r\n") or archived_bytes.count(b"\n") != 30:
        raise ManifestValidationError("archived authorization is not the expected LF incident artifact")
    if hashlib.sha256(archived_bytes.replace(b"\n", b"\r\n")).hexdigest() != archived["original_operational_crlf_sha256"]:
        raise ManifestValidationError("archived authorization CRLF reconstruction does not match the incident record")
    _validate_repository_artifact(
        auth["consumption_record"], repo_root, execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree,
        verify_target_worktree=verify_target_worktree,
    )
    if auth["single_use"] is not True or auth["state"] != "consumed" or auth["reusable"] is not False:
        raise ManifestValidationError("prior authorization is not recorded as consumed and non-reusable")


def _validate_readiness(source: dict[str, Any], target: dict[str, Any]) -> None:
    """Keep the source preflight separate from any target runtime authority."""
    _require_exact_values(source, {
        "source_preflight_complete": True,
        "formal_run_authorized": False,
        "formal_results_created": False,
    }, "source_side_readiness")
    _require_exact_values(target, {
        "transfer_verified": False,
        "cloud_runtime_verified": False,
        "cloud_target_qualified": False,
        "formal_run_authorized": False,
        "formal_results_created": False,
    }, "target_side_readiness")


def _validate_cloud_target(cloud: dict[str, Any]) -> None:
    """Reject outcome claims about hardware or a container not yet used here."""
    _require_keys(cloud, CLOUD_TARGET_FIELDS, "intended_cloud_target")
    _require_non_empty_string(cloud["region"], "intended_cloud_target.region")
    if cloud["provider_class"] != "DOMESTIC_CONTAINER_GPU_SERVICE":
        raise ManifestValidationError("intended_cloud_target.provider_class does not match the frozen value")
    _require_exact_values(cloud["hardware"], {
        "node_count": 1,
        "gpu_count": 1,
        "requested_gpu": "NVIDIA GeForce RTX 5090",
        "requested_vram_gb": 32,
        "requested_cpu_cores": 26,
        "requested_host_memory_gb": 63,
        "scaling_mode": "MANUAL",
        "multi_container": False,
        "preemptible": False,
        "persistent_volume_gb": 100,
        "persistent_mount": "/workspace/persist",
        "provenance_class": "USER_SELECTED_PRE_OUTCOME_ENGINEERING_TARGET",
        "hardware_verified": False,
    }, "intended_cloud_target.hardware")
    _require_exact_values(cloud["container"], {
        "image_repository": "pytorch/pytorch",
        "image_tag": "2.12.1-cuda13.0-cudnn9-devel",
        "expected_platform": "linux/amd64",
        "expected_image_manifest_digest": "sha256:ac63aaae09996612bdaf12bbf6d5fe840af6bed3100d6dc15fcb5fd1f4f957c4",
        "provenance_class": "EXPECTED_TARGET_IMAGE_IDENTITY",
        "source_registry_resolution_verified": False,
        "actual_target_image_digest": None,
        "target_image_verified": False,
    }, "intended_cloud_target.container")


def _validate_source_bindings(manifest: dict[str, Any]) -> None:
    """Validate explicit source and target roots without equating Windows and Linux paths."""
    _require_keys(manifest["source_roots"], SOURCE_ROOT_FIELDS, "source_roots")
    for key in SOURCE_ROOT_FIELDS:
        _require_non_empty_string(manifest["source_roots"][key], f"source_roots.{key}")
    _require_exact_values(manifest["target_bindings"], {
        "repository_root": "/workspace/persist/llm-representation-research",
        "model_snapshot_root": "/workspace/persist/models/qwen3-4b",
        "persistent_root": "/workspace/persist",
        "transfer_mode": "MANUAL_VERIFIED_COPY_REQUIRED",
        "path_relocation_only": True,
    }, "target_bindings")


def validate_manifest(
    manifest: dict[str, Any], repo_root: Path, model_root: Path, mode: str, *, check_git: bool = True,
    verify_target_checkout: bool = False,
) -> str | None:
    """Validate a manifest and its declared source or transferred artifacts."""
    _require_keys(manifest, REQUIRED_TOP_LEVEL, "manifest")
    if manifest["schema_version"] != SCHEMA_VERSION:
        raise ManifestValidationError("unsupported manifest schema version")
    if mode not in {"source-draft", "archived-checkout"}:
        raise ManifestValidationError("validation mode must be source-draft or archived-checkout")
    _require_exact_values(manifest["manifest_identity"], {
        "experiment": "EXP-020A",
        "manifest_type": "cloud_migration",
        "schema_version": SCHEMA_VERSION,
    }, "manifest_identity")
    _validate_source_bindings(manifest)
    observed_checkout_commit = _validate_git_binding(manifest["git_binding"], repo_root, mode, check_git=check_git)
    if verify_target_checkout:
        if mode != "archived-checkout":
            raise ManifestValidationError("target checkout verification requires archived-checkout mode")
        _validate_target_checkout_environment(repo_root, manifest["git_binding"])
    execution_base_commit = manifest["git_binding"]["execution_base_commit"]
    validate_source_worktree = mode == "source-draft"
    _validate_registry(
        manifest["authority_artifacts"], repo_root, ("model_qualification_artifact",), "authority_artifacts",
        repository=True, execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree, verify_target_worktree=verify_target_checkout,
    )
    _validate_registry(
        manifest["execution_critical_repository_artifacts"],
        repo_root,
        EXPECTED_EXECUTION_ROLES,
        "execution_critical_repository_artifacts",
        repository=True, execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree, verify_target_worktree=verify_target_checkout,
    )
    _validate_formal_inputs(
        manifest["formal_input_artifacts"], repo_root,
        execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree,
        verify_target_worktree=verify_target_checkout,
    )
    _validate_model_snapshot(manifest["model_snapshot"], model_root)
    _validate_authorization(
        manifest["prior_consumed_authorization"], repo_root,
        execution_base_commit=execution_base_commit,
        validate_source_worktree=validate_source_worktree,
        verify_target_worktree=verify_target_checkout,
    )
    _validate_global_repository_registry_uniqueness(manifest)
    _validate_no_formal_results(repo_root)
    _validate_readiness(manifest["source_side_readiness"], manifest["target_side_readiness"])
    _validate_cloud_target(manifest["intended_cloud_target"])
    _require_exact_values(manifest["prohibited_operations"], {
        "cloud_created": False,
        "artifacts_uploaded": False,
        "model_loaded": False,
        "gpu_used": False,
        "formal_run_authorized": False,
        "formal_results_created": False,
    }, "prohibited_operations")
    return observed_checkout_commit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--model-root", type=Path, required=True)
    parser.add_argument("--mode", choices=("source-draft", "archived-checkout"), required=True)
    parser.add_argument("--verify-target-checkout", action="store_true")
    args = parser.parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        observed = validate_manifest(
            manifest, args.repo_root, args.model_root, args.mode,
            verify_target_checkout=args.verify_target_checkout,
        )
    except (ManifestValidationError, OSError, json.JSONDecodeError) as error:
        print(f"CLOUD_MIGRATION_MANIFEST_INVALID: {error}")
        return 1
    if args.mode == "source-draft":
        print("CLOUD_MIGRATION_SOURCE_DRAFT_READY_FOR_REREVIEW")
    else:
        print("CLOUD_MIGRATION_ARCHIVED_CHECKOUT_VERIFIED")
        print(f"observed_checkout_commit={observed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
