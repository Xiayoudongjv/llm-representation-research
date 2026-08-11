"""EXP-009: evaluate normal answer-level generation on controlled prompts."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.model_loader import check_cuda_or_raise, load_causal_lm, load_tokenizer, print_model_info


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--prompts_path", default="experiments/exp009/reasoning_eval_prompts.json")
    parser.add_argument("--output_dir", default="results/exp009")
    parser.add_argument("--max_new_tokens", type=int, default=32)
    parser.add_argument("--temperature", type=float, default=0.0)
    return parser.parse_args()


def load_prompts(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        prompts = json.load(handle)
    if len(prompts) != 24 or {item["group"] for item in prompts} != {"logic", "causality", "analogy", "definition"}:
        raise ValueError("Expected 24 prompts across logic, causality, analogy, and definition.")
    return prompts


def build_instruction(question: str) -> str:
    return f"Answer the following question concisely. Respond with only the final answer, without explanation.\n\nQuestion: {question}\nAnswer:"


def generate_answer(model, tokenizer, question: str, max_new_tokens: int, temperature: float) -> str:
    prompt = build_instruction(question)
    if getattr(tokenizer, "chat_template", None):
        messages = [{"role": "user", "content": prompt}]
        encoded_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    else:
        encoded_text = prompt
    inputs = tokenizer(encoded_text, return_tensors="pt")
    device = getattr(model, "device", None)
    if device is not None and str(device) != "meta":
        inputs = {key: value.to(device) for key, value in inputs.items()}
    generation_kwargs = {
        "max_new_tokens": max_new_tokens,
        "do_sample": temperature > 0.0,
        "pad_token_id": tokenizer.eos_token_id,
    }
    if temperature > 0.0:
        generation_kwargs["temperature"] = temperature
    with torch.inference_mode():
        generated = model.generate(**inputs, **generation_kwargs)
    prompt_length = inputs["input_ids"].shape[-1]
    answer = tokenizer.decode(generated[0][prompt_length:], skip_special_tokens=True).strip()
    if "</think>" in answer:
        answer = answer.split("</think>", 1)[1].strip()
    return answer


def is_correct(answer: str, item: dict) -> bool:
    normalized = answer.lower().strip()
    if item["scoring_type"] == "multiple_choice":
        expected = item["expected_answer"].lower()
        return re.search(rf"(?<![a-z]){re.escape(expected)}(?![a-z])", normalized) is not None
    return any(
        re.search(rf"(?<!\w){re.escape(acceptable.lower())}(?!\w)", normalized) is not None
        for acceptable in item["acceptable_answers"]
    )


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    check_cuda_or_raise()
    prompts = load_prompts(PROJECT_ROOT / args.prompts_path)
    output_dir = PROJECT_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    tokenizer = load_tokenizer(args.model_name)
    model = load_causal_lm(args.model_name, dtype=args.dtype)
    print_model_info(model)

    result_rows = []
    for index, item in enumerate(prompts, start=1):
        answer = generate_answer(model, tokenizer, item["question"], args.max_new_tokens, args.temperature)
        correct = is_correct(answer, item)
        result_rows.append([item["id"], item["group"], item["question"], item["expected_answer"], answer, correct])
        print(f"[{index}/{len(prompts)}] {item['id']}: correct={correct}; answer={answer!r}")

    result_header = ["id", "group", "question", "expected_answer", "model_answer", "is_correct"]
    write_csv(output_dir / "answer_eval_results.csv", result_header, result_rows)

    group_rows = []
    group_accuracy = {}
    for group in ["logic", "causality", "analogy", "definition"]:
        group_results = [row for row in result_rows if row[1] == group]
        num_correct = sum(row[-1] for row in group_results)
        accuracy = num_correct / len(group_results)
        group_accuracy[group] = accuracy
        group_rows.append([group, len(group_results), num_correct, accuracy])
    write_csv(output_dir / "group_accuracy.csv", ["group", "num_items", "num_correct", "accuracy"], group_rows)

    summary = {
        "model_name": args.model_name,
        "prompt_count": len(prompts),
        "overall_accuracy": sum(row[-1] for row in result_rows) / len(result_rows),
        "group_accuracy": group_accuracy,
        "max_new_tokens": args.max_new_tokens,
        "temperature": args.temperature,
        "note": "Normal generation only; no activation steering or hidden-state intervention was applied.",
    }
    (output_dir / "answer_eval_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.bar(list(group_accuracy), list(group_accuracy.values()))
    axis.set_xlabel("Group")
    axis.set_ylabel("Accuracy")
    axis.set_ylim(0, 1.0)
    axis.set_title("EXP-009 Group Accuracy")
    figure.tight_layout()
    figure.savefig(output_dir / "group_accuracy.png")
    plt.close(figure)
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
