# Paper A Novelty and Similarity Audit

Read-only Task 099B-0 audit. This document is novelty/prior-art authority for
Task 099B. It does not modify the manuscript and does not substitute for a
commercial full-text plagiarism database.

## 1. Executive Verdict

- `TEXTUAL_SIMILARITY_RISK = LOW`
- `TITLE_COLLISION = NONE`
- `NOVELTY_VERDICT = DEFENSIBLE_BUT_INCREMENTAL`
- `PRIMARY_NOVELTY_TYPE = empirical-design`
- `TUNED_LENS_OVERLAP = HIGH`
- `MODEL_STITCHING_OVERLAP = HIGH`
- `LAYERWISE_READOUT_OVERLAP = MODERATE`
- `FOUND_POST_2024_DIRECT_NEIGHBOR = true`
- `NEW_PRIOR_ART_CHANGES_CORE_POSITIONING = false`
- `PRIOR_ART_OVERLAP_BLOCKING = false`
- `NEW_EXPERIMENT_REQUIRED = false`

The central observation that layer-specific affine readouts are often needed is
not novel. Tuned Lens and model stitching already establish it. Paper-A remains
defensible as a controlled empirical chain: fixed reference readout, FIT-only
featurewise recalibration, held-out source-family separation, preregistered
independent replication, and an explicit negative susceptibility test.

## 2. Audit Scope and Search Date

- Audit date: `2026-08-19`
- Public-web search cutoff: `2026-08-19`
- Repository commit reviewed: `49fcae87567d340eb4e22d62b953cb9c90ee9840`
- Sources used: public arXiv metadata/abstract pages, OpenReview pages, ICML
  2025 virtual site, and public web search engines for exact/near-exact phrases.
- Audit type A: public-web textual similarity screen.
- Audit type B: scientific novelty / prior-art overlap audit.

No commercial full-text similarity database was used. Any lexical measure is a
`PUBLIC-WEB TEXT SIMILARITY SCREEN`, not a Turnitin or iThenticate percentage.

## 3. Paper-A Claim Fingerprint

- Title:
  `Fixed Readout Compatibility and Featurewise Recalibration Across Transformer Depth: A Controlled, Preregistered Evidence Chain with Heterogeneous and Negative Results`
- Central research question:
  Can a fixed semantic readout remain compatible across Transformer depth, can
  low-capacity FIT-only featurewise recalibration restore its utility, is that
  recovery stable across conditions, and can independent degradation magnitude
  predict calibration susceptibility?
- One-sentence central claim:
  Fixed semantic readouts can lose compatibility across depth; FIT-only
  featurewise recalibration can substantially restore readout performance under
  some conditions, but the benefit is heterogeneous and is not reliably
  predicted by simple degradation magnitude.
- Abstract empirical claims:
  - Local task-associated representations are manipulable under held-out
    controls.
  - Manipulability does not produce stable task-specific behavioral advantage.
  - Fixed readout accuracy can drop substantially across depth.
  - Featurewise recalibration can produce large recovery in some conditions.
  - Independent preregistered replication returns `NO_REPLICATION`.
  - The 10-condition panel shows descriptive positivity but the preregistered
    simple degradation-magnitude predictor is `NOT_SUPPORTED`.
- Introduction gap statement:
  Depth-dependent representation change creates a measurement problem when a
  readout trained at one layer is reused at another as if the space were fixed;
  a drop may reflect coordinate incompatibility rather than information loss.
- Contribution bullets / method key phrases:
  - Fixed semantic readout.
  - FIT-only featurewise recalibration.
  - Held-out source-family separation.
  - Explicit negative replication.
  - Preregistered condition panel.
  - Separation of readout recovery from representation equivalence.
- Results core conclusion:
  Readout incompatibility and calibration utility are real but
  condition-dependent.
- Discussion main interpretation:
  Simple degradation magnitude is insufficient to explain calibration
  susceptibility; mechanism remains unresolved.
