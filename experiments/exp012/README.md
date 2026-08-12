# EXP-012 Frozen Behavioral Link Reanalysis

This offline analysis replaces EXP-010's preliminary 24-item behavior with the
frozen EXP-011D 80-item benchmark. It computes descriptive Pearson, Spearman,
and leave-one-group-out sensitivity results for four task groups only.

```bash
python experiments/exp012/frozen_behavior_link.py
```

No Qwen run, model loading, or causal inference occurs.
