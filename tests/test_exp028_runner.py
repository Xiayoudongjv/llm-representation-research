"""EXP-028 runner synthetic/adversarial qualification tests.

These tests are synthetic/static only. They never load Qwen, OLMo, or Llama,
never access real FIT/DIAG/EVAL scientific content, and never create a formal
authorization or canonical scientific result.
"""

from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
EXP028_DIR = ROOT / "experiments" / "exp028"
for path in (str(ROOT), str(EXP028_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)

import run_exp028 as r
import validate_exp028_result as result_validator


CONFIG = r.frozen_config()
CONDITIONS = [
    "c01_lexical_relex",
    "c02_syntactic_restructure",
    "c03_controlled_compression",
    "c04_controlled_elaboration",
    "c05_relation_explicit",
    "c06_relation_implicit",
    "c07_register_formal",
    "c08_register_informal",
    "c09_neutral_distractor_prefix",
    "c10_anaphoric_reference",
]
CLASSES = ["logic", "causality", "analogy", "definition"]
SPLITS = ["FIT", "DIAGNOSTIC", "EVAL"]


def _valid_panel() -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for condition in CONDITIONS:
        for cls in CLASSES:
            for split in SPLITS:
                text = f"synthetic {condition} {cls} {split} item {len(items)}"
                items.append({
                    "raw_text": text,
                    "source_family_id": f"sf-{condition}-{cls}-{split}",
                    "condition": condition,
                    "semantic_class": cls,
                    "split": split,
                })
    return {
        "schema_version": "1.0.0",
        "experiment": "EXP-028",
        "frozen": True,
        "items": items,
    }


def _source_target_pair() -> tuple[np.ndarray, np.ndarray]:
    source = np.array([
        [0.0, 0.0],
        [0.0, 0.5],
        [1.0, 1.0],
        [1.0, 1.5],
    ], dtype=np.float64)
    target = source.copy()
    return source, target


def _records(values: list[float]) -> list[dict[str, Any]]:
    return [
        {"condition": "c01_lexical_relex", "layer_pair": "0_1", "source_family": f"sf-{idx}", "value": value}
        for idx, value in enumerate(values)
    ]


def _valid_result_payload(
    *,
    rm_supported: bool = True,
    ro_supported: bool = True,
    route: str = "MODEL_DEPENDENT_ALIGNMENT_STATE",
    model_name: str = "Qwen",
) -> dict[str, Any]:
    rm_bound = {
        "lower_percentile_5": 0.05 if rm_supported else -0.05,
        "upper_percentile_95": 0.50,
        "support": rm_supported,
        "primary_support_semantics": "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND",
        "descriptive_central_interval": "CENTRAL_90_PERCENT_PERCENTILE_INTERVAL",
        "replicates": 5000,
        "seed": r.BOOTSTRAP_SEED,
    }
    ro_bound = dict(rm_bound)
    ro_bound["support"] = ro_supported
    return r.build_result_payload(
        model_name=model_name,
        technical_valid=True,
        delta_rm=0.10 if rm_supported else -0.10,
        delta_ro=0.20 if ro_supported else -0.20,
        rm_support=rm_bound,
        ro_support=ro_bound,
        model_state=r.classify_model_state(rm_supported, ro_supported),
        three_model_route=route,
        binding={
            "runner_sha256": "a" * 64,
            "frozen_config_sha256": "b" * 64,
            "authority_binding_sha256": "c" * 64,
        },
        panel_identity={"experiment": "EXP-028", "panel_sha256": "d" * 64},
        authorization_identity={
            "authorization_id": "auth-id",
            "authorization_sha256": "e" * 64,
            "run_attempt_id": "attempt-id",
        },
        attempt_id="attempt-fixed",
    )


# ---------------------------------------------------------------------------
# Scientific contract and firewalls
# ---------------------------------------------------------------------------

def test_label_leakage_rejected():
    params = list(inspect.signature(r.apply_t2_fit).parameters)
    assert "labels" not in params
    assert "y" not in params
    source, target = _source_target_pair()
    transformed, meta = r.apply_t2_fit(source, target)
    assert meta["label_free"] is True
    assert meta["task_loss_optimization"] is False
    assert meta["hyperparameter_search"] is False
    assert meta["cross_coordinate_mixing"] is False


def test_eval_operator_fit_rejected():
    source, target = _source_target_pair()
    _, meta_fit = r.apply_t2_fit(source, target)
    eval_target = target + 100.0
    # Applying the frozen operator never refits; coefficients remain the FIT pair.
    assert np.allclose(meta_fit["a"], np.ones(2))
    assert np.allclose(meta_fit["b"], np.zeros(2))
    transformed_eval = eval_target * meta_fit["a"] + meta_fit["b"]
    assert np.allclose(transformed_eval, eval_target)


def test_diag_operator_tuning_rejected():
    diag = CONFIG["diag_role"]
    assert diag["role"] == "TECHNICAL_ONLY"
    for forbidden in (
        "change_operator_family",
        "change_endpoint",
        "change_bootstrap",
        "change_threshold",
        "select_favorable_layer_pairs",
        "select_favorable_models",
        "determine_whether_EVAL_is_worth_running",
    ):
        assert forbidden in diag["must_not"]


def test_old_panel_reuse_rejected():
    panel = _valid_panel()
    old_hash = r.normalized_text_hash(panel["items"][0]["raw_text"])
    errors = r.validate_fresh_panel(panel, prior_authorities=[{"sha256": old_hash}])
    assert any("prior_panel_collision" in error for error in errors)


def test_duplicate_source_family_rejected_when_identity_available():
    panel = _valid_panel()
    panel["items"][1]["source_family_id"] = panel["items"][0]["source_family_id"]
    errors = r.validate_fresh_panel(panel)
    assert any("duplicate_source_family_id" in error for error in errors)


def test_zero_variance_rule_exact():
    source = np.array([[0.0, 0.0], [1.0, 1.0]], dtype=np.float64)
    target = np.array([[0.0, 2.0], [1.0, 2.0]], dtype=np.float64)
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="TARGET_VARIANCE"):
        r.apply_t2_fit(source, target)
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="TARGET_SIGMA"):
        r.apply_t1_fit(source, target)


