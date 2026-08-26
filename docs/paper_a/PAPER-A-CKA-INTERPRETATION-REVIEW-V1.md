# PAPER-A CKA Interpretation Review V1

## Scope

This review uses only `cka_functional_summary.json` and
`cka_comparison_manifest.json`. The analysis is restricted to the frozen EVAL
split, directed off-diagonal layer pairs, arithmetic mean over the ten frozen
EVAL conditions, and model-wise Spearman associations. No models were pooled.

## 1. Observed statistics

| Model | Pairs | CKA vs C0 | CKA vs D | CKA vs R |
|---|---:|---:|---:|---:|
| Qwen | 756 | 0.8371975188 | -0.8373251441 | -0.6738306904 |
| OLMo | 240 | 0.7588530439 | -0.8082050892 | -0.3729283754 |
| Llama | 240 | 0.7706164976 | -0.7633765918 | -0.5188534647 |

The primary registered comparison is CKA vs C0. CKA vs D and CKA vs R are
secondary comparisons. These are observed rank associations, not causal
effects.

## 2. Model-wise comparison

The three model-specific analyses all show a positive CKA–C0 association in
their respective pair sets. The three CKA–D associations are negative, and the
three CKA–R associations are also negative. The magnitudes differ by model;
therefore the results should be reported separately rather than summarized by
a pooled estimate.

The model-wise pair counts are structurally different because the layer counts
differ: Qwen contributes 756 directed pairs, while OLMo and Llama each
contribute 240. This is another reason not to pool the observations.

## 3. Relationships examined

### CKA and C0

The observed Spearman associations are positive for Qwen, OLMo, and Llama.
Within each model and the evaluated EVAL layer-pair set, larger CKA values are
associated with larger C0 values in rank order.

This supports a model-wise descriptive relationship between CKA and C0. It
does not establish that CKA causes compatibility or that CKA is a substitute
for C0.

### CKA and D

The observed Spearman associations are negative for all three models. This is
a model-wise numerical relationship between CKA and the registered D values
under the frozen condition pooling.

The result supports reporting the association as a secondary comparison. It
does not establish a mechanism for degradation or imply that CKA determines D.

### CKA and R

The observed Spearman associations are negative for all three models, with
different magnitudes across models.

This supports a descriptive model-wise comparison between CKA and R. It does
not establish why restricted recovery varies, nor does it establish a causal
or mechanistic relation.

## 4. Evidence classification

### SUPPORTED

- In the EVAL split, CKA has model-specific rank associations with C0 across
  directed off-diagonal layer pairs.
- In the same restricted analysis, CKA can be compared descriptively with D
  and R through model-wise Spearman statistics.
- The association signs and magnitudes can be reported separately for Qwen,
  OLMo, and Llama.
- The analysis is a secondary comparison using the recorded condition pooling;
  it does not introduce a new functional metric.

### NOT_SUPPORTED

- Causal claims linking CKA to functional compatibility, degradation, or
  recovery.
- Mechanism discovery or explanation of information flow.
- Claims that CKA explains representation geometry.
- Claims that CKA and C0, D, or R are equivalent measures.
- Cross-model pooled conclusions.
- Generalization beyond the evaluated models, layers, pair sets, and EVAL
  split.
- Claims about behavioral control, reasoning improvement, or model cognition.

## 5. Manuscript recommendation

**Recommendation: supplement.**

Place the complete CKA matrices, pair counts, and model-wise Spearman table in
the supplement as a secondary analysis. If referenced in the main text, use at
most a brief statement that CKA was compared with fixed-readout compatibility
metrics on the EVAL split, with full results deferred to the supplement.

The main contribution should remain the fixed-readout compatibility analysis;
the CKA comparison should not be used to enlarge its claims.

## 6. Reviewer-defense interpretation

The defensible reviewer-facing description is:

> We report a model-wise, off-diagonal EVAL comparison between centered linear
> CKA and the existing fixed-readout metrics. The comparison uses Spearman
> associations separately for each model and does not pool models or infer
> causality. It is included as a secondary relationship analysis rather than
> as a mechanistic explanation.

This framing is supported by the recorded split, pair scope, metric list,
model list, and absence of pooled statistics in the comparison manifest. The
comparison manifest also records that model inference, hidden-state
extraction, canonical-result modification, and scientific interpretation were
not performed during artifact generation.
