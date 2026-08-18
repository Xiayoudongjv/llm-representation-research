# Paper A Post-Revision Reviewer Re-evaluation

This is Task-099D, a narrow independent re-review of the revised Paper-A
manuscript. It checks only whether Task-099C resolved the Task-099B rejection
reasons. It does not re-audit the dataset, runtime, prior-art landscape, or
protocol.

## 1. Executive Verdict

- `REVISED_MANUSCRIPT_VERDICT = BORDERLINE`
- `REVIEW_CONFIDENCE = MEDIUM`
- The scientific wording and evidence boundaries are now substantially improved.
- No remaining major scientific issue rises to `STILL_MAJOR`.
- The two remaining partial issues are production-asset and bibliography
  verification tasks, not scientific blockers.
- The manuscript is reviewable and can proceed to figure/table/reference
  finalization.

## 2. 099B Major-Issue Resolution Audit

| Issue ID | 099B concern | 099C change | Reviewer verification | Remaining concern | Final status |
| --- | --- | --- | --- | --- | --- |
| M1 | Central claim blurred formal vs descriptive support | Narrowed and locked the central claim | Abstract, Introduction, Results, and Conclusion now consistently use bounded language; formal vs descriptive distinction is explicit | None | RESOLVED |
| M2 | Top prior works and citations were TODO/unverified | Added prior-art-aware references 1-11 | Tuned Lens, stitching, and direct neighbors are now positioned in Related Work; metadata still needs primary-source final verification | `REFERENCE_VERIFICATION_PENDING` | PARTIALLY_RESOLVED_NONBLOCKING |
| M3 | Main figures absent | Added evidence-summary table and explicit figure plan | The scientific figure plan is production-ready, but actual rendered figures are still pending | `FIGURE_ASSET_PENDING` | PARTIALLY_RESOLVED_NONBLOCKING |
| M4 | Abstract/Introduction gap overgeneralized prior-work assumptions | Rewrote Abstract and Introduction | The revised text no longer claims "first", "prior work assumes stable", or "unlike all previous work" | None | RESOLVED |
| M5 | Reproducibility details underspecified | Added counts, class mapping, data separation, and inference details | Methods now provide a paper-level reproducible account without engineering audit history | None | RESOLVED |

### Resolution Summary

- `MANUSCRIPT_SCIENCE_RESOLVED = true`
- `PRODUCTION_ASSET_PENDING = true` for actual rendered figures
- `REFERENCE_VERIFICATION_PENDING = true` for final bibliography metadata
- `SCIENTIFIC_CLAIM_GAP = false`
- `WRITING_CLARITY = false`
- `METHODS_DETAIL_PENDING = false`
- `OTHER = false`

## 3. Central Claim

- `CENTRAL_CLAIM_VERDICT = ACCEPTABLE`
- Title remains appropriately bounded.
- Abstract explicitly concedes layer-specific readout adaptation is prior art.
- Introduction contributions are framed as measurement, evidence, and negative
  replication contributions.
- Results do not restate a stronger claim than the bounded central claim.
- Discussion and Conclusion remain consistent with `NO_REPLICATION` and
  `NOT_SUPPORTED`.
- Conclusion does not re-strengthen the Abstract.

The locked claim:

> Fixed semantic readouts can lose compatibility across Transformer depth under
> held-out evaluation. Low-capacity FIT-only featurewise recalibration can
> restore substantial readout performance in multiple tested conditions,
> although the effect is heterogeneous across datasets and splits. Moreover, a
> preregistered independent measure of fixed-readout degradation did not
> reliably predict the magnitude of calibration benefit.

is supported by the visible evidence chain.

## 4. Novelty Positioning

- `NOVELTY_POSITIONING_VERDICT = DEFENSIBLE_BUT_INCREMENTAL_WELL_POSITIONED`
- The revised manuscript explicitly does not claim:
  - affine calibration novelty
  - layer-specific readout novelty
  - model-stitching novelty
  - representation-alignment theory novelty
- The contribution is correctly placed on:
  - fixed-readout compatibility measurement
  - held-out empirical design
  - source-family separation
  - replication/non-replication sequence
  - independent DIAGNOSTIC/EVAL
  - preregistered susceptibility test

This is prior-art-aware incremental positioning and is acceptable.

## 5. Negative Results and Boundaries

- `NEGATIVE_RESULT_FRAMING = CLEAR`
- `BEHAVIORAL_BOUNDARY = CLEAR`
- EXP-023 is presented as a main result with `NO_REPLICATION`, not as
  "heterogeneity only".
