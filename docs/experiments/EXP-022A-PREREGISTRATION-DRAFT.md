# EXP-022A Preregistration Draft

Version: v0.2

Status: FREEZE CANDIDATE — NOT FROZEN

Implementation authorized: false

Model execution authorized: false

Formal EVAL access authorized: false

Scientific result status: NOT RUN

Historical authority reconciliation source:
`docs/research/experiments/EXP-022A-PROTOCOL-RECONCILIATION.md`

Reconciliation status: `AUTHORITY_RECONCILIATION_COMPLETE_v1.0`

This document records current proposed scientific decisions so they survive
migration and review.

Nothing marked `PROPOSED_NEW_FREEZE` or `PENDING_STATIC_RECONCILIATION` is frozen.

## Experiment title and position

Experiment title: `EXP-022A — Clean-State Layerwise Readout Transport Diagnosis`

Experiment type: prospectively preregistered mechanism follow-up on an existing
controlled dataset.

EXP-022A is NOT:

- an EXP-021 retry;
- EXP-021 Stage-P;
- an intervention-propagation experiment;
- a target-acquisition experiment;
- a perturbation-transport experiment;
- a functional-binding experiment;
- an independent-dataset replication.

The records used by EXP-022A have appeared in the earlier experimental lineage.
Held-out EVAL in EXP-022A therefore means held out from EXP-022A fitting, not
globally unseen data across the whole research program.

## Authority-resolved scientific object

`AUTHORITY_RESOLVED`

Representation object: `h_l^clean(x)`

Meaning: clean, non-intervened hidden representation at layer `l`.

Measurement target: `Y(x) = SOURCE_SEMANTIC_CLASS`

Frozen class universe/order:

```text
logic
causality
analogy
definition
```

`TARGET_SEMANTIC_CLASS` is NOT the EXP-022A measurement target.

EXP-022A does not measure:

- `delta_(s->t)`
- `h_l^TASK`
- `Delta h_l`
- target acquisition
- intervention perturbation transport

Construct definitions are referenced from `docs/research/CONSTRUCT-REGISTRY.md`
rather than redefined in this draft.

## Core research questions

`PROPOSED_NEW_FREEZE`

RQ1 — Held-Out Fixed-Frame Degradation

Does a source-semantic-class readout fitted only at the reference layer on FIT
data show degradation when applied unchanged to deeper clean representations on
untouched EVAL data?

RQ2 — Layerwise Readout Rescue

Conditional on evidence for held-out fixed-frame degradation, does allowing
increasingly adaptive layer-specific readout fitting recover held-out
source-class decoding performance?

Hierarchical logic:

First establish degradation.
Then interpret rescue.

Do not describe rescue as proof of coordinate remapping.

## Dataset identity

Historical controlled artifact: `experiments/exp003/prompts_controlled.json`

SHA-256:
`72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`

Authority-resolved facts:

- 24 records
- fields include: `id`, `group`, `variant_type`, `text`
- `SOURCE_SEMANTIC_CLASS` comes from `group`
- Do NOT print formal text

Exact EXP-022A FIT/EVAL ID arrays: `RESOLVED_092B`

Exact per-split record identities: `RESOLVED_092B`

## Complementary splits

Historical structure:

- Split A: original-style FIT, paraphrase-style EVAL
- Split B: paraphrase-style FIT, original-style EVAL

Current proposed EXP-022A requirements:

- 12 FIT records per split
- 12 untouched EVAL records per split
- four classes represented in FIT and EVAL
- candidate exact EVAL balance: 3 records per class

Exact EVAL balance: `RESOLVED_3_PER_CLASS`

Do NOT claim `orig_01 == para_01` source family.

Historical source-family pairing authority: `NOT AVAILABLE`

Task-091C status: `BLOCKED_NO_HISTORICAL_PAIR_AUTHORITY`

## Split inference boundary

`PROPOSED_NEW_FREEZE`

Analyze Split A separately.

Analyze Split B separately.

Do not pool A+B as 24 statistically independent observations.

Do not perform source-family paired bootstrap across A/B.

Cross-split agreement is a concordance diagnostic, not two independent
replications.

## Reference representation

Authority-resolved historical candidate:

- reference block: `16`
- hidden-state tuple index: `17`

Role in EXP-022A: reference measurement-frame origin.

Preferred scientific notation: `L_ref`

Do not call it an intervention layer when describing EXP-022A scientific
measurement.

Exact architecture/index reconciliation: `RESOLVED_092B`

## Depth set

Current proposal:

- all decoder block outputs from block16 through block27
- plus final normalized hidden state

Candidate semantics:

- block16 = reference
- block27 pre-final-RMSNorm = primary final endpoint candidate
- final post-RMSNorm = secondary mechanistic endpoint candidate
- intermediate block17–block26 trajectory = secondary descriptive trajectory candidate

Exact hook/hidden-state identity for every layer: `RESOLVED_092B`

Depth roles: `PROPOSED_NEW_FREEZE`

## Readout ladder

`PROPOSED_NEW_FREEZE`

A0 — Fixed Frame

Fit at `L_ref` on the split FIT set:

```text
S_ref
C_ref
```

Evaluate all layers using:

```text
C_ref(S_ref(h_l^EVAL))
```

