# EXP-024 Authorization / Formal-Run Readiness Narrow Rereview

Review type: `AUTHORIZATION_READINESS_NARROW_REREVIEW`

Review timestamp: `2026-08-18T15:37:04+00:00`

Final verdict: `READY_FOR_SINGLE_USE_FORMAL_AUTHORIZATION`

This read-only Task-098C-R2 review does not modify the runner, frozen
protocol, frozen dataset, condition panel, schemas, or qualification artifact.
It does not load a model or tokenizer, use formal dataset text, create or
consume a formal authorization, run the scientific experiment, or create a
canonical result.

## Repository Identity

- Branch: `main`
- Entry `HEAD`:
  `f531fabfb9201800e1cd4fcbf1775cca096cf8a7`
- Entry `origin/main`:
  `f531fabfb9201800e1cd4fcbf1775cca096cf8a7`
- Formal-runtime implementation commit:
  `fbd2448dfb3505763f0dfbbe2186502b60489a41`
- Qualification-evidence storage commit:
  `f531fabfb9201800e1cd4fcbf1775cca096cf8a7`
- Tracked worktree clean at entry: `true`
- Staging empty at entry: `true`

Known untracked forensic paths were present and were not staged or modified:

- `exp020a_results.json`
- `experiments/exp021/authorization/`
- `experiments/exp021/consumed/`
- `experiments/exp021/engineering/`
- `experiments/exp023/exp023_formal_run_authorization.json`

None of these paths is the EXP-024 production authorization, consumption, or
canonical-result location.

## Frozen Authorities

Current file hashes:

- Preregistration:
  `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`
- Frozen dataset:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Condition panel:
  `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`
- Data schema:
  `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec`
- Freeze manifest:
  `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`

Git diff from pre-F1 authority commit
`7cd26603a4affd33e7a549bbd57165ebab5b12e0` to current entry `HEAD` showed no
changes to the preregistration, frozen dataset, condition-panel spec, data
schema, or freeze-manifest paths.

Modified flags:

```text
EXP024_R2_FROZEN_PREREG_MODIFIED = false
EXP024_R2_FROZEN_DATASET_MODIFIED = false
EXP024_R2_CONDITION_PANEL_MODIFIED = false
EXP024_R2_DATA_SCHEMA_MODIFIED = false
```

## Original Blocker Closure

The prior blocker was `_execute_formal_after_consumption(...)` raising
`EXP024_FORMAL_RUNTIME_NOT_QUALIFIED_IN_098A`. Current production source shows
that function delegates to `_execute_formal_analysis(...)`, and `run_formal`
calls it after validation and consumption.

- Original formal placeholder closed: `true`
- Production formal runtime is structurally executable: `true`

## Production Formal Call Graph

`run_formal` reaches the following production path:

```text
authorization file load
-> frozen-authority verification
-> canonical-result collision check
-> authorization validation
-> tracked-tree/staging cleanliness checks
-> exclusive single-use authorization consumption
-> formal analysis
   -> frozen dataset load
   -> partition integrity validation
   -> qualified model/tokenizer runtime load
   -> qualified representation extraction
   -> FIT-only reference scaler/classifier fitting
   -> FIT-only condition calibration
   -> DIAGNOSTIC S_diag computation
   -> EVAL G_eval computation
   -> primary Spearman and exact one-sided permutation
   -> result assembly and validation
-> canonical no-clobber publication
```

- Production formal call graph: `PASS`

## Authorization Consumption Safety

`_pre_consumption_static_checks` runs authorization validation before
`_consume_formal_authorization`. Consumption uses `O_CREAT | O_EXCL` for a
single-use record and fails on `FileExistsError`. Formal analysis starts only
after consumption.

- Authorization consumption order: `PASS`
- Post-consumption runtime structurally executable: `true`
- Repeat-use protection: `PASS`

## Formal Hook-Path Binding

Static source audit confirms formal analysis uses
`_load_qualification_runtime` and `_run_qualification_forward`, the same
production loader/tokenizer/forward-hook path exercised by the model-hook
qualification. No separate unqualified formal hook path was found.

- Formal hook path covered by qualification: `true`

## Qualification Identity

- Qualification artifact:
  `experiments/exp024/engineering/model_hook_qualification.json`
- Qualification SHA-256:
  `72e7f48d68a022819cfed5045061af5b0d6d84de659a49e056487b9d20da8d8f`
- Qualification status: `QUALIFICATION_PASSED`
- Qualified runner commit:
  `fbd2448dfb3505763f0dfbbe2186502b60489a41`

Read-only closed-loop validation:

- Standalone qualification validator: `PASS`
- Production qualification verifier: `PASS`
- Authorization-path dry verification: `PASS`

The dry verification used an in-memory authorization object; no authorization
file was created or consumed.

## Runner and Commit Binding Semantics

- Current runner SHA-256:
  `6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`
- Runner bytes unchanged from the F1 implementation commit: `true`
- Production authorization validator binds
  `authorized_repository_commit` to the current repository `HEAD`.
