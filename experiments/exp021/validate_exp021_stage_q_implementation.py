"""Metadata, AST, and production-entry-contract validator for EXP-021 Stage-Q."""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import re
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "experiments/exp021/run_exp021_stage_q.py"
TESTS = ROOT / "tests/test_exp021_stage_q.py"
AUTHORITY = ROOT / "experiments/exp021/exp021_preregistration_reconciliation.json"
ORIGINAL = ROOT / "docs/experiments/EXP-021-PREREGISTRATION.md"
AMENDMENT = ROOT / "docs/experiments/EXP-021-PREREGISTRATION-AMENDMENT-01-DRAFT.md"
EXPECTED_ORIGINAL_SHA256 = "2ea9c54a49c41b3c1c8e6c39b029dc333d3ee6753ae0608603d6365ae063301a"
EXPECTED_AMENDMENT_SHA256 = "c026587c90b74d75e9f395001f94732d41f3b550c22247e5613cc6d3cc880635"
EXPECTED_AUTHORITY_BLOB = "08d621f311dbc1c9c2c00ef024cdc42a6ac3c6f7"
FORBIDDEN_MODULE_IMPORTS = {"torch", "transformers", "accelerate", "datasets", "safetensors"}
NEUTRAL_DYNAMIC_TEST = "test_neutral_production_path_validates_before_publish"
STAGE_Q_DYNAMIC_TEST = "test_stage_q_production_path_validates_neutral_before_consumption"
REQUIRED_COMMIT_BINDING_TESTS = {
    "test_authority_archive_commit_used_as_blob_anchor_without_head_gate",
    "test_authorization_accepts_exact_live_commit_binding",
    "test_authorization_rejects_live_commit_mismatch",
    "test_authorization_rejects_live_runner_hash_mismatch",
    "test_authorization_rejects_authority_archive_commit_as_live_commit",
    "test_authorization_rejects_descendant_commit_substitution",
    "test_neutral_production_entry_binds_live_commit_before_consumption",
    "test_stage_q_production_entry_binds_live_commit_before_consumption",
}
REQUIRED_DISPOSITION_TESTS = {
    "test_disposition_requires_explicit_authorization",
    "test_disposition_preserves_original_authorization_hash",
    "test_disposition_frees_active_authorization_path",
    "test_disposition_record_binds_authorization_hash",
    "test_disposition_rejects_consumed_authorization",
    "test_disposition_rejects_consumption_record",
    "test_disposition_rejects_qualification_result",
    "test_disposition_rejects_hash_drift",
    "test_disposition_rejects_existing_archive_destination",
    "test_disposition_rejects_existing_disposition_record",
    "test_disposition_does_not_create_replacement_authorization",
    "test_disposition_does_not_create_consumption_record",
    "test_disposition_archive_is_not_active_authorization",
    "test_disposition_failure_before_journal_leaves_active_unchanged",
    "test_disposition_prepared_before_move_blocks_replacement",
    "test_disposition_os_replace_failure_blocks_replacement",
    "test_disposition_interrupted_after_move_is_recoverable",
    "test_disposition_final_publication_failure_is_recoverable",
    "test_disposition_recovery_preserves_archive_and_finalizes",
    "test_disposition_recovery_is_idempotent_after_completion",
    "test_disposition_recovery_rejects_identity_mismatch",
    "test_disposition_archive_without_journal_or_record_fails_closed",
    "test_disposition_record_without_archive_fails_closed",
    "test_disposition_active_and_archive_both_exist_fails_closed",
    "test_disposition_incomplete_blocks_replacement_eligibility",
    "test_disposition_recovery_rejects_tampered_self_hashed_journal",
    "test_disposition_rejects_valid_self_hash_but_drifted_runner_identity",
    "test_disposition_recovery_resumes_exact_pre_move_prepared_state",
    "test_disposition_recovery_cross_authorization_attack_fails",
}
REQUIRED_HISTORICAL_PROVENANCE_TESTS = {
    "test_historical_neutral_producer_and_current_executor_identity_are_independent",
    "test_historical_neutral_producer_commit_tamper_fails",
    "test_historical_neutral_producer_runner_sha_tamper_fails",
    "test_stage_q_current_executor_drift_after_historical_result_still_fails",
    "test_stage_q_neutral_result_sha_dependency_mismatch_fails",
}

