# EXP-026 Routing Rules

Status: `FROZEN_DESIGN_NOT_RUN`

These routing rules are frozen before any EXP-026 DIAGNOSTIC/EVAL outcome
access. They translate registered structural summaries into the next research
priority without overclaiming architecture or family causality.

## Common Support Class Abbreviations

For each model `m`:

- `DIST_SUPPORT[m]`:
  `POSITIVE_SUPPORTED` or `NOT_SUPPORTED`.
- `SDI_CLASS[m]`:
  `SOURCE_DOMINANT`, `TARGET_DOMINANT`, `NO_DOMINANCE`, or
  `NO_ROW_OR_COLUMN_VARIATION`.
- `LOW_D_SUPPORT[m]`:
  `SUPPORTED`, `NOT_SUPPORTED`, or `NOT_EVALUABLE`.
- `LOCALIZATION[m]` and `LOCALIZATION_R[m]` are scalar descriptive values.
- `BOUNDARY_SET[m]` is the set of maximizing target-boundary indices for `J`.
- `BOUNDARY_SET_R[m]` is the set of maximizing target-boundary indices for
  `J_R`.

## P1: Operator Capacity / Transition-Specific Operator

Per-model trigger `P1[m]` requires all of:

1. `DIST_SUPPORT[m] == POSITIVE_SUPPORTED`;
2. `LOW_D_SUPPORT[m] == SUPPORTED`;
3. `LOCALIZATION[m] >= 0.5`;
4. `LOCALIZATION_R[m] >= 0.5`;
5. `BOUNDARY_SET[m]` and `BOUNDARY_SET_R[m]` intersect.

Interpretation: strong localized structure is descriptively supported and
recovery concentrates around the same transition.

Global route `P1` triggers if `P1[Q]` or `P1[O]` is true.

Next priority when selected:

```text
OPERATOR_CAPACITY / TRANSITION_SPECIFIC_OPERATOR
```

## P2: Reference Organization and Source-Anchor Resolution

Per-model trigger `P2[m]` requires:

```text
SDI_CLASS[m] == SOURCE_DOMINANT
```

Global route `P2` triggers if `P2[Q]` or `P2[O]` is true.

Interpretation: source/reference dependence is the dominant registered signal.

Next priority when selected:

```text
REFERENCE_ORGANIZATION_AND_SOURCE_ANCHOR_RESOLUTION
```

## P3: Third-Model Independent Validation

Global route `P3` triggers if the two models have materially different
registered structural signatures, defined as either:

1. `DIST_SUPPORT[Q] != DIST_SUPPORT[O]`; or
2. `SDI_CLASS[Q] != SDI_CLASS[O]` and both classes are in
   `{SOURCE_DOMINANT, TARGET_DOMINANT}`.

Interpretation: the Qwen and OLMo structural profiles are materially different.

Next priority when selected:

```text
THIRD-MODEL INDEPENDENT VALIDATION
```

Candidate third model may later be `Llama-3.2-1B-Instruct`, but EXP-026 does not
freeze or run Llama. Do not use the previous 8B Llama as an automatic next
model; audit a roughly 1B Llama-family model first to reduce scale confounding.

## P4: Minimum Sufficient Alignment Operator

Per-model trigger `P4[m]` requires:

```text
LOW_D_SUPPORT[m] == SUPPORTED
```

Global route `P4` triggers if `P4[Q]` or `P4[O]` is true.

Interpretation: recovery is demonstrated broadly where raw degradation does not
provide the simple explanation.

Next priority when selected:

```text
MINIMUM_SUFFICIENT_ALIGNMENT_OPERATOR
```

## P5: Reconsider Panel/Reference Specificity

Global route `P5` triggers only if none of `P1`, `P2`, `P3`, or `P4` triggers.

Interpretation: the matrices are largely flat/stable and recovery is weak;
deprioritize operator escalation and reconsider whether the previous signals are
panel/reference-specific.

Next priority when selected:

```text
RECONSIDER_PANEL_AND_REFERENCE_SPECIFICITY
```

## Conflict Resolution

Strict global precedence:

```text
P3 > P1 > P2 > P4 > P5
```

Implementation rule:

1. If `P3` is true, selected route = `P3`.
2. Else if `P1` is true, selected route = `P1`.
3. Else if `P2` is true, selected route = `P2`.
4. Else if `P4` is true, selected route = `P4`.
5. Else selected route = `P5`.

If a route is `NOT_EVALUABLE` because source-coverage fails, it is treated as
not triggered. The full descriptive matrix may still be retained.

## Prohibited Routing Interpretations

- Do not call a selected route architecture-caused.
- Do not call a selected route family-caused.
- Do not use an unregistered matrix subregion to select a route.
- Do not alter precedence after observing the structural summaries.
- Do not lower the source usability floor or relax the LOW_D mask to trigger a
  preferred route.