- It binds `authorized_runner_sha256` to the current runner SHA-256.
- The qualification storage commit is not a direct authorization field; the
  authorization binds the qualification content SHA, which then binds the
  runner and frozen authorities through production verification.

Therefore Task 098D must bind `authorized_repository_commit` to the final
post-R2 review commit produced by this task, not to the pre-R2 entry
`f531fabfb9201800e1cd4fcbf1775cca096cf8a7`. The runner SHA must remain
`6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`.

## Historical Qualification Selection

Production qualification verification uses the canonical path
`experiments/exp024/engineering/model_hook_qualification.json`. Historical
qualification files under `qualification_history/` are not consulted by the
authorization verifier.

- Old R4 historical SHA:
  `be1388b8a8e8b73f0589984e0da2cad1c17cc08c93cad7427446469089ec7463`
- Old R4 authorization eligibility for F1 runner: `false`
- Current qualification selection unambiguous: `true`

## Primary-Analysis Spot Audit

Production source is statically consistent with the frozen primary analysis:

- Scientific unit: `condition`
- Number of conditions: `10`
- Primary diagnostic: `S_diag(c)`
- Primary outcome: `G_eval(c)`
- Primary statistic: `Spearman_rho`
- Primary inference: exact one-sided condition-level permutation
- Exact permutation count: `3628800`
- Alpha: `0.05`
- Support criterion: `rho>0_and_p<=0.05`
- Tie handling: average ranks

No Pearson fallback, asymptotic primary p-value, layer/row unit, favorable
condition subset, dynamic primary calibration variant, alternate alpha, or
two-sided rescue was found.

- Primary analysis binding: `PASS`
- Post-hoc primary escape hatch: `NONE`

## FIT / DIAGNOSTIC / EVAL Dataflow

Static spot audit confirms FIT-only calibration fitting, DIAGNOSTIC-only
`S_diag`, EVAL-only `G_eval`, and no outcome-dependent partition selection.

- FIT / DIAG / EVAL dataflow: `PASS`

## Focused Test Evidence

Rerun in this R2 review:

```text
pytest -q tests/test_exp024_runner.py
98 passed, 4 warnings
```

This result is the authoritative focused-suite result for this review.

## Result Publication Gate

Production source still publishes the canonical result only after
authorization consumption, formal analysis, and result validation. It uses
no-clobber atomic publication and keeps failure paths from creating a
canonical result.

- Result publication gate: `PASS`

## Preexisting Formal-State Check

- Preexisting EXP-024 formal authorization: `false`
- Preexisting EXP-024 authorization consumption: `false`
- Preexisting EXP-024 canonical formal result: `false`

Only the tracked preflight artifact and qualification/history evidence are
present under the EXP-024 result/engineering areas; none is a formal
authorization, consumption, or canonical result.

## Authorization Schema Readiness

The production authorization schema and verifier require the exact fields:

```text
schema_version
experiment
authorization_id
single_use
authorized_repository_commit
authorized_runner_sha256
frozen_manifest_sha256
frozen_dataset_sha256
preregistration_sha256
model_name
model_snapshot_identity
model_hook_qualification_sha256
canonical_result_path
authorization_created_at_utc
```

`additionalProperties` is `false`. Task 098D can construct a unique,
schema-valid, single-use authorization against the post-R2 review commit.

- Authorization schema ready: `PASS`

## Task 098D Binding Instruction

```text
EXP024_R2_TASK098D_AUTHORIZATION_BINDING_INSTRUCTION =
Task 098D MUST set authorized_repository_commit to the exact HEAD produced by
this R2 review commit, and MUST keep:
authorized_runner_sha256 =
6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f
model_hook_qualification_sha256 =
72e7f48d68a022819cfed5045061af5b0d6d84de659a49e056487b9d20da8d8f
frozen_manifest_sha256 =
1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59
frozen_dataset_sha256 =
46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404
preregistration_sha256 =
55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810
model_name = Qwen/Qwen3-1.7B
model_snapshot_identity = 70d244cc86ccca08cf5af4e1e306ecf908b1ad5e
canonical_result_path = experiments/exp024/results/exp024_results.json
```

## Scientific Non-Execution

```text
EXP024_R2_MODEL_LOAD_PERFORMED = false
EXP024_R2_TOKENIZER_LOAD_PERFORMED = false
EXP024_R2_FORMAL_DATASET_TEXT_USED = false
EXP024_R2_SCIENTIFIC_ENDPOINT_COMPUTED = false
EXP024_R2_FORMAL_AUTHORIZATION_CREATED = false
EXP024_R2_FORMAL_AUTHORIZATION_CONSUMED = false
EXP024_R2_FORMAL_RUN_PERFORMED = false
EXP024_R2_FORMAL_RESULT_CREATED = false
EXP024_R2_SCIENTIFIC_OUTCOME_OBSERVED = false
```

## Final Verdict

```text
EXP024_098C_R2_FINAL_VERDICT = READY_FOR_SINGLE_USE_FORMAL_AUTHORIZATION
```

The next task is exactly one single-use EXP-024 formal authorization creation
and validation; do not execute the formal run or consume the authorization in
this review.
