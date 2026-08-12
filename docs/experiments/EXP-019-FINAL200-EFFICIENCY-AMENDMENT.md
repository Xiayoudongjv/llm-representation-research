# EXP-019 Final-200 Efficiency Amendment

Before evaluator training and before any EXP-017 targetness evaluation, the
collection workflow was amended for efficiency. Earlier planning emphasized
`human_authored` and `manually_adapted_external` examples. The amended
development workflow also permits:

- `rule_composed`
- `independent_external`
- `ai_assisted_surface_normalized`

This amendment is documented transparently; the amended workflow is not
identical to the original preregistration.

## Safeguards retained

- EXP-017 outputs were not accessed.
- Classifier predictions were not used.
- The normalization stage received no task label or other class metadata.
- Semantic content could not be changed during normalization.
- Provenance was recorded honestly.
- Final class counts remained 50 per class.
- External-source diversity was audited.
- Human audit remains mandatory before freezing or evaluator training.

The 40-row random human audit remains primary. Similarity flags are a
supplementary review and do not replace the random audit.
