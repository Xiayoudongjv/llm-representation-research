# EXP-027 Preregistration

Status: `FROZEN_DESIGN_NOT_RUN`

Experiment: `EXP-027`

Task: `102B_EXP027_PREREGISTRATION_AND_FROZEN_DESIGN`

This document freezes the prospective scientific design for the EXP-027
third-model triangulation. It is not a formal authorization, runner
qualification, formal result, or scientific outcome. It must not be used to
perform model inference on real EXP-027 formal data.

## 1. Scientific Question

Does the independently selected third model
`Meta-Llama-3.2-1B-Instruct` exhibit:

- A. the registered Qwen-like profile,
- B. the registered OLMo-like profile, or
- C. a valid but different third registered profile?

The comparison is exact component matching of three frozen components:

```text
(distance_association_status, dominance_status, low_d_recovery_status)
```

This is triangulation, not architecture causality, model-family causality,
universality, significance rescue, transport, invariant validation, or
functional-binding evidence.

## 2. Authority and Provenance

Authority order:

1. frozen EXP-026 configs / preregistration / manifests
2. canonical EXP-026 result artifact
3. executable EXP-026 implementation that generated the accepted result
4. EXP-026 validators
5. EXP-027 model/provenance/carrier qualification artifacts
6. EXP-027 102A implementation and tests
7. canonical experiment documentation
8. research handoff
9. hypothesis backlog
10. task text

Primary recovered EXP-026 authority:

- Frozen config:
  `experiments/exp026/exp026_frozen_config.json`
  - SHA-256:
    `ccf60c8a9dc6f3b9d3cce533910334e1f8ec33665a1cf692b98a8aaf683afb57`
- Frozen preregistration:
  `experiments/exp026/EXP-026-PREREGISTRATION.md`
  - SHA-256:
    `730175071e315b484e360b6359945f567bfe8edf4f52e6a0893c3f2a7dadf8e1`
- Metric specification:
  `experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md`
  - SHA-256:
    `5f58445e26eee7effddd7cd5b4ae255b7153d61fa7a76b5c0684fa1dbb08d8db`
- Layer-carrier mapping:
  `experiments/exp026/EXP-026-LAYER-CARRIER-MAPPING.md`
  - SHA-256:
    `04c6565ff366fc04960966fcff148228c5338870756c75375baf976177d6dfb1`
- Routing rules:
  `experiments/exp026/EXP-026-ROUTING-RULES.md`
  - SHA-256:
    `4ff6be135066e1cd0bbcad54ee6c7472d693d35063df8202326b5bd0b4308856`
- Executable implementation:
  `experiments/exp026/run_exp026.py`
  - SHA-256:
    `6ab29c35889ce35b9d4bc9ee98d2665865a088312940f10815714a574d2060a0`

Canonical EXP-026 result:

- Path: `experiments/exp026/results/exp026_results.json`
- SHA-256:
  `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551`

EXP-027 102A authority:

- `experiments/exp027/engineering/EXP-027-LLAMA-MODEL-AUTHORITY.md`
- `experiments/exp027/engineering/llama32_native_converted_provenance.json`
- `experiments/exp027/engineering/llama32_model_authority_qualification.json`

Tag provenance below as:

- `INHERITED_EXP026`
- `QUALIFIED_EXP027_102A`
- `NEW_PROSPECTIVE_EXP027_RULE`
- `OPERATIONAL_INTEGRITY_RULE`

## 3. Frozen EXP-026 Reference Profiles

`INHERITED_EXP026`

- QWEN_REFERENCE_PROFILE:
  `(POSITIVE_SUPPORTED, TARGET_DOMINANT, NOT_SUPPORTED)`
- OLMO_REFERENCE_PROFILE:
  `(POSITIVE_SUPPORTED, SOURCE_DOMINANT, SUPPORTED)`

These are read-only motivation and comparison anchors. EXP-027 must not rerun,
recompute, or modify them.

