# Paper-A Claim-Prior-Art Matrix

Status: `PRIOR_ART_AUDIT_ARTIFACT_PA_NOVELTY_001`
Scope: Paper A through EXP-027; EXP-028 excluded from Paper A novelty claims.

## Legend

Overlap levels: `DIRECT`, `HIGH`, `MODERATE`, `LOW`, `NO_CLOSE_MATCH_FOUND`.

Novelty statuses: `NOT_NOVEL`, `LIKELY_NOT_NOVEL`, `PARTIALLY_DIFFERENTIATED`, `POTENTIALLY_NOVEL_REQUIRES_VERIFICATION`, `DISTINCT_EMPIRICAL_RESULT`, `UNRESOLVED`.

## Claim Rows

| CLAIM_ID | CLAIM_TEXT | CLOSEST_PRIOR_WORK | YEAR | PRIOR_OPERATION | OVERLAP_TYPE | OVERLAP_LEVEL | NOVELTY_STATUS |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | Representations/readouts exhibit cross-depth incompatibility | Tuned Lens; Logit Lens; BERT layerwise probing | 2020-2023 | Layerwise decoding and probe trajectories show predictions/decodability change with depth | Operational | HIGH | NOT_NOVEL |
| C2 | A fixed readout trained at one layer loses compatibility at other layers | Tracing Representation Progression; Tuned Lens | 2024 / 2023 | Last-layer classifier directly applied to hidden layers; per-block affine probes | Operational | HIGH | NOT_NOVEL |
| C3 | Compatibility is associated with source-target layer distance | Tracing Representation Progression; CKA/SVCCA layer similarity | 2024 / 2017-2019 | Layer similarity and direct-classifier accuracy vary monotonically with layer proximity | Operational | HIGH | NOT_NOVEL |
| C4 | A source-layer x target-layer compatibility matrix is scientifically useful | Model stitching; CKA cross-layer matrices; Balogh & Jelasity | 2021 / 2025 | Layer-to-layer stitching and similarity matrices are standard comparison tools | Operational | MODERATE | LIKELY_NOT_NOVEL |
| C5 | Cross-depth compatibility contains a source-vs-target organizational component | Model stitching asymmetry; Balogh & Jelasity layer self-comparison failures | 2025 | Asymmetric layer correspondences and source/target role effects are observed | Conceptual | MODERATE | PARTIALLY_DIFFERENTIATED |
| C6 | SDI summarizes source-dominant vs target-dominant organization | No exact named metric found; row/column effects in compatibility matrices are closest | N/A | Two-way decomposition of layer transfer matrices | Metric | LOW | POTENTIALLY_NOVEL_REQUIRES_VERIFICATION |
| C7 | Simple featurewise/moment recalibration is a distinct recalibratability dimension | Direct matching in stitching; featurewise normalization/calibration | 2021-2025 | Low-capacity affine/direct matching and moment matching are established | Operational | HIGH | PARTIALLY_DIFFERENTIATED |
| C8 | Distance-associated structure does not determine source/target organization | No close equivalent found | N/A | Paper A cross-metric dissociation | Empirical | LOW | DISTINCT_EMPIRICAL_RESULT |
| C9 | Source/target organization does not determine simple recalibratability | No close equivalent found | N/A | Paper A cross-metric dissociation | Empirical | LOW | DISTINCT_EMPIRICAL_RESULT |
| C10 | Compatibility can be characterized as a multidimensional profile | Layerwise similarity/trajectory analyses; stitching comparisons | 2021-2025 | Multiple dimensions are often reported, but not under this exact profile definition | Conceptual | MODERATE | PARTIALLY_DIFFERENTIATED |
| C11 | Qwen, OLMo and Llama exhibit three different registered profiles | Not All Models Localize Linguistic Knowledge in the Same Place; cross-model stitching | 2021 / 2025 | Cross-model differences in layer localization/representation are established | Empirical | MODERATE | DISTINCT_EMPIRICAL_RESULT |
| C12 | Llama prospectively breaks a simple source/target-dominance <-> recalibratability mapping | No close equivalent found | N/A | Prospective third-model triangulation | Empirical | LOW | DISTINCT_EMPIRICAL_RESULT |
| C13 | Cross-model profile dissociation is a phenomenon beyond ordinary cross-layer transfer degradation | Cross-model layerwise probing; cross-model stitching | 2021-2026 | Cross-model layerwise differences are ordinary prior art | Conceptual | MODERATE | PARTIALLY_DIFFERENTIATED |
| C14 | Fixed-readout degradation should not automatically mean information disappearance | Causality != Decodability; Functional Alignment Can Mislead; probing critiques | 2025 / 2019-2022 | Decodability/causal-role distinction is established | Conceptual | HIGH | NOT_NOVEL |
| C15 | Carrier semantics must be matched functionally across architectures | Tuned Lens/Patchscopes carrier conventions; final-norm/hidden-state practices | 2023-2024 | Carrier choice and layer mapping are known practical issues | Operational | MODERATE | PARTIALLY_DIFFERENTIATED |

## Core-Novelty Ranking

| Contribution class | Conservative ranking |
| --- | --- |
| A. cross-layer mismatch | HIGH_CONFIDENCE_NOT_NOVEL |
| B. distance-associated structure | HIGH_CONFIDENCE_NOT_NOVEL |
| C. source x target compatibility measurement | LOW_NOVELTY |
| D. source/target organization | MODERATE_NOVELTY |
| E. recalibratability as separate measurement dimension | LOW_NOVELTY |
| F. multidimensional compatibility profile | MODERATE_NOVELTY |
| G. three-model registered profile pattern | MODERATE_NOVELTY |
| H. source/target organization x recalibratability dissociation | STRONG_NOVELTY_CANDIDATE |
| I. Carrier Comparability Rule | MODERATE_NOVELTY |
| J. scientific governance / prospective routing | NOT_A_SCIENTIFIC_NOVELTY |

## Final Adjudication

- `DISTANCE_LAW_FIRST_CLAIM = NOT_SUPPORTED_AS_FIRST`
- `SOURCE_TARGET_ORGANIZATION_PRIOR_ART = PARTIALLY_OVERLAPPING`
- `RECALIBRATABILITY_DISSOCIATION_PRIOR_ART = PARTIALLY_OVERLAPPING`
- `STRONGEST_NOVELTY_CANDIDATE = cross-model source/target-organization x recalibratability dissociation, especially the EXP-027 prospective third-model profile`
- `STRONGEST_COLLISION = SemRF (arXiv:2606.32022)`

The final adjudication is deliberately conservative: individual components of the Paper-A profile are present in prior work, but the registered cross-model dissociation is not currently identified as a single established result.
