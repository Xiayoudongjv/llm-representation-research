# EXP-024 Focused Dataset Rereview R2

Status: `READY_FOR_DATASET_AND_PROTOCOL_FREEZE`

This is the focused independent rereview of the repaired Task-097D-A candidate
dataset. It reviews the repair performed in Task-097D-FIX against the five
blocking construct-defect classes identified by Task-097D-R. It does not
repeat a fresh full blind review of all 880 source families.

## Rereview Identity

- Reviewer task: `097D-R2`
- Review mode: read-only scientific dataset audit
- Reviewed candidate: `experiments/exp024/data/exp024_condition_panel_candidate.json`
- Repair log: `experiments/exp024/data/exp024_dataset_repair_log.json`
- Model/tokenizer/representation access: none
- Scientific-outcome access: none
- Candidate, manifest, repair log, protocol, condition panel, schema, validator, or preregistration modified: `false`

## Repaired Candidate Identity

- Original reviewed candidate SHA-256:
  `8583b57d9ed0ff98bd6d81eb3fc8f0f6c97a17d9acc63699b9d9b80e5c62eac5`
- Repaired candidate SHA-256:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Repair-log SHA-256:
  `33d70d2526792ec255a781db72c7bff515e8dd2e9693eaec1a06d5257827987d`
- Record count: `1760`
- Source-family count: `880`
- Condition count: `10`
- Semantic-class count: `4`
- FIT / DIAGNOSTIC / EVAL families: `240 / 320 / 320`
- Candidate state: `CANDIDATE_NOT_FROZEN`

The frozen mechanical validator was rerun:

- `EXP024_SCHEMA_VALIDATION = PASS`
- `EXP024_MECHANICAL_VALIDATION = PASS`
- Exact text duplicates: `0`
- Normalized text duplicates: `0`
- Unresolved internal near duplicates: `0`
- Historical exact reuse: `0`
- Historical direct paraphrase suspects: `0`

## Repair Diff Verification

Using the repair-log entry mapping, the current candidate contains exactly the
336 changed source families described by the repair log. Each family contains
two records, so the changed-record scope is 672.

Reconstruction results:

- Expected changed source families: `336`
- Expected changed records: `672`
- Changed families reviewed: `336`
- Unlogged changed families: `0`
- Logged-but-unchanged families: `0`
- Replacement families with old ID absent / new ID present: `168`
- Corrected or regenerated same-ID families: `168`

The repair-log action distribution is:

- `family_replaced`: `168`
- `definition_grammar_and_or_realization_corrected`: `113`
- `condition_realization_regenerated`: `55`

Provenance is internally consistent, and no extra unlogged changed family was
detected by the reconstructed diff.

## 336 Changed-Family Review

Every changed family was reviewed for semantic-class validity, reference-form
validity, realization fidelity, condition-rule satisfaction, information
retention, competing-relation control, class ambiguity, outcome-cue absence,
and pair/family coherence.

Deterministic semantic-validity screening returned:

- `PASS`: `336`
- `MINOR`: `0`
- `MODERATE_NONBLOCKING`: `0`
- `BLOCKING`: `0`

The old defect-specific grammar screens were negative across all changed
families:

- c03 `with is` / broken-phrase pattern: `0`
- c07 `Should X is` / `Owing to X is` pattern: `0`
- definition article-agreement pattern: `0`
- analogy same-word-pair pattern: `0`
- outcome-bearing phrase pattern: `0`

## Five Original Blocker Classes

All five blocker classes from Task-097D-R were independently rechecked against
the repaired content and are `RESOLVED`.

| Blocker | Original defect | Repair evidence | Verdict |
| --- | --- | --- | --- |
| `BLOCK-001` | Systematic logic subject-rule incompatibility | 162 logic families replaced with compatible subject/rule pairs | `RESOLVED` |
| `BLOCK-002` | c03 compression grammar/coherence defects | 66 c03 logic/causality/definition families corrected or regenerated | `RESOLVED` |
| `BLOCK-003` | c07 formal transformation grammar defects | 44 c07 logic/causality families corrected or regenerated | `RESOLVED` |
| `BLOCK-004` | Definition article/property grammar defects | 113 definition families grammar/realization corrected | `RESOLVED` |
| `BLOCK-005` | Analogy same-word pair defects | 6 affected analogy families replaced | `RESOLVED` |

No constructor-side claim was accepted as evidence by itself.

## Five Affected Condition-Class Cells

