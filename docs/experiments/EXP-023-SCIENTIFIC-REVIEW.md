# EXP-023 Scientific Review and Closeout

This document closes EXP-023 after one valid canonical formal result. It is a
scientific review and claim-boundary record, not a rerun, rescue analysis, or
new experiment.

## Authoritative Artifacts

- Repository commit: `cc9141f87b4725460e30ab77f173d2fd95906824`
- Canonical result: `experiments/exp023/results/exp023_results.json`
- Canonical result SHA-256: `f30591ad942e82a322e594695ce1d5023586261fd7b8bccaa208b0d46f388000`
- Authorization ID: `9ca46d07-570a-494a-b785-01d6f7fdbeac`
- Authorization SHA-256: `ccdce00b246b733976d23987a3f488aabf8d36f7ccb25fe0e1fcc7b81f0932bd`
- Run attempt ID: `c52d3aec-f8f3-402e-a2f1-bf14d0087b57`
- Consumption record: `experiments/exp023/results/authorization_consumption/ccdce00b246b733976d23987a3f488aabf8d36f7ccb25fe0e1fcc7b81f0932bd.json`
- Consumption SHA-256: `46d4edafba8e7f9375a6011f4b423777ca538c981cb664a6cbb4a9532422394b`
- Frozen preregistration: `docs/experiments/EXP-023-PREREGISTRATION.md`
- Frozen preregistration SHA-256: `11bfa984d436ba06f7f3d1b0db24b90439742e9d9a87d124880834b437749f0b`
- Frozen dataset: `experiments/exp023/data/exp023_independent_controlled.json`
- Frozen dataset SHA-256: `9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a`
- Model/hook qualification SHA-256: `5297d1ae185d5cacfbbd4a71cff0803a75c37c1d83e2c9a5077201ff79a3dc52`
- Technical status: `VALID`
- Result validation: `PASS`
- Scientific status: `FORMAL_ANALYSIS_COMPLETED`

## Registered Primary Outcome

### Split A

- `G_cal = 0.25`
- Primary favorable: `10`
- Primary unfavorable: `2`
- Exact p: `0.019287109375`
- Split-level support: `true`

### Split B

- `G_cal = 0.0`
- Primary favorable: `1`
- Primary unfavorable: `1`
- Exact p: `0.75`
- Split-level support: `false`

### Cross-split classification

- `EXP023_REGISTERED_OUTCOME = NO_REPLICATION`
- Do not relabel as `PARTIAL_REPLICATION`: the unsupported split has
  `G_cal = 0`, not `G_cal > 0`.

## Observation

### Split A

- `A0_reference_BA = 0.9375`
- `A0_final_pre_BA = 0.59375`
- `A_mu_final_pre_BA = 0.90625`
- `A_sigma_final_pre_BA = 0.8125`
- `A_mu_sigma_final_pre_BA = 0.84375`
- `D_fixed = -0.34375`
- `D_fixed_exact_p = 0.001708984375`
- `G_cal = 0.25`
- `G_cal_exact_p = 0.019287109375`
- Bootstrap `G_cal` CI: `[0.0625, 0.40625]`
- Bootstrap `D_fixed` CI: `[-0.5, -0.1875]`

### Split B

- `A0_reference_BA = 0.9375`
- `A0_final_pre_BA = 0.90625`
- `A_mu_final_pre_BA = 0.90625`
- `A_sigma_final_pre_BA = 0.875`
- `A_mu_sigma_final_pre_BA = 0.90625`
- `D_fixed = -0.03125`
- `D_fixed_exact_p = 0.5`
- `G_cal = 0.0`
- `G_cal_exact_p = 0.75`
- Bootstrap `G_cal` CI: `[-0.09375, 0.09375]`
- Bootstrap `D_fixed` CI: `[-0.125, 0.0625]`

## Operational Result

- `GENERAL_CROSS_SPLIT_CALIBRATION_REPLICATION = NOT_SUPPORTED`
- `EXP023_REGISTERED_OUTCOME = NO_REPLICATION`
- Split A showed substantial fixed-readout degradation and substantial
  featurewise recalibration rescue.
- Split B showed little fixed-readout degradation and no recalibration rescue.
- Do not pool A/B to obtain an alternate positive endpoint.

## D_fixed / G_cal Dependency Warning

`D_fixed = A0_final - A0_reference`.

`G_cal = A_mu_sigma_final - A0_final`.

The two quantities share `A0_final`, therefore:

- do not compute naive `correlation(D_fixed, G_cal)` as causal evidence;
- do not claim that greater degradation predicts greater rescue from these two
  splits;
- treat the Split-A co-occurrence as hypothesis-generating only.

Future susceptibility diagnostics must be independent of the confirmatory EVAL
quantity entering `G_cal`.

## Mean / Scale Secondary Signal

### Split A

- `G_mu = 0.3125`
- `G_sigma = 0.21875`
- `G_joint_over_mu = -0.0625`
- `G_joint_over_sigma = 0.03125`