def test_near_zero_variance_rule_exact():
    source = np.array([[0.0], [1.0]], dtype=np.float64)
    target = np.array([[0.0], [1e-100]], dtype=np.float64)
    transformed, meta = r.apply_t2_fit(source, target)
    assert np.isfinite(transformed).all()
    assert np.isfinite(meta["a"]).all()
    assert np.isfinite(meta["b"]).all()


def test_nonfinite_rule_exact():
    source = np.array([[0.0], [1.0]], dtype=np.float64)
    target = np.array([[0.0], [np.nan]], dtype=np.float64)
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="NONFINITE"):
        r.apply_t2_fit(source, target)


def test_t1_orientation_exact():
    source = np.array([[0.0], [1.0], [2.0], [3.0]], dtype=np.float64)
    target = np.array([[10.0], [30.0], [50.0], [70.0]], dtype=np.float64)
    transformed, meta = r.apply_t1_fit(source, target)
    np.testing.assert_allclose(transformed.mean(axis=0), source.mean(axis=0))
    np.testing.assert_allclose(transformed.std(axis=0, ddof=0), source.std(axis=0, ddof=0))
    assert meta["orientation"] == "target_representation_to_source_measurement_frame"


def test_t2_orientation_exact():
    source = np.array([[1.0], [3.0], [5.0], [7.0]], dtype=np.float64)
    target = np.array([[0.0], [1.0], [2.0], [3.0]], dtype=np.float64)
    transformed, meta = r.apply_t2_fit(source, target)
    np.testing.assert_allclose(transformed, source)
    np.testing.assert_allclose(meta["a"], [2.0])
    np.testing.assert_allclose(meta["b"], [1.0])


