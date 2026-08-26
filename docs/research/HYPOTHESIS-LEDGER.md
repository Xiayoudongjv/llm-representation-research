# Hypothesis Ledger

This file records hypotheses, not established claims. Speculative entries must
not be cited as findings or moved into `CLAIM-LEDGER.md` as fact.

## Post-Anchor Reconciliation Guardrail

Recovered theory material is retained in `RESEARCH-ASSET-MAP.md` and defined
where needed in `CONSTRUCT-REGISTRY.md` before it can enter this ledger. A
coherent theory candidate, analogy, innovation candidate, or historical AI
refinement is not a registered hypothesis. Promotion requires the existing
prospective route, a Cross-Gap Audit, a falsifiable prediction, a defined
equivalence/invariant condition where relevant, and separate route-review
approval. This guardrail does not revise the evidence or status of any
existing hypothesis.

## HYP-CALIBRATION-001

- ID: `HYP-CALIBRATION-001`
- Title: Layer-dependent featurewise calibration may explain part of fixed-readout degradation
- Origin: EXP-022A A0/A1 ladder
- Hypothesis: A substantial component of deeper-layer fixed-readout degradation can be reduced by a constrained diagonal/featurewise recalibration learned using FIT-only statistics.
- Current evidence: EXP-022A discovery-stage A1 > A0 signal; EXP-023 independent preregistered `NO_REPLICATION`; EXP-024 valid panel showed all 10 conditions had positive `G_eval` descriptively.
- Counterevidence: Split B `G_cal = 0` and unsupported; general cross-split replication failed; controlled dataset remains small.
- Status: `NOT_SUPPORTED_AS_GENERAL_CROSS_SPLIT_REPLICATION`
- Dependencies: EXP-022A and EXP-023 canonical results.
- Next discriminating experiment: Conditional susceptibility test using an independent diagnostic that does not share the confirmatory `G_cal` outcome.
- EXP-023 protocol status: `FORMAL_ANALYSIS_COMPLETED`
- Claim boundary: Conditional, hypothesis-generating signal only; not a general calibration mechanism.

## HYP_CALIBRATION_CONDITIONAL_002

- ID: `HYP_CALIBRATION_CONDITIONAL_002`
- Title: Featurewise recalibration benefit may be conditional on independently measurable readout mismatch
- Origin: EXP-023 `NO_REPLICATION` with strong Split-A rescue and Split-B null; EXP-022A complementary split pattern.
- Hypothesis: Featurewise recalibration benefit may occur primarily when a representation/readout interface exhibits independently measurable layerwise mismatch, rather than being a uniform property of all held-out conditions.
- Current evidence: EXP-024 valid formal test observed rho `0.28401877872187725`, exact one-sided p `0.2115079365079365`, primary support false; all 10 conditions had positive `S_diag` and `G_eval` descriptively. EXP-025 OLMo panel observed rho `0.3765432098765432`, exact permutation p `0.14020502645502644`, primary support false.
- Counterevidence: EXP-024 and EXP-025 primary support rules were not met; simple independent degradation magnitude did not significantly rank calibration benefit; condition-level diagnostic had limited resolution and substantial ties.
- Status: `NOT_SUPPORTED_BY_EXP024_AND_EXP025_PRIMARY_TESTS`
- Dependencies: EXP-024 canonical result `experiments/exp024/results/exp024_results.json`; EXP-025 canonical result `experiments/exp025/results/exp025_results.json`.
- Next discriminating experiment: No immediate confirmatory follow-up; preserve the mechanism gap unless a materially different, theoretically justified, separately preregistered question is proposed. Primary routing is now `MODEL_DEPTH_COMPATIBILITY_PROFILE`.
- Claim boundary: Simple susceptibility predictor not supported; this does not negate the descriptive panel calibration benefit and does not establish general unrelatedness.

## HYP_MEAN_CALIBRATION_001

- ID: `HYP_MEAN_CALIBRATION_001`
- Title: Mean/location recalibration may dominate scale recalibration under conditional degradation
- Origin: EXP-023 Split-A secondary mean/scale decomposition.
- Hypothesis: When featurewise recalibration is beneficial, mean/location correction may account for more of the rescue than scale correction.
- Current evidence: EXP-023 Split A `G_mu = +0.3125`, `G_sigma = +0.21875`; EXP-024 condition-panel mean/scale outputs are descriptive only and no mean-only primary test is registered.
- Counterevidence: Single supported split; Split B null; secondary descriptive design.
- Status: `HYPOTHESIS_GENERATING_ONLY`
- Dependencies: `HYP_CALIBRATION_CONDITIONAL_002`.
- Next discriminating experiment: Deferred behind conditional susceptibility design.
- Claim boundary: Secondary descriptive signal; not an established mechanism and not promoted above `HYP_CALIBRATION_CONDITIONAL_002`.

