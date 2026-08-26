# PAPER-A CKA Experiment Protocol V1

## Status and scope

This document records the completed design and execution protocol for the
Paper A secondary CKA analysis. It is an engineering and reproducibility
record. It does not alter Paper A canonical results, claims, or claim
registers.

- Protocol ID: `PAPER-A-CKA-V1`
- Corrected authority: `PAPER-A-CKA-RUN-AUTHORITY-V1.1`
- Split: `EVAL` only
- Scientific role: secondary representational-comparison analysis

## 1. Motivation

Paper A measures fixed-readout compatibility across Transformer depth. The CKA
analysis provides a separate representation-similarity description that can be
compared with the existing fixed-readout quantities. It is not intended to
replace the fixed-readout evaluation or to explain its mechanism.

## 2. Hypothesis

The primary descriptive hypothesis is that layer-pair CKA will show a positive
rank relationship with the existing C0 compatibility values within each model.
The secondary comparisons examine the rank relationships of CKA with D and R.

This is an association hypothesis. It does not posit that CKA causes
compatibility, degradation, or recovery, and it does not posit a mechanism or
information-flow process.

## 3. Dataset and sample order

- Dataset: `experiments/exp024/data/exp024_condition_panel_frozen.json`
- Dataset SHA-256:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Partition: `EVAL`
- Sample count: 640 unique records
- Sample ID field: `record_id`
- Text field: `text`
- Ordering: dataset-file order filtered to EVAL
- Sample-order hash algorithm: SHA-256 of the UTF-8 bytes of
  `\n`.join(ordered record IDs)
- Sample-order hash:
  `6ff5adb902c7bc691b078c73b3b267005fe37f74b6fd675ba1225d4f8971baea`

No sampling or selection was performed after the corrected 640-record
inventory. The same sample order was required for every layer within every
model.

## 4. Models and layer coverage

| Analysis name | Frozen model identity | Layers | Hidden size | Representation storage |
|---|---|---:|---:|---|
| Qwen | `Qwen/Qwen3-1.7B`, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | 28 | 2048 | float32 assets |
| OLMo | `allenai/OLMo-2-0425-1B-Instruct`, revision `48d788eca847d4d7548f375ad03d3c9312f6139e` | 16 | 2048 | float32 assets |
| Llama | `Meta-Llama-3.2-1B-Instruct`, local converted snapshot authority in EXP-027 | 16 | 2048 | float32 assets |

The CKA matrices therefore have shapes 28 x 28, 16 x 16, and 16 x 16,
respectively. CKA was computed within each model only; no cross-model CKA
matrix was produced.

## 5. Representation extraction

The representation carrier was fixed as:

- module path: `model.model.layers[layer]`;
- carrier: decoder block output, post-block residual stream;
- position: before the next Transformer block and before the model's final
  normalization;
- hook identity: `FORWARD_HOOK_DECODER_BLOCK_OUTPUT`.

The extraction did not use `outputs.hidden_states` as its source. The token
position was selected using `attention_mask_sum_minus_one`. Tokenization used
special tokens, no padding, no truncation, and tensor return mode as specified
by the frozen protocol.

For each model and layer, the extracted asset recorded model identity, layer
index, carrier, dtype, sample count, representation shape, and sample-order
hash. Extraction involved no training and no probe fitting.

## 6. CKA method

The analysis used centered linear CKA. For two aligned layer matrices (X) and
\(Y\), rows correspond to the same 640 EVAL samples. Each matrix was centered
over samples before the linear Gram comparison. The normalized centered linear
alignment was computed as:

\[
\operatorname{CKA}(X,Y) =
\frac{\lVert X_c^{\mathsf T}Y_c\rVert_F^2}
{\sqrt{\lVert X_c^{\mathsf T}X_c\rVert_F^2
\lVert Y_c^{\mathsf T}Y_c\rVert_F^2}}.
\]

Implementation constraints:

- float64 accumulation;
- deterministic computation;
- no PCA;
- no random projection;
- no nonlinear kernel;
- no SVCCA, RSA, learned alignment, training, or probe fitting;
- finite-value, symmetry, diagonal, shape, layer-order, and sample-order
  validation.

## 7. Comparison metrics

The CKA matrices were compared with the existing Paper A canonical EVAL
matrices for:

- `C0`;
- `D`;
- `R`.

The canonical Figure 03 data retained ten frozen condition slices. For the
one-row-per-layer-pair comparison table, each metric was represented by its
arithmetic mean over those ten slices. This was condition pooling of the
existing quantities, not introduction of a new metric.

Only off-diagonal directed layer pairs were included:

- Qwen: 28 x 27 = 756 pairs;
- OLMo: 16 x 15 = 240 pairs;
- Llama: 16 x 15 = 240 pairs.

The table records model, source layer, target layer, CKA, C0, D, R, an
off-diagonal indicator, and forward/backward pair direction. No new
directionality metric was created.

## 8. Statistics

Statistics were computed separately for each model and pair set:

- primary: Spearman association, CKA vs C0;
- secondary: Spearman association, CKA vs D;
- secondary: Spearman association, CKA vs R.

No cross-model pooling, regression, prediction model, or additional statistical
metric was used. The comparison does not provide a causal estimate or an
uncertainty interval by itself.

## 9. Interpretation boundary

The analysis may support statements about observed model-wise associations,
relationships, and comparisons between CKA and the existing fixed-readout
metrics on the EVAL layer-pair sets.

It may not support claims about:

- causality;
- mechanism discovery;
- information flow;
- representation-geometry explanation;
- equivalence of CKA with C0, D, or R;
- generalization beyond the evaluated models, layers, and EVAL split;
- behavioral control, reasoning improvement, or cognitive structure.

The CKA analysis is therefore a secondary descriptive analysis, not a causal,
mechanistic, or behavioral test.

## 10. Reproducibility information

Primary protocol and authority files:

- `experiments/paper_a_cka/paper_a_cka_protocol.py`
- `docs/paper_a/PAPER-A-CKA-RUN-AUTHORITY-V1.1.md`
- `experiments/paper_a_cka/paper_a_cka_run_manifest.json`

Validated asset and result manifests:

- Asset manifest SHA-256:
  `bf4ee044b26706594ff262567997c1acee534b608ff5d002c3f98dcb77403ba2`
- CKA result manifest SHA-256:
  `c2469ca526ae5701f334c776d6338c1e1daa90fffc4d0474866b2a878d0b628a`
- Qwen matrix SHA-256:
  `6920b642f5085b9411befb8eaf55ad98537892dfb2050edb0490ef074e41b3c2`
- OLMo matrix SHA-256:
  `effb9b8bad61594a2423ecb5f0f6f424d5e44ec21adea3c59cca5989a88845d5`
- Llama matrix SHA-256:
  `aa06ed6f45886dfb1927c3cc361707897dc5b93d4d0a2bc7ef528c593cac2e9d`

Canonical Paper A files were protected by the following recorded hashes:

- scientific results:
  `77ffef1b4f253505e30baf50eee0039a925345b831744bf5d7f4f59b8980ed4c`
- claim register:
  `2e274b716a7d6d8a235988f88fada92cea1670b28ddfe28e2521f180a303813e`
- paper asset manifest:
  `d0e4a5caee548a200ed64387d6955631fc8c54214e650f86f2f7284a0e1ad5aa`
- Figure 03 matrix data:
  `faac6f63379bbee4c4b116856683ff27cdee032c54b7a40df2416f65c6c6e599`

The completed result manifest records all CKA matrices as valid, with finite
values, valid symmetry, and valid diagonals. The protocol and result artifacts
record that Paper A canonical files were not modified.