REQUIRED_CHECKPOINT_MAPPING_TESTS = {
    "test_checkpoint_and_probability_validation_reject_invalid_values",
    "test_checkpoint_mapping_accepts_frozen_metadata_shape",
    "test_checkpoint_mapping_rejects_missing_tuple_semantics",
    "test_checkpoint_mapping_rejects_unknown_metadata_key",
    "test_checkpoint_mapping_rejects_unknown_checkpoint_object",
    "test_checkpoint_mapping_rejects_missing_required_checkpoint",
    "test_checkpoint_mapping_rejects_wrong_tuple_semantics_type",
    "test_checkpoint_mapping_rejects_malformed_checkpoint_object",
    "test_descriptive_final_checkpoint_remains_descriptive_only",
    "test_real_reconciliation_checkpoint_mapping_passes",
}
REQUIRED_LIFECYCLE_TESTS = {
    "test_lifecycle_static_accepts_active_neutral_authorization",
    "test_lifecycle_neutral_valid_state_passes",
    "test_lifecycle_stage_q_valid_state_passes",
    "test_lifecycle_unknown_authorization_fails",
    "test_lifecycle_unknown_directory_fails",
    "test_lifecycle_legacy_result_paths_fail",
    "test_lifecycle_legacy_results_directory_fails",
    "test_lifecycle_unknown_consumed_or_engineering_child_fails",
    "test_lifecycle_multiple_active_authorizations_fail",
    "test_lifecycle_active_and_consumed_impossible_fails",
    "test_lifecycle_result_without_consumption_fails",
    "test_lifecycle_consumed_neutral_authorization_not_active",
    "test_lifecycle_consumed_neutral_qualified_result_static_passes",
    "test_lifecycle_identity_two_dispositions_plus_consumed_neutral_passes",
    "test_lifecycle_consumed_authorization_wrong_result_authorization_id_fails",
    "test_lifecycle_consumed_authorization_malformed_consumption_fails",
    "test_lifecycle_consumed_authorization_same_identity_disposition_fails",
    "test_lifecycle_consumed_authorization_result_attempt_mismatch_fails",
    "test_lifecycle_consumed_neutral_not_neutral_active",
    "test_lifecycle_stage_q_with_active_neutral_fails",
    "test_lifecycle_neutral_with_stage_q_consumption_fails",
    "test_lifecycle_known_disposition_paths_not_globally_rejected",
    "test_lifecycle_wrong_disposition_name_fails",
    "test_lifecycle_prepared_journal_matching_active_authorization_passes",
    "test_lifecycle_active_with_completed_disposition_fails",
    "test_lifecycle_active_with_journal_for_other_authorization_fails",
    "test_lifecycle_identity_completed_historical_plus_active_passes",
    "test_lifecycle_identity_neutral_production_entry_reaches_authorization_semantics",
    "test_lifecycle_identity_two_completed_historical_dispositions_plus_active_passes",
    "test_lifecycle_identity_historical_journal_not_unresolved_for_active",
    "test_lifecycle_identity_stage_q_coexists_with_historical_disposition_passes",
    "test_lifecycle_identity_real_current_structure_static_preflight_passes",
    "test_lifecycle_identity_same_authorization_active_and_disposition_fails",
    "test_lifecycle_identity_same_authorization_active_and_archive_fails",
    "test_lifecycle_identity_unresolved_prepared_blocks_replacement",
    "test_lifecycle_identity_unresolved_partial_blocks_replacement",
    "test_lifecycle_identity_ambiguous_historical_blocks_replacement",
    "test_lifecycle_identity_malformed_historical_disposition_fails",
    "test_lifecycle_identity_historical_archive_hash_mismatch_fails",
    "test_lifecycle_identity_historical_disposition_identity_mismatch_fails",
    "test_lifecycle_identity_multiple_active_authorization_ids_fail",
    "test_lifecycle_identity_cross_authorization_disposition_claims_active_fails",
    "test_lifecycle_identity_arbitrary_historical_artifact_fails",
    "test_lifecycle_identity_resolved_historical_plus_unknown_child_fails",
    "test_lifecycle_static_preflight_with_active_authorization_passes",
    "test_lifecycle_neutral_production_entry_reaches_authorization_semantics",
    "test_lifecycle_neutral_production_entry_unknown_authorization_fails_before_consumption",
    "test_lifecycle_stage_q_production_entry_reaches_neutral_semantics",
    "test_lifecycle_stage_q_production_entry_active_neutral_fails_before_semantics",
}

REQUIRED_STAGE_Q_090K_TESTS = {
    "test_stage_q_frozen_fit_json_array_positive_regression",
    "test_stage_q_frozen_fit_loader_fails_closed",
    "test_stage_q_consumed_attempt_archives_identity_wise_in_temp",
    "test_stage_q_consumed_archive_bytes_equal_original",
    "test_stage_q_archived_q1_plus_active_q2_passes",
    "test_stage_q_archived_q1_q2_reaches_consumption_boundary",
    "test_stage_q_archived_q1_q2_consumed_remain_independent",
    "test_stage_q_two_archived_generations_plus_active_q3_passes",
    "test_stage_q_archive_wrong_consumption_sha_fails",
    "test_stage_q_archive_path_digest_mismatch_fails",
    "test_stage_q_archive_consumption_claims_different_auth_fails",
    "test_stage_q_archive_status_attempt_id_mismatch_fails",
    "test_stage_q_archive_invalid_result_with_terminal_status_fails",
    "test_stage_q_archive_same_authorization_reuse_fails",
    "test_stage_q_active_q2_with_unresolved_q1_archive_fails",
    "test_stage_q_cross_generation_swap_fails",
    "test_stage_q_unknown_archive_child_fails",
    "test_stage_q_duplicate_historical_generation_identity_fails",
    "test_stage_q_second_consumption_does_not_overwrite_canonical",
    "test_stage_q_terminal_status_rejects_non_technical_invalid_outcome",
}



class ValidationError(RuntimeError):
    """Raised for a static implementation defect."""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json_no_duplicates(path: Path) -> dict:
    def hook(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValidationError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=hook)
    if not isinstance(value, dict):
        raise ValidationError(f"expected JSON object: {path}")
    return value


