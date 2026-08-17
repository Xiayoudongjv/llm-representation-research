# Canonical Result Retention Policy

This policy defines which research artifacts must be durably retained in pushed
Git or another explicitly named durable store, and which execution-local
artifacts may remain outside version control.

## Artifact Classes

### CANONICAL_RESULT

A canonical result is a byte-identical result artifact that supports a current
scientific or engineering claim and is safe to commit to Git.

- Must be durable in pushed Git or another explicitly named durable store.
- Preferred when the raw artifact contains no prohibited content.
- Must preserve experiment/result identity, primary result/gate values,
  technical/result status, and sufficient evidence to audit the claim.

### CANONICAL_SANITIZED_DERIVATIVE

A sanitized canonical derivative is used when the raw result contains content
unsuitable for Git.

- Must preserve the source SHA-256.
- Must preserve experiment/result identity.
- Must preserve row/item counts where applicable.
- Must preserve scientifically relevant non-text fields.
- Must preserve primary result/gate values and technical/result status.
- Must record sanitization rule/version and excluded content classes.
- Must provide sufficient evidence to reproduce the current tracked conclusion.
- Must not be described as byte-identical to the raw source.

### RESULT_VALIDATION_AND_STATUS

Result validation and status records must be durable when required to interpret
a canonical result.

- Must durably record scientific or engineering result status.
- Must durably record technical validity.
- Must durably record primary gate/status.
- Must durably record canonical result hash or sanitized-source hash.
- Must durably record validator status where applicable.
- The result artifact and its tracked interpretation must not contradict one
  another.

### AUTHORIZATION_LIFECYCLE_EVIDENCE

Authorization lifecycle evidence may be durably represented without tracking
all raw authorization payloads.

- Durable fields include authorization ID, authorization SHA-256,
  consumption SHA-256, run attempt ID, single-use/consumed state, terminal
  disposition, and canonical result identity.
- Raw authorization payloads may remain local when hashed lifecycle identity is
  sufficient for audit.
- This policy does not require every authorization file to be committed.

### EXECUTION_LOCAL_FORENSIC_RECORD

Execution-local forensic records include machine-specific paths, cache paths,
raw authorization payloads, raw generated text, raw hidden states, raw
activation tensors, credentials, tokens, secrets, and private keys.

- These records normally remain local.
- They must not be committed as canonical evidence unless separately proven
  necessary and safe.
- Non-sensitive identity, hash, and status derivatives may be tracked instead.

### GENERATED_DIAGNOSTIC

Ordinary diagnostics, caches, temporary outputs, and regenerable development
results may remain ignored when they are not canonical evidence and their loss
would not prevent auditing a scientific conclusion.

- Existing `.gitignore` behavior is preserved.
- Task-093B2 does not edit `.gitignore`.

## Durability Rule

A canonical result that supports a current scientific or engineering claim must
be durable in pushed Git or another explicitly named durable store.

Preferred hierarchy:

1. byte-identical raw canonical artifact when Git-safe;
2. sanitized canonical derivative when raw artifact contains prohibited content;
3. summary-only retention is insufficient when unique item-level/result-level
   audit evidence would otherwise be lost.

## Version-Control Content Rules

Permitted canonical artifact content:

- item/record IDs
- condition labels
- semantic/class labels
- predicted labels
- correctness indicators
- probability vectors
- aggregate statistics
- bootstrap/test values
- runtime package/device metadata
- commit hashes
- authorization IDs/hashes
- attempt IDs
- result hashes

Prohibited unless explicitly approved:

- prompt text
- generated free text
- reasoning/completions
- raw hidden states
- raw activations
- credentials/secrets
- unnecessary absolute local/cloud paths
- raw authorization payloads when hashed lifecycle identity suffices

## Current Experiment Retention State

- EXP-017 = `SANITIZED_CANONICAL_REQUIRED`
- EXP-018 = `RAW_CANONICAL_DURABLE`
- EXP-019 = `RAW_CANONICAL_DURABLE`
- EXP-020A = `BYTE_IDENTICAL_RAW_CANONICAL_DURABLE`
- EXP-021 Q3 = `SANITIZED_CANONICAL_REQUIRED`
- EXP-022A = `RAW_CANONICAL_DURABLE`

## Current Canonical Evidence

| Experiment | Retention state | Tracked artifact or status | Canonical artifact SHA-256 |
| --- | --- | --- | --- |
| EXP-017 | `SANITIZED_CANONICAL_DURABLE` | `docs/experiments/canonical/EXP-017-BEHAVIORAL-RESULTS-SANITIZED.csv` | `c4e14f3fd6cad8232bf597a10b59b9299fa4f937ef4b814202665707571d64cc` |
| EXP-017 | `SANITIZED_CANONICAL_DURABLE` | `docs/experiments/canonical/EXP-017-BEHAVIORAL-RESULTS-MANIFEST.json` | `37b5af173bf000eebc5135da4d8265c05182dd4cc8bcab5d10bbae6fae2b767a` |
| EXP-018 | `RAW_CANONICAL_DURABLE` | existing tracked canonical evidence | `durable` |
| EXP-019 | `RAW_CANONICAL_DURABLE` | existing tracked canonical evidence | `durable` |
| EXP-020A | `BYTE_IDENTICAL_RAW_CANONICAL_DURABLE` | `experiments/exp020/results/exp020a_results.json` | `c603b763c5b5723b002d67ce71a073beba9668bf8bc49e0a215cc54d5f82e26a` |
| EXP-021 Q3 | `SANITIZED_CANONICAL_MEASUREMENT_DURABLE` | `docs/experiments/canonical/EXP-021-STAGE-Q-Q3-RESULT-SANITIZED.json` | `763fa2b2ea54ae9e8e487d4261e611489c00c40a3c45b50a98930d7d7aa6d44e` |
| EXP-021 lifecycle | `SANITIZED_LEDGER_DURABLE` | `docs/experiments/canonical/EXP-021-AUTHORIZATION-LIFECYCLE-LEDGER.json` | `621b4d7d0fda7a26844c9fe0ed3bdb2a03cdb8732ae75ab670ec2054f6497531` |
| EXP-022A result | `RAW_CANONICAL_DURABLE` | `experiments/exp022a/results/exp022a_results.json` | `2a26f77116acf37aac6462b997300d890445cac0f0ec98ffc5ec710b36a975c9` |
| EXP-022A attempt-2 lifecycle | `RAW_LIFECYCLE_EVIDENCE_DURABLE` | `experiments/exp022a/results/authorization_consumption/87fe8af5e944805dbae7c5e1527efdab1c0e050059bc0a2b53618440b62daf49.json` | `b74e16afcb2932571b9fdbd350552e62a74a73f459b3714d4b3acfc52c06a8db` |
