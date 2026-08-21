# Claim Ledger

| Claim | Status | Evidence |
| --- | --- | --- |
| task-associated local discriminability | SUPPORTED | EXP-003/EXP-018 representation lineage |
| held-out target-directed local representational movement | SUPPORTED | EXP-018 |
| same-family larger-model replication | SUPPORTED | EXP-020A recovered canonical result: `docs/experiments/canonical/EXP-020A-CANONICAL-RESULT-RECOVERY.json`; primary gate `REPRESENTATION_REPLICATION_SUPPORTED`. |
| relational invariant preservation | NOT_SUPPORTED / FAILED | canonical EXP-018 authority |
| task-specific behavioral advantage | NOT_SUPPORTED | EXP-017 |
| independent output evaluator generalization | FAILED | EXP-019 |
| clean fixed source-class cross-layer readout qualification | FAILED | EXP-021 Q3 canonical result |
| clean layerwise held-out source-class linear decodability | NOT_TESTED | no canonical result |
| clean readout-coordinate remapping | NOT_TESTED | no canonical result |
| intervention perturbation transport | NOT_TESTED | no canonical result |
| functional binding | NOT_TESTED | no canonical result |
| non-Abelian transport | SPECULATIVE | no direct experiment |
| directional packing / cognitive-folding-style compression | SPECULATIVE | no direct experiment |
| fixed-frame deeper-layer degradation | PARTIALLY_SUPPORTED / SPLIT_DEPENDENT | EXP-021; EXP-022A; EXP-023 Split A supported `D_fixed`, Split B not |
| featurewise recalibration rescue | DESCRIPTIVE_SIGNAL / CONDITIONAL_NOT_GENERAL | EXP-022A A1; EXP-023 strong Split-A rescue but null Split B |
| general cross-split featurewise calibration replication | NOT_SUPPORTED | EXP-023 canonical result `NO_REPLICATION` |
| conditional featurewise calibration benefit | HYPOTHESIS_GENERATING / SIMPLE_PREDICTOR_NOT_SUPPORTED | EXP-023 split heterogeneity; EXP-024 primary test did not support the simple independent degradation-magnitude predictor |
| mean-vs-scale calibration decomposition | SECONDARY_DESCRIPTIVE | EXP-023 Split-A `G_mu > G_sigma`; secondary only |
| fixed variant-direction explanation | NOT_SUPPORTED | EXP-022A/EXP-023 complementary split degradation/rescue pattern |
| panel-bounded featurewise calibration benefit | OBSERVED_DESCRIPTIVE | EXP-024 canonical result: `G_eval > 0` in 10/10 registered conditions; descriptive panel observation |
| simple condition-level degradation-magnitude susceptibility prediction | NOT_SUPPORTED | EXP-024 canonical result: rho `0.28401877872187725`, exact one-sided p `0.2115079365079365`, support false |
| cross-model fixed-readout degradation breadth | NOT_ESTABLISHED | EXP-025 canonical result: `D-`; 7 positive, 2 negative, 1 zero; exact one-sided p `0.08984375` |
| cross-model FIT-only featurewise recalibration recovery | LIMITED_SUPPORT | EXP-025 canonical result: `G+`; 7 positive, 1 negative, 2 zero; exact one-sided p `0.03515625` |
| simple degradation-magnitude susceptibility prediction across both registered panels | NOT_SUPPORTED | EXP-024 and EXP-025 both failed the registered support rule; EXP-025 rho `0.3765432098765432`, exact permutation p `0.14020502645502644` |
| core fixed-readout degradation existence | SUPPORTED | Qwen evidence chain remains; EXP-025 `D-` narrows breadth but does not refute the existence claim |
| same-family layerwise readout refit rescue | NOT_SUPPORTED_IN_EXP022A | EXP-022A G_refit unsupported both splits |
| coordinate transport | NOT_TESTED | no canonical result |
| functional binding / behavioral control | NOT_SUPPORTED / NOT_TESTED_BY_EXP022A | EXP-017; EXP-022A did not directly test this claim |

