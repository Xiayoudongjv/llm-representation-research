# Behavioral Targetness Framework

## Purpose

EXP-017 measured frozen source-task answer accuracy. That outcome established
neither target-task conversion nor task-style change. This framework separates
representation-level target movement from an independently measured,
target-sensitive behavioral quantity.

## Three Non-Interchangeable Outcomes

| Outcome | Question | Current status |
|---|---|---|
| Representation targetness | Does a hidden-state evaluator indicate target-directed movement? | EXP-018 supports this on its held-out controlled representation design. |
| Behavioral targetness | Does an output become more characteristic of the target task family? | Unmeasured; requires a separately frozen evaluator. |
| Source-task correctness | Is the output correct for its original item? | Measured in EXP-017; not a targetness score. |

The three measures must not be merged into a single “success” label. A lower
source-task accuracy is not target conversion, and a predicted target class is
not evidence of correct target-task performance.

## Independent Evaluation Principle

The future behavioral classifier must not use steered outputs, intervention
labels, correctness changes, hidden states, or steering vectors during design,
training, tuning, or acceptance. Only after it is frozen may it be applied to
published intervention outputs. This prevents targetness features from being
invented around observed differences.

## Planned Operational Measure

The preregistered primary direction is a transparent TF-IDF plus multinomial
logistic-regression classifier trained on a separate, non-steered, balanced
response corpus. For each output it will return class probabilities, including
`P(target_task | output)` and `P(source_task | output)`. The main future
quantity is the change in target probability relative to no intervention, with
TASK versus matched random as the causal comparison.

## Interpretation Limits

If TASK exceeds RANDOM on a frozen targetness measure without excess generic
degradation, that would support target-sensitive behavioral movement in the
tested setting. It would still not establish reasoning improvement, general
task conversion, or an explanation of benchmark difficulty. If TASK and RANDOM
behave similarly, the result is consistent with generic perturbation or with a
limitation of the evaluator. If the evaluator itself fails preregistered
acceptance criteria, no behavioral-targetness interpretation is available.

## Relation to the Negative EXP-017 Result

EXP-017's negative source-accuracy result remains intact. The absence of a
TASK advantage over matched random is not retrospectively attributed to a weak
metric. The current source-accuracy measure simply leaves target-sensitive
behavior unresolved; any later conclusion depends on an independently frozen
evaluator.
