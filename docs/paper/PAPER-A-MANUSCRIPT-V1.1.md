# Fixed-Readout Operational Compatibility Across Transformer Depths: A Three-Model Empirical Dissociation

## Abstract

Layerwise probes, readout transfer, and representation comparison make it
possible to ask whether a task readout remains usable as a language model is
processed through depth. These measurements are related, but they need not
answer the same question. Layerwise decodability does not establish that the
same decision rule remains usable across depths; direct readout reuse is
therefore a distinct empirical question. A readout can transfer directly to
another depth, degrade under direct reuse, or regain some utility after a
deliberately restricted calibration step. We study this distinction with a
preregistered operational measurement: a readout fit at source depth is
applied without retraining at each target depth. We report directed
source-target matrices for three decoder-only language models and separate
direct compatibility, degradation, and restricted FIT-only recovery. Across
the tested panel, all three models show positive distance-associated structure
in degradation, but their source and target organization and restricted
recovery profiles differ. Qwen3-1.7B is target-dominant with unsupported
LOW-D recovery; OLMo-2-1B-Instruct is source-dominant with supported LOW-D
recovery; Meta-Llama-3.2-1B-Instruct is target-dominant with supported LOW-D
recovery. Earlier negative evidence also matters: complementary-split
recovery is `NO_REPLICATION`, and a separate degradation predictor is
unsupported in two registered panels. As a secondary analysis, centered
linear CKA has a positive descriptive association with direct compatibility in
each model, while remaining a symmetric similarity measure rather than a
substitute for directed readout transfer. The evidence supports a bounded
three-model comparison of operational compatibility, heterogeneity, and
measurement limits; it does not establish a general representation theory or
a causal account of layerwise change.

## 1. Introduction

Transformer representations are routinely inspected through probes, layerwise
decoders, logit-based readouts, and comparisons between hidden states. These
operations are useful because different depths can support different
measurements of a task-relevant variable. Yet the word “support” covers
several distinct questions. Layerwise decodability does not establish that the
same decision rule remains usable across depths; direct readout reuse is
therefore a distinct empirical question. A readout trained at one depth may
transfer directly to another depth, fail under direct reuse while a low-capacity
recalibration restores some utility, or exhibit a model-specific pattern
across the source and target axes.

Prior work provides important neighboring tools and observations. Layerwise
decoding and tuned intermediate readouts make intermediate prediction
accessible [Belrose et al., 2023]. Model stitching and representation matching
study compatibility through learned transformations or similarity criteria
[Bansal et al., 2021; Csiszárik et al., 2021; Maiorca et al., 2023]. Work on
activation intervention and layerwise progression further motivates separating
what can be measured from what can be inferred [Li et al., 2023; Jiang et al.,
2024]. These studies do not make the present operational measurement
redundant: they motivate the distinction between direct reuse and restricted
recovery, but Paper A does not claim a new probing, alignment, or
representation-similarity method.

The gap addressed here is narrower. Aggregate transfer or degradation scores
can hide whether compatibility is organized primarily by source depth, target
depth, distance between depths, or a mixture that differs by model. A recovery
score can also be mistaken for evidence that direct compatibility was merely a
calibration problem. When direct reuse degrades, a separate question is
whether utility can be restored by a deliberately low-capacity calibration
without turning the measurement into a general adapter-fitting problem. We
therefore ask: when a task readout is fit at one decoder depth and applied
without retraining at another depth, how do direct operational compatibility,
degradation, and restricted FIT-only recovery vary across depth and across the
three tested language models?

Our measurement is deliberately bounded. For every directed source-target pair,
we preserve the source readout and evaluate it at the target. We define `C0`
as direct fixed-readout compatibility, `D` as degradation relative to the
source-layer self condition, and `R` as recovery under a registered
featurewise FIT-only calibration diagnostic. The full source-target matrix is
the operational object. Normalized depth distance, a source/target dominance
index (SDI), and a LOW-D recovery statistic provide complementary summaries;
none is treated as a latent-space coordinate or a causal description.

This distinction matters for interpreting layerwise probes, readout
portability, and representation comparisons. Reporting only direct
compatibility could support the statement that a fixed source readout is not
directly reusable. Reporting only recalibrated performance could support the
statement that utility is recoverable after restricted recalibration. Direct
reuse and restricted recoverability answer different operational questions;
reporting only one can hide the distinction between immediate readout
portability and limited recalibratability. `R` is not an estimate of best
possible alignment, best possible adapter performance, or general
transformation capacity.

