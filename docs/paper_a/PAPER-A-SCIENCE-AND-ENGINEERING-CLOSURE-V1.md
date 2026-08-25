# Paper A science and engineering closure V1

Status: `PAPER_A_SCIENCE_AND_ENGINEERING_CLOSURE_V1`

This record freezes the manuscript-facing interpretation of the already
validated Paper A scientific asset package. It does not change any canonical
result, statistic, bootstrap interval, matrix, or source hash.

## Closure gates

- `PAPER_A_CORE_SCIENCE_COMPLETE = true`
- `PAPER_A_ACTIVE_SCIENTIFIC_EXPERIMENTS_REMAIN = false`
- `PAPER_A_CURRENT_RESOURCE_SCIENCE_CLOSED = true`
- `PAPER_A_RELEASE_VALID = true`
- `PAPER_A_CONTINUOUS_MAGNITUDE_HARDENING_PASS = true`
- `PAPER_A_CONSTRUCT_VALIDITY_HARDENING_PASS = true`
- `PAPER_A_RECOVERABILITY_CLAIM_HARDENING_PASS = true`
- `PAPER_A_MULTI_AXIS_CLAIM_HARDENING_PASS = true`
- `PAPER_A_MODEL_SCOPE_HARDENING_PASS = true`
- `PAPER_A_DIRECTIONALITY_HARDENING_PASS = true`
- `PAPER_A_EXTERNAL_VALIDITY_BOUNDARY_PASS = true`
- `PAPER_A_THREE_CONTRIBUTIONS_FROZEN = true`
- `PAPER_A_REVIEWER_ATTACK_MATRIX_COMPLETE = true`

## Three frozen contributions

1. **Direct compatibility / restricted recoverability decomposition.** We
   distinguish direct fixed-readout reuse across depth from recoverability
   under deliberately restricted FIT-only calibration.
2. **Three-model multi-axis operational characterization.** Across three
   tested language models, degradation, source/target dominance, and
   restricted recovery form partially dissociable joint operational profiles,
   rather than a single common scalar pattern.
3. **Structured characterization with boundaries.** We characterize full
   source-target depth matrices, split/condition heterogeneity, a
   preregistered negative predictor result, and exploratory directional
   asymmetry while explicitly bounding cross-task and mechanistic claims.

## Terminology and carrier

The primary term is **fixed-readout operational compatibility**. “Recoverability”
means **recoverability under deliberately restricted FIT-only calibration**;
the calibration is a diagnostic intervention, not a novel calibration method.
The carrier is the post-block, pre-final-normalization, last-valid-token
carrier. These measurements do not establish semantic equivalence,
information equivalence, geometric equivalence, causal computation, or
whole-representation equivalence.

## Frozen boundaries

- `CROSS_TASK_ROBUSTNESS = NOT_ESTABLISHED`.
- Directionality is `POST_HOC_EXPLORATORY_SECONDARY`; the directionality line is
  closed with no further matrix mining.
- The preregistered simple predictors in EXP-024/EXP-025 were unsupported
  under their registered tests; this is not evidence that compatibility has no
  predictable structure.
- `CKA = NO_GO`; `SVCCA = DO_NOT_ADD`.
- `EXP-021 = ENGINEERING_ONLY`; `EXP-020A` is not fixed-readout compatibility
  evidence.
- The fourth model is a `FUTURE_CANDIDATE_LAB_RESOURCE_DEPENDENT` and does not
  block Paper A manuscript V0.1.
- EXT-B terminated before model inference at its frozen dataset-construction
  gate; it is not a model-level negative result.

## Release evidence

The release validator checks the canonical SSOT, claim register, asset
manifest, figure/table hashes, profile magnitudes and intervals, directionality
label, and all engineering/external-validity boundaries. The reviewer attack
matrix and continuous-magnitude audit are manuscript-facing safeguards, not
new scientific analyses.
