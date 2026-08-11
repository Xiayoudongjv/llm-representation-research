## EXP-004: Static Steering Vector Baseline

Goal: test whether a centroid-difference direction shifts source-group
representations toward a target-group region at a selected layer.

Run the Qwen baseline:

```bash
python experiments/exp004/static_steering.py --model_name Qwen/Qwen3-1.7B --layer 16 --source_group logic --target_group causality
```

Expected outputs under `results/exp004/` are steering metrics, per-prompt
assignments, steering metadata, and two plots. This is representation-level
steering, not generation-time activation steering. Full hidden-state tensors
are not saved.
