import hashlib
import json
import sys
import uuid
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
EXP025_DIR = ROOT / "experiments" / "exp025"
if str(EXP025_DIR) not in sys.path:
    sys.path.insert(0, str(EXP025_DIR))

import run_exp025 as runner


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_design_identity_binding():
    assert runner.DESIGN_COMMIT == "0d2affeea9cab72ee89620a8bb917927010f6ac2"
    assert runner.DESIGN_CONFIG_SHA256 == sha256_file(runner.DESIGN_CONFIG_PATH)
    assert runner.DESIGN_PREREGISTRATION_SHA256 == sha256_file(runner.DESIGN_PREREGISTRATION_PATH)
    assert runner.DESIGN_MODEL_SELECTION_SHA256 == sha256_file(runner.DESIGN_MODEL_SELECTION_PATH)
    assert runner.DESIGN_CHECKPOINT_MAPPING_SHA256 == sha256_file(runner.DESIGN_CHECKPOINT_MAPPING_PATH)
    assert runner.DESIGN_VALIDATOR_SHA256 == sha256_file(runner.DESIGN_VALIDATOR_PATH)


def test_model_revision_pinned():
    assert runner.MODEL_ID == "allenai/OLMo-2-0425-1B-Instruct"
    assert runner.MODEL_REVISION == "48d788eca847d4d7548f375ad03d3c9312f6139e"
    assert runner.MODEL_FAMILY == "OLMo2"
    assert runner.FALLBACK_MODEL == "google/gemma-3-1b-it"


def test_checkpoint_mapping_frozen():
    assert runner.REFERENCE_BLOCK_INDEX == 9
    assert runner.FINAL_BLOCK_INDEX == 15
    assert runner.REFERENCE_CHECKPOINT == "block9_pre_final_rmsnorm"
    assert runner.FINAL_CHECKPOINT == "block15_pre_final_rmsnorm"
    assert runner.POST_FINAL_CHECKPOINT == "block15_post_final_rmsnorm"
    assert runner.olmo_candidate_block(16, 28, 16) == 9
    assert runner.olmo_candidate_block(27, 28, 16) == 15


def test_mode_requires_one_mode():
    with pytest.raises(SystemExit):
        runner.build_parser().parse_args([])


def test_formal_run_fails_closed_without_authorization(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "FORMAL_AUTHORIZATION_PATH", tmp_path / "missing.json")
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.run_formal(ROOT)


def test_last_valid_token_index():
    mask = np.array([[1, 1, 1, 0]], dtype=np.int64)
    assert runner.last_valid_token_indices(mask)[0] == 2


def test_float32_conversion_from_numpy():
    value = np.array([1, 2, 3], dtype=np.float64)
    output = runner.to_float32_analysis_array(value)
    assert output.dtype == np.float32


def test_bfloat16_tensor_to_float32_numpy_boundary():
    torch = pytest.importorskip("torch")
    if not torch.cuda.is_available() or not torch.cuda.is_bf16_supported():
        pytest.skip("BF16 support not available on this runtime")
    value = torch.tensor([1.0, -2.0, 3.5], dtype=torch.bfloat16, device="cuda:0")
    output = runner.to_float32_analysis_array(value)
    assert isinstance(output, np.ndarray)
    assert output.dtype == np.float32
    assert np.allclose(output, np.array([1.0, -2.0, 3.5], dtype=np.float32), atol=1e-2)


def test_checkpoint_extraction_flattens_single_batch_dimension():
    torch = pytest.importorskip("torch")
    tensor = torch.tensor([[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]], dtype=torch.float32)
    mask = torch.tensor([[1, 1, 1]], dtype=torch.long)
    output = runner._extract_checkpoint_array(tensor, mask)
    assert output.shape == (3,)
    assert output.dtype == np.float32
    assert np.allclose(output, np.array([7.0, 8.0, 9.0], dtype=np.float32))


def test_class_probability_class_mapping():
    rng = np.random.RandomState(1)
    X = rng.normal(size=(40, 4))
    y = ["logic", "causality", "analogy", "definition"] * 10
    model, mapping = runner.fit_classifier(X, y)
    assert mapping == ["analogy", "causality", "definition", "logic"]
    probs = model.predict_proba(X)
    assert probs.shape == (40, 4)
    assert np.allclose(probs.sum(axis=1), 1.0)


