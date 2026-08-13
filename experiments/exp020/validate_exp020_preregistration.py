"""Validate EXP-020A frozen protocol inputs without loading Qwen3-4B."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXP_DIR = Path(__file__).resolve().parent
CONFIG_PATH = EXP_DIR / "exp020_frozen_config.json"
PROMPT_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
SOURCE_CONDITIONS_PATH = ROOT / "experiments" / "exp018" / "validation_conditions.json"
LOCAL_AUDIT_PATH = EXP_DIR / "results" / "qwen3_4b_local_integrity_and_duplicate_audit.json"
LOCAL_QUALIFICATION_PATH = EXP_DIR / "results" / "qwen3_4b_hardware_qualification.json"
FORMAL_OUTPUTS = {
    "transition_metrics.csv",
    "probe_metrics.csv",
    "invariant_metrics.csv",
    "pair_summary.csv",
    "representation_summary.json",
    "validation_summary.json",
    "behavioral_outputs.csv",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def flattened_ids(grouped: dict[str, list[str]]) -> list[str]:
    return [item_id for ids in grouped.values() for item_id in ids]


def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    source = json.loads(SOURCE_CONDITIONS_PATH.read_text(encoding="utf-8"))
    prompts = json.loads(PROMPT_PATH.read_text(encoding="utf-8"))
    model = config["model"]
    layers = config["layer_indexing"]
    dataset = config["dataset"]

    require(config["scientific_status"] == "NOT_STARTED", "EXP-020A scientific status is not frozen as NOT_STARTED")
    require(model == {
        **model,
        "model_id": "Qwen/Qwen3-4B",
        "revision": "1cfa9a7208912126459214e8b04321603b3df60c",
        "canonical_path": r"D:\Qwen3-4B-transfer",
        "local_files_only": True,
        "dtype": "bfloat16",
        "device": "cuda:0",
        "model_type": "qwen3",
        "architecture": "Qwen3ForCausalLM",
        "num_transformer_blocks": 36,
        "hidden_size": 2560,
        "vocab_size": 151936,
        "execution_mode": "MODE_A_NATIVE",
    }, "model identity fields differ from the frozen protocol")
    external_config = Path(model["canonical_path"]) / "config.json"
    require(external_config.is_file(), "canonical local model config is absent")
    require(sha256(external_config) == model["config_sha256"], "canonical model config hash differs")

    require(layers["block_index_definition"] == "0-based transformer block index in model.model.layers", "block index semantics changed")
    require(layers["hidden_states_tuple_definition"] == "hidden_states[0] is the embedding output; hidden_states[k + 1] is the output after transformer block k", "hidden-state semantics changed")
    require(layers["mapping_rule"] == "round(depth_fraction * (num_blocks - 1))", "layer mapping rule changed")
    require(layers["primary"] == {"depth_fraction": 0.5, "block_index": 18, "hidden_states_index": 19}, "primary layer mapping differs")
    require(layers["secondary_descriptive"] == {"depth_fraction": 0.75, "block_index": 26, "hidden_states_index": 27}, "secondary layer mapping differs")

    require(sha256(PROMPT_PATH) == dataset["prompt_file_sha256"], "prompt file hash differs")
    require(sha256(SOURCE_CONDITIONS_PATH) == dataset["source_conditions_sha256"], "source conditions hash differs")
    source_manifest = {"splits": source["splits"], "ordered_transitions": source["ordered_transitions"], "groups": source["groups"]}
    require(canonical_sha256(source_manifest) == dataset["split_transition_manifest_sha256"], "split/transition manifest hash differs")
    require(dataset["splits"] == source["splits"] and dataset["ordered_transitions"] == source["ordered_transitions"], "fit/eval IDs or transitions differ from frozen source")
    prompt_ids = {item["id"] for item in prompts}
    for split in dataset["splits"]:
        fit_ids = flattened_ids(split["fit_ids"])
        eval_ids = flattened_ids(split["evaluation_ids"])
        require(len(fit_ids) == 12 and len(eval_ids) == 12, f"unexpected split size: {split['id']}")
        require(set(fit_ids).isdisjoint(eval_ids), f"fit/eval overlap: {split['id']}")
        require(set(fit_ids + eval_ids) <= prompt_ids, f"unknown prompt ID: {split['id']}")
    require(len(dataset["ordered_transitions"]) == 12, "ordered transition count differs")
    require(dataset["aggregate_paired_evaluation_count"] == 72, "aggregate paired evaluation count differs")

    require(config["conditions"] == ["BASELINE", "TASK", "MATCHED_RANDOM", "OPPOSITE"], "condition list differs")
    require(config["beta"] == {"primary": 0.75, "secondary_descriptive": [0.5], "search_permitted": False, "secondary_cannot_rescue_primary": True}, "beta policy differs")
    probe = config["probe"]
    require(probe["fit_data_only"] is True and probe["tuning_on_evaluation_permitted"] is False, "probe fit boundary differs")
    require(probe["preprocessing"] == {"class": "StandardScaler", "with_mean": True, "with_std": True}, "probe preprocessing differs")
    require(probe["classifier"] == {
        "class": "LogisticRegression", "solver": "lbfgs", "penalty": "l2", "C": 1.0,
        "multi_class": "multinomial", "max_iter": 1000, "class_weight": None,
        "random_state": 20260319, "class_order": ["logic", "causality", "analogy", "definition"],
    }, "probe classifier policy differs")
    require(config["statistics"] == {
        "report_for": ["task_effect", "D_random", "D_opposite"],
        "primary_report_fields": ["N", "mean", "median", "standard_deviation", "bootstrap_95_percent_CI", "proportion_greater_than_zero"],
        "bootstrap_seed": 20260812,
        "bootstrap_resamples": 10000,
    }, "bootstrap/statistics policy differs")
    gate = config["representation_gate"]
    require(gate["supported_label"] == "REPRESENTATION_REPLICATION_SUPPORTED" and gate["not_supported_label"] == "REPRESENTATION_REPLICATION_NOT_SUPPORTED" and gate["invalid_label"] == "REPRESENTATION_REPLICATION_INVALID", "gate labels differ")
    require(len(gate["all_required"]) == 5 and gate["secondary_layer_can_rescue"] is False, "gate criteria differ")
    require(config["behavior_boundary"]["exp020a_behavior"] == "NOT_RUN" and config["behavior_boundary"]["exp020b"] == "CONDITIONAL_SEPARATE_PREREGISTRATION_ONLY", "behavior boundary differs")

    audit = json.loads(LOCAL_AUDIT_PATH.read_text(encoding="utf-8"))
    qualification = json.loads(LOCAL_QUALIFICATION_PATH.read_text(encoding="utf-8"))
    require(audit["integrity_status"] == "PASS" and audit["source_revision_from_download_metadata"] == model["revision"], "local snapshot audit does not support frozen revision")
    require(qualification["qualification_status"] == "READY_FOR_EXP020_PREREGISTRATION_REVIEW", "hardware qualification is not ready")
    require(qualification["selected_execution_mode"] == model["execution_mode"] and qualification["zero_hook_status"] == "ZERO_HOOK_EQUIVALENCE_PASS", "frozen execution mode or hook check differs")
    require(config["boundaries"] == {"formal_exp020_results_created": False, "exp017_accessed": False, "exp019_accessed": False, "raw_hidden_state_persistence_allowed": False}, "scientific boundary differs")
    results = EXP_DIR / "results"
    require(not any((results / name).exists() for name in FORMAL_OUTPUTS), "formal EXP-020A result file exists before execution")

    print("EXP020_PREREGISTRATION_VALIDATION_PASS")
    print("model_revision:", model["revision"])
    print("primary_block_hidden_state:", layers["primary"]["block_index"], layers["primary"]["hidden_states_index"])
    print("secondary_block_hidden_state:", layers["secondary_descriptive"]["block_index"], layers["secondary_descriptive"]["hidden_states_index"])
    print("prompt_file_sha256:", dataset["prompt_file_sha256"])
    print("fit_eval_per_split:", dataset["fit_count_per_split"], dataset["evaluation_count_per_split"])


if __name__ == "__main__":
    main()
