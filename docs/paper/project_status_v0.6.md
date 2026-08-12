# Project Status v0.6

## Current Phase

Evidence restructuring after the first behavioral pilot.

## Completed

- Controlled representation geometry and cross-model replication.
- Centroid-steering baselines and sampled operational layer-role analyses.
- Research Audit v1.
- EXP-018 independent representation validation.
- Qwen hook-semantics diagnostic.
- EXP-017 frozen generation-time behavioral pilot.

## Current Strongest Results

The strongest positive result is independently validated task-directed
representation transition: EXP-018's held-out frozen probe favored TASK over
matched random and opposite in all 216 tested conditions.

The strongest negative result is that this representation-level transition did
not yield a task-specific behavioral advantage over matched random in EXP-017.
Both TASK and RANDOM had .6375 source-task accuracy, below the exactly replicated
.750 baseline.

## Current Major Unresolved Question

Does the hidden-state transition lack behavioral consequences entirely, or did
the current source-accuracy outcome fail to measure target-sensitive behavioral
change? The current record does not answer this question.

## Future-Work Boundary

Priority directions are: (1) an independent target-sensitive behavioral
evaluator; (2) intervention-timing decomposition of prefill, decode, and both;
and (3), only if target-sensitive behavior exists, a layer-wise behavioral
controllability study. No post-hoc beta or layer search should be used merely
to reverse the negative EXP-017 result. RSM should not return as a core metric
without new independent justification.
