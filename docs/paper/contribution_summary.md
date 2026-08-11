# Contribution Summary

## Core Question

When does a representation-level transformation move hidden states toward a
target task-associated region while preserving useful relational structure?

## Main Idea

Use controlled prompt groups to measure hidden-state geometry, apply calibrated
centroid steering between groups, and assess transition success together with an
RSM-based proxy for relational preservation. Use the resulting frontier and
invariant-aware beta selection to identify an exploratory operating point.

## Completed Evidence Chain

### Geometry: EXP-001 / EXP-002 / EXP-003

Final-layer geometry, layer-wise analysis, and paraphrase controls provide
cautious evidence for task-associated structure in the controlled prompt set.

### Transformation: EXP-004 / EXP-004B / EXP-005

The steering baselines show that calibrated centroid differences can induce
representation-level transitions across all 12 ordered group pairs, with beta
0.75 reaching full assignment in the current setting.

### Validity: EXP-006 / EXP-007 / EXP-008

The RSM proxy exposes a trade-off between assignment and relational distortion.
EXP-007 identifies beta 0.75 as a frontier point, and EXP-008 shows that it is
retained under most invariant-aware penalty settings.

## What This Project Currently Shows

It shows a reproducible exploratory procedure for measuring task-associated
geometry and selecting calibrated representation-level transformations in
`Qwen/Qwen3-1.7B`. In this controlled setting, beta 0.75 is a stable operating
point across most tested penalties.

## What It Does Not Yet Show

It does not show generation-time control, answer-level reasoning improvement,
true logical or semantic invariance, a proven semantic latent space, learned
constrained transformations, or generalization beyond this model and prompt
set.

## Why It Matters

The work makes the distinction between representation movement and valid
transformation explicit. It provides measurable intermediate criteria and a
clear next test: determine whether representation-level validity relates to
answer-level task outcomes.
