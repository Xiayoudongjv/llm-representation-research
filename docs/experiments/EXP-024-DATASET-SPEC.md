# EXP-024 Dataset Structural Specification

Status: `DRAFT_NOT_FROZEN`

This document defines the structural validation rules for the prospective
EXP-024 controlled dataset. It does not contain or generate the formal dataset.

## Purpose

The validator must mechanically prove the following before dataset freeze:

- no source family crosses FIT/DIAGNOSTIC/EVAL partitions
- no forbidden source family crosses conditions
- class balance is exact within every condition/partition cell
- condition balance is exact
- partition balance is exact
- record-role balance is exact
- no future scientific outcome fields are present

## Allocation

| Quantity | Value |
| --- | ---: |
| Conditions | `10` |
| Semantic classes | `4` |
| FIT families per class per condition | `6` |
| DIAGNOSTIC families per class per condition | `8` |
| EVAL families per class per condition | `8` |
| Total source families | `880` |
| Record roles per family | `2` |
| Total records | `1760` |

## Record Structure

Each record must contain at minimum:

- `record_id`
- `source_family_id`
- `semantic_class`
- `condition_id`
- `partition`
- `record_role`
- `base_content_identity`
- `transformation_rule_id`
- `text`
- `independence_group`
- `review_status`
- `provenance`

### Record Roles

- `reference_form`: canonical/original expression. Used only as the common
  reference basis for fitting the global reference readout and scaler.
- `condition_realization`: condition-specific transformed expression. Used for
  all model inference at block16-pre and block27-pre in FIT/DIAGNOSTIC/EVAL.

Every source family must contain exactly one `reference_form` and exactly one
`condition_realization` record.

## Source-Family Identity Contract

Recommended deterministic family ID:

```text
exp024_<condition_id>_<partition>_<semantic_class>_<zero_padded_index>
```

Example:

```text
exp024_c03_controlled_compression_EVAL_logic_0001
```

Requirements:

- Globally unique and deterministic.
- Invariant across the two record roles in the family.
- Encodes condition and partition for mechanical leakage checks.
- Does not rely on filename conventions alone.
- Must remain stable after dataset freeze.

## Partition Independence

Validator checks:

- `FIT intersect DIAGNOSTIC = empty`
- `FIT intersect EVAL = empty`
- `DIAGNOSTIC intersect EVAL = empty`
- `EXP024_CROSS_PARTITION_FAMILY_OVERLAP = 0`

No direct or simple paraphrase lineage may cross partitions. No
source-family-derived sibling record may cross partitions.

## Condition Independence

Validator checks:

- Each source family appears in exactly one `condition * partition` cell.
- `EXP024_CROSS_CONDITION_FORBIDDEN_FAMILY_OVERLAP = 0`

The same underlying semantic content must not be reused across condition units.
This avoids pseudo-replication across primary condition scores.

## Class Balance

Within every `condition * partition` cell:

- `logic`: exact allocated count
- `causality`: exact allocated count
- `analogy`: exact allocated count
- `definition`: exact allocated count

Expected counts:

| Partition | Families per class |
| --- | ---: |
| FIT | `6` |
| DIAGNOSTIC | `8` |
| EVAL | `8` |

## Condition Balance

Each condition must contain:

- all four semantic classes
- all three partitions
- `6 + 8 + 8 = 22` families per semantic class

## Partition Balance

Across the dataset:

- FIT total families: `10 * 4 * 6 = 240`
- DIAGNOSTIC total families: `10 * 4 * 8 = 320`
- EVAL total families: `10 * 4 * 8 = 320`
- Total source families: `880`

## Record-Role Balance

Every source family must have exactly:

- one `reference_form`
- one `condition_realization`

Total records must equal `2 * 880 = 1760`.

## Text and Semantic-Equivalence Rules

- `text` must be nonempty.
- `text` must not introduce new truth-relevant information.
- `text` must preserve the frozen semantic class.
- `text` must be the realization specified by `transformation_rule_id`.
- `text` must not leak class labels through trivial wording.
- `text` must not be selected based on EXP-022A/EXP-023 outcomes.
- Any condition with `BLOCKING_CONSTRUCT_DEFECT` must be replaced before freeze.

## Condition ID and Transformation Rule

Every record's `condition_id` must match an ID in
`experiments/exp024/condition_panel_spec.json`.

Every record's `transformation_rule_id` must be the rule associated with that
condition.

## Review Status

Every record and condition must have a review status:

- `PASS`
- `MODERATE_NONBLOCKING_LIMITATION`
- `BLOCKING_CONSTRUCT_DEFECT`

Freeze is permitted only when no `BLOCKING_CONSTRUCT_DEFECT` remains.
Moderate limitations must remain visible in provenance.

## Provenance

Each record must include provenance with at least:

- creator task
- reviewer task
- `created_at_utc`
- `reviewed_at_utc`
- `frozen_sha256` once dataset freeze occurs

A dataset-level SHA-256 must be computed at freeze time.

## Prohibited Outcome Fields

The formal dataset must not include:

- `hidden_state`
- `representation`
- `prediction`
- `balanced_accuracy`
- `S_diag`
- `G_eval`
- `G_mu`
- `G_sigma`
- `calibration_result`
- `scientific_outcome`

Scientific outcomes are computed later by the runner and must not be embedded in
the dataset.

## Validation Contract

Before dataset freeze, a validator must produce:

- `DATASET_FAMILY_OVERLAP_CHECK = PASS`
- `DATASET_CLASS_BALANCE_CHECK = PASS`
- `DATASET_CONDITION_BALANCE_CHECK = PASS`
- `DATASET_PARTITION_BALANCE_CHECK = PASS`
- `DATASET_RECORD_ROLE_CHECK = PASS`
- `DATASET_SCHEMA_FIELDS_CHECK = PASS`
- `DATASET_NO_OUTCOME_FIELDS_CHECK = PASS`
- `DATASET_SHA256_RECORDED = true`

Failure of any check is blocking for dataset freeze.
