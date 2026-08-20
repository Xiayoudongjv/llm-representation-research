import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

try:
    import torch
except ImportError:  # pragma: no cover - torch is required by the repository runtime
    torch = None


ROOT = Path(__file__).resolve().parents[1]
EXP026_DIR = ROOT / "experiments" / "exp026"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(EXP026_DIR) not in sys.path:
    sys.path.insert(0, str(EXP026_DIR))

import run_exp026 as runner


def _observations():
    return runner._hardcoded_synthetic_observations()


def _summary(
    *,
    distance_support="NOT_SUPPORTED",
    sdi_class="NO_DOMINANCE",
    low_d_support="NOT_SUPPORTED",
    localization=0.0,
    boundaries=None,
    localization_r=0.0,
    boundaries_r=None,
):
    return {
        "point": {
            "localization": {"localization": localization, "boundaries": boundaries or []},
            "localization_r": {"localization": localization_r, "boundaries": boundaries_r or []},
        },
        "support": {
            "distance_support": distance_support,
            "sdi_class": sdi_class,
            "low_d_support": low_d_support,
        },
    }


class FakeTokenizer:
    def __call__(self, text, return_tensors="pt", padding=False, truncation=False):
        torch = pytest.importorskip("torch")
        ids = torch.tensor([[0, 1, 2, 3]], dtype=torch.long)
        return {"input_ids": ids, "attention_mask": torch.ones_like(ids)}


class FakeLayer(torch.nn.Module if torch is not None else object):
    def __init__(self, output):
        super().__init__()
        self.output = output

    def forward(self, _inputs):
        return self.output


class FakeModel:
    def __init__(self, layers):
        self.model = SimpleNamespace(layers=layers)

    def __call__(self, **_kwargs):
        for layer in self.model.layers:
            layer(None)
        return {}


def test_frozen_authorities_match():
    actual = runner.verify_frozen_design(ROOT)
    assert actual == runner.EXPECTED_DESIGN_HASHES


def test_model_registry_is_pinned():
    assert set(runner.MODEL_KEYS) == {"Q", "O"}
    assert runner.MODEL_REGISTRY["Q"]["num_hidden_layers"] == 28
    assert runner.MODEL_REGISTRY["O"]["num_hidden_layers"] == 16
    assert runner.MODEL_REGISTRY["Q"]["hidden_size"] == 2048
    assert runner.MODEL_REGISTRY["O"]["hidden_size"] == 2048


def test_mode_requires_one_mode():
    with pytest.raises(SystemExit):
        runner.build_parser().parse_args([])


def test_formal_run_fails_closed_without_authorization(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "FORMAL_AUTHORIZATION_PATH", tmp_path / "missing.json")
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.run_formal_run(ROOT)


def test_last_valid_token_indices_numpy():
    mask = np.array([[1, 1, 1, 0], [1, 1, 0, 0]], dtype=np.int64)
    assert runner.last_valid_token_indices(mask) == [2, 1]


def test_last_valid_token_indices_rejects_empty_and_zero_mask():
    with pytest.raises(ValueError):
        runner.last_valid_token_indices(np.array([0, 0, 0], dtype=np.int64))
    with pytest.raises(ValueError):
        runner.last_valid_token_indices(np.array([], dtype=np.int64))


def test_select_last_valid_token_torch():
    torch = pytest.importorskip("torch")
    hidden = torch.tensor(
        [
            [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]],
            [[10.0, 11.0, 12.0], [13.0, 14.0, 15.0], [16.0, 17.0, 18.0]],
        ],
        dtype=torch.float32,
    )
    mask = torch.tensor([[1, 1, 0], [1, 1, 1]], dtype=torch.long)
    selected = runner.select_last_valid_token(hidden, mask)
    assert torch.is_tensor(selected)
    assert selected.shape == (2, 3)
    assert torch.equal(selected[0], hidden[0, 1])
    assert torch.equal(selected[1], hidden[1, 2])


