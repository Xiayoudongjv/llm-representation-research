import json
import sys
from copy import deepcopy
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


def _synthetic_registry():
    return {
        "A": {"model_id": "synthetic-A", "model_revision": "synthetic", "num_hidden_layers": 4, "hidden_size": 2},
        "B": {"model_id": "synthetic-B", "model_revision": "synthetic", "num_hidden_layers": 3, "hidden_size": 2},
    }


def _valid_synthetic_payload(tmp_path):
    registry = _synthetic_registry()
    result = runner.execute_scientific_executor(
        root=ROOT,
        observations_by_model=runner._hardcoded_synthetic_observations(),
        model_registry=registry,
        result_path=tmp_path / "synthetic_result.json",
        authorization_identity={
            "authorization_id": "TEST_SYNTHETIC_AUTH",
            "authorization_sha256": "a" * 64,
            "consumption_record_sha256": "b" * 64,
            "run_attempt_id": "test-attempt",
            "classification": "SYNTHETIC_QUALIFICATION_AUTHORIZATION",
            "execution_binding": runner._synthetic_execution_binding(ROOT, registry),
            "qualification_hashes": runner._synthetic_qualification_hashes(),
        },
        bootstrap_replicates=20,
    )
    assert runner.validate_synthetic_result_schema(result["payload"]) == []
    return result["payload"]


@pytest.fixture(scope="module")
def valid_synthetic_payload(tmp_path_factory):
    return _valid_synthetic_payload(tmp_path_factory.mktemp("exp026_deep_schema"))


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
    assert runner.MODEL_REGISTRY["Q"]["model_revision"] == "70d244cc86ccca08cf5af4e1e306ecf908b1ad5e"
    assert runner.MODEL_REGISTRY["O"]["model_revision"] == "48d788eca847d4d7548f375ad03d3c9312f6139e"


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
    runner.bind_logical_block_carriers(model, 3)
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
    with pytest.raises(runner.ProtocolIntegrityError, match="INDEPENDENT_GOLDEN_DBAR_FAILED"):
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


@pytest.mark.parametrize(
    ("name", "mutate"),
    [
        ("empty_authorities", lambda p: p.__setitem__("authority_hashes", {})),
        ("empty_provenance", lambda p: p.__setitem__("provenance", {})),
        ("empty_authorization", lambda p: p.__setitem__("authorization_identity", {})),
        ("empty_consumption", lambda p: p["authorization_identity"].__setitem__("consumption_record_sha256", "")),
        ("missing_attempt", lambda p: p["authorization_identity"].pop("run_attempt_id")),
        ("empty_routing", lambda p: p.__setitem__("routing", {})),
        ("wrong_model_revision", lambda p: p["models"]["A"].__setitem__("model_revision", "wrong")),
        ("wrong_layer_count", lambda p: p["models"]["A"].__setitem__("num_hidden_layers", 99)),
        ("wrong_source_order", lambda p: p["model_profiles"]["A"]["matrices"]["c0_eval"].__setitem__("source_layer_order", [1, 0, 2, 3])),
        ("wrong_target_order", lambda p: p["model_profiles"]["A"]["matrices"]["c0_eval"].__setitem__("target_layer_order", [1, 0, 2, 3])),
        ("wrong_condition_order", lambda p: p["model_profiles"]["A"]["matrices"]["c0_eval"].__setitem__("condition_order", list(reversed(runner.CONDITION_ORDER)))),
        ("wrong_matrix_shape", lambda p: p["model_profiles"]["A"]["matrices"]["c0_eval"].__setitem__("shape", [4, 4, 9])),
        ("invalid_eligibility", lambda p: p["model_profiles"]["A"]["matrices"]["c0_eval"].__setitem__("eligible_source_mask", [True])),
        ("invalid_coverage", lambda p: p["model_profiles"]["A"]["source_qualification"].__setitem__("source_coverage_evaluable", "invalid")),
        ("invalid_not_evaluable", lambda p: p["model_profiles"]["A"]["source_qualification"].__setitem__("source_coverage_evaluable", False)),
        ("invalid_technical_validity", lambda p: p["provenance"].__setitem__("technical_validity", {"status": "INVALID"})),
    ],
)
def test_deep_result_schema_rejects_nested_scientific_mutations(valid_synthetic_payload, name, mutate):
    payload = deepcopy(valid_synthetic_payload)
    mutate(payload)
    assert runner.validate_synthetic_result_schema(payload), name