The five blocking condition/class cells from the original review were inspected
across the full FIT/DIAGNOSTIC/EVAL scope, not only the originally cited
examples.

| Condition | Class | Full-cell families | Verdict |
| --- | --- | --- | --- |
| `c03_controlled_compression` | `logic` | 22 | `PASS` |
| `c03_controlled_compression` | `causality` | 22 | `PASS` |
| `c03_controlled_compression` | `definition` | 22 | `PASS` |
| `c07_register_formal` | `logic` | 22 | `PASS` |
| `c07_register_formal` | `causality` | 22 | `PASS` |

Remaining blockers in affected cells: `0`.

## Two Formerly Blocking Conditions

The two conditions originally marked blocking were rechecked at the condition
level across all four semantic classes and all three partitions.

| Formerly blocking condition | Families reviewed | Verdict |
| --- | --- | --- |
| `c03_controlled_compression` | 88 | `PASS` |
| `c07_register_formal` | 88 | `PASS` |

Transformation fidelity, cross-class consistency, difficulty asymmetry,
surface-template concentration, semantic-equivalence stability, and unit
coherence are acceptable. Both conditions are nonblocking.

## Global Independence Checks

- DIAGNOSTIC/EVAL source-family overlap: `0`
- DIAGNOSTIC/EVAL base-content identity overlap: `0`
- DIAGNOSTIC/EVAL semantic-sibling blockers: `0`
- Cross-condition base-content identity reuse: `0`
- Cross-condition base-content blockers: `0`
- Cross-condition direct-paraphrase blockers: `0`
- Historical exact reuse: `0`
- Historical direct-paraphrase blockers: `0`

A coarse Jaccard `>= 0.80` screen across changed-vs-all records reports a large
number of high-similarity pairs. These are dominated by the known synthetic
`causality`, `definition`, and `logic` slot-template similarities rather than
distinct source-family reuse or direct paraphrase. They are therefore not
blocking for the already-accepted synthetic-template limitation.

## Global Duplicate / Leakage Checks

- Exact text duplicates: `0`
- Normalized text duplicates: `0`
- Unresolved blocking near duplicates: `0`
- Base-content identity duplication across conditions: `0`
- Partition style leakage: `MINOR`
- Class-template leakage: `MODERATE_NONBLOCKING`
- Analogy-template status: `MODERATE_CONSTRUCT_INHERENT_TEMPLATE_LIMITATION`

Partition surface statistics remain similar across FIT, DIAGNOSTIC, and EVAL;
the repair did not introduce a repair-specific partition style signature.

## Existing Nonblocking Limitations

The four original nonblocking construction limitations were reviewed:

1. Synthetic slot-template construction.
2. Compressed analogy colon-notation concentration.
3. Systematic length differences for compression/elaboration.
4. Historical screen is mechanical rather than full semantic review.

Repair outcome:

- Existing limitations upgraded to blocking: `0`
- New repair-induced blocking template limitation: `0`

## New-Defect Search

The repaired families were screened for new repeated templates, repair-fingerprint
wording, condition-level stylistic separation, partition-specific repair wording,
artificial vocabulary concentration, complexity shifts, reference/transformed
asymmetry, and loss of condition distinctness.

- New blocking defects introduced: `0`
- Collapsed condition pairs: `0`

## Condition-Level Inference Assessment

- Condition-level inference-unit validity: `LIMITED_BUT_DEFENSIBLE`
- Within-condition measurement precision: `ADEQUATE`
  - FIT: `6` per class per condition
  - DIAGNOSTIC: `8` per class per condition
  - EVAL: `8` per class per condition
- Outcome-bearing metadata: `ABSENT`

The repaired panel still supports the ten prospectively defined conditions as
the primary units for the exact pairing permutation test, subject to the
transparent limitations already documented.

## Blocking Findings

No blocking construct defect remains.

- Original blocker classes: `5`
- Original blockers resolved: `5`
- Remaining affected-cell blockers: `0`
- Formerly blocking conditions now nonblocking: `2`
- New blocking defects introduced: `0`
- Final blocking-construct-defect count: `0`

## Final Verdict

```text
EXP024_R2_FINAL_VERDICT =
READY_FOR_DATASET_AND_PROTOCOL_FREEZE
```

The repaired candidate is ready for `Task 097E`, which should freeze the
repaired dataset identity, final preregistration, condition-panel
specification, data schema, primary `S_diag` formula, primary `G_eval` formula,
Spearman statistic, exact one-sided condition permutation, support rule, and
known nonblocking limitations.

