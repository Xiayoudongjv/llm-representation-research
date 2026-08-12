"""Amended EXP-017 behavioral runner; use --dry-run before any official --run.

The runner reads all scientific conditions from intervention_conditions_v2.json.
It saves only row-level behavioral outputs and aggregates, never activations or
steering vectors.  The official path is intentionally explicit and atomic.
"""

from __future__ import annotations

import argparse
import gc
import sys
import uuid
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.exp017.hook_diagnostic import LastTokenHook, resolve_cache_dir
from src.answer_scoring import normalize_answer, score_answer
from src.experiment_io import load_json, save_json, write_csv
from src.extraction import get_model_input_device, move_tokenized_inputs_to_device
from src.model_loader import check_cuda_or_raise, load_causal_lm, load_tokenizer


CONFIG_PATH = Path(__file__).with_name("intervention_conditions_v2.json")
FIT_PROMPTS_PATH = ROOT / "experiments" / "exp003" / "prompts_controlled.json"
BEHAVIOR_DATASET_PATH = ROOT / "experiments" / "exp011" / "expanded_answer_prompts.json"
OUTPUT_DIR = ROOT / "results" / "exp017"
ROW_FIELDS = [
    "item_id", "source_group", "target_group", "condition", "layer", "beta",
    "generated_text", "normalized_answer", "strict_correct", "output_token_count",
    "empty_answer", "repetition_flag", "malformed_flag",
]
CONDITION_SUMMARY_FIELDS = [
    "condition", "total", "correct", "accuracy", "accuracy_delta_vs_no_intervention",
    "empty_rate", "repetition_rate", "malformed_rate", "mean_output_token_count", "median_output_token_count",
]
GROUP_SUMMARY_FIELDS = [
    "condition", "source_group", "total", "correct", "accuracy", "accuracy_delta_vs_no_intervention",
    "empty_rate", "repetition_rate", "malformed_rate", "mean_output_token_count", "median_output_token_count",
]


def load_and_validate_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    """Load the amendment and reject incomplete or internally inconsistent inputs."""
    config = load_json(path)
    required = {"model", "dtype", "dataset", "generation", "direction_estimation", "conditions", "random_control", "hook_semantics", "outcomes"}
    missing = sorted(required - set(config))
    if missing:
        raise ValueError(f"Amendment config is missing keys: {missing}")
    conditions = config["conditions"]
    if [item.get("id") for item in conditions] != ["NO_INTERVENTION", "TASK_REAL", "MATCHED_RANDOM", "OPPOSITE"]:
        raise ValueError("EXP-017 amendment must contain exactly its frozen four conditions in order.")
    interventions = conditions[1:]
    if len({(item.get("layer"), item.get("beta")) for item in interventions}) != 1:
        raise ValueError("All amended intervention conditions must share one frozen layer/beta setting.")
    if config["dataset"].get("delta_fit_prohibited") is not True:
        raise ValueError("Behavioral data must be explicitly prohibited from delta fitting.")
    transitions = config["direction_estimation"].get("transitions", {})
    groups = config["dataset"].get("groups", [])
    if set(transitions) != set(groups) or set(transitions.values()) != set(groups):
        raise ValueError("Transitions must define one symmetric target mapping for every behavioral group.")
    return config


def load_behavioral_dataset(path: Path = BEHAVIOR_DATASET_PATH, groups: list[str] | None = None) -> list[dict[str, Any]]:
    """Load only the frozen 80-item behavioral evaluation dataset."""
    items = load_json(path)
    expected_groups = groups or ["logic", "causality", "analogy", "definition"]
    if not isinstance(items, list) or len(items) != 80:
        raise ValueError("EXP-017 requires exactly the frozen 80-item EXP-011D dataset.")
    if len({item.get("id") for item in items}) != len(items):
        raise ValueError("Behavioral item IDs must be unique.")
    if Counter(item.get("group") for item in items) != Counter({group: 20 for group in expected_groups}):
        raise ValueError("Behavioral dataset must contain exactly 20 items per frozen group.")
    if any(item.get("scoring_rule") != "boundary_aware" for item in items):
        raise ValueError("Every behavioral item must retain boundary_aware scoring.")
    return items


