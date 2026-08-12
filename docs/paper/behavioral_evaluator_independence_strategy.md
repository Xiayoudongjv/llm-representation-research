# Behavioral Evaluator Independence Strategy

The current 760-row corpus is a procedural development corpus. Its balanced
families and split isolation are useful, but Task 049B found substantial
lexical and template shortcut risk, including a strong simple-marker baseline
and single-source `rule_composed` provenance. It must not be described as the
frozen final behavioral evaluator dataset.

## Two Evidence Tiers

Tier 1 retains the existing procedural training, validation, test, and lexical
challenge metrics as descriptive development robustness evidence. These
metrics are not discarded or retroactively changed.

Tier 2 is an independent natural-language final set. It is the decisive test
of evaluator validity and is not merged with the procedural corpus. Its
primary set contains exactly 200 clear, balanced examples: 50 per class.

## Independence Requirements

The final set must use at least two genuinely distinct provenance categories,
with no source above 70% and no class uniquely tied to a provenance. It must
not use the current generator, procedural template families, current marker
vocabulary as a writing recipe, classifier predictions, or EXP-017 outputs.
It should contain natural, self-contained short answers across overlapping
neutral domains.

Before classifier evaluation, exact and normalized duplicates, repeated
three-word prefixes, character n-gram similarity, and TF-IDF nearest-neighbor
similarity against the procedural corpus must be audited with thresholds fixed
in advance. A blinded human audit covers at least 40 primary examples and
records agreement, naturalness, lexical giveaway, self-containedness, and
ambiguity.

## Acceptance and Lock

The primary classifier and hyperparameters are frozen before final-set results
are viewed. The independent set is evaluated exactly once. Acceptance requires
balanced accuracy >= 0.70, macro-F1 >= 0.70, and recall >= 0.60 for every
class. Failure is recorded as `FAILED_INDEPENDENT_GENERALIZATION`; EXP-017
remains locked. Only a passing Tier 2 result unlocks targetness scoring.
