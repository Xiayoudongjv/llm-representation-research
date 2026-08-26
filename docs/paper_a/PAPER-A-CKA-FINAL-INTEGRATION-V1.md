# PAPER-A CKA Final Integration V1

## 1. Role in Paper A

CKA is a secondary supporting analysis. It is not a core contribution of Paper
A and does not replace the fixed-readout compatibility analysis.

Its role is to provide a separate representational-similarity comparison with
the existing functional compatibility quantities. The results are used only
to describe associations and relationships under the completed evaluation
protocol.

## 2. Experimental setup

- Split: `EVAL`
- Samples: 640 unique records
- Models: Qwen, OLMo, and Llama
- Representation carrier: decoder block output, post-block residual stream,
  before final normalization
- Similarity method: centered linear CKA
- Pair scope: directed off-diagonal layer pairs
- Functional comparisons: C0, D, and R
- Statistics: model-wise Spearman associations; no cross-model pooling

## 3. Results

| Model | CKA-C0 | CKA-D | CKA-R |
|---|---:|---:|---:|
| Qwen | 0.8372 | -0.8373 | -0.6738 |
| OLMo | 0.7589 | -0.8082 | -0.3729 |
| Llama | 0.7706 | -0.7634 | -0.5189 |

## 4. Observations

The CKA-C0 comparison is positive for all three models. The CKA-D and CKA-R
comparisons are negative for all three models. This provides a consistent
model-wise association pattern across Qwen, OLMo, and Llama, while the
magnitudes differ by model.

The result supports a descriptive relationship between representational
similarity and the existing fixed-readout metrics on the EVAL split. It is a
comparison of completed measurements, not a replacement for those metrics.

## 5. Boundary

The CKA analysis does not support:

- causality;
- mechanism claims;
- information-flow claims;
- explanations of representation geometry;
- equivalence between CKA and C0, D, or R;
- generalization beyond the evaluated models, layers, and EVAL split.

The manuscript should use only the terms association, relationship, and
comparison when describing this analysis.

## 6. Manuscript recommendation

CKA strengthens Paper A as secondary supporting evidence because the observed
association pattern is directionally consistent across three models. It adds a
distinct comparison between representational similarity and the existing
fixed-readout measurements without changing the primary experiment.

It should remain a secondary or supplementary result rather than a new
contribution. This placement preserves Paper A's focus on fixed-readout
compatibility and avoids expanding the manuscript into causal, mechanistic, or
information-flow claims.