def load_fit_prompts(path: Path = FIT_PROMPTS_PATH, groups: list[str] | None = None) -> list[dict[str, Any]]:
    """Load only the 24 controlled EXP-003 prompts permitted for delta fitting."""
    prompts = load_json(path)
    expected_groups = groups or ["logic", "causality", "analogy", "definition"]
    if not isinstance(prompts, list) or len(prompts) != 24:
        raise ValueError("Delta fitting requires exactly the 24 controlled EXP-003 prompts.")
    if Counter(item.get("group") for item in prompts) != Counter({group: 6 for group in expected_groups}):
        raise ValueError("EXP-003 fit prompts must contain exactly six prompts per group.")
    if any(not item.get("text") for item in prompts):
        raise ValueError("Every EXP-003 fit prompt must have non-empty text.")
    return prompts


def assert_data_isolation(fit_prompts: list[dict[str, Any]], behavioral_items: list[dict[str, Any]]) -> None:
    """Fail closed when any record ID or object appears in both fit and evaluation data."""
    fit_ids = {item["id"] for item in fit_prompts}
    behavioral_ids = {item["id"] for item in behavioral_items}
    overlap = sorted(fit_ids & behavioral_ids)
    if overlap:
        raise ValueError(f"Behavioral IDs may not enter delta fitting: {overlap}")
    if any(item in behavioral_items for item in fit_prompts):
        raise ValueError("Behavioral records may not be reused as steering fit records.")


def build_prompt(question: str, template: str) -> str:
    """Use the frozen concise-answer template exactly as stored in the amendment."""
    return template.format(question=question)


def construct_task_deltas(
    fit_representations: dict[str, np.ndarray], fit_prompts: list[dict[str, Any]], transitions: dict[str, str],
) -> dict[tuple[str, str], np.ndarray]:
    """Fit group centroids from EXP-003 only and construct one raw delta per transition."""
    fit_ids = {item["id"] for item in fit_prompts}
    if set(fit_representations) != fit_ids:
        raise ValueError("Representations for delta fitting must be exactly the permitted EXP-003 fit IDs.")
    centroids: dict[str, np.ndarray] = {}
    for source_group in transitions:
        vectors = [np.asarray(fit_representations[item["id"]], dtype=np.float64) for item in fit_prompts if item["group"] == source_group]
        if len(vectors) != 6:
            raise ValueError(f"Expected six fit vectors for {source_group!r}.")
        centroids[source_group] = np.mean(np.stack(vectors), axis=0)
    return {(source, target): centroids[target] - centroids[source] for source, target in transitions.items()}


def construct_random_deltas(task_deltas: dict[tuple[str, str], np.ndarray], random_config: dict[str, Any], layer: int) -> dict[tuple[str, str], np.ndarray]:
    """Build one deterministic equal-norm random direction per frozen transition."""
    vectors: dict[tuple[str, str], np.ndarray] = {}
    indices = random_config["source_group_index"]
    for (source, target), task_delta in task_deltas.items():
        rng = np.random.default_rng(np.random.SeedSequence([random_config["base_seed"], layer, indices[source], indices[target]]))
        random_vector = rng.standard_normal(np.asarray(task_delta).shape)
        task_norm = float(np.linalg.norm(task_delta))
        random_norm = float(np.linalg.norm(random_vector))
        vectors[(source, target)] = random_vector if task_norm == 0 else random_vector * (task_norm / random_norm)
    return vectors


def vector_for_condition(condition_id: str, transition: tuple[str, str], task_deltas: dict, random_deltas: dict) -> np.ndarray | None:
    """Return the frozen vector for one condition without per-item refitting or resampling."""
    if condition_id == "NO_INTERVENTION":
        return None
    if condition_id == "TASK_REAL":
        return task_deltas[transition]
    if condition_id == "MATCHED_RANDOM":
        return random_deltas[transition]
    if condition_id == "OPPOSITE":
        return -task_deltas[transition]
    raise ValueError(f"Unknown frozen condition: {condition_id}")


def collateral_flags(answer: str) -> tuple[bool, bool]:
    """Apply the amendment's exact empty and malformed/non-short-answer rules."""
    stripped = answer.strip()
    empty = not stripped
    malformed = empty or "\n" in answer or len(stripped.split()) > 12 or len(stripped) > 160
    return empty, malformed


