# Fixed Readout Compatibility and Featurewise Recalibration Across Transformer Depth: A Controlled, Preregistered Evidence Chain with Heterogeneous and Negative Results

Status: `ASSETS_FINALIZED_099E`

This document is a derived manuscript. Canonical experiment results, frozen
protocols, scientific reviews, and research ledgers outrank it.

## Abstract

Intermediate representations in frozen language models change across Transformer
depth. Prior work already shows that layer-specific affine probes, learned
interfaces, and stitching adapters can recover performance across representation
mismatches. We therefore do not claim that layer-specific readout adaptation is
new. We study a narrower fixed-readout measurement problem: whether a fixed
semantic-class readout loses compatibility with deeper representations, whether
low-capacity FIT-only featurewise recalibration can restore readout utility,
whether that recovery is stable across held-out data conditions, and whether an
independent degradation magnitude can prospectively predict calibration
susceptibility. Across a controlled chain using a frozen Qwen3-1.7B setup with
held-out source-family separation, fixed-readout accuracy degrades at deeper
checkpoints, and featurewise recalibration produces substantial recovery in
multiple tested conditions. However, the independent preregistered replication
returns `NO_REPLICATION`: one complementary split shows substantial rescue while
the other shows no rescue. In a separate frozen 10-condition panel, all ten
conditions show positive diagnostic degradation and positive calibration benefit
descriptively, but the preregistered primary test of simple independent
degradation-magnitude prediction is `NOT_SUPPORTED`
(`rho = 0.28401877872187725`, exact one-sided permutation `p = 0.2115079365079365`).
The bounded conclusion is that fixed-readout incompatibility, calibration
utility, and susceptibility predictability are distinct empirical questions;
simple degradation magnitude is not sufficient to explain calibration
susceptibility.

## 1. Introduction

Hidden states in Transformer language models change across depth. Prior work
shows that learned layer-specific readouts and simple alignment adapters can
improve cross-representation compatibility [1, 2]. Those findings already
establish that different layers or models often require adapted interfaces. We
do not treat that observation as our contribution.

This paper studies a narrower measurement problem. A classifier or semantic
readout trained at one checkpoint is sometimes reused at another checkpoint as
though the readout remained compatible. When accuracy drops, one possible
interpretation is that task-associated information has disappeared; an
alternative is that the fixed readout has become incompatible with the deeper
representation. Distinguishing those interpretations requires a controlled
measurement design rather than a new family of layer-specific probes.

We ask four questions:

1. Does a fixed semantic readout lose compatibility when evaluated on deeper
   representations under held-out conditions?
2. Can low-capacity, FIT-only featurewise recalibration restore that readout
   without refitting a layer-specific classifier?
3. Is that calibration benefit stable across complementary data conditions and
   an independent replication split?
4. Can an independently measured degradation magnitude measured before the
   confirmatory EVAL outcome predict condition-level calibration susceptibility?

The contribution is the controlled combination of fixed readout, deliberately
low-capacity recalibration, held-out source-family separation, explicit
replication/non-replication evidence, and a preregistered independent
susceptibility test.

**Figure 1** presents the tested evidence chain and marks behavioral control,
functional binding, and coordinate transport as outside the current boundary. The negative results are part of the main scientific
argument, not appendix caveats.

Specifically, this paper makes four prior-art-aware contributions:

- **Contribution 1:** a fixed-readout compatibility measurement framework in
  which the reference classifier and scaler are frozen on FIT data and are never
  refit for deeper checkpoints.
- **Contribution 2:** empirical evidence that fixed-readout accuracy can degrade
  across depth and that FIT-only featurewise recalibration can recover readout
  performance in multiple tested conditions, with explicit condition and split
  heterogeneity.
- **Contribution 3:** a preregistered replication/non-replication sequence using
  held-out source-family controls, including the registered `NO_REPLICATION`
  outcome in EXP-023.
- **Contribution 4:** an independent DIAGNOSTIC/EVAL condition-level design whose
  registered primary test returns a valid negative result in EXP-024.

