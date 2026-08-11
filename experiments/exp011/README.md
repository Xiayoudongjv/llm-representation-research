# EXP-011 Expanded Answer-level Dataset

## Purpose

EXP-011 expands answer-level evaluation beyond the unstable 24-item baseline
and prepares a stronger behavioral dataset for later evaluation.

## Dataset

The dataset contains 80 deterministic short-answer items: 20 each for logic,
causality, analogy, and definition. Each item includes a lowercase acceptable
answer list for transparent string-containment scoring.

## Validation

```bash
python experiments/exp011/validate_dataset.py
```

## Important

This task does not run Qwen and does not measure model accuracy. It prepares
and validates the dataset only.
