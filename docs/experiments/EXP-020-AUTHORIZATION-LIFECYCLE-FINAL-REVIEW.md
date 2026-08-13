# EXP-020 Authorization-Lifecycle Final Review

## Scope

Task 082F reviewed only Task 082E's durable single-use authorization lifecycle, no-replace canonical publication, provenance, and synthetic regression coverage. No model, formal runner mode, prompt/source content, or scientific computation was accessed.

## Entry and Archive Scope

Reviewed commit: `6f7289d14d8163acdacfe7804e446cd0f39ab1fb` (`Harden EXP-020 authorization lifecycle`). It is a descendant of `d080cafd1e36c0daa3128fdff50010b86a02a570` and changes exactly the runner, its synthetic test module, and the two Task 082D rereview reports.

The Task 082B and 082D report hashes matched their required values at entry. The archive worktree was clean, `main` tracked `origin/main`, and no authorization, consumption record, canonical formal result, or staging result existed.

## Scientific-Semantic Non-Drift

The commit diff does not modify prompt rendering, tokenizer behavior, hidden-state extraction, layer mapping, split construction, directions, controls, probe fitting, probability mapping, effect formulas, bootstrap/statistics, or primary/secondary gate semantics. The changed runner functions are limited to authorization consumption, authorization provenance validation, no-replace publication, and formal-path ordering.

## Authorization Consumption

The deterministic path is:

`experiments/exp020/results/authorization_consumption/<full authorization SHA-256>.json`

The filename is derived only from the validated authorization artifact SHA-256. `os.open` uses `O_WRONLY | O_CREAT | O_EXCL` with mode `0o600`, so one concurrent consumer can create the record and every existing record, including empty, malformed, or partial content, blocks reuse.

Authorization parsing, schema/scope checks, clean-worktree and binding/integrity checks, and canonical-result absence checks occur before acquisition. Acquisition occurs before validators that access formal authority/source structures, formal prompt access, model loading, tokenization, RNG use, scientific computation, or output staging. After exclusive creation, write or fsync failure leaves the path in place; there is no retry or record-removal path. A distinct authorization SHA-256 maps to a distinct record.

Result provenance includes authorization ID/SHA-256, consumption-record path, and run-attempt ID. Reuse failure is an authorization/technical block, not a scientific gate outcome.

## No-Replace Publication

The canonical result remains `experiments/exp020/results/exp020a_results.json`. Complete in-memory validation precedes unique staging in the destination directory. Staged JSON is flushed and fsynced. Publication uses `os.link(staging, final)`, which requires an absent final destination; the formal publication path has no replacement operation or overwrite fallback.

If linking fails, the existing destination is untouched and staging cleanup is attempted. After successful linking, a staging-unlink failure preserves the valid canonical result and returns a cleanup-warning status. Staging names, engineering reports, and authorization-consumption records are excluded from canonical-result detection.

## Validation

- Preregistration validator: pass.
- Implementation-specification validator: pass.
- Runner AST validation: pass.
- Targeted synthetic tests: 92 passed.

The tests cover exclusive first/second use, concurrent consumers, bad pre-existing records, write/fsync failure persistence, path identity, ordering, canonical-result precheck, concurrent publishers, race-created destinations, no-overwrite fallback, serialization/fsync/validation failures, cleanup failure, and provenance validation.

## Findings

- Critical findings: none.
- Noncritical findings: pytest emitted one existing scikit-learn `penalty` deprecation warning; all tests passed.

## Final Status

`READY_FOR_REVIEW_ARCHIVE_AND_FORMAL_AUTHORIZATION_DECISION`

Formal EXP-020A remains prohibited. This review adds no scientific evidence and does not support behavioral control, reasoning improvement, scale invariance, task manifolds, or cognitive-space transformation.
