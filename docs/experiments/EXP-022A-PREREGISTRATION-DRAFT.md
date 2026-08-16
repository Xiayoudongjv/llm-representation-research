# EXP-022A Preregistration Draft

Version: v0.1

Status: DRAFT — NOT FROZEN

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

Exact EXP-022A FIT/EVAL ID arrays: `PENDING_STATIC_RECONCILIATION`

Exact per-split record identities: `PENDING_STATIC_RECONCILIATION`

## Complementary splits

Historical structure:

- Split A: original-style FIT, paraphrase-style EVAL
- Split B: paraphrase-style FIT, original-style EVAL

Current proposed EXP-022A requirements:

- 12 FIT records per split
- 12 untouched EVAL records per split
- four classes represented in FIT and EVAL
- candidate exact EVAL balance: 3 records per class

Exact EVAL balance: `PROPOSED_NEW_FREEZE`

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

Exact architecture/index reconciliation: `PENDING_STATIC_RECONCILIATION`

## Depth set

Current proposal:

- all decoder block outputs from block16 through block27
- plus final normalized hidden state

Candidate semantics:

- block16 = reference
- block27 pre-final-RMSNorm = primary final endpoint candidate
- final post-RMSNorm = secondary mechanistic endpoint candidate
- intermediate block17–block26 trajectory = secondary descriptive trajectory candidate

Exact hook/hidden-state identity for every layer:
`PENDING_STATIC_RECONCILIATION`

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

Historical family:

- `StandardScaler`
- multinomial logistic regression

Exact effective parameters: `PENDING_STATIC_RECONCILIATION`

A future frozen specification must state every scientifically relevant
effective parameter explicitly and not rely on version-dependent sklearn
defaults.

At minimum static reconciliation must recover/decide:

- solver
- penalty
- C
- fit_intercept
- class_weight
- max_iter
- tol
- multi-class behavior under installed sklearn version
- random_state applicability
- scaler with_mean
- scaler with_std

Do NOT fill unknown values in this draft.

## Primary score

`PROPOSED_NEW_FREEZE`

Primary performance metric: Balanced Accuracy.

BA = mean per-class recall across the four frozen source-semantic classes.

With exact 3-per-class EVAL balance, observed BA equals ordinary accuracy
numerically, but BA remains the scientific metric because all four classes
receive equal weight.

Secondary reporting candidates:

- raw correct count
- accuracy
- per-class recall
- macro-F1
- full probability vector

Do not make probability-based metrics primary in v0.1.

## Primary estimand 1

`PROPOSED_NEW_FREEZE`

```text
D_fixed = BA_final^(A0) - BA_ref^(A0)
```

Interpretation: negative values indicate held-out fixed-frame readout
degradation between reference and primary final representation.

Primary directional question: `D_fixed < 0`.

Do not claim this is already known from EXP-021. EXP-021 used a different
FIT-LOO qualification estimand.

## Primary estimand 2

`PROPOSED_NEW_FREEZE`

```text
G_refit = BA_final^(A2) - BA_final^(A0)
```

Interpretation: positive values indicate layer-wise linear refit rescue relative
to the fixed frame at the primary final representation.

Hierarchical rule candidate: `G_refit` becomes primary mechanism-interpretable
only after the preregistered fixed-degradation gate is supported.

Do NOT label `G_refit` as proof of coordinate remapping.

## Secondary estimands

`PRE-SPECIFIED_SECONDARY_CANDIDATE`

```text
G_scale  = BA_final^(A1) - BA_final^(A0)
G_noncal = BA_final^(A2) - BA_final^(A1)
R_refit  = BA_final^(A2) - BA_ref^(A2)
```

Possible interpretation only:

- `G_scale`: featurewise-affine recalibration rescue
- `G_noncal`: additional same-family linear-refit rescue beyond featurewise recalibration
- `R_refit`: change in held-out layerwise-refit linear decodability from reference to final representation

Explicitly prohibit: `R_refit` decline == information disappearance.

## Evidence vector

Current preferred result representation: do NOT force one mutually exclusive
mechanism label.

Candidate evidence vector:

```text
FIXED_DEGRADATION
SCALE_RESCUE
REFIT_RESCUE
ADDITIONAL_REFIT_RESCUE
REFIT_RETENTION_CHANGE
SPLIT_CONCORDANCE
```

Status values and exact classification rules remain:
`PROPOSED_NEW_FREEZE / NOT YET FINALIZED`

## Resampling unit

Task-091C constraint: historical source-family clustering is not supported.

Current proposed within-split resampling unit: held-out EVAL record ID.

All repeated measurements from one EVAL record must remain together across A0,
A1, A2, and all depth checkpoints.

Mark: `PROPOSED_NEW_FREEZE`

Do not create original/paraphrase family pairing.

## Bootstrap proposal

`PROPOSED_NEW_FREEZE — NOT YET REVIEWED`

Candidate:

- 10,000 bootstrap replicates
- RNG: NumPy `PCG64(20260817)`

For each split separately:

- within each source semantic class, sample 3 EVAL record IDs with replacement
  from that class's 3 EVAL records
- total per replicate: 12 EVAL records
- use identical resampled record identities for every readout condition and
  layer in the replicate

Candidate CI:

- 95% percentile interval
- NumPy quantile method: `"linear"`

This statistical choice requires preregistration review before freeze.

## Hierarchical primary inference

`PROPOSED_NEW_FREEZE`

For each split separately:

Step 1: Compute bootstrap CI for `D_fixed`.

