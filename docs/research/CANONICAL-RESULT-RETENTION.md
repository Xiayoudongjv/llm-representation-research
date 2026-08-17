# Canonical Result Retention Policy

This policy defines which research artifacts must be durably retained in the
pushed Git repository and which execution-local artifacts may remain outside
version control.

## Artifact Classes

### CANONICAL_SCIENTIFIC_RESULT

A canonical scientific result is an item-level or aggregate artifact that is
required to audit a published scientific conclusion.

- Must be preserved in pushed Git or another explicitly identified durable
  repository.
- If the original runtime artifact contains content unsuitable for Git, a
  sanitized canonical derivative may be tracked instead.
- The sanitized derivative must preserve enough evidence to audit the published
  scientific conclusion.
- Required provenance fields:
  - source artifact identity or path class
  - source SHA-256
  - sanitization version
  - sanitized artifact SHA-256, recorded after generation
  - creation or reconciliation task
  - excluded field classes
  - row/item counts where applicable
  - scientific-result identity
- A sanitized artifact must not be described as byte-identical to the local raw
  source.

### RESULT_VALIDATION_AND_STATUS

Result status and technical-validity records must be durable when they are
required to interpret a scientific result.

- Must durably record scientific result status.
- Must durably record technical validity.
- Must durably record primary gate/status.
- Must durably record canonical result hash or sanitized-source hash.
- Must durably record validator status where applicable.
- The result artifact and its tracked scientific interpretation must not
  contradict one another.

### AUTHORIZATION_LIFECYCLE_EVIDENCE

Raw authorization payloads may remain local when their scientific role is
durably represented by non-sensitive lifecycle evidence.

- Durable fields include:
  - authorization ID
  - authorization SHA-256
  - consumption SHA-256
  - attempt ID where applicable
  - single-use/consumed state
  - terminal disposition
  - scientific-result identity
- A sanitized lifecycle ledger may satisfy durability without tracking the raw
  authorization payload.
- This policy does not require every authorization file to be committed.

### EXECUTION_LOCAL_RECORD

Execution-local records include machine-specific paths, cache paths, raw
authorization payloads, raw generated text, raw hidden states, raw activation
tensors, credentials, tokens, secrets, and private keys.

- These records normally remain local and must not be committed as canonical
  scientific evidence.
- Non-sensitive identity, hash, and status derivatives may be tracked instead.

### GENERATED_DIAGNOSTIC

Ordinary diagnostics, caches, temporary outputs, and regenerable development
results may remain ignored when they are not canonical scientific evidence and
their loss would not prevent auditing the scientific conclusion.

- Existing `.gitignore` behavior is preserved.
- Task-093B does not edit `.gitignore`.

## Version-Control Content Rules

Canonical sanitized artifacts may contain:

- record/item IDs
- class labels
- condition/readout labels
- predicted labels
- correctness indicators
- probabilities
- aggregate metrics
- test statistics
- runtime software/device metadata
- integrity hashes
- non-sensitive attempt/result identifiers

Canonical sanitized artifacts must not contain:

- prompt text
- generated free-text responses unless scientifically indispensable and
  separately approved
- raw hidden states
- raw activation tensors
- credentials
- API tokens
- secrets
- private keys
- unnecessary absolute local filesystem paths
- raw authorization payloads when a sanitized identity/hash record suffices

## Current Canonical Sanitized Evidence

| Artifact | Role | Sanitized artifact SHA-256 | Referenced raw source SHA-256 |
| --- | --- | --- | --- |
| `docs/experiments/canonical/EXP-017-BEHAVIORAL-RESULTS-SANITIZED.csv` | `SANITIZED_CANONICAL_SCIENTIFIC_RESULT` | `c4e14f3fd6cad8232bf597a10b59b9299fa4f937ef4b814202665707571d64cc` | `258cfcbd77978e12bd96a3ed0fd9c202be000997fd16de90178a4b22ae4252d5` |
| `docs/experiments/canonical/EXP-017-BEHAVIORAL-RESULTS-MANIFEST.json` | `SANITIZED_CANONICAL_SCIENTIFIC_RESULT` | `bdc7d394713a8ae1958b73488631e4e15089c239d4e8fda988a289526e7e56a0` | `N/A` |
| `docs/experiments/canonical/EXP-021-STAGE-Q-Q3-RESULT-SANITIZED.json` | `SANITIZED_CANONICAL_SCIENTIFIC_RESULT` | `672d73e61719cd328b7815667311f5e3070fd7b12b6b8dc799b00a4e46d15235` | `833002c8e8bf47883bbab2063c4dfe7d91346a1c055ac5df4d50357cb061b851` |
| `docs/experiments/canonical/EXP-021-AUTHORIZATION-LIFECYCLE-LEDGER.json` | `SANITIZED_AUTHORIZATION_LIFECYCLE_LEDGER` | `ca0603b2951d248159b0838e58f4b1980d0b26495cc8f608a621c654047d91b7` | local lifecycle evidence set |