- Conclusion final claim:
  The evidence supports a bounded, conditional claim rather than a unified
  representation theory.

## 4. Textual Similarity Audit

Method: searched public web/arXiv/OpenReview/ICML pages for exact and
near-exact phrases from the manuscript title, abstract, introduction gap
statement, contribution sentences, and bounded central claim.

- Public exact-title search: no collision found.
- No exact public phrase match was found for the manuscript title or the
  bounded central-claim sentence.
- Common phrases such as "intermediate representations", "layer-specific
  probes", "model stitching", and "fixed readout" are ordinary field
  terminology and are not treated as high-risk plagiarism evidence.
- `PAPER_A_099B0_HIGH_RISK_PHRASE_COUNT = 0`
- `PAPER_A_099B0_TEXTUAL_SIMILARITY_RISK = LOW`

This is a public-web screen only. It cannot rule out similarity against
subscription or institution-only databases.

## 5. Terminology Collision Audit

- `fixed readout`: common but not a standardized claimed term.
- `readout compatibility`: ordinary descriptive phrasing.
- `FIT-only featurewise recalibration`: operationally specific to the paper but
  composed of common components.
- `layerwise readout`: broad prior-art cluster.
- `representation drift` / `readout drift`: common descriptive terms.
- `Tuned Lens`, `model stitching`, `probing`: established named methods.

No protected or distinctively proprietary terminology was identified. The main
collision risk is conceptual overlap, not lexical identity.

## 6. Direct Prior-Art Landscape

- Tuned Lens: per-block affine probes for latent prediction inspection.
- Model stitching: simple learned adapters for functional compatibility.
- Representation similarity/matching: Csisz?rik et al.
- Latent space translation via semantic alignment.
- Functional-alignment caution: stitching performance can mislead.
- Layerwise readout / probing and representation progression literature.
- 2025-2026 neighbors on representation-readout coupling and grokking/collapse
  dynamics.

The paper's own Related Work already concedes that "different layers may
benefit from different affine readouts" is established. The remaining question
is whether Paper-A's specific controlled evidence chain is new.

## 7. Tuned Lens Comparison

- `PAPER_A_VS_TUNED_LENS`: high conceptual overlap on layer-specific affine
  readouts.
- `TUNED_LENS_OVERLAP = HIGH`
- Tuned Lens trains a per-block affine probe from hidden states to vocabulary
  or logit space.
- Paper-A keeps a reference readout fixed and permits only low-capacity
  FIT-only featurewise location/scale recalibration.
- Tuned Lens establishes depth-wise readout mismatch; Paper-A measures
  compatibility of an existing fixed readout rather than fitting a new per-layer
  decoder.

Verdict: not blocking, but Tuned Lens must be cited and the novelty language
must not claim "layers need different readouts".

## 8. Model Stitching / Alignment Comparison

- `PAPER_A_VS_MODEL_STITCHING`: high conceptual overlap on simple adapters
  restoring performance.
- `MODEL_STITCHING_OVERLAP = HIGH`
- Model stitching connects components of different trained models through a
  simple trainable layer.
- Paper-A is within one frozen model across depth and does not stitch model
  halves; it calibrates features of an already fixed readout.
- Recovering accuracy under recalibration does not establish representation
  equivalence.

Verdict: not blocking, but any "simple adaptation can rescue performance"
claim must be scoped as within-model, fixed-readout calibration.

## 9. Layerwise Readout Literature

- `LAYERWISE_READOUT_OVERLAP = MODERATE`
- Relevant anchors: probing/decoding critiques, Tuned Lens, model stitching,
  representation similarity, fresh-head probing, and representation progression
  tracing.
- Paper-A adds a deliberately narrow operational protocol and a
  preregistered negative replication plus condition-panel negative primary.
- The novelty is empirical design rather than introducing the concept of
  layerwise readout analysis.

## 10. 2025-2026 New Neighbors

