# LLM Representation Research

Research on representation geometry, task-conditioned transformations and relational invariants in LLM reasoning.

Current Stage:

EXP-004

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

## Current Milestone: EXP-002 Layer-wise Representation Geometry

Run the layer-wise Qwen analysis:

```bash
python experiments/exp002/analyze_layers.py --model_name Qwen/Qwen3-1.7B
```

EXP-002 evaluates layers 0, 4, 8, 12, 16, 20, 24, and 28 using one forward
pass per prompt. It saves only compact metrics, diagnostics, and plots; full
representation tensors are not saved.

## Current Milestone: EXP-003 Lexical and Paraphrase Control

Run the controlled Qwen analysis:

```bash
python experiments/exp003/analyze_controlled_geometry.py --model_name Qwen/Qwen3-1.7B
```

EXP-003 evaluates original-style and paraphrased prompts across the same
selected layers. It saves compact control metrics and plots only; full hidden
state tensors are not saved.

## Current Milestone: EXP-004 Static Steering Vector Baseline

Run the representation-level steering baseline:

```bash
python experiments/exp004/static_steering.py --model_name Qwen/Qwen3-1.7B --layer 16 --source_group logic --target_group causality
```

EXP-004 applies a normalized centroid-difference vector to source-group
representations. It is not generation-time steering and does not save full
hidden-state tensors.

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
