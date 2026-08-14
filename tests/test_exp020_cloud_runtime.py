"""Synthetic, no-model tests for EXP-020 cloud runtime preparation."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path

import pytest

from experiments.exp020 import prepare_cloud_runtime as runtime


ROOT = Path(__file__).parents[1]
ARCHIVED_AUTHORIZATION = (
    ROOT
    / "experiments/exp020/archive/consumed_authorizations/exp020_formal_run_authorization.json"
)
ACTIVE_AUTHORIZATION = ROOT / "experiments/exp020/exp020_formal_run_authorization.json"
CONSUMPTION_RECORD = (
    ROOT
    / "experiments/exp020/results/authorization_consumption"
    / "070d2e2ccaf8857c2a3d439ea6c87420784f6029c9340ccf2d042399f7ecfd01.json"
)


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _synthetic_model_manifest(root: Path) -> tuple[dict[str, object], Path]:
    model = root / "model"
    model.mkdir()
    config = {
        "architectures": ["Qwen3ForCausalLM"],
        "model_type": "qwen3",
        "num_hidden_layers": 36,
        "hidden_size": 2560,
        "torch_dtype": "bfloat16",
    }
    (model / "config.json").write_text(json.dumps(config), encoding="utf-8")
    return {"model_snapshot": {"identity": dict(runtime.FROZEN_MODEL_IDENTITY)}}, model


def _runtime_layout(tmp_path: Path) -> tuple[Path, Path, Path, Path, Path]:
    persistent = tmp_path / "persist"
    storage = persistent / "models"
    verified_model = storage / "verified-snapshot"
    target_alias = storage / "qwen3-4b"
    repository = persistent / "repository"
    # Windows treats the frozen Linux alias spelling as a drive-qualified path.
    # The public preparation tests patch the already-validated layout, so use a
    # temporary child path here while preserving production Linux semantics.
    canonical_alias = repository / "canonical-compatibility-alias"
    verified_model.mkdir(parents=True)
    repository.mkdir()
    return repository, verified_model, storage, target_alias, canonical_alias


def _patch_public_prepare(
    monkeypatch: pytest.MonkeyPatch,
    layout: tuple[Path, Path, Path, Path, Path],
) -> None:
    monkeypatch.setattr(runtime, "_is_posix_target", lambda: True)
    monkeypatch.setattr(runtime, "_validated_layout", lambda *_args: layout)
    monkeypatch.setattr(runtime, "_validate_model_identity", lambda *_args: None)
    monkeypatch.setattr(runtime, "_require_ignored_alias", lambda *_args: None)


def _manifest_file(tmp_path: Path) -> Path:
    path = tmp_path / "manifest.json"
    path.write_text("{}", encoding="utf-8")
    return path


def _mock_directory_symlinks(monkeypatch: pytest.MonkeyPatch) -> None:
    """Simulate directory aliases so safety branches run on Windows and Linux."""
    aliases: dict[str, Path] = {}
    real_lexists = runtime.os.path.lexists
    real_is_symlink = Path.is_symlink
    real_resolved = runtime._resolved

    def fake_symlink(target: Path, alias: Path, **_kwargs: object) -> None:
        target_key = os.fspath(target)
        aliases[os.fspath(alias)] = (
            aliases[target_key]
            if target_key in aliases
            else real_resolved(Path(target))
        )

    def fake_lexists(path: object) -> bool:
        return os.fspath(path) in aliases or real_lexists(path)

    def fake_is_symlink(path: Path) -> bool:
        return os.fspath(path) in aliases or real_is_symlink(path)

    def fake_resolved(path: Path) -> Path:
        key = os.fspath(path)
        if key in aliases:
            return aliases[key]
        return real_resolved(path)

    monkeypatch.setattr(runtime.os, "symlink", fake_symlink)
    monkeypatch.setattr(runtime.os.path, "lexists", fake_lexists)
    monkeypatch.setattr(Path, "is_symlink", fake_is_symlink)
    monkeypatch.setattr(runtime, "_resolved", fake_resolved)


def test_consumed_authorization_is_archived_with_exact_lf_and_crlf_identities() -> None:
    data = ARCHIVED_AUTHORIZATION.read_bytes()
    assert not ACTIVE_AUTHORIZATION.exists()
    assert _digest(ARCHIVED_AUTHORIZATION) == "2108b26b4fe7a91e821f0c3a819ab3e0d0b1ff5c1d676e5368c3ab2a71ca0f48"
    assert data.count(b"\r\n") == 0
    assert data.count(b"\n") == 30
    assert hashlib.sha256(data.replace(b"\n", b"\r\n")).hexdigest() == "070d2e2ccaf8857c2a3d439ea6c87420784f6029c9340ccf2d042399f7ecfd01"
    assert _digest(CONSUMPTION_RECORD) == "0a39e6a214512ffac928620768100ac9a5c20e1a1fbd8c72c44f76413f6864cc"


def test_model_identity_rejects_wrong_config_hash_and_revision(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest, model = _synthetic_model_manifest(tmp_path)
    config_hash = _digest(model / "config.json")
    monkeypatch.setattr(runtime, "FROZEN_CONFIG_SHA256", config_hash)
    runtime._validate_model_identity(manifest, model)
    monkeypatch.setattr(runtime, "FROZEN_CONFIG_SHA256", "0" * 64)
    with pytest.raises(runtime.CloudRuntimePreparationError, match="config hash"):
        runtime._validate_model_identity(manifest, model)
    monkeypatch.setattr(runtime, "FROZEN_CONFIG_SHA256", config_hash)
    manifest["model_snapshot"]["identity"]["revision"] = "wrong"
    with pytest.raises(runtime.CloudRuntimePreparationError, match="identity"):
        runtime._validate_model_identity(manifest, model)


def test_validator_failure_precedes_alias_preflight_and_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, verified_model, storage, _target_alias, canonical_alias = _runtime_layout(tmp_path)
    target_alias = storage / "missing-parent" / "qwen3-4b"
    layout = (repository, verified_model, storage, target_alias, canonical_alias)
    _patch_public_prepare(monkeypatch, layout)

    def fail_validator(*_args: object, **_kwargs: object) -> None:
        raise runtime.ManifestValidationError("synthetic validation failure")

    with pytest.raises(runtime.CloudRuntimePreparationError, match="target verification failed"):
        runtime.prepare_cloud_runtime(
            repository, _manifest_file(tmp_path), verified_model, manifest_validator=fail_validator
        )
    assert not target_alias.parent.exists()
    assert not target_alias.exists()
    assert not canonical_alias.exists()


def test_validator_failure_leaves_existing_bytes_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _runtime_layout(tmp_path)
    repository, verified_model, _storage, _target_alias, _canonical_alias = layout
    sentinel = repository / "preexisting.txt"
    sentinel.write_bytes(b"unchanged-by-validation-failure")
    _patch_public_prepare(monkeypatch, layout)

    def fail_validator(*_args: object, **_kwargs: object) -> None:
        raise runtime.ManifestValidationError("synthetic validation failure")

    with pytest.raises(runtime.CloudRuntimePreparationError):
        runtime.prepare_cloud_runtime(
            repository, _manifest_file(tmp_path), verified_model, manifest_validator=fail_validator
        )
    assert sentinel.read_bytes() == b"unchanged-by-validation-failure"


def test_binding_policy_rejects_outside_target_and_traversal() -> None:
    bindings = {
        "persistent_root": "/workspace/persist",
        "model_snapshot_root": "/outside/qwen3-4b",
        "repository_root": "/workspace/persist/repository",
    }
    with pytest.raises(runtime.CloudRuntimePreparationError, match="permitted model-storage"):
        runtime._validate_binding_texts(bindings)
    bindings["model_snapshot_root"] = "/workspace/persist/models/../qwen3-4b"
    with pytest.raises(runtime.CloudRuntimePreparationError, match="absolute normalized"):
        runtime._validate_binding_texts(bindings)


def test_resolved_model_root_must_stay_inside_storage(tmp_path: Path) -> None:
    storage = tmp_path / "persist" / "models"
    outside = tmp_path / "outside-model"
    storage.mkdir(parents=True)
    outside.mkdir()
    with pytest.raises(runtime.CloudRuntimePreparationError, match="verified model root"):
        runtime._require_inside(outside.resolve(), storage.resolve(), "verified model root")


def test_lexical_inside_symlink_resolving_outside_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    storage = tmp_path / "persist" / "models"
    storage.mkdir(parents=True)
    outside = tmp_path / "outside-model"
    outside.mkdir()
    lexical_inside = storage / "linked-model"
    real_resolved = runtime._resolved
    monkeypatch.setattr(
        runtime,
        "_resolved",
        lambda path: outside.resolve() if path == lexical_inside else real_resolved(path),
    )
    with pytest.raises(runtime.CloudRuntimePreparationError, match="verified model root"):
        runtime._require_inside(
            runtime._resolved(lexical_inside), runtime._resolved(storage), "verified model root"
        )


def test_alias_preflight_rejects_missing_parent_regular_file_and_outside_parent(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    missing_parent = tmp_path / "missing"
    with pytest.raises(runtime.CloudRuntimePreparationError, match="parent is missing"):
        runtime._preflight_alias(missing_parent / "alias", target, missing_parent)
    assert not missing_parent.exists()

    allowed_parent = tmp_path / "allowed"
    allowed_parent.mkdir()
    regular_file = allowed_parent / "alias"
    regular_file.write_bytes(b"preserve")
    with pytest.raises(runtime.CloudRuntimePreparationError, match="already exists"):
        runtime._preflight_alias(regular_file, target, allowed_parent)
    assert regular_file.read_bytes() == b"preserve"

    outside_parent = tmp_path / "outside"
    outside_parent.mkdir()
    with pytest.raises(runtime.CloudRuntimePreparationError, match="escapes"):
        runtime._preflight_alias(outside_parent / "alias", target, allowed_parent)


def test_broken_symlink_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    parent = tmp_path / "parent"
    parent.mkdir()
    target = tmp_path / "target"
    target.mkdir()
    broken = parent / "broken"
    real_is_symlink = Path.is_symlink
    monkeypatch.setattr(runtime.os.path, "lexists", lambda path: Path(path) == broken)
    monkeypatch.setattr(
        Path, "is_symlink", lambda path: path == broken or real_is_symlink(path)
    )
    with pytest.raises(runtime.CloudRuntimePreparationError, match="required path is unavailable"):
        runtime._preflight_alias(broken, target, parent)


def test_conflicting_target_alias_prevents_repository_alias_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _runtime_layout(tmp_path)
    repository, verified_model, _storage, target_alias, canonical_alias = layout
    target_alias.write_bytes(b"do-not-replace")
    _patch_public_prepare(monkeypatch, layout)
    with pytest.raises(runtime.CloudRuntimePreparationError, match="already exists"):
        runtime.prepare_cloud_runtime(
            repository, _manifest_file(tmp_path), verified_model, manifest_validator=lambda *_args, **_kwargs: None
        )
    assert target_alias.read_bytes() == b"do-not-replace"
    assert not os.path.lexists(canonical_alias)


def test_conflicting_repository_alias_prevents_target_alias_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    layout = _runtime_layout(tmp_path)
    repository, verified_model, _storage, target_alias, canonical_alias = layout
    canonical_alias.write_bytes(b"do-not-replace")
    _patch_public_prepare(monkeypatch, layout)
    with pytest.raises(runtime.CloudRuntimePreparationError, match="already exists"):
        runtime.prepare_cloud_runtime(
            repository, _manifest_file(tmp_path), verified_model, manifest_validator=lambda *_args, **_kwargs: None
        )
    assert canonical_alias.read_bytes() == b"do-not-replace"
    assert not os.path.lexists(target_alias)


def test_correct_two_alias_creation_and_repeated_preparation_are_idempotent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _mock_directory_symlinks(monkeypatch)
    layout = _runtime_layout(tmp_path)
    repository, verified_model, _storage, target_alias, canonical_alias = layout
    _patch_public_prepare(monkeypatch, layout)
    manifest = _manifest_file(tmp_path)
    first = runtime.prepare_cloud_runtime(
        repository, manifest, verified_model, manifest_validator=lambda *_args, **_kwargs: None
    )
    assert first == {
        "persistent_target_binding_alias_created": True,
        "windows_canonical_compatibility_alias_created": True,
    }
    assert runtime._resolved(target_alias) == verified_model.resolve()
    assert runtime._resolved(canonical_alias) == verified_model.resolve()
    second = runtime.prepare_cloud_runtime(
        repository, manifest, verified_model, manifest_validator=lambda *_args, **_kwargs: None
    )
    assert second == {
        "persistent_target_binding_alias_created": False,
        "windows_canonical_compatibility_alias_created": False,
    }


def test_linux_compatibility_alias_is_narrowly_ignored() -> None:
    ignore_rules = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/D:\\\\Qwen3-4B-transfer" in ignore_rules


def test_preparation_utility_never_imports_sensitive_runtime_or_outputs_content(
    tmp_path: Path,
) -> None:
    source = ROOT / "experiments/exp020/prepare_cloud_runtime.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    assert not any(name.startswith(("torch", "transformers", "safetensors")) for name in imports)
    assert not any("run_exp020a" in name for name in imports)
    source_text = source.read_text(encoding="utf-8")
    assert "exp020a_results" not in source_text

    secret = "FORMAL_CONTENT_MUST_NOT_BE_EMITTED"
    invalid_metadata = tmp_path / "metadata.json"
    invalid_metadata.write_text(json.dumps(secret), encoding="utf-8")
    with pytest.raises(runtime.CloudRuntimePreparationError) as captured:
        runtime._load_json(invalid_metadata)
    assert secret not in str(captured.value)


def test_preparation_refuses_non_linux_execution(tmp_path: Path) -> None:
    with pytest.raises(runtime.CloudRuntimePreparationError, match="Linux target checkout"):
        runtime.prepare_cloud_runtime(tmp_path, tmp_path / "manifest.json", tmp_path / "model")