## HYP-TRANSPORT-001

- ID: `HYP-TRANSPORT-001`
- Title: Constrained coordinate transport may restore a reference readout
- Origin: EXP-022A A2 did not show the expected refit-specific rescue.
- Hypothesis: A constrained coordinate transport applied before a fixed reference readout can restore a reference readout under layer-dependent nonstationarity.
- Current evidence: No direct EXP-022A support; A2 did not outperform A1.
- Counterevidence: `G_refit` unsupported in both splits.
- Status: `ACTIVE_BUT_DEFERRED_BEHIND_CALIBRATION`
- Dependencies: HYP-CALIBRATION-001 should be tested first.
- Next discriminating experiment: Compare simple featurewise recalibration with more flexible constrained transport in a new, separately preregistered experiment.
- Claim boundary: Not established as a mechanism.

## HYP-COVER-001

- ID: `HYP-COVER-001`
- Title: Representational overlap and destructive interference are distinct
- Origin: Ten-point covering / packing analogy.
- Hypothesis: Overlap between knowledge/task regions may be benign or useful; the relevant quantity is harmful interference under constrained readout/transformation.
- Current evidence: Conceptual analogy only; no direct experiment.
- Counterevidence: None direct; construct boundary not yet operationalized.
- Status: `INCUBATING_CONCEPTUAL`
- Dependencies: Operational definitions for overlap and destructive interference.
- Next discriminating experiment: Deferred until construct definitions and a suitable measurement design exist.
- Claim boundary: Covering geometry is an analogy/source of formal constructs, not evidence that LLM latent space obeys the same theorem.

## HYP-OPERATOR-001

- ID: `HYP-OPERATOR-001`
- Title: Representation transformations may form a reusable operator vocabulary
- Origin: Generalization of identity/recalibration/transport ladder.
- Hypothesis: Representation transformations may form a reusable operator vocabulary.
- Current evidence: No direct experiment.
- Counterevidence: No established meaningful transport/transformation family yet.
- Status: `DEPENDENT_FUTURE`
- Dependencies: At least one meaningful transport/transformation family must be empirically established first.
- Next discriminating experiment: Deferred.
- Claim boundary: Do not assert non-Abelian structure.
- KAN / operator-family note: Standard KAN provides a concrete example of function-valued edges and a prospective `T0`-`T5` complexity ladder, but it does not provide evidence for this hypothesis and must not be cited as validation of the project's operator theory.
- Deferred sub-question: Does held-out fixed-readout recovery require operator complexity beyond diagonal affine recalibration? Candidate label `HYP_OPERATOR_CAPACITY_001` is not registered as a separate active hypothesis; status `DEFERRED_OR_REASSESS`, evidence `NOT_TESTED`.
- EXP-025 routing note: `D-` assigns higher priority to model/depth compatibility profiling than to immediate operator-capacity escalation; operator-capacity work remains a deferred backup direction, not abandoned.

## HYP-OPERATOR-NET-001

- ID: `HYP-OPERATOR-NET-001`
- Title: Operator-Routed Structured-State Neural Architecture
- Hypothesis: A neural architecture whose node states preserve structured or multiple candidate representations and whose edges apply conditionally selected, constrained transformation operators may provide a useful inductive bias for tasks involving symmetry, uncertainty, compositional transformation, or representation alignment.
- Origin: User neural-connection/operator question + DeepSeek proposed Geo-Fold interpretation + project independent reformulation.
- Current evidence: None; not tested.
- Counterevidence / limitations: Traditional networks already use matrix/linear operators; novelty not established; prior-art review required.
- Status: `LONG_TERM` / `PRIOR_ART_REQUIRED` / `NOT_TESTED`
- Dependencies: `HYP-CALIBRATION-001`, `HYP-TRANSPORT-001`, `HYP-OPERATOR-001`.
- Next discriminating experiment: Deferred until meaningful progress on calibration/transport and prior-art review.
- Claim boundary: Not an established architecture, not a new AI paradigm, not a non-Abelian network, not quantum.

