# EXP-024 Freeze Review

Status: `FROZEN_READY_FOR_RUNNER_ENGINEERING`

This document records the freeze of the independently reviewed EXP-024
dataset, protocol, condition panel, and primary-analysis authorities. The
freeze changes identity/status metadata only; it does not redesign science.

## Freeze Entry State

- Repository: `D:\Research\llm-representation-research`
- Branch: `main`
- Source preparation commit:
  `9008bb50792841018f99071002d3fa05d5deca05`
- R2 final verdict: `READY_FOR_DATASET_AND_PROTOCOL_FREEZE`
- Candidate mechanical validation: `PASS`
- Candidate repaired SHA:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Repair-log SHA:
  `33d70d2526792ec255a781db72c7bff515e8dd2e9693eaec1a06d5257827987d`

## Frozen Authority Identities

| Authority | Path | SHA-256 |
| --- | --- | --- |
| Frozen dataset | `experiments/exp024/data/exp024_condition_panel_frozen.json` | `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404` |
| Final preregistration | `docs/experiments/EXP-024-PREREGISTRATION.md` | `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810` |
| Condition panel | `experiments/exp024/condition_panel_spec.json` | `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954` |
| Data schema | `experiments/exp024/data_schema.json` | `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec` |
| Candidate validator | `experiments/exp024/validate_exp024_candidate_dataset.py` | `d2d95333430754fd48889d0840182b0047413c9abcf7d5610392950d74ab5c52` |
| Repair log | `experiments/exp024/data/exp024_dataset_repair_log.json` | `33d70d2526792ec255a781db72c7bff515e8dd2e9693eaec1a06d5257827987d` |
| R2 Markdown review | `docs/experiments/EXP-024-DATASET-REREVIEW-R2.md` | `fce960a3e2f668e9da449f14b2b821af8f8a49a83f4a3ba9a02d4a46ef95f463` |
| R2 structured review | `experiments/exp024/data/exp024_independent_rereview_r2.json` | `a7dc98bf58411793106a1a112273be799ea97ee22d2a4e070a0fe109b968344e` |
| Frozen manifest | `experiments/exp024/exp024_frozen_manifest.json` | `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59` |
| Freeze validator | `experiments/exp024/validate_exp024_freeze.py` | `4118c6dfe3393d7f136c2657dfa7cb48cc10b11d71c43495b9518c90b53db2b7` |

## Dataset Byte Identity

The frozen dataset was created as a byte-for-byte copy of the reviewed repaired
candidate dataset.

- Source candidate SHA:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Frozen dataset SHA:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- `EXP024_FROZEN_DATASET_MATCHES_R2_REVIEWED_CANDIDATE = true`
- `EXP024_DATASET_BYTE_DRIFT = false`

No normalization, pretty-printing, metadata insertion, key reordering, or
newline conversion was applied.

## Preregistration Semantic-Diff Audit

The final preregistration was derived from
`docs/experiments/EXP-024-PREREGISTRATION-DRAFT.md`.

Classified differences:

- Title/status from draft to frozen: `FREEZE_METADATA_ONLY`
- Hypothesis status and protocol stage: `FREEZE_METADATA_ONLY`
- Panel status: `FREEZE_METADATA_ONLY`
- Frozen dataset/schema/condition-panel paths: `FREEZE_METADATA_ONLY`
- Frozen authority identity block: `FREEZE_METADATA_ONLY`
- Model/outcome access flag updates: `FREEZE_METADATA_ONLY`
- Next-step wording from dataset construction to runner engineering:
  `EDITORIAL_NO_SEMANTIC_CHANGE`

- `EXP024_PROTOCOL_SCIENTIFIC_CHANGE_COUNT = 0`

Hypothesis, condition definitions, allocation, model revision, checkpoints,
classifier/scaler contract, `S_diag`, `G_eval`, Spearman statistic, exact
one-sided condition permutation, support rule, negative-result taxonomy, and
claim boundaries are unchanged.

## Condition Panel Identity

- Path: `experiments/exp024/condition_panel_spec.json`
- SHA-256:
  `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`
- Conditions frozen: `10`
- Semantic classes frozen: `logic`, `causality`, `analogy`, `definition`
- Condition IDs, names, rules, allowed edits, forbidden edits, and
  semantic-equivalence criteria: unchanged.

## Data Schema Identity

- Path: `experiments/exp024/data_schema.json`
- SHA-256:
  `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec`
- Frozen allocation:
  - FIT: `6` families per class per condition
  - DIAGNOSTIC: `8` families per class per condition
  - EVAL: `8` families per class per condition
  - Total: `880` source families / `1760` records

## Primary Analysis Freeze

- `EXP024_PRIMARY_SCIENTIFIC_UNIT = condition`
- `EXP024_N_CONDITIONS = 10`
- `EXP024_PRIMARY_DIAGNOSTIC = S_diag(c)`
  - `S_diag(c) = BA_A0(block16_pre_final_rmsnorm, DIAG_c) - BA_A0(block27_pre_final_rmsnorm, DIAG_c)`
- `EXP024_PRIMARY_OUTCOME = G_eval(c)`
  - `G_eval(c) = BA_A_mu_sigma(block27_pre_final_rmsnorm, EVAL_c) - BA_A0(block27_pre_final_rmsnorm, EVAL_c)`
