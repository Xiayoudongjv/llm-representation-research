# Paper A Post-Closure Construct Sensitivity Preregistration V1

Status: `FROZEN_BEFORE_SENSITIVITY_RESULT_EXPOSURE`

This document freezes a small, descriptive audit of already registered Paper A
construct components. It does not alter the primary EXP-026/027 design or
outcomes. It is not a new Paper A primary hypothesis, a replication, a rescue
analysis, a mechanism experiment, a new model/task/carrier study, or an
operator sweep.

## 1. Scientific purpose and epistemic status

The audit addresses three bounded reviewer questions:

1. whether the registered SDI ratio obscures its two variance components or
   has a degenerate denominator;
2. what registered LOW-D auxiliary quantities accompany the categorical
   summary; and
3. whether absolute LOW-D recovery is reported alongside the available
   balanced-accuracy headroom.

The frozen labels are:

```text
ANALYSIS_STATUS=POST_CLOSURE_CONSTRUCT_SENSITIVITY
PRIMARY_PAPER_A_RESULTS_CHANGED=false
REGISTERED_EXP026_027_OUTCOMES_REINTERPRETED=false
CONFIRMATORY_STATUS=NONE
NEW_MODEL_INFERENCE=false
NEW_MODEL_FITTING=false
NEW_BOOTSTRAP=false
NEW_PERMUTATION_TEST=false
NEW_HYPOTHESIS_TEST=false
```

Any eventual result must be described as `POST-CLOSURE DESCRIPTIVE
SENSITIVITY`. It must not be described as confirmatory, a replication, or
validation of a universal construct.

## 2. Frozen authorities and data boundary

The design inherits the following local authorities without modification:

| Authority | SHA-256 |
|---|---|
| `experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md` | `5f58445e26eee7effddd7cd5b4ae255b7153d61fa7a76b5c0684fa1dbb08d8db` |
| `experiments/exp026/EXP-026-PREREGISTRATION.md` | `730175071e315b484e360b6359945f567bfe8edf4f52e6a0893c3f2a7dadf8e1` |
| `experiments/exp026/exp026_frozen_config.json` | `ccf60c8a9dc6f3b9d3cce533910334e1f8ec33665a1cf692b98a8aaf683afb57` |
| `docs/experiments/EXP-026-SCIENTIFIC-REVIEW.md` | `383e9c99cb585aad110cc01489727a8d70c05d0ad96f36f11788b7568b0dd1c5` |
| `docs/experiments/EXP-027-PREREGISTRATION.md` | `83ba4bb14e87334a6c52a8746f86874eab9578e646abc736057fbd1f4e6322fe` |
| `experiments/exp027/exp027_frozen_design.json` | `b37bfd9c3d57bf891ef1993b3a1d7737fcedbe143813d61f5c7ae9ecb0bc5b1a` |
| `docs/experiments/EXP-027-SCIENTIFIC-REVIEW.md` | `3db403913c443d8f08ad3553289d26cd14b49713a43243e8d3d43b027881a7a7` |
| `experiments/exp026/results/exp026_results.json` | `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551` |
| `experiments/exp027/results/exp027_results.json` | `1f15027d17456f5dc8ff4803452c732af8ba464f70e537195b8833d9d44f6c6d` |

The Paper A submission candidates remain outside this checkpoint and must not
be changed during sensitivity preregistration:

```text
docs/paper/PAPER-A-MANUSCRIPT-V1.2.md
SHA-256 = 7a33b9474bdfdd93d871d5969ce2d1561c63d3b8828e15317208c6201595f5e3

docs/paper/PAPER-A-SUPPLEMENT-V1.md
SHA-256 = 88057f6701d255914f9d2664f5ca453fee5fae473809533d28eb64937b8a6bcc
```

The inherited panel is the frozen EXP-024/025 condition panel: 1,760 records,
880 source families, four semantic classes, ten registered conditions, and
source-family-disjoint FIT, DIAGNOSTIC, and EVAL partitions. The model scope is
the existing Paper A panel: Qwen3-1.7B, OLMo-2-0425-1B-Instruct, and
Meta-Llama-3.2-1B-Instruct. No new model forward pass, representation
extraction, classifier fitting, split, prompt, carrier, or condition is
permitted.

The sensitivity execution may read only the canonical EXP-026/027 result
artifacts and their bound metadata needed to identify the registered matrices,
eligible-source identities, masks, and fields. It must not inspect or print
previously unreported sensitivity values before this preregistration is
committed.

## 3. Module A — registered SDI component decomposition

### 3.1 Question

Determine descriptively whether the registered SDI sign/classification is
accompanied by nonzero source- and target-axis variance components and whether
the denominator is numerically degenerate.

### 3.2 Frozen definitions

Use the exact EXP-026 definitions on the eligible-source off-diagonal `Dbar`
matrix:

```text
SOURCE_VARIANCE = population variance of eligible-source off-diagonal row means
TARGET_VARIANCE = population variance of eligible-source off-diagonal column means
SDI = (SOURCE_VARIANCE - TARGET_VARIANCE)
      / (SOURCE_VARIANCE + TARGET_VARIANCE)
```

Use `numpy.var(..., ddof=0)`. Preserve the registered zero-denominator rule:
if the denominator is exactly zero, the registered SDI is zero with status
`NO_ROW_OR_COLUMN_VARIATION`.

For each of Qwen, OLMo, and Llama, report exactly:

- `SOURCE_VARIANCE`;
- `TARGET_VARIANCE`;
- `SOURCE_VARIANCE + TARGET_VARIANCE`;
- the registered `SDI`;
- the existing registered SDI status.

No new significance test, interval, threshold, or SDI-like statistic is
permitted.

### 3.3 Authority route

If canonical output already stores `SOURCE_VARIANCE` and `TARGET_VARIANCE`,
copy those exact fields and classify the operation
`REGISTERED_COMPONENT_EXPOSURE`.

If those fields are absent but the exact canonical `Dbar` matrix and
eligible-source identity are present, reconstruct the two already-registered
components deterministically and classify the operation
`REGISTERED_COMPONENT_RECONSTRUCTION`. The reconstructed SDI must reproduce
the canonical SDI within `1e-12` absolute error. Otherwise the sensitivity run
is blocked; no alternative definition may be introduced.

The output is descriptive exposure of registered components, not validation of
SDI stability, an intrinsic model property, causal organization, or robustness
across tasks or carriers.

## 4. Module B0 — registered LOW-D auxiliary exposure

Before any headroom calculation, expose only quantities already required by
the frozen LOW-D specification. For each model, report where canonically
available:

- `eligible_pair_count`;
- `positive_recovery_pair_fraction`;
- registered `LOW_D_RECOVERY` point estimate;
- existing registered interval and status.

If an auxiliary is omitted from the publication artifact but is recoverable
from the exact canonical DIAGNOSTIC mask and EVAL `Rbar` matrix, deterministic
reconstruction is permitted and must be labelled
`REGISTERED_LOW_D_AUXILIARY_RECONSTRUCTION`; otherwise use
`REGISTERED_LOW_D_AUXILIARY_EXPOSURE`.

The mask is fixed exactly as:

```text
eligible source rows
AND off-diagonal pairs
AND Dbar_diag(i,j) <= 0
```

The mask is created from the ten equally weighted DIAGNOSTIC conditions and is
then applied to EVAL. Do not change the `<= 0` threshold, reselect pairs,
include diagonal pairs, use EVAL for selection, or pool models inferentially.

## 5. Module B1 — LOW-D headroom descriptive sensitivity

This is the only genuinely new sensitivity in this protocol. It is descriptive
and has no support/failure classification.

### 5.1 Frozen question and inputs

The question is whether absolute LOW-D restricted-recovery magnitudes should be
read alongside different available balanced-accuracy headroom. Use the exact
registered LOW-D pair mask from Module B0. Do not use calibrated performance
to define selection or headroom.

For each selected source-target pair on EVAL, compute:

```text
C0bar_eval(i,j) = equal-weight mean across the same ten EVAL conditions of C0
HEADROOM(i,j) = 1 - C0bar_eval(i,j)
```

Balanced accuracy has maximum 1. The EVAL values are measurement inputs for
this descriptive summary; they do not alter the registered mask or primary
outcomes.

### 5.2 Required output

For each model report only the following headroom summaries:

- pair count;
- mean, median, Q25, and Q75 of `C0bar_eval`;
- mean, median, Q25, and Q75 of `HEADROOM`;
- minimum and maximum `HEADROOM`;
- alongside them, the registered `LOW_D_RECOVERY` and registered LOW-D status
  for reference.

Quantiles are frozen as:

```text
numpy.quantile
method = "linear"
quantiles = (0.25, 0.50, 0.75)
```

No p-value, confidence interval, bootstrap, permutation test, cross-model
pooled inference, arbitrary threshold, or new support label is permitted.

### 5.3 Explicitly forbidden derivatives

The following are not computed in this protocol:

- `R / (1 - C0)`;
- normalized recovery;
- percentage of available headroom recovered;
- headroom-adjusted `R`;
- residualized `R`;
- partial correlation or regression adjustment;
- matching by `C0`;
- threshold sensitivity;
- operator sensitivity;
- alternate recalibration;
- new tasks, carriers, models, or CKA analyses.

The audit must not classify headroom as an artifact or non-artifact. If later
review finds visible headroom differences, the only permitted manuscript
consequence is a bounded limitation that absolute recovery magnitudes are
partly constrained by available balanced-accuracy headroom and should not be
read as normalized recovery capacity. If headroom is broadly non-degenerate,
the only permitted statement is that nonzero available headroom was observed
in the registered LOW-D sets; this does not establish that headroom explains
or fails to explain model differences.

## 6. LOW-D construct rationale

`LOW-D` means `LOW-DEGRADATION RECOVERY DIAGNOSTIC`. Its registered question is
conditional: pairs selected prospectively from independent DIAGNOSTIC data by
`Dbar_diag(i,j) <= 0` are evaluated on held-out EVAL data to ask whether the
frozen FIT-only restricted recalibration has positive average gain `R`.

LOW-D is not low-dimensional analysis, an intrinsic model trait, general
recoverability, normalized recovery capacity, or an operator-independent
construct. The profile belongs to the tested model × task panel × carrier ×
readout × restricted-calibration protocol. Existing canonical profile labels
are unchanged.

## 7. No outcome-dependent analysis branches

The execution path is fixed before sensitivity output exposure:

1. bind canonical identities and schemas;
2. expose or deterministically reconstruct the registered SDI components;
3. expose or deterministically reconstruct registered LOW-D auxiliaries;
4. apply the unchanged registered LOW-D mask;
5. compute the fixed B1 headroom summaries;
6. validate schema, counts, masks, and deterministic arithmetic;
7. stop for independent review.

No result-dependent choice of statistic, model, subset, threshold, operator,
quantile method, or interpretation branch is allowed. A concrete construct-
integrity problem would require a new preregistration before any follow-up
analysis.

## 8. Manuscript and page-budget policy

This sensitivity cannot overturn EXP-026/027 outcomes, change registered
status labels, convert `NOT_SUPPORTED` to `SUPPORTED`, create a fourth Paper A
contribution, create a headline result, or raise the claim ceiling.

Module A, B0, and B1 numeric detail belongs in the supplement. The main text
may receive at most one or two sentences of construct clarification or a
bounded limitation, offset by compression elsewhere. The already existing
V1.2 manuscript and Supplement V1 are not modified by this preregistration.

## 9. Stop rule

After Modules A, B0, and B1 are executed and independently reviewed, stop
Paper A science by default. Do not automatically perform threshold sweeps,
headroom-normalized gains, alternate recalibration operators, new tasks,
carriers, models, CKA, or EXP-028. Any follow-up requires a new prospective
preregistration before result exposure.

## 10. Reproducibility and non-execution record

The future sensitivity implementation must be deterministic, use existing
canonical artifacts only, and preserve all source-family, condition, mask,
and EVAL/FIT boundaries. It must not load model weights or execute a model.
No analysis script, result file, manuscript change, or supplement change is
created by this preregistration task.

```text
TEMPORAL_SCOPE=NONE
NEW_SENSITIVITY_RESULTS_EXPOSED=false
FORMAL_MODEL_INFERENCE_PERFORMED=false
```

This protocol is frozen before any new SDI-component or headroom value is
reported.
