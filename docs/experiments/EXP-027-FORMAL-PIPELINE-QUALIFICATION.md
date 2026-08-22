# EXP-027 Formal Pipeline Qualification

Task: `102D_EXP027_FORMAL_PIPELINE_QUALIFICATION`

Status: `EXP027_102D_FORMAL_PIPELINE_QUALIFICATION_COMPLETE`

This qualification is engineering-only. It did not create an EXP-027 formal
authorization, did not consume a real authorization, did not access real
FIT/DIAG/EVAL records through model inference, and did not create a scientific
result.

## Repository

- Branch: `main`
- Entry HEAD: `b9155a71986697a33b12c17e179a0ff650752fcb`
- Final qualification HEAD: `b9155a71986697a33b12c17e179a0ff650752fcb`
- Origin/main at qualification: `b9155a71986697a33b12c17e179a0ff650752fcb`
- Tracked tree: clean at entry
- Staging: empty at entry
- Historical untracked EXP-020A/EXP-021/EXP-023/EXP-024/EXP-025/EXP-026 evidence preserved.

## Qualification Artifact

- Path: `experiments/exp027/engineering/exp027_formal_pipeline_qualification.json`
- SHA-256: `b5eacfc95e17c085827227d4b7abc26dea2d7fddb0771bf577171841b486ee70`

## Runner

- Path: `experiments/exp027/run_exp027.py`
- SHA-256: `0b61655d47b464dc204f92d85bab314aaaceb23fd4d751345c6e314de62bcd4b`
- Supported modes:
  - `--static-preflight`
  - `--synthetic-preflight`
  - `--neutral-model-preflight`
  - `--formal-run`
- Scientific runtime override surfaces: none.

## Result Validator

- Path: `experiments/exp027/validate_exp027_result.py`
- SHA-256: `ee888a3122cf85c67a987ae6c05ef0079678e267d559e40a0a77c77efe63f21d`

## Preflight Results

- Static preflight: `PASS`
  - Artifact: `experiments/exp027/engineering/exp027_static_preflight.json`
  - SHA-256: `efb73a9c0443e492bb16dcf3b957c0596fa5389cf4bafe08578d7b7ed06c61e5`
- Synthetic end-to-end: `PASS`
  - Artifact: `experiments/exp027/engineering/exp027_synthetic_preflight.json`
  - SHA-256: `9f3c227e6dcc0b4dce246a72552b96340166139564e0e9e67f08b8b87546e8fa`
  - Integrated route: `THIRD_REGISTERED_PROFILE`
  - Optimized/reference bootstrap CI equivalence: `true`
- Neutral model preflight: `NOT_REQUIRED_WITH_JUSTIFICATION`
  - Artifact: `experiments/exp027/engineering/exp027_neutral_model_preflight.json`
  - SHA-256: `efd535c53eae33191cb1fd384435d1b49fc4e759240317a48d332189c145dde3`
  - Justification: Task 102A-LQ already qualified the exact local Llama runtime, carrier hooks, dtype, hidden size, layer count, tokenizer contract, and neutral extraction semantics. Repeating expensive real-model checks would not improve authority.

## Frozen Carrier / Hook Contract

- Third model: `Meta-Llama-3.2-1B-Instruct`
- Model source: `META_OFFICIAL_NATIVE_DISTRIBUTION`
- Converted checkpoint SHA-256: `1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f`
- Logical decoder layers: `0..15`
- Hidden size: `2048`
- Formal carrier: `FORWARD_HOOK_DECODER_BLOCK_OUTPUT`
- Block-15 hook semantics: `post_decoder_block_residual_before_model_final_RMSNorm`
- Forbidden carrier: `outputs.hidden_states[-1]`
- Extraction order: `last valid token -> detach -> CPU -> float32 -> NumPy`

## Completion Gate

| Gate | Result |
| --- | --- |
| `FORMAL_RUNNER_IMPLEMENTED` | `true` |
| `FORMAL_RUNNER_MATCHES_FROZEN_DESIGN` | `true` |
| `STATIC_PREFLIGHT_PASS` | `true` |
| `SYNTHETIC_END_TO_END_PASS` | `true` |
| `NEUTRAL_MODEL_PREFLIGHT_NOT_REQUIRED_WITH_JUSTIFICATION` | `true` |
| `AUTHORIZATION_FAIL_CLOSED` | `true` |
| `SINGLE_USE_CONSUMPTION_CONTRACT_VERIFIED` | `true` |
| `CRASH_SEMANTICS_VERIFIED` | `true` |
| `NO_AUTOMATIC_RETRY` | `true` |
| `OUTCOME_BLIND_PROGRESS_VERIFIED` | `true` |
| `RATE_LIMITED_PROGRESS_VERIFIED` | `true` |
| `ATOMIC_PUBLICATION_VERIFIED` | `true` |
| `RESULT_COLLISION_FAIL_CLOSED` | `true` |
| `RESULT_SCHEMA_VALIDATED` | `true` |
| `OPTIMIZED_BOOTSTRAP_INTEGRATION_EQUIVALENT` | `true` |
| `NO_QWEN_OLMO_RERUN_PATH` | `true` |
| `NO_SCIENTIFIC_RUNTIME_OVERRIDES` | `true` |
| `LOW_D_LEAKAGE_FIREWALL_PRESERVED` | `true` |
| `FINAL_RMSNORM_TRAP_PRESERVED` | `true` |
| `ALL_TARGETED_TESTS_PASS` | `true` |

## Authorization Contract

- Missing authorization: rejected before formal data access.
- Malformed authorization: rejected.
- Wrong HEAD, runner hash, frozen-design hash, preregistration hash, model hash, or dataset hash: rejected by binding mismatch.
- Already-consumed authorization: rejected with `FORMAL_AUTHORIZATION_ALREADY_CONSUMED`.
- Consumption is atomic and happens before scientific inference.
- A crash after consumption does not permit automatic retry or reauthorization.

## Progress Contract

- Progress is outcome-blind and stage-level only.
- No route, support class, SDI, LOW-D, CI, matrix cell, or profile value is emitted before publication.
- Optional state file is atomic and uses only allowed progress keys.
- Formal CLI has no scientific runtime override flags.

## Test Evidence

Commands and results:

- `python experiments/exp027/validate_exp027_preregistration.py`: PASS
- `python -m pytest tests/test_exp027_preregistration.py -q`: `17 passed`
- `python -m pytest tests/test_exp027_102c_adversarial.py -q`: `105 passed`
- `python -m pytest tests/test_exp027_bootstrap_optimized_prototype.py tests/test_exp027_progress.py -q`: `13 passed`
- `python -m pytest tests/test_exp027_formal_pipeline.py -q`: `37 passed`

## Scientific Firewall

- `REAL_FIT_ACCESSED=false`
- `REAL_DIAG_ACCESSED=false`
- `REAL_EVAL_ACCESSED=false`
- `LLAMA_SCIENTIFIC_INFERENCE_PERFORMED=false`
- `SCIENTIFIC_MATRIX_COMPUTED=false`
- `SCIENTIFIC_RESULT_CREATED=false`
- `FORMAL_AUTHORIZATION_CREATED=false`
- `FORMAL_AUTHORIZATION_CONSUMED=false`
- `FORMAL_RUN_PERFORMED=false`

## Next Task

`102E_EXP027_SINGLE_USE_FORMAL_AUTHORIZATION`

No formal command is authorized by this document. The eventual formal run remains
`FUTURE_FORMAL_COMMAND_NOT_AUTHORIZED` until Task 102E issues a single-use
authorization and a human launches exactly one command from VSCode PowerShell.
