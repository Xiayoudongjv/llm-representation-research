# EXP-025 End-to-End Qualification Standard

Classification: `GOVERNANCE_AND_QUALIFICATION_STANDARD_ONLY`

This document replaces the prior end-to-end readiness interpretation for
EXP-025. It does not alter the historical engineering qualification artifact
and does not grant formal-run readiness.

## Superseded Readiness Definition

The prior qualification artifact reported:

```text
ENGINEERING_STATUS = PASS
MEASUREMENT_STATUS = PASS
FORMAL_RUN_READINESS = READY
PRODUCTION_CALL_GRAPH = PASS
```

That definition was insufficient because it never exercised the real
post-consumption scientific executor. The prior artifact is preserved and
classified as:

```text
HISTORICALLY_VALID_FOR_THE_CHECKS_ACTUALLY_PERFORMED
BUT_INSUFFICIENT_FOR_FORMAL_EXECUTION_READINESS
```

## New Readiness Requirement

Future:

```text
FORMAL_RUN_READINESS = READY
```

must be impossible unless a qualification test exercises the real production
path:

```text
run_formal
  -> authorization validation
  -> atomic authorization consumption
  -> real _execute_formal_analysis
  -> canonical-result construction
  -> publication boundary
```

Qualification tests must use synthetic fixtures or frozen non-outcome fixtures
instead of real DIAGNOSTIC/EVAL scientific data. They must prove algorithmic
reachability, not scientific outcome correctness.

## Firewall Requirements During Qualification

```text
FIT may train classifier/recalibration parameters.
DIAGNOSTIC may only compute registered S_diag quantities.
EVAL may only compute registered held-out evaluation quantities.
No fitted object may use DIAGNOSTIC or EVAL.
No DIAGNOSTIC result may alter EVAL processing.
No EVAL result may alter analysis choices.
```

The qualification must keep real outcomes unreachable:

```text
EXP025_QUALIFICATION_DIAG_OUTCOME_VIEWED = false
EXP025_QUALIFICATION_EVAL_OUTCOME_VIEWED = false
EXP025_QUALIFICATION_FORMAL_DATASET_MODEL_INFERENCE = 0
```

## Required End-to-End Test Surface

The following tests must exist and pass before any future formal authorization:

1. Fresh authorization followed by full mocked/synthetic formal execution.
2. Exactly-once authorization consumption.
3. Science unreachable before authorization consumption.
4. FIT/DIAGNOSTIC/EVAL firewall enforcement.
5. All four calibration variants exercised:
   `A0`, `A_mu`, `A_sigma`, `A_mu_sigma`.
6. Class probability mapping through `classifier.classes_`.
7. Frozen condition ordering.
8. `S_diag` calculation.
9. `G_eval` calculation.
10. Spearman calculation with ties.
11. Exact permutation p-value on a hand-computable fixture.
12. Routing classification.
13. Canonical-result schema validation.
14. Provenance validation.
15. Atomic publication.
16. Existing-result rejection.
17. Double-consumption rejection.
18. Publication failure fail-closed behavior.

## Acceptance Criteria

The future engineering qualification is acceptable only when all of the
following are true:

- The real `run_formal -> _execute_formal_analysis -> publication` call graph is
  executed by a test using non-outcome fixtures.
- Authorization validation and atomic consumption occur exactly once.
- No scientific code is reachable before consumption.
- The four calibration variants are computed through production helpers.
- Condition-level `S_diag` and `G_eval` are produced in frozen condition order.
- The exact permutation count is `3,628,800`.
- The result object validates against the canonical schema.
- The result publication path is atomic and refuses existing results.
- No real DIAGNOSTIC/EVAL outcome is viewed.
- No canonical scientific result is created during qualification.

## Non-Acceptance Statuses

The following are not acceptable for future formal readiness:

- a static call-graph check alone;
- a qualification-only extraction implementation;
- a unit test that passes while production remains broken;
- a test that mocks the `_execute_formal_analysis` boundary without exercising
  production code;
- a test that reads real DIAGNOSTIC/EVAL outcome data.

## Implementation Result

Task 100D-E implemented the formal executor and ran the new synthetic
formal-pipeline qualification. The real production call graph was exercised
with isolated synthetic fixtures; no real DIAGNOSTIC/EVAL outcome was accessed.

```text
EXP025_FORMAL_PIPELINE_QUALIFICATION = PASS
EXP025_REAL_PRODUCTION_EXECUTOR_REACHED = true
EXP025_ATOMIC_CONSUMPTION_TEST = PASS
EXP025_ATOMIC_PUBLICATION_TEST = PASS
EXP025_FORMAL_RUN_READINESS = READY
```

## Recovery Authorization Gate

After the future implementation passes this standard:

1. Create exactly one recovery authorization labeled:
   `PROTOCOL_RECOVERY_ATTEMPT_AFTER_PREINFERENCE_TECHNICAL_INVALIDITY`.
2. Preserve the machine-schema-required purpose
   `SINGLE_USE_FORMAL_RUN` if the runner requires it.
3. Bind the repaired runtime commit and runner SHA-256.
4. Consume it atomically.
5. Execute exactly one formal run.

No recovery authorization is created by this document.

## Required Flags

```text
EXP025_END_TO_END_QUALIFICATION_STANDARD_SPECIFIED = true
EXP025_PREVIOUS_FORMAL_READINESS_SUPERSEDED = true
EXP025_FIT_DIAG_EVAL_FIREWALL_SPECIFIED = true
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = true
EXP025_FORMAL_EXECUTOR_IMPLEMENTED = true
EXP025_FORMAL_PIPELINE_QUALIFICATION = PASS
EXP025_FORMAL_RUN_READINESS = READY
EXP025_NEXT_TASK = 100D_F_ADVERSARIAL_FORMAL_EXECUTOR_REREVIEW
```
