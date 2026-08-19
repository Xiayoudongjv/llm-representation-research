# EXP-025 100D-C Consumed Formal Attempt Audit

Classification: `FAILED_AFTER_AUTHORIZATION_CONSUMPTION`

This is a canonical governance/audit record for the consumed EXP-025 formal
attempt v3. It does not reinterpret the frozen scientific design and does not
create a scientific result.

## Attempt Record

- Experiment: `EXP-025`
- Formal command launch count: `3`
- Preconsumption abort count: `2`
- Authorization ID: `dd1ed3c4-3e57-406c-bd67-99231d1190af`
- Authorization path:
  `experiments/exp025/exp025_formal_run_authorization_v3.json`
- Authorization SHA-256:
  `d61632be96f67670a61641f2dff577178a822fa0ac5380fdaf1ea434d14f85d7`
- Consumption path:
  `experiments/exp025/results/authorization_consumption/dd1ed3c4-3e57-406c-bd67-99231d1190af.json`
- Consumption SHA-256:
  `daf2da97aa543c89febf792e19c60f24338682007dc2ad07fbee4d26443a4215`
- Run-attempt ID: `4da5201151ba45dba5197f9923e4b7d1`
- Consumed at UTC: `2026-08-19T06:39:22.067687+00:00`
- Repository commit at consumption: `f3aa196201aa7b1ee80dd2637c7ecd97a3df3e07`
- Runner SHA-256:
  `c6382f44729792bd68f6dab5494f71cb44588da43c2932fedb1970742afbf2a2`

## Event Chain

```text
authorization validation
  -> atomic authorization consumption
  -> _execute_formal_analysis
  -> immediate ProtocolIntegrityError
     "FORMAL_SCIENCE_NOT_AUTHORIZED_IN_100D_A"
```

The production `_execute_formal_analysis` function remained a stub and raised
before any scientific execution path was entered.

## Canonical Statuses

```text
ATTEMPT_STATUS = FAILED_AFTER_AUTHORIZATION_CONSUMPTION
RESULT_STATUS = NO_VALID_RESULT
SCIENTIFIC_STATUS = TECHNICALLY_INVALID_NOT_OBSERVED
V3_AUTHORIZATION_STATUS =
  CONSUMED_BY_TECHNICALLY_INVALID_PRE_INFERENCE_ATTEMPT
VALID_SCIENTIFIC_RESULT_COUNT = 0
```

This attempt is not:

- a negative result;
- a null result;
- a failed replication;
- a failed measurement;
- scientific evidence against any hypothesis.

## Scientific Firewall Facts

```text
DIAG_DATA_ACCESSED = false
EVAL_DATA_ACCESSED = false
DIAG_INFERENCE_PERFORMED = false
EVAL_INFERENCE_PERFORMED = false
SCIENTIFIC_RNG_USED = false
REGISTERED_ANALYSIS_STARTED = false
CANONICAL_RESULT_CREATED = false
EXP025_OUTCOME_OBSERVED = false
```

No frozen scientific parameter, hypothesis, threshold, model, revision,
dataset, partition, condition, checkpoint, calibration variant, statistic, or
routing rule was changed by this attempt.

## Formal Executor Status

```text
FORMAL_EXECUTOR_STATUS = NOT_IMPLEMENTED
FROZEN_IMPLEMENTATION_COVERAGE =
  0/12 registered scientific/publication endpoints implemented
```

The current `run_exp025.py` contains authorization validation and atomic
consumption, but the post-consumption scientific executor is a fail-closed
stub. This audit therefore treats end-to-end formal execution as unimplemented,
even though non-scientific qualification checks previously passed.

## Prior Readiness Supersession

The earlier engineering qualification artifact reported:

```text
ENGINEERING_STATUS = PASS
MEASUREMENT_STATUS = PASS
FORMAL_RUN_READINESS = READY
PRODUCTION_CALL_GRAPH = PASS
```

Those statuses were valid only for the checks actually performed. They did not
establish end-to-end formal scientific executability because the qualification
path never exercised the real `_execute_formal_analysis` implementation.

The historical qualification artifact is preserved unchanged. Its readiness
value is superseded by Task 100D-D governance.

## Recovery Rule Status

```text
RECOVERY_RULE = RECOVERY_RULE_NOT_PREEXISTING
```

No prospective recovery rule existed before this consumed technically-invalid
pre-inference attempt. Any future recovery attempt is therefore governed by a
post-hoc governance amendment, not by the original single-use authorization
protocol alone.

## Evidence Preservation

The following are historical evidence and must not be modified or deleted:

- `experiments/exp025/exp025_formal_run_authorization_v3.json`
- `experiments/exp025/results/authorization_consumption/dd1ed3c4-3e57-406c-bd67-99231d1190af.json`
- `experiments/exp025/engineering/exp025_engineering_qualification.json`
- `experiments/exp025/engineering/EXP-025-100D-PRECONSUMPTION-FAILURE-AUDIT.md`

## Task 100D-D Boundary

This audit was created without:

- executing `--formal-run`;
- accessing DIAGNOSTIC outcomes;
- accessing EVAL outcomes;
- creating a new authorization;
- modifying `run_exp025.py`;
- modifying frozen scientific hypotheses/endpoints;
- reinterpreting EXP-025 scientifically.

## Audit Flags

```text
EXP025_PRIOR_CONSUMED_ATTEMPT_STATUS = TECHNICALLY_INVALID_NOT_OBSERVED
EXP025_PRIOR_SCIENTIFIC_OUTCOME_EXPOSURE = false
EXP025_PREVIOUS_FORMAL_READINESS_SUPERSEDED = true
EXP025_FORMAL_EXECUTOR_STATUS = NOT_IMPLEMENTED
EXP025_IMPLEMENTATION_COVERAGE_BASELINE = 0/12
EXP025_RECOVERY_RULE = RECOVERY_RULE_NOT_PREEXISTING
```
