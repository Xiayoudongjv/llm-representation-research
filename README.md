# LLM Representation Research

Research on representation geometry, task-conditioned transformations and relational invariants in LLM reasoning.

Current Stage:

EXP-011 dataset design added; no Qwen run yet

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

## Current Milestone: EXP-004B Calibrated Static Steering

Run the calibrated representation-level steering baseline:

```bash
python experiments/exp004b/calibrated_steering.py --model_name Qwen/Qwen3-1.7B --layer 16 --source_group logic --target_group causality
```

EXP-004B scales the raw centroid-difference vector by beta and reports
similarity movement, centroid assignments, and relative perturbation size. It
is not generation-time steering and does not save full hidden-state tensors.

## Current Milestone: EXP-005 Multi-pair Calibrated Steering Generalization

Run the multi-pair steering analysis:

```bash
python experiments/exp005/multipair_steering.py --model_name Qwen/Qwen3-1.7B --layer 16
```

EXP-005 evaluates all 12 ordered transitions among the four controlled task
groups. It saves pair summaries, asymmetry metrics, and heatmaps without saving
full hidden-state tensors.

## Current Milestone: EXP-006 Relational Invariant Score

Run the relational invariant analysis:

```bash
python experiments/exp006/relational_invariant_score.py --model_name Qwen/Qwen3-1.7B --layer 16
```

EXP-006 compares source-group representation similarity matrices before and
after calibrated steering. RSM correlation is only a proxy invariant; full
hidden-state tensors are not saved.

## Current Milestone: EXP-007 Transition Validity Frontier

Run the frontier analysis over EXP-006 results:

```bash
python experiments/exp007/validity_frontier.py
```

EXP-007 summarizes the trade-off between transition success, invariant
violation, and perturbation magnitude. Its scalar validity scores are
exploratory and do not define a final theory.

## Current Milestone: EXP-008 Invariant-constrained Steering

Run the invariant-constrained selection analysis over existing EXP-006 and
EXP-007 results:

```bash
python experiments/exp008/invariant_constrained_selection.py
```

EXP-008 selects among discrete beta candidates using assignment success,
invariant violation, and relative perturbation penalties. It does not rerun
Qwen, learn a transformation, or save full hidden-state tensors.

## Current Milestone: EXP-009 Answer-level Reasoning Evaluation

Run the normal-generation behavioral baseline:

```bash
python experiments/exp009/run_answer_eval.py --model_name Qwen/Qwen3-1.7B
```

EXP-009 evaluates concise answers on 24 deterministic prompts across logic,
causality, analogy, and definition. It does not apply activation steering or
save full hidden-state tensors.

## Current Milestone: EXP-009B Scoring Audit and Answer Normalization

Run the conservative audit over existing EXP-009 outputs:

```bash
python experiments/exp009b/audit_scoring.py
```

EXP-009B compares strict accuracy with an audited upper bound and labels
scoring misses, partial answers, ambiguous cases, and likely wrong answers. It
does not rerun Qwen or use an LLM judge.

## Current Milestone: EXP-010 Representation Validity vs Answer Difficulty

Run the exploratory group-level analysis over existing representation and
answer-level results:

```bash
python experiments/exp010/representation_behavior_link.py
```

EXP-010 computes four-group Pearson correlations for exploratory comparison.
It is non-causal, underpowered, and does not rerun Qwen.

## Current Milestone: EXP-011 Expanded Answer-level Dataset

Validate the expanded dataset without running a model:

```bash
python experiments/exp011/validate_dataset.py
```

EXP-011 adds 80 deterministic short-answer items across logic, causality,
analogy, and definition. It is dataset design only; Qwen evaluation is deferred.

## Project Status

Experiments are complete through EXP-010. Paper Draft v0.3 and the associated
status, results, and claims documents are available under `docs/paper`.
Engineering utilities for IO, representation extraction, and plotting are
covered by local tests.

## Developer Checks

```bash
python -m compileall src experiments
python -m pytest tests
```

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