The strongest bounded claim is:

> Fixed semantic readouts can lose compatibility across Transformer depth under
> held-out evaluation. Low-capacity FIT-only featurewise recalibration can
> restore substantial readout performance in multiple tested conditions,
> although the effect is heterogeneous across datasets and splits. Moreover, a
> preregistered independent measure of fixed-readout degradation did not
> reliably predict the magnitude of calibration benefit.

This claim does not assert representation invariance, coordinate transport,
semantic preservation, universal calibration, causal reasoning control, true
task axes, general cognitive space, or functional binding.

## 2. Related Work

### 2.1 Probing and intermediate representation decoding

Probing research trains classifiers to estimate what can be decoded from
intermediate hidden states. It demonstrates that layer-specific readouts can
expose task-relevant structure, but decoding performance is not equivalent to
causal role, representation equivalence, or behavioral control [1]. Paper-A
inherits this caution and uses fixed semantic-class readouts rather than
training a new probe at each layer.

### 2.2 Tuned Lens and layer-specific decoding

Tuned Lens trains per-block affine probes from hidden states to vocabulary or
logit space and uses them to inspect latent predictions across depth [1]. It
already establishes that hidden representations often require layer-specific
affine readouts. Paper-A therefore does not claim novelty for
"different layers need different readouts." It differs by keeping a fixed
semantic-class reference readout and allowing only low-capacity FIT-only
featurewise recalibration, then testing whether that restricted interface
recovers utility under held-out conditions.

### 2.3 Model stitching and representation compatibility

Model stitching connects components of different trained models through a
simple trainable layer and interprets stitched performance as a bounded
functional compatibility signal [2, 3]. Related representation-matching work
shows that simple transformations can align spaces with semantic supervision
[4]. Paper-A does not claim representation interchangeability or general
alignment. Its operation is within one frozen model across depth, with a fixed
readout and featurewise location/scale calibration fitted on FIT data.

### 2.4 Functional-alignment caution

Functional alignment can mislead: models can become functionally aligned while
representing different information [5]. This motivates the paper's boundary
claim that recovering readout accuracy under recalibration does not establish
representation equivalence.

### 2.5 Representation alignment and steering

Steering and alignment work manipulates hidden states along task-derived
directions. Prior work demonstrates local target-directed movement, but not
automatic behavioral control [6]. EXP-017 and EXP-019 are therefore boundary
evidence against a representational-manipulability-to-behavior jump.

### 2.6 Layerwise and recent representation-readout work

Recent work continues to study representation progression and the separation
between representation and readout [7, 8]. Direct 2025-2026 neighbors include
functional-alignment caution [5], fresh-head probing for localizing
representation/readout failure [8], and the decodability/causality boundary
[9]. Adjacent work on post-grokking representation collapse [10] and multi-speed
learning [11] is relevant to mechanism but does not duplicate the present
preregistered fixed-readout condition panel.

## 3. Methods

### 3.1 Model and representation checkpoints

The main evidence chain uses `Qwen/Qwen3-1.7B`, exact local snapshot
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. The larger-model representation
replication EXP-020A uses `Qwen/Qwen3-4B`. EXP-018 includes secondary
Gemma-3-1B configurations, but the behavioral and later calibration studies
focus on Qwen3 models. Model and tokenizer loading used local-only offline
semantics; no alternate snapshot or network fallback was permitted.

For the frozen Qwen3-1.7B implementation, hidden-state tuple semantics are:

- `hidden_states[0]` is the embedding output;
- `hidden_states[1..27]` are decoder block outputs before final RMSNorm;
- `hidden_states[28]` is the post-final-RMSNorm last hidden state.

The primary final checkpoint is block27 pre-final RMSNorm. Post-final RMSNorm
is descriptive only and is not silently substituted for the preregistered
pre-final checkpoint.

### 3.2 Operational semantic-class construct and class mapping

