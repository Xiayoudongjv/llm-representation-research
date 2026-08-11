# EXP-011 Expanded Answer-level Dataset

## Purpose

EXP-011 expands answer-level evaluation beyond the unstable 24-item baseline
and prepares a stronger behavioral dataset for later evaluation.

## Dataset

The dataset contains 80 deterministic short-answer items: 20 each for logic,
causality, analogy, and definition. Each item uses boundary-aware matching over
a lowercase acceptable-answer list. Raw substring scoring was rejected because
short answers such as `no` can otherwise create false positives.

## Validation

```bash
python experiments/exp011/validate_dataset.py
python experiments/exp011/audit_dataset_quality.py
```

The quality audit records a per-item semantic and scoring review in
`dataset_quality_audit.csv` and writes aggregate findings to
`dataset_quality_summary.json`.

## Important

This task does not run Qwen and does not measure model accuracy. Boundary-aware
scoring hardens the dataset configuration before a future evaluation run.