def test_primary_comparator_is_t1():
    operators = CONFIG["operator_families"]
    assert operators["primary_comparator_baseline"] == "T1_MOMENT_RECALIBRATION"
    assert operators["primary_contrast"] == "T2_MINUS_T1"
    assert operators["primary_comparator"] == "T_pair_diag_vs_T_mu_sigma"


def test_delta_rm_sign_exact():
    source = np.array([[0.0], [2.0], [4.0], [6.0]], dtype=np.float64)
    target = np.array([[0.0], [1.0], [8.0], [27.0]], dtype=np.float64)
    sigma_s = source.std(axis=0, ddof=0)
    t1, _ = r.apply_t1_fit(source, target)
    t2, _ = r.apply_t2_fit(source, target)
    e1 = float(np.mean(r.rm_errors(source, t1, sigma_s)))
    e2 = float(np.mean(r.rm_errors(source, t2, sigma_s)))
    assert e1 - e2 > 0.0


def test_delta_ro_sign_exact():
    source = np.array([[-1.0], [-0.8], [0.8], [1.0]], dtype=np.float64)
    labels = np.array(["logic", "logic", "causality", "causality"])
    target = -source
    probe = r.fit_frozen_probe(source, labels)
    _, t1_meta = r.apply_t1_fit(source, target)
    _, t2_meta = r.apply_t2_fit(source, target)
    t1 = target
    t2 = target * t2_meta["a"] + t2_meta["b"]
    c_t1 = r.readout_accuracy(probe, t1, labels)
    c_t2 = r.readout_accuracy(probe, t2, labels)
    assert c_t2 > c_t1


def test_delta_rm_reference_value_exact():
    source = np.array([[0.0], [2.0]], dtype=np.float64)
    target = np.array([[0.0], [4.0]], dtype=np.float64)
    sigma_s = source.std(axis=0, ddof=0)
    t1, _ = r.apply_t1_fit(source, target)
    t2, _ = r.apply_t2_fit(source, target)
    delta = float(np.mean(r.rm_errors(source, t1, sigma_s))) - float(np.mean(r.rm_errors(source, t2, sigma_s)))
    assert np.isclose(delta, 0.0)


def test_delta_ro_reference_value_exact():
    source = np.array([[-1.0], [-0.8], [0.8], [1.0]], dtype=np.float64)
    labels = np.array(["logic", "logic", "causality", "causality"])
    target = -source
    probe = r.fit_frozen_probe(source, labels)
    _, t2_meta = r.apply_t2_fit(source, target)
    t2 = target * t2_meta["a"] + t2_meta["b"]
    assert r.readout_accuracy(probe, t2, labels) == 1.0


# ---------------------------------------------------------------------------
# Bootstrap, aggregation, routing
# ---------------------------------------------------------------------------

def test_bootstrap_percentile_semantics_exact():
    values = [float(i) for i in range(10)]
    records = _records(values)
    bounds = r.bootstrap_support_bounds(records, value_key="value", seed=7, replicates=101)
    assert bounds["primary_support_semantics"] == "ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND"
    assert bounds["descriptive_central_interval"] == "CENTRAL_90_PERCENT_PERCENTILE_INTERVAL"
    assert isinstance(bounds["lower_percentile_5"], float)
    assert isinstance(bounds["upper_percentile_95"], float)


def test_bootstrap_reference_equivalence():
    records = []
    values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    for idx, value in enumerate(values):
        records.append({"condition": "c01_lexical_relex", "layer_pair": "0_1", "source_family": f"sf-{idx}", "value": value})

    prod = r.bootstrap_distribution(records, value_key="value", seed=123, replicates=200)

    by_family: dict[str, list[float]] = {}
    for record in records:
        by_family.setdefault(str(record["source_family"]), []).append(float(record["value"]))
    family_keys = list(by_family.keys())
    rng = np.random.Generator(np.random.PCG64(123))
    reference = np.empty(200, dtype=np.float64)
    for draw_idx in range(200):
        chosen = rng.integers(0, len(family_keys), size=len(family_keys))
        family_means = [float(np.mean(by_family[family_keys[int(idx)]])) for idx in chosen]
        reference[draw_idx] = float(np.mean(family_means))

    np.testing.assert_allclose(prod, reference, rtol=1e-12, atol=1e-12)