def test_dataset_firewall_separation():
    _, metas = runner.load_frozen_dataset(ROOT)
    result = runner.validate_dataset_firewall(metas)
    assert result["status"] == "PASS"
    assert result["record_count"] == 1760
    assert result["source_family_count"] == 880
    assert result["condition_count"] == 10
    assert result["overlaps"] == {"fit_diag": 0, "fit_eval": 0, "diag_eval": 0}


def test_recalibration_known_answer():
    mean = np.array([1.0, -2.0, 0.0, 3.0], dtype=np.float32)
    scale = np.array([2.0, 4.0, 1.0, 5.0], dtype=np.float32)
    X = np.array([[3.0, 2.0, 0.0, 13.0]], dtype=np.float32)
    expected = (X - mean) / scale
    actual = runner.transform_with_stats(X, mean, scale)
    assert np.allclose(actual, expected, atol=1e-6)


def test_qualification_does_not_publish_scientific_result(tmp_path, monkeypatch):
    output_path = tmp_path / "qualification.json"
    monkeypatch.setattr(runner, "ENGINEERING_QUALIFICATION_PATH", output_path)
    result = runner.run_engineering_qualification(ROOT, publish=True)
    assert result["formal_run_performed"] is False
    assert result["scientific_result_created"] is False
    assert result["diag_outcome_viewed"] is False
    assert result["eval_outcome_viewed"] is False
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["scientific_result_created"] is False


def test_result_schema_validation_reachable_from_production_path():
    # The production run_formal entry point is wired to the same frozen design verifier.
    identities = runner.verify_frozen_design(ROOT)
    assert identities["design_config_sha256"] == runner.DESIGN_CONFIG_SHA256



def _write_valid_authorization(path: Path, authorization_id: str, **overrides):
    repo_commit = overrides.pop("repo_commit", runner._repository_commit(ROOT))
    runner_sha = overrides.pop("runner_sha", sha256_file(Path(runner.__file__)))
    qualification_sha = overrides.pop("qualification_sha", sha256_file(runner.ENGINEERING_QUALIFICATION_PATH))
    model_id = overrides.pop("model_id", runner.MODEL_ID)
    model_revision = overrides.pop("model_revision", runner.MODEL_REVISION)
    if overrides:
        raise ValueError(f"unexpected overrides: {sorted(overrides)}")
    authorization = {
        "schema_version": "1.0.0",
        "authorization_id": authorization_id,
        "experiment": "EXP-025",
        "purpose": "SINGLE_USE_FORMAL_RUN",
        "single_use": True,
        "issued_at_utc": "2026-08-19T00:00:00+00:00",
        "authorization_created_at_utc": "2026-08-19T00:00:00+00:00",
        "repository_commit": repo_commit,
        "authorized_repository_commit": repo_commit,
        "runner_sha256": runner_sha,
        "qualification_artifact_sha256": qualification_sha,
        "qualification_status": "PASS",
        "formal_run_readiness": "READY",
        "frozen_authority_hashes": {
            "exp025_preregistration": runner.DESIGN_PREREGISTRATION_SHA256,
            "model_selection": runner.DESIGN_MODEL_SELECTION_SHA256,
            "checkpoint_mapping": runner.DESIGN_CHECKPOINT_MAPPING_SHA256,
            "frozen_config": runner.DESIGN_CONFIG_SHA256,
            "design_validator": runner.DESIGN_VALIDATOR_SHA256,
        },
        "dataset_identity": {
            "path": "experiments/exp024/data/exp024_condition_panel_frozen.json",
            "sha256": runner.INHERITED_DATASET_SHA256,
        },
        "condition_panel_identity": {
            "path": "experiments/exp024/condition_panel_spec.json",
            "sha256": sha256_file(ROOT / "experiments" / "exp024" / "condition_panel_spec.json"),
        },
        "model_id": model_id,
        "model_revision": model_revision,
        "model_family": "OLMo2",
        "formal_mode": "--formal-run",
        "authorized_execution_count": 1,
        "canonical_result_path": "experiments/exp025/results/exp025_results.json",
        "consumption_directory": "experiments/exp025/results/authorization_consumption",
        "formal_run_performed": False,
        "scientific_result_created": False,
    }
    path.write_text(json.dumps(authorization, indent=2, sort_keys=True), encoding="utf-8")
    return authorization