def apply_repetition_flags(rows: list[dict[str, Any]]) -> None:
    """Set adjacent-in-dataset-order exact repetition flags within condition/source group."""
    prior: dict[tuple[str, str], str] = {}
    for row in rows:
        key = (row["condition"], row["source_group"])
        answer = row["normalized_answer"]
        row["repetition_flag"] = key in prior and prior[key] == answer
        prior[key] = answer


def summarize_rows(rows: list[dict[str, Any]], conditions: list[dict[str, Any]], groups: list[str]) -> tuple[list[dict], list[dict]]:
    """Produce frozen condition and source-group summaries from future row data."""
    def make_summary(subset: list[dict], condition: str, group: str | None, baseline_accuracy: float) -> dict:
        total = len(subset)
        correct = sum(bool(row["strict_correct"]) for row in subset)
        accuracy = correct / total if total else float("nan")
        counts = np.asarray([row["output_token_count"] for row in subset], dtype=float)
        row = {"condition": condition, "total": total, "correct": correct, "accuracy": accuracy,
               "accuracy_delta_vs_no_intervention": accuracy - baseline_accuracy,
               "empty_rate": float(np.mean([row["empty_answer"] for row in subset])),
               "repetition_rate": float(np.mean([row["repetition_flag"] for row in subset])),
               "malformed_rate": float(np.mean([row["malformed_flag"] for row in subset])),
               "mean_output_token_count": float(np.mean(counts)), "median_output_token_count": float(np.median(counts))}
        if group is not None:
            row["source_group"] = group
        return row

    condition_rows, group_rows = [], []
    for condition in conditions:
        condition_id = condition["id"]
        subset = [row for row in rows if row["condition"] == condition_id]
        baseline = [row for row in rows if row["condition"] == "NO_INTERVENTION"]
        condition_rows.append(make_summary(subset, condition_id, None, sum(bool(row["strict_correct"]) for row in baseline) / len(baseline)))
        for group in groups:
            group_subset = [row for row in subset if row["source_group"] == group]
            baseline_group = [row for row in baseline if row["source_group"] == group]
            group_rows.append(make_summary(group_subset, condition_id, group, sum(bool(row["strict_correct"]) for row in baseline_group) / len(baseline_group)))
    return condition_rows, group_rows


def collect_fit_representations(model, tokenizer, fit_prompts: list[dict], layer: int) -> dict[str, np.ndarray]:
    """Collect in-memory EXP-003 L16 last-token vectors; never write vectors to disk."""
    device = get_model_input_device(model)
    vectors = {}
    with torch.no_grad():
        for item in fit_prompts:
            inputs = move_tokenized_inputs_to_device(tokenizer(item["text"], return_tensors="pt"), device)
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            vectors[item["id"]] = outputs.hidden_states[layer][0, -1, :].detach().float().cpu().numpy()
    return vectors


def generate_answer(model, tokenizer, question: str, generation: dict[str, Any], vector: np.ndarray | None, layer: int | None) -> tuple[str, int]:
    """Generate one frozen answer, installing the validated hook only for a vector condition."""
    encoded_text = build_prompt(question, generation["prompt_template"])
    if getattr(tokenizer, "chat_template", None):
        encoded_text = tokenizer.apply_chat_template([{"role": "user", "content": encoded_text}], tokenize=False, add_generation_prompt=True)
    inputs = move_tokenized_inputs_to_device(tokenizer(encoded_text, return_tensors="pt"), get_model_input_device(model))
    handle = None
    if vector is not None:
        activation = next(model.parameters())
        delta = torch.as_tensor(vector, device=activation.device, dtype=activation.dtype)
        handle = model.model.layers[layer].register_forward_hook(LastTokenHook(delta))
    try:
        with torch.inference_mode():
            generated = model.generate(**inputs, do_sample=generation["do_sample"], max_new_tokens=generation["max_new_tokens"], pad_token_id=tokenizer.eos_token_id, use_cache=True)
    finally:
        if handle is not None:
            handle.remove()
    output_ids = generated[0][inputs["input_ids"].shape[-1]:]
    answer = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    if "</think>" in answer:
        answer = answer.split("</think>", 1)[1].strip()
    return answer, int(output_ids.shape[-1])


