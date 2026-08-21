# EXP-026 Registered Scientific Result Audit

Review type: `READ_ONLY_IDENTITY_AND_RESULT_VALIDATION`

Task: `101G_EXP026_REGISTERED_SCIENTIFIC_RESULT_AUDIT`

Formal verdict: `RESULT_STATUS = VALID_REGISTERED_RESULT`

## Execution Identity

- Repository: `D:\Research\llm-representation-research`
- Authorization-bound HEAD: `f5713f398b4c9fa17e790bd1d03388f36460a45a`
- Formal launch count: `1`
- Formal process status: `EXITED`
- Authorization ID: `b3763f43-d365-4a24-86fc-263f53dc84cb`
- Authorization SHA-256: `83adcafa0648e94d8a50b7132bc9713abf2d9ee58bb930690b775ec93248dcd2`
- Runner SHA-256: `6ab29c35889ce35b9d4bc9ee98d2665865a088312940f10815714a574d2060a0`
- Run attempt ID: `f5e6aadca9a946fbb1061154fe14211a`

## Canonical Artifacts

- Canonical result: `experiments/exp026/results/exp026_results.json`
- Canonical result exists: `true`
- Canonical result SHA-256: `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551`
- Canonical result byte length: `1323656`
- Consumption evidence: `experiments/exp026/results/authorization_consumption/b3763f43-d365-4a24-86fc-263f53dc84cb.json`
- Consumption SHA-256: `4a35bfed3622ef82540e6bd42a843a56c9b5c465a686c1e2201ea5de012cd82a`

## Frozen Authority Check

- Frozen authority hashes match: `true`
- Engineering qualification hash: `bbce631a27e20762212eb905278b4398c4850485faacd62e865b2f7a286f2e2d`
- Formal pipeline qualification hash: `f474e28d04362fdebcf6eee5348a8b558a898124bc3c01cb7e053add59051690`
- Production schema/provenance/technical validity: `PASS`

## Uniqueness Check

- No duplicate canonical result found.
- No alternate `exp026_formal_result.json` found.
- Authorization consumed exactly once.
- `ATTEMPT_STATUS = COMPLETED_AND_PUBLISHED_ONCE`

## Registered Endpoint Summary

- Registered route: `P3`
- Scientific status: `P3_MATERIALLY_DIFFERENT_MODEL_SIGNATURES`
- Qwen: `TARGET_DOMINANT`, distance `POSITIVE_SUPPORTED`, LOW-D `NOT_SUPPORTED`.
- OLMo: `SOURCE_DOMINANT`, distance `POSITIVE_SUPPORTED`, LOW-D `SUPPORTED`.

## Authority Boundary

Do not execute `--formal-run` again, create another EXP-026 authorization,
modify the existing authorization, or delete/rewrite the canonical result or
consumption record. Interpret only after this audit, and only within the frozen
claim ceiling.