# EXP-024 Formal Runtime Implementation Report

Status: `FORMAL_RUNTIME_IMPLEMENTED_AND_FRESHLY_QUALIFIED`

This report records the Task-098C-F1 implementation that replaced the
previously blocking placeholder in `experiments/exp024/run_exp024.py`. It does
not create a formal authorization, consume one, run the real EXP-024 scientific
experiment, or observe a scientific outcome.

## Previous Blocker

The prior authorization-readiness review reported:

```text
EXP024_098C_FINAL_VERDICT = ENGINEERING_AUTHORIZATION_GATE_BLOCKED
```

`_execute_formal_after_consumption(...)` raised:

```text
TechnicalInvalidError("EXP024_FORMAL_RUNTIME_NOT_QUALIFIED_IN_098A")
```

The consumption order was already correct, but consuming an authorization
would have led to a known structural non-executability.

## Entry Repository Identity

- Branch: `main`
- Entry HEAD:
  `7cd26603a4affd33e7a549bbd57165ebab5b12e0`
- Entry `origin/main`:
  `7cd26603a4affd33e7a549bbd57165ebab5b12e0`
- Tracked worktree clean at entry: `true`
- Staging empty at entry: `true`

Preserved untracked forensic paths were not staged or modified:

- `exp020a_results.json`
- `experiments/exp021/authorization/`
- `experiments/exp021/consumed/`
- `experiments/exp021/engineering/`
- `experiments/exp023/exp023_formal_run_authorization.json`

## Implemented Runner Identity

- Formal-runtime implementation commit:
  `fbd2448dfb3505763f0dfbbe2186502b60489a41`
- Production runner:
  `experiments/exp024/run_exp024.py`
- Runner SHA-256 after implementation:
  `6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`
- Placeholder removed: `true`
- Frozen protocol modified: `false`
- Frozen dataset modified: `false`
- Condition panel modified: `false`
- Data schema modified: `false`

## Implementation Call Graph

`_execute_formal_after_consumption` now delegates to
`_execute_formal_analysis`, which performs:

```text
frozen authority verification
-> canonical result collision check
-> condition-panel order verification
-> formal dataset loading
-> explicit FIT / DIAGNOSTIC / EVAL integrity validation
-> exact model/tokenizer loading through qualified runtime
-> registered representation extraction
-> FIT-only reference scaler and C_ref fitting
-> FIT-only per-condition final calibration fitting
-> DIAGNOSTIC S_diag computation
-> EVAL G_eval computation
-> condition-level descriptive secondary outcomes
-> primary Spearman and exact one-sided permutation
-> formal result assembly
-> result schema validation
```

`run_formal` preserves the prior ordering:

```text
authorization validation
-> exclusive single-use consumption
-> formal scientific execution
-> result validation
-> canonical no-clobber publication
```

## FIT / DIAGNOSTIC / EVAL Isolation

`_validate_formal_partition_integrity` fail-closes before any science on:

- missing record fields
- unknown condition, semantic class, partition, or role
- duplicate record IDs
- malformed family role pairs
- cross-partition source-family overlap
- missing condition/class cells
- incorrect frozen cell counts

FIT is the only partition used for:

- reference scaler fitting
- fixed `C_ref` classifier fitting
- condition-specific `mu_final,c` and `sigma_final,c` estimation

DIAGNOSTIC is the only partition used for `S_diag`.

EVAL is the only partition used for `G_eval`, `G_mu`, `G_sigma`, and the joint
descriptive decompositions.

## Frozen Readout and Calibration Bindings

- Reference checkpoint: `block16_pre_final_rmsnorm`
- Final checkpoint: `block27_pre_final_rmsnorm`
- Reference classifier: one frozen LogisticRegression contract
- Reference scaler: frozen `StandardScaler` contract
- Calibration variants: `A0`, `A_mu`, `A_sigma`, `A_mu_sigma`
- Classifier output labels map through `classifier.classes_`
- Calibration parameters are estimated only from FIT condition-realization
  records at `block27_pre_final_rmsnorm`

## Primary Analysis Bindings

```text
S_diag(c) = BA_A0(block16_pre_final_rmsnorm, DIAG_c)
          - BA_A0(block27_pre_final_rmsnorm, DIAG_c)

G_eval(c) = BA_A_mu_sigma(block27_pre_final_rmsnorm, EVAL_c)
          - BA_A0(block27_pre_final_rmsnorm, EVAL_c)

rho_primary = Spearman(S_diag(c), G_eval(c))
p = count(rho_perm >= rho_observed) / N!
N! = 3628800
alpha = 0.05
supported = rho_primary > 0 AND p <= 0.05
```