## HYP-BELIEF-001

- ID: `HYP-BELIEF-001`
- Title: Structured multi-hypothesis representations for partially observed physical states
- Origin: Long-term embodied/physical-state representation branch.
- Hypothesis: Under incomplete/noisy physical observations, an AI system may benefit from maintaining multiple candidate world states rather than collapsing immediately to one reconstructed interpretation.
- Current evidence: No current LLM experiment.
- Counterevidence: Not tested.
- Status: `LONG_TERM_EMBODIED_BRANCH`
- Dependencies: Separate future embodied or physical-state research program.
- Next discriminating experiment: Deferred.
- Claim boundary: Not quantum superposition; not evidence from current LLM experiments; not current EXP-022A scope.

## HYP-LEXICAL-OPERATOR-001

- ID: `HYP-LEXICAL-OPERATOR-001`
- Title: Contextual Lexical/Semantic Transformations as Reusable Operators
- Origin: Word2Vec-to-contextual-transformation historical bridge; DeepSeek speculative operator-language proposal.
- Hypothesis: Some contextual semantic effects may be representable as reusable transformations rather than only as resulting positions; candidate operator identities should be discovered empirically from hidden-state transitions.
- Current evidence: None; not tested.
- Counterevidence / limitations: Fixed part-of-speech operator mappings are not supported; word order sensitivity is not a proof of non-Abelian language structure.
- Status: `FUTURE_NOT_TESTED` / `PRIOR_ART_REQUIRED` / `NOT_ACTIVE`
- Dependencies: `HYP-CALIBRATION-001`, `HYP-TRANSPORT-001`, potentially `HYP-OPERATOR-001`.
- Next discriminating experiment: Deferred until prior-art review and a separately preregistered protocol.
- Claim boundary: Not an established semantic mechanism; do not assign fixed geometric operators to lexical categories.

## HYP-ATTENTION-GEOMETRY-001

- ID: `HYP-ATTENTION-GEOMETRY-001`
- Title: Representation–Attention Geometry Coupling
- Origin: Project synthesis from attention routing, value transport, and representation geometry.
- Hypothesis: Layer- and context-dependent changes in representation state may systematically alter attention routing, while attention-mediated value transport may reciprocally reshape downstream representation geometry.
- Current evidence: None; not tested.
- Counterevidence / limitations: Standard decoder attention is already dynamic with context; attention score is not automatically a metric tensor; causal-mask softening is not planning.
- Status: `LONG_TERM` / `PRIOR_ART_REQUIRED` / `NOT_TESTED`
- Dependencies: `HYP-CALIBRATION-001`, `HYP-TRANSPORT-001`, potentially `HYP-OPERATOR-001`.
- Next discriminating experiment: Candidate future test would apply a preregistered representation transformation at an internal checkpoint, continue the frozen forward computation, and measure predicted changes in Q/K relations, attention matrices, value transport, downstream representations, and eventually behavior.
- Claim boundary: Not active; no direct empirical support; EXP-023 does not test attention routing or attention–geometry coupling.

## HYP-RESIDUAL-FLOW-001

- ID: `HYP-RESIDUAL-FLOW-001`
- Title: Residual-Flow Hypothesis
- Origin: Task 102A-ASSET prospective theory registration; residual-architecture incremental form and EXP-026 registered compatibility-profile pattern.
- Hypothesis: Cross-depth fixed-readout compatibility change can be productively studied as an accumulated consequence of layerwise identity-biased incremental operators, `h_{l+1} = h_l + F_l(h_l)`.
- Current evidence: `MOTIVATED_BY_EXISTING_ARCHITECTURES_AND_CURRENT_EMPIRICAL_PATTERN`; not confirmed by ResNet, EXP-026, or EXP-027.
- Counterevidence / limitations: `D(i,j)` is operational only; ResNet is an architectural analogue; Kakeya/covering ideas are distant inspiration; dynamic residual routing is prior art; functional binding is not established.
- Status: `PROSPECTIVE` / `NOT_YET_VALIDATED` / `DEFERRED_BEHIND_EXP027`
- Dependencies: `HYP-EXP026-*`, `HYP-OPERATOR-001`, Minimum Sufficient Alignment Operator, future invariant/conserved-structure definitions.
- Next discriminating experiment: Deferred until after EXP-027. Candidate future tests are the vision/ResNet cross-depth compatibility matrix and the controlled residual-vs-non-residual parameterization test.
- Predictions: RF-1 through RF-5 are registered under `ASSET-RESIDUAL-FLOW-001` in `RESEARCH-ASSET-MAP.md`; each is `PROSPECTIVE`.
- Claim boundary: `PROSPECTIVE_MECHANISTIC_HYPOTHESIS`; not a confirmed theory, not functional binding, and not a new EXP-027 endpoint.

