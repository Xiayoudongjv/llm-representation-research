# EXP-009B Scoring Audit and Answer Normalization

## Goal

Audit the strict EXP-009 answer scores with conservative normalization and
transparent heuristics. This separates clear scoring misses from ambiguous or
likely-wrong answers before later behavioral experiments.

Run:

```bash
python experiments/exp009b/audit_scoring.py
```

Expected outputs under `results/exp009b`:

- `audited_answer_results.csv`
- `audit_summary.json`
- `group_accuracy_comparison.csv`
- `group_accuracy_comparison.png`

The audit reads existing EXP-009 outputs. No Qwen generation is run, no LLM
judge is used, and no hidden-state tensors are saved.
