# EXP-025 100D Preconsumption Failure Audit

Classification: `PRECONSUMPTION_ENGINEERING_FAILURE`

This attempt failed before authorization consumption and before any
scientific execution.

## Attempt Record

- Formal command launch count: `1`
- Process exit code: `1`
- Failure string: `EXP025_FAIL_CLOSED: FORMAL_AUTHORIZATION_NOT_CONSUMED_IN_100B`
- Authorization ID: `798f71e8-ff9f-4dd6-94b0-f1f0fcc02589`
- Authorization SHA-256: `f9488e2e46b4ff0ab2f3d268027306fa2ff23de2ab6f8fbab532062a24c99e16`
- Authorization consumed: `false`
- Consumption artifact: `absent`
- Run attempt ID: `absent`
- DIAG outcome viewed: `false`
- EVAL outcome viewed: `false`
- Scientific result: `absent`

## Status

- Not a scientific negative.
- Not a measurement failure.
- Not a formal scientific result.

## Reconciliation

- `EXP025_FROZEN_DESIGN_CONTRADICTION = false`
- `EXP025_RUNTIME_IMPLEMENTATION_CONTRADICTION = true`
- `EXP025_LEGACY_DESIGN_VALIDATOR_STATUS = POST_AUTHORIZATION_SCOPE_LIMITATION`

The frozen scientific design did not require formal authorization consumption
during Task 100B. The failure was caused by a stale runtime sentinel in
`run_exp025.py`.

The standalone Task 100A design validator treats
`exp025_formal_run_authorization.json` as a formal-result path, which is a
post-authorization scope limitation rather than evidence that the frozen
scientific design itself forbids authorization. The frozen authority hashes
remain unchanged.