- `FOUND_POST_2024_DIRECT_NEIGHBOR = true`
- `Functional Alignment Can Mislead` (ICML 2025 Spotlight) reinforces the
  readout-recovery vs representation-equivalence distinction.
- `Fresh-Head Probe` (OpenReview `230T2UcWwR`) studies failure localization
  between representation and readout.
- `Causality != Decodability` (NeurIPS 2025, arXiv:2510.09794) reinforces the
  boundary between decoding and causal role.
- `Post-Grokking Collapse` (arXiv:2608.07436) and `Two Speeds of Learning`
  (arXiv:2605.27078) are nearby in mechanism style but not direct substitutes
  for the Paper-A preregistered condition panel.
- `NEW_PRIOR_ART_CHANGES_CORE_POSITIONING = false`
- `PRIOR_ART_OVERLAP_BLOCKING = false`

These neighbors require citation and careful positioning. They do not
replicate the exact frozen Paper-A chain.

## 11. Claim-by-Claim Novelty Matrix

| Claim family | Prior-art status | Overlap | Verdict |
| --- | --- | --- | --- |
| Layers can need different affine readouts | Tuned Lens, stitching | HIGH | Established; do not claim novelty |
| Fixed-readout accuracy can drop across depth | Probing/Tuned Lens adjacent | MODERATE | Defensible but must be scoped |
| FIT-only featurewise recalibration can recover some conditions | Stitching/alignment adjacent | MODERATE | Defensible as controlled operational variant |
| Recovery is heterogeneous / `NO_REPLICATION` | Paper-A chain | LOW | Defensible negative evidence |
| Simple degradation magnitude does not predict calibration benefit | Paper-A EXP-024 | LOW | Defensible preregistered negative |
| Readout recovery is not representation equivalence | Functional Alignment Can Mislead | LOW for new claim, HIGH for boundary | Defensible but must cite |

`CLAIMS_REQUIRING_NARROWING_COUNT = 3`

## 12. Top-5 Direct Prior Works

1. Belrose et al., *Eliciting Latent Predictions from Transformers with the
   Tuned Lens*, arXiv:2303.08112.
2. Bansal, Nakkiran, and Barak, *Revisiting Model Stitching to Compare Neural
   Representations*, NeurIPS 2021, arXiv:2106.07682.
3. Csisz?rik et al., *Similarity and Matching of Neural Network
   Representations*, NeurIPS 2021, arXiv:2110.14633.
4. *Functional Alignment Can Mislead: Examining Model Stitching*, ICML 2025
   Spotlight, https://icml.cc/virtual/2025/poster/44458.
5. *Tracing Representation Progression*, arXiv:2406.14479.

All five are `must_cite = true`.

## 13. Paper-A Defensible Novelty

Paper-A's defensible novelty is the controlled empirical design and the
explicit negative/boundary evidence chain:

- One frozen model family with a fixed semantic readout.
- Low-capacity FIT-only featurewise recalibration, not arbitrary alignment.
- Held-out source-family separation between FIT and EVAL.
- Preregistered independent replication with `NO_REPLICATION`.
- Preregistered condition-panel primary test with `NOT_SUPPORTED`.
- Explicit separation of readout recovery from representation equivalence.

This is `empirical-design` novelty, not a new method or a new conceptual
mechanism.

## 14. Claims That Must Be Removed or Narrowed

1. Any sentence that can be read as "Paper-A discovers that layers need
   different readouts." Narrow to: "Paper-A measures the compatibility of a
   fixed readout under a restricted recalibration protocol."
2. Any sentence that implies calibration recovery establishes representation
   or coordinate equivalence. Narrow to: "Recovery is a bounded within-model
   readout utility result and is not evidence of equivalence."
3. Any sentence that suggests degradation magnitude is generally sufficient or
   insufficient across models, tasks, or representations. Narrow to: "In the
   frozen EXP-024 condition panel, simple degradation magnitude did not predict
   calibration benefit."

