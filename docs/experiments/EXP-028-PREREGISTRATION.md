# EXP-028 Preregistration

**Experiment:** EXP-028
**Working name:** PAIRED_INFORMATION_BEYOND_MARGINAL_RECALIBRATION
**Status:** `FROZEN_DESIGN_NOT_RUN`
**103C correction:** prospective preregistration clarification; see `EXP-028-103C-PREREGISTRATION-CORRECTION.md`
**Preregistration task:** `103B_EXP028_AUTHORITY_BINDING_AND_PREREGISTRATION_DRAFT`
**Authority/freeze commit:** `86c120f56ee615540ecff15bb62f8d05eaca7700`

## Scientific Question

Given a fixed source-layer readout and a deeper target representation, does a
FIT-only, label-free, coordinatewise affine map learned from paired
representations provide held-out improvement beyond inherited marginal
mean/scale recalibration in:

1. direct representation matching, and
2. fixed-readout compatibility?

EXP-028 does **not** test transport directly, does **not** establish invariant
preservation, does **not** test Functional Binding, and does **not** validate
Residual-Flow as a whole.

## Origin and Scope

- `ORIGIN_CLASS = RESULT_CONDITIONED_ASSET_DERIVED_CANDIDATE`
- `FULL_RESIDUAL_FLOW_TEST = false`
- `FULL_MSA_TEST = false`
- `TRANSPORT_TEST = false`
- `INVARIANT_TEST = false`
- `FUNCTIONAL_BINDING_TEST = false`

Primary ancestry: EXP-007 (`transformation success != transformation
validity`), EXP-022A (`A_mu_sigma`), EXP-026, EXP-027, `HYP-TRANSPORT-001`,
Minimum Sufficient Alignment motivation, and Residual-Flow RF-4 relevance only.

## Authority Binding

The explicit authority-binding table is in
`experiments/exp028/exp028_authority_binding.json`.

### Model Authorities

