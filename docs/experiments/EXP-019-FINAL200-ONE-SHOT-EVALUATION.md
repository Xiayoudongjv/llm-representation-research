# EXP-019 Final-200 One-Shot Evaluation

## Frozen Inputs

Final-200, the persisted evaluator artifact, and frozen config were hash-verified before prediction. Dataset size was 200 with 50 rows per class.

## Independence Controls

Only `response_text` was supplied as evaluator input. No evaluator retraining occurred after freeze. No Final-200 example was modified after predictions were generated. Acceptance thresholds were frozen before evaluation.

## One-Shot Procedure

The persisted evaluator was loaded once, class/probability mapping was checked against the frozen config, and one `predict_proba` call generated all 200 predictions. No fitting, hyperparameter modification, or rerun occurred.

## Primary Metrics

- Balanced accuracy: 0.4850
- Macro F1: 0.4580
- Accuracy: 0.4850

## Per-Class Metrics

- logic: precision=0.5909, recall=0.2600, F1=0.3611
- causality: precision=0.3939, recall=0.2600, F1=0.3133
- analogy: precision=0.4468, recall=0.8400, F1=0.5833
- definition: precision=0.5686, recall=0.5800, F1=0.5743

## Confusion Matrix

Rows are true classes; columns are logic, causality, analogy, definition.

| true class | logic | causality | analogy | definition |
| --- | ---: | ---: | ---: | ---: |
| logic | 13 | 7 | 15 | 15 |
| causality | 7 | 13 | 25 | 5 |
| analogy | 1 | 5 | 42 | 2 |
| definition | 1 | 8 | 12 | 29 |

## Procedural vs Independent Performance

Procedural test balanced accuracy and macro F1 were both 1.0000. Independent Final-200 balanced accuracy was 0.4850 and macro F1 was 0.4580. Historical three-word-marker baselines were validation BA=0.8417 and procedural test BA=0.7000.

## Error Audit

There were 103 misclassified rows. The error CSV is descriptive only and did not trigger repair or rerunning.

## Generalization Interpretation

The substantial procedural-to-independent change indicates that procedural performance was likely inflated by lexical or template structure; the frozen evaluator did not meet the preregistered independent-generalization threshold.

## Acceptance Decision

`FAILED_INDEPENDENT_GENERALIZATION`

## EXP-017 Unlock Decision

EXP-017 remains `LOCKED` for targetness evaluation; no EXP-017 output was read.

## Limitations

This is one frozen independent test set and an output-only TF-IDF/logistic-regression evaluator. Its result does not by itself establish semantic task understanding or behavioral steering effects.
