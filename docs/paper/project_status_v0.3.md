# Project Status v0.3

## 1. Current Stage

EXP-000B through EXP-010 are complete. Paper Draft v0.3 has been prepared.
Shared engineering utilities have been added for experiment IO, representation
extraction, and plotting, together with local tests.

## 2. Completed Experiments

- **EXP-000B:** Extracted hidden-state metadata from Qwen/Qwen3-1.7B.
- **EXP-001:** Established a final-layer representation geometry baseline.
- **EXP-002:** Compared geometry across selected Transformer layers.
- **EXP-003:** Added lexical and paraphrase controls.
- **EXP-004:** Tested normalized static centroid steering.
- **EXP-004B:** Calibrated centroid steering strength.
- **EXP-005:** Evaluated all 12 ordered multi-pair transitions.
- **EXP-006:** Defined an RSM-based invariant violation proxy.
- **EXP-007:** Identified a transition-validity frontier.
- **EXP-008:** Performed invariant-aware discrete beta selection.
- **EXP-009:** Created a normal-generation answer-level baseline.
- **EXP-009B:** Audited answer scoring conservatively.
- **EXP-010:** Explored representation-behavior correlations at group level.

## 3. Main Findings

- Task-associated geometry appears in a weak, controlled form.
- Layer-wise geometry is non-monotonic.
- Calibrated centroid steering succeeds at representation-level transitions.
- IVS provides a proxy measure of relational preservation.
- Beta 0.75 is the current exploratory frontier point.
- The answer-level baseline is modest, with overall accuracy 0.625.
- The representation-behavior link is inconclusive because n=4 groups is too small.

## 4. Engineering Status

The project now includes:

- `src/experiment_io.py` for JSON/CSV IO and schema checks
- `src/extraction.py` for shared layer and last-token extraction helpers
- `src/experiment_plots.py` for common matplotlib patterns
- pytest tests covering the shared utilities
- compileall and pytest developer checks

Existing experiment scripts have not yet been migrated to the shared utilities.

## 5. What Is Not Yet Proven

- reasoning improvement
- generation-time steering
- generalization to other models or naturalistic datasets
- true logical invariance
- a causal representation-behavior relationship

## 6. Recommended Next Steps

1. Run EXP-011 with an expanded answer-level dataset.
2. Define an optional human or LLM-assisted answer annotation protocol, with human checks and no replacement of transparent scoring.
3. Migrate experiment scripts gradually to the shared utilities.
4. Polish the paper and add related work.
5. Only then attempt generation-time intervention.
