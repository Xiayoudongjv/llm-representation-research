## EXP-005: Multi-pair Calibrated Steering Generalization

Goal: test calibrated centroid steering across all 12 ordered transitions
between the four EXP-003 task groups.

Run the Qwen analysis:

```bash
python experiments/exp005/multipair_steering.py --model_name Qwen/Qwen3-1.7B --layer 16
```

Expected outputs under `results/exp005/` include complete per-beta metrics,
per-prompt assignments, pair and asymmetry summaries, metadata, and four
heatmaps. Each prompt receives one forward pass. Full hidden-state tensors are
not saved.
