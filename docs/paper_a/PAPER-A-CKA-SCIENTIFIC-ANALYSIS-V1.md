# PAPER-A CKA Scientific Analysis V1

## Scope and provenance

This memo reads only the completed comparison summary and comparison manifest
under `experiments/paper_a_cka/comparison/`. It does not recompute CKA, run
inference, extract hidden states, or alter any result.

The comparison uses:

- split: `EVAL`;
- directed off-diagonal layer pairs only;
- arithmetic mean over ten frozen EVAL conditions;
- separate Spearman statistics for each model;
- no cross-model pooling.

The comparison manifest records the input CKA, Paper A canonical, and source
result hashes. Its status is `VALIDATED_COMPARISON_ARTIFACTS` and it records
that model inference, hidden-state extraction, canonical-result modification,
and scientific interpretation were not performed during artifact generation.

## 1. Observed statistics

| Model | Pair count | CKA vs C0 | CKA vs D | CKA vs R |
|---|---:|---:|---:|---:|
| Qwen | 756 | 0.8371975188315528 | -0.8373251441408364 | -0.6738306903755658 |
| OLMo | 240 | 0.7588530438644798 | -0.8082050892065848 | -0.3729283753818091 |
| Llama | 240 | 0.770616497595761 | -0.7633765918249892 | -0.5188534646866533 |

These are the actual recorded Spearman coefficients. The comparison outputs do
not provide confidence intervals, standard errors, p-values, bootstrap results,
or multiplicity adjustments. Accordingly, this memo makes no inferential
uncertainty claim beyond reporting the observed coefficients.

## 2. Metric definitions used in this comparison

The comparison quantities are defined at the analysis level as follows:

- **CKA vs C0:** Spearman rank association between the CKA value and C0 for
  the same directed layer pair.
- **CKA vs D:** Spearman rank association between the CKA value and D for the
  same directed layer pair.
- **CKA vs R:** Spearman rank association between the CKA value and R for the
  same directed layer pair.

Each coefficient is model-specific and uses only that model's off-diagonal
pair set. The two input JSON files do not restate expanded semantic prose for
the canonical C0, D, and R quantities; this memo therefore does not assign
additional meanings to those labels.

## 3. Model-wise analysis

### Qwen

Qwen contributes 756 directed off-diagonal pairs. The recorded CKA vs C0
coefficient is positive (`0.8371975188315528`). The coefficients for CKA vs D
and CKA vs R are negative (`-0.8373251441408364` and
`-0.6738306903755658`).

### OLMo

OLMo contributes 240 directed off-diagonal pairs. The recorded CKA vs C0
coefficient is positive (`0.7588530438644798`). The coefficients for CKA vs D
and CKA vs R are negative (`-0.8082050892065848` and
`-0.3729283753818091`).

### Llama

Llama contributes 240 directed off-diagonal pairs. The recorded CKA vs C0
coefficient is positive (`0.770616497595761`). The coefficients for CKA vs D
and CKA vs R are negative (`-0.7633765918249892` and
`-0.5188534646866533`).

## 4. Cross-model comparison without pooling

The sign pattern is the same in the three separate model analyses:

- CKA vs C0 is positive for Qwen, OLMo, and Llama;
- CKA vs D is negative for all three models;
- CKA vs R is negative for all three models.

The magnitudes are model-dependent. Qwen has the largest recorded CKA vs C0
coefficient and the largest-magnitude CKA vs R coefficient. OLMo has the
largest-magnitude CKA vs D coefficient. These are comparisons of separate
model-wise coefficients, not a pooled estimate or a claim of statistical
equivalence across models.

## 5. Evidence classification

### SUPPORTED

- In the recorded EVAL comparison, CKA and C0 have positive model-wise rank
  associations for each of the three models.
- CKA and D have negative recorded model-wise rank associations for each model.
- CKA and R have negative recorded model-wise rank associations for each model.
- The strength of the observed relationships varies by model.
- The results support a descriptive comparison of CKA with the existing
  functional quantities under the specified pair scope and condition pooling.

### NOT_SUPPORTED

The outputs do not support:

- causal claims;
- mechanism claims;
- claims about information flow;
- claims that CKA explains representation geometry;
- claims that CKA is equivalent to C0, D, or R;
- a pooled cross-model relationship;
- generalization beyond these models, layer pairs, and the EVAL split;
- claims about behavioral control, reasoning improvement, or model cognition.

The signs of the coefficients should be described as observed associations or
model-dependent relationships, not as explanations.

## 6. Manuscript recommendation

**Recommendation: supplement.**

The complete coefficient table and pair-count accounting belong in the
supplement as a secondary analysis. The main text may mention that a separate
CKA comparison was performed, but should avoid making it a central result
because the available summary contains no uncertainty estimates and no pooled
analysis.

This placement preserves the primary Paper A focus on fixed-readout
compatibility while making the secondary relationship analysis available for
reviewer inspection.

## 7. Validation boundary

The comparison summary and manifest were treated as read-only inputs. No new
metric, model run, hidden-state extraction, CKA computation, or scientific
result was created. Canonical Paper A files and the existing comparison
outputs were not modified.
