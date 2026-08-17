# EXP-023 Preregistration Draft

Version: v0.1

Status: DRAFT_PROTOCOL_AWAITING_INDEPENDENT_DATASET_FREEZE

Implementation authorized: false

Model execution authorized: false

Formal EVAL access authorized: false

Scientific result status: NOT_RUN

This document records the prospective EXP-023 scientific protocol. It is not
frozen. No EXP-023 scientific records, model outputs, runner code, dataset, or
authorization are created by this draft.

## Experiment class and position

Experiment title: `EXP-023 — Independent Featurewise Calibration Replication and Mean/Scale Decomposition`

Classification:

`PROSPECTIVE_CONFIRMATORY_REPLICATION_WITH_SECONDARY_MECHANISM_DECOMPOSITION`

Primary purpose:

`INDEPENDENT_FEATUREWISE_CALIBRATION_REPLICATION`

Secondary purpose:

`DESCRIPTIVE_MEAN_SCALE_DECOMPOSITION`

EXP-023 independently tests whether the FIT-only layer-dependent combined
featurewise recalibration signal observed in EXP-022A replicates on entirely new
controlled material. It also describes whether that signal is more consistent
with mean adaptation, scale adaptation, or their combination.

EXP-023 is not:

- general coordinate transport;
- attention geometry;
- attention intervention;
- RMSNorm causality;
- behavior;
- functional binding;
- multi-model scaling;
- operator-network architecture.

## Historical motivation

EXP-022A is recorded only as discovery motivation. Its data are not EXP-023
replication data.

EXP-022A block27 pre-final observed values:

- Split A: `A0 = 0.6667`, `A1 = 0.7500`
- Split B: `A0 = 0.2500`, `A1 = 0.7500`

`A1` was a secondary/descriptive signal. Same-family refit rescue was not
supported.

## Primary research question

Does FIT-only layer-dependent combined featurewise recalibration improve
held-out balanced accuracy of an unchanged reference classifier at the
preregistered deep checkpoint on completely new controlled data?

Primary estimand:

```text
G_cal = BA(A_mu_sigma, block27_pre_final_rmsnorm)
        - BA(A0, block27_pre_final_rmsnorm)
```

Primary directional hypothesis:

```text
G_cal > 0
```

## D_fixed contextual role

Define:

```text
D_fixed = BA(A0, block27_pre_final_rmsnorm) - BA(A0, reference)
```

`D_fixed` is a contextual endpoint. It does NOT serially gate the primary
`G_cal` test.

Interpretation rule:

- If `D_fixed` degradation is supported AND `G_cal` is supported, the permitted
  wording is `calibration rescue/stabilization of fixed-frame degradation`.
- If `G_cal` is supported but `D_fixed` degradation is not supported, use only
  `featurewise calibration improved/stabilized fixed-readout held-out performance`.

## Model binding

Primary model:

```text
Qwen/Qwen3-1.7B
snapshot = 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e
```

The same primary model is used as in EXP-022A to isolate data independence and
calibration mechanism. EXP-023 does not add a second model.

## Dataset design

The primary EXP-023 dataset must be entirely new.

Do NOT reuse:

- `experiments/exp003/prompts_controlled.json`;
- any EXP-021 scientific record;
- any EXP-022A scientific record;
- simple paraphrases of old source items.

Prospective design:

- four `SOURCE_SEMANTIC_CLASS` values: `logic`, `causality`, `analogy`, `definition`;
- eight new source families per class;
- one `original_style` and one `paraphrase` per family;
- 32 source families;
- 64 records total;
- 32 records per variant;
- eight records per class per variant.

## Explicit family authority

Each new record must contain explicit:

- `record_id`
- `source_family_id`
- `SOURCE_SEMANTIC_CLASS`
- `variant_type`
- `text` / required content field

Each `source_family_id` binds exactly one `original_style` and one `paraphrase`
of the same semantic class. Family identity must not be inferred from a numeric
suffix.

## Raw variant contract

Raw values:

- `original_style`
- `paraphrase`

Canonical analysis roles:

- `original_style -> original`
- `paraphrase -> paraphrase`

Use a single authoritative mapping.

## Splits

Split A:

- FIT = 32 `original_style`
- EVAL = 32 `paraphrase`

Split B:

- FIT = 32 `paraphrase`
- EVAL = 32 `original_style`

Each split contains eight records per class. Analyze Split A and Split B
independently. Never pool A+B for primary significance.

## Representation object

Use:

```text
h_l^clean(x)
```

Meaning: clean, non-intervened, last-valid-token hidden representation at layer
`l`.

No steering, no beta, no generation manipulation. Maintain qualified EXP-022A
tokenizer/hook semantics unless a separate prospective engineering compatibility
review establishes necessity.

## Checkpoints

Reference:

```text
block16_pre_final_rmsnorm = hidden_states[17]
```

Primary:

```text
block27_pre_final_rmsnorm
```

using the qualified block27 pre-final hook.

Descriptive trajectory:

```text
block16 through block27 pre-final
```

Secondary descriptive:

```text
block27_post_final_rmsnorm
```

No post-outcome layer promotion is permitted.

## Reference scaler and classifier

Within each split independently:

1. At the reference layer FIT representations, estimate `mu_ref` and `sigma_ref`.
2. Fit `StandardScaler` and a frozen reference `LogisticRegression`, `C_ref`.

`C_ref` remains unchanged for all four conditions:

- `A0`
- `A_mu`
- `A_sigma`
- `A_mu_sigma`

## Classifier contract

Use the frozen EXP-022A classifier family unless a prospective compatibility
amendment is approved before protocol freeze:

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

## Condition definitions

### A0

Fixed reference calibration:

```text
z_A0 = (h_l - mu_ref) / sigma_ref
C_ref(z_A0)
```

### A_mu

Mean-only layer adaptation:

```text
z_A_mu = (h_l - mu_l) / sigma_ref
C_ref(z_A_mu)
```

`mu_l` is estimated from layer FIT representations only. `sigma_ref` is
retained. No EVAL statistics are used.

### A_sigma

Scale-only layer adaptation:

```text
z_A_sigma = (h_l - mu_ref) / sigma_l
C_ref(z_A_sigma)
```

`sigma_l` is estimated from layer FIT representations only. `mu_ref` is
retained. No EVAL statistics are used. Use deterministic sklearn-compatible
zero-variance handling.

### A_mu_sigma

Combined layer adaptation:

```text
z_A_mu_sigma = (h_l - mu_l) / sigma_l
C_ref(z_A_mu_sigma)
```

This reproduces the operational form of EXP-022A `A1`. Prospectively it can be
represented as:

```text
T_l_to_ref(h) = mu_ref + sigma_ref * ((h - mu_l) / sigma_l)
S_ref(T_l_to_ref(h)) = S_l(h)
```

This does NOT retroactively change EXP-022A historical transport claim status.

## Primary metric and estimand

Primary metric: balanced accuracy.

Primary checkpoint: `block27_pre_final_rmsnorm`.

Balanced EVAL means BA equals accuracy numerically for the balanced design, but
BA must still be calculated and reported.

For each split independently:

```text
G_cal = BA(A_mu_sigma) - BA(A0)
```

Positive `G_cal` indicates improved held-out performance under combined
featurewise recalibration.

## Primary exact test

Paired correctness comparison:

```text
A_mu_sigma vs A0
```

For each EVAL record:

```text
favorable f = A_mu_sigma correct AND A0 incorrect
unfavorable u = A_mu_sigma incorrect AND A0 correct
m = f + u
```

Test:

```text
p = P[Binomial(m, 0.5) >= f]
one-sided
mid-p = false
if m = 0, p = 1
alpha = 0.05
```

Split-level support requires:

```text
G_cal > 0 AND p <= 0.05
```

## Cross-split classification

- `FULL_REPLICATION`: both splits satisfy primary support.
- `PARTIAL_REPLICATION`: exactly one split satisfies primary support AND the
  other has `G_cal > 0`.
- `SPLIT_HETEROGENEOUS`: `G_cal` signs differ.
- `NO_REPLICATION`: none of the above.

Do not manufacture a pooled significance result.

## D_fixed context test

Compare `A0` reference vs `A0` final-pre correctness.

Degradation-favorable discordance:

```text
reference correct AND final A0 incorrect
```

Opposite discordance:

```text
reference incorrect AND final A0 correct
```

Use the same one-sided exact conditional Binomial test with `alpha = 0.05`.
Report separately from `G_cal`.

## Secondary mechanism effects

At `block27_pre_final_rmsnorm`, report:

```text
G_mu = BA(A_mu) - BA(A0)
G_sigma = BA(A_sigma) - BA(A0)
G_joint_over_mu = BA(A_mu_sigma) - BA(A_mu)
G_joint_over_sigma = BA(A_mu_sigma) - BA(A_sigma)
```

These are secondary mechanism estimands.

## Secondary mechanism inference policy

Use `DESCRIPTIVE SECONDARY` inference for `A_mu` and `A_sigma` rather than
adding additional formal significance families.

Report:

- balanced accuracy;
- paired discordance counts;
- effect differences;
- bootstrap confidence intervals.

Do NOT designate `mean-only supported` or `scale-only supported` using arbitrary
post-hoc percentage thresholds. Mechanism language remains graded. Examples:

- mean-only effect larger descriptively;
- scale-only effect larger descriptively;
- both individually limited but combined stronger;
- combined effect not reproduced.

## Bootstrap

Secondary robustness only.

- 10,000 replicates.
- RNG: `PCG64(20260818)`.
- Within each split independently.
- Class-stratified EVAL resampling.
- Eight records per class with replacement.
- Carry together for each sampled record: `A0`, `A_mu`, `A_sigma`,
  `A_mu_sigma`, and reference correctness when required.
- CI: 2.5% to 97.5%.
- NumPy quantile method: `linear`.
- No A/B pooling.

## Full-depth trajectory

Compute descriptively for every preregistered clean checkpoint:

- `A0`
- `A_mu`
- `A_sigma`
- `A_mu_sigma`

No inferential promotion of another layer is permitted.

## Final RMSNorm secondary status

Report descriptively:

```text
BA_post - BA_pre
```

for all four conditions.

Status: `SECONDARY_MECHANISTIC_CLUE_ONLY`.

Do not test RMSNorm causality. Do not modify or intervene on RMSNorm.

## Attention boundary

EXP-023 performs calibration only for downstream fixed-readout analysis. The
calibrated state is NOT fed back through the remaining Transformer computation.

Therefore EXP-023 does NOT test:

- attention routing changes;
- Q/K geometry changes;
- KV-cache alignment;
- attention–geometry coupling;
- generation effects.

Any future attention hypothesis remains a separate experiment.

## Transport boundary

EXP-023 prospectively tests only the constrained diagonal featurewise family
represented by `A_mu_sigma`.

It does NOT test:

- orthogonal transport;
- general affine transport;
- low-rank transport;
- nonlinear transport.

Broader `HYP-TRANSPORT-001` remains deferred.

## Dataset blindness

The dataset must be constructed and frozen before any EXP-023 model execution.

Dataset creators may know the historical EXP-022A phenomenon. They may NOT use
EXP-023 model output, classifier probabilities, calibration effects, or
endpoint results to edit/select records. Do not claim researcher-content
blindness.

## Data quality gate

Before model execution verify:

- 64 records;
- 32 unique families;
- eight families per class;
- one `original_style` and one `paraphrase` per family;
- same class within family;
- unique record IDs;
- unique family IDs;
- nonempty text;
- no EXP-022A item reuse;
- no direct old-item paraphrase reuse;
- balanced class/variant structure.

