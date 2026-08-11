## EXP-007: Transition Validity Frontier

Goal: identify a steering-strength operating point that balances target-region
transition success, relational preservation, and perturbation magnitude.

Run the analysis over EXP-006 CSV outputs:

```bash
python experiments/exp007/validity_frontier.py
```

Expected outputs under `results/exp007/` include validity scores, pair-level
frontier recommendations, an aggregate JSON summary, and four plots. The
scalar validity scores are exploratory and are not final theoretical
definitions.
