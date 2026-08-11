## EXP-004B: Calibrated Static Steering

Goal: test whether scaling a centroid-difference direction by its actual
source-to-target magnitude produces stronger representation-level movement.

Run the Qwen baseline:

```bash
python experiments/exp004b/calibrated_steering.py --model_name Qwen/Qwen3-1.7B --layer 16 --source_group logic --target_group causality
```

Expected outputs under `results/exp004b/` are calibrated steering metrics,
per-prompt assignments, metadata, and three plots. This is representation-level
calibrated centroid steering, not generation-time steering. Full hidden-state
tensors are not saved.
