## EXP-001: Representation Geometry Baseline

Goal: measure pairwise cosine similarity and a 2D PCA projection for the last-token representations of 12 controlled prompts.

Run a syntax check:

```bash
python -m compileall src experiments
```

Run with the fallback model:

```bash
python experiments/exp001/compute_geometry.py --use_fallback
```

Run with Qwen:

```bash
python experiments/exp001/compute_geometry.py --model_name Qwen/Qwen3-1.7B
```

Expected output files under `results/exp001/`:

- `representations_metadata.json`
- `cosine_similarity.csv`
- `pca_coords.csv`
- `pca_plot.png`

Only compact representations and derived metrics are saved. Full hidden-state tensors are not saved.
