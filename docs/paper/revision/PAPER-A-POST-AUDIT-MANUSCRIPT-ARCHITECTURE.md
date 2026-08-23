# Paper-A Post-Audit Manuscript Architecture

Status: `PA_REVISION_000_MANUSCRIPT_ARCHITECTURE`
Strategy: `STRUCTURAL_REBUILD`

The stale EXP-025 manuscript should be rebuilt, not locally patched. Valid methods/evidence sentences may be reused selectively, but the narrative spine and section order must follow the narrowed three-model dissociation.

## Frozen Central Contract

- `FINAL_RESEARCH_QUESTION = Do models with shared depth-distance-associated fixed-readout compatibility structure also share source/target organization and simple recalibratability?`
- `FINAL_PRIMARY_CONTRIBUTION = A prospectively strengthened three-model empirical dissociation showing that shared distance-associated fixed-readout compatibility structure does not uniquely determine source/target organization or simple recalibratability in the tested models.`
- `FINAL_ONE_SENTENCE_RESULT = In three prospectively registered 1B-class language models, all three show positive depth-distance-associated fixed-readout compatibility structure, but source/target organization and simple LOW-D recalibratability form non-identical profiles: Qwen TARGET_DOMINANT + NOT_SUPPORTED, OLMo SOURCE_DOMINANT + SUPPORTED, and Llama TARGET_DOMINANT + SUPPORTED.`

## Narrative Spine

1. Known problem: cross-layer representation/readout mismatch is established.
2. Gap: scalar mismatch/transfer scores may hide multiple compatibility properties.
3. Question: does shared distance-associated structure imply shared organization and recalibratability?
4. Measurement: distance-associated structure, SDI source/target organization, LOW-D recalibratability.
5. Evidence: Qwen, OLMo, Llama.
6. Prospective test: EXP-027 third-model routing.
7. Inference: shared distance structure coexists with different organization/recalibratability states in the tested models.
8. Boundary: LEVEL_2 empirical dissociation; no mechanism or universal taxonomy.

## Experiment Roles

| Experiment | Manuscript role |
| --- | --- |
| EXP-021 | HISTORICAL_CONTEXT |
| EXP-022A | HISTORICAL_CONTEXT |
| EXP-023 | SUPPLEMENT |
| EXP-024 | SUPPLEMENT |
| EXP-025 | MAIN_TEXT_SUPPORT |
| EXP-026 | MAIN_TEXT_CORE |
| EXP-027 | MAIN_TEXT_CORE |
| EXP-017 through EXP-020 | ancestry/motivation only; not primary evidence |

## Abstract Architecture

| Part | Must say | Must not say |
| --- | --- | --- |
| 1 Established context | fixed readouts can become incompatible across depth; layerwise decoding and stitching are prior art | "we discovered" cross-layer incompatibility |
| 2 Unresolved question | whether shared distance-associated structure implies shared organization and recalibratability | universal or causal question |
| 3 Measurement approach | fixed readout, source x target matrix, SDI, LOW-D, three models | governance as scientific novelty |
| 4 Result | three profiles; Llama breaks the simple two-model mapping | independence, orthogonality, universal regimes |
| 5 Implication | scalar compatibility score may hide distinct measurement properties | practical impact, mechanism, transport |

## Introduction Architecture

- P1: known layerwise mismatch.
- P2: why one degradation/transfer score may be insufficient.
- P3: exact empirical research question.
- P4: operational measurement framework.
- P5: three-model empirical result and EXP-027 prospective role.
- P6: bounded contributions and explicit limitations.

## Related Work Architecture

Clusters:

- Layerwise probing and fixed-readout transfer
- Logit Lens / Tuned Lens
- Patchscopes / activation transfer
- Representation similarity: CKA / SVCCA / CCA
- Representation stitching and alignment
- SemRF and closest source/target organizational work

For each cluster, define established knowledge, what Paper-A does not claim, and the remaining gap.

## Methods Architecture

Conceptual order:

1. source layer / target layer
2. fixed-readout compatibility
3. source x target compatibility matrix
4. normalized depth distance
5. distance-associated statistic
6. SDI source/target organization statistic
7. LOW-D recalibratability
8. model-level profile
9. prospective routing / EXP-027
10. carrier comparability

Governance appears in a compact reproducibility subsection, not as the central method.

## Results Architecture

- R1: fixed-readout compatibility varies with depth distance.
- R2: simple recalibration does not provide a universal explanation.
- R3: source/target organization differs across models.
- R4: first two models suggest but do not establish a simple mapping.
- R5: prospectively tested Llama profile breaks the mapping.
- R6: joint profile comparison establishes LEVEL_2 empirical dissociation.

Map experiment evidence to these conceptual sections rather than a chronological EXP diary.

## Figure Architecture

Existing figures are largely pre-EXP026 and must be reused selectively.

- Reusable with reframing: conceptual framework, fixed-readout degradation, EXP-023 heterogeneity, EXP-024 negative panel.
- Stale or deprioritize: early manipulability figures unless used as brief ancestry.
- New required: a four-panel synthesis figure:
  - Panel A: source x target matrix intuition.
  - Panel B: three-model distance support.
  - Panel C: organization x recalibratability coordinate plane.
  - Panel D: prospective EXP-027 routing logic.

`NEW_SYNTHESIS_FIGURE_REQUIRED = true`

## Discussion Architecture

- A. What the empirical dissociation changes.
- B. Why readout degradation should not be one scalar phenomenon.
- C. Measurement vs information absence.
- D. Probe portability / monitoring implications only.
- E. Architecture/training history as future hypotheses only.
- F. Explicit limits.
- G. Relation to the future Paper-B transformation-complexity question.

No EXP-028 evidence.

## Limitation Architecture

Required limitations:

- three models only
- 1B-class scope
- model-family confounding
- no statistical independence
- no causal/mechanistic decomposition
- simple recalibration is not general adapter alignment
- SemRF/Tuned-Lens conceptual overlap
- distance relation is not novel
- no demonstrated practical industry impact

## Title Directions

Conservative:

- Cross-Depth Fixed-Readout Compatibility Profiles Across Three Language Models
- Measuring Source/Target Organization and Recalibratability in Cross-Depth Fixed-Readout Compatibility

Balanced:

- Shared Depth-Distance Structure, Divergent Compatibility Profiles Across Models
- A Three-Model Empirical Dissociation of Fixed-Readout Compatibility Dimensions

Aggressive:

- When Shared Layerwise Structure Does Not Imply Shared Compatibility Organization

Final polished title is deferred to PA-REVISION-007.