def test_to_float32_analysis_array_from_numpy():
    array = runner.to_float32_analysis_array(np.array([1, 2, 3], dtype=np.float64))
    assert isinstance(array, np.ndarray)
    assert array.dtype == np.float32


def test_to_float32_analysis_array_from_torch_and_ndim_reduction():
    torch = pytest.importorskip("torch")
    tensor = torch.tensor([[1.0, 2.0, 3.0]], dtype=torch.float32)
    array = runner.to_float32_analysis_array(tensor, expected_ndim=1)
    assert array.shape == (3,)
    assert array.dtype == np.float32


def test_to_float32_analysis_array_rejects_nonfinite():
    with pytest.raises(runner.TechnicalInvalidError):
        runner.to_float32_analysis_array(np.array([np.nan], dtype=np.float32))


def test_json_safe_handles_paths_and_nonfinite_floats():
    value = {"path": Path("D:/tmp/file.json"), "nan": np.nan, "list": [np.float32(1.5), np.inf]}
    safe = runner._json_safe(value)
    assert safe["path"] == "D:\\tmp\\file.json" if "\\" in str(Path("D:/tmp/file.json")) else "D:/tmp/file.json"
    assert safe["nan"] is None
    assert safe["list"] == [1.5, None]
    json.dumps(safe, allow_nan=False)


def test_atomic_write_and_exclusive_race(tmp_path):
    path = tmp_path / "artifact.json"
    sha1 = runner._atomic_write_json_exclusive(path, {"ok": True})
    assert path.exists()
    assert len(sha1) == 64
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._atomic_write_json_exclusive(path, {"ok": False})


def test_atomic_write_json(tmp_path):
    path = tmp_path / "plain.json"
    sha = runner._atomic_write_json(path, {"a": [1, 2]})
    assert json.loads(path.read_text(encoding="utf-8")) == {"a": [1, 2]}
    assert len(sha) == 64


def test_extract_block_hidden_state_unwraps_tuple():
    torch = pytest.importorskip("torch")
    tensor = torch.tensor([1.0, 2.0])
    assert runner._extract_block_hidden_state((tensor, None)).equal(tensor)
    with pytest.raises(TypeError):
        runner._extract_block_hidden_state(())


def test_forward_hook_capture():
    torch = pytest.importorskip("torch")
    capture = runner.ForwardHookCapture()
    tensor = torch.tensor([1.0, 2.0])
    capture.record((tensor,))
    assert capture.count == 1
    assert capture.value.equal(tensor)
    with pytest.raises(RuntimeError):
        capture.record((tensor,))


def test_balanced_accuracy_known_answer_and_errors():
    y = list(runner.CLASS_ORDER) * 2
    assert runner.balanced_accuracy(y, y) == 1.0
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.balanced_accuracy(list(runner.CLASS_ORDER[:3]) * 2, list(runner.CLASS_ORDER[:3]) * 2)
    with pytest.raises(ValueError):
        runner.balanced_accuracy(y, y[:-1])


def test_fit_classifier_probability_class_mapping():
    rng = np.random.RandomState(7)
    X = rng.normal(size=(80, 8))
    y = list(runner.CLASS_ORDER) * 20
    model, mapping = runner.fit_classifier(X, y)
    assert mapping == sorted(runner.CLASS_ORDER)
    probs = model.predict_proba(X)
    assert probs.shape == (80, 4)
    assert np.allclose(probs.sum(axis=1), 1.0)


def test_fit_scaler_and_transform_with_stats_known_answer():
    mean = np.array([1.0, -2.0, 0.0, 3.0], dtype=np.float32)
    scale = np.array([2.0, 4.0, 1.0, 5.0], dtype=np.float32)
    X = np.array([[3.0, 2.0, 0.0, 13.0]], dtype=np.float32)
    expected = (X - mean) / scale
    assert np.allclose(runner.transform_with_stats(X, mean, scale), expected, atol=1e-6)


