# Paper A Adversarial Scientific Review

This is Task 099B, a read-only adversarial scientific review of the current
`PAPER-A-FIRST-FULL-DRAFT.md`. It is not a revision. It accepts Task-099B-0's
novelty baseline and attacks the manuscript from a Transformer representation,
probing, Tuned Lens, model stitching, alignment, and mechanistic
interpretability reviewer perspective.

## 1. Executive Verdict

- `CURRENT_DRAFT_VERDICT = WEAK_REJECT`
- `REVIEW_CONFIDENCE = MEDIUM`
- `CENTRAL_CLAIM_VERDICT = NEEDS_NARROWING`
- `NOVELTY_VERDICT = DEFENSIBLE_BUT_INCREMENTAL_NEEDS_REFRAMING`
- `GAP_STATEMENT_VERDICT = NEEDS_NARROWING`
- `ABSTRACT_VERDICT = MINOR_REVISION`
- `REPRODUCIBILITY_VERDICT = MINOR_GAPS`
- `MAIN_FIGURES_VERDICT = MISSING_CRITICAL_FIGURE`
- `ENGINEERING_DETAIL_LEVEL = APPROPRIATE`

The evidence chain is honest and the negative results are visible. The current
draft is not ready for submission mainly because the main figures/tables and
verified references do not yet exist in the manuscript, the novelty frame still
needs tightening, and the central claim occasionally blurs formal support with
descriptive evidence. These are major but manuscript-fixable issues; no new
experiment is required.

### Required Flags

- `PAPER_A_099B_ADVERSARIAL_REVIEW_COMPLETE = true`
- `PAPER_A_099B_CURRENT_DRAFT_VERDICT = WEAK_REJECT`
- `PAPER_A_099B_REVIEW_CONFIDENCE = MEDIUM`
- `PAPER_A_099B_CENTRAL_CLAIM_VERDICT = NEEDS_NARROWING`
- `PAPER_A_099B_NOVELTY_VERDICT = DEFENSIBLE_BUT_INCREMENTAL_NEEDS_REFRAMING`
- `PAPER_A_099B_GAP_STATEMENT_VERDICT = NEEDS_NARROWING`
- `PAPER_A_099B_ABSTRACT_VERDICT = MINOR_REVISION`
- `PAPER_A_099B_REPRODUCIBILITY_VERDICT = MINOR_GAPS`
- `PAPER_A_099B_MAIN_FIGURES_VERDICT = MISSING_CRITICAL_FIGURE`
- `PAPER_A_099B_ENGINEERING_DETAIL_LEVEL = APPROPRIATE`
- `PAPER_A_099B_BLOCKING_ISSUE_COUNT = 0`
- `PAPER_A_099B_MAJOR_ISSUE_COUNT = 5`
- `PAPER_A_099B_MINOR_ISSUE_COUNT = 4`
- `PAPER_A_099B_EXP023_NEGATIVE_VISIBLE = true`
- `PAPER_A_099B_EXP024_PRIMARY_NEGATIVE_VISIBLE = true`
- `PAPER_A_099B_BEHAVIORAL_BOUNDARY_VISIBLE = true`
- `PAPER_A_099B_TUNED_LENS_POSITIONING = CLEAR`
- `PAPER_A_099B_MODEL_STITCHING_POSITIONING = CLEAR`
- `PAPER_A_099B_TRANSPORT_OVERCLAIM_FOUND = false`
- `PAPER_A_099B_FUNCTIONAL_OVERCLAIM_FOUND = false`
- `PAPER_A_099B_NEW_EXPERIMENT_REQUIRED_FOR_CORE_CLAIM = false`
- `PAPER_A_099B_SECOND_MODEL_REPLICATION = OPTIONAL_FOR_BREADTH`
- `PAPER_A_099B_HIGHEST_PRIORITY_REVISION = core claim scope`
- `PAPER_A_099B_NEXT_TASK = 099C_MANUSCRIPT_REVISION`

## 2. Reviewer First Impression

- `REVIEWER_ONE_SENTENCE_SUMMARY`:
  The paper reports a controlled, preregistered chain showing that fixed
  semantic readouts can degrade across Transformer depth and that low-capacity
  FIT-only featurewise recalibration gives condition-dependent rescue, but the
  simple prospective degradation-magnitude predictor is not supported.
- `REVIEWER_ONE_SENTENCE_REJECT_RISK`:
  A reviewer could reject this as an incremental, one-model-family empirical
  observation whose primary mechanistic predictor is null and whose
  contribution is not yet sufficiently distinguished from Tuned Lens/model
  stitching/alignment work.

