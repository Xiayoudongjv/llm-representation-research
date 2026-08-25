import importlib.util
import json


SPEC = importlib.util.spec_from_file_location(
    "extb_v2_validator",
    "experiments/paper_a_ext_b/validate_paper_a_ext_b_construction_v2.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def test_v2_validator_passes_without_production_data():
    assert MODULE.validate() == []


def test_all_conditions_have_closed_synthetic_renderings():
    for task in MODULE.TASKS:
        for condition in MODULE.CONDITIONS:
            reference = MODULE.render_synthetic(task, condition, "reference")
            realization = MODULE.render_synthetic(task, condition, "realization")
            assert "{" not in reference and "}" not in reference
            assert "{" not in realization and "}" not in realization
            assert "xa01" not in reference + realization
            assert "xa01" not in reference + realization
        assert MODULE.render_synthetic(task, "c03_controlled_compression", "reference") != MODULE.render_synthetic(task, "c03_controlled_compression", "realization")


def test_constants_identity_order_and_quantitative_uniqueness():
    assert MODULE.family_id("spatial", ["task", "revision", 1, "left"]) == MODULE.family_id("spatial", ["task", "revision", 1, "left"])
    family = MODULE.family_id("spatial", ["task", "revision", 1, "left"])
    assert MODULE.record_id(family, MODULE.CONDITIONS[0], "reference") != MODULE.record_id(family, MODULE.CONDITIONS[0], "realization")
    assert f"{17:06d}" == "000017"
    assert MODULE.selection_hash(["task", 1]) == MODULE.selection_hash(["task", 1])
    pairs = [(11 + ((i - 1) % 22), 4 - ((i - 1) // 22)) for i in range(1, 221)]
    assert len(set(pairs)) == 220


def test_canonical_json_and_schema_reject_malformed_fixture(tmp_path):
    assert MODULE.canonical_json({"b": 1, "a": 2}) == '{"a":2,"b":1}'
    malformed = tmp_path / "malformed.json"
    malformed.write_text(json.dumps({"required_fields": ["model_output"]}), encoding="utf-8")
    errors = []
    MODULE._validate_schema(malformed, errors)
    assert errors