### Split B

- `G_mu = 0.0`
- `G_sigma = -0.03125`
- `G_joint_over_mu = 0.0`
- `G_joint_over_sigma = 0.03125`

Permitted secondary interpretation: Split A provides a hypothesis-generating
signal that mean/location recalibration may account for more of the observed
rescue than scale recalibration.

Do not claim that mean drift is an established mechanism, scale drift is
irrelevant, or mean-only recalibration is generally superior.

## EXP-022A Comparison

The strongest degradation/rescue occurred in different complementary splits
across EXP-022A and EXP-023. Therefore:

- `FIXED_VARIANT_DIRECTION_EXPLANATION = NOT_SUPPORTED`
- Do not claim original-to-paraphrase or paraphrase-to-original always
  degrades.
- Conservative interpretation: fixed-readout compatibility appears condition
  and dataset dependent.
- This is Interpretation, not established mechanism.

## Claim Boundaries

- `GENERAL_COORDINATE_TRANSPORT = NOT_TESTED`
- `FUNCTIONAL_BINDING = NOT_TESTED`
- `BEHAVIORAL_CONTROL = NOT_SUPPORTED_BY_EXP023`
- `CONDITIONAL_CALIBRATION_SIGNAL = OBSERVED_HYPOTHESIS_GENERATING`
- `MEAN_ONLY_CALIBRATION_SIGNAL = OBSERVED_SECONDARY_DESCRIPTIVE`
- Do not reinterpret featurewise calibration as proof of transport.
- Do not promote `HYP_TRANSPORT_001`.

## Paper-A Evidence-to-Claim Assessment

Bounded core claim:

> Fixed readout compatibility can degrade substantially across depth under some
> held-out conditions. FIT-only featurewise recalibration can substantially
> restore performance in such cases, but this rescue is not uniformly
> reproducible across complementary data conditions.

- `PAPER_A_CORE_CLAIM = SUPPORTED_WITH_SCOPE_LIMITATIONS`

Reject stronger formulations: universal readout drift, robust general
calibration mechanism, general coordinate transport, functional control, or
behavioral steering mechanism.

### Evidence chain

- EXP-018: held-out local representational manipulability.
- EXP-017: representational intervention did not yield task-specific
  correctness-level behavioral advantage over matched random control.
- EXP-019: independent behavioral evaluator failed generalization, limiting
  behavioral interpretation.
- EXP-020A: larger-model replication of local representational manipulability.
- EXP-021: fixed source-semantic readout failed to remain uniformly qualified
  across depth.
- EXP-022A: discovery-stage featurewise calibration rescue.
- EXP-023: independent preregistered `NO_REPLICATION`, with one strong rescue
  split and one null split.

This is not a chain of uniformly positive experiments. The positive/negative
tension is part of the contribution.

## Paper and Venue Readiness

- `PAPER_A_DRAFT_READINESS = START_FIRST_DRAFT_NOW`
- `PAPER_A_SUBMISSION_READINESS = ONE_TARGETED_FOLLOWUP_RECOMMENDED`
- `TMLR_READINESS = CONDITIONAL_AFTER_TARGETED_FOLLOWUP`
- `NEURAL_NETWORKS_READINESS = CONDITIONAL_AFTER_TARGETED_FOLLOWUP`
- `CCF_A_TOP_CONFERENCE_READINESS = NOT_YET_SUFFICIENT_EVIDENCE`

CCF-A assessment is limited by one dominant model family, small controlled
dataset scale, absence of an independent susceptibility predictor, unresolved
split heterogeneity, and lack of general transport/function evidence.
`NO_REPLICATION` does not mean unpublishable.

## Recommended Next High-Information Question

At most one follow-up direction is recommended:

> Can an independent FIT-only or separately held-out diagnostic predict which
> conditions will exhibit deep fixed-readout degradation and therefore benefit
> from recalibration?

The future design must separate the susceptibility diagnostic from the
confirmatory EVAL partition so the predictor does not algebraically share the
outcome quantity.

Do not create or execute EXP-024 in this task.

## Scientific Labeling

- Observation: Split A/B exact balanced accuracy, effects, and tests above.
- Operational Result: `NO_REPLICATION`.
- Interpretation: calibration rescue appears condition-dependent rather than
  uniformly reproducible.
- Speculation: independent frame/readout mismatch diagnostics may predict
  calibration susceptibility.

## Research-State Updates

- `HYP-CALIBRATION-001`: downgraded from active high priority to
  `NOT_SUPPORTED_AS_GENERAL_CROSS_SPLIT_REPLICATION`.
- `HYP_CALIBRATION_CONDITIONAL_002`: new active prospective hypothesis.
- `HYP_MEAN_CALIBRATION_001`: subordinate hypothesis-generating-only entry.
- Claim ledger updated to preserve negative and conditional evidence.

## Next Task

Proceed to a bounded Paper-A first draft using the scope-limited core claim and
the above evidence chain. Do not automatically create EXP-024.
