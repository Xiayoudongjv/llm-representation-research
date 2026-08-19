# EXP-025 Formal Implementation Coverage Matrix

Classification: `GOVERNANCE_AND_COVERAGE_STATUS`

Baseline commit: `f3aa196201aa7b1ee80dd2637c7ecd97a3df3e07`

Current runner SHA-256:
`c28c424a502fb755a44458f34be2811a8ab121b39b6a3062096e8d350da0c201`

## Baseline

```text
IMPLEMENTATION_COVERAGE = 12/12 VERIFIED
```

Task 100D-G repaired the formal executor against verified adversarial
rereview findings B1 and M1-M6. The production post-consumption path is now
implemented, structurally validated, tested on synthetic fixtures, and
qualified end to end. No real DIAGNOSTIC or EVAL data was accessed.

## Status Vocabulary

- `IMPLEMENTED_AND_TESTED`
- `IMPLEMENTED_UNTESTED`
- `PARTIAL`
- `NOT_IMPLEMENTED`
- `SPECIFICATION_GAP`
- `VERIFIED`

## Coverage Matrix

| REGISTERED_REQUIREMENT | FROZEN_AUTHORITY | CURRENT_IMPLEMENTATION | TEST_COVERAGE | STATUS |
| --- | --- | --- | --- | --- |
| 1. Frozen dataset loading and identity validation | EXP-025 preregistration; EXP-025 frozen config; EXP-024 frozen dataset identity | Implemented and invoked by `_execute_formal_analysis` | Formal partition/identity tests | `VERIFIED` |
| 2. OLMo tokenizer/model identity | EXP-025 model selection; EXP-025 preregistration | Implemented and bound to production runtime | Synthetic and identity tests | `VERIFIED` |
| 3. Reference-checkpoint representation extraction | EXP-025 checkpoint mapping; EXP-024 representation contract | Implemented through `_formal_record_extractor` | Extraction dtype/shape and synthetic E2E tests | `VERIFIED` |
| 4. Final-checkpoint representation extraction | EXP-025 checkpoint mapping; EXP-024 representation contract | Implemented through `_formal_record_extractor` | Extraction dtype/shape and synthetic E2E tests | `VERIFIED` |
| 5. FIT-only reference classifier training and usability gate | EXP-025 preregistration; EXP-024 classifier/scaler contract | Implemented via `_formal_fit_reference_readout` with `fit_reference_ba >= 0.75` enforcement | Macro-BA, usability threshold, and synthetic formal tests | `VERIFIED` |
| 6. DIAGNOSTIC fixed-readout evaluation | EXP-025 preregistration; EXP-024 primary diagnostic definition | Implemented in formal analysis loop | Synthetic E2E and BA tests | `VERIFIED` |
| 7. `S_diag(c)` | EXP-025 preregistration; EXP-024 primary diagnostic definition | Implemented via `compute_s_diag` | Synthetic E2E and route tests | `VERIFIED` |
| 8. EVAL `A0` | EXP-025 preregistration; EXP-024 calibration contract | Implemented via `calibration_condition_predictions` | Calibration-variant and synthetic E2E tests | `VERIFIED` |
| 9. EVAL `A_mu` | EXP-025 preregistration; EXP-024 calibration contract | Implemented via `calibration_condition_predictions` | Calibration-variant and synthetic E2E tests | `VERIFIED` |
| 10. EVAL `A_sigma` | EXP-025 preregistration; EXP-024 calibration contract | Implemented via `calibration_condition_predictions` | Zero-variance and synthetic E2E tests | `VERIFIED` |
| 11. EVAL `A_mu_sigma` and `G_eval(c)` | EXP-025 preregistration; EXP-024 calibration/confirmatory contract | Implemented via `calibration_condition_predictions` and `compute_g_eval` | Calibration-variant and synthetic E2E tests | `VERIFIED` |
| 12. Secondary Spearman/permutation, routing, provenance, atomic publication | EXP-025 preregistration; EXP-024 exact-test/routing precedent | Implemented via `exact_one_sided_permutation_p`, `route_replication`, `atomic_publish_validated_result` | Spearman/permutation/binomial/provenance/atomic-publication tests | `VERIFIED` |

## Task 100D-G Repair Record

Repaired findings from Task 100D-F:

- B1: enforce `fit_reference_ba >= 0.75` before formal pipeline continuation.
- M1: complete canonical provenance and structural nested result-schema validation.
- M2: disclose `POST_HOC_PROTOCOL_RECOVERY` governance binding.
- M3: replace overwrite-capable publication with exclusive same-volume link publication.
- M4: derive the registered-statistics expected-value check from actual synthetic output.
- M5: register `mean_s_diag`, `median_s_diag`, `mean_g_eval`, and `median_g_eval`.
- M6: harden degenerate/non-finite Spearman and permutation behavior.

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
EXP025_IMPLEMENTATION_ENDPOINTS_VERIFIED = 12/12
EXP025_FORMAL_EXECUTOR_STATUS = IMPLEMENTED_AND_TESTED
EXP025_FORMAL_EXECUTOR_SPEC_COMPLETE = true
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = true
EXP025_ENGINEERING_REQUALIFICATION = PASS
EXP025_MEASUREMENT_REQUALIFICATION = PASS
EXP025_FORMAL_PIPELINE_QUALIFICATION = PASS
EXP025_FORMAL_RUN_READINESS = READY
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
EXP025_NEXT_TASK = 100D_H_TARGETED_POST_REPAIR_REREVIEW
```