The semantic construct uses four operational classes:

- `logic`
- `causality`
- `analogy`
- `definition`

Each record is assigned to exactly one class by the frozen dataset construction
rules. These classes are controlled operational labels for fixed-readout
measurement; they are not a complete reasoning ontology and are not used to
claim a universal task-axis decomposition.

The frozen dataset contains `1760` records across `880` source families,
organized into the `10` registered condition families of EXP-024. The primary
inferential unit is the condition (`N = 10`); the record and source-family counts
describe data construction, not the inferential sample for the primary test.

### 3.3 Fixed reference readout and data separation

A global fixed reference readout `C_ref` is trained only from FIT reference-form
representations at `block16_pre_final_rmsnorm`. A reference scaler
`mu_ref, sigma_ref` is estimated from the same FIT data and remains frozen. The
classifier contract is frozen and uses L2-regularized multinomial logistic
regression. No hyperparameter tuning is performed; the frozen production runner
used a fixed random seed and a single classifier contract.

The main source-family partitions are:

- `FIT`: used to fit reference scaler, classifier, or per-condition calibration
  parameters;
- `DIAGNOSTIC`: used only for the independent susceptibility diagnostic in
  EXP-024;
- `EVAL`: used only for confirmatory outcomes.

EXP-024 enforces source-family independence: `FIT`, `DIAGNOSTIC`, and `EVAL`
are pairwise disjoint, and no source-family-derived sibling crosses partitions.

### 3.4 Featurewise recalibration

For the discovery and replication studies, the fixed frame is `A0`. The
featurewise recalibration `A1` is a low-capacity per-feature location/scale
adjustment applied before the fixed readout. `A2` is a layer-wise linear refit
used as a comparison; it is not the primary mechanism.

For EXP-024, condition-specific recalibration variants are:

```text
z_A0         = (h - mu_ref)       / sigma_ref
z_A_mu       = (h - mu_final,c)   / sigma_ref
z_A_sigma    = (h - mu_ref)       / sigma_final,c
z_A_mu_sigma = (h - mu_final,c)   / sigma_final,c
```

The classifier `C_ref` is never refit.

### 3.5 EXP-024 condition-level primary design

EXP-024 uses a frozen panel of ten surface-realization conditions:

`c01_lexical_relex`, `c02_syntactic_restructure`,
`c03_controlled_compression`, `c04_controlled_elaboration`,
`c05_relation_explicit`, `c06_relation_implicit`,
`c07_register_formal`, `c08_register_informal`,
`c09_neutral_distractor_prefix`, `c10_anaphoric_reference`.

For each condition `c`, the primary diagnostic is:

```text
S_diag(c) =
    BA_A0(block16_pre_final_rmsnorm, DIAG_c)
  - BA_A0(block27_pre_final_rmsnorm, DIAG_c)
```

Higher `S_diag(c)` means greater independent diagnostic fixed-readout
degradation.

The primary confirmatory outcome is:

```text
G_eval(c) =
    BA_A_mu_sigma(block27_pre_final_rmsnorm, EVAL_c)
  - BA_A0(block27_pre_final_rmsnorm, EVAL_c)
```

Higher `G_eval(c)` means greater calibration rescue on untouched EVAL source
families.

`S_diag(c)` and `G_eval(c)` use disjoint source families. This removes the
algebraic shared-A0 limitation documented after EXP-023.

### 3.6 Primary inference

The primary scientific unit is the condition, `N = 10`. The primary statistic
is Spearman's rank correlation between `S_diag(c)` and `G_eval(c)`. Ties were
handled according to the frozen protocol; the manuscript reports the registered
result and does not perform a post-hoc alternative tie analysis. The test is a
one-sided exact permutation test enumerating all `10! = 3,628,800` pairings.
The registered support rule is:

```text
PRIMARY_SUPPORTED =
    rho > 0
    AND exact_one_sided_p <= 0.05
```