No layer-specific parameter adaptation.

A1 — Featurewise-Affine Recalibration

At each layer `l`, fit only scaler `S_l` on that layer's FIT representations;
keep reference classifier `C_ref` fixed; evaluate:

```text
C_ref(S_l(h_l^EVAL))
```

Interpret narrowly: tests whether featurewise centering/scaling adaptation
improves reference classifier readout. Do NOT claim the same raw-space
hyperplane is preserved.

A2 — Layer-wise Linear Refit

At each layer `l`, fit `S_l` and same-family classifier `C_l` on that layer's
FIT representations; evaluate only on untouched EVAL:

```text
C_l(S_l(h_l^EVAL))
```

No EVAL-based tuning.

## Classifier specification status

`FREEZE_092C_REVISED`

Historical family:

- `StandardScaler`
- multinomial logistic regression

Exact effective parameters: `RESOLVED_092B`; explicit EXP-022A constructor
values: `FROZEN_092C`.

The frozen scientific scaler semantics are:

```text
StandardScaler(with_mean=True, with_std=True)
```

The frozen intended classifier semantics are:

```text
multiclass multinomial logistic regression
L2 regularization
solver = lbfgs
C = 1.0
fit_intercept = true
tol = 1e-4
class_weight = None
dual = false
max_iter = 1000
warm_start = false
random_state = 20260812
```

No layer-specific values. No tuning.

Detailed historical semantics and implementation-only argument treatment are
recorded in the Task-092B static operational reconciliation section below.

## Primary score

`FREEZE_092C_REVISED`

Primary performance metric: Balanced Accuracy.

BA is retained as the named primary score because the four frozen
source-semantic classes receive equal weight.

Each split contains exactly:

- 3 logic
- 3 causality
- 3 analogy
- 3 definition

Therefore, under the frozen balanced EVAL design:

`BA = ordinary accuracy = correct / 12`

for every layer/readout condition.

Primary effects are discrete paired item-level correctness contrasts.

Effect resolution: `1 / 12`.

Do not describe BA in EXP-022A as a smooth/continuous performance measure.

Secondary reporting candidates remain descriptive:

- raw correct count
- accuracy
- per-class recall
- macro-F1
- full probability vector

Probability-based metrics must not become primary.

## Inferential Target and Scope

`FREEZE_092C_REVISED`

The primary estimands are first and foremost finite controlled-set estimands
over the 12 preregistered EVAL records within each split.

The EVAL records are not claimed to be a probability sample from a formally
defined natural-language population.

Therefore:

- observed BA differences are exact descriptive effects for the frozen
  controlled EVAL set;
- any exact paired test adds a preregistered exchangeability-null model;
- that test does not convert the controlled set into a probability sample.

Claims must remain scoped to the controlled EXP-022A evaluation design unless
independently replicated later.

## Primary estimand 1 ? D_fixed

`FREEZE_092C_REVISED`

```text
D_fixed = BA_final^(A0) - BA_ref^(A0)
```

Define per-EVAL-item discordant correctness changes:

```text
loss_i: reference correct AND final A0 incorrect
gain_i: reference incorrect AND final A0 correct
```

Then:

```text
D_fixed = (number_of_gains - number_of_losses) / 12
```

Interpretation: negative values indicate held-out fixed-frame readout
degradation between reference and primary final representation.

Directional degradation corresponds to `losses > gains`.

Exact primary p-value for `D_fixed`:

```text
m_D = losses + gains
p_D = P[Binomial(m_D, 0.5) >= losses]
```

Primary support rule:

```text
D_FIXED_SUPPORTED iff D_fixed < 0 AND one-sided exact p_D <= 0.05
Otherwise: D_FIXED_NOT_SUPPORTED
```

`D_FIXED_NOT_SUPPORTED` does NOT mean stable.

Do not claim this is already known from EXP-021. EXP-021 used a different
FIT-LOO qualification estimand.

## Primary estimand 2 ? G_refit

`FREEZE_092C_REVISED`

```text
G_refit = BA_final^(A2) - BA_final^(A0)
```

Define per-EVAL-item discordant correctness changes:

```text
improvement: A0 final incorrect AND A2 final correct
harm:        A0 final correct   AND A2 final incorrect
```

Then:

```text
G_refit = (improvements - harms) / 12
```

Interpretation: positive values indicate layer-wise linear refit rescue relative
to the fixed frame at the primary final representation.

Exact primary p-value for `G_refit`:

```text
m_G = improvements + harms
p_G = P[Binomial(m_G, 0.5) >= improvements]
```

Primary mechanism status is gated:

```text
G_REFIT_PRIMARY_SUPPORTED iff D_FIXED_SUPPORTED
                          AND G_refit > 0
                          AND one-sided exact p_G <= 0.05
```

If `D_fixed` is not supported, `G_refit` MUST still be calculated and reported
as `PRE_SPECIFIED_SECONDARY_CONTRAST`, but it cannot support the primary rescue
claim. No outcome may suppress its reporting.

Do NOT label `G_refit` as proof of coordinate remapping.

## Secondary estimands

`FREEZE_092C_REVISED`

```text
G_scale  = BA_final^(A1) - BA_final^(A0)
G_noncal = BA_final^(A2) - BA_final^(A1)
R_refit  = BA_final^(A2) - BA_ref^(A2)
```

