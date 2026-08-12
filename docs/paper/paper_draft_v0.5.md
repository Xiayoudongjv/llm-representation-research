# Paper Draft v0.5: Cross-Model Synthesis

## Abstract

We study controlled task-associated hidden-state geometry, calibrated
centroid-based representation transitions, and a relational-preservation proxy
in Qwen/Qwen3-1.7B and google/gemma-3-1b-it. Across these two small LLMs, the
controlled geometry and calibrated representation-transition phenomena were
observed at the representation level. In both models, stronger steering moved
source representations toward target centroids while increasing perturbation
and RSM-based relational disruption. The depth profile and useful steering
strength differed by model: Qwen's strongest controlled signal was around layer
16, whereas Gemma's strongest separation and paraphrase-retention scores were
at its final hidden-state index. Qwen's beta-0.75 frontier did not fully carry
over to Gemma. A frozen Qwen behavioral baseline further shows that current
representation metrics do not reliably explain answer-level difficulty. These
findings are a cross-model replication across two small LLMs, not evidence of
generation-time improvement or a general account of reasoning.

## 1. Motivation

Representation-space analyses can detect structured differences among prompt
groups, but target-centroid movement alone is insufficient to evaluate a
transformation. We therefore examine transition success jointly with a proxy
for preservation of within-source relational structure. The central empirical
question is whether these representation-level observations remain visible in a
second model family under a fixed controlled prompt set.

## 2. Experimental Setting

The controlled dataset contains 24 English prompts: six prompts in each of
logic, causality, analogy, and definition, with original-style and paraphrase
variants. Analyses use last-token hidden-state representations and raw
plain-text prompts. Qwen and Gemma were evaluated separately with their own
observed layer profiles; no nominal layer number is treated as an equivalent
cross-model location.

For steering, a source-group representation is changed in memory by
`h' = h + beta * (centroid_target - centroid_source)`. We measure target
similarity, nearest-centroid assignment, relative perturbation, and the
correlation between source-group representational similarity matrices (RSMs)
before and after steering. RSM correlation is a relational-preservation proxy,
not a logical invariant.

## 3. Controlled Geometry Across Models

Qwen EXP-003 showed its strongest controlled signal around layer 16:
separation was 0.073015, silhouette was 0.182165, and paraphrase retention was
0.036424. Gemma EXP-013 showed positive separation and silhouette at multiple
nonembedding layers. Its strongest separation was 0.093294 at layer 26, its
strongest silhouette was 0.139718 at layer 16, and its strongest paraphrase
retention was 0.071401 at layer 26.

Thus, task-associated geometry, paraphrase-controlled signal, and a
non-monotonic layer profile were observed in both models. The depth profile was
model-dependent: Qwen showed its strongest controlled signal in a mid-depth
region, whereas Gemma's strongest separation and paraphrase-retention scores
occurred at the final hidden-state index. The data do not support treating a
mid- or mid-deep peak as model-invariant.

## 4. Calibrated Representation Transitions

Qwen EXP-005 and EXP-006 found that all 12 ordered group transitions reached
full nearest-centroid target assignment by beta 0.75. EXP-007's exploratory
frontier analysis selected beta 0.75 for all pairs, with mean IVS 0.002850 and
mean RSM Pearson 0.997150 at that point. EXP-008 found this Qwen selection
robust across most of its penalty settings, while noting that all selection
rules were exploratory.

Gemma EXP-014 used the fixed layer-26 choice from EXP-013 and the same
predeclared beta schedule. All 12 ordered transitions reached assignment of at
least 0.5 and eventually reached full assignment. At beta 0.75, six of twelve
transitions had first reached full assignment; mean assignment was 0.875 and
mean IVS was 0.017970. The predeclared Gemma exploratory rule selected beta
1.0, where mean assignment was 0.972 and mean IVS was 0.028977.

The qualitative transition-preservation tradeoff replicated across models:
larger positive beta increased target-directed movement and relative
perturbation, while mean IVS increased and mean RSM Pearson decreased. The
operating point was model-dependent. In particular, the Qwen beta-0.75 frontier
was only partially reproduced in Gemma.

## 5. Transition Validity Framing

The strongest current framework is empirical: a representation transformation
should not be judged solely by target transition success, but jointly by
transition success and relational preservation. The two-model evidence supports
this as an evaluation framework because both models show the same qualitative
tension between increasing transition strength and increasing RSM disruption.
It is not a mathematical necessity, a definition of true logical validity, or
a claim that RSM captures every meaningful invariant.

## 6. Behavioral Evidence and Its Limit

The frozen Qwen EXP-011D answer-level baseline scored 60/80 (0.750): causality
0.950, definition 0.850, logic 0.750, and analogy 0.450. EXP-012 replaced an
earlier smaller benchmark in an n=4 group-level descriptive analysis. Several
representation-behavior correlations changed substantially, including sign
changes for incoming final IVS and incoming final RSM Pearson. Accordingly,
current representation metrics do not provide a reliable geometry-to-behavior
inference.

Gemma does not yet have a behavioral benchmark in this project. The paper does
not compare Qwen and Gemma behavior.

## 7. Contributions

1. A controlled analysis of task-associated hidden-state geometry.
2. A calibrated centroid-steering baseline for representation-level
   transitions.
3. A relational-preservation proxy based on RSM structure.
4. An empirical transition-preservation validity framing.
5. Cross-model replication across Qwen3-1.7B and Gemma-3-1B-IT showing that
   geometry and transition phenomena replicate qualitatively while layer depth
   and steering strength remain model-dependent.
6. A carefully audited behavioral baseline showing that current representation
   metrics do not yet explain answer-level difficulty.

## 8. Limitations

- Only two small LLMs were studied.
- The prompt set contains 24 hand-designed controlled prompts and four groups.
- Layer selection is model-specific and analyses use last-token states only.
- Steering is centroid-based and evaluated only in representation space.
- No generation-time intervention was performed.
- The behavioral baseline currently exists only for Qwen.
- RSM preservation is a limited proxy rather than an exhaustive account of
  relational structure.

## 9. Conclusion

Across Qwen/Qwen3-1.7B and google/gemma-3-1b-it, controlled task-associated
geometry and calibrated representation transitions were observed at the
representation level. The qualitative tradeoff between transition strength and
relational preservation also appeared in both models. At the same time, the
strongest layer and the useful steering strength differed by model. The next
scientific question is whether carefully controlled generation-time
intervention has observable behavioral consequences; this remains untested.
