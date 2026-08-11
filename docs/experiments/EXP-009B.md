# EXP-009B Scoring Audit and Answer Normalization

## Research Question

How much of EXP-009's apparent error rate is due to brittle scoring rules?

## Why This Experiment Is Needed

EXP-009 established a behavioral baseline but found strict scoring failures.
Before intervention or validity-behavior correlation experiments, the answer
scoring must be audited.

## Input

The audit uses `results/exp009/answer_eval_results.csv` and
`experiments/exp009/reasoning_eval_prompts.json`.

## Method

No new model generation is performed. Model answers are lowercased, stripped,
cleaned of a few leading answer phrases and trailing punctuation, and have
repeated spaces collapsed. A conservative heuristic assigns labels for strict
correctness, clear scoring misses, partial correctness, likely wrong answers,
and ambiguous cases. No LLM judge or human evaluation is used.

## Metrics

- strict accuracy
- audited upper-bound accuracy
- group-level strict and audited comparison
- scoring miss count
- ambiguous count
- partially-correct count
- likely-wrong count

The audited upper bound counts only `strict_correct` and
`likely_correct_scoring_miss` as correct. Ambiguous and partially-correct cases
are not counted as correct.

## Expected Outcomes

### Outcome A

Audited upper-bound accuracy is close to strict accuracy. Strict scoring is
probably adequate for this small set.

### Outcome B

Audited upper-bound accuracy is higher. Strict scoring underestimates some
clearly matching answers.

### Outcome C

Many ambiguous cases remain. Prompt design or scoring rules need improvement.

## Limitations

- heuristic audit only
- no human annotation
- no LLM judge
- semantic correctness is not fully resolved
- small dataset

## Results

Placeholder until the audit is run.

## Next Step

If scoring remains brittle, revise the EXP-009 prompt set and acceptable
answers. If scoring is stable enough, EXP-010 can test the relation between
representation-level validity metrics and answer-level difficulty.
