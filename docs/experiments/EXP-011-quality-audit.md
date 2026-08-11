# EXP-011 Dataset Quality Audit

## Purpose

This audit reviews the 80 EXP-011 short-answer items before any model run. It
checks semantic determinism, answer coverage, template repetition, difficulty,
and the limitations of containment-based scoring.

## Audit Criteria

Every item receives a quality label, ambiguity risk, scoring risk, estimated
difficulty, issue types, and a short note in
`experiments/exp011/dataset_quality_audit.csv`. The audit records the original
and final wording for every conservative revision.

## Group-specific Risks

Logic items are checked for explicit premises and conclusions. Causality items
must state a single direction rather than rely on modal or multi-causal wording.
Analogy items receive the strictest review because a target can otherwise have
several natural relations. Definition items must map to one common term without
leaking that term in the question.

## Revisions

Twenty items were revised while retaining their IDs and group counts: two
logic items, eight causality items, eight analogy items, and two definition
items. Revisions removed real-world exception-prone logic premises, weak causal
modality, context-free acceptable answers, and analogy or definition targets
with multiple plausible answers.

## Difficulty Balance

Difficulty is a conservative structural estimate, not a model-performance
measure. Most items are easy, with medium items distributed across all four
groups; no items are labeled hard. The audit reports group-level counts rather
than forcing artificial equality.

## Scoring Risks

Task 022 found eight substring risks from two-character `no` answers under
`case_insensitive_contains`. Task 023 introduced `src/answer_scoring.py` and
changed all EXP-011 items to `boundary_aware` matching. The post-fix audit has
zero remaining substring-scoring-risk items. Legacy raw substring support is
retained only for reproducibility.

## Final Readiness Decision

`dataset_ready_for_model_evaluation` is currently `true`. The final wording has
no remaining flagged ambiguity, duplicate, or raw-substring risk under the
boundary-aware scoring configuration.

EXP-011D subsequently applied only the eight clear lexical or wording additions
identified by EXP-011C. No partial, ambiguous, or likely wrong answer was added
to the accepted vocabulary.

## Limitations

This is a rule-based/manual design audit and not empirical proof that items are
unbiased or equally difficult. It does not run Qwen, load a language model, or
measure model behavior.