The condition panel is fixed/designed, not a random sample from all possible
surface transformations. The reported primary `p` therefore does not support a
population-of-transformations claim. Secondary `G_mu`, `G_sigma`, bootstrap
intervals, and descriptive full-depth trajectories are prespecified descriptive
only. No post-hoc test is used to replace the primary.

### 3.7 Evidence summary

**Table 1** is the canonical evidence-summary table, rendered in
`docs/paper/tables/paper_a_evidence_summary.md` from the same experiment
results. It is summarized below:

| Experiment | Scientific question | Design | Primary outcome | Interpretation | Boundary |
| --- | --- | --- | --- | --- | --- |
| EXP-018 | Are task-associated hidden-state directions locally manipulable? | Held-out task-directed vs matched-random/opposite probe changes | Target-directed movement consistently positive | Local representational manipulability | No behavioral control |
| EXP-020A | Does the representation-level effect replicate in a larger same-family model? | Same-family higher-parameter model | `REPRESENTATION_REPLICATION_SUPPORTED` | Same-family replication | Not cross-family generality |
| EXP-017 | Does representation manipulation produce task-specific behavioral advantage? | Matched-control correctness test | Overall accuracy difference `0.0000` | No demonstrated behavioral control | Output-level interpretation unresolved |
| EXP-019 | Can an independent output-only evaluator establish semantic task identity? | One-shot independent Final-200 evaluation | Balanced accuracy `0.4850`; threshold failed | Independent evaluator not established | Behavioral boundary remains |
| EXP-021 | Does a fixed readout remain qualified across depth? | Fixed source-semantic readout across clean checkpoints | Did not pass globally at deeper checkpoints | Fixed-readout qualification is depth/condition dependent | Qualification scope, not formal universal drift |
| EXP-022A | Does fixed-readout degradation occur in a discovery frame? | Fixed readout at reference vs block27-pre | `PARTIAL_CONCORDANCE`; Split B `D_fixed = -0.50`, `p = 0.015625` | Fixed-readout degradation observed | Discovery stage |
| EXP-023 | Does featurewise calibration rescue replicate across complementary splits? | Independent preregistered replication | `NO_REPLICATION` | Split A rescue, Split B null rescue | No general cross-split calibration claim |
| EXP-024 | Does independent `S_diag` predict independent `G_eval` across the panel? | 10-condition independent DIAGNOSTIC/EVAL design | Primary `NOT_SUPPORTED`; `rho = 0.284`, exact `p = 0.2115` | Simple degradation predictor unsupported | 10/10 positivity is descriptive only |

## 4. Results

### 4.1 Local representational manipulability

**Figure 2** (`docs/paper/figures/fig02_manipulability`) presents the
EXP-018 frozen probe summary and EXP-020A same-family replication means with
their canonical bootstrap intervals.

EXP-018 used a held-out fit/evaluation design with task-directed,
matched-norm random, and exact opposite interventions. Across the frozen
primary probe conditions, task-directed movement increased target probability
relative to matched random in 216/216 conditions; the mean task-minus-random
target-probability change was `+0.8366` (median `+0.8800`). Task-directed
movement also exceeded opposite movement in 216/216 conditions, with a mean
task-minus-opposite change of `+0.9471` (median `+0.9855`).

The relational-preservation comparison was negative: task-directed movement
did not systematically improve the preregistered IVS advantage over matched
random translation. The narrow conclusion is local representational
manipulability, not relational preservation and not behavioral control.

EXP-020A extended the representation-level claim to a same-family
higher-parameter model. Its recovered canonical result is
`REPRESENTATION_REPLICATION_SUPPORTED`. Across the frozen primary
comparisons, task-minus-random target-probability differences were positive in
72/72 comparisons (mean `+0.8732`), and task-minus-opposite differences were
also positive in 72/72 comparisons (mean `+0.9864`).

### 4.2 Representation-level manipulability does not imply behavioral control

