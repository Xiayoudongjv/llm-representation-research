# EXP-022A Scientific Closeout

This document closes EXP-022A after the first valid canonical formal result.
It is a scientific closeout record, not a new experiment.

## Authoritative Artifacts

- Canonical result: `experiments/exp022a/results/exp022a_results.json`
- Canonical result SHA-256: `2a26f77116acf37aac6462b997300d890445cac0f0ec98ffc5ec710b36a975c9`
- Frozen preregistration SHA-256: `609aab2b3cc96f4ea316b45741b2ae427e682c72c7546c8a9520201f94547698`
- Formal dataset SHA-256: `72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`
- Model/hook qualification SHA-256: `5f2e82180ccb1381626513758209b060f43e3f70431d08c15a1e74af0fe4ffe2`

## Observation

### Split A

- Reference A0 balanced accuracy: `0.9166666666666666`
- block27-pre balanced accuracy:
  - A0: `0.6666666666666666`
  - A1: `0.75`
  - A2: `0.5833333333333333`
- `D_fixed`: `-0.25`
- `D_fixed` exact p: `0.125`
- `G_scale`: `0.08333333333333337`
- `G_refit`: `-0.08333333333333337`
- `G_refit` exact p: `1.0`
- `G_noncal`: `-0.16666666666666674`
- `R_refit`: `-0.33333333333333337`
- Primary `D_fixed` supported: `false`
- `G_refit` supported: `false`

### Split B

- Reference A0 balanced accuracy: `0.75`
- block27-pre balanced accuracy:
  - A0: `0.25`
  - A1: `0.75`
  - A2: `0.5`
- `D_fixed`: `-0.5`
- `D_fixed` exact p: `0.015625`
- `G_scale`: `0.5`
- `G_refit`: `0.25`
- `G_refit` exact p: `0.125`
- `G_noncal`: `-0.25`
- `R_refit`: `-0.25`
- Primary `D_fixed` supported: `true`
- `G_refit` supported: `false`

### Featurewise recalibration observation

- Split A: A0_final = `0.6667`, A1_final = `0.7500`, G_scale = `+0.0833`.
- Split B: A0_final = `0.2500`, A1_final = `0.7500`, G_scale = `+0.5000`.
- A1 remained substantially more stable than A0 across deeper checkpoints,
  especially in Split B.
- `G_scale` is secondary/descriptive. It is not promoted to a preregistered
  primary confirmed mechanism.

### A2 / same-family refit observation

- Split A: A2_final = `0.5833`.
- Split B: A2_final = `0.5000`.
- In both splits: `A2_final < A1_final`.
- Primary serial `G_refit` support: `false` in both splits.
- Split B serial gate opened because `D_fixed` was supported, but
  `G_refit` exact p = `0.125`, so mechanism support remained `false`.

### Final RMSNorm descriptive clue

This is a secondary descriptive observation, not a causal claim.

- Split A:
  - block27-pre A0 = `0.6667`, block27-post A0 = `0.2500`; post-final delta = `-0.4167`
  - A1: `0.7500 -> 0.7500`
  - A2: `0.5833 -> 0.5833`
- Split B:
  - A0: `0.2500 -> 0.2500`
  - A1: `0.7500 -> 0.7500`
  - A2: `0.5000 -> 0.5833`

Register only as `SECONDARY_MECHANISTIC_CLUE`.

## Operational Result

The canonical cross-split synthesis is:

- `D_fixed` = `PARTIAL_CONCORDANCE`
- `G_refit` = `SPLIT_HETEROGENEOUS`

Required closeout wording:

The preregistered primary fixed-readout degradation criterion was supported in
Split B but not Split A.

The direction of `D_fixed` was negative in both splits.

Therefore EXP-022A provides partial, split-dependent evidence of fixed-frame
held-out degradation rather than full cross-split primary confirmation.

Do not upgrade `PARTIAL_CONCORDANCE` into full replication.

## Interpretation

The strongest permitted interpretation is:

- EXP-022A is consistent with layer-dependent readout-frame nonstationarity,
  but the evidence is split-dependent.
- The strong descriptive recovery of A1, especially in Split B, suggests that
  featurewise recalibration may account for a substantial portion of the
  fixed-frame degradation.
- The failure of A2 to outperform A1, and the absence of preregistered
  `G_refit` support, argues against prioritizing unrestricted same-family
  classifier refitting as the next explanation.

This document does not state or imply:

- coordinate remapping proven
- representation information preserved globally
- dynamic latent geometry proven
- RMSNorm is the cause
- transport proven

## Speculation

The following entries are hypotheses, not established claims. They are formally
registered in `docs/research/HYPOTHESIS-LEDGER.md`.

- `HYP-CALIBRATION-001`: FIT-only featurewise/diagonal recalibration may explain
  part of fixed-readout degradation.
- `HYP-TRANSPORT-001`: constrained coordinate transport may restore a reference
  readout, but it is deferred behind calibration.
- `HYP-COVER-001`: representational overlap and destructive interference are
  distinct constructs; currently conceptual.
- `HYP-OPERATOR-001`: representation transformations may form a reusable
  operator vocabulary; dependent on future empirical transport results.
- `HYP-BELIEF-001`: structured multi-hypothesis representations may be useful
  for partially observed physical states; long-term embodied branch.

Next scientific question, not an EXP-023 protocol:

Does FIT-only featurewise/diagonal recalibration generalize beyond the current
12-record complementary splits and explain the observed readout stabilization?