- EXP-024 explicitly separates:
  - descriptive `S_diag > 0` in 10/10 conditions
  - descriptive `G_eval > 0` in 10/10 conditions
  - registered primary `NOT_SUPPORTED` with full `rho` and exact `p`
- The reader is not left with "overall calibration successfully replicated".
- EXP-017/EXP-019 function as boundary evidence in Results and Discussion,
  not merely Limitations.

### Claim-Evidence Spot Check

| Manuscript claim | Matrix status | Spot-check verdict |
| --- | --- | --- |
| Local representation-level manipulability | `SUPPORTED_WITH_SCOPE_LIMITATIONS` | SUPPORTED_WITH_SCOPE_LIMITATION |
| Same-family larger-model representation replication | `SUPPORTED` | SUPPORTED |
| Manipulability does not imply behavioral control | `SUPPORTED_NEGATIVE_BOUNDARY` | SUPPORTED_WITH_SCOPE_LIMITATION |
| Fixed readout compatibility is depth/condition dependent | `SUPPORTED_WITH_SCOPE_LIMITATIONS` | SUPPORTED_WITH_SCOPE_LIMITATION |
| Featurewise recalibration can rescue some degraded readouts | `CONDITIONAL_SIGNAL` | DESCRIPTIVE_ONLY for breadth; SUPPORTED for one formal split-level case |
| General cross-split replication unsupported | `SUPPORTED_NEGATIVE` | SUPPORTED |
| Simple susceptibility predictor unsupported | `HYPOTHESIS_GENERATING / SIMPLE_PREDICTOR_NOT_SUPPORTED` | SUPPORTED |
| Mean/scale decomposition secondary | `SECONDARY_DESCRIPTIVE` | DESCRIPTIVE_ONLY |
| Calibration recovery does not imply information preservation | boundary claim | SUPPORTED_WITH_SCOPE_LIMITATION |
| Behavioral control not established | `SUPPORTED_NEGATIVE_BOUNDARY` | SUPPORTED |
| Functional binding not tested | matrix boundary | NOT_TESTED |
| Coordinate transport not tested | matrix boundary | NOT_TESTED |

No `CLAIM_MATRIX_MANUSCRIPT_DRIFT` was found.

## 6. Statistical Exposition

- `STATISTICAL_EXPOSITION = CLEAR`
- The revised manuscript separates:
  - `1760 records`
  - `880 source families`
  - `10 primary inferential conditions`
- It explicitly states `N = 10` for the primary Spearman/permutation test.
- It preserves:
  - `rho = 0.28401877872187725`
  - exact one-sided `p = 0.2115079365079365`
  - `PRIMARY_SUPPORTED = false`
- No language such as "trend", "near significance", "partial support", or
  "power excuse" is used to soften the primary negative.
- The `10/10 G_eval` positivity is labeled panel-bounded descriptive only.

## 7. Methods Reproducibility

- `REPRODUCIBILITY_VERDICT = ADEQUATE`
- Paper-level reproducibility is now adequate: model name/snapshot, checkpoint
  semantics, local-only model/tokenizer loading, four semantic classes, class
  mapping, FIT/DIAGNOSTIC/EVAL separation, `C_ref`, calibration variants,
  `S_diag`, `G_eval`, Spearman, exact permutation, alpha/support rule, and
  evidence-summary table are present.
- No internal authorization/task/commit audit history is required or used as a
  substitute for scientific methods.

## 8. Results Structure

- `RESULTS_STRUCTURE = SCIENTIFIC_ARGUMENT`
- Results now proceed by scientific question:
  1. local representational manipulability
  2. behavioral boundary
  3. fixed-readout degradation
  4. recalibration and heterogeneity
  5. failed prospective susceptibility prediction
- Experiment IDs are used as evidence references, not as the section structure.

## 9. Figures and References

### Figures

- `FIGURE_PLAN_VERDICT = READY_FOR_PRODUCTION`
- The plan requires:
  - EXP-023 split heterogeneity and `NO_REPLICATION` visible
  - EXP-024 all 10 conditions visible
  - `rho`, exact `p`, and `NOT_SUPPORTED` visible
  - panel-bounded positivity visually separated from weak predictiveness
- Actual rendered figures remain pending, but this does not alter the current
  scientific verdict.

### References

- `REFERENCE_POSITIONING = POSITIONING_READY_METADATA_PENDING`
- Critical prior art is positioned correctly.
- Final author/venue/year/DOI/bibliography verification remains pending for
  submission formatting.
