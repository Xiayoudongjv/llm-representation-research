# PAPER-A CKA Empirical Reading V1

## Scope

This memo reports observations from the completed PA-CKA comparison summary
and manifest only. The comparison uses the EVAL split, directed off-diagonal
layer pairs, arithmetic mean over ten frozen EVAL conditions, and separate
Spearman statistics by model. No inference, hidden-state extraction, or new
CKA computation was performed for this reading step.

## 1. Raw observations

| Model | Pair count | Spearman(CKA,C0) | Spearman(CKA,D) | Spearman(CKA,R) |
|---|---:|---:|---:|---:|
| Qwen | 756 | 0.8371975188315528 | -0.8373251441408364 | -0.6738306903755658 |
| OLMo | 240 | 0.7588530438644798 | -0.8082050892065848 | -0.3729283753818091 |
| Llama | 240 | 0.770616497595761 | -0.7633765918249892 | -0.5188534646866533 |

The primary recorded comparison is CKA vs C0. CKA vs D and CKA vs R are
recorded as secondary comparisons.

## 2. Cross-model analysis

### Consistency

The sign pattern is consistent across all three models:

- Spearman(CKA,C0) is positive for Qwen, OLMo, and Llama.
- Spearman(CKA,D) is negative for Qwen, OLMo, and Llama.
- Spearman(CKA,R) is negative for Qwen, OLMo, and Llama.

Thus, the direction of each observed rank relationship replicates across the
three separate model-wise analyses.

### Differences

The magnitudes are not identical:

- Qwen has the largest CKA–C0 coefficient (`0.8371975188315528`).
- OLMo has the largest-magnitude CKA–D coefficient
  (`-0.8082050892065848`).
- Qwen has the largest-magnitude CKA–R coefficient
  (`-0.6738306903755658`).

These are comparisons of separate coefficients. The manifest records no pooled
cross-model statistic, and none is inferred here.

## 3. Paper A relevance

### SUPPORTED

- The completed EVAL comparison directly supports reporting positive,
  model-wise rank relationships between CKA and C0 for Qwen, OLMo, and Llama.
- It directly supports reporting negative, model-wise rank relationships
  between CKA and D and between CKA and R for the same models.
- It supports describing the sign pattern as consistent across the three
  model-specific analyses, while retaining model-dependent magnitudes.
- It supports a descriptive comparison between CKA and the existing Paper A
  functional quantities for the evaluated directed layer pairs.

### NOT_SUPPORTED

The data do not justify:

- causal claims;
- mechanism claims;
- information-flow claims;
- claims that CKA explains representation geometry;
- claims that CKA is equivalent to C0, D, or R;
- pooled cross-model conclusions;
- conclusions beyond the evaluated models, layers, pair sets, and EVAL split;
- behavioral or reasoning claims.

The observations should be described only as associations, relationships,
consistency, or model-dependent patterns.

## 4. Manuscript impact

### Classification: STRENGTHENS — SECONDARY SUPPORT

The result strengthens Paper A in a limited secondary sense: the same sign
pattern is observed in three separate model-wise comparisons, providing a
descriptive relationship between CKA and the existing fixed-readout metrics.

This does not strengthen the causal, mechanistic, information-flow, or
representation-geometry interpretation of Paper A, because those claims are
not tested by these outputs.

Recommended manuscript treatment is a secondary or supplementary result. The
main text should not treat this comparison as a new central contribution or as
an explanation of the fixed-readout findings.

## 5. Provenance and validation boundary

The input manifest records:

- split: `EVAL`;
- models: Qwen, OLMo, Llama;
- pair scope: off-diagonal directed layer pairs;
- metrics: `CKA_vs_C0`, `CKA_vs_D`, `CKA_vs_R`;
- no model inference or hidden-state extraction during comparison generation;
- no canonical-result modification;
- deterministic comparison artifact status.

The source summary and comparison manifest were treated as read-only. No new
scientific computation was performed, and this memo is the only new file
created for the empirical-reading step.