We use “empirical dissociation” only to denote non-identical joint operational
profiles across the measured quantities; it does not imply statistical
independence, orthogonality, or distinct latent factors. The main result is a
three-model empirical dissociation. Distance-associated degradation is
supported in Qwen3-1.7B, OLMo-2-1B-Instruct, and Meta-Llama-3.2-1B-Instruct,
but the model profiles are not identical. Qwen is target-dominant and does not
support the registered LOW-D recovery summary; OLMo is source-dominant with
supported LOW-D recovery; Llama is target-dominant with supported LOW-D
recovery. The earlier evidence chain constrains how this profile should be
read: EXP-023 reports `NO_REPLICATION` across complementary splits, while
EXP-024 and EXP-025 do not support a simple separate degradation-based
predictor. A post-closure centered linear CKA analysis provides a secondary
association with `C0`, but does not replace the directed analysis.

The paper makes exactly three contributions:

1. **Measurement decomposition:** distinguish direct fixed-readout
   compatibility from restricted FIT-only recoverability under a registered
   source-target protocol.
2. **Empirical characterization:** characterize model- and depth-dependent
   operational profiles across three tested decoder-only language models.
3. **Evidence structure:** report directed matrices, split/condition
   heterogeneity, registered negative evidence, and bounded exploratory
   directional asymmetry.

The claims are bounded to the tested models, carrier, task panel, and
registered conditions. Decodability or representation-level manipulability is
not treated as a behavioral consequence; behavioral consequence is a separate
question outside the present fixed-readout evidence.

## 2. Related Work

### 2.1 Layerwise probing and readout transfer

Layerwise probing asks what a representation makes decodable at different
depths. Tuned Lens is a direct neighboring example: it fits layer-specific
affine readouts for intermediate predictions [Belrose et al., 2023]. Paper A
does not claim novelty for layer-specific readouts. Its contrast is between
direct reuse of a fixed source readout and a deliberately restricted FIT-only
calibration diagnostic. The source readout is held fixed during the direct
transfer measurement, so the question is operational reuse rather than the
best decoder available at each layer.

### 2.2 Logit-based inspection and activation transfer

Logit Lens-style inspection and related activation-transfer approaches expose
information through intermediate states [nostalgebraist, 2020]. The original
Logit Lens source is an online technical post rather than a peer-reviewed
paper. Patchscopes provides a broad framework for inspecting and intervening
on hidden representations [Ghandeharioun et al., 2024]. These approaches
establish useful interfaces for asking layerwise questions, but Paper A does
not claim novelty for hidden-state inspection or intervention. The present
unit is a source-target readout measurement with a fixed task classifier and
explicit held-out evaluation.

### 2.3 Stitching, affine alignment, and representation matching

Model stitching and representation matching compare networks through learned
maps, correspondence procedures, or similarity measures [Bansal et al., 2021;
Csiszárik et al., 2021]. Latent-space translation similarly studies learned
cross-representation transformations [Maiorca et al., 2023]. Paper A is a
within-model, cross-depth study and does not introduce affine alignment, a
general adapter, or a transport method. Its restricted calibration is a
low-capacity diagnostic endpoint, not a general alignment procedure. Related
caution about functional success and representation equivalence is also prior
art [Smith et al., 2025].

### 2.4 Similarity measures and layerwise progression

Representation-similarity measures and studies of layerwise progression
provide complementary views of changing hidden states [Csiszárik et al.,
2021; Jiang et al., 2024]. Centered kernel alignment (CKA) was introduced as
a representation-similarity measure by Kornblith et al. [2019]. The present
manuscript includes centered linear CKA as a secondary descriptive comparison
after the
core measurements. CKA is not used to define `C0`, `D`, or `R`, and it is
symmetric by construction. Accordingly, it does not answer the directed
source-target question by itself. Paper A does not claim novelty for CKA, CCA,
SVCCA, or similarity analysis.

### 2.5 Readout/representation boundaries

