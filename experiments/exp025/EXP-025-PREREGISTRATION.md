# EXP-025 Preregistration

Status: `FROZEN_DESIGN_NOT_RUN`

This is the frozen prospective design for EXP-025. It is closed to
outcome-dependent change before any OLMo model forward pass on EXP-025 formal
scientific data, any DIAGNOSTIC/EVAL outcome access, any formal-run
authorization, or any scientific result creation.

## Experiment Identity

- Experiment: `EXP-025`
- Role: `CROSS_MODEL_ROUTING_EXPERIMENT`
- Design status: `FROZEN_DESIGN_NOT_RUN`
- Scientific status: `NOT_OBSERVED`
- Primary change: `MODEL FAMILY`
- Inherited dataset and condition panel: `EXP-024`
- Next task: `100B_EXP025_ENGINEERING_QUALIFICATION`

## Scientific Isolation

EXP-025 is not Paper B and is not a new scientific construct battery.

The only intended major scientific change from EXP-024 is:

```text
Qwen3-1.7B -> OLMo-2-0425-1B-Instruct
```

The following are forbidden in EXP-025:

- KAN operator or KAN-like nonlinear adapter
- MLP adapter
- LoRA
- low-rank operator
- full affine operator
- nonlinear spline adapter
- invariant objective
- functional-binding experiment
- new steering intervention
- layer sweep
- model shopping after semantic measurement qualification begins

## Frozen Model

- Primary model: `allenai/OLMo-2-0425-1B-Instruct`
- Exact Hugging Face revision: `48d788eca847d4d7548f375ad03d3c9312f6139e`
- Model family: `OLMo2`
- Architecture: `Olmo2ForCausalLM`
- `model_type`: `olmo2`
- License: `apache-2.0`
- Frozen config SHA-256:
  `0d15ebb6cb8d998513b46ef337214176a6fd59fe5f16b30387c70d5f87795a9c`
- Frozen tokenizer config SHA-256:
  `50c412c57d832057a3d5db42064c741f751e570f7c8788f037bfb0d2dd6e5f49`
- `num_hidden_layers`: `16`
- `hidden_size`: `2048`
- `num_attention_heads`: `16`
- `num_key_value_heads`: `16`
- `torch_dtype`: `bfloat16`
- `max_position_embeddings`: `4096`
- `vocab_size`: `100352`
- Reported BF16 parameter count: `1484916736`
- `transformers_version` in model config: `4.50.0`
- Local runtime Transformers version is separately recorded and must be
  checked for compatibility during Task 100B. It is not a model-shopping
  trigger.

## Data Control

Inherit the EXP-024 frozen dataset byte-for-byte:

- Path: `experiments/exp024/data/exp024_condition_panel_frozen.json`
- SHA-256:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Record count: `1760`
- Source-family count: `880`
- Condition count: `10`
- Semantic-class count: `4`
- Semantic classes: `logic`, `causality`, `analogy`, `definition`
- Record roles: `reference_form`, `condition_realization`

EXP-025 reuses the same source families, semantic classes, FIT partition,
DIAGNOSTIC partition, EVAL partition, ten-condition panel, and frozen condition
order. This isolates `MODEL FAMILY` while keeping `DATASET` fixed.

Cross-model replication does not by itself establish cross-dataset generality.

## FIT / DIAGNOSTIC / EVAL Firewall

Inherit EXP-024 source-family separation:

- FIT: `6` source families per condition and semantic class
- DIAGNOSTIC: `8` source families per condition and semantic class
- EVAL: `8` source families per condition and semantic class
- `FIT intersect DIAGNOSTIC = empty`
- `FIT intersect EVAL = empty`
- `DIAGNOSTIC intersect EVAL = empty`

FIT may be used only for:

- OLMo-specific `C_ref_OLMo`
- OLMo-specific reference scaler
- OLMo-specific condition recalibration parameters

DIAGNOSTIC is used only for frozen diagnostic quantities.

EVAL is used only for frozen confirmatory outcome quantities.

Before formal execution, no EVAL label/outcome may be inspected to choose a
layer, model, calibration variant, or threshold.

## Model-Specific Readout

Absolute prohibition:

```text
DO NOT apply the Qwen C_ref to OLMo hidden states.
```

EXP-025 fits a model-specific readout:

```text
OLMo block9_pre_final_rmsnorm + OLMo FIT only -> C_ref_OLMo
```

Then the same frozen `C_ref_OLMo` is fixed for all later OLMo checkpoint
representations.

The replicated construct is:

```text
FIXED-READOUT-WITHIN-MODEL EXPERIMENTAL CONSTRUCT
```

