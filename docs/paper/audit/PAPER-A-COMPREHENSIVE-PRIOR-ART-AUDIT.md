# Paper-A Comprehensive Prior-Art and Claim-Collision Audit

Status: `PRIOR_ART_AUDIT_ARTIFACT_PA_NOVELTY_001`
Task: `PA-NOVELTY-001`
Repository audited: `D:\Research\llm-representation-research`
Audit nature: adversarial, read-only, novelty adjudication. No manuscript, experiment, result, protocol, or dataset was modified.

## 1. Executive Verdict

Paper-A's broad layerwise fixed-readout mismatch and distance-associated degradation claims are not novel. The defensible novelty is narrower: the registered cross-model source/target organization x recalibratability dissociation, including the prospective third-model Llama profile from EXP-027.

Recommended route: `ROUTE_B` (`PAPER_A_STANDALONE_NARROWED`).

Paper-A must stop presenting fixed-readout incompatibility, distance-associated structure, affine/moment recalibration, or the decodability/causal-role distinction as novel. It may still present the three-model registered profile dissociation as a distinct empirical contribution, with strict claim limits.

## 2. Search Scope

Searched operations and constructs, not only exact terms:

- fixed readout across Transformer depth
- layerwise decoding, logit lens, tuned lens, patchscopes
- representation similarity: SVCCA, CCA, CKA, matching, stitching
- cross-layer and cross-model alignment, affine mappings, feature transfer
- source/target layer compatibility matrices and asymmetry
- depth-use, layerwise prediction dynamics, residual-stream dynamics
- decodability versus causal role / information disappearance
- carrier/final-norm/hidden-state extraction comparability
- semantic reference frames and measurement drift in residual streams

Covered literatures:

- pre-LLM and early representation-similarity work
- vision/stitching literature
- LLM interpretability and layerwise-decoding literature
- recent residual-stream and depth-usage work
- prospective/registered profile work where available

## 3. Search Terminology Map

| Paper-A construct | Operational search terms used |
| --- | --- |
| fixed readout | fixed readout; last-layer classifier across layers; direct decoding; logit lens |
| source-target matrix | layer-to-layer compatibility matrix; cross-layer stitching matrix; source/target layer effects |
| distance-associated structure | layer distance; monotonic layer similarity; depth-wise degradation |
| SDI/source-target dominance | row/column effect; source-dominant; target-dominant; layer alignment asymmetry |
| recalibratability | affine alignment; moment matching; featurewise normalization; simple adapter |
| profile dissociation | multidimensional representation profile; compatibility profile; cross-model profile |
| carrier comparability | final layer norm; hidden-state API; residual stream carrier; carrier semantics |
| fixed-readout measurement drift | comparable readout coordinates; apparent motion measurement drift; semantic reference frame |

## 4. Closest Prior Works

1. **SemRF** (`arXiv:2606.32022`) — strongest conceptual collision: fixed semantic reference frames, intermediate readout comparability, apparent motion versus measurement drift.
2. **Chen et al. 2025** (`arXiv:2506.06609`) — affine mappings between residual streams transfer features across models.
3. **Shah & Khosla 2026** (`arXiv:2510.01706`) — hierarchical/multi-level optimal transport for layer-to-layer and brain-region alignment.
4. **Gupta et al. 2025** (`arXiv:2510.18871`) — fine-grained layer-wise prediction dynamics.
5. **Csordas et al. 2025** (`arXiv:2505.13898`) — depth contributes less to new computation and more to fine-grained adjustments.
6. **Tikhomirova & Wulff 2026** (`arXiv:2601.03798`) — layer-wise accessibility of psycholinguistic features.
7. **Tuned Lens** (`arXiv:2303.08112`) — per-block affine readouts.
8. **Bansal et al. 2021** (`arXiv:2106.07682`) — simple stitching adapters as functional compatibility evidence.
9. **Balogh & Jelasity 2025** (`arXiv:2412.11299`) — direct matching versus task-loss matching and same-network layer self-comparison.
10. **Smith et al. 2025** — functional alignment can mislead.
11. **Raghu 2017 / Kornblith 2019 / Morcos 2018** — SVCCA, CKA, CCA similarity foundations.
12. **Curth et al. 2026** (`arXiv:2604.12426`) — adaptive depth use.

## 5. Claim-by-Claim Adjudication

See `PAPER-A-CLAIM-PRIOR-ART-MATRIX.md` for the full C1-C15 table. Summary:

- `C1`, `C2`, `C3`, `C14`: established prior art. Not novel.
- `C4`, `C7`, `C10`, `C11`, `C13`, `C15`: partially differentiated or low-to-moderate novelty.
- `C5`: partially differentiated; source/target role effects exist in stitching literature.
- `C6`, `C8`, `C9`, `C12`: potentially distinct, but must be scoped as empirical results/metrics rather than broad mechanistic claims.

## 6. Distance-Law Verdict

`DISTANCE_LAW_FIRST_CLAIM = NOT_SUPPORTED_AS_FIRST`

Layer distance is a standard predictor of similarity/decodability and appears extensively in prior work. Paper-A may report its registered distance statistic as a component of its profile, but may not claim a new general distance law.

## 7. Source/Target-Organization Verdict

`SOURCE_TARGET_ORGANIZATION_PRIOR_ART = PARTIALLY_OVERLAPPING`

Layer-to-layer matrices and asymmetric correspondences are established. The two-way source/target decomposition is related to existing row/column and alignment asymmetry work. It may be retained as a paper-specific operationalization, not a novel general organizational law.

## 8. Recalibratability/Dissociation Verdict

