# Research Audit v1 — Construction–Evaluation Independence

## Scope and verdict

This is a red-team audit of EXP-001 through EXP-016 and the EXP-017
preregistration. It evaluates whether the construction of an intervention,
metric, or selection rule is independent of the evidence used to validate it.
It does not rerun either model and it does not alter historical code or
results.

**Overall severity: HOLD_BEFORE_BEHAVIOR.** The present record is adequate for
describing small-prompt representation geometry and for demonstrating an
operational vector-arithmetic property. It is not adequate for claims that
centroid steering independently achieves a task transition, preserves a
relational invariant, identifies functional layer roles, or motivates a full
generation-time behavioral study. The EXP-017 hook diagnostic may proceed as
an implementation diagnostic only; a behavioral effect study should wait for
construction-independent validation.

The critical issue is structural rather than a numerical error: several
steering outcomes are evaluated on the same representations used to estimate
both the source/target centroids and the steering vector.

## A. Claim-to-evidence trace

| Claim family | Origin and exact result | Construction independent of evaluation? | Support level | Audit finding |
|---|---|---|---|---|
| Qwen task-associated geometry | EXP-001/002/003; controlled EXP-003 separation peaked at layer 16, 0.073015, silhouette 0.182165, paraphrase-retention 0.036424. | No train/test split, but these are descriptive statistics rather than fitted-predictive claims. | partially_supported | A 24-prompt hand-designed sample has group structure; scope is narrow. |
| Qwen non-monotonic layer profile | EXP-002/003 layer curves; layer 16 was the reported peak for several Qwen metrics. | Descriptive, same fixed prompt set. | partially_supported | A sampled-layer pattern exists on this prompt set; it is not a general layer law. |
| Mid-/mid-deep geometry peak | EXP-003 Qwen peak at 16; EXP-013 Gemma best separation/retention at final layer 26, while silhouette peaked at 16. | Same 24 controlled prompts in both models. | contradicted | Cross-model evidence fails the claimed common mid-depth peak. |
| Cross-model geometry replication | EXP-013: Gemma separation 0.093294 at L26, silhouette 0.139718 at L16, retention 0.071401 at L26; positive controlled signals across late layers. | Same designed dataset, new model family. | partially_supported | Replicates an operational geometry signal in a second model, not its peak location or broad generality. |
| Centroid steering can achieve task transition | EXP-004B/005/006, then EXP-014: target assignment rises and reaches 1.0 for pairs at suitable beta. | **No.** Centroids and deltas are estimated from the evaluated source representations; classifier uses those same centroids. | operational_only | This demonstrates an in-sample translation toward a constructed target centroid, not independent task conversion. |
| Multi-pair calibrated transition | EXP-005 Qwen and EXP-014 Gemma: all 12 ordered pairs eventually reached assignment 1.0. | No; same coupling for every pair. | operational_only | The multi-pair count repeats the same construction check twelve times; it is not twelve independent validations. |
| Qwen beta-0.75 validity frontier | EXP-007: 12/12 pairs selected beta 0.75; mean assignment 1.0, IVS 0.002850, RSM Pearson 0.997150. | No; EXP-007 reselects from EXP-006 in-sample CSVs. | unsupported | It is a post hoc operating point on the data that generated the direction and metric. |
| RSM/IVS measures relational preservation | EXP-006/014 report high RSM Pearson and low IVS under steering. | No matched-norm random-direction or held-out RSM control was run. | unsupported | It is a cosine-RSM change proxy, not a demonstrated relational invariant. |
| Assignment–preservation tradeoff | EXP-006/014: assignment rises with beta while IVS rises and RSM Pearson falls. | Curves are in-sample and both axes depend on the same common translation. | partially_supported | A descriptive tradeoff exists for this metric construction; its scientific interpretation is not independent. |
| Invariant-constrained selection is robust | EXP-008: 23/24 penalty settings selected mean beta 0.75. | No; all settings reuse EXP-006 outputs. | operational_only | Robustness to a family of post hoc scalarizations is not independent validation. |
| Encoding/control/safe layer roles | EXP-015/016: Qwen encoding/control L16, mean-safe L4@1; Gemma encoding L26, control/safe L16@0.75. | No; roles are extrema/threshold selections on the same 24 prompts and steering grid. | operational_only | These are useful labels for the fixed rules, not evidence of distinct functional modules. |
| Layer-role separation across models | EXP-016 classifies separation as supported; normalized control depths are 0.571 (Qwen) and 0.615 (Gemma). | Same construction and sampled grid in each model. | partially_supported | The selected summaries differ within models; causal or functional interpretation is unsupported. |
| Representation–behavior relation | EXP-010 had four-group exploratory correlations; EXP-012 changed rankings and two signs when frozen EXP-011D behavior replaced EXP-009 behavior. | No held-out prediction; n=4 groups. | contradicted | A stable explanatory relation does not survive benchmark substitution. |
| Behavioral baseline | EXP-011D frozen rescoring: 60/80 = 0.750; causality .950, definition .850, logic .750, analogy .450. | Separate frozen answer benchmark; no steering yet. | partially_supported | This is a useful audited baseline, subject to finite-answer scoring limits. |
| Generation-time steering affects behavior | No completed behavioral intervention experiment. | Not applicable. | unknown | No result exists. EXP-017 is design-only. |

