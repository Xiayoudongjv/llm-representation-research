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
