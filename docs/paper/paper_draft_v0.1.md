# When Is a Representation Transformation Valid?

## A Probe of Task-Associated Geometry and Relational Preservation in LLM Hidden States

## Abstract

This draft reports an exploratory representation-level study of hidden states from `Qwen/Qwen3-1.7B`.
It examines task-associated geometry, calibrated centroid steering, a relational invariant proxy, and a transition-validity frontier.
Calibrated steering moved selected representations toward target-group centroid regions while RSM correlations remained high at the selected operating point.
These findings do not demonstrate generation-time control, reasoning improvement, semantic latent spaces, or true logical invariance.

## 1. Introduction

Representation transformations matter because proposed model interventions often assume internal states can move between useful regions.
Moving a representation is not sufficient if relations among source examples are distorted.
This project asks: **When is a representation transformation valid?**
We study this question with controlled prompts, hidden-state geometry, calibrated centroid steering, and a proxy for relational preservation.

## 2. Research Questions

- **RQ1.** Do task-associated prompts exhibit measurable geometry in hidden representation space?
- **RQ2.** Does task-associated geometry vary across Transformer depth?
- **RQ3.** Does the geometry survive lexical/paraphrase control?
- **RQ4.** Can calibrated centroid steering induce representation-level transitions between task groups?
- **RQ5.** Can such transitions preserve internal relational structure?
- **RQ6.** Can we identify a transition-validity operating point?

## 3. Method

### 3.1 Model and Representation Extraction

All experiments use `Qwen/Qwen3-1.7B`.
We extract layer-wise hidden states and use the last-token hidden state as each prompt representation.
No completed experiment applies generation-time intervention or evaluates generated answers.

### 3.2 Prompt Groups

Prompt groups are logic, causality, analogy, and definition.
EXP-003 uses a controlled English set of 24 prompts: six per group, with three `original_style` and three `paraphrase` items.
The prompts are manually designed controls rather than a benchmark dataset.

### 3.3 Representation Geometry Metrics

We use cosine similarity, PCA, within/between similarity, separation score, and cosine-distance silhouette score.
PCA is a visualization and compact variance summary, not proof of cluster structure.

### 3.4 Calibrated Centroid Steering

For source centroid \(c_{source}\), target centroid \(c_{target}\), and source representation \(h\), calibrated steering applies

\[
h' = h + \beta (c_{target} - c_{source}).
\]

This is representation-level centroid steering only, not generation-time activation steering.

### 3.5 Relational Invariant Proxy

Let RSM be the representation similarity matrix for a source group.
We compare upper-triangle values before and after steering and define

\[
\mathrm{IVS} = 1 - \mathrm{Pearson}(\mathrm{RSM}_{before}, \mathrm{RSM}_{after}).
\]

This is only a proxy for relational invariance; it does not establish logical or semantic invariance.

### 3.6 Transition Validity Frontier

The frontier combines transition success, invariant preservation, and perturbation magnitude.
EXP-007 recommends the lowest-IVS beta among settings with full target assignment.

## 4. Experiments and Results

### 4.1 EXP-001 Final-layer Geometry

EXP-001 used 12 prompts at final layer 28.
Its first two PCA components explained about 0.54 of variance.
Analogy and causality appeared relatively compact, while definition prompts were more dispersed.
This is cautious evidence of task-associated patterns in this prompt set, not proof of semantic categories.

### 4.2 EXP-002 Layer-wise Geometry

EXP-002 measured layers 0, 4, 8, 12, 16, 20, 24, and 28.
Layer 16 had the largest separation score, about 0.137.
Layer 4 had the largest silhouette score, about 0.478, in the earlier 12-prompt setting.
Geometry was not monotonic with depth, and layer 0 had near-zero cross-prompt variance in this extraction setup.

### 4.3 EXP-003 Paraphrase Control

EXP-003 used 24 prompts, four groups, and `original_style`/`paraphrase` variants.
Token counts were better balanced, and the final-layer token-count/norm correlation was near zero, about -0.005.
The strongest controlled separation and weak but positive paraphrase retention occurred around layer 16.
This reduces but does not eliminate lexical, template, and manual-design confounds.

### 4.4 EXP-004 and EXP-004B Static Steering

Normalized logic-to-causality steering was weak.
Calibrated steering using the raw centroid difference was stronger: beta 0.5 first crossed target/source similarity, and beta 0.75 reached target assignment rate 1.0 for the six logic prompts.
The required perturbation magnitude was nontrivial.

### 4.5 EXP-005 Multi-pair Steering

EXP-005 tested all 12 ordered group transitions.
All reached target assignment rate 1.0 by beta 0.75.
Causality-definition had a relatively small delta norm, about 79.10, while causality-analogy had a larger norm, about 118.23.
Final assignment showed no asymmetry, although threshold onset did for some pairs.

### 4.6 EXP-006 Relational Invariant Score

IVS increased with beta and RSM Pearson decreased with beta.
At beta 0.75, mean target assignment was 1.0 with mean IVS about 0.00285 and mean RSM Pearson about 0.99715.
The RSM proxy is useful for describing a trade-off but may be insensitive because each source group has six prompts.

### 4.7 EXP-007 Transition Validity Frontier

EXP-007 analyzed EXP-006 CSV results without rerunning the model.
All 12 ordered transitions recommended beta 0.75.
At that beta, mean assignment was 1.0, mean IVS was about 0.00285, mean RSM Pearson was about 0.99715, and mean relative perturbation was about 0.345.
This is a stable exploratory operating point, not a universal optimum or behavioral intervention setting.

## 5. Discussion

The selected hidden states show task-associated geometry in the controlled prompt set.
Calibrated centroid steering can move source representations toward target centroid regions.
Movement alone is insufficient: higher beta values retain saturated assignment while increasing IVS and perturbation magnitude.
The RSM proxy provides a first validity criterion and motivates later task-conditioned transformations with explicit preservation terms.

## 6. Limitations

- One model: `Qwen/Qwen3-1.7B`.
- Small, English-only, manually controlled prompt sets.
- Last-token representations only.
- No generation-time intervention, answer correctness, or reasoning evaluation.
- RSM invariant is only a proxy for relational preservation.
- Nearest-centroid assignment is not a reasoning transformation.
- Large beta may create out-of-distribution representations.

## 7. Future Work

Future work should test generation-time intervention, answer-level reasoning evaluation, larger prompt sets, multiple models, multiple layers, invariant-constrained steering, learned task-conditioned transformations, local cover or transition maps, and stronger relational invariants.

## 8. Conclusion

This project provides an exploratory framework for probing representation transformation validity using task-associated geometry, calibrated centroid steering, and relational invariant proxies.
It does not establish generation-time control, reasoning improvement, semantic latent spaces, or true logical invariance.
