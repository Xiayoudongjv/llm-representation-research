# Paper-A Cross-Task Outcome Routing

Status: `PA_EXT_A_001_OUTCOME_ROUTING`

This document defines mutually interpretable prospective outcome routes for
the single authorized Paper-A extension. It does not privilege replication and
does not create results.

## 1. Registered Profile Tuple

For each model:

```text
PROFILE(model) =
(distance_state, source_target_state, low_d_state)
```

Historical profiles:

- Qwen: `(POSITIVE_SUPPORTED, TARGET_DOMINANT, NOT_SUPPORTED)`
- OLMo: `(POSITIVE_SUPPORTED, SOURCE_DOMINANT, SUPPORTED)`
- Llama: `(POSITIVE_SUPPORTED, TARGET_DOMINANT, SUPPORTED)`

## 2. Component State Spaces

- `distance_state`: `POSITIVE_SUPPORTED` or `NOT_SUPPORTED`
- `source_target_state`: `SOURCE_DOMINANT`, `TARGET_DOMINANT`,
  `NO_DOMINANCE`, or `NO_ROW_OR_COLUMN_VARIATION`
- `low_d_state`: `SUPPORTED` or `NOT_SUPPORTED`

Technical or measurement invalidity yields no profile state and routes to A6.

## 3. Primary Outcome Routes

The routes below are evaluated after the frozen statistical contract and
exact-match component construction. Precedence is top-down and exhaustive.

### A1: `THREE_MODEL_PROFILE_STABILITY`

Definition: every model's new profile tuple exactly equals its historical
profile tuple.

Interpretation: profile organization is stable across the original and new
independently designed task panels in the three tested models. Claim ceiling:
two-panel stability only; no universal task-invariant property.

### A2: `PARTIAL_PROFILE_STABILITY`

Definition: not A1, and at least one model has an exact full-tuple match with
its historical profile.

Reporting requirement: list exactly which models matched and which dimensions
changed for the nonmatching models. Partial stability is descriptive, not a
secondary success criterion.

### A3: `TASK_CONDITIONAL_ORGANIZATION`

Definition: not A1 or A2; all valid new distance states remain
`POSITIVE_SUPPORTED`; at least one model changes `source_target_state`; and no
model changes `low_d_state`.

Interpretation: the shared positive distance-associated structure persists, but
source/target organization is task-conditional in one or more models.

### A4: `TASK_CONDITIONAL_RECALIBRATABILITY`

Definition: not A1 or A2; all valid new distance states remain
`POSITIVE_SUPPORTED`; no model changes `source_target_state`; and at least one
model changes `low_d_state`.

Interpretation: the shared positive distance-associated structure persists, but
simple recalibratability is task-conditional in one or more models.

### A5: `BROAD_TASK_CONDITIONAL_PROFILE`

Definition: any other valid outcome not covered by A1-A4. This includes any
valid model changing `distance_state`, or changes in both
`source_target_state` and `low_d_state` within the valid three-model set.

Interpretation: multiple profile dimensions are model-by-task rather than
model-only. The model-only profile framing must be narrowed substantially.

### A6: `NOT_FULLY_ADJUDICATED`

Definition: any model or overall measurement is technically or
measurement-invalid under frozen validity rules.

Interpretation: no structural conclusion. Measurement failure does not imply
absence of the phenomenon. No rescue run, statistic replacement, or layer
subset repair is allowed.

## 4. Shared Distance Structure

In addition to the primary route, report:

- all three new distance states positive: shared positive distance-associated
  structure persists across the two tested panels.
- some positive: shared structure is partial.
- none positive: distance structure is task-conditional in the tested set.

This is a descriptive report, not an independent confirmatory claim.

## 5. Empirical Nonredundancy Boundary

The original evidence supports `LEVEL_2` empirical nonredundancy. The new task
reports whether that nonredundancy persists, disappears, or changes. It must
not be described as statistical independence, causal independence, or
latent-factor independence.

## 6. No Rescue Rules

- A1 is not the only valid outcome.
- A2-A5 are valid scientific outcomes.
- A6 is a measurement boundary, not a negative scientific result.
- No outcome may trigger a second panel, fourth model, statistic change,
  threshold change, or post-hoc harmonization.

## 7. Hard Flags

- `REPLICATION_IS_SUCCESS_ONLY = false`
- `OUTCOME_ROUTING_FROZEN = true`
- `REAL_EXT_A_RESULTS_CREATED = false`