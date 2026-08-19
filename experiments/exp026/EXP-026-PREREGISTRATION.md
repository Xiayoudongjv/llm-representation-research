# EXP-026 Preregistration

Status: `FROZEN_DESIGN_NOT_RUN`

This is the frozen prospective scientific design for EXP-026. It is closed to
outcome-dependent change before any EXP-026 model forward pass on formal
scientific data, any DIAGNOSTIC/EVAL outcome access, any formal-run
authorization, or any scientific result creation.

## Experiment Identity

- Experiment: `EXP-026`
- Working name: `Model-Depth Fixed-Readout Compatibility Matrix`
- Design selected in Task 101A: `FULL_SOURCE_TARGET_COMPATIBILITY_MATRIX`
- Model scope: `TWO_MODEL_COMPARATIVE_PROFILE`
- Protocol stage: `FROZEN_DESIGN_NOT_RUN`
- Runner created: `false`
- GPU run executed: `false`
- Formal authorization created: `false`
- Scientific result created: `false`

## Scientific Motivation

EXP-024 produced a Qwen direction of `D+ / G+`. EXP-025 produced an OLMo
direction of `D- / G+`. The next experiment must explain why a single-reference
fixed-readout degradation result differs across these two models without
assuming depth causes degradation and without assuming the difference is
architecture-caused.

Primary question:

> How does fixed-readout compatibility vary jointly with source layer and target
> layer, and how much of the apparent depth effect is depth-distance structured,
> locally transition-structured, source-reference dependent, model dependent, or
> partly independent from recalibratability?

## Claim Language

The registered claim family is:

```text
MODEL-DEPENDENT COMPATIBILITY ORGANIZATION
```

not `ARCHITECTURE-DEPENDENT COMPATIBILITY ORGANIZATION`.

EXP-026 may establish differences between the two frozen models. It cannot
attribute those differences specifically to architecture, training recipe,
tokenizer, model family, or scale without additional controls.

## Frozen Model Set

Exactly two primary models are frozen:

- `Q`: `Qwen/Qwen3-1.7B`, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- `O`: `allenai/OLMo-2-0425-1B-Instruct`, revision `48d788eca847d4d7548f375ad03d3c9312f6139e`

No floating revisions. Llama, Qwen3-4B, Gemma, and any fallback model are not
part of EXP-026. Llama is explicitly deferred as a possible independent
third-model validation experiment only if EXP-026 routing makes that
scientifically useful.

## Dataset and Condition Panel

Reuse exactly the frozen EXP-024/EXP-025 dataset and ten-condition panel:

- Dataset: `experiments/exp024/data/exp024_condition_panel_frozen.json`
- Dataset SHA-256:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Condition panel: `experiments/exp024/condition_panel_spec.json`
- Panel SHA-256:
  `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`
- Data schema: `experiments/exp024/data_schema.json`
- Data-schema SHA-256:
  `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec`
- Frozen manifest: `experiments/exp024/exp024_frozen_manifest.json`
- Manifest SHA-256:
  `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`
- EXP-024 preregistration: `docs/experiments/EXP-024-PREREGISTRATION.md`
- EXP-024 preregistration SHA-256:
  `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`

Frozen condition order:

```text
c01_lexical_relex
c02_syntactic_restructure
c03_controlled_compression
c04_controlled_elaboration
c05_relation_explicit
c06_relation_implicit
c07_register_formal
c08_register_informal
c09_neutral_distractor_prefix
c10_anaphoric_reference
```

Semantic classes: `logic`, `causality`, `analogy`, `definition`.

Partition allocation per condition and semantic class:

- FIT: `6` source families
- DIAGNOSTIC: `8` source families
- EVAL: `8` source families

Do not regenerate or reshuffle the dataset. The experiment tests cross-model /
cross-depth compatibility structure within the existing panel, not cross-dataset
generality.

## FIT / DIAGNOSTIC / EVAL Firewall

FIT may determine only:

- source-layer classifier parameters `h_m,i`;
- pairwise FIT-only recalibration parameters.

DIAGNOSTIC may determine only:

- source-layer technical eligibility;
- pre-registered diagnostic quantities;
- any explicitly frozen diagnostic mask.

EVAL determines all confirmatory compatibility/recovery summaries.

