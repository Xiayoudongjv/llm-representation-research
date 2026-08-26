# PAPER-A POSITIONING FREEZE V1

Status: frozen manuscript-positioning guidance. This document does not add
experiments, alter canonical results, or raise the claim ceiling.

## 1. Research Question

Paper A asks:

> When a readout is fit at one decoder depth and applied without retraining at
> another depth, how does its direct operational compatibility vary across
> depth and across the three tested language models?

The measurement is deliberately bounded. The carrier is the last valid token
at the post-decoder-block residual, before the next block and before the
model's final normalization. The primary object is a directed source-target
compatibility matrix, not a claim about a latent representation space.

The registered measures are:

- `C0`: direct fixed-readout compatibility;
- `D`: degradation relative to the source-layer self condition; and
- `R`: restricted FIT-only recovery after the registered calibration procedure.

## 2. Core Contribution

Exactly three contributions are frozen.

### Contribution 1 — A bounded operational measurement

**Final wording:** Paper A defines and evaluates direct fixed-readout
cross-depth compatibility, together with a restricted FIT-only recovery
diagnostic, under a registered source-target matrix protocol.

**Evidence source:** EXP-026 and EXP-027 frozen results; the EXP-026/027
matrix and metric specifications; Paper A Figures 1 and 3.

**Reviewer risk:** A reviewer may read “functional” or “recovery” as a causal
or mechanistic claim. The manuscript must state that these are operational
readout measurements and that the calibration is a diagnostic intervention,
not a learned alignment or mechanism test.

### Contribution 2 — Model- and depth-dependent operational profiles

**Final wording:** Across the three tested decoder-only language models,
direct compatibility, degradation, source/target dominance, and restricted
recovery form different operational profiles; restricted recovery is observed
for some profiles and conditions, but is not uniform.

**Evidence source:** EXP-026 and EXP-027 model profiles, continuous values and
canonical confidence intervals; Paper A Figure 2 and Table 1.

**Reviewer risk:** Three models do not establish an architecture-wide law.
Categorical profile labels must remain accompanied by continuous magnitudes
and intervals, and no causal explanation for model differences is permitted.

### Contribution 3 — Directed and heterogeneous evidence reporting

**Final wording:** Paper A reports full directed source-target matrices and
explicit split/condition heterogeneity, preserves the preregistered negative
predictor result, and treats cross-direction asymmetry as an exploratory
secondary observation.

**Evidence source:** EXP-022A/023/024/025/026/027 frozen results; Paper A
Figures 3–5, Tables 1–2 and the directionality closure record.

**Reviewer risk:** A matrix is not evidence of geometry, information flow, or
directional causality. The negative predictor result is scoped to its
registered tests and cannot be turned into a claim that compatibility has no
structure.

## 3. Claim Firewall

The following classifications apply to the unqualified concepts named in the
positioning discussion. The safe wording is the only wording authorized for
the manuscript.

| Candidate claim | Status | Evidence and safe wording | Reviewer boundary |
|---|---|---|---|
| Fixed-readout compatibility | **SAFE** | `C0`, `D`, and `R` directly measure this under the registered protocol. Say: “fixed-readout operational compatibility varies across depth in the tested models and conditions.” | Do not generalize beyond the tested carrier, panel, models, or conditions. |
| Functional compatibility | **MODERATE** | Use only as shorthand after defining it as operational readout compatibility. Prefer: “operational compatibility of a task readout.” | “Functional” can imply preserved computation, behavior, or mechanism. |
| Readout portability | **MODERATE** | Say: “direct cross-depth reuse of a fixed readout under the tested protocol.” | Do not claim general portability across tasks, models, prompts, or representations. |
| Functional coordinate persistence | **UNSUPPORTED** | No result establishes a persistent coordinate system or stable task coordinates. | Do not use “coordinate persistence,” “shared coordinates,” or equivalent language. |
| Directionality | **SAFE** | The directed matrices support an exploratory, descriptive asymmetry claim across the three tested models. | No “information flow,” causal direction, universal orientation, or geometric asymmetry. |
| Representation geometry | **UNSUPPORTED** | CKA is a secondary similarity measure, not a completed geometric validation of Paper A. | Do not claim manifolds, geometric equivalence, or geometry-driven behavior. |
| Information flow | **UNSUPPORTED** | The experiments measure readout transfer, not causal transport or information flow. | No causal mechanism, layer-to-layer information flow, or computational transformation claim. |

Additional standing limits:

- Cross-task/task-panel robustness is **not established**.
- The three-model panel does not support architecture-wide or universal claims.
- The registered negative predictor result does not prove the absence of
  structure.
- Directional asymmetry is exploratory and descriptive, not a new causal
  theory.

## 3A. Falsification and Triangulation Ladder