- Reference positioning is not a novelty failure.

## 10. Remaining Risks

- `TOP_REMAINING_ACCEPTANCE_RISK = incremental one-model contribution with an unsupported simple susceptibility predictor; the manuscript must rely on transparent bounded framing rather than mechanism or generality`
- Other nonblocking risks:
  - actual figure production has not occurred yet
  - bibliography metadata is not final-verified
  - cross-model generality remains untested and is correctly limited

No remaining risk is a `NEW_EXPERIMENT_REQUIRED` scientific blocker.

## 11. Venue Readiness

| Venue | Current scientific readiness | Main remaining gap |
| --- | --- | --- |
| TMLR | MEDIUM | Final figures/tables and bounded contribution framing |
| Neural Networks | MEDIUM | Need finished figures and sharper layerwise/readout positioning |
| Stronger conference / CCF-A-like | LOW | Incremental contribution and one-model evidence likely insufficient |

Venue ambition does not change the core-claim validity.

## 12. Experiment Necessity

- `NEW_EXPERIMENT_REQUIRED_FOR_CORE_CLAIM = false`
- `SECOND_MODEL_REPLICATION = OPTIONAL_FOR_BREADTH`
- No new scientific blocker was discovered.
- The remaining issues are figure/table and reference-verification production
  tasks.
- Experiment line remains closed.

## 13. Final Reviewer Verdict

- `REVISED_MANUSCRIPT_VERDICT = BORDERLINE`
- `REVIEW_CONFIDENCE = MEDIUM`
- `NEXT_TASK = 099E_FIGURE_TABLE_AND_REFERENCE_FINALIZATION`

The revised manuscript has addressed the original scientific rejection reasons.
It is not yet submission-ready, but it is ready for figure/table and reference
finalization.

### Required Flags

- `PAPER_A_099D_POST_REVISION_REREVIEW_COMPLETE = true`
- `PAPER_A_099D_REVISED_MANUSCRIPT_VERDICT = BORDERLINE`
- `PAPER_A_099D_REVIEW_CONFIDENCE = MEDIUM`
- `PAPER_A_099D_CENTRAL_CLAIM_VERDICT = ACCEPTABLE`
- `PAPER_A_099D_NOVELTY_POSITIONING_VERDICT = DEFENSIBLE_BUT_INCREMENTAL_WELL_POSITIONED`
- `PAPER_A_099D_NEGATIVE_RESULT_FRAMING = CLEAR`
- `PAPER_A_099D_BEHAVIORAL_BOUNDARY = CLEAR`
- `PAPER_A_099D_STATISTICAL_EXPOSITION = CLEAR`
- `PAPER_A_099D_REPRODUCIBILITY_VERDICT = ADEQUATE`
- `PAPER_A_099D_RESULTS_STRUCTURE = SCIENTIFIC_ARGUMENT`
- `PAPER_A_099D_TUNED_LENS_POSITIONING = CLEAR`
- `PAPER_A_099D_MODEL_STITCHING_POSITIONING = CLEAR`
- `PAPER_A_099D_MAJOR_ISSUES_RESOLVED = 3`
- `PAPER_A_099D_MAJOR_ISSUES_PARTIAL_NONBLOCKING = 2`
- `PAPER_A_099D_MAJOR_ISSUES_STILL_MAJOR = 0`
- `PAPER_A_099D_FIGURE_PLAN_VERDICT = READY_FOR_PRODUCTION`
- `PAPER_A_099D_REFERENCE_POSITIONING = POSITIONING_READY_METADATA_PENDING`
- `PAPER_A_099D_TRANSPORT_OVERCLAIM_FOUND = false`
- `PAPER_A_099D_FUNCTIONAL_OVERCLAIM_FOUND = false`
- `PAPER_A_099D_BEHAVIORAL_OVERCLAIM_FOUND = false`
- `PAPER_A_099D_NEW_EXPERIMENT_REQUIRED_FOR_CORE_CLAIM = false`
- `PAPER_A_099D_SECOND_MODEL_REPLICATION = OPTIONAL_FOR_BREADTH`
- `PAPER_A_099D_TOP_REMAINING_RISK = incremental one-model contribution and pending figure/reference finalization`
- `PAPER_A_099D_NEXT_TASK = 099E_FIGURE_TABLE_AND_REFERENCE_FINALIZATION`

Task 099D stops here. Do not automatically modify the manuscript, produce
figures, or design an experiment.
