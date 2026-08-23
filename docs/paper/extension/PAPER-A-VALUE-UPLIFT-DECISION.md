# Paper-A Prospective Value-Uplift Extension Decision

Status: `PA_VALUE_000_COMPLETE`
Task: `PA-VALUE-000`
Repository: `D:\Research\llm-representation-research`
Entry authority:
- `ENTRY_HEAD = 1054d570774aba6b8b4519641bb747e6af5c232a`
- `origin/main = 1054d570774aba6b8b4519641bb747e6af5c232a`
- `TREE_STATE = CLEAN_TRACKED_WITH_PREEXISTING_UNTRACKED_ARTIFACTS`
- `STAGING_STATE = EMPTY`

## 1. Purpose

This task decides whether Paper A should perform exactly one prospective
scientific extension before manuscript rewriting resumes. It is a
design-decision task only. No new scientific data, model inference, panel
generation, experiment execution, outcome exposure, or manuscript rewriting
was performed.

## 2. Frozen Paper A Baseline

Paper A already supports the following without any extension:

- Three-model `LEVEL_2` empirical dissociation among Qwen, OLMo, and Llama.
- All three models show positive depth-distance-associated fixed-readout
  compatibility structure.
- Qwen: `TARGET_DOMINANT + NOT_SUPPORTED` for simple LOW-D recalibratability.
- OLMo: `SOURCE_DOMINANT + SUPPORTED` for simple LOW-D recalibratability.
- Llama: `TARGET_DOMINANT + SUPPORTED` for simple LOW-D recalibratability.
- The Llama profile prospectively breaks a simple two-model mapping.
- Within the tested set, SDI and LOW-D are empirically non-redundant.
- A single scalar degradation/transfer score is insufficient for these
  measured properties.
- Carrier Comparability Rule is controlled across architectures.
- The EXP-023/EXP-024/EXP-025 negative/falsification lineage is visible.
- SemRF/Tuned-Lens differentiation is documented, with a moderate residual
  contribution: the cross-model profile dissociation.

These are already available benefits and are not counted as benefits of any
new experiment.

## 3. Current Paper A Value Gaps

| Gap | Description | Severity | Addressability |
| --- | --- | --- | --- |
| G1 PANEL/TASK DEPENDENCE | Profiles may be specific to the existing semantic panel. | MAJOR | REQUIRES_NEW_EVIDENCE |
| G2 DESCRIPTIVE-TAXONOMY RISK | Profiles may be mainly descriptive labels. | MODERATE | PARTIALLY_ADDRESSABLE_BY_WRITING; predictive evidence would help |
| G3 PREDICTIVE UTILITY | No demonstration that measured dimensions predict a consequence beyond distance-only description. | MAJOR | REQUIRES_NEW_EVIDENCE |
| G4 GENERALIZATION | Three models remain a narrow set. | MODERATE | PARTIALLY_ADDRESSABLE_BY_WRITING; not addressed by either offered route |
| G5 MECHANISM | No causal mechanism is established. | MAJOR | OUT_OF_SCOPE_FOR_PAPER_A |
| G6 PRACTICAL CONSEQUENCE | No demonstrated downstream utility. | MODERATE | OUT_OF_SCOPE_FOR_PAPER_A |

## 4. Route Comparison Summary

- `ROUTE_0_NO_EXTENSION`: viable fallback; manuscript revision alone can
  mitigate boundedness, descriptive-taxonomy framing, and generalization
  wording, but cannot close G1 or G3.
- `ROUTE_A_FRESH_CROSS_TASK_REPLICATION`: directly targets G1 and partially
  strengthens construct stability; clean Paper A measurement question; high
  negative-result value; low Paper B contamination risk.
- `ROUTE_B_HELD_OUT_PREDICTIVE_CONSEQUENCE`: would target G3 and G2, but as
  currently formulated is not clearly scientifically distinct from EXP-024
  and carries higher Paper B boundary risk.

## 5. Recommendation

