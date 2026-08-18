# Paper-A First-Draft Scaffold

Status: `MANUSCRIPT_ARCHITECTURE_NOT_YET_PROSE_DRAFT`

This file is a derived manuscript-planning asset. Canonical experiment results
and research ledgers outrank it.

## Working Titles

- Conservative journal style: `Layerwise Readout Compatibility and Featurewise Recalibration in Frozen Language Models`
- Stronger defensible conference style: `Task-Associated Representations Decode Locally but Do Not Guarantee Stable Readout: Depth-Dependent Degradation and Conditional Recalibration in Frozen LLMs`
- Neutral internal working title: `Paper-A: From Local Manipulability to Conditional Readout Calibration`

No title is final. Reject titles that imply universal transport, causal
control, functional binding, dynamic manifolds, or invariant reasoning without
clear qualification.

## Central Research Question

When task-associated structure is locally decodable and manipulable in a frozen
language model, how stable is its readout compatibility across depth, and when
can simple FIT-only featurewise recalibration recover a degraded fixed
readout?

The question distinguishes representation existence, readout compatibility,
transport, function, and behavior.

## Core Claim

> Fixed readout compatibility can degrade substantially across depth under some
> held-out conditions. FIT-only featurewise recalibration can substantially
> restore performance in such cases, but this rescue is not uniformly
> reproducible across complementary data conditions.

- `PAPER_A_CORE_CLAIM_STATUS = SUPPORTED_WITH_SCOPE_LIMITATIONS`

## Contributions

1. A controlled held-out framework distinguishing local representational
   manipulability from downstream readout stability and functional control.
2. Evidence that fixed readout compatibility can degrade across depth and
   conditions in frozen language models.
3. A FIT-only featurewise recalibration analysis showing large recovery in some
   degraded regimes but independent cross-split non-replication.
4. A negative/replication-aware evidence chain defining limits on stronger
   transport, function, and behavior interpretations.

Do not describe the overall framework as novel unless a future prior-art
review supports that wording.

## Claim Boundaries

Paper A does **not** claim:

- universal task axes;
- global cognitive space;
- general transport proof;
- causal functional binding;
- behavioral control;
- attention-geometry proof;
- general operator algebra validation;
- scale invariance;
- cross-model universality;
- robust cross-split calibration replication.

## Evidence Hierarchy

- Primary paper evidence: EXP-018, EXP-021, EXP-022A, EXP-023, EXP-024.
- Supporting evidence: EXP-020A.
- Boundary/negative evidence: EXP-017, EXP-019.
- Hypothesis-generating evidence: EXP-023 mean/scale decomposition and the
  EXP-024 panel-level descriptive calibration signal.
- Background/historical evidence: earlier representation-lineage work cited
  only for orientation.

## Experiment-to-role assignment

- EXP-018: establish local held-out representational manipulability.
- EXP-020A: replicate that representational phenomenon at larger model scale.
- EXP-017: show representation intervention does not automatically yield
  behavioral correctness control.
- EXP-019: constrain the behavioral endpoint because evaluator generalization
  failed.
- EXP-021: show fixed readout qualification is not uniformly stable across
  depth.
- EXP-022A: generate/discover the featurewise recalibration rescue signal.
- EXP-023: perform independent preregistered replication and expose
  heterogeneity/`NO_REPLICATION`.
- EXP-024: perform the prospectively reserved condition-panel susceptibility
  test; primary predictor `NOT_SUPPORTED`, with broad descriptive panel benefit.

## Paper Narrative

- Part I: Task-associated structure is locally identifiable and manipulable.
- Part II: Local manipulability does not straightforwardly become behavioral
  control.
- Part III: A fixed readout interface is not uniformly stable across depth.
- Part IV: Simple featurewise recalibration can strongly restore readout
  performance in some conditions.
- Part V: Independent preregistered replication shows the rescue is
  heterogeneous rather than uniformly reproducible.
- Part VI: EXP-024 directly tests the condition-panel susceptibility question;
  a simple degradation-magnitude predictor is not supported, so the mechanism
  remains unresolved.

The narrative is a scientific tension, not a success ladder.

## Introduction Outline

