from experiments.paper_a_ext_b.validate_paper_a_ext_b_construction_spec_v1 import (
    CONDITIONS,
    canonical_string,
    family_id,
    record_id,
    validate_spec,
)


def test_static_construction_spec_passes_without_data_generation():
    assert validate_spec() == []


def test_identity_normalization_is_deterministic():
    assert canonical_string("  A\u00a0B  ") == "a b"
    family = family_id("quantitative", ["task", "c01", 1])
    assert family == family_id("quantitative", ["task", "c01", 1])
    assert record_id(family, CONDITIONS[0], "reference") != record_id(family, CONDITIONS[0], "realization")
