# EXP-028 Runner Qualification

**Task:** `103D_EXP028_RUNNER_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION`
**Status:** `SYNTHETICALLY_QUALIFIED`
**Scientific contract:** `FINAL_FROZEN_PRE_DATA`

## Scope

This task implements the frozen EXP-028 engineering surface:

- `experiments/exp028/run_exp028.py`
- `experiments/exp028/validate_exp028_result.py`
- `tests/test_exp028_runner.py`
- `experiments/exp028/engineering/exp028_runner_synthetic_qualification.json`

The runner exposes:

- `--static-preflight`
- `--synthetic-qualification`
- `--formal-run`

Formal-run mode is authorization-gated. Task 103D did not invoke formal-run,
create an authorization, access real FIT/DIAG/EVAL, load a real model, or
create a canonical scientific result.

## Implemented Contract

- T0 identity, T1 inherited moment recalibration, and T2 paired coordinatewise
  affine OLS.
- Label-free, FIT-only T2 with no cross-coordinate mixing.
- Frozen numerical-degeneracy handling without tunable epsilon.
- `DELTA_RM` and `DELTA_RO` sign conventions.
- Equal-weight aggregation: source-family mean -> condition mean -> layer-pair
  mean -> model mean.
- Condition-stratified source-family cluster bootstrap using
  `numpy.random.PCG64(20260819)`, 5000 replicates.
- One-sided 95% lower support bound (`q_0.05`) and central 90% descriptive
  interval `[q_0.05, q_0.95]`.
- Exact model-level and three-model routing.
- Secondary pair-break control.
- JSON-safe recursive serialization and atomic canonical publication with
  duplicate-result rejection.
- Single-use authorization lifecycle interface.
- Outcome-blind progress reporting.

## Synthetic Coverage

The focused pytest suite contains 49 passing tests covering the required
adversarial cases, including label leakage, EVAL/DIAG operator tuning, old-panel
and source-family reuse, numerical degeneracy, operator orientation, endpoint
sign/reference values, bootstrap clustering and percentile semantics, route
coverage, operator-capacity rejection, result-schema corruption, serialization
safety, and authorization reuse.

Warnings observed during the suite are `sklearn` deprecation warnings for the
frozen `LogisticRegression(penalty=...)` surface. They are classified as
`KNOWN_DEPRECATION` and are not repaired because the frozen classifier contract
must remain unchanged.

## Known Limitations

- 103D uses synthetic representations only; no real model weights are loaded.
- The real scientific panel is not generated in this task.
- Formal-run currently validates and gates the authorization lifecycle but
  stops before scientific execution because a frozen panel and representation
  archive do not yet exist.

## Remaining Gates

- `103E_EXP028_RUNNER_REREVIEW_AND_FRESH_PANEL_GENERATION_QUALIFICATION`
- Fresh-panel generation and authority freeze
- Neutral model/real-model extraction qualification if required by a later task
- Single-use formal authorization creation
- Exactly one authorized formal-run