It is not cross-model coordinate transfer.

## Tokenization Contract

Preserve the EXP-024 scientific tokenization logic:

```text
tokenizer(text, return_tensors="pt")
```

Do not automatically use the OLMo chat template merely because the model card
contains one.

Preserve:

- same raw scientific prompt text
- same last-valid-token extraction semantics
- same padding/truncation semantics
- same special-token policy

Only tokenizer vocabulary/special-token implementation is allowed to differ.

If OLMo default special-token behavior materially conflicts with the frozen
construct, the correct status is `STOP_AND_REPORT`; do not silently modify the
construct.

## Checkpoint Mapping

Frozen checkpoint mapping:

- Qwen reference block: `block16_pre_final_rmsnorm`
- Qwen final block: `block27_pre_final_rmsnorm`
- OLMo reference checkpoint: `block9_pre_final_rmsnorm`
- OLMo final checkpoint: `block15_pre_final_rmsnorm`
- OLMo post-final descriptive checkpoint: `block15_post_final_rmsnorm`

Mapping rule:

```text
normalized_depth = block_index / (num_hidden_layers - 1)
OLMo candidate = round(normalized_depth * (OLMo_num_hidden_layers - 1))
```

Numerical derivation:

- Qwen reference normalized depth: `16 / 27`
- OLMo reference candidate: `round(16 / 27 * 15) = round(8.8888888889) = 9`
- Qwen final normalized depth: `27 / 27 = 1.0`
- OLMo final candidate: `15 / 15 = 1.0`

Block indexing is `0-based` for both models.

Task 100B must verify actual OLMo hook/hidden-state semantics before any formal
scientific execution. The mapping is frozen in this design; it is not
outcome-dependent and no layer sweep is permitted.

## Representation Object

Use clean, non-intervened, last-valid-token hidden representations at the
frozen OLMo checkpoint.

The OLMo representation must be the residual-stream output after the complete
selected decoder block and before the final `model.norm`, matching the logical
EXP-024 construct rather than the Qwen module name.

## Classifier Contract

Use the same frozen classifier contract as EXP-024:

```text
LogisticRegression:
  solver = lbfgs
  penalty = L2
  C = 1
  fit_intercept = true
  tol = 1e-4
  class_weight = none
  dual = false
  max_iter = 1000
  warm_start = false
```

No hyperparameter tuning is allowed. Outputs must be mapped through
`classifier.classes_`.

## Calibration Variants

Exactly four variants are allowed, inherited from Paper A / EXP-024:

```text
A0
A_mu
A_sigma
A_mu_sigma
```

No other calibration family is allowed.

## Primary Scientific Questions

`RQ1` (primary): `FIXED_READOUT_DEGRADATION_CROSS_MODEL`

```text
Does fixed semantic readout compatibility degrade across depth in an
independent model family?
```

`RQ2` (primary): `FIT_ONLY_RECALIBRATION_RECOVERY_CROSS_MODEL`

```text
Can the already-defined low-capacity FIT-only featurewise recalibration
recover held-out readout performance in that model?
```

`RQ3` (secondary only): `SECONDARY`

```text
Does the previously preregistered independent degradation diagnostic
predict calibration susceptibility in the new model?
```

`RQ3` is not the sole success criterion for EXP-025.

## Primary Estimands

For each condition `c`:

```text
S_diag(c) =
    BA_A0(block9_pre_final_rmsnorm, DIAG_c)
  - BA_A0(block15_pre_final_rmsnorm, DIAG_c)
```

```text
G_eval(c) =
    BA_A_mu_sigma(block15_pre_final_rmsnorm, EVAL_c)
  - BA_A0(block15_pre_final_rmsnorm, EVAL_c)
```

Definitions follow EXP-024 with the frozen OLMo checkpoint substitution.

Panel-level descriptive summaries:

- `mean(S_diag(c))`
- `median(S_diag(c))`
- `mean(G_eval(c))`
- `median(G_eval(c))`

These are descriptive and do not replace the primary classification rules.

## D / G Inference Rules

The scientific/inferential unit is `condition`, with `N = 10`.

`D` is fixed-readout degradation evidence.

`G` is held-out recalibration recovery evidence.

For `D`, use the condition-level values `S_diag(c)`.

For `G`, use the condition-level values `G_eval(c)`.

For each evidence direction:

1. Count positive, negative, and exactly zero condition values.
2. Use the nonzero values as the effective sample size.
3. Under the null `P(positive direction) = 0.5`, compute an exact one-sided
   binomial p-value:

```text
p_exact = P(Bin(effective_n, 0.5) >= observed_positive_count)
```