def publish_outputs_atomically(rows: list[dict], config: dict[str, Any], output_dir: Path = OUTPUT_DIR) -> None:
    """Publish all five official outputs only after the complete 320-row run succeeds."""
    if output_dir.exists():
        raise FileExistsError(f"Refusing to overwrite official EXP-017 output directory: {output_dir}")
    if len(rows) != len(load_behavioral_dataset(groups=config["dataset"]["groups"])) * len(config["conditions"]):
        raise ValueError("Refusing to publish an incomplete official EXP-017 run.")
    condition_rows, group_rows = summarize_rows(rows, config["conditions"], config["dataset"]["groups"])
    staging = output_dir.with_name(f"{output_dir.name}_tmp_{uuid.uuid4().hex}")
    write_csv(staging / "behavioral_outputs.csv", ROW_FIELDS, rows)
    write_csv(staging / "condition_summary.csv", CONDITION_SUMMARY_FIELDS, condition_rows)
    write_csv(staging / "group_summary.csv", GROUP_SUMMARY_FIELDS, group_rows)
    save_json({"row_count": len(rows), "primary_causal_comparison": config["outcomes"]["primary_causal_comparison"], "claim_boundary": config["claim_boundary"]}, staging / "behavioral_validation_summary.json")
    save_json({"model": config["model"], "conditions": config["conditions"], "generation": config["generation"], "vectors_persisted": False}, staging / "run_metadata.json")
    staging.replace(output_dir)


def dry_run(config: dict[str, Any]) -> None:
    """Validate frozen data and print the planned 320 generations without loading a model."""
    groups = config["dataset"]["groups"]
    fit_prompts = load_fit_prompts(groups=groups)
    behavioral_items = load_behavioral_dataset(groups=groups)
    assert_data_isolation(fit_prompts, behavioral_items)
    expected = len(behavioral_items) * len(config["conditions"])
    print(f"fit_prompt_count: {len(fit_prompts)}")
    print(f"behavioral_item_count: {len(behavioral_items)}")
    print(f"condition_count: {len(config['conditions'])}")
    print(f"expected_official_generation_count: {expected}")
    print("dry_run=passed_no_model_loaded_no_results_created")


def run_official(config: dict[str, Any], cache_root: Path) -> None:
    """Execute the explicit future official run; never called by --dry-run."""
    check_cuda_or_raise()
    groups = config["dataset"]["groups"]
    fit_prompts, behavioral_items = load_fit_prompts(groups=groups), load_behavioral_dataset(groups=groups)
    assert_data_isolation(fit_prompts, behavioral_items)
    cache_dir = resolve_cache_dir(cache_root)
    tokenizer = load_tokenizer(config["model"], cache_dir=cache_dir, local_files_only=True)
    model = load_causal_lm(config["model"], dtype=config["dtype"], cache_dir=cache_dir, local_files_only=True)
    model.eval()
    try:
        layer = config["conditions"][1]["layer"]
        task_deltas = construct_task_deltas(collect_fit_representations(model, tokenizer, fit_prompts, layer), fit_prompts, config["direction_estimation"]["transitions"])
        random_deltas = construct_random_deltas(task_deltas, config["random_control"], layer)
        rows = []
        for condition in config["conditions"]:
            for item in behavioral_items:
                transition = (item["group"], config["direction_estimation"]["transitions"][item["group"]])
                vector = vector_for_condition(condition["id"], transition, task_deltas, random_deltas)
                answer, token_count = generate_answer(model, tokenizer, item["question"], config["generation"], vector, condition["layer"])
                empty, malformed = collateral_flags(answer)
                rows.append({"item_id": item["id"], "source_group": item["group"], "target_group": transition[1], "condition": condition["id"], "layer": condition["layer"], "beta": condition["beta"], "generated_text": answer, "normalized_answer": normalize_answer(answer), "strict_correct": score_answer(answer, item["acceptable_answers"], item["scoring_rule"]), "output_token_count": token_count, "empty_answer": empty, "repetition_flag": False, "malformed_flag": malformed})
        apply_repetition_flags(rows)
        publish_outputs_atomically(rows, config)
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()


def main() -> None:
    """Run a no-model dry validation by default, requiring --run for official execution."""
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--run", action="store_true", help="Run all 320 official generations and publish atomically.")
    parser.add_argument("--cache-dir", type=Path, default=Path(r"D:\AI_Cache\huggingface"))
    args = parser.parse_args()
    config = load_and_validate_config()
    if args.dry_run:
        dry_run(config)
    else:
        run_official(config, args.cache_dir)


if __name__ == "__main__":
    main()