SemRF is an arXiv preprint on residual-stream dynamics and semantic reference
frames [Gu et al., 2026]. ICR Probe studies cross-layer hidden-state dynamics
for hallucination detection [Zhang et al., 2025]; it is neighboring work, not
the present `C0`/`D`/`R` decomposition. Kniazev and Fijalkow study a fixed
source-layer probe evaluated at other target layers without retraining in a
structured world-model setting [Kniazev and Fijalkow, 2026]. This is prior art
for cross-layer frozen-probe transfer, although its task, model, and scientific
setting differ substantially from Paper A. Recent work on readout failure and
representation progression emphasizes that decodability, use in a model, and
representation comparison should not be collapsed into one construct
[freshhead2025localising; Huang and Chang, 2025]. The cited readout-failure
item is retained with its repository-recorded partial author verification; its
full author list requires final primary-source checking. SemRF and the
structured-world-model study are arXiv preprints, not presented here as
peer-reviewed or accepted work.

Paper A follows the same caution. It studies a fixed-readout operational
interface and a restricted recovery diagnostic, not semantic equivalence,
information flow, or a causal mechanism. The positioning boundary is
explicit: layer-specific readouts, frozen-probe transfer, affine feature
transfer, activation inspection, representation similarity, and reference-
frame drift are established areas of related work. The bounded delta here is
their combination in a registered within-model measurement: direct
fixed-readout compatibility, restricted FIT-only recovery, directed
source-target matrices, negative and non-replication evidence, and a
three-model operational profile.

## 3. Methods

### 3.1 Models, data, and carrier

The confirmatory panel contains three decoder-only language models:

| Model | Frozen identity | Blocks | Hidden size |
|---|---|---:|---:|
| Qwen | `Qwen/Qwen3-1.7B`, revision `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e` | 28 | 2048 |
| OLMo | `allenai/OLMo-2-0425-1B-Instruct`, revision `48d788eca847d4d7548f375ad03d3c9312f6139e` | 16 | 2048 |
| Llama | `Meta-Llama-3.2-1B-Instruct`, registered converted-model hash `1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f` | 16 | 2048 |

The core panel contains 1,760 records from 880 source families, four semantic
task classes, and ten registered surface conditions. FIT, DIAGNOSTIC, and EVAL
partitions are source-family disjoint. The frozen condition-panel dataset is
`experiments/exp024/data/exp024_condition_panel_frozen.json` with SHA-256
`46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`; its
condition specification has SHA-256
`a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954`.
The separate CKA asset authority records 640 uniquely ordered EVAL samples
with sample-order hash
`6ff5adb902c7bc691b078c73b3b267005fe37f74b6fd675ba1225d4f8971baea`.

The carrier is the last valid token at the decoder block output: the
post-block residual stream before model-level final normalization. Each logical
block is identified by its decoder-layer module output; the final normalized
state and language-model head are excluded from the pre-final carrier
definition. This is an observational carrier selected by the registered
implementation. It is not the whole representation and should not be read as
a semantic or geometric object.

### 3.2 Source and target depths

For a model with `L` decoder blocks, source and target indices range over
`0, ..., L-1`. Normalized depth is `d(l) = l/(L-1)`. A matrix entry at row `i`
and column `j` uses a readout fit at source depth `i` and a representation
measured at target depth `j`. Diagonal entries are source-layer self
conditions; off-diagonal entries are direct cross-depth reuse. Equal
normalized depths across models are not assumed to be functionally equivalent.

### 3.3 Fixed reference readout

Let `X_l` be the carrier matrix at depth `l` and `Y` the task labels. A source
readout is fit on the FIT partition at source depth `s`:

\[
W_s = f(X_s^{FIT}, Y^{FIT}).
\]

The classifier is multinomial `LogisticRegression` with `solver=lbfgs`,
`penalty=l2`, `C=1.0`, `fit_intercept=true`, `tol=1e-4`,
`class_weight=None`, `dual=false`, `max_iter=1000`, and
`warm_start=false`. It is fit on the source carrier and labels with no
hyperparameter search. For every target `t`, the same `W_s` is evaluated on
`X_t^{EVAL}`. Class order is taken from the fitted classifier's
`classes_` mapping.

There is no target-specific refit in the direct measurement. The restricted
recovery diagnostic uses featurewise `StandardScaler(with_mean=true,
with_std=true)` statistics estimated from FIT representations and retains the
registered reference classifier. Stronger adapter performance would answer a
different question from this deliberately restricted diagnostic.

### 3.4 Direct compatibility `C0`