EXP-017 tested whether the same task-derived direction that moved hidden states
also produced a task-specific correctness-level behavioral advantage. The
frozen overall accuracy was `0.6375` for both `TASK_REAL` and
`MATCHED_RANDOM`; the difference was `0.0000`. Item-level correctness differed
on 22/80 items, with the group pattern mixed rather than task-directed. The
matched-random condition also showed a higher malformed-output rate, so the one
apparent group advantage was not clean behavioral evidence.

EXP-019 attempted an independent output-only behavioral task-identity
evaluator. Procedural development performance was high, but the one-shot
independent Final-200 evaluation failed: balanced accuracy was `0.4850`,
macro F1 was `0.4580`, and recall failed the preregistered `>= 0.60` threshold
for multiple classes. The independent evaluator therefore did not establish
semantic task-identity classification, and the output-level targetness
interpretation of EXP-017 remains unresolved.

Together, EXP-017 and EXP-019 function as boundary evidence. They prevent the
paper from interpreting EXP-018/EXP-020A as behavioral or functional control.

### 4.3 Fixed semantic readout compatibility degrades across depth

**Figure 3** (`docs/paper/figures/fig03_fixed_readout_degradation`) plots the
EXP-021 checkpoint-level fixed-readout accuracy for both qualification splits.

EXP-021 Stage-Q used a fixed source-semantic readout across frozen
intervention and normalized-depth checkpoints. The measurement qualification
did not pass globally. For Split A, accuracy was `0.9167` at the intervention
checkpoint and `0.9167` through normalized depths `0.625`, `0.75`, and
`0.875`, but fell to `0.6667` at block27 pre-final RMSNorm and `0.2500` at
post-final RMSNorm. For Split B, accuracy was `0.6667` at the intervention
checkpoint and `0.6667` at normalized depth `0.625`, fell to `0.4167` at
`0.875`, then to `0.2500` at block27 pre-final RMSNorm and `0.1667` at
post-final RMSNorm.

EXP-021 is an engineering measurement-qualification result, not a full formal
scientific result. The permitted interpretation is that a fixed readout did not
remain uniformly qualified across deeper clean checkpoints.

EXP-022A tested the same fixed-readout degradation question in a discovery
frame. In Split A, `A0` balanced accuracy fell from `0.9167` at the reference
checkpoint to `0.6667` at block27-pre. In Split B, `A0` fell from `0.7500` to
`0.2500`. The primary fixed-readout degradation criterion was supported in
Split B (`D_fixed = -0.50`, exact `p = 0.015625`) but not Split A
(`D_fixed = -0.25`, exact `p = 0.125`). The cross-split synthesis is
`PARTIAL_CONCORDANCE`.

### 4.4 Featurewise recalibration can recover readout performance, but replication is heterogeneous

**Figure 4** (`docs/paper/figures/fig04_exp023_heterogeneity`) makes the EXP-023
Split A/Split B heterogeneity and the registered `NO_REPLICATION` outcome
visually explicit.

EXP-022A found descriptive featurewise recovery. In Split A, `A1` increased
block27-pre balanced accuracy from `0.6667` (`A0`) to `0.7500`
(`G_scale = +0.0833`). In Split B, `A1` increased block27-pre balanced accuracy
from `0.2500` to `0.7500` (`G_scale = +0.5000`). In contrast, `A2` was below
`A1` in both splits, and preregistered `G_refit` support was false in both
splits. Thus the recovery signal is featurewise recalibration, not unrestricted
layer-specific refitting.

EXP-023 was the independent preregistered replication. Its registered outcome
is `NO_REPLICATION`.

In Split A, `A0` fell from `0.9375` to `0.59375`, and joint featurewise
recalibration `A_mu_sigma` reached `0.84375`, yielding
`G_cal = +0.2500` (exact `p = 0.0193`, split-level support true). In Split B,
`A0` fell only from `0.9375` to `0.90625`, and `A_mu_sigma` remained
`0.90625`, yielding `G_cal = 0.0` (exact `p = 0.75`, split-level support
false). The unsupported split is a null rescue, not a partial rescue, so the
cross-split label remains `NO_REPLICATION`.

