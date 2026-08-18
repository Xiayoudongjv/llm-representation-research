# EXP-024 Authorization / Formal-Run Readiness Review

Review timestamp: `2026-08-18T14:47:00+00:00`

Final verdict: `ENGINEERING_AUTHORIZATION_GATE_BLOCKED`

## Repository Identity

- Branch: `main`
- Reviewed HEAD: `6fd91876b1d708b98fefc23a32e81493680c1b78`
- `HEAD == origin/main`: `true`
- Tracked worktree clean: `true`
- Staging empty at review start: `true`
- Preserved untracked forensic paths:
  - `exp020a_results.json`
  - `experiments/exp021/authorization/`
  - `experiments/exp021/consumed/`
  - `experiments/exp021/engineering/`
  - `experiments/exp023/exp023_formal_run_authorization.json`

## Authority Summary

- Frozen preregistration SHA-256:
  `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`
- Frozen dataset SHA-256:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Condition-panel SHA-256:
  `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`
- Data-schema SHA-256:
  `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec`
- Frozen manifest SHA-256:
  `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`
- Dataset record count: `1760`
- Source-family count: `880`
- Condition count: `10`
- Frozen model name: `Qwen/Qwen3-1.7B`
- Frozen model snapshot: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

## Frozen-Protocol Primary Registry

- Reference checkpoint: `block16_pre_final_rmsnorm`
- Final checkpoint: `block27_pre_final_rmsnorm`
- Primary scientific unit: `condition`
- Primary diagnostic: `S_diag(c)`
- Primary outcome: `G_eval(c)`
- Primary statistic: `Spearman_rho`
- Primary inference: exact one-sided condition-level permutation
- Exact permutation count: `3628800`
- Support criterion: `rho>0_and_p<=0.05`
- Alpha: `0.05`
- Tie handling: average ranks
- Post-hoc primary escape hatch found: `NONE`

## R4 Qualification Gate

- Runner patch commit:
  `1f5082e0d8246432157cb43832430ac3214e846a`
- Runner SHA-256:
  `709572c77110eab497d3851f0e998a0c330b5422e8e7cdea5ec9195fae99da76`
- Qualification evidence storage commit:
  `6fd91876b1d708b98fefc23a32e81493680c1b78`
- Canonical qualification artifact:
  `experiments/exp024/engineering/model_hook_qualification.json`
- Canonical qualification artifact SHA-256:
  `be1388b8a8e8b73f0589984e0da2cad1c17cc08c93cad7427446469089ec7463`
- Canonical qualification status: `QUALIFICATION_PASSED`
- Canonical model metadata location:
  `model.model_name`, `model.model_snapshot`

Read-only re-verification results:

- Standalone qualification validator: `PASS`
- Production qualification verifier: `PASS`
- Authorization-path dry verification: `PASS`
- Runner bytes unchanged from patch commit to evidence storage HEAD: `true`

## Commit-Binding Semantics

The runner patch commit and qualification storage commit differ:

- Patched runner commit: `1f5082e0d8246432157cb43832430ac3214e846a`
- Qualification storage commit: `6fd91876b1d708b98fefc23a32e81493680c1b78`

This is acceptable because:

1. `experiments/exp024/run_exp024.py` is byte-identical between those commits.
2. Production authorization binds `authorized_runner_sha256` to the runner file
   content SHA, not to a commit tag.
3. `qualified_runner_commit` remains provenance in the qualification artifact.

Task 098D authorization must bind `authorized_repository_commit` to the final
reviewed HEAD after this readiness-review artifact is committed. The runner
bytes and R4 qualification SHA must remain unchanged.

## Authorization Schema Gate

- Schema path: `experiments/exp024/exp024_formal_run_authorization.schema.json`
- `additionalProperties`: `false`
- `single_use` is constrained to `true`
- Required fields match production `_validate_formal_authorization`
- Model, runner, frozen authority, qualification identity, and result path
  bindings are present and fail-closed

`EXP024_098C_SINGLE_USE_SCHEMA = PASS`

## Consumption-Order Gate

Production `run_formal` performs:

1. frozen-authority verification
2. result-collision verification
3. authorization validation
4. tracked-tree/staging checks
5. authorization consumption via `O_CREAT | O_EXCL`
6. only then `_execute_formal_after_consumption`

`EXP024_098C_CONSUMPTION_ORDER = PASS`

Repeat-use protection is implemented by exclusive atomic consumption record
creation.

`EXP024_098C_REPEAT_USE_PROTECTION = PASS`

## Formal-Runtime Execution Gate

`_execute_formal_after_consumption` is still a fail-closed placeholder:

```text
TechnicalInvalidError: EXP024_FORMAL_RUNTIME_NOT_QUALIFIED_IN_098A
```

No production implementation currently performs formal dataset inference,
reference fitting, condition calibration, `S_diag`, `G_eval`, primary
Spearman/permutation analysis, or canonical formal-result assembly.

This is a blocking engineering gate:

```text
EXP024_098C_FINAL_VERDICT = ENGINEERING_AUTHORIZATION_GATE_BLOCKED
```

Because consumption occurs before the placeholder is reached, issuing an
authorization now would risk consuming it without producing a valid formal
result. Do not issue authorization until the formal runtime is implemented,
qualified, and re-reviewed.

## Prior Formal-State Check

- Preexisting EXP-024 formal authorization: `false`
- Preexisting EXP-024 authorization consumption: `false`
- Preexisting EXP-024 canonical formal result: `false`
- Residual staging/canonical result collision: `NONE`

## Result Publication Gate

- Canonical path is fixed in production: `experiments/exp024/results/exp024_results.json`
- Publication validates the complete formal result object
- Publication checks canonical/staging collision
- Publication uses no-clobber atomic write

`EXP024_098C_RESULT_PUBLICATION_GATE = PASS`

## Non-Scientific Test Results

- Focused EXP-024 runner tests: `86 passed, 2 warnings`
- No model, tokenizer, formal dataset text, or scientific endpoint access
  occurred during this review.

## Review Actions

This task created only the review Markdown and structured JSON. No runner,
validator, frozen authority, qualification artifact, authorization, result, or
formal data was modified.