`C0(s,t)` is the balanced-accuracy compatibility of the readout fit at source
depth `s` when evaluated on the target representation at `t` under each
condition. It is an operational score on the registered task panel. High `C0`
indicates that the fixed readout remains usable under this evaluation; it does
not establish preserved semantics, behavior, or a causal role for the
representation.

### 3.5 Degradation `D`

Let `Cself(s) = C0(s,s)`. We define direct degradation as

\[
D(s,t) = Cself(s) - C0(s,t).
\]

`D` is a readout-relative performance difference. It is not information loss,
semantic loss, geometric loss, or an estimate of what a model computes at a
layer. Positive `D` means lower target performance than the source self
condition under this fixed readout.

### 3.6 Restricted recovery `R`

The recovery endpoint applies the preregistered low-capacity featurewise
FIT-only calibration at the target and retains the registered reference
classifier. If `Ccal(s,t)` is the calibrated target score,

\[
R(s,t) = Ccal(s,t) - C0(s,t).
\]

`R` measures improvement under a restricted diagnostic operation. It is a
deliberately restricted diagnostic of limited recalibratability, not an attempt
to learn best possible alignment, a best possible adapter, or general
transformation capacity. It does not measure equivalence to the source
representation. All calibration parameters are fit on FIT data; EVAL data are
used to measure the resulting outcome.

### 3.7 Directed source-target matrices

For each model we retain the full matrix orientation. Rows correspond to the
source readout depth and columns to the target representation depth. This
orientation matters because `C0(s,t)` and `C0(t,s)` need not agree. Matrix
summaries preserve the distinction between source and target effects rather
than replacing a directed object with a single unordered similarity.

### 3.8 Normalized-distance association

For off-diagonal pairs we associate `D(s,t)` with absolute normalized depth
distance,

\[
\Delta(s,t) = |d(s)-d(t)|.
\]

The distance statistic is Spearman rank association using average ranks for
ties, implemented with `scipy.stats.spearmanr` and `nan_policy="raise"`.
Support requires a positive point estimate and a positive one-sided
cluster-bootstrap lower bound. It summarizes a relationship in the measured
matrix; distance is not claimed as a causal explanation.

### 3.9 Source/target dominance index

For each model, the source/target dominance index is

\[
SDI = \frac{V_{source}-V_{target}}{V_{source}+V_{target}},
\]

where `V_source` is the population variance (`ddof=0`) of off-diagonal row
means and `V_target` is the population variance of off-diagonal column means.
Negative SDI is classified as target-dominant and positive SDI as
source-dominant when the registered interval supports the sign. SDI is an
organization summary for the operational matrix. It is not evidence about
information flow or a representation geometry.

### 3.10 LOW-D statistic

LOW-D selects off-diagonal pairs using the registered `Dbar <= 0` mask. The
mask is created from DIAGNOSTIC quantities and held fixed for EVAL aggregation.
The EVAL estimand is the mean restricted recovery `R` over that mask. Support
requires a positive point estimate and a positive one-sided cluster-bootstrap
lower bound. This statistic asks whether recovery is observed in pairs that do
not show positive average degradation under the registered diagnostic mask. It
is conditional on that mask and is not a universal recovery guarantee.

### 3.11 Model-level profile

Each model profile contains three registered components: distance-associated
degradation, SDI source/target organization, and LOW-D recovery support. The
profile is reported as a joint descriptive summary. It is not a claim that
these components are statistically independent or that they correspond to
separate latent factors.

### 3.12 Prospective third-model routing

Qwen and OLMo results were already available when the initial descriptive
comparison was formed. Their profiles happened to align in the initial
two-model comparison, but two profiles were insufficient to determine whether
that pattern would persist. A third model was therefore routed prospectively
before Llama result exposure because the initial descriptive association
between source/target organization and LOW-D recovery required another tested
profile. Llama's exact profile was not prospectively predicted. After result
exposure, the interpretation that Llama breaks the simple two-model mapping is
a bounded post-hoc synthesis, not a universal taxonomy.

### 3.13 Statistical inference

The core profile intervals are condition-stratified source-family cluster
bootstrap intervals. The EVAL source-family cluster is the resampling unit;
FIT-fitted classifiers and FIT-only calibration statistics remain fixed. The
bootstrap uses 5,000 replicates, `numpy.random.PCG64(20260819)`, 95% intervals,
and `numpy.percentile(..., method="linear")`. A positive one-sided lower bound
uses the fifth percentile; a negative one-sided upper bound uses the 95th
percentile. No row-wise or cell-wise bootstrap is used.

