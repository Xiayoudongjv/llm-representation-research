# Project Status v0.5

## Current Phase

- Controlled geometry replication: complete in Qwen3-1.7B and Gemma-3-1B-IT.
- Representation-level steering and RSM-preservation replication: complete in
  both models.
- Qwen behavioral baseline: provisionally frozen at EXP-011D (60/80 = 0.750).
- Cross-model behavior: not yet measured because Gemma has no behavioral
  benchmark in this project.
- Engineering: 37 local tests passing at the time of this documentation update.
- Paper: draft v0.5, pending freeze and later formal polish.

## Central Status

The project has cross-model representation-level evidence for controlled
geometry, calibrated centroid transitions, and a transition-preservation
tradeoff. It also has direct evidence that the layer and steering operating
point differ between the two studied models. It does not yet have evidence that
these representation transformations affect generated answers.

## Recommended Next Steps

1. **Primary scientific step — generation-time intervention pilot.** Freeze
   paper draft v0.5 first, then test a carefully instrumented pilot with
   explicit controls, no claim of reasoning improvement, and a predeclared
   behavioral evaluation plan.
2. **Secondary robustness step — Gemma behavioral baseline.** Run the existing
   quality-controlled answer benchmark on Gemma before making cross-model
   behavioral comparisons.
3. Add an independent human-annotation sample for scoring reliability.

Neither follow-up is performed by this documentation update.
