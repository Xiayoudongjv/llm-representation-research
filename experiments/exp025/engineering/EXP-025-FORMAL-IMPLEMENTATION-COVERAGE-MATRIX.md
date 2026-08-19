# EXP-025 Formal Implementation Coverage Matrix

Classification: `GOVERNANCE_AND_COVERAGE_BASELINE_ONLY`

Baseline commit: `f3aa196201aa7b1ee80dd2637c7ecd97a3df3e07`

Current runner SHA-256:
`c6382f44729792bd68f6dab5494f71cb44588da43c2932fedb1970742afbf2a2`

## Baseline

```text
FROZEN_IMPLEMENTATION_COVERAGE = 0/12
```

The post-consumption `_execute_formal_analysis` function is a stub. Supporting
helpers exist in `run_exp025.py`, but no formal scientific/publication endpoint
is implemented or wired into the production post-consumption path.

## Status Vocabulary

- `IMPLEMENTED_AND_TESTED`
- `IMPLEMENTED_UNTESTED`
- `PARTIAL`
- `NOT_IMPLEMENTED`
- `SPECIFICATION_GAP`

## Coverage Matrix

| REGISTERED_REQUIREMENT | FROZEN_AUTHORITY | CURRENT_IMPLEMENTATION | TEST_COVERAGE | STATUS |
| --- | --- | --- | --- | --- |
| 1. Frozen dataset loading and identity validation | EXP-025 preregistration; EXP-025 frozen config; EXP-024 frozen dataset identity | Helpers exist but are not invoked by `_execute_formal_analysis` | None for formal path | `NOT_IMPLEMENTED` |
| 2. OLMo tokenizer/model identity | EXP-025 model selection; EXP-025 preregistration | Qualification-only helpers exist; not wired to formal executor | None for formal path | `NOT_IMPLEMENTED` |
| 3. Reference-checkpoint representation extraction | EXP-025 checkpoint mapping; EXP-024 representation contract | Qualification-only extraction helpers exist; not wired to formal executor | None for formal path | `NOT_IMPLEMENTED` |
| 4. Final-checkpoint representation extraction | EXP-025 checkpoint mapping; EXP-024 representation contract | Qualification-only extraction helpers exist; not wired to formal executor | None for formal path | `NOT_IMPLEMENTED` |
| 5. FIT-only reference classifier training | EXP-025 preregistration; EXP-024 classifier/scaler contract | Qualification-only fit helper exists; not formal scientific path | None for formal path | `NOT_IMPLEMENTED` |
| 6. DIAGNOSTIC fixed-readout evaluation | EXP-025 preregistration; EXP-024 primary diagnostic definition | Not implemented | None | `NOT_IMPLEMENTED` |
| 7. `S_diag(c)` | EXP-025 preregistration; EXP-024 primary diagnostic definition | Not implemented | None | `NOT_IMPLEMENTED` |
| 8. EVAL `A0` | EXP-025 preregistration; EXP-024 calibration contract | Not implemented | None | `NOT_IMPLEMENTED` |
| 9. EVAL `A_mu` | EXP-025 preregistration; EXP-024 calibration contract | Not implemented | None | `NOT_IMPLEMENTED` |
| 10. EVAL `A_sigma` | EXP-025 preregistration; EXP-024 calibration contract | Not implemented | None | `NOT_IMPLEMENTED` |
| 11. EVAL `A_mu_sigma` and `G_eval(c)` | EXP-025 preregistration; EXP-024 calibration/confirmatory contract | Not implemented | None | `NOT_IMPLEMENTED` |
| 12. Secondary Spearman/permutation, routing, provenance, atomic publication | EXP-025 preregistration; EXP-024 exact-test/routing precedent | Not implemented | None | `NOT_IMPLEMENTED` |

## Supporting Code vs Formal Endpoint

The presence of the following qualification-only helpers does not count as
formal endpoint implementation:

- `sha256_file`, `read_json`, `write_json`;
- `last_valid_token_indices`, `select_last_valid_token`,
  `to_float32_analysis_array`;
- `fit_scaler`, `fit_classifier`, `transform_with_stats`,
  `predict_with_classifier`;
- `_run_qualification_forward`, `_extract_checkpoint_array`;
- `verify_frozen_design`, `verify_inherited_dataset`,
  `load_frozen_dataset`, `validate_dataset_firewall`.

These may be reused by the future executor, but only after the frozen
specification gaps are resolved and the production call graph is implemented
and tested end to end.

## Required Flags

```text
EXP025_IMPLEMENTATION_COVERAGE_BASELINE = 0/12
EXP025_FORMAL_EXECUTOR_STATUS = NOT_IMPLEMENTED
EXP025_FORMAL_EXECUTOR_SPEC_COMPLETE = true
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = true
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
EXP025_NEXT_TASK = 100D_E_IMPLEMENT_FROZEN_FORMAL_EXECUTOR
```
