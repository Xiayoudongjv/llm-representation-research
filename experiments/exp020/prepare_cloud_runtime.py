"""Prepare fail-closed Linux path compatibility for EXP-020 cloud validation.

This utility only validates file identity and creates exact directory symlinks
after the complete migration validator and both conflict preflights succeed.
It never imports the formal runner, torch, transformers, or safetensors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.exp020.validate_cloud_migration_manifest import (  # noqa: E402
    ManifestValidationError,
    validate_manifest,
)


FROZEN_MODEL_IDENTITY = {
    "model_id": "Qwen/Qwen3-4B",
    "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
    "architecture": "Qwen3ForCausalLM",
    "model_type": "qwen3",
    "transformer_blocks": 36,
    "hidden_size": 2560,
    "dtype": "bfloat16",
}
FROZEN_CONFIG_SHA256 = "8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a"
FROZEN_WINDOWS_CANONICAL_PATH = r"D:\Qwen3-4B-transfer"


class CloudRuntimePreparationError(RuntimeError):
    """Raised when target identity, roots, or aliases fail closed validation."""


def _is_posix_target() -> bool:
    """Return whether this process is running in the Linux target environment."""
    return os.name == "posix"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise CloudRuntimePreparationError(f"invalid JSON metadata: {path}") from error
    if not isinstance(value, dict):
        raise CloudRuntimePreparationError(f"JSON metadata must be an object: {path}")
    return value


def _resolved(path: Path) -> Path:
    try:
        return path.resolve(strict=True)
    except OSError as error:
        raise CloudRuntimePreparationError(f"required path is unavailable: {path}") from error


def _absolute_normalized_posix(value: Any, name: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise CloudRuntimePreparationError(f"{name} must be a non-empty absolute path")
    path = PurePosixPath(value)
    if not path.is_absolute() or ".." in path.parts or str(path) != value:
        raise CloudRuntimePreparationError(f"{name} must be an absolute normalized path")
    return path


def _require_inside(path: Path, root: Path, name: str) -> None:
    if path != root and root not in path.parents:
        raise CloudRuntimePreparationError(f"{name} resolves outside its permitted root")


def _validate_binding_texts(
    bindings: dict[str, Any],
) -> tuple[PurePosixPath, PurePosixPath, PurePosixPath, PurePosixPath]:
    """Validate the closed POSIX path policy before touching the filesystem."""
    persistent_root = _absolute_normalized_posix(
        bindings.get("persistent_root"), "persistent mount"
    )
    target_binding = _absolute_normalized_posix(
        bindings.get("model_snapshot_root"), "model target binding"
    )
    repository_root = _absolute_normalized_posix(
        bindings.get("repository_root"), "repository target binding"
    )
    model_storage_root = persistent_root / "models"
    if target_binding.parent != model_storage_root:
        raise CloudRuntimePreparationError(
            "model target binding parent does not equal the permitted model-storage root"
        )
    return persistent_root, model_storage_root, target_binding, repository_root


def _validate_model_identity(manifest: dict[str, Any], model_root: Path) -> None:
    snapshot = manifest.get("model_snapshot")
    if not isinstance(snapshot, dict) or snapshot.get("identity") != FROZEN_MODEL_IDENTITY:
        raise CloudRuntimePreparationError("manifest model identity does not match the frozen model")
    config_path = _resolved(model_root) / "config.json"
    if not config_path.is_file() or _sha256(config_path) != FROZEN_CONFIG_SHA256:
        raise CloudRuntimePreparationError("verified model config hash does not match the frozen model")
    config = _load_json(config_path)
    observed = {
        "architecture": config.get("architectures", [None])[0]
        if isinstance(config.get("architectures"), list)
        else None,
        "model_type": config.get("model_type"),
        "transformer_blocks": config.get("num_hidden_layers"),
        "hidden_size": config.get("hidden_size"),
        "dtype": config.get("torch_dtype"),
    }
    expected = {key: FROZEN_MODEL_IDENTITY[key] for key in observed}
    if observed != expected:
        raise CloudRuntimePreparationError(
            "verified model config metadata does not match the frozen model"
        )


def _preflight_alias(alias: Path, target: Path, allowed_parent: Path) -> bool:
    """Return whether a symlink must be created, without changing the filesystem."""
    if alias.parent != allowed_parent or ".." in alias.parts:
        raise CloudRuntimePreparationError(
            f"compatibility alias escapes its permitted root: {alias}"
        )
    if not allowed_parent.is_dir():
        raise CloudRuntimePreparationError(f"required alias parent is missing: {allowed_parent}")
    if not os.path.lexists(alias):
        return True
    if not alias.is_symlink():
        raise CloudRuntimePreparationError(f"compatibility alias path already exists: {alias}")
    if _resolved(alias) != target:
        raise CloudRuntimePreparationError(f"conflicting compatibility alias: {alias}")
    return False


def _create_preflighted_alias(
    alias: Path, link_target: Path, expected_resolved_target: Path, create: bool
) -> bool:
    """Create a preflighted alias and verify its final resolved target exactly."""
    if not create:
        return False
    try:
        os.symlink(link_target, alias, target_is_directory=True)
    except OSError as error:
        raise CloudRuntimePreparationError(
            f"compatibility alias creation failed: {alias}"
        ) from error
    if not alias.is_symlink() or _resolved(alias) != expected_resolved_target:
        raise CloudRuntimePreparationError(
            f"compatibility alias verification failed: {alias}"
        )
    return True


def _require_ignored_alias(repo_root: Path, alias: Path) -> None:
    relative = alias.relative_to(repo_root).as_posix()
    completed = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", "--", relative],
        cwd=repo_root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise CloudRuntimePreparationError(
            "compatibility alias is not covered by a tracked ignore rule: "
            f"{relative}"
        )


def _validated_layout(
    manifest: dict[str, Any], repo_root: Path, verified_model_root: Path
) -> tuple[Path, Path, Path, Path, Path]:
    """Resolve and confine all roots without creating any directory or alias."""
    bindings = manifest.get("target_bindings")
    if not isinstance(bindings, dict):
        raise CloudRuntimePreparationError("manifest target bindings are missing")
    (
        persistent_text,
        model_storage_text,
        target_binding_text,
        repository_text,
    ) = _validate_binding_texts(bindings)

    persistent_root = _resolved(Path(persistent_text))
    model_storage_root = _resolved(Path(model_storage_text))
    declared_repo_root = _resolved(Path(repository_text))
    repo_root = _resolved(repo_root)
    verified_model_root = _resolved(verified_model_root)
    if repo_root != declared_repo_root:
        raise CloudRuntimePreparationError(
            "repository root does not match the closed manifest target binding"
        )
    _require_inside(model_storage_root, persistent_root, "model-storage root")
    if model_storage_root.parent != persistent_root:
        raise CloudRuntimePreparationError(
            "resolved model-storage root is not directly under the persistent mount"
        )
    _require_inside(verified_model_root, model_storage_root, "verified model root")

    target_binding = Path(target_binding_text)
    if _resolved(target_binding.parent) != model_storage_root:
        raise CloudRuntimePreparationError(
            "target binding parent is not the resolved model-storage root"
        )
    canonical_alias = repo_root / FROZEN_WINDOWS_CANONICAL_PATH
    if canonical_alias.parent != repo_root or ".." in canonical_alias.parts:
        raise CloudRuntimePreparationError(
            "repository compatibility alias escapes the repository root"
        )
    return (
        repo_root,
        verified_model_root,
        model_storage_root,
        target_binding,
        canonical_alias,
    )


def prepare_cloud_runtime(
    repo_root: Path,
    manifest_path: Path,
    verified_model_root: Path,
    *,
    manifest_validator: Callable[..., str | None] = validate_manifest,
) -> dict[str, bool]:
    """Validate first, then create two preflighted, exact Linux aliases.

    A race-time creation failure may leave only a correctly targeted first alias.
    This utility never creates parent directories, overwrites a path, unlinks an
    alias, or redirects an existing alias.
    """
    if not _is_posix_target():
        raise CloudRuntimePreparationError(
            "cloud runtime preparation requires a Linux target checkout"
        )
    manifest = _load_json(manifest_path)
    (
        repo_root,
        verified_model_root,
        model_storage_root,
        target_binding,
        canonical_alias,
    ) = _validated_layout(manifest, repo_root, verified_model_root)
    _validate_model_identity(manifest, verified_model_root)
    try:
        manifest_validator(
            manifest,
            repo_root,
            verified_model_root,
            "archived-checkout",
            verify_target_checkout=True,
        )
    except ManifestValidationError as error:
        raise CloudRuntimePreparationError(
            f"cloud migration target verification failed: {error}"
        ) from error

    target_create = _preflight_alias(
        target_binding, verified_model_root, model_storage_root
    )
    _require_ignored_alias(repo_root, canonical_alias)
    canonical_create = _preflight_alias(canonical_alias, verified_model_root, repo_root)
    return {
        "persistent_target_binding_alias_created": _create_preflighted_alias(
            target_binding, verified_model_root, verified_model_root, target_create
        ),
        "windows_canonical_compatibility_alias_created": _create_preflighted_alias(
            canonical_alias, target_binding, verified_model_root, canonical_create
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--verified-model-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare_cloud_runtime(
            args.repo_root, args.manifest, args.verified_model_root
        )
    except CloudRuntimePreparationError as error:
        print(f"CLOUD_RUNTIME_PREPARATION_BLOCKED: {error}")
        return 1
    print("CLOUD_RUNTIME_PREPARATION_READY_FOR_REVIEW")
    for key, value in result.items():
        print(f"{key}={str(value).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
