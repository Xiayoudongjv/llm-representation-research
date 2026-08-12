# EXP-019 Error Audit

## Status

**POST-DECISION DESCRIPTIVE ANALYSIS**. This document uses the already
generated one-shot predictions only. It did not retrain the evaluator, alter
Final-200, remove features, or trigger another prediction run.

## Overall Result

Final-200 balanced accuracy was 0.4850, macro F1 was 0.4580, and accuracy was
0.4850. There were 103 errors among 200 frozen examples.

## Confusion Directions

The largest single off-diagonal direction was causality to analogy: 25 of 50
causality examples. Other large directions were logic to analogy (15), logic
to definition (15), and definition to analogy (12). These counts describe the
frozen evaluator on this dataset; they do not identify causal features or
license a post-hoc change.

## Class-Wise Performance

| Class | Recall | F1 |
|---|---:|---:|
| logic | 0.2600 | 0.3611 |
| causality | 0.2600 | 0.3133 |
| analogy | 0.8400 | 0.5833 |
| definition | 0.5800 | 0.5743 |

Analogy generalized better than logic and causality in this sample. This is a
descriptive class difference, not evidence of a stable or universal hierarchy.

## Confidence

Mean maximum probability was 0.3462 and median maximum probability was
0.3339. Mean maximum probability was 0.3625 on correct rows and 0.3309 on
incorrect rows. Low confidence is consistent with uncertainty under the frozen
classifier, but this audit does not calibrate, retune, or reinterpret the
model.

## Provenance Performance

| Provenance | n | Accuracy | Balanced accuracy |
|---|---:|---:|---:|
| ai_assisted_surface_normalized | 38 | 0.4737 | 0.4923 |
| independent_external | 39 | 0.4615 | 0.4813 |
| not_recorded | 72 | 0.5000 | 0.4250 |
| rule_composed | 51 | 0.4902 | 0.5417 |

## Topic Performance

Topic groups were uneven, from one to 48 examples. The larger groups had
accuracy of 0.5532 for biology (n=47), 0.4583 for earth science (n=48), 0.4167
for physics (n=24), and 0.6774 for technology (n=31). Small topic groups are
too sparse for comparative conclusions.

## Length-Band Performance

| Length band | n | Accuracy | Balanced accuracy |
|---|---:|---:|---:|
| short | 5 | 0.0000 | 0.0000 |
| medium | 132 | 0.4318 | 0.4842 |
| limited_long | 63 | 0.6349 | 0.5895 |

The short band is especially small and is descriptive only. No example was
removed or edited based on these results.

## Boundary

The Final-200 set is now contaminated for confirmatory evaluation of any
redesigned evaluator. These observations may guide future hypotheses, but a
future evaluator requires a new untouched independent test set.