def test_deep_result_schema_rejects_transposed_values_with_stale_metadata(valid_synthetic_payload):
    payload = deepcopy(valid_synthetic_payload)
    matrix = payload["model_profiles"]["A"]["matrices"]["c0_eval"]
    asymmetric = np.asarray(matrix["values"], dtype=np.float32)
    asymmetric[0, 1, :] += 0.125
    matrix["values"] = asymmetric.swapaxes(0, 1).tolist()
    errors = runner.validate_synthetic_result_schema(payload)
    assert "matrix_delta_semantics" in errors


def test_deep_result_schema_roundtrip_preserves_serialized_semantics(valid_synthetic_payload):
    payload = valid_synthetic_payload
    round_tripped = json.loads(json.dumps(payload, sort_keys=True))
    assert runner.validate_synthetic_result_schema(round_tripped) == []


class EncodedPredictionModel:
    def __init__(self, source_column):
        self.source_column = source_column
        self.classes_ = np.asarray(runner.CLASS_ORDER)

    def predict(self, X):
        return [runner.CLASS_ORDER[int(round(row[self.source_column]))] for row in X]


def _encoded_labels(correct_count):
    return [index if index < correct_count else (index + 1) % len(runner.CLASS_ORDER) for index in range(len(runner.CLASS_ORDER))]


def test_asymmetric_production_c0_and_delta_semantics():
    observations = []
    for condition_index, condition in enumerate(runner.CONDITION_ORDER):
        target0_source0 = _encoded_labels(4)
        target1_source0 = _encoded_labels(2 if condition_index % 2 == 0 else 1)
        target0_source1 = _encoded_labels(1 if condition_index % 2 == 0 else 2)
        target1_source1 = _encoded_labels(3)
        for class_index, semantic_class in enumerate(runner.CLASS_ORDER):
            observations.append(runner.ExtractedObservation(
                record_id=f"golden-{condition}-{semantic_class}", partition="EVAL", condition_id=condition,
                semantic_class=semantic_class, source_family_id=f"golden-{condition}-{semantic_class}",
                vectors=np.asarray([
                    [target0_source0[class_index], target0_source1[class_index]],
                    [target1_source0[class_index], target1_source1[class_index]],
                ], dtype=np.float32),
            ))
    c0 = runner._compute_c0_for_partition(observations, "EVAL", 2, runner.CONDITION_ORDER, [EncodedPredictionModel(0), EncodedPredictionModel(1)])
    for index in range(len(runner.CONDITION_ORDER)):
        expected = np.asarray([[1.0, 0.50 if index % 2 == 0 else 0.25], [0.25 if index % 2 == 0 else 0.50, 0.75]], dtype=np.float32)
        assert np.array_equal(c0[:, :, index], expected)
    delta = runner.delta_from_c0(c0)
    assert delta[0, 1, 0] == pytest.approx(0.5)
    assert delta[1, 0, 0] == pytest.approx(0.5)
    assert delta[1, 0, 1] == pytest.approx(0.25)
    assert not np.allclose(c0, c0.swapaxes(0, 1))
    assert not np.allclose(delta, c0 - np.stack([c0[i, i, :] for i in range(2)], axis=0)[:, None, :])


