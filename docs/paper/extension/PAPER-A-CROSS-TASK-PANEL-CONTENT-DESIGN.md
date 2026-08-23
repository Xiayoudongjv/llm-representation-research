# Paper-A Cross-Task Panel Content Design

Status: `PA_EXT_A_002_CONTENT_DESIGN_FROZEN_PRE_DATA`

This document freezes HOW the new scientific panel will be constructed.
It does not create the real source bank, real candidate items, FIT/DIAG/EVAL
data, model inference, hidden states, results, or authorization.

## 1. Chronology and Binding

- `V1_PROTOCOL_FROZEN = FINAL_FROZEN_PRE_DATA_PROTOCOL`
- `V2_CONTENT_DESIGN_FROZEN = true`
- `PANEL_CONTENT_STATUS = PANEL_CONTENT_NOT_YET_CREATED`

The V1 protocol authority is unchanged. This document is a narrow prospective
content-design binding, not a rewrite of measurement, statistics, routing, or
model authority.

## 2. Old-Panel Semantic Exclusion Registry

Authoritative old semantic universe, from EXP-024:

- Old task families: one four-way semantic relation classification universe.
- Old semantic classes:
  - `logic`
  - `causality`
  - `analogy`
  - `definition`
- Old condition IDs:
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
- Old dataset authority:
  - `experiments/exp024/data/exp024_condition_panel_frozen.json`
- Old source-family ID prefix: `exp024_`
- Old base-content ID prefix: `exp024_base_`

Fields that are item-level lexical/template identities are available in the
frozen dataset and must be checked mechanically at real-panel validation.
They are not reconstructed here from memory.

## 3. Formal Definitions

- `TASK_FAMILY`: a bounded family of classification problems sharing one
  argument schema, one answer semantics, and one class-label role.
- `SEMANTIC_RELATION`: the relation whose truth/value determines class
  membership within a task family.
- `TASK_INSTANCE`: one concrete instantiation of a task family with exactly
  one declared semantic relation label.
- `SOURCE_ITEM`: one human-authored canonical text that becomes the
  `reference_form` for one source family.
- `TRANSFORMED_ITEM`: one deterministic surface realization derived from a
  source item by a frozen transformation rule.

## 4. New Task Universe

The new task universe is four distinct non-propositional relation families
over two explicit arguments. It is designed to be disjoint from the old
`logic/causality/analogy/definition` classes.

`NEW_TASK_FAMILY_COUNT = 4`
`NEW_SEMANTIC_RELATION_COUNT = 4`

### TF_SPATIAL

- `TASK_FAMILY_ID = exta_tf_spatial`
- Scientific definition: classify a static spatial configuration relation
  between two concrete referents or regions.
- Discriminated content: which spatial relation is asserted.
- Allowed semantic relation: `exta_rel_spatial_configuration`.
- Forbidden relations: causal, logical entailment, analogy, definition,
  temporal order, quantitative comparison, part-whole.
- Class mapping: `TF_SPATIAL`.
- Distinctness: old `logic` concerns truth/entailment; old `causality`
  concerns production/explanation; spatial configuration is neither.
- Ambiguity boundary: if an item implies temporal/causal reading, it is
  invalid under the predefined rules.

### TF_TEMPORAL

- `TASK_FAMILY_ID = exta_tf_temporal`
- Scientific definition: classify temporal order/overlap between two events
  or states without asserting causation.
- Discriminated content: which temporal relation is asserted.
- Allowed semantic relation: `exta_rel_temporal_order`.
- Forbidden relations: causation, counterfactual dependence, logical
  entailment, analogy, definition.
- Class mapping: `TF_TEMPORAL`.
- Distinctness: temporal order is not old `causality`.
- Ambiguity boundary: any item with causal marker or counterfactual reading
  is invalid.

### TF_QUANTITATIVE

- `TASK_FAMILY_ID = exta_tf_quantitative`
- Scientific definition: classify a relative magnitude or quantity relation
  between two measurable arguments.
- Discriminated content: greater, less, equal, or explicitly marked
  incomparable magnitude.
- Allowed semantic relation: `exta_rel_quantitative_comparison`.
- Forbidden relations: logical validity, causal relation, analogy,
  definition, spatial containment, temporal order, part-whole.