## 4. Model Identity and Provenance

`QUALIFIED_EXP027_102A`

- Model: `Meta-Llama-3.2-1B-Instruct`
- Source: `META_OFFICIAL_NATIVE_DISTRIBUTION`
- Native checkpoint:
  `D:\AI_Cache\llama_home\.llama\checkpoints\Llama3.2-1B-Instruct`
- Converted checkpoint:
  `D:\AI_Cache\llama_hf\Llama3.2-1B-Instruct-meta-converted-v4463-attempt3`
- Converted `model.safetensors` SHA-256:
  `1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f`
- Native MD5 verification: `PASS`
- Native tensors: `147`
- Converted tensors: `146`
- Tied output/embedding: `true`
- Q/K official Meta-to-HF permutation: verified exactly, `max_abs_diff=0.0`
- Native-to-converted provenance: `PASS`

Runtime identity:

- `LlamaForCausalLM`
- `model_type=llama`
- Hidden size: `2048`
- Intermediate size: `8192`
- Logical decoder blocks: `16`
- Attention heads: `32`
- KV heads: `8`
- Vocab size: `128256`
- Max position embeddings: `131072`
- Rope theta: `500000.0`
- Execution dtype: `torch.bfloat16`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`

## 5. Input Rendering

`INHERITED_EXP026`

The formal model input is the dataset record `text` field, rendered as raw text.
No chat template is used.

- Text field: `text`
- Template: none / raw text
- `NEWLINE` and other whitespace: preserved as provided by the frozen dataset
  string; no normalization beyond the dataset string itself.
- Model input mapping: exactly `tokenizer(record["text"], ...)`.

This preserves cross-model semantic input identity while using the qualified
Llama tokenizer. Token identity is not treated as a scientific matching
criterion.

## 6. Tokenization

`INHERITED_EXP026` for semantic contract; `QUALIFIED_EXP027_102A` for tokenizer.

Tokenizer authority:

- Vocab: `128256`
- BOS: `128000`
- EOS: `128001`
- EOT: `128009`
- Chat template used: `false`

Frozen tokenizer invocation:

```text
tokenizer(text, return_tensors="pt", padding=False, truncation=False)
```

- `add_special_tokens`: default `true`
- `padding`: `false`
- `truncation`: `false`
- `max_length`: none
- attention mask: tokenizer-produced mask
- representation-token rule: attention-mask-derived last valid non-padding token

No post-hoc tokenizer special-token policy change is authorized.

## 7. Representation Carrier

`INHERITED_EXP026` plus `QUALIFIED_EXP027_102A`

Formal carrier API:

```text
FORWARD_HOOK_DECODER_BLOCK_OUTPUT
```

Logical layer `l` maps to `model.model.layers[l]`.

Carrier meaning:

```text
after decoder block
before next decoder block
and for block 15 before model-level final RMSNorm
```

- Blocks `0..14`: hook output corresponds to the post-block residual state.
- Block `15`: hook output is raw decoder block output, pre-final-model-RMSNorm.
- `model(...).hidden_states[-1]` is post-final-model-normalization and is not
  a formal carrier.
- `output_hidden_states=True` may be used for oracle verification only.
- Extraction path: hook output -> last valid token -> detach -> CPU -> float32
  -> NumPy.
- Hooks are observational only and removed after capture.
- All 16 decoder blocks use the same formal carrier API; no final-block special
  scientific representation.

## 8. Dataset and Split Identity

`INHERITED_EXP026` / `INHERITED_EXP024`

Reuse exactly the frozen EXP-024/EXP-025/EXP-026 dataset and panel. Do not
create a new split, filter items, rebalance, or replace examples.

- Dataset:
  `experiments/exp024/data/exp024_condition_panel_frozen.json`
  - SHA-256:
    `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Condition panel:
  `experiments/exp024/condition_panel_spec.json`
  - SHA-256:
    `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`
