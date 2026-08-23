# EXP-028 Panel Content Design Review

Status: `EXP028_103F1_PANEL_CONTENT_DESIGN_REVIEW`
Design state: `FINAL_FROZEN_PRE_DATA_V2_CONTENT_DESIGN`
No real panel was generated. No model inference occurred. No authorization was created.

## 1. Why 103F/103F0 Blocked

Task 103F found EXP-028 inherited a 10-condition semantic structure but lacked a committed item-generation authority. Task 103F0 confirmed the historical slot templates, lexicons, and generation source were not in the repository. The inherited generator therefore could not be reproduced prospectively.

## 2. Which Historical Semantic Authorities Were Recovered

- `experiments/exp024/condition_panel_spec.json`: all 10 condition definitions.
- `experiments/exp024/data_schema.json`: four semantic classes, FIT/DIAG/EVAL allocation, family/record schema.
- `docs/experiments/EXP-019-DATASET-PROTOCOL.md`: operational class definitions.
- `experiments/exp023/data/exp023_independent_controlled.json`: historical class/paraphrase examples.

## 3. Which Historical Content-Generation Authorities Were Missing

- The actual deterministic slot templates.
- The frozen lexical pools.
- The original item-generation source code/data used to create the EXP-024 880-family panel.

## 4. Candidate Generation Routes Considered

| Route | Verdict | Reason |
| --- | --- | --- |
| A: deterministic slot template + frozen lexicon | SELECTED | Strong reproducibility/auditability; no model generation; no post-hoc human selection |
| B: human-authored source bank + deterministic transformation | REJECTED_FOR_NOW | More human discretion and not fully freezable without committing the bank now |
| C: other non-model deterministic method | REJECTED_FOR_NOW | No better method identified for preserving the inherited schema |

## 5. Selected Route and Rationale

`ROUTE_A_DETERMINISTIC_SLOT_TEMPLATE_PLUS_FROZEN_LEXICON`

This route preserves the inherited class/condition semantics while making every item traceable to template IDs and lexicon IDs. Candidate selection and split assignment are deterministic and outcome-independent.

## 6. Condition Semantics

All 10 inherited EXP-024 conditions are retained unchanged:

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

## 7. Class Semantics

Frozen order: `logic`, `causality`, `analogy`, `definition`.

- `logic`: validity, entailment, deduction, condition satisfaction, contradiction, or logical conclusion.
- `causality`: cause-effect or mechanism relation.
- `analogy`: relational correspondence or mapped relation.
- `definition`: concept meaning/identity/reference.

Where historical definitions were underdetermined, the minimum operational criterion above is marked prospective and is not a recovered historical fact.

## 8. Source-Family Definition

One source family is one underlying semantic construction unit with exactly two records: `reference_form` and `condition_realization`. A family cannot cross condition, class, or FIT/DIAG/EVAL. Allocation is inherited as `6/8/8` families per class per condition.

## 9. Paraphrase-Family Definition

Paraphrase identity is construction provenance, not embedding similarity. The paraphrase family is the canonical reference/realization pair for a source family, with maximum two surface variants and no split/condition/class crossing.

## 10. Template Design

Four template families per class and one condition transformation template per condition. Template IDs, slot types, slot order, punctuation, articles, tense, negation, connectives, and clause structure are frozen. Class-specific templates are documented; neutral templates may be shared.

## 11. Lexicon Design

Twelve semantic-role pools are frozen with 64 entries each in the future non-model lexicon manifest. No word may be selected for expected model behavior. Duplicate entries are prohibited within and across pools.

## 12. Confound-Control Strategy

Lexical, template, length, punctuation, and syntax controls are frozen. Class-exclusive surface markers are avoided where not intrinsic. Counterbalancing uses shared neutral pools across classes/conditions when semantically legitimate.

## 13. Deterministic Candidate-Selection Rule

Candidates are enumerated deterministically and sorted by a canonical tuple. The first N valid candidates per cell are selected after freshness exclusion. No human/model scoring, difficulty filtering, or result-aware pruning is allowed.

## 14. Split/Freshness Integration

Split assignment uses stable SHA-256 ordering of source-family IDs. Freshness uses NFKC normalization, whitespace collapse, and SHA-256 collision checks against prior panels.

## 15. Human-Review Restrictions

Human review may reject only objective defects: malformed grammar, empty fields, broken template realization, duplicate construction, or generator-induced semantic contradiction. It may not reject by difficulty or model expectation.

## 16. Remaining Scientific Risks

- The deterministic grammar can still generate unnatural or borderline semantic examples; objective validation is required.
- Class/condition counterbalancing reduces but cannot fully eliminate all lexical/template correlations.
- Historical freshness screening is mechanical and does not guarantee deep semantic independence.

## 17. Explicit No-Inference Statement

No real EXP-028 panel, model representation, model inference, DELTA_RM/DELTA_RO, bootstrap, model state, three-model route, authorization, formal run, or canonical result was created.

## Final Design Flags

- `CONTENT_DESIGN_ROUTE = ROUTE_A_DETERMINISTIC_SLOT_TEMPLATE_PLUS_FROZEN_LEXICON`
- `HISTORICAL_CONDITION_SCHEMA = PASS`
- `CLASS_SEMANTIC_DEFINITIONS = FROZEN`
- `SOURCE_FAMILY_CONTRACT = FROZEN`
- `PARAPHRASE_FAMILY_CONTRACT = FROZEN`
- `TEMPLATE_CONTRACT = FROZEN`
- `LEXICON_CONTRACT = FROZEN`
- `CONTENT_PROVENANCE_CONTRACT = FROZEN`
- `CANDIDATE_SELECTION_CONTRACT = FROZEN`
- `SPLIT_ASSIGNMENT_CONTRACT = FROZEN`
- `HUMAN_REVIEW_CONTRACT = FROZEN`
- `ADVERSARIAL_DESIGN_REVIEW = PASS`
- `PREREGISTRATION_STATE = FINAL_FROZEN_PRE_DATA_V2_CONTENT_DESIGN`