Status: `PRE_SPECIFIED_SECONDARY`

Report for each secondary contrast:

- point estimate
- underlying paired item-count changes where applicable
- class-stratified item-resampling robustness interval

Interpretation only:

- `G_scale`: featurewise-affine recalibration rescue
- `G_noncal`: additional same-family linear-refit rescue beyond featurewise recalibration
- `R_refit`: change in held-out performance of the preregistered linear readout family from reference to final representation

Do NOT assign binary `SUPPORTED` / `NOT_SUPPORTED` labels to these secondary
effects.

Do NOT apply formal secondary p-value testing in EXP-022A.

Secondary multiplicity policy: `DESCRIPTIVE_NO_BINARY_SUPPORT`.

Explicitly prohibit: `R_refit` decline == information disappearance.

Poor A2 performance does not establish absence of linear information under all
possible linear classifiers.

## Evidence vector

`FREEZE_092C_REVISED`

Keep the non-exclusive evidence-vector architecture.

Primary binary components:

```text
FIXED_DEGRADATION = SUPPORTED / NOT_SUPPORTED
REFIT_RESCUE = SUPPORTED / NOT_SUPPORTED / PRIMARY_GATE_CLOSED_SECONDARY_REPORTED
```

Cross-split primary summary:

```text
CROSS_SPLIT_SUPPORTED
PARTIAL_CONCORDANCE
SPLIT_HETEROGENEOUS
NOT_SUPPORTED
```

Secondary components:

```text
SCALE_RESCUE_ESTIMATE
ADDITIONAL_REFIT_RESCUE_ESTIMATE
REFIT_RETENTION_CHANGE_ESTIMATE
DEPTH_TRAJECTORY
```

Do not give secondary components binary discovery labels.

## Secondary item-resampling unit

Task-091C constraint: historical source-family clustering is not supported.

Current proposed within-split secondary bootstrap unit: held-out EVAL record ID.

All repeated measurements from one EVAL record must remain together across A0,
A1, A2, and all depth checkpoints.

Mark: `FREEZE_092C_REVISED`

Do not create original/paraphrase family pairing.

## Secondary bootstrap robustness interval

`FREEZE_092C_REVISED`

Bootstrap is removed from all primary support decisions.

Role: `SECONDARY_ITEM_RESAMPLING_ROBUSTNESS_SUMMARY`

Frozen candidate:

- 10,000 replicates
- RNG: NumPy `PCG64(20260817)`
- per split separately
- stratified by `SOURCE_SEMANTIC_CLASS`
- sample 3 records with replacement from each class's frozen 3 EVAL records
- all readout/layer measurements for a sampled EVAL record remain paired
- 95% percentile endpoints
- NumPy quantile method: `"linear"`

Output name:

`class-stratified item-resampling robustness interval`

This interval is NOT interpreted as population-sampling coverage.

It cannot change any primary exact-test conclusion.

## Exact conditional paired primary inference

`FREEZE_092C_REVISED`

Replace bootstrap-based primary inference with a one-sided exact conditional
paired test equivalent to exact McNemar / exact sign test on discordant
correctness pairs.

For each primary comparison, define two binary correctness values per EVAL
record.

Condition on total discordant count:

```text
m = n_plus + n_minus
```

Under the directional null, discordant direction is exchangeable with
probability `0.5`.

Exact one-sided probability:

```text
p_exact = P[Binomial(m, 0.5) >= number of discordant changes in the preregistered favorable direction]
```

No asymptotic approximation.

No continuity correction.

No mid-p.

No Monte Carlo approximation.

If `m = 0`, define `p_exact = 1.0`.

Interpretation label: `EXACT_CONDITIONAL_PAIRED_EVIDENCE_STATISTIC`, not
population-sampling certainty.

Prospectively freeze:

```text
alpha = 0.05
```

for each directional exact primary test. Tests are one-sided because directions
were preregistered before formal EXP-022A execution. No alpha may be changed
after result observation.

## Exact-test discreteness

`FREEZE_092C_REVISED`

The exact paired test is intentionally conservative at `n=12`.

For example:

- 4 favorable discordant changes and 0 unfavorable discordant changes gives
  `p_exact = 0.0625` and does NOT satisfy `alpha=0.05`.
- 5 favorable discordant changes and 0 unfavorable discordant changes gives
  `p_exact = 0.03125` and does satisfy `alpha=0.05`.
- `m=0` gives `p_exact = 1.0`.

This discreteness is accepted prospectively.

No alternate primary method may be substituted after results are known.

## Serial primary gate / multiplicity

`FREEZE_092C_REVISED`

Within each split, the primary sequence is:

1. `D_fixed`
2. conditional primary interpretation of `G_refit`

This is a preregistered serial gate.

No separate multiplicity correction is applied to the second primary claim,
because the stronger rescue claim requires success of the upstream degradation
claim and its own level-alpha test.

Do not describe this as two unconstrained independent `alpha=0.05` discoveries.

The primary rescue statement is a conjunction:

`degradation established AND refit rescue established`.

## Secondary inference

`FREEZE_092C_REVISED`

`G_scale`, `G_noncal`, `R_refit`, and full-depth trajectories are pre-specified
secondary candidates.

