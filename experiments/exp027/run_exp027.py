"""EXP-027 third-model formal pipeline.

This runner is a production engineering surface for the frozen EXP-027 design.
It has strictly separated modes and never runs formal science without a valid,
unconsumed single-use authorization. Importing this module does not load a model
or access formal FIT/DIAG/EVAL content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
ENGINEERING_DIR = EXP_DIR / "engineering"
FROZEN_DESIGN_PATH = EXP_DIR / "exp027_frozen_design.json"
PREREG_PATH = ROOT / "docs" / "experiments" / "EXP-027-PREREGISTRATION.md"
RESULT_PATH = EXP_DIR / "results" / "exp027_results.json"
AUTHORIZATION_PATH = EXP_DIR / "exp027_formal_run_authorization.json"
CONSUMPTION_DIR = EXP_DIR / "results" / "authorization_consumption"
FORMAL_ATTEMPT_PATH = EXP_DIR / "results" / "exp027_formal_attempt.json"
QUALIFICATION_PATH = ENGINEERING_DIR / "exp027_formal_pipeline_qualification.json"
NEUTRAL_EVIDENCE_PATH = ENGINEERING_DIR / "llama32_model_authority_qualification.json"
PROVENANCE_PATH = ENGINEERING_DIR / "llama32_native_converted_provenance.json"
BOOTSTRAP_SEED = 20260819
BOOTSTRAP_REPLICATES = 5000

_STATIC_FLAG = "--static-preflight"
_SYNTHETIC_FLAG = "--synthetic-preflight"
_NEUTRAL_FLAG = "--neutral-model-preflight"
_FORMAL_FLAG = "--formal-run"
_REPO_ROOT_FLAG = "--repo-root"
_AUTHORIZATION_FILE_FLAG = "--authorization-file"

for path in (str(EXP_DIR), str(ENGINEERING_DIR), str(ROOT / "experiments" / "exp026")):
    if path not in sys.path:
        sys.path.insert(0, path)

import validate_exp027_preregistration as design_validator
import validate_exp027_result as result_validator
import exp027_bootstrap_optimized_prototype as bootstrap_proto
import exp027_progress as progress
import run_exp026 as ref


class Exp027ProtocolIntegrityError(RuntimeError):
    """Raised when an EXP-027 frozen authority or execution invariant fails."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_string(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    return value


def _atomic_write_json(path: Path, payload: Any) -> str:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return sha256_file(path)


def _atomic_write_json_exclusive(path: Path, payload: Any) -> str:
    path = Path(path)
    if path.exists():
        raise Exp027ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")
    return _atomic_write_json(path, payload)


def _repository_commit(root: Path = ROOT) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()


def _load_frozen_design(root: Path = ROOT) -> dict[str, Any]:
    if design_validator.validate_immutable_content():
        raise Exp027ProtocolIntegrityError("EXP027_IMMUTABLE_AUTHORITIES_INVALID")
    return read_json(root / FROZEN_DESIGN_PATH)


def verify_exp027_authorities(root: Path = ROOT) -> dict[str, Any]:
    design = _load_frozen_design(root)
    prereg = root / PREREG_PATH
    if not prereg.is_file():
        raise Exp027ProtocolIntegrityError("EXP027_PREREGISTRATION_MISSING")
    return {
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "frozen_design_sha256": sha256_file(root / FROZEN_DESIGN_PATH),
        "preregistration_sha256": sha256_file(prereg),
        "model_identity": {
            "model_id": design["third_model_identity"]["model_id"],
            "model_source": design["third_model_identity"]["model_source"],
            "model_class": design["third_model_identity"]["model_class"],
            "converted_model_hash": design["third_model_identity"]["converted_model_hash"],
        },
        "dataset_hashes": design["dataset_hashes"],
    }


def _verify_expected_model_provenance(root: Path = ROOT) -> None:
    design = _load_frozen_design(root)
    model = design["third_model_identity"]
    expected_hash = str(model["converted_model_hash"]).casefold()
    provenance = read_json(root / PROVENANCE_PATH)
    converted = provenance.get("converted_sha256", {})
    actual = str(converted.get("model.safetensors", "")).casefold()
    if not actual or actual != expected_hash:
        raise Exp027ProtocolIntegrityError("EXP027_MODEL_HASH_MISMATCH")


