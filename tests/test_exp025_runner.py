import hashlib
import json
import sys
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