def test_average_rank_and_spearman_rho():
    assert runner.average_rank([3, 1, 2, 2]) == [4.0, 1.0, 2.5, 2.5]
    assert runner.spearman_rho([1, 2, 3], [4, 5, 6]) == pytest.approx(1.0)
    assert runner.spearman_rho([1, 2, 3], [6, 5, 4]) == pytest.approx(-1.0)


def test_normalized_depth():
    assert runner.normalized_depth(0, 4) == 0.0
    assert runner.normalized_depth(3, 4) == 1.0
    with pytest.raises(ValueError):
        runner.normalized_depth(0, 1)


def test_fake_all_layer_extraction():
    torch = pytest.importorskip("torch")
    layers = [
        FakeLayer(torch.tensor([[[float(i), float(i + 1), float(i + 2)]] * 4], dtype=torch.float32))
        for i in range(3)
    ]
    model = FakeModel(layers)
    _, _, matrix = runner.extract_all_layers(FakeTokenizer(), model, torch.device("cpu"), "neutral", 3)
    assert matrix.shape == (3, 3)
    assert matrix.dtype == np.float32
    assert np.isfinite(matrix).all()


def test_matrix_from_observations_and_condition_pool():
    obs = _observations()["A"]
    X, y = runner._matrix_from_observations(obs, 0)
    assert X.shape == (len(obs), 2)
    assert set(y) == set(runner.CLASS_ORDER)
    matrix = np.arange(40, dtype=np.float32).reshape(2, 2, 10)
    assert np.allclose(runner._condition_pool(matrix), matrix.mean(axis=2))


def test_distance_association_sdi_and_localization_primitives():
    num_layers = 4
    eligible = [True, True, True, True]
    dbar = np.array(
        [
            [0.0, 0.2, 0.4, 0.8],
            [0.1, 0.0, 0.3, 0.7],
            [0.3, 0.2, 0.0, 0.5],
            [0.7, 0.5, 0.4, 0.0],
        ],
        dtype=np.float32,
    )
    point = runner._distance_association_point(dbar, eligible, num_layers)
    assert isinstance(point, float)
    sdi = runner._sdi_point(dbar, eligible, num_layers)
    assert "sdi" in sdi and sdi["status"] == "EVALUABLE"
    localization = runner._localization_point(dbar, eligible, num_layers)
    assert 0.0 <= localization["localization"] <= 1.0
    low_mask, pairs = runner._low_d_pair_mask(dbar, eligible, num_layers)
    assert low_mask.shape == (num_layers, num_layers)
    assert all(i != j for i, j in pairs)


def test_compute_matrix_profile_synthetic_shapes_and_diagonal():
    fixtures = _observations()
    profile = runner.compute_matrix_profile(
        fixtures["A"],
        num_layers=4,
        condition_order=runner.CONDITION_ORDER,
        bootstrap_replicates=0,
    )
    assert profile["num_layers"] == 4
    assert profile["c0_eval"].shape == (4, 4, 10)
    assert profile["c0_diag"].shape == (4, 4, 10)
    assert profile["c_cal_eval"].shape == (4, 4, 10)
    assert profile["r_eval"].shape == (4, 4, 10)
    assert np.allclose(np.diagonal(profile["d_eval"][:, :, 0]), 0.0)
    assert any(profile["source_qualification"]["eligible_source_mask"])
    assert "distance_association" in profile["point"]
    assert "sdi" in profile["point"]
    assert "low_d_recovery" in profile["point"]


def test_synthetic_expected_values():
    fixtures = _observations()
    a = runner.compute_matrix_profile(fixtures["A"], num_layers=4, condition_order=runner.CONDITION_ORDER, bootstrap_replicates=0)
    b = runner.compute_matrix_profile(fixtures["B"], num_layers=3, condition_order=runner.CONDITION_ORDER, bootstrap_replicates=0)
    runner._verify_synthetic_expected_values(a, b)


