# Next-Phase Preregistration

## Research Questions

- **RQ1:** Does independently validated target-directed representation movement
  reproduce in `Qwen/Qwen3-4B` under a frozen protocol?
- **RQ2:** Only if RQ1 passes at its primary representation gate, does the same
  intervention yield behavioral specificity beyond matched-norm random?
- **RQ3:** After one intervention, does the independently measured
  target-associated effect persist, attenuate, disappear, reverse, or differ
  from controls through downstream layers?

RQ3 descriptions are mechanistic and descriptive. The protocol does not claim
that downstream layers correct or compensate for an intervention.

## Frozen Phase Boundaries

EXP-019 is closed after failed independent measurement validation. This phase
does not rescue that evaluator, modify Final-200, inspect EXP-017 outcomes for
parameter selection, expand task taxonomy, search layers or betas, or add a
second 4B model. After EXP-020 and EXP-021 (plus a conditional EXP-022 only if
triggered), the project stops experiments and returns to paper integration.

## Hardware and Precision Boundary

`Qwen/Qwen3-4B` is the primary new model. Qualification uses neutral diagnostic
strings only, trying native dtype at batch size one, then safe CPU offload only
after native memory failure, then one deterministic 4-bit configuration only
if offload is unavailable or impractical. The first workable mode is frozen.
If it is quantized, EXP-020 is described as a higher-parameter quantized
replication, not a pure model-scale ablation.

## Claim Ceiling

Allowed claims require new evidence: held-out task-associated representation
replication; behavioral specificity under frozen controls; and descriptive
downstream persistence patterns. Forbidden claims include reasoning
improvement, true cognitive task spaces, representation-caused behavioral task
conversion, active downstream correction, universal scale trends, and semantic
task identity validated by EXP-019.
