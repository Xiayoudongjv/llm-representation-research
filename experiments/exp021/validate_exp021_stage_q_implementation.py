"""Metadata, AST, and production-entry-contract validator for EXP-021 Stage-Q."""

from __future__ import annotations

import ast
import hashlib
import json
import re
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
            "validate_authority_files", "build_static_execution_binding", "consume_authorization",
            "validate_model_manifest", "_load_model_and_tokenizer", "_forward_with_capture",
            "construct_expected_hook_output", "validate_active_hook_output",
            "validate_neutral_result", "atomic_publish_json",
        },
        "neutral path",
    )
    require_calls(
        stage_q,
        {
            "validate_authority_files", "validate_neutral_result", "consume_authorization",
            "validate_model_manifest", "_load_model_and_tokenizer", "load_fit_source_records",
            "extract_fit_representations", "leave_one_out_fixed_probe", "stage_q_global_gate",
            "validate_stage_q_result", "atomic_publish_json",
        },
        "Stage-Q path",
    )
    if not called_before(neutral, "consume_authorization", "_load_model_and_tokenizer"):
        raise ValidationError("neutral authorization is not consumed before model load")
    if not called_before(neutral, "validate_neutral_result", "atomic_publish_json"):
        raise ValidationError("neutral result is not validated before publication")
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
    if not called_before(stage_q, "validate_stage_q_result", "atomic_publish_json"):
        raise ValidationError("Stage-Q result is not validated before publication")
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
    environment_validator = function_node(tree, "_validate_neutral_execution_environment")
    if "runtime_identity" not in ast.unparse(environment_validator):
        raise ValidationError("neutral environment validation does not use dynamic runtime identity binding")
    if not TESTS.is_file():
        raise ValidationError("Stage-Q production-entry regression tests are missing")
    tests_tree = ast.parse(TESTS.read_text(encoding="utf-8"), filename=str(TESTS))
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
    if "sha256_file" in call_names(static) or "_validate_safetensors_header" in call_names(static):
        raise ValidationError("static preflight directly reads model payloads")
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
