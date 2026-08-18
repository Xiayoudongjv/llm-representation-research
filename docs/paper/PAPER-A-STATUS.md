# Paper-A Status

Status: `PAPER_A_097A_EVIDENCE_ARCHITECTURE_AND_DRAFT_SCAFFOLD_COMPLETE`

This file records manuscript-planning state only. It is not scientific
authority and must never outrank canonical experiment results or the claim
ledger.

## Draft Readiness

- `PAPER_A_DRAFT_READINESS = START_FIRST_DRAFT_NOW`

Rationale: the evidence chain supports a coherent bounded manuscript with
visible negative and heterogeneous results.

## Submission Readiness

- `PAPER_A_SUBMISSION_READINESS = NOT_READY_TO_SUBMIT_YET`

Rationale: the full prose draft and citation/prior-art completion remain. The
targeted susceptibility predictor has now been tested by EXP-024 with a valid
negative primary, so it is no longer an open prospective gap. A second model
would broaden but is not required to start or finish the bounded draft.

## Central Unresolved Scientific Gap

EXP-024 directly tested the previously open question:

> Can an independent DIAGNOSTIC degradation magnitude predict confirmatory
> EVAL calibration benefit at the condition level?

Registered result: primary support `false`.

The remaining scientific gap is not the absence of a susceptibility test. It is
that a simple independent degradation-magnitude measure is insufficient to
explain condition-level calibration benefit, while the actual mechanism remains
unresolved. Cross-model generality also remains untested.

## Venue Readiness

| Venue | Current fit | Main strength | Main weakness | Minimum additional evidence needed |
| --- | --- | --- | --- | --- |
| TMLR | conditional | transparent negative result and reproducibility controls | simple susceptibility predictor not supported; mechanism unresolved | clearly bounded claim; optional cross-model breadth |
| Neural Networks | conditional | layerwise readout + calibration analysis | one model family, controlled data | cross-model generality or mechanistic condition-level diagnostic |
| ICLR | cautious | clean controlled chain and negative evidence | small evidence breadth | stronger mechanistic or generalization evidence |
| NeurIPS | cautious | interesting negative/heterogeneous result | no causal/functional mechanism | independent predictor and broader validation |
| ICML | cautious | controlled methodology | limited theoretical/functional contribution | clear mechanism-level advance |

No acceptance probabilities are assigned.

## Guardrails

- EXP-023 must remain visible as `NO_REPLICATION`.
- EXP-017 and EXP-019 negative/boundary evidence must remain visible.
- General transport, functional binding, and universal calibration claims are
  forbidden in current manuscript language.
- The targeted follow-up slot for `HYP_CALIBRATION_CONDITIONAL_002` has been
  executed by EXP-024; its primary result is `NOT_SUPPORTED`.
- EXP-024's 10/10 positive `S_diag`/`G_eval` values are descriptive only and
  must not be presented as a new confirmatory positivity test.

## Current Files

- Scaffold: `docs/paper/PAPER-A-FIRST-DRAFT-SCAFFOLD.md`
- Claim matrix: `docs/paper/PAPER-A-CLAIM-EVIDENCE-MATRIX.md`
- Figure plan: `docs/paper/PAPER-A-FIGURE-PLAN.md`
- Status: `docs/paper/PAPER-A-STATUS.md`

## Next Step

Proceed to `Task 097A-W`: begin the actual Paper-A prose draft with the
bounded story and the EXP-024 negative primary explicitly visible.

Do not automatically create EXP-025, create a replacement authorization, or
launch a second-model replication rescue.

## Follow-Up Design

- `FOLLOWUP_DESIGN_STATUS = COMPLETED_NEGATIVE_PRIMARY`
- `SELECTED_FOLLOWUP_DESIGN = B` (executed as EXP-024)
- Design draft: `docs/experiments/EXP-024-DESIGN-DRAFT.md`
- Prior-art gap note: `docs/paper/PAPER-A-PRIOR-ART-GAP-NOTE.md`
- Preregistration draft: `docs/experiments/EXP-024-PREREGISTRATION-DRAFT.md`
- Protocol review: `docs/experiments/EXP-024-PROTOCOL-DESIGN-REVIEW.md`
- Dataset schema spec: `docs/experiments/EXP-024-DATASET-SPEC.md`

Selected evidence gap:

> Can a condition-level fixed-readout degradation diagnostic estimated on
> independent DIAGNOSTIC source families predict FIT-only featurewise
> recalibration benefit on source-family-independent EVAL families?

Design-level decisions:

- `PRIMARY_SCIENTIFIC_UNIT = condition/panel`
- `SECOND_MODEL_REQUIRED = false`
- `DIAGNOSTIC_EVAL_INDEPENDENCE = PASS`
- `ALGEBRAIC_SHARED_A0_PRIMARY_ANALYSIS = false`
- Primary diagnostic: `D_diag_cond = BA_A0_diag(block27-pre) - BA_A0_diag(block16-pre)`
- Primary confirmatory endpoint:
  `G_eval_cond = BA_A_mu_sigma_EVAL(block27-pre) - BA_A0_EVAL(block27-pre)`
- `EXP024_DESIGN_DRAFT_CREATED = true`
- `EXP024_PREREGISTRATION_DRAFT_CREATED = true`
- `EXP024_PREREGISTRATION_FROZEN = true`
- `EXP024_PROTOCOL_REVIEW = READY_FOR_DATASET_CONSTRUCTION`
- `EXP024_PRIMARY_RESULT = NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`
- `EXP024_PRIMARY_RHO = 0.28401877872187725`
- `EXP024_PRIMARY_EXACT_P = 0.2115079365079365`
- `EXP024_PANEL_POSITIVE_DESCRIPTIVE = 10/10 S_diag, 10/10 G_eval`

`PAPER_A_DRAFT_READINESS` remains `START_FIRST_DRAFT_NOW`.

`PAPER_A_CORE_CLAIM = SUPPORTED_WITH_SCOPE_LIMITATIONS_AND_NEGATIVE_SUSCEPTIBILITY`

The bounded story remains publishable as a careful positive/negative evidence
chain; the simple susceptibility predictor is explicitly `NOT_SUPPORTED` in
EXP-024.
