## EXP-006: Relational Invariant Score

Goal: test whether calibrated centroid steering preserves within-source
relational structure while moving representations toward target regions.

Run the Qwen analysis:

```bash
python experiments/exp006/relational_invariant_score.py --model_name Qwen/Qwen3-1.7B --layer 16
```

Expected outputs under `results/exp006/` include invariant metrics, pair
summaries, transition tradeoffs, metadata, and four diagnostic plots. Full
hidden-state tensors are not saved. RSM correlation is only a proxy invariant,
not proof of logical or semantic invariance.