@pytest.mark.parametrize(
    ("attribute", "replacement", "expected_error"),
    [
        ("_compute_c0_for_partition", lambda *_args: np.zeros((2, 2, 10), dtype=np.float32), "INDEPENDENT_GOLDEN_C0_FAILED"),
        ("_compute_c_cal_for_partition", lambda *_args: np.zeros((2, 2, 10), dtype=np.float32), "INDEPENDENT_GOLDEN_CCAL_FAILED"),
        ("delta_from_c0", lambda matrix: np.zeros_like(matrix), "INDEPENDENT_GOLDEN_D_FAILED"),
        ("residual_from_calibration", lambda calibrated, baseline: np.zeros_like(calibrated), "INDEPENDENT_GOLDEN_R_FAILED"),
        ("_condition_pool", lambda matrix: np.zeros((2, 2), dtype=np.float32), "INDEPENDENT_GOLDEN_DBAR_FAILED"),
        ("_distance_association_point", lambda *_args: 0.0, "INDEPENDENT_GOLDEN_DISTANCE_ASSOCIATION_FAILED"),
        ("_sdi_point", lambda *_args: {"source_variance": 0.0, "target_variance": 0.0, "sdi": 0.0}, "INDEPENDENT_GOLDEN_SDI_FAILED"),
        ("_low_d_pair_mask", lambda *_args: (np.zeros((3, 3), dtype=bool), []), "INDEPENDENT_GOLDEN_LOW_D_RECOVERY_FAILED"),
        ("classify_route", lambda *_args: {"route": "P5"}, "INDEPENDENT_GOLDEN_ROUTING_FAILED"),
        ("normalized_depth", lambda index, _layers: float(index), "INDEPENDENT_GOLDEN_NORMALIZED_DEPTH_FAILED"),
    ],
)
def test_independent_numeric_goldens_detect_semantic_sabotage(monkeypatch, attribute, replacement, expected_error):
    monkeypatch.setattr(runner, attribute, replacement)
    with pytest.raises(runner.ProtocolIntegrityError, match=expected_error):
        runner.verify_independent_numeric_goldens()


def test_independent_numeric_goldens_cover_registered_primitives():
    outcome = runner.verify_independent_numeric_goldens()
    assert set(outcome) == {"C0", "D", "CCAL", "R", "DBAR", "RBAR", "DISTANCE_ASSOCIATION", "SDI", "LOW_D_RECOVERY", "ROUTING", "NORMALIZED_DEPTH", "NORMALIZED_PAIR_DISTANCE"}
    assert set(outcome.values()) == {"PASS"}


def test_logical_block_carrier_adversaries_and_ordered_capture():
    torch = pytest.importorskip("torch")
    blocks = [FakeLayer(torch.full((1, 4, 3), float(index))) for index in range(3)]
    model = FakeModel(blocks)
    model.model.embed_tokens = object()
    model.model.norm = object()
    runner.bind_logical_block_carriers(model, 3)
    assert runner.logical_block_carriers(model, 3) == blocks
    _, _, matrix = runner.extract_all_layers(FakeTokenizer(), model, torch.device("cpu"), "neutral", 3)
    assert np.array_equal(matrix[:, 0], np.array([0.0, 1.0, 2.0], dtype=np.float32))
    with pytest.raises(runner.ProtocolIntegrityError, match="COUNT"):
        runner._raw_logical_block_carriers(FakeModel(blocks[:2]), 3)
    with pytest.raises(runner.ProtocolIntegrityError, match="DUPLICATE"):
        runner._raw_logical_block_carriers(FakeModel([blocks[0], blocks[0], blocks[2]]), 3)
    embedding_model = FakeModel([model.model.embed_tokens, blocks[1], blocks[2]])
    embedding_model.model.embed_tokens = model.model.embed_tokens
    with pytest.raises(runner.ProtocolIntegrityError, match="NONBLOCK"):
        runner._raw_logical_block_carriers(embedding_model, 3)
    norm_model = FakeModel([blocks[0], blocks[1], model.model.norm])
    norm_model.model.norm = model.model.norm
    with pytest.raises(runner.ProtocolIntegrityError, match="NONBLOCK"):
        runner._raw_logical_block_carriers(norm_model, 3)
    for invalid in (
        [blocks[2], blocks[1], blocks[0]],
        [blocks[1], blocks[2], blocks[0]],
        [blocks[0], blocks[2], blocks[1]],
        [FakeLayer(torch.zeros((1, 4, 3))) for _ in range(3)],
    ):
        model.model.layers = invalid
        with pytest.raises(runner.ProtocolIntegrityError, match="IDENTITY_OR_ORDER"):
            runner.logical_block_carriers(model, 3)


