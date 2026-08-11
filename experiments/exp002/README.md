## EXP-002: Layer-wise Representation Geometry

EXP-002 measures representation geometry at layers 0, 4, 8, 12, 16, 20, 24,
and 28 using the unchanged 12-prompt set from EXP-001. Each prompt receives
one forward pass; full hidden-state tensors are not saved.

Run a syntax check:

```bash
python -m compileall src experiments
```

Run the Qwen analysis:

```bash
python experiments/exp002/analyze_layers.py --model_name Qwen/Qwen3-1.7B
```

Expected outputs under `results/exp002/` include layer and group metrics,
prompt token counts, centroid distances, diagnostics, one PCA plot per layer,
and layer-wise separation and silhouette plots.
