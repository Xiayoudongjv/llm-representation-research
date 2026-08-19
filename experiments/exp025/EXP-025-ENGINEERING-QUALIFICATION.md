# EXP-025 Engineering Qualification

Status: `FORMAL_RUN_READINESS = BLOCKED`

This document records the Task 100B engineering-qualification attempt for
EXP-025. It does not contain DIAGNOSTIC or EVAL scientific outcomes.

## Result Summary

- `ENGINEERING_STATUS = FAIL`
- `MEASUREMENT_STATUS = FAIL`
- `FORMAL_RUN_READINESS = BLOCKED`
- `EXP025_FALLBACK_USED = false`
- `EXP025_DIAG_OUTCOME_VIEWED = false`
- `EXP025_EVAL_OUTCOME_VIEWED = false`
- `EXP025_FORMAL_RUN_PERFORMED = false`
- `EXP025_SCIENTIFIC_RESULT_CREATED = false`

## Blocking Reason

The exact pinned OLMo model revision config and tokenizer files are present in
the local HF cache, but the model weights file is not present:

```text
model.safetensors missing from snapshot
48d788eca847d4d7548f375ad03d3c9312f6139e
```

The real model/tokenizer/hook qualification therefore could not be executed in
this attempt. The failure is a model-acquisition/runtime availability block,
not a scientific measurement result.

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
- Transformers: `5.14.1`
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
12 passed
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

## Next Action

The weights file `model.safetensors` must be acquired for the exact pinned
revision before real runtime qualification can be repeated. After acquisition,
rerun:

```text
python experiments/exp025/run_exp025.py --engineering-qualification
```

Do not fall back to another model on the basis of scientific outcomes.