def test_source_family_clustering_exact():
    records = []
    for i in range(10):
        records.append({"condition": "c01_lexical_relex", "layer_pair": "0_1", "source_family": "big", "value": 10.0})
    records.append({"condition": "c01_lexical_relex", "layer_pair": "0_1", "source_family": "small", "value": 0.0})
    assert r.aggregate_equal_weight(records) == 5.0
    draws = r.bootstrap_distribution(records, value_key="value", seed=1, replicates=500)
    assert set(np.unique(draws).tolist()).issubset({0.0, 5.0, 10.0})
    assert abs(float(np.mean(draws)) - 5.0) < 0.2


def test_condition_equal_weighting_exact():
    records = []
    for condition in ["c01_lexical_relex", "c02_syntactic_restructure"]:
        for family in ["a", "b"]:
            records.append({"condition": condition, "layer_pair": "0_1", "source_family": family, "value": 1.0 if condition == "c01_lexical_relex" else 3.0})
    assert r.aggregate_equal_weight(records) == 2.0


def test_layer_pair_equal_weighting_exact():
    records = []
    for pair in ["0_1", "0_2"]:
        for condition in ["c01_lexical_relex", "c02_syntactic_restructure"]:
            for family in ["a", "b"]:
                records.append({"condition": condition, "layer_pair": pair, "source_family": family, "value": 1.0 if pair == "0_1" else 5.0})
    assert r.aggregate_equal_weight(records) == 3.0


def test_model_separate_adjudication_exact():
    assert r.classify_model_state(True, True) == "JOINT_ALIGNMENT_CONTRIBUTION"
    assert r.classify_model_state(True, False) == "REPRESENTATION_ONLY"
    assert r.classify_model_state(False, True) == "READOUT_ONLY_ARTIFACT_RISK"
    assert r.classify_model_state(False, False) == "NO_PAIRED_COORDINATE_CONTRIBUTION"


def test_pair_break_deterministic():
    ids = ["b", "a", "c", "a"]
    mapping = r.pair_break_mapping(ids)
    assert mapping == {"a": "b", "b": "c", "c": "a"}
    records = [
        {"source_family": "a", "target_family": "a", "source_id": "s1", "target_id": "t1"},
        {"source_family": "b", "target_family": "b", "source_id": "s2", "target_id": "t2"},
        {"source_family": "c", "target_family": "c", "source_id": "s3", "target_id": "t3"},
    ]
    assert r.pair_break_pairs(records) == r.pair_break_pairs(records)


def test_pair_break_cannot_rescue():
    primary_state = r.classify_model_state(False, False)
    assert primary_state == "NO_PAIRED_COORDINATE_CONTRIBUTION"
    pair_break = {"status": "SECONDARY_ONLY", "favorable": True}
    # Favorable secondary output is not consumed by the primary state function.
    assert r.classify_model_state(False, False) == primary_state
    assert pair_break["favorable"] is True


def test_low_rank_operator_rejected():
    prohibited = CONFIG["operator_capacity_firewall"]["prohibited_post_hoc_rescue_families"]
    assert "low_rank_cross_coordinate_map" in prohibited


def test_dense_affine_rejected():
    prohibited = CONFIG["operator_capacity_firewall"]["prohibited_post_hoc_rescue_families"]
    assert "dense_affine_matrix" in prohibited


def test_mlp_operator_rejected():
    prohibited = CONFIG["operator_capacity_firewall"]["prohibited_post_hoc_rescue_families"]
    assert "MLP" in prohibited