Condition is the only primary inference unit. No condition, layer, checkpoint,
classifier, or outcome-dependent primary escape hatch is added.

## Formal Result Assembly

The assembled result includes the frozen result schema fields plus:

- experiment, runner, model, dataset, class identities
- condition-level `S_diag`, `G_eval`, `G_mu`, `G_sigma`, and joint metrics
- DIAGNOSTIC/EVAL/reference balanced-accuracy tables
- primary Spearman, exact permutation count, p-value, and support verdict
- provenance for authorization and consumption identities
- `hidden_states_included = false`
- `prompt_text_included = false`

`validate_result_schema(result, formal=True)` is called before publication.

## Tests

- Focused EXP-024 runner tests: `98 passed, 4 warnings`
- Static freeze validation: `PASS`
- Static preflight: `PASS`
- Full suite with `PYTHONPATH=.`: `788 passed, 2 skipped, 5 failed`
- Full-suite failures are pre-existing canonical-result collision failures in
  `tests/test_exp022a_runner.py` and `tests/test_exp023_runner.py`, unrelated to
  this EXP-024 implementation.

Added synthetic production-path tests cover:

- complete formal analysis through injected records/runtime
- production call-graph ordering
- failure without canonical publication
- atomic publication to `tmp_path`
- FIT/DIAG/EVAL leakage mutations
- malformed condition/class/duplicate-family fail-closed cases

## Fresh Qualification

A fresh real model/tokenizer/hook qualification was run on the new runner
commit because changing the runner invalidated the prior qualification binding.

- Fresh qualification artifact:
  `experiments/exp024/engineering/model_hook_qualification.json`
- Fresh qualification SHA-256:
  `72e7f48d68a022819cfed5045061af5b0d6d84de659a49e056487b9d20da8d8f`
- Fresh qualification status: `QUALIFICATION_PASSED`
- Qualified runner commit:
  `fbd2448dfb3505763f0dfbbe2186502b60489a41`
- Qualified runner SHA-256:
  `6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`

All required qualification checks passed:

- Reference checkpoint: `PASS`
- Final checkpoint: `PASS`
- Hook firing cardinality: `PASS`
- Hook cleanup: `PASS`
- Owned hooks remaining: `0`
- Repeatability: `PASS`, max absolute difference `0.0`
- Representation finite: `PASS`
- Representation output dtype: `float32`

## Qualification Producer / Consumer Closure

- Standalone qualification validator: `PASS`
- Production qualification verifier: `PASS`
- Authorization-path dry verification: `PASS`

The fresh qualification SHA is the only authorization-eligible model-hook
qualification for the implemented runner.

## Historical R4 Binding

The pre-implementation R4 qualification artifact is preserved at:

`experiments/exp024/engineering/qualification_history/model_hook_qualification_1f5082e_709572c7_R4_passed.json`

- Historical R4 qualification SHA-256:
  `be1388b8a8e8b73f0589984e0da2cad1c17cc08c93cad7427446469089ec7463`
- Authorization eligibility for the F1 runner: `false`

## Scientific Non-Execution

- Formal dataset record content used: `false`
- Formal dataset text tokenized: `false`
- Real representation extraction performed: `false`
- Formal classifier fit performed: `false`
- Formal recalibration performed: `false`
- Formal balanced accuracy computed: `false`
- `S_diag` computed: `false`
- `G_eval` computed: `false`
- Primary Spearman computed: `false`
- Primary permutation test performed: `false`
- Formal authorization created: `false`
- Formal authorization consumed: `false`
- Formal result created: `false`
- Scientific outcome observed: `false`

Synthetic fixture analogues were used only in isolated tests and are not
recorded as EXP-024 scientific computations.

## Next Gate

```text
EXP024_098C_F1_STATUS = FORMAL_RUNTIME_IMPLEMENTED_AND_FRESHLY_QUALIFIED
EXP024_098C_F1_GATE = READY_FOR_NARROW_AUTHORIZATION_READINESS_REREVIEW
```

The next task is `Task 098C-R2`: a narrow independent authorization-readiness
rereview. It must not issue the formal authorization. Task 098D may create one
single-use authorization only after R2 passes.