## EXP-026 Mechanism Hypothesis Disposition

EXP-026 is a completed, valid registered scientific result. These are prospective
mechanism statuses, not causal findings. They map the Task 101H `H1`-`H5`
updates without creating duplicate or conflicting hypothesis IDs.

### HYP-EXP026-COMPAT-ORG-001

- ID: `HYP-EXP026-COMPAT-ORG-001`
- Title: Depth-associated fixed-readout compatibility organization
- Origin: EXP-026 full source/target compatibility matrix across Qwen and OLMo.
- Hypothesis: Fixed-readout compatibility is structured by depth distance.
- Current evidence: Qwen distance association `0.7049462571528698`, CI `[0.6851830380886905, 0.7080622074980855]`, `POSITIVE_SUPPORTED`; OLMo distance association `0.7519250367843754`, CI `[0.7438987161061725, 0.7582397801058931]`, `POSITIVE_SUPPORTED`.
- Status: `SUPPORTED_IN_BOTH_TESTED_MODELS`
- Claim boundary: This is depth-distance structure in two tested models only; it is not a causal depth law.

### HYP-EXP026-LOCALIZED-TRANSITION-002

- ID: `HYP-EXP026-LOCALIZED-TRANSITION-002`
- Title: Localized transition explanation of compatibility change
- Origin: EXP-026 registered route `P1` did not trigger globally.
- Hypothesis: A specific localized transition plus concentrated recovery would identify an operator-capacity target.
- Current evidence: The registered route did not select `P1`; localization values were evaluable but below the route threshold.
- Status: `NOT_PRIMARY_REGISTERED_ROUTE`
- Claim boundary: Frozen secondary descriptive evidence is retained only; no localized transition mechanism is established.

### HYP-EXP026-SOURCE-REFERENCE-003

- ID: `HYP-EXP026-SOURCE-REFERENCE-003`
- Title: Source/reference dependence of fixed-readout compatibility
- Origin: EXP-026 SDI endpoint and registered `P2`.
- Hypothesis: Source/reference organization is a dominant registered signal for compatibility.
- Current evidence: OLMo `SDI = 0.5249651786448143`, class `SOURCE_DOMINANT`; Qwen `SDI = -0.17355352410373298`, class `TARGET_DOMINANT`.
- Status: `SUPPORTED_BUT_MODEL_DEPENDENT`
- Claim boundary: Source dominance was registered in OLMo, not both models; it is not a universal reference-dependence claim.

### HYP-EXP026-MODEL-ORGANIZATION-004

- ID: `HYP-EXP026-MODEL-ORGANIZATION-004`
- Title: Model-dependent compatibility organization
- Origin: EXP-026 registered `P3` route.
- Hypothesis: The two tested models organize source/target fixed-readout compatibility differently.
- Current evidence: `SDI_CLASS[Q] != SDI_CLASS[O]`, both in `{SOURCE_DOMINANT, TARGET_DOMINANT}`; registered route `P3`.
- Status: `SUPPORTED`
- Claim boundary: This establishes material model-dependent difference, not architecture/family causality.

### HYP-EXP026-RECALIBRATABILITY-005

- ID: `HYP-EXP026-RECALIBRATABILITY-005`
- Title: Recalibratability is partly independent of raw degradation
- Origin: EXP-026 LOW-D recovery endpoint and prior EXP-025 `G+`.
- Hypothesis: FIT-only recovery benefit is not uniformly reducible to raw fixed-readout degradation magnitude.
- Current evidence: OLMo `LOW_D_SUPPORT = SUPPORTED`; Qwen `LOW_D_SUPPORT = NOT_SUPPORTED`.
- Status: `CONDITIONAL_MODEL_DEPENDENT_SUPPORT`
- Claim boundary: Conditional model-dependent support only; no transport, preserved-information, or universal recovery claim.