def load_runner_module():
    spec = importlib.util.spec_from_file_location("exp021_runner_under_validation", RUNNER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validator_write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _validator_neutral_authorization(root: Path, authorization_id: str) -> dict:
    return {
        "schema_version": "1.0.0",
        "experiment": "EXP-021",
        "scope": "NEUTRAL_HOOK_ORACLE_QUALIFICATION",
        "authorization_id": authorization_id,
        "issued_at": "2099-08-15T00:00:00+00:00",
        "expires_at": "2099-08-16T00:00:00+00:00",
        "runner_commit": "d" * 40,
        "runner_sha256": "a" * 64,
        "implementation_hashes": {"runner": "a" * 64, "validator": "b" * 64},
        "authority_hashes": {
            "original": "c" * 64,
            "amendment": "d" * 64,
            "reconciliation": "e" * 64,
        },
        "model_manifest": {"identity": "manifest-sha"},
        "environment_binding": {
            "device": "cuda:0",
            "dtype": "float16",
            "local_files_only": True,
            "model_eval_mode": True,
            "gradients_enabled": False,
            "use_cache": False,
        },
        "allowed_output_path": str(root / "engineering" / "neutral.json"),
        "maximum_launch_count": 1,
        "fit_access_permitted": False,
        "eval_access_permitted": False,
        "scientific_result_permitted": False,
        "automatic_retry_permitted": False,
    }


def _validator_active_authorization(root: Path, runner, authorization_id: str):
    auth = _validator_neutral_authorization(root, authorization_id)
    path = root / "experiments/exp021/authorization/neutral.json"
    _validator_write_json(path, auth)
    return path, auth, runner.sha256_file(path)


def _validator_completed_disposition(root: Path, runner, authorization_id: str):
    auth_path, auth, auth_hash = _validator_active_authorization(
        root, runner, authorization_id
    )
    runner.disposition_unconsumed_nonexecutable_authorization(
        repo_root=root,
        authorization_path=auth_path,
        expected_authorization_id=auth["authorization_id"],
        expected_authorization_sha256=auth_hash,
        expected_scope=runner.NEUTRAL_SCOPE,
        explicit_disposition_authorized=True,
        non_executable_reason="validator identity-aware lifecycle dynamic check",
    )
    return auth, auth_hash


def _validator_consumption_record(root: Path, runner, authorization: dict, authorization_hash: str):
    path = root / "experiments/exp021/consumed/neutral.json"
    _validator_write_json(
        path,
        {
            "schema_version": "1.0.0",
            "experiment": "EXP-021",
            "authorization_hash": authorization_hash,
            "attempt_id": "ATTEMPT-VALIDATOR-CONSUMED",
            "runner_commit": authorization["runner_commit"],
            "acquired_at": "2026-08-16T00:00:00+00:00",
            "scope": runner.NEUTRAL_SCOPE,
            "output_path": str(root / "experiments/exp021/engineering/neutral_result.json"),
            "state": "consumed",
        },
    )
    return path


def _validator_stage_q_authorization(root: Path, runner, authorization_id: str):
    auth = {
        "schema_version": "1.0.0",
        "experiment": "EXP-021",
        "scope": runner.STAGE_Q_SCOPE,
        "authorization_id": authorization_id,
        "issued_at": "2099-08-15T00:00:00+00:00",
        "expires_at": "2099-08-16T00:00:00+00:00",
        "runner_commit": "d" * 40,
        "runner_sha256": "a" * 64,
        "implementation_hashes": {"runner": "a" * 64, "validator": "b" * 64},
        "authority_hashes": {
            "original": "c" * 64,
            "amendment": "d" * 64,
            "reconciliation": "e" * 64,
        },
        "model_manifest": {"identity": "manifest-sha"},
        "environment_binding": {
            "device": "cuda:0",
            "dtype": "float16",
            "local_files_only": True,
            "model_eval_mode": True,
            "gradients_enabled": False,
            "use_cache": False,
        },
        "allowed_output_path": str(root / "experiments" / "exp021" / "engineering" / "stage_q_result.json"),
        "maximum_launch_count": 1,
        "fit_access_permitted": True,
        "eval_access_permitted": False,
        "scientific_result_permitted": False,
        "automatic_retry_permitted": False,
        "stage_p_intervention_permitted": False,
        "per_checkpoint_probe_refit_permitted": False,
    }
    path = root / "experiments" / "exp021" / "authorization" / "stage_q.json"
    _validator_write_json(path, auth)
    return path, auth, runner.sha256_file(path)


def _validator_stage_q_consumption(
    root: Path, runner, authorization: dict, authorization_hash: str, attempt_id: str
):
    path = root / "experiments" / "exp021" / "consumed" / "stage_q.json"
    _validator_write_json(
        path,
        {
            "schema_version": "1.0.0",
            "experiment": "EXP-021",
            "authorization_hash": authorization_hash,
            "attempt_id": attempt_id,
            "runner_commit": authorization["runner_commit"],
            "acquired_at": "2026-08-16T00:00:00+00:00",
            "scope": runner.STAGE_Q_SCOPE,
            "output_path": str(root / "experiments" / "exp021" / "engineering" / "stage_q_result.json"),
            "state": "consumed",
        },
    )
    return path


class ImportAndCallVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.function_depth = 0
        self.module_forbidden_imports: list[str] = []
        self.forbidden_imports: list[tuple[str, int, int]] = []
        self.module_calls: list[tuple[str, int]] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".", 1)[0]
            if root in FORBIDDEN_MODULE_IMPORTS:
                self.forbidden_imports.append((root, node.lineno, self.function_depth))
                if self.function_depth == 0:
                    self.module_forbidden_imports.append(root)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".", 1)[0]
        if root in FORBIDDEN_MODULE_IMPORTS:
            self.forbidden_imports.append((root, node.lineno, self.function_depth))
            if self.function_depth == 0:
                self.module_forbidden_imports.append(root)

    def visit_Call(self, node: ast.Call) -> None:
        if self.function_depth == 0:
            self.module_calls.append((ast.unparse(node.func), node.lineno))
        self.generic_visit(node)