Candidate support rule:

- upper endpoint of 95% CI < 0 => `FIXED_DEGRADATION_SUPPORTED`
- otherwise => `FIXED_DEGRADATION_NOT_SUPPORTED`

`NOT_SUPPORTED` does not imply evidence of stability.

Step 2: Only if Step 1 is supported, interpret `G_refit` as the second primary
contrast.

Candidate support rule:

- lower endpoint of 95% CI > 0 => `REFIT_RESCUE_SUPPORTED`
- otherwise => `REFIT_RESCUE_NOT_SUPPORTED`

The hierarchical gate is intended to prevent interpreting rescue when the
held-out fixed degradation itself was not established.

## Secondary inference

`G_scale`, `G_noncal`, `R_refit`, and full-depth trajectories are pre-specified
secondary candidates.

They may receive CIs but may not replace a failed primary result.

No layer scanning may be used to promote a secondary layer into a primary claim.

Multiplicity policy beyond the hierarchical primary gate:
`PENDING_PREREGISTRATION_REVIEW`

## Cross-split concordance

`PROPOSED_NEW_FREEZE`

Proposed categories:

```text
CROSS_SPLIT_SUPPORTED
PARTIAL_CONCORDANCE
SPLIT_HETEROGENEOUS
NOT_SUPPORTED
```

Draft definitions:

- `CROSS_SPLIT_SUPPORTED`: both split-specific CIs support the same
  preregistered direction.
- `PARTIAL_CONCORDANCE`: one split supports the direction and the other point
  estimate has the same direction but its CI includes zero.
- `SPLIT_HETEROGENEOUS`: point estimates have opposite signs, or one split
  clearly supports the opposite direction.
- `NOT_SUPPORTED`: neither supports the preregistered direction and there is no
  clear heterogeneity.

Cross-split concordance is not two independent replications.

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

## Final RMSNorm secondary analysis

`SECONDARY_CANDIDATE`

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

bootstrap_ci
cross_split_status
```

Exact schema: `PENDING_PREREGISTRATION_REVIEW`

Prohibit persistence of:

- prompt text
- raw hidden tensors
- raw activation tensors

## Stopping rule

`PROPOSED_NEW_FREEZE`

One authorized formal scientific run.

After formal result generation, stop.

No same-experiment result-driven:

- classifier-family change
- hyperparameter tuning
- C tuning
- solver switching
- nonlinear probe
- primary-layer change
- item deletion
- original/paraphrase retroactive pairing
- A/B pooling
- structured alignment
- bootstrap change
- CI-method change
- primary metric change
- favorable-layer selection
- intervention addition

Any follow-up requires a new protocol / experiment.

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

## Operational constants pending static reconciliation

`PENDING_STATIC_RECONCILIATION`

- exact Split A FIT IDs
- exact Split A EVAL IDs
- exact Split B FIT IDs
- exact Split B EVAL IDs
- exact 3-per-class balance verification
- exact Qwen3-1.7B snapshot/revision
- exact tokenizer identity if extraction requires it
- exact reference-layer operational identity
- exact block17–block27 extraction identities
- exact final pre-RMSNorm extraction identity
- exact final post-RMSNorm extraction identity
- exact last-valid-token semantics
- exact StandardScaler effective configuration
- exact LogisticRegression effective configuration
- exact classifier probability/class mapping
- exact representation dtype requirements
- exact FIT-only fitting boundaries
- exact EVAL access boundary
- frozen artifact hashes needed by the future config

`EXP022A_PREREGISTRATION_FREEZE_BLOCKED_BY_STATIC_RECONCILIATION = true`

## Review questions before v1.0

`OPEN_REVIEW_ITEMS`

1. Is BA the correct primary score for n=12 balanced four-class EVAL?
2. Is class-stratified item bootstrap with 3 items/class statistically
   defensible as the preregistered inferential procedure?
3. Is percentile bootstrap CI appropriate at this sample size?
4. Should D_fixed be the sole first primary gate?
5. Is G_refit appropriately hierarchical after D_fixed?
6. Are G_scale/G_noncal/R_refit correctly secondary?
7. Is block27 pre-final-RMSNorm sufficiently prior-justified as primary final
   endpoint?
8. Is the cross-split concordance rule sufficiently conservative?
9. Is any multiplicity control needed for the pre-specified secondary set?
10. Are all result interpretations weaker than the actual estimands?

## Current preregistration state flags

```text
EXP022A_PREREGISTRATION_VERSION = v0.1
EXP022A_PREREGISTRATION_STATUS = DRAFT
EXP022A_PREREGISTRATION_FROZEN = false
EXP022A_AUTHORITY_RECONCILIATION = COMPLETE_v1.0
EXP022A_STATIC_OPERATIONAL_RECONCILIATION = PENDING_092B
EXP022A_OPEN_REVIEW_ITEMS_PRESENT = true
EXP022A_SOURCE_FAMILY_BOOTSTRAP_SUPPORTED = false
EXP022A_SPLIT_WISE_EVAL_ITEM_INFERENCE = PROPOSED_NEW_FREEZE
EXP022A_CONTRAST_BASED_PREREGISTRATION = PROPOSED
EXP022A_IMPLEMENTATION_AUTHORIZED = false
EXP022A_MODEL_EXECUTION_AUTHORIZED = false
EXP022A_FORMAL_EVAL_ACCESS_AUTHORIZED = false
FROZEN_AUTHORITY_MODIFIED = false
REAL_EXPERIMENT_EVIDENCE_MODIFIED = false
```