- P1: Why internal representation evidence is often interpreted too strongly.
- P2: Distinguish decodability/manipulability from stable downstream usability.
- P3: Introduce depth-dependent readout compatibility as an interface problem.
- P4: Introduce the controlled experimental program.
- P5: Summarize main findings, including the negative and heterogeneous
  results.
- P6: State contributions.
- P7: Scope and limitations.

No polished prose yet.

## Abstract Scaffold

- Problem: internal representation evidence is often over-interpreted as
  functional control or stable task knowledge.
- Gap: local manipulability does not establish readout stability, transport, or
  behavior.
- Method: controlled held-out manipulation, fixed readout qualification,
  featurewise recalibration, and independent replication.
- Finding 1: task-associated representations are locally manipulable and
  same-family replicated.
- Finding 2: fixed readout compatibility degrades across depth in some
  conditions.
- Replication finding: independent EXP-023 result is `NO_REPLICATION`, with
  strong Split-A rescue and null Split B.
- Boundary: transport, functional binding, and behavioral control are not
  supported by this chain.
- Implication: future work should test an independent predictor of calibration
  susceptibility.

## Related Work Buckets

- Representation probing / decodability: needed to position local
  discriminability claims.
- Representation intervention / steering: needed to position EXP-017/018.
- Layerwise representation dynamics: needed for depth-dependent readout
  results.
- Readout/probe stability: directly relevant to EXP-021/022A/023.
- Representation alignment / transport: relevant but must remain untested in
  the current evidence chain.
- Feature normalization / calibration: needed for featurewise recalibration.
- Mechanistic interpretability: relevant to intervention and readout framing.
- Behavioral validation of interventions: needed for EXP-017/019 boundaries.

Mark all buckets as `PRIOR_ART_SEARCH_REQUIRED` until a separate literature
task provides sufficient citation coverage.

## Methods Outline

- 3.1 Model and representation extraction
- 3.2 Task/semantic class construction
- 3.3 FIT/EVAL separation
- 3.4 Fixed-reference readout
- 3.5 Representation intervention controls
- 3.6 Layerwise readout qualification
- 3.7 Featurewise recalibration conditions: `A0`, `A_mu`, `A_sigma`, `A_mu_sigma`
- 3.8 Primary/secondary statistical testing
- 3.9 Replication criteria
- 3.10 Provenance/reproducibility controls

Keep engineering provenance only insofar as it supports scientific
reproducibility.

## Results Outline

- 4.1 Task-associated representations are locally manipulable
  - Source: EXP-018 and EXP-020A
- 4.2 Local manipulability does not establish behavioral control
  - Source: EXP-017 and EXP-019
- 4.3 Fixed readout compatibility degrades across depth
  - Source: EXP-021
- 4.4 Featurewise recalibration reveals a candidate recovery mechanism
  - Source: EXP-022A
- 4.5 Independent replication reveals split-dependent calibration effects
  - Source: EXP-023
- 4.6 EXP-024 condition-panel susceptibility test: broad positive panel
  benefit but simple predictor not supported
  - Source: EXP-024 canonical result and EXP-024 scientific review
- 4.7 What the combined evidence supports and does not support
  - Integrated claim-boundary synthesis

EXP-023 must be titled as non-replication, not successful replication.
EXP-024 must be titled as a negative primary with a descriptive panel benefit,
not as support for the simple susceptibility predictor.

## Discussion Outline

- 5.1 Representational manipulability versus stable usability
- 5.2 Readout compatibility as a layer-dependent interface problem
- 5.3 Why calibration heterogeneity matters
- 5.4 Relation to coordinate transport: what remains untested
- 5.5 Implications for representation interventions
- 5.6 Limitations
- 5.7 Mechanism gap after condition-panel susceptibility test

Do not present operator/attention theories as findings.

## Limitations