The LOW-D pair mask is computed once from the original DIAGNOSTIC records and
held fixed across bootstrap replicates; mean EVAL `Rbar` is recomputed on
resampled EVAL records. EXP-024 and EXP-025 use their registered exact
one-sided permutation tests for the condition-level predictor. We do not pool
models into an inferential sample. The inferential unit and resampling unit
remain those fixed by each preregistration.

### 3.14 Reproducibility and leakage controls

The analysis binds model identity, snapshot or converted-model identity,
runner, dataset, split, layer mapping, carrier, and authority hashes. The
primary authority pointers are `experiments/exp026/EXP-026-PREREGISTRATION.md`,
`experiments/exp026/EXP-026-LAYER-CARRIER-MAPPING.md`, and
`experiments/exp026/EXP-026-MATRIX-METRIC-SPECIFICATION.md`; the model-specific
third-profile result is `experiments/exp027/results/exp027_results.json`.
Canonical result artifacts are
`experiments/exp022a/results/exp022a_results.json`,
`experiments/exp023/results/exp023_results.json`,
`experiments/exp024/results/exp024_results.json`,
`experiments/exp025/results/exp025_results.json`,
`experiments/exp026/results/exp026_results.json`, and
`experiments/exp027/results/exp027_results.json`.

FIT, DIAGNOSTIC, and EVAL source families are disjoint in the condition panel.
Calibration uses FIT data only. Direct source readouts are not retrained on
EVAL data. No result-driven layer or condition selection is used. These
settings, the dataset/panel hashes above, and the canonical artifact paths
provide the compact main-text reproduction pointer; full authority records
remain the source of exact provenance.

## 4. Results

### 4.1 Distance-associated degradation is shared across the tested panel

All three tested models meet the registered positive-support rule for the
distance association. The values below are the canonical continuous
statistics, not a re-computation performed for this manuscript.

| Model | Distance statistic | One-sided 95% cluster-bootstrap CI | Registered status |
|---|---:|---|---|
| Qwen3-1.7B | 0.7049462571528698 | [0.6851830380886905, 0.7080622074980855] | `POSITIVE_SUPPORTED` |
| OLMo-2-1B-Instruct | 0.7519250367843754 | [0.7438987161061725, 0.7582397801058931] | `POSITIVE_SUPPORTED` |
| Meta-Llama-3.2-1B-Instruct | 0.6077483252598234 | [0.5949008758383216, 0.6154160155280691] | `POSITIVE_SUPPORTED` |

The common sign is a panel-bounded descriptive result: larger normalized
source-target separation is associated with larger fixed-readout degradation
under the tested carrier and task panel. The point estimates differ, and the
shared status does not imply equal magnitudes or a common layerwise law.

### 4.2 Negative evidence limits a uniform recovery interpretation

The discovery and replication sequence limits an interpretation in which
direct failure is uniformly removable by calibration. EXP-022A reported
split-dependent degradation and recovery. EXP-023 was the separate
preregistered replication, with registered outcome `NO_REPLICATION`: restricted
recalibration did not replicate uniformly across complementary splits. This
is evidence of split heterogeneity, not evidence that recovery is absent in
every setting.

EXP-024 tested whether a separate diagnostic degradation magnitude would rank
later calibration benefit. Its registered result was `NOT_SUPPORTED`, with
`rho = 0.28401877872187725` and exact one-sided permutation
`p = 0.2115079365079365`. EXP-025 repeated the panel on OLMo-2-1B-Instruct;
its registered route was `D-_G+`, indicating cross-model heterogeneity in
degradation/recovery, while its separate predictor remained unsupported
(`rho = 0.3765432098765432`, exact permutation
`p = 0.14020502645502644`). These results retain their epistemic role in the
main argument while detailed condition histories remain in the supplement.

### 4.3 Source and target organize the profiles differently

The SDI values show that the common distance association does not determine a
single source/target organization.

