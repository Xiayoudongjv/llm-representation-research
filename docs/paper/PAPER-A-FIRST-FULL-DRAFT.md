# Fixed Readout Compatibility and Featurewise Recalibration Across Transformer Depth: A Controlled, Preregistered Evidence Chain with Heterogeneous and Negative Results

Status: `FIRST_FULL_DRAFT_CREATED`

This document is a derived manuscript draft. Canonical experiment results,
frozen protocols, scientific reviews, and research ledgers outrank it.

## Abstract

Intermediate representations in frozen language models change across
Transformer depth, but many representational analyses apply fixed probes or
readouts as though the coordinate system were stable. We study a narrow version
of this problem: whether a fixed semantic-class readout remains compatible with
deeper representations, whether low-capacity FIT-only featurewise recalibration
can restore its utility, whether that recovery is stable across data
conditions, and whether an independently measured degradation magnitude can
prospectively predict calibration susceptibility. Across a controlled chain of
experiments, we find that local task-associated representations are
manipulable under held-out controls, yet that manipulability does not produce a
stable task-specific behavioral advantage. Fixed readout accuracy can drop
substantially across depth, and featurewise recalibration can produce large
recovery in some conditions. Independent preregistered replication, however,
returns `NO_REPLICATION`: one complementary split shows substantial rescue,
while the other shows no rescue. In a separate 10-condition panel, all ten
conditions show positive diagnostic degradation and positive calibration
benefit descriptively; nevertheless, the preregistered primary test of simple
independent degradation-magnitude prediction is `NOT_SUPPORTED`
(`rho = 0.2840`, exact one-sided permutation `p = 0.2115`). The bounded
conclusion is that fixed-readout incompatibility and calibration utility are
real but condition-dependent, and that simple degradation magnitude is not
sufficient to explain calibration susceptibility.

## 1. Introduction

Hidden states in Transformer language models are not static objects. As an
input moves through successive blocks, the representation can change in both
geometry and information content. This depth-dependent variation creates a
measurement problem for representational analyses: a classifier, probe, or
readout trained at one layer is often reused at another layer as if the
representation space were fixed. When performance drops, it is tempting to
conclude that task-associated information has disappeared. An alternative is
that the information remains present, but the fixed readout has become
incompatible with the coordinate system of the deeper representation.

This paper studies the narrower, tractable version of that problem. We focus
on four questions:

1. Does a fixed semantic readout lose compatibility when moved across
   Transformer depth?
2. Can low-capacity, FIT-only featurewise recalibration restore that readout
   without refitting a layer-specific classifier?
3. Is that calibration benefit stable across complementary data conditions?
4. Can an independent degradation magnitude measured before the confirmatory
   EVAL outcome predict condition-level calibration susceptibility?

We do not attempt to answer the entire representation-to-behavior chain.
Coordinate transport, causal control, universal calibration, functional
binding, and general cognitive-space claims are outside the evidence assembled
here and are explicitly not claimed.

The controlled chain begins with held-out representation manipulation
(EXP-018), continues through a larger-model representation-level replication
(EXP-020A), and then separates representation effects from behavioral control
(EXP-017, EXP-019). The central readout question is addressed by a fixed
readout qualification study (EXP-021), a discovery-stage featurewise
recalibration study (EXP-022A), an independent preregistered replication
(EXP-023), and a final preregistered condition-panel susceptibility test
(EXP-024).

The scientific contribution is not the observation that different layers may
benefit from different affine readouts; prior work already establishes that
phenomenon. The contribution is the controlled combination of fixed readout,
deliberately low-capacity recalibration, held-out source-family separation,
and explicit negative replication. EXP-023 and EXP-024 are part of the main
story, not appendix-only caveats.

The strongest bounded claim is:

> Fixed semantic readouts can lose compatibility across Transformer depth.
> Low-capacity FIT-only featurewise recalibration can substantially restore
> readout performance under multiple held-out conditions, but the benefit is
> not uniformly reproducible across data conditions and is not reliably
> predicted by a simple independent measure of fixed-readout degradation
> magnitude.

This claim is deliberately conditional. It does not assert representation
invariance, coordinate transport, semantic preservation, universal calibration,
causal reasoning control, true task axes, general cognitive space, or
functional binding.

## 2. Related Work

### 2.1 Probing and intermediate representation decoding

