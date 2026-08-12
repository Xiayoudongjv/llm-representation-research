# Recommended Next Experiments

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
six beta values per model. Qwen's encoding/control layer was 16, while its
lowest-IVS threshold-eligible safe-control setting was layer 4 at beta 1.0.
Gemma's encoding peak was final layer 26, while its control and safe-control
setting was layer 16 at beta 0.75. The sampled role structure is therefore
interpretable and model-specific: encoding depth differs, control depth is
similar, and safe-control depth differs. The study did not identify causal
modules, but it did provide pre-behavioral control/safety selections.

Future work:

1. Design a preregistered generation-time intervention pilot using the
   model-specific control/safe-control choices from EXP-016, explicit sham and
   no-intervention controls, and the frozen behavioral evaluation protocol.
2. Replicate the frozen behavioral benchmark on Gemma using normal generation
   and the existing quality-controlled scoring protocol.
3. Add an independent human-annotation sample for scoring reliability.

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