def test_probability_mapping_uses_noncanonical_classifier_class_order():
    model = SimpleNamespace(classes_=np.asarray(["definition", "logic", "analogy", "causality"]))
    probabilities = np.asarray([[0.10, 0.20, 0.30, 0.40]], dtype=np.float32)
    assert runner.probability_column_index(model, "causality") == 3
    assert runner.probability_for_class(probabilities, model, "causality")[0] == pytest.approx(0.40)
    assert runner.probability_for_class(probabilities, model, "logic")[0] == pytest.approx(0.20)


def test_distance_sdi_and_low_d_adversaries_are_semantic_not_shape_only():
    dbar = np.asarray([[0.0, 1.0, 2.0], [4.0, 0.0, 1.0], [4.0, 3.0, 0.0]], dtype=np.float32)
    assert runner._distance_association_point(dbar, [True, True, True], 3) == pytest.approx(1.5 / np.sqrt(22.0))
    assert runner._distance_association_point(dbar, [True, False, True], 3) != pytest.approx(1.5 / np.sqrt(22.0))
    target_dominant = runner._sdi_point(dbar, [True, True, True], 3)
    assert target_dominant["sdi"] < 0.0
    source_dominant = runner._sdi_point(dbar.T, [True, True, True], 3)
    assert source_dominant["sdi"] > 0.0
    flat = runner._sdi_point(np.zeros((3, 3), dtype=np.float32), [True, True, True], 3)
    assert flat["status"] == "NO_ROW_OR_COLUMN_VARIATION" and flat["sdi"] == 0.0
    diag = np.asarray([[0.0, -1.0, 0.5], [-0.1, 0.0, 1.0], [0.2, -0.5, 0.0]], dtype=np.float32)
    rbar = np.asarray([[0.0, 0.25, 99.0], [0.0, 0.0, 0.0], [0.0, -0.50, 0.0]], dtype=np.float32)
    before = runner._summarize_point_profile(dbar, rbar, [True, False, True], 3, diag)["low_d_recovery"]
    rbar[0, 2] = -999.0
    after = runner._summarize_point_profile(dbar, rbar, [True, False, True], 3, diag)["low_d_recovery"]
    assert before["pairs"] == after["pairs"] == [(0, 1), (2, 1)]
    assert before["mean_recovery"] == after["mean_recovery"]


def test_publication_race_preserves_preexisting_bytes(tmp_path, monkeypatch):
    path = tmp_path / "race.json"
    original_open = runner.os.open
    original_bytes = b'{"preexisting":"race"}\n'

    def race_open(name, flags, mode):
        Path(name).write_bytes(original_bytes)
        return original_open(name, flags, mode)

    monkeypatch.setattr(runner.os, "open", race_open)
    with pytest.raises(runner.ProtocolIntegrityError, match="PATH_ALREADY_EXISTS"):
        runner._publish_result_exclusive(ROOT, path, {"new": "payload"})
    assert path.read_bytes() == original_bytes


def test_cross_object_schema_rejects_coherent_transpose_with_stale_axis_binding(valid_synthetic_payload):
    payload = deepcopy(valid_synthetic_payload)
    for profile in payload["model_profiles"].values():
        matrix = profile["matrices"]["dbar_diag"]
        values = np.asarray(matrix["values"], dtype=np.float32)
        values[0, 1] = 0.375
        matrix["values"] = values.tolist()
        matrix["axis_binding"] = runner._matrix_axis_binding(values, list(range(values.shape[0])), list(range(values.shape[1])))
    for profile in payload["model_profiles"].values():
        for matrix in profile["matrices"].values():
            matrix["values"] = np.asarray(matrix["values"], dtype=np.float32).swapaxes(0, 1).tolist()
    errors = runner.validate_synthetic_result_schema(payload)
    assert any(error.endswith("_axis_binding") for error in errors)