- Class mapping: `TF_QUANTITATIVE`.
- Distinctness: magnitude comparison is not old `logic` or `causality`.
- Ambiguity boundary: vague non-measurable predicates are invalid.

### TF_MEREOLOGICAL

- `TASK_FAMILY_ID = exta_tf_mereological`
- Scientific definition: classify a part-whole or constituent-membership
  relation between two entities.
- Discriminated content: whether one argument is a part/constituent/member
  of the other.
- Allowed semantic relation: `exta_rel_part_whole`.
- Forbidden relations: definitional equivalence, synonymy, analogy, logic,
  causality, temporal order, spatial location.
- Class mapping: `TF_MEREOLOGICAL`.
- Distinctness: old `definition` concerns meaning specification; part-whole
  is a world relation, not a definitional equivalence.
- Ambiguity boundary: if an item reduces to a dictionary-style definition,
  it is invalid.

## 5. Semantic-Relation Set

### exta_rel_spatial_configuration

- `RELATION_ID = exta_rel_spatial_configuration`
- Operational meaning: the static location/containment/adjacency relation
  between two concrete referents.
- Class role: one of four multiclass labels.
- Argument structure: `ARG_A`, `ARG_B`; both concrete referents or regions.
- Validity conditions: a spatial relation is unambiguously determinable from
  the source text.
- Invalid/ambiguous cases: causal/temporal readings, missing argument,
  figurative spatial language, contradictory location claims.
- Task-family membership: `exta_tf_spatial`.
- Old-panel overlap check: no old `logic/causality/analogy/definition` class
  match.

### exta_rel_temporal_order

- `RELATION_ID = exta_rel_temporal_order`
- Operational meaning: the order/overlap between two events or states.
- Class role: one of four multiclass labels.
- Argument structure: `ARG_A`, `ARG_B`; both events or states.
- Validity conditions: an order/overlap relation is unambiguously
  determinable, with no causal implication.
- Invalid/ambiguous cases: causal markers, counterfactual dependence,
  atemporal states, missing event arguments.
- Task-family membership: `exta_tf_temporal`.
- Old-panel overlap check: explicitly non-causal, so distinct from
  `causality`.

### exta_rel_quantitative_comparison

- `RELATION_ID = exta_rel_quantitative_comparison`
- Operational meaning: relative magnitude/quantity between two measurable
  arguments.
- Class role: one of four multiclass labels.
- Argument structure: `ARG_A`, `ARG_B`; both measurable quantities/entities.
- Validity conditions: a determinate comparison relation exists and is not
  inferred from model performance.
- Invalid/ambiguous cases: vague predicates, missing quantities, categorical
  relations, causal or logical claims.
- Task-family membership: `exta_tf_quantitative`.
- Old-panel overlap check: no old `logic/causality/analogy/definition` match.

### exta_rel_part_whole

- `RELATION_ID = exta_rel_part_whole`
- Operational meaning: whether one argument is a part, constituent, material,
  or member of the other.
- Class role: one of four multiclass labels.
- Argument structure: `ARG_A`, `ARG_B`; one whole and one part/constituent/
  member.
- Validity conditions: a part-whole relation is unambiguously determinable.
- Invalid/ambiguous cases: definitional equivalence, class inclusion stated
  as dictionary meaning, metaphor, causal production.
- Task-family membership: `exta_tf_mereological`.
- Old-panel overlap check: distinct from old `definition`.

## 6. New Condition Set

Ten deterministic surface-realization conditions, all new IDs. They preserve
task family, semantic relation, class label, and source-family identity.

- `xa01_synonym_variant`
- `xa02_constituent_reorder`
- `xa03_redundancy_reduction`
- `xa04_explicative_elaboration`
- `xa05_overt_relation_marker`
- `xa06_implicit_relation_marker`
- `xa07_precise_register`
- `xa08_colloquial_register`
- `xa09_neutral_context_prefix`
- `xa10_coreference_shift`

No old EXP-024 condition template text may be copied.

## 7. Human Source-Bank Authoring Contract

- `AUTHORING_SCHEME = FIXED_COUNT_DIRECT_AUTHORING`
- `SURPLUS_POLICY = FIXED_COUNT_DIRECT_AUTHORING`
- `AUTHOR_ROLE = SOURCE_BANK_AUTHOR`, a role, not a named person.
- Author may see: frozen content design, source-item schema, slot list,
  objective grammar/validity rules.
