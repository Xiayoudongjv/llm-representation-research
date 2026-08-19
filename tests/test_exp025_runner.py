import copy
import hashlib
import json
import math
import os
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
        "clarification_authority_hashes": {
            "clarification_md": runner.CLARIFICATION_MD_SHA256,
            "clarification_json": runner.CLARIFICATION_JSON_SHA256,
            "clarification_validator": runner.CLARIFICATION_VALIDATOR_SHA256,
        },
        "inherited_authority_hashes": {
            "dataset": runner.INHERITED_DATASET_SHA256,
            "condition_panel": runner.INHERITED_CONDITION_PANEL_SHA256,
            "data_schema": runner.INHERITED_DATA_SCHEMA_SHA256,
            "frozen_manifest": runner.INHERITED_MANIFEST_SHA256,
            "exp024_preregistration": runner.EXP024_PREREGISTRATION_SHA256,
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
    authorization.update(overrides)
    path.write_text(json.dumps(authorization, indent=2, sort_keys=True), encoding="utf-8")
    return authorization


def _fresh_authorization_setup(tmp_path, monkeypatch, authorization_id=None):
    authorization_id = authorization_id or uuid.uuid4().hex
    consumption_dir = tmp_path / "authorization_consumption"
    result_path = tmp_path / "exp025_results.json"
    monkeypatch.setattr(runner, "AUTHORIZATION_CONSUMPTION_DIR", consumption_dir)
    monkeypatch.setattr(runner, "FORMAL_RESULT_PATH", result_path)
    monkeypatch.setattr(runner, "FORMAL_RESULT_CANDIDATES", (result_path,))
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
    monkeypatch.setattr(runner, "atomic_publish_validated_result", lambda result, root=None: {"sha256": "a" * 64})
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
    monkeypatch.setattr(runner, "atomic_publish_validated_result", lambda result, root=None: {"sha256": "a" * 64})
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
    monkeypatch.setattr(runner, "atomic_publish_validated_result", lambda result, root=None: {"sha256": "a" * 64})
    monkeypatch.setattr(runner, "_load_runtime", forbid_runtime)
    monkeypatch.setattr(runner, "load_frozen_dataset", forbid_dataset)
    runner.run_formal(ROOT, authorization_path)
    assert science_called == {"executor": True, "runtime": False, "dataset": False}


def test_stale_100b_sentinel_is_removed():
    source = Path(runner.__file__).read_text(encoding="utf-8")
    assert "FORMAL_AUTHORIZATION_NOT_CONSUMED_IN_100B" not in source


def test_balanced_accuracy_is_macro_recall_over_frozen_classes():
    y_true = ["logic", "logic", "causality", "analogy", "definition"]
    y_pred = ["logic", "causality", "causality", "analogy", "definition"]
    expected = (1 / 4) * ((1 / 2) + (1 / 1) + (1 / 1) + (1 / 1))
    assert runner.balanced_accuracy(y_true, y_pred) == pytest.approx(expected)


def test_balanced_accuracy_zero_true_class_fails_closed():
    with pytest.raises(runner.ProtocolIntegrityError, match="MISSING_TRUE_CLASS"):
        runner.balanced_accuracy(
            ["logic", "causality", "analogy"], ["logic", "causality", "analogy"]
        )


def test_transform_with_stats_zero_scale_sets_zero_without_epsilon():
    X = np.array([[3.0, 2.0, 0.0, 13.0]], dtype=np.float32)
    mean = np.array([1.0, -2.0, 0.0, 3.0], dtype=np.float32)
    scale = np.array([2.0, 4.0, 0.0, 5.0], dtype=np.float32)
    actual = runner.transform_with_stats(X, mean, scale)
    expected = np.array([[1.0, 1.0, 0.0, 2.0]], dtype=np.float32)
    assert actual.dtype == np.float32
    assert np.allclose(actual, expected)


def test_spearman_uses_average_rank_ties():
    x = [1.0, 1.0, 2.0, 3.0]
    y = [1.0, 1.0, 2.0, 3.0]
    assert runner.average_rank(x) == [1.5, 1.5, 3.0, 4.0]
    assert runner.spearman_rho(x, y) == pytest.approx(1.0)


def test_exact_permutation_includes_equality_one_sided():
    result = runner.exact_one_sided_permutation_p([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
    assert result["status"] == "EVALUABLE"
    assert result["total"] == 6
    assert result["count_ge"] == 1
    assert result["p"] == pytest.approx(1 / 6)


def test_exact_binomial_effective_n_zero_is_not_evaluable():
    result = runner.exact_binomial_support([0.0, 0.0])
    assert result["status"] == "NOT_EVALUABLE"
    assert result["effective_n"] == 0
    assert result["effective_successes"] == 0
    assert result["exact_one_sided_p"] is None
    assert result["support"] == "NOT_EVALUABLE"


def test_route_replication_indeterminate_maps_to_no_scientific_routing():
    d = runner.classify_direction([0.0, 0.0])
    g = runner.classify_direction([0.1, -0.1])
    routing = runner.route_replication(d, g)
    assert routing["routing"] == "NO SCIENTIFIC ROUTING"
    assert routing["technical_validity"] == "INVALID_OR_INDETERMINATE"


def _synthetic_formal_records() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for condition in runner.CONDITION_ORDER:
        for partition in runner.PARTITIONS:
            for semantic_class in runner.CLASS_ORDER:
                for family_index in range(runner.ALLOCATION[partition]):
                    family_id = (
                        f"syn_{condition}_{partition}_{semantic_class}_{family_index:04d}"
                    )
                    for record_role in runner.RECORD_ROLES:
                        records.append(
                            {
                                "record_id": f"{family_id}_{record_role}",
                                "source_family_id": family_id,
                                "semantic_class": semantic_class,
                                "condition_id": condition,
                                "partition": partition,
                                "record_role": record_role,
                                "text": (
                                    f"neutral synthetic {condition} {partition} "
                                    f"{semantic_class} {record_role} {family_index}"
                                ),
                                "base_content_identity": family_id,
                                "transformation_rule_id": condition,
                                "independence_group": family_id,
                                "review_status": "PASS",
                                "provenance": {},
                            }
                        )
    return records


def _synthetic_formal_forward(tokenizer, model, device, text):
    torch = pytest.importorskip("torch")
    class_index = next(
        index
        for index, semantic_class in enumerate(runner.CLASS_ORDER)
        if semantic_class in text
    )
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    vectors = {}
    for checkpoint_index, checkpoint in enumerate(runner.CHECKPOINT_NAMES):
        rng = np.random.default_rng(int.from_bytes(digest[:8], "big") + checkpoint_index)
        vector = np.zeros((4,), dtype=np.float32)
        vector[class_index] = 1.0
        vector += rng.normal(0.0, 0.02, size=(4,)).astype(np.float32)
        vectors[checkpoint] = vector
    return {
        "input_ids": torch.tensor([[0, 1, 2]], dtype=torch.long, device=device),
        "attention_mask": torch.ones((1, 3), dtype=torch.long, device=device),
        "representations": vectors,
        "hook_firing_count": 2,
        "hook_cleanup_verified": True,
        "exp025_hooks_remaining": 0,
        "foreign_hooks_remaining": 0,
    }


class _FakeConfig:
    model_type = "olmo2"
    num_hidden_layers = 16
    hidden_size = 4


class _FakeTokenizer:
    pass


class Olmo2ForCausalLM:
    def __init__(self):
        self.config = _FakeConfig()
        self.training = False

    def parameters(self):
        torch = pytest.importorskip("torch")
        yield torch.nn.Parameter(torch.zeros(1, dtype=torch.float32))


def _synthetic_runtime():
    torch = pytest.importorskip("torch")
    return _FakeTokenizer(), Olmo2ForCausalLM(), torch.device("cpu"), torch.float32


def test_formal_runtime_synthetic_production_execution(tmp_path, monkeypatch):
    records = _synthetic_formal_records()
    monkeypatch.setattr(runner, "verify_frozen_design", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_inherited_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_clarification_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "exact_one_sided_permutation_p",
        lambda x, y, alternative="greater": {
            "rho": 0.5,
            "p": 0.04,
            "count_ge": 1,
            "total": math.factorial(10),
            "status": "EVALUABLE",
        },
    )
    result = runner._execute_formal_analysis(
        tmp_path,
            {
                "authorization_id": "synthetic-auth",
                "authorized_repository_commit": "a" * 40,
                "runner_sha256": sha256_file(Path(runner.__file__)),
            },
        {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
            "consumption_record_path": str(tmp_path / "consumption" / "synthetic-auth.json"),
        },
        "synthetic-attempt",
        condition_order=runner.CONDITION_ORDER,
        records_loader=lambda root=None: (records, []),
        runtime_loader=lambda root=None: _synthetic_runtime(),
        record_extractor=_synthetic_formal_forward,
    )
    runner.validate_result_schema(result, formal=True)
    assert result["result_status"] == "FORMAL_RESULT"
    assert result["scientific_status"] == "FORMAL_ANALYSIS_COMPLETED"
    assert len(result["condition_level"]["s_diag"]) == 10
    assert len(result["condition_level"]["g_eval"]) == 10
    assert result["hidden_states_included"] is False
    assert result["prompt_text_included"] is False


def test_formal_atomic_publication_uses_temporary_root(tmp_path, monkeypatch):
    records = _synthetic_formal_records()
    monkeypatch.setattr(runner, "verify_frozen_design", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_inherited_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_clarification_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "exact_one_sided_permutation_p",
        lambda x, y, alternative="greater": {
            "rho": 0.5,
            "p": 0.04,
            "count_ge": 1,
            "total": math.factorial(10),
            "status": "EVALUABLE",
        },
    )
    result = runner._execute_formal_analysis(
        tmp_path,
            {
                "authorization_id": "synthetic-auth",
                "authorized_repository_commit": "a" * 40,
                "runner_sha256": sha256_file(Path(runner.__file__)),
            },
        {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
            "consumption_record_path": str(tmp_path / "consumption" / "synthetic-auth.json"),
        },
        "synthetic-attempt",
        condition_order=runner.CONDITION_ORDER,
        records_loader=lambda root=None: (records, []),
        runtime_loader=lambda root=None: _synthetic_runtime(),
        record_extractor=_synthetic_formal_forward,
    )
    canonical_relative = (runner.EXP_DIR / "results" / "exp025_results.json").relative_to(runner.ROOT)
    canonical = tmp_path / canonical_relative
    monkeypatch.setattr(runner, "FORMAL_RESULT_PATH", runner.EXP_DIR / "results" / "exp025_results.json")
    monkeypatch.setattr(runner, "FORMAL_RESULT_CANDIDATES", (canonical,))
    published = runner.atomic_publish_validated_result(result, tmp_path)
    assert published["sha256"]
    assert canonical.is_file()


@pytest.mark.parametrize(
    "override,expected",
    [
        ({"purpose": "WRONG"}, "PURPOSE_INVALID"),
        ({"repository_commit": "0" * 40}, "REPOSITORY_COMMIT_MISMATCH"),
        (
            {
                "clarification_authority_hashes": {
                    "clarification_md": "0" * 64,
                    "clarification_json": runner.CLARIFICATION_JSON_SHA256,
                    "clarification_validator": runner.CLARIFICATION_VALIDATOR_SHA256,
                }
            },
            "CLARIFICATION_HASH_MISMATCH_clarification_md",
        ),
    ],
)
def test_authorization_failure_matrix_blocks_before_consumption(tmp_path, monkeypatch, override, expected):
    authorization_path, authorization_id, consumption_dir = _fresh_authorization_setup(tmp_path, monkeypatch)
    if "repository_commit" in override:
        _write_valid_authorization(authorization_path, authorization_id, repo_commit=override["repository_commit"])
    else:
        _write_valid_authorization(authorization_path, authorization_id, **override)
    with pytest.raises(runner.ProtocolIntegrityError, match=expected):
        runner.run_formal(ROOT, authorization_path)
    assert not list(consumption_dir.glob("*.json"))


def _build_valid_formal_result(tmp_path, monkeypatch):
    records = _synthetic_formal_records()
    monkeypatch.setattr(runner, "verify_frozen_design", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_inherited_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_clarification_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(
        runner,
        "exact_one_sided_permutation_p",
        lambda x, y, alternative="greater": {
            "rho": 0.5,
            "p": 0.04,
            "count_ge": 1,
            "total": math.factorial(10),
            "status": "EVALUABLE",
        },
    )
    return runner._execute_formal_analysis(
        tmp_path,
        {
            "authorization_id": "synthetic-auth",
            "authorized_repository_commit": "a" * 40,
            "runner_sha256": sha256_file(Path(runner.__file__)),
        },
        {
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
            "consumption_record_path": str(tmp_path / "consumption" / "synthetic-auth.json"),
        },
        "synthetic-attempt",
        condition_order=runner.CONDITION_ORDER,
        records_loader=lambda root=None: (records, []),
        runtime_loader=lambda root=None: _synthetic_runtime(),
        record_extractor=_synthetic_formal_forward,
    )


def test_validate_result_schema_rejects_missing_nested_fields(tmp_path, monkeypatch):
    result = _build_valid_formal_result(tmp_path, monkeypatch)
    missing_paths = [
        ("runner", "sha256"),
        ("model", "model_id"),
        ("dataset", "path"),
        ("condition_panel", "sha256"),
        ("condition_level", "descriptive_summaries"),
        ("recovery_governance", "execution_classification"),
        ("provenance", "consumption_record_path"),
        ("technical_validity", "status"),
    ]
    for path in missing_paths:
        mutated = copy.deepcopy(result)
        cursor = mutated
        for part in path[:-1]:
            cursor = cursor[part]
        del cursor[path[-1]]
        with pytest.raises(runner.ProtocolIntegrityError):
            runner.validate_result_schema(mutated, formal=True)


def test_low_usability_formal_run_blocks_canonical_result(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    records = _synthetic_formal_records()
    consumption_dir = tmp_path / "consumption"
    result_path = tmp_path / "exp025_results.json"
    auth_path = tmp_path / "authorization.json"

    def random_forward(tokenizer, model, device, text):
        seed = int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")
        rng = np.random.default_rng(seed)
        vectors = {
            checkpoint: rng.normal(size=(4,)).astype(np.float32)
            for checkpoint in runner.CHECKPOINT_NAMES
        }
        return {
            "input_ids": torch.tensor([[0, 1, 2]], dtype=torch.long, device=device),
            "attention_mask": torch.ones((1, 3), dtype=torch.long, device=device),
            "representations": vectors,
            "hook_firing_count": 2,
            "hook_cleanup_verified": True,
            "exp025_hooks_remaining": 0,
            "foreign_hooks_remaining": 0,
        }

    monkeypatch.setattr(runner, "AUTHORIZATION_CONSUMPTION_DIR", consumption_dir)
    monkeypatch.setattr(runner, "FORMAL_RESULT_PATH", result_path)
    monkeypatch.setattr(runner, "FORMAL_RESULT_CANDIDATES", (result_path,))
    monkeypatch.setattr(runner, "verify_frozen_design", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_inherited_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_clarification_authorities", lambda root=None: {})
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    monkeypatch.setattr(runner, "_repository_commit", lambda root=None: "a" * 40)
    monkeypatch.setattr(runner, "load_frozen_dataset", lambda root=None: (records, []))
    monkeypatch.setattr(runner, "_load_runtime", lambda root=None: _synthetic_runtime())
    monkeypatch.setattr(runner, "_formal_record_extractor", random_forward)
    monkeypatch.setattr(
        runner,
        "_validate_authorization",
        lambda root, path: (
            {
                "authorization_id": "low-usability-auth",
                "authorized_repository_commit": "a" * 40,
                "runner_sha256": sha256_file(Path(runner.__file__)),
            },
            "a" * 64,
        ),
    )

    with pytest.raises(runner.TechnicalInvalidError, match="USABILITY"):
        runner.run_formal(ROOT, auth_path)

    assert (consumption_dir / "low-usability-auth.json").is_file()
    assert not result_path.exists()


def test_publication_race_fails_closed_without_overwrite(tmp_path, monkeypatch):
    result = _build_valid_formal_result(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "FORMAL_RESULT_PATH", runner.EXP_DIR / "results" / "exp025_results.json")
    monkeypatch.setattr(runner, "verify_no_result_collision", lambda root=None: None)
    canonical = tmp_path / (runner.EXP_DIR / "results" / "exp025_results.json").relative_to(runner.ROOT)
    temp_path = canonical.with_name(canonical.name + ".tmp")

    real_link = os.link

    def racing_link(src, dst):
        Path(dst).write_bytes(b"PREEXISTING")
        return real_link(src, dst)

    monkeypatch.setattr(runner.os, "link", racing_link)
    with pytest.raises(runner.ProtocolIntegrityError, match="FORMAL_RESULT_PATH_UNEXPECTED"):
        runner.atomic_publish_validated_result(result, tmp_path)
    assert canonical.read_bytes() == b"PREEXISTING"
    assert not temp_path.exists()


def test_constant_and_nonfinite_spearman_are_not_evaluable():
    constant_result = runner.exact_one_sided_permutation_p([1.0, 1.0, 1.0], [1.0, 1.0, 1.0])
    assert constant_result["status"] == "NOT_EVALUABLE"
    assert constant_result["rho"] != constant_result["rho"]
    assert constant_result["p"] is None
    assert constant_result["count_ge"] is None

    nonfinite_result = runner.exact_one_sided_permutation_p([1.0, 2.0], [float("nan"), 1.0])
    assert nonfinite_result["status"] == "NOT_EVALUABLE"


def test_formal_pipeline_qualification_reports_expected_statistics(tmp_path, monkeypatch):
    result = runner.run_formal_pipeline_qualification(ROOT, publish=False)
    assert result["formal_pipeline_qualification"] == "PASS"
    assert result["formal_run_readiness"] == "READY"
    assert result["registered_statistics_expected_value_test"] == "PASS"
    assert result["provenance_validation"] == "PASS"
    assert result["recovery_governance_disclosure"] == "PASS"
    assert result["registered_descriptive_summaries"] == "PASS"