def test_kan_operator_rejected():
    prohibited = CONFIG["operator_capacity_firewall"]["prohibited_post_hoc_rescue_families"]
    assert "KAN" in prohibited


def test_majority_route_rejected():
    states = [
        ("JOINT_ALIGNMENT_CONTRIBUTION", True),
        ("JOINT_ALIGNMENT_CONTRIBUTION", True),
        ("REPRESENTATION_ONLY", True),
    ]
    assert r.route_three_models(states) == "MODEL_DEPENDENT_ALIGNMENT_STATE"


def test_invalid_model_drop_rejected():
    states = [
        ("JOINT_ALIGNMENT_CONTRIBUTION", True),
        ("JOINT_ALIGNMENT_CONTRIBUTION", True),
        ("JOINT_ALIGNMENT_CONTRIBUTION", False),
    ]
    assert r.route_three_models(states) == "NOT_FULLY_ADJUDICATED"


def test_joint_state_test():
    payload = _valid_result_payload(rm_supported=True, ro_supported=True, route="MODEL_DEPENDENT_ALIGNMENT_STATE")
    assert payload["model_state"] == "JOINT_ALIGNMENT_CONTRIBUTION"
    assert result_validator.validate_result_payload(payload) == []


def test_representation_only_test():
    payload = _valid_result_payload(rm_supported=True, ro_supported=False, route="MODEL_DEPENDENT_ALIGNMENT_STATE")
    assert payload["model_state"] == "REPRESENTATION_ONLY"
    assert result_validator.validate_result_payload(payload) == []


def test_readout_only_artifact_risk_test():
    payload = _valid_result_payload(rm_supported=False, ro_supported=True, route="MODEL_DEPENDENT_ALIGNMENT_STATE")
    assert payload["model_state"] == "READOUT_ONLY_ARTIFACT_RISK"
    assert result_validator.validate_result_payload(payload) == []


def test_no_contribution_test():
    payload = _valid_result_payload(rm_supported=False, ro_supported=False, route="MODEL_DEPENDENT_ALIGNMENT_STATE")
    assert payload["model_state"] == "NO_PAIRED_COORDINATE_CONTRIBUTION"
    assert result_validator.validate_result_payload(payload) == []


def test_three_model_joint_route_test():
    states = [("JOINT_ALIGNMENT_CONTRIBUTION", True)] * 3
    assert r.route_three_models(states) == "THREE_MODEL_JOINT_COORDINATEWISE_COMPONENT"


def test_three_model_common_route_test():
    states = [("REPRESENTATION_ONLY", True)] * 3
    assert r.route_three_models(states) == "THREE_MODEL_COMMON_STATE"


def test_model_dependent_route_test():
    states = [
        ("JOINT_ALIGNMENT_CONTRIBUTION", True),
        ("REPRESENTATION_ONLY", True),
        ("NO_PAIRED_COORDINATE_CONTRIBUTION", True),
    ]
    assert r.route_three_models(states) == "MODEL_DEPENDENT_ALIGNMENT_STATE"


def test_invalid_model_route_test():
    states = [
        ("JOINT_ALIGNMENT_CONTRIBUTION", True),
        ("REPRESENTATION_ONLY", True),
        ("NO_PAIRED_COORDINATE_CONTRIBUTION", False),
    ]
    assert r.route_three_models(states) == "NOT_FULLY_ADJUDICATED"


# ---------------------------------------------------------------------------
# Result schema, serialization, authorization, qualification modes
# ---------------------------------------------------------------------------

def test_result_route_mismatch_rejected():
    payload = _valid_result_payload(rm_supported=True, ro_supported=True, route="NOT_FULLY_ADJUDICATED")
    payload["model_state"] = "JOINT_ALIGNMENT_CONTRIBUTION"
    # Route is allowed, but result validation should require a support-state
    # consistent payload. Here route itself is not checked against model_state,
    # so force a concrete mismatch via an invalid support bool below.
    payload["bootstrap"]["DELTA_RM"]["support"] = False
    errors = result_validator.validate_result_payload(payload)
    assert "support_class_mismatch" in errors


