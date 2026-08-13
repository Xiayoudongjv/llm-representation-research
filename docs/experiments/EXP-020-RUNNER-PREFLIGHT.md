# EXP-020A Runner Preflight

## Status

This document covers runner implementation, synthetic validation, static preflight, and one neutral engineering preflight. Formal scientific execution is not run.

- formal scientific execution = NOT_RUN
- formal FIT/EVAL inference = false
- formal scientific results = false

## Runner Modes

- `--static-preflight`: validators, authority hashes, local config metadata, environment versions, result/authorization absence, and planned schemas only.
- `--neutral-model-preflight`: one local-only forward using exactly the neutral hardware diagnostic sentence; reports only shapes, versions, dtype/device, and pass/fail metadata.
- `--formal-run`: requires a future, separate authorization artifact before prompt/source loading, tokenizer/model loading, output creation, or representation extraction.

## Formal Authorization Lock

The future artifact must identify EXP-020A, set `formal_run_authorized` true, and bind the protocol, implementation-spec, and runner commits. Task 082A does not create it. Without it the runner reports `FORMAL_RUN_BLOCKED_NOT_AUTHORIZED` before any formal-data/model/output action.

## Future Formal Output Schema

The future atomic publication set contains in-memory validated item-level effects, probe and transition diagnostics, pair summaries, and a representation summary. It includes only frozen IDs/effects/summaries, environment and authority provenance, and primary-versus-secondary separation. Raw hidden states, token IDs, logits, probabilities outside frozen effect rows, and generated text are never persisted.

## Atomic Publication

Formal output is written only after all in-memory schema, count, and finiteness checks. A uniquely named staging directory is atomically renamed to the final formal output directory. A failed staging attempt is never published as a final result set.

## Boundary

`READY_FOR_EXP020_FORMAL_RUN_REVIEW` means the runner can be reviewed for a later authorization. It does not authorize model inference on formal FIT/EVAL records or EXP-020A scientific execution.
