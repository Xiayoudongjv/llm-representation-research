# EXP-018: Independent Validation of Centroid Steering and RSM Preservation

## Status and scope

This is a preregistered representation-level validation design. It directly
addresses the `HOLD_BEFORE_BEHAVIOR` findings in Research Audit v1. It has no
runner yet, does not generate text, and does not evaluate behavior.

The two primary risks are:

1. source/target centroids, steering directions, and nearest-centroid outcomes
   were previously calculated from the same representations; and
2. a low cosine-RSM invariant violation score (IVS) may arise under a generic
   common additive translation rather than a task-directed perturbation.

EXP-018 tests Qwen/Qwen3-1.7B and google/gemma-3-1b-it. It uses the unchanged
24-prompt EXP-003 controlled dataset only. No prompt is used for both centroid
or probe fitting and evaluation within a split.

## Research questions

1. Does a centroid-derived direction move held-out source representations
   toward the target class when the held-out representations did not estimate
   either centroid?
2. Does that movement appear in an evaluator that is fitted separately from
   the steering centroids?
3. Does the task direction preserve held-out source cosine-RSM structure better
   than an equal-norm random common translation?

## Frozen data and splits

The input is `experiments/exp003/prompts_controlled.json`, with four groups
and six items per group. “Items 1-3” and “items 4-6” are frozen as the
following existing IDs, not inferred at runtime from file order.

| Split | Fit IDs per group | Evaluation IDs per group |
|---|---|---|
| A | `*_orig_01`, `*_orig_02`, `*_orig_03` | `*_para_01`, `*_para_02`, `*_para_03` |
| B | `*_para_01`, `*_para_02`, `*_para_03` | `*_orig_01`, `*_orig_02`, `*_orig_03` |

The exact 24 IDs are enumerated in
`experiments/exp018/validation_conditions.json`. This complementary design
also makes prompt-variant distribution a limitation: each split evaluates a
different wording style than it fits. Results must be reported separately by
split before any aggregate statement.

## Frozen models, layers, and beta grid

Primary layers are Qwen L16 and Gemma L16. They are the previously selected
operational-control layers. Gemma L26 is included as a predefined secondary
contrast because it was its representation-best layer in EXP-013. No new layer
search is permitted.

The complete beta grid is `[0.50, 0.75, 1.00]`. No layer, beta, split, metric,
or aggregation rule may be added after observing results.

## Direction fitting and held-out application

For every model, frozen layer, split, and ordered source-target pair:

1. extract the last-token representations for all 24 prompts;
2. select the three fit samples in the source and target groups;
3. compute `delta_task = centroid_target_fit - centroid_source_fit` from fit
   samples only; and
4. apply `h' = h + beta * delta` only to held-out source representations.

There are twelve ordered group transitions. Held-out samples must never change
fitted centroids, directions, preprocessing statistics, or probe parameters.

## Evaluator 1: held-out centroid assignment

The first evaluator computes all four class centroids using only the fit
representations. It classifies each held-out source representation before and
after intervention by cosine similarity to those fit-only centroids.

For every held-out item, report source assignment, target assignment,
similarity to source, similarity to target, and target-minus-source
similarity. This evaluator remains centroid-related, but differs from prior
experiments because both centroids and evaluated examples are split-separated.
It is not the primary independence test.

## Evaluator 2: independent linear probe

The primary transition evaluator is a multinomial logistic-regression probe
fit only on the 12 fit representations (three per group). Its frozen pipeline
is:

- `StandardScaler(with_mean=True, with_std=True)` fit on training features
  only;
- `LogisticRegression(solver="lbfgs", penalty="l2", C=1.0,
  multi_class="multinomial", max_iter=1000, class_weight=None,
  random_state=20260319)`; and
- fixed class order `logic`, `causality`, `analogy`, `definition`.

The fitted scaler and probe are applied unchanged to held-out representations
before and after every condition. Held-out labels are used only to aggregate
predeclared outcomes. Record predicted class, source probability, target
probability, target-minus-source probability, and target prediction rate. The
small fit sample means this is an independent evaluator, not a high-capacity
or definitive classifier.

## Frozen controls

For every task direction, construct two controls and apply exactly the same
beta grid to the same held-out source representations.

| Condition | Vector | Purpose |
|---|---|---|
| task-directed | `delta_task` | Reference direction estimated from fit centroids. |
| matched-norm random | deterministic random `delta_random`, scaled so `||delta_random|| = ||delta_task||` | Tests generic common translation at equal vector norm. |
| opposite direction | `-delta_task` | Tests directional specificity. |

The base random seed is `20260319`. For each vector use NumPy
`SeedSequence([20260319, model_index, layer, split_index, source_index,
target_index])`, sample a standard-normal vector in the representation
dimension, and scale it exactly to the L2 norm of the matching task delta.
The exact indices are frozen in the JSON. A random vector is generated once
per model/layer/split/direction and reused for every associated held-out source
item and beta.

## Relational-preservation comparison

For each held-out source group, calculate the cosine RSM and its upper-triangle
Pearson correlation to the unsteered held-out source RSM. Report RSM Pearson,
IVS (`1 - RSM Pearson`), and RSM Frobenius distance separately for task,
matched-random, and opposite-direction conditions.

The preregistered relational comparison is paired by model, layer, split,
ordered transition, and beta:

`IVS_task < IVS_random` at equal norm.

Absolute low IVS is not a success criterion. With three held-out source items,
each RSM has only three off-diagonal values; therefore pair-level reporting and
the paired direction comparison are required, and any aggregate result must be
described as small-sample evidence.

## Primary success criteria

Centroid-transition evidence may be upgraded above `operational_only` only if
all of the following occur on held-out samples:

1. task steering produces target-directed movement in the held-out centroid
   evaluator;
2. the independent probe shows an increase in target-minus-source probability
   and target prediction rate; and
3. task steering differs meaningfully from matched-norm random steering in the
   same direction on pair-level results.

The report must show every ordered pair rather than relying only on a mean. No
p-value threshold is specified for this intentionally small controlled study.

Relational-preservation evidence may be upgraded only if task steering shows
systematically lower IVS than the paired matched-norm random translation over
the frozen comparisons. “Systematically” requires an explicit count of
task-better, random-better, and tied finite pair-level comparisons; no
post-result threshold may replace that report.

## Negative-result policy

- If held-out centroid movement disappears, downgrade the historical centroid
  transition claim.
- If the probe does not distinguish task from matched-random steering, do not
  call the intervention task-directed.
- If task IVS does not outperform matched-random IVS, downgrade IVS to a
  generic perturbation diagnostic.
- If results differ by Split A versus Split B, report the heterogeneity and do
  not pool it into a general claim.
- Do not redesign metrics, fit/evaluation assignments, or selection criteria
  after results are known.

## Predeclared result records

No output filenames are created by this design task. A future runner must emit
at least one row per model/layer/split/source-target/beta/condition/held-out
item, plus paired aggregate summaries. It must record the frozen configuration
verbatim and save no model weights or hidden-state tensors.

## Interpretation boundary

Even a positive EXP-018 result would test representation-level generalization
and relative RSM preservation only. It would not establish reasoning
improvement, a causal cognitive mechanism, or generation-time behavioral
effects.
