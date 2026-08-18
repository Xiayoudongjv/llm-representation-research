# EXP-024 Dataset Construction Report

Status: `CANDIDATE_NOT_FROZEN`

This report describes mechanical construction of the EXP-024 controlled
condition-panel candidate dataset. It does not claim independent scientific or
semantic review has passed.

## Construction Procedure

1. Read the frozen protocol draft, dataset schema, condition panel spec, and
   protocol review.
2. Generated 880 unique base semantic items from the four controlled semantic
   classes using deterministic, outcome-independent slot templates.
3. Assigned source families to `condition * partition * semantic_class` cells
   with the registered RNG seed `EXP024_ALLOC_RNG_SEED = 20260818`.
4. For each family, generated one `reference_form` and one
   `condition_realization` record using the assigned condition rule.
5. Performed a post-generation exact-duplicate sweep and corrected 22
   cross-role exact duplicates.
6. Ran the mechanical validator with no model, tokenizer, hidden-state, or
   scientific outcome access.

## Condition Panel Summary

The candidate uses exactly the ten conditions from
`experiments/exp024/condition_panel_spec.json`:

- `c01_lexical_relex`
- `c02_syntactic_restructure`
- `c03_controlled_compression`
- `c04_controlled_elaboration`
- `c05_relation_explicit`
- `c06_relation_implicit`
- `c07_register_formal`
- `c08_register_informal`
- `c09_neutral_distractor_prefix`
- `c10_anaphoric_reference`

No condition was added, removed, renamed, merged, split, or reinterpreted.

## Exact Counts

| Quantity | Value |
| --- | ---: |
| Conditions | `10` |
| Semantic classes | `4` |
| Unique source families | `880` |
| Records | `1760` |
| FIT source families | `240` |
| DIAGNOSTIC source families | `320` |
| EVAL source families | `320` |
| FIT families per class per condition | `6` |
| DIAGNOSTIC families per class per condition | `8` |
| EVAL families per class per condition | `8` |

Every family contains exactly one `reference_form` and one
`condition_realization` record.

## Schema Validation

- `EXP024_SCHEMA_VALIDATION = PASS`
- All required fields are present.
- No prohibited outcome-bearing fields are present.
- `record_id` uniqueness: `PASS`
- `source_family_id` uniqueness: `PASS`
- Condition/class/partition/record-role enums: `PASS`

## Partition and Family Independence

- `EXP024_CROSS_PARTITION_FAMILY_OVERLAP = 0`
- `EXP024_CROSS_CONDITION_FORBIDDEN_FAMILY_OVERLAP = 0`
- No source family appears across multiple conditions, partitions, or classes.
- No direct or simple paraphrase lineage crosses partitions.

## Internal Duplicate Checks

- Exact text duplicates: `0`
- Normalized text duplicates: `0`
- Internal near-duplicate pairs at Jaccard threshold `0.95`: `0`

## Historical Independence Checks

Compared candidate text against available prior controlled dataset files from
EXP-017, EXP-018, EXP-019, EXP-020, and EXP-023.

- `EXP024_HISTORICAL_EXACT_REUSE = 0`
- `EXP024_HISTORICAL_DIRECT_PARAPHRASE_SUSPECTS = 0`

This is a mechanical screen, not a complete semantic independence review.

## Surface Diagnostics

Outcome-free descriptive statistics for condition-realization records:

| Group | Records | Avg chars | Avg words | Avg sentence marks |
| --- | ---: | ---: | ---: | ---: |
| Overall | `880` | `89.9` | `15.6` | `1.0` |
| FIT | `240` | `96.3` | `16.5` | `1.0` |
| DIAGNOSTIC | `320` | `95.8` | `16.4` | `1.0` |
| EVAL | `320` | `95.7` | `16.5` | `1.0` |
| `c01_lexical_relex` | `88` | `91.6` | `15.4` | `1.0` |
| `c02_syntactic_restructure` | `88` | `96.2` | `15.6` | `1.0` |
| `c03_controlled_compression` | `88` | `66.6` | `11.6` | `1.0` |
| `c04_controlled_elaboration` | `88` | `142.5` | `24.9` | `1.0` |
| `c05_relation_explicit` | `88` | `105.2` | `17.9` | `1.0` |
| `c06_relation_implicit` | `88` | `76.5` | `12.6` | `1.0` |
| `c07_register_formal` | `88` | `98.1` | `17.0` | `1.0` |
| `c08_register_informal` | `88` | `90.9` | `15.8` | `1.0` |
| `c09_neutral_distractor_prefix` | `88` | `112.9` | `19.8` | `1.0` |
| `c10_anaphoric_reference` | `88` | `78.5` | `14.1` | `1.0` |