`RECALIBRATABILITY_DISSOCIATION_PRIOR_ART = PARTIALLY_OVERLAPPING`

Affine/moment recalibration and cross-model affine transfer are established. The exact registered dissociation—source/target organization does not determine simple recalibratability—was not located as a single established result. This is the strongest novelty candidate, but it is only partially differentiated because each component has prior art.

## 9. Construct-Name Audit

| Paper-A term | Status |
| --- | --- |
| fixed-readout compatibility | established method/measure; not a new term |
| source-target dominance / SDI | paper-specific metric; no prior exact name found |
| recalibratability | operationally distinguishable, but conceptually close to alignment/stitching |
| compatibility profile | useful descriptive container; not a new deep construct |
| carrier comparability rule | engineering/measurement rule; moderate novelty |
| transport | not tested; must remain absent from Paper-A claims |
| functional binding / invariant / residual-flow theory | not Paper-A supported theory; must not be imported |

## 10. Strongest Reviewer Collision Arguments

- **Measurement-drift collision**: SemRF argues fixed readout coordinates can make apparent residual motion a measurement artifact. Paper-A must show its SDI/profile claims are not simply restating this boundary.
- **Affine stitching collision**: Chen et al. 2025 shows affine residual-stream mappings transfer features across models; this limits novelty of affine/moment recalibration.
- **Layerwise depth collision**: Gupta, Csordas, Curth, and Tikhomirova each show depth/layer dynamics; this limits novelty of distance-associated structure.
- **Functional-alignment caution**: Smith et al. 2025 limits mechanistic interpretation of any recovery result.
- **Novelty laundering risk**: The three-model profile is defensible only as a registered empirical pattern, not as a general law or mechanism.

## 11. What Paper A Must No Longer Claim

- Fixed-readout incompatibility is new.
- Affine/moment recalibration is new.
- Distance-associated degradation is a new law.
- Source/target matrices are a new measurement idea.
- Recovery under recalibration proves representation equivalence or information preservation.
- Decodability/causal-role distinction is novel.
- Three-model profile establishes a general law of LLM depth organization.
- EXP-028 / Residual-Flow / invariant / Functional Binding are supported by Paper-A evidence.
- First/novel/unprecedented language without strong evidence.

## 12. What Paper A Can Still Defensibly Claim

- A narrow, preregistered three-model empirical profile exists for Qwen, OLMo, and Llama.
- The three registered profiles are:
  - Qwen: `TARGET_DOMINANT + NOT_SUPPORTED`
  - OLMo: `SOURCE_DOMINANT + SUPPORTED`
  - Llama: `TARGET_DOMINANT + SUPPORTED`
- The Llama profile prospectively breaks a simple source/target-dominance-to-recalibratability mapping.
- Distance-associated structure, source/target organization, and simple recalibratability are dissociable in the current registered measurement framework.
- Carrier comparability was controlled explicitly across architectures.
- Paper-A can report negative/narrow results without overstating mechanism.

## 13. Remaining Uncertainty

- SemRF is new and its full formal scope is not yet fully absorbed; its overlap with SDI needs a dedicated future comparison.
- The exact source-family bootstrap and statistical support conventions must be audited in the manuscript against the canonical results before submission.
- Cross-model profile claims remain bounded to three small models and controlled panels; generalization is unestablished.
- The novelty of SDI as a metric has not been independently searched through every possible name variant.
- The draft is stale through EXP-025 only and currently lacks EXP-026/027 and Llama; manuscript synchronization is outside this task.

## 14. Recommended Paper A Route

`PAPER_A_ROUTE = ROUTE_B` (`PAPER_A_STANDALONE_NARROWED`)

Paper-A should remain a standalone paper, but must be narrowed to the registered three-model profile dissociation, with prior art openly cited and broad novelty claims removed. It should not be absorbed into Paper B and should not be positioned as a strong standalone novelty claim without further prospective validation.

## Audit Completeness Checklist

- Searched operations rather than only terminology: `YES`
- Searched pre-LLM literature: `YES`
- Searched vision/stitching literature: `YES`
- Inspected closest papers where accessible: `YES` (abstracts/primary pages for critical collisions)
- Verified critical citations: `PARTIAL` (identifiers/abstracts verified; full bibliographic reconciliation not run against all indexes)
- Actively attempted to falsify Paper-A novelty: `YES`
- Distinguished new term / metric / experiment / empirical result / general insight: `YES`

## Final Flags

- `PA_NOVELTY_001_STATUS = COMPLETE`
- `ENTRY_HEAD = 2c7d96c2dbdbebf26d2d7e16d499a41656369a7e`
- `PAPERS_SCREENED = 21`
- `PAPERS_DEEPLY_REVIEWED = 12`
- `DISTANCE_LAW_FIRST_CLAIM = NOT_SUPPORTED_AS_FIRST`
- `SOURCE_TARGET_ORGANIZATION_PRIOR_ART = PARTIALLY_OVERLAPPING`
- `RECALIBRATABILITY_DISSOCIATION_PRIOR_ART = PARTIALLY_OVERLAPPING`
- `STRONGEST_NOVELTY_CANDIDATE = cross-model source/target-organization x recalibratability dissociation, especially the EXP-027 prospective third-model profile`
- `STRONGEST_COLLISION = SemRF (arXiv:2606.32022)`
- `PAPER_A_ROUTE = ROUTE_B`
- `MANUSCRIPT_MODIFIED = false`
- `NEW_EXPERIMENT_PERFORMED = false`
- `CURRENT_NEXT_TASK = PA-NOVELTY-002_CLAIM_FREEZE_AND_STORY_REDESIGN`
