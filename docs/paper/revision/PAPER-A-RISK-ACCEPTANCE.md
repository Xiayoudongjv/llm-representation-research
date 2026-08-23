# Paper-A Risk Acceptance

Status: `PA_REVISION_000_RISK_ACCEPTANCE`
Predecessor decision: `FINAL_STANDALONE_DECISION = STANDALONE_VIABLE_BUT_HIGH_RISK`

## Scientific Ceiling

`PAPER_A_SCIENTIFIC_CEILING = NARROW_EMPIRICAL_DISSOCIATION`

Paper-A accepts these boundaries:

1. Cross-layer mismatch is not novel.
2. Distance-associated compatibility degradation is not a first discovery.
3. Source x target matrices are not novel by themselves.
4. Source/target organization has partial prior-art overlap.
5. Recalibration/alignment has partial prior-art overlap.
6. Paper-A does not establish statistical independence.
7. Paper-A does not establish causal/mechanistic independence.
8. Paper-A does not establish a universal LLM taxonomy.
9. Paper-A does not identify architecture or training history as causal determinants.
10. Paper-A does not establish practical adapter, safety, or training improvements.

## Risk Register

| RISK | DESCRIPTION | DISPOSITION |
| --- | --- | --- |
| RISK_1 | SemRF/Tuned Lens may cause reviewers to see Paper-A as incremental | ACCEPT_RISK; mitigate in writing by explicit differentiation |
| RISK_2 | Three models limit generalization | ACCEPT_RISK; claim only within tested set |
| RISK_3 | Profile characterization may be perceived as taxonomy | ACCEPT_RISK; emphasize registered prospective EXP-027 routing |
| RISK_4 | No mechanism | ACCEPT_RISK; frame as empirical measurement paper |
| RISK_5 | Practical consequence is methodological, not demonstrated | ACCEPT_RISK; forbid impact claims |

No risk requires a new experiment.

## Counts

- `SCIENTIFIC_RISKS_ACCEPTED = 5`
- `WRITING_MITIGATIONS_REQUIRED = 5`
- `NEW_EXPERIMENT_REQUIRED = false`
