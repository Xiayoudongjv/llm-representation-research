# EXP-028 103C Preregistration Correction Note

**Task:** `103C_EXP028_PREREGISTRATION_REREVIEW_AND_ENGINEERING_SPEC`
**Status:** `PROSPECTIVE_PREREGISTRATION_CLARIFICATION`
**Preregistration commit:** `86c120f56ee615540ecff15bb62f8d05eaca7700`
**Entry HEAD at rereview:** `7271aa1aa9c2e2a6a46a908e97a702dc35dfcd7f`

This correction is prospective and pre-data. The following firewalls were true at
the time of correction:

- `REAL_EXP028_FIT_ACCESSED = false`
- `REAL_EXP028_DIAG_ACCESSED = false`
- `REAL_EXP028_EVAL_ACCESSED = false`
- `EXP028_RESULT_CREATED = false`
- `EXP028_AUTHORIZATION_CREATED = false`
- `EXP028_FORMAL_RUN_PERFORMED = false`

## Corrections

0. **Authority commit anchor.** The frozen config, validator, and preregistration header previously named `cb581bcfa3640d72f121c34b1cdd59cc3cc672c9` as the authority/freeze commit. The actual EXP-028 preregistration commit is `86c120f56ee615540ecff15bb62f8d05eaca7700`; the anchor fields are corrected to that commit.

1. **Bootstrap support semantics.** The inherited quantiles `[5, 95]` were
   previously described as a `95% percentile CI`. This is not a two-sided 95% CI.
   The scientific gate is now explicit: the primary support decision uses a
   one-sided 95% lower percentile bound (`q_0.05`). The interval
   `[q_0.05, q_0.95]` is retained only as a central 90% descriptive interval.

2. **Primary comparator and sign conventions.** The primary contrast is now
   explicit as `T2_MINUS_T1`, with `T1_MOMENT_RECALIBRATION` as the frozen
   baseline. `DELTA_RM` and `DELTA_RO` sign conventions are explicit in the
   frozen config and preregistration document.

3. **Aggregation completeness.** Source-family aggregation is explicit as an
   equal-weight mean over fresh EVAL source families after item-level
   aggregation.

4. **Freshness authority completeness.** The full prior-panel authority list and
   hashes are now enumerated in the frozen config and preregistration document.

5. **Pair-break determinism.** Scope, ordering, condition handling, and
   source-family handling are explicit and validator-covered.

## Validator behavior

`experiments/exp028/validate_exp028_preregistration.py` now rejects the
ambiguous legacy `ci_level` field and requires the corrected
`primary_support_ci`, `descriptive_central_interval`, and
`support_decision_uses` fields. It also covers the corrected aggregation,
pair-break, and freshness fields.

## Scope firewall

This correction does not redesign EXP-028, change the frozen primary endpoints,
change the operator family, change the panel allocation, create a result, run a
model, or authorize a formal run.
