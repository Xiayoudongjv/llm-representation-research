# EXP-025 Engineering Qualification

Status: `FORMAL_RUN_READINESS = READY`

This document records the Task 100B engineering-qualification attempt for
EXP-025. It does not contain DIAGNOSTIC or EVAL scientific outcomes.

## Result Summary

- `ENGINEERING_STATUS = PASS`
- `MEASUREMENT_STATUS = PASS`
- `FORMAL_RUN_READINESS = READY`
- `EXP025_FALLBACK_USED = false`
- `EXP025_DIAG_OUTCOME_VIEWED = false`
- `EXP025_EVAL_OUTCOME_VIEWED = false`
- `EXP025_FORMAL_RUN_PERFORMED = false`
- `EXP025_SCIENTIFIC_RESULT_CREATED = false`

## Repair Applied

- `BF16_NUMPY_BOUNDARY_REPAIR = true`
- `BF16_MODEL_RUNTIME_PRESERVED = true`
- `SCIENTIFIC_EXTRACTION_ARRAY_DTYPE = float32`
- `FROZEN_SCIENTIFIC_DESIGN_CHANGED = false`

The centralized Tensor-to-NumPy helper now explicitly converts:

```text
tensor.detach().cpu().to(torch.float32).numpy()
```

Single-record last-valid-token extraction is flattened to the frozen
`[hidden_size]` vector contract before classifier/scaler processing.

## Frozen Design Status

Frozen Task 100A design files remain unchanged:

- `experiments/exp025/EXP-025-PREREGISTRATION.md`
- `experiments/exp025/EXP-025-MODEL-SELECTION.md`
- `experiments/exp025/EXP-025-CHECKPOINT-MAPPING.md`
- `experiments/exp025/exp025_frozen_config.json`
- `experiments/exp025/validate_exp025_design.py`

`EXP025_DESIGN_VALIDATION = PASS` was rerun before the qualification attempt.

## Environment Observed

- Python: `3.11.9`
- PyTorch: `2.12.1+cu130`
- Transformers: `5.15.0`
- NumPy: `2.4.6`
- scikit-learn: `1.9.0`
- Hugging Face Hub: `1.27.0`
- CUDA available: `true`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`
- GPU VRAM: about `7.96 GB`

## Static and Test Coverage

The EXP-025 runner was implemented at:

```text
experiments/exp025/run_exp025.py
```

It provides:

- `--engineering-qualification`
- `--formal-run`
- `--static-preflight`

The formal-run path fails closed without a single-use authorization.

Focused tests are in:

```text
tests/test_exp025_runner.py
```

Focused pytest result:

```text
14 passed
```

Covered checks include:

- frozen design identity binding
- model revision pinning
- checkpoint mapping assertion
- mode fail-closed
- formal-run authorization requirement
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

Stop here. Do not create or consume a formal-run authorization in this task.
The next gate is exactly `100C_SINGLE_FORMAL_RUN_AUTHORIZATION`.
