# PAPER-A CKA Result Audit V1

## 1. Input provenance

This audit covers only the completed PA-CKA functional-comparison outputs:

- Split: `EVAL`
- Comparison manifest: `PA-CKA-FUNCTIONAL-COMPARISON-V1`
- Summary manifest: `PA-CKA-FUNCTIONAL-COMPARISON-SUMMARY-V1`
- Pair scope: directed off-diagonal layer pairs only
- Condition handling: arithmetic mean over the ten frozen EVAL conditions
- Statistic: Spearman correlation, computed separately by model

Recorded input hashes:

- CKA asset manifest: `bf4ee044b26706594ff262567997c1acee534b608ff5d002c3f98dcb77403ba2`
- CKA result manifest: `c2469ca526ae5701f334c776d6338c1e1daa90fffc4d0474866b2a878d0b628a`
- Qwen CKA matrix: `6920b642f5085b9411befb8eaf55ad98537892dfb2050edb0490ef074e41b3c2`
- OLMo CKA matrix: `effb9b8bad61594a2423ecb5f0f6f424d5e44ec21adea3c59cca5989a88845d5`
- Llama CKA matrix: `aa06ed6f45886dfb1927c3cc361707897dc5b93d4d0a2bc7ef528c593cac2e9d`
- Figure 03 canonical matrix data: `faac6f63379bbee4c4b116856683ff27cdee032c54b7a40df2416f65c6c6e599`

The comparison manifest records the Paper A canonical scientific-results,
claim-register, and paper-asset-manifest hashes as unchanged inputs.

## 2. Statistical quantities computed

The analysis computes, per model and using off-diagonal directed layer pairs:

- Spearman association between CKA and C0 (primary comparison);
- Spearman association between CKA and D (secondary comparison);
- Spearman association between CKA and R (secondary comparison).

No cross-model pooling, regression, prediction model, diagonal pair, or new
directionality metric is recorded.

## 3. Model-wise results summary

| Model | Directed off-diagonal pairs | CKA vs C0 | CKA vs D | CKA vs R |
|---|---:|---:|---:|---:|
| Qwen | 756 | 0.8371975188 | -0.8373251441 | -0.6738306904 |
| OLMo | 240 | 0.7588530439 | -0.8082050892 | -0.3729283754 |
| Llama | 240 | 0.7706164976 | -0.7633765918 | -0.5188534647 |

Audit checks:

- Models included: Qwen, OLMo, Llama — **PASS**
- Pair counts: 756, 240, 240 — **PASS**
- CKA vs C0, CKA vs D, and CKA vs R present — **PASS**
- Cross-model pooled statistics — **NOT PRESENT**
- Diagonal pairs — **NOT INCLUDED**

## 4. What the analysis supports

Within the frozen EVAL split, this secondary analysis supports reporting
model-specific associations between centered linear CKA and the registered
fixed-readout compatibility quantities C0, D, and R across directed
off-diagonal layer pairs.

The results support a descriptive comparison of representational similarity
with those existing functional metrics under the stated condition pooling and
model-specific pair sets.

## 5. What the analysis does not support

This audit does not support claims of:

- causality;
- mechanism discovery;
- information flow;
- representation-geometry explanation;
- equivalence between CKA and functional compatibility;
- generalization beyond the evaluated models, layers, and EVAL split;
- behavioral control or reasoning improvement.

The associations should therefore be described as model-wise relationships or
comparisons, not as explanations of why functional compatibility varies.

No model inference, hidden-state extraction, canonical-result modification, or
scientific interpretation was performed during this audit.
