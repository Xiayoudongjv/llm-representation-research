# EXP-022A Formal Attempt 001

THIS ATTEMPT IS NOT AN EXP-022A SCIENTIFIC RESULT.

## Identity

- Authorization ID: `fc1be2e7-aa46-4bd8-bbec-d74a862d384b`
- Authorization SHA-256: `50e55539c9bce1dbc5788fb08c7dc0ba5cf9ba88bb2d0a7f6f3478bd0c9ff3e2`
- Run attempt ID: `4058117a-f0ce-4298-bf8e-7f102ff7de4e`
- Consumption record SHA-256: `899f4ce3fbeec786bdd434c2a3c897491d2bbf5879d8e771d84a692d000b55ae`
- Technical failure evidence SHA-256: `df7c30565f4fcccea37181f62a00289d4fe3d9d651e9368cbac7ecbd1702283f`
- Runner commit used: `5a44c3c6115b5e4187364e7120db6522be5c6973`

## Failure

- Failure: `PRODUCTION_VARIANT_ROLE_MISMATCH`
- Raw variant universe: `original_style` / `paraphrase`
- Incorrect expected universe: `original` / `paraphrase`
- Failure stage: post-consumption structural dataset validation
- Model load: not performed
- FIT/EVAL: not performed
- Scientific outcome: `NOT_OBSERVED`
- Canonical result: not created

## Classification

- Classification: `PREOUTCOME_TECHNICAL_FAILURE`
- Root cause: `PRODUCTION_SCHEMA_ADAPTER_DEFECT`
- Specific defect: `RAW_VARIANT_ENUM_TO_CANONICAL_ROLE_MAPPING_MISSING`
- Correction: schema adapter only

## Retry Eligibility

- Attempt-1 scientific outcome: `NOT_OBSERVED`
- Failure occurred before model/tokenizer/FIT/EVAL/RNG
- Dataset and preregistration unchanged
- Corrective patch restores frozen split semantics
- New-attempt eligibility: `ELIGIBLE_AFTER_PREOUTCOME_TECHNICAL_CORRECTION`

## Lifecycle State

- Attempt status: `TECHNICALLY_INVALID`
- Technical validity: `TECHNICALLY_INVALID`
- Result status: `NO_SCIENTIFIC_RESULT`
- Scientific status: `NOT_OBSERVED`
- Formal launch count: `1`
- Authorization consumed: `true`
- No rerun occurred.
