# EXP-019 Independent Behavioral Evaluator Dataset Protocol

## Scope and Risk

This protocol designs a future independent response dataset for the frozen
EXP-019 behavioral-targetness evaluator. It creates no training examples,
trains no classifier, and does not inspect EXP-017 intervention outputs. The
central dataset risk is that a four-class classifier may learn topic or content
vocabulary rather than task-family response structure. Dataset construction
must therefore produce substantially more topical and lexical overlap across
classes than a naïve independently sampled four-class corpus.

## Content-Family Strategy

A **content family** is one semantic topic or concept from which closely
matched responses can be constructed for logic, causality, analogy, and
definition. The intended pattern is shared or closely matched content followed
by one response in each task class. Perfect semantic identity is not required;
the requirement is that class label should not be trivially recoverable from
topic alone.

Families should be class-balanced whenever feasible. The entire family,
including all responses, source prompts, near-duplicates, and paraphrases,
belongs to exactly one split. No family may cross train, validation, or test.

## Operational Class Definitions

| Class | Operational response category |
|---|---|
| logic | Primarily expresses validity, entailment, deduction, condition satisfaction, contradiction, or a logical conclusion. |
| causality | Primarily expresses a cause-effect or mechanism relation. |
| analogy | Primarily expresses relational correspondence or a mapped relation between entities or concepts. |
| definition | Primarily states what a concept means, is, or refers to. |

These are behavioral response categories, not claims about internal cognition.

## Output-Only Constraint

The future classifier receives only `response_text`. It must not receive the
original prompt, source-task label, intervention condition, correctness label,
hidden states, steering vectors, or an item ID that carries task information.
The future dataset schema includes no intervention-condition field.

## Frozen Counts and Family-Level Splits

The minimum remains 190 examples per class, 760 total: 120/class train,
30/class validation, and 40/class test. With fully balanced four-class content
families, this implies a preferred minimum of 190 families: 120 train, 30
validation, and 40 test, each contributing one response per class. If a family
is incomplete, split-level class counts must still meet the frozen targets and
family balance deviations must be recorded.

The split manifest is deterministic with seed `20260812`. Train, validation,
and test are disjoint at content-family, paraphrase-family, source-prompt, and
near-duplicate-family level. The test split remains sealed until evaluator
development choices and acceptance rules are frozen.

## Length and Format Balancing

Responses must be concise because EXP-017 uses concise answers. Record the
following frozen length bands and balance their distributions across all four
classes and splits:

| Band | Token range |
|---|---:|
| short | 1–5 |
| medium | 6–12 |
| limited-long | 13–20 |

No class may consist mainly of one-word responses while another consists mainly
of sentence-length responses. Within each class, vary style so logic is not
mostly yes/no, causality is not mostly “because”, definition is not mostly “X
is”, and analogy is not mostly colon or arrow syntax. This reduces trivial
template recognition without deliberately removing genuine task structure.

## Provenance and Label Quality

Each record must declare provenance: human-authored/manual construction,
deterministic/procedural construction, independently sourced educational
example, or another documented independent source. No single provenance source
may uniquely dominate a class. This protocol does not authorize model-generated
data.

Labels are assigned independently of the future classifier as `clear`,
`borderline`, or `exclude`. Only clear records enter the primary dataset.
Borderline records may be retained separately for later robustness work;
ambiguous responses must not be forced into a class.

## Lexical Challenge and Paraphrases

Prepare a lexical-challenge subset before evaluator training. It should exclude
or mask obvious direct class-label words where possible, including “logic”,
“cause”, “because”, “analogy”, “define”, “definition”, and predeclared similar
markers. It must not be constructed after observing classifier errors.

Reserve independent paraphrase families as well. All near-paraphrases of one
underlying example remain within the same split and have a shared
`paraphrase_family_id`.

## Leakage, Duplicate, and Balance Audits

Before training, audit exact text duplicates, normalized duplicates, high
character-n-gram overlap, high TF-IDF cosine similarity, paraphrase-family
leakage, and template-family leakage across splits. If a near-duplicate family
is found, keep the whole family in one split.

Also report per-class and per-split example count, response length,
provenance, punctuation distribution, yes/no proportion, explicit causal
marker frequency, copular-definition-pattern frequency, and colon/arrow
analogy-format frequency. Exact equality is not required, but no trivial
single-feature separation is acceptable.

## Human Audit and Short-Answer Feasibility

Before training, reserve a blinded manual audit of at least 10% of the future
dataset. Auditors assess label plausibility, ambiguity, lexical leakage, and
length/format anomalies without seeing classifier predictions.

Very short responses may lack enough output-only information to identify task
family. Future evaluator reporting must assess classifiability separately for
short, medium, and limited-long bands. If 1–5-token responses are near chance,
that limitation must be reported rather than hidden. This does not authorize
post-hoc changes to EXP-017 generation length.

## Frozen Acceptance Sequence

1. Construct the independent dataset.
2. Run the dataset leakage audit.
3. Freeze the dataset manifest.
4. Train the evaluator.
5. Validate on the frozen validation split.
6. Run the final test exactly once.
7. Run lexical and paraphrase challenges.
8. Apply the predeclared evaluator acceptance criteria.
9. Only after acceptance, unlock EXP-017 outputs for targetness evaluation.

No steering output may be inspected before step 9.