## 15. Introduction / Contribution Reframing Guidance

- Open with the measurement problem, not a claim that depth-wise readout
  incompatibility is newly discovered.
- Explicitly state that Tuned Lens and model stitching establish that simple
  affine/adaptor readouts are often layer-specific.
- Present Paper-A's contribution as a controlled, preregistered evidence chain
  with heterogeneous and negative results.
- Make the negative replication and negative susceptibility result central, not
  appendix caveats.
- Avoid universal language: "calibration utility is real", "readout recovery
  implies equivalence", "representation drift explains behavior", and
  "functional binding" are not supported.
- Cite all top direct prior works before claiming a gap.

## 16. Inputs for Task 099B

### Required Audit Flags

- `PAPER_A_099B0_AUDIT_COMPLETE = true`
- `PAPER_A_099B0_SEARCH_CUTOFF_DATE = 2026-08-19`
- `PAPER_A_099B0_TEXTUAL_SIMILARITY_RISK = LOW`
- `PAPER_A_099B0_HIGH_RISK_PHRASE_COUNT = 0`
- `PAPER_A_099B0_TITLE_COLLISION = NONE`
- `PAPER_A_099B0_TOP_DIRECT_PRIOR_COUNT = 5`
- `PAPER_A_099B0_TUNED_LENS_OVERLAP = HIGH`
- `PAPER_A_099B0_MODEL_STITCHING_OVERLAP = HIGH`
- `PAPER_A_099B0_LAYERWISE_READOUT_OVERLAP = MODERATE`
- `PAPER_A_099B0_FOUND_POST_2024_DIRECT_NEIGHBOR = true`
- `PAPER_A_099B0_NEW_PRIOR_ART_CHANGES_CORE_POSITIONING = false`
- `PAPER_A_099B0_PRIOR_ART_OVERLAP_BLOCKING = false`
- `PAPER_A_099B0_NOVELTY_VERDICT = DEFENSIBLE_BUT_INCREMENTAL`
- `PAPER_A_099B0_PRIMARY_NOVELTY_TYPE = empirical-design`
- `PAPER_A_099B0_PAPER_A_VS_TUNED_LENS = same phenomenon, different fixed-readout protocol`
- `PAPER_A_099B0_PAPER_A_VS_MODEL_STITCHING = within-model fixed readout calibration, not cross-model stitching`
- `PAPER_A_099B0_CLAIMS_REQUIRING_NARROWING_COUNT = 3`
- `PAPER_A_099B0_CRITICAL_MISSING_CITATION_COUNT = 5`
- `PAPER_A_099B0_NEW_EXPERIMENT_REQUIRED = false`

### TASK_099B_REQUIRED_INPUTS

- Top-5 direct prior works: Tuned Lens; Revisiting Model Stitching; Similarity
  and Matching; Functional Alignment Can Mislead; Tracing Representation
  Progression.
- Novelty threat ranking:
  1. Tuned Lens (`HIGH`)
  2. Revisiting Model Stitching (`HIGH`)
  3. Similarity and Matching (`MODERATE-HIGH`)
  4. Functional Alignment Can Mislead (`MODERATE`, mainly boundary claim)
  5. Tracing Representation Progression (`MODERATE`)
- Textual-similarity risks: `LOW`; no public exact-title or central-claim
  phrase collision found.
- Terminology collisions: ordinary field terms; no proprietary collision.
- Central claim risk: broad wording can be read as established prior art.
- Gap-statement risk: "information may remain present" must not become a
  representation-equivalence claim.
- Contribution risk: must not imply layer-specific readout novelty.
- Claims requiring removal/narrowing: the three in Section 14.
- 2025-2026 direct neighbors: Functional Alignment Can Mislead, Fresh-Head
  Probe, Causality != Decodability, Post-Grokking Collapse, Two Speeds of
  Learning.

Task 099B must use this audit as its novelty authority and must not restart
from an unverified prior-art baseline.
