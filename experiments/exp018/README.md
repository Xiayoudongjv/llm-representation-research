# EXP-018: Independent Validation Preregistration

EXP-018 is a design-only, representation-level validation study. It responds
to Research Audit v1 by separating fit prompts from evaluation prompts and by
comparing task steering with matched-norm random and opposite-direction
controls.

`independent_validation.py` implements the frozen protocol. It has an explicit
dry-run mode that loads no model and writes no result files:

```powershell
python experiments/exp018/independent_validation.py --dry-run
```

The official model-forward run is deliberately opt-in and must not be used
until separately authorized:

```powershell
python experiments/exp018/independent_validation.py --run
```

The runner reads its models, layers, splits, betas, probe settings, random seed,
and controls only from `validation_conditions.json`. It validates that every
fit/evaluation split is disjoint before fitting centroids, the scaler, or the
probe. No raw hidden-state tensors are persisted.

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

Future official output schemas are `transition_metrics.csv`, `probe_metrics.csv`,
`invariant_metrics.csv`, `pair_summary.csv`, `validation_summary.json`, and
`split_metadata.json` under `results/exp018/`. Dry-run never creates them.

No historical experiment, paper draft, or EXP-017 preregistration is changed by
this directory.