- `PREFERRED_ROUTE = ROUTE_A_FRESH_CROSS_TASK_REPLICATION`
- `SECOND_BEST_ROUTE = NO_EXTENSION`

Scientific rationale:

The central Paper-A claim is a three-model empirical dissociation. The most
load-bearing remaining vulnerability is whether that dissociation is a
property of the current semantic panel rather than a stable measurement
phenomenon. A prospectively frozen, independent task/semantic panel directly
tests that vulnerability. Positive, negative, and ambiguous outcomes are all
scientifically interpretable, and the route does not import operator-complexity
science from Paper B.

Route A must keep frozen: models, carrier semantics, distance statistic,
source/target statistic, LOW-D definition, and routing logic. It must make
fresh: stimulus/task panel, item families, and FIT/DIAG/EVAL partitions where
applicable.

Route B is not selected at this time because the candidate outcome is not yet
specified distinctly from EXP-024's calibration-benefit endpoint. A richer
predictor applied to the same or a closely related endpoint would constitute a
post-hoc rescue risk. It is deferred, not redesigned.

## 6. Prior-Art Gate

The completed Paper-A audit did not deeply screen cross-task probe-portability
or profile-stability work. Therefore:

- `TARGETED_PRIOR_ART_UPDATE_REQUIRED = true`

This update is a precondition inside the next design task. It does not itself
create a new experiment.

## 7. Paper A vs Paper B Firewall

- Route A classification: `CLEAN_PAPER_A_EXTENSION`.
- Route B classification: `BOUNDARY_RISK` because "predictive consequence"
  can drift toward transformation/operator-complexity science unless the
  outcome is explicitly a Paper-A measurement consequence.
- `EXP028_MODIFIED = false`

## 8. One-Extension Rule

- `ONE_EXTENSION_RULE = PASS`
- At most one extension is authorized.
- Route B is only future work, not an immediate second extension.

## 9. Hard Flags

- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `NEW_EXPERIMENT_PERFORMED = false`
- `NEW_MODEL_INFERENCE_PERFORMED = false`
- `EXP028_MODIFIED = false`
- `REAL_EXP028_INPUT_PANEL_CREATED = false`
- `REAL_EXP028_MODEL_INFERENCE_PERFORMED = false`
- `EXP028_AUTHORIZATION_CREATED = false`
- `EXP028_RESULT_CREATED = false`

## 10. Next Task

`PA-EXT-A-001_PROSPECTIVE_CROSS_TASK_REPLICATION_PROTOCOL_DESIGN`

The next task must address G1 exactly: determine whether the registered
cross-depth compatibility profiles retain their organization under a
prospectively frozen, independent task/semantic panel. It must not write the
protocol yet.

## 11. Final Flags

- `PA_VALUE_000_STATUS = COMPLETE`
- `ROUTE_0_VERDICT = NOT_PREFERRED`
- `ROUTE_A_VERDICT = ELIGIBLE`
- `ROUTE_A_EXPECTED_VALUE = MODERATE`
- `ROUTE_A_NEGATIVE_RESULT_VALUE = HIGH`
- `ROUTE_A_PAPER_B_CONTAMINATION = NONE`
- `ROUTE_B_VERDICT = INELIGIBLE_POST_HOC_RESCUE`
- `ROUTE_B_EXPECTED_VALUE = LOW`
- `ROUTE_B_EXP024_DISTINCTNESS = FAIL`
- `ROUTE_B_NEGATIVE_RESULT_VALUE = MODERATE`
- `TARGETED_PRIOR_ART_UPDATE_REQUIRED = true`
- `PREFERRED_ROUTE = ROUTE_A_FRESH_CROSS_TASK_REPLICATION`
- `SECOND_BEST_ROUTE = NO_EXTENSION`
- `ONE_EXTENSION_RULE = PASS`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `NEW_EXPERIMENT_PERFORMED = false`
- `NEW_MODEL_INFERENCE_PERFORMED = false`
- `EXP028_MODIFIED = false`