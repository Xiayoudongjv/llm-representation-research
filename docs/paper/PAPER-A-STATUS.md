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

- `PAPER_A_SUBMISSION_READINESS = ONE_TARGETED_FOLLOWUP_RECOMMENDED`

Rationale: the largest remaining evidence gap is the absence of an independent
susceptibility predictor. This gap is material for a mechanism-level claim.

## Central Unresolved Scientific Gap

Can a FIT-only or separately held-out diagnostic predict which held-out
conditions will exhibit deep fixed-readout degradation and therefore benefit
from featurewise recalibration?

The existing experiments cannot answer this because:

- EXP-022A generated the recalibration signal in a discovery context;
- EXP-023 independently showed `NO_REPLICATION`;
- the diagnostic used in the current chain algebraically shares the
  confirmatory `A0_final` quantity with `G_cal`;
- no experiment separated a susceptibility predictor from the confirmatory
  EVAL partition.

## Venue Readiness

| Venue | Current fit | Main strength | Main weakness | Minimum additional evidence needed |
| --- | --- | --- | --- | --- |
| TMLR | conditional | transparent negative result and reproducibility controls | no independent susceptibility predictor | targeted follow-up or clearly bounded claim |
| Neural Networks | conditional | layerwise readout + calibration analysis | one model family, controlled data | cross-model or susceptibility diagnostic |
| ICLR | cautious | clean controlled chain and negative evidence | small evidence breadth | stronger mechanistic or generalization evidence |
| NeurIPS | cautious | interesting negative/heterogeneous result | no causal/functional mechanism | independent predictor and broader validation |
| ICML | cautious | controlled methodology | limited theoretical/functional contribution | clear mechanism-level advance |

No acceptance probabilities are assigned.

## Guardrails

- EXP-023 must remain visible as `NO_REPLICATION`.
- EXP-017 and EXP-019 negative/boundary evidence must remain visible.
- General transport, functional binding, and universal calibration claims are
  forbidden in current manuscript language.
- The targeted follow-up slot is reserved for `HYP_CALIBRATION_CONDITIONAL_002`.

## Current Files

- Scaffold: `docs/paper/PAPER-A-FIRST-DRAFT-SCAFFOLD.md`
- Claim matrix: `docs/paper/PAPER-A-CLAIM-EVIDENCE-MATRIX.md`
- Figure plan: `docs/paper/PAPER-A-FIGURE-PLAN.md`
- Status: `docs/paper/PAPER-A-STATUS.md`

## Next Step

Choose between:

- `Task 097A-W`: begin actual Paper-A prose drafting; or
- `Task 097B`: design the targeted follow-up for
  `HYP_CALIBRATION_CONDITIONAL_002`.

Do not create EXP-024 or run new models in Task 097A.

## Follow-Up Design

- `FOLLOWUP_DESIGN_STATUS = FROZEN_NOT_RUN`
- `SELECTED_FOLLOWUP_DESIGN = B`
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

`PAPER_A_DRAFT_READINESS` remains `START_FIRST_DRAFT_NOW`. Prose drafting may
continue in parallel with Task-097D dataset construction and review.