The strongest positive evidence is the combination of EXP-022A discovery
recovery and EXP-023 Split A formal rescue. The strongest negative evidence is
the EXP-023 `NO_REPLICATION` outcome and the EXP-024 exact-permutation primary
failure. The largest scientific weakness is that the current manuscript
demonstrates condition-dependent phenomena without resolving what governs the
heterogeneity.

## 3. Central Claim Audit

The manuscript's central claim is:

> Fixed semantic readouts can lose compatibility across Transformer depth.
> Low-capacity FIT-only featurewise recalibration can substantially restore
> readout performance under multiple held-out conditions, but the benefit is
> not uniformly reproducible across data conditions and is not reliably
> predicted by a simple independent measure of fixed-readout degradation
> magnitude.

| Claim component | Verdict | Basis |
| --- | --- | --- |
| Fixed readouts can lose compatibility across depth | `SUPPORTED_WITH_SCOPE_LIMITATIONS` | EXP-021 did not remain qualified at deep checkpoints; EXP-022A/EXP-023 show depth-dependent A0 drops in at least some splits/conditions. |
| FIT-only featurewise recalibration can substantially restore readout performance under multiple held-out conditions | `DESCRIPTIVE_ONLY` for the multi-condition breadth, `SUPPORTED` for one formal split-level case | EXP-022A is discovery/descriptive; EXP-023 has one formal supported split; EXP-024 10/10 is descriptive panel evidence only. The phrase "multiple held-out conditions" needs formal-vs-descriptive qualification. |
| Benefit is not uniformly reproducible | `SUPPORTED` | EXP-023 `NO_REPLICATION` with Split A rescue and Split B null. |
| Simple degradation magnitude does not reliably predict calibration benefit | `SUPPORTED` | EXP-024 primary `rho = 0.28401877872187725`, exact one-sided `p = 0.2115079365079365`, support false. |

- `CENTRAL_CLAIM_VERDICT = NEEDS_NARROWING`
- The last two components are faithful. The second component is the main
  overreach: "under multiple held-out conditions" could be read as formal
  multi-condition support when much of that support is descriptive or limited
  to one formal split-level case.

## 4. Novelty Audit After 099B-0

- Task-099B-0 verdict accepted: `DEFENSIBLE_BUT_INCREMENTAL`
- This review upholds that baseline but finds the manuscript positioning still
  needs revision.
- `NOVELTY_VERDICT = DEFENSIBLE_BUT_INCREMENTAL_NEEDS_REFRAMING`
- `PRIMARY_NOVELTY_TYPE = EMPIRICAL_DESIGN_NOVELTY + NEGATIVE_EVIDENCE_CONTRIBUTION`

The manuscript already correctly states that "different layers may benefit from
different affine readouts" is prior art. However, the Abstract and Introduction
still open with a broad "many representational analyses apply fixed probes or
readouts as though the coordinate system were stable" framing. A Tuned
Lens/model-stitching-aware reviewer can attack that gap as overstated. The
paper should lead with its specific empirical design and negative-evidence
chain.

## 5. Claim?Evidence Mismatches

- `MAJOR`: The central-claim phrase "can substantially restore readout
  performance under multiple held-out conditions" is broader than the formal
  evidence. It should separate one formal split-level rescue from descriptive
  multi-condition observations.
- `MINOR`: Conclusion says "Simple FIT-only featurewise recalibration can often
  recover readout utility." `often` is not established by a formal count or
  population claim; prefer "in several observed conditions" or "descriptively".
- `MINOR`: Introduction says representations "can change in both geometry and
  information content." This is acceptable as motivation but should be marked
  as a general framing, not a result of this paper.
- `MINOR`: EXP-021 is an engineering measurement-qualification result; the
  manuscript does label it as such, but the phrase "Fixed readout accuracy can
  drop substantially across depth" should continue to cite it only as
  qualification evidence, not as a formal scientific degradation test.

No mismatch was found for the negative outcomes themselves. EXP-023 and EXP-024
are represented accurately.

## 6. Negative-Result Visibility

- `EXP023_NEGATIVE_VISIBLE = true`
  Abstract states `NO_REPLICATION`; Results state the registered outcome and
  explain why Split B is a null rescue, not partial replication; Discussion
  and Conclusion preserve the heterogeneity.
- `EXP024_PRIMARY_NEGATIVE_VISIBLE = true`
  Abstract reports `NOT_SUPPORTED`, `rho`, and `p`; Results give the full
  support rule and label `HYP_CALIBRATION_CONDITIONAL_002` as
  `NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`.