EVAL may not select source layers, target layers, matrix regions, transition
locations, calibration variants, statistics, or thresholds.

## Logical Layer Carriers

The layer carrier is the output residual state of each Transformer decoder
block, after that block, before the next decoder block, and before any
model-level final normalization. This carrier is architecture-aware and is
defined separately in
`experiments/exp026/EXP-026-LAYER-CARRIER-MAPPING.md`.

Eligible depth set: all Transformer decoder blocks, excluding embedding state,
LM-head logits, post-LM-head state, and inconsistent final-normalized-only
carriers. No layer outcome may be inspected during mapping.

## Normalized Depth

Within a model with `L` eligible blocks and block index `l in {0,...,L-1}`:

```text
d(l) = l / (L - 1)
```

Normalized depth is used only for within-/cross-model profile summaries. Equal
normalized depths across models are not claimed to be functionally equivalent.

## Source-Layer Classifier

For each model `m` and source layer `i`, fit one frozen semantic classifier
`h_m,i` using only FIT condition-realization representations from source layer
`i`.

Classifier contract:

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

No hyperparameter tuning. No per-layer classifier selection. Outputs are mapped
through `classifier.classes_`.

## Source-Layer Technical Usability

For every source layer `i`:

1. Train `h_m,i` on FIT.
2. Evaluate same-layer DIAGNOSTIC readout on DIAGNOSTIC only.

`BA_diag_self(m,i)` is the arithmetic mean over the ten conditions of the
condition-level four-class balanced accuracy of `h_m,i` on same-layer DIAGNOSTIC
condition-realization records.

If `BA_diag_self(m,i) >= 0.75`, source row `i` is
`CONFIRMATORY_ELIGIBLE`. Otherwise source row `i` is
`DESCRIPTIVE_ONLY_TECHNICALLY_UNQUALIFIED`.

The threshold is not lowered after seeing the profile. The row is never deleted
from the descriptive matrix. EVAL never determines source eligibility.

## Source-Coverage Gate

Source-dependent confirmatory endpoints are evaluable only when, for each model
separately:

- eligible source count >= `ceil(L / 2)`;
- normalized-depth span of eligible sources >= `0.5`.

For Qwen this requires at least `14` eligible sources. For OLMo this requires at
least `8` eligible sources.

If coverage fails, source-dependent confirmatory endpoints are `NOT_EVALUABLE`;
the full descriptive matrix may still be retained.

## Matrix Definitions

For model `m`, source `i`, target `j`, condition `c`:

- `C0_m(i,j,c)` = EVAL balanced accuracy of source classifier `h_m,i` applied
  directly to target-layer-`j` EVAL representations under condition `c`; no
  recalibration.
- `Cself_m(i,c) = C0_m(i,i,c)`.
- `D_m(i,j,c) = Cself_m(i,c) - C0_m(i,j,c)`.

`D > 0` means fixed-readout compatibility loss relative to the source readout's
same-layer EVAL performance. `D < 0` means target-layer compatibility exceeds
the corresponding same-layer baseline.

`D` is not called information loss, representation loss, or semantic
destruction.

By construction, `D_m(i,i,c) = 0`. Diagonal cells are retained as sanity checks
and excluded from off-diagonal structural summaries unless a metric explicitly
states otherwise.

## Recalibrated Matrix

Primary recalibration variant: `A_mu_sigma`.

For pair `(i,j)` and condition `c`, FIT-only featurewise calibration quantities
are estimated and applied exactly as in
`experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md`:

- `Ccal_m(i,j,c)` = EVAL balanced accuracy after the frozen pairwise
  `A_mu_sigma` calibration;
- `R_m(i,j,c) = Ccal_m(i,j,c) - C0_m(i,j,c)`.

Positive `R` means held-out improvement from the frozen FIT-only featurewise
recalibration. `R` does not infer transport, equivalence, invariant
preservation, or causal repair.

`A_mu` and `A_sigma` may be retained as secondary/descriptive outputs but never
compete with `A_mu_sigma` for primary recovery or routing.

## Condition-Pooled Matrices

```text
Dbar_m(i,j) = arithmetic mean over the fixed 10 conditions of D_m(i,j,c)
Rbar_m(i,j) = arithmetic mean over the fixed 10 conditions of R_m(i,j,c)
```

All ten conditions receive equal weight. No condition dropping.

