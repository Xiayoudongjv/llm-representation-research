from __future__ import annotations

import importlib.util
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "experiments" / "paper_a_ext_b" / "build_paper_a_ext_b_dataset_v2.py"
SPEC = importlib.util.spec_from_file_location("extb_v2_builder_recovery", MODULE_PATH)
assert SPEC and SPEC.loader
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def synthetic_sources(count: int = 220) -> list[dict]:
    sources = []
    for rank in range(count):
        source_tuple = ["exta_tf_spatial", "synthetic-recovery", rank, "left"]
        sources.append({
            "source_tuple": source_tuple,
            "selection_hash": builder.selection_hash(source_tuple),
            "selection_rank": rank,
            "source_identity": {"task_id": "exta_tf_spatial", "source_revision": "synthetic-recovery", "source_row_ordinal": rank, "label": "left"},
            "arg_a": f"synthetic_a_{rank:06d}",
            "arg_b": f"synthetic_b_{rank:06d}",
            "relation_key": "left",
            "source_provenance": {"source_type": "synthetic_recovery_fixture", "source_row_ordinal": rank},
        })
    return sources


def test_one_condition_and_two_records_per_family() -> None:
    render = json.loads((ROOT / "experiments/paper_a_ext_b/paper_a_ext_b_rendering_conditions_c01_c10_v2.json").read_text(encoding="utf-8"))
    task, records = builder._task_objects("TF_SPATIAL", "exta_tf_spatial", "spatial", synthetic_sources(), render)
    assert task["family_count"] == 220
    assert task["record_count"] == 440
    assert len(records) == 440
    grouped = defaultdict(list)
    for row in records:
        grouped[row["family_id"]].append(row)
    assert len(grouped) == 220
    assert all(len(rows) == 2 for rows in grouped.values())
    assert all({row["record_role"] for row in rows} == {"reference", "realization"} for rows in grouped.values())
    assert all(len({row["condition_id"] for row in rows}) == 1 for rows in grouped.values())


def test_frozen_condition_and_split_allocation_is_deterministic() -> None:
    first = [builder._split_for_rank(rank) for rank in range(220)]
    second = [builder._split_for_rank(rank) for rank in range(220)]
    assert first == second
    assert Counter(condition for condition, _within, _split in first) == {condition: 22 for condition in builder.CONDITIONS}
    assert Counter(split for _condition, _within, split in first) == {"FIT": 60, "DIAGNOSTIC": 80, "EVAL": 80}
    assert Counter((split, condition) for condition, _within, split in first) == {
        (split, condition): expected
        for split, expected in (("FIT", 6), ("DIAGNOSTIC", 8), ("EVAL", 8))
        for condition in builder.CONDITIONS
    }


def test_record_ids_and_c03_rendering_remain_frozen() -> None:
    family = builder.family_id("spatial", ["exta_tf_spatial", "synthetic", 1, "left"])
    assert builder.record_id(family, "c01_lexical_relex", "reference") == builder.record_id(family, "c01_lexical_relex", "reference")
    render = json.loads((ROOT / "experiments/paper_a_ext_b/paper_a_ext_b_rendering_conditions_c01_c10_v2.json").read_text(encoding="utf-8"))
    reference = builder.render_text(render, "TF_SPATIAL", "left", "A", "B", "c03_controlled_compression", "reference")
    realization = builder.render_text(render, "TF_SPATIAL", "left", "A", "B", "c03_controlled_compression", "realization")
    assert reference == "It is the case that A is left of B."
    assert realization == "A is left of B."
    assert reference != realization


def test_output_records_cover_v2_required_fields_without_writing_production_data() -> None:
    render = json.loads((ROOT / "experiments/paper_a_ext_b/paper_a_ext_b_rendering_conditions_c01_c10_v2.json").read_text(encoding="utf-8"))
    task, records = builder._task_objects("TF_SPATIAL", "exta_tf_spatial", "spatial", synthetic_sources(), render)
    required = set(json.loads((ROOT / "experiments/paper_a_ext_b/paper_a_ext_b_record_schema_v2.json").read_text(encoding="utf-8"))["required_fields"])
    assert all(required <= set(row) for row in records)
    assert not (ROOT / "experiments/paper_a_ext_b/data").exists()
