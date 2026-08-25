# Paper A EXT-B: Terminal Dataset-Stage Failure

## Disposition

EXT-B is terminated at the dataset-construction gate.

```text
EXT_B_LIFECYCLE_STATUS = TERMINATED
EXT_B_TERMINATION_STAGE = DATASET_CONSTRUCTION
EXT_B_TERMINATION_REASON = FROZEN_GLOBAL_RENDERED_TEXT_DUPLICATE_GATE_FAILURE
EXT_B_FURTHER_SCIENTIFIC_AMENDMENT_ALLOWED = false
EXT_B_FURTHER_DATASET_RETRY_ALLOWED = false
```

The independent review classified the single V2 recovery production attempt
as `CLASS A: TRUE_FROZEN_DATASET_VALIDATION_FAILURE`.  The V2 authority
uniquely requires global exact-byte and normalized-text rejection across all
records, and both the repaired builder and validator conform to that rule.
The construction therefore failed its prospectively frozen duplicate gate.

The failure occurred after the combined in-memory record list was assembled
and before any temporary or canonical publication.  No canonical source bank,
task dataset, panel, manifest, or freeze binding was created.

## Scientific boundary

EXT-B did not reach model inference and did not create a canonical external
panel.  It did not test model-level cross-task robustness, and no model
replication or nonreplication result exists.  Cross-task/task-panel robustness
is therefore `NOT_ESTABLISHED`.

This outcome must not be described as a model failure, a representation
failure, a task-invariance failure, or a failed model-family effect.

The core Paper A science and the EXP-026/EXP-027 results are unaffected.

## Bound state

```text
CORE_PAPER_A_SCIENCE_COMPLETE = true
EXT_B_STATUS = TERMINATED_PRE_MODEL_INFERENCE_AT_DATASET_GATE
PAPER_A_CROSS_TASK_CLAIM = NOT_ESTABLISHED
EXT_B_CANONICAL_PANEL_CREATED = false
EXT_B_MODEL_INFERENCE_PERFORMED = false
EXT_B_CROSS_TASK_ROBUSTNESS_TESTED = false
EXT_B_CROSS_TASK_ROBUSTNESS_STATUS = NOT_ESTABLISHED
EXT_B_MODEL_AUTHORIZATION_ALLOWED = false
EXT_B_V3_CREATED = false
```

The terminal manifest binds the frozen authorities, the science-neutral
condition-assignment recovery, the failed production-attempt record, the
repaired builder and validator, and this archival review document.