## Confirmatory Hierarchy

- PRIMARY-1: `DISTANCE_ASSOCIATION` per model.
- PRIMARY-2: `SOURCE_DOMINANCE_INDEX` (`SDI`) per model.
- SECONDARY-CONFIRMATORY: `LOW_D_RECOVERY`.
- SECONDARY/DESCRIPTIVE: `LOCALIZATION`, cross-model normalized matrix
  similarity, and full `C0/D/R` matrices.

Exact definitions and support rules are frozen in
`experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md`.

## Statistical Unit and Uncertainty

The statistical unit is the source family cluster, not a matrix cell or row.

Uncertainty uses condition-stratified source-family cluster bootstrap
resampling of EVAL source families, preserving condition structure, all layer
outputs for a sampled source family, and source-target matrix dependence.

Full bootstrap semantics are frozen in
`experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md`.

No row-wise or cell-wise bootstrap is used.

## Routing

Routing rules are prospectively frozen in
`experiments/exp026/EXP-026-ROUTING-RULES.md`:

- `P1`: localized transition plus concentrated recovery -> operator capacity.
- `P2`: source-reference dominance -> reference/source-anchor resolution.
- `P3`: materially different model structural signatures -> third-model
  independent validation.
- `P4`: broad `LOW_D_RECOVERY` support -> minimum sufficient alignment operator.
- `P5`: flat/stable matrices and weak recovery -> reconsider panel/reference
  specificity.

Conflict resolution is frozen before execution.

## Llama Position

Llama is not part of EXP-026. If `P3` triggers later, the candidate third model
may be `Llama-3.2-1B-Instruct`, but EXP-026 does not freeze or run Llama. Do not
use the previous 8B Llama as an automatic next model; audit a roughly 1B
Llama-family model first to reduce scale confounding.

## Claim Ceiling

Even under the strongest successful result, EXP-026 may claim at most:

> The two tested models exhibit reproducible differences in depth-structured
> source/target fixed-readout compatibility under the frozen condition panel,
> and FIT-only featurewise recalibratability is not fully reducible to raw
> fixed-readout compatibility loss.

Do not claim universal latent geometry, architecture causality, family
causality, transport, invariant preservation, functional binding, or behavioral
causality.

## Resource Plan

- Exploit one-forward all-layer extraction.
- One model loaded at a time.
- One partition/stream at a time.
- Last-valid-token vectors only.
- CPU float32 analysis representations.
- Local ignored cache or streaming accumulator.
- Summary-only canonical Git artifacts.
- No sequence-level hidden tensors, model weights in repo, or raw hidden-state
  tensors in Git.

## Extraction Cache

If a local representation cache is used, freeze cache schema, model identity,
revision, layer-carrier map hash, dataset partition hash, record identity, and
dtype. Cache is an engineering/reproducibility artifact, not scientific
authority. Stale or mismatched cache fails closed.

## Formal Result Content

Future canonical result should contain at least model identities, layer-carrier
mapping identities, eligible-source masks, technical-usability BA per source
layer, `C0`, `D`, primary `A_mu_sigma` `Ccal`, `R`, condition-pooled matrices,
primary structural summaries, secondary summaries, routing classification, and
complete authority/provenance identities. Large matrices may be serialized in a
deterministic compact format. No raw hidden tensors.

## Technical Qualification Before Formal Run

Future implementation must separately prove all-layer carrier extraction,
logical block mapping, last-valid-token correctness, Qwen and OLMo
model-specific hooks/mapping, classifier loop, pairwise recalibration, matrix
indexing, diagonal identity, partition firewall, cluster-resampling semantics,
routing implementation, and atomic publication. Synthetic end-to-end
qualification must exercise the real matrix executor.

## No Runner

Task 101B freezes design only:

- `EXP026_RUNNER_CREATED = false`
- `EXP026_GPU_RUN_EXECUTED = false`
- `EXP026_FORMAL_AUTHORIZATION_CREATED = false`
- `EXP026_SCIENTIFIC_RESULT_CREATED = false`

## Next Step

If and only if `EXP026_SPECIFICATION_GAPS = 0` and design validation is `PASS`:

```text
101C_EXP026_RUNNER_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION
```

Otherwise:

```text
STOP_AND_RESOLVE_DESIGN_GAPS
```
