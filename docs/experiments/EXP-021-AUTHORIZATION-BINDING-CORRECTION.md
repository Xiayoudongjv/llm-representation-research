# EXP-021 Authorization Binding Correction

## Scope

Task 089D corrects the pre-consumption blocker established by Task 089C. The
correction is engineering-only and does not change the frozen EXP-021
scientific protocol.

## Problem

The reviewed runner used `ARCHIVE_COMMIT` (`db11ff7...`) both as the frozen
authority-blob anchor and as the required live `HEAD`. After the Stage-Q
implementation was archived at `aeb6b48...`, neutral and Stage-Q production
entries were unreachable before authorization consumption.

## Correction

- Renamed the authority identity to `AUTHORITY_ARCHIVE_COMMIT`.
- Removed the live `HEAD == AUTHORITY_ARCHIVE_COMMIT` requirement.
- Preserved `git ls-tree AUTHORITY_ARCHIVE_COMMIT` verification for the frozen
  amendment and reconciliation blobs.
- Kept exact live execution binding through the validated authorization:
  `runner_commit == current HEAD` and `runner_sha256 == current runner SHA-256`.
- Added a non-destructive, explicit disposition lifecycle for issued,
  unconsumed, non-executable authorizations.

## Current authorization status

`ISSUED_BUT_UNCONSUMED_AND_NONEXECUTABLE_PENDING_BINDING_CORRECTION`

The Task 089B authorization remains byte-identical and unconsumed. It is not
dispositioned, and no replacement authorization exists.

## Runtime boundary

No neutral qualification, Stage-Q, Stage-P, model load, tokenizer load,
FIT/EVAL access, or scientific result occurred during this correction.

## Task 089E independent rereview

Task 089E passed commit-binding semantics and the general disposition
semantics listed in `EXP-021-STAGE-Q-IMPLEMENTATION.md`. Its sole remaining
finding was `DISPOSITION_CRASH_CONSISTENCY_BLOCKER`.

## Task 089F correction

Task 089F adds an explicit recoverable disposition transaction state and a
replacement-authorization gate. The original disposition remains non-consumptive
and byte-preserving. Interrupted states are now classified as either
`PREPARED_OR_IN_PROGRESS` or `PARTIAL_OR_RECOVERY_REQUIRED`, never inferred
from active-path absence alone.

The Task 089B authorization remains:

`ISSUED_BUT_UNCONSUMED_AND_NONEXECUTABLE_PENDING_BINDING_CORRECTION`

It is byte-identical and unconsumed. It has not been dispositioned, and no
replacement authorization exists.

## Task 089G independent rereview

Task 089G passed the disposition crash-consistency state machine, recovery
detection, and replacement gate. It found one remaining defect:
`RECOVERY_IDENTITY_DRIFT_ACCEPTED`.

## Task 089H correction

Task 089H closes the recovery identity-binding defect. Recovery no longer
treats journal self-hash as authorization or transaction identity. It rebuilds
the expected identity from the active or archived authorization and rejects any
self-consistent but drifted journal.

The Task 089B authorization remains unconsumed, byte-identical, and not
dispositioned. No replacement authorization exists.
