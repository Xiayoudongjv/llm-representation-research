# Current Research Brief

THIS IS A DERIVED MIGRATION ARTIFACT. NOT A PRIMARY AUTHORITY SOURCE.

Canonical artifacts outrank this brief. Read this for orientation only.

## 1. Core research question

How do task-relevant representations move, degrade, and potentially need to be
recalibrated or transported across layers and interventions?

## 2. Current framework

- Representation -> Local Geometry -> Manipulation -> Transport -> Invariant Preservation -> Functional Binding -> Behavior.
- The current transformation ladder is: Identity -> featurewise recalibration -> orthogonal -> affine -> low-rank -> nonlinear.

## 3. Strongest evidence chain

- EXP-018/EXP-020A support local representational manipulability and same-family larger-model replication.
- EXP-021 and EXP-022A show fixed-frame readout degradation across deeper clean checkpoints.
- EXP-022A shows descriptive featurewise-recalibration recovery, especially in Split B.
- EXP-022A does not support same-family layerwise readout refit rescue.
- EXP-023 independently returns `NO_REPLICATION`: strong Split-A rescue, null Split B.
- EXP-024 returns a valid condition-panel primary `NOT_SUPPORTED` for the simple degradation-magnitude predictor, while 10/10 conditions show positive `S_diag` and `G_eval` descriptively.
- EXP-025 returns a valid OLMo cross-model panel result: `D-` / `G+`; degradation breadth is not established, recovery support is limited.

## 4. Current claim boundaries

- Decodability/manipulability does not equal causal functional role.
- Speculation must not enter the claim ledger as fact.
- EXP-022A evidence is partial and split-dependent for the primary fixed-frame criterion.
- Featurewise recalibration is currently descriptive, not a confirmed mechanism.
- EXP-023 shows calibration rescue is conditional, not general cross-split replication.
- EXP-024 shows broad panel-level calibration benefit descriptively, but the simple independent degradation-magnitude predictor is not supported.
- EXP-025 shows mixed OLMo fixed-readout degradation and limited second-family recovery support; the simple predictor remains unsupported.
- Coordinate transport is not tested.

## 5. EXP-022A exact scientific synthesis

- Canonical result SHA-256: `2a26f77116acf37aac6462b997300d890445cac0f0ec98ffc5ec710b36a975c9`
- `D_fixed` = `PARTIAL_CONCORDANCE`
- `G_refit` = `SPLIT_HETEROGENEOUS`
- Primary fixed-readout degradation: supported in Split B but not Split A.
- `D_fixed` direction: negative in both splits.
- Featurewise recalibration: descriptive high-value signal.
- Same-family refit rescue: not supported.

## 5a. EXP-023 exact scientific synthesis

- Canonical result SHA-256: `f30591ad942e82a322e594695ce1d5023586261fd7b8bccaa208b0d46f388000`
- `EXP023_REGISTERED_OUTCOME = NO_REPLICATION`
- Split A `G_cal = +0.25`, supported.
- Split B `G_cal = 0.0`, unsupported.
- `D_fixed`: substantial in Split A, little in Split B.
- Secondary mean/scale signal: `G_mu > G_sigma` in Split A; descriptive only.

## 5b. EXP-024 exact scientific synthesis

- Canonical result SHA-256: `50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69`
- `EXP024_REGISTERED_OUTCOME = NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`
- Primary `rho = 0.28401877872187725`.
- Exact one-sided permutation `p = 0.2115079365079365`.
- Registered support rule: `rho > 0 AND p <= 0.05`; not satisfied.
- `S_diag > 0`: 10/10 conditions.
- `G_eval > 0`: 10/10 conditions.
- Design improvement: DIAGNOSTIC predictor and EVAL outcome use independent
  source families; `EXP024_SHARED_EVAL_A0_ALGEBRAIC_DEPENDENCY = false`.

## 5c. EXP-025 exact scientific synthesis

- Canonical result SHA-256:
  `bbac2f03b24bdf2ec93485c201d3c0cf50588ed51659e607bb97b231181765a9`
- Execution classification: `POST_HOC_PROTOCOL_RECOVERY`
- `D`: `NOT_SUPPORTED` (`D-`); exact one-sided p `0.08984375`.
- `G`: `SUPPORTED` (`G+`); exact one-sided p `0.03515625`.
- RQ3 susceptibility predictor: rho `0.3765432098765432`, exact permutation p
  `0.14020502645502644`, support false.
- Registered routing: `D-_G+`.
- `mean(S_diag) = 0.065625`; `mean(G_eval) = 0.109375`.
- `S_diag`: 7 positive, 2 negative, 1 zero.
- `G_eval`: 7 positive, 1 negative, 2 zero.
- Cross-model degradation breadth: `NOT_ESTABLISHED`.
- Cross-model recovery: `LIMITED_SUPPORT`.
- Transport / functional binding: `NOT_TESTED`.

## 6. Active hypotheses

- `HYP-CALIBRATION-001`: `NOT_SUPPORTED_AS_GENERAL_CROSS_SPLIT_REPLICATION`
- `HYP_CALIBRATION_CONDITIONAL_002`: `NOT_SUPPORTED_BY_EXP024_AND_EXP025_PRIMARY_TESTS`
- `HYP_MEAN_CALIBRATION_001`: `HYPOTHESIS_GENERATING_ONLY`
- `HYP-TRANSPORT-001`: `ACTIVE_BUT_DEFERRED_BEHIND_CALIBRATION`
- `HYP-COVER-001`: `INCUBATING_CONCEPTUAL`
- `HYP-OPERATOR-001`: `DEPENDENT_FUTURE`
- `HYP-BELIEF-001`: `LONG_TERM_EMBODIED_BRANCH`