@pytest.mark.parametrize(
    ("matrix_name", "expected_error"),
    [("d_eval", "matrix_delta_semantics"), ("r_eval", "matrix_residual_semantics"),
     ("dbar_eval", "matrix_dbar_semantics"), ("rbar_eval", "matrix_rbar_semantics")],
)
def test_cross_object_schema_rejects_matrix_relation_mutations(valid_synthetic_payload, matrix_name, expected_error):
    payload = deepcopy(valid_synthetic_payload)
    matrix = payload["model_profiles"]["A"]["matrices"][matrix_name]
    values = np.asarray(matrix["values"], dtype=np.float32)
    values.flat[0] += 0.25
    matrix["values"] = values.tolist()
    matrix["axis_binding"] = runner._matrix_axis_binding(values, list(range(values.shape[0])), list(range(values.shape[1])))
    assert expected_error in runner.validate_synthetic_result_schema(payload)


def test_cross_object_schema_rejects_coverage_and_eligibility_contradictions(valid_synthetic_payload):
    payload = deepcopy(valid_synthetic_payload)
    payload["model_profiles"]["A"]["confirmatory_status"] = "NOT_EVALUABLE_SOURCE_COVERAGE"
    assert "coverage_evaluable_status" in runner.validate_synthetic_result_schema(payload)
    payload = deepcopy(valid_synthetic_payload)
    payload["model_profiles"]["A"]["source_qualification"]["eligible_source_count"] = 0
    assert "source_qualification_count_mismatch" in runner.validate_synthetic_result_schema(payload)
    payload = deepcopy(valid_synthetic_payload)
    payload["model_profiles"]["A"]["source_qualification"]["eligible_depth_span"] = 0.0
    assert "source_qualification_span_mismatch" in runner.validate_synthetic_result_schema(payload)


def test_cross_object_schema_rejects_routing_endpoint_contradiction():
    summary = _summary()
    summary["source_qualification"] = {"source_coverage_evaluable": True}
    profiles = {"Q": deepcopy(summary), "O": deepcopy(summary)}
    routing = runner.classify_route(profiles["Q"], profiles["O"])
    profiles["Q"]["support"]["sdi_class"] = "SOURCE_DOMINANT"
    errors = []
    runner._validate_routing_against_profiles(routing, profiles, errors)
    assert errors == ["routing_profile_mismatch"]


def test_production_ccal_golden_and_r_integration():
    runner._verify_production_ccal_golden()


def test_normalized_depth_vector_and_pair_distance_goldens():
    assert [runner.normalized_depth(index, 4) for index in range(4)] == pytest.approx([0.0, 1 / 3, 2 / 3, 1.0])
    assert runner.normalized_pair_distance(0, 1, 4) == 1 / 3
    assert runner.normalized_pair_distance(0, 3, 4) == 1.0
    assert runner.normalized_pair_distance(1, 3, 4) == 2 / 3


def _distance_fixture_values():
    matrix = np.asarray(
        [[0.0, 1.0, 2.0, 3.0], [4.0, 0.0, 2.0, 1.0],
         [3.0, 2.0, 0.0, 4.0], [1.0, 3.0, 4.0, 0.0]],
        dtype=np.float32,
    )
    return [float(matrix[i, j]) for i in range(4) for j in range(4) if i != j], matrix


def _production_distances(num_layers):
    return {
        gap: [
            runner.normalized_pair_distance(i, j, num_layers)
            for i in range(num_layers) for j in range(num_layers)
            if i != j and abs(i - j) == gap
        ]
        for gap in range(1, num_layers)
    }


def test_normalized_distance_l4_tie_test():
    groups = _production_distances(4)
    assert all(len(set(values)) == 1 for values in groups.values())
    assert groups[1][0] == 1 / 3
    assert groups[2][0] == 2 / 3
    assert groups[3][0] == 1.0


def test_normalized_distance_l16_tie_test():
    groups = _production_distances(16)
    assert all(len(set(values)) == 1 for values in groups.values())
    assert len({values[0] for values in groups.values()}) == 15


def test_normalized_distance_l28_tie_test():
    groups = _production_distances(28)
    assert all(len(set(values)) == 1 for values in groups.values())
    assert len({values[0] for values in groups.values()}) == 27