| Limitation | Severity | Status |
| --- | --- | --- |
| controlled/small semantic task universe | nonfatal | visible scope limit |
| primarily Qwen3 model family | follow-up-addressable | cross-model breadth needed |
| limited model-scale breadth | follow-up-addressable | EXP-020A supports same-family only |
| limited independent data families | nonfatal | controlled replication design |
| readout-level rather than functional/behavioral endpoint | nonfatal | boundary is explicit |
| calibration heterogeneity | follow-up-addressable | central unresolved gap |
| exploratory origin of EXP-022A mechanism signal | nonfatal | requires confirmatory framing |
| simple susceptibility diagnostic not predictive; mechanism remains unresolved | follow-up-addressable | highest-priority gap |
| no proof of general coordinate transport | nonfatal | must not be claimed |
| no causal binding evidence | nonfatal | must not be claimed |
| potentially limited ecological validity | follow-up-addressable | not addressed here |

## Figures

See `PAPER-A-FIGURE-PLAN.md`. Approximately seven main figures are proposed from
existing canonical data only.

## Tables

- Table 1: Experiment lineage and role (main or appendix)
- Table 2: Model/task/dataset/split summary (main)
- Table 3: EXP-022A versus EXP-023 comparison (main)
- Table 4: Claim-evidence matrix (appendix)

### Table 3 planned comparison

| Experiment | Role | Split | A0 reference | A0 final-pre | Recalibration final-pre | Effect | Primary support | Cross-split |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EXP-022A | discovery | A original->paraphrase | 0.9167 | 0.6667 | A1 0.75 | G_scale +0.0833 | D_fixed false; G_refit false | PARTIAL_CONCORDANCE |
| EXP-022A | discovery | B paraphrase->original | 0.75 | 0.25 | A1 0.75 | G_scale +0.5 | D_fixed true; G_refit false | SPLIT_HETEROGENEOUS |
| EXP-023 | confirmatory | A | 0.9375 | 0.59375 | A_mu_sigma 0.84375 | G_cal +0.25 | true | NO_REPLICATION |
| EXP-023 | confirmatory | B | 0.9375 | 0.90625 | A_mu_sigma 0.90625 | G_cal 0.0 | false | NO_REPLICATION |

The strongest affected split flips between EXP-022A and EXP-023. Permitted
interpretation: simple fixed variant-direction explanation is not supported.

EXP-024 is a separate condition-panel test (`N = 10`). Its primary Spearman
`rho = 0.28401877872187725`, exact one-sided `p = 0.2115079365079365`, and
registered support is `false`; all 10 conditions had `S_diag > 0` and
`G_eval > 0` descriptively. It is not added to the split-level EXP-022A/EXP-023
table above.

## Claim-Evidence Matrix

See `PAPER-A-CLAIM-EVIDENCE-MATRIX.md`.

## Venue Readiness

See `PAPER-A-STATUS.md`. No acceptance probabilities are assigned.

## Missing Evidence

- Cross-model and larger-model calibration replication.
- A mechanistic condition-level susceptibility model beyond simple independent
  degradation magnitude.

## Next Follow-Up Slot

EXP-024 completed the prospectively reserved susceptibility follow-up. Its
preregistered primary predictor was `NOT_SUPPORTED`, while the broad
panel-level calibration benefit remains descriptive.

No new confirmatory follow-up is authorized unless it addresses a materially
different preregistered question.

## Open Writing Questions

- Which figures are main versus appendix?
- How much engineering provenance belongs in the main paper?
- What prior art must be cited before claiming framework novelty?
- How should EXP-017 and EXP-019 be summarized without hiding the negative
  evidence?
- Which venue should receive the first complete draft?

## Source Authority

- Canonical scientific review: `docs/experiments/EXP-023-SCIENTIFIC-REVIEW.md`
- Canonical scientific review: `docs/experiments/EXP-024-SCIENTIFIC-REVIEW.md`
- Claim ledger: `docs/research/CLAIM-LEDGER.md`
- Hypothesis ledger: `docs/research/HYPOTHESIS-LEDGER.md`
- Experiment lineage: `docs/research/EXPERIMENT-LINEAGE.md`
- Current research brief: `docs/research/CURRENT-RESEARCH-BRIEF.md`
- Research spine: `docs/research/RESEARCH-SPINE.md`
- Construct registry: `docs/research/CONSTRUCT-REGISTRY.md`

This scaffold is `NON-AUTHORITATIVE_DERIVED_FROM_CANONICAL_EVIDENCE`.
