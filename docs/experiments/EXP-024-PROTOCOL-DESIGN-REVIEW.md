# EXP-024 Protocol Design Review

Status: `READY_FOR_DATASET_CONSTRUCTION`

This document reviews the Task-097C EXP-024 protocol for construct validity,
independence, sampling-unit defensibility, statistical identifiability,
condition-panel limitations, dataset burden, primary/secondary separation,
prior-art distinction, and Paper-A relevance.

## Verdict

```text
EXP024_PROTOCOL_REVIEW = READY_FOR_DATASET_CONSTRUCTION
```

No blocking construct defect is identified at the protocol level. Dataset
generation may proceed under the drafted schema and condition-panel
specification, followed by independent dataset review before freeze.

## Construct Validity

The primary construct is condition-level fixed-readout susceptibility.

- `S_diag(c)` operationalizes susceptibility as the same fixed readout becoming
  less accurate from block16-pre to block27-pre on independent DIAGNOSTIC
  families.
- `G_eval(c)` operationalizes calibration benefit as the improvement from A0 to
  A_mu_sigma on independent EVAL families.
- The reference/canonical expression is not a panel unit, so the panel tests
  realization-condition heterogeneity rather than baseline difficulty.

Assessment: `PASS`.

## Independence

- FIT, DIAGNOSTIC, and EVAL are source-family disjoint.
- No source family crosses partitions.
- No source family is reused across conditions.
- The diagnostic and outcome partitions do not share records.
- The primary predictor uses DIAGNOSTIC families only.
- The primary outcome uses EVAL families only.

Assessment: `PASS`.

The protocol explicitly removes the EXP-023 shared-A0 limitation at the
observation level:

```text
EXP024_SHARED_EVAL_A0_ALGEBRAIC_DEPENDENCY = false
```

## Sampling Unit

The primary unit is `condition/panel`.

- Each condition contributes one `S_diag` and one `G_eval`.
- Layers are not independent samples.
- Items are not independent samples across shared families or models.
- The exact permutation test permutes condition pairings, not items or layers.

Assessment: `PASS`.

## Statistical Identifiability

- `N_CONDITIONS = 10`.
- Primary statistic is Spearman rank correlation.
- Primary test is one-sided exact permutation across conditions.
- Exact enumeration size is `10! = 3,628,800`, computationally feasible.
- Support rule is `rho > 0 AND exact_one_sided_p <= 0.05`.
- No flexible regression or post-hoc diagnostic selection is primary.

Assessment: `PASS_WITH_SMALL_N_LIMITATION`.

The design is statistically identifiable but has limited power for moderate
effects because the condition panel is small. This is acknowledged and
documented; the design deliberately increases independent units rather than
pseudo-replicating rows.

## Condition-Panel Limitations

The panel is bounded to ten surface/realization transformations in a controlled
semantic task universe.

- It does not cover all possible linguistic conditions.
- It is not selected from EXP-022A/EXP-023 favorable outcomes.
- It does not establish general population-level linguistic universality.
- Some transformations may interact with token position; last-valid-token
  selection is specified.

Assessment: `MODERATE_NONBLOCKING_LIMITATION`.

## Dataset Burden

Proposed allocation:

```text
10 conditions * 4 classes * (6 FIT + 8 DIAGNOSTIC + 8 EVAL) = 880 families
2 record roles per family = 1760 records
```

Burden assessment:

- Content generation: high but bounded and auditable.
- Equivalence review: high; condition-specific semantic review is required.
- Model inference: moderate; one frozen local model, two primary checkpoints,
  plus optional descriptive depth extraction.

Assessment: `ACCEPTABLE_FOR_CONTROLLED_DESIGN`.

## Primary/Secondary Separation

Primary:

- `S_diag(c)`
- `G_eval(c)`
- Spearman rho
- exact one-sided condition permutation
- support rule `rho > 0 AND p <= 0.05`

Secondary/descriptive:

- A_mu and A_sigma decomposition
- FIT/DIAGNOSTIC mean-shift and scale-shift diagnostics
- margin degradation
- full-depth trajectory
- bootstrap intervals

No secondary analysis may replace the primary after outcomes are observed.

Assessment: `PASS`.

## Prior-Art Distinction

The protocol does not claim novelty for:

- layer-specific affine readouts;
- affine alignment;
- trained transformations restoring task performance.

The distinctive prospective question is whether a fixed-readout degradation
diagnostic on DIAGNOSTIC families predicts FIT-only featurewise recalibration
benefit on independent EVAL families.

Assessment: `PASS_WITH_PRIOR_ART_SEARCH_STILL_PARTIAL`.

## Paper-A Relevance

This is the single targeted follow-up for
`HYP_CALIBRATION_CONDITIONAL_002`.

- Positive result would add a prospective condition-level susceptibility
  predictor.
- Negative result would narrow the Paper-A mechanism claim without invalidating
  the bounded core claim.
- The protocol preserves `PAPER_A_DRAFT_READINESS = START_FIRST_DRAFT_NOW`.

Assessment: `PASS`.

## Final Protocol Review

```text
EXP024_PROTOCOL_REVIEW = READY_FOR_DATASET_CONSTRUCTION
```

Next step is Task-097D: construct and independently review the EXP-024
controlled dataset. Do not freeze the preregistration or run the model here.
