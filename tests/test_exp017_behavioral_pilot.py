"""Offline tests for amended EXP-017 runner isolation and frozen semantics."""

from pathlib import Path

import numpy as np
import pytest
import torch

from experiments.exp017.behavioral_pilot import (
    CONDITION_SUMMARY_FIELDS,
    GROUP_SUMMARY_FIELDS,
    ROW_FIELDS,
    assert_data_isolation,
    collateral_flags,
    construct_random_deltas,
    construct_task_deltas,
    load_and_validate_config,
    load_behavioral_dataset,
    load_fit_prompts,
    publish_outputs_atomically,
    vector_for_condition,
)
from experiments.exp017.hook_diagnostic import LastTokenHook


CONFIG = load_and_validate_config()
GROUPS = CONFIG["dataset"]["groups"]


def synthetic_fit_data():
    prompts = [{"id": f"fit_{group}_{index}", "group": group, "text": "controlled"} for group in GROUPS for index in range(6)]
    vectors = {item["id"]: np.full(3, GROUPS.index(item["group"]) + 1.0) for item in prompts}
    return prompts, vectors


def test_config_conditions_are_frozen():
    assert [item["id"] for item in CONFIG["conditions"]] == ["NO_INTERVENTION", "TASK_REAL", "MATCHED_RANDOM", "OPPOSITE"]
    assert {(item["layer"], item["beta"]) for item in CONFIG["conditions"][1:]} == {(16, 0.75)}


def test_exp003_only_fit_and_exp011d_evaluation_datasets_validate():
    fit_prompts = load_fit_prompts(groups=GROUPS)
    behavioral = load_behavioral_dataset(groups=GROUPS)
    assert len(fit_prompts) == 24
    assert len(behavioral) == 80
    assert_data_isolation(fit_prompts, behavioral)


def test_behavioral_ids_cannot_enter_centroid_fitting():
    with pytest.raises(ValueError, match="Behavioral IDs"):
        assert_data_isolation([{"id": "same", "group": "logic", "text": "x"}], [{"id": "same"}])


def test_one_task_delta_per_frozen_transition():
    prompts, vectors = synthetic_fit_data()
    deltas = construct_task_deltas(vectors, prompts, CONFIG["direction_estimation"]["transitions"])
    assert set(deltas) == set(CONFIG["direction_estimation"]["transitions"].items())
    assert len(deltas) == 4


def test_random_norm_matches_task_norm_and_is_deterministic():
    prompts, vectors = synthetic_fit_data()
    task = construct_task_deltas(vectors, prompts, CONFIG["direction_estimation"]["transitions"])
    first = construct_random_deltas(task, CONFIG["random_control"], 16)
    second = construct_random_deltas(task, CONFIG["random_control"], 16)
    for key in task:
        assert np.isclose(np.linalg.norm(first[key]), np.linalg.norm(task[key]))
        assert np.array_equal(first[key], second[key])


def test_same_random_vector_is_reused_for_items_and_generation_steps():
    prompts, vectors = synthetic_fit_data()
    task = construct_task_deltas(vectors, prompts, CONFIG["direction_estimation"]["transitions"])
    random = construct_random_deltas(task, CONFIG["random_control"], 16)
    transition = ("logic", "causality")
    assert vector_for_condition("MATCHED_RANDOM", transition, task, random) is random[transition]
    assert vector_for_condition("MATCHED_RANDOM", transition, task, random) is random[transition]


def test_opposite_is_exact_negative_task_delta_and_baseline_is_none():
    prompts, vectors = synthetic_fit_data()
    task = construct_task_deltas(vectors, prompts, CONFIG["direction_estimation"]["transitions"])
    random = construct_random_deltas(task, CONFIG["random_control"], 16)
    transition = ("logic", "causality")
    assert np.array_equal(vector_for_condition("OPPOSITE", transition, task, random), -task[transition])
    assert vector_for_condition("NO_INTERVENTION", transition, task, random) is None


def test_hook_modifies_last_token_only():
    hidden = torch.zeros(1, 3, 2)
    hooked = LastTokenHook(torch.tensor([1.0, 0.0]))(None, (), hidden)
    assert torch.equal(hooked[:, :-1], hidden[:, :-1])
    assert torch.equal(hooked[0, -1], torch.tensor([1.0, 0.0]))


@pytest.mark.parametrize(
    ("answer", "empty", "malformed"),
    [("", True, True), ("ok", False, False), ("one\ntwo", False, True), (" ".join(["x"] * 13), False, True), ("x" * 161, False, True)],
)
def test_frozen_malformed_thresholds(answer, empty, malformed):
    assert collateral_flags(answer) == (empty, malformed)


def test_output_schemas_are_stable():
    assert ROW_FIELDS == ["item_id", "source_group", "target_group", "condition", "layer", "beta", "generated_text", "normalized_answer", "strict_correct", "output_token_count", "empty_answer", "repetition_flag", "malformed_flag"]
    assert "accuracy_delta_vs_no_intervention" in CONDITION_SUMMARY_FIELDS
    assert "source_group" in GROUP_SUMMARY_FIELDS


def test_atomic_publication_rejects_incomplete_rows(tmp_path: Path):
    with pytest.raises(ValueError, match="incomplete"):
        publish_outputs_atomically([], CONFIG, tmp_path / "exp017")
    assert not (tmp_path / "exp017").exists()


def test_no_raw_hidden_state_persistence_api():
    source = Path("experiments/exp017/behavioral_pilot.py").read_text(encoding="utf-8")
    assert "np.save" not in source
    assert "torch.save" not in source
    assert "vectors_persisted\": False" in source


def test_condition_mapping_by_source_group_is_frozen():
    assert CONFIG["direction_estimation"]["transitions"] == {"logic": "causality", "causality": "logic", "analogy": "definition", "definition": "analogy"}


def test_frozen_scorer_metadata_is_boundary_aware():
    assert all(item["scoring_rule"] == "boundary_aware" for item in load_behavioral_dataset(groups=GROUPS))
