# PAPER-A EXT-A Content Production V3 Amendment

Status: `FINAL_FROZEN_PRE_DATA_V3_CONTENT_PRODUCTION_SIMPLIFICATION`

This is a prospective pre-data amendment. It changes HOW source semantic
instances are produced; it does not change the scientific question, task
families, semantic relations, dataset shape, measurement contract,
statistics, routing, model set, carrier rules, or one-extension stopping rule.

## 1. Chronology

- `V1`: protocol frozen before content design.
- `V2`: human-authored source-bank content design frozen.
- `V3`: pre-data content-production simplification.

`NO_REAL_SOURCE_DATA_EXISTED_AT_TIME_OF_V3_AMENDMENT = true`

## 2. Selected Route

- `SELECTED_ROUTE = ADOPT_ROUTE_S`
- Previous route: `HUMAN_AUTHORED_SOURCE_BANK_DETERMINISTIC_TRANSFORMATION`
- New route:
  `STRUCTURED_SEMANTIC_ASSET_BANK_PLUS_DETERMINISTIC_COMPOSITION_RENDERING`

## 3. Authority Preservation

- Previous V2 content-design path:
  `experiments/paper_a_ext_a/paper_a_ext_a_panel_content_design.json`
- Previous V2 content-design SHA-256:
  `82dd8d944691c49d5586defdf999d0afdb70f95bd5b4f568ffa5c72642829ce6`
- V3 does not delete, rewrite, or reinterpret V2.
- V3 is an explicitly versioned successor authority.

## 4. What Changes

- `PANEL_AUTHORITY_ROUTE`
- `SOURCE_CONTENT_PRODUCTION_METHOD`
- `SEMANTIC_ASSET_SCHEMA`
- `COMPOSITION_RULE`
- `ENUMERATION_RULE`
- `RENDERING_RULE`
- `HUMAN_REVIEW_SCOPE`

## 5. What Does Not Change

- `SCIENTIFIC_QUESTION_MODIFIED = false`
- `TASK_FAMILY_SET_MODIFIED = false`
- `SEMANTIC_RELATION_SET_MODIFIED = false`
- `DATASET_SHAPE_MODIFIED = false`
- `MEASUREMENT_CONTRACT_MODIFIED = false`
- `STATISTICAL_CONTRACT_MODIFIED = false`
- `OUTCOME_ROUTING_MODIFIED = false`

## 6. Production Method

1. Humans define reusable semantic assets and admissibility rules.
2. A deterministic composer constructs 880 source-family semantic instances
   from predeclared slots and assets.
3. A deterministic renderer produces `reference` and `condition_realization`
   text using frozen templates.
4. The generator assigns partitions, IDs, families, and serializes the panel.
5. An independent validator recomputes authority hashes, counts, isolation,
   balance, freshness, and synthetic status.

## 7. Review Scope

`ITEM_LEVEL_HUMAN_REVIEW_REQUIRED = ASSET_AND_RULE_LEVEL_ONLY`

Final sentence-level manual approval is not required. Assets and rendering
rules are validated before generation; generated items inherit correctness by
construction where mechanically checkable.

## 8. Governance Path

- `PA-EXT-A-003`: generator/validator implementation and synthetic qualification
- `PA-EXT-A-004`: minimal pre-data release gate
- `PA-EXT-A-005`: real semantic-asset/source content creation and panel freeze
- `PA-EXT-A-006`: formal execution qualification/authorization as needed
- `PA-EXT-A-007`: formal run and result adjudication

`SIMPLIFIED_GOVERNANCE_PATH = PASS`

`AUTHORITY_BY_HASH = PASS`

## 9. Hard Flags

- `REAL_EXT_A_SEMANTIC_ASSET_BANK_CREATED = false`
- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_CANDIDATE_ITEMS_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_HIDDEN_STATES_ACCESSED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `REAL_EXT_A_AUTHORIZATION_CREATED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`

## 10. Next Task

`PA-EXT-A-003_GENERATOR_VALIDATOR_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION`