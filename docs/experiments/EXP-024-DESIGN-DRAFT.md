# EXP-024 Design Draft

Status: `DESIGN_DRAFT_NOT_FROZEN`

This document is a prospective experimental-design draft only. It is not a
frozen preregistration, dataset, runner, authorization, or scientific result.
Canonical experiment evidence and research ledgers outrank it.

## Experiment Label

- Experiment: `EXP-024`
- Target hypothesis: `HYP_CALIBRATION_CONDITIONAL_002`
- Role in Paper-A: one targeted follow-up to close the highest-priority
  evidence gap identified after EXP-023.

## Selection Summary

- `SELECTED_FOLLOWUP_DESIGN = B`
- `PRIMARY_SCIENTIFIC_UNIT = condition/panel`
- `SECOND_MODEL_REQUIRED = false`
- `DIAGNOSTIC_EVAL_INDEPENDENCE = PASS`
- `ALGEBRAIC_SHARED_A0_PRIMARY_ANALYSIS = false`
- Primary diagnostic: condition-level fixed-readout degradation on independent
  DIAGNOSTIC families.
- Primary confirmatory endpoint: condition-level featurewise-recalibration
  benefit on source-family-independent EVAL families.

## Research Question

Can an independently measured condition-level diagnostic on held-out
DIAGNOSTIC source families identify conditions where a fixed block16 reference
readout becomes incompatible at block27-pre and where FIT-only featurewise
recalibration subsequently helps on untouched EVAL source families?

The experiment separates two questions:

1. Can prospective fixed-readout mismatch be measured without touching the
   confirmatory EVAL partition?
2. Does that mismatch predict recalibration rescue, rather than merely
   co-occurring with it in the same confirmatory partition?

## Hypothesis

Prospective hypothesis:

> A condition-level fixed-readout degradation score estimated on independent
> DIAGNOSTIC families is positively associated with condition-level
> FIT-only featurewise recalibration benefit estimated on source-family
> independent EVAL families.

Prediction is operationalized as a preregistered one-sided exact permutation
test of monotonic association across condition/panel units. It is not an
item-level classifier, a layer-level regression, or a post-hoc same-EVAL
correlation.

Null hypothesis: no positive monotonic association exists between the
condition-level DIAGNOSTIC mismatch score and the condition-level EVAL
calibration benefit.

## Constructs

- `condition/panel`: a prospectively defined controlled semantic/perturbation
  condition. Conditions are the independent inference units.
- `source family`: a family of related records sharing an origin/paraphrase
  structure. FIT, DIAGNOSTIC, and EVAL partitions must use disjoint source
  families within each condition.
- `fixed reference readout`: a semantic-class readout fitted on FIT data at
  block16-pre and then held constant when evaluated at other checkpoints.
- `featurewise recalibration`: low-capacity FIT-only mean, scale, or combined
  per-feature recalibration applied before the fixed reference readout.
- `balanced accuracy`: class-balanced accuracy at the condition/partition
  level.

## FIT / DIAGNOSTIC / EVAL Partitioning

For each condition:

- FIT may estimate the fixed reference readout and allowed featurewise
  recalibration statistics.
- DIAGNOSTIC may estimate the prospective mismatch/susceptibility score.
- EVAL must remain untouched when the diagnostic and prediction rule are
  defined, and is used only for the confirmatory endpoint.

Independence requirements:

- DIAGNOSTIC and EVAL must not share individual source families.
- The primary predictor must not use EVAL outcomes or representations from the
  EVAL partition.
- The primary outcome must not reuse the DIAGNOSTIC partition used to define
  the predictor.
- Partitions should be balanced across the four semantic classes within each
  condition where possible.

## Sampling Unit

The primary scientific/inference unit is `condition/panel`.

- Transformer layers are not treated as independent samples.
- Individual classifier predictions are not treated as independent when they
  share source families or fitted models.
- Models are not treated as independent replicates in the primary design.
- The number of conditions, not the number of rows per condition, drives the
  primary inferential degrees of freedom.

## Model and Checkpoint Scope

Model scope:

- Single default anchor: `Qwen/Qwen3-1.7B`
- Snapshot: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- `SECOND_MODEL_REQUIRED = false`
- Cross-model susceptibility is deferred as a secondary axis because it
  increases compute without resolving the primary heterogeneity mechanism.

Checkpoint scope:

- Primary reference checkpoint: `block16_pre_final_rmsnorm`.
- Primary confirmatory checkpoint: `block27_pre_final_rmsnorm`.
- Other layers, `block16` through `block27`, may be recorded descriptively but
  are not primary inferential units.
- Primary checkpoints are fixed before data outcomes are observed.

## Primary Diagnostic Definition

Primary diagnostic:

```text
D_diag_cond = BA_A0_diag(block27-pre) - BA_A0_diag(block16-pre)
```

Here `BA_A0_diag(checkpoint)` is the balanced accuracy of the fixed block16
reference readout evaluated on the condition's DIAGNOSTIC source families at
the specified checkpoint.

Properties:

- It uses semantic-class labels in the DIAGNOSTIC partition.
- It does not use the EVAL partition.
- It directly measures the hypothesized fixed-readout degradation.
- It is mechanistically interpretable as readout incompatibility across depth.
- It does not refit a layer-specific classifier.

Alternative diagnostic metrics are secondary, including:

- FIT-only standardized mean-shift magnitude.
- FIT-only scale-shift magnitude.
- A preregistered combined frame-mismatch score.
- DIAGNOSTIC decision-margin stability.

The primary metric is not selected because of a favorable historical
mean/scale signal. It is selected because it most directly operationalizes
the fixed-readout degradation that `HYP_CALIBRATION_CONDITIONAL_002` proposes
as the susceptibility construct.

## Calibration Conditions

Primary endpoint uses:

- `A0`: fixed reference readout.
- `A_mu_sigma`: FIT-only featurewise mean and scale recalibration.

Secondary descriptive conditions:

- `A_mu`: FIT-only featurewise mean recalibration.
- `A_sigma`: FIT-only featurewise scale recalibration.

The primary endpoint does not discard `A_mu` and `A_sigma`; they remain as
secondary decomposition outputs.

## Primary Confirmatory Endpoint

Primary confirmatory endpoint:

```text
G_eval_cond = BA_A_mu_sigma_EVAL(block27-pre) - BA_A0_EVAL(block27-pre)
```

`BA_A_mu_sigma_EVAL` uses the FIT-only recalibration statistics estimated on
FIT families and applies them to the fixed readout at block27-pre, evaluated
on source-family-independent EVAL families.

This is not the same as `BA_A0_diag`. The primary analysis therefore does not
share `A0_final` between the diagnostic and the confirmatory endpoint.

## Statistical Test

Primary test:

- Unit of analysis: condition/panel.
- Association measure: preregistered rank association, for example Spearman
  rho or Kendall tau, between `D_diag_cond` and `G_eval_cond` across
  conditions.
- Direction: one-sided, positive monotonic association.
- Inference: exact permutation test across condition labels, conditional on
  the observed paired values.
- Decision threshold: prespecified alpha and a prespecified monotonic
  criterion, fixed before any EVAL observation.

Why permutation/rank inference:

- The condition count is small by design.
- No high-precision asymptotic or bootstrap item-level assumption is
  warranted.
- The test respects condition as the independent sampling unit.

## Secondary Analyses

All secondary and prespecified:

- Same rank-association procedure for `G_mu_cond` and `G_sigma_cond` where
  those are condition-level secondary endpoint decompositions.
- Descriptive layerwise trajectory from block16-pre through block27-pre for
  each condition.
- Robustness of the primary association to the alternative FIT-only mismatch
  diagnostics.
- Leave-one-condition sensitivity as descriptive stability evidence only.
- No flexible meta-model, no variable selection after seeing EVAL, and no
  post-hoc pooling of conditions.

## Falsification Criteria

Primary test fails if the prespecified positive monotonic association is not
supported.

Interpretation depends on the failure pattern:

- Diagnostic fails to predict degradation: mismatch cannot yet be
  prospectively identified by this metric.
- Diagnostic predicts degradation but not calibration benefit: readout
  degradation and calibratability are distinct constructs.
- Diagnostic predicts both: supports conditional calibration susceptibility.
- No degradation occurs: measurement regime insufficient to test
  susceptibility.

No single negative outcome is interpreted as "representations do not drift."

## Negative-Result Interpretation

A negative primary result does not overturn EXP-021/EXP-022A/EXP-023
observations. It means Paper-A cannot yet promote the conditional
susceptibility hypothesis to an independently predicted mechanism.

Paper-A would then:

- retain the bounded core claim already supported by existing evidence;
- present the follow-up as a failed prospective susceptibility test;
- avoid claiming calibration benefit is predictable or mechanistically
  explained;
- leave `HYP_CALIBRATION_CONDITIONAL_002` as `NOT_SUPPORTED_BY_EXP024` or
  another appropriate canonical status only after formal analysis.

## Leakage Controls

- EVAL source families are untouched when defining the diagnostic and
  prediction rule.
- The primary predictor and primary outcome use different partitions.
- The fixed reference readout and featurewise recalibration statistics come
  only from FIT.
- No layer-specific classifier is refitted for the primary mechanism.
- No high-dimensional flexible meta-model is used.
- Dataset and protocol will be frozen before any formal inference.
- Formal prompt/record text exposure and formal-data inference must be tracked
  in the eventual runner/qualification tasks.
- `ALGEBRAIC_SHARED_A0_PRIMARY_ANALYSIS = false`.

## Prior-Art Distinction

Tuned Lens and related work establish that layer-specific affine readouts can
decode hidden states across depth. Model stitching establishes that simple
trained layers can functionally align bottom/top model representations.
Functional-alignment cautions establish that functional alignment does not
imply informational similarity.

Paper-A must not claim novelty merely because:

- hidden representations require layer-specific readouts;
- affine maps can align representations;
- a trained linear/affine transformation restores task performance.

The prospective distinction under test is:

- a fixed semantic-class readout is held constant across depth;
- only low-capacity FIT-only featurewise recalibration is allowed;
- no layer-specific classifier refitting is used for the primary mechanism;
- the susceptibility signal is measured on DIAGNOSTIC families and tested
  against confirmatory benefit on independent EVAL families.

## Paper-A Contribution If Successful

A successful EXP-024 would add:

> Calibration susceptibility varies predictably across controlled conditions,
> and an independent condition-level fixed-readout degradation diagnostic can
> prospectively identify that susceptibility before EVAL outcomes are
> observed.

This would close the highest-priority Paper-A evidence gap without claiming
universal transport, functional binding, behavioral control, or a general
calibration mechanism.

## Paper-A Interpretation If Negative

A negative EXP-024 would leave Paper-A as a bounded negative/heterogeneous
evidence contribution. The paper would explicitly report that the conditional
susceptibility hypothesis was tested and not supported, and that readout
degradation and calibratability remain distinguishable constructs.

## Candidate Comparison Matrix

Scores are qualitative: `HIGH`, `MEDIUM`, `LOW`.

| Criterion | A: layerwise diagnostic | B: multi-condition panel | C: cross-model susceptibility | D: item-level prospective diagnostic |
| --- | --- | --- | --- | --- |
| Primary unit | layer | condition/panel | model/condition | item/family |
| Scientific information gain | MEDIUM | HIGH | MEDIUM | MEDIUM |
| Independence from existing outcome | HIGH | HIGH | HIGH | HIGH |
| Algebraic-coupling risk | LOW-MEDIUM | LOW | LOW | LOW-MEDIUM |
| Statistical identifiability | LOW-MEDIUM | MEDIUM-HIGH | MEDIUM | LOW |
| Sample efficiency | HIGH | MEDIUM | LOW | LOW |
| Compute cost | LOW | LOW-MEDIUM | HIGH | LOW-MEDIUM |
| Dataset-construction burden | LOW | HIGH | LOW-MEDIUM | MEDIUM |
| Implementation risk | LOW | MEDIUM | HIGH | MEDIUM-HIGH |
| Continuity with EXP-022A/023 | HIGH | MEDIUM-HIGH | MEDIUM | MEDIUM |
| Paper-A journal uplift | MEDIUM | HIGH | MEDIUM | MEDIUM |
| Paper-A CCF-A uplift | LOW | MEDIUM | HIGH | LOW-MEDIUM |
| Post-hoc flexibility risk | MEDIUM | LOW-MEDIUM | LOW-MEDIUM | HIGH |

Selection rationale:

- `A` is rejected because layers are dependent repeated computational stages;
  common depth trends can create apparent association, and the effective
  layer-count is small.
- `B` is selected because it supplies multiple independent heterogeneity
  units, directly tests which conditions are susceptible, and preserves a
  clean diagnostic/confirmatory separation.
- `C` is deferred because cross-model breadth does not by itself resolve the
  primary mechanism question and materially increases compute.
- `D` is rejected because item-level predictions within shared families and
  fitted models risk overfitting and weak identifiability.

## Minimum Dataset Requirement

Recommended at design level:

- `6-10` prospectively defined independent semantic/perturbation conditions,
  with a target of `8`.
- Each condition has independent FIT, DIAGNOSTIC, and EVAL source families.
- Each condition is balanced across four semantic classes where feasible.
- Example layout: 24 source families per condition, partitioned as 8 FIT,
  8 DIAGNOSTIC, and 8 EVAL, yielding roughly 4 records per class in each
  partition.

This is a design-level recommendation only. Exact wording, family counts,
condition definitions, and record counts are deferred to Task-097C.

Do not claim high-precision power estimates without justified effect
distribution assumptions. The design deliberately increases independent
condition units rather than merely adding rows within one unit.

## Compute Estimate Class

- Single-model frozen local inference at block16-pre and block27-pre.
- Descriptive layerwise extraction from block16 through block27.
- No model training; no second model; no high-dimensional meta-model fitting.
- Compute class: moderate single-GPU/CPU inference, materially lower than a
  cross-model design.

## Falsification Condition

Primary test rejects the null only if the prespecified one-sided exact
permutation association across conditions is met. A failure to meet that
criterion is a negative or indeterminate primary result as specified above.

## Next Step

Proceed to Task-097C: EXP-024 dataset/protocol design and preregistration
draft. Do not generate the dataset, freeze the preregistration, implement the
runner, or run any model in this task.

## Current Status

- `EXP024_DESIGN_DRAFT_CREATED = true`
- `EXP024_PREREGISTRATION_FROZEN = false`
- `NEW_DATASET_CREATED = false`
- `MODEL_RUN_PERFORMED = false`
- `FORMAL_DATA_INFERENCE = false`
- `NEW_RESULT_CREATED = false`
- `EXP024_AUTHORIZATION_CREATED = false`