def verify_no_result_collision(root: Path = ROOT) -> None:
    result = root / RESULT_PATH
    if result.exists():
        raise Exp027ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")


def verify_no_authorization_contamination(root: Path = ROOT) -> None:
    auth = root / AUTHORIZATION_PATH
    if auth.exists():
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_ALREADY_EXISTS")
    consumption_dir = root / CONSUMPTION_DIR
    if consumption_dir.exists():
        records = list(consumption_dir.glob("*.json"))
        if records:
            raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_CONSUMPTION_ALREADY_EXISTS")

def verify_exp027_dataset_hashes(root: Path = ROOT) -> None:
    design = _load_frozen_design(root)
    manifest = design["dataset_manifest"]
    expected = design["dataset_hashes"]
    required = {
        manifest["dataset_path"]: expected["dataset_sha256"],
        manifest["condition_panel_path"]: expected["condition_panel_sha256"],
        manifest["data_schema_path"]: expected["data_schema_sha256"],
        manifest["frozen_manifest_path"]: expected["frozen_manifest_sha256"],
        manifest["exp024_preregistration_path"]: expected["exp024_preregistration_sha256"],
    }
    for relative_path, expected_hash in required.items():
        actual_hash = sha256_file(root / relative_path)
        if actual_hash != expected_hash:
            raise Exp027ProtocolIntegrityError("EXP027_DATASET_HASH_MISMATCH")


def classify_exp027_lifecycle(
    authorization_path: Path | None,
    consumption_dir: Path,
    result_path: Path,
) -> str:
    authorization_path = Path(authorization_path) if authorization_path is not None else None
    consumption_dir = Path(consumption_dir)
    result_path = Path(result_path)
    auth_exists = authorization_path is not None and authorization_path.is_file()
    consumption_records = list(consumption_dir.glob("*.json")) if consumption_dir.exists() else []
    result_exists = result_path.exists()

    if not auth_exists and not consumption_records and not result_exists:
        return "S0_PRISTINE_UNAUTHORIZED"
    if auth_exists and not consumption_records and not result_exists:
        return "S1_AUTHORIZED_UNUSED"
    if auth_exists and len(consumption_records) == 1 and not result_exists:
        return "S2_CONSUMED_IN_PROGRESS"
    if auth_exists and len(consumption_records) == 1 and result_exists:
        return "S3_PUBLISHED"
    return "SX_INVALID_STATE"


def validate_formal_lifecycle(lifecycle: str) -> str:
    if lifecycle == "S0_PRISTINE_UNAUTHORIZED":
        raise Exp027ProtocolIntegrityError("FORMAL_RUN_REQUIRES_AUTHORIZATION")
    if lifecycle == "S2_CONSUMED_IN_PROGRESS":
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_ALREADY_CONSUMED")
    if lifecycle == "S3_PUBLISHED":
        raise Exp027ProtocolIntegrityError("CANONICAL_RESULT_ALREADY_EXISTS")
    if lifecycle == "SX_INVALID_STATE":
        raise Exp027ProtocolIntegrityError("FORMAL_LIFECYCLE_INVALID_STATE")
    return lifecycle


def validate_exp027_authorization(root: Path, authorization_path: Path) -> tuple[dict[str, Any], str]:
    if not authorization_path.is_file():
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_FILE_MISSING")
    auth = read_json(authorization_path)
    if auth.get("schema_version") != "1.0.0":
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_SCHEMA_VERSION_INVALID")
    if auth.get("experiment") != "EXP-027":
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXPERIMENT_MISMATCH")
    if auth.get("purpose") != "SINGLE_USE_FORMAL_RUN":
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_PURPOSE_INVALID")
    if auth.get("single_use") is not True:
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_NOT_SINGLE_USE")
    if auth.get("authorized_execution_count") != 1:
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_EXECUTION_COUNT_INVALID")
    if auth.get("formal_mode") != "--formal-run":
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_MODE_INVALID")
    current_binding = verify_exp027_authorities(root)
    bound = auth.get("execution_binding")
    if not isinstance(bound, Mapping) or bound != current_binding:
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_BINDING_MISMATCH")
    return auth, sha256_file(authorization_path)


