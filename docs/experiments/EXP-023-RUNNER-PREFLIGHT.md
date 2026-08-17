# EXP-023 Runner Preflight

Status: `EXP023_STATIC_PREFLIGHT_PASS` / `EXP023_SYNTHETIC_PREFLIGHT_PASS`

This document records engineering-only validation. It does not establish any
EXP-023 scientific result, calibration replication, mean/scale mechanism, or
model-hook runtime correctness.

## Implementation scope

- Frozen authority validation
- Strict frozen dataset/schema loading
- Complementary Split A / Split B construction
- Clean hidden-state extraction interfaces
- `A0`, `A_mu`, `A_sigma`, and `A_mu_sigma` analysis
- Primary `G_cal` and contextual, non-gating `D_fixed`
- Secondary descriptive mechanism estimands
- Exact paired binomial tests
- Class-stratified paired bootstrap
- Full-depth descriptive trajectories
- Final-RMSNorm descriptive deltas
- Result schema validation
- Single-use authorization validation and exclusive consumption
- Atomic no-overwrite publication
- Post-consumption technical-failure evidence

## Frozen authority identities

- Frozen preregistration: `docs/experiments/EXP-023-PREREGISTRATION.md`
- Frozen preregistration SHA-256: `11bfa984d436ba06f7f3d1b0db24b90439742e9d9a87d124880834b437749f0b`
- Frozen dataset: `experiments/exp023/data/exp023_independent_controlled.json`
- Frozen dataset SHA-256: `9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a`
- Freeze commit: `0f427a45e8ee09a1c526beef8a66f8764b8d583e`
- Model: `Qwen/Qwen3-1.7B`
- Snapshot: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

## Scientific semantics implemented

- Primary condition: `A_mu_sigma`
- Primary control: `A0`
- Primary estimand: `G_cal = BA(A_mu_sigma) - BA(A0)`
- Primary checkpoint: `block27_pre_final_rmsnorm`
- Reference checkpoint: `block16_pre_final_rmsnorm`
- `D_fixed = BA(A0_final) - BA(A0_reference)`
- `D_fixed` role: `CONTEXTUAL_NOT_GATE`
- Secondary estimands: `G_mu`, `G_sigma`, `G_joint_over_mu`, `G_joint_over_sigma`
- Bootstrap RNG: `PCG64(20260818)`, `10,000` replicates per split
- Split sizes: 32 FIT / 32 EVAL per split, 8 records per class
- No layer-specific classifier refit
- No secondary significance tests
- Full-depth and final-RMSNorm reporting are descriptive only

## Static preflight

- Result: `PASS`
- Dataset structural validation: `PASS`
- Frozen preregistration hash: `PASS`
- Frozen dataset hash: `PASS`
- Historical exclusion dataset hash: `PASS`
- Freeze manifest consistency: `PASS`
- Model load: `false`
- Tokenizer load: `false`
- Formal prompt text accessed: `false`
- Scientific result created: `false`

## Synthetic preflight

- Result: `PASS`
- Classification: `ENGINEERING_SYNTHETIC_PREFLIGHT_ONLY`
- Model load: `false`
- Tokenizer load: `false`
- Formal prompt text accessed: `false`
- Scientific result created: `false`
- Cross-split synthetic result: engineering-only; no scientific interpretation

## Focused tests

- Command: `pytest -q tests/test_exp023_runner.py`
- Result: `49 passed`

## Full regression suite

- Command: `PYTHONPATH=. pytest -q`
- Result: `683 passed, 2 skipped, 2 failed`
- The two failures are pre-existing EXP-022A result-collision tests in `tests/test_exp022a_runner.py`; they fail because the canonical EXP-022A result now exists. They are unrelated to the EXP-023 runner.
- Exclusion verification: `PYTHONPATH=. pytest -q --ignore=tests/test_exp022a_runner.py`
- Exclusion result: `616 passed, 2 skipped`

## Known warnings

- Existing scikit-learn `FutureWarning` about the `penalty` constructor argument appears in unrelated prior-experiment tests. It is not introduced by the EXP-023 runner and is not a blocking engineering defect.

## Boundary

- `MODEL_LOAD_PERFORMED = false`
- `TOKENIZER_LOAD_PERFORMED = false`
- `FORMAL_FIT_PERFORMED = false`
- `FORMAL_EVAL_PERFORMED = false`
- `FORMAL_BOOTSTRAP_PERFORMED = false`
- `EXP023_SCIENTIFIC_RESULT_CREATED = false`
- `EXP023_OUTCOME_OBSERVED = false`
- `EXP023_FORMAL_RUN_AUTHORIZED = false`

## Next required step

`REAL MODEL/HOOK ENGINEERING QUALIFICATION` under Task 096B. Do not issue a
formal authorization or launch EXP-023 from this preflight.
