# Paper-A Figure Plan

This file proposes figures only. Do not generate plots in Task 097A. Every
figure must come from existing canonical data or documented constructs.

## Figure 1: Conceptual distinction among representation, readout, and function

- Question: What distinctions prevent representation movement from being read
  as functional control?
- Source artifact(s): `docs/research/RESEARCH-SPINE.md`,
  `docs/research/CONSTRUCT-REGISTRY.md`.
- Panel plan: one conceptual diagram with three non-equivalent levels:
  representation/state, readout compatibility, downstream function/behavior.
- Required data: none; construct-level diagram.
- Caption thesis: local representation structure is not the same as stable
  downstream usability.
- Interpretation boundary: no causal arrow should imply transport or control.
- Ready/not ready: `READY_TO_DRAFT_FROM_CONSTRUCTS`.

## Figure 2: Target-directed representation manipulation in EXP-018/EXP-020A

- Question: Is task-associated representation movement locally manipulable
  under held-out controls?
- Source artifact(s): `docs/experiments/EXP-018.md`;
  `docs/experiments/canonical/EXP-020A-CANONICAL-RESULT-RECOVERY.json`;
  `experiments/exp020/results/exp020a_results.json`.
- Panel plan:
  - Panel A: EXP-018 task-directed versus matched-random/opposite probe changes.
  - Panel B: EXP-020A same-family replication gate summary.
- Required data: existing summary tables/values from source artifacts.
- Caption thesis: local representational manipulability is supported, but only
  at the representation-readout level.
- Interpretation boundary: no behavioral control or general task conversion is
  claimed.
- Ready/not ready: `READY_FROM_EXISTING_SUMMARIES`; no new computation.

## Figure 3: Depth-wise fixed-readout qualification in EXP-021

- Question: Does a fixed readout remain qualified across depth?
- Source artifact(s):
  `docs/experiments/canonical/EXP-021-STAGE-Q-Q3-RESULT-SANITIZED.json`;
  local sanitized source if needed.
- Panel plan: line/bar plot of split-level accuracy or pass status across
  checkpoints for Split A and Split B.
- Required data: checkpoint pass/accuracy fields already present in the
  canonical sanitized result.
- Caption thesis: fixed readout qualification degrades at deeper clean
  checkpoints and is split/condition dependent.
- Interpretation boundary: this is readout qualification, not a universal
  representation-quality or functional claim.
- Ready/not ready: `READY_FROM_EXISTING_RESULT`.

## Figure 4: EXP-022A featurewise recalibration decomposition

- Question: Does simple featurewise recalibration recover a degraded fixed
  readout in the discovery experiment?
- Source artifact(s):
  `experiments/exp022a/results/exp022a_results.json`;
  `docs/experiments/EXP-022A-SCIENTIFIC-CLOSEOUT.md`.
- Panel plan:
  - Panel A: A0 reference versus A0 final-pre for each split.
  - Panel B: A0/A1/A2 final-pre comparison.
  - Panel C: descriptive `G_scale` values.
- Required data: existing split metrics and secondary values.
- Caption thesis: featurewise recalibration is a candidate recovery mechanism
  in the discovery experiment, especially where degradation is strong.
- Interpretation boundary: exploratory origin; not an independent confirmatory
  result.
- Ready/not ready: `READY_FROM_EXISTING_RESULT`.

## Figure 5: EXP-023 independent replication and heterogeneity

- Question: Does the featurewise calibration rescue replicate across
  independent complementary splits?
- Source artifact(s): `experiments/exp023/results/exp023_results.json`;
  `docs/experiments/EXP-023-SCIENTIFIC-REVIEW.md`.
- Panel plan:
  - Panel A: Split A and Split B A0/A_mu/A_sigma/A_mu_sigma final-pre balanced
    accuracy.
  - Panel B: Split A and Split B `G_cal` with bootstrap intervals.
  - Panel C: explicit cross-split classification label `NO_REPLICATION`.
- Required data: split-level metrics, primary tests, bootstrap intervals.
- Caption thesis: independent replication shows strong rescue in Split A and a
  null Split B, so the general cross-split calibration claim is not supported.
- Interpretation boundary: do not hide Split B; do not pool A/B; do not relabel
  as `PARTIAL_REPLICATION`.
- Ready/not ready: `READY_FROM_EXISTING_RESULT`.

## Figure 6: Evidence synthesis and claim-boundary diagram

- Question: What does the complete EXP-017 through EXP-023 chain support and
  what remains untested?
- Source artifact(s): `docs/paper/PAPER-A-CLAIM-EVIDENCE-MATRIX.md`;
  `docs/research/CLAIM-LEDGER.md`; `docs/research/EXPERIMENT-LINEAGE.md`.
- Panel plan: evidence-flow diagram from local manipulability to conditional
  calibration, with explicit negative/boundary branches.
- Required data: none beyond existing claim statuses.
- Caption thesis: the contribution is the controlled distinction and the
  tension between positive and negative evidence, not a uniformly positive
  mechanism story.
- Interpretation boundary: transport, functional binding, and behavior remain
  untested or unsupported.
- Ready/not ready: `READY_TO_DRAFT_FROM_LEDGERS`.

## Main/Appendix Placement

- Main paper candidate figures: 1, 2, 3, 4, 5, 6.
- If page limits require cuts, Figure 6 can move to appendix.
- Do not fabricate plots from nonexistent results.
