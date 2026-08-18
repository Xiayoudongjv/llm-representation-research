# EXP-024 Runner and Static Preflight

Status: `EXP024_STATIC_PREFLIGHT_PASS`

This document records the Task-098A runner implementation and deterministic
static preflight. No model, tokenizer, hidden-state extraction, formal
classifier fitting, or scientific outcome was produced in this task.

## Runner Architecture

- Production runner: `experiments/exp024/run_exp024.py`
- Result schema: `experiments/exp024/exp024_result_schema.json`
- Authorization schema: `experiments/exp024/exp024_formal_run_authorization.schema.json`
- Static preflight artifact: `experiments/exp024/results/runner_preflight.json`
- Focused tests: `tests/test_exp024_runner.py`

The CLI requires exactly one explicit mode:

- `--static-preflight`
- `--model-hook-qualification`
- `--formal-run`

No mode fails closed. Task-098A executes only `--static-preflight`.

## Frozen Authority Binding

All production modes verify exact SHA-256 identities before mode-specific work:

- Frozen dataset:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Final preregistration:
  `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`
- Frozen manifest:
  `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`
- Model revision:
  `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

Any drift raises `ProtocolIntegrityError`; no warning-and-continue path exists.

## Production Call Graph

The formal-run path is ordered:

1. Parse mode and repository identity.
2. Validate frozen authority identities.
3. Reject if a canonical result already exists.
4. Validate authorization schema and all bindings.
5. Atomically consume the single-use authorization.
6. Only then execute formal data/model computation.
7. Validate the complete result object.
8. Atomically publish the canonical result with no-clobber.

This order is enforced in code and tested with monkeypatched sentinels.

## Partition Separation

`FIT`, `DIAGNOSTIC`, and `EVAL` records are derived from explicit metadata and
kept disjoint:

- Reference `C_ref` uses only FIT `reference_form` records.
- Condition-specific recalibration uses only FIT `condition_realization`
  records.
- `S_diag` uses only DIAGNOSTIC records.
- `G_eval` uses only EVAL records.

No helper accepts the full dataset and chooses a partition through an
unreviewable internal branch.

## Readout and Calibration Wiring

- Deterministic class order: `logic`, `causality`, `analogy`, `definition`.
- Classifier probability/label mapping uses `classifier.classes_`.
- Reference scaler and fixed `C_ref` are fit from the registered reference-FIT
  pool only.
- Condition-specific final FIT means/scales are derived per condition.
- `A0`, `A_mu`, `A_sigma`, and `A_mu_sigma` use the frozen formulas.
- Primary outcome remains `A_mu_sigma - A0`; `A_mu` and `A_sigma` are secondary.

## Primary Analysis Implementation

- `S_diag(c) = BA_A0(block16_pre_final_rmsnorm, DIAG_c) - BA_A0(block27_pre_final_rmsnorm, DIAG_c)`
- `G_eval(c) = BA_A_mu_sigma(block27_pre_final_rmsnorm, EVAL_c) - BA_A0(block27_pre_final_rmsnorm, EVAL_c)`
- Primary statistic: `Spearman_rho` over exactly 10 condition units.
- Tie handling: standard average ranks.
- Primary test: exact one-sided condition-level permutation.
- Exact permutation count: `3628800`.
- Support rule: `rho_primary > 0` and exact one-sided `p <= 0.05`.

The exact permutation implementation uses `itertools.permutations` and the
rank-centered Spearman/Pearson equivalence. It does not use Monte Carlo.

## Authorization and Publication

- Authorization schema is implemented; no live authorization instance was
  created.
- Consumption uses atomic `O_CREAT | O_EXCL`.
- Result publication uses validated staging plus no-clobber hard-link
  publication.
- The production call path invokes result validation before publication.
- Incomplete or invalid result objects cannot publish.

## Test Coverage

Focused tests cover frozen identities, no candidate fallback, explicit pairing
metadata, deterministic class mapping, partition disjointness, FIT-only
readout/recalibration, DIAG-only `S_diag`, EVAL-only `G_eval`, balanced
accuracy, average-rank ties, Spearman, exact-permutation equivalence and
denominator, one-sided `>=` rule, primary support rule, secondary non-replacement,
formal-mode fail-closed behavior, stale runner/qualification rejection,
single-use consumption, production call order, no-clobber publication, result
validation reachability, static-preflight model absence, qualification
formal-data isolation, and no-mode failure.

## Static Preflight Result

- Runner SHA-256:
  `7a20264725c7963904c2cce12e1a68705778d3716f7ceaf09f1ab708b0798717`
- Preflight artifact SHA-256:
  `d146e64f3825051f5a6dea5978272ea2acef53e0ecf65077e9f5e62d42409df7`
- Frozen dataset record/family counts: `1760 / 880`
- Condition count: `10`
- Semantic class count: `4`
- FIT / DIAGNOSTIC / EVAL families: `240 / 320 / 320`
- `EXP024_STATIC_PREFLIGHT = PASS`

## Known Implementation Limitations

- Task-098A does not execute model/hook qualification or formal run.
- The formal-run mode is implemented fail-closed and requires a future
  single-use authorization plus a valid model/hook qualification artifact.
- Full repository `pytest -q` remains blocked by pre-existing collection errors
  in unrelated tests (`ModuleNotFoundError: No module named 'src'` and
  `No module named 'experiments'`). The focused EXP-024 suite passes
  `31 passed`.

## Explicit Statement

```text
NO MODEL / SCIENTIFIC RUN PERFORMED
```

- `MODEL_LOAD_PERFORMED = false`
- `TOKENIZER_LOAD_PERFORMED = false`
- `REPRESENTATION_EXTRACTION_PERFORMED = false`
- `FORMAL_DATA_INFERENCE_PERFORMED = false`
- `FORMAL_CLASSIFIER_FIT_PERFORMED = false`
- `MODEL_HOOK_QUALIFICATION_PERFORMED = false`
- `FORMAL_AUTHORIZATION_CREATED = false`
- `FORMAL_AUTHORIZATION_CONSUMED = false`
- `SCIENTIFIC_OUTCOME_OBSERVED = false`
- `FORMAL_RESULT_CREATED = false`

## 098B Qualification Implementation Patch

Previous state:
`QUALIFICATION_ENTRYPOINT_PRESENT_RUNTIME_MISSING`

New state:
`QUALIFICATION_RUNTIME_IMPLEMENTED_NOT_YET_RUN`

The `--model-hook-qualification` mode now routes to the real non-formal
qualification runtime. This patch does not execute that runtime against the
real model.

### Qualification Call Graph

The production qualification path is ordered:

1. Validate frozen authority file hashes only.
2. Obtain the fixed qualification-only neutral inputs.
3. Load the registered local tokenizer.
4. Load the registered local model and validate architecture.
5. Run neutral forward passes with the shared checkpoint-extraction path.
6. Validate the qualification result.
7. Publish the technical qualification artifact with no-clobber.

The path does not call `load_frozen_dataset`, `partition_records`,
`fit_reference_classifier`, `fit_scaler`, `compute_S_diag`, `compute_G_eval`,
or formal-result publication.

### Neutral-Input Firewall

Qualification uses exactly four deterministic neutral engineering strings
bound by the runner source SHA. They are not EXP-024 records, paraphrases,
condition templates, or scientific labels. The runner does not deserialize
formal record text during qualification.

### Shared Production Extraction Path

The same checkpoint extraction helpers are used by qualification and are
available for the future formal runtime:

- `last_valid_token_indices`
- `select_last_valid_token_at_indices`
- `extract_block_hidden_state`
- `ForwardHookCapture`
- `block_output_hook_capture`
- `extract_checkpoint_tensors`
- `extract_last_token_representations`
- `to_float32_analysis_array`

Reference checkpoint:
`block16_pre_final_rmsnorm` / `hidden_states[17]`

Final checkpoint:
`block27_pre_final_rmsnorm` via a forward hook on
`model.model.layers[27]`

Secondary checkpoint:
`block27_post_final_rmsnorm` / `hidden_states[28]`

### Model / Tokenizer Loading

Qualification loads the exact local snapshot:

`D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-1.7B\snapshots\70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