4. `D+` requires:

```text
observed_positive_count > observed_negative_count
AND exact_one_sided_p <= 0.05
```

5. `D-` is the complement `NOT D+`.

6. `G+` and `G-` use the same rule with `G_eval(c)`.

This rule uses the existing condition-level inferential unit, a fixed alpha of
`0.05`, and no post-hoc magnitude threshold. It is frozen before OLMo
DIAGNOSTIC/EVAL outcome access.

## Secondary RQ3 Analysis

`RQ3` is secondary and uses the EXP-024-compatible test:

```text
rho_secondary = Spearman(S_diag(c), G_eval(c))
```

Exact one-sided permutation test across all condition pairings:

```text
10! = 3,628,800
```

Secondary support rule:

```text
rho_secondary > 0 AND exact_one_sided_p <= 0.05
```

A positive or negative secondary result is interpreted alongside the EXP-024
primary result; it does not silently restore
`HYP_CALIBRATION_CONDITIONAL_002` to an active supported state.

## Frozen Replication Classification

Before formal execution, the following routing is fixed:

```text
IF D+ AND G+:
  Paper A breadth = STRENGTHENED
  operator/mechanism line = HIGH PRIORITY CANDIDATE

IF D+ AND G-:
  Paper A degradation breadth = STRENGTHENED
  generic calibration breadth = WEAKENED
  next mechanism question = MODEL-DEPENDENT OPERATOR SUFFICIENCY

IF D- AND G+:
  general fixed-readout degradation = NOT CROSS-MODEL REPLICATED
  operator-repair program = DEFER / REASSESS
  model/depth compatibility profile = HIGHER PRIORITY

IF D- AND G-:
  general fixed-readout degradation = NOT CROSS-MODEL REPLICATED
  operator-repair program = DEFER / REASSESS
  model/depth compatibility profile = HIGHER PRIORITY

IF technical/measurement invalid:
  NO SCIENTIFIC ROUTING
```

The `D-` routing branches do not distinguish `G+` from `G-` for scientific
routing because degradation absence is the gate.

## Measurement Qualification Gate

Task 100B must perform a lightweight OLMo measurement qualification before any
formal scientific run.

Allowed qualification checks:

- technical extraction validity
- determinism
- finite vectors
- correct shapes
- correct token position
- correct block identity
- `C_ref_OLMo` training path correctness
- class probability mapping correctness
- FIT-only reference readout usability

Frozen usability threshold:

```text
EXP025_MEASUREMENT_QUALIFICATION_MIN_REFERENCE_BALANCED_ACCURACY = 0.75
```

This threshold is a technical usability floor, not a scientific outcome. It
must be computed from OLMo FIT reference-form records only.

If qualification fails, scientific status is:

```text
NOT_INTERPRETABLE_AS_CROSS_MODEL_REPLICATION
```

Do not change layer, model, or threshold without a new explicit design
revision.

## Theory-Asset Firewall

The following assets are preserved, but EXP-025 does not test them:

- KAN/operator family
- minimum sufficient operator
- Kakeya / covering
- constrained compositional factorization
- invariant preservation
- coordinate transport
- functional binding
- representation scaling profile `Psi(N,l)`

EXP-025 results may change future priority only; they do not directly support
these assets.

## Hardware and Cost Policy

Target hardware: CUDA-capable RTX 5060 Laptop GPU with about 8GB VRAM.

Policy:

- prefer BF16/FP16 compatible loading
- use conservative batch sizes
- stream representations where necessary
- do not persist large raw hidden-state tensor artifacts
- keep only scientific aggregates and small reproducibility artifacts
- do not enlarge the experiment grid because the model is small

## Forbidden Additions

Do not add:

- more conditions
- more layers
- more calibration types
- more random seeds
- more models
- post-hoc best condition/layer/calibration selection
- favorable subset analysis

## Access Audit

- `EXP025_DESIGN_CREATED = true`
- `EXP025_FORMAL_RUN_PERFORMED = false`
- `EXP025_SCIENTIFIC_RESULT_CREATED = false`
- `EXP025_SEMANTIC_FORMAL_INFERENCE = false`
- `EXP025_DIAG_OUTCOME_VIEWED = false`
- `EXP025_EVAL_OUTCOME_VIEWED = false`
- `EXP025_MODEL_ACCESS_PERFORMED_THIS_TASK = false`

## Next Step

The next task is `100B_EXP025_ENGINEERING_QUALIFICATION`. It must perform the
lightweight measurement qualification using neutral/technical inputs only and
must not create a formal result or authorization.
