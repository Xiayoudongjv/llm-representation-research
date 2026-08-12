# EXP-019 Independent Target-Sensitive Behavioral Evaluator Preregistration

## Status and Central Question

This is a design preregistration only. It does not train an evaluator, inspect
EXP-017 generated outputs, or define a new intervention experiment. The future
question is: **does an independently validated hidden-state task transition
produce a corresponding increase in target-task behavioral characteristics?**
This is distinct from whether steering improves source-task accuracy.

## Non-Circularity Rule

The evaluator must be designed, trained, tuned, and accepted without using
EXP-017 `TASK_REAL`, `MATCHED_RANDOM`, or `OPPOSITE` outputs; intervention
labels; EXP-017 correctness differences; hidden states; or steering vectors.
EXP-017 outputs may be evaluated only after the evaluator, its data split, and
acceptance decision are frozen. Source-task correctness remains a separate
previously measured outcome and must not be used as an evaluator feature or
training label.

## Target Classes and Distinct Concepts

The fixed task families are logic, causality, analogy, and definition. The
future report must retain three distinct quantities:

1. **Task-style targetness:** structural characteristics of a response that
   are typical of a target family.
2. **Task-class prediction:** the class assigned by a frozen evaluator seeing
   only the response text.
3. **Source-task correctness:** answer correctness under EXP-011D's frozen
   rule, reported separately from targetness.

Class prediction is an operational behavioral measure, not proof that an
answer performs the target task correctly.

## Evaluator-Family Decision

| Family | Independence | Shortcut risk | Reproducibility / complexity | Decision |
|---|---|---|---|---|
| Hand-coded lexical heuristics | Auditable but feature choice can be post hoc | High | High / low | Not primary. |
| Hand-coded structural heuristics | Auditable | Medium; difficult to cover all classes fairly | High / medium | Optional descriptive audit only. |
| TF-IDF + LogisticRegression | Separate labeled data; transparent coefficients | Moderate and auditable | High / low | **Frozen primary direction.** |
| Frozen small encoder + classifier | Separate data possible | Moderate; less inspectable | Medium / medium-high | Deferred comparator, not primary. |
| Blinded human annotation | Independent if condition-blind | Lower lexical shortcut risk | Medium / high | Optional evaluator audit. |
| LLM judge | Prompt/model dependence and opaque revisions | High / variable | Lower / medium | Not permitted as primary evaluator. |

The proposed primary evaluator is a deterministic word- and character-TF-IDF
feature union with multinomial `LogisticRegression`. It is selected because
coefficients and top features can be inspected, the pipeline is compact, and
all fitting can be reproduced from a separate response dataset. It is not
accepted merely for high training accuracy.

## Independent Evaluator-Training Data

Create a new, non-steered response dataset with clean examples labeled by task
family. It must exclude all EXP-017 outputs, intervention labels, hidden-state
vectors, steering vectors, and benchmark correctness metadata. Examples may be
independently authored or sourced from appropriately documented non-steered
materials, but each record must preserve provenance and a task-family label.

The minimum desired balanced corpus is 190 responses per class (760 total):
120/class train, 30/class validation, and 40/class final test. Each split must
include independently authored paraphrase variants where feasible. No class may
borrow records, near-duplicates, or prompt-response pairs across splits.

## Frozen Data Splits and Development Policy

Before collection or training, assign a stable record ID and split using a
documented deterministic split manifest with base seed `20260812`. The train,
validation, and final-test partitions are disjoint by response, source prompt,
and near-duplicate family. Development may inspect train and validation only.
The final test set remains sealed until preprocessing, vocabulary policy,
regularization grid, and acceptance decision rules are frozen. EXP-017 outputs
may not enter any split.

## Lexical-Leakage Audit

The evaluator must report, without post hoc feature removal:

- top positive TF-IDF features per class and their document frequencies;
- a held-out confusion matrix and per-class precision/recall;
- a frozen lexical-challenge test in which obvious explicit class-name words
  and predeclared task-label phrases are removed or replaced;
- performance on held-out paraphrase examples; and
- lexical-overlap summaries between train, validation, and test records.

The evaluator is rejected if acceptance depends on a few explicit task-name
markers, a single collapsed class, or training-only performance.

## Acceptance Criteria

All criteria must be met before freezing the evaluator for post hoc application
to EXP-017 outputs:

1. final-test balanced accuracy at least **0.70**;
2. final-test macro-F1 at least **0.70**;
3. every class recall at least **0.60**;
4. held-out paraphrase subset balanced accuracy at least **0.60**;
5. lexical-challenge balanced accuracy at least **0.55** and no more than
   0.15 below the ordinary final-test balanced accuracy; and
6. the top-feature audit must show no single explicit class-name marker is the
   sole plausible basis for a class decision.

These are deliberately moderate, predeclared thresholds for a four-way,
undergraduate-scale text task. Failure leaves the behavioral targetness
question unresolved; it does not authorize threshold relaxation or evaluator
substitution after looking at EXP-017 outputs.

## Future Metrics After Evaluator Freeze

For each output, a future analysis may record:

- `P(target_task | output)`;
- `P(source_task | output)`; and
- `target_minus_source_behavior_probability`.

The primary quantity is change in target-behavior probability relative to
`NO_INTERVENTION`. The primary causal comparison is `TASK_REAL` versus
`MATCHED_RANDOM`; `TASK_REAL` versus `OPPOSITE` is secondary. A class flip is
not, by itself, successful task conversion.

## Interpretation Matrix

| Frozen future pattern | Interpretation ceiling |
|---|---|
| Representation targetness increases; behavioral targetness increases; source accuracy unchanged | Behavioral direction changed without demonstrated capability improvement. |
| Representation targetness increases; behavioral targetness unchanged | Representation-behavior dissociation under these measures. |
| TASK and RANDOM increase targetness similarly | Generic perturbation or evaluator limitation, not task-specific control. |
| Evaluator fails acceptance | The behavioral targetness question remains unresolved. |

## Optional Blinded Human Audit

An optional small human-validation subset may assess only task-family
characteristics and separately judge correctness. Annotators must be blinded to
intervention condition and must not see condition labels or steering claims.
This audit is not executed or designed into a scoring override here.

## Boundary

No model run, evaluator training, classifier fitting, layer/beta search, LLM
judge, or EXP-017 output inspection is authorized by this preregistration.
