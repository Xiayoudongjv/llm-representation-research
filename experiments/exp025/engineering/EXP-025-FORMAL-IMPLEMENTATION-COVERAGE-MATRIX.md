# EXP-025 Formal Implementation Coverage Matrix

Classification: `GOVERNANCE_AND_COVERAGE_STATUS`

Baseline commit: `f3aa196201aa7b1ee80dd2637c7ecd97a3df3e07`

Current runner SHA-256:
`ec3ec1378d52ffe03c6aea5a8c16da4a6c28cd26aee8235e0a1842b36d983d3f`

## Baseline

```text
IMPLEMENTATION_COVERAGE = 12/12
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
| 1. Frozen dataset loading and identity validation | EXP-025 preregistration; EXP-025 frozen config; EXP-024 frozen dataset identity | Implemented and invoked by `_execute_formal_analysis` | Formal partition/identity tests | `IMPLEMENTED_AND_TESTED` |
| 2. OLMo tokenizer/model identity | EXP-025 model selection; EXP-025 preregistration | Implemented and bound to production runtime | Synthetic and identity tests | `IMPLEMENTED_AND_TESTED` |
| 3. Reference-checkpoint representation extraction | EXP-025 checkpoint mapping; EXP-024 representation contract | Implemented through `_formal_record_extractor` | Extraction dtype/shape and synthetic E2E tests | `IMPLEMENTED_AND_TESTED` |
| 4. Final-checkpoint representation extraction | EXP-025 checkpoint mapping; EXP-024 representation contract | Implemented through `_formal_record_extractor` | Extraction dtype/shape and synthetic E2E tests | `IMPLEMENTED_AND_TESTED` |
| 5. FIT-only reference classifier training | EXP-025 preregistration; EXP-024 classifier/scaler contract | Implemented via `_formal_fit_reference_readout` | Macro-BA and synthetic formal tests | `IMPLEMENTED_AND_TESTED` |
| 6. DIAGNOSTIC fixed-readout evaluation | EXP-025 preregistration; EXP-024 primary diagnostic definition | Implemented in formal analysis loop | Synthetic E2E and BA tests | `IMPLEMENTED_AND_TESTED` |
| 7. `S_diag(c)` | EXP-025 preregistration; EXP-024 primary diagnostic definition | Implemented via `compute_s_diag` | Synthetic E2E and route tests | `IMPLEMENTED_AND_TESTED` |
| 8. EVAL `A0` | EXP-025 preregistration; EXP-024 calibration contract | Implemented via `calibration_condition_predictions` | Calibration-variant and synthetic E2E tests | `IMPLEMENTED_AND_TESTED` |
| 9. EVAL `A_mu` | EXP-025 preregistration; EXP-024 calibration contract | Implemented via `calibration_condition_predictions` | Calibration-variant and synthetic E2E tests | `IMPLEMENTED_AND_TESTED` |
| 10. EVAL `A_sigma` | EXP-025 preregistration; EXP-024 calibration contract | Implemented via `calibration_condition_predictions` | Zero-variance and synthetic E2E tests | `IMPLEMENTED_AND_TESTED` |
| 11. EVAL `A_mu_sigma` and `G_eval(c)` | EXP-025 preregistration; EXP-024 calibration/confirmatory contract | Implemented via `calibration_condition_predictions` and `compute_g_eval` | Calibration-variant and synthetic E2E tests | `IMPLEMENTED_AND_TESTED` |
| 12. Secondary Spearman/permutation, routing, provenance, atomic publication | EXP-025 preregistration; EXP-024 exact-test/routing precedent | Implemented via `exact_one_sided_permutation_p`, `route_replication`, `atomic_publish_validated_result` | Spearman/permutation/binomial/atomic-publication tests | `IMPLEMENTED_AND_TESTED` |

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
EXP025_IMPLEMENTATION_COVERAGE = 12/12
EXP025_FORMAL_EXECUTOR_STATUS = IMPLEMENTED_AND_TESTED
EXP025_FORMAL_EXECUTOR_SPEC_COMPLETE = true
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = true
EXP025_ENGINEERING_REQUALIFICATION = PASS
EXP025_MEASUREMENT_REQUALIFICATION = PASS
EXP025_FORMAL_PIPELINE_QUALIFICATION = PASS
EXP025_FORMAL_RUN_READINESS = READY
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
EXP025_NEXT_TASK = 100D_F_ADVERSARIAL_FORMAL_EXECUTOR_REREVIEW
```