def consume_exp027_authorization(
    root: Path,
    authorization: Mapping[str, Any],
    authorization_sha: str,
    *,
    run_attempt_id: str | None = None,
    consumption_dir: Path | None = None,
) -> tuple[dict[str, Any], str]:
    authorization_id = str(authorization.get("authorization_id", ""))
    if not authorization_id:
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_ID_MISSING")
    run_attempt_id = run_attempt_id or uuid.uuid4().hex
    consumption_dir = consumption_dir or (root / CONSUMPTION_DIR)
    consumption_path = consumption_dir / f"{authorization_id}.json"
    if consumption_path.exists():
        raise Exp027ProtocolIntegrityError("FORMAL_AUTHORIZATION_ALREADY_CONSUMED")
    record = {
        "schema_version": "1.0.0",
        "classification": "AUTHORIZATION_CONSUMPTION",
        "authorization_id": authorization_id,
        "authorization_sha256": authorization_sha,
        "consumed_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_attempt_id": run_attempt_id,
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
        "authority_binding": verify_exp027_authorities(root),
    }
    consumption_sha = _atomic_write_json_exclusive(consumption_path, record)
    record["consumption_record_sha256"] = consumption_sha
    return record, consumption_sha


def _authorization_path_for(root: Path, authorization_file: str | None) -> Path | None:
    if authorization_file:
        return Path(authorization_file).resolve()
    candidate = root / AUTHORIZATION_PATH
    return candidate if candidate.is_file() else None


