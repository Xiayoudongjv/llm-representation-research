## EXP-003: Lexical and Paraphrase Control

Goal: test whether task-group geometry remains when each group contains both
original-style and paraphrased prompts with varied surface wording.

Run the Qwen analysis:

```bash
python experiments/exp003/analyze_controlled_geometry.py --model_name Qwen/Qwen3-1.7B
```

Expected outputs under `results/exp003/` include layer, group, variant, token,
and diagnostic metrics, centroid distances, PCA plots for each selected layer,
and separation, silhouette, and paraphrase-retention plots.

Each prompt is processed with one forward pass. Full hidden-state tensors are
not saved.
