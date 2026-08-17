# Hypothesis Ledger

This file records hypotheses, not established claims. Speculative entries must
not be cited as findings or moved into `CLAIM-LEDGER.md` as fact.

## HYP-CALIBRATION-001

- ID: `HYP-CALIBRATION-001`
- Title: Layer-dependent featurewise calibration may explain part of fixed-readout degradation
- Origin: EXP-022A A0/A1 ladder
- Hypothesis: A substantial component of deeper-layer fixed-readout degradation can be reduced by a constrained diagonal/featurewise recalibration learned using FIT-only statistics.
- Current evidence: EXP-022A A1 > A0 at block27-pre in both splits; large recovery in Split B.
- Counterevidence: Split A recovery incomplete; `G_scale` was secondary/descriptive; small controlled dataset.
- Status: `ACTIVE_HIGH_PRIORITY`
- Dependencies: EXP-022A canonical result; no next-experiment protocol frozen yet.
- Next discriminating experiment: Independent or expanded held-out validation of FIT-only featurewise recalibration / diagonal affine transport.
- Claim boundary: Descriptive mechanism signal only; not a confirmed causal mechanism.

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
