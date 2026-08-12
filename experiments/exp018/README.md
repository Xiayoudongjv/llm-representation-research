# EXP-018: Independent Validation Preregistration

EXP-018 is a design-only, representation-level validation study. It responds
to Research Audit v1 by separating fit prompts from evaluation prompts and by
comparing task steering with matched-norm random and opposite-direction
controls.

There is intentionally no runner in this directory. Do not load a model or
generate output as part of this preregistration.

The frozen design is documented in
[`docs/experiments/EXP-018-PREREGISTRATION.md`](../../docs/experiments/EXP-018-PREREGISTRATION.md).
The machine-readable configuration is
[`validation_conditions.json`](validation_conditions.json).

Primary configuration:

- Models: `Qwen/Qwen3-1.7B`, `google/gemma-3-1b-it`
- Primary layers: Qwen L16 and Gemma L16
- Predefined secondary contrast: Gemma L26
- Splits: original-style fit / paraphrase evaluation, and the reverse
- Betas: 0.50, 0.75, 1.00
- Conditions: task-directed, matched-norm random, opposite direction
- Primary independent evaluator: fit-only multinomial logistic-regression
  probe

No historical experiment, paper draft, or EXP-017 preregistration is changed
by this directory.
