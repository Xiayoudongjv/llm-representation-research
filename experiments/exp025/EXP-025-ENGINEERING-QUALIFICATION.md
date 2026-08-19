# EXP-025 Engineering Qualification

Status: `FORMAL_RUN_READINESS = READY`

This document records the EXP-025 engineering and measurement qualification
state after the Task 100B-R BF16 boundary repair and the Task 100D-A
authorization-consumption repair. It does not contain DIAGNOSTIC or EVAL
scientific outcomes.

## Result Summary

- `ENGINEERING_STATUS = PASS`
- `MEASUREMENT_STATUS = PASS`
- `FORMAL_RUN_READINESS = READY`
- `EXP025_FALLBACK_USED = false`
- `EXP025_DIAG_OUTCOME_VIEWED = false`
- `EXP025_EVAL_OUTCOME_VIEWED = false`
- `EXP025_FORMAL_RUN_PERFORMED = false`
- `EXP025_SCIENTIFIC_RESULT_CREATED = false`

## Repairs Applied

### BF16 NumPy Boundary

- `BF16_NUMPY_BOUNDARY_REPAIR = true`
- `BF16_MODEL_RUNTIME_PRESERVED = true`
- `SCIENTIFIC_EXTRACTION_ARRAY_DTYPE = float32`
- `FROZEN_SCIENTIFIC_DESIGN_CHANGED = false`

The centralized Tensor-to-NumPy helper explicitly converts:

```text
tensor.detach().cpu().to(torch.float32).numpy()
```

Single-record last-valid-token extraction is flattened to the frozen
`[hidden_size]` vector contract before classifier/scaler processing.

### Formal Authorization Consumption

- Root cause: `run_formal` contained a stale 100B sentinel and raised
  `FORMAL_AUTHORIZATION_NOT_CONSUMED_IN_100B` before validation or
  consumption.
- Repair: the formal path now follows:

```text
validate authorization identity
-> verify no existing result
-> verify authorization not already consumed
-> atomically create exclusive consumption record
-> create run-attempt identity
-> then reach scientific executor
```

- Atomic consumption uses exclusive file creation, so a second use of the
  same authorization fails closed.
- Scientific execution remains explicitly gated as
  `FORMAL_SCIENCE_NOT_AUTHORIZED_IN_100D_A`; Task 100D-A does not run formal
  science.

## Frozen Design Status

Frozen Task 100A design files remain unchanged:

- `experiments/exp025/EXP-025-PREREGISTRATION.md`
- `experiments/exp025/EXP-025-MODEL-SELECTION.md`
- `experiments/exp025/EXP-025-CHECKPOINT-MAPPING.md`
- `experiments/exp025/exp025_frozen_config.json`
- `experiments/exp025/validate_exp025_design.py`

The runner's frozen-authority verifier passes. The standalone
`validate_exp025_design.py` still contains a legacy result-candidate check
that treats `exp025_formal_run_authorization.json` as a forbidden result
artifact, so it reports a collision while the preconsumption authorization
remains. That validator was not modified.

## Environment Observed

- Python: `3.11.9`
- PyTorch: `2.12.1+cu130`
- Transformers: `5.14.1`
- NumPy: `2.4.6`
- scikit-learn: `1.9.0`
- Hugging Face Hub: `1.27.0`
- CUDA available: `true`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`
- GPU VRAM: about `7.96 GB`

## Test Coverage

Focused tests are in:

```text
tests/test_exp025_runner.py
```

Focused pytest result:

```text
22 passed
```

Covered checks include:

- frozen design identity binding
- model revision pinning
- checkpoint mapping assertion
- mode fail-closed
- formal-run authorization requirement
- fresh authorization consumption
- double-consumption rejection
- existing-result rejection
- wrong repository-commit rejection
- wrong model identity rejection
- science-before-consumption call-order guard
- class probability mapping
- FIT/DIAG/EVAL firewall separation
- recalibration known-answer behavior
- qualification cannot publish a scientific result
- BF16 Tensor-to-NumPy conversion boundary
- single-record representation flattening

## Qualification Checks

- `MODEL_IDENTITY`: PASS
- `TOKENIZER_CONTRACT`: PASS
- `CHECKPOINT_MAPPING`: PASS
- `HIDDEN_STATE_EXTRACTION`: PASS
- `DETERMINISM`: PASS
- `PROBABILITY_CLASS_MAPPING`: PASS
- `MEASUREMENT_QUALIFICATION`: PASS
- `RECALIBRATION_PATH`: PASS
- `RESOURCE_FEASIBILITY`: PASS
- `PRODUCTION_CALL_GRAPH`: PASS
- `FIT_DIAG_EVAL_FIREWALL`: PASS

## Next Action

Stop here. Do not create a new authorization and do not run formal science.
The next gate is `100C2_EXP025_REAUTHORIZATION_AFTER_PRECONSUMPTION_REPAIR`.