def _fresh_authorization_setup(tmp_path, monkeypatch, authorization_id=None):
    authorization_id = authorization_id or uuid.uuid4().hex
    consumption_dir = tmp_path / "authorization_consumption"
    monkeypatch.setattr(runner, "AUTHORIZATION_CONSUMPTION_DIR", consumption_dir)
    authorization_path = tmp_path / "authorization.json"
    _write_valid_authorization(authorization_path, authorization_id)
    return authorization_path, authorization_id, consumption_dir


def test_fresh_authorization_is_consumed_and_reaches_executor(tmp_path, monkeypatch):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    calls = []

    def fake_execute(root, authorization, consumption, run_attempt_id):
        calls.append((root, authorization, consumption, run_attempt_id))
        return {"executor": "reached"}

    monkeypatch.setattr(runner, "_execute_formal_analysis", fake_execute)
    result = runner.run_formal(ROOT, authorization_path)
    assert result == {"executor": "reached"}
    assert len(calls) == 1

    consumption_path = consumption_dir / f"{authorization_id}.json"
    assert consumption_path.exists()
    record = json.loads(consumption_path.read_text(encoding="utf-8"))
    assert record["authorization_id"] == authorization_id
    assert record["authorization_sha256"] == sha256_file(authorization_path)
    assert record["run_attempt_id"] == calls[0][3]


def test_double_consumption_is_rejected(tmp_path, monkeypatch):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    calls = []

    def fake_execute(root, authorization, consumption, run_attempt_id):
        calls.append(run_attempt_id)
        return None

    monkeypatch.setattr(runner, "_execute_formal_analysis", fake_execute)
    runner.run_formal(ROOT, authorization_path)
    with pytest.raises(runner.ProtocolIntegrityError, match="AUTHORIZATION_ALREADY_CONSUMED"):
        runner.run_formal(ROOT, authorization_path)
    assert len(calls) == 1
    assert len(list(consumption_dir.glob("*.json"))) == 1


def test_existing_result_blocks_consumption(tmp_path, monkeypatch):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    result_path = tmp_path / "exp025_results.json"
    result_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(runner, "FORMAL_RESULT_CANDIDATES", (result_path,))
    with pytest.raises(runner.ProtocolIntegrityError, match="FORMAL_RESULT_PATH_UNEXPECTED"):
        runner.run_formal(ROOT, authorization_path)
    assert not list(consumption_dir.glob("*.json"))


def test_wrong_repository_commit_blocks_consumption(tmp_path, monkeypatch):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    _write_valid_authorization(authorization_path, authorization_id, repo_commit="0" * 40)
    with pytest.raises(runner.ProtocolIntegrityError, match="REPOSITORY_COMMIT_MISMATCH"):
        runner.run_formal(ROOT, authorization_path)
    assert not list(consumption_dir.glob("*.json"))


@pytest.mark.parametrize(
    "override,expected",
    [
        ({"model_id": "wrong/model"}, "MODEL_ID_MISMATCH"),
        ({"model_revision": "deadbeef"}, "MODEL_REVISION_MISMATCH"),
    ],
)
def test_wrong_model_identity_blocks_consumption(tmp_path, monkeypatch, override, expected):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    _write_valid_authorization(authorization_path, authorization_id, **override)
    with pytest.raises(runner.ProtocolIntegrityError, match=expected):
        runner.run_formal(ROOT, authorization_path)
    assert not list(consumption_dir.glob("*.json"))


def test_science_paths_are_not_reached_before_consumption(tmp_path, monkeypatch):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    science_called = {"executor": False, "runtime": False, "dataset": False}

    def fake_execute(root, authorization, consumption, run_attempt_id):
        science_called["executor"] = True
        return None

    def forbid_runtime(*args, **kwargs):
        science_called["runtime"] = True
        raise AssertionError("runtime reached before consumption")

    def forbid_dataset(*args, **kwargs):
        science_called["dataset"] = True
        raise AssertionError("dataset loader reached before consumption")

    monkeypatch.setattr(runner, "_execute_formal_analysis", fake_execute)
    monkeypatch.setattr(runner, "_load_runtime", forbid_runtime)
    monkeypatch.setattr(runner, "load_frozen_dataset", forbid_dataset)
    runner.run_formal(ROOT, authorization_path)
    assert science_called == {"executor": True, "runtime": False, "dataset": False}


def test_stale_100b_sentinel_is_removed():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "FORMAL_AUTHORIZATION_NOT_CONSUMED_IN_100B" not in source