- Data schema:
  `experiments/exp024/data_schema.json`
  - SHA-256:
    `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec`
- Frozen manifest:
  `experiments/exp024/exp024_frozen_manifest.json`
  - SHA-256:
    `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`
- EXP-024 preregistration:
  `docs/experiments/EXP-024-PREREGISTRATION.md`
  - SHA-256:
    `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`

Partitions: `FIT`, `DIAGNOSTIC`, `EVAL`

Record role used for formal inference: `condition_realization`

Per condition and semantic class:

- FIT: `6` source families
- DIAGNOSTIC: `8` source families
- EVAL: `8` source families

Semantic classes: `logic`, `causality`, `analogy`, `definition`.

Condition order:

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

## 9. Source-Target Matrix

`INHERITED_EXP026`

EXP-027 has 16 qualified logical decoder blocks, indices `0..15`. The frozen
domain is the full ordered source-target matrix over those blocks.

- Source domain: all `0..15`
- Target domain: all `0..15`
- Matrix orientation: rows = source layers, columns = target layers
- Ordered-pair semantics:
  source-layer classifier evaluated on target-layer representation
- Diagonal included in raw matrices; diagonal `D=0` by construction and
  excluded from off-diagonal structural summaries
- Layer-subset shopping: forbidden
- Depth normalization:
  `d(l) = l / (num_layers - 1) = l / 15`

## 10. Fixed-Readout Compatibility Estimand

`INHERITED_EXP026`

- Fit one frozen classifier `h_m,i` per source layer `i` on FIT
  condition-realization representations only.
- Evaluate `h_m,i` on target-layer EVAL representations without refitting.
- `C0_m(i,j,c)` is four-class macro-averaged recall.
- `Cself_m(i,c) = C0_m(i,i,c)`
- `D_m(i,j,c) = Cself_m(i,c) - C0_m(i,j,c)`
- Recalibrated target uses frozen `A_mu_sigma` FIT-only featurewise
  mean/scale adaptation.
- `Ccal_m(i,j,c)` is the calibrated balanced accuracy.
- `R_m(i,j,c) = Ccal_m(i,j,c) - C0_m(i,j,c)`
- Condition pooling is equal-weight arithmetic mean over all 10 conditions:
  `Dbar(i,j) = mean_c D(i,j,c)`, `Rbar(i,j) = mean_c R(i,j,c)`.

Boundary statements:

```text
readout degradation != information disappearance
alignment recovery != transport proof
compatibility != functional binding
```

## 11. Depth-Distance Association

`INHERITED_EXP026`

Over confirmatory-eligible source rows and all off-diagonal target pairs:

```text
x(i,j) = abs(d(i) - d(j))
y(i,j) = Dbar(i,j)
rho = Spearman(x, y)
```

- Tie handling: average ranks.
- Implementation identity: custom average-rank Spearman in
  `run_exp026.py`; not a latent-geometric distance.
- Support rule:

```text
POSITIVE_SUPPORTED if one-sided 95% cluster-bootstrap lower bound > 0
NOT_SUPPORTED otherwise
```

No two-sided p-value is used for this primary endpoint.

## 12. SDI

`INHERITED_EXP026`

For off-diagonal `Dbar` restricted to eligible source rows:

```text
row_mean_i = mean_{j != i} Dbar(i,j)
column_mean_j = mean_{eligible i != j} Dbar(i,j)
SOURCE_VARIANCE = population_variance(row_mean_i)
TARGET_VARIANCE = population_variance(column_mean_j)
SDI = (SOURCE_VARIANCE - TARGET_VARIANCE)
      / (SOURCE_VARIANCE + TARGET_VARIANCE)
```

- Variance convention: `numpy.var(..., ddof=0)`.
- Zero denominator: `SDI=0`, status `NO_ROW_OR_COLUMN_VARIATION`.
- Support classes:

```text
SOURCE_DOMINANT if SDI > 0 and one-sided 95% lower bound > 0
TARGET_DOMINANT if SDI < 0 and one-sided 95% upper bound < 0
NO_DOMINANCE otherwise
NO_ROW_OR_COLUMN_VARIATION if denominator exactly zero
```

## 13. LOW-D Recovery

`INHERITED_EXP026`

- Use DIAGNOSTIC only to create the prospective pair mask.
- `LOW_OR_NONDEGRADATION_PAIR iff Dbar_diag(i,j) <= 0`
- Evaluate only on EVAL over the frozen DIAGNOSTIC-selected pair set:

```text
LOW_D_RECOVERY = mean Rbar_eval(i,j)
```

- Also report `eligible_pair_count` and `positive_recovery_pair_fraction`.
- If eligible pair count is zero: `NOT_EVALUABLE`.
- Support rule:

```text
SUPPORTED if point estimate > 0 and one-sided 95% cluster-bootstrap lower bound > 0
NOT_SUPPORTED otherwise
NOT_EVALUABLE if eligible_pair_count == 0
```

Do not relax the `<= 0` mask criterion.

## 14. Bootstrap and Statistical Rules

`INHERITED_EXP026`

- Statistical unit: `source_family_cluster`
- Resampling unit: `source_family`
- Strata: `condition`
- Design: condition-stratified source-family cluster bootstrap
- Keep FIT-fitted classifiers and FIT-only calibration statistics fixed
- Resample EVAL source families with replacement within each condition
- Preserve all records/layers for a sampled source family
- Recompute the full matrix on resampled EVAL records
- Replicates: `5000`
- Bit generator: `numpy.random.PCG64`
- Seed: `20260819`
- CI level: `95%`
- CI method: percentile
- Quantile method: `numpy.percentile(..., method="linear")`
- One-sided positive lower bound: 5th percentile
- One-sided negative upper bound: 95th percentile
- Invalid replicate handling: skip replicates that do not preserve all four
  semantic classes
- LOW-D mask: computed once on DIAGNOSTIC and fixed across replicates

The optimized 102A bootstrap prototype may be used as an engineering
implementation only because 102A tests demonstrated draw/statistic/
classification/routing equivalence and preserved the reference implementation.
Performance optimization must not alter the estimator.

## 15. Technical / Measurement Validity

`INHERITED_EXP026` plus `OPERATIONAL_INTEGRITY_RULE`

Technical validity includes:

- source-layer DIAGNOSTIC technical-usability floor `0.75`
- source coverage: eligible source count `>= 8` and normalized-depth span
  `>= 0.5`
- all 16 carriers captured exactly once
- last-valid-token selection must be attention-mask derived
- analysis representations finite and `float32`
- no nonfinite, shape-invalid, or hook-missing carrier state

Measurement invalidity:

```text
TECHNICALLY_INVALID or source-coverage not evaluable
=> RESULT_STATUS = UNOBSERVED_OR_INVALID
=> SCIENTIFIC_PROFILE_ROUTE = NOT_ASSIGNED
```

Keep `ATTEMPT_STATUS`, `RESULT_STATUS`, and `SCIENTIFIC_STATUS` distinct.

## 16. Registered Third-Model Profile Routing

`NEW_PROSPECTIVE_EXP027_RULE`

After a valid EXP-027 result, derive:

```text
LLAMA_REGISTERED_PROFILE =
(distance_association_status, dominance_status, low_d_recovery_status)
```

Use exact match only. No continuous similarity, weighted score, nearest
neighbor, or subjective resemblance.

Routing:

