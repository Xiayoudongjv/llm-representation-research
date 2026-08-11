# EXP-010 Representation Validity vs Answer Difficulty

## Goal

Explore whether group-level representation metrics correspond to answer-level
task difficulty using existing EXP-003, EXP-005, EXP-006, EXP-009, and EXP-009B
results.

Run:

```bash
python experiments/exp010/representation_behavior_link.py
```

Expected outputs under `results/exp010`:

- `group_behavior_representation_summary.csv`
- `exploratory_correlations.csv`
- `representation_behavior_summary.json`
- four PNG plots

This is a four-group, exploratory, non-causal analysis. It does not rerun
Qwen, establish that representation metrics explain behavior, or save model
weights or hidden-state tensors.
