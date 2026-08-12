# EXP-013 Gemma Cross-Model Geometry Replication

Run the fixed 24-prompt EXP-003 controlled geometry analysis on the locally
cached `google/gemma-3-1b-it` snapshot:

```bash
python experiments/exp013/gemma_geometry_replication.py
```

The experiment uses raw plain-text prompts, float16 CUDA, batch size 1, and
last-token hidden-state representations at normalized Gemma depths. It performs
no generation, steering, or hidden-state persistence.