| Model | SDI | One-sided 95% cluster-bootstrap CI | Classification |
|---|---:|---|---|
| Qwen3-1.7B | -0.17355352410373298 | [-0.18868527431441903, -0.15827487462584097] | `TARGET_DOMINANT` |
| OLMo-2-1B-Instruct | 0.5249651786448143 | [0.49101491890702714, 0.5584696075004959] | `SOURCE_DOMINANT` |
| Meta-Llama-3.2-1B-Instruct | -0.41426422986393563 | [-0.4342173411679606, -0.39239628027572504] | `TARGET_DOMINANT` |

Qwen and Llama therefore have negative target-dominant SDI values, whereas
OLMo has a positive source-dominant value. This comparison is a statement
about organization of the measured source-target matrix. It does not identify
why the models differ, and it does not turn source/target dominance into a
directional process.

### 4.4 LOW-D recovery is model-dependent

The LOW-D recovery estimand produces a different split across models.

| Model | LOW-D mean recovery | One-sided 95% cluster-bootstrap CI | Status |
|---|---:|---|---|
| Qwen3-1.7B | 0.00013923267534205524 | [-0.00009933156284070251, 0.00036107659009100833] | `NOT_SUPPORTED` |
| OLMo-2-1B-Instruct | 0.04785714308465166 | [0.044028989621438086, 0.0515186088984566] | `SUPPORTED` |
| Meta-Llama-3.2-1B-Instruct | 0.0014030612453970375 | [0.0007325690004461426, 0.002186791592619705] | `SUPPORTED` |

The Qwen interval crosses zero, while the OLMo and Llama intervals are
positive under the registered LOW-D rule. The support labels should not be
read as equal recovery magnitudes: the Llama point estimate is much smaller
than OLMo's, despite sharing the categorical support label.

### 4.5 Prospective Llama routing and bounded synthesis

The initial two-model comparison contained Qwen target-dominant with
unsupported LOW-D recovery and OLMo source-dominant with supported LOW-D
recovery. Llama was routed prospectively before its result was exposed. Llama
exhibits a combination not present in the initial two-model comparison:
target-dominant organization together with supported LOW-D recovery. This
breaks the simple descriptive mapping suggested by the initial two tested
models. The interpretation is a bounded post-hoc synthesis of a prospectively
routed third profile; it is not evidence for a universal taxonomy.

The joint profile is:

| Model | Distance association | SDI organization | LOW-D recovery |
|---|---|---|---|
| Qwen3-1.7B | positive, supported | target-dominant | not supported |
| OLMo-2-1B-Instruct | positive, supported | source-dominant | supported |
| Meta-Llama-3.2-1B-Instruct | positive, supported | target-dominant | supported |

The shared distance-associated result coexists with different organization and
restricted recovery profiles in the tested panel. A single scalar score does
not capture all of this measured source/target and recovery variation.

### 4.6 Secondary CKA comparison

CKA was added only after core science closure to ask whether a symmetric
representation-similarity measure covaried with the completed operational
measurements, not to redefine them. As a post-closure secondary analysis,
centered linear CKA was computed on the EVAL split for 640 samples per model
using the same post-block residual carrier before final normalization. The
model-wise off-diagonal comparisons were:

| Model | Spearman(CKA, `C0`) | Spearman(CKA, `D`) | Spearman(CKA, `R`) |
|---|---:|---:|---:|
| Qwen | 0.8372 | -0.8373 | -0.6738 |
| OLMo | 0.7589 | -0.8082 | -0.3729 |
| Llama | 0.7706 | -0.7634 | -0.5189 |

Across the three models, CKA has a strong positive descriptive association with
direct fixed-readout operational compatibility, while its associations with
degradation and restricted recovery are negative. These are comparisons of
completed measurements on the EVAL split. Because CKA is symmetric by
construction, it does not replace the directed source-target compatibility
analysis. Full CKA asset and comparison details belong in the supplement.

## 5. Discussion

### 5.1 Direct reuse and restricted recovery answer different questions

The central distinction is operational. `C0` asks whether a readout trained at
one depth can be used at another depth without retraining. `R` asks whether a
specific low-capacity FIT-only calibration improves that target measurement.
Restricted recovery was designed as a diagnostic of limited recalibratability,
not as an attempt to learn the best possible cross-depth transformation. A
stronger adapter would answer a different question and would not be a
replacement for this endpoint. The observed profiles show why these endpoints
should be reported separately.

### 5.2 Model-dependent organization is part of the result

