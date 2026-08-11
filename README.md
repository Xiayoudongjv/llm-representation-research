# LLM Representation Research

Research on representation geometry, task-conditioned transformations and relational invariants in LLM reasoning.

Current Stage:

EXP-001

## Current Milestone: EXP-000B Hidden State Extraction

Run the syntax check:

```bash
python -m compileall src experiments
```

Run the fallback model:

```bash
python experiments/exp000/extract_hidden_states.py --use_fallback
```

Run Qwen:

```bash
python experiments/exp000/extract_hidden_states.py --model_name Qwen/Qwen3-1.7B
```

The extraction writes metadata only; full hidden-state tensors and model
weights are not committed.

## Current Milestone: EXP-001 Representation Geometry Baseline

Run the syntax check:

```bash
python -m compileall src experiments
```

Run the fallback geometry baseline:

```bash
python experiments/exp001/compute_geometry.py --use_fallback
```

Run with Qwen:

```bash
python experiments/exp001/compute_geometry.py --model_name Qwen/Qwen3-1.7B
```

The geometry baseline saves compact metadata, cosine similarities, PCA
coordinates, and a PCA plot. Full hidden-state tensors and model weights are
not saved.

Environment Setup

Roadmap

EXP000
↓

Representation

↓

Geometry

↓

Steering

↓

Task-conditioned Transformation

↓

Relational Invariant

↓

Papers
