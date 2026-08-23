# Paper-A Post-Audit Claim Freeze

Status: `PA_NOVELTY_002_POST_AUDIT_CLAIM_FREEZE`
Scope: EXP-021 through EXP-027 only. EXP-028 is not Paper-A evidence.
Predecessor authority: `PA_NOVELTY_001_COMPLETE`, route `ROUTE_B_STANDALONE_NARROWED`.

## Central Contract

- `CENTRAL_RESEARCH_QUESTION = Does shared depth-distance-associated fixed-readout compatibility imply shared source/target organization and simple recalibratability across models?`
- `ONE_SENTENCE_RESULT = In three prospectively registered 1B-class language models, all three show positive depth-distance-associated fixed-readout compatibility structure, but source/target organization and low-dimensional recalibratability combine differently, with Llama matching Qwen on target dominance and OLMo on supported LOW-D recovery.`
- `PRIMARY_CONTRIBUTION = A preregistered three-model empirical dissociation of cross-depth fixed-readout compatibility dimensions: distance-associated structure is common, while source/target organization and simple recalibratability are not determined by that common structure.`

## Classification Legend

- Scientific roles: `BACKGROUND_ONLY`, `ESTABLISHED_PRIOR_ART`, `METHOD_OPERATION`, `MEASUREMENT_CONTRIBUTION`, `PRIMARY_EMPIRICAL_CONTRIBUTION`, `SECONDARY_EMPIRICAL_CONTRIBUTION`, `METHODOLOGICAL_RIGOR`, `LIMITATION`, `FUTURE_HYPOTHESIS`, `PROHIBITED_OVERCLAIM`.
- `NOVELTY_CONFIDENCE`: `HIGH`, `MODERATE`, `LOW`, `NOT_APPLICABLE`.
- `EVIDENCE_CONFIDENCE`: `HIGH`, `MODERATE`, `LOW`.
- Manuscript roles: `ABSTRACT_PRIMARY`, `ABSTRACT_SECONDARY`, `INTRODUCTION_CONTRIBUTION`, `RESULTS`, `DISCUSSION`, `LIMITATION`, `RELATED_WORK`, `DO_NOT_USE`.

## Frozen Claim Matrix