- `BEHAVIORAL_BOUNDARY_VISIBLE = true`
  EXP-017/EXP-019 negative evidence is in Results 4.2 and Discussion 5.5,
  and behavioral control is explicitly disclaimed.
- `NEGATIVE_RESULT_FRAMING = HONEST`
- `EXP-024 10/10 positivity` is correctly labeled descriptive and not used as
  a replacement primary test.

## 7. Statistical and Inferential Audit

The primary statistical design is clearly stated: unit is condition, `N = 10`,
Spearman correlation, one-sided exact permutation over all `10!` orderings, and
registered support rule `rho > 0 AND p <= 0.05`.

Strengths:
- The manuscript avoids treating the large record/source-family construction as
  the inferential sample; the primary unit is explicitly the condition.
- Exact one-sided `p = 0.2115079365079365` is reported and correctly not
  labeled significant.
- The 10/10 positive panel observations are explicitly descriptive only.

Gaps:
- Record counts, source-family counts, and dataset sizes are not stated in the
  manuscript. Adding `1760 records`, `880 source families`, and `10 conditions`
  would improve transparency without creating false power.
- Tie handling for the Spearman correlation and exact permutation is referenced
  only indirectly by "substantial ties" in Limitations. The main text should
  state the tie method and whether the primary statistic used the same tie
  handling as the preregistration.
- The exact permutation and one-sided direction are clear, but the manuscript
  should state that inference is fixed-panel/condition-level and does not
  generalize to a population of transformations.

`STATISTICAL_EXPOSITION_VERDICT = MINOR_GAPS`

## 8. Methods and Reproducibility

The manuscript includes model snapshot, hidden-state tuple semantics, semantic
classes, FIT/DIAGNOSTIC/EVAL separation, `C_ref`, frozen scaler, featurewise
recalibration formulas, EXP-024 primary design, and primary inference.

`REPRODUCIBILITY_VERDICT = MINOR_GAPS`

Missing or underspecified from the manuscript alone:
- Exact dataset sizes and source-family counts.
- Class-to-label mapping and construction rules for the four semantic classes.
- Classifier optimization details, regularization strength, convergence rule,
  random seed, and whether the seed is frozen.
- Exact balanced-accuracy implementation and treatment of malformed outputs.
- Tie method for Spearman and permutation inference.
- Data/code availability statement.

These are minor because the design is unusually well specified for a first full
draft, but they should be closed before submission.

## 9. Prior-Art Positioning

For each of Task-099B-0's Top-5 direct prior works:

| Prior work | Most vulnerable manuscript claim | Required revision type |
| --- | --- | --- |
| Tuned Lens | "Fixed semantic readouts can lose compatibility across depth" appears as if it could be the main novelty. | `CLAIM_NARROWING`; explicitly concede layer-specific affine decoding is established. |
| Revisiting Model Stitching | "Featurewise recalibration can restore readout performance" overlaps with simple adapter recovery. | `REFERENCE_POSITIONING`; distinguish within-model fixed readout calibration from cross-model stitching. |
| Similarity and Matching of Neural Network Representations | "Featurewise recalibration" sits in the broad representation-matching lineage. | `REFERENCE_POSITIONING`; cite and narrow. |
| Functional Alignment Can Mislead | "Readout recovery is not representation equivalence" is correct but currently has only a TODO citation. | `REFERENCE_POSITIONING`; verify and cite. |
| Tracing Representation Progression | "Depth-wise fixed-readout compatibility measurement" could look like a broad progression claim. | `CLAIM_NARROWING`; scope to the frozen protocol and condition panel. |

- `TUNED_LENS_POSITIONING = CLEAR`
- `MODEL_STITCHING_POSITIONING = CLEAR`

The prose conceptually distinguishes Paper-A from both Tuned Lens and model
stitching. The remaining problem is citation completion and tightening the
Abstract/Introduction gap language.

## 10. Figures and Tables

- `MAIN_FIGURES_VERDICT = MISSING_CRITICAL_FIGURE`
- The manuscript currently contains only TODO placeholders and one
  condition-level table. The figure plan is good, but the draft itself has no
  actual figures.
- Most important figure/table changes:
  1. Create the EXP-023 figure showing Split A rescue, Split B null rescue, and
     the explicit `NO_REPLICATION` classification.
  2. Create the EXP-024 scatter of `S_diag(c)` vs `G_eval(c)` with all 10
     labeled conditions, plus a paired panel showing 10/10 positivity without
     hiding the weak rank association.
  3. Add one main evidence-summary table with columns: Experiment, Question,
     Design, Primary result, Interpretation, Boundary. This table should
     emphasize scientific progression, not engineering chronology.

## 11. Discussion and Limitations