The evidence sequence must distinguish registered negative evidence,
cross-model heterogeneity, and prospective model triangulation:

### Level A — Registered negative evidence

- **EXP-023:** restricted recalibration was not uniformly stable across
  complementary splits; the formal result is `NO_REPLICATION`.
- **EXP-024:** simple independent degradation magnitude did not support the
  registered susceptibility prediction in the ten-condition panel; the
  formal result is `NOT_SUPPORTED`.

### Level B — Cross-model heterogeneity

**EXP-025** showed that the tested OLMo panel did not uniformly reproduce a
simple Qwen-style degradation/recovery pattern (`D- / G+`). This is
cross-model heterogeneity, not a universal model-family falsification.

### Level C — Prospective triangulation with bounded synthesis

**EXP-026** provides the registered Qwen/OLMo matrix and profile comparison;
**EXP-027** provides the third registered Llama profile. The safe synthesis is:

> The third tested profile breaks a simple descriptive mapping suggested by
> the first two tested models.

This mapping statement is a bounded/post-hoc synthesis of the registered
three-model evidence, not a preregistered universal theory test.

## 4. Reviewer Attack Risks

1. **“This is just probing.”** Explain that the central contrast is direct
   reuse of a frozen readout versus a separately registered restricted
   FIT-only calibration diagnostic. Do not call the calibration a mechanism.
2. **“Functional means behavior.”** Replace unqualified “functional” with
   “operational readout” wherever possible.
3. **“Three models are too few.”** Name the three models in every cross-model
   summary and state that the result is panel-bounded.
4. **“Asymmetry implies causality.”** Define directionality as the inequality
   of directed operational matrix entries and label it exploratory.
5. **“A matrix proves geometry.”** State that source-target matrices are an
   operational representation; they are not latent-space coordinates.
6. **“The negative predictor proves no structure.”** Report only that the
   preregistered predictor was unsupported under its registered tests.
7. **“The last-token carrier is the whole representation.”** State the
   post-block, pre-final-normalization, last-valid-token carrier limitation.
8. **“CKA upgrades the paper to a geometry paper.”** CKA is secondary and
   descriptive. It cannot establish equivalence, mechanism, or causality.

9. **“Cross-layer probe/readout transfer is already known.”** Paper A does
   not introduce a new alignment or probing method. It asks whether direct
   reuse of a fixed source readout and recoverability under deliberately
   restricted FIT-only recalibration exhibit the same cross-depth structure.
   The directed matrices, registered negative evidence, and three tested model
   profiles are the bounded empirical contribution.

## 4A. Prior-Art Boundary

The following repository-recorded, externally verified facts define the
positioning boundary. They are not claims of exhaustive literature coverage.

- **Tuned Lens:** trains an affine probe for each Transformer block to decode
  intermediate hidden states. Paper A therefore does not claim novelty for
  layer-specific affine readouts or adapted intermediate readout interfaces.
- **Patchscopes:** provides a broad framework for inspecting, projecting, and
  intervening on hidden representations. Paper A does not claim novelty for
  hidden-state inspection or intervention.
- **Functional Alignment Can Mislead:** supports the distinction between
  successful functional/model-stitching alignment and representation or
  information equivalence. This caution is prior art, not a Paper A novelty
  claim.
- **Model stitching and affine feature transfer:** prior work includes affine
  mappings for transferring probes, steering vectors, and linear features
  across models. Paper A is a within-model, cross-depth measurement study, not
  a cross-model feature-transfer method.
- **SemRF and ICR Probe:** these are conceptual/empirical neighbors for
  residual-stream dynamics, measurement drift, and cross-layer hidden-state
  evolution. Paper A does not claim novelty for those broad phenomena.
- **Structured world-model probe transfer:** repository-recorded work also
  includes fixed source-layer probes evaluated across target layers. Paper A
  must not claim to be the first frozen-probe cross-layer transfer or first
  source-layer cross-target matrix.

Paper A's remaining defensible novelty delta is the controlled empirical
decomposition of direct fixed-readout operational compatibility from restricted
FIT-only recoverability, combined with full directed source-target matrices,
registered negative/non-replication evidence, and a three-model multi-axis
operational profile. This is scoped to the tested models, carrier, task panel,
and registered conditions.

### External Prior-Art Check Queue

Before manuscript writing, independently verify the exact bibliographic and
scope details for Tuned Lens, Patchscopes, Functional Alignment Can Mislead,
model stitching/feature transfer, SemRF, ICR Probe, and the structured
world-model probe-transfer work. Also verify any use of “first”, “novel”, or
“only”.

## 5. Allowed Terminology

Use these terms with their stated scope:

- fixed-readout operational compatibility;
- direct cross-depth readout reuse;
- directed source-target compatibility matrix;
- compatibility degradation under a fixed readout;
- restricted FIT-only calibration or recovery diagnostic;
- model-dependent operational profile;
- split/condition heterogeneity;
- exploratory directional asymmetry;
- tested post-block residual carrier;
- centered linear CKA as a secondary representational-similarity measure,
  with a brief bounded main-text reference and supplement eligibility after
  its separate analysis is run and validated.

Preferred title wording is “operational compatibility,” not unqualified
“functional compatibility.”

## 6. Forbidden Terminology

Do not use any of the following as Paper A claims:

- functional coordinate persistence;
- persistent or shared task coordinates;
- semantic equivalence or representational equivalence;
- geometric equivalence, task manifolds, or cognitive space;
- information flow, causal transport, or layerwise causal mechanism;
- universal depth law, architecture-wide law, or scale invariance;
- robust across tasks, general across models, or all-conditions invariance;
- disentangled latent factors or fundamental axes;
- causal independence or statistically independent dimensions;
- “first,” “only,” or “novel” without a separately verified literature scope;
- behavioral control, reasoning improvement, or cognitive transformation.

## 7. Experimental Extension Boundary

### Current Paper A

The completed evidence supports the three contributions in Section 2 using
the frozen EXP-022A through EXP-027 lineage, the registered three-model panel,
the defined carrier, and the registered C0/D/R measures. The paper may report
exploratory directionality, but must retain its descriptive status.

The Paper A CKA module is a completed post-closure secondary analysis. Its
execution authority is `PAPER-A-CKA-RUN-AUTHORITY-V1.1.md`, and its manuscript
integration authority is `PAPER-A-CKA-FINAL-INTEGRATION-V1.md`. It is
`CKA_POST_CLOSURE`, `CKA_SECONDARY_ONLY`, `CKA_NOT_CORE_CONTRIBUTION`,
`CKA_MAIN_TEXT_ALLOWED = BRIEF_BOUNDED_REFERENCE_ONLY`, and
`CKA_SUPPLEMENT_ALLOWED = true`.

Safe wording is:

> Across the three tested models, CKA shows a strong descriptive association
> with direct fixed-readout operational compatibility.

Because CKA is symmetric by construction, it does not replace the directed
source-target compatibility analysis. This does not claim that CKA explains
directionality. The original core-science closure recorded `CKA = NO_GO` at
the time of that closure; the later bounded analysis does not rewrite that
historical state or alter the three core contributions.

### Future work

- **Cross-task directionality:** a separate, independently designed task-panel
  study is required. Paper A currently records this boundary as not
  established.
- **Fourth model:** a separately qualified model and preregistered execution
  are required before making claims about broader model coverage.
- **Larger-scale compatibility maps:** broader layers, tasks, conditions, or
  models require new data, new authority, and a new analysis boundary; they
  cannot be presented as extensions of the existing sample without a new
  protocol.

These extensions are not evidence for the current manuscript and must not be
used to fill gaps in the current claim set.

## 7A. Positioning Authority Rule

For manuscript positioning, precedence is:

```text
canonical experimental results
> canonical Paper A claim/science registers
> Paper A science closure
> this positioning guidance
> manuscript prose
```

This file governs manuscript positioning only. It cannot alter scientific
outcomes, canonical statistics, or claim ceilings.

## 8. Final Positioning Statement

Paper A is a scoped empirical study of fixed-readout operational compatibility
across Transformer depth. It shows that direct cross-depth reuse is
non-uniform, that restricted FIT-only recovery can differ from direct
compatibility across the tested model profiles, and that the resulting
source-target matrices are directed and heterogeneous. The cross-direction
asymmetry is exploratory. The paper does not establish semantic or geometric
equivalence, persistent task coordinates, causal mechanisms, information flow,
behavioral control, or cross-task universality.

**Recommended title:** *Measuring Asymmetric Operational Compatibility of
Fixed Readouts Across Transformer Depths.*

### Title audit

| Candidate | Assessment | Risk |
|---|---|---|
| 1. *Fixed Readouts Reveal Asymmetric Functional Compatibility Across Transformer Depths* | Too assertive for the positioning freeze. | “Reveal” sounds stronger than a measurement claim, and “functional” can imply behavior or mechanism. |
| 2. *Measuring Asymmetric Functional Compatibility of Fixed Readouts Across Transformer Depths* | Safest of the three candidates. | Retains the ambiguous word “functional”; replace it with “operational.” |
| 3. *Fixed-Readout Transfer Reveals Asymmetric Compatibility Across Transformer Representations* | Plausible but less precise. | “Transfer” may imply portability and “representations” is broader than the tested carrier. |

Among the three candidate titles, candidate 2 is the safest because it uses a
measurement framing rather than “reveal” or “transfer.” Replace “functional”
with “operational” in the final title to match the frozen evidence boundary.