## Read-Only Guarantee

- Candidate dataset modified: `false`
- Candidate manifest modified: `false`
- Repair log modified: `false`
- Condition-panel specification modified: `false`
- Data schema modified: `false`
- Preregistration draft modified: `false`
- Validator modified: `false`
- Model load performed: `false`
- Tokenizer load performed: `false`
- Representation extraction performed: `false`
- `S_diag` computed: `false`
- `G_eval` computed: `false`
- Scientific outcome observed: `false`

## Required Flags

- `EXP024_R2_REVIEWED_CANDIDATE_SHA256 = 46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- `EXP024_R2_REPAIR_LOG_SHA256 = 33d70d2526792ec255a781db72c7bff515e8dd2e9693eaec1a06d5257827987d`
- `EXP024_R2_CHANGED_SOURCE_FAMILIES_EXPECTED = 336`
- `EXP024_R2_CHANGED_SOURCE_FAMILIES_REVIEWED = 336`
- `EXP024_R2_CHANGED_RECORDS_EXPECTED = 672`
- `EXP024_R2_UNLOGGED_CHANGED_FAMILIES = 0`
- `EXP024_R2_LOGGED_BUT_UNCHANGED_FAMILIES = 0`
- `EXP024_R2_ORIGINAL_BLOCKER_CLASSES = 5`
- `EXP024_R2_ORIGINAL_BLOCKERS_RESOLVED = 5`
- `EXP024_R2_AFFECTED_CONDITION_CLASS_CELLS = 5`
- `EXP024_R2_AFFECTED_CONDITION_CLASS_BLOCKERS_REMAINING = 0`
- `EXP024_R2_FORMERLY_BLOCKING_CONDITIONS = 2`
- `EXP024_R2_FORMERLY_BLOCKING_CONDITIONS_NOW_NONBLOCKING = 2`
- `EXP024_R2_NEW_BLOCKING_DEFECTS_INTRODUCED = 0`
- `EXP024_R2_PAIRING_STRUCTURE = PASS`
- `EXP024_R2_DIAGNOSTIC_EVAL_FAMILY_OVERLAP = 0`
- `EXP024_R2_DIAGNOSTIC_EVAL_SEMANTIC_SIBLING_BLOCKERS = 0`
- `EXP024_R2_CROSS_CONDITION_BASE_CONTENT_BLOCKERS = 0`
- `EXP024_R2_HISTORICAL_EXACT_REUSE = 0`
- `EXP024_R2_HISTORICAL_DIRECT_PARAPHRASE_BLOCKERS = 0`
- `EXP024_R2_EXACT_TEXT_DUPLICATES = 0`
- `EXP024_R2_UNRESOLVED_BLOCKING_NEAR_DUPLICATES = 0`
- `EXP024_R2_PARTITION_STYLE_LEAKAGE = MINOR`
- `EXP024_R2_CLASS_TEMPLATE_LEAKAGE = MODERATE_NONBLOCKING`
- `EXP024_R2_ANALOGY_TEMPLATE_STATUS = MODERATE_CONSTRUCT_INHERENT_TEMPLATE_LIMITATION`
- `EXP024_R2_EXISTING_NONBLOCKING_LIMITATIONS_REVIEWED = 4`
- `EXP024_R2_EXISTING_LIMITATIONS_UPGRADED_TO_BLOCKING = 0`
- `EXP024_R2_COLLAPSED_CONDITION_PAIRS = 0`
- `EXP024_R2_CONDITION_LEVEL_INFERENCE_UNIT_VALIDITY = LIMITED_BUT_DEFENSIBLE`
- `EXP024_R2_WITHIN_CONDITION_MEASUREMENT_PRECISION = ADEQUATE`
- `EXP024_R2_OUTCOME_BEARING_METADATA = ABSENT`
- `EXP024_R2_BLOCKING_CONSTRUCT_DEFECTS = 0`
- `EXP024_R2_FINAL_VERDICT = READY_FOR_DATASET_AND_PROTOCOL_FREEZE`
- `MODEL_LOAD_PERFORMED = false`
- `TOKENIZER_LOAD_PERFORMED = false`
- `REPRESENTATION_EXTRACTION_PERFORMED = false`
- `S_DIAG_COMPUTED = false`
- `G_EVAL_COMPUTED = false`
- `SCIENTIFIC_OUTCOME_OBSERVED = false`
