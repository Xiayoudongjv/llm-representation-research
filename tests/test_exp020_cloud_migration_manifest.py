"""Synthetic-only tests for the EXP-020 cloud migration manifest validator."""

from __future__ import annotations

import hashlib
import json
import os
import ast
import subprocess
import sys
from pathlib import Path

import pytest

from experiments.exp020.validate_cloud_migration_manifest import (
    ARTIFACT_FIELDS,
    EXPECTED_MODEL_ROLES,
    EXPECTED_TOKENIZER_ROLES,
    ManifestValidationError,
    _relative_path,
    _require_keys,
    _validate_artifact,
    _validate_authorization,
    _validate_cloud_target,
    _validate_git_binding,
    _validate_git_binding_schema,
    _validate_model_snapshot,
    _validate_no_formal_results,
    _validate_repository_artifact,
    _validate_readiness,
    _validate_registry,
    _validate_source_bindings,
    _validate_target_checkout_environment,
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact(root: Path, role: str, relative_path: str, content: bytes = b"x") -> dict[str, object]:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {
        "logical_role": role,
        "relative_path": relative_path,
        "sha256": _digest(path),
        "size_bytes": len(content),
        "required": True,
        "provenance_class": "SYNTHETIC_TEST_ARTIFACT",
        "content_access_level": "LEVEL_0_FILE_IDENTITY",
    }


def _snapshot(root: Path) -> dict[str, object]:
    config = _artifact(root, "model_config", "config.json", b"{}")
    generation = _artifact(root, "generation_config", "generation_config.json", b"{}")
    index_payload = {"metadata": {"total_size": 6}, "weight_map": {"a": "one.safetensors", "b": "two.safetensors", "c": "three.safetensors"}}
    index = _artifact(root, "model_index", "model.safetensors.index.json", json.dumps(index_payload).encode())
    shards = [
        _artifact(root, "model_shard_1", "one.safetensors", b"1"),
        _artifact(root, "model_shard_2", "two.safetensors", b"2"),
        _artifact(root, "model_shard_3", "three.safetensors", b"3"),
    ]
    tokenizer = [
        _artifact(root, "tokenizer_config", "tokenizer_config.json", b"{}"),
        _artifact(root, "tokenizer_json", "tokenizer.json", b"{}"),
        _artifact(root, "tokenizer_vocab", "vocab.json", b"{}"),
        _artifact(root, "tokenizer_merges", "merges.txt", b"x"),
    ]
    return {
        "identity": {
            "model_id": "Qwen/Qwen3-4B",
            "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
            "architecture": "Qwen3ForCausalLM",
            "model_type": "qwen3",
            "transformer_blocks": 36,
            "hidden_size": 2560,
            "dtype": "bfloat16",
        },
        "required_model_files": [config, generation, index, *shards],
        "required_tokenizer_files": tokenizer,
        "index_summary": {"tensor_count": 3, "raw_tensor_bytes": 6, "index_sha256": index["sha256"]},
    }


def test_valid_synthetic_snapshot_accepts_relative_relocation(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    _validate_model_snapshot(snapshot, tmp_path)
    target = tmp_path / "linux-target"
    target.mkdir()
    assert _relative_path(tmp_path, "config.json").name == "config.json"
    assert str(target).endswith("linux-target")


@pytest.mark.parametrize("relative", ["../escape.txt", "C:/absolute.txt", "/absolute.txt"])
def test_absolute_or_traversal_paths_are_rejected(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ManifestValidationError):
        _relative_path(tmp_path, relative)


def test_missing_renamed_and_changed_same_size_artifacts_fail(tmp_path: Path) -> None:
    entry = _artifact(tmp_path, "role", "artifact.txt", b"ab")
    (tmp_path / "artifact.txt").write_bytes(b"cd")
    with pytest.raises(ManifestValidationError):
        _validate_artifact(entry, tmp_path)


def test_changed_artifact_byte_size_fails(tmp_path: Path) -> None:
    entry = _artifact(tmp_path, "role", "artifact.txt", b"ab")
    (tmp_path / "artifact.txt").write_bytes(b"abc")
    with pytest.raises(ManifestValidationError, match="size mismatch"):
        _validate_artifact(entry, tmp_path)
    entry["relative_path"] = "renamed.txt"
    with pytest.raises(ManifestValidationError):
        _validate_artifact(entry, tmp_path)


def test_registry_rejects_unknown_missing_duplicate_and_case_collision(tmp_path: Path) -> None:
    one = _artifact(tmp_path, "one", "one.txt")
    two = _artifact(tmp_path, "two", "two.txt")
    with pytest.raises(ManifestValidationError):
        _validate_registry([one, two], tmp_path, ("one",), "test")
    duplicate = dict(one)
    duplicate["logical_role"] = "one"
    with pytest.raises(ManifestValidationError):
        _validate_registry([one, duplicate], tmp_path, ("one", "one"), "test")
    upper = _artifact(tmp_path, "two", "ONE.TXT")
    with pytest.raises(ManifestValidationError):
        _validate_registry([one, upper], tmp_path, ("one", "two"), "test")


def test_registry_rejects_duplicate_logical_role_before_path_validation(tmp_path: Path) -> None:
    one = _artifact(tmp_path, "one", "one.txt")
    duplicate_role = _artifact(tmp_path, "one", "two.txt")
    with pytest.raises(ManifestValidationError, match="duplicate logical roles"):
        _validate_registry([one, duplicate_role], tmp_path, ("one", "two"), "test")


def test_unresolved_or_escaping_symlink_is_rejected(tmp_path: Path) -> None:
    broken = tmp_path / "broken"
    try:
        os.symlink(tmp_path / "does-not-exist", broken)
    except (NotImplementedError, OSError):
        pytest.skip("symlinks are unavailable in this Windows test environment")
    with pytest.raises(ManifestValidationError):
        _relative_path(tmp_path, "broken")


def test_model_index_rejects_unknown_shard_and_bad_summary(tmp_path: Path) -> None:
    snapshot = _snapshot(tmp_path)
    index_path = tmp_path / "model.safetensors.index.json"
    payload = json.loads(index_path.read_text())
    payload["weight_map"]["a"] = "unknown.safetensors"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    snapshot["required_model_files"][2]["sha256"] = _digest(index_path)
    snapshot["required_model_files"][2]["size_bytes"] = index_path.stat().st_size
    with pytest.raises(ManifestValidationError):
        _validate_model_snapshot(snapshot, tmp_path)
    payload["weight_map"]["a"] = "one.safetensors"
    index_path.write_text(json.dumps(payload), encoding="utf-8")
    snapshot["required_model_files"][2]["sha256"] = _digest(index_path)
    snapshot["required_model_files"][2]["size_bytes"] = index_path.stat().st_size
    snapshot["index_summary"]["raw_tensor_bytes"] = 7
    with pytest.raises(ManifestValidationError):
        _validate_model_snapshot(snapshot, tmp_path)


def test_authorization_must_be_consumed_and_non_reusable(tmp_path: Path) -> None:
    repo, _, _ = _synthetic_repo(tmp_path, with_untracked_migration_paths=False)
    authorization = _artifact(repo, "prior_formal_authorization", "authorization.json")
    consumption = _artifact(repo, "prior_authorization_consumption", "consumption.json")
    _git(repo, "add", "authorization.json", "consumption.json")
    _git(repo, "commit", "-m", "authorization provenance")
    execution_base = _git(repo, "rev-parse", "HEAD")
    for artifact in (authorization, consumption):
        artifact["git_blob_sha256"] = artifact["sha256"]
        artifact["git_blob_size_bytes"] = artifact["size_bytes"]
    value = {"authorization": authorization, "consumption_record": consumption, "single_use": True, "state": "consumed", "reusable": False}
    _validate_authorization(
        value, repo, execution_base_commit=execution_base,
        validate_source_worktree=True, verify_target_worktree=False,
    )
    value["reusable"] = True
    with pytest.raises(ManifestValidationError):
        _validate_authorization(
            value, repo, execution_base_commit=execution_base,
            validate_source_worktree=True, verify_target_worktree=False,
        )


def test_repository_artifact_distinguishes_source_worktree_from_target_blob(tmp_path: Path) -> None:
    repo, _, _ = _synthetic_repo(tmp_path, with_untracked_migration_paths=False)
    _git(repo, "config", "core.autocrlf", "false")
    _git(repo, "config", "core.eol", "lf")
    path = repo / "authority.txt"
    path.write_bytes(b"frozen\nidentity\n")
    _git(repo, "add", "authority.txt")
    _git(repo, "commit", "-m", "LF authority")
    execution_base = _git(repo, "rev-parse", "HEAD")
    blob = path.read_bytes()
    path.write_bytes(blob.replace(b"\n", b"\r\n"))
    artifact = _artifact(repo, "authority", "authority.txt", path.read_bytes())
    artifact["git_blob_sha256"] = hashlib.sha256(blob).hexdigest()
    artifact["git_blob_size_bytes"] = len(blob)
    _validate_repository_artifact(
        artifact, repo, execution_base_commit=execution_base,
        validate_source_worktree=True, verify_target_worktree=False,
    )
    _git(repo, "checkout", "--", "authority.txt")
    _validate_repository_artifact(
        artifact, repo, execution_base_commit=execution_base,
        validate_source_worktree=False, verify_target_worktree=True,
    )


def test_canonical_and_staging_results_are_rejected(tmp_path: Path) -> None:
    _validate_no_formal_results(tmp_path)
    staging = tmp_path / "experiments/exp020/results/exp020a_results.json.tmp-test"
    staging.parent.mkdir(parents=True)
    staging.write_text("{}", encoding="utf-8")
    with pytest.raises(ManifestValidationError):
        _validate_no_formal_results(tmp_path)


def test_readiness_and_cloud_target_cannot_claim_unverified_state() -> None:
    source = {"source_preflight_complete": True, "formal_run_authorized": False, "formal_results_created": False}
    target = {"transfer_verified": False, "cloud_runtime_verified": False, "cloud_target_qualified": False, "formal_run_authorized": False, "formal_results_created": False}
    _validate_readiness(source, target)
    target["cloud_runtime_verified"] = True
    with pytest.raises(ManifestValidationError):
        _validate_readiness(source, target)
    cloud = {
        "provider_class": "DOMESTIC_CONTAINER_GPU_SERVICE",
        "region": "synthetic-region",
        "hardware": {
            "node_count": 1, "gpu_count": 1, "requested_gpu": "NVIDIA GeForce RTX 5090",
            "requested_vram_gb": 32, "requested_cpu_cores": 26, "requested_host_memory_gb": 63,
            "scaling_mode": "MANUAL", "multi_container": False, "preemptible": False,
            "persistent_volume_gb": 100, "persistent_mount": "/workspace/persist",
            "provenance_class": "USER_SELECTED_PRE_OUTCOME_ENGINEERING_TARGET", "hardware_verified": False,
        },
        "container": {
            "image_repository": "pytorch/pytorch", "image_tag": "2.12.1-cuda13.0-cudnn9-devel",
            "expected_platform": "linux/amd64", "expected_image_manifest_digest": "sha256:ac63aaae09996612bdaf12bbf6d5fe840af6bed3100d6dc15fcb5fd1f4f957c4",
            "provenance_class": "EXPECTED_TARGET_IMAGE_IDENTITY", "source_registry_resolution_verified": False,
            "actual_target_image_digest": None, "target_image_verified": False,
        },
    }
    _validate_cloud_target(cloud)
    cloud["hardware"]["hardware_verified"] = True
    with pytest.raises(ManifestValidationError):
        _validate_cloud_target(cloud)


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)
    return result.stdout.strip()


def _binding(base: str) -> dict[str, object]:
    paths = [
        "docs/experiments/EXP-020-CLOUD-MIGRATION-PREFLIGHT.md",
        "experiments/exp020/cloud_migration_manifest.json",
        "experiments/exp020/validate_cloud_migration_manifest.py",
        "tests/test_exp020_cloud_migration_manifest.py",
    ]
    return {
        "schema_version": "1.0.0", "execution_base_commit": base,
        "binding_policy": "EXACT_MIGRATION_ONLY_DESCENDANT", "allowed_migration_paths": paths,
        "source_draft_requirements": {"live_head_equals_execution_base": True, "migration_paths_untracked": True, "tracked_worktree_clean": True, "staging_empty": True, "no_unexpected_untracked_files": True},
        "archived_checkout_requirements": {"live_head_strict_descendant": True, "exact_committed_delta": True, "tracked_worktree_clean": True, "staging_empty": True, "no_unexpected_untracked_files": True},
        "observed_checkout_commit_policy": "OBSERVE_LIVE_HEAD_ONLY_NOT_SERIALIZED",
        "target_checkout_policy": {"schema_version": "1.0.0", "target_operating_system": "Linux", "core_autocrlf": False, "core_eol": "lf", "configuration_applied_before_checkout": True, "checkout_mode": "DETACHED_EXACT_COMMIT", "floating_branch_prohibited": True},
    }


def _synthetic_repo(tmp_path: Path, *, with_untracked_migration_paths: bool = True) -> tuple[Path, str, dict[str, object]]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Synthetic test")
    _git(repo, "config", "user.email", "synthetic@example.invalid")
    (repo / "baseline.txt").write_text("baseline", encoding="utf-8")
    _git(repo, "add", "baseline.txt")
    _git(repo, "commit", "-m", "base")
    base = _git(repo, "rev-parse", "HEAD")
    binding = _binding(base)
    if with_untracked_migration_paths:
        for relative in binding["allowed_migration_paths"]:
            path = repo / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("synthetic migration file", encoding="utf-8")
    return repo, base, binding


def _commit_migration_paths(repo: Path, binding: dict[str, object], *extra_paths: str) -> str:
    paths = [*binding["allowed_migration_paths"], *extra_paths]
    for relative in extra_paths:
        path = repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("synthetic sentinel", encoding="utf-8")
    _git(repo, "add", *paths)
    _git(repo, "commit", "-m", "archive migration files")
    return _git(repo, "rev-parse", "HEAD")


def test_source_draft_and_archived_lifecycle_modes(tmp_path: Path) -> None:
    repo, base, binding = _synthetic_repo(tmp_path)
    assert _validate_git_binding(binding, repo, "source-draft", check_git=True, expected_execution_base=base) is None
    archived_head = _commit_migration_paths(repo, binding)
    assert _validate_git_binding(binding, repo, "archived-checkout", check_git=True, expected_execution_base=base) == archived_head


def test_source_draft_rejects_changed_head_staged_and_untracked_files(tmp_path: Path) -> None:
    repo, base, binding = _synthetic_repo(tmp_path)
    (repo / "unexpected.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding(binding, repo, "source-draft", check_git=True, expected_execution_base=base)
    (repo / "unexpected.txt").unlink()
    (repo / "staged-source.txt").write_text("x", encoding="utf-8")
    _git(repo, "add", "staged-source.txt")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding(binding, repo, "source-draft", check_git=True, expected_execution_base=base)
    _git(repo, "restore", "--staged", "staged-source.txt")
    (repo / "staged-source.txt").unlink()
    _git(repo, "add", *binding["allowed_migration_paths"])
    _git(repo, "commit", "-m", "changed head")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding(binding, repo, "source-draft", check_git=True, expected_execution_base=base)


@pytest.mark.parametrize("extra_path", [
    "experiments/exp020/run_exp020a.py",
    "experiments/exp020/exp020_frozen_config.json",
    "docs/experiments/EXP-020-PREREGISTRATION.md",
    "docs/experiments/EXP-020-IMPLEMENTATION-SPECIFICATION.md",
    "experiments/exp020/validate_exp020_preregistration.py",
    "experiments/exp003/prompts_controlled.json",
    "docs/unrelated.md",
])
def test_archived_checkout_rejects_any_extra_or_scientific_delta(tmp_path: Path, extra_path: str) -> None:
    repo, base, binding = _synthetic_repo(tmp_path)
    _commit_migration_paths(repo, binding, extra_path)
    with pytest.raises(ManifestValidationError, match="committed delta"):
        _validate_git_binding(binding, repo, "archived-checkout", check_git=True, expected_execution_base=base)


def test_archived_checkout_rejects_base_head_non_descendant_dirty_staged_and_untracked(tmp_path: Path) -> None:
    repo, base, binding = _synthetic_repo(tmp_path)
    with pytest.raises(ManifestValidationError, match="strict descendant"):
        _validate_git_binding(binding, repo, "archived-checkout", check_git=True, expected_execution_base=base)
    _commit_migration_paths(repo, binding)
    (repo / "dirty.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding(binding, repo, "archived-checkout", check_git=True, expected_execution_base=base)
    (repo / "dirty.txt").unlink()
    (repo / "baseline.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding(binding, repo, "archived-checkout", check_git=True, expected_execution_base=base)
    _git(repo, "checkout", "--", "baseline.txt")
    (repo / "staged.txt").write_text("x", encoding="utf-8")
    _git(repo, "add", "staged.txt")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding(binding, repo, "archived-checkout", check_git=True, expected_execution_base=base)


def test_git_binding_schema_rejects_missing_unknown_reordered_duplicate_and_observed_fields(tmp_path: Path) -> None:
    _, base, binding = _synthetic_repo(tmp_path)
    for key in tuple(binding):
        invalid = dict(binding)
        del invalid[key]
        with pytest.raises(ManifestValidationError):
            _validate_git_binding_schema(invalid, expected_execution_base=base)
    invalid = dict(binding)
    invalid["observed_checkout_commit"] = "caller-controlled"
    with pytest.raises(ManifestValidationError):
        _validate_git_binding_schema(invalid, expected_execution_base=base)
    invalid = dict(binding)
    invalid["allowed_migration_paths"] = list(reversed(invalid["allowed_migration_paths"]))
    with pytest.raises(ManifestValidationError):
        _validate_git_binding_schema(invalid, expected_execution_base=base)
    invalid = dict(binding)
    invalid["allowed_migration_paths"] = [*invalid["allowed_migration_paths"][:-1], invalid["allowed_migration_paths"][-2]]
    with pytest.raises(ManifestValidationError):
        _validate_git_binding_schema(invalid, expected_execution_base=base)


def test_cli_rejects_missing_or_invalid_lifecycle_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    from experiments.exp020 import validate_cloud_migration_manifest as validator

    monkeypatch.setattr(sys, "argv", ["validator"])
    with pytest.raises(SystemExit):
        validator.main()
    monkeypatch.setattr(sys, "argv", ["validator", "--mode", "invalid"])
    with pytest.raises(SystemExit):
        validator.main()


def test_synthetic_eol_checkout_policy_reproduces_lf_blob(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    _git(source, "init")
    _git(source, "config", "user.name", "Synthetic test")
    _git(source, "config", "user.email", "synthetic@example.invalid")
    artifact = source / "docs/authority.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"line one\nline two\n")
    _git(source, "add", "docs/authority.md")
    _git(source, "commit", "-m", "LF base")
    base = _git(source, "rev-parse", "HEAD")
    inherited = tmp_path / "inherited"
    target = tmp_path / "target"
    _git(source, "-c", "core.autocrlf=true", "clone", str(source), str(inherited))
    _git(source, "clone", "--no-checkout", str(source), str(target))
    _git(target, "config", "core.autocrlf", "false")
    _git(target, "config", "core.eol", "lf")
    _git(target, "checkout", "--detach", base)
    source_bytes = artifact.read_bytes()
    inherited_bytes = (inherited / "docs/authority.md").read_bytes()
    target_bytes = (target / "docs/authority.md").read_bytes()
    assert inherited_bytes != source_bytes
    assert b"\r\n" in inherited_bytes
    assert len(inherited_bytes) != len(source_bytes)
    assert _digest(inherited / "docs/authority.md") != _digest(artifact)
    assert target_bytes == source_bytes
    assert b"\r\n" not in target_bytes
    assert _digest(target / "docs/authority.md") == _digest(artifact)


def test_target_checkout_environment_requires_local_lf_and_detached_head(tmp_path: Path) -> None:
    repo, base, binding = _synthetic_repo(tmp_path)
    _commit_migration_paths(repo, binding)
    _git(repo, "config", "core.autocrlf", "false")
    _git(repo, "config", "core.eol", "lf")
    _git(repo, "checkout", "--detach", "HEAD")
    _validate_target_checkout_environment(repo, binding)
    _git(repo, "config", "core.autocrlf", "true")
    with pytest.raises(ManifestValidationError):
        _validate_target_checkout_environment(repo, binding)
    _git(repo, "config", "core.autocrlf", "false")
    _git(repo, "config", "--unset", "core.eol")
    with pytest.raises(ManifestValidationError):
        _validate_target_checkout_environment(repo, binding)


def test_checkout_policy_rejects_unknown_renamed_and_floating_branch(tmp_path: Path) -> None:
    _, base, binding = _synthetic_repo(tmp_path)
    invalid = json.loads(json.dumps(binding))
    invalid["target_checkout_policy"]["unknown"] = True
    with pytest.raises(ManifestValidationError):
        _validate_git_binding_schema(invalid, expected_execution_base=base)
    invalid = json.loads(json.dumps(binding))
    invalid["target_checkout_policy"]["eol"] = invalid["target_checkout_policy"].pop("core_eol")
    with pytest.raises(ManifestValidationError):
        _validate_git_binding_schema(invalid, expected_execution_base=base)
    invalid = json.loads(json.dumps(binding))
    invalid["target_checkout_policy"]["checkout_mode"] = "FLOATING_BRANCH"
    with pytest.raises(ManifestValidationError):
        _validate_git_binding_schema(invalid, expected_execution_base=base)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("source_git", {"commit": "commit", "branch": "main", "tracking": "origin/main"}),
        ("source_roots", {"repository_root": "C:/repo", "model_snapshot_root": "C:/model"}),
        ("target_bindings", {"repository_root": "/repo", "model_snapshot_root": "/model", "persistent_root": "/persist", "transfer_mode": "COPY", "path_relocation_only": True}),
        ("hardware", {"node_count": 1, "gpu_count": 1, "requested_gpu": "NVIDIA GeForce RTX 5090", "requested_vram_gb": 32, "requested_cpu_cores": 26, "requested_host_memory_gb": 63, "scaling_mode": "MANUAL", "multi_container": False, "preemptible": False, "persistent_volume_gb": 100, "persistent_mount": "/workspace/persist", "provenance_class": "USER_SELECTED_PRE_OUTCOME_ENGINEERING_TARGET", "hardware_verified": False}),
        ("container", {"image_repository": "pytorch/pytorch", "image_tag": "tag", "expected_platform": "linux/amd64", "expected_image_manifest_digest": "sha256:abc", "provenance_class": "EXPECTED_TARGET_IMAGE_IDENTITY", "source_registry_resolution_verified": False, "actual_target_image_digest": None, "target_image_verified": False}),
        ("artifact", {"logical_role": "role", "relative_path": "x", "sha256": "a" * 64, "size_bytes": 1, "required": True, "provenance_class": "SYNTHETIC", "content_access_level": "LEVEL_0_FILE_IDENTITY"}),
        ("source_readiness", {"source_preflight_complete": True, "formal_run_authorized": False, "formal_results_created": False}),
        ("target_readiness", {"transfer_verified": False, "cloud_runtime_verified": False, "cloud_target_qualified": False, "formal_run_authorized": False, "formal_results_created": False}),
    ],
)
def test_closed_schema_rejects_missing_unknown_and_renamed_fields(name: str, value: dict[str, object]) -> None:
    expected = set(value)
    for field in tuple(expected):
        missing = dict(value)
        del missing[field]
        with pytest.raises(ManifestValidationError):
            _require_keys(missing, expected, name)
    unknown = dict(value)
    unknown["unknown_field"] = "x"
    with pytest.raises(ManifestValidationError):
        _require_keys(unknown, expected, name)
    renamed = dict(value)
    field = next(iter(expected))
    renamed[f"renamed_{field}"] = renamed.pop(field)
    with pytest.raises(ManifestValidationError):
        _require_keys(renamed, expected, name)


@pytest.mark.parametrize("alias", ["cpu_cores", "host_memory_gib", "persistent_storage_gib", "mount_path", "manual_selection"])
def test_legacy_hardware_aliases_are_rejected(alias: str) -> None:
    cloud = {
        "provider_class": "DOMESTIC_CONTAINER_GPU_SERVICE", "region": "synthetic-region",
        "hardware": {"node_count": 1, "gpu_count": 1, "requested_gpu": "NVIDIA GeForce RTX 5090", "requested_vram_gb": 32, "requested_cpu_cores": 26, "requested_host_memory_gb": 63, "scaling_mode": "MANUAL", "multi_container": False, "preemptible": False, "persistent_volume_gb": 100, "persistent_mount": "/workspace/persist", "provenance_class": "USER_SELECTED_PRE_OUTCOME_ENGINEERING_TARGET", "hardware_verified": False},
        "container": {"image_repository": "pytorch/pytorch", "image_tag": "2.12.1-cuda13.0-cudnn9-devel", "expected_platform": "linux/amd64", "expected_image_manifest_digest": "sha256:ac63aaae09996612bdaf12bbf6d5fe840af6bed3100d6dc15fcb5fd1f4f957c4", "provenance_class": "EXPECTED_TARGET_IMAGE_IDENTITY", "source_registry_resolution_verified": False, "actual_target_image_digest": None, "target_image_verified": False},
    }
    cloud["hardware"][alias] = 1
    with pytest.raises(ManifestValidationError):
        _validate_cloud_target(cloud)
    del cloud["hardware"][alias]
    cloud["hardware"]["requested_gpu"] = "RTX 5090 32GB"
    with pytest.raises(ManifestValidationError):
        _validate_cloud_target(cloud)
    cloud["hardware"]["requested_gpu"] = "NVIDIA GeForce RTX 5090"
    _validate_cloud_target(cloud)


def test_empty_required_strings_are_rejected(tmp_path: Path) -> None:
    manifest = {
        "source_git": {"commit": "7865727284d633b7d7d174773d8d7ecf5ef35869", "branch": "main", "tracking": "origin/main"},
        "source_roots": {"repository_root": "", "model_snapshot_root": "C:/model"},
        "target_bindings": {"repository_root": "/workspace/persist/llm-representation-research", "model_snapshot_root": "/workspace/persist/models/qwen3-4b", "persistent_root": "/workspace/persist", "transfer_mode": "MANUAL_VERIFIED_COPY_REQUIRED", "path_relocation_only": True},
    }
    with pytest.raises(ManifestValidationError):
        _validate_source_bindings(manifest)
    manifest["source_roots"]["repository_root"] = "C:/repo"
    manifest["target_bindings"]["persistent_root"] = ""
    with pytest.raises(ManifestValidationError):
        _validate_source_bindings(manifest)
    entry = _artifact(tmp_path, "role", "artifact.txt")
    entry["provenance_class"] = ""
    with pytest.raises(ManifestValidationError):
        _validate_artifact(entry, tmp_path)


def test_integrity_error_never_discloses_synthetic_formal_content(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    sentinel = "SYNTHETIC_FORMAL_CONTENT_MUST_NOT_APPEAR"
    entry = _artifact(tmp_path, "role", "formal.json", sentinel.encode("utf-8"))
    entry["size_bytes"] = int(entry["size_bytes"]) + 1
    with pytest.raises(ManifestValidationError) as error:
        _validate_artifact(entry, tmp_path)
    print(f"CLOUD_MIGRATION_MANIFEST_INVALID: {error.value}")
    captured = capsys.readouterr()
    assert sentinel not in captured.out
    assert sentinel not in captured.err
    assert "size mismatch" in captured.out


def test_validator_module_uses_no_formal_runner_import() -> None:
    source = Path(__file__).parents[1] / "experiments/exp020/validate_cloud_migration_manifest.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith(("torch", "transformers", "safetensors")) for name in imports)
    assert not any("run_exp020a" in name for name in imports)