The Discussion is unusually disciplined:
- It separates observation, operational interpretation, negative mechanism
  result, open mechanism, theoretical boundaries, and measurement-resolution
  limitation.
- It correctly states readout recovery is not representation equivalence.
- It does not turn the failed predictor into a general mechanism claim.

Weaknesses:
- The Conclusion's "often recover readout utility" is broader than the formal
  evidence.
- The Limitations list is strong but the broadest Introduction/Abstract
  sentences should already be scoped; limitations should not be the first
  place the reader learns the main evidence is one model family.
- "This suggests" is not aggressively converted to "therefore" in this draft,
  which is a strength.

## 12. Venue Assessment

| Venue | Scientific fit | Novelty fit | Evidence sufficiency | Current manuscript readiness |
| --- | --- | --- | --- | --- |
| TMLR | STRONG | CONDITIONAL | ADEQUATE for bounded claim | MAJOR_REVISION |
| Neural Networks | CONDITIONAL | CONDITIONAL | ADEQUATE with better figures/table | MAJOR_REVISION |
| Stronger conference / CCF-A-like | CONDITIONAL | WEAK | INSUFFICIENT without mechanism or broader validation | WEAK_REJECT |

No acceptance probabilities are assigned. Venue prestige does not change the
scientific result.

## 13. New-Experiment Necessity

- `IS_NEW_EXPERIMENT_REQUIRED_TO_SUPPORT_CURRENT_CORE_CLAIM = false`
- `NEW_EXPERIMENT_REQUIRED_FOR_CORE_CLAIM = false`
- The core claim can be made honest through claim narrowing and manuscript
  revision. The negative primary is a valid scientific result and is not a
  reason to launch a rescue experiment.
- `SECOND_MODEL_REPLICATION = OPTIONAL_FOR_BREADTH`
- Specific reviewer objection it would address: "The observed calibration
  benefit and null susceptibility predictor may be specific to Qwen3-1.7B."
  It is optional because the current bounded claim already limits generality to
  the studied model family.

## 14. Blocking Issues

`BLOCKING_ISSUE_COUNT = 0`

No issue requires new data or cannot be resolved by manuscript, figure/table,
reference, claim-scope, or methods-clarification changes.

## 15. Major Issues

`MAJOR_ISSUE_COUNT = 5`

1. `M1` `CLAIM_NARROWING` ? Central claim's "under multiple held-out
   conditions" must separate formal split-level support from descriptive
   multi-condition evidence.
2. `M2` `REFERENCE_POSITIONING` ? Top prior works and critical citations are
   still TODO/unverified in the manuscript.
3. `M3` `FIGURE_TABLE_ONLY` ? Main figures are absent; EXP-023 heterogeneity
   and EXP-024 all-10 scatter are not yet visible.
4. `M4` `MANUSCRIPT_ONLY` ? Abstract/Introduction gap opens with an
   overgeneralized "fixed probes/readouts as though the coordinate system were
   stable" framing.
5. `M5` `METHODS_REPRODUCIBILITY` ? Dataset sizes, class mapping,
   optimization/seed details, tie handling, and data/code availability are
   underspecified.

## 16. Minor Issues

`MINOR_ISSUE_COUNT = 4`

1. Conclusion says "often recover" without formal frequency/population support.
2. Results still use experiment IDs as section anchors more than ideal; it
   remains partly experiment-log-like even though the science is organized.
3. EXP-021 qualification scope could be repeated at every use of "fixed readout
   accuracy drops" to avoid treating it as formal scientific degradation.
4. Introduction's "geometry and information content" motivation is acceptable
   but should be flagged as framing, not an experimental result.

## 17. Ordered Revision Plan

1. Narrow the central claim: explicitly label formal vs descriptive support.
2. Reframe the Abstract and Introduction gap/contributions around the specific
   fixed-readout protocol, held-out controls, and negative-evidence chain.
3. Add the evidence-summary table and two critical figures (EXP-023
   heterogeneity and EXP-024 all-10 scatter).
4. Verify and complete all required citations, including the Top-5 direct prior
   works.
5. Expand the statistical exposition: record/source-family counts, tie handling,
   exact permutation, and fixed-panel inference boundary.
6. Close reproducibility gaps: dataset sizes, class mapping, optimization,
   seed, metric definitions, and data/code availability.
7. Tighten Results prose from experiment-log transitions to scientific-argument
   transitions.
8. Adjust Discussion/Conclusion wording, especially "often recover".
9. Polish language, figures, and table captions for the target venue.

Task 099B stops here. The experiment line remains closed; the next task is
`099C_MANUSCRIPT_REVISION`.