The cross-model comparison is not a search for one preferred profile. OLMo's
source-dominant SDI contrasts with the target-dominant Qwen and Llama values.
OLMo and Llama meet the LOW-D support rule, whereas Qwen does not. The Llama
profile also shows why a two-model descriptive mapping would be too narrow.
These differences are empirical properties of the tested panel. Architecture,
training history, and implementation details are possible subjects for future
hypotheses, not explanations established by these data.

### 5.3 Frozen-readout failure has a limited interpretation

Failure of a frozen source readout identifies an operational interface mismatch
under that readout, not the absence of every task-relevant signal at the target
depth. Lower `C0` is compatible with readout-relative incompatibility, changes
in the measured carrier, or both. Recovery under a restricted procedure does
not prove source-target equivalence, and failure of recovery does not prove
that a task-related signal is absent. The paper thus uses “operational
compatibility” rather than an unqualified claim about what a layer contains.

### 5.4 Directionality and CKA have complementary roles

The directed matrices permit an exploratory comparison of `C0(s,t)` and
`C0(t,s)`. Directionality is reported as a descriptive secondary observation;
it is not interpreted as information flow or causal direction. CKA supplies a
symmetric representational-similarity comparison. Its positive relationship
with `C0` is useful context, but symmetry means that it does not encode which
layer supplied the readout and which layer supplied the target representation.

### 5.5 Implications for measurement design

For probe portability and layerwise monitoring, the methodological implication
is to report source and target axes, direct reuse, calibration status, and
model identity together. A readout that transfers well at one depth pair does
not establish broad portability. A calibration that improves a restricted
endpoint does not establish a general adapter. These observations motivate
measurement designs that preserve direction, split provenance, and the
distinction between primary and diagnostic endpoints.

## 6. Limitations

The evidence is bounded in several ways.

1. The panel contains three tested language models. The results do not support
   architecture-wide or universal claims.
2. The models are approximately 1B-class, with model-family and training-history
   differences that are not experimentally separated.
3. The carrier is one post-block, pre-final-normalization, last-valid-token
   extraction. It does not represent every token, layer signal, or model
   interface.
4. The profile properties are jointly reported, but no statistical independence
   among them is established.
5. The design does not provide a mechanism or causal decomposition of
   layerwise change.
6. Restricted recalibration is a deliberately low-capacity FIT-only diagnostic,
   not general learned adapter alignment.
7. Cross-task and task-panel robustness is `NOT_ESTABLISHED`.
8. Directionality is exploratory and secondary; it is not a causal account.
9. CKA is a secondary similarity comparison and does not establish semantic,
   information, or geometric equivalence.
10. The study demonstrates no practical or industry impact beyond the tested
    measurement setting.
11. Distance-associated cross-layer structure is measured here but is not
    presented as a new distance law.

These limitations are part of the claim boundary. In particular, the paper
does not claim semantic equivalence, representational equivalence, persistent
task coordinates, causal computation, behavioral control, or cross-task
universality.

## 7. Conclusion

Across three tested language models, fixed-readout compatibility shows a shared
positive distance-associated structure but non-identical source/target
organization and restricted recovery profiles. The registered negative and
non-replication results prevent a uniform calibration interpretation, while
the secondary CKA comparison provides descriptive context without replacing
the directed operational measurement. Paper A therefore contributes a scoped
empirical dissociation of direct fixed-readout compatibility and restricted
recoverability, with claims limited to the tested carrier, panel, models, and
conditions.

## Figures and Tables

### [FIGURE 1 HERE] — Operational measurement framework

Show a FIT-trained source readout applied to every target depth, with separate
branches for direct `C0`, degradation `D`, and restricted FIT-only recovery
`R`. Mark source/target orientation and the boundary between measurement and
interpretation. The figure should not depict a latent space or a causal flow.

### [FIGURE 2 HERE] — Three-model operational profiles

Use four panels: distance-associated degradation with canonical intervals; SDI
source/target organization; LOW-D recovery with canonical intervals; and the
registered profile/routing summary. Keep continuous values visible alongside
categorical statuses.

### [FIGURE 3 HERE] — Full directed source-target matrices

Show the model-specific directed matrices with source depth on rows and target
depth on columns. State that matrix orientation is operational and that
cross-direction asymmetry is exploratory.

### [TABLE 1 HERE] — Canonical three-model profile