| CLAIM_ID | SAFE_CLAIM_TEXT | SCIENTIFIC_ROLE | NOVELTY_STATUS | EVIDENCE_STATUS | SUPPORTING_EXPERIMENTS | CLOSEST_PRIOR_ART | CLAIM_CEILING | FORBIDDEN_STRONGER_VERSION | MANUSCRIPT_ROLE |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| FC-01 | Fixed readouts can become incompatible with representations at other depths | ESTABLISHED_PRIOR_ART | NOT_NOVEL | HIGH | EXP-021, EXP-022A, EXP-023 | Tuned Lens; Logit Lens; tracing representation progression | Observed in controlled panels, not a first discovery | Paper A is first to show fixed-readout incompatibility | RELATED_WORK |
| FC-02 | Depth-distance-associated fixed-readout compatibility structure is supported in all three tested models | SECONDARY_EMPIRICAL_CONTRIBUTION | LOW | HIGH | EXP-026 Qwen and OLMo; EXP-027 Llama | Layerwise similarity/depth-use literature | Three tested models only; no universal distance law | Distance-associated degradation is a new law | RESULTS |
| FC-03 | Source/target organization differs materially across tested models | SECONDARY_EMPIRICAL_CONTRIBUTION | MODERATE | HIGH | EXP-026; EXP-027 | Model stitching asymmetry; HOT | Qwen target-dominant, OLMo source-dominant, Llama target-dominant; model-dependent | Architecture causes source/target organization | RESULTS |
| FC-04 | Simple LOW-D recalibratability differs across tested models | SECONDARY_EMPIRICAL_CONTRIBUTION | MODERATE | HIGH | EXP-026; EXP-027 | Affine stitching; feature transfer; functional alignment caution | Qwen not supported, OLMo supported, Llama supported | Recalibratability is a fixed model property | RESULTS |
| FC-05 | Shared distance-associated structure does not determine source/target organization and simple recalibratability in the three tested models | PRIMARY_EMPIRICAL_CONTRIBUTION | MODERATE | HIGH | EXP-026; EXP-027 | SemRF; affine stitching; layerwise profiling | Three-model registered dissociation; not statistical/causal independence | Organization and recalibratability are statistically or causally independent | ABSTRACT_PRIMARY |
| FC-06 | Llama prospectively produced the third registered profile: TARGET_DOMINANT + SUPPORTED | SECONDARY_EMPIRICAL_CONTRIBUTION | MODERATE | HIGH | EXP-027 | EXP-026 profile comparison | One third model; prospective routing strengthens credibility, not originality | Prospective routing itself is novel | RESULTS |
| FC-07 | Cross-depth fixed-readout compatibility can be operationally profiled along distance structure, source/target organization, and recalibratability | MEASUREMENT_CONTRIBUTION | LOW | HIGH | EXP-026; EXP-027 | Layer similarity matrices; stitching matrices; SemRF frames | Paper-A operational profile, not a universal taxonomy | This is a universal compatibility taxonomy | RESULTS |
| FC-08 | SDI is a paper-specific two-way source/target organization statistic | MEASUREMENT_CONTRIBUTION | LOW | HIGH | EXP-026; EXP-027 | Row/column variance decompositions; HOT layer coupling | Operational statistic; no exact prior-name found | SDI is a novel general organizational law | RESULTS |
| FC-09 | LOW-D is a paper-specific registered test of simple featurewise/moment recalibration | MEASUREMENT_CONTRIBUTION | LOW | HIGH | EXP-026; EXP-027 | Affine/stitching/moment-matching work | Operational test; not a novel alignment method | LOW-D is a new representation-alignment algorithm | RESULTS |
| FC-10 | Carrier comparability was controlled across Qwen, OLMo, and Llama, including final-norm carrier semantics | METHODOLOGICAL_RIGOR | MODERATE | HIGH | EXP-026; EXP-027 qualification | Tuned Lens/Patchscopes carrier practices | Measurement comparability control | Carrier control proves representation equivalence | RESULTS |
| FC-11 | Prospective routing and frozen statistical gates increase evidential credibility, not prior-art originality | METHODOLOGICAL_RIGOR | NOT_APPLICABLE | HIGH | EXP-027 | None | Governance contribution only | Prospective design is itself scientific novelty | DISCUSSION |
| FC-12 | Claims are limited to three controlled 1B-class models and do not establish architecture, training-history, or universal causes | LIMITATION | NOT_APPLICABLE | HIGH | EXP-026; EXP-027 | N/A | Narrow model/panel boundary | Three models generalize to all LLMs | LIMITATION |
| FC-13 | The mechanism of profile dissociation is unresolved | FUTURE_HYPOTHESIS | NOT_APPLICABLE | HIGH | EXP-026; EXP-027 | SemRF; depth-use work | Future mechanism question, not a tested answer | Profile dissociation has an established mechanism | DISCUSSION |

## Prohibited Overclaims

| PROHIBITED_CLAIM_ID | PROHIBITED_TEXT | REPLACEMENT |
| --- | --- | --- |
| PX-01 | First discovery of a cross-layer distance law | Depth-distance-associated structure was measured in three tested models; distance laws are prior art |
| PX-02 | First source-target layer matrix | Source/target matrices are established; Paper-A uses one operational matrix profile |
| PX-03 | First demonstration of fixed-readout cross-layer incompatibility | Fixed-readout incompatibility is prior art; Paper-A studies its multidimensional organization |
| PX-04 | Three universal compatibility regimes | Three tested models produced three profiles; no universal regime is claimed |
| PX-05 | Source/target organization is statistically or causally independent of recalibratability | The three registered profiles dissociate in the tested sample; independence is not claimed |
| PX-06 | Architecture causes the profile differences | Model-dependent profiles are observed; architecture causality is not tested |
| PX-07 | Training history causes the profile differences | Training history is not tested as a causal factor |
| PX-08 | Simple recalibration failure predicts adapter failure | LOW-D support is an operational readout-recovery test, not an adapter-performance predictor |
| PX-09 | Fixed-readout degradation means semantic information disappeared | Degradation is readout-compatibility evidence only; decodability is not causal absence |
| PX-10 | EXP-028, Residual-Flow, invariant, Functional Binding, or transport are supported by Paper-A | These are excluded from Paper-A evidence |
| PX-11 | Results generalize to all LLMs or all Transformers | Results are limited to the three registered controlled models and panels |
| PX-12 | Demonstrated practical/industry impact | Only methodological implications may be discussed |

## Counts

- `CORE_CLAIMS_FROZEN = 13`
- `PROHIBITED_OVERCLAIMS = 12`
- `PAPER_A_EXTENSION_REQUIRED = false`
- `PAPER_A_MANUSCRIPT_MODIFIED = false`
- `NEW_EXPERIMENT_PERFORMED = false`