The strongest degradation and strongest rescue appeared in different
complementary splits across EXP-022A and EXP-023. The fixed variant-direction
explanation is therefore `NOT_SUPPORTED`; readout compatibility appears
condition and dataset dependent.

### 4.5 Independent susceptibility prediction is not supported

**Figure 5** (`docs/paper/figures/fig05_exp024_primary_scatter`) shows the
registered EXP-024 primary scatter with all ten conditions, exact rho/p, and
`NOT_SUPPORTED`. **Figure 6** (`docs/paper/figures/fig06_exp024_broad_benefit`)
shows the paired descriptive panel observation.

#### 4.5.1 Descriptive observation

EXP-024 was a separate preregistered condition-panel test with `N = 10`
conditions. All ten conditions had positive `S_diag` and positive `G_eval`
descriptively:

| Condition | `S_diag` | `G_eval` |
| --- | ---: | ---: |
| `c01_lexical_relex` | 0.5000 | 0.40625 |
| `c02_syntactic_restructure` | 0.4375 | 0.46875 |
| `c03_controlled_compression` | 0.3125 | 0.34375 |
| `c04_controlled_elaboration` | 0.3125 | 0.5000 |
| `c05_relation_explicit` | 0.5000 | 0.4375 |
| `c06_relation_implicit` | 0.4375 | 0.3750 |
| `c07_register_formal` | 0.3125 | 0.34375 |
| `c08_register_informal` | 0.34375 | 0.46875 |
| `c09_neutral_distractor_prefix` | 0.4375 | 0.46875 |
| `c10_anaphoric_reference` | 0.3125 | 0.3125 |

The `10/10` positive observations are descriptive panel evidence only. They
are not a replacement primary sign test and are not confirmatory significance.

#### 4.5.2 Registered primary result

The preregistered primary test of simple independent degradation-magnitude
prediction was:

```text
rho = 0.28401877872187725
exact_one_sided_p = 0.2115079365079365
PRIMARY_SUPPORTED = false
```

Therefore `HYP_CALIBRATION_CONDITIONAL_002` is
`NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`. The direction was positive, but the
association did not meet the registered support rule.

The prespecified secondary Spearman between `S_diag` and `G_mu` was
`0.2840`; between `S_diag` and `G_sigma` it was `-0.5067`. These are
descriptive only and do not replace the primary.

The correct dual-proposition reading is: broad panel-bounded positive
calibration benefit does not imply successful prospective susceptibility
prediction.

### 4.6 Integrated claim-boundary synthesis

The combined chain supports a bounded positive/negative story:

- Local representation-level manipulability is supported.
- Manipulability does not establish behavioral control.
- Fixed readout compatibility can degrade across depth.
- FIT-only featurewise recalibration can rescue some degraded readouts.
- General cross-split calibration replication is not supported.
- Panel-bounded descriptive calibration benefit is observed in EXP-024.
- Simple independent degradation magnitude does not reliably rank calibration
  susceptibility.

General coordinate transport, functional binding, universal calibration, and
cross-model generality remain outside the supported claims.

## 5. Discussion

### 5.1 Observation

Fixed readout degradation was repeatedly observed across deeper checkpoints.
Featurewise recalibration improved readout accuracy in several degraded
conditions, and EXP-024 observed positive `G_eval` in all ten panel conditions.
These observations make it difficult to interpret every fixed-readout failure
as evidence that task-associated information has disappeared.

### 5.2 Operational interpretation

Fixed-readout failure is ambiguous. It can reflect information loss, readout
frame mismatch, or both. Recalibration that restores readout utility without
access to new task labels is consistent with readout incompatibility
contributing to the observed performance degradation. It does not prove that
all relevant information was preserved, that the deeper representation is
equivalent to the reference representation, or that the recalibration is a
representation transport mechanism.

### 5.3 Negative mechanism result

