# EXP-026 101D-R Runtime Repair Audit

## Scope

This record supersedes the limited formal-pipeline qualification at commit
`ff82bd8face417af6969f745a3560e0b571a4f42`. That earlier record is retained
as historical evidence, but it is not sufficient to qualify a formal run: it
did not exercise a production-connected executor, full authorization binding,
source-family cluster resampling, or deep result-schema validation.

This repair changes no frozen scientific authority. It repairs only the
executor and qualification boundary in `run_exp026.py`, with focused tests in
`tests/test_exp026_runner.py`.

## Closed Defects

- B1: formal and synthetic modes share one authorization-consumption and
  scientific-executor path; the data source is injected at that boundary.
- B2: a formal authorization must bind repository commit, runner hash, frozen
  and inherited authority identities, panel/partition identities, models, and
  repaired qualification hashes.
- B3: inadequate DIAGNOSTIC source coverage produces
  `NOT_EVALUABLE_SOURCE_COVERAGE`; no support classification or route is
  emitted.
- B4: bootstrap resampling is condition-stratified by `source_family_id` and
  retains each selected family cluster's complete records.
- M1: canonical result validation checks nested profile, matrix, condition,
  layer-order, mask, and bootstrap fields.
- M2: independent hand-specified numeric goldens cover condition pooling,
  calibration arithmetic, and class mapping; a sabotage test verifies that
  they fail closed.
- M3: synthetic qualification uses synthetic authorization, consumption, and
  exclusive temporary publication through the shared executor.
- M4: focused tests cover carrier extraction, matrix orientation, diagonal
  baseline, D sign, class mapping, ten-condition pooling, low-D masking,
  coverage failure, and cluster resampling.

## Qualification Boundary

The repaired engineering and synthetic-formal qualification JSON files are
versioned as `*_101d_r.json`; the prior qualification files are not overwritten.
They are execution records, not scientific results. They contain no FIT,
DIAGNOSTIC, or EVAL panel content, no hidden states, and no model output.

The frozen `validate_exp026_design.py` remains unmodified. It is a
pre-implementation validator whose explicit `NO_RUNNER_PATHS` rule rejects any
existing runner, so it is expected to fail after implementation. The applicable
post-implementation authority check is the runner's read-only
`--static-preflight`, which verifies the frozen hashes without accessing the
inherited panel.

`FORMAL_RUN_READINESS` may be reported as `READY` only when both repaired
qualification records, all frozen-authority checks, and the targeted test
suite pass for the committed runner identity. Formal authorization and formal
execution remain separate future actions.
