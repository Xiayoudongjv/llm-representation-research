# Paper-A Cross-Task Replication Protocol

Status: `PA_EXT_A_001_PROTOCOL_DESIGN`

This document is prospective and pre-data. It freezes the scientific protocol
for the single authorized Paper-A extension. It does not create panel items,
model inference, hidden-state access, results, authorization, or manuscript
changes.

## 1. Purpose

Paper-A gap `G1 PANEL/TASK_DEPENDENCE = MAJOR`.

The experiment asks whether the registered cross-depth fixed-readout
compatibility profiles are stable under a prospectively frozen, genuinely
independent semantic/task panel.

A changed profile is a scientifically valid result. This is not a
replication-for-success experiment.

## 2. Authority Order

1. `PAPER-A-EXT-A-CROSS-TASK-PREREGISTRATION.md`
2. `paper_a_ext_a_frozen_config.json`
3. Frozen EXP-027 design and canonical result
4. Frozen EXP-026 design and canonical result
5. EXP-024 frozen panel, schema, and manifest
6. Existing Paper-A claim and novelty assets
7. Research asset and lineage documents

Task text and chat memory are not scientific authority.

## 3. Frozen Original-Panel Authority

The original semantic/task panel is the EXP-024 condition panel.

- `experiments/exp024/data/exp024_condition_panel_frozen.json`
- `experiments/exp024/condition_panel_spec.json`
- `experiments/exp024/data_schema.json`
- `experiments/exp024/exp024_frozen_manifest.json`

Original panel structure:

- 10 conditions: `c01_lexical_relex` through `c10_anaphoric_reference`
- 4 semantic classes: `logic`, `causality`, `analogy`, `definition`
- Partitions: `FIT=6`, `DIAGNOSTIC=8`, `EVAL=8` per class per condition
- 880 source families, 1760 records
- Each source family has one `reference_form` and one `condition_realization`
- Record role used by formal analysis: `condition_realization`
- No model-specific panel differences in the canonical authority

The new panel must be demonstrably independent from this panel.

## 4. What Must Remain Fixed

The extension changes task/panel content only. Unless a concrete technical
impossibility is demonstrated and recorded prospectively, the following are
inherited unchanged from EXP-026/027:

- Model set and exact model identities
- Tokenizer identities and raw-text invocation semantics
- Carrier hook semantics for each model
- Normalized depth grid and source/target layer-pair semantics
- Fixed-readout training rule and FIT/DIAG/EVAL firewall
- Distance metric `D = Cself - C0`
- Source/target organization metric `SDI`
- LOW-D recalibration definition and `A_mu_sigma` recalibration
- Source-family-cluster bootstrap semantics
- Confidence-interval and support-threshold rules
- Model-level profile routing

## 5. Permitted Changes

Only task/panel dimensions may prospectively change:

- semantic relation classes
- task families
- stimulus vocabulary
- templates
- item families
- surface form
- panel size and class count, only with prospective justification
- task-specific labels, if any

No measurement, statistic, threshold, model, carrier, or routing change may be
packaged as a panel change.

## 6. Formal Definition of Cross-Task Independence

`CROSS_TASK_INDEPENDENCE_LEVEL =
NEW_TASK_FAMILIES_AND_NEW_SEMANTIC_RELATIONS`

Minimum required independence:

- The new semantic relation families must not be the EXP-024 families
  `logic`, `causality`, `analogy`, or `definition` under a renamed surface.
- The new task families must not be a paraphrase-only transformation of the
  old families.
- New source families must not reuse EXP-024 `base_content_identity` values.
- New source families must not reuse EXP-024 source-family IDs.

Weak forms are explicitly rejected:

- `NEW_ITEMS_ONLY`
- `NEW_LEXICAL_REALIZATIONS`
- `NEW_TEMPLATES` alone
- Paraphrase replication

`NEW_SEMANTIC_RELATIONS` is the minimum. `NEW_TASK_FAMILIES` is the preferred
operational target.

## 7. Freshness Firewall

The new panel must not be selected based on:

- existing model performance
- existing compatibility results
- anticipated replication probability
- pilot hidden states
- probe results
- difficulty shopping
- model-family preference

No candidate task family may be accepted or rejected because it is expected to
reproduce `Qwen = TARGET / NOT_SUPPORTED`, `OLMo = SOURCE / SUPPORTED`, or
`Llama = TARGET / SUPPORTED`.

Task selection must be outcome-independent.

## 8. Panel-Authority Route

Selected prospective route:

`PANEL_AUTHORITY_ROUTE =
HUMAN_AUTHORED_SOURCE_BANK_DETERMINISTIC_TRANSFORMATION`

Rationale:

