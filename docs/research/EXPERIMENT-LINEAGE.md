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
- EXP-025 -> cross-model panel replication on `allenai/OLMo-2-0425-1B-Instruct`; registered `D-_G+`.
- EXP-026 -> completed valid registered result; material model-dependent compatibility organization; route `P3`.

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

## EXP-025 Result Summary

- Canonical result SHA-256:
  `bbac2f03b24bdf2ec93485c201d3c0cf50588ed51659e607bb97b231181765a9`
- Execution classification: `POST_HOC_PROTOCOL_RECOVERY`
- `D`: `NOT_SUPPORTED`, direction `D-`; 7 positive, 2 negative, 1 zero; exact
  one-sided `p = 0.08984375`.
- `G`: `SUPPORTED`, direction `G+`; 7 positive, 1 negative, 2 zero; exact
  one-sided `p = 0.03515625`.
- RQ3 susceptibility predictor: rho `0.3765432098765432`, exact permutation
  `p = 0.14020502645502644`, support false.
- Registered routing: `D-_G+`.
- Claim boundary: core degradation existence remains supported by the Qwen
  chain; cross-model degradation breadth is not established; recovery has
  limited second-family support.

## EXP-026 Result Summary

- Canonical result SHA-256:
  `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551`
- Authorization ID: `b3763f43-d365-4a24-86fc-263f53dc84cb`
- Authorization SHA-256: `83adcafa0648e94d8a50b7132bc9713abf2d9ee58bb930690b775ec93248dcd2`
- Consumption SHA-256: `4a35bfed3622ef82540e6bd42a843a56c9b5c465a686c1e2201ea5de012cd82a`
- Runner SHA-256: `6ab29c35889ce35b9d4bc9ee98d2665865a088312940f10815714a574d2060a0`
- Registered route: `P3`
- Scientific status: `P3_MATERIALLY_DIFFERENT_MODEL_SIGNATURES`
- Qwen: distance `POSITIVE_SUPPORTED`; SDI `TARGET_DOMINANT`; LOW-D `NOT_SUPPORTED`.
- OLMo: distance `POSITIVE_SUPPORTED`; SDI `SOURCE_DOMINANT`; LOW-D `SUPPORTED`.
- Claim boundary: model-dependent structural difference; no architecture/family causality.

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
- Explicit Task 100A froze a bounded EXP-025 cross-model replication design;
  execution was later completed under a post-hoc protocol-recovery
  authorization after pre-inference engineering failure.

Post-EXP-025 branch:

- EXP-025 completed as a valid `POST_HOC_PROTOCOL_RECOVERY` result.
- `D-` means cross-model degradation breadth is not established; the next
  highest-information question is model/depth compatibility, not immediate
  operator-capacity escalation.
- `G+` gives limited cross-model recovery support.
- Primary next direction: `MODEL_DEPTH_COMPATIBILITY_PROFILE`.
- Backup next direction:
  `OPERATOR_CAPACITY_MINIMUM_SUFFICIENT_ALIGNMENT`.

Post-EXP-026 branch:

- EXP-026 completed as a valid registered result with route `P3`.
- Primary next scientific task: `THIRD_MODEL_INDEPENDENT_VALIDATION`.
- `P4` operator-capacity route remains `LIVE_BUT_DEFERRED`.
- Next task: `102A_EXP027_THIRD_MODEL_SELECTION_AND_DESIGN_AUDIT`.

Post-Task-101B branch (superseded):

- Task 101B froze the EXP-026 full source/target compatibility matrix design.
- Later tasks implemented, qualified, authorized, executed, and audited EXP-026;
  the valid canonical result is now the authoritative post-design state.

This is an experimental-priority decision, not a scientific claim.

Post-102A-ASSET theory registration:

- Residual-Flow registered as a prospective theoretical asset; no new experiment was created.
- EXP-027 remains `THIRD_MODEL_INDEPENDENT_TRIANGULATION`.
- Paper B candidate: minimum near-identity compatibility correction with registered structural preservation; not committed.