| depth-distance-associated fixed-readout compatibility structure | SUPPORTED_IN_BOTH_TESTED_MODELS | EXP-026 canonical result: Qwen distance association `0.7049462571528698`, `POSITIVE_SUPPORTED`; OLMo distance association `0.7519250367843754`, `POSITIVE_SUPPORTED` |
| materially different cross-model source/target organization | SUPPORTED | EXP-026 canonical result: Qwen `TARGET_DOMINANT`, OLMo `SOURCE_DOMINANT`; registered route `P3` |
| Qwen target-dominant fixed-readout organization | SUPPORTED | EXP-026 canonical result: Qwen SDI `-0.17355352410373298`, class `TARGET_DOMINANT` |
| OLMo source-dominant fixed-readout organization | SUPPORTED | EXP-026 canonical result: OLMo SDI `0.5249651786448143`, class `SOURCE_DOMINANT` |
| LOW-D recalibration recovery in OLMo | SUPPORTED | EXP-026 canonical result: OLMo mean recovery `0.04785714308465166`, positive fraction `0.8285714285714286`, `SUPPORTED` |
| LOW-D recalibration recovery in Qwen | NOT_SUPPORTED | EXP-026 canonical result: Qwen mean recovery `0.00013923267534205524`, positive fraction `0.07425742574257425`, `NOT_SUPPORTED` |
| recalibratability uniformly reducible to raw degradation | NOT_SUPPORTED_AS_UNIFORM_MODEL_CLAIM | EXP-026 OLMo `SUPPORTED` vs Qwen `NOT_SUPPORTED` LOW-D recovery; not uniform across tested models |
| architecture/family causality for EXP-026 organization | NOT_ESTABLISHED | EXP-026 registered claim ceiling prohibits architecture/family causal attribution |
| cross-model mechanism replication | NOT_CLAIMED | EXP-026 allows model-dependent structural difference, not same-mechanism cross-model replication |
| coordinate transport / invariance / functional binding / behavior | NOT_TESTED | no EXP-026 canonical result for these constructs |

## Status semantics

- `SUPPORTED`: canonical result supports the claim.
- `NOT_SUPPORTED`: canonical result does not support the claim.
- `NOT_ESTABLISHED`: no canonical support for breadth/generality exists; not an assertion of global absence.
- `LIMITED_SUPPORT`: a registered result supports a bounded/second-family interpretation, but not a broad generality claim.
- `FAILED`: canonical result failed an explicit test.
- `NOT_TESTED`: no canonical result exists.
- `SPECULATIVE`: hypothesis only.
- `PARTIALLY_SUPPORTED / SPLIT_DEPENDENT`: some preregistered support, but not full cross-condition confirmation.
- `DESCRIPTIVE_SIGNAL`: secondary/descriptive observation, not a primary confirmed mechanism.
- `DESCRIPTIVE_SIGNAL / CONDITIONAL_NOT_GENERAL`: secondary rescue signal observed in some conditions, but not general cross-split replication.
- `HYPOTHESIS_GENERATING`: observation suggests a prospective hypothesis; not directly tested as a claim.
- `OBSERVED_DESCRIPTIVE`: panel-level descriptive observation; not a confirmatory sign test.
- `HYPOTHESIS_GENERATING / SIMPLE_PREDICTOR_NOT_SUPPORTED`: conditional hypothesis remains, but the simple preregistered susceptibility predictor did not meet its support rule.
- `SECONDARY_DESCRIPTIVE`: preregistered secondary/descriptive decomposition only.
- `NOT_SUPPORTED_IN_EXP022A`: the named experiment did not provide preregistered support.
- `NOT_TESTED_BY_EXP022A`: outside the named experiment''s primary scope.
- `SUPPORTED_IN_BOTH_TESTED_MODELS`: the registered result supports the claim in both EXP-026 tested models, not in general.
- `MATERIALLY_DIFFERENT`: registered structural signatures differ materially across the compared models; this is descriptive comparative support, not causal attribution.
- `NOT_SUPPORTED_AS_UNIFORM_MODEL_CLAIM`: the registered result contradicts a uniform across-model simplification.
- `NOT_CLAIMED`: deliberately outside the registered claim ceiling.