- Maximizes genuine independence from the synthetic EXP-024 construction.
- Allows a new semantic relation/task family with auditable content control.
- Deterministic transformation rules preserve reproducibility.
- Public-benchmark contamination is avoided because the source bank is
  project-authored and frozen before formal access.

Rejected alternatives:

- `DETERMINISTIC_SLOT_TEMPLATE_FROZEN_LEXICON`: lower confidence of genuine
  semantic-family independence from the old synthetic panel.
- `EXISTING_PUBLIC_TASK_SOURCE_FROZEN_SAMPLING`: pretraining-exposure and
  benchmark-contamination interpretation risks are higher.

The actual source bank is not created in this task.

## 9. Panel Size and Balance Policy

Default prospective structure, inherited for comparability unless PA-EXT-A-002
provides a pre-data scientific justification:

- 4 mutually exclusive semantic relation classes
- 10 conditions
- `FIT=6`, `DIAGNOSTIC=8`, `EVAL=8` families per class per condition
- 880 source families
- 1760 records

Any change in class count, condition count, or allocation must be justified
before panel content creation and recorded in the frozen panel design. Changes
must not be chosen to make the old profile more or less likely.

## 10. Public-Benchmark Contamination Control

Public benchmark items are disfavored for the primary new panel. If a public
source is later proposed, the panel design must state what the result can and
cannot mean under likely pretraining exposure, and the item identity must be
recorded. Benchmark freshness is not item freshness.

## 11. Task-Difficulty Confound Controls

The panel design must enforce, outcome-independently:

- exact class balance
- exact item/family counts
- bounded surface-length distribution
- no answer-position leakage
- no lexical marker leakage
- no template repetition leakage
- no source-family reuse across conditions or partitions
- no paraphrase-family leakage
- no task-label leakage in stimulus text

Difficulty matching may not use model outcomes or hidden-state previews.

## 12. Primary Scientific Question

`PRIMARY_SCIENTIFIC_QUESTION = "When Qwen3-1.7B, OLMo-2-1B-Instruct, and
Meta-Llama-3.2-1B-Instruct are held fixed in model identity, carrier
semantics, depth coordinates, fixed-readout procedures, statistics, and
routing, are the registered three-component cross-depth compatibility profiles
stable when the original EXP-024 semantic task panel is replaced by a
prospectively designed, genuinely independent semantic/task panel?"`

This wording does not assume stability.

## 13. Primary Unit of Inference

`PRIMARY_INFERENCE_UNIT = MODEL_LEVEL_REGISTERED_PROFILE`

Each model has:

- `DISTANCE_STATE`
- `SOURCE_TARGET_STATE`
- `LOW_D_STATE`

Layer-pair observations are not treated as independent model-level
replications. The bootstrap preserves source-family clustering and condition
stratification.

## 14. Frozen Historical Profiles

Repository-authoritative old profiles:

- Qwen: `(POSITIVE_SUPPORTED, TARGET_DOMINANT, NOT_SUPPORTED)`
- OLMo: `(POSITIVE_SUPPORTED, SOURCE_DOMINANT, SUPPORTED)`
- Llama: `(POSITIVE_SUPPORTED, TARGET_DOMINANT, SUPPORTED)`

These are read-only historical authority. They must not be recomputed under
new rules.

## 15. New-Panel Profile Construction

`NEW_PROFILE(model) = (distance_state, source_target_state, low_d_state)`

Computed from the new panel using exactly the frozen EXP-026/027 measurement
and statistical rules. No post-hoc harmonization between old and new panels is
allowed.

## 16. Profile Stability Definitions

- `EXACT_PROFILE_STABILITY`: all three registered categorical components of a
  model tuple match.
- `DIMENSION_LEVEL_STABILITY`: a named component matches while another differs.
- `PARTIAL_PROFILE_STABILITY`: some but not all components match.

Stability is categorical and model-by-model, dimension-by-dimension. No
continuous "profile similarity" score is used.

## 17. Outcome Routing

See:

`docs/paper/extension/PAPER-A-CROSS-TASK-OUTCOME-ROUTING.md`

Primary routes are `A1` through `A6`, with no replication-success privilege.

## 18. Shared Distance Structure

Prospective interpretation:

- all three new distance states positive: shared positive distance-associated
  structure persists across the two tested panels.
- some remain positive: shared distance structure is partial, not universal.
- none remain positive: distance structure is task-conditional in the tested
  model/panel set.

## 19. Empirical Nonredundancy Boundary

The original evidence supports empirical nonredundancy at `LEVEL_2`, not
statistical or causal independence. The new task evaluates whether
nonredundancy persists, disappears, or changes; it does not upgrade the claim
to independence or latent-factor independence.

## 20. Statistical Contract

Inherited from EXP-026/027 unless impossible:

- distance statistic: `Spearman_rho`, average ranks
- `SDI=(source_var-target_var)/(source_var+target_var)`, `numpy.var(ddof=0)`
- LOW-D mask: frozen DIAGNOSTIC `Dbar <= 0` off-diagonal pairs
- LOW-D estimand: mean `Rbar` on the frozen mask
- bootstrap: condition-stratified source-family cluster bootstrap
- resampling unit: `source_family`
- statistical unit: `source_family_cluster`
- RNG: `numpy.random.PCG64`, seed `20260819`
- replicates: `5000`
- percentile method: `numpy.percentile_method_linear`
- support bound: one-sided 95% lower/upper percentile as registered per metric
- invalid replicates: skip replicates that do not preserve all four classes

No statistic, threshold, or CI rule may be changed to alter replication
probability.

## 21. Cross-Task Comparison

For each model and each component, compare old and new categorical states.
Report model-by-model and dimension-by-dimension. The primary routing is
categorical and exact; no post-hoc continuous profile similarity is allowed.

## 22. Formal Hypothesis Structure

The experiment is an adjudication among stability and task-conditional
outcome routes, not `H1 = replicate` versus `H0 = failure`.

If individual metric support is reported, it inherits the existing registered
statistical meaning. No new confirmatory null is introduced here.

## 23. Negative-Result Value

- All three exact profiles replicate: supports cross-task stability over the
  two tested panels; no universal task-invariant model property.
- Only distance replicates: shared distance structure, but higher-order
  profile dimensions are task-conditional.
- Source/target organization changes: organization is task-conditional.
- LOW-D changes: simple recalibratability is task-conditional.
- All components change: the model-only profile framing must be narrowed
  substantially.

No outcome triggers a replacement panel design.

## 24. Claim Ceilings

`PROFILE_STABILITY_CLAIM_CEILING = "profile stability across two independently
designed task panels in the three tested models"`

`TASK_CONDITIONAL_CLAIM_CEILING = "compatibility profiles are task-conditional
in the tested model/task set"`

Forbidden: universal model property, task-invariant property, transport,
invariant preservation, functional binding, mechanism, causal independence.

## 25. One-Extension Stopping Rule

This is the ONE Paper-A extension. After valid execution:

- no second fresh panel
- no alternative task panel
- no fourth model
- no statistic replacement
- no threshold replacement
- no replication repair

Regardless of result, return to manuscript revision.

## 26. Firewalls

- `EXP024_ANTI_RESCUE_FIREWALL`: no predictive endpoint; Route A does not
  rescue EXP-024; EXP-024 remains a negative result.
- `EXP028_FIREWALL`: no paired transformation operator complexity, no `T2 vs
  T1`, no `DELTA_RM`, no `DELTA_RO`, no minimum-alignment complexity, no
  structural validity endpoint; EXP-028 remains paused and untouched.
- `MANUSCRIPT_FIREWALL`: no Paper-A manuscript, figure, table, or claim prose
  change.

## 27. Future Execution Graph

- `PA-EXT-A-002`: panel content design and freeze
- `PA-EXT-A-003`: generator/validator implementation and synthetic qualification
- `PA-EXT-A-004`: independent pre-data rereview
- `PA-EXT-A-005`: real fresh panel generation/validation/freeze
- `PA-EXT-A-006`: model/hardware qualification if required
- `PA-EXT-A-007`: single-use formal authorization
- `PA-EXT-A-008`: exactly one formal execution
- `PA-EXT-A-009`: result validation and scientific adjudication

## 28. Preregistration State

`PREREGISTRATION_STATE = FINAL_FROZEN_PRE_DATA_PROTOCOL`

`PANEL_CONTENT_STATUS = PANEL_CONTENT_NOT_YET_CREATED`

Protocol frozen does not mean panel content exists. No real panel items are
created by this task.

## 29. Hard Flags

- `REAL_EXT_A_PANEL_CREATED = false`
- `REAL_EXT_A_CANDIDATE_ITEMS_CREATED = false`
- `REAL_EXT_A_FIT_DATA_CREATED = false`
- `REAL_EXT_A_DIAG_DATA_CREATED = false`
- `REAL_EXT_A_EVAL_DATA_CREATED = false`
- `REAL_EXT_A_MODEL_INFERENCE_PERFORMED = false`
- `REAL_EXT_A_HIDDEN_STATES_ACCESSED = false`
- `REAL_EXT_A_RESULTS_CREATED = false`
- `REAL_EXT_A_AUTHORIZATION_CREATED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `EXP028_MODIFIED = false`