EXP-024 directly tested the simplest prospective susceptibility predictor:
larger independent diagnostic degradation should rank larger calibration
benefit. The primary test did not support this predictor. The result is a
negative mechanism result, not evidence that calibration benefit and
degradation are unrelated in general.

### 5.4 Open mechanism

Future mechanistic work may need to consider covariance or non-diagonal
structure, margin geometry, higher-order frame mismatch, or local class
configuration. These possibilities are speculation. EXP-024 does not establish
any of them.

### 5.5 Theoretical boundaries

The evidence chain preserves several distinctions:

- Decodability does not equal causal role.
- Manipulability does not equal behavioral control.
- Calibration does not equal coordinate transport.
- Readout recovery does not equal representation equivalence.
- Representation compatibility does not equal functional binding.

The negative behavioral evidence from EXP-017 and EXP-019 is therefore part of
the scientific contribution rather than an appendix artifact.

### 5.6 Measurement-resolution limitation

EXP-024 `S_diag` values lie in a narrow discrete range with substantial ties.
This is a measurement-resolution limitation. It does not turn the registered
`NOT_SUPPORTED` primary into an implicit positive result.

## 6. Limitations

The main limitations are:

1. The primary evidence remains largely one model family.
2. The semantic construct has four operational classes.
3. The condition panel is frozen and not a random sample from all possible
   surface transformations.
4. EXP-024 primary inference uses `N = 10` conditions; the primary unit is the
   condition, not the larger record count.
5. EXP-024 condition-level diagnostic resolution is limited and tied.
6. Calibration is deliberately low-capacity featurewise adaptation, not
   arbitrary alignment.
7. Cross-model generality is untested.
8. Behavioral control is not established.
9. Functional binding is not tested.
10. General coordinate transport is not tested.

These limitations bound the claims and identify what a stronger venue-level
manuscript would need. They are not post-hoc excuses for the negative results.

## 7. Conclusion

Three bounded conclusions follow from the evidence chain:

1. Fixed semantic readout compatibility can degrade across Transformer depth
   under the tested settings.
2. FIT-only featurewise recalibration can recover substantial readout
   performance in multiple tested conditions, but replication is heterogeneous
   across datasets and splits.
3. A simple independent degradation-magnitude diagnostic did not reliably
   predict calibration benefit under the registered EXP-024 primary test.

The mechanism governing calibration susceptibility remains unresolved. Future
work should study which structural properties of representation/readout
mismatch govern calibration susceptibility.

## References

1. N. Belrose, Z. Furman, L. Smith, D. Halawi, I. Ostrovsky, L. McKinney,
   S. Biderman, and J. Steinhardt, *Eliciting Latent Predictions from
   Transformers with the Tuned Lens*, arXiv:2303.08112.
2. Y. Bansal, P. Nakkiran, and B. Barak, *Revisiting Model Stitching to Compare
   Neural Representations*, NeurIPS 2021, pages 225--236, arXiv:2106.07682.
3. A. Csisz?rik, P. K?r?si-Szab?, ?. Matszangosz, G. Papp, and D. Varga,
   *Similarity and Matching of Neural Network Representations*, NeurIPS 2021,
   pages 5656--5668, arXiv:2110.14633.
4. V. Maiorca, L. Moschella, A. Norelli, M. Fumero, F. Locatello, and
   E. Rodol?, *Latent Space Translation via Semantic Alignment*, arXiv:2311.00664.
5. D. Smith, H. Mannering, and A. Marcu, *Functional Alignment Can Mislead:
   Examining Model Stitching*, ICML 2025 Spotlight,
   https://icml.cc/virtual/2025/poster/44458.
6. K. Li, O. Patel, F. Vi?gas, H. Pfister, and M. Wattenberg,
   *Inference-Time Intervention: Eliciting Truthful Answers from a Language
   Model*, NeurIPS 2023 Spotlight, arXiv:2306.03341.
