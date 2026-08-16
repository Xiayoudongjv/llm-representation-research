"""EXP-021 neutral hook qualification and FIT-only Stage-Q infrastructure.

The module is intentionally import-safe.  Importing it performs no file or
network access and imports no model-runtime package.  Model-runtime imports
are confined to the two execution functions, which are never called by the
static preflight or by the synthetic test suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


EXPERIMENT = "EXP-021"
SCHEMA_VERSION = "1.0.0"
AUTHORITY_ARCHIVE_COMMIT = "db11ff7a1ab90ad05c7aaf7451b6dba206bdeb8e"
AUTHORITY_ARCHIVE_PARENT = "163112e91bfed2576b87827672c21b49df75f0e2"
ORIGINAL_PREREGISTRATION_SHA256 = (
    "2ea9c54a49c41b3c1c8e6c39b029dc333d3ee6753ae0608603d6365ae063301a"
)
AMENDMENT_SHA256 = (
    "c026587c90b74d75e9f395001f94732d41f3b550c22247e5613cc6d3cc880635"
)
AMENDMENT_BLOB_OID = "7a71dcc767db4a785fd3fdee2d75681427ae76f6"
RECONCILIATION_BLOB_OID = "08d621f311dbc1c9c2c00ef024cdc42a6ac3c6f7"
RECONCILIATION_SHA256 = (
    "4630a253db1454c9b6cb0850bf6f99cf61781d44e48e37994cba8e1c6d47da95"
)

AUTHORITY_ORIGINAL = Path("docs/experiments/EXP-021-PREREGISTRATION.md")
AUTHORITY_AMENDMENT = Path(
    "docs/experiments/EXP-021-PREREGISTRATION-AMENDMENT-01-DRAFT.md"
)
AUTHORITY_RECONCILIATION = Path(
    "experiments/exp021/exp021_preregistration_reconciliation.json"
)
AUTHORIZATION_ARCHIVE_RELATIVE_DIR = Path(
    "experiments/exp021/authorization/archive/superseded_unconsumed_nonexecutable"
)
AUTHORIZATION_DISPOSITION_RELATIVE_DIR = Path(
    "experiments/exp021/authorization/dispositions"
)
AUTHORIZATION_DISPOSITION_JOURNAL_RELATIVE_DIR = Path(
    "experiments/exp021/authorization/disposition_journal"
)
AUTHORIZATION_DISPOSITION_TYPE = "SUPERSEDED_UNCONSUMED_NONEXECUTABLE"
EXP020_CONFIG = Path("experiments/exp020/exp020_frozen_config.json")
NEUTRAL_RESULT_RELATIVE_PATH = Path("experiments/exp021/engineering/neutral_result.json")
NEUTRAL_CONSUMPTION_RELATIVE_PATH = Path("experiments/exp021/consumed/neutral.json")
STAGE_Q_RESULT_RELATIVE_PATH = Path("experiments/exp021/engineering/stage_q_result.json")
STAGE_Q_CONSUMPTION_RELATIVE_PATH = Path("experiments/exp021/consumed/stage_q.json")
STAGE_Q_CONSUMPTION_ARCHIVE_RELATIVE_DIR = Path(
    "experiments/exp021/consumed/archive/stage_q"
)
STAGE_Q_CONSUMPTION_ARCHIVE_JOURNAL_RELATIVE_DIR = Path(
    "experiments/exp021/consumed/archive/stage_q_journal"
)
STAGE_Q_CONSUMPTION_ARCHIVE_STATUS_RELATIVE_DIR = Path(
    "experiments/exp021/consumed/archive/stage_q_status"
)
STAGE_Q_AUTHORIZATION_ARCHIVE_RELATIVE_DIR = Path(
    "experiments/exp021/authorization/archive/consumed_stage_q"
)
RUNNER_IMPLEMENTATION_RELATIVE_PATH = Path("experiments/exp021/run_exp021_stage_q.py")
VALIDATOR_IMPLEMENTATION_RELATIVE_PATH = Path("experiments/exp021/validate_exp021_stage_q_implementation.py")
EXPECTED_NEUTRAL_RESULT_SHA256 = "0a6273050e6c9974e917ea4de4865bc8428a5b7f634a32c29d8a634ae49c9bf1"
EXPECTED_NEUTRAL_PRODUCER_COMMIT = "6d828cafc5c22926cdfce5060118b1dcaf15aeb4"
EXPECTED_NEUTRAL_PRODUCER_RUNNER_SHA256 = "eb083ccb216b6d2987cf5de217fc1bb3f6361af4cebf0f702c63560b83715259"
EXPECTED_NEUTRAL_PRODUCER_VALIDATOR_SHA256 = "3ba0c0e32596c2cdaf35740f4410162b9d681684d95b759ea626c2b3b1170ee4"
LIFECYCLE_EXPERIMENT_DIR = Path("experiments/exp021")
LIFECYCLE_MODE_STATIC = "static"
LIFECYCLE_MODE_NEUTRAL = "neutral"
LIFECYCLE_MODE_STAGE_Q = "stage_q"
LIFECYCLE_ACTIVE_AUTHORIZATION_PATHS = {
    Path("experiments/exp021/authorization/neutral.json"): "neutral",
    Path("experiments/exp021/authorization/stage_q.json"): "stage_q",
}
LIFECYCLE_CONSUMPTION_PATHS = {
    Path("experiments/exp021/consumed/neutral.json"): "neutral",
    Path("experiments/exp021/consumed/stage_q.json"): "stage_q",
}
LIFECYCLE_ENGINEERING_RESULT_PATHS = {
    Path("experiments/exp021/engineering/neutral_result.json"): "neutral",
    Path("experiments/exp021/engineering/stage_q_result.json"): "stage_q",
}
LIFECYCLE_KNOWN_DIRECTORIES = {
    Path("experiments/exp021/authorization"),
    Path("experiments/exp021/authorization/archive"),
    Path("experiments/exp021/authorization/archive/superseded_unconsumed_nonexecutable"),
    Path("experiments/exp021/authorization/archive/consumed_stage_q"),
    Path("experiments/exp021/authorization/dispositions"),
    Path("experiments/exp021/authorization/disposition_journal"),
    Path("experiments/exp021/consumed"),
    Path("experiments/exp021/consumed/archive"),
    Path("experiments/exp021/consumed/archive/stage_q"),
    Path("experiments/exp021/consumed/archive/stage_q_journal"),
    Path("experiments/exp021/consumed/archive/stage_q_status"),
    Path("experiments/exp021/engineering"),
}
LIFECYCLE_SCAN_DIRECTORIES = {
    Path("experiments/exp021/authorization"),
    Path("experiments/exp021/consumed"),
    Path("experiments/exp021/engineering"),
}
LIFECYCLE_LEGACY_CONTAMINATION_PATHS = {
    Path("experiments/exp021/results"),
    Path("experiments/exp021/neutral_qualification_result.json"),
    Path("experiments/exp021/stage_q_result.json"),
}
NEUTRAL_DIAGNOSTIC_TEXT = "A neutral diagnostic sentence is used for engineering qualification."
EXPECTED_SHARD_FILES = {"model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors"}
EXP020_CONFIG_SHA256 = "f760f781b4b744a10938eb4de032e0cc345a021706821ecf0ca8523f5d57e667"

CHECKPOINTS = (
    {"name": "intervention", "block_index": 16, "hidden_state_index": 17, "role": "primary"},
    {"name": "normalized_0.625", "block_index": 17, "hidden_state_index": 18, "role": "required"},
    {"name": "normalized_0.75", "block_index": 20, "hidden_state_index": 21, "role": "required"},
    {"name": "normalized_0.875", "block_index": 24, "hidden_state_index": 25, "role": "required"},
    {"name": "final_block_pre_final_rmsnorm", "block_index": 27, "hidden_state_index": None, "role": "required"},
    {"name": "final_normalized_hidden_state", "block_index": 27, "hidden_state_index": 28, "role": "descriptive"},
)
CHECKPOINT_MAPPING_METADATA_KEYS = frozenset({"num_transformer_blocks", "tuple_semantics"})
TUPLE_SEMANTICS_FROZEN_TEXT = (
    "hidden_states[0] is embedding output; "
    "hidden_states[1..27] are decoder block outputs before final RMSNorm; "
    "hidden_states[28] is the post-final-RMSNorm last_hidden_state in the inspected Qwen3 Transformers implementation."
)
REQUIRED_GATE_CHECKPOINTS = tuple(
    checkpoint["name"] for checkpoint in CHECKPOINTS if checkpoint["role"] != "descriptive"
)
INTERVENTION_BLOCK = 16
INTERVENTION_HIDDEN_STATE_INDEX = 17
BETA = 0.75
CLASS_ORDER = ("logic", "causality", "analogy", "definition")
STAGE_Q_SCOPE = "EXP021_STAGE_Q_FIT_ONLY_MEASUREMENT_QUALIFICATION"
NEUTRAL_SCOPE = "NEUTRAL_HOOK_ORACLE_QUALIFICATION"

DISPOSITION_STATE_ACTIVE = "ACTIVE"
DISPOSITION_STATE_PREPARED = "PREPARED"
DISPOSITION_STATE_PREPARED_OR_IN_PROGRESS = "PREPARED_OR_IN_PROGRESS"
DISPOSITION_STATE_DISPOSITIONED = "DISPOSITIONED"
DISPOSITION_STATE_PARTIAL_OR_RECOVERY_REQUIRED = "PARTIAL_OR_RECOVERY_REQUIRED"
DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT = "AMBIGUOUS_OR_CORRUPT"
DISPOSITION_STATE_CLEAR = "CLEAR"

STAGE_Q_ARCHIVE_TYPE = "CONSUMED_STAGE_Q_TECHNICALLY_INVALID_NO_RESULT"
STAGE_Q_ARCHIVE_STATE_ACTIVE = "ACTIVE"
STAGE_Q_ARCHIVE_STATE_PREPARED = "PREPARED"
STAGE_Q_ARCHIVE_STATE_PREPARED_OR_IN_PROGRESS = "PREPARED_OR_IN_PROGRESS"
STAGE_Q_ARCHIVE_STATE_ARCHIVED = "ARCHIVED"
STAGE_Q_ARCHIVE_STATE_PARTIAL_OR_RECOVERY_REQUIRED = "PARTIAL_OR_RECOVERY_REQUIRED"
STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT = "AMBIGUOUS_OR_CORRUPT"
STAGE_Q_ARCHIVE_STATE_CLEAR = "CLEAR"

DISPOSITION_RECORD_KEYS = frozenset(
    {
        "schema_version", "experiment", "disposition_type", "authorization_id",
        "authorization_sha256", "authorization_scope", "authorization_runner_commit",
        "authorization_runner_sha256", "authorization_consumed",
        "consumption_record_exists", "qualification_result_exists",
        "non_executable_reason", "replacement_automatically_authorized",
        "original_can_never_be_consumed", "archived_authorization_path",
        "disposition_record_id", "disposition_timestamp",
        "explicit_disposition_authorized", "transaction_id", "state",
        "journal_sha256",
    }
)
DISPOSITION_JOURNAL_KEYS = frozenset(
    {
        "schema_version", "experiment", "disposition_type", "authorization_id",
        "authorization_sha256", "authorization_scope", "authorization_runner_commit",
        "authorization_runner_sha256", "transaction_id", "disposition_record_id",
        "state", "expected_archive_path", "expected_disposition_path",
        "non_executable_reason", "created_at", "updated_at",
        "explicit_disposition_authorized", "journal_sha256",
    }
)

STAGE_Q_ARCHIVE_JOURNAL_KEYS = frozenset(
    {
        "schema_version", "experiment", "archive_type", "authorization_id",
        "authorization_sha256", "consumption_sha256", "attempt_id", "scope",
        "runner_commit", "transaction_id", "status_record_id", "state",
        "expected_authorization_archive_path", "expected_consumption_archive_path",
        "expected_status_path", "original_can_never_be_consumed", "result_exists",
        "attempt_outcome", "measurement_status", "created_at", "updated_at",
        "explicit_archival_authorized", "journal_sha256",
    }
)

STAGE_Q_TERMINAL_ATTEMPT_STATUS_KEYS = frozenset(
    {
        "schema_version", "experiment", "status_type", "authorization_id",
        "authorization_sha256", "consumption_sha256", "attempt_id", "scope",
        "runner_commit", "transaction_id", "status_record_id",
        "authorization_archive_path", "consumption_archive_path",
        "journal_sha256", "attempt_outcome", "measurement_status",
        "result_exists", "original_can_never_be_consumed", "created_at", "state",
    }
)

COMMON_AUTHORIZATION_KEYS = frozenset(
    {
        "schema_version", "experiment", "scope", "authorization_id",
        "issued_at", "expires_at", "runner_commit", "runner_sha256",
        "implementation_hashes", "authority_hashes", "model_manifest", "environment_binding",
        "allowed_output_path", "maximum_launch_count", "fit_access_permitted",
        "eval_access_permitted", "scientific_result_permitted",
        "automatic_retry_permitted",
    }
)
NEUTRAL_AUTHORIZATION_KEYS = frozenset(COMMON_AUTHORIZATION_KEYS)
CONSUMPTION_KEYS = frozenset(
    {
        "schema_version", "experiment", "authorization_hash", "attempt_id",
        "runner_commit", "acquired_at", "scope", "output_path", "state",
    }
)
NEUTRAL_RESULT_KEYS = frozenset(
    {
        "schema_version", "experiment", "result_classification", "attempt_id",
        "authorization_id", "authorization_hash", "runner_commit", "runner_sha256",
        "implementation_hashes", "authority_hashes", "model_manifest",
        "canonical_snapshot_path", "resolved_snapshot_path", "execution_environment",
        "hook_block", "token_rule", "beta", "diagnostic_vector", "neutral_input_identity",
        "cache_semantics", "checks", "started_at", "finished_at", "fit_eval_accessed",
        "scientific_result_created", "overall_pass",
    }
)
NEUTRAL_EXECUTION_ENVIRONMENT_KEYS = frozenset(
    {
        "python", "torch", "transformers", "cuda_runtime", "nvidia_driver", "gpu",
        "dtype", "device", "local_files_only", "model_eval_mode",
        "gradients_enabled", "use_cache",
    }
)
NEUTRAL_DIAGNOSTIC_VECTOR_KEYS = frozenset({"algorithm", "length", "sha256"})
NEUTRAL_INPUT_IDENTITY_KEYS = frozenset({"sha256"})
RUNTIME_IDENTITY_KEYS = frozenset(
    {"python", "torch", "transformers", "cuda_runtime", "nvidia_driver", "gpu"}
)
STAGE_Q_AUTHORIZATION_KEYS = frozenset(
    {
        *COMMON_AUTHORIZATION_KEYS,
        "eval_access_permitted", "stage_p_intervention_permitted",
        "scientific_result_permitted", "per_checkpoint_probe_refit_permitted",
    }
)
STAGE_Q_RESULT_KEYS = frozenset(
    {
        "schema_version", "experiment", "result_classification", "runner_commit",
        "runner_sha256", "implementation_hashes", "authority_hashes", "model_manifest",
        "canonical_snapshot_path", "resolved_snapshot_path", "neutral_result_binding",
        "stage_q_authorization_binding",
        "split_summaries", "checkpoint_summaries", "processed_fit_ids",
        "checkpoint_mapping", "execution_environment", "created_at",
        "eval_accessed", "prompt_content_printed", "stage_p_accessed",
        "scientific_result_created", "global_pass", "descriptive_post_norm",
    }
)


class ProtocolError(RuntimeError):
    """Raised when a frozen protocol or authorization check fails."""


def sha256_bytes(data: bytes) -> str:
    """Return the SHA-256 digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Hash a file incrementally without materializing large model files."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json_no_duplicates(path: str | Path) -> dict[str, Any]:
    """Read UTF-8 JSON and reject duplicate object keys."""

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProtocolError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            value = json.load(handle, object_pairs_hook=hook)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"Cannot parse UTF-8 JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ProtocolError(f"Expected a JSON object: {path}")
    return value