def test_routing_priority_order():
    p1_summary = _summary(distance_support="POSITIVE_SUPPORTED", sdi_class="SOURCE_DOMINANT", low_d_support="SUPPORTED", localization=1.0, boundaries=[0], localization_r=1.0, boundaries_r=[0])
    assert runner.classify_route(
        p1_summary,
        p1_summary,
    )["route"] == "P1"
    assert runner.classify_route(
        _summary(sdi_class="SOURCE_DOMINANT"),
        _summary(sdi_class="TARGET_DOMINANT"),
    )["route"] == "P3"
    assert runner.classify_route(
        _summary(low_d_support="SUPPORTED"),
        _summary(low_d_support="SUPPORTED"),
    )["route"] == "P4"
    assert runner.classify_route(_summary(), _summary())["route"] == "P5"


def test_matrix_serialization_roundtrip():
    matrix = np.arange(18, dtype=np.float32).reshape(3, 3, 2)
    serialized = runner._matrix_serialization(
        matrix,
        source_order=[0, 1, 2],
        target_order=[0, 1, 2],
        condition_order=["a", "b"],
        eligible_source_mask=[True, False, True],
    )
    assert serialized["shape"] == [3, 3, 2]
    assert serialized["dtype"] == "float32"
    restored = np.asarray(serialized["values"], dtype=np.float32)
    assert np.array_equal(restored, matrix)
    json.dumps(serialized, allow_nan=False)


def test_result_schema_rejects_shallow_or_malformed_nested_payload():
    payload = {
        "schema_version": runner.RESULT_SCHEMA_VERSION,
        "classification": "EXP026_SCIENTIFIC_RESULT",
        "experiment": runner.EXPERIMENT,
        "authority_hashes": {}, "model_profiles": {}, "models": {},
    }
    errors = runner.validate_result_schema(payload)
    assert "authority_hashes" in errors
    assert "model_profiles" in errors
    assert "runner_sha256" in errors


def test_result_publication_race(tmp_path):
    path = tmp_path / "result.json"
    payload = {"x": 1}
    sha = runner._publish_result_exclusive(ROOT, path, payload)
    assert len(sha) == 64
    with pytest.raises(runner.ProtocolIntegrityError):
        runner._publish_result_exclusive(ROOT, path, payload)


def test_authorization_consumption_exclusive(tmp_path, monkeypatch):
    auth = {"authorization_id": "AUTH_001"}
    consumption = tmp_path / "consumption"
    record, sha = runner.consume_authorization(ROOT, tmp_path / "auth.json", auth, "a" * 64, run_attempt_id="attempt-1", consumption_dir=consumption)
    assert record["run_attempt_id"] == "attempt-1"
    assert (consumption / "AUTH_001.json").exists()
    assert len(sha) == 64
    with pytest.raises(runner.ProtocolIntegrityError):
        runner.consume_authorization(ROOT, tmp_path / "auth.json", auth, "a" * 64, run_attempt_id="attempt-2", consumption_dir=consumption)


def test_formal_authorization_validation_full_binding(tmp_path, monkeypatch):
    binding = runner.formal_execution_binding(ROOT)
    monkeypatch.setattr(runner, "_qualification_binding", lambda root: {"engineering_qualification": "a" * 64, "formal_pipeline_qualification": "b" * 64})
    auth = {
        "schema_version": "1.0.0",
        "experiment": runner.EXPERIMENT,
        "purpose": "SINGLE_USE_FORMAL_RUN",
        "single_use": True,
        "authorized_execution_count": 1,
        "formal_mode": "--formal-run",
        "execution_binding": binding,
        "qualification_hashes": {"engineering_qualification": "a" * 64, "formal_pipeline_qualification": "b" * 64},
    }
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth), encoding="utf-8")
    validated, auth_sha = runner.validate_formal_authorization(ROOT, path)
    assert validated == auth
    assert auth_sha == runner.sha256_file(path)