They may receive class-stratified item-resampling robustness intervals but may
not replace a failed primary result.

They must not receive binary `SUPPORTED` / `NOT_SUPPORTED` labels.

No formal secondary p-value testing is applied.

No multiplicity correction is applied to descriptive secondary contrasts.

No layer scanning may be used to promote a secondary layer into a primary claim.

## Cross-split concordance

`FREEZE_092C_REVISED`

Do NOT combine p-values.

Do NOT assume split independence.

For any primary directional claim:

`CROSS_SPLIT_SUPPORTED` only when BOTH Split A and Split B independently
satisfy the preregistered split-specific support criterion in the same
direction.

Describe this as a conjunction across complementary split views, not two
independent replications.

No independence assumption is required merely to demand that both component
criteria hold.

Do not derive a pooled effect or combined p-value.

Revised categories:

```text
CROSS_SPLIT_SUPPORTED
PARTIAL_CONCORDANCE
SPLIT_HETEROGENEOUS
NOT_SUPPORTED
```

Definitions:

- `CROSS_SPLIT_SUPPORTED`: both split-specific primary criteria support the
  preregistered direction.
- `PARTIAL_CONCORDANCE`: exactly one split supports the direction, and the
  other split's observed effect estimate has the same sign but does not meet
  its exact support rule.
- `SPLIT_HETEROGENEOUS`: observed split point estimates have opposite signs,
  OR one split provides preregistered directional support while the other
  provides support for the opposite direction, if an opposite-direction
  diagnostic is pre-specified. Do not create an unplanned opposite-direction
  hypothesis test merely to fill this category.
- `NOT_SUPPORTED`: neither split supports the preregistered direction, and
  there is no sign-defined split heterogeneity.

These categories are concordance summaries, not independent-replication
statistics.

## Exact Paired Test Interpretation

`FREEZE_092C_REVISED`

The 12 EVAL records are a fixed controlled evaluation set.

The observed effect itself is an exact finite-set quantity.

The exact conditional paired test uses a working exchangeability null over
discordant item directions.

This assumption is an inferential model, not evidence that the EVAL items are a
probability sample.

Therefore p-values do not justify population-general claims.

Independent replication on newly constructed source items is required before
claiming broader generality.

## Historical Stage-Q benchmark

Task-091D resolution: Stage-Q ruleset portability = `PARTIALLY_PORTABLE`.

Historical benchmarks only:

- correct `>= 7/12`
- 95% two-sided Clopper-Pearson lower bound `> 0.25`
- all four predicted classes represented

These may be reported only under `historical_stage_q_benchmark`.

They must not affect EXP-022A primary inference.

Global all-checkpoint Stage-Q gate: `DO_NOT_MIGRATE`

FIT-only / no-EVAL Stage-Q scope: `DO_NOT_MIGRATE`

## Full-depth descriptive trajectory

`FREEZE_092C_REVISED`

Keep block16 through block27-pre, plus block27-post, as a secondary descriptive
trajectory.

For every layer/readout condition report:

- BA
- `correct / 12`
- per-class recall

An optional preregistered class-stratified item-resampling robustness interval
may be reported.

No layer-specific hypothesis tests.

No multiplicity-adjusted layer discovery.

No post-hoc promotion of a layer into a primary endpoint.

## Final RMSNorm secondary analysis

`SECONDARY_CANDIDATE`

Keep `hidden_states[28]`, post-final-RMSNorm, as a secondary mechanistic
endpoint.

Its prospective inclusion is motivated in part by prior EXP-021 measurement
behavior. It is not primary and cannot replace block27-pre based on EXP-022A
outcome.

For each `Ak`:

```text
Delta_norm^(Ak) = BA_post_final_RMSNorm^(Ak) - BA_pre_final_RMSNorm^(Ak)
```

Purpose: describe whether final normalization is associated with additional
readout change under each adaptation level.

Do NOT add radial/angular decomposition.

## Technical validity principle

`TECHNICAL_INVALIDITY` must remain separate from `ADVERSE_SCIENTIFIC_RESULT`.

Candidate technical-invalidity causes:

- authority/config identity mismatch
- wrong model snapshot
- wrong layer identity
- FIT/EVAL overlap
- incorrect split IDs
- incorrect source-semantic labels/order
- EVAL used in fitting/tuning
- missing/duplicate EVAL observations
- incomplete A0/A1/A2 paired predictions
- classifier class-map mismatch
- invalid probability width
- nonfinite probabilities
- invalid probability normalization
- representation extraction failure
- wrong representation shape
- accidental intervention
- result/provenance/schema corruption
- unauthorized formal execution

These are candidates pending final technical gate freeze.

Valid adverse scientific outcomes include:

- low accuracy
- missing predicted class
- no fixed degradation
- no recalibration rescue
- no refit rescue
- refit decline
- split disagreement

These must never be converted into technical invalidity merely because they are
scientifically unfavorable.

## Probability diagnostics

`FREEZE_092C_REVISED`

Persist full four-class probability vectors.

Pre-specify as secondary diagnostics only:

- multiclass log loss
- mean true-class probability

If retained, explicitly label them:

`CALIBRATION_SENSITIVE_SECONDARY_DIAGNOSTIC`

They must not:

- replace BA
- alter primary support
- rescue a failed primary result

Do not add Brier score unless separately justified before freeze.

## Result artifact draft

Proposed per-EVAL prediction fields:

```text
split_id
eval_record_id
source_semantic_class
layer_id
representation_role
readout_condition

true_class
predicted_class

probability_logic
probability_causality
probability_analogy
probability_definition

correct
```

Proposed aggregate fields:

```text
balanced_accuracy
accuracy
per_class_recall
macro_f1

D_fixed
G_scale
G_refit
G_noncal
R_refit

d_fixed_one_sided_exact_p
g_refit_one_sided_exact_p
primary_gate_status
class_stratified_item_resampling_robustness_interval
cross_split_status
```

Exact schema: `PENDING_PREREGISTRATION_REVIEW`

Prohibit persistence of:

- prompt text
- raw hidden tensors
- raw activation tensors

## Stopping rule

`FREEZE_092C_REVISED`

One authorized formal scientific run.

After formal result generation, stop.

Convergence/no-retry policy:

```text
ConvergenceWarning with finite fitted coefficients AND finite valid probabilities
= TECHNICAL_WARNING_VALID_RESULT
```

Such warnings must be persisted in result metadata. No retry, no solver change,
no `max_iter` increase, and no `C` change are permitted.

```text
Hard estimator fit exception
OR nonfinite fitted coefficients
OR nonfinite/invalid probability outputs
= TECHNICALLY_INVALID
```

No same-experiment retry is permitted for a technically invalid run.

No same-experiment result-driven:

- re-run for scientific rescue
- classifier-family change
- hyperparameter change
- C tuning
- solver switching
- nonlinear probe
- primary-layer change
- metric change
- test change
- alpha change
- item deletion
- original/paraphrase retroactive pairing
- A/B pooling
- structured alignment
- bootstrap change
- CI-method change
- favorable-layer selection
- intervention addition

Any follow-up requires a new experiment / preregistration.

## Preregistered claim language

`FREEZE_092C_REVISED`

If `D_fixed` and gated `G_refit` are supported:

Allowed:

"The fixed reference readout showed supported held-out degradation at the
pre-registered final representation, while the preregistered layer-specific
linear readout family showed supported rescue."

Allowed interpretation: readout nonstationarity + linear-family refit rescue.

Not allowed: coordinate remapping proven.

If `D_fixed` supported and `G_refit` not supported:

Allowed:

"Fixed-frame degradation was supported, but the preregistered linear readout
family did not show supported rescue."

If `D_fixed` not supported:

Allowed:

"Held-out fixed-frame degradation was not supported. The preregistered refit
contrast is reported as secondary."

Not allowed: "representation is stable."

If splits disagree, report split heterogeneity / lack of concordance, not
replication.

## Interpretation boundary

EXP-022A may directly support evidence about:

- held-out fixed-frame degradation
- featurewise recalibration rescue
- layer-wise same-family linear-refit rescue
- additional refit rescue beyond recalibration
- held-out linear-decoding change
- depth-dependent readout nonstationarity
- split concordance / heterogeneity

Interpretive but not directly identified:

- readout-coordinate remapping
- representation compression
- late-layer integration

EXP-022A cannot establish:

- information absence
- nonlinear-decoding absence
- target acquisition
- perturbation transport
- causal propagation
- functional binding
- behavioral control
- cognitive folding
- non-Abelian dynamics
- universal Transformer laws


## Task-092B static operational reconciliation

Status: `EXP022A_STATIC_OPERATIONAL_RECONCILIATION = RESOLVED_092B`

### Exact frozen split identities

Authority source: `experiments/exp020/exp020_frozen_config.json` `dataset.splits`,
verified against `experiments/exp003/prompts_controlled.json` and
`experiments/exp021/engineering/stage_q_result.json`.

`EXACT_EVAL_CLASS_BALANCE = RESOLVED_3_PER_CLASS`

All four sets contain 12 unique IDs; FIT and EVAL are disjoint within each
split; every referenced ID exists in the controlled artifact. Do not claim A/B
statistical independence. Task-091C source-family negative remains valid.

Split A FIT:

```text
logic_orig_01, logic_orig_02, logic_orig_03
causality_orig_01, causality_orig_02, causality_orig_03
analogy_orig_01, analogy_orig_02, analogy_orig_03
definition_orig_01, definition_orig_02, definition_orig_03
```

Split A EVAL:

```text
logic_para_01, logic_para_02, logic_para_03
causality_para_01, causality_para_02, causality_para_03
analogy_para_01, analogy_para_02, analogy_para_03
definition_para_01, definition_para_02, definition_para_03
```

Split B FIT:

```text
logic_para_01, logic_para_02, logic_para_03
causality_para_01, causality_para_02, causality_para_03
analogy_para_01, analogy_para_02, analogy_para_03
definition_para_01, definition_para_02, definition_para_03
```

Split B EVAL:

```text
logic_orig_01, logic_orig_02, logic_orig_03
causality_orig_01, causality_orig_02, causality_orig_03
analogy_orig_01, analogy_orig_02, analogy_orig_03
definition_orig_01, definition_orig_02, definition_orig_03
```

Split identity reuse: `REUSE_FROZEN`.

### Model identity