- `EXP024_PRIMARY_STATISTIC = Spearman_rho`
- `EXP024_PRIMARY_TEST = exact_one_sided_condition_permutation`
- `EXP024_EXACT_PERMUTATION_COUNT = 3628800`
- `EXP024_PRIMARY_SUPPORT_RULE = rho>0_and_p<=0.05`
- Model: `Qwen/Qwen3-1.7B`
- Model revision:
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Reference checkpoint: `block16_pre_final_rmsnorm`
- Primary final checkpoint: `block27_pre_final_rmsnorm`

## Known Nonblocking Limitations

Carried forward as accepted and documented:

- Synthetic slot-template construction.
- Compressed analogy colon-notation concentration.
- Systematic length differences for compression and elaboration conditions.
- Mechanical rather than full semantic historical-independence screen.
- Condition-level inference-unit validity is `LIMITED_BUT_DEFENSIBLE`.

Freeze means accepted and documented, not perfect.

## Model/Outcome Access Audit

- `EXP024_MODEL_LOAD_PERFORMED = false`
- `TOKENIZER_LOAD_PERFORMED = false`
- `REPRESENTATION_EXTRACTION_PERFORMED = false`
- `CLASSIFIER_FIT_PERFORMED = false`
- `S_DIAG_COMPUTED = false`
- `G_EVAL_COMPUTED = false`
- `SPEARMAN_COMPUTED = false`
- `PERMUTATION_TEST_PERFORMED = false`
- `EXP024_SCIENTIFIC_OUTCOME_OBSERVED = false`
- `EXP024_AUTHORIZATION_CREATED = false`
- `EXP024_RUNNER_CREATED = false`

## Validator Result

Reran:

- `python experiments/exp024/validate_exp024_candidate_dataset.py`
- `python experiments/exp024/validate_exp024_freeze.py`

Both returned `PASS`. The freeze validator confirmed frozen dataset byte
identity, preregistration status, condition-panel/schema identities, frozen
model revision, primary-analysis formulas, exact permutation count, support
rule, dataset counts, and absence of formal result paths.

## Final Freeze Verdict

```text
EXP024_FREEZE_GATE = FROZEN_READY_FOR_RUNNER_ENGINEERING
```

The frozen authorities are ready for `Task 098A — Implement EXP-024
Frozen-Protocol Runner and Static Tests`. Task 098A may perform runner
engineering and static preflight, but must not execute a formal model/data
scientific run.

## Required Flags

- `EXP024_FROZEN_DATASET_CREATED = true`
- `EXP024_FROZEN_DATASET_SHA256 = 46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- `EXP024_FROZEN_DATASET_MATCHES_R2_REVIEWED_CANDIDATE = true`
- `EXP024_FINAL_PREREGISTRATION_CREATED = true`
- `EXP024_FINAL_PREREGISTRATION_SHA256 = 55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`
- `EXP024_CONDITION_PANEL_SHA256 = a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`
- `EXP024_DATA_SCHEMA_SHA256 = e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec`
- `EXP024_R2_REVIEW_SHA256 = fce960a3e2f668e9da449f14b2b821af8f8a49a83f4a3ba9a02d4a46ef95f463`
- `EXP024_R2_STRUCTURED_REVIEW_SHA256 = a7dc98bf58411793106a1a112273be799ea97ee22d2a4e070a0fe109b968344e`
- `EXP024_FROZEN_MANIFEST_CREATED = true`
- `EXP024_FROZEN_MANIFEST_SHA256 = 1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`
- `EXP024_FREEZE_VALIDATOR_CREATED = true`
- `EXP024_FREEZE_VALIDATOR_RESULT = PASS`
- `EXP024_PREREGISTRATION_STATUS = FROZEN_NOT_RUN`
- `EXP024_DATASET_STATUS = FROZEN_NOT_RUN`
- `EXP024_PRIMARY_SCIENTIFIC_UNIT = condition`
- `EXP024_N_CONDITIONS = 10`
- `EXP024_PRIMARY_DIAGNOSTIC = S_diag(c)`
- `EXP024_PRIMARY_OUTCOME = G_eval(c)`
- `EXP024_PRIMARY_STATISTIC = Spearman_rho`
- `EXP024_PRIMARY_TEST = exact_one_sided_condition_permutation`
- `EXP024_EXACT_PERMUTATION_COUNT = 3628800`
- `EXP024_PRIMARY_SUPPORT_RULE = rho>0_and_p<=0.05`
- `EXP024_MODEL_REVISION = 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- `EXP024_PROTOCOL_SCIENTIFIC_CHANGE_COUNT = 0`
- `EXP024_DATASET_BYTE_DRIFT = false`
- `EXP024_MODEL_LOAD_PERFORMED = false`
- `EXP024_REPRESENTATION_EXTRACTION_PERFORMED = false`
- `EXP024_SCIENTIFIC_OUTCOME_OBSERVED = false`
- `EXP024_AUTHORIZATION_CREATED = false`
- `EXP024_RUNNER_CREATED = false`
- `EXP024_FREEZE_GATE = FROZEN_READY_FOR_RUNNER_ENGINEERING`