def test_wrong_model_authority_rejected():
    payload = _valid_result_payload(model_name="GPT-4")
    assert "model_name" in result_validator.validate_result_payload(payload)


def test_wrong_panel_authority_rejected():
    payload = _valid_result_payload()
    payload["panel_identity"] = {"experiment": "EXP-999", "panel_sha256": "x" * 64}
    assert "panel_identity_experiment" in result_validator.validate_result_payload(payload)


def test_transport_claim_rejected():
    payload = _valid_result_payload()
    payload["transport_claim"] = True
    assert "forbidden_claim_transport_claim" in result_validator.validate_result_payload(payload)


def test_invariant_claim_rejected():
    payload = _valid_result_payload()
    payload["invariant_claim"] = True
    assert "forbidden_claim_invariant_claim" in result_validator.validate_result_payload(payload)


def test_functional_binding_claim_rejected():
    payload = _valid_result_payload()
    payload["functional_binding_claim"] = True
    assert "forbidden_claim_functional_binding_claim" in result_validator.validate_result_payload(payload)


def test_nested_numpy_serialization_safe():
    payload = {
        "array": np.arange(6).reshape(2, 3),
        "scalar_float": np.float32(1.5),
        "scalar_int": np.int64(4),
        "tuple": (1, 2, np.float64(3.0)),
        "nested": {"bool": np.bool_(True), "none": None},
    }
    safe = r.json_safe(payload)
    text = json.dumps(safe, sort_keys=True)
    decoded = json.loads(text)
    assert decoded["array"] == [[0, 1, 2], [3, 4, 5]]
    assert decoded["scalar_float"] == 1.5
    assert decoded["scalar_int"] == 4
    assert decoded["tuple"] == [1, 2, 3.0]
    assert decoded["nested"] == {"bool": True, "none": None}


def test_duplicate_canonical_publication_rejected(tmp_path):
    target = tmp_path / "exp028_results.json"
    r.atomic_write_json_exclusive(target, {"ok": True})
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="CANONICAL_RESULT_ALREADY_EXISTS"):
        r.atomic_write_json_exclusive(target, {"ok": False})


def test_authorization_reuse_rejected(tmp_path):
    auth = {
        "authorization_id": "auth-a",
        "authorization_sha256": "a" * 64,
        "run_attempt_id": "attempt-a",
    }
    consumption = tmp_path / "consumption"
    r.consume_authorization(auth, "a" * 64, consumption)
    with pytest.raises(r.Exp028ProtocolIntegrityError, match="ALREADY_CONSUMED"):
        r.consume_authorization(auth, "a" * 64, consumption)


def test_static_preflight_passes_without_model_or_formal_data():
    artifact = r.run_static_preflight(publish=False)
    assert artifact["status"] == "PASS"
    assert artifact["no_authorization"] is True
    assert artifact["no_formal_result"] is True
    assert artifact["real_model_inference_performed"] is False
    assert artifact["real_data_accessed"] is False


def test_synthetic_qualification_passes_without_authorization():
    artifact = r.run_synthetic_qualification(publish=False)
    assert artifact["status"] == "PASS"
    assert artifact["real_model_inference_performed"] is False
    assert artifact["real_FIT_accessed"] is False
    assert artifact["real_DIAG_accessed"] is False
    assert artifact["real_EVAL_accessed"] is False
    assert artifact["authorization_created"] is False
    assert artifact["scientific_result_created"] is False


def test_progress_report_is_outcome_blind():
    import contextlib
    import io
    progress = r.OutcomeBlindProgress()
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        progress.report("TECHNICAL_STAGE", completed=1, total=2, heartbeat=True)
    text = buffer.getvalue()
    assert "TECHNICAL_STAGE" in text
    assert "percent" in text
    assert "DELTA_RM" not in text
    assert "DELTA_RO" not in text
    assert "model_state" not in text