- Author must not see: model outputs, hidden states, compatibility matrices,
  probe scores, LOW-D outcomes, profile routes, item-specific model
  correctness, old registered profiles, or any expected replication outcome.
- Author must not author more than the required slot count.
- Author must not select "nice" items after surplus.
- Every source item must be assigned to its predetermined slot before
  authoring.

## 8. Objective Rejection Contract

Allowed rejection codes:

- `SEMANTIC_CONTRADICTION`
- `RELATION_NOT_INSTANTIATED`
- `DUPLICATE_NORMALIZED_CONTENT`
- `UNFILLED_ARGUMENT`
- `UNGRAMMATICAL_UNDER_FROZEN_RULE`
- `HISTORICAL_OVERLAP`
- `FORBIDDEN_LEXICAL_LEAKAGE`
- `FAMILY_ID_COLLISION`

Forbidden rejection reasons include expected difficulty, model confidence,
hidden-state geometry, expected profile replication, or "representative"
judgment. Every rejection must be logged with a code and no model outcome.

## 9. Review Contract

- Reviewer role: `SOURCE_BANK_REVIEWER`.
- Review is limited to objective semantic/structural validity.
- Reviewer may not use model outputs, hidden states, embeddings, difficulty
  estimates, compatibility outputs, or profile results.
- Reviewer outcome must be one of:
  - `VALID`
  - `OBJECTIVE_DEFECT_<CODE>`
  - `AMBIGUOUS_UNDER_PREDEFINED_RULE`

No numeric subjective quality score.

## 10. Disagreement Handling

- Author/reviewer disagreement is resolved by the predefined rule.
- `AMBIGUOUS_UNDER_PREDEFINED_RULE` items are excluded and logged.
- Excluded slots are re-authored once under the same contract; no
  outcome-based shopping or "discuss until it sounds right".

## 11. Deterministic Transformation Contract

- `TRANSFORMATION_OWNER = PA-EXT-A-003_GENERATOR`
- `SOURCE_OWNER = HUMAN_AUTHORED_SOURCE_BANK`
- The generator must not author semantic content, choose relations, call a
  model, or score quality.
- Each transformed item is mechanically traceable from:
  - `SOURCE_ITEM_ID`
  - `TRANSFORMATION_ID`
  - `TRANSFORMATION_PARAMETERS`
- Invariant properties:
  - task-family identity
  - semantic relation
  - class label
  - source-family identity
  - logical/truth conditions where applicable
- Allowed changes:
  - surface wording
  - syntactic form
  - entity realization under the frozen lexicon
  - non-semantic lexical content

## 12. Source-Family and Transformation-Family Contract

- One source family contains exactly one `reference_form` and one
  `condition_realization`.
- Transformed variants share the source family.
- A source family never crosses `FIT`, `DIAG`, or `EVAL`.
- `TRANSFORMATION_FAMILY_ID` is source-family scoped and cannot cross
  partitions.

## 13. Panel Structure and Exact Counts

The frozen protocol's default structure is inherited and made exact:

- `NEW_CLASS_COUNT = 4` (one per task family)
- `NEW_CONDITION_COUNT = 10`
- `FIT_FAMILIES_PER_CLASS_PER_CONDITION = 6`
- `DIAG_FAMILIES_PER_CLASS_PER_CONDITION = 8`
- `EVAL_FAMILIES_PER_CLASS_PER_CONDITION = 8`
- `SOURCE_BANK_SIZE = 880` source families
- `FINAL_PANEL_SIZE = 1760` records
- `FIT_SOURCE_FAMILIES = 240`; `FIT_RECORDS = 480`
- `DIAG_SOURCE_FAMILIES = 320`; `DIAG_RECORDS = 640`
- `EVAL_SOURCE_FAMILIES = 320`; `EVAL_RECORDS = 640`

No increase in sample size to chase significance.

## 14. Balance Contract

Balanced outcome-independently by task family, semantic relation, class,
condition, source family, transformation family, and partition. Balancing
may not use model success or hidden states.

## 15. Surface-Length Control

- Primary model-independent measure: `WHITESPACE_TOKEN_COUNT`.
- Secondary descriptive measure: `CHARACTER_COUNT`.
- Canonical source items must be in the predeclared range `8..28`
  whitespace tokens inclusive.