def test_normalized_distance_symmetry_test():
    for num_layers in (4, 16, 28):
        for i in range(num_layers):
            for j in range(num_layers):
                assert runner.normalized_pair_distance(i, j, num_layers) == runner.normalized_pair_distance(j, i, num_layers)


def test_normalized_distance_boundary_test():
    for num_layers in (4, 16, 28):
        assert all(runner.normalized_pair_distance(i, i, num_layers) == 0.0 for i in range(num_layers))
        assert runner.normalized_pair_distance(0, num_layers - 1, num_layers) == 1.0


def test_distance_rank_class_golden():
    expected_ranks = [3.5, 8.5, 11.5, 3.5, 3.5, 8.5, 8.5, 3.5, 3.5, 11.5, 8.5, 3.5]
    distances = [runner.normalized_pair_distance(i, j, 4) for i in range(4) for j in range(4) if i != j]
    assert runner.average_rank(distances) == expected_ranks


def test_distance_rho_tie_golden():
    _values, matrix = _distance_fixture_values()
    assert runner._distance_association_point(matrix, [True] * 4, 4) == -0.30641293851417056


def test_old_float_subtraction_sabotage():
    expected_ranks = [3.5, 8.5, 11.5, 3.5, 3.5, 8.5, 8.5, 3.5, 3.5, 11.5, 8.5, 3.5]
    values, _matrix = _distance_fixture_values()
    old_distances = [abs(i / 3.0 - j / 3.0) for i in range(4) for j in range(4) if i != j]
    assert runner.average_rank(old_distances) != expected_ranks
    assert runner.spearman_rho(old_distances, values) != -0.30641293851417056


def test_raw_index_distance_semantic_sabotage():
    normalized = [runner.normalized_pair_distance(i, j, 4) for i in range(4) for j in range(4) if i != j]
    raw = [float(abs(i - j)) for i in range(4) for j in range(4) if i != j]
    assert raw != normalized
    assert normalized[0] == 1 / 3
    assert raw[0] == 1.0


def test_coverage_failure_profile_serialization_validation_roundtrip(monkeypatch):
    monkeypatch.setattr(
        runner, "_source_qualification",
        lambda _obs, layers, _models, _conditions: {
            "ba_diag_self": [0.0] * layers, "eligible_source_mask": [False] * layers,
            "eligible_source_count": 0, "eligible_depth_span": 0.0,
            "source_coverage_evaluable": False,
        },
    )
    observations = runner._hardcoded_synthetic_observations()
    profiles = {key: runner.compute_matrix_profile(rows, num_layers=(4 if key == "A" else 3), bootstrap_replicates=20) for key, rows in observations.items()}
    registry = _synthetic_registry()
    auth = {
        "authorization_id": "COVERAGE_FAILURE_FIXTURE", "authorization_sha256": "a" * 64,
        "consumption_record_sha256": "b" * 64, "run_attempt_id": "coverage-failure",
        "classification": "SYNTHETIC_QUALIFICATION_AUTHORIZATION",
        "execution_binding": runner._synthetic_execution_binding(ROOT, registry),
        "qualification_hashes": runner._synthetic_qualification_hashes(),
    }
    payload = runner.build_result_payload(
        model_profiles=profiles,
        routing={"route": "SYNTHETIC_NOT_ROUTED", "trigger_state": "SYNTHETIC_QUALIFICATION", "endpoint_evaluability": "SYNTHETIC_NOT_ROUTED", "conflict_resolution": "NOT_APPLICABLE"},
        authorities=runner.verify_frozen_design(ROOT), repository_commit=runner._repository_commit(ROOT),
        runner_sha256=runner.sha256_file(Path(runner.__file__)), authorization_identity=auth,
        model_registry=registry,
    )
    assert all(profile["confirmatory_status"] == "NOT_EVALUABLE_SOURCE_COVERAGE" for profile in payload["model_profiles"].values())
    assert runner.validate_synthetic_result_schema(payload) == []
    broken = deepcopy(payload)
    broken["model_profiles"]["A"].pop("confirmatory_status")
    assert runner.validate_synthetic_result_schema(broken)
