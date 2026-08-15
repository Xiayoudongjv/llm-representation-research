# EXP-021 Stage-Q Implementation

## Scope and authority

This document records the implementation boundary for the EXP-021 Stage-Q
measurement-qualification infrastructure. The frozen EXP-021 preregistration
and amendment remain the scientific authorities. This implementation does not
change prompts, splits, layer roles, beta values, probe settings, or gate
criteria.

The runner validates the archived authority files and the execution identity
before any runtime path can proceed. Authority and model paths are confined to
their declared roots, JSON schemas are closed, and publication refuses to
overwrite existing files.

Static preflight validates only authority metadata, small index metadata, file
names, and sizes. It does not stream safetensors payloads. Full seven-file
identity verification is performed only after a separate engineering
authorization has been atomically consumed and before model loading.

## CLI modes

The runner exposes exactly three mutually exclusive modes:

- `--static-preflight`: metadata and implementation checks only;
- `--neutral-hook-qualification`: the separately authorized engineering
  qualification path;
- `--stage-q`: the separately authorized FIT-only measurement path.

There is no Stage-P mode and no implicit fallback between modes.

## Authorization lifecycle

Neutral qualification and Stage-Q use separate, single-use authorization
records with exact scopes. Authorization is validated and atomically consumed
before model loading or diagnostic execution. Reuse, scope mismatch, malformed
schemas, path escape, and publication collisions fail closed.

The implementation creates no authorization and cannot authorize itself. This
task therefore leaves both authorization flags false.

Authorization timestamps, expiry, implementation hashes, authority hashes,
model-manifest identity, runtime requirements, permissions, and the frozen
engineering output path are checked before consumption. Consumption parents
must already exist; consumption and publication use exclusive creation and
never overwrite or retry.

## Neutral hook dependency

Stage-Q is dependent on a passed, separately published neutral hook-oracle
qualification result with matching execution identity and no scientific data.
The oracle is defined at Qwen block 16 (hidden-state index 17), uses one
unpadded prompt and the last valid token, and checks the exact additive hook
operation, target/non-target behavior, invocation count, and tensor
shape/dtype/device invariants.

## Stage-Q computation

Stage-Q is FIT-only. For each checkpoint and split, the fixed probe is trained
using only the remaining intervention-layer FIT representations. The probe is
not tuned on evaluation data and is reused for downstream checkpoint
measurement. Probability columns are mapped through the fitted classifier’s
explicit class order.

The preregistered checkpoints, layer mapping, direction construction, control
conditions, and primary beta remain fixed. Evaluation representations are
never used to fit directions or probes.

After Stage-Q authorization consumption, the source adapter reads the frozen
split manifest and selects exactly twelve FIT-role IDs for one split at a time.
Only those records enter tokenization and forward execution; EVAL records are
not routed, logged, or serialized. The adapter records IDs, split, role, and
class metadata without exposing prompt text in results.

Production execution obtains hidden states 17, 18, 21, 25, and 28, plus a
block-27 pre-final-RMSNorm hook capture. The pre-final-RMSNorm capture remains
the primary final checkpoint; hidden state 28 is descriptive only. Hooks are
removed in `finally` blocks, and every forward is single-sequence,
no-padding, no-truncation, evaluation-mode, no-gradient, and `use_cache=False`.

The engineering result is redacted: it contains split/ID counts and summary
statistics but no prompt text, hidden vectors, individual probabilities,
intervention effects, persistence outcomes, or behavioral results.

## Result classification

The implementation preserves the distinction between technical invalidity and
scientific outcome. Stage-Q requires all checkpoints and splits to be present,
valid, and covered by the exact Clopper–Pearson gate (`k >= 7` and lower bound
greater than `0.25`). A technical failure is invalid rather than a scientific
failure. No result is published unless its closed schema, identity, routing,
and gate checks pass.

Final-layer post-RMSNorm values are descriptive only when produced by the
reviewed path; they are not silently substituted for the preregistered
measurement.

## Prohibited claims

This infrastructure does not establish behavioral control, reasoning gains,
scale invariance, universal representation replication, cognitive-space
transformation, or true task manifolds. It does not authorize formal
execution, and it creates no scientific result in this task.

## Task 088D rereview outcome

Independent Task 088D rereview established three Stage-Q implementation
blockers:

1. the complete neutral-result validation function was not reachable from the
   production neutral qualification publication path;

2. neutral-result drift validation did not fully bind `execution_environment`,
   `diagnostic_vector`, and `neutral_input_identity`;

3. implementation validation and regression coverage remained too
   source/AST-oriented to prove production-entry reachability.

The frozen scientific protocol, amendment, reconciliation artifact,
checkpoint semantics, FIT adapter semantics, LOFO statistics, global gate,
hook mathematics, authorization model, and Stage-P boundaries were not
changed.

## Task 088E corrections

Task 088E closes only the three Task-088D blockers.

### Blocker 1

`run_neutral_hook_qualification()` now calls the complete
`validate_neutral_result(result, authority, binding)` as its publication gate
immediately before `atomic_publish_json()`. The previous local
`require_exact_keys()` call was replaced, so schema-only publication is no
longer possible.

