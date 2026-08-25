# Paper A Directionality Exploratory Closure

Status: `POST_HOC_EXPLORATORY_SECONDARY_ANALYSIS`

This document archives the completed directionality analysis as an exploratory
secondary analysis. It does not upgrade the analysis to confirmatory evidence,
and it closes this scientific line without further matrix mining.

## Canonical inputs and orientation

The analysis is bound to the canonical result files below. Their SHA-256
identities are recorded in
`experiments/paper_a/directionality_exploratory_manifest.json`.

- EXP-026: `experiments/exp026/results/exp026_results.json`
- EXP-027: `experiments/exp027/results/exp027_results.json`
- EXP-027 canonical manifest:
  `docs/experiments/canonical/EXP-027-CANONICAL-RESULT-MANIFEST.json`

The matrix convention is source rows and target columns. For each unordered
off-diagonal layer pair, after averaging the ten frozen evaluation conditions:

`A_C(i,j) = C0(i,j) - C0(j,i)`

`A_D(i,j) = D(i,j) - D(j,i)`

`A_R(i,j) = R(i,j) - R(j,i)`

The archived validator recomputes these quantities read-only from the
canonical matrices.

## Descriptive results

| Model | mean \|A_C\| | signed shallow/deep bias | C0_SymErr | mean \|A_D\| | mean \|A_R\| |
|---|---:|---:|---:|---:|---:|
| Qwen | 0.129067 | -0.066567 | 0.236573 | 0.129191 | 0.133796 |
| OLMo | 0.137292 | 0.123646 | 0.313139 | 0.155755 | 0.128359 |
| Llama | 0.167031 | 0.072448 | 0.307183 | 0.171198 | 0.160234 |

The exploratory A_C/A_R Spearman associations are Qwen `-0.9512`, OLMo
`-0.4576`, and Llama `-0.8878`.

Using absolute normalized layer distance thresholds of 0.25 and 0.50, the
mean absolute A_C remains nonzero in every model. This is descriptive distance
robustness, not an IID significance claim:

- `DIRECTIONALITY_SURVIVES_DISTANCE_025 = true`
- `DIRECTIONALITY_SURVIVES_DISTANCE_050 = true`

The preferred shallow/deep orientation is not uniform across models. The
directionality result is therefore classified as materially present
descriptively across all three models, with the conceptual statement
`SUPPORTED_EXPLORATORILY`.

## Statistical closure and claim boundary

`PA_DIRECTIONALITY_INFERENCE_CLASS = POST_HOC_EXPLORATORY_DESCRIPTIVE`.

No new bootstrap inference, p-values, significance labels, confidence
intervals, or permutation tests were generated. Layer pairs share endpoints,
so they are dependent; no unique directionality resampling unit had been
frozen before this post-hoc analysis. The existing descriptive and
distance-stratified summaries are sufficient for closure.

Allowed interpretation:

- Operational fixed-readout compatibility is directed as a measurement.
- Substantial forward/reverse asymmetry is descriptively present in all three tested models.
- The preferred shallow/deep orientation is not uniform across the three tested models.
- The asymmetry persists after excluding adjacent layers and under larger normalized depth thresholds.

The analysis does not establish universal directionality, asymmetric
representation geometry, asymmetric information flow, compensation, or an
architectural cause.

## Paper role and next action

`PAPER_A_DIRECTIONALITY_ROLE = EXPLORATORY_SECONDARY_MAIN_TEXT`.

The main text may present the A_C definition, mean absolute A_C, model-specific
orientation, and distance robustness. A_D, A_R, their correlation, SymErr, and
condition-level detail belong in supplementary material. Recommended figures
are pooled C0 heatmaps, diverging A_C heatmaps, model-stratified absolute A_C
descriptions, and descriptive shallow-to-deep versus deep-to-shallow summaries.

`PA_DIRECTIONALITY_SCIENTIFIC_LINE = CLOSED_NO_FURTHER_MATRIX_MINING`.

`PAPER_A_NEXT_TASK = PAPER_A_CKA_ASSET_FEASIBILITY_AUDIT`.

No model inference was run, and the canonical EXP-026 and EXP-027 results were
not modified.