def function_node(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return node
    raise ValidationError(f"missing required function: {name}")


def called_before(function: ast.FunctionDef, first: str, second: str) -> bool:
    calls: dict[str, int] = {}
    for node in ast.walk(function):
        if isinstance(node, ast.Call):
            name = ast.unparse(node.func)
            if name in {first, second}:
                calls.setdefault(name, node.lineno)
    return first in calls and second in calls and calls[first] < calls[second]


def call_names(function: ast.FunctionDef) -> set[str]:
    """Return direct and attribute call names in a function body."""
    return {ast.unparse(node.func) for node in ast.walk(function) if isinstance(node, ast.Call)}


def calls_any_function_containing(function: ast.FunctionDef, needle: str) -> bool:
    """Return whether any call in a function's AST mentions ``needle``."""
    return any(
        needle in ast.unparse(node.func)
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
    )


def require_calls(function: ast.FunctionDef, required: set[str], label: str) -> None:
    calls = call_names(function)
    missing = sorted(required - calls)
    if missing:
        raise ValidationError(f"{label} is missing production calls: {missing}")


def guarded_call(function: ast.FunctionDef, call_name: str, guard_name: str) -> bool:
    """Require a call to occur syntactically inside an if guard."""
    for node in ast.walk(function):
        if not isinstance(node, ast.If) or guard_name not in ast.unparse(node.test):
            continue
        if any(isinstance(child, ast.Call) and ast.unparse(child.func) == call_name for child in ast.walk(node)):
            return True
    return False


def validate() -> None:
    if not RUNNER.is_file():
        raise ValidationError("runner is missing")
    if sha256(ORIGINAL) != EXPECTED_ORIGINAL_SHA256:
        raise ValidationError("original preregistration hash changed")
    if sha256(AMENDMENT) != EXPECTED_AMENDMENT_SHA256:
        raise ValidationError("amendment hash changed")
    authority = read_json_no_duplicates(AUTHORITY)
    if authority.get("original_preregistration_sha256") != EXPECTED_ORIGINAL_SHA256:
        raise ValidationError("authority original hash mismatch")
    if authority.get("overall_status") != "EXP021_AMENDMENT_READY_FOR_TARGETED_FINAL_REREVIEW":
        raise ValidationError("authority readiness status mismatch")
    if authority.get("stage_q_authorizable") is not False or authority.get("stage_p_authorizable") is not False:
        raise ValidationError("authorization boundary is open")
    if authority.get("hook_oracle_runtime_qualification_status") != "NOT_RUN":
        raise ValidationError("neutral qualification must remain unrun")
    if authority.get("hook_oracle_runtime_qualified") is not False:
        raise ValidationError("neutral runtime qualification status mismatch")
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"), filename=str(RUNNER))
    visitor = ImportAndCallVisitor()
    visitor.visit(tree)
    if visitor.module_forbidden_imports:
        raise ValidationError(f"forbidden module-level imports: {visitor.module_forbidden_imports}")
    if any(depth == 0 for _, _, depth in visitor.forbidden_imports):
        raise ValidationError("runtime library imported at module scope")
    # The only module-scope call is the guarded CLI entry point.
    # These constructors only define immutable protocol constants; they do
    # not perform filesystem, network, model, or dataset work at import time.
    safe_constant_calls = {"main", "SystemExit", "Path", "tuple", "frozenset"}
    unguarded_calls = [item for item in visitor.module_calls if item[0] not in safe_constant_calls]
    if unguarded_calls:
        raise ValidationError(f"module-level calls imply import-time work: {unguarded_calls}")
    source = RUNNER.read_text(encoding="utf-8")
    constant_names = {
        node.targets[0].id
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    }
    if "AUTHORITY_ARCHIVE_COMMIT" not in constant_names:
        raise ValidationError("authority archive identity is missing")
    if "CHECKPOINT_MAPPING_METADATA_KEYS" not in constant_names:
        raise ValidationError("checkpoint mapping metadata schema is missing")
    if "TUPLE_SEMANTICS_FROZEN_TEXT" not in constant_names:
        raise ValidationError("frozen tuple semantics constant is missing")
    if "ARCHIVE_COMMIT" in constant_names:
        raise ValidationError("legacy runtime HEAD constant is still present")
    lifecycle_constants = {
        "LIFECYCLE_MODE_STATIC",
        "LIFECYCLE_MODE_NEUTRAL",
        "LIFECYCLE_MODE_STAGE_Q",
        "LIFECYCLE_ACTIVE_AUTHORIZATION_PATHS",
        "LIFECYCLE_CONSUMPTION_PATHS",
        "LIFECYCLE_ENGINEERING_RESULT_PATHS",
        "LIFECYCLE_KNOWN_DIRECTORIES",
        "LIFECYCLE_SCAN_DIRECTORIES",
        "LIFECYCLE_LEGACY_CONTAMINATION_PATHS",
        "STAGE_Q_CONSUMPTION_ARCHIVE_RELATIVE_DIR",
        "STAGE_Q_CONSUMPTION_ARCHIVE_JOURNAL_RELATIVE_DIR",
        "STAGE_Q_CONSUMPTION_ARCHIVE_STATUS_RELATIVE_DIR",
        "STAGE_Q_AUTHORIZATION_ARCHIVE_RELATIVE_DIR",
    }
    missing_lifecycle_constants = sorted(lifecycle_constants - constant_names)
    if missing_lifecycle_constants:
        raise ValidationError(f"mode-specific lifecycle constants are missing: {missing_lifecycle_constants}")
    authority_files = function_node(tree, "validate_authority_files")
    authority_files_source = ast.unparse(authority_files)
    if "rev-parse" in authority_files_source:
        raise ValidationError("authority archive commit still constrains live HEAD")
    for legacy_path_token in (
        "experiments/exp021/authorization",
        "experiments/exp021/results",
        "experiments/exp021/neutral_qualification_result.json",
        "experiments/exp021/stage_q_result.json",
    ):
        if legacy_path_token in authority_files_source:
            raise ValidationError(f"stale global mutable-path denylist remains in validate_authority_files: {legacy_path_token}")
    for lifecycle_function in (
        "inspect_lifecycle_paths",
        "validate_lifecycle_state",
        "validate_mode_lifecycle",
    ):
        function_node(tree, lifecycle_function)
    for identity_function in (
        "_group_disposition_artifacts",
        "_validate_completed_historical_disposition",
        "_reject_active_identity_disposition_state",
        "_group_stage_q_archive_artifacts",
        "_validate_completed_stage_q_archive",
        "_validate_stage_q_archive_identity_state",
        "validate_stage_q_archive_journal",
        "validate_stage_q_terminal_attempt_status",
        "archive_consumed_stage_q_technically_invalid_attempt",
    ):
        function_node(tree, identity_function)
    mode_validator = function_node(tree, "validate_mode_lifecycle")
    mode_validator_source = ast.unparse(mode_validator)
    if "inspect_lifecycle_paths" not in mode_validator_source or "validate_lifecycle_state" not in mode_validator_source:
        raise ValidationError("mode-specific lifecycle validation is incomplete")
    impossible_state_validator = function_node(tree, "_validate_no_impossible_lifecycle_state")
    impossible_state_source = ast.unparse(impossible_state_validator)
    for identity_token in (
        "_group_disposition_artifacts",
        "_validate_completed_historical_disposition",
        "_validate_stage_q_archive_identity_state",
        "active_hashes",
        "authorization_id",
    ):
        if identity_token not in impossible_state_source:
            raise ValidationError("impossible lifecycle validation is not authorization-identity-aware")
    for mode_state_function in (
        "_validate_neutral_lifecycle_state",
        "_validate_stage_q_lifecycle_state",
    ):
        if "_reject_active_identity_disposition_state" not in call_names(
            function_node(tree, mode_state_function)
        ):
            raise ValidationError(
                f"{mode_state_function} does not apply identity-aware disposition rejection"
            )
    for mode in ("--static-preflight", "--neutral-hook-qualification", "--stage-q"):
        if mode not in source:
            raise ValidationError(f"missing CLI mode: {mode}")
    if "--stage-p" in source or "def run_stage_p" in source:
        raise ValidationError("Stage-P execution was added")
    if "prompt" in source.lower() and "read_text" in source.lower():
        raise ValidationError("runner appears to read prompt text")
    if "torch.equal(actual_hook_output, expected)" not in source:
        raise ValidationError("exact active-hook oracle is missing")
    if "beta.ppf" not in source:
        raise ValidationError("Clopper–Pearson convention is missing")
    if "ENGINEERING_MEASUREMENT_QUALIFICATION_ONLY" not in source and "ENGINEERING_NEUTRAL_HOOK_QUALIFICATION_ONLY" not in source:
        raise ValidationError("engineering-only result classification is missing")
    neutral = function_node(tree, "run_neutral_hook_qualification")
    stage_q = function_node(tree, "run_stage_q")
    require_calls(
        neutral,
        {
            "validate_authority_files", "validate_mode_lifecycle", "build_static_execution_binding",
            "consume_authorization", "validate_model_manifest", "_load_model_and_tokenizer",
            "_forward_with_capture", "construct_expected_hook_output", "validate_active_hook_output",
            "validate_neutral_result", "atomic_publish_json",
        },
        "neutral path",
    )
    require_calls(
        stage_q,
        {
            "validate_authority_files", "validate_mode_lifecycle", "validate_neutral_result",
            "build_historical_neutral_binding", "consume_authorization", "validate_model_manifest",
            "_load_model_and_tokenizer", "load_fit_source_records", "extract_fit_representations",
            "leave_one_out_fixed_probe", "stage_q_global_gate", "validate_stage_q_result",
            "atomic_publish_json",
        },
        "Stage-Q path",
    )
    if not called_before(neutral, "validate_mode_lifecycle", "consume_authorization"):
        raise ValidationError("neutral lifecycle validation is not before authorization consumption")
    if not called_before(neutral, "consume_authorization", "_load_model_and_tokenizer"):
        raise ValidationError("neutral authorization is not consumed before model load")
    if not called_before(neutral, "validate_neutral_result", "atomic_publish_json"):
        raise ValidationError("neutral result is not validated before publication")
    if not called_before(stage_q, "validate_mode_lifecycle", "validate_neutral_result"):
        raise ValidationError("Stage-Q lifecycle validation is not before neutral-result validation")
    if not called_before(stage_q, "validate_mode_lifecycle", "consume_authorization"):
        raise ValidationError("Stage-Q lifecycle validation is not before authorization consumption")
    if not called_before(stage_q, "build_historical_neutral_binding", "validate_neutral_result"):
        raise ValidationError("historical neutral-result binding is not built before result validation")
    if not called_before(stage_q, "validate_neutral_result", "consume_authorization"):
        raise ValidationError("Stage-Q neutral drift is not checked before authorization consumption")
    if not called_before(stage_q, "consume_authorization", "_load_model_and_tokenizer"):
        raise ValidationError("Stage-Q authorization is not consumed before model load")
    if not called_before(stage_q, "consume_authorization", "load_fit_source_records"):
        raise ValidationError("Stage-Q authorization is not consumed before FIT source access")
    if not called_before(neutral, "validate_model_manifest", "_load_model_and_tokenizer"):
        raise ValidationError("neutral full model verification is not before model load")
    if not called_before(stage_q, "validate_model_manifest", "_load_model_and_tokenizer"):
        raise ValidationError("Stage-Q full model verification is not before model load")
    consume = function_node(tree, "consume_authorization")
    require_calls(consume, {"validate_authorization", "confined_path"}, "authorization consumption")
    adapter = function_node(tree, "load_fit_source_records")
    require_calls(adapter, {"validate_fit_eval_routing"}, "FIT source adapter")
    adapter_source = ast.unparse(adapter)
    if "read_json_value_no_duplicates" not in adapter_source:
        raise ValidationError("FIT source loader does not parse the frozen JSON document")
    if "isinstance(document, list)" not in adapter_source:
        raise ValidationError("FIT source loader does not fail closed on a non-array document")
    if "for line in" in adapter_source:
        raise ValidationError("FIT source loader still assumes JSONL")
    if not called_before(stage_q, "validate_stage_q_result", "atomic_publish_json"):
        raise ValidationError("Stage-Q result is not validated before publication")
    historical_binding = function_node(tree, "build_historical_neutral_binding")
    historical_binding_source = ast.unparse(historical_binding)
    for token in (
        "EXPECTED_NEUTRAL_RESULT_SHA256",
        "EXPECTED_NEUTRAL_PRODUCER_COMMIT",
        "EXPECTED_NEUTRAL_PRODUCER_RUNNER_SHA256",
        "EXPECTED_NEUTRAL_PRODUCER_VALIDATOR_SHA256",
        "_git_blob_sha256",
        "sha256_file",
    ):
        if token not in historical_binding_source:
            raise ValidationError(f"historical neutral-result provenance binding is missing {token}")
    function_node(tree, "_git_blob_sha256")
    neutral_validator = function_node(tree, "validate_neutral_result")
    require_calls(
        neutral_validator,
        {
            "_validate_neutral_execution_environment",
            "_validate_neutral_diagnostic_vector",
            "_validate_neutral_input_identity",
        },
        "neutral drift validator",
    )
    runtime_identity_constructor = function_node(tree, "runtime_identity_binding")
    require_calls(
        runtime_identity_constructor,
        {"_nvidia_runtime_identity"},
        "dynamic runtime identity constructor",
    )
    execution_binding = function_node(tree, "build_static_execution_binding")
    require_calls(
        execution_binding,
        {"runtime_identity_binding"},
        "execution binding",
    )
    if "rev-parse" not in ast.unparse(execution_binding):
        raise ValidationError("live execution commit is not established")
    disposition = function_node(tree, "disposition_unconsumed_nonexecutable_authorization")
    require_calls(
        disposition,
        {
            "_publish_disposition_journal",
            "_archive_disposition_authorization",
            "_publish_disposition_record",
            "inspect_disposition_transaction",
        },
        "disposition lifecycle",
    )
    if not called_before(disposition, "_publish_disposition_journal", "_archive_disposition_authorization"):
        raise ValidationError("disposition journal is not published before archive move")
    if not called_before(disposition, "_archive_disposition_authorization", "_publish_disposition_record"):
        raise ValidationError("disposition archive move is not before final publication")
    archive_fn = function_node(tree, "_archive_disposition_authorization")
    if "os.replace" not in ast.unparse(archive_fn) or "sha256_file" not in call_names(archive_fn):
        raise ValidationError("disposition does not archive original bytes fail-closed")
    for name in (
        "validate_disposition_journal",
        "inspect_disposition_transaction",
        "recover_disposition_transaction",
        "is_replacement_authorization_blocked",
        "_read_archived_authorization_for_recovery",
        "_disposition_transaction_ids",
    ):
        function_node(tree, name)
    journal_validator = function_node(tree, "validate_disposition_journal")
    if "journal_sha256" not in ast.unparse(journal_validator):
        raise ValidationError("disposition journal validator is incomplete")
    journal_binding = function_node(tree, "_load_matching_journal")
    journal_binding_source = ast.unparse(journal_binding)
    for token in (
        "authorization_runner_commit",
        "authorization_runner_sha256",
        "transaction_id",
        "disposition_record_id",
    ):
        if token not in journal_binding_source:
            raise ValidationError(f"disposition journal binding is missing {token}")
    disposition_validator = function_node(tree, "validate_disposition_record")
    if "original_can_never_be_consumed" not in ast.unparse(disposition_validator):
        raise ValidationError("disposition validator is incomplete")
    if "DISPOSITION_STATE_DISPOSITIONED" not in ast.unparse(disposition_validator):
        raise ValidationError("completed disposition state is not verified")
    recovery = function_node(tree, "recover_disposition_transaction")
    require_calls(
        recovery,
        {
            "_read_active_authorization_for_disposition",
            "_read_archived_authorization_for_recovery",
            "_disposition_transaction_ids",
            "_load_matching_journal",
            "_build_disposition_record",
            "_publish_disposition_record",
            "inspect_disposition_transaction",
        },
        "disposition recovery",
    )
    inspection = function_node(tree, "inspect_disposition_transaction")
    require_calls(
        inspection,
        {
            "_read_active_authorization_for_disposition",
            "_read_archived_authorization_for_recovery",
            "_disposition_transaction_ids",
            "_load_matching_journal",
        },
        "disposition inspection",
    )
    if "replacement_blocked" not in ast.unparse(inspection):
        raise ValidationError("disposition inspection does not define replacement blocking")
    if "DISPOSITION_STATE_PARTIAL_OR_RECOVERY_REQUIRED" not in ast.unparse(inspection):
        raise ValidationError("disposition inspection does not detect recovery-required state")
    environment_validator = function_node(tree, "_validate_neutral_execution_environment")
    if "runtime_identity" not in ast.unparse(environment_validator):
        raise ValidationError("neutral environment validation does not use dynamic runtime identity binding")
    if not TESTS.is_file():
        raise ValidationError("Stage-Q production-entry regression tests are missing")
    tests_tree = ast.parse(TESTS.read_text(encoding="utf-8"), filename=str(TESTS))
    for name in (
        REQUIRED_COMMIT_BINDING_TESTS
        | REQUIRED_DISPOSITION_TESTS
        | REQUIRED_HISTORICAL_PROVENANCE_TESTS
        | REQUIRED_CHECKPOINT_MAPPING_TESTS
        | REQUIRED_LIFECYCLE_TESTS
        | REQUIRED_STAGE_Q_090K_TESTS
    ):
        function_node(tests_tree, name)
    neutral_dynamic_test = function_node(tests_tree, NEUTRAL_DYNAMIC_TEST)
    stage_q_dynamic_test = function_node(tests_tree, STAGE_Q_DYNAMIC_TEST)
    if not calls_any_function_containing(neutral_dynamic_test, "run_neutral_hook_qualification"):
        raise ValidationError("neutral production-entry regression test does not invoke the real entry")
    if not calls_any_function_containing(stage_q_dynamic_test, "run_stage_q"):
        raise ValidationError("Stage-Q production-entry regression test does not invoke the real entry")
    manifest = function_node(tree, "validate_model_manifest")
    if not guarded_call(manifest, "sha256_file", "verify_payload") or not guarded_call(manifest, "_validate_safetensors_header", "verify_payload"):
        raise ValidationError("full model verification is not guarded by post-consumption verify_payload")
    static = function_node(tree, "run_static_preflight")
    if "validate_mode_lifecycle" not in call_names(static):
        raise ValidationError("static preflight does not perform mode-specific lifecycle validation")
    if "sha256_file" in call_names(static) or "_validate_safetensors_header" in call_names(static):
        raise ValidationError("static preflight directly reads model payloads")
    with tempfile.TemporaryDirectory() as tmpdir:
        lifecycle_root = Path(tmpdir)
        active_path = lifecycle_root / "experiments/exp021/authorization/neutral.json"
        active_path.parent.mkdir(parents=True)
        active_path.write_text("{}", encoding="utf-8")
        try:
            lifecycle_state = load_runner_module().validate_mode_lifecycle(lifecycle_root, "static")
        except Exception as exc:
            raise ValidationError(f"static lifecycle validation does not recognize active neutral authorization: {exc}")
        if lifecycle_state.get("active_neutral") is None:
            raise ValidationError("static lifecycle inspection does not classify active neutral authorization")
        unknown_path = lifecycle_root / "experiments/exp021/authorization/unknown.json"
        unknown_path.write_text("{}", encoding="utf-8")
        try:
            load_runner_module().validate_mode_lifecycle(lifecycle_root, "static")
        except Exception:
            pass
        else:
            raise ValidationError("closed-world lifecycle validation accepts an unknown authorization artifact")
    with tempfile.TemporaryDirectory() as tmpdir:
        consumed_root = Path(tmpdir)
        consumed_runner = load_runner_module()
        _auth_path, consumed_auth, consumed_hash = _validator_active_authorization(
            consumed_root, consumed_runner, "AUTH-DYN-CONSUMED"
        )
        _validator_consumption_record(
            consumed_root, consumed_runner, consumed_auth, consumed_hash
        )
        consumed_state = consumed_runner.validate_mode_lifecycle(
            consumed_root, consumed_runner.LIFECYCLE_MODE_STATIC
        )
        if consumed_state.get("active_neutral") is not None:
            raise ValidationError("matching consumption did not deactivate the retained neutral authorization")
        if consumed_state.get("consumed_neutral") is None:
            raise ValidationError("matching consumption was not classified as consumed neutral evidence")
        if consumed_state.get("retained_authorizations", {}).get("neutral") is None:
            raise ValidationError("retained consumed authorization was not preserved as audit evidence")
        wrong_consumption = _validator_consumption_record(
            consumed_root, consumed_runner, consumed_auth, "f" * 64
        )
        try:
            consumed_runner.validate_mode_lifecycle(
                consumed_root, consumed_runner.LIFECYCLE_MODE_STATIC
            )
        except Exception:
            pass
        else:
            raise ValidationError("mismatched consumption identity did not fail closed")
    with tempfile.TemporaryDirectory() as tmpdir:
        identity_root = Path(tmpdir)
        identity_runner = load_runner_module()
        historical_auth, historical_hash = _validator_completed_disposition(
            identity_root, identity_runner, "AUTH-DYN-A"
        )
        active_path, active_auth, active_hash = _validator_active_authorization(
            identity_root, identity_runner, "AUTH-DYN-B"
        )
        if historical_hash == active_hash:
            raise ValidationError("identity-aware dynamic fixtures do not have distinct hashes")
        try:
            static_state = identity_runner.validate_mode_lifecycle(
                identity_root, identity_runner.LIFECYCLE_MODE_STATIC
            )
            neutral_state = identity_runner.validate_mode_lifecycle(
                identity_root, identity_runner.LIFECYCLE_MODE_NEUTRAL
            )
        except Exception as exc:
            raise ValidationError(
                f"identity-aware lifecycle does not accept completed historical disposition plus distinct active authorization: {exc}"
            )
        if static_state.get("active_neutral") is None:
            raise ValidationError("identity-aware static lifecycle did not classify the active replacement")
        if len(static_state.get("disposition_records", [])) != 1:
            raise ValidationError("identity-aware static lifecycle did not retain the completed historical disposition")
        if neutral_state.get("active_neutral") is None:
            raise ValidationError("identity-aware neutral lifecycle did not classify the active replacement")
        unresolved_journal = (
            identity_root
            / "experiments/exp021/authorization/disposition_journal"
            / f"{'a' * 64}.json"
        )
        _validator_write_json(unresolved_journal, {})
        try:
            identity_runner.validate_mode_lifecycle(
                identity_root, identity_runner.LIFECYCLE_MODE_STATIC
            )
        except Exception:
            pass
        else:
            raise ValidationError("unresolved historical disposition does not block a distinct active replacement")
    dynamic_runner = load_runner_module()
    frozen_prompt = ROOT / "experiments/exp003/prompts_controlled.json"
    if dynamic_runner.sha256_file(frozen_prompt) != "72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472":
        raise ValidationError("frozen FIT artifact hash changed before JSON-array dynamic proof")
    frozen_records = dynamic_runner.load_fit_source_records(
        ROOT, "A_original_fit_paraphrase_eval"
    )
    if len(frozen_records) != 12 or frozen_records[0]["item_id"] != "logic_orig_01":
        raise ValidationError("frozen FIT JSON array did not parse into the expected Stage-Q FIT records")
    with tempfile.TemporaryDirectory() as tmpdir:
        archive_root = Path(tmpdir)
        archive_runner = load_runner_module()
        q1_path, q1_auth, q1_hash = _validator_stage_q_authorization(
            archive_root, archive_runner, "AUTH-DYN-SQ-Q1"
        )
        q1_consumption_path = _validator_stage_q_consumption(
            archive_root,
            archive_runner,
            q1_auth,
            q1_hash,
            "ATTEMPT-DYN-SQ-Q1",
        )
        q1_consumption_hash = archive_runner.sha256_file(q1_consumption_path)
        status = archive_runner.archive_consumed_stage_q_technically_invalid_attempt(
            repo_root=archive_root,
            authorization_path=q1_path,
            consumption_path=q1_consumption_path,
            expected_authorization_id=q1_auth["authorization_id"],
            expected_authorization_sha256=q1_hash,
            expected_consumption_sha256=q1_consumption_hash,
            expected_attempt_id="ATTEMPT-DYN-SQ-Q1",
            explicit_archival_authorized=True,
        )
        if status["attempt_outcome"] != "TECHNICALLY_INVALID":
            raise ValidationError("consumed Stage-Q archive did not preserve technical-invalidity classification")
        if status["measurement_status"] != "NOT_OBSERVED_DUE_TO_TECHNICAL_INVALIDITY":
            raise ValidationError("consumed Stage-Q archive did not preserve no-observation status")
        archived_state = archive_runner.validate_mode_lifecycle(
            archive_root, archive_runner.LIFECYCLE_MODE_STATIC
        )
        if archived_state.get("active_stage_q") is not None:
            raise ValidationError("archived consumed Stage-Q authorization was misclassified as active")
        if len(archived_state.get("stage_q_consumption_archives", [])) != 1:
            raise ValidationError("consumed Stage-Q archive was not recognized as historical evidence")
        _validator_write_json(
            archive_root / "experiments" / "exp021" / "authorization" / "stage_q.json",
            q1_auth,
        )
        q1_reuse_consumption_path = _validator_stage_q_consumption(
            archive_root,
            archive_runner,
            q1_auth,
            q1_hash,
            "ATTEMPT-DYN-SQ-Q1-REUSE",
        )
        if archive_runner.sha256_file(q1_reuse_consumption_path) == q1_hash:
            raise ValidationError("archived-vs-canonical dynamic fixture lacks the file-hash collision identity")
        try:
            archive_runner.validate_mode_lifecycle(
                archive_root, archive_runner.LIFECYCLE_MODE_STATIC
            )
        except Exception:
            pass
        else:
            raise ValidationError("archived consumed Stage-Q authorization coexisted with a canonical same-generation consumption")
        (archive_root / "experiments" / "exp021" / "authorization" / "stage_q.json").unlink()
        q1_reuse_consumption_path.unlink()
        _validator_write_json(
            archive_root / "experiments" / "exp021" / "authorization" / "stage_q.json",
            q1_auth,
        )
        try:
            archive_runner.validate_mode_lifecycle(
                archive_root, archive_runner.LIFECYCLE_MODE_STATIC
            )
        except Exception:
            pass
        else:
            raise ValidationError("archived consumed Stage-Q authorization was reactivated")
        (archive_root / "experiments" / "exp021" / "authorization" / "stage_q.json").unlink()
        _q2_path, _q2_auth, q2_hash = _validator_stage_q_authorization(
            archive_root, archive_runner, "AUTH-DYN-SQ-Q2"
        )
        if q1_hash == q2_hash:
            raise ValidationError("Stage-Q archive dynamic fixtures do not have distinct identities")
        try:
            multi_state = archive_runner.validate_mode_lifecycle(
                archive_root, archive_runner.LIFECYCLE_MODE_STATIC
            )
        except Exception as exc:
            raise ValidationError(
                f"consumed Stage-Q archive does not coexist with a fresh authorization: {exc}"
            )
        if multi_state.get("active_stage_q") is None:
            raise ValidationError("fresh Stage-Q authorization was not classified as active after archival")
        if len(multi_state.get("stage_q_authorization_archives", [])) != 1:
            raise ValidationError("historical consumed Stage-Q authorization archive is missing after coexistence")
        q2_consumption_path = _validator_stage_q_consumption(
            archive_root,
            archive_runner,
            _q2_auth,
            q2_hash,
            "ATTEMPT-DYN-SQ-Q2",
        )
        try:
            q2_consumed_state = archive_runner.validate_mode_lifecycle(
                archive_root, archive_runner.LIFECYCLE_MODE_STATIC
            )
        except Exception as exc:
            raise ValidationError(
                f"distinct-generation canonical Stage-Q consumption is not representable after archival: {exc}"
            )
        if q2_consumed_state.get("active_stage_q") is not None:
            raise ValidationError("distinct-generation canonical Stage-Q consumption was misclassified as active")
        if q2_consumed_state.get("consumed_stage_q") is None:
            raise ValidationError("distinct-generation canonical Stage-Q consumption was not classified as consumed")
    with tempfile.TemporaryDirectory() as tmpdir:
        provenance_runner = load_runner_module()
        neutral_result_path = ROOT / "experiments/exp021/engineering/neutral_result.json"
        if not neutral_result_path.is_file():
            raise ValidationError("real neutral qualification result is missing for provenance proof")
        result = provenance_runner.read_json_no_duplicates(neutral_result_path)
        historical_binding = provenance_runner.build_historical_neutral_binding(
            ROOT,
            neutral_result_path,
            result,
        )
        if historical_binding.get("runner_commit") != "6d828cafc5c22926cdfce5060118b1dcaf15aeb4":
            raise ValidationError("historical neutral producer commit is not independently identified")
        current_commit = provenance_runner._git_output(ROOT, "rev-parse", "HEAD")
        if historical_binding.get("runner_commit") == current_commit:
            raise ValidationError("historical producer and current executor identities are not separated")
        try:
            provenance_runner.validate_neutral_result(result, authority, historical_binding)
        except Exception as exc:
            raise ValidationError(
                f"historically valid neutral result does not validate against producer identity: {exc}"
            )
        current_binding = {
            "runner_commit": current_commit,
            "runner_sha256": provenance_runner.implementation_hashes(ROOT)["runner"],
            "implementation_hashes": provenance_runner.implementation_hashes(ROOT),
            "authority_hashes": provenance_runner.authority_hashes(ROOT),
            "model_manifest": provenance_runner.model_manifest_binding(
                authority["primary_model_identity"]
            ),
            "environment_binding": provenance_runner.required_environment_binding(),
            "runtime_identity": {
                key: result["execution_environment"][key]
                for key in provenance_runner.RUNTIME_IDENTITY_KEYS
            },
        }
        try:
            provenance_runner.validate_neutral_result(result, authority, current_binding)
        except Exception:
            pass
        else:
            raise ValidationError("current-executor drift no longer fails closed for historical neutral result")
        tampered = dict(result)
        tampered["runner_commit"] = "0" * 40
        try:
            provenance_runner.build_historical_neutral_binding(
                ROOT,
                neutral_result_path,
                tampered,
            )
        except Exception:
            pass
        else:
            raise ValidationError("tampered historical producer commit is accepted")

    mapping_validator = function_node(tree, "validate_checkpoint_mapping")
    mapping_validator_source = ast.unparse(mapping_validator)
    if "tuple_semantics" not in mapping_validator_source or "TUPLE_SEMANTICS_FROZEN_TEXT" not in mapping_validator_source:
        raise ValidationError("checkpoint mapping validator does not explicitly recognize tuple_semantics")
    if "CHECKPOINT_MAPPING_METADATA_KEYS" not in mapping_validator_source:
        raise ValidationError("checkpoint mapping validator does not enforce exact metadata schema")
    checkpoint_mapping = authority.get("checkpoint_mapping")
    if not isinstance(checkpoint_mapping, dict):
        raise ValidationError("frozen authority checkpoint mapping is missing or invalid")
    try:
        load_runner_module().validate_checkpoint_mapping(checkpoint_mapping)
    except Exception as exc:
        raise ValidationError(f"static preflight cannot validate frozen checkpoint mapping: {exc}")
    if "neutral_result_path" not in ast.unparse(stage_q):
        raise ValidationError("Stage-Q neutral qualification dependency is missing")
    if "results" in source and "scientific" not in source:
        raise ValidationError("result-path separation is unclear")
    for name, value in {
        "INTERVENTION_BLOCK": 16,
        "INTERVENTION_HIDDEN_STATE_INDEX": 17,
        "BETA": 0.75,
    }.items():
        assignments = [node for node in tree.body if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)]
        if not assignments or ast.literal_eval(assignments[0].value) != value:
            raise ValidationError(f"frozen constant mismatch: {name}")


def main() -> int:
    try:
        validate()
    except (OSError, UnicodeError, SyntaxError, ValidationError) as exc:
        print(f"EXP021_STAGE_Q_IMPLEMENTATION_VALIDATION_FAIL: {exc}")
        return 1
    print("EXP021_STAGE_Q_IMPLEMENTATION_VALIDATION_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