Probing research uses trained classifiers to estimate what can be decoded from
intermediate hidden states. This line of work demonstrates that layer-specific
readouts can expose task-relevant structure, but it also warns that decoding
performance is not equivalent to causal role, representation equivalence, or
behavioral control. Paper-A inherits this caution. The present experiments use
fixed semantic-class readouts and deliberately do not train a new probe at each
layer for the primary mechanism.

[TODO: citation for probing/decoding critiques and layer-specific linear probe
literature beyond the anchors below.]

### 2.2 Tuned Lens and layer-specific decoding

Tuned Lens trains a per-block affine probe from hidden states to vocabulary or
logit space and uses those probes to inspect latent predictions across depth
[TODO: exact citation; reviewed reference: Belrose et al., "Eliciting Latent
Predictions from Transformers with the Tuned Lens", arXiv:2303.08112].

Tuned Lens already establishes that hidden representations often require
layer-specific affine readouts and that iterative decoding can expose
depth-wise prediction dynamics. Paper-A therefore does not claim novelty for
"different layers need different readouts."

### 2.3 Model stitching and representation compatibility

Model stitching connects components of different trained models through a
simple trainable layer and interprets stitched performance as a bounded
functional compatibility signal [TODO: exact citation; reviewed reference:
Bansal, Nakkiran, and Barak, "Revisiting Model Stitching to Compare Neural
Representations", NeurIPS 2021, arXiv:2106.07682].

Stitching and related alignment methods show that simple learned adapters can
restore task performance even when representations differ. Paper-A differs by
keeping the reference readout fixed and allowing only featurewise
location/scale calibration fitted on FIT data.

### 2.4 Functional-alignment caution

Functional alignment can mislead: models can become functionally aligned while
representing different information [TODO: exact citation; reviewed reference:
Smith, Mannering, and Marcu, "Functional Alignment Can Mislead: Examining Model
Stitching", ICML 2025 Spotlight].

This caution motivates our distinction between readout recovery and
representation equivalence. Recovering classification accuracy under
recalibration does not establish that the deeper representation is
informationally or geometrically equivalent to the reference representation.

### 2.5 Representation alignment and steering

Steering and alignment work manipulates hidden states along task-derived
directions. Prior work demonstrates local target-directed movement, but it does
not automatically establish behavioral control. EXP-017 and EXP-019 are
therefore positioned as boundary evidence rather than as a behavioral steering
success story.

[TODO: citation for representation steering / activation interventions; avoid
claiming a complete prior-art search.]

## 3. Methods

### 3.1 Model and representation checkpoints

The main evidence chain uses `Qwen/Qwen3-1.7B`, exact local snapshot
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. The larger-model representation
replication EXP-020A uses `Qwen/Qwen3-4B`. EXP-018 includes secondary
Gemma-3-1B configurations, but the behavioral and later calibration studies
focus on Qwen3 models.

For the frozen Qwen3-1.7B implementation, hidden-state tuple semantics are:

- `hidden_states[0]` is the embedding output;
- `hidden_states[1..27]` are decoder block outputs before final RMSNorm;
- `hidden_states[28]` is the post-final-RMSNorm last hidden state.

The primary final checkpoint is block27 pre-final RMSNorm. Post-final RMSNorm
is descriptive only and is not silently substituted for the preregistered
pre-final checkpoint.

### 3.2 Operational semantic-class construct

The semantic construct uses four operational classes:

- `logic`
- `causality`
- `analogy`
- `definition`

This is a controlled semantic-class construct, not a complete reasoning
ontology. It is used to evaluate fixed semantic readouts, not to claim a
universal task-axis decomposition.

### 3.3 Fixed reference readout and data separation

A global fixed reference readout `C_ref` is trained only from FIT reference-form
representations at `block16_pre_final_rmsnorm`. A reference scaler
`mu_ref, sigma_ref` is estimated from the same FIT data and remains frozen. The
classifier contract is frozen and uses L2-regularized multinomial logistic
regression; no hyperparameter tuning is performed.

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
z_A0       = (h - mu_ref)       / sigma_ref
z_A_mu     = (h - mu_final,c)   / sigma_ref
z_A_sigma  = (h - mu_ref)       / sigma_final,c
z_A_mu_sigma = (h - mu_final,c) / sigma_final,c
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

`S_diag(c)` and `G_eval(c)` use disjoint source families. The formulas are
analogous, but they do not share the same observations. This removes the
algebraic shared-A0 limitation documented after EXP-023.

### 3.6 Primary inference

The primary scientific unit is the condition, `N = 10`. The primary statistic
is Spearman's rank correlation between `S_diag(c)` and `G_eval(c)`. The test is
a one-sided exact permutation test enumerating all `10! = 3,628,800` pairings.
The registered support rule is:

```text
PRIMARY_SUPPORTED =
    rho > 0
    AND exact_one_sided_p <= 0.05
```

Secondary `G_mu`, `G_sigma`, bootstrap intervals, and descriptive full-depth
trajectories are prespecified descriptive only. No post-hoc test is used to
replace the primary.

## 4. Results

### 4.1 Task-associated representations are locally manipulable

EXP-018 used a held-out fit/evaluation design with task-directed,
matched-norm random, and exact opposite interventions. Across the frozen
primary probe conditions, task-directed movement increased target probability
relative to matched random in 216/216 conditions; the mean task-minus-random
target-probability change was `+0.8366` (median `+0.8800`). Task-directed
movement also exceeded opposite movement in 216/216 conditions, with a mean
task-minus-opposite change of `+0.9471` (median `+0.9855`).

The relational-preservation comparison was negative: task-directed movement
did not systematically improve the preregistered IVS advantage over matched
random translation. Therefore the narrow conclusion is local representational
manipulability, not relational preservation and not behavioral control.

EXP-020A extended the representation-level claim to a same-family
higher-parameter model. Its recovered canonical result is
`REPRESENTATION_REPLICATION_SUPPORTED`. Across the frozen primary
comparisons, task-minus-random target-probability differences were positive in
72/72 comparisons (mean `+0.8732`), and task-minus-opposite differences were
also positive in 72/72 comparisons (mean `+0.9864`).

### 4.2 Manipulability does not establish behavioral control

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

### 4.3 Fixed readout compatibility degrades across depth

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

### 4.5 EXP-024: broad positive panel benefit but susceptibility prediction fails

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
access to new task labels is evidence that at least part of the failure is
readout incompatibility. It is not evidence that the deeper representation is
equivalent to the reference representation.

### 5.3 Negative mechanism result

EXP-024 directly tested the simplest prospective susceptibility predictor:
larger independent diagnostic degradation should rank larger calibration
benefit. The primary test did not support this predictor. The result is a
negative mechanism result, not evidence that calibration benefit and
degradation are unrelated in general.

### 5.4 Open mechanism

Future mechanistic work may need to consider higher-order frame mismatch,
covariance or non-diagonal structure, margin geometry, or local class
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
4. Calibration is deliberately low-capacity featurewise adaptation, not
   arbitrary alignment.
5. EXP-024 condition-level diagnostic resolution is limited and tied.
6. Behavioral and functional binding are not established.
7. General coordinate transport is not tested.

These limitations are not presented as post-hoc excuses for the negative
results. They bound the claims and identify what a stronger venue-level
manuscript would need.

## 7. Conclusion

Fixed semantic readouts can become incompatible with deeper representations.
Simple FIT-only featurewise recalibration can often recover readout utility,
but this recovery is heterogeneous and its magnitude is not explained by the
preregistered simple degradation predictor. The appropriate current conclusion
is therefore bounded: readout incompatibility and calibration utility are real
but condition-dependent. Future work should study which structural properties
of representation/readout mismatch govern calibration susceptibility.

This paper deliberately does not end with a unified representation theory.
The positive/negative evidence chain is the contribution.

## References / Citation TODOs

- [TODO: exact citation] Belrose et al., "Eliciting Latent Predictions from
  Transformers with the Tuned Lens", arXiv:2303.08112.
- [TODO: exact citation] Bansal, Nakkiran, and Barak, "Revisiting Model
  Stitching to Compare Neural Representations", NeurIPS 2021,
  arXiv:2106.07682.
- [TODO: exact citation] Smith, Mannering, and Marcu, "Functional Alignment Can
  Mislead: Examining Model Stitching", ICML 2025 Spotlight.
- [TODO: citation] Probing/decoding critique literature.
- [TODO: citation] Representation steering / activation intervention
  literature.

Citation metadata is intentionally not fabricated. References must be
verified against primary sources before submission.

## Figure and Table Placement Notes

- [TODO: figure] EXP-024 scatter of `S_diag(c)` versus `G_eval(c)` with all ten
  conditions shown.
- [TODO: figure] Paired `S_diag`/`G_eval` display for the ten-condition panel.
- [TODO: exact table reference] Full experiment-to-claim matrix in
  `docs/paper/PAPER-A-CLAIM-EVIDENCE-MATRIX.md`.

The full manuscript draft is `NON-AUTHORITATIVE_DERIVED_FROM_CANONICAL_EVIDENCE`.