with `local_files_only=True`, `HF_HUB_OFFLINE=1`, and
`TRANSFORMERS_OFFLINE=1`. No network fallback or alternate model is used.
Architecture validation requires `Qwen3ForCausalLM`, `model_type=qwen3`,
28 blocks, hidden size 2048, and 28 transformer layers.

### Hook and Materialization Checks

- Forward hooks are observational and removed in `finally`.
- Hook firing cardinality must be exactly one for each qualification pass.
- Repeatability uses two identical neutral forward passes.
- Selected checkpoint vectors are detached, moved to CPU, converted to
  `float32`, and checked for finite values.
- Qualification artifacts store only shape, dtype, finite status, norm, and
  SHA-256 digest; raw hidden-state vectors are not persisted.

### Qualification Validator

`validate_model_hook_qualification` checks runner SHA, runner source commit,
frozen authority hashes, model/tokenizer metadata, neutral-input count,
checkpoint checks, hook checks, repeatability, materialization, and formal-data
firewall flags. `publish_model_hook_qualification` calls the validator before
the no-clobber atomic write.

### Patch-Task Statement

`EXP024_MODEL_HOOK_QUALIFICATION_PERFORMED = false`

No real model, tokenizer, hidden state, or formal dataset inference was
executed by this patch task.

## Hook-Ownership Cleanup Correction

The first real Task-098B qualification exposed a false-positive cleanup
criterion. All runtime checks passed except `hook_cleanup`.

Old criterion:

`target module total forward hooks after qualification == 0`

Correct criterion:

`all EXP-024-owned hook handles removed`

Transformers may legitimately install and retain its own internal
`output_capturing_hook` on `model.model.layers[27]` after a forward pass with
`output_hidden_states=True`. Such foreign hooks are not EXP-024 state and must
not be removed by EXP-024 qualification.

The historical failed qualification artifact remains:

`experiments/exp024/engineering/model_hook_qualification.json`

SHA-256:

`b46e9b78a7ae8f8725d86f52f0dc4fae61be6fce8025de1d661954e6d469f0c8`

Its status is `QUALIFICATION_FAILED` and it is not authorization-eligible
evidence for the current or future runner.