| Model | Identity | Snapshot / Source | Layers | Hidden |
|---|---|---|---|---|
| Qwen | `Qwen/Qwen3-1.7B` | `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | `0..27` | `2048` |
| OLMo | `allenai/OLMo-2-0425-1B-Instruct` | `48d788eca847d4d7548f375ad03d3c9312f6139e` | `0..15` | `2048` |
| Llama | `Meta-Llama-3.2-1B-Instruct` | META official native -> HF converted, `1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f` | `0..15` | `2048` |

### Carrier Semantics

- API: `FORWARD_HOOK_DECODER_BLOCK_OUTPUT`
- Module path: `model.model.layers[l]`
- Output: post-decoder-block residual before next block and before model final norm
- Forbidden carrier: `outputs.hidden_states[-1]`

### Probe Contract

- Classifier: `LogisticRegression`
- Solver: `lbfgs`; penalty: `L2`; `C=1.0`
- `fit_intercept=true`; `tol=1e-4`; `class_weight=null`
- `dual=false`; `max_iter=1000`; `warm_start=false`
- Class order: `logic`, `causality`, `analogy`, `definition`
- Probability mapping: `classifier.classes_`
- FIT-only: `FIT_condition_realization_only`

### Moment Recalibration `A_mu_sigma`

`T_mu_sigma(h_j)_k = ((h_j,k - mu_j,k^FIT) / sigma_j,k^FIT) * sigma_i,k^FIT + mu_i,k^FIT`

This is a target-to-source-frame marginal mean/scale recalibration. All moments
come from FIT paired representations only, using population variance (`ddof=0`).

## Operator Families

Three frozen primary conditions:

- `T0`: identity / raw fixed frame, `T0(h_j)=h_j`
- `T1`: inherited moment recalibration, `T_mu_sigma`
- `T2`: paired coordinatewise affine alignment, `T_pair_diag(h_j)_k = a_k*h_j,k + b_k`

`T_pair_diag` is:

- label-free;
- FIT-only;
- closed-form coordinatewise OLS;
- no cross-coordinate mixing;
- no hyperparameter search;
- no task-loss optimization;
- not optimized against `DELTA_RO`.

Primary comparator: `T_pair_diag vs T_mu_sigma` (`T2_MINUS_T1`).
Frozen baseline: `T1_MOMENT_RECALIBRATION`. Frozen contrast: `T2_MINUS_T1`.
`T0` remains baseline/descriptive context and may not replace `T1` as the primary comparator.

## Numerical Edge-Case Rules

- Frozen `epsilon = 0.0`.
- Population variance convention: `ddof=0`.
- Zero target variance: `TECHNICALLY_INVALID_MODEL`.
- Non-finite variance, covariance, or fitted coefficient:
  `TECHNICALLY_INVALID_MODEL`.
- Source denominator sigma <= 0 or non-finite: `TECHNICALLY_INVALID_MODEL`.
- Near-zero positive variance is computed without an epsilon and invalidated if
  non-finite.
- No tunable epsilon and no post-outcome tuning.

## Primary Endpoints

### Representation endpoint: `DELTA_RM`

`DELTA_RM = E(T_mu_sigma) - E(T_pair_diag)`

where

`E(T) = mean over fresh EVAL item and coordinate of ((T(h_j)_k - h_i,k) / sigma_i,k^FIT)^2`.

Positive means paired information improves direct representation matching beyond
marginal recalibration.

### Readout endpoint: `DELTA_RO`

`DELTA_RO = C_pair - C_mu_sigma`

where each `C` is the balanced accuracy of the frozen source-layer probe `P_i`
applied to the corresponding transformed target representation on fresh EVAL.

Positive means paired coordinate information contributes fixed-readout recovery
beyond marginal recalibration.

Balanced accuracy is macro-average per-class recall over `logic`, `causality`,
`analogy`, and `definition`.

## Model-Level State Routing

- `RM_SUPPORTED` iff `ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND` for `DELTA_RM` is greater than `0`
- `RO_SUPPORTED` iff `ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND` for `DELTA_RO` is greater than `0`
- The central 90% interval `[q_0.05, q_0.95]` is descriptive only and does not determine support.

| State | Registered interpretation |
|---|---|
| `(RM+, RO+)` | `JOINT_ALIGNMENT_CONTRIBUTION` |
| `(RM+, RO-)` | `REPRESENTATION_ONLY` |
| `(RM-, RO+)` | `READOUT_ONLY_ARTIFACT_RISK` |
| `(RM-, RO-)` | `NO_PAIRED_COORDINATE_CONTRIBUTION` |

`READOUT_ONLY_ARTIFACT_RISK` is cautionary and is **not** alignment success.

## Three-Model Routing

Exact state matching only. No majority vote, no endpoint voting, no
nearest-profile routing, no post-hoc grouping.

- Any model technically invalid: `NOT_FULLY_ADJUDICATED`
- All three `JOINT_ALIGNMENT_CONTRIBUTION`: `THREE_MODEL_JOINT_COORDINATEWISE_COMPONENT`
- All three share another exact state: `THREE_MODEL_COMMON_STATE`
- Otherwise: `MODEL_DEPENDENT_ALIGNMENT_STATE`

One invalid model is never dropped to create a two-model success claim.

## Bootstrap Contract

- Design: condition-stratified source-family cluster bootstrap
- Resampling unit: `source_family`
- Statistical unit: `source_family_cluster`
- Strata: `condition`
- Row multiplicity: all records of sampled source family
- Bit generator: `numpy.random.PCG64`
- Seed: `20260819`
- Replicates: `5000`
- CI method: percentile
- Quantile method: `numpy.percentile_method_linear`

Primary support decision:

- `primary_support_ci = ONE_SIDED_95_PERCENT_LOWER_PERCENTILE_BOUND`
- Level: `0.95`
- Side: lower
- Percentile: `5`
- A primary endpoint is supported iff its one-sided 95% lower percentile
  bootstrap bound is greater than `0`.

Descriptive interval only:

- `descriptive_central_interval = CENTRAL_90_PERCENT_PERCENTILE_INTERVAL`
- Level: `0.90`
- Lower percentile: `5`
- Upper percentile: `95`
- This is a central 90% interval and does **not** determine support.
- `two_sided_95_percent_ci_used = false`

Additional operational quantiles:

- One-sided positive lower bound: `5`
- One-sided negative upper bound: `95`

- Invalid replicate handling: skip replicates that do not preserve all four classes
- No operator refit and no probe refit inside EVAL bootstrap
- No bootstrap shopping

The seed/replicate count inherits EXP-026 and EXP-027 source-family cluster
conventions.

## Aggregation Order

For each model, in this exact order:

1. `item/source_family`: mean over fresh EVAL source-family item-level pairs
2. `source_family`: mean over fresh EVAL source families, equal weight
3. `condition`: arithmetic mean over all 10 conditions, equal weight
4. `layer_pair`: arithmetic mean over all preregistered ordered forward pairs `j > i`, equal weight
5. `model`: independent per model

Forbidden weighting: token count, layer distance, EXP-027 profile weighting,
LOW-D subset selection, and interesting-layer selection.

The primary statistics cannot be altered by token count, layer distance,
number of items per family, LOW-D status, EXP-027 profile, or
interesting-layer selection.

## DIAG Role

`DIAG` is technical qualification only.

DIAG may check probe qualification, finite operator coefficients, required
layer/source coverage, normalized depth span, class integrity, and source-family
integrity.

DIAG must **not** select favorable layer pairs or models, change operator family,
endpoint, bootstrap, or threshold, or determine whether EVAL is worth running.

Inherited qualification floors:

- Source technical floor: `0.75` on DIAGNOSTIC
- Source coverage minimum count: `8`
- Source coverage minimum fraction: `0.5`
- Source coverage minimum normalized depth span: `0.5`

## Pair-Break Control

- Status: `SECONDARY_ONLY`
- Purpose: test whether paired-map behavior depends on true item correspondence
  rather than marginal statistics only
- Scope: `within_FIT_per_condition_per_layer_pair`
- Ordering: lexicographic source-family ID
- Condition handling: independent per condition
- Source-family handling: preserve source-family count and marginals
- Procedure: within FIT, sort source-family IDs lexicographically and assign the
  target sequence by a deterministic cyclic shift of one
- Preserves source marginals, target marginals, sample count, and coordinates
- Same operator family: coordinatewise OLS
- RNG: none (deterministic cyclic shift)
- It cannot rescue a failed primary endpoint.

## Operator Capacity Firewall

EXP-028 remains coordinatewise. The following are prohibited post-hoc rescue
families:

`dense_affine_matrix`, `low_rank_cross_coordinate_map`,
`orthogonal_Procrustes`, `MLP`, `KAN`, `spline_adapter`,
`attention_adapter`, `learned_residual_network`.

Only a prospectively adjudicated EXP-028 result may motivate a later
cross-coordinate capacity experiment.

## Claim Ceiling

Even the strongest registered EXP-028 outcome may support only:

> Paired item-level coordinate information contributes held-out direct
> representation matching and fixed-readout compatibility beyond marginal
> feature recalibration in the tested model(s).

EXP-028 may **not** establish transport, semantic equivalence, information
preservation, invariant preservation, Functional Binding, reasoning causality,
universal transformer law, Residual-Flow confirmation, or MSA confirmation.

## Fresh Data Firewall

EXP-028 must use fresh scientific items. No EXP-024/025/026/027 scientific FIT,
DIAG, or EVAL item may become EXP-028 confirmatory scientific evidence.

Prior-panel exclusion authorities:

| Authority | Path | SHA-256 |
|---|---|---|
| EXP-023 independent controlled panel | `experiments/exp023/data/exp023_independent_controlled.json` | `9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a` |
| EXP-024 frozen condition panel dataset | `experiments/exp024/data/exp024_condition_panel_frozen.json` | `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404` |
| EXP-024 condition panel specification | `experiments/exp024/condition_panel_spec.json` | `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954` |
| EXP-024 data schema | `experiments/exp024/data_schema.json` | `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec` |
| EXP-024 frozen manifest | `experiments/exp024/exp024_frozen_manifest.json` | `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59` |

Freshness normalization: NFKC normalization, strip, then collapse each maximal
Unicode whitespace run to a single ASCII space. Duplicate hash is SHA-256 of the
UTF-8 normalized text.

Required freshness checks:

1. no normalized raw-text SHA-256 collision with prior scientific panels;
2. no prior source-family reuse where source-family identity exists;
3. no paraphrase-family leakage where such identity exists;
4. panel frozen before scientific model inference;
5. no item replacement after real hidden-state extraction begins.

The final scientific panel is **not** generated in 103B or 103C.

## Terminology

Use: cross-depth fixed-readout compatibility, marginal recalibration, paired
coordinate information, coordinatewise alignment, representation-match
contribution, fixed-readout contribution.

Avoid confirmatory use of: true semantic axis, semantic transport,
representation preservation, latent equivalence, causal transformation, valid
transport.

## No Scientific Execution

- `REAL_EXP028_FIT_ACCESSED = false`
- `REAL_EXP028_DIAG_ACCESSED = false`
- `REAL_EXP028_EVAL_ACCESSED = false`
- `EXP028_SCIENTIFIC_INFERENCE_PERFORMED = false`
- `EXP028_RESULT_CREATED = false`
- `EXP028_AUTHORIZATION_CREATED = false`
- `EXP028_FORMAL_RUN_PERFORMED = false`

## Validator

`experiments/exp028/validate_exp028_preregistration.py`

The validator checks the frozen design JSON and the explicit authority-binding
file. It does not load a model or access real scientific data.

## Next Step

`103D_EXP028_RUNNER_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION`
