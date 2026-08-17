# EXP-023 Runner Preflight

Status: `EXP023_STATIC_PREFLIGHT_PASS` / `EXP023_SYNTHETIC_PREFLIGHT_PASS` /
`EXP023_MODEL_HOOK_ENGINEERING_QUALIFIED`

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

## Real Model / Hook Engineering Qualification

- Result: `PASS`
- Qualification status: `MODEL_HOOK_ENGINEERING_QUALIFIED`
- Classification: `ENGINEERING_MODEL_HOOK_QUALIFICATION_ONLY`
- Artifact: `experiments/exp023/engineering/model_hook_qualification.json`
- Artifact SHA-256: `3adcb480a6d7da1a62b026aaac8946f914e73099444e26784045a486d49577d6`
- Runner SHA-256: `339a69a997af7521db9c351c191bde0e9749b2cf528efedfd4f3043607830990`
- Repository commit: `8dc252f749f2c11005e4891bea2aa20e3f947611`
- Runtime identity: Python `3.11.9`, torch `2.12.1+cu130`, transformers `5.14.1`, CUDA `13.0`, NVIDIA GeForce RTX 5060 Laptop GPU, `cuda:0`, `torch.float16`
- Model: `Qwen/Qwen3-1.7B`, snapshot `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`, `Qwen3ForCausalLM`, `qwen3`, 28 blocks, hidden size 2048
- Tokenizer: `Qwen2Tokenizer`, offline snapshot, `add_special_tokens=true`
- Hidden-state tuple length `29`: `PASS`
- Block16 hook versus `hidden_states[17]`: `PASS`
- Block26 hook versus `hidden_states[27]`: `PASS`
- Block27 pre-final hook capture: `PASS`
- Final RMSNorm oracle versus `hidden_states[28]`: `PASS`
- Pre/post final-RMSNorm distinction: `PASS`
- Zero-perturbation forward hooks: `PASS`
- Hook cleanup: `PASS`
- Last-valid-token runtime: `PASS`
- Float32 analysis boundary: `PASS`
- All 13 checkpoint extraction identities: `PASS`
- Production extraction path exercised: `true`
- Formal dataset model inference count: `0`
- Formal prompt text exposed: `false`
- Formal run authorized: `false`
- Scientific result created: `false`
- EXP-023 outcome observed: `false`
- Neutral inputs: deterministic engineering-only; only identity hashes recorded

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

- `MODEL_LOAD_PERFORMED = true`
- `TOKENIZER_LOAD_PERFORMED = true`
- `FORMAL_FIT_PERFORMED = false`
- `FORMAL_EVAL_PERFORMED = false`
- `FORMAL_BOOTSTRAP_PERFORMED = false`
- `EXP023_MODEL_HOOK_ENGINEERING_QUALIFIED = true`
- `EXP023_SCIENTIFIC_RESULT_CREATED = false`
- `EXP023_OUTCOME_OBSERVED = false`
- `EXP023_FORMAL_RUN_AUTHORIZED = false`

## Next required step

`TASK 096C TARGETED PRODUCTION-READINESS REREVIEW`. If that rereview passes,
issue one new single-use EXP-023 formal authorization and launch exactly once.
Do not issue a formal authorization or launch EXP-023 from this preflight.