def read_json_value_no_duplicates(path: str | Path) -> Any:
    """Read any UTF-8 JSON value while rejecting duplicate object keys."""

    def hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProtocolError(f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    try:
        with Path(path).open("r", encoding="utf-8") as handle:
            return json.load(handle, object_pairs_hook=hook)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ProtocolError(f"Cannot parse UTF-8 JSON: {path}") from exc


def require_exact_keys(value: Mapping[str, Any], expected: Iterable[str], label: str) -> None:
    """Reject missing and unknown keys in a closed protocol object."""
    expected_set = set(expected)
    actual_set = set(value)
    if actual_set != expected_set:
        missing = sorted(expected_set - actual_set)
        unknown = sorted(actual_set - expected_set)
        raise ProtocolError(f"{label} keys differ; missing={missing}, unknown={unknown}")


def require_bool(value: Any, label: str) -> bool:
    """Require a real JSON boolean, not an integer that happens to compare equal."""
    if not isinstance(value, bool):
        raise ProtocolError(f"{label} must be boolean")
    return value


def require_string(value: Any, label: str, *, nonempty: bool = True) -> str:
    """Require a strict string field."""
    if not isinstance(value, str) or (nonempty and not value):
        raise ProtocolError(f"{label} must be a non-empty string")
    return value


def parse_timestamp(value: Any, label: str) -> datetime:
    """Parse a timezone-aware ISO-8601 timestamp."""
    text = require_string(value, label)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ProtocolError(f"{label} is not a valid ISO-8601 timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ProtocolError(f"{label} must include a timezone")
    return parsed.astimezone(timezone.utc)


def require_finite_number(value: Any, label: str) -> float:
    """Require a finite non-boolean number."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ProtocolError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ProtocolError(f"{label} must be finite")
    return result


def confined_path(path: str | Path, root: str | Path, *, allow_missing: bool = False) -> Path:
    """Resolve a path and reject traversal or symlink escape from ``root``."""
    root_path = Path(root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root_path / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root_path)
    except ValueError as exc:
        raise ProtocolError(f"Path escapes permitted root: {path}") from exc
    if not allow_missing and not resolved.exists():
        raise ProtocolError(f"Required path does not exist: {resolved}")
    return resolved


def atomic_publish_json(path: str | Path, payload: Mapping[str, Any], root: str | Path) -> Path:
    """Publish JSON once with exclusive creation and no overwrite."""
    destination = confined_path(path, root, allow_missing=True)
    if not destination.parent.is_dir():
        raise ProtocolError(f"Required publication parent is missing: {destination.parent}")
    serialized = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    try:
        with destination.open("x", encoding="utf-8", newline="") as handle:
            handle.write(serialized)
    except FileExistsError as exc:
        raise ProtocolError(f"Refusing to overwrite existing result: {destination}") from exc
    return destination


def _git_output(repo_root: Path, *args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=repo_root, text=True).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProtocolError(f"Git identity check failed: git {' '.join(args)}") from exc


def _git_blob_sha256(repo_root: Path, commit: str, relative_path: str) -> str:
    """Return the SHA-256 of a committed Git blob without changing live HEAD."""
    try:
        blob = subprocess.check_output(
            ["git", "show", f"{commit}:{relative_path}"],
            cwd=repo_root,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProtocolError(
            f"Historical Git blob unavailable: {commit}:{relative_path}"
        ) from exc
    return sha256_bytes(blob)


def _validate_safetensors_header(path: Path) -> None:
    """Validate only the small safetensors header and offsets, never tensor payloads."""
    try:
        with path.open("rb") as handle:
            prefix = handle.read(8)
            if len(prefix) != 8:
                raise ProtocolError(f"Short safetensors header: {path}")
            header_length = int.from_bytes(prefix, "little")
            header_bytes = handle.read(header_length)
            header = json.loads(header_bytes.decode("utf-8"))
        payload_size = path.stat().st_size - 8 - header_length
        tensors = [value for key, value in header.items() if key != "__metadata__"]
        if not tensors or any(
            not isinstance(value.get("data_offsets"), list)
            or len(value["data_offsets"]) != 2
            or not 0 <= value["data_offsets"][0] <= value["data_offsets"][1] <= payload_size
            for value in tensors
        ):
            raise ProtocolError(f"Invalid safetensors offsets: {path}")
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ProtocolError(f"Invalid safetensors header: {path}") from exc


def validate_model_manifest(identity: Mapping[str, Any], *, verify_payload: bool = False) -> None:
    """Validate manifest metadata, optionally streaming payload hashes after authorization."""
    required_identity = {
        "model_id": "Qwen/Qwen3-1.7B",
        "architecture": "Qwen3ForCausalLM",
        "model_type": "qwen3",
        "transformer_blocks": 28,
        "hidden_size": 2048,
        "vocab_size": 151936,
        "execution_dtype": "float16",
        "execution_device": "cuda:0",
        "local_files_only": True,
        "network_access_permitted": False,
        "model_eval_mode": True,
        "gradients_enabled": False,
        "use_cache": False,
    }
    for key, expected in required_identity.items():
        if identity.get(key) != expected:
            raise ProtocolError(f"Model identity mismatch for {key}")
    snapshot = confined_path(identity["resolved_snapshot_path"], identity["resolved_snapshot_path"])
    if snapshot != Path(identity["canonical_snapshot_path"]).resolve():
        raise ProtocolError("Canonical and resolved snapshot paths differ")
    manifest = identity.get("file_manifest")
    if not isinstance(manifest, list) or len(manifest) != 7:
        raise ProtocolError("The prospective manifest must contain seven files")
    entries: dict[str, tuple[int, str]] = {}
    for item in manifest:
        if set(item) != {"file", "bytes", "sha256"}:
            raise ProtocolError("Manifest entry schema mismatch")
        filename = item["file"]
        if (
            not isinstance(filename, str)
            or Path(filename).name != filename
            or not isinstance(item["bytes"], int)
            or isinstance(item["bytes"], bool)
            or not isinstance(item["sha256"], str)
            or len(item["sha256"]) != 64
        ):
            raise ProtocolError("Manifest contains a non-local filename")
        if filename in entries:
            raise ProtocolError("Duplicate manifest filename")
        entries[filename] = (item["bytes"], item["sha256"])
        file_path = snapshot / filename
        if not file_path.is_file() or file_path.is_symlink():
            raise ProtocolError(f"Manifest file is not a regular file: {file_path}")
        if file_path.stat().st_size != item["bytes"]:
            raise ProtocolError(f"Manifest hash mismatch: {file_path}")
        if verify_payload and sha256_file(file_path) != item["sha256"]:
            raise ProtocolError(f"Manifest hash mismatch: {file_path}")
    expected_shards = EXPECTED_SHARD_FILES
    index_path = snapshot / "model.safetensors.index.json"
    index = read_json_no_duplicates(index_path)
    references = set(index.get("weight_map", {}).values())
    if references != expected_shards or index.get("metadata", {}).get("total_size") != 4063479808:
        raise ProtocolError("Safetensors index does not match the frozen two-shard manifest")
    if any(Path(name).is_absolute() or ".incomplete" in name for name in references):
        raise ProtocolError("Safetensors index contains an unsafe reference")
    if verify_payload:
        for shard in expected_shards:
            _validate_safetensors_header(snapshot / shard)


def validate_authority_files(repo_root: str | Path, *, verify_model_files: bool = False) -> dict[str, Any]:
    """Validate archived authority identities and return the reconciliation object."""
    root = Path(repo_root).resolve()
    original = root / AUTHORITY_ORIGINAL
    amendment = root / AUTHORITY_AMENDMENT
    reconciliation = root / AUTHORITY_RECONCILIATION
    if sha256_file(original) != ORIGINAL_PREREGISTRATION_SHA256:
        raise ProtocolError("Original preregistration hash mismatch")
    if sha256_file(amendment) != AMENDMENT_SHA256:
        raise ProtocolError("Archived amendment hash mismatch")
    if sha256_file(reconciliation) != RECONCILIATION_SHA256:
        raise ProtocolError("Archived reconciliation hash mismatch")
    if _git_output(root, "ls-tree", AUTHORITY_ARCHIVE_COMMIT, str(AUTHORITY_AMENDMENT)).split()[2] != AMENDMENT_BLOB_OID:
        raise ProtocolError("Amendment Git blob mismatch")
    if _git_output(root, "ls-tree", AUTHORITY_ARCHIVE_COMMIT, str(AUTHORITY_RECONCILIATION)).split()[2] != RECONCILIATION_BLOB_OID:
        raise ProtocolError("Reconciliation Git blob mismatch")
    data = read_json_no_duplicates(reconciliation)
    if data.get("overall_status") != "EXP021_AMENDMENT_READY_FOR_TARGETED_FINAL_REREVIEW":
        raise ProtocolError("Unexpected amendment readiness status")
    if data.get("hook_oracle_protocol_status") != "FROZEN":
        raise ProtocolError("Hook protocol is not frozen")
    if data.get("hook_oracle_runtime_qualification_status") != "NOT_RUN":
        raise ProtocolError("Hook runtime qualification must remain not run")
    if data.get("hook_oracle_runtime_qualified") is not False:
        raise ProtocolError("Hook runtime qualification status mismatch")
    if data.get("stage_q_authorizable") is not False or data.get("stage_p_authorizable") is not False:
        raise ProtocolError("Stage authorization boundary is open")
    statuses = {item["id"]: item["status"] for item in data["open_decision_statuses"]}
    if statuses.get("R17") != "RESOLVED_BY_TRANSPARENT_PROSPECTIVE_PRE_RUN_AMENDMENT":
        raise ProtocolError("R17 status mismatch")
    if statuses.get("R20") != "RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT":
        raise ProtocolError("R20 status mismatch")
    if statuses.get("R22") != "REMAINS_OPEN_NONBLOCKING":
        raise ProtocolError("R22 status mismatch")
    validate_model_manifest(data["primary_model_identity"], verify_payload=verify_model_files)
    validate_checkpoint_mapping(data["checkpoint_mapping"])
    checkpoint = data["checkpoint_mapping"]["intervention"]
    if (checkpoint["block_index"], checkpoint["hidden_state_index"], checkpoint["beta"]) != (16, 17, 0.75):
        raise ProtocolError("Intervention checkpoint mismatch")
    threshold = data["stage_q_fit_only_measurement_qualification"]["qualification_metrics"]["threshold_verification"]
    if threshold != {
        "correct": 7,
        "total": 12,
        "lower_bound": 0.276669685682,
        "strictly_greater_than_chance": True,
        "interval_definition": "scipy.stats.beta.ppf(0.025, correct, total-correct+1)",
    }:
        raise ProtocolError("Stage-Q statistical rule mismatch")
    return data


def _is_unsafe_lifecycle_entry(path: Path) -> bool:
    """Return True for symlinks, junctions, or other reparse-style ambiguity."""
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if callable(is_junction) and is_junction():
            return True
    except OSError:
        return True
    return False


def _matches_disposition_file(path: Path, directory: Path) -> bool:
    """Return True when path is exactly one SHA-256-named JSON child of directory."""
    try:
        relative = path.relative_to(directory)
    except ValueError:
        return False
    return len(relative.parts) == 1 and re.fullmatch(r"[0-9a-f]{64}\.json", relative.name) is not None


def inspect_lifecycle_paths(repo_root: str | Path) -> dict[str, Any]:
    """Return the closed-world lifecycle path state for EXP-021 mutable artifacts."""
    root = Path(repo_root).resolve()
    state: dict[str, Any] = {
        "root": root,
        "active_neutral": None,
        "active_stage_q": None,
        "consumed_neutral": None,
        "consumed_stage_q": None,
        "engineering_neutral": None,
        "engineering_stage_q": None,
        "retained_authorizations": {},
        "disposition_archives": [],
        "disposition_journals": [],
        "disposition_records": [],
        "stage_q_authorization_archives": [],
        "stage_q_consumption_archives": [],
        "stage_q_consumption_journals": [],
        "stage_q_consumption_statuses": [],
        "unknown_paths": [],
        "legacy_contamination": [],
    }
    authorization_files: dict[str, Path] = {}
    consumption_files: dict[str, Path] = {}
    for scan_relative in sorted(LIFECYCLE_SCAN_DIRECTORIES, key=lambda path: path.as_posix()):
        scan_root = root / scan_relative
        if not os.path.lexists(scan_root):
            continue
        if _is_unsafe_lifecycle_entry(scan_root):
            raise ProtocolError(f"Unsafe lifecycle path: {scan_relative.as_posix()}")
        if not scan_root.is_dir():
            raise ProtocolError(f"Lifecycle scan root is not a directory: {scan_relative.as_posix()}")
        for dirpath, dirnames, filenames in os.walk(scan_root, topdown=True, followlinks=False):
            current = Path(dirpath)
            for dirname in list(dirnames):
                child = current / dirname
                relative = child.relative_to(root).as_posix()
                if _is_unsafe_lifecycle_entry(child):
                    state["unknown_paths"].append(relative)
                    dirnames.remove(dirname)
                    continue
                if Path(relative) not in LIFECYCLE_KNOWN_DIRECTORIES:
                    state["unknown_paths"].append(relative)
                    dirnames.remove(dirname)
                    continue
            for filename in filenames:
                child = current / filename
                relative = child.relative_to(root).as_posix()
                if _is_unsafe_lifecycle_entry(child):
                    state["unknown_paths"].append(relative)
                    continue
                relative_path = Path(relative)
                if relative_path in LIFECYCLE_ACTIVE_AUTHORIZATION_PATHS:
                    scope = LIFECYCLE_ACTIVE_AUTHORIZATION_PATHS[relative_path]
                    authorization_files[scope] = child
                elif relative_path in LIFECYCLE_CONSUMPTION_PATHS:
                    scope = LIFECYCLE_CONSUMPTION_PATHS[relative_path]
                    consumption_files[scope] = child
                elif relative_path in LIFECYCLE_ENGINEERING_RESULT_PATHS:
                    scope = LIFECYCLE_ENGINEERING_RESULT_PATHS[relative_path]
                    if scope == "neutral":
                        state["engineering_neutral"] = child
                    else:
                        state["engineering_stage_q"] = child
                elif _matches_disposition_file(relative_path, AUTHORIZATION_ARCHIVE_RELATIVE_DIR):
                    state["disposition_archives"].append(relative)
                elif _matches_disposition_file(relative_path, AUTHORIZATION_DISPOSITION_JOURNAL_RELATIVE_DIR):
                    state["disposition_journals"].append(relative)
                elif _matches_disposition_file(relative_path, AUTHORIZATION_DISPOSITION_RELATIVE_DIR):
                    state["disposition_records"].append(relative)
                elif _matches_disposition_file(relative_path, STAGE_Q_AUTHORIZATION_ARCHIVE_RELATIVE_DIR):
                    state["stage_q_authorization_archives"].append(relative)
                elif _matches_disposition_file(relative_path, STAGE_Q_CONSUMPTION_ARCHIVE_RELATIVE_DIR):
                    state["stage_q_consumption_archives"].append(relative)
                elif _matches_disposition_file(relative_path, STAGE_Q_CONSUMPTION_ARCHIVE_JOURNAL_RELATIVE_DIR):
                    state["stage_q_consumption_journals"].append(relative)
                elif _matches_disposition_file(relative_path, STAGE_Q_CONSUMPTION_ARCHIVE_STATUS_RELATIVE_DIR):
                    state["stage_q_consumption_statuses"].append(relative)
                else:
                    state["unknown_paths"].append(relative)
    for legacy_relative in LIFECYCLE_LEGACY_CONTAMINATION_PATHS:
        legacy_path = root / legacy_relative
        if os.path.lexists(legacy_path):
            state["legacy_contamination"].append(legacy_relative.as_posix())
    for scope, expected_scope in (
        ("neutral", NEUTRAL_SCOPE),
        ("stage_q", STAGE_Q_SCOPE),
    ):
        authorization_path = authorization_files.get(scope)
        consumption_path = consumption_files.get(scope)
        if authorization_path is None:
            if consumption_path is not None:
                raise ProtocolError(
                    f"{scope} consumption record exists without a retained authorization identity"
                )
            continue
        if consumption_path is None:
            state[f"active_{scope}"] = authorization_path
            continue
        _classify_consumed_authorization(
            root,
            state,
            scope,
            expected_scope,
            authorization_path,
            consumption_path,
        )
    return state


def _authorization_keys_for_scope(scope: str) -> frozenset[str]:
    """Return the closed authorization schema for one lifecycle scope."""
    if scope == NEUTRAL_SCOPE:
        return NEUTRAL_AUTHORIZATION_KEYS
    if scope == STAGE_Q_SCOPE:
        return STAGE_Q_AUTHORIZATION_KEYS
    raise ProtocolError(f"Unsupported authorization scope: {scope}")


def _validate_retained_authorization_identity(
    authorization_path: Path, expected_scope: str
) -> dict[str, Any]:
    """Validate a retained authorization sufficiently for consumption correlation."""
    authorization = read_json_no_duplicates(authorization_path)
    require_exact_keys(
        authorization,
        _authorization_keys_for_scope(expected_scope),
        "retained authorization",
    )
    if authorization["schema_version"] != SCHEMA_VERSION or authorization["experiment"] != EXPERIMENT:
        raise ProtocolError("Retained authorization schema identity mismatch")
    if authorization["scope"] != expected_scope:
        raise ProtocolError("Retained authorization scope mismatch")
    require_string(authorization["authorization_id"], "authorization_id")
    require_string(authorization["runner_commit"], "runner_commit")
    runner_sha256 = require_string(authorization["runner_sha256"], "runner_sha256")
    if len(runner_sha256) != 64:
        raise ProtocolError("Retained authorization runner_sha256 must be a SHA-256 digest")
    return authorization


def _validate_consumption_identity(
    consumption_path: Path, expected_scope: str
) -> dict[str, Any]:
    """Validate a canonical consumption record for lifecycle correlation."""
    consumption = read_json_no_duplicates(consumption_path)
    require_exact_keys(consumption, CONSUMPTION_KEYS, "consumption record")
    if consumption["schema_version"] != SCHEMA_VERSION or consumption["experiment"] != EXPERIMENT:
        raise ProtocolError("Consumption record schema identity mismatch")
    if consumption["scope"] != expected_scope:
        raise ProtocolError("Consumption record scope mismatch")
    if consumption["state"] != "consumed":
        raise ProtocolError("Consumption record state must be consumed")
    authorization_hash = require_string(consumption["authorization_hash"], "authorization_hash")
    if len(authorization_hash) != 64:
        raise ProtocolError("Consumption authorization_hash must be a SHA-256 digest")
    require_string(consumption["attempt_id"], "attempt_id")
    require_string(consumption["runner_commit"], "runner_commit")
    require_string(consumption["output_path"], "output_path")
    parse_timestamp(consumption["acquired_at"], "acquired_at")
    return consumption


def _classify_consumed_authorization(
    root: Path,
    state: dict[str, Any],
    scope: str,
    expected_scope: str,
    authorization_path: Path,
    consumption_path: Path,
) -> None:
    """Classify a retained authorization as consumed, never active, when identity matches."""
    authorization = _validate_retained_authorization_identity(authorization_path, expected_scope)
    consumption = _validate_consumption_identity(consumption_path, expected_scope)
    authorization_hash = sha256_file(authorization_path)
    if consumption["authorization_hash"] != authorization_hash:
        raise ProtocolError("Consumption authorization hash does not match retained authorization")
    if consumption["runner_commit"] != authorization["runner_commit"]:
        raise ProtocolError("Consumption runner commit does not match retained authorization")
    state[f"active_{scope}"] = None
    state[f"consumed_{scope}"] = consumption_path
    state["retained_authorizations"][scope] = authorization_path


def _lifecycle_artifact_sha256(relative: str) -> str | None:
    """Return the lowercase SHA-256 digest encoded in a canonical disposition path."""
    try:
        name = Path(relative).name
    except Exception:
        return None
    if not name.endswith(".json"):
        return None
    digest = name[:-5]
    if re.fullmatch(r"[0-9a-f]{64}", digest):
        return digest
    return None


def _group_disposition_artifacts(state: Mapping[str, Any]) -> dict[str, dict[str, list[str]]]:
    """Group canonical disposition paths by their encoded authorization SHA-256."""
    groups: dict[str, dict[str, list[str]]] = {}
    for kind in ("archives", "journals", "records"):
        for relative in state[f"disposition_{kind}"]:
            digest = _lifecycle_artifact_sha256(relative)
            if digest is None:
                raise ProtocolError(f"Disposition artifact has an invalid identity: {relative}")
            group = groups.setdefault(digest, {"archives": [], "journals": [], "records": []})
            group[kind].append(relative)
    return groups


def _group_stage_q_archive_artifacts(
    state: Mapping[str, Any],
) -> dict[str, dict[str, list[str]]]:
    """Group consumed Stage-Q archive paths by their encoded authorization SHA-256."""
    groups: dict[str, dict[str, list[str]]] = {}
    for kind, state_key in (
        ("authorization_archives", "stage_q_authorization_archives"),
        ("consumption_archives", "stage_q_consumption_archives"),
        ("journals", "stage_q_consumption_journals"),
        ("statuses", "stage_q_consumption_statuses"),
    ):
        for relative in state[state_key]:
            digest = _lifecycle_artifact_sha256(relative)
            if digest is None:
                raise ProtocolError(f"Stage-Q archive artifact has an invalid identity: {relative}")
            group = groups.setdefault(
                digest,
                {
                    "authorization_archives": [],
                    "consumption_archives": [],
                    "journals": [],
                    "statuses": [],
                },
            )
            group[kind].append(relative)
    return groups


def _validate_completed_stage_q_archive(
    root: Path,
    digest: str,
    group: Mapping[str, list[str]],
) -> None:
    """Require a historical consumed Stage-Q generation to be fully resolved and valid."""
    auth_archives = group["authorization_archives"]
    consumption_archives = group["consumption_archives"]
    journals = group["journals"]
    statuses = group["statuses"]
    if len(auth_archives) != 1 or len(consumption_archives) != 1 or len(journals) != 1 or len(statuses) != 1:
        raise ProtocolError(
            "Impossible lifecycle state: unresolved historical Stage-Q archive blocks replacement"
        )
    auth_rel = auth_archives[0]
    consumption_rel = consumption_archives[0]
    journal_rel = journals[0]
    status_rel = statuses[0]
    auth_path = root / auth_rel
    consumption_path = root / consumption_rel
    journal_path = root / journal_rel
    status_path = root / status_rel
    if sha256_file(auth_path) != digest:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization archive hash mismatch")
    authorization = read_json_no_duplicates(auth_path)
    require_exact_keys(authorization, STAGE_Q_AUTHORIZATION_KEYS, "archived Stage-Q authorization")
    if authorization["schema_version"] != SCHEMA_VERSION or authorization["experiment"] != EXPERIMENT:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization archive schema mismatch")
    if authorization["scope"] != STAGE_Q_SCOPE:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization archive scope mismatch")
    _validate_retained_authorization_identity(auth_path, STAGE_Q_SCOPE)
    if type(authorization["maximum_launch_count"]) is not int or authorization["maximum_launch_count"] != 1:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization must be single-launch")
    if authorization["automatic_retry_permitted"] is not False:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization must not permit retry")
    if authorization["fit_access_permitted"] is not True:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization must be FIT-scoped")
    if authorization["eval_access_permitted"] is not False or authorization["scientific_result_permitted"] is not False:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization has invalid data access")
    if authorization["stage_p_intervention_permitted"] is not False or authorization["per_checkpoint_probe_refit_permitted"] is not False:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q authorization has invalid Stage-P permissions")
    consumption = _validate_consumption_identity(consumption_path, STAGE_Q_SCOPE)
    consumption_hash = sha256_file(consumption_path)
    if consumption["authorization_hash"] != digest:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q consumption identity mismatch")
    journal = read_json_no_duplicates(journal_path)
    validate_stage_q_archive_journal(journal)
    status = read_json_no_duplicates(status_path)
    validate_stage_q_terminal_attempt_status(status)
    if journal["authorization_sha256"] != digest:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q archive journal identity mismatch")
    if journal["consumption_sha256"] != consumption_hash:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q archive journal consumption mismatch")
    if journal["attempt_id"] != consumption["attempt_id"]:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q archive journal attempt mismatch")
    if journal["expected_authorization_archive_path"] != auth_rel:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q archive journal auth path mismatch")
    if journal["expected_consumption_archive_path"] != consumption_rel:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q archive journal consumption path mismatch")
    if journal["expected_status_path"] != status_rel:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q archive journal status path mismatch")
    if status["authorization_sha256"] != digest:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status identity mismatch")
    if status["consumption_sha256"] != consumption_hash:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status consumption mismatch")
    if status["attempt_id"] != consumption["attempt_id"]:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status attempt mismatch")
    if status["authorization_id"] != authorization["authorization_id"]:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status auth ID mismatch")
    if status["runner_commit"] != authorization["runner_commit"]:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status runner mismatch")
    if status["authorization_archive_path"] != auth_rel:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status auth path mismatch")
    if status["consumption_archive_path"] != consumption_rel:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status consumption path mismatch")
    if status["journal_sha256"] != journal["journal_sha256"]:
        raise ProtocolError("Impossible lifecycle state: historical Stage-Q terminal status journal mismatch")


def _validate_stage_q_archive_identity_state(state: Mapping[str, Any]) -> None:
    """Reject same-authorization reactivation and unresolved Stage-Q archive states."""
    groups = _group_stage_q_archive_artifacts(state)
    if not groups:
        return
    root = Path(state["root"])
    active_paths = [
        path
        for path in (state["active_neutral"], state["active_stage_q"])
        if path is not None
    ]
    active_hashes = {sha256_file(path) for path in active_paths} if active_paths else set()
    consumed_stage_q_authorization_hash = None
    if state["consumed_stage_q"] is not None:
        canonical_consumption = _validate_consumption_identity(
            state["consumed_stage_q"], STAGE_Q_SCOPE
        )
        consumed_stage_q_authorization_hash = canonical_consumption["authorization_hash"]
    for digest, group in groups.items():
        if digest in active_hashes:
            raise ProtocolError("Impossible lifecycle state: active authorization has a consumed Stage-Q archive")
        if (
            consumed_stage_q_authorization_hash is not None
            and digest == consumed_stage_q_authorization_hash
        ):
            raise ProtocolError("Impossible lifecycle state: canonical consumed Stage-Q authorization has a historical archive")
        _validate_completed_stage_q_archive(root, digest, group)


def _validate_completed_historical_disposition(
    root: Path,
    digest: str,
    group: Mapping[str, list[str]],
    *,
    active_authorization_id: str | None,
) -> None:
    """Require a non-active disposition identity to be fully resolved and internally valid."""
    archives = group["archives"]
    journals = group["journals"]
    records = group["records"]
    if len(archives) != 1 or len(records) != 1:
        raise ProtocolError(
            "Impossible lifecycle state: unresolved historical disposition blocks a replacement authorization"
        )
    if len(journals) > 1:
        raise ProtocolError("Impossible lifecycle state: malformed historical disposition journal evidence")
    archive_rel = archives[0]
    record_rel = records[0]
    archive_path = root / archive_rel
    record_path = root / record_rel
    if sha256_file(archive_path) != digest:
        raise ProtocolError("Impossible lifecycle state: historical disposition archive hash mismatch")
    record = read_json_no_duplicates(record_path)
    validate_disposition_record(record)
    if record["authorization_sha256"] != digest:
        raise ProtocolError("Impossible lifecycle state: historical disposition identity mismatch")
    if active_authorization_id is not None and record["authorization_id"] == active_authorization_id:
        raise ProtocolError("Impossible lifecycle state: active authorization has a completed disposition")
    if record["authorization_scope"] not in {NEUTRAL_SCOPE, STAGE_Q_SCOPE}:
        raise ProtocolError("Impossible lifecycle state: historical disposition scope mismatch")
    archived = read_json_no_duplicates(archive_path)
    archived_keys = (
        NEUTRAL_AUTHORIZATION_KEYS
        if record["authorization_scope"] == NEUTRAL_SCOPE
        else STAGE_Q_AUTHORIZATION_KEYS
    )
    require_exact_keys(archived, archived_keys, "archived authorization")
    if archived["schema_version"] != SCHEMA_VERSION or archived["experiment"] != EXPERIMENT:
        raise ProtocolError("Impossible lifecycle state: historical disposition archive schema mismatch")
    if archived["scope"] != record["authorization_scope"]:
        raise ProtocolError("Impossible lifecycle state: historical disposition archive scope mismatch")
    if archived["authorization_id"] != record["authorization_id"]:
        raise ProtocolError("Impossible lifecycle state: historical disposition archive authorization ID mismatch")
    if (
        archived["runner_commit"] != record["authorization_runner_commit"]
        or archived["runner_sha256"] != record["authorization_runner_sha256"]
    ):
        raise ProtocolError("Impossible lifecycle state: historical disposition archive runner identity mismatch")
    expected_transaction_id, expected_record_id = _disposition_transaction_ids(digest)
    if record["transaction_id"] != expected_transaction_id or record["disposition_record_id"] != expected_record_id:
        raise ProtocolError("Impossible lifecycle state: historical disposition transaction identity mismatch")
    if record["archived_authorization_path"] != archive_rel:
        raise ProtocolError("Impossible lifecycle state: historical disposition archive path mismatch")
    if journals:
        journal_rel = journals[0]
        journal_path = root / journal_rel
        journal = read_json_no_duplicates(journal_path)
        validate_disposition_journal(journal)
        if journal["authorization_sha256"] != digest:
            raise ProtocolError("Impossible lifecycle state: historical disposition journal identity mismatch")
        if journal["transaction_id"] != expected_transaction_id or journal["disposition_record_id"] != expected_record_id:
            raise ProtocolError("Impossible lifecycle state: historical disposition journal transaction mismatch")
        if journal["expected_archive_path"] != archive_rel or journal["expected_disposition_path"] != record_rel:
            raise ProtocolError("Impossible lifecycle state: historical disposition journal path mismatch")
        if record["journal_sha256"] != journal["journal_sha256"]:
            raise ProtocolError("Impossible lifecycle state: historical disposition journal record mismatch")


def _validate_neutral_result_lifecycle_correlation(state: Mapping[str, Any]) -> None:
    """Require the retained neutral authorization, consumption, and result to bind."""
    if state["engineering_neutral"] is None:
        return
    if state["consumed_neutral"] is None:
        raise ProtocolError("Impossible lifecycle state: neutral qualification result without neutral consumption record")
    root = Path(state["root"])
    authorization_path = state.get("retained_authorizations", {}).get("neutral")
    if authorization_path is None:
        raise ProtocolError("Neutral qualification result exists without a retained neutral authorization identity")
    authorization = read_json_no_duplicates(authorization_path)
    consumption = read_json_no_duplicates(state["consumed_neutral"])
    result = read_json_no_duplicates(state["engineering_neutral"])
    require_exact_keys(result, NEUTRAL_RESULT_KEYS, "neutral result")
    if result["schema_version"] != SCHEMA_VERSION or result["experiment"] != EXPERIMENT:
        raise ProtocolError("Neutral result schema identity mismatch")
    if result["result_classification"] != "ENGINEERING_NEUTRAL_HOOK_QUALIFICATION_ONLY" or result["overall_pass"] is not True:
        raise ProtocolError("Neutral result is not a qualified engineering-only result")
    authorization_hash = sha256_file(authorization_path)
    if result["authorization_id"] != authorization["authorization_id"]:
        raise ProtocolError("Neutral result authorization ID does not match retained authorization")
    if result["authorization_hash"] != authorization_hash:
        raise ProtocolError("Neutral result authorization hash does not match retained authorization")
    if result["authorization_hash"] != consumption["authorization_hash"]:
        raise ProtocolError("Neutral result authorization hash does not match consumption record")
    if result["attempt_id"] != consumption["attempt_id"]:
        raise ProtocolError("Neutral result attempt ID does not match consumption record")
    if result["runner_commit"] != authorization["runner_commit"] or result["runner_sha256"] != authorization["runner_sha256"]:
        raise ProtocolError("Neutral result runner identity does not match retained authorization")


def _validate_no_impossible_lifecycle_state(state: Mapping[str, Any]) -> None:
    """Reject contradictory active/consumed/result/disposition combinations.

    Completed historical dispositions are grouped by authorization SHA-256 and
    may coexist with a later active authorization of a different identity.
    Same-identity active/disposition conflicts and unresolved prior generations
    remain fail closed.
    """
    if state["active_neutral"] is not None and state["active_stage_q"] is not None:
        raise ProtocolError("Impossible lifecycle state: multiple active authorizations")
    if state["active_neutral"] is not None and state["consumed_neutral"] is not None:
        raise ProtocolError("Impossible lifecycle state: active neutral authorization with neutral consumption record")
    if state["active_stage_q"] is not None and state["consumed_stage_q"] is not None:
        raise ProtocolError("Impossible lifecycle state: active Stage-Q authorization with Stage-Q consumption record")
    if state["engineering_neutral"] is not None and state["consumed_neutral"] is None:
        raise ProtocolError("Impossible lifecycle state: neutral qualification result without neutral consumption record")
    if state["engineering_stage_q"] is not None and state["consumed_stage_q"] is None:
        raise ProtocolError("Impossible lifecycle state: Stage-Q result without Stage-Q consumption record")
    if state["engineering_neutral"] is not None:
        _validate_neutral_result_lifecycle_correlation(state)

    active_paths = [
        path
        for path in (state["active_neutral"], state["active_stage_q"])
        if path is not None
    ]
    active_hashes = {sha256_file(path) for path in active_paths} if active_paths else set()
    root = Path(state["root"])
    groups = _group_disposition_artifacts(state)
    retained_paths = [
        path
        for path in state.get("retained_authorizations", {}).values()
        if path is not None
    ]
    retained_hashes = {sha256_file(path) for path in retained_paths} if retained_paths else set()
    active_ids: list[str | None] = []
    if active_paths and groups:
        for path in active_paths:
            auth = read_json_no_duplicates(path)
            if isinstance(auth, Mapping) and isinstance(auth.get("authorization_id"), str):
                active_ids.append(auth["authorization_id"])
            else:
                active_ids.append(None)

    for digest, group in groups.items():
        if digest in retained_hashes:
            raise ProtocolError(
                "Impossible lifecycle state: consumed authorization has a disposition lifecycle"
            )
        if digest in active_hashes:
            if group["archives"] or group["records"]:
                raise ProtocolError(
                    "Impossible lifecycle state: active authorization with archive or completed disposition"
                )
            continue
        _validate_completed_historical_disposition(
            root,
            digest,
            group,
            active_authorization_id=active_ids[0] if active_ids else None,
        )
    _validate_stage_q_archive_identity_state(state)


def _reject_active_identity_disposition_state(state: Mapping[str, Any]) -> None:
    """Reject disposition artifacts that refer to the currently active authorization."""
    active_paths = [
        path
        for path in (state["active_neutral"], state["active_stage_q"])
        if path is not None
    ]
    if not active_paths:
        return
    active_hashes = {sha256_file(path) for path in active_paths}
    for kind in ("disposition_archives", "disposition_journals", "disposition_records"):
        for relative in state[kind]:
            digest = _lifecycle_artifact_sha256(relative)
            if digest in active_hashes:
                raise ProtocolError("Qualification is incompatible with an active disposition lifecycle")


def _validate_neutral_lifecycle_state(state: Mapping[str, Any]) -> None:
    if state["active_neutral"] is None:
        raise ProtocolError("Neutral qualification requires an active neutral authorization")
    if state["active_stage_q"] is not None:
        raise ProtocolError("Neutral qualification is incompatible with an active Stage-Q authorization")
    if state["consumed_neutral"] is not None:
        raise ProtocolError("Neutral authorization has already been consumed")
    if state["consumed_stage_q"] is not None:
        raise ProtocolError("Neutral qualification is incompatible with a Stage-Q consumption record")
    if state["engineering_neutral"] is not None:
        raise ProtocolError("Neutral qualification result already exists")
    if state["engineering_stage_q"] is not None:
        raise ProtocolError("Neutral qualification is incompatible with a Stage-Q result")
    _reject_active_identity_disposition_state(state)


def _validate_stage_q_lifecycle_state(state: Mapping[str, Any]) -> None:
    if state["active_neutral"] is not None:
        raise ProtocolError("Stage-Q requires the neutral authorization to be consumed")
    if state["consumed_neutral"] is None:
        raise ProtocolError("Stage-Q requires a neutral consumption record")
    if state["engineering_neutral"] is None:
        raise ProtocolError("Stage-Q requires a neutral qualification result")
    if state["engineering_stage_q"] is not None:
        raise ProtocolError("Stage-Q result already exists")
    if state["active_stage_q"] is None:
        raise ProtocolError("Stage-Q requires an active Stage-Q authorization")
    if state["consumed_stage_q"] is not None:
        raise ProtocolError("Stage-Q authorization has already been consumed")
    _reject_active_identity_disposition_state(state)


def validate_lifecycle_state(state: Mapping[str, Any], mode: str) -> None:
    """Apply the closed-world lifecycle rules for one execution mode."""
    if mode not in {LIFECYCLE_MODE_STATIC, LIFECYCLE_MODE_NEUTRAL, LIFECYCLE_MODE_STAGE_Q}:
        raise ProtocolError(f"Unknown lifecycle validation mode: {mode}")
    if state["unknown_paths"]:
        raise ProtocolError(f"Unknown lifecycle artifact: {state['unknown_paths'][0]}")
    if state["legacy_contamination"]:
        raise ProtocolError(f"Legacy lifecycle contamination: {state['legacy_contamination'][0]}")
    _validate_no_impossible_lifecycle_state(state)
    if mode == LIFECYCLE_MODE_STATIC:
        return
    if mode == LIFECYCLE_MODE_NEUTRAL:
        _validate_neutral_lifecycle_state(state)
    else:
        _validate_stage_q_lifecycle_state(state)


def validate_mode_lifecycle(repo_root: str | Path, mode: str) -> dict[str, Any]:
    """Inspect and validate mutable EXP-021 lifecycle state for a single mode."""
    state = inspect_lifecycle_paths(repo_root)
    validate_lifecycle_state(state, mode)
    return state


def validate_checkpoint_mapping(mapping: Mapping[str, Any]) -> None:
    """Validate the six frozen checkpoint roles without loading a model."""
    expected = {item["name"]: item for item in CHECKPOINTS}
    allowed_keys = CHECKPOINT_MAPPING_METADATA_KEYS | set(expected)
    if set(mapping) != allowed_keys:
        raise ProtocolError("Checkpoint mapping top-level schema mismatch")
    if mapping.get("num_transformer_blocks") != 28:
        raise ProtocolError("Checkpoint mapping block count mismatch")
    if mapping.get("tuple_semantics") != TUPLE_SEMANTICS_FROZEN_TEXT:
        raise ProtocolError("Checkpoint mapping tuple semantics mismatch")
    for name, checkpoint in expected.items():
        actual = mapping.get(name)
        if not actual or actual.get("block_index") != checkpoint["block_index"]:
            raise ProtocolError(f"Checkpoint mismatch: {name}")
        if actual.get("hidden_state_index") != checkpoint["hidden_state_index"]:
            raise ProtocolError(f"Hidden-state index mismatch: {name}")
    if mapping["final_block_pre_final_rmsnorm"].get("access") != "hooked_block_27_output":
        raise ProtocolError("Primary final checkpoint access mismatch")
    if mapping["final_block_pre_final_rmsnorm"].get("role") != "PRIMARY_FINAL_CHECKPOINT":
        raise ProtocolError("Primary final checkpoint role mismatch")
    if mapping["final_normalized_hidden_state"].get("role") != "DESCRIPTIVE_ONLY":
        raise ProtocolError("Post-normalization checkpoint role mismatch")


def clopper_pearson_lower_bound(correct: int, total: int = 12, alpha: float = 0.05) -> float:
    """Return the exact two-sided Clopper–Pearson lower bound."""
    if isinstance(correct, bool) or isinstance(total, bool) or not isinstance(correct, int) or not isinstance(total, int):
        raise ProtocolError("Correct and total must be strict integers")
    if total != 12 or not 0 <= correct <= total or alpha != 0.05:
        raise ProtocolError("EXP-021 Stage-Q uses fixed n=12 and alpha=0.05")
    if correct == 0:
        return 0.0
    from scipy.stats import beta  # Runtime-only scientific utility import.

    return float(beta.ppf(alpha / 2.0, correct, total - correct + 1))


def checkpoint_passes(correct: int, total: int = 12) -> bool:
    """Apply the frozen k>=7 and exact lower-bound>0.25 rule."""
    return correct >= 7 and clopper_pearson_lower_bound(correct, total) > 0.25


def stage_q_global_gate(rows: Iterable[Mapping[str, Any]], splits: Sequence[str], checkpoints: Sequence[str] = REQUIRED_GATE_CHECKPOINTS) -> bool:
    """Require every split/checkpoint cell to pass exactly once."""
    expected = {(split, checkpoint) for split in splits for checkpoint in checkpoints}
    observed: dict[tuple[str, str], Mapping[str, Any]] = {}
    for row in rows:
        key = (str(row["split_id"]), str(row["checkpoint"]))
        if key in observed or key not in expected:
            raise ProtocolError(f"Duplicate or unexpected Stage-Q cell: {key}")
        if type(row.get("n")) is not int or row["n"] != 12 or type(row.get("correct")) is not int or not isinstance(row.get("pass"), bool):
            raise ProtocolError("Stage-Q gate cell has non-strict statistics")
        observed[key] = row
    if set(observed) != expected:
        return False
    return all(row["pass"] and checkpoint_passes(row["correct"], row["n"]) for row in observed.values())


def map_classifier_probabilities(probabilities: Any, classifier_classes: Sequence[str], class_order: Sequence[str] = CLASS_ORDER) -> Any:
    """Map classifier probability columns through ``classes_`` explicitly."""
    if len(classifier_classes) != len(set(classifier_classes)):
        raise ProtocolError("Classifier class order contains duplicates")
    if set(classifier_classes) != set(class_order):
        raise ProtocolError("Classifier classes do not match frozen semantic classes")
    import numpy as np  # Runtime-only numerical utility import.

    array = np.asarray(probabilities)
    if array.ndim != 2 or array.shape[1] != len(classifier_classes):
        raise ProtocolError("Probability matrix shape does not match classifier classes")
    mapped = np.empty((array.shape[0], len(class_order)), dtype=array.dtype)
    for source_index, label in enumerate(classifier_classes):
        mapped[:, class_order.index(label)] = array[:, source_index]
    if not np.isfinite(mapped).all():
        raise ProtocolError("Nonfinite classifier probability")
    return mapped


def leave_one_out_fixed_probe(
    representations: Mapping[str, Any],
    labels: Sequence[str],
    class_order: Sequence[str] = CLASS_ORDER,
    injection_checkpoint: str = "intervention",
) -> list[dict[str, Any]]:
    """Fit one FIT-only probe per fold and reuse it at every checkpoint."""
    import numpy as np  # Runtime-only numerical utility import.
    from sklearn.linear_model import LogisticRegression  # Runtime-only utility import.
    from sklearn.preprocessing import StandardScaler  # Runtime-only utility import.

    if injection_checkpoint not in representations:
        raise ProtocolError("Missing intervention representations")
    n = len(labels)
    if n != 12:
        raise ProtocolError("Stage-Q requires exactly 12 FIT items per split")
    if tuple(class_order) != CLASS_ORDER:
        raise ProtocolError("Stage-Q semantic class order is not frozen")
    if set(labels) != set(class_order) or any(labels.count(label) != 3 for label in class_order):
        raise ProtocolError("Stage-Q FIT items must contain three examples per class")
    arrays = {name: np.asarray(value) for name, value in representations.items()}
    expected_checkpoints = {item["name"] for item in CHECKPOINTS}
    if set(arrays) != expected_checkpoints:
        raise ProtocolError("Stage-Q checkpoint representation set is incomplete or unexpected")
    if any(
        array.shape[0] != n
        or array.ndim != 2
        or array.shape[1] != 2048
        or not np.isfinite(array).all()
        for array in arrays.values()
    ):
        raise ProtocolError("Representation arrays must be [12, hidden_size]")
    result: list[dict[str, Any]] = []
    for held_out in range(n):
        train_indices = [index for index in range(n) if index != held_out]
        scaler = StandardScaler().fit(arrays[injection_checkpoint][train_indices])
        classifier_kwargs = {"max_iter": 1000, "random_state": 20260812}
        try:
            classifier = LogisticRegression(multi_class="multinomial", **classifier_kwargs)
        except TypeError:
            # scikit-learn 1.9 removed the redundant keyword; multinomial is
            # the default for the multiclass solver in that API.
            classifier = LogisticRegression(**classifier_kwargs)
        classifier.fit(
            scaler.transform(arrays[injection_checkpoint][train_indices]),
            [labels[i] for i in train_indices],
        )
        for checkpoint, array in arrays.items():
            mapped = map_classifier_probabilities(
                classifier.predict_proba(scaler.transform(array[[held_out]])),
                classifier.classes_, class_order,
            )
            if not np.isfinite(mapped).all() or not np.allclose(mapped.sum(axis=1), 1.0, rtol=1e-6, atol=1e-6):
                raise ProtocolError("Classifier probabilities are not finite and normalized")
            predicted = class_order[int(np.argmax(mapped[0]))]
            result.append({
                "held_out_index": held_out,
                "checkpoint": checkpoint,
                "true_class": labels[held_out],
                "predicted_class": predicted,
                "probabilities": mapped[0].tolist(),
                "correct": predicted == labels[held_out],
            })
    return result


def validate_fit_eval_routing(records: Iterable[Mapping[str, Any]], fit_ids: Sequence[str], eval_ids: Sequence[str], active_split: str) -> list[dict[str, Any]]:
    """Return FIT-role records and reject duplicate, overlapping, or EVAL routing."""
    fit_set, eval_set = set(fit_ids), set(eval_ids)
    if len(fit_set) != len(fit_ids) or len(eval_set) != len(eval_ids) or fit_set & eval_set:
        raise ProtocolError("FIT/EVAL IDs are duplicate or overlapping")
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for record in records:
        item_id = record.get("item_id")
        if item_id in seen:
            raise ProtocolError("Duplicate processed item ID")
        seen.add(item_id)
        if record.get("split_id") != active_split or record.get("role") != "FIT":
            raise ProtocolError("Non-FIT or wrong-split item entered Stage-Q routing")
        if item_id not in fit_set or item_id in eval_set:
            raise ProtocolError("Unknown or EVAL item entered Stage-Q routing")
        selected.append(
            {
                "item_id": item_id,
                "split_id": active_split,
                "role": "FIT",
                **({key: record[key] for key in ("task_class", "prompt_text") if key in record}),
            }
        )
    if {item["item_id"] for item in selected} != fit_set:
        raise ProtocolError("Missing FIT item in Stage-Q routing")
    return selected


def deterministic_diagnostic_vector(hidden_size: int) -> tuple[list[float], str]:
    """Construct a nonzero engineering-only vector and return its identity hash."""
    if isinstance(hidden_size, bool) or not isinstance(hidden_size, int) or hidden_size <= 0:
        raise ProtocolError("Hidden size must be a positive integer")
    values = [1.0 if index % 2 == 0 else -1.0 for index in range(hidden_size)]
    encoded = json.dumps(values, separators=(",", ":")).encode("utf-8")
    return values, sha256_bytes(encoded)


def _validate_neutral_execution_environment(
    environment: Mapping[str, Any],
    required: Mapping[str, Any],
    runtime_identity: Mapping[str, Any],
) -> None:
    """Require full runtime identity and the frozen deterministic environment fields."""
    if not isinstance(environment, Mapping):
        raise ProtocolError("neutral execution_environment must be an object")
    require_exact_keys(
        environment,
        NEUTRAL_EXECUTION_ENVIRONMENT_KEYS,
        "neutral execution_environment",
    )
    for key, expected in required.items():
        if environment.get(key) != expected:
            raise ProtocolError(f"Neutral execution_environment drift in {key}")
    if not isinstance(runtime_identity, Mapping):
        raise ProtocolError("runtime identity binding must be an object")
    require_exact_keys(
        runtime_identity,
        RUNTIME_IDENTITY_KEYS,
        "runtime identity binding",
    )
    for key in RUNTIME_IDENTITY_KEYS:
        require_string(environment[key], f"execution_environment.{key}")
        require_string(runtime_identity[key], f"runtime_identity.{key}")
        if environment[key] != runtime_identity[key]:
            raise ProtocolError(f"Neutral execution_environment drift in {key}")


def _validate_neutral_diagnostic_vector(diagnostic_vector: Mapping[str, Any]) -> None:
    """Require the exact deterministic diagnostic-vector identity."""
    if not isinstance(diagnostic_vector, Mapping):
        raise ProtocolError("neutral diagnostic_vector must be an object")
    require_exact_keys(
        diagnostic_vector,
        NEUTRAL_DIAGNOSTIC_VECTOR_KEYS,
        "neutral diagnostic_vector",
    )
    if diagnostic_vector["algorithm"] != "alternating_plus_minus_one":
        raise ProtocolError("Neutral diagnostic vector algorithm drift")
    if type(diagnostic_vector["length"]) is not int or diagnostic_vector["length"] != 2048:
        raise ProtocolError("Neutral diagnostic vector length drift")
    expected_sha256 = deterministic_diagnostic_vector(diagnostic_vector["length"])[1]
    if diagnostic_vector["sha256"] != expected_sha256:
        raise ProtocolError("Neutral diagnostic vector hash drift")


def _validate_neutral_input_identity(neutral_input_identity: Mapping[str, Any]) -> None:
    """Require the exact hashed neutral-input identity."""
    if not isinstance(neutral_input_identity, Mapping):
        raise ProtocolError("neutral_input_identity must be an object")
    require_exact_keys(
        neutral_input_identity,
        NEUTRAL_INPUT_IDENTITY_KEYS,
        "neutral_input_identity",
    )
    if neutral_input_identity["sha256"] != _neutral_input_identity():
        raise ProtocolError("Neutral input identity hash drift")


def construct_expected_hook_output(original: Any, delta: Any, beta: float = BETA, selected_token_index: int = -1) -> Any:
    """Construct the exact expected tensor using the frozen hook operation order."""
    expected = original.clone()
    if expected is original:
        raise ProtocolError("Expected hook tensor must be an independent clone")
    delta_cast = delta.to(device=original.device, dtype=original.dtype)
    expected[:, selected_token_index, :] += beta * delta_cast
    return expected


def production_hook_factory(delta: Any, beta: float, selected_token_index: int, *, active: bool) -> tuple[Callable[..., Any], dict[str, int]]:
    """Build the production hook mutation independently from expected construction."""
    state = {"invocations": 0}

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        state["invocations"] += 1
        if not active:
            return output
        hidden = output[0] if isinstance(output, tuple) else output
        mutated = hidden.clone()
        delta_cast = delta.to(device=hidden.device, dtype=hidden.dtype)
        mutated[:, selected_token_index, :] += beta * delta_cast
        if isinstance(output, tuple):
            return (mutated, *output[1:])
        return mutated

    return hook, state


def capture_output_hook(state: dict[str, Any]) -> Callable[..., Any]:
    """Capture an independent clone of a block output for oracle comparison."""
    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        state["invocations"] = int(state.get("invocations", 0)) + 1
        hidden = output[0] if isinstance(output, tuple) else output
        state["value"] = hidden.clone()
        return output

    return hook


def validate_active_hook_output(
    original: Any,
    actual_hook_output: Any,
    expected: Any,
    selected_token_index: int,
    invocation_count: int,
    equal_fn: Callable[[Any, Any], bool] | None = None,
) -> None:
    """Enforce exact active-hook, shape/dtype/device, token, and call-count checks."""
    if invocation_count != 1:
        raise ProtocolError("Active hook invocation count must equal one")
    if actual_hook_output is original or actual_hook_output is expected:
        raise ProtocolError("Active hook comparison must use independent tensors")
    if selected_token_index < 0:
        selected_token_index += original.shape[1]
    if not 0 <= selected_token_index < original.shape[1]:
        raise ProtocolError("Selected token index is outside the sequence")
    if (
        actual_hook_output.shape != original.shape
        or actual_hook_output.dtype != original.dtype
        or actual_hook_output.device != original.device
    ):
        raise ProtocolError("Active hook changed tensor shape, dtype, or device")
    if equal_fn is None:
        import torch  # Runtime-only model-runtime import.

        if not torch.equal(actual_hook_output, expected):
            raise ProtocolError("Active hook output failed torch.equal construction oracle")
    elif not equal_fn(actual_hook_output, expected):
        raise ProtocolError("Active hook output failed torch.equal construction oracle")
    for token_index in range(original.shape[1]):
        if token_index == selected_token_index:
            continue
        compare = torch.equal if equal_fn is None else equal_fn
        if not compare(actual_hook_output[:, token_index, :], original[:, token_index, :]):
            raise ProtocolError("Non-target token changed")


def validate_inactive_hook_output(no_hook: Any, inactive: Any, equal_fn: Callable[[Any, Any], bool] | None = None) -> None:
    """Require exact inactive-hook equality without approximate rescue."""
    if no_hook is inactive:
        raise ProtocolError("Inactive hook comparison cannot compare a tensor with itself")
    if equal_fn is None:
        import torch  # Runtime-only model-runtime import.

        equal_fn = torch.equal
    if not equal_fn(no_hook, inactive):
        raise ProtocolError("Inactive hook differs from no-hook output")


def authority_hashes(repo_root: str | Path) -> dict[str, str]:
    """Return the three frozen authority file hashes used by runtime binding."""
    root = Path(repo_root).resolve()
    return {
        "original": sha256_file(root / AUTHORITY_ORIGINAL),
        "amendment": sha256_file(root / AUTHORITY_AMENDMENT),
        "reconciliation": sha256_file(root / AUTHORITY_RECONCILIATION),
    }


def implementation_hashes(repo_root: str | Path) -> dict[str, str]:
    """Return hashes for both production Python files."""
    root = Path(repo_root).resolve()
    return {
        "runner": sha256_file(Path(__file__).resolve()),
        "validator": sha256_file(root / "experiments/exp021/validate_exp021_stage_q_implementation.py"),
    }


def model_manifest_binding(identity: Mapping[str, Any]) -> dict[str, Any]:
    """Return a complete, JSON-stable binding for the frozen model manifest."""
    return {
        "model_id": identity["model_id"],
        "architecture": identity["architecture"],
        "model_type": identity["model_type"],
        "canonical_snapshot_path": identity["canonical_snapshot_path"],
        "resolved_snapshot_path": identity["resolved_snapshot_path"],
        "file_manifest": identity["file_manifest"],
    }


def required_environment_binding() -> dict[str, Any]:
    """Return the pre-runtime environment requirements frozen by the authority."""
    return {
        "dtype": "float16",
        "device": "cuda:0",
        "local_files_only": True,
        "model_eval_mode": True,
        "gradients_enabled": False,
        "use_cache": False,
    }


def _nvidia_runtime_identity() -> tuple[str, str]:
    """Return the canonical NVIDIA driver and GPU identities without loading a model."""
    try:
        output = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=name,driver_version",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        ).strip().splitlines()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ProtocolError("NVIDIA runtime identity is unavailable") from exc
    if not output:
        raise ProtocolError("NVIDIA runtime identity is unavailable")
    try:
        gpu, driver = (part.strip() for part in output[0].split(",", 1))
    except ValueError as exc:
        raise ProtocolError("NVIDIA runtime identity format is invalid") from exc
    if not gpu or not driver:
        raise ProtocolError("NVIDIA runtime identity is incomplete")
    return driver, gpu


def runtime_identity_binding() -> dict[str, str]:
    """Return the live dynamic runtime identity used by neutral result validation."""
    import importlib.metadata

    import torch

    driver, gpu = _nvidia_runtime_identity()
    python_version = sys.version.split()[0]
    torch_version = getattr(torch, "__version__", None)
    transformers_version = importlib.metadata.version("transformers")
    cuda_runtime = getattr(torch.version, "cuda", None)
    if not isinstance(python_version, str) or not python_version:
        raise ProtocolError("Python runtime identity is unavailable")
    if not isinstance(torch_version, str) or not torch_version:
        raise ProtocolError("torch runtime identity is unavailable")
    if not isinstance(transformers_version, str) or not transformers_version:
        raise ProtocolError("transformers runtime identity is unavailable")
    if not isinstance(cuda_runtime, str) or not cuda_runtime:
        raise ProtocolError("CUDA runtime identity is unavailable")
    identity = {
        "python": python_version,
        "torch": torch_version,
        "transformers": transformers_version,
        "cuda_runtime": cuda_runtime,
        "nvidia_driver": driver,
        "gpu": gpu,
    }
    require_exact_keys(identity, RUNTIME_IDENTITY_KEYS, "runtime identity binding")
    return identity


def build_static_execution_binding(root: str | Path, authority: Mapping[str, Any]) -> dict[str, Any]:
    """Build live pre-runtime identities used to validate authorization fields."""
    root_path = Path(root).resolve()
    return {
        "runner_commit": _git_output(root_path, "rev-parse", "HEAD"),
        "runner_sha256": implementation_hashes(root_path)["runner"],
        "implementation_hashes": implementation_hashes(root_path),
        "authority_hashes": authority_hashes(root_path),
        "model_manifest": model_manifest_binding(authority["primary_model_identity"]),
        "environment_binding": required_environment_binding(),
        "runtime_identity": runtime_identity_binding(),
    }


def build_historical_neutral_binding(
    repo_root: str | Path,
    result_path: str | Path,
    result: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the immutable producing-runner binding for a historical neutral result.

    Stage-Q validates the neutral prerequisite against the implementation that
    actually produced it, not against the current Stage-Q runner.  The result
    file must still be the frozen canonical bytes, and its recorded producer
    identities must match the archived Git blobs at the frozen producer commit.
    """
    root = Path(repo_root).resolve()
    if sha256_file(result_path) != EXPECTED_NEUTRAL_RESULT_SHA256:
        raise ProtocolError("Stage-Q neutral result SHA dependency mismatch")
    require_exact_keys(result, NEUTRAL_RESULT_KEYS, "neutral result")
    runner_commit = require_string(result["runner_commit"], "neutral result runner_commit")
    runner_sha256 = require_string(result["runner_sha256"], "neutral result runner_sha256")
    implementation_hashes = result["implementation_hashes"]
    if not isinstance(implementation_hashes, Mapping) or set(implementation_hashes) != {"runner", "validator"}:
        raise ProtocolError("neutral result implementation_hashes schema mismatch")
    validator_sha256 = require_string(
        implementation_hashes["validator"], "neutral result validator hash"
    )
    if runner_commit != EXPECTED_NEUTRAL_PRODUCER_COMMIT:
        raise ProtocolError("Neutral result producer commit is not the frozen historical commit")
    if runner_sha256 != EXPECTED_NEUTRAL_PRODUCER_RUNNER_SHA256:
        raise ProtocolError("Neutral result producer runner SHA is not the frozen historical identity")
    if implementation_hashes["runner"] != EXPECTED_NEUTRAL_PRODUCER_RUNNER_SHA256:
        raise ProtocolError("Neutral result producer runner hash mismatch")
    if validator_sha256 != EXPECTED_NEUTRAL_PRODUCER_VALIDATOR_SHA256:
        raise ProtocolError("Neutral result producer validator hash mismatch")
    if (
        _git_blob_sha256(
            root,
            runner_commit,
            RUNNER_IMPLEMENTATION_RELATIVE_PATH.as_posix(),
        )
        != runner_sha256
    ):
        raise ProtocolError("Historical runner Git blob does not match producer runner SHA")
    if (
        _git_blob_sha256(
            root,
            runner_commit,
            VALIDATOR_IMPLEMENTATION_RELATIVE_PATH.as_posix(),
        )
        != validator_sha256
    ):
        raise ProtocolError("Historical validator Git blob does not match producer validator SHA")
    execution_environment = result["execution_environment"]
    if not isinstance(execution_environment, Mapping):
        raise ProtocolError("neutral result execution_environment must be an object")
    runtime_identity = {
        key: require_string(execution_environment[key], f"execution_environment.{key}")
        for key in RUNTIME_IDENTITY_KEYS
    }
    return {
        "runner_commit": runner_commit,
        "runner_sha256": runner_sha256,
        "implementation_hashes": implementation_hashes,
        "authority_hashes": result["authority_hashes"],
        "model_manifest": result["model_manifest"],
        "environment_binding": required_environment_binding(),
        "runtime_identity": runtime_identity,
    }


def validate_authorization(
    authorization: Mapping[str, Any],
    expected_scope: str,
    repo_root: str | Path,
    *,
    expected_identity: Mapping[str, Any] | None = None,
    expected_output_path: str | Path | None = None,
) -> Path:
    """Fully validate a single-use authorization before it can be consumed."""
    expected_keys = NEUTRAL_AUTHORIZATION_KEYS if expected_scope == NEUTRAL_SCOPE else STAGE_Q_AUTHORIZATION_KEYS
    require_exact_keys(authorization, expected_keys, "authorization")
    if authorization["schema_version"] != SCHEMA_VERSION or authorization["experiment"] != EXPERIMENT:
        raise ProtocolError("Authorization schema identity mismatch")
    if authorization["scope"] != expected_scope:
        raise ProtocolError("Authorization scope mismatch")
    require_string(authorization["authorization_id"], "authorization_id")
    issued = parse_timestamp(authorization["issued_at"], "issued_at")
    expires = parse_timestamp(authorization["expires_at"], "expires_at")
    if expires <= issued or expires <= datetime.now(timezone.utc):
        raise ProtocolError("Authorization is expired or has an invalid time range")
    if type(authorization["maximum_launch_count"]) is not int or authorization["maximum_launch_count"] != 1:
        raise ProtocolError("maximum_launch_count must be the integer 1")
    if expected_scope == NEUTRAL_SCOPE and require_bool(authorization["fit_access_permitted"], "fit_access_permitted"):
        raise ProtocolError("Neutral authorization must prohibit FIT access")
    if expected_scope == STAGE_Q_SCOPE and not require_bool(authorization["fit_access_permitted"], "fit_access_permitted"):
        raise ProtocolError("Stage-Q authorization must permit FIT access")
    for key in ("eval_access_permitted", "scientific_result_permitted", "automatic_retry_permitted"):
        if require_bool(authorization[key], key):
            raise ProtocolError(f"Authorization must prohibit {key}")
    if expected_scope == STAGE_Q_SCOPE:
        for key in ("stage_p_intervention_permitted", "per_checkpoint_probe_refit_permitted"):
            if require_bool(authorization[key], key):
                raise ProtocolError(f"Authorization must prohibit {key}")
    for key in ("runner_commit", "runner_sha256"):
        require_string(authorization[key], key)
    if len(authorization["runner_sha256"]) != 64:
        raise ProtocolError("runner_sha256 must be a SHA-256 digest")
    for field, required in (
        ("implementation_hashes", {"runner", "validator"}),
        ("authority_hashes", {"original", "amendment", "reconciliation"}),
    ):
        value = authorization[field]
        if not isinstance(value, Mapping) or set(value) != required:
            raise ProtocolError(f"{field} schema mismatch")
        if any(not isinstance(item, str) or len(item) != 64 for item in value.values()):
            raise ProtocolError(f"{field} contains an invalid digest")
    if not isinstance(authorization["model_manifest"], Mapping):
        raise ProtocolError("model_manifest must be an object")
    if not isinstance(authorization["environment_binding"], Mapping):
        raise ProtocolError("environment_binding must be an object")
    output_path = confined_path(authorization["allowed_output_path"], repo_root, allow_missing=True)
    if "results" in output_path.parts or "scientific" in output_path.name.lower():
        raise ProtocolError("Engineering output path is not distinct from scientific results")
    if expected_output_path is not None and output_path != confined_path(expected_output_path, repo_root, allow_missing=True):
        raise ProtocolError("Authorization output path is not the frozen engineering path")
    if expected_identity is not None:
        for key in ("runner_commit", "runner_sha256", "implementation_hashes", "authority_hashes", "model_manifest", "environment_binding"):
            if authorization[key] != expected_identity[key]:
                raise ProtocolError(f"Authorization identity drift in {key}")
    return output_path



def _disposition_scope_paths(scope: str) -> tuple[Path, Path]:
    """Return the frozen consumption and result paths for a supported scope."""
    if scope == NEUTRAL_SCOPE:
        return NEUTRAL_CONSUMPTION_RELATIVE_PATH, NEUTRAL_RESULT_RELATIVE_PATH
    if scope == STAGE_Q_SCOPE:
        return STAGE_Q_CONSUMPTION_RELATIVE_PATH, STAGE_Q_RESULT_RELATIVE_PATH
    raise ProtocolError(f"Unsupported disposition scope: {scope}")


def _disposition_transaction_paths(
    root: Path, authorization_sha256: str
) -> tuple[Path, Path, Path]:
    """Return the deterministic archive, journal, and disposition paths."""
    archive_path = confined_path(
        root / AUTHORIZATION_ARCHIVE_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    journal_path = confined_path(
        root / AUTHORIZATION_DISPOSITION_JOURNAL_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    disposition_path = confined_path(
        root / AUTHORIZATION_DISPOSITION_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    return archive_path, journal_path, disposition_path


def _disposition_transaction_ids(authorization_sha256: str) -> tuple[str, str]:
    """Return the deterministic transaction identities for an authorization hash."""
    return "DISP-TXN-" + authorization_sha256, "DISP-" + authorization_sha256


def _relative_path_string(path: Path, root: Path) -> str:
    """Return a portable slash-separated path relative to ``root``."""
    return path.relative_to(root).as_posix()


def _disposition_journal_sha256(journal: Mapping[str, Any]) -> str:
    """Hash the stable journal identity without the self-referential digest field."""
    stable = {key: value for key, value in journal.items() if key != "journal_sha256"}
    canonical = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def validate_disposition_journal(journal: Mapping[str, Any]) -> None:
    """Validate the closed schema and fail-closed invariants of a disposition journal."""
    require_exact_keys(journal, DISPOSITION_JOURNAL_KEYS, "disposition journal")
    if journal["schema_version"] != SCHEMA_VERSION or journal["experiment"] != EXPERIMENT:
        raise ProtocolError("Disposition journal schema identity mismatch")
    if journal["disposition_type"] != AUTHORIZATION_DISPOSITION_TYPE:
        raise ProtocolError("Disposition journal type mismatch")
    if journal["state"] != DISPOSITION_STATE_PREPARED:
        raise ProtocolError("Disposition journal must be in PREPARED state")
    require_string(journal["authorization_id"], "authorization_id")
    require_string(journal["authorization_sha256"], "authorization_sha256")
    if len(journal["authorization_sha256"]) != 64:
        raise ProtocolError("authorization_sha256 must be a SHA-256 digest")
    require_string(journal["authorization_scope"], "authorization_scope")
    require_string(journal["authorization_runner_commit"], "authorization_runner_commit")
    require_string(journal["authorization_runner_sha256"], "authorization_runner_sha256")
    if len(journal["authorization_runner_sha256"]) != 64:
        raise ProtocolError("authorization_runner_sha256 must be a SHA-256 digest")
    require_string(journal["transaction_id"], "transaction_id")
    require_string(journal["disposition_record_id"], "disposition_record_id")
    require_string(journal["expected_archive_path"], "expected_archive_path")
    require_string(journal["expected_disposition_path"], "expected_disposition_path")
    require_string(journal["non_executable_reason"], "non_executable_reason")
    parse_timestamp(journal["created_at"], "created_at")
    parse_timestamp(journal["updated_at"], "updated_at")
    if journal["explicit_disposition_authorized"] is not True:
        raise ProtocolError("Disposition journal requires explicit authorization")
    require_string(journal["journal_sha256"], "journal_sha256")
    if len(journal["journal_sha256"]) != 64:
        raise ProtocolError("journal_sha256 must be a SHA-256 digest")
    if journal["journal_sha256"] != _disposition_journal_sha256(journal):
        raise ProtocolError("Disposition journal self-hash mismatch")


def validate_disposition_record(record: Mapping[str, Any]) -> None:
    """Validate the closed schema and fail-closed invariants of a disposition record."""
    require_exact_keys(record, DISPOSITION_RECORD_KEYS, "disposition record")
    if record["schema_version"] != SCHEMA_VERSION or record["experiment"] != EXPERIMENT:
        raise ProtocolError("Disposition schema identity mismatch")
    if record["disposition_type"] != AUTHORIZATION_DISPOSITION_TYPE:
        raise ProtocolError("Disposition type mismatch")
    if record["state"] != DISPOSITION_STATE_DISPOSITIONED:
        raise ProtocolError("Disposition record state must be DISPOSITIONED")
    require_string(record["authorization_id"], "authorization_id")
    require_string(record["authorization_sha256"], "authorization_sha256")
    if len(record["authorization_sha256"]) != 64:
        raise ProtocolError("authorization_sha256 must be a SHA-256 digest")
    require_string(record["authorization_scope"], "authorization_scope")
    require_string(record["authorization_runner_commit"], "authorization_runner_commit")
    require_string(record["authorization_runner_sha256"], "authorization_runner_sha256")
    if len(record["authorization_runner_sha256"]) != 64:
        raise ProtocolError("authorization_runner_sha256 must be a SHA-256 digest")
    if record["authorization_consumed"] is not False:
        raise ProtocolError("Disposition requires an unconsumed authorization")
    if record["consumption_record_exists"] is not False:
        raise ProtocolError("Disposition requires no consumption record")
    if record["qualification_result_exists"] is not False:
        raise ProtocolError("Disposition requires no qualification result")
    require_string(record["non_executable_reason"], "non_executable_reason")
    if record["replacement_automatically_authorized"] is not False:
        raise ProtocolError("Disposition must not automatically authorize a replacement")
    if record["original_can_never_be_consumed"] is not True:
        raise ProtocolError("Disposition must permanently prohibit original consumption")
    require_string(record["archived_authorization_path"], "archived_authorization_path")
    require_string(record["disposition_record_id"], "disposition_record_id")
    require_string(record["transaction_id"], "transaction_id")
    parse_timestamp(record["disposition_timestamp"], "disposition_timestamp")
    if record["explicit_disposition_authorized"] is not True:
        raise ProtocolError("Disposition requires explicit authorization")
    require_string(record["journal_sha256"], "journal_sha256")
    if len(record["journal_sha256"]) != 64:
        raise ProtocolError("journal_sha256 must be a SHA-256 digest")


def _read_active_authorization_for_disposition(
    root: Path,
    authorization_path: str | Path,
    expected_scope: str,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
) -> tuple[Path, dict[str, Any], str, str, str, str]:
    """Validate an active authorization and all preconditions before intent creation."""
    auth_path = confined_path(authorization_path, root)
    consumption_rel, result_rel = _disposition_scope_paths(expected_scope)
    consumption_path = confined_path(root / consumption_rel, root, allow_missing=True)
    result_path = confined_path(root / result_rel, root, allow_missing=True)
    if os.path.lexists(consumption_path):
        raise ProtocolError("Cannot disposition authorization with an existing consumption record")
    if os.path.lexists(result_path):
        raise ProtocolError("Cannot disposition authorization with an existing qualification result")
    authorization = read_json_no_duplicates(auth_path)
    expected_keys = NEUTRAL_AUTHORIZATION_KEYS if expected_scope == NEUTRAL_SCOPE else STAGE_Q_AUTHORIZATION_KEYS
    require_exact_keys(authorization, expected_keys, "authorization")
    if authorization["schema_version"] != SCHEMA_VERSION or authorization["experiment"] != EXPERIMENT:
        raise ProtocolError("Authorization schema identity mismatch")
    if authorization["scope"] != expected_scope:
        raise ProtocolError("Authorization scope mismatch")
    authorization_id = require_string(authorization["authorization_id"], "authorization_id")
    if authorization_id != expected_authorization_id:
        raise ProtocolError("Authorization ID does not match expected disposition identity")
    authorization_hash = sha256_file(auth_path)
    if authorization_hash != expected_authorization_sha256:
        raise ProtocolError("Authorization hash does not match expected disposition identity")
    runner_commit = require_string(authorization["runner_commit"], "runner_commit")
    runner_sha256 = require_string(authorization["runner_sha256"], "runner_sha256")
    if len(runner_sha256) != 64:
        raise ProtocolError("runner_sha256 must be a SHA-256 digest")
    return auth_path, authorization, authorization_id, authorization_hash, runner_commit, runner_sha256


def _read_archived_authorization_for_recovery(
    root: Path,
    archive_path: Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str,
) -> dict[str, Any]:
    """Independently validate an archived authorization for recovery identity."""
    if sha256_file(archive_path) != expected_authorization_sha256:
        raise ProtocolError("Archived authorization hash mismatch during recovery")
    authorization = read_json_no_duplicates(archive_path)
    expected_keys = NEUTRAL_AUTHORIZATION_KEYS if expected_scope == NEUTRAL_SCOPE else STAGE_Q_AUTHORIZATION_KEYS
    require_exact_keys(authorization, expected_keys, "archived authorization")
    if authorization["schema_version"] != SCHEMA_VERSION or authorization["experiment"] != EXPERIMENT:
        raise ProtocolError("Archived authorization schema identity mismatch")
    if authorization["scope"] != expected_scope:
        raise ProtocolError("Archived authorization scope mismatch")
    authorization_id = require_string(authorization["authorization_id"], "authorization_id")
    if authorization_id != expected_authorization_id:
        raise ProtocolError("Archived authorization ID mismatch")
    runner_commit = require_string(authorization["runner_commit"], "runner_commit")
    runner_sha256 = require_string(authorization["runner_sha256"], "runner_sha256")
    if len(runner_sha256) != 64:
        raise ProtocolError("Archived runner_sha256 must be a SHA-256 digest")
    return authorization


def _build_disposition_journal(
    root: Path,
    archive_path: Path,
    disposition_path: Path,
    authorization_id: str,
    authorization_hash: str,
    authorization_scope: str,
    runner_commit: str,
    runner_sha256: str,
    transaction_id: str,
    disposition_record_id: str,
    non_executable_reason: str,
) -> dict[str, Any]:
    """Build and validate the PREPARED disposition intent journal."""
    timestamp = datetime.now(timezone.utc).isoformat()
    journal: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "disposition_type": AUTHORIZATION_DISPOSITION_TYPE,
        "authorization_id": authorization_id,
        "authorization_sha256": authorization_hash,
        "authorization_scope": authorization_scope,
        "authorization_runner_commit": runner_commit,
        "authorization_runner_sha256": runner_sha256,
        "transaction_id": transaction_id,
        "disposition_record_id": disposition_record_id,
        "state": DISPOSITION_STATE_PREPARED,
        "expected_archive_path": _relative_path_string(archive_path, root),
        "expected_disposition_path": _relative_path_string(disposition_path, root),
        "non_executable_reason": non_executable_reason,
        "created_at": timestamp,
        "updated_at": timestamp,
        "explicit_disposition_authorized": True,
        "journal_sha256": "",
    }
    journal["journal_sha256"] = _disposition_journal_sha256(journal)
    validate_disposition_journal(journal)
    return journal


def _publish_disposition_journal(
    journal_path: Path, journal: Mapping[str, Any], root: Path
) -> Path:
    """Exclusively create the PREPARED disposition journal."""
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    return atomic_publish_json(journal_path, journal, root)


def _archive_disposition_authorization(
    auth_path: Path, archive_destination: Path, authorization_hash: str
) -> None:
    """Move original authorization bytes to archive and verify byte preservation."""
    archive_destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(auth_path, archive_destination)
    except OSError as exc:
        raise ProtocolError("Authorization archive move failed") from exc
    if sha256_file(archive_destination) != authorization_hash:
        raise ProtocolError("Archived authorization hash drifted during disposition")


def _build_disposition_record(journal: Mapping[str, Any]) -> dict[str, Any]:
    """Build and validate the completed disposition record from the exact journal identity."""
    record: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "disposition_type": AUTHORIZATION_DISPOSITION_TYPE,
        "authorization_id": journal["authorization_id"],
        "authorization_sha256": journal["authorization_sha256"],
        "authorization_scope": journal["authorization_scope"],
        "authorization_runner_commit": journal["authorization_runner_commit"],
        "authorization_runner_sha256": journal["authorization_runner_sha256"],
        "authorization_consumed": False,
        "consumption_record_exists": False,
        "qualification_result_exists": False,
        "non_executable_reason": journal["non_executable_reason"],
        "replacement_automatically_authorized": False,
        "original_can_never_be_consumed": True,
        "archived_authorization_path": journal["expected_archive_path"],
        "disposition_record_id": journal["disposition_record_id"],
        "disposition_timestamp": datetime.now(timezone.utc).isoformat(),
        "explicit_disposition_authorized": True,
        "transaction_id": journal["transaction_id"],
        "state": DISPOSITION_STATE_DISPOSITIONED,
        "journal_sha256": journal["journal_sha256"],
    }
    validate_disposition_record(record)
    return record


def _publish_disposition_record(
    disposition_path: Path, record: Mapping[str, Any], root: Path
) -> Path:
    """Exclusively create the completed disposition record."""
    disposition_path.parent.mkdir(parents=True, exist_ok=True)
    return atomic_publish_json(disposition_path, record, root)


def _load_matching_journal(
    root: Path,
    journal_path: Path,
    archive_path: Path,
    disposition_path: Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str,
    expected_runner_commit: str,
    expected_runner_sha256: str,
    expected_transaction_id: str,
    expected_disposition_record_id: str,
) -> dict[str, Any]:
    """Load a journal and require exact independent authorization/transaction identity."""
    journal = read_json_no_duplicates(journal_path)
    validate_disposition_journal(journal)
    if journal["authorization_id"] != expected_authorization_id:
        raise ProtocolError("Disposition journal authorization ID mismatch")
    if journal["authorization_sha256"] != expected_authorization_sha256:
        raise ProtocolError("Disposition journal authorization hash mismatch")
    if journal["authorization_scope"] != expected_scope:
        raise ProtocolError("Disposition journal authorization scope mismatch")
    if journal["authorization_runner_commit"] != expected_runner_commit:
        raise ProtocolError("Disposition journal runner commit mismatch")
    if journal["authorization_runner_sha256"] != expected_runner_sha256:
        raise ProtocolError("Disposition journal runner SHA mismatch")
    if journal["transaction_id"] != expected_transaction_id:
        raise ProtocolError("Disposition journal transaction ID mismatch")
    if journal["disposition_record_id"] != expected_disposition_record_id:
        raise ProtocolError("Disposition journal record ID mismatch")
    expected_archive = _relative_path_string(archive_path, root)
    expected_disposition = _relative_path_string(disposition_path, root)
    if journal["expected_archive_path"] != expected_archive:
        raise ProtocolError("Disposition journal archive path mismatch")
    if journal["expected_disposition_path"] != expected_disposition:
        raise ProtocolError("Disposition journal disposition path mismatch")
    return journal


def _load_matching_disposition_record(
    root: Path,
    disposition_path: Path,
    archive_path: Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str,
    expected_runner_commit: str,
    expected_runner_sha256: str,
    expected_transaction_id: str,
    expected_disposition_record_id: str,
    journal: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Load and require exact independent identity, archive, and optional journal binding."""
    record = read_json_no_duplicates(disposition_path)
    validate_disposition_record(record)
    if record["authorization_id"] != expected_authorization_id:
        raise ProtocolError("Disposition record authorization ID mismatch")
    if record["authorization_sha256"] != expected_authorization_sha256:
        raise ProtocolError("Disposition record authorization hash mismatch")
    if record["authorization_scope"] != expected_scope:
        raise ProtocolError("Disposition record authorization scope mismatch")
    if record["authorization_runner_commit"] != expected_runner_commit:
        raise ProtocolError("Disposition record runner commit mismatch")
    if record["authorization_runner_sha256"] != expected_runner_sha256:
        raise ProtocolError("Disposition record runner SHA mismatch")
    if record["transaction_id"] != expected_transaction_id:
        raise ProtocolError("Disposition record transaction ID mismatch")
    if record["disposition_record_id"] != expected_disposition_record_id:
        raise ProtocolError("Disposition record record ID mismatch")
    if record["archived_authorization_path"] != _relative_path_string(archive_path, root):
        raise ProtocolError("Disposition record archive path mismatch")
    if sha256_file(archive_path) != record["authorization_sha256"]:
        raise ProtocolError("Disposition record archive hash mismatch")
    if journal is not None:
        if record["transaction_id"] != journal["transaction_id"]:
            raise ProtocolError("Disposition record transaction identity mismatch")
        if record["disposition_record_id"] != journal["disposition_record_id"]:
            raise ProtocolError("Disposition record ID mismatch")
        if record["journal_sha256"] != journal["journal_sha256"]:
            raise ProtocolError("Disposition record journal hash mismatch")
    return record


def inspect_disposition_transaction(
    repo_root: str | Path,
    active_authorization_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str = NEUTRAL_SCOPE,
) -> dict[str, Any]:
    """Inspect filesystem state and return an unambiguous disposition lifecycle state."""
    root = Path(repo_root).resolve()
    require_string(expected_authorization_id, "expected_authorization_id")
    require_string(expected_authorization_sha256, "expected_authorization_sha256")
    active_path = confined_path(active_authorization_path, root, allow_missing=True)
    archive_path, journal_path, disposition_path = _disposition_transaction_paths(
        root, expected_authorization_sha256
    )
    active_exists = os.path.lexists(active_path)
    archive_exists = os.path.lexists(archive_path)
    journal_exists = os.path.lexists(journal_path)
    disposition_exists = os.path.lexists(disposition_path)

    def result(state: str, replacement_blocked: bool) -> dict[str, Any]:
        return {
            "state": state,
            "active_exists": active_exists,
            "archive_exists": archive_exists,
            "journal_exists": journal_exists,
            "disposition_exists": disposition_exists,
            "active_authorization_path": _relative_path_string(active_path, root),
            "archive_path": _relative_path_string(archive_path, root),
            "journal_path": _relative_path_string(journal_path, root),
            "disposition_path": _relative_path_string(disposition_path, root),
            "replacement_blocked": replacement_blocked,
        }

    if active_exists and archive_exists:
        return result(DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT, True)

    if active_exists:
        if journal_exists:
            (
                _active_path,
                _authorization,
                _authorization_id,
                authorization_hash,
                runner_commit,
                runner_sha256,
            ) = _read_active_authorization_for_disposition(
                root,
                active_path,
                expected_scope,
                expected_authorization_id,
                expected_authorization_sha256,
            )
            transaction_id, disposition_record_id = _disposition_transaction_ids(
                authorization_hash
            )
            _load_matching_journal(
                root,
                journal_path,
                archive_path,
                disposition_path,
                expected_authorization_id,
                expected_authorization_sha256,
                expected_scope,
                runner_commit,
                runner_sha256,
                transaction_id,
                disposition_record_id,
            )
            if disposition_exists:
                return result(DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT, True)
            return result(DISPOSITION_STATE_PREPARED_OR_IN_PROGRESS, True)
        if disposition_exists:
            return result(DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT, True)
        return result(DISPOSITION_STATE_ACTIVE, True)

    if archive_exists:
        if sha256_file(archive_path) != expected_authorization_sha256:
            return result(DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT, True)
        journal = None
        archived = None
        if journal_exists or disposition_exists:
            archived = _read_archived_authorization_for_recovery(
                root,
                archive_path,
                expected_authorization_id,
                expected_authorization_sha256,
                expected_scope,
            )
            transaction_id, disposition_record_id = _disposition_transaction_ids(
                expected_authorization_sha256
            )
        if journal_exists:
            journal = _load_matching_journal(
                root,
                journal_path,
                archive_path,
                disposition_path,
                expected_authorization_id,
                expected_authorization_sha256,
                expected_scope,
                archived["runner_commit"],
                archived["runner_sha256"],
                transaction_id,
                disposition_record_id,
            )
        if disposition_exists:
            _load_matching_disposition_record(
                root,
                disposition_path,
                archive_path,
                expected_authorization_id,
                expected_authorization_sha256,
                expected_scope,
                archived["runner_commit"],
                archived["runner_sha256"],
                transaction_id,
                disposition_record_id,
                journal,
            )
            return result(DISPOSITION_STATE_DISPOSITIONED, False)
        if journal_exists:
            return result(DISPOSITION_STATE_PARTIAL_OR_RECOVERY_REQUIRED, True)
        return result(DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT, True)

    if journal_exists or disposition_exists:
        return result(DISPOSITION_STATE_AMBIGUOUS_OR_CORRUPT, True)
    return result(DISPOSITION_STATE_CLEAR, False)


def is_replacement_authorization_blocked(
    repo_root: str | Path,
    active_authorization_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str = NEUTRAL_SCOPE,
) -> bool:
    """Return whether an unresolved disposition state blocks a replacement authorization."""
    return inspect_disposition_transaction(
        repo_root,
        active_authorization_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_scope,
    )["replacement_blocked"]


def recover_disposition_transaction(
    repo_root: str | Path,
    active_authorization_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str = NEUTRAL_SCOPE,
    *,
    explicit_disposition_authorized: bool,
    non_executable_reason: str,
) -> dict[str, Any]:
    """Resume only an exact interrupted disposition transaction or return the completed one.

    The journal is never the authority for authorization or transaction identity.
    Recovery reconstructs expected runner and transaction identity from the active
    authorization, or from the archived authorization after the move.
    """
    root = Path(repo_root).resolve()
    if explicit_disposition_authorized is not True:
        raise ProtocolError("Explicit disposition recovery authorization is required")
    require_string(non_executable_reason, "non_executable_reason")
    active_path = confined_path(active_authorization_path, root, allow_missing=True)
    archive_path, journal_path, disposition_path = _disposition_transaction_paths(
        root, expected_authorization_sha256
    )
    lifecycle = inspect_disposition_transaction(
        root,
        active_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_scope,
    )

    if lifecycle["state"] == DISPOSITION_STATE_DISPOSITIONED:
        archived = _read_archived_authorization_for_recovery(
            root,
            archive_path,
            expected_authorization_id,
            expected_authorization_sha256,
            expected_scope,
        )
        transaction_id, disposition_record_id = _disposition_transaction_ids(
            expected_authorization_sha256
        )
        record = _load_matching_disposition_record(
            root,
            disposition_path,
            archive_path,
            expected_authorization_id,
            expected_authorization_sha256,
            expected_scope,
            archived["runner_commit"],
            archived["runner_sha256"],
            transaction_id,
            disposition_record_id,
        )
        validate_disposition_record(record)
        return record

    if lifecycle["state"] == DISPOSITION_STATE_PREPARED_OR_IN_PROGRESS:
        (
            active_path,
            _authorization,
            _authorization_id,
            authorization_hash,
            runner_commit,
            runner_sha256,
        ) = _read_active_authorization_for_disposition(
            root,
            active_path,
            expected_scope,
            expected_authorization_id,
            expected_authorization_sha256,
        )
        transaction_id, disposition_record_id = _disposition_transaction_ids(
            authorization_hash
        )
        journal = _load_matching_journal(
            root,
            journal_path,
            archive_path,
            disposition_path,
            expected_authorization_id,
            expected_authorization_sha256,
            expected_scope,
            runner_commit,
            runner_sha256,
            transaction_id,
            disposition_record_id,
        )
        if journal["non_executable_reason"] != non_executable_reason:
            raise ProtocolError("Disposition recovery non-executable reason mismatch")
        _archive_disposition_authorization(active_path, archive_path, authorization_hash)
        record = _build_disposition_record(journal)
        _publish_disposition_record(disposition_path, record, root)
    elif lifecycle["state"] == DISPOSITION_STATE_PARTIAL_OR_RECOVERY_REQUIRED:
        archived = _read_archived_authorization_for_recovery(
            root,
            archive_path,
            expected_authorization_id,
            expected_authorization_sha256,
            expected_scope,
        )
        transaction_id, disposition_record_id = _disposition_transaction_ids(
            expected_authorization_sha256
        )
        journal = _load_matching_journal(
            root,
            journal_path,
            archive_path,
            disposition_path,
            expected_authorization_id,
            expected_authorization_sha256,
            expected_scope,
            archived["runner_commit"],
            archived["runner_sha256"],
            transaction_id,
            disposition_record_id,
        )
        if journal["non_executable_reason"] != non_executable_reason:
            raise ProtocolError("Disposition recovery non-executable reason mismatch")
        record = _build_disposition_record(journal)
        _publish_disposition_record(disposition_path, record, root)
    else:
        raise ProtocolError("Disposition transaction is not in a recoverable state")

    final = inspect_disposition_transaction(
        root,
        active_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_scope,
    )
    if final["state"] != DISPOSITION_STATE_DISPOSITIONED:
        raise ProtocolError("Disposition recovery did not reach a completed state")
    return record


def disposition_unconsumed_nonexecutable_authorization(
    repo_root: str | Path,
    authorization_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_scope: str = NEUTRAL_SCOPE,
    *,
    explicit_disposition_authorized: bool,
    non_executable_reason: str,
) -> dict[str, Any]:
    """Archive an issued, unconsumed, non-executable authorization without consuming it.

    The operation is modeled as an explicit crash-safe transaction: publish a
    PREPARED journal, move the original bytes to archive, verify the archive
    hash, then publish the completed disposition record. Interrupted states are
    detectable and block replacement until exact recovery.
    """
    root = Path(repo_root).resolve()
    if explicit_disposition_authorized is not True:
        raise ProtocolError("Explicit disposition authorization is required")
    require_string(non_executable_reason, "non_executable_reason")
    (
        auth_path,
        _authorization,
        authorization_id,
        authorization_hash,
        runner_commit,
        runner_sha256,
    ) = _read_active_authorization_for_disposition(
        root,
        authorization_path,
        expected_scope,
        expected_authorization_id,
        expected_authorization_sha256,
    )
    archive_path, journal_path, disposition_path = _disposition_transaction_paths(
        root, authorization_hash
    )
    if (
        os.path.lexists(archive_path)
        or os.path.lexists(journal_path)
        or os.path.lexists(disposition_path)
    ):
        raise ProtocolError("Disposition transaction state already exists")
    transaction_id, disposition_record_id = _disposition_transaction_ids(
        authorization_hash
    )
    journal = _build_disposition_journal(
        root,
        archive_path,
        disposition_path,
        authorization_id,
        authorization_hash,
        expected_scope,
        runner_commit,
        runner_sha256,
        transaction_id,
        disposition_record_id,
        non_executable_reason,
    )
    _publish_disposition_journal(journal_path, journal, root)
    _archive_disposition_authorization(auth_path, archive_path, authorization_hash)
    record = _build_disposition_record(journal)
    _publish_disposition_record(disposition_path, record, root)
    final = inspect_disposition_transaction(
        root,
        auth_path,
        authorization_id,
        authorization_hash,
        expected_scope,
    )
    if final["state"] != DISPOSITION_STATE_DISPOSITIONED:
        raise ProtocolError("Disposition transaction did not reach a completed state")
    return record


def consume_authorization(
    authorization_path: str | Path,
    consumption_path: str | Path,
    repo_root: str | Path,
    expected_scope: str,
    *,
    expected_identity: Mapping[str, Any] | None = None,
    expected_output_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate and atomically consume a single-use authorization."""
    authorization = read_json_no_duplicates(authorization_path)
    output_path = validate_authorization(
        authorization,
        expected_scope,
        repo_root,
        expected_identity=expected_identity,
        expected_output_path=expected_output_path,
    )
    consumption_destination = confined_path(consumption_path, repo_root, allow_missing=True)
    if os.path.lexists(consumption_destination):
        raise ProtocolError("Authorization has already been consumed")
    authorization_hash = sha256_file(authorization_path)
    attempt = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "authorization_hash": authorization_hash,
        "attempt_id": str(uuid.uuid4()),
        "runner_commit": authorization["runner_commit"],
        "acquired_at": datetime.now(timezone.utc).isoformat(),
        "scope": expected_scope,
        "output_path": str(output_path),
        "state": "consumed",
    }
    destination = consumption_destination
    if not destination.parent.is_dir():
        raise ProtocolError(f"Required consumption parent is missing: {destination.parent}")
    try:
        with destination.open("x", encoding="utf-8", newline="") as handle:
            json.dump(attempt, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
    except FileExistsError as exc:
        raise ProtocolError("Authorization was consumed concurrently") from exc
    return authorization, attempt


def _stage_q_archive_transaction_paths(
    root: Path, authorization_sha256: str
) -> tuple[Path, Path, Path, Path]:
    """Return deterministic consumed Stage-Q archive, journal, and status paths."""
    authorization_archive_path = confined_path(
        root / STAGE_Q_AUTHORIZATION_ARCHIVE_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    consumption_archive_path = confined_path(
        root / STAGE_Q_CONSUMPTION_ARCHIVE_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    journal_path = confined_path(
        root / STAGE_Q_CONSUMPTION_ARCHIVE_JOURNAL_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    status_path = confined_path(
        root / STAGE_Q_CONSUMPTION_ARCHIVE_STATUS_RELATIVE_DIR / f"{authorization_sha256}.json",
        root,
        allow_missing=True,
    )
    return authorization_archive_path, consumption_archive_path, journal_path, status_path


def _stage_q_archive_transaction_ids(authorization_sha256: str) -> tuple[str, str]:
    """Return deterministic consumed Stage-Q transaction identities."""
    return "SQ-ARCH-TXN-" + authorization_sha256, "SQ-STATUS-" + authorization_sha256


def _stage_q_archive_journal_sha256(journal: Mapping[str, Any]) -> str:
    """Hash the stable consumed Stage-Q journal identity without the self field."""
    stable = {key: value for key, value in journal.items() if key != "journal_sha256"}
    canonical = json.dumps(stable, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_bytes(canonical.encode("utf-8"))


def validate_stage_q_archive_journal(journal: Mapping[str, Any]) -> None:
    """Validate the closed schema and fail-closed invariants of an archive journal."""
    require_exact_keys(journal, STAGE_Q_ARCHIVE_JOURNAL_KEYS, "Stage-Q archive journal")
    if journal["schema_version"] != SCHEMA_VERSION or journal["experiment"] != EXPERIMENT:
        raise ProtocolError("Stage-Q archive journal schema identity mismatch")
    if journal["archive_type"] != STAGE_Q_ARCHIVE_TYPE:
        raise ProtocolError("Stage-Q archive journal type mismatch")
    if journal["state"] != STAGE_Q_ARCHIVE_STATE_PREPARED:
        raise ProtocolError("Stage-Q archive journal must be in PREPARED state")
    require_string(journal["authorization_id"], "authorization_id")
    require_string(journal["authorization_sha256"], "authorization_sha256")
    require_string(journal["consumption_sha256"], "consumption_sha256")
    require_string(journal["attempt_id"], "attempt_id")
    if len(journal["authorization_sha256"]) != 64 or len(journal["consumption_sha256"]) != 64:
        raise ProtocolError("Stage-Q archive journal contains an invalid SHA-256 digest")
    if journal["scope"] != STAGE_Q_SCOPE:
        raise ProtocolError("Stage-Q archive journal scope mismatch")
    require_string(journal["runner_commit"], "runner_commit")
    require_string(journal["transaction_id"], "transaction_id")
    require_string(journal["status_record_id"], "status_record_id")
    require_string(journal["expected_authorization_archive_path"], "expected_authorization_archive_path")
    require_string(journal["expected_consumption_archive_path"], "expected_consumption_archive_path")
    require_string(journal["expected_status_path"], "expected_status_path")
    if journal["original_can_never_be_consumed"] is not True:
        raise ProtocolError("Stage-Q archive journal must permanently exhaust the authorization")
    if journal["result_exists"] is not False:
        raise ProtocolError("Stage-Q archive journal requires no canonical result")
    if journal["attempt_outcome"] != "TECHNICALLY_INVALID":
        raise ProtocolError("Stage-Q archive journal attempt outcome mismatch")
    if journal["measurement_status"] != "NOT_OBSERVED_DUE_TO_TECHNICAL_INVALIDITY":
        raise ProtocolError("Stage-Q archive journal measurement status mismatch")
    parse_timestamp(journal["created_at"], "created_at")
    parse_timestamp(journal["updated_at"], "updated_at")
    if journal["explicit_archival_authorized"] is not True:
        raise ProtocolError("Stage-Q archive journal requires explicit authorization")
    require_string(journal["journal_sha256"], "journal_sha256")
    if len(journal["journal_sha256"]) != 64:
        raise ProtocolError("journal_sha256 must be a SHA-256 digest")
    if journal["journal_sha256"] != _stage_q_archive_journal_sha256(journal):
        raise ProtocolError("Stage-Q archive journal self-hash mismatch")


def validate_stage_q_terminal_attempt_status(status: Mapping[str, Any]) -> None:
    """Validate the closed terminal-attempt schema for a no-result technical invalidity."""
    require_exact_keys(status, STAGE_Q_TERMINAL_ATTEMPT_STATUS_KEYS, "Stage-Q terminal attempt status")
    if status["schema_version"] != SCHEMA_VERSION or status["experiment"] != EXPERIMENT:
        raise ProtocolError("Stage-Q terminal attempt schema identity mismatch")
    if status["status_type"] != STAGE_Q_ARCHIVE_TYPE:
        raise ProtocolError("Stage-Q terminal attempt status type mismatch")
    if status["state"] != STAGE_Q_ARCHIVE_STATE_ARCHIVED:
        raise ProtocolError("Stage-Q terminal attempt status must be ARCHIVED")
    require_string(status["authorization_id"], "authorization_id")
    require_string(status["authorization_sha256"], "authorization_sha256")
    require_string(status["consumption_sha256"], "consumption_sha256")
    require_string(status["attempt_id"], "attempt_id")
    require_string(status["scope"], "scope")
    if status["scope"] != STAGE_Q_SCOPE:
        raise ProtocolError("Stage-Q terminal attempt scope mismatch")
    require_string(status["runner_commit"], "runner_commit")
    require_string(status["transaction_id"], "transaction_id")
    require_string(status["status_record_id"], "status_record_id")
    require_string(status["authorization_archive_path"], "authorization_archive_path")
    require_string(status["consumption_archive_path"], "consumption_archive_path")
    require_string(status["journal_sha256"], "journal_sha256")
    if len(status["authorization_sha256"]) != 64 or len(status["consumption_sha256"]) != 64:
        raise ProtocolError("Stage-Q terminal attempt status contains an invalid SHA-256 digest")
    if len(status["journal_sha256"]) != 64:
        raise ProtocolError("Stage-Q terminal attempt journal_sha256 must be a SHA-256 digest")
    if status["attempt_outcome"] != "TECHNICALLY_INVALID":
        raise ProtocolError("Stage-Q terminal attempt outcome must be TECHNICALLY_INVALID")
    if status["measurement_status"] != "NOT_OBSERVED_DUE_TO_TECHNICAL_INVALIDITY":
        raise ProtocolError("Stage-Q terminal attempt measurement status mismatch")
    if status["result_exists"] is not False:
        raise ProtocolError("Stage-Q terminal attempt must have no canonical result")
    if status["original_can_never_be_consumed"] is not True:
        raise ProtocolError("Stage-Q terminal attempt must permanently exhaust the authorization")
    parse_timestamp(status["created_at"], "created_at")


def _read_consumed_stage_q_for_archive(
    root: Path,
    authorization_path: str | Path,
    consumption_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_consumption_sha256: str,
    expected_attempt_id: str,
) -> tuple[Path, dict[str, Any], str, Path, dict[str, Any], str]:
    """Validate consumed Stage-Q evidence before an archival transaction may start."""
    auth_path = confined_path(authorization_path, root)
    consumption_destination = confined_path(consumption_path, root)
    result_path = confined_path(root / STAGE_Q_RESULT_RELATIVE_PATH, root, allow_missing=True)
    if os.path.lexists(result_path):
        raise ProtocolError("Cannot archive a Stage-Q attempt with an existing canonical result")
    authorization = read_json_no_duplicates(auth_path)
    validate_authorization(authorization, STAGE_Q_SCOPE, root)
    consumption = _validate_consumption_identity(consumption_destination, STAGE_Q_SCOPE)
    authorization_hash = sha256_file(auth_path)
    consumption_hash = sha256_file(consumption_destination)
    if authorization_hash != expected_authorization_sha256:
        raise ProtocolError("Stage-Q archive authorization hash mismatch")
    if consumption_hash != expected_consumption_sha256:
        raise ProtocolError("Stage-Q archive consumption hash mismatch")
    if authorization["authorization_id"] != expected_authorization_id:
        raise ProtocolError("Stage-Q archive authorization ID mismatch")
    if consumption["authorization_hash"] != authorization_hash:
        raise ProtocolError("Stage-Q consumption authorization hash does not match retained authorization")
    if consumption["attempt_id"] != expected_attempt_id:
        raise ProtocolError("Stage-Q archive attempt ID mismatch")
    if consumption["runner_commit"] != authorization["runner_commit"]:
        raise ProtocolError("Stage-Q consumption runner commit does not match retained authorization")
    return (
        auth_path,
        authorization,
        authorization_hash,
        consumption_destination,
        consumption,
        consumption_hash,
    )


def _build_stage_q_archive_journal(
    root: Path,
    authorization_archive_path: Path,
    consumption_archive_path: Path,
    status_path: Path,
    authorization: Mapping[str, Any],
    authorization_hash: str,
    consumption: Mapping[str, Any],
    consumption_hash: str,
    transaction_id: str,
    status_record_id: str,
) -> dict[str, Any]:
    """Build and validate the PREPARED Stage-Q consumed-attempt archive journal."""
    timestamp = datetime.now(timezone.utc).isoformat()
    journal: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "archive_type": STAGE_Q_ARCHIVE_TYPE,
        "authorization_id": authorization["authorization_id"],
        "authorization_sha256": authorization_hash,
        "consumption_sha256": consumption_hash,
        "attempt_id": consumption["attempt_id"],
        "scope": STAGE_Q_SCOPE,
        "runner_commit": authorization["runner_commit"],
        "transaction_id": transaction_id,
        "status_record_id": status_record_id,
        "state": STAGE_Q_ARCHIVE_STATE_PREPARED,
        "expected_authorization_archive_path": _relative_path_string(authorization_archive_path, root),
        "expected_consumption_archive_path": _relative_path_string(consumption_archive_path, root),
        "expected_status_path": _relative_path_string(status_path, root),
        "original_can_never_be_consumed": True,
        "result_exists": False,
        "attempt_outcome": "TECHNICALLY_INVALID",
        "measurement_status": "NOT_OBSERVED_DUE_TO_TECHNICAL_INVALIDITY",
        "created_at": timestamp,
        "updated_at": timestamp,
        "explicit_archival_authorized": True,
        "journal_sha256": "",
    }
    journal["journal_sha256"] = _stage_q_archive_journal_sha256(journal)
    validate_stage_q_archive_journal(journal)
    return journal


def _publish_stage_q_archive_journal(journal_path: Path, journal: Mapping[str, Any], root: Path) -> Path:
    """Exclusively create the PREPARED Stage-Q archive journal."""
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    return atomic_publish_json(journal_path, journal, root)


def _archive_stage_q_authorization(
    auth_path: Path, archive_destination: Path, authorization_hash: str
) -> None:
    """Move retained consumed Stage-Q authorization bytes to identity-keyed archive."""
    archive_destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(auth_path, archive_destination)
    except OSError as exc:
        raise ProtocolError("Stage-Q authorization archive move failed") from exc
    if sha256_file(archive_destination) != authorization_hash:
        raise ProtocolError("Archived Stage-Q authorization hash drifted during archival")


def _archive_stage_q_consumption(
    consumption_path: Path, archive_destination: Path, consumption_hash: str
) -> None:
    """Move original Stage-Q consumption bytes to identity-keyed archive."""
    archive_destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(consumption_path, archive_destination)
    except OSError as exc:
        raise ProtocolError("Stage-Q consumption archive move failed") from exc
    if sha256_file(archive_destination) != consumption_hash:
        raise ProtocolError("Archived Stage-Q consumption hash drifted during archival")


def _build_stage_q_terminal_attempt_status(
    journal: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    """Build and validate the terminal no-result technical-invalidity status record."""
    status: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "status_type": STAGE_Q_ARCHIVE_TYPE,
        "authorization_id": journal["authorization_id"],
        "authorization_sha256": journal["authorization_sha256"],
        "consumption_sha256": journal["consumption_sha256"],
        "attempt_id": journal["attempt_id"],
        "scope": STAGE_Q_SCOPE,
        "runner_commit": journal["runner_commit"],
        "transaction_id": journal["transaction_id"],
        "status_record_id": journal["status_record_id"],
        "authorization_archive_path": journal["expected_authorization_archive_path"],
        "consumption_archive_path": journal["expected_consumption_archive_path"],
        "journal_sha256": journal["journal_sha256"],
        "attempt_outcome": journal["attempt_outcome"],
        "measurement_status": journal["measurement_status"],
        "result_exists": journal["result_exists"],
        "original_can_never_be_consumed": journal["original_can_never_be_consumed"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state": STAGE_Q_ARCHIVE_STATE_ARCHIVED,
    }
    validate_stage_q_terminal_attempt_status(status)
    return status


def _publish_stage_q_terminal_attempt_status(
    status_path: Path, status: Mapping[str, Any], root: Path
) -> Path:
    """Exclusively create the terminal Stage-Q attempt status."""
    status_path.parent.mkdir(parents=True, exist_ok=True)
    return atomic_publish_json(status_path, status, root)


def archive_consumed_stage_q_technically_invalid_attempt(
    repo_root: str | Path,
    authorization_path: str | Path,
    consumption_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_consumption_sha256: str,
    expected_attempt_id: str,
    *,
    explicit_archival_authorized: bool,
) -> dict[str, Any]:
    """Archive a consumed technically-invalid no-result Stage-Q attempt.

    The original authorization and consumption are moved to identity-keyed
    archives. A PREPARED journal is published first, both moves are hash
    verified, a terminal attempt status is published last, and only then is the
    singleton active-consumption slot considered retired.
    """
    root = Path(repo_root).resolve()
    if explicit_archival_authorized is not True:
        raise ProtocolError("Explicit Stage-Q archive authorization is required")
    require_string(expected_authorization_id, "expected_authorization_id")
    require_string(expected_authorization_sha256, "expected_authorization_sha256")
    require_string(expected_consumption_sha256, "expected_consumption_sha256")
    require_string(expected_attempt_id, "expected_attempt_id")
    (
        auth_path,
        authorization,
        authorization_hash,
        consumption_destination,
        consumption,
        consumption_hash,
    ) = _read_consumed_stage_q_for_archive(
        root,
        authorization_path,
        consumption_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_consumption_sha256,
        expected_attempt_id,
    )
    (
        authorization_archive_path,
        consumption_archive_path,
        journal_path,
        status_path,
    ) = _stage_q_archive_transaction_paths(root, authorization_hash)
    if (
        os.path.lexists(authorization_archive_path)
        or os.path.lexists(consumption_archive_path)
        or os.path.lexists(journal_path)
        or os.path.lexists(status_path)
    ):
        raise ProtocolError("Stage-Q archive transaction state already exists")
    transaction_id, status_record_id = _stage_q_archive_transaction_ids(authorization_hash)
    journal = _build_stage_q_archive_journal(
        root,
        authorization_archive_path,
        consumption_archive_path,
        status_path,
        authorization,
        authorization_hash,
        consumption,
        consumption_hash,
        transaction_id,
        status_record_id,
    )
    _publish_stage_q_archive_journal(journal_path, journal, root)
    _archive_stage_q_consumption(consumption_destination, consumption_archive_path, consumption_hash)
    _archive_stage_q_authorization(auth_path, authorization_archive_path, authorization_hash)
    status = _build_stage_q_terminal_attempt_status(journal, authorization)
    _publish_stage_q_terminal_attempt_status(status_path, status, root)
    final = inspect_stage_q_archive_transaction(
        root,
        authorization_path,
        consumption_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_consumption_sha256,
        expected_attempt_id,
    )
    if final["state"] != STAGE_Q_ARCHIVE_STATE_ARCHIVED:
        raise ProtocolError("Stage-Q archive transaction did not reach a completed state")
    return status


def inspect_stage_q_archive_transaction(
    repo_root: str | Path,
    authorization_path: str | Path,
    consumption_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_consumption_sha256: str,
    expected_attempt_id: str,
) -> dict[str, Any]:
    """Inspect filesystem state and return an unambiguous Stage-Q archive lifecycle state."""
    root = Path(repo_root).resolve()
    active_path = confined_path(authorization_path, root, allow_missing=True)
    active_consumption_path = confined_path(consumption_path, root, allow_missing=True)
    (
        authorization_archive_path,
        consumption_archive_path,
        journal_path,
        status_path,
    ) = _stage_q_archive_transaction_paths(root, expected_authorization_sha256)
    active_exists = os.path.lexists(active_path)
    active_consumption_exists = os.path.lexists(active_consumption_path)
    auth_archive_exists = os.path.lexists(authorization_archive_path)
    consumption_archive_exists = os.path.lexists(consumption_archive_path)
    journal_exists = os.path.lexists(journal_path)
    status_exists = os.path.lexists(status_path)

    def result(state: str, replacement_blocked: bool) -> dict[str, Any]:
        return {
            "state": state,
            "active_authorization_exists": active_exists,
            "active_consumption_exists": active_consumption_exists,
            "authorization_archive_exists": auth_archive_exists,
            "consumption_archive_exists": consumption_archive_exists,
            "journal_exists": journal_exists,
            "status_exists": status_exists,
            "active_authorization_path": _relative_path_string(active_path, root),
            "active_consumption_path": _relative_path_string(active_consumption_path, root),
            "authorization_archive_path": _relative_path_string(authorization_archive_path, root),
            "consumption_archive_path": _relative_path_string(consumption_archive_path, root),
            "journal_path": _relative_path_string(journal_path, root),
            "status_path": _relative_path_string(status_path, root),
            "replacement_blocked": replacement_blocked,
        }

    if active_exists and auth_archive_exists:
        return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
    if active_consumption_exists and consumption_archive_exists:
        return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)

    if active_exists and active_consumption_exists:
        if journal_exists or auth_archive_exists or consumption_archive_exists or status_exists:
            return result(STAGE_Q_ARCHIVE_STATE_PREPARED_OR_IN_PROGRESS, True)
        return result(STAGE_Q_ARCHIVE_STATE_ACTIVE, True)

    if not active_exists and not active_consumption_exists:
        if auth_archive_exists and consumption_archive_exists and status_exists:
            if sha256_file(authorization_archive_path) != expected_authorization_sha256:
                return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
            if sha256_file(consumption_archive_path) != expected_consumption_sha256:
                return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
            archived_auth = _read_archived_stage_q_authorization_for_recovery(
                root,
                authorization_archive_path,
                expected_authorization_id,
                expected_authorization_sha256,
            )
            archived_consumption = _validate_consumption_identity(
                consumption_archive_path, STAGE_Q_SCOPE
            )
            if archived_consumption["authorization_hash"] != expected_authorization_sha256:
                return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
            status = read_json_no_duplicates(status_path)
            validate_stage_q_terminal_attempt_status(status)
            if status["authorization_sha256"] != expected_authorization_sha256:
                return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
            if status["consumption_sha256"] != expected_consumption_sha256:
                return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
            if status["attempt_id"] != expected_attempt_id:
                return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)
            return result(STAGE_Q_ARCHIVE_STATE_ARCHIVED, False)
        if auth_archive_exists or consumption_archive_exists or journal_exists or status_exists:
            return result(STAGE_Q_ARCHIVE_STATE_PARTIAL_OR_RECOVERY_REQUIRED, True)
        return result(STAGE_Q_ARCHIVE_STATE_CLEAR, False)

    return result(STAGE_Q_ARCHIVE_STATE_AMBIGUOUS_OR_CORRUPT, True)


def _read_archived_stage_q_authorization_for_recovery(
    root: Path,
    archive_path: Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
) -> dict[str, Any]:
    """Validate an archived consumed Stage-Q authorization for recovery identity."""
    if sha256_file(archive_path) != expected_authorization_sha256:
        raise ProtocolError("Archived Stage-Q authorization hash mismatch during recovery")
    authorization = read_json_no_duplicates(archive_path)
    require_exact_keys(authorization, STAGE_Q_AUTHORIZATION_KEYS, "archived Stage-Q authorization")
    if authorization["schema_version"] != SCHEMA_VERSION or authorization["experiment"] != EXPERIMENT:
        raise ProtocolError("Archived Stage-Q authorization schema identity mismatch")
    if authorization["scope"] != STAGE_Q_SCOPE:
        raise ProtocolError("Archived Stage-Q authorization scope mismatch")
    if authorization["authorization_id"] != expected_authorization_id:
        raise ProtocolError("Archived Stage-Q authorization ID mismatch")
    return authorization


def recover_stage_q_archive_transaction(
    repo_root: str | Path,
    authorization_path: str | Path,
    consumption_path: str | Path,
    expected_authorization_id: str,
    expected_authorization_sha256: str,
    expected_consumption_sha256: str,
    expected_attempt_id: str,
    *,
    explicit_archival_authorized: bool,
) -> dict[str, Any]:
    """Resume only an exact interrupted Stage-Q consumed-attempt archive transaction."""
    root = Path(repo_root).resolve()
    if explicit_archival_authorized is not True:
        raise ProtocolError("Explicit Stage-Q archive recovery authorization is required")
    active_path = confined_path(authorization_path, root, allow_missing=True)
    active_consumption_path = confined_path(consumption_path, root, allow_missing=True)
    (
        authorization_archive_path,
        consumption_archive_path,
        journal_path,
        status_path,
    ) = _stage_q_archive_transaction_paths(root, expected_authorization_sha256)
    lifecycle = inspect_stage_q_archive_transaction(
        root,
        authorization_path,
        consumption_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_consumption_sha256,
        expected_attempt_id,
    )

    if lifecycle["state"] == STAGE_Q_ARCHIVE_STATE_ARCHIVED:
        return read_json_no_duplicates(status_path)

    if lifecycle["state"] == STAGE_Q_ARCHIVE_STATE_PREPARED_OR_IN_PROGRESS:
        (
            _auth_path,
            authorization,
            authorization_hash,
            consumption_destination,
            consumption,
            consumption_hash,
        ) = _read_consumed_stage_q_for_archive(
            root,
            active_path,
            active_consumption_path,
            expected_authorization_id,
            expected_authorization_sha256,
            expected_consumption_sha256,
            expected_attempt_id,
        )
        journal = read_json_no_duplicates(journal_path)
        validate_stage_q_archive_journal(journal)
        if journal["authorization_sha256"] != expected_authorization_sha256:
            raise ProtocolError("Stage-Q archive recovery journal identity mismatch")
        _archive_stage_q_consumption(consumption_destination, consumption_archive_path, consumption_hash)
        _archive_stage_q_authorization(active_path, authorization_archive_path, authorization_hash)
        status = _build_stage_q_terminal_attempt_status(journal, authorization)
        _publish_stage_q_terminal_attempt_status(status_path, status, root)
    elif lifecycle["state"] == STAGE_Q_ARCHIVE_STATE_PARTIAL_OR_RECOVERY_REQUIRED:
        if not os.path.lexists(authorization_archive_path) or not os.path.lexists(consumption_archive_path):
            raise ProtocolError("Stage-Q archive recovery is missing archived identity")
        authorization = _read_archived_stage_q_authorization_for_recovery(
            root,
            authorization_archive_path,
            expected_authorization_id,
            expected_authorization_sha256,
        )
        consumption = _validate_consumption_identity(consumption_archive_path, STAGE_Q_SCOPE)
        if consumption["authorization_hash"] != expected_authorization_sha256:
            raise ProtocolError("Stage-Q archive recovery consumption identity mismatch")
        if sha256_file(consumption_archive_path) != expected_consumption_sha256:
            raise ProtocolError("Stage-Q archive recovery consumption hash mismatch")
        if not os.path.lexists(journal_path):
            raise ProtocolError("Stage-Q archive recovery journal is missing")
        journal = read_json_no_duplicates(journal_path)
        validate_stage_q_archive_journal(journal)
        if journal["authorization_sha256"] != expected_authorization_sha256:
            raise ProtocolError("Stage-Q archive recovery journal identity mismatch")
        status = _build_stage_q_terminal_attempt_status(journal, authorization)
        _publish_stage_q_terminal_attempt_status(status_path, status, root)
    else:
        raise ProtocolError("Stage-Q archive transaction is not in a recoverable state")

    final = inspect_stage_q_archive_transaction(
        root,
        authorization_path,
        consumption_path,
        expected_authorization_id,
        expected_authorization_sha256,
        expected_consumption_sha256,
        expected_attempt_id,
    )
    if final["state"] != STAGE_Q_ARCHIVE_STATE_ARCHIVED:
        raise ProtocolError("Stage-Q archive recovery did not reach a completed state")
    return read_json_no_duplicates(status_path)


def _load_model_and_tokenizer(identity: Mapping[str, Any]) -> tuple[Any, Any]:
    """Load the frozen model only from an authorized execution path."""
    import torch  # Runtime-only model-runtime import.
    from transformers import AutoModelForCausalLM, AutoTokenizer  # Runtime-only import.

    snapshot = identity["resolved_snapshot_path"]
    tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        snapshot, torch_dtype=torch.float16, local_files_only=True,
    ).to("cuda:0")
    model.eval()
    model.config.use_cache = False
    return model, tokenizer


def _model_layers(model: Any) -> Any:
    """Return the frozen decoder layer sequence or fail closed."""
    layers = getattr(getattr(model, "model", None), "layers", None)
    if layers is None or len(layers) != 28:
        raise ProtocolError("Frozen Qwen3 decoder layer layout is unavailable")
    return layers


def _neutral_inputs(tokenizer: Any, torch: Any) -> tuple[dict[str, Any], int]:
    """Tokenize the fixed neutral sentence without padding or truncation."""
    tokenized = tokenizer(
        NEUTRAL_DIAGNOSTIC_TEXT,
        return_tensors="pt",
        padding=False,
        truncation=False,
    )
    inputs = dict(tokenized)
    input_ids = inputs.get("input_ids")
    attention_mask = inputs.get("attention_mask")
    if input_ids is None or attention_mask is None or input_ids.ndim != 2 or input_ids.shape[0] != 1:
        raise ProtocolError("Neutral tokenizer did not return one unpadded sequence")
    if not torch.equal(attention_mask, torch.ones_like(attention_mask)):
        raise ProtocolError("Neutral sequence contains padding")
    selected = int(attention_mask[0].sum().item()) - 1
    if selected < 0:
        raise ProtocolError("Neutral sequence has no valid token")
    return inputs, selected


def _forward_with_capture(model: Any, tokenizer: Any, capture_hooks: Sequence[Callable[..., Any]], torch: Any) -> tuple[Any, dict[str, Any], int]:
    """Run one no-generation forward while ensuring all hooks are removed."""
    layers = _model_layers(model)
    inputs, selected = _neutral_inputs(tokenizer, torch)
    device = next(model.parameters()).device
    inputs = {key: value.to(device) if hasattr(value, "to") else value for key, value in inputs.items()}
    handles = [layers[INTERVENTION_BLOCK].register_forward_hook(hook) for hook in capture_hooks]
    try:
        with torch.no_grad():
            outputs = model(
                **inputs,
                output_hidden_states=True,
                return_dict=True,
                use_cache=False,
            )
    finally:
        for handle in reversed(handles):
            handle.remove()
    if outputs.hidden_states is None or len(outputs.hidden_states) != 29:
        raise ProtocolError("Neutral forward hidden-state tuple is invalid")
    return outputs, {"selected_token_index": selected}, selected


def _runtime_environment(torch: Any, model: Any) -> dict[str, Any]:
    """Collect runtime identity only after authorized model loading."""
    runtime_identity = runtime_identity_binding()
    return {
        **runtime_identity,
        "dtype": str(next(model.parameters()).dtype).replace("torch.", ""),
        "device": str(next(model.parameters()).device),
        "local_files_only": True,
        "model_eval_mode": not model.training,
        "gradients_enabled": torch.is_grad_enabled(),
        "use_cache": bool(getattr(model.config, "use_cache", True)),
    }


def _neutral_input_identity() -> str:
    """Hash the neutral input without placing its text in any result."""
    return sha256_bytes(NEUTRAL_DIAGNOSTIC_TEXT.encode("utf-8"))


def _load_frozen_split_config(root: Path) -> dict[str, Any]:
    """Load only the frozen split metadata after Stage-Q authorization."""
    config_path = confined_path(root / EXP020_CONFIG, root)
    if sha256_file(config_path) != EXP020_CONFIG_SHA256:
        raise ProtocolError("Frozen EXP-020 split configuration hash mismatch")
    config = read_json_no_duplicates(config_path)
    dataset = config.get("dataset")
    if not isinstance(dataset, Mapping) or len(dataset.get("splits", [])) != 2:
        raise ProtocolError("Frozen split metadata is invalid")
    return config


def load_fit_source_records(root: Path, split_id: str) -> list[dict[str, str]]:
    """Extract only active-split FIT records; EVAL text is never parsed or returned."""
    config = _load_frozen_split_config(root)
    dataset = config["dataset"]
    split = next((item for item in dataset["splits"] if item.get("id") == split_id), None)
    if not isinstance(split, Mapping):
        raise ProtocolError("Unknown frozen split")
    fit_ids_by_class = split.get("fit_ids")
    if not isinstance(fit_ids_by_class, Mapping) or set(fit_ids_by_class) != set(CLASS_ORDER):
        raise ProtocolError("Frozen FIT role metadata is invalid")
    fit_ids = [item_id for label in CLASS_ORDER for item_id in fit_ids_by_class[label]]
    if len(fit_ids) != 12 or len(set(fit_ids)) != 12 or any(len(fit_ids_by_class[label]) != 3 for label in CLASS_ORDER):
        raise ProtocolError("Frozen split must contain exactly twelve unique FIT IDs")
    fit_set = set(fit_ids)
    prompt_path = confined_path(root / dataset["prompt_file"], root)
    if sha256_file(prompt_path) != dataset["prompt_file_sha256"]:
        raise ProtocolError("Frozen prompt source hash mismatch")
    document = read_json_value_no_duplicates(prompt_path)
    if not isinstance(document, list):
        raise ProtocolError("Frozen prompt source must be a JSON array")
    records: list[dict[str, str]] = []
    seen: set[str] = set()
    for record in document:
        if not isinstance(record, Mapping):
            raise ProtocolError("FIT source record schema is invalid")
        item_id = record.get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ProtocolError("FIT source record schema is invalid")
        if item_id in seen:
            raise ProtocolError("Duplicate prompt source ID")
        seen.add(item_id)
        if not isinstance(record.get("text"), str) or not isinstance(record.get("group"), str):
            raise ProtocolError("FIT source record schema is invalid")
        if item_id not in fit_set:
            continue
        expected_group = next(label for label in CLASS_ORDER if item_id in set(fit_ids_by_class[label]))
        if record["group"] != expected_group:
            raise ProtocolError("FIT source record class routing is invalid")
        records.append({"item_id": item_id, "split_id": split_id, "role": "FIT", "task_class": record["group"], "prompt_text": record["text"]})
    selected_ids = {record["item_id"] for record in records}
    if selected_ids != fit_set:
        raise ProtocolError("Frozen split FIT source is incomplete")
    return validate_fit_eval_routing(records, fit_ids, [], split_id)


def _last_token_representation(tensor: Any, selected_token_index: int, torch: Any) -> Any:
    """Return a finite CPU representation without serializing hidden states."""
    if tensor.ndim != 3 or tensor.shape[0] != 1 or tensor.shape[2] != 2048:
        raise ProtocolError("Unexpected hidden-state tensor shape")
    value = tensor[0, selected_token_index, :].detach()
    if not torch.isfinite(value).all():
        raise ProtocolError("Nonfinite hidden-state representation")
    return value.to("cpu").numpy().copy()


def extract_fit_representations(model: Any, tokenizer: Any, records: Sequence[Mapping[str, str]], torch: Any) -> dict[str, Any]:
    """Extract the frozen six checkpoint representations for FIT records only."""
    import numpy as np

    layers = _model_layers(model)
    representations = {item["name"]: {} for item in CHECKPOINTS}
    for record in records:
        capture: dict[str, Any] = {}
        inputs = tokenizer(record["prompt_text"], return_tensors="pt", padding=False, truncation=False)
        inputs = dict(inputs)
        input_ids = inputs.get("input_ids")
        attention_mask = inputs.get("attention_mask")
        if input_ids is None or attention_mask is None or input_ids.ndim != 2 or input_ids.shape[0] != 1:
            raise ProtocolError("FIT tokenizer did not return one sequence")
        if not torch.equal(attention_mask, torch.ones_like(attention_mask)):
            raise ProtocolError("FIT source unexpectedly contains padding")
        selected = int(attention_mask[0].sum().item()) - 1
        if selected < 0:
            raise ProtocolError("FIT source has no valid token")
        inputs = {key: value.to(next(model.parameters()).device) if hasattr(value, "to") else value for key, value in inputs.items()}
        handle = layers[27].register_forward_hook(capture_output_hook(capture))
        try:
            with torch.no_grad():
                outputs = model(**inputs, output_hidden_states=True, return_dict=True, use_cache=False)
        finally:
            handle.remove()
        if capture.get("invocations") != 1 or outputs.hidden_states is None or len(outputs.hidden_states) != 29:
            raise ProtocolError("FIT forward checkpoint capture failed")
        for checkpoint in CHECKPOINTS:
            name = checkpoint["name"]
            if name == "final_block_pre_final_rmsnorm":
                hidden = capture["value"]
            else:
                hidden = outputs.hidden_states[checkpoint["hidden_state_index"]]
            representations[name][record["item_id"]] = _last_token_representation(hidden, selected, torch)
    arrays = {}
    for checkpoint in CHECKPOINTS:
        name = checkpoint["name"]
        ids = [record["item_id"] for record in records]
        arrays[name] = np.stack([representations[name][item_id] for item_id in ids]).astype("float16")
    return arrays


def summarize_checkpoint(rows: Sequence[Mapping[str, Any]], checkpoint: str, split_id: str) -> dict[str, Any]:
    """Validate technical invariants and summarize twelve fixed-probe predictions.

    True-label coverage and record/probability integrity are technical-validity
    prerequisites and fail closed. Predicted argmax class coverage is a frozen
    Stage-Q pass criterion: an incomplete predicted class set produces a valid
    adverse checkpoint with pass=false rather than a ProtocolError.
    """
    selected = [row for row in rows if row.get("checkpoint") == checkpoint]
    if len(selected) != 12:
        raise ProtocolError("Each Stage-Q checkpoint must produce exactly twelve predictions")
    for row in selected:
        if (
            not isinstance(row.get("true_class"), str)
            or not isinstance(row.get("predicted_class"), str)
            or not isinstance(row.get("correct"), bool)
        ):
            raise ProtocolError("Stage-Q prediction record has invalid scalar types")
        probabilities = row.get("probabilities")
        if not isinstance(probabilities, list) or len(probabilities) != 4 or any(not math.isfinite(float(value)) for value in probabilities):
            raise ProtocolError("Stage-Q probability record is invalid")
        if not math.isclose(sum(float(value) for value in probabilities), 1.0, rel_tol=1e-6, abs_tol=1e-6):
            raise ProtocolError("Stage-Q probabilities are not normalized")
    true_classes = [row.get("true_class") for row in selected]
    predicted_classes = [row.get("predicted_class") for row in selected]
    if set(true_classes) != set(CLASS_ORDER):
        raise ProtocolError("Stage-Q checkpoint lacks required true semantic classes")
    predicted_class_coverage_pass = set(predicted_classes) == set(CLASS_ORDER)
    correct = sum(bool(row.get("correct")) for row in selected)
    lower = clopper_pearson_lower_bound(correct, 12)
    return {
        "split_id": split_id,
        "checkpoint": checkpoint,
        "n": 12,
        "correct": correct,
        "accuracy": correct / 12.0,
        "clopper_pearson_lower_bound": lower,
        "predicted_class_coverage_pass": predicted_class_coverage_pass,
        "pass": predicted_class_coverage_pass and checkpoint_passes(correct, 12),
    }


def validate_neutral_result(result: Mapping[str, Any], authority: Mapping[str, Any], binding: Mapping[str, Any]) -> None:
    """Require a passed neutral result bound to all current execution identities."""
    require_exact_keys(result, NEUTRAL_RESULT_KEYS, "neutral result")
    if result["result_classification"] != "ENGINEERING_NEUTRAL_HOOK_QUALIFICATION_ONLY" or result["overall_pass"] is not True:
        raise ProtocolError("Neutral qualification did not pass")
    for key in ("runner_commit", "runner_sha256", "implementation_hashes", "authority_hashes"):
        if result[key] != binding[key]:
            raise ProtocolError(f"Neutral result drift in {key}")
    if result["model_manifest"] != model_manifest_binding(authority["primary_model_identity"]):
        raise ProtocolError("Neutral result model manifest drift")
    if result["canonical_snapshot_path"] != authority["primary_model_identity"]["canonical_snapshot_path"] or result["resolved_snapshot_path"] != authority["primary_model_identity"]["resolved_snapshot_path"]:
        raise ProtocolError("Neutral result snapshot path drift")
    if result["hook_block"] != INTERVENTION_BLOCK or result["beta"] != BETA:
        raise ProtocolError("Neutral result hook or beta drift")
    if result["token_rule"] != "last valid token of one unpadded sequence" or result["cache_semantics"].get("use_cache") is not False:
        raise ProtocolError("Neutral result token/cache semantics drift")
    if result["fit_eval_accessed"] is not False or result["scientific_result_created"] is not False:
        raise ProtocolError("Neutral result access boundary is invalid")
    if not isinstance(result["checks"], Mapping) or not all(value is True for value in result["checks"].values()):
        raise ProtocolError("Neutral result contains a failed check")
    _validate_neutral_execution_environment(
        result["execution_environment"],
        binding["environment_binding"],
        binding["runtime_identity"],
    )
    _validate_neutral_diagnostic_vector(result["diagnostic_vector"])
    _validate_neutral_input_identity(result["neutral_input_identity"])


def validate_stage_q_result(result: Mapping[str, Any]) -> None:
    """Validate the redacted engineering-only Stage-Q result schema."""
    require_exact_keys(result, STAGE_Q_RESULT_KEYS, "Stage-Q result")
    if result["result_classification"] != "ENGINEERING_MEASUREMENT_QUALIFICATION_ONLY":
        raise ProtocolError("Stage-Q result classification is not engineering-only")
    if result["eval_accessed"] is not False or result["prompt_content_printed"] is not False or result["stage_p_accessed"] is not False or result["scientific_result_created"] is not False:
        raise ProtocolError("Stage-Q result violates the access boundary")
    if result["stage_q_authorization_binding"].get("scope") != STAGE_Q_SCOPE:
        raise ProtocolError("Stage-Q authorization provenance is invalid")
    if not isinstance(result["checkpoint_summaries"], Mapping) or set(result["checkpoint_summaries"]) != {"A_original_fit_paraphrase_eval", "B_paraphrase_fit_original_eval"}:
        raise ProtocolError("Stage-Q result omits or adds a split")
    for split_summary in result["checkpoint_summaries"].values():
        if set(split_summary) != {item["name"] for item in CHECKPOINTS}:
            raise ProtocolError("Stage-Q result omits or adds a checkpoint")


def run_neutral_hook_qualification(repo_root: str | Path) -> None:
    """Execute neutral qualification only after consuming its authorization."""
    root = Path(repo_root).resolve()
    authority = validate_authority_files(root, verify_model_files=False)
    validate_mode_lifecycle(root, LIFECYCLE_MODE_NEUTRAL)
    validate_checkpoint_mapping(authority["checkpoint_mapping"])
    binding = build_static_execution_binding(root, authority)
    auth_path = confined_path(root / "experiments/exp021/authorization/neutral.json", root)
    consumption_path = confined_path(root / "experiments/exp021/consumed/neutral.json", root, allow_missing=True)
    output_path = confined_path(NEUTRAL_RESULT_RELATIVE_PATH, root, allow_missing=True)
    authorization, consumption = consume_authorization(
        auth_path,
        consumption_path,
        root,
        NEUTRAL_SCOPE,
        expected_identity=binding,
        expected_output_path=output_path,
    )
    # Runtime imports and full shard verification begin only after consumption.
    import torch

    validate_model_manifest(authority["primary_model_identity"], verify_payload=True)
    model, tokenizer = _load_model_and_tokenizer(authority["primary_model_identity"])
    started = datetime.now(timezone.utc).isoformat()
    reference_state: dict[str, Any] = {}
    _forward_with_capture(model, tokenizer, [capture_output_hook(reference_state)], torch)
    inactive_state: dict[str, Any] = {}
    inactive_hook, inactive_counter = production_hook_factory(
        deterministic_diagnostic_vector(2048)[0], BETA, 0, active=False
    )
    _, inactive_context, selected = _forward_with_capture(
        model,
        tokenizer,
        [capture_output_hook(inactive_state), inactive_hook],
        torch,
    )
    active_pre: dict[str, Any] = {}
    active_post: dict[str, Any] = {}
    diagnostic_values, diagnostic_sha = deterministic_diagnostic_vector(2048)
    active_hook, active_counter = production_hook_factory(
        torch.tensor(diagnostic_values, dtype=torch.float32, device="cuda:0"),
        BETA,
        selected,
        active=True,
    )
    _, active_context, active_selected = _forward_with_capture(
        model,
        tokenizer,
        [capture_output_hook(active_pre), active_hook, capture_output_hook(active_post)],
        torch,
    )
    if reference_state.get("invocations") != 1 or inactive_state.get("invocations") != 1:
        raise ProtocolError("Neutral capture invocation count mismatch")
    if active_pre.get("invocations") != 1 or active_post.get("invocations") != 1:
        raise ProtocolError("Active capture invocation count mismatch")
    if not torch.equal(reference_state["value"], inactive_state["value"]):
        raise ProtocolError("Inactive hook changed the captured block output")
    expected = construct_expected_hook_output(active_pre["value"], torch.tensor(diagnostic_values, device="cuda:0"), BETA, active_selected)
    validate_active_hook_output(
        active_pre["value"],
        active_post["value"],
        expected,
        active_selected,
        active_counter["invocations"],
    )
    with torch.no_grad():
        environment = _runtime_environment(torch, model)
    checks = {
        "inactive_hook_exact": True,
        "active_hook_exact": True,
        "inactive_invocations": inactive_counter["invocations"] == 1,
        "active_invocations": active_counter["invocations"] == 1,
        "selected_last_valid_token": active_selected == selected,
        "use_cache_false": environment["use_cache"] is False,
        "gradients_disabled": environment["gradients_enabled"] is False,
    }
    if not all(checks.values()):
        raise ProtocolError("Neutral hook qualification failed")
    finished = datetime.now(timezone.utc).isoformat()
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "result_classification": "ENGINEERING_NEUTRAL_HOOK_QUALIFICATION_ONLY",
        "attempt_id": consumption["attempt_id"],
        "authorization_id": authorization["authorization_id"],
        "authorization_hash": consumption["authorization_hash"],
        "runner_commit": binding["runner_commit"],
        "runner_sha256": binding["runner_sha256"],
        "implementation_hashes": binding["implementation_hashes"],
        "authority_hashes": binding["authority_hashes"],
        "model_manifest": model_manifest_binding(authority["primary_model_identity"]),
        "canonical_snapshot_path": authority["primary_model_identity"]["canonical_snapshot_path"],
        "resolved_snapshot_path": authority["primary_model_identity"]["resolved_snapshot_path"],
        "execution_environment": environment,
        "hook_block": INTERVENTION_BLOCK,
        "token_rule": "last valid token of one unpadded sequence",
        "beta": BETA,
        "diagnostic_vector": {"algorithm": "alternating_plus_minus_one", "length": len(diagnostic_values), "sha256": diagnostic_sha},
        "neutral_input_identity": {"sha256": _neutral_input_identity()},
        "cache_semantics": {"use_cache": False, "shared_kv_cache": False},
        "checks": checks,
        "started_at": started,
        "finished_at": finished,
        "fit_eval_accessed": False,
        "scientific_result_created": False,
        "overall_pass": True,
    }
    validate_neutral_result(result, authority, binding)
    atomic_publish_json(output_path, result, root)


def run_stage_q(repo_root: str | Path) -> None:
    """Execute Stage Q only after neutral qualification and authorization checks."""
    root = Path(repo_root).resolve()
    authority = validate_authority_files(root, verify_model_files=False)
    validate_mode_lifecycle(root, LIFECYCLE_MODE_STAGE_Q)
    validate_checkpoint_mapping(authority["checkpoint_mapping"])
    binding = build_static_execution_binding(root, authority)
    neutral_result_path = confined_path(root / NEUTRAL_RESULT_RELATIVE_PATH, root)
    neutral_result = read_json_no_duplicates(neutral_result_path)
    historical_binding = build_historical_neutral_binding(
        root,
        neutral_result_path,
        neutral_result,
    )
    validate_neutral_result(neutral_result, authority, historical_binding)
    auth_path = confined_path(root / "experiments/exp021/authorization/stage_q.json", root)
    consumption_path = confined_path(root / "experiments/exp021/consumed/stage_q.json", root, allow_missing=True)
    output_path = confined_path(STAGE_Q_RESULT_RELATIVE_PATH, root, allow_missing=True)
    authorization, consumption = consume_authorization(
        auth_path,
        consumption_path,
        root,
        STAGE_Q_SCOPE,
        expected_identity=binding,
        expected_output_path=output_path,
    )
    # Full model identity verification occurs only after irreversible consumption.
    import torch

    validate_model_manifest(authority["primary_model_identity"], verify_payload=True)
    model, tokenizer = _load_model_and_tokenizer(authority["primary_model_identity"])
    config = _load_frozen_split_config(root)
    all_gate_rows: list[dict[str, Any]] = []
    split_summaries: dict[str, Any] = {}
    checkpoint_summaries: dict[str, Any] = {}
    processed_fit_ids: dict[str, list[str]] = {}
    for split in config["dataset"]["splits"]:
        split_id = split["id"]
        records = load_fit_source_records(root, split_id)
        fit_ids = [record["item_id"] for record in records]
        processed_fit_ids[split_id] = fit_ids
        labels = [record["task_class"] for record in records]
        representations = extract_fit_representations(model, tokenizer, records, torch)
        probe_rows = leave_one_out_fixed_probe(representations, labels)
        split_summaries[split_id] = {"fit_count": len(records), "fit_ids": fit_ids}
        for checkpoint in CHECKPOINTS:
            name = checkpoint["name"]
            summary = summarize_checkpoint(probe_rows, name, split_id)
            checkpoint_summaries.setdefault(split_id, {})[name] = summary
            if name in REQUIRED_GATE_CHECKPOINTS:
                all_gate_rows.append(summary)
    gate = stage_q_global_gate(
        all_gate_rows,
        tuple(split["id"] for split in config["dataset"]["splits"]),
        REQUIRED_GATE_CHECKPOINTS,
    )
    descriptive = {
        split_id: values["final_normalized_hidden_state"]
        for split_id, values in checkpoint_summaries.items()
    }
    with torch.no_grad():
        execution_environment = _runtime_environment(torch, model)
    result = {
        "schema_version": SCHEMA_VERSION,
        "experiment": EXPERIMENT,
        "result_classification": "ENGINEERING_MEASUREMENT_QUALIFICATION_ONLY",
        "runner_commit": binding["runner_commit"],
        "runner_sha256": binding["runner_sha256"],
        "implementation_hashes": binding["implementation_hashes"],
        "authority_hashes": binding["authority_hashes"],
        "model_manifest": model_manifest_binding(authority["primary_model_identity"]),
        "canonical_snapshot_path": authority["primary_model_identity"]["canonical_snapshot_path"],
        "resolved_snapshot_path": authority["primary_model_identity"]["resolved_snapshot_path"],
        "neutral_result_binding": {
            "attempt_id": neutral_result["attempt_id"],
            "authorization_id": neutral_result["authorization_id"],
            "authorization_hash": neutral_result["authorization_hash"],
            "runner_sha256": neutral_result["runner_sha256"],
        },
        "stage_q_authorization_binding": {
            "authorization_id": authorization["authorization_id"],
            "authorization_hash": consumption["authorization_hash"],
            "attempt_id": consumption["attempt_id"],
            "scope": STAGE_Q_SCOPE,
        },
        "split_summaries": split_summaries,
        "checkpoint_summaries": checkpoint_summaries,
        "processed_fit_ids": processed_fit_ids,
        "checkpoint_mapping": authority["checkpoint_mapping"],
        "execution_environment": execution_environment,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "eval_accessed": False,
        "prompt_content_printed": False,
        "stage_p_accessed": False,
        "scientific_result_created": False,
        "global_pass": gate,
        "descriptive_post_norm": descriptive,
    }
    validate_stage_q_result(result)
    atomic_publish_json(output_path, result, root)


def run_static_preflight(repo_root: str | Path) -> dict[str, Any]:
    """Run metadata-only authority and implementation preflight."""
    root = Path(repo_root).resolve()
    authority = validate_authority_files(root)
    validate_mode_lifecycle(root, LIFECYCLE_MODE_STATIC)
    validate_checkpoint_mapping(authority["checkpoint_mapping"])
    return {
        "status": "EXP021_STATIC_PREFLIGHT_PASS",
        "experiment": EXPERIMENT,
        "stage_q_authorizable": False,
        "stage_p_authorizable": False,
        "model_manifest_validated": True,
        "prompt_text_accessed": False,
        "tensor_payload_accessed": False,
        "persistent_output_created": False,
    }


def build_parser() -> argparse.ArgumentParser:
    """Build the mutually exclusive three-mode CLI parser."""
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--static-preflight", action="store_true")
    modes.add_argument("--neutral-hook-qualification", action="store_true")
    modes.add_argument("--stage-q", action="store_true")
    parser.add_argument("--repo-root", default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Dispatch exactly one explicit mode."""
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    try:
        if args.static_preflight:
            print(json.dumps(run_static_preflight(repo_root), indent=2, sort_keys=True))
        elif args.neutral_hook_qualification:
            run_neutral_hook_qualification(repo_root)
        elif args.stage_q:
            run_stage_q(repo_root)
    except ProtocolError as exc:
        print(f"EXP021_STAGE_Q_FAIL_CLOSED: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
