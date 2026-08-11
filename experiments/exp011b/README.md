# EXP-011B Expanded Answer-Level Evaluation

## Purpose

Evaluate normal deterministic Qwen generation on the 80-item, quality-audited
EXP-011 dataset and compare group accuracy descriptively with EXP-009.

## Model and Dataset

- Model: `Qwen/Qwen3-1.7B`
- Dataset: `experiments/exp011/expanded_answer_prompts.json`
- Items: 80 total, 20 each for logic, causality, analogy, and definition

## Command

```bash
python experiments/exp011b/run_expanded_answer_eval.py
```

## Generation and Scoring

Generation uses `do_sample=False` and `max_new_tokens=32`. Answers are scored
with each item's `boundary_aware` rule via `src.answer_scoring`; no logits or
hidden states are saved.

## Outputs

- `answer_eval_results.csv`
- `group_accuracy.csv`
- `overall_summary.json`
- `group_accuracy.png`
