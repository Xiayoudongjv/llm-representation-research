# EXP-024 Authorization / Formal-Run Readiness Review

Review timestamp: `2026-08-18T15:20:00+00:00`

Final verdict: `READY_FOR_NARROW_AUTHORIZATION_READINESS_REREVIEW`

This is the current readiness artifact after Task-098C-F1 implemented and
freshly qualified the formal execution runtime. The prior blocked-review text
is superseded and preserved in the git history of the previous commit.

## Current Repository Identity

- Branch: `main`
- Reviewed HEAD: `fbd2448dfb3505763f0dfbbe2186502b60489a41`
- `HEAD == origin/main`: `true`
- Tracked worktree clean after evidence commit: pending Commit 2 verification
- Staging empty after evidence commit: pending Commit 2 verification

## Current Runner Identity

- Runner implementation commit:
  `fbd2448dfb3505763f0dfbbe2186502b60489a41`
- Runner SHA-256:
  `6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`
- Placeholder removed: `true`
- Production formal call graph: `PASS`
- Frozen protocol / dataset / condition panel / data schema modified: `false`

## Current Qualification Identity

- Fresh qualification artifact:
  `experiments/exp024/engineering/model_hook_qualification.json`
- Fresh qualification SHA-256:
  `72e7f48d68a022819cfed5045061af5b0d6d84de659a49e056487b9d20da8d8f`
- Qualification status: `QUALIFICATION_PASSED`
- Qualified runner commit:
  `fbd2448dfb3505763f0dfbbe2186502b60489a41`
- Qualified runner SHA-256:
  `6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`

Closed-loop verification:

- Standalone qualification validator: `PASS`
- Production qualification verifier: `PASS`
- Authorization-path dry verification: `PASS`

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

## Formal Runtime Gates

- FIT / DIAGNOSTIC / EVAL isolation: `PASS`
- Fixed reference classifier binding: `PASS`
- Calibration parameters FIT-only: `PASS`
- Primary inference unit condition: `PASS`
- Primary analysis binding: `PASS`
- Result assembly / schema validation: `PASS`
- Atomic no-clobber publication: `PASS`
- Failure without canonical publication: `PASS`

## Historical R4 Qualification

The pre-implementation R4 qualification remains historical evidence and is not
authorization-eligible for the F1 runner.

- Historical path:
  `experiments/exp024/engineering/qualification_history/model_hook_qualification_1f5082e_709572c7_R4_passed.json`
- Historical SHA-256:
  `be1388b8a8e8b73f0589984e0da2cad1c17cc08c93cad7427446469089ec7463`
- F1 authorization eligibility: `false`

## Test Results

- Focused EXP-024 runner tests: `98 passed, 4 warnings`
- Static freeze validation: `PASS`
- Static preflight: `PASS`
- Full suite with `PYTHONPATH=.`:
  `788 passed, 2 skipped, 5 pre-existing unrelated failures`

The five full-suite failures are canonical-result collision failures in
`tests/test_exp022a_runner.py` and `tests/test_exp023_runner.py`; no EXP-024
test fails.

## Scientific Non-Execution

- Formal dataset record content used: `false`
- Formal dataset text tokenized: `false`
- Real representation extraction performed: `false`
- Formal classifier fit / recalibration / balanced accuracy: `false`
- `S_diag` / `G_eval` / primary Spearman / primary permutation: `false`
- Formal authorization created or consumed: `false`
- Formal result created: `false`
- Scientific outcome observed: `false`

## Next Gate

```text
EXP024_098C_F1_STATUS = FORMAL_RUNTIME_IMPLEMENTED_AND_FRESHLY_QUALIFIED
EXP024_098C_F1_GATE = READY_FOR_NARROW_AUTHORIZATION_READINESS_REREVIEW
```

The next task is `Task 098C-R2`, a narrow independent authorization-readiness
rereview. Do not create a formal authorization in this task.
