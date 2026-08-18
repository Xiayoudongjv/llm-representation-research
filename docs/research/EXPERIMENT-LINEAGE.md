# Experiment Lineage

This file records the cumulative scientific chain and the current
result-conditioned decision branch. It is navigation/synthesis only.
Canonical experimental artifacts outrank it.

## Cumulative Scientific Chain

- EXP-018 -> local representational manipulability.
- EXP-020A -> same-family larger-model replication.
- EXP-017 -> manipulability did not produce task-specific behavioral control.
- EXP-019 -> independent evaluator failed generalization; behavioral targetness unresolved.
- EXP-021 -> fixed source-semantic readout failed to remain qualified across deeper clean checkpoints.
- EXP-022A -> diagnosed fixed-frame degradation with the A0/A1/A2 ladder.
- EXP-023 -> independent preregistered `NO_REPLICATION`; one strong featurewise-calibration rescue split and one null split.

## EXP-022A Result Summary

- Primary: partial split-dependent fixed-frame degradation.
- Mechanistic descriptive clue: featurewise recalibration recovery.
- Not supported: same-family refit rescue.
- Next research question: Is the A1 recovery a reproducible featurewise/diagonal calibration phenomenon, or an artifact of the current small controlled dataset/split?

## EXP-023 Result Summary

- Primary: `NO_REPLICATION`.
- Split A: substantial fixed-readout degradation and substantial featurewise
  recalibration rescue (`G_cal = +0.25`, supported).
- Split B: little fixed-readout degradation and no recalibration rescue
  (`G_cal = 0.0`, unsupported).
- Secondary: Split A mean/scale decomposition suggests a larger mean than scale
  signal; descriptive only.
- Claim boundary: calibration rescue is conditional, not general.

## Result-Conditioned Decision Tree

- A0 degradation: present directionally in both splits; primary-supported only in Split B.
- A1: descriptive recovery.
- A2: no preregistered rescue.
- Actual branch selected: `REPLICATE / STRESS-TEST FEATUREWISE RECALIBRATION`.
- Deferred: general affine/nonlinear coordinate transport.

Post-EXP-023 branch:

- General calibration replication: `NOT_SUPPORTED`.
- Next question: test an independent susceptibility predictor separated from
  confirmatory EVAL.
- Do not automatically launch a generic replication or EXP-024.

This is an experimental-priority decision, not a scientific claim.
