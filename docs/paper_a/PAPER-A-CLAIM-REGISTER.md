# Paper A Claim Register

Status: `READY_FOR_PAPER_A_SCIENCE_FREEZE`

The machine-readable source is
`experiments/paper_a/canonical/paper_a_claim_register.json`. The ten claims
below are the complete current Paper A claim set; any later proposal must be
marked as new rather than silently added.

| ID | Evidence status | Claim ceiling | Evidence |
|---|---|---|---|
| C1 | `VERIFIED` | Compatibility varies across depth in the tested models and registered conditions. | EXP-026, EXP-027 |
| C2 | `VERIFIED_CONDITIONAL` | FIT-only restricted recovery occurs for some tested profiles, not uniformly. | EXP-026, EXP-027 |
| C3 | `VERIFIED` | Direct compatibility and restricted recoverability are empirically distinct operational dimensions. | EXP-026, EXP-027 |
| C4 | `VERIFIED_NEGATIVE` | The preregistered simple compatibility predictor was unsupported. | EXP-024, EXP-025 |
| C5 | `VERIFIED_SCOPED` | The three tested models have different operational profiles. | EXP-026, EXP-027 |
| C6 | `VERIFIED` | Directed source-target matrices are the operational representation of cross-depth compatibility. | EXP-026, EXP-027 |
| C7 | `VERIFIED` | Compatibility and recovery vary across splits, conditions, and model profiles. | EXP-022A, EXP-023, EXP-025 |
| C8 | `SUPPORTED_EXPLORATORILY` | Directional asymmetry is observed exploratorily across the three tested models. | Directionality closure |
| C9 | `NOT_ESTABLISHED` | Cross-task/task-panel robustness is not established. | EXT-A/EXT-B boundaries |
| C10 | `NOT_ESTABLISHED / OUT_OF_SCOPE` | Underlying geometry, causal mechanism, and semantic equivalence are not established. | Paper A claim ceiling |

## Wording safeguards

Do not describe C3 as statistical or causal independence. Do not generalize C5
to all architectures or infer architecture causality. Do not describe C8 as a
first discovery, universal direction, causal information flow, or geometric
asymmetry. Do not convert C9 or C10 into model-level negative results.

## Novelty positioning

The following are current prior-art positioning labels, not immutable scientific
facts: cross-layer transfer and distance-related degradation are extensions;
directionality has prior art and the model-dependent signed pattern is an
exploratory novelty candidate; the direct-compatibility/restricted-recovery
combination and multi-axis model profile are strong combination candidates;
the calibration method itself is not novel; functional compatibility is not
representational equivalence.

## Freeze boundaries

`CKA = NO_GO_REQUIRES_MODEL_RERUN_LOW_INCREMENTAL_VALUE`;
`SVCCA = DO_NOT_ADD`; cross-task work is closed; directionality is
`CLOSED_NO_FURTHER_MATRIX_MINING`; a fourth model is future and resource-
dependent. These boundaries do not block Paper A science freeze.