7. J. Jiang, J. Zhou, and Z. Zhu, *Tracing Representation Progression:
   Analyzing and Enhancing Layer-Wise Similarity*, ICLR 2025 Poster,
   arXiv:2406.14479.
8. *Localising Failure between Representation and Readout: A Fresh-Head Probe
   for Parameter-Space Model Merging*, OpenReview `230T2UcWwR`, TMLR
   Paper8964. Full author list pending final primary-source verification.
9. L. Huang and Y. Chang, *Causality != Decodability, and Vice Versa: Lessons
   from Interpreting Counting ViTs*, NeurIPS 2025, arXiv:2510.09794.
10. A. Janati, K. El Maghraoui, A. Kanavalau, and A. Belfatmi, *Post-Grokking
    Collapse at the Representation-Readout Interface in Muon-Trained
    Transformers*, arXiv:2608.07436.
11. C.-N. Chou, O. Uzdelewicz, N.-C. Chiu, Y.-Y. Yang, and S. Chung, *Two
    Speeds of Learning: A Representation-Readout Decomposition of Grokking and
    Double Descent*, arXiv:2605.27078.

BibTeX: `docs/paper/references.bib`. Verification record:
`docs/paper/PAPER-A-REFERENCE-VERIFICATION.md`. Ten references are verified;
reference 8 is partial pending author-list confirmation.

## Figure and Table Placement Notes

The manuscript now uses six main figures and two main tables generated from
canonical evidence. Vector SVG and preview PNG versions are stored in
`docs/paper/figures/`; table artifacts are stored in `docs/paper/tables/`.

### Main figures

- **Figure 1** (`fig01_framework`): tested evidence chain from fixed semantic
  readout through held-out recovery, replication/heterogeneity, and independent
  susceptibility testing. The dashed boundary marks behavioral control,
  functional binding, and coordinate transport as not established.
- **Figure 2** (`fig02_manipulability`): EXP-018 frozen probe summary
  (`216/216` task > matched-random; `216/216` task > opposite) and EXP-020A
  observed means with canonical bootstrap 95% intervals. The EXP-020A gate is
  `REPRESENTATION_REPLICATION_SUPPORTED`.
- **Figure 3** (`fig03_fixed_readout_degradation`): EXP-021 fixed-readout
  accuracy across qualification checkpoints for Split A and Split B.
  Checkpoint-level predicted-class coverage failures are marked; the result is
  engineering measurement qualification only, with `global_pass = false`.
- **Figure 4** (`fig04_exp023_heterogeneity`): panel (a) EXP-023 final-block
  readout performance by variant and split; panel (b) `G_cal` point estimates
  with canonical bootstrap intervals. The caption and figure both state
  registered cross-split outcome `NO_REPLICATION`.
- **Figure 5** (`fig05_exp024_primary_scatter`): EXP-024 `S_diag(c)` vs
  `G_eval(c)` for all 10 frozen conditions. The annotation reports
  `rho = 0.28401877872187725`, exact one-sided
  `p = 0.2115079365079365`, and registered support `NOT_SUPPORTED`. No
  dominant trend line is used to visually inflate the association.
- **Figure 6** (`fig06_exp024_broad_benefit`): paired condition-level
  `S_diag(c)` and `G_eval(c)` display in frozen condition order. It shows
  `10/10` positivity for both while labeling this as descriptive panel
  observation only, not a new confirmatory positivity test.

### Main tables

- **Table 1** (`docs/paper/tables/paper_a_evidence_summary.md`): scientific
  progression evidence summary across EXP-018, EXP-017, EXP-019, EXP-020A,
  EXP-021, EXP-022A, EXP-023, and EXP-024.
- **Table 2** (`docs/paper/tables/exp024_condition_outcomes.md`): all ten
  EXP-024 condition outcomes with canonical `S_diag(c)`, `G_eval(c)`, and
  diagnostic balanced-accuracy fields, plus the registered primary summary.

The full manuscript is `NON_AUTHORITATIVE_DERIVED_FROM_CANONICAL_EVIDENCE`.
