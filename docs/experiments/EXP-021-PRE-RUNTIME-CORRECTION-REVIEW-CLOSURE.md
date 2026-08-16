# EXP-021 Pre-Runtime Correction Review Closure

## Scope

This closure covers the EXP-021 pre-runtime engineering correction cycle that
began after the independently reviewed Stage-Q implementation was archived at:

aeb6b48ce837acb0672053761693e49a85c7a698

The cycle completed before any real neutral runtime qualification, Stage-Q
execution, FIT/EVAL access, or scientific result.

## Triggering findings

1. Task 089C:
   frozen authority archive commit was incorrectly used as required live HEAD,
   making authorized production execution unreachable.

2. Task 089E:
   authorization disposition had a crash-consistency gap after archive move but
   before disposition-record publication.

3. Task 089G:
   recovery accepted self-consistent but authority-drifted journal identities.

4. Task 089J:
   frozen `tuple_semantics` metadata was incorrectly treated as an unexpected
   checkpoint.

5. Task 089L:
   global mutable-path denylist conflicted with the authorization/result/
   disposition lifecycle and made legitimate production states unreachable.

## Final corrections

A. `AUTHORITY_ARCHIVE_COMMIT` is only the historical Git/blob anchor for frozen
authority.

B. Executable launches are exact-bound to:
- authorization.runner_commit == live HEAD
- authorization.runner_sha256 == current runner hash

before consumption.

C. Unconsumed/non-executable authorization disposition is:
- explicit;
- non-destructive;
- journaled before irreversible move;
- crash-recoverable;
- authority-bound during recovery;
- distinct from consumption;
- unable to authorize replacement automatically.

D. Recovery expected identity comes from active/archive authorization, not from
journal self-consistency.

E. Checkpoint mapping uses an exact closed schema and recognizes
`tuple_semantics` as frozen non-checkpoint metadata.

F. Mutable lifecycle validation is closed-world and mode-specific across:
- active authorization;
- consumption;
- engineering results;
- disposition journal/archive/record.

G. Unknown/incompatible lifecycle artifacts fail closed.

## Final independent review

Task 089N:
EXP021_089N_INDEPENDENT_REREVIEW_PASS

Validator:
EXP021_STAGE_Q_IMPLEMENTATION_VALIDATION_PASS

Targeted tests:
163 passed, 1 skipped

Real static preflight:
EXP021_STATIC_PREFLIGHT_PASS
exit code 0

Synthetic production-entry tests established structural reachability for:
- neutral qualification to semantic authorization validation;
- Stage-Q to neutral-result / Stage-Q authorization semantic validation;

without model/tokenizer/FIT/EVAL execution.

## Reviewed identities

- `experiments/exp021/run_exp021_stage_q.py`
  `f75c0c0a93e8177a7f87670a4c6bb70f8f0339c69ba98f4fe6a75251ed1f7e49`
- `experiments/exp021/validate_exp021_stage_q_implementation.py`
  `ba981c2663d9fda92ab6e42b514edc90173568f39ea1ae0bea78b1b4568a3f09`
- `tests/test_exp021_stage_q.py`
  `2070640b878df59f732ca258e50e3b17fc7f267f51b8f5a26898f9c3581d37eb`
- `docs/experiments/EXP-021-STAGE-Q-IMPLEMENTATION.md`
  `b5260eb64f02255221d1aa90054c4581e89c760290c4b96f7ebcd34cfb1468f7`
- `docs/experiments/EXP-021-AUTHORIZATION-BINDING-CORRECTION.md`
  `c275b719f23d332d5a26bdc2ff0e703a48ff6a8ab8a9255e34c3cce5c242c321`

## Existing obsolete authorization

authorization ID:
EXP021-NEUTRAL-3f7fa96e04954837946a19a42ddcf0f4

SHA-256:
24354add1de463052759459b2b0daae7d80b1666ceca2398e77fa9e868ae8061

state:
ISSUED
UNCONSUMED
NONEXECUTABLE

It was NOT consumed, modified, or dispositioned during the correction cycle.

It does NOT authorize execution under the corrected committed implementation.

## Scientific boundary

EXP021_HOOK_ORACLE_RUNTIME_QUALIFIED = false

EXP021_MEASUREMENT_QUALIFICATION_AUTHORIZED = false

EXP021_STAGE_Q_AUTHORIZABLE = false

EXP021_STAGE_P_AUTHORIZABLE = false

EXP021_SCIENTIFIC_STATUS = NOT_STARTED

No model/tokenizer load, FIT/EVAL access, propagation measurement, or scientific
result occurred during the correction cycle.

## Exact next gate

After this correction is committed and pushed:

the obsolete unconsumed 089B authorization may be explicitly dispositioned
using the reviewed disposition lifecycle.

Only after a complete valid disposition may a separate explicit decision issue
a fresh single-use neutral hook runtime qualification authorization bound to
the new committed runner identity.
