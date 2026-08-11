# EXP-009 Answer-level Reasoning Evaluation

## Goal

Evaluate normal model answers on a small deterministic set from the four
controlled groups: logic, causality, analogy, and definition.

Run:

```bash
python experiments/exp009/run_answer_eval.py --model_name Qwen/Qwen3-1.7B
```

Expected outputs under `results/exp009`:

- `answer_eval_results.csv`
- `group_accuracy.csv`
- `answer_eval_summary.json`
- `group_accuracy.png`

This is a behavioral baseline using normal generation. It does not apply
activation steering or save hidden-state tensors.