## B. Centroid-steering construction audit

The relevant scripts (`exp004b`, `exp005`, `exp006`, `exp014`, `exp015`, and
`exp016`) implement the same core operation. For a source group (s), target
group (t), and their centroids computed from a representation matrix,

\[
\delta_{s,t}=c_t-c_s, \qquad h'=h+\beta\delta_{s,t}.
\]

At `beta = 1`, the mean of the steered source representations is exactly the
original target centroid:

\[
\operatorname{mean}(h'_s)=c_s+(c_t-c_s)=c_t.
\]

The classifier is `nearest_centroid_labels`, which assigns by cosine similarity
to the original group centroids. Thus it evaluates source examples whose mean
has been constructed to equal one of its evaluation prototypes. The same 24
EXP-003 representations are used to fit `c_s`, `c_t`, and `delta`, and to
measure source-to-target assignment, target-minus-source cosine, and RSM.

This does not make every individual source point equal to `c_t`, and cosine
classification prevents an algebraic guarantee that every point is assigned to
the target. It nevertheless builds a strong target advantage into the outcome.
The fraction of observed assignment success attributable to this construction
cannot be quantified from the existing outputs because there is no held-out
centroid fit, alternative classifier, or matched-norm direction control.

**Finding: direct transition success is an in-sample operational construction
check, not independent evidence of task conversion.** The correct limited
statement is: *adding a target-minus-source centroid vector moves the source
group mean to the target centroid and can change nearest-centroid labels on the
same representation sample.*

## C. RSM/IVS audit and deterministic sanity check

`src/invariants.py` constructs an uncentered cosine RSM, takes its upper
triangle, computes Pearson (and optionally Spearman) correlation before versus
after, and defines `IVS = 1 - Pearson`. It also reports a Frobenius distance.

For a common additive translation (h_i'=h_i+v) applied to every source item:

- Euclidean pairwise distances and difference vectors are exactly invariant.
- Dot products, norms, and pairwise cosine similarities are not invariant.
- A high correlation among upper-triangle cosine entries can occur when the
  shared vector affects all entries similarly or the translation is small
  relative to representation norms; it does not establish a semantic or
  task-relational invariant.

The deterministic, non-tuned sanity calculation is recorded in
`results/audit_v1/rsm_synthetic_sanity.csv`: six 64-dimensional synthetic
representations (seed `20260318`, within-group noise SD 0.3) received either a
centroid-directed translation, an equal-norm random translation, an orthogonal
rotation, or anisotropic scaling. Results were:

| Transform | RSM Pearson | IVS |
|---|---:|---:|
| centroid-directed translation | 0.987489 | 0.012511 |
| equal-norm random translation | 0.984560 | 0.015440 |
| orthogonal rotation | 1.000000 | 0.000000 |
| anisotropic scaling | 0.855485 | 0.144515 |

This is a mathematical sanity example, not a calibration to historical model
results. It shows why low IVS is compatible with a generic shared translation.
No historical experiment tests whether the reported low IVS exceeds a
matched-norm random-vector baseline. Therefore the claim that low IVS is
direction-specific relational preservation is **unsupported**.

## D. Independence and reuse table

| Analysis | Direction/selection fitting data | Evaluation data | Independence judgment |
|---|---|---|---|
| EXP-001/002/003 geometry | None; descriptive summaries of 12/24 prompts | Same prompts | descriptive_only |
| EXP-004B | EXP-003 24 representations: centroids and delta | Same source representations and centroids | fully_in_sample |
| EXP-005/006 | Same 24 representations per ordered pair | Same source representations, centroids, and RSMs | fully_in_sample |
| EXP-007/008 | Existing EXP-006 in-sample rows, including beta grid | Same rows reused for frontier/penalty selection | fully_in_sample_reuse |
| EXP-013 | None; descriptive Gemma geometry on the same controlled prompt design | Same 24 prompts | descriptive_only_cross_model |
| EXP-014 | Gemma EXP-003 24 representations: centroids and delta | Same source representations, centroids, and RSMs | fully_in_sample |
| EXP-015/016 | Same 24 prompts; layer/beta grid and role criteria | Same grid selects and reports roles | fully_in_sample_selection |
| EXP-009/009B/011D | Frozen questions and answer rules; no centroid fitting | Generated answers on those questions | behavioral_baseline_only |
| EXP-010/012 | Group-aggregated representation summaries plus group behavior scores | Same four group aggregates; no fitted predictor holdout | n4_descriptive_reuse |

No historical centroid-steering result includes a held-out prompt split. No
historical IVS result includes a matched-norm random steering control. Reuse of
the same 24 prompts propagates into EXP-004B through EXP-016, including the
beta and layer selection analyses.

## E. What exactly are the EXP-015/016 roles?

In EXP-016, `encoding` is the sampled layer maximizing the geometry tuple
`(separation, paraphrase retention, silhouette)`. `control` is the lowest-beta
row reaching mean assignment >= 0.9. `safe` is the threshold-eligible row with
minimum mean IVS; `efficient` maximizes assignment / relative perturbation;
`best validity` maximizes `assignment - IVS - 0.1 * perturbation`. These are
clear operational definitions, and the full EXP-016 grid was fixed before that
run. EXP-015 was a narrower pilot with analogous fixed rules.

However, the broader role vocabulary was developed after the earlier geometry
and steering sequence, and all selection criteria act on the same 24 prompts
and the same centroid-derived outcomes. The terms therefore must be separated:

| Label | Defensible audit wording | Not established |
|---|---|---|
| encoding layer | sampled layer with the largest chosen controlled-geometry score | a layer that encodes a cognitive task variable |
| control layer | sampled layer/beta satisfying the predefined in-sample centroid-assignment rule | a causal control module |
| mean-constrained safe-control | threshold-eligible setting with minimum **mean** cosine-RSM IVS | robust safety, per-prompt safety, or behavioral preservation |
| validity / efficient layer | winner of an exploratory scalar rule on this grid | a scientifically validated optimal intervention point |

Qwen's EXP-016 `L4 @ beta 1.0` is explicitly **mean-constrained**, not
pairwise robust: mean assignment was 0.917 while its minimum pair assignment
was 0.667. Calling it simply “safe” would overstate the result.

## F. Selection and multiplicity risk

The record contains sequential exploration: selected Qwen layer 16 became the
steering layer; EXP-007 chose beta 0.75 from EXP-006; EXP-008 scanned 24
lambda/gamma settings; EXP-015 piloted selected layers; EXP-016 expanded the
grid after that pilot. The individual scripts often label their own grid or
criteria as fixed, but that does not make the overall research sequence
independent of prior observed results.

| Result family | Audit category | Reason |
|---|---|---|
| EXP-001 to EXP-008 Qwen geometry, steering, frontier, constraint scans | exploratory / post_hoc_selection | Choices and scalarizations were iterated on the same prompt family. |
| EXP-009/009B and EXP-011D behavioral baselines | exploratory, then audited/frozen | The final benchmark is improved, but answer-set rescoring changed accuracy from .650 to .750. |
| EXP-013 Gemma geometry | preregistered_followup with exploratory antecedents | New model is valuable, but prompt design and comparison targets came from Qwen work. |
| EXP-014 Gemma steering | preregistered_followup with construction coupling | Cross-family rerun does not remove in-sample centroid evaluation. |
| EXP-015/016 role studies | preregistered_followup after exploratory pilot | Per-run grids were fixed, but role framing and layer range followed previous outputs. |
| EXP-017 | preregistered_design_only | Conditions and random controls are frozen before its behavioral outcome, but layers/directions arose from the prior coupled analyses. |

## G. Representation–behavior assessment

The strongest final behavioral source is EXP-011D: 60/80 correct (.750), with
causality .950, definition .850, logic .750, and analogy .450. That is a
behavioral baseline, not evidence about representation causation.

EXP-010 linked four group-level representation summaries to four group
accuracies. EXP-012 substituted the frozen EXP-011D behavior vector: two
correlations (`mean_incoming_final_ivs` and
`mean_incoming_final_rsm_pearson`) changed sign; the largest absolute change
was 0.5112. EXP-012's strongest positive Pearson was only .3985 and strongest
negative was -.9056, both with `n = 4`. A four-point correlation cannot support
reliable inference, and no held-out predictive test exists.

**Finding:** the proposition that geometry/steering metrics explain behavioral
difficulty is unsupported; a stable descriptive relation is contradicted by
benchmark sensitivity. It remains possible that a relationship exists, but
the current evidence does not identify one.

## H. EXP-017 preregistration audit

Strengths: it freezes the 80-item EXP-011D benchmark, short deterministic
generation, a zero-intervention baseline, three specified real conditions,
matched-norm random-vector controls, an opposite-direction subset, and a
stop rule. It also correctly labels L4 as only mean-safe and requires a
pre-generation KV-cache hook diagnostic.

Risks that remain:

- Task directions use raw centroid differences estimated from EXP-003's 24
  raw plain-text prompts, while behavioral prompts follow the EXP-011B prompt
  path (including its chat-template policy). This is a distribution and
  tokenization-context mismatch.
- The real directions and operating points remain products of the coupled,
  in-sample representation evidence above. Random controls test generic
  perturbation during generation, but cannot retroactively validate the
  representation-level frontier.
- The outcome is source-group accuracy. Decreasing it is explicitly not task
  conversion; without an independently defined target-task behavioral outcome,
  “conversion” cannot be inferred.
- The opposite-direction condition covers only 20 fixed items and has less
  precision than the main comparisons.

**Readiness judgment:** `READY_FOR_HOOK_DIAGNOSTIC`; **not ready for a full
behavioral-effect interpretation**. A behavioral experiment may be described
only as a fixed pilot testing real versus matched-norm random perturbations,
not as a confirmation of safe control or task transition.

## I. Required claim downgrades

| Current term | Maximum defensible wording |
|---|---|
| task transformation | in-sample movement of a source representation mean toward a target centroid, with nearest-centroid label changes |
| relational invariant | cosine-RSM correlation proxy under a shared additive perturbation |
| validity frontier | exploratory in-sample scalar operating-point summary |
| safe-control | mean-constrained low-IVS, threshold-eligible setting; not robust safety |
| cross-model replication | two-model replication of some descriptive controlled-geometry and vector-arithmetic patterns |
| functional layer role | operational winner of a fixed sampled-grid rule |
| behavioral relevance | unknown; current four-group descriptive links are benchmark-sensitive |

## J. Decisive audit questions

1. **Is centroid-steering success substantially built in?** Yes. At beta 1 the
   source mean is exactly the target centroid, and assignment is evaluated
   against the centroids fitted from the same representations. It is not a
   pointwise algebraic guarantee, but it is a critical construction-evaluation
   coupling.
2. **Could low IVS largely follow from common translation?** Yes, plausibly.
   The deterministic sanity table shows matched-norm random translation can
   also yield a very high cosine-RSM correlation. Existing data cannot assign a
   percentage of the observed effect to this mechanism.
3. **What survives as independent evidence?** Narrow descriptive group geometry
   in two model families; non-monotonicity on the fixed prompt design; and the
   mathematical fact that centroid-vector addition moves a group mean. None
   independently establishes task conversion, relational preservation, or
   behavior.
4. **Simplest non-causal explanation of EXP-016?** Different sampled layers
   have different cosine geometry, norm profiles, and centroid separations.
   Applying threshold and extremum rules to coupled metrics can select distinct
   labels without identifying distinct functional regions.
5. **What would falsify the current validity framing?** Held-out prompts or a
   new prompt set showing that matched-norm random directions equal or exceed
   the real direction on assignment/RSM, or that the selected validity point
   does not predict independently measured preservation or behavior.
6. **Highest-value independent validation:** split prompts before fitting
   centroids/directions and evaluate held out, with matched-norm random and
   alternative-direction controls evaluated under the same frozen metric.
7. **Is generation still the correct next step?** Not as a full confirmatory
   behavioral study. The already preregistered hook diagnostic is appropriate;
   the audit posture for behavioral interpretation is hold pending an
   independence check.

## K. Severity table and remediation posture

| Severity | Issue | Required posture |
|---|---|---|
| CRITICAL | Same centroids/delta construct and evaluate steering assignment | Do not present transition assignment as independent success. |
| HIGH | Common translation can preserve cosine-RSM rank structure without task-specific preservation | Do not treat low IVS as relational invariance without comparative controls. |
| HIGH | No held-out split across the steering/validity sequence | Treat all operating points as exploratory/in-sample. |
| HIGH | Sequential selection of beta, scalarization, layer, and role labels | Avoid confirmatory wording and aggregate winner claims. |
| HIGH | Representation–behavior links use four groups and are benchmark-sensitive | Do not claim explanation or prediction of behavior. |
| MEDIUM | “Safe” depends on mean IVS; Qwen L4 has minimum pair assignment .667 | Use “mean-constrained” and report pair-level failures. |
| MEDIUM | EXP-017 direction-estimation context differs from behavioral prompt context | Keep the next action at hook-diagnostic scope. |

The appropriate status is **major claim revision plus an independent validation
gate**, not a claim of fatal numerical invalidity. Existing results should be
preserved as exploratory evidence with the limitations stated above.