Partition surface distributions are intentionally similar. Condition-level
length differences are consistent with the transformation rules and were not
selected to optimize difficulty.

## Known Limitations

- `MODERATE_NONBLOCKING_LIMITATION`: synthetic slot-template construction,
  especially for definition records.
- `MODERATE_NONBLOCKING_LIMITATION`: analogy records under compressed
  realization can use compact colon notation.
- `MODERATE_NONBLOCKING_LIMITATION`: controlled compression and elaboration
  conditions produce systematic length differences.
- `MODERATE_NONBLOCKING_LIMITATION`: the historical screen is mechanical, not
  full semantic historical-independence review.

No blocking construct defect was identified during construction.

## Items Replaced During Construction

- `22` `c08_register_informal` logic condition-realization records were
  surface-adjusted after the initial generation because their realization text
  exactly matched the corresponding reference-form text.
- The adjustment appended `, as a rule` and preserved the condition rule,
  semantic class, and target relation.
- No replacement used model-derived outcomes.

## Final Candidate SHA

- Candidate path:
  `experiments/exp024/data/exp024_condition_panel_candidate.json`
- `EXP024_CANDIDATE_DATASET_SHA256 =
  8583b57d9ed0ff98bd6d81eb3fc8f0f6c97a17d9acc63699b9d9b80e5c62eac5`

## Mechanical Acceptance Gate

```text
EXP024_MECHANICAL_VALIDATION = PASS
EXP024_DATASET_REVIEW_GATE = READY_FOR_INDEPENDENT_DATASET_REVIEW
```

No model, tokenizer, representation extraction, A0, S_diag, G_eval, Spearman
rho, or permutation test was performed.

## Next Step

Stop candidate editing until Task-097D-R returns findings. Do not freeze the
dataset or preregistration in this task.


## Independent-Review Repair Cycle

- Repair task: `097D-FIX`
- Original reviewed candidate SHA: `8583b57d9ed0ff98bd6d81eb3fc8f0f6c97a17d9acc63699b9d9b80e5c62eac5`
- Repaired candidate SHA: `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Repair log path: `experiments/exp024/data/exp024_dataset_repair_log.json`
- Repair log SHA: `33d70d2526792ec255a781db72c7bff515e8dd2e9693eaec1a06d5257827987d`
- Blocking defect classes targeted: `5`
  - `BLOCK-001`: systematic logic subject-rule incompatibility
  - `BLOCK-002`: c03 compression grammar/coherence defects
  - `BLOCK-003`: c07 formal transformation grammar defects
  - `BLOCK-004`: definition article/property grammar defects
  - `BLOCK-005`: analogy same-word pair defects
- Affected conditions/classes:
  - c03 with logic, causality, definition
  - c07 with logic, causality
  - logic, definition, and analogy reference families as identified by Task-097D-R
- Repair scope:
  - Replaced semantically invalid logic families with valid subject-rule pairs.
  - Regenerated c03 and c07 condition realizations for affected class cells.
  - Corrected definition article/property grammar defects.
  - Replaced analogy same-word families with valid analogical pairs.
- Families changed: `336`
- Records changed: `672`
- Mechanical validation: rerun after repair.
- Remaining acknowledged nonblocking limitations: synthetic slot-template construction, compressed analogy colon-notation concentration, systematic length differences, mechanical historical screen.
- Model access: `false`
- Scientific outcome access: `false`
- Repair gate: `READY_FOR_FOCUSED_INDEPENDENT_REREVIEW`