### Blocker 2

`validate_neutral_result()` now delegates to three closed validators:

- `_validate_neutral_execution_environment()`;
- `_validate_neutral_diagnostic_vector()`;
- `_validate_neutral_input_identity()`.

The corrected complete validator is the same function used by Stage-Q before
authorization consumption, so a neutral result that is drifted in any bound
identity category cannot be published or reused downstream.

### Blocker 3

The implementation validator now requires:

- `run_neutral_hook_qualification()` calls `validate_neutral_result()` before
  `atomic_publish_json()`;
- `validate_neutral_result()` calls all three identity-category validators;
- the synthetic regression suite contains dynamic production-entry tests that
  invoke the real `run_neutral_hook_qualification()` and `run_stage_q()`
  functions with mocked model/tokenizer/data/runtime dependencies.

Static AST presence is treated as a necessary but not sufficient contract;
runtime call-graph order is checked by the dynamic tests.

## Corrected neutral publication trust chain

The production neutral qualification path is ordered as follows:

1. authority/static validation;
2. authorization validation and single-use consumption;
3. full model manifest verification;
4. model and tokenizer loading;
5. no-hook forward;
6. inactive-hook forward;
7. active-hook forward and exact oracle check;
8. complete `validate_neutral_result()`;
9. atomic publication.

If complete validation raises, atomic publication is not called. If the
validator is removed or sabotaged, the dynamic regression contract fails.

## Neutral identity drift binding

### `execution_environment`

Exact keys required:

`python`, `torch`, `transformers`, `cuda_runtime`, `nvidia_driver`, `gpu`,
`dtype`, `device`, `local_files_only`, `model_eval_mode`,
`gradients_enabled`, `use_cache`.

Frozen deterministic values must match exactly:

- `dtype = float16`;
- `device = cuda:0`;
- `local_files_only = true`;
- `model_eval_mode = true`;
- `gradients_enabled = false`;
- `use_cache = false`.

The remaining runtime identity fields are exact-bound against an independent
`runtime_identity_binding()` produced from:

- `sys.version` for Python;
- `torch.__version__` for torch;
- installed `transformers` metadata;
- `torch.version.cuda` for CUDA runtime;
- `nvidia-smi` for NVIDIA driver and GPU identity.

Actual and expected values are independently sourced: the result carries the
neutral qualification runtime environment, while validation uses the current
execution binding, not the result itself.

### `diagnostic_vector`

Exact keys required:

- `algorithm = alternating_plus_minus_one`;
- `length = 2048`;
- `sha256 = deterministic_diagnostic_vector(2048)`.

### `neutral_input_identity`

Exact keys required:

- `sha256 = _neutral_input_identity()`.

Each category is a closed schema: missing, extra, or drifted fields fail.

## Dynamic production-entry regression coverage

The synthetic suite now proves both production entries through monkeypatched
dependencies:

- neutral valid path reaches `validate_neutral_result()` exactly once before
  `atomic_publish_json()`;
- neutral environment drift raises and does not publish;
- neutral validator removal is detected by the publication-order contract;
- Stage-Q valid path validates the live neutral result before
  `consume_authorization()`;
- Stage-Q drifted neutral identity raises before authorization consumption,
  model load, FIT adapter access, or publication.

These tests use pytest temporary directories and no real model, tokenizer,
CUDA/GPU, FIT/EVAL, network, or formal-data access.

## Task 088F rereview outcome

Independent Task 088F passed Blocker 1 and Blocker 3. It left Blocker 2 open
because the dynamic runtime identity fields were only presence-checked and were
not exact-bound to an independent expected runtime identity.

## Task 088G correction

Task 088G closes the remaining dynamic runtime identity binding defect without
changing scientific semantics. The runner now reuses one canonical runtime
identity constructor for neutral result construction, neutral result
validation, and Stage-Q live drift validation. Wrong-but-non-empty values for
all six dynamic runtime fields are rejected, and Stage-Q runtime drift stops
before authorization consumption, model verification, model/tokenizer loading,
FIT adapter access, or publication.

No runtime qualification has been performed. Stage-Q remains unauthorized.
Scientific status remains `NOT_STARTED`.

## Status

```text
EXP021_SCIENTIFIC_STATUS = NOT_STARTED

EXP021_HOOK_ORACLE_PROTOCOL_STATUS = FROZEN
EXP021_HOOK_ORACLE_RUNTIME_QUALIFIED = false

EXP021_STAGE_Q_IMPLEMENTED = true
EXP021_STAGE_Q_AUTHORIZABLE = false
EXP021_STAGE_P_AUTHORIZABLE = false
```

Stage-Q remains engineering/measurement qualification only. Task 088G does
not authorize neutral qualification, Stage-Q, Stage-P, formal inference, or
any scientific result.

## Next review

Independent review must inspect the implementation, authority checks,
authorization lifecycle, neutral-result dependency, FIT/EVAL routing, and
closed result schemas before any authorization or runtime qualification is
considered. Model loading, tokenizer loading, neutral qualification, Stage-Q,
Stage-P, formal inference, and scientific result publication remain blocked
until those reviews and their separate gates pass.