def run_static_preflight(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    verify_exp027_authorities(root)
    _verify_expected_model_provenance(root)
    verify_no_result_collision(root)
    verify_no_authorization_contamination(root)
    design = _load_frozen_design(root)
    _ = read_json(root / NEUTRAL_EVIDENCE_PATH)
    _ = read_json(root / PROVENANCE_PATH)
    artifact = {
        "schema_version": "1.0.0",
        "classification": "EXP027_STATIC_PREFLIGHT",
        "experiment": "EXP-027",
        "status": "PASS",
        "frozen_authorities_match": True,
        "no_formal_result": True,
        "no_authorization": True,
        "no_authorization_consumption": True,
        "model_provenance_present": True,
        "carrier_contract": design["carrier_semantics"],
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
    }
    if publish:
        path = ENGINEERING_DIR / "exp027_static_preflight.json"
        _atomic_write_json(path, artifact)
    return artifact


def _neutral_preflight_not_required(root: Path) -> dict[str, Any]:
    evidence = read_json(root / NEUTRAL_EVIDENCE_PATH)
    if evidence.get("real_panel_accessed") is not False:
        raise Exp027ProtocolIntegrityError("EXP027_NEUTRAL_EVIDENCE_FIREWALL_INVALID")
    if evidence.get("carrier_mapping_verified") is not True:
        raise Exp027ProtocolIntegrityError("EXP027_NEUTRAL_CARRIER_MAPPING_NOT_VERIFIED")
    if evidence.get("hidden_size") != 2048 or evidence.get("num_hidden_layers") != 16:
        raise Exp027ProtocolIntegrityError("EXP027_NEUTRAL_RUNTIME_IDENTITY_INVALID")
    return {
        "schema_version": "1.0.0",
        "classification": "EXP027_NEUTRAL_MODEL_PREFLIGHT",
        "experiment": "EXP-027",
        "status": "NOT_REQUIRED_WITH_JUSTIFICATION",
        "justification": "EXP027_102A_LQ neutral Llama runtime/carrier qualification already completed; real-panel access false.",
        "evidence_path": str(root / NEUTRAL_EVIDENCE_PATH),
        "real_panel_accessed": evidence.get("real_panel_accessed"),
        "scientific_matrix_computed": evidence.get("scientific_matrix_computed"),
    }


def run_neutral_model_preflight(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    verify_exp027_authorities(root)
    artifact = _neutral_preflight_not_required(root)
    if publish:
        path = ENGINEERING_DIR / "exp027_neutral_model_preflight.json"
        _atomic_write_json(path, artifact)
    return artifact


def _profile_component_from_support(support: Mapping[str, Any]) -> dict[str, str]:
    return {
        "distance_association_status": support.get("distance_support", "NOT_EVALUABLE"),
        "dominance_status": support.get("sdi_class", "NO_DOMINANCE"),
        "low_d_recovery_status": support.get("low_d_support", "NOT_EVALUABLE"),
    }


def compute_exp027_profile(
    observations: Sequence[ref.ExtractedObservation],
    *,
    num_layers: int,
    bootstrap_replicates: int = BOOTSTRAP_REPLICATES,
    rng: np.random.Generator | None = None,
) -> dict[str, Any]:
    if rng is None:
        rng = np.random.default_rng(np.random.PCG64(BOOTSTRAP_SEED))
    point_profile = ref.compute_matrix_profile(
        observations,
        num_layers=num_layers,
        condition_order=ref.CONDITION_ORDER,
        bootstrap_replicates=0,
    )
    bootstrap = None
    if point_profile["source_qualification"]["source_coverage_evaluable"] and bootstrap_replicates > 0:
        bootstrap = bootstrap_proto.optimized_matrix_bootstrap(
            observations,
            num_layers,
            ref.CONDITION_ORDER,
            bootstrap_replicates,
            rng,
        )
    support = ref._support_classes(point_profile["point"], bootstrap)
    profile = dict(point_profile)
    profile["bootstrap"] = bootstrap
    profile["support"] = support
    profile["confirmatory_status"] = point_profile["confirmatory_status"]
    return profile


def run_synthetic_preflight(root: Path = ROOT, *, publish: bool = True) -> dict[str, Any]:
    verify_exp027_authorities(root)
    observations = ref._hardcoded_synthetic_observations()["A"]
    num_layers = 4
    reference_rng = np.random.default_rng(np.random.PCG64(77123))
    reference = ref.compute_matrix_profile(
        observations,
        num_layers=num_layers,
        condition_order=ref.CONDITION_ORDER,
        bootstrap_replicates=20,
        rng=reference_rng,
    )
    optimized_rng = np.random.default_rng(np.random.PCG64(77123))
    optimized = bootstrap_proto.optimized_matrix_bootstrap(
        observations,
        num_layers,
        ref.CONDITION_ORDER,
        20,
        optimized_rng,
    )
    ci_equal = (
        np.array_equal(reference["bootstrap"]["distance_association_ci"], optimized["distance_association_ci"], equal_nan=True)
        and np.array_equal(reference["bootstrap"]["sdi_ci"], optimized["sdi_ci"], equal_nan=True)
        and np.array_equal(reference["bootstrap"]["low_d_recovery_ci"], optimized["low_d_recovery_ci"], equal_nan=True)
    )
    if not ci_equal:
        raise Exp027ProtocolIntegrityError("OPTIMIZED_BOOTSTRAP_CI_NOT_EQUIVALENT")
    integrated = compute_exp027_profile(
        observations,
        num_layers=num_layers,
        bootstrap_replicates=20,
        rng=np.random.default_rng(np.random.PCG64(77123)),
    )
    components = _profile_component_from_support(integrated["support"])
    technical_valid = bool(integrated["source_qualification"]["source_coverage_evaluable"])
    route, result_status = design_validator.route_profile(
        components,
        technical_valid=technical_valid,
        measurement_valid=technical_valid,
    )
    artifact = {
        "schema_version": "1.0.0",
        "classification": "EXP027_SYNTHETIC_PREFLIGHT",
        "experiment": "EXP-027",
        "status": "PASS",
        "synthetic_model": "synthetic-A",
        "synthetic_layers": num_layers,
        "bootstrap_replicates": 20,
        "reference_optimized_ci_equivalent": ci_equal,
        "integrated_profile_route": route,
        "integrated_result_status": result_status,
        "formal_data_accessed": False,
        "scientific_result_created": False,
        "repository_commit": _repository_commit(root),
        "runner_sha256": sha256_file(Path(__file__)),
    }
    if publish:
        path = ENGINEERING_DIR / "exp027_synthetic_preflight.json"
        _atomic_write_json(path, artifact)
    return artifact

def _extract_exp027_layers(tokenizer: Any, model: Any, device: Any, text: str) -> np.ndarray:
    import torch

    encoded = tokenizer(text, return_tensors="pt", padding=False, truncation=False)
    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    backbone = model.model
    layers = list(backbone.layers)
    if len(layers) != 16:
        raise Exp027ProtocolIntegrityError("EXP027_LOGICAL_CARRIER_COUNT_MISMATCH")
    captures: list[Any] = [None] * len(layers)
    handles = []
    with torch.inference_mode():
        for index, module in enumerate(layers):
            def hook(_module, _args, output, index=index):
                if isinstance(output, (tuple, list)):
                    output = output[0]
                captures[index] = output
            handles.append(module.register_forward_hook(hook))
        try:
            model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=True,
                use_cache=False,
            )
        finally:
            for handle in handles:
                handle.remove()
    last_index = int(attention_mask[0].sum()) - 1
    arrays = []
    for capture in captures:
        if capture is None:
            raise Exp027ProtocolIntegrityError("EXP027_HOOK_CAPTURE_MISSING")
        array = capture[0, last_index, :].detach().cpu().to(torch.float32).numpy()
        if array.shape != (2048,) or not np.isfinite(array).all():
            raise Exp027ProtocolIntegrityError("EXP027_EXTRACTED_ARRAY_INVALID")
        arrays.append(array.astype(np.float32))
    return np.stack(arrays, axis=0).astype(np.float32)


def _load_exp027_runtime(root: Path):
    import torch

    design = _load_frozen_design(root)
    model_dir = Path(design["third_model_identity"]["converted_checkpoint_path"])
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(
        str(model_dir),
        dtype=torch.bfloat16,
        local_files_only=True,
        use_cache=False,
    )
    model.eval()
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model.to(device)
    return tokenizer, model, device


def load_exp027_observations(root: Path = ROOT) -> list[ref.ExtractedObservation]:
    design = _load_frozen_design(root)
    dataset_path = root / design["dataset_manifest"]["dataset_path"]
    expected_hash = design["dataset_hashes"]["dataset_sha256"]
    if sha256_file(dataset_path) != expected_hash:
        raise Exp027ProtocolIntegrityError("EXP027_DATASET_HASH_MISMATCH")
    records = ref._validate_formal_records(read_json(dataset_path))
    tokenizer, model, device = _load_exp027_runtime(root)
    observations = []
    for record in records:
        if record["record_role"] != "condition_realization":
            continue
        vectors = _extract_exp027_layers(tokenizer, model, device, str(record["text"]))
        observations.append(ref.ExtractedObservation(
            record_id=str(record["record_id"]),
            partition=str(record["partition"]),
            condition_id=str(record["condition_id"]),
            semantic_class=str(record["semantic_class"]),
            source_family_id=str(record["source_family_id"]),
            vectors=vectors,
        ))
    del model
    return observations


def _runtime_environment() -> dict[str, Any]:
    environment = {
        "python_version": sys.version.split()[0],
        "numpy_version": np.__version__,
    }
    try:
        import torch
        environment["torch_version"] = torch.__version__
        environment["cuda_available"] = bool(torch.cuda.is_available())
        environment["gpu_name"] = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:
        environment["torch_version"] = None
        environment["cuda_available"] = None
        environment["gpu_name"] = None
    return environment


def build_exp027_result_payload(
    *,
    profile: Mapping[str, Any],
    components: Mapping[str, str],
    route: str,
    result_status: str,
    technical_valid: bool,
    measurement_valid: bool,
    authorization_identity: Mapping[str, Any],
    execution_binding: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "classification": "EXP027_SCIENTIFIC_RESULT",
        "experiment": "EXP-027",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "attempt_status": "COMPLETED",
        "result_status": result_status,
        "scientific_status": "OBSERVED" if result_status == "VALID_REGISTERED_RESULT" else "NOT_OBSERVED",
        "profile": dict(components),
        "route": route,
        "technical_validity": bool(technical_valid),
        "measurement_validity": bool(measurement_valid),
        "authorization_identity": dict(authorization_identity),
        "execution_binding": dict(execution_binding),
        "execution_environment": _runtime_environment(),
        "profile_archive": _json_safe(profile),
    }


def execute_exp027_scientific_executor(
    *,
    root: Path,
    observations: Sequence[ref.ExtractedObservation],
    result_path: Path,
    authorization_identity: Mapping[str, Any],
    bootstrap_replicates: int,
) -> dict[str, Any]:
    profile = compute_exp027_profile(
        observations,
        num_layers=16,
        bootstrap_replicates=bootstrap_replicates,
    )
    technical_valid = bool(profile["source_qualification"]["source_coverage_evaluable"])
    measurement_valid = technical_valid
    components = _profile_component_from_support(profile["support"])
    route, result_status = design_validator.route_profile(
        components,
        technical_valid=technical_valid,
        measurement_valid=measurement_valid,
    )
    binding = verify_exp027_authorities(root)
    payload = build_exp027_result_payload(
        profile=profile,
        components=components,
        route=route,
        result_status=result_status,
        technical_valid=technical_valid,
        measurement_valid=measurement_valid,
        authorization_identity=authorization_identity,
        execution_binding=binding,
    )
    errors = result_validator.validate_result_payload(payload)
    if errors:
        raise Exp027ProtocolIntegrityError(f"RESULT_SCHEMA_INVALID_{errors}")
    result_sha = _atomic_write_json_exclusive(result_path, payload)
    return {"payload": payload, "profile": profile, "result_sha256": result_sha, "route": route}


def run_formal_run(
    root: Path = ROOT,
    authorization_file: str | None = None,
    *,
    progress_state_path: Path | str | None = None,
) -> dict[str, Any]:
    verify_exp027_authorities(root)
    verify_no_result_collision(root)
    state_path = Path(progress_state_path) if progress_state_path is not None else None
    progress_reporter = progress.OutcomeBlindProgress(state_path=state_path)
    progress_reporter.report("AUTHORIZATION_VALIDATION", completed=0, total=1, heartbeat=True)
    auth_path = _authorization_path_for(root, authorization_file)
    lifecycle = classify_exp027_lifecycle(
        auth_path,
        root / CONSUMPTION_DIR,
        root / RESULT_PATH,
    )
    validate_formal_lifecycle(lifecycle)
    if auth_path is None:
        raise Exp027ProtocolIntegrityError("FORMAL_RUN_REQUIRES_AUTHORIZATION")
    authorization, authorization_sha = validate_exp027_authorization(root, auth_path)
    verify_exp027_dataset_hashes(root)
    _verify_expected_model_provenance(root)
    progress_reporter.report("AUTHORIZATION_VALIDATED", completed=1, total=1, heartbeat=True)
    consumption, consumption_sha = consume_exp027_authorization(
        root,
        authorization,
        authorization_sha,
    )
    progress_reporter.report("AUTHORIZATION_CONSUMED", completed=1, total=1, heartbeat=True)
    observations = load_exp027_observations(root)
    progress_reporter.report("EXTRACTION_COMPLETE", completed=1, total=1, heartbeat=True)
    result = execute_exp027_scientific_executor(
        root=root,
        observations=observations,
        result_path=root / RESULT_PATH,
        authorization_identity={
            "authorization_id": authorization["authorization_id"],
            "authorization_sha256": authorization_sha,
            "consumption_record_sha256": consumption_sha,
            "run_attempt_id": consumption["run_attempt_id"],
        },
        bootstrap_replicates=BOOTSTRAP_REPLICATES,
    )
    progress_reporter.report("PUBLICATION_COMPLETE", completed=1, total=1, heartbeat=True, publication_status="PUBLISHED")
    result["authorization_consumption"] = consumption
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    for flag in (_STATIC_FLAG, _SYNTHETIC_FLAG, _NEUTRAL_FLAG, _FORMAL_FLAG):
        modes.add_argument(flag, action="store_true")
    parser.add_argument(_REPO_ROOT_FLAG, default=None)
    parser.add_argument(_AUTHORIZATION_FILE_FLAG, default=None)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.repo_root).resolve() if args.repo_root else ROOT
    try:
        if args.static_preflight:
            result = run_static_preflight(root)
            print("EXP027_STATIC_PREFLIGHT = PASS")
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.synthetic_preflight:
            result = run_synthetic_preflight(root)
            print("EXP027_SYNTHETIC_PREFLIGHT = PASS")
            print(json.dumps({"status": result["status"], "route": result["integrated_profile_route"]}, indent=2, sort_keys=True))
            return 0
        if args.neutral_model_preflight:
            result = run_neutral_model_preflight(root)
            print("EXP027_NEUTRAL_MODEL_PREFLIGHT = NOT_REQUIRED_WITH_JUSTIFICATION")
            print(json.dumps(result, indent=2, sort_keys=True))
            return 0
        if args.formal_run:
            run_formal_run(root, args.authorization_file)
            return 0
    except Exp027ProtocolIntegrityError as exc:
        print("EXP027_MODE = FAIL")
        print(f"EXP027_ERROR = {exc}")
        return 1
    except Exception as exc:
        print("EXP027_MODE = FAIL")
        print(f"EXP027_ERROR = {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())