- Model: `Qwen/Qwen3-1.7B`
- Architecture: `Qwen3ForCausalLM`
- Model type: `qwen3`
- Blocks: `28`
- Hidden size: `2048`
- Vocab size: `151936`
- Snapshot identity: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Historical execution dtype: `float16`
- Historical device: `cuda:0`
- Repository revision: `UNRECOVERED_NOT_USED_AS_EXECUTION_IDENTITY`
- Model identity basis: frozen content/snapshot manifest

### Tokenizer identity

- Tokenizer class: `Qwen2Tokenizer`
- Source: same frozen local snapshot
- `tokenizer_config.json` SHA-256:
  `d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101`
- `tokenizer.json` SHA-256:
  `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`
- Historical loader: `AutoTokenizer.from_pretrained(snapshot, local_files_only=True)`
- Historical tokenizer call: `return_tensors="pt"`, `padding=False`, `truncation=False`
- `add_special_tokens = true`
- `EXP022A_ADD_SPECIAL_TOKENS = true`

### Depth and tuple semantics

- `hidden_states[0]` = embedding output
- `hidden_states[1..27]` = decoder block 0..26 outputs, pre-final-RMSNorm
- `hidden_states[28]` = post-final-RMSNorm final normalized hidden state
- block27 pre-final-RMSNorm output is NOT tuple-accessible; it requires the
  frozen block27 output-hook semantics.

```text
block16 -> hs17
block17 -> hs18
block18 -> hs19
block19 -> hs20
block20 -> hs21
block21 -> hs22
block22 -> hs23
block23 -> hs24
block24 -> hs25
block25 -> hs26
block26 -> hs27
block27-pre -> hook, hs index null
block27-post -> hs28
```

### Reference and final identities

- Reference `L_ref`: block `16`, `hidden_states[17]`, pre-final-RMSNorm block output.
- Primary-final candidate operational identity: block27 pre-final-RMSNorm,
  `hooked_block_27_output`.
- Post-final candidate: `hidden_states[28]`, post-final-RMSNorm.

Primary endpoint freeze: primary reference = block `16` / `hidden_states[17]`;
primary final endpoint = block27 pre-final-RMSNorm hooked output. Justification:
this representation boundary was established as the historical primary-final
boundary before EXP-021 results were observed. Do not select it because of the
observed EXP-021 trajectory. `hidden_states[28]` remains a secondary mechanistic
endpoint.

### Token-position semantics

Historical extraction rule:

- one prompt per forward
- `padding=False`
- `truncation=False`
- attention mask validated all-ones
- selected token index = `int(attention_mask[0].sum().item()) - 1`
- representation = `tensor[0, selected_token_index, :]`

This is attention-mask-derived last-valid-token selection, not blind `-1`
selection. Status: `REUSE_FROZEN`.

### Representation numeric semantics

- Historical model hidden states: `torch.float16`
- Extraction: detach, CPU, NumPy copy
- Historical stored/stacked representation arrays: `float16`

EXP-022A analysis freeze:

- model execution remains `float16`
- historical extraction remains from `float16` hidden states
- immediately after extraction and before scaler/probe fitting, each
  representation vector is deterministically converted to NumPy `float32`
- all A0/A1/A2 analysis arrays enter the readout pipeline as `float32`

`EXP022A_ANALYSIS_DTYPE = FLOAT32_AFTER_FLOAT16_EXTRACTION`

This is a prospective numerical-analysis precision decision, not historical
Stage-Q behavior. Raw hidden tensors are not persisted.

### Historical StandardScaler semantics

- Historical construction: `StandardScaler()` under pinned `scikit-learn==1.9.0`
- Effective values: `copy=True`, `with_mean=True`, `with_std=True`
- Historical Stage-Q fit population: 11 FIT observations inside each LOO fold
- No historical Stage-Q full-FIT scaler exists

Historical scaler semantics: `RESOLVED`.

EXP-022A explicit scientific scaler freeze:

```text
StandardScaler(with_mean=True, with_std=True)
```

`copy=True` may be used as the implementation setting, but it is not a
scientific estimand and must not alter outputs.

`EXP022A_STANDARD_SCALER = EXPLICIT_WITH_MEAN_TRUE_WITH_STD_TRUE`

Do not rely on future sklearn defaults for `with_mean`/`with_std`.

### Historical LogisticRegression semantics

Historical effective semantics:

- `solver=lbfgs`
- effective L2 behavior
- `C=1.0`
- `fit_intercept=True`
- `tol=0.0001`
- `class_weight=None`
- `dual=False`
- `intercept_scaling=1`
- `l1_ratio=0.0` unused
- `max_iter=1000`
- `n_jobs=None`
- `verbose=0`
- `warm_start=False`
- `random_state=20260812`

Multinomial semantics: `EFFECTIVE_HISTORICAL_MULTINOMIAL`.

EXP-022A intended statistical model freeze:

```text
multiclass multinomial logistic regression
L2 regularization
solver = lbfgs
C = 1.0
fit_intercept = true
tol = 1e-4
class_weight = None
dual = false
max_iter = 1000
warm_start = false
random_state = 20260812
```

`EXP022A_CLASSIFIER = EXPLICIT_MULTINOMIAL_L2_LBFGS_C1`

