# EXP-019 Evaluator Development

## Goal

The evaluator estimates `P(task_class | response_text)` for logic, causality,
analogy, and definition. It does not assess correctness, reasoning ability,
answer quality, semantic validity, or improvement from an intervention.

## Data Separation

Training, configuration selection, and all reports use only the procedural
760-row corpus. The independent Final-200 candidate pool was not read for
selection or evaluation. EXP-017 outputs remained unread.

## Procedural Development Corpus

The canonical corpus is `data/behavioral_targetness_dataset.csv`: 190 rows per
class, all with recorded `rule_composed` provenance. Earlier audits documented
substantial template and lexical-shortcut risk, so strong procedural metrics
cannot be interpreted as semantic robustness.

## Frozen Split

Family-level splits use seed 20260812: 480 train rows (120 families/class),
120 validation rows (30/class), and 160 procedural test rows (40/class).
Hyperparameters are selected on validation only; the selected pipeline is fit
on train only for the one procedural test protocol.

## Evaluator Family

The frozen primary family is word plus `char_wb` TF-IDF with multinomial
Logistic Regression. Input is raw `response_text` only. IDs, labels,
provenance, topics, prompts, and length metadata are not model features.

## Validation Search

The frozen 80-configuration grid crosses the declared word/character n-gram,
minimum-document-frequency, and C values. Selection uses balanced accuracy,
then macro-F1, minimum class recall, and simplicity for configurations within
0.005 balanced accuracy.

## Frozen Configuration

The persisted configuration records class order as `logic`, `causality`,
`analogy`, `definition`, train/validation hashes, seed, selected validation
metrics, and access flags. The classifier's internal lexical class-column
order is separately recorded and mapped to the fixed output order.

## Procedural Test

The procedural test report contains balanced accuracy, macro-F1, accuracy,
per-class metrics, confusion matrix, and descriptive probability statistics.
It is a one-protocol result and does not authorize retuning.

## Lexical Challenge

The frozen subset is `lexical_challenge=true` within the procedural test
split: 20 rows, five per class. Its balanced accuracy is compared against the
ordinary procedural test balanced accuracy using the preregistered 0.15-drop
rule.

## Paraphrase Challenge

No separate frozen held-out paraphrase evaluation set exists in the current
procedural corpus. The result is `PARAPHRASE_CHALLENGE_NOT_AVAILABLE`; no new
set was generated after model selection.

## Shortcut Audit

The feature audit reports positive and negative word/character coefficients,
feature-group magnitude, confusion matrix, and per-class results. The earlier
three-word marker diagnostic (validation balanced accuracy 0.8417; test 0.7000)
is retained as a warning rather than a comparator that proves robustness.

## Limitations

All 760 corpus rows are procedurally rule-composed, and the historical data
validity audit classified the corpus as requiring diversity remediation.
Perfect procedural performance can therefore reflect construction templates or
lexical regularities. This evaluator is not semantically validated.

## Evaluator Development Status

The development status is `EVALUATOR_DEV_MIXED`: procedural and lexical
criteria can pass while the preregistered held-out paraphrase evidence is not
available.

## Independent Final-200 Gate

The independent Final-200 set remains untouched. It must be human-audited and
frozen before it can serve as the independent evaluation gate.

## EXP-017 Lock Status

EXP-017 remains locked. No EXP-017 output was read, and this development result
does not unlock behavioral intervention analysis.