Include distance statistic and interval, SDI statistic and interval with
source/target class, and LOW-D mean and interval with support status.

### [TABLE 2 HERE] — Evidence and claim hierarchy

| Evidence layer | Registered observation | Manuscript role |
|---|---|---|
| Positive shared structure | Distance-associated degradation supported in all three tested models | Registered cross-model result, panel-bounded |
| Restricted recovery | LOW-D support differs by model | Registered profile result |
| Source/target organization | Qwen and Llama target-dominant; OLMo source-dominant | Registered heterogeneity result |
| Negative evidence | EXP-023 `NO_REPLICATION`; EXP-024 predictor `NOT_SUPPORTED`; EXP-025 predictor unsupported | Registered boundary evidence |
| Prospective triangulation | EXP-027 yields a third profile that breaks a simple two-model mapping | Bounded synthesis |
| Secondary similarity | CKA is positively associated with `C0` in each model | Secondary supporting analysis |
| Not established | Cross-task robustness, semantic equivalence, geometry, mechanism, information flow, and causality | Explicit claim firewall |

## Reproducibility and Evidence Note

The manuscript's numerical values are transcribed from the version-controlled
EXP-022A, EXP-023, EXP-024, EXP-025, EXP-026, and EXP-027 result artifacts,
the validated Paper A scientific asset register, and the continuous-magnitude
audit. CKA values are transcribed from the validated PA-CKA comparison
summary. The local bibliography is `docs/paper/references.bib`; its
verification record is `docs/paper/PAPER-A-REFERENCE-VERIFICATION.md`. The
bibliography entry for the fresh-head probe paper remains partial pending
final author-list verification. No model inference, new experiment, or new
statistic was performed for this manuscript draft.

## AI Use Statement — Draft for Author Verification

**AUTHOR_VERIFY**

AI assistance contributed to ideation and hypothesis refinement, experimental
and method-design feedback, code assistance, result interpretation, literature
discovery and summarization, and manuscript organization and drafting during
the project. The canonical scientific results in this manuscript come from
version-controlled experiment artifacts and validated machine-readable
authorities, not from LLM assertions. AI suggestions are not scientific
authority. Human authors remain responsible for checking every citation,
number, interpretation, disclosure requirement, and final claim before
submission.

## References

Reference keys and bibliographic metadata are maintained in
`docs/paper/references.bib`. The manuscript uses the locally verified entries
for Tuned Lens, model stitching, representation matching, latent-space
translation, functional-alignment caution, inference-time intervention,
layerwise progression, and decodability-versus-causal-role boundaries. The
following six entries were added from the externally verified identities
provided for this revision:

- nostalgebraist. “interpreting GPT: the logit lens.” LessWrong / AI
  Alignment Forum, 2020. Online technical/blog source; not peer reviewed.
- Asma Ghandeharioun, Avi Caciularu, Adam Pearce, Lucas Dixon, and Mor Geva.
  “Patchscopes: A Unifying Framework for Inspecting Hidden Representations of
  Language Models.” Proceedings of the 41st International Conference on
  Machine Learning, PMLR 235:15466–15490, 2024.
- Simon Kornblith, Mohammad Norouzi, Honglak Lee, and Geoffrey Hinton.
  “Similarity of Neural Network Representations Revisited.” Proceedings of
  the 36th International Conference on Machine Learning, PMLR 97:3519–3529,
  2019.
- Jian Gu, Aldeida Aleti, Chunyang Chen, and Hongyu Zhang. “SemRF: A Semantic
  Reference Frame for Residual-Stream Dynamics in Language Models.”
  arXiv:2606.32022, 2026. arXiv preprint.
- Zhenliang Zhang, Xinyu Hu, Huixuan Zhang, Junzhe Zhang, and Xiaojun Wan.
  “ICR Probe: Tracking Hidden State Dynamics for Reliable Hallucination
  Detection in LLMs.” Proceedings of the 63rd Annual Meeting of the
  Association for Computational Linguistics (Volume 1: Long Papers),
  17986–18002, 2025. DOI: 10.18653/v1/2025.acl-long.880.
- Roman Kniazev and Nathanaël Fijalkow. “Transformers Linearly Represent
  Highly Structured World Models.” arXiv:2605.18847, 2026. arXiv preprint.

The local citation record for the fresh-head probe paper remains partial
pending full author-list verification.
