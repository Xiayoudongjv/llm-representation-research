# Recommended Next Experiments

## EXP-019 Target-Sensitive Behavioral Evaluation

EXP-019 is intended to distinguish representation-level target movement from
target-sensitive behavioral movement. It does not attribute the negative
EXP-017 source-accuracy result to a weak metric; that is an unresolved
possibility requiring an independently frozen evaluator.

The current 760-row corpus is a procedural development corpus. It is
structurally valid but remains under scientific validity audit and is not the
frozen final behavioral evaluator dataset. The next gate is independent
natural final-set construction and human audit. The evaluator is not yet
valid, and no EXP-017 output may inform dataset design, feature design, or
evaluator acceptance.

## Updated Recommendation: EXP-011 Expanded Answer-level Dataset

EXP-010 remains inconclusive because its correlation analysis has only four
groups, and the answer-level dataset contains only six questions per group.
Before any intervention experiment, the behavioral evaluation should be made
larger, balanced, and less dependent on brittle answer matching.

EXP-011 should:

- expand each group from 6 to approximately 20-30 questions
- keep a deterministic short-answer format
- improve acceptable-answer lists and scoring documentation
- preserve balanced group sizes
- produce both group-level and item-level accuracy
- optionally include conservative audit labels and a human annotation sample

The dataset design and EXP-011B normal-generation evaluation are complete.

## EXP-011 Status

Dataset design, EXP-011B normal generation, and the EXP-011C conservative
scoring audit are complete. The audit found eight defensible lexical or
wording misses and a conservative audited accuracy of 0.750, but it does not
replace independent human annotation or establish reasoning quality.

EXP-011D applied exactly those eight approved additions and reproduced 0.750
through offline rescoring. The expanded behavioral baseline is provisionally
frozen pending independent annotation or new evidence.

EXP-012 replaced EXP-010's preliminary behavior with the frozen benchmark and
found benchmark-sensitive descriptive correlations, including two sign changes.
With only four groups, it does not justify further representation-behavior
interpretation.

EXP-013 then replicated the controlled 24-prompt geometry analysis on
`google/gemma-3-1b-it` using raw plain-text prompts and normalized depth. Both
task-associated geometry and paraphrase-controlled signal replicated, but the
largest Gemma separation occurred at its final layer while its largest
silhouette occurred at normalized depth 0.62. This supports a cautious
second-model representation-level steering probe, not a general claim about
universal layer locations or behavioral effects.

EXP-014 completed that fixed Gemma steering probe at the model-specific layer
26. All 12 ordered transitions reached full target assignment, and increasing
beta increased both target-directed movement and relational distortion. Gemma's
predeclared exploratory operating point was beta 1.0: beta 0.75 reached mean
assignment 0.875 with mean IVS 0.017970, unlike Qwen's 1.0 and 0.002850. The
cross-model evidence therefore supports model-dependent operating points, not a
universal beta.

EXP-015 tested fixed low, mid, and final indices in both models without
changing prompts, layers, or beta values after observation. Qwen's encoding and
control layer were both 16, but its safe-control layer was 28. Gemma's encoding
layer was 26, while both its control and safe-control layer were 16. Gemma's
beta-0.75 IVS range across tested layers was 0.017768, exceeding the
predeclared materiality threshold of 0.01. This pilot supports a broader
model-specific layer-validity study rather than immediate generation-time
intervention.

EXP-016 completed that preregistered expansion across seven sampled layers and
six beta values per model. Qwen's operational encoding/control selection was
layer 16, while its lowest-mean-IVS threshold-eligible setting was layer 4 at
beta 1.0. Gemma's operational encoding selection was final layer 26, while its
control and lowest-mean-IVS selection was layer 16 at beta 0.75. These are
sampled-grid operational labels, not causal layer roles. In particular, Qwen
L4 at beta 1.0 had mean assignment 0.917 but minimum pair assignment 0.667,
so it is mean-constrained rather than pairwise-robust safe control.

Research Audit v1 found a critical construction-evaluation coupling in the
historical centroid-steering results: the source/target centroids and deltas
were fitted on representations that were also evaluated by nearest-centroid
assignment. It also found that absolute low IVS is not task-specific evidence
without matched-norm random common-translation controls. Consequently,
EXP-017 remains limited to a future hook-semantics diagnostic, not a full
behavioral-effect interpretation.

EXP-018 now freezes the required independent representation validation before
any behavioral study. It uses complementary three-per-group fit/evaluation
splits of the unchanged EXP-003 controlled prompts, fit-only centroids, a
fit-only multinomial linear probe, matched-norm random and opposite-direction
controls, and an explicit task-versus-random IVS comparison. It does not create
a runner or run either model at preregistration time.

Future work:

1. Implement EXP-018 exactly as preregistered, without new layer or beta
   search, and inspect held-out task-versus-random outcomes.
2. Implement only a tiny Qwen KV-cache hook diagnostic for the frozen EXP-017
   semantics, then stop for inspection before behavioral generation.
3. Do not interpret or expand EXP-017 behavioral effects unless EXP-018
   resolves the construction-independence gate.
4. Replicate the frozen behavioral benchmark on Gemma using normal generation
   and the existing quality-controlled scoring protocol.
5. Add an independent human-annotation sample for scoring reliability.

The previous exploratory options are retained below as historical planning
context; this recommendation supersedes their priority ordering.

## Option A: EXP-008 Generation-time Intervention Probe

- **Goal:** Apply a carefully instrumented intervention during generation at a selected layer and beta.
- **Why it matters:** Tests whether representation-level movement has an observable generation-time consequence.
- **Difficulty:** High; requires robust hooks, safety checks, and clear controls.
- **Expected value:** High, but difficult to interpret without answer-level evaluation.
- **Recommendation priority:** 3.

## Option B: EXP-008 Answer-level Reasoning Evaluation

- **Goal:** Evaluate answers on controlled tasks before and after an intervention or representation-derived condition.
- **Why it matters:** Connects representation measurements to task outcomes.
- **Difficulty:** Medium to high; needs a defensible dataset, scoring method, and baselines.
- **Expected value:** Very high for testing behavioral relevance.
- **Recommendation priority:** 2.

## Option C: EXP-008 Invariant-constrained Steering

- **Goal:** Select or optimize steering strengths that improve target movement while penalizing RSM distortion.
- **Why it matters:** Directly tests the transition-validity trade-off found in EXP-006 and EXP-007.
- **Difficulty:** Medium; remains representation-level and reuses current data and metrics.
- **Expected value:** High for strengthening the method before generation-time work.
- **Recommendation priority:** 1.

## Option D: EXP-008 Multi-model Replication

- **Goal:** Repeat controlled geometry, steering, and frontier analyses on additional open models.
- **Why it matters:** Tests whether the findings are specific to one model.
- **Difficulty:** Medium to high, depending on hardware and cache availability.
- **Expected value:** High for external validity, but broadens scope before the current proxy is strengthened.
- **Recommendation priority:** 4.

## Recommended Next Step

Start with **Option C, Invariant-constrained Steering**.
It follows directly from the observed frontier and keeps the next step inside the established representation-level scope.
Option B should follow to test answer-level relevance before claims about reasoning behavior.