No layer-specific values. No tuning. Implementation must use a version-pinned
constructor that realizes these semantics under the frozen scikit-learn version.

Do NOT require preservation of the historical compatibility/fallback code
pattern if a cleaner explicit constructor realizes the same intended model.
Record implementation-only arguments separately.

### Class / probability mapping

- `classifier.classes_` must uniquely contain all four frozen classes.
- Probability columns are explicitly remapped to `logic`, `causality`,
  `analogy`, `definition`.
- Predicted class = frozen class order at argmax of mapped probabilities.
- Status: `REUSE_FROZEN_IMPLEMENTATION_SEMANTICS`.

### A0 / A1 / A2 static status

A0:

- `EXP022A_A0_FULL_FIT_PROCEDURE = FREEZE_092C_REVISED`
- For each split, extract `L_ref` FIT representations.
- Deterministically cast analysis vectors according to the frozen
  analysis-dtype rule.
- Fit `S_ref` on all 12 FIT records.
- Fit `C_ref` on all 12 standardized FIT records.
- No LOO training.
- Apply fitted `S_ref + C_ref` unchanged to the untouched EVAL representation
  at `L_ref` and every downstream clean EVAL representation.
- No refitting by layer.

A1:

- `EXP022A_A1_STATIC_SPECIFICATION = FREEZE_092C_REVISED`
- For each layer `l`, fit `S_l` using only the 12 split FIT representations at
  layer `l`.
- Do not refit `C_ref`.
- Evaluate `C_ref(S_l(EVAL_l))`.
- Interpret only as per-feature FIT-derived mean/scale readout adaptation.
- Do not claim preservation of the same raw-space hyperplane.

A2:

- `EXP022A_A2_STATIC_SPECIFICATION = FREEZE_092C_REVISED`
- For each layer `l`, fit `S_l` on layer-l split FIT representations.
- Fit preregistered same-family `C_l` on those standardized FIT
  representations.
- Evaluate untouched `EVAL_l`.
- No hyperparameter tuning.

Do not implement A0/A1/A2 in this task.

### FIT / EVAL boundary

- `EXP022A_FIT_BOUNDARY = STATICALLY_IDENTIFIABLE`
- `EXP022A_EVAL_IDENTITY = STATICALLY_IDENTIFIABLE`

No EVAL representation may affect scaler fitting, classifier fitting,
hyperparameter selection, layer selection, metric selection, or threshold
selection. EVAL may be accessed only after condition-specific fit is complete,
and only by a future authorized protocol. Task-092BP does not authorize EVAL
access.

### Task-092B draft-conflict result

`EXP022A_DRAFT_AUTHORITY_CONFLICT = false`

Supported:

- split IDs
- 3-per-class balance
- `block16/hs17`
- block27 pre-final identity
- post-final identity
- full depth identity
- last-valid-token construct

Resolved by Task-092C:

- StandardScaler constructor
- LogisticRegression constructor
- effective multinomial wording
- representation numeric dtype decision
- full-FIT A0 procedure
- `add_special_tokens` explicit value

### Freeze-blocker status

- `EXP022A_HARD_FREEZE_BLOCKERS_PRESENT = false`
- `EXP022A_SOFT_NEW_FREEZE_ITEMS_PRESENT = false`
- `EXP022A_REREVIEW_REQUIRED = true`

Task-092C resolved the prior soft statistical/static items. Remaining pre-freeze
items are limited to independent rereview of v0.2, technical consistency checks,
and future post-freeze schema/authorization design.

Implementation readiness is not claimed.

### Task-092B Compliance Incident

`FORMAL_PROMPT_TEXT_EXPOSED = true`

Incident scope: during early Task-092B schema inspection, three controlled
prompt strings were printed in a tool transcript before suppression.

No repository file was modified. No model was run. No tokenizer was run. No
hidden/EVAL representations were computed. No predictions or metrics were
observed.

Classification: `PREREGISTRATION_PROCESS_COMPLIANCE_INCIDENT`, not
`SCIENTIFIC_RESULT_CONTAMINATION`.

Limitation: because the 24 controlled records are reused across complementary
FIT/EVAL roles, the project must NOT claim that EXP-022A EVAL textual content
remained fully researcher-blind before preregistration freeze. Use instead:
"EVAL is computationally held out from fitting/tuning." Do not use: "EVAL
content was unseen by researchers."

### POST_092B_CONTENT_EXPOSURE_GUARD

The exposed prompt contents may NOT be used to:

- change split identities
- change item inclusion
- change class definitions
- change primary/secondary metric
- change endpoint
- change readout family
- change hyperparameters
- change statistical method because of item content
- construct item-specific rules
- exclude difficult/favorable items

Future reviewers must not reopen or print controlled prompt text. Remaining
protocol changes must be justified only by historical authority, generic
statistical considerations, model architecture, pre-existing v0.1 design, or
reproducibility/technical correctness.

`EXP022A_POST_092B_CONTENT_EXPOSURE_GUARD = ACTIVE`

### Static reconciliation resolved