def test_formal_authorization_rejects_any_frozen_binding_mismatch(tmp_path, monkeypatch):
    binding = runner.formal_execution_binding(ROOT)
    monkeypatch.setattr(runner, "_qualification_binding", lambda root: {"engineering_qualification": "a" * 64, "formal_pipeline_qualification": "b" * 64})
    auth = {"schema_version": "1.0.0", "experiment": runner.EXPERIMENT, "purpose": "SINGLE_USE_FORMAL_RUN", "single_use": True, "authorized_execution_count": 1, "formal_mode": "--formal-run", "execution_binding": dict(binding), "qualification_hashes": {"engineering_qualification": "a" * 64, "formal_pipeline_qualification": "b" * 64}}
    auth["execution_binding"]["panel_identity_sha256"] = "0" * 64
    path = tmp_path / "auth.json"
    path.write_text(json.dumps(auth), encoding="utf-8")
    with pytest.raises(runner.ProtocolIntegrityError, match="BINDING_MISMATCH"):
        runner.validate_formal_authorization(ROOT, path)


def test_static_preflight():
    result = runner.run_static_preflight(ROOT)
    assert result["status"] == "PASS"
    assert result["frozen_authorities_match"] is True
    assert result["no_formal_result"] is True
    assert result["no_authorization_contamination"] is True


def test_synthetic_formal_qualification_uses_real_executor(tmp_path, monkeypatch):
    # The production synthetic pipeline does not touch real scientific records.
    result = runner.run_synthetic_formal_qualification(ROOT, publish=False)
    assert result["status"] == "PASS"
    assert result["real_executor_connected"] is True
    assert result["formal_data_accessed"] is False
    assert result["scientific_result_created"] is False


def test_engineering_qualification_orchestration(tmp_path, monkeypatch):
    torch = pytest.importorskip("torch")
    monkeypatch.setattr(runner, "MODEL_KEYS", ("A", "B"))
    monkeypatch.setattr(
        runner,
        "MODEL_REGISTRY",
        {
            "A": {"model_id": "fake-A", "model_revision": "rA", "num_hidden_layers": 2, "hidden_size": 3},
            "B": {"model_id": "fake-B", "model_revision": "rB", "num_hidden_layers": 2, "hidden_size": 3},
        },
    )
    monkeypatch.setattr(runner, "ENGINEERING_QUALIFICATION_PATH", tmp_path / "qualification.json")
    monkeypatch.setattr(runner, "load_runtime", lambda key: (None, SimpleNamespace(config=SimpleNamespace(model_type="fake", num_hidden_layers=2, hidden_size=3)), torch.device("cpu"), torch.float32))
    monkeypatch.setattr(runner, "extract_all_layers", lambda tokenizer, model, device, text, num_layers: (None, None, np.zeros((num_layers, 3), dtype=np.float32)))
    result = runner.run_engineering_qualification(ROOT, publish=True)
    assert result["status"] == "PASS"
    assert result["formal_data_accessed"] is False
    assert result["scientific_result_created"] is False
    assert (tmp_path / "qualification.json").exists()


def test_condition_pool_requires_all_ten_frozen_conditions():
    with pytest.raises(runner.ProtocolIntegrityError, match="ALL_FROZEN_CONDITIONS"):
        runner._condition_pool(np.zeros((2, 2, 9), dtype=np.float32))


def test_source_coverage_failure_is_not_evaluable_and_never_routes(monkeypatch):
    fixtures = _observations()["A"]
    monkeypatch.setattr(
        runner,
        "_source_qualification",
        lambda *_args: {"ba_diag_self": [0.0] * 4, "eligible_source_mask": [False] * 4,
                         "eligible_source_count": 0, "eligible_depth_span": 0.0,
                         "source_coverage_evaluable": False},
    )
    profile = runner.compute_matrix_profile(fixtures, num_layers=4, bootstrap_replicates=10)
    assert profile["confirmatory_status"] == "NOT_EVALUABLE_SOURCE_COVERAGE"
    assert set(profile["support"].values()) == {"NOT_EVALUABLE"}
    assert runner.classify_route(profile, profile)["route"] == "NOT_EVALUABLE"


