# EXP-023 Dataset Candidate Review

Status: `CANDIDATE_DATASET_AWAITING_INDEPENDENT_REVIEW_AND_FREEZE`

This document reviews the candidate dataset only. It does not freeze the dataset.

## Candidate identity

- Dataset path: `experiments/exp023/data/exp023_independent_controlled.json`
- Dataset SHA-256: `9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a`
- Record count: `64`
- Source family count: `32`
- Classes: `logic`, `causality`, `analogy`, `definition`
- Raw variant universe: `original_style`, `paraphrase`
- Historical exclusion dataset SHA-256: `72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`

## Construction boundaries

- Construction occurred before any EXP-023 model execution or scientific outcome.
- No model, tokenizer, hidden-state, classifier, scaler, attention, bootstrap, or endpoint computation was performed.
- No outcome-based item selection or generation-based item selection was used.
- The historical controlled dataset was inspected only as a schema/exclusion authority; no historical prompt text was reproduced here.

## Structural validation

- `STRUCTURAL_VALIDATION = PASS`
- `DATASET_CONTENT_FAMILIES_PASS = 32/32`
- `OLD_RECORD_EXACT_REUSE_COUNT = 0`
- `OLD_SOURCE_ITEM_DIRECT_REUSE_COUNT = 0`
- `OLD_ITEM_SIMPLE_PARAPHRASE_COUNT = 0`
- `MODEL_EXECUTION_PERFORMED = false`
- `EXP023_OUTCOME_OBSERVED = false`

## Surface-length diagnostics

- Overall words: min `8`, max `22`, mean `13.56`
- Overall characters: min `41`, max `139`, mean `74.05`

- `logic`: n=`16`, words min/max/mean=`8`/`22`/`14.88`
- `causality`: n=`16`, words min/max/mean=`9`/`16`/`12.94`
- `analogy`: n=`16`, words min/max/mean=`9`/`18`/`13.56`
- `definition`: n=`16`, words min/max/mean=`9`/`20`/`12.88`
- `original_style`: n=`32`, words min/max/mean=`9`/`22`/`13.5`
- `paraphrase`: n=`32`, words min/max/mean=`8`/`22`/`13.62`

These diagnostics are quality checks, not outcome-based covariates.

## Family-by-family audit

| source_family_id | class | pair_complete | semantic_equivalence | nontrivial_paraphrase | historical_independence | content_clarity | status |
|---|---|---|---|---|---|---|---|
| `exp023_logic_001` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_002` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_003` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_004` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_005` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_006` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_007` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_logic_008` | `logic` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_001` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_002` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_003` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_004` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_005` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_006` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_007` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_causality_008` | `causality` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_001` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_002` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_003` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_004` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_005` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_006` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_007` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_analogy_008` | `analogy` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_001` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_002` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_003` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_004` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_005` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_006` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_007` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |
| `exp023_definition_008` | `definition` | PASS | PASS | PASS | PASS | PASS | PASS |

## Review readiness

- `EXP023_DATASET_CANDIDATE_STATUS = READY_FOR_SINGLE_CONTENT_AND_INDEPENDENCE_REVIEW`
- `EXP023_DATASET_FROZEN = false`
- `EXP023_PREREGISTRATION_CHANGED = false`
