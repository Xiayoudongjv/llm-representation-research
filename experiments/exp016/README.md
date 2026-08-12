# EXP-016 Full Layer-Strength Validity Study

Run the fixed local-cache representation study:

```bash
python experiments/exp016/full_layer_validity_study.py
```

The study evaluates seven predeclared hidden-state indices per model, six fixed
positive beta values, and all 12 ordered group transitions. It saves pair-level
scalar metrics, aggregates, summaries, and plots only; no generated text or raw
hidden-state tensors are stored.
