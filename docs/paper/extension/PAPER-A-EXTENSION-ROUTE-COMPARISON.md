# Paper-A Extension Route Comparison

Status: `PA_VALUE_000_ROUTE_COMPARISON`
Predecessor decision: `PA_VALUE_000_COMPLETE`

## 1. Candidate Routes

- `ROUTE_0_NO_EXTENSION`
- `ROUTE_A_FRESH_CROSS_TASK_REPLICATION`
- `ROUTE_B_HELD_OUT_PREDICTIVE_CONSEQUENCE`

No fourth route was introduced.

## 2. Value/Cost/Risk Matrix

Qualitative only. No fake numeric precision.

| Dimension | ROUTE_0 | ROUTE_A | ROUTE_B |
| --- | --- | --- | --- |
| SCIENTIFIC_VALUE_GAIN | NONE | MODERATE | HIGH_IF_DISTINCT |
| NOVELTY_GAIN | NONE | LOW | MODERATE_IF_DISTINCT |
| SIGNIFICANCE_GAIN | NONE | LOW | HIGH_IF_DISTINCT |
| GENERALIZATION_GAIN | NONE | MODERATE_TASK_LEVEL | NONE |
| CONSTRUCT_VALIDITY_GAIN | NONE | HIGH | MODERATE |
| PREDICTIVE_VALUE_GAIN | NONE | NONE | HIGH_IF_DISTINCT |
| SCOPE_EXPANSION | NONE | MODERATE | MODERATE |
| POST_HOC_RISK | NONE | LOW | HIGH |
| PAPER_B_CONTAMINATION_RISK | NONE | NONE | MODERATE |
| IMPLEMENTATION_COST | NONE | HIGH | HIGH |
| INTERPRETABILITY_IF_NEGATIVE | HIGH | HIGH | MODERATE |

## 3. Route A Detailed Assessment

Candidate question: Do the registered cross-depth compatibility profiles
observed in the current semantic panel retain their organization under a
prospectively frozen, independent task/semantic panel?

What stays frozen:
- models
- carrier semantics
- distance statistic
- source/target statistic
- LOW-D definition
- routing logic

What must be fresh:
- stimulus/task panel
- item families
- FIT/DIAG/EVAL partitions where applicable

Prospective outcomes, without privileging replication:
- `STABLE_PROFILE_STRUCTURE`
- `PARTIALLY_TASK_CONDITIONAL_PROFILE`
- `MODEL_BY_TASK_PROFILE_INTERACTION`
- `NO_CROSS_TASK_STABILITY`
- `INVALID_OR_UNADJUDICATED`

Positive outcome: the three-model dissociation is not merely an artifact of
one semantic panel; it generalizes at least to a second prospectively frozen
task family.

Negative outcome: profile organization is task-conditional, which is an
important boundary on the current empirical claim and is still publishable.

Ambiguous outcome: model-by-task interaction indicates that the measured
dimensions are neither universal nor purely panel-specific, motivating future
conditional work without Paper A overclaiming.

Route A does not establish mechanism, transport, invariance, or functional
binding.

## 4. Route B Detailed Assessment

Candidate question: Does a prospectively frozen multidimensional compatibility
description provide held-out predictive information about a cross-layer
measurement consequence beyond a distance-only baseline?

EXP-024 anti-rescue firewall comparison:

| Element | EXP-024 | Route B as currently formulated |
| --- | --- | --- |
| Predictor | Simple `S_diag(c)` degradation magnitude | Multidimensional profile description |
| Outcome | `G_eval(c)` calibration benefit | "cross-layer measurement consequence"; not yet frozen |
| Unit | Condition | Not yet frozen |
| Model scope | One model/panel | Not yet frozen |
| Data | DIAGNOSTIC/EVAL condition panel | Not yet frozen |
| Hypothesis | degradation magnitude predicts calibration benefit | not yet formally stated |
| Statistical test | Spearman exact permutation | not yet frozen |
| Decision rule | `rho > 0 AND p <= 0.05` | not yet frozen |

Because the outcome and unit are unspecified, a richer predictor could be
applied to the same calibration-benefit endpoint and become a post-hoc rescue
of EXP-024. Until a clearly distinct, preregistered cross-layer measurement
consequence is specified, Route B fails the anti-rescue firewall.

- `ROUTE_B_EXP024_DISTINCTNESS = FAIL`
- `ROUTE_B_VERDICT = INELIGIBLE_POST_HOC_RESCUE`

Route B may be revisited only as explicitly deferred future work with a
distinct outcome.

## 5. Prior-Art Collision Check

The completed Paper-A prior-art audit screened fixed-readout, source/target
matrices, distance effects, recalibration, stitching, and SemRF/Tuned Lens.
It did not deeply screen:

- cross-task stability of layerwise probe/readout transfer
- probe portability across task families
- profile construction under task distribution shift

Therefore:
- `TARGETED_PRIOR_ART_UPDATE_REQUIRED = true`

This is a precondition for the Route A protocol-design task. It is not a full
new literature review in this decision task.

## 6. Paper A vs Paper B Firewall

- `ROUTE_A = CLEAN_PAPER_A_EXTENSION`
- `ROUTE_B = BOUNDARY_RISK`
- `ROUTE_0 = CLEAN`

Any route classified as `PAPER_B_CONTAMINATION` is ineligible. Route B is not
currently promoted for this reason in addition to the anti-rescue firewall.

## 7. One-Extension Rule

- `ONE_EXTENSION_RULE = PASS`
- Paper A may perform at most one extension.
- Route B is deferred future work, not a second current extension.

## 8. Final Routing

- `PREFERRED_ROUTE = ROUTE_A_FRESH_CROSS_TASK_REPLICATION`
- `SECOND_BEST_ROUTE = NO_EXTENSION`
- Next task if Route A proceeds: `PA-EXT-A-001_PROSPECTIVE_CROSS_TASK_REPLICATION_PROTOCOL_DESIGN`