```text
IF technical/measurement validity fails:
    RESULT_STATUS = UNOBSERVED_OR_INVALID
    SCIENTIFIC_PROFILE_ROUTE = NOT_ASSIGNED

ELSE IF LLAMA_REGISTERED_PROFILE == QWEN_REFERENCE_PROFILE:
    SCIENTIFIC_PROFILE_ROUTE = EXP026_PROFILE_MATCH_QWEN

ELSE IF LLAMA_REGISTERED_PROFILE == OLMO_REFERENCE_PROFILE:
    SCIENTIFIC_PROFILE_ROUTE = EXP026_PROFILE_MATCH_OLMO

ELSE:
    SCIENTIFIC_PROFILE_ROUTE = THIRD_REGISTERED_PROFILE
```

`THIRD_REGISTERED_PROFILE` means only that the valid registered three-component
profile did not exactly equal either frozen reference. It does not automatically
mean a new mechanism, architecture class, geometry, or causal regime.

## 17. Outcome-Blind Execution

`OPERATIONAL_INTEGRITY_RULE`

Before atomic canonical result publication, later formal execution may expose
only:

```text
timestamp
stage
completed
total
percent
elapsed
heartbeat
publication_status
```

It must not expose rho, SDI, LOW-D values, confidence intervals, p-values,
support states, profile route, condition-level values, matrix cells, or
best/worst layers.

No hidden preview file, console preview, intermediate human-inspectable
scientific CSV, or automatic retry is allowed.

## 18. Stop Rules

`OPERATIONAL_INTEGRITY_RULE`

Stop without formal execution if:

- frozen authority hashes or model provenance conflict
- carrier qualification conflicts
- any primary semantic remains unresolved
- a formal authorization or result already exists unexpectedly
- real FIT/DIAG/EVAL model inference would be required before formal
  authorization

No reasonable-default resolution of a primary scientific ambiguity is allowed.

## 19. Negative-Result Interpretation

`NEW_PROSPECTIVE_EXP027_RULE`

- Qwen exact match: a third model exhibits the Qwen registered profile;
  no universality or architecture causality.
- OLMo exact match: a third model exhibits the OLMo registered profile;
  no universality or architecture causality.
- Third registered profile: the two prior profiles do not exhaust the valid
  registered outcome space; no new mechanism claim without further experiments.
- Depth-distance association not supported: weakens the emerging breadth claim;
  do not rescue by changing layers or distance.
- Technical/measurement invalidity: no structural conclusion; measurement
  failure does not imply absence of the phenomenon.

## 20. Claims Explicitly Not Tested

`OPERATIONAL_INTEGRITY_RULE`

EXP-027 does not test:

- architecture causality
- model-family causality
- universality
- coordinate transport
- invariant preservation
- functional binding
- behavioral control
- Residual-Flow confirmation
- KAN operator validity
- information disappearance

## 21. Formal-Run Boundary

`OPERATIONAL_INTEGRITY_RULE`

- `EXP027_102B_PREREGISTRATION_FROZEN = true`
- `EXP027_FORMAL_AUTHORIZED = false`
- `EXP027_FORMAL_RUN_PERFORMED = false`
- `EXP027_SCIENTIFIC_RESULT_CREATED = false`
- No formal authorization is created here.
- Next task after successful 102B:
  `102C_EXP027_ENGINEERING_AND_ADVERSARIAL_REVIEW`

Later formal execution requires a separate successful 102C adversarial review,
formal-pipeline qualification, single-use authorization, and exactly one human
launch.

## 22. Future-Theory Firewall

`OPERATIONAL_INTEGRITY_RULE`

Readable future-theory assets include Minimum Sufficient Alignment Operator,
Residual-Flow Hypothesis, structural invariants, functional binding, KAN /
constrained operator families, and Kakeya / coverage inspiration.

They are only:

```text
PROSPECTIVE_THEORETICAL_ASSET
HYPOTHESIS
DISTANT_MATHEMATICAL_INSPIRATION
```

They must not enter EXP-027 as primary metrics, layer-selection rules, SDI,
LOW-D definitions, distance statistics, bootstrap rules, or profile routing.
EXP-027 may motivate later Residual-Flow work; it cannot confirm it.
