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

No EXP-011 implementation is proposed here yet.

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