- exact Split A FIT IDs
- exact Split A EVAL IDs
- exact Split B FIT IDs
- exact Split B EVAL IDs
- exact per-split class counts
- exact model identity/snapshot
- tokenizer class/source/manifest identity
- reference-layer operational identity
- full block16-block27 depth map
- final pre-RMSNorm identity
- final post-RMSNorm identity
- last-valid-token semantics
- representation numeric semantics
- historical StandardScaler effective semantics
- historical LogisticRegression effective semantics
- class/probability mapping semantics
- FIT-only and EVAL access boundaries
- existing frozen artifact identities/hashes

### Soft new-freeze pending review

None from static/statistical review.

Remaining pre-freeze work is independent rereview of v0.2 and future
post-freeze schema/authorization design.

`EXP022A_PREREGISTRATION_FREEZE_BLOCKED_BY_STATIC_RECONCILIATION = false`


## Pre-freeze review items

`EXP022A_REREVIEW_REQUIRED = true`

Task-092C resolved the prior scientific/statistical review questions.

Remaining pre-freeze items:

1. independent rereview of the v0.2 freeze candidate (Task 092E)
2. technical consistency of exact-test definitions
3. technical consistency of classifier constructor under frozen sklearn version
4. schema/authorization design still to occur AFTER preregistration freeze

Do not claim implementation readiness.


## Current preregistration state flags

```text
EXP022A_PREREGISTRATION_VERSION = v0.2
EXP022A_PREREGISTRATION_STATUS = FREEZE_CANDIDATE_NOT_FROZEN
EXP022A_PRIMARY_METRIC = BALANCED_ACCURACY_EQUAL_TO_ACCURACY_ON_FROZEN_BALANCED_EVAL
EXP022A_PRIMARY_INFERENCE = ONE_SIDED_EXACT_CONDITIONAL_PAIRED
EXP022A_PRIMARY_ALPHA = 0.05
EXP022A_MID_P = false
EXP022A_BOOTSTRAP_ROLE = SECONDARY_ITEM_RESAMPLING_ROBUSTNESS
EXP022A_D_FIXED = PRIMARY
EXP022A_G_REFIT = GATED_PRIMARY_ALWAYS_REPORTED_SECONDARY_IF_GATE_CLOSED
EXP022A_SECONDARY_BINARY_SUPPORT = false
EXP022A_SPLIT_POOLING = PROHIBITED
EXP022A_CROSS_SPLIT_INDEPENDENCE_ASSUMED = false
EXP022A_PRIMARY_ENDPOINT = BLOCK27_PRE_FINAL_RMSNORM
EXP022A_ANALYSIS_DTYPE = FLOAT32_AFTER_FLOAT16_EXTRACTION
EXP022A_ADD_SPECIAL_TOKENS = true
EXP022A_STANDARD_SCALER = EXPLICIT_WITH_MEAN_TRUE_WITH_STD_TRUE
EXP022A_CLASSIFIER = EXPLICIT_MULTINOMIAL_L2_LBFGS_C1
EXP022A_EXACT_TEST_EXCHANGEABILITY_NULL = EXPLICITLY_DISCLOSED
EXP022A_POPULATION_SAMPLING_CLAIM = false
EXP022A_EVAL_RESEARCHER_CONTENT_BLIND = false
EXP022A_EVAL_COMPUTATIONALLY_HELD_OUT = true
EXP022A_POST_092B_CONTENT_EXPOSURE_GUARD = ACTIVE
EXP022A_REREVIEW_REQUIRED = true
EXP022A_PREREGISTRATION_FROZEN = false
EXP022A_IMPLEMENTATION_AUTHORIZED = false
EXP022A_MODEL_EXECUTION_AUTHORIZED = false
EXP022A_FORMAL_EVAL_ACCESS_AUTHORIZED = false
MODEL_LOAD_PERFORMED = false
TOKENIZER_LOAD_PERFORMED = false
CONTROLLED_PROMPT_TEXT_ACCESSED = false
FORMAL_EVAL_REPRESENTATIONS_ACCESSED = false
FROZEN_AUTHORITY_MODIFIED = false
REAL_EXPERIMENT_EVIDENCE_MODIFIED = false
COMMIT_PERFORMED = true
PUSH_PERFORMED = true

EXP022A_AUTHORITY_RECONCILIATION = COMPLETE_v1.0
EXP022A_STATIC_OPERATIONAL_RECONCILIATION = RESOLVED_092B
EXP022A_DRAFT_AUTHORITY_CONFLICT = false
EXP022A_HARD_FREEZE_BLOCKERS_PRESENT = false
EXP022A_SOFT_NEW_FREEZE_ITEMS_PRESENT = false
EXP022A_A0_FULL_FIT_PROCEDURE = FREEZE_092C_REVISED
EXP022A_A1_STATIC_SPECIFICATION = FREEZE_092C_REVISED
EXP022A_A2_STATIC_SPECIFICATION = FREEZE_092C_REVISED
EXP022A_INDEPENDENT_REVIEW_092C = COMPLETE
EXP022A_OPEN_REVIEW_ITEMS_PRESENT = true
EXP022A_SOURCE_FAMILY_BOOTSTRAP_SUPPORTED = false
EXP022A_SPLIT_WISE_EVAL_ITEM_INFERENCE = FREEZE_092C_REVISED
EXP022A_CONTRAST_BASED_PREREGISTRATION = FREEZE_092C_REVISED
FORMAL_PROMPT_TEXT_EXPOSED_IN_092B = true
```
