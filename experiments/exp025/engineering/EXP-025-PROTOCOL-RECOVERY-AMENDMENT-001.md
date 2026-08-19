# EXP-025 Protocol Recovery Amendment 001

Amendment ID: `EXP025_PROTOCOL_RECOVERY_AMENDMENT_001`

Classification: `POST_HOC_GOVERNANCE_AMENDMENT`

This document records a post-hoc governance decision for the EXP-025 consumed
technically-invalid pre-inference formal attempt. It is not a pre-registered
recovery rule and it is not a scientific design change.

## Status

```text
EXP025_PROTOCOL_RECOVERY_AMENDMENT_CREATED = true
EXP025_RECOVERY_AMENDMENT_CLASS = POST_HOC_GOVERNANCE_AMENDMENT
EXP025_SCIENTIFIC_DESIGN_CHANGED = false
EXP025_PREVIOUS_FORMAL_READINESS_SUPERSEDED = true
```

## Explicit Boundary

```text
THIS IS A POST-HOC GOVERNANCE AMENDMENT,
NOT A PRE-REGISTERED RECOVERY RULE.
```

Because no recovery rule existed before the consumed invalid attempt, a future
run is not covered by the original single-use authorization protocol alone.
Any future recovery attempt must be authorized separately and must be labeled
as a recovery attempt.

## Conditions Met by the Consumed Attempt

The amendment may be considered only because all of the following facts are
independently established:

1. The prior authorization was consumed.
2. The failure was a deterministic implementation defect.
3. No DIAGNOSTIC dataset was accessed.
4. No EVAL dataset was accessed.
5. No scientific inference was performed.
6. No scientific RNG was used.
7. No registered statistic was computed.
8. No scientific outcome was viewed.
9. No scientific parameter, hypothesis, threshold, model, or layer was changed.

## Frozen-No-Change List

The recovery amendment must prohibit changes to all of the following:

- research questions;
- primary and secondary endpoints;
- model;
- model revision;
- dataset;
- FIT/DIAGNOSTIC/EVAL partitions;
- 10-condition panel;
- condition order;
- reference checkpoint;
- final checkpoint;
- classifier definition;
- recalibration definitions;
- `S_diag` definition;
- `G_eval` definition;
- Spearman statistic;
- permutation procedure;
- thresholds;
- routing rules.

No rescue is permitted:

- no layer shopping;
- no model switch;
- no condition dropping;
- no threshold adjustment;
- no alternate statistics.

## Supersession of Prior Readiness

The prior engineering qualification artifact is retained as historical
evidence:

`experiments/exp025/engineering/exp025_engineering_qualification.json`

Its previous values:

```text
ENGINEERING_STATUS = PASS
MEASUREMENT_STATUS = PASS
FORMAL_RUN_READINESS = READY
PRODUCTION_CALL_GRAPH = PASS
```

are now interpreted as:

```text
HISTORICALLY_VALID_FOR_THE_CHECKS_ACTUALLY_PERFORMED
BUT_INSUFFICIENT_FOR_FORMAL_EXECUTION_READINESS
```

They must not be reused as evidence of end-to-end formal executability.

## Future Recovery Authorization Semantics

No recovery authorization is created in Task 100D-D.

Any future authorization must:

- be explicitly labeled:
  `PROTOCOL_RECOVERY_ATTEMPT_AFTER_PREINFERENCE_TECHNICAL_INVALIDITY`;
- preserve the machine-schema-required formal purpose field
  `purpose = SINGLE_USE_FORMAL_RUN` if the runner requires it;
- bind the repaired runtime commit, not any earlier commit;
- bind the repaired runner SHA-256;
- bind the post-repair qualification SHA-256;
- be single-use and consumed atomically;
- not reauthorize the already-consumed v3 authorization.

Governance classification and machine schema purpose are separate concepts.

## Recovery Authorization Gate

A recovery authorization may be issued only after:

1. Task 100D-E implements the frozen formal executor.
2. The specification gaps identified in the formal-executor specification are
   resolved by a frozen authority or an explicit binding decision.
3. The end-to-end qualification standard is met using synthetic or frozen
   non-outcome fixtures.
4. The implementation coverage matrix is no longer `0/12`.
5. A focused production-readiness rereview confirms the real production call
   graph.

## Firewall and Non-Execution

Task 100D-D leaves:

```text
DIAG_DATA_ACCESSED = false
EVAL_DATA_ACCESSED = false
DIAG_INFERENCE_PERFORMED = false
EVAL_INFERENCE_PERFORMED = false
SCIENTIFIC_RNG_USED = false
VALID_SCIENTIFIC_RESULT_COUNT = 0
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
```

## Required Flags

```text
EXP025_PROTOCOL_RECOVERY_AMENDMENT_CREATED = true
EXP025_RECOVERY_AMENDMENT_CLASS = POST_HOC_GOVERNANCE_AMENDMENT
EXP025_SCIENTIFIC_DESIGN_CHANGED = false
EXP025_PREVIOUS_FORMAL_READINESS_SUPERSEDED = true
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = true
EXP025_NEXT_TASK = 100D_E_IMPLEMENT_FROZEN_FORMAL_EXECUTOR
```
