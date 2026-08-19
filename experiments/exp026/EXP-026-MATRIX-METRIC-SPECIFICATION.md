# EXP-026 Matrix Metric Specification

Status: `FROZEN_DESIGN_NOT_RUN`

This file freezes every result-changing matrix, summary, calibration, and
uncertainty definition for EXP-026.

## Common Identity Contracts

- `CLASS_ORDER = ("logic", "causality", "analogy", "definition")`.
- `PARTITIONS = ("FIT", "DIAGNOSTIC", "EVAL")`.
- `RECORD_ROLES = ("reference_form", "condition_realization")`.
- `ALLOCATION = {"FIT": 6, "DIAGNOSTIC": 8, "EVAL": 8}`.
- `N_CONDITIONS = 10`.
- Condition order is the same ten-condition order bound in the preregistration.
- Record representations are last-valid-token vectors in `float32` with shape
  `[hidden_size]`.

## Balanced Accuracy

Four-class balanced accuracy is macro-averaged per-class recall:

```text
BA = (1/4) * sum_{class in CLASS_ORDER} recall(class)
```

- Inputs must be equal length.
- True class set must exactly equal the four-class universe.
- Predicted labels must belong only to the four-class universe.
- A missing or zero-count class is a protocol-integrity error.
- Predictions are mapped through `classifier.classes_`.

This is the same unadjusted balanced-accuracy definition used by EXP-024/025.

## Classifier Contract

For each model `m` and source layer `i`, fit one frozen semantic classifier
`h_m,i` using only FIT condition-realization representations from source layer
`i`.

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

No hyperparameter tuning, no per-layer classifier selection, and no refitting
after FIT.

## Featurewise Statistics and Frozen Scaler Contract

Featurewise mean and standard deviation are estimated with `StandardScaler`:

```text
StandardScaler(with_mean=true, with_std=true)
```

Scale values use sample standard deviation, as implemented by scikit-learn.
Features with `scale <= 0` are treated as zero-scale dimensions; their centered
value is left at zero. Division is performed only for `scale > 0`.

## Pairwise Recalibration Definitions

For a pair with source layer `i` and target layer `j`, define:

- `mu_src(m,i)`, `sigma_src(m,i)`: FIT condition-realization featurewise
  statistics at source layer `i`.
- `mu_tgt(m,j,c)`, `sigma_tgt(m,j,c)`: FIT condition-realization featurewise
  statistics at target layer `j` for condition `c`.

The source classifier `h_m,i` is never refit.

### A0

```text
z_A0 = (h_target - mu_src) / sigma_src
Ccal_A0 = h_m,i(z_A0)
```

### A_mu

```text
z_A_mu = (h_target - mu_tgt) / sigma_src
Ccal_A_mu = h_m,i(z_A_mu)
```

### A_sigma

```text
z_A_sigma = (h_target - mu_src) / sigma_tgt
Ccal_A_sigma = h_m,i(z_A_sigma)
```

### A_mu_sigma

```text
z_A_mu_sigma = (h_target - mu_tgt) / sigma_tgt
Ccal_A_mu_sigma = h_m,i(z_A_mu_sigma)
```

All statistics are FIT-only. No DIAGNOSTIC or EVAL feature statistic may enter
calibration fitting.

`A_mu_sigma` is the primary recalibration variant. `A_mu` and `A_sigma` are
secondary/descriptive only.

## Source-Layer Technical Usability

For each source layer `i`:

- Train `h_m,i` on FIT.
- Evaluate `h_m,i` on same-layer DIAGNOSTIC condition-realization records.
- For each condition `c`, compute the condition-level four-class balanced
  accuracy `BA_diag_self(m,i,c)`.
- Define:

```text
BA_diag_self(m,i) =
  (1 / 10) * sum_c BA_diag_self(m,i,c)
```

Frozen source technical-usability floor:

```text
SOURCE_TECHNICAL_FLOOR = 0.75
```

- If `BA_diag_self(m,i) >= 0.75`, source row `i` is
  `CONFIRMATORY_ELIGIBLE`.
- Otherwise source row `i` is
  `DESCRIPTIVE_ONLY_TECHNICALLY_UNQUALIFIED`.

The threshold is not lowered after seeing the profile. The row is retained in
the full descriptive matrix. EVAL never determines source eligibility.

## Source-Coverage Gate

For each model separately, source-dependent confirmatory endpoints are
`EVALUABLE` only when both conditions hold:

1. eligible source count >= `ceil(L / 2)`;
2. normalized-depth span of eligible sources >= `0.5`.

If either condition fails:

```text
SOURCE_DEPENDENT_CONFIRMATORY_ENDPOINTS = NOT_EVALUABLE
```

The full descriptive matrix may still be retained.

## Raw Compatibility Matrix

For model `m`, source `i`, target `j`, condition `c`:

```text
C0_m(i,j,c) =
  BA(h_m,i applied directly to target-layer-j EVAL representations under condition c)
```

No recalibration.

```text
Cself_m(i,c) = C0_m(i,i,c)
D_m(i,j,c) = Cself_m(i,c) - C0_m(i,j,c)
```

`D_m(i,i,c) = 0` by construction. Diagonal cells are excluded from off-diagonal
structural summaries.

## Recalibrated Matrix

```text
Ccal_m(i,j,c) =
  BA(h_m,i applied to A_mu_sigma-calibrated target-layer-j EVAL representations under condition c)
R_m(i,j,c) = Ccal_m(i,j,c) - C0_m(i,j,c)
```

Positive `R` means held-out improvement from the frozen FIT-only featurewise
recalibration. Do not infer transport, equivalence, invariant preservation, or
causal repair.

## Condition-Pooled Matrices

```text
Dbar_m(i,j) = (1/10) * sum_c D_m(i,j,c)
Rbar_m(i,j) = (1/10) * sum_c R_m(i,j,c)
```

All ten conditions receive equal weight. No condition dropping.

## Structural Summary S1: DISTANCE_ASSOCIATION

For each model, compute over confirmatory-eligible source rows and all
off-diagonal target pairs:

```text
x(i,j) = abs(d(i) - d(j))
y(i,j) = Dbar_m(i,j)
```

Define:

```text
DISTANCE_ASSOCIATION_m = Spearman(x, y)
```

Tie handling:

```text
average ranks
```

Implementation identity: `scipy.stats.spearmanr` with `nan_policy="raise"`.

This asks whether compatibility loss is ordered by normalized source-target
depth distance. It does not establish causal depth drift.

### S1 Support Rule

- Point estimate `rho = DISTANCE_ASSOCIATION_m`.
- Cluster-bootstrap uncertainty is defined below.
- Support class:

```text
POSITIVE_SUPPORTED if one-sided 95% cluster-bootstrap lower bound > 0
NOT_SUPPORTED otherwise
```

No two-sided p-value is used for the primary S1 endpoint.

## Structural Summary S2: SOURCE_DOMINANCE_INDEX

For the off-diagonal `Dbar` matrix restricted to confirmatory-eligible source
rows:

```text
row_mean_i = mean_{j != i} Dbar(i,j)
column_mean_j = mean over eligible i != j Dbar(i,j)
```

Variance convention:

```text
population variance: sum((value - mean)^2) / N
```

Using `numpy.var(..., ddof=0)`.

```text
SOURCE_VARIANCE = population_variance(row_mean_i)
TARGET_VARIANCE = population_variance(column_mean_j)
SDI = (SOURCE_VARIANCE - TARGET_VARIANCE)
      / (SOURCE_VARIANCE + TARGET_VARIANCE)
```

Zero-denominator behavior:

```text
if SOURCE_VARIANCE + TARGET_VARIANCE == 0:
    SDI = 0
    status = NO_ROW_OR_COLUMN_VARIATION
```

Interpretation:

- `SDI > 0`: stronger source/reference organization.
- `SDI < 0`: stronger target organization.
- `SDI = 0`: balanced or no variation.

This is an operational summary, not a causal decomposition.

### S2 Support Rule

- Point estimate `SDI`.
- Cluster-bootstrap uncertainty is defined below.
- Support classes:

```text
SOURCE_DOMINANT if SDI > 0 and one-sided 95% lower bound > 0
TARGET_DOMINANT if SDI < 0 and one-sided 95% upper bound < 0
NO_DOMINANCE otherwise
NO_ROW_OR_COLUMN_VARIATION if the raw denominator is exactly zero
```

## Structural Summary S3: LOCALIZATION (SECONDARY/DESCRIPTIVE)

For adjacent target layers `j,j+1`, over confirmatory-eligible source rows:

```text
J_m(j) = mean_i abs(Dbar_m(i,j+1) - Dbar_m(i,j))
```

Define:

```text
LOCALIZATION = max_j J(j) / sum_j J(j)
```

Zero-denominator behavior:

```text
if sum_j J(j) == 0:
    LOCALIZATION = 0
    status = NO_TARGET_BOUNDARY_VARIATION
```

The maximizing boundary location may be reported descriptively. The selected
boundary is not confirmatory.

Recovery concentration analog for routing only:

```text
J_R_m(j) = mean_i abs(Rbar_m(i,j+1) - Rbar_m(i,j))
LOCALIZATION_R = max_j J_R(j) / sum_j J_R(j)
```

with the same zero-denominator behavior.

Status: `SECONDARY_DESCRIPTIVE`.

## Summary S4: LOW_D_RECOVERY (SECONDARY-CONFIRMATORY)

Use DIAGNOSTIC only to create a prospective pair mask.

For each eligible source-target off-diagonal pair:

```text
Dbar_diag_m(i,j) =
  (1/10) * sum_c D_m(i,j,c computed on DIAGNOSTIC records)
```

Define:

```text
LOW_OR_NONDEGRADATION_PAIR iff Dbar_diag_m(i,j) <= 0
```

Then evaluate only on EVAL:

```text
LOW_D_RECOVERY_m = mean Rbar_eval_m(i,j)
```

over the frozen DIAGNOSTIC-selected pair set.

Also report `eligible_pair_count` and `positive_recovery_pair_fraction`.

Effective-n behavior:

```text
if eligible_pair_count == 0:
    LOW_D_RECOVERY_m = NOT_EVALUABLE
    positive_recovery_pair_fraction = NOT_EVALUABLE
```

Support rule:

```text
SUPPORTED if point estimate > 0 and one-sided 95% cluster-bootstrap lower bound > 0
NOT_SUPPORTED otherwise
NOT_EVALUABLE if eligible_pair_count == 0
```

Do not relax the `<= 0` criterion.

## Cross-Model Comparison

Do not define a confirmatory architecture or family effect.

Primary cross-model comparison is comparison of the two frozen model-specific
structural signatures. Signature includes:

- `DISTANCE_ASSOCIATION`;
- `SDI`;
- `LOCALIZATION`;
- mean off-diagonal `Dbar`;
- mean off-diagonal `Rbar`;
- `LOW_D_RECOVERY`.

Differences are `MODEL-DEPENDENT PROFILE DIFFERENCES`, not architecture-caused
differences.

## Normalized Matrix Similarity (DESCRIPTIVE)

Cross-model normalized matrix similarity is descriptive only.

Common normalized-depth grid:

```text
G = {0.0, 0.1, ..., 1.0}
```

Interpolation method:

```text
linear interpolation over the normalized-depth grid
```

Implementation identity: `scipy.interpolate.RegularGridInterpolator` with
`method="linear"` and `bounds_error=False`, `fill_value=None`. Each model's
`Dbar` and `Rbar` matrix is evaluated on the common `G x G` grid using its own
normalized-depth coordinates. Diagonal grid cells are excluded. The resulting
off-diagonal flattened-grid values are compared descriptively with:

- Spearman rank correlation (average ranks);
- Pearson correlation.

Missing values are not expected because all-block extraction is frozen. If a
missing value occurs, that grid cell is omitted pairwise and the omission is
reported.

Status: `DESCRIPTIVE`.

## Statistical Unit and Bootstrap Specification

Primary uncertainty unit:

```text
EVAL source-family cluster
```

Resampling unit:

```text
source family
```

Resampling design:

```text
condition-stratified source-family cluster bootstrap
```

Procedure:

1. Keep the FIT-fitted classifiers and FIT-only calibration statistics fixed.
2. For each condition and semantic class, resample EVAL source families with
   replacement to the same original cell count.
3. Preserve all layer outputs for a sampled source family.
4. Preserve source-target matrix dependence by recomputing the full matrix on
   the resampled EVAL records.
5. Compute the requested structural summary for each replicate.

No row-wise or cell-wise bootstrap is used.

Bootstrap parameters:

- Number of replicates: `5000`.
- RNG algorithm: `numpy.random.PCG64`.
- Seed: `20260819`.
- RNG construction: `numpy.random.Generator(numpy.random.PCG64(20260819))`.
- CI level: `95%`.
- Quantile method: `numpy.percentile(..., method="linear")`.
- One-sided positive lower bound: `5th` percentile.
- One-sided negative upper bound: `95th` percentile.

For `LOW_D_RECOVERY`, the DIAGNOSTIC-selected pair mask is computed once from
the original DIAGNOSTIC records and held fixed across bootstrap replicates; the
mean `Rbar_eval` is recomputed on resampled EVAL records for the fixed mask.

## Permutation Policy

No layer-order permutation test is used for the primary summaries because the
layer-pair matrix is not a set of independent observations. Confidence intervals
use the source-family cluster bootstrap above.

No p-value correction is required for the small confirmatory hierarchy because
the two primary summaries have distinct operational definitions and are not
treated as a multiple-testing family.

## Specification Gap Resolution Table

| Gap | Resolution |
| --- | --- |
| Layer-carrier extraction | Frozen in `EXP-026-LAYER-CARRIER-MAPPING.md`; hook on each decoder-layer output. |
| Source eligibility coverage | Frozen floor `0.75`; coverage gate >= `ceil(L/2)` and span >= `0.5`. |
| Variance convention for SDI | Population variance (`ddof=0`). |
| Spearman ties | Average ranks via `scipy.stats.spearmanr` with `nan_policy="raise"`. |
| Bootstrap unit | Source-family cluster, condition-stratified, EVAL records. |
| Bootstrap RNG | `numpy.random.PCG64(20260819)`. |
| Bootstrap replicates/CI | `5000`; percentile; 95%; linear quantile interpolation. |
| Localization zero denominator | `LOCALIZATION=0`, status `NO_TARGET_BOUNDARY_VARIATION`. |
| `LOW_D_RECOVERY` effective n=0 | `NOT_EVALUABLE`. |
| Interpolation behavior | Linear interpolation on common normalized-depth grid; descriptive only. |
| Routing conflict resolution | Frozen in `EXP-026-ROUTING-RULES.md`. |

`EXP026_SPECIFICATION_GAPS = 0`.

## Prohibited Inference

Do not interpret `D` as information loss, representation loss, or semantic
destruction.

Do not interpret `R` as transport, equivalence, invariant preservation, or
causal repair.

Do not call cross-model differences architecture-caused, family-caused,
tokenizer-caused, recipe-caused, or scale-caused.

Do not use matrix cells as independent observations.
