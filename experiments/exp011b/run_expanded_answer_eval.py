"""EXP-011B: normal-generation evaluation on the expanded EXP-011 dataset."""

from __future__ import annotations

import argparse
import math
import sys
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.answer_scoring import normalize_answer, score_answer
from src.experiment_io import load_json, read_csv, save_json, write_csv
from src.model_loader import check_cuda_or_raise, load_causal_lm, load_tokenizer, print_model_info


GROUPS = ["logic", "causality", "analogy", "definition"]
Z_95 = 1.959963984540054


def parse_args() -> argparse.Namespace:
    """Parse deterministic normal-generation options."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--prompts_path", default="experiments/exp011/expanded_answer_prompts.json")
    parser.add_argument("--output_dir", default="results/exp011b")
    parser.add_argument("--max_new_tokens", type=int, default=32)
    return parser.parse_args()


def build_instruction(question: str) -> str:
    """Build the fixed concise-answer prompt used for every dataset item."""
    return f"Answer the following question with only the short answer, without explanation.\nQuestion: {question}\nAnswer:"


def wilson_interval(correct: int, total: int) -> tuple[float, float]:
    """Return a descriptive two-sided 95% Wilson interval for a proportion."""
    if total <= 0:
        raise ValueError("Wilson interval requires a positive total.")
    proportion = correct / total
    denominator = 1 + Z_95**2 / total
    center = (proportion + Z_95**2 / (2 * total)) / denominator
    margin = Z_95 * math.sqrt((proportion * (1 - proportion) + Z_95**2 / (4 * total)) / total) / denominator
    return center - margin, center + margin


def load_dataset(path: Path) -> list[dict]:
    """Load the validated 80-item EXP-011 dataset."""
    items = load_json(path)
    if not isinstance(items, list) or len(items) != 80:
        raise ValueError("Expected the 80-item EXP-011 dataset.")
    if Counter(item.get("group") for item in items) != Counter({group: 20 for group in GROUPS}):
        raise ValueError("Expected exactly 20 items for each EXP-011 group.")
    if any(item.get("scoring_rule") != "boundary_aware" for item in items):
        raise ValueError("EXP-011B requires boundary_aware scoring for every item.")
    return items


def generate_answer(model, tokenizer, question: str, max_new_tokens: int) -> tuple[str, int]:
    """Generate one deterministic short answer without saving model internals."""
    prompt = build_instruction(question)
    if getattr(tokenizer, "chat_template", None):
        encoded_text = tokenizer.apply_chat_template(
            [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
        )
    else:
        encoded_text = prompt
    inputs = tokenizer(encoded_text, return_tensors="pt")
    device = getattr(model, "device", None)
    if device is not None and str(device) != "meta":
        inputs = {key: value.to(device) for key, value in inputs.items()}
    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    prompt_length = inputs["input_ids"].shape[-1]
    output_ids = generated[0][prompt_length:]
    answer = tokenizer.decode(output_ids, skip_special_tokens=True).strip()
    if "</think>" in answer:
        answer = answer.split("</think>", 1)[1].strip()
    return answer, int(output_ids.shape[-1])


def exp009_comparison() -> tuple[dict[str, float], float | None]:
    """Load EXP-009 group results when the prior baseline is available."""
    group_path = PROJECT_ROOT / "results/exp009/group_accuracy.csv"
    summary_path = PROJECT_ROOT / "results/exp009/answer_eval_summary.json"
    if not group_path.exists():
        return {}, None
    group_accuracy = {row["group"]: float(row["accuracy"]) for row in read_csv(group_path)}
    overall = load_json(summary_path).get("overall_accuracy") if summary_path.exists() else None
    return group_accuracy, overall


def save_group_plot(rows: list[dict], output_path: Path) -> None:
    """Save a default-style group accuracy plot with Wilson error bars."""
    labels = [row["group"] for row in rows]
    values = [row["accuracy"] for row in rows]
    lower_errors = [row["accuracy"] - row["ci95_low"] for row in rows]
    upper_errors = [row["ci95_high"] - row["accuracy"] for row in rows]
    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(labels, values, yerr=[lower_errors, upper_errors], capsize=4)
    axis.set_xlabel("Group")
    axis.set_ylabel("Accuracy")
    axis.set_ylim(0, 1.0)
    axis.set_title("EXP-011B Group Accuracy (Wilson 95% CI)")
    figure.tight_layout()
    figure.savefig(output_path)
    plt.close(figure)


def main() -> None:
    """Run deterministic generation, score answers, and save compact results."""
    args = parse_args()
    check_cuda_or_raise()
    dataset = load_dataset(PROJECT_ROOT / args.prompts_path)
    output_dir = PROJECT_ROOT / args.output_dir
    tokenizer = load_tokenizer(args.model_name)
    model = load_causal_lm(args.model_name, dtype=args.dtype)
    print_model_info(model)

    result_rows: list[dict] = []
    for index, item in enumerate(dataset, start=1):
        model_answer, output_token_count = generate_answer(model, tokenizer, item["question"], args.max_new_tokens)
        correct = score_answer(model_answer, item["acceptable_answers"], item["scoring_rule"])
        result_rows.append({
            "id": item["id"], "group": item["group"], "question": item["question"],
            "expected_answer": item["expected_answer"], "acceptable_answers": str(item["acceptable_answers"]),
            "scoring_rule": item["scoring_rule"], "model_answer": model_answer,
            "normalized_model_answer": normalize_answer(model_answer), "is_correct": correct,
            "output_token_count": output_token_count,
        })
        print(f"[{index}/{len(dataset)}] {item['id']}: correct={correct}; answer={model_answer!r}")
    write_csv(output_dir / "answer_eval_results.csv", list(result_rows[0]), result_rows)

    group_rows: list[dict] = []
    group_accuracy: dict[str, float] = {}
    for group in GROUPS:
        group_results = [row for row in result_rows if row["group"] == group]
        correct = sum(row["is_correct"] for row in group_results)
        low, high = wilson_interval(correct, len(group_results))
        accuracy = correct / len(group_results)
        group_accuracy[group] = accuracy
        group_rows.append({"group": group, "total": len(group_results), "correct": correct, "accuracy": accuracy, "ci95_low": low, "ci95_high": high})
    write_csv(output_dir / "group_accuracy.csv", list(group_rows[0]), group_rows)
    save_group_plot(group_rows, output_dir / "group_accuracy.png")

    total_correct = sum(row["is_correct"] for row in result_rows)
    overall_low, overall_high = wilson_interval(total_correct, len(result_rows))
    exp009_group_accuracy, exp009_overall_accuracy = exp009_comparison()
    summary = {
        "model_name": args.model_name,
        "dataset_path": args.prompts_path,
        "total_items": len(result_rows),
        "correct_items": total_correct,
        "overall_accuracy": total_correct / len(result_rows),
        "ci95_low": overall_low,
        "ci95_high": overall_high,
        "generation_configuration": {"do_sample": False, "temperature": None, "max_new_tokens": args.max_new_tokens, "dtype": args.dtype, "prompt_template": "Answer the following question with only the short answer, without explanation.\\nQuestion: {question}\\nAnswer:"},
        "scoring_rule": "boundary_aware",
        "exp009_accuracy_by_group": exp009_group_accuracy,
        "exp011b_accuracy_by_group": group_accuracy,
        "accuracy_change_by_group": {group: group_accuracy[group] - exp009_group_accuracy[group] for group in GROUPS if group in exp009_group_accuracy},
        "exp009_overall_accuracy": exp009_overall_accuracy,
        "note": "Normal deterministic generation only; no activation steering or hidden-state intervention was applied. Wilson intervals are descriptive uncertainty only.",
    }
    save_json(summary, output_dir / "overall_summary.json")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
