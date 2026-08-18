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
- EXP-024 -> valid condition-panel susceptibility test; simple independent degradation-magnitude predictor `NOT_SUPPORTED`; broad descriptive calibration benefit observed in 10/10 conditions.

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

## EXP-024 Result Summary

- Primary: `NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`.
- Observed rho: `0.28401877872187725`.
- Exact one-sided permutation p: `0.2115079365079365`.
- Registered support rule: `rho > 0 AND p <= 0.05`; not satisfied.
- Descriptive panel observation: `S_diag > 0` and `G_eval > 0` in all 10/10
  conditions.
- Claim boundary: broad panel-level calibration benefit is descriptive; a simple
  independent degradation-magnitude susceptibility predictor is not supported.

## Result-Conditioned Decision Tree

- A0 degradation: present directionally in both splits; primary-supported only in Split B.
- A1: descriptive recovery.
- A2: no preregistered rescue.
- Actual branch selected: `REPLICATE / STRESS-TEST FEATUREWISE RECALIBRATION`.
- Deferred: general affine/nonlinear coordinate transport.

Post-EXP-024 branch:

- Simple independent susceptibility prediction: `NOT_SUPPORTED`.
- Preserve the mechanism gap; do not automatically launch EXP-025 or a
  replication rescue.
- Paper-A full prose drafting may proceed with the bounded story.
- Second-model breadth is optional/venue-uplift, not a validity requirement for
  the current bounded manuscript.

This is an experimental-priority decision, not a scientific claim.
