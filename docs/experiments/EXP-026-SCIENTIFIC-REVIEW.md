# EXP-026 Scientific Review and Registered Interpretation

Review type: `INDEPENDENT_POST_HOC_SCIENTIFIC_REVIEW`

Task: `101H_EXP026_REGISTERED_SCIENTIFIC_RESULT_AUDIT_AND_INTERPRETATION`

Timestamp: `2026-08-21`

Formal verdict: `EXP026_101H_COMPLETE`

## Formal Result Identity

- Experiment: `EXP-026`
- Working name: `Model-Depth Fixed-Readout Compatibility Matrix`
- Execution repository commit: `f5713f398b4c9fa17e790bd1d03388f36460a45a`
- Runner SHA-256: `6ab29c35889ce35b9d4bc9ee98d2665865a088312940f10815714a574d2060a0`
- Authorization ID: `b3763f43-d365-4a24-86fc-263f53dc84cb`
- Authorization SHA-256: `83adcafa0648e94d8a50b7132bc9713abf2d9ee58bb930690b775ec93248dcd2`
- Authorization consumption SHA-256: `4a35bfed3622ef82540e6bd42a843a56c9b5c465a686c1e2201ea5de012cd82a`
- Run attempt ID: `f5e6aadca9a946fbb1061154fe14211a`
- Engineering qualification SHA-256: `bbce631a27e20762212eb905278b4398c4850485faacd62e865b2f7a286f2e2d`
- Formal pipeline qualification SHA-256: `f474e28d04362fdebcf6eee5348a8b558a898124bc3c01cb7e053add59051690`
- Canonical result: `experiments/exp026/results/exp026_results.json`
- Canonical result SHA-256: `9a5bed41b432e2f89b0873869d76e1f5775f9b38caff9472553fca335bbba551`
- Canonical result byte length: `1323656`

## Result Validation Identity

- `RESULT_STATUS = VALID_REGISTERED_RESULT`
- `ATTEMPT_STATUS = COMPLETED_AND_PUBLISHED_ONCE`
- Formal authorization consumed exactly once.
- Schema/provenance/technical validity: `PASS`
- No duplicate canonical result found.
- Frozen authority hashes match.

## Registered Observations

### Qwen/Qwen3-1.7B

- Source coverage evaluable: `true`
- Eligible source count: `28`
- Eligible depth span: `1.0`
- Distance association: `0.7049462571528698`
- Distance CI: `[0.6851830380886905, 0.7080622074980855]`
- Distance support: `POSITIVE_SUPPORTED`
- SDI: `-0.17355352410373298`
- SDI CI: `[-0.18868527431441903, -0.15827487462584097]`
- SDI class: `TARGET_DOMINANT`
- Localization: `0.13796495277734067`, `EVALUABLE`
- LOW-D effective n: `202`
- LOW-D mean recovery: `0.00013923267534205524`
- LOW-D positive fraction: `0.07425742574257425`
- LOW-D CI: `[-9.933156284070251e-05, 0.00036107659009100833]`
- LOW-D support: `NOT_SUPPORTED`

### allenai/OLMo-2-0425-1B-Instruct

- Source coverage evaluable: `true`
- Eligible source count: `16`
- Eligible depth span: `1.0`
- Distance association: `0.7519250367843754`
- Distance CI: `[0.7438987161061725, 0.7582397801058931]`
- Distance support: `POSITIVE_SUPPORTED`
- SDI: `0.5249651786448143`
- SDI CI: `[0.49101491890702714, 0.5584696075004959]`
- SDI class: `SOURCE_DOMINANT`
- Localization: `0.1630150787539261`, `EVALUABLE`
- LOW-D effective n: `35`
- LOW-D mean recovery: `0.04785714308465166`
- LOW-D positive fraction: `0.8285714285714286`
- LOW-D CI: `[0.044028989621438086, 0.0515186088984566]`
- LOW-D support: `SUPPORTED`

## Registered Routing

- `P1 = false`
- `P2 = true`
- `P3 = true`
- `P4 = true`
- `P5 = false`
- `EXP026_REGISTERED_ROUTE = P3`
- `EXP026_SCIENTIFIC_STATUS = P3_MATERIALLY_DIFFERENT_MODEL_SIGNATURES`
- Conflict resolution: `P3_P1_P2_P4_P5_PRECEDENCE`

## Interpretation Ceiling

Allowed scientific interpretations:

- Both tested models show strong depth-distance-associated fixed-readout compatibility structure.
- Qwen and OLMo show materially different source/target organization.
- Qwen is `TARGET_DOMINANT` under the registered SDI.
- OLMo is `SOURCE_DOMINANT` under the registered SDI.
- LOW-D recalibration recovery is supported in OLMo but not Qwen.
- Recalibratability is therefore not uniformly reducible to raw fixed-readout degradation across the tested models.
- The observed structural differences are `MODEL_DEPENDENT`, not architecture-causal.

Forbidden interpretations:

- Architecture causality.
- Family causality.
- Universality.
- Information disappearance.
- Transport.
- Invariance.
- Functional binding.
- Behavioral causality.
- Scale law.

## Hypothesis Disposition

- `H1` depth-associated compatibility organization: `SUPPORTED_IN_BOTH_TESTED_MODELS`
- `H2` localized transition explanation: `NOT_PRIMARY_REGISTERED_ROUTE`; retain only frozen secondary evidence.
- `H3` source/reference dependence: `SUPPORTED_BUT_MODEL_DEPENDENT`
- `H4` model-dependent compatibility organization: `SUPPORTED`
- `H5` recalibratability partly independent of raw degradation: `CONDITIONAL_MODEL_DEPENDENT_SUPPORT`

These statuses are mechanistic/prospective only. They do not establish causal architecture, transport, invariance, binding, or behavior.

## Relation to EXP-025

EXP-026 is a structured follow-up to the prior OLMo `D- / G+` observation. OLMo
shows registered LOW-D recovery despite low diagnostic degradation for selected
pairs. Therefore a simple monotonic relationship between raw degradation
magnitude and recalibration benefit is insufficient for the tested OLMo
setting.

This must not be read as proof that recovery preserves information or that
transport is supported.

## Routing After EXP-026

- Primary next scientific task: `THIRD_MODEL_INDEPENDENT_VALIDATION`
- `P4` operator-capacity route: `SCIENTIFICALLY_LIVE_BUT_DEFERRED_BY_REGISTERED_P3_PRECEDENCE`
- Do not choose `P4` now.

## Performance Engineering Debt

The 5000-replicate cluster bootstrap repeatedly recomputed matrix-level
quantities and caused approximately multi-hour/single-core execution.

EXP-026 must not be altered. A separate EXP-027 engineering task may optimize
the bootstrap implementation only if the statistical resampling unit, RNG
semantics, replicate count, estimand, percentile/CI semantics remain unchanged,
and synthetic equivalence is demonstrated against the current reference
implementation. No scientific simplification for speed.

## Paper-A Impact

Narrow update only: depth-structured fixed-readout compatibility is observed in
both tested models, while source/target organization differs materially across
models.

Do not claim that the same mechanism replicated cross-model. Do not perform a
broad Paper-A rewrite in this task.

## Next Step

`EXP026_NEXT_TASK = 102A_EXP027_THIRD_MODEL_SELECTION_AND_DESIGN_AUDIT`

Create an EXP-027 pre-design note only; do not freeze an EXP-027 preregistration,
do not access real EXP-027 data, and do not issue an EXP-027 formal
authorization.