def test_bootstrap_resamples_complete_source_family_clusters(monkeypatch):
    observations = []
    for condition in runner.CONDITION_ORDER:
        for class_index, semantic_class in enumerate(runner.CLASS_ORDER):
            for family in range(2):
                for member in range(2):
                    observations.append(runner.ExtractedObservation(
                        record_id=f"{condition}-{semantic_class}-{family}-{member}", partition="EVAL",
                        condition_id=condition, semantic_class=semantic_class,
                        source_family_id=f"{condition}-{semantic_class}-{family}",
                        vectors=np.full((2, 2), class_index + member / 10, dtype=np.float32),
                    ))
    captured = []
    def fake_c0(sample, *_args):
        captured.append(list(sample))
        return np.zeros((2, 2, 10), dtype=np.float32)
    monkeypatch.setattr(runner, "_compute_c0_for_partition", fake_c0)
    monkeypatch.setattr(runner, "_compute_c_cal_for_partition", lambda *_args: np.zeros((2, 2, 10), dtype=np.float32))
    monkeypatch.setattr(runner, "_summarize_point_profile", lambda *_args: {"distance_association": 0.0, "sdi": {"sdi": 0.0}})
    class IdentityClusterRng:
        def integers(self, low, high, size):
            return np.arange(size, dtype=np.int64)
    runner._bootstrap_model_summaries(
        observations, 2, runner.CONDITION_ORDER, [], {}, [True, True],
        np.zeros((2, 2), dtype=np.float32), np.zeros((2, 2), dtype=bool), 1,
        IdentityClusterRng(),
    )
    sampled = captured[0]
    for family in {item.source_family_id for item in sampled}:
        assert sum(item.source_family_id == family for item in sampled) % 2 == 0


def test_independent_numeric_goldens_detect_sabotaged_condition_pool(monkeypatch):
    monkeypatch.setattr(runner, "_condition_pool", lambda matrix: np.zeros((2, 2), dtype=np.float32))
    with pytest.raises(runner.ProtocolIntegrityError, match="INDEPENDENT_GOLDEN_CONDITION_POOL_FAILED"):
        runner.verify_independent_numeric_goldens()


def test_synthetic_qualification_calls_shared_authorized_executor(monkeypatch):
    original = runner._run_authorized_executor
    calls = []
    def observed_executor(**kwargs):
        calls.append(set(kwargs))
        return original(**kwargs)
    monkeypatch.setattr(runner, "_run_authorized_executor", observed_executor)
    result = runner.run_synthetic_formal_qualification(ROOT, publish=False)
    assert result["shared_authorized_executor"] == "PASS"
    assert calls and {"authorization_validator", "observations_provider", "result_path"} <= calls[0]


def test_matrix_orientation_baseline_sign_and_class_mapping_contract():
    # Hand-specified matrices: C0[source, target, condition], diagonal baseline,
    # and D = Cself - C0.  This is not derived from production output.
    c0 = np.zeros((2, 2, 10), dtype=np.float32)
    c0[0, 0, :] = 0.9
    c0[0, 1, :] = 0.4
    c0[1, 0, :] = 0.3
    c0[1, 1, :] = 0.8
    d = np.zeros_like(c0)
    for source in range(2):
        for target in range(2):
            d[source, target, :] = c0[source, source, :] - c0[source, target, :]
    assert np.allclose(np.diagonal(d[:, :, 0]), 0.0)
    assert np.all(d[0, 1, :] > 0.0)
    assert np.all(d[1, 0, :] > 0.0)
    assert runner.classifier_class_mapping(SimpleNamespace(classes_=np.asarray(sorted(runner.CLASS_ORDER)))) == sorted(runner.CLASS_ORDER)