## 7. Deferred hypotheses

- General affine/nonlinear coordinate transport is deferred behind simple calibration.
- Non-Abelian operator structure is not asserted.
- Embodied structured-belief representation is a long-term branch.

## 8. Next scientific decision

EXP-024 is closed with a valid `NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST` canonical
result. The immediate next step is a bounded Paper-A full prose draft using the
current positive/negative evidence chain. Do not automatically launch EXP-025,
a replacement authorization, or a second-model replication rescue; second-model
breadth is optional/venue-uplift only.

Explicit Task 100A froze a bounded EXP-025 cross-model replication design using
`allenai/OLMo-2-0425-1B-Instruct`; execution was later completed under a
post-hoc protocol-recovery authorization after pre-inference engineering
failure.

Task 100F has now archived the valid EXP-025 recovery result. The next research
direction is `MODEL_DEPTH_COMPATIBILITY_PROFILE`; backup is
`OPERATOR_CAPACITY_MINIMUM_SUFFICIENT_ALIGNMENT`. Do not create EXP-026 yet.

## 9. Frozen authority links/hashes

- Preregistration: `docs/experiments/EXP-022A-PREREGISTRATION.md`
  - SHA-256: `609aab2b3cc96f4ea316b45741b2ae427e682c72c7546c8a9520201f94547698`
- Formal dataset: `experiments/exp003/prompts_controlled.json`
  - SHA-256: `72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`
- Model/hook qualification: `experiments/exp022a/engineering/model_hook_qualification.json`
  - SHA-256: `5f2e82180ccb1381626513758209b060f43e3f70431d08c15a1e74af0fe4ffe2`
- Attempt-2 canonical result: `experiments/exp022a/results/exp022a_results.json`
  - SHA-256: `2a26f77116acf37aac6462b997300d890445cac0f0ec98ffc5ec710b36a975c9`
- EXP-023 frozen preregistration: `docs/experiments/EXP-023-PREREGISTRATION.md`
  - SHA-256: `11bfa984d436ba06f7f3d1b0db24b90439742e9d9a87d124880834b437749f0b`
- EXP-023 frozen dataset: `experiments/exp023/data/exp023_independent_controlled.json`
  - SHA-256: `9143ceceab106c71dedb806190e146401975bf6bd84cb99b3b4cb7adc75afa2a`
- EXP-023 canonical result: `experiments/exp023/results/exp023_results.json`
  - SHA-256: `f30591ad942e82a322e594695ce1d5023586261fd7b8bccaa208b0d46f388000`

- EXP-024 frozen preregistration: `docs/experiments/EXP-024-PREREGISTRATION.md`
  - SHA-256: `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`
- EXP-024 frozen dataset: `experiments/exp024/data/exp024_condition_panel_frozen.json`
  - SHA-256: `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- EXP-024 model/hook qualification: `experiments/exp024/engineering/model_hook_qualification.json`
  - SHA-256: `72e7f48d68a022819cfed5045061af5b0d6d84de659a49e056487b9d20da8d8f`
- EXP-024 canonical result: `experiments/exp024/results/exp024_results.json`
  - SHA-256: `50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69`

- EXP-025 canonical result: `experiments/exp025/results/exp025_results.json`
  - SHA-256: `bbac2f03b24bdf2ec93485c201d3c0cf50588ed51659e607bb97b231181765a9`
- EXP-025 recovery authorization:
  `experiments/exp025/exp025_protocol_recovery_authorization_001.json`
  - SHA-256: `be2c8aaa70cc5b24ed5bf9a9edae288c75803b9c5974e2872544a77c2fe8814d`
- EXP-025 recovery consumption:
  `experiments/exp025/results/authorization_consumption/7b3dbdaf-1fb4-4272-a80b-58b99adac59d.json`
  - SHA-256: `2d88598be6deaf8e078c0e7ae8d9c1ed49f2946d6f2356d89dec3451025602c6`

## 10. Instructions to future AI

- Canonical artifacts outrank chat summaries.
- Technical failure is not scientific failure.
- Decodability/manipulability is not causal role.
- Speculation must not enter the claim ledger as fact.
- Do not modify frozen protocol after outcome.
- Do not modify frozen EXP-023 protocol after outcome.
- Do not modify frozen EXP-024 protocol after outcome.
- Do not modify the archived EXP-025 result or recovery provenance.

## 11. Long-Horizon Research Asset Map

Long-horizon ideas, analogies, system-architecture inspirations, and application
branches are indexed separately so they survive migration without being promoted
to established claims.

- Asset map: `RESEARCH-ASSET-MAP.md`
- Hypotheses: `HYPOTHESIS-LEDGER.md`
- Experiment chain: `EXPERIMENT-LINEAGE.md`

## 12. Operator-Routed Structured-State Architecture

Long-horizon architecture entry. Status: `LONG_TERM / PRIOR_ART_REQUIRED / NOT_TESTED`.

Core chain: structured node state + operator-valued connection + conditional
routing + composition + invariant validation.

- Hypothesis: `HYP-OPERATOR-NET-001`
- Asset map: `RESEARCH-ASSET-MAP.md`

## 13. Long-Horizon Conceptual Assets: Word2Vec State-Operator and Attention-Geometry Coupling

- State–Operator Duality: Word2Vec-to-contextual-transformation conceptual bridge.
- Attention–Geometry Coupling: representation state may affect routing; attention-mediated transport may reshape later representation.
- Status for both: `LONG_TERM` / `PRIOR_ART_REQUIRED` / `NOT_TESTED`.
- Active scientific priority is now a bounded Paper-A full draft; EXP-024 completed the susceptibility follow-up with a valid negative primary.