- No tested-model tokenizer length may control inclusion.
- Length audit must be class-conditioned and must not use model outcomes.

## 16. Lexical and Semantic-Relation Leakage Control

Allowed static controls:

- static vocabulary audit
- class-conditional surface-form counts
- predefined lexical-overlap checks
- shared entity/vocabulary pool where semantically possible
- multiple lexical realizations per relation marker

Forbidden:

- model-guided dataset cleaning
- using Qwen/OLMo/Llama predictions to rebalance or remove items
- embedding-based selection/deduplication/scoring

Residual relation-specific vocabulary is documented as a limitation; it is
controlled but cannot be eliminated without making the task unnatural.

## 17. Historical Freshness Contract

Future real-panel validation must reject:

- exact raw-text recurrence
- normalized-text recurrence
- source-family recurrence
- semantic-source recurrence
- template recurrence where historically available

New IDs must use the `exta_` prefix, never `exp024_`.

## 18. Public Corpus / LLM / Embedding Firewalls

- No MMLU/BBH/GLUE/etc import.
- No LLM-generated source-bank items.
- No LLM generation followed by human filtering.
- No embedding or neural-similarity selection/rejection/clustering/scoring.

Static deterministic normalization and deduplication are allowed.

## 19. Item Schema

Future item fields:

- `item_id`
- `task_family_id`
- `semantic_relation_id`
- `class_id`
- `condition_id`
- `source_item_id`
- `source_family_id`
- `transformation_id`
- `transformation_family_id`
- `raw_text`
- `normalized_text`
- `partition`
- `authoring_provenance`
- `review_status`
- `rejection_history`
- `content_design_sha256`

Real `raw_text` is not populated in this task.

## 20. Deterministic Identifiers

- `TASK_FAMILY_ID = exta_tf_<slug>`
- `SEMANTIC_RELATION_ID = exta_rel_<slug>`
- `SOURCE_FAMILY_ID = exta_sf_<condition_id>_<partition>_<task_family_id>_<zero_padded_index>`
- `SOURCE_ITEM_ID = <source_family_id>_source`
- `TRANSFORMATION_ID = exta_xform_<condition_id>`
- `TRANSFORMATION_FAMILY_ID = <source_family_id>_xform`
- `FINAL_ITEM_ID = <source_family_id>_<record_role>`
- `record_role` is `reference` or `realization`.

## 21. Synthetic Fixture Contract

For PA-EXT-A-003 only:

- Use placeholders such as `SYNTH_TASK_A`, `SYNTH_RELATION_B`,
  `SYNTH_ENTITY_1`, `SYNTH_ENTITY_2`.
- Required flags:
  - `SYNTHETIC = true`
  - `SCIENTIFIC_USE_ALLOWED = false`
  - `FORMAL_PANEL_ALLOWED = false`

Synthetic fixtures must not instantiate the real task families.

## 22. Future Generator Requirements

The PA-EXT-A-003 generator must:

- load and verify the exact frozen content design
- verify design SHA
- accept only contract-valid source-bank records
- apply deterministic transformations
- construct deterministic identities
- apply static historical exclusion
- assign splits deterministically
- serialize reproducibly

It must not author semantic content, choose task families or relations,
score quality, or call a model.

## 23. Future Independent Validator Requirements

The independent validator must check:

- design hash
- task-family membership
- semantic-relation membership
- schema completeness
- semantic-construction trace
- source-family isolation
- transformation-family isolation
- partition integrity
- class/task/relation balance
- historical freshness
- no synthetic content in production
- no free-form unbound items

Validation must not be tautological with generation.

## 24. One-Panel Stopping Rule

Exactly one real independent panel may be created. No alternative task-family
set, replacement source bank, second panel, or item replacement based on model
outcomes is allowed. Objective pre-inference defects may be repaired only
under the predeclared correction policy.

## 25. Hard Flags

- `REAL_EXT_A_SOURCE_BANK_CREATED = false`
- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_CANDIDATE_ITEMS_CREATED = false`
- `REAL_EXT_A_FIT_DATA_CREATED = false`
- `REAL_EXT_A_DIAG_DATA_CREATED = false`
- `REAL_EXT_A_EVAL_DATA_CREATED = false`
- `REAL_EXT_A_HIDDEN_STATES_ACCESSED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `REAL_EXT_A_AUTHORIZATION_CREATED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`