## Data freeze requirement

The final frozen protocol must bind:

- dataset path;
- dataset SHA-256;
- dataset manifest identity.

Task-095C does not create the dataset. Therefore status after this task is:

```text
DRAFT_PROTOCOL_AWAITING_INDEPENDENT_DATASET_FREEZE
```

## Technical validity

Preserve prior failure semantics:

- `ConvergenceWarning` + finite result = `VALID_WITH_WARNING`;
- fit exception = `TECHNICALLY_INVALID`;
- nonfinite values = `TECHNICALLY_INVALID`.

No automatic retry. No hyperparameter rescue. No layer or model substitution.

## Falsification

Independent primary failure matters. If `A_mu_sigma` does not satisfy the
preregistered replication criterion:

- do not tune;
- do not substitute layers;
- do not change model;
- do not expand the operator family inside EXP-023.

Update `HYP-CALIBRATION-001` accordingly after a formal result exists.

## Result decision tree

- `FULL_REPLICATION`: strengthen calibration hypothesis.
- `PARTIAL_REPLICATION`: retain as split-sensitive.
- `SPLIT_HETEROGENEOUS`: investigate variant/context dependence.
- `NO_REPLICATION`: downgrade calibration hypothesis.

If the combined effect replicates, use secondary `A_mu`/`A_sigma` results to
motivate a future mechanism test. Do not declare a dominant mechanism from weak
descriptive differences alone.

## Paper boundary

Even successful EXP-023 cannot establish:

- behavioral control;
- functional binding;
- attention mechanism causality;
- global information preservation;
- general transport;
- non-Abelian operator structure;
- dynamic manifold theory;
- world-model dynamics;
- scaling law.

## Review questions

1. Is `A_mu_sigma` vs `A0` the sole primary comparison? Yes.
2. Is `D_fixed` contextual rather than a serial gate? Yes.
3. Is the 64-record design structurally balanced? Yes.
4. Is primary data genuinely independent of EXP-022A? Yes, by prospective dataset-freeze requirement.
5. Are `A_mu` and `A_sigma` secondary descriptive mechanisms? Yes.
6. Is no favorable post-hoc layer/model rescue possible? Yes.
7. Is final RMSNorm still secondary? Yes.
8. Does the protocol accidentally claim attention effects? No.
9. Does the protocol accidentally test general coordinate transport? No.
10. Is a negative EXP-023 outcome cleanly interpretable without modification? Yes.

## Validation flags

```text
EXP023_PRIMARY_PURPOSE = INDEPENDENT_FEATUREWISE_CALIBRATION_REPLICATION
EXP023_PRIMARY_CONDITION = A_mu_sigma
EXP023_PRIMARY_CONTROL = A0
EXP023_PRIMARY_ESTIMAND = G_cal
EXP023_D_FIXED_ROLE = CONTEXTUAL_NOT_GATE
EXP023_SECONDARY_POLICY = DESCRIPTIVE_MEAN_SCALE_DECOMPOSITION
EXP023_PRIMARY_CHECKPOINT = block27_pre_final_rmsnorm
EXP023_PROPOSED_TOTAL_RECORDS = 64
EXP023_PROPOSED_SOURCE_FAMILIES_PER_CLASS = 8
EXP023_SPLIT_A_EVAL_N = 32
EXP023_SPLIT_B_EVAL_N = 32
EXP023_DATASET_REUSES_EXP022A = false
EXP023_ATTENTION_EFFECT_TESTED = false
EXP023_GENERAL_TRANSPORT_TESTED = false
EXP023_RMSNORM_CAUSAL_TESTED = false
MODEL_EXECUTION_PERFORMED = false
SCIENTIFIC_RESULT_CREATED = false
EXP023_PROTOCOL_STATUS = DRAFT_PROTOCOL_AWAITING_INDEPENDENT_DATASET_FREEZE
```
