# Paper-A Claim-Evidence Matrix

This matrix is a manuscript guardrail. Canonical experiment results and
`docs/research/CLAIM-LEDGER.md` outrank it.

## C1: Local representational manipulability

- Statement: On a controlled held-out task-semantic design, task-directed
  hidden-state interventions produce target-directed movement measurable by an
  independent fit-only probe.
- Status: `SUPPORTED_WITH_SCOPE_LIMITATIONS`
- Supporting evidence: EXP-018 primary probe and held-out centroid results.
- Limiting evidence: small controlled prompt set; fixed models/layers; EXP-018
  does not establish behavioral control.
- Allowed wording: locally manipulable task-associated representations.
- Forbidden wording: universal task axes, general causal control, global
  cognitive geometry.
- Paper section: Results 4.1.

## C2: Larger-model replication of manipulability

- Statement: Same-family higher-parameter representation-level replication is
  supported under frozen EXP-020A controls.
- Status: `SUPPORTED`
- Supporting evidence: EXP-020A recovered canonical result;
  `REPRESENTATION_REPLICATION_SUPPORTED`.
- Limiting evidence: same-family replication only; not cross-family or
  cross-task universality.
- Allowed wording: same-family larger-model representation replication.
- Forbidden wording: cross-model universality, general scale invariance.
- Paper section: Results 4.1.

## C3: Manipulability does not imply behavioral control

- Statement: Representational manipulability does not automatically produce
  task-specific correctness-level behavioral advantage.
- Status: `SUPPORTED_NEGATIVE_BOUNDARY`
- Supporting evidence: EXP-017 matched-control result.
- Limiting evidence: EXP-019 evaluator generalization failure limits the
  behavioral endpoint interpretation.
- Allowed wording: no demonstrated behavioral control from representation
  manipulation.
- Forbidden wording: representation steering causes or controls behavior.
- Paper section: Results 4.2.

## C4: Fixed readout stability varies across depth/conditions

- Statement: A fixed source-semantic readout does not remain uniformly
  qualified across deeper clean checkpoints.
- Status: `SUPPORTED_WITH_SCOPE_LIMITATIONS`
- Supporting evidence: EXP-021 Stage-Q Q3 sanitized canonical result.
- Limiting evidence: qualification/measurement scope; small controlled design.
- Allowed wording: readout compatibility is layer/condition dependent.
- Forbidden wording: universal layerwise drift or proven dynamic manifold.
- Paper section: Results 4.3.

## C5: Featurewise recalibration can rescue some degraded readouts

- Statement: FIT-only featurewise recalibration can substantially restore fixed
  readout performance in some degraded held-out conditions.
- Status: `CONDITIONAL_SIGNAL`
- Supporting evidence: EXP-022A A1 recovery; EXP-023 Split A strong `G_cal`; EXP-024 10/10 positive `G_eval` descriptive panel observation.
- Limiting evidence: EXP-023 Split B null; discovery-stage origin.
- Allowed wording: candidate recovery mechanism observed in specific
  conditions.
- Forbidden wording: robust general calibration mechanism or universal rescue.
- Paper section: Results 4.4 and 4.5.

## C6: General cross-split calibration replication is not supported

- Statement: Independent preregistered replication returned `NO_REPLICATION`
  for cross-split featurewise calibration.
- Status: `SUPPORTED_NEGATIVE`
- Supporting evidence: EXP-023 canonical result.
- Limiting evidence: one confirmatory experiment; controlled dataset.
- Allowed wording: general cross-split calibration replication not supported.
- Forbidden wording: calibration failed globally or is absent.
- Paper section: Results 4.5.

## C7: Calibration susceptibility may be conditional

- Statement: Featurewise calibration benefit varies by condition, but a simple
  independent degradation-magnitude diagnostic does not prospectively rank it
  under the registered EXP-024 primary test.
- Status: `HYPOTHESIS_GENERATING / SIMPLE_PREDICTOR_NOT_SUPPORTED`
- Supporting evidence: EXP-022A and EXP-023 split heterogeneity; EXP-024
  positive descriptive panel benefit in all 10 conditions.
- Limiting evidence: EXP-024 primary `p = 0.2115079365079365`, support false;
  limited condition-level diagnostic resolution; fixed panel/model.
- Allowed wording: conditional heterogeneity remains; simple predictor not
  supported.
- Forbidden wording: known causal mechanism, established predictor, or
  conditioning factor.
- Paper section: Discussion 5.3 and 5.7.

## C8: Mean-only signal is secondary/hypothesis-generating

- Statement: Split-A secondary decomposition suggests mean/location
  recalibration may contribute more than scale recalibration.
- Status: `SECONDARY_DESCRIPTIVE`
- Supporting evidence: EXP-023 Split A `G_mu > G_sigma`.
- Limiting evidence: Split B null; descriptive only.
- Allowed wording: secondary hypothesis-generating mean signal.
- Forbidden wording: mean drift established mechanism; scale irrelevant.
- Paper section: Results 4.5 secondary subsection.

## C9: General coordinate transport is not tested

- Statement: The current chain does not test general coordinate transport.
- Status: `NOT_TESTED`
- Supporting evidence: none direct.
- Limiting evidence: no canonical transport result.
- Allowed wording: transport remains untested.
- Forbidden wording: transport proven or supported.
- Paper section: Discussion 5.4.

## C10: Functional binding is not tested

- Statement: The current chain does not establish causal functional binding.
- Status: `NOT_TESTED`
- Supporting evidence: none direct.
- Limiting evidence: EXP-017/EXP-019 boundary results.
- Allowed wording: functional binding remains outside the current evidence.
- Forbidden wording: functional binding demonstrated.
- Paper section: Discussion 5.4.

## C11: Panel-bounded featurewise calibration benefit is observed descriptively

- Statement: Within the frozen EXP-024 10-condition panel, FIT-only featurewise
  recalibration produced positive `G_eval` in all 10 registered conditions.
- Status: `SUPPORTED_DESCRIPTIVELY`
- Supporting evidence: EXP-024 canonical result `G_eval > 0` in 10/10
  conditions.
- Limiting evidence: descriptive panel observation only; no preregistered
  cross-condition positivity test; fixed model and controlled dataset.
- Allowed wording: panel-bounded descriptive calibration benefit.
- Forbidden wording: universal calibration, population-wide guarantee,
  cross-model generality, causal mechanism.
- Paper section: Results 4.6.

## C12: Simple independent degradation-magnitude susceptibility prediction is not supported

- Statement: The preregistered EXP-024 primary test did not support the
  prediction that larger independent `S_diag(c)` ranks larger confirmatory
  `G_eval(c)`.
- Status: `NOT_SUPPORTED`
- Supporting evidence: EXP-024 canonical primary `rho = 0.28401877872187725`,
  exact one-sided `p = 0.2115079365079365`, support false.
- Limiting evidence: one panel; limited condition-level predictor resolution
  and substantial ties; fixed model.
- Allowed wording: simple susceptibility predictor not supported.
- Forbidden wording: calibration unrelated in general; predictor failure as
  universal mechanism denial.
- Paper section: Results 4.6 and Discussion 5.3/5.7.

## EXP-025 Claim Updates

EXP-025 extends the panel to `allenai/OLMo-2-0425-1B-Instruct` and requires
the following narrow claim-level updates:

- **CLAIM A1 — core existence:** fixed readout compatibility loss can occur
  across depth. Status: `SUPPORTED`. Evidence remains the Qwen chain.
- **CLAIM A2 — cross-model degradation breadth:** fixed-readout degradation is
  broadly/stably reproduced across model families. Status: `NOT_ESTABLISHED`.
  Evidence: EXP-025 `D-`.
- **CLAIM B — FIT-only low-capacity featurewise recalibration recovery:**
  Status: `STRENGTHENED_WITH_LIMITED_CROSS_MODEL_SUPPORT`. Evidence: EXP-025
  `G+`.
- **CLAIM C — cross-model generality:** Status:
  `LIMITED_CROSS_MODEL_SUPPORT`. Evidence: recovery support is second-family
  but not architecture-independent; degradation breadth is not replicated.
- **CLAIM D — simple degradation magnitude predicts recalibration
  susceptibility:** Status: `NOT_SUPPORTED`. Evidence: EXP-024 and EXP-025 both
  failed the registered support rule.
- **CLAIM E — transport / invariant preservation / functional binding /
  behavioral effect:** Status: `NOT_TESTED`.

Existing C4/C5/C7/C12 remain correct for their original scope; their limiting
evidence now also includes the EXP-025 cross-model result where applicable.

## Matrix Summary

| ID | Statement | Status | Supporting | Limiting | Paper section |
| --- | --- | --- | --- | --- | --- |
| C1 | local representational manipulability | `SUPPORTED_WITH_SCOPE_LIMITATIONS` | EXP-018 | small controlled design | 4.1 |
| C2 | larger-model replication of manipulability | `SUPPORTED` | EXP-020A | same-family only | 4.1 |
| C3 | manipulability does not imply behavioral control | `SUPPORTED_NEGATIVE_BOUNDARY` | EXP-017 | EXP-019 endpoint limit | 4.2 |
| C4 | fixed readout stability varies | `SUPPORTED_WITH_SCOPE_LIMITATIONS` | EXP-021 | qualification scope | 4.3 |
| C5 | featurewise recalibration can rescue some readouts | `CONDITIONAL_SIGNAL` | EXP-022A/EXP-023 Split A | EXP-023 Split B null | 4.4/4.5 |
| C6 | general calibration replication not supported | `SUPPORTED_NEGATIVE` | EXP-023 | one confirmatory experiment | 4.5 |
| C7 | calibration susceptibility may be conditional | `HYPOTHESIS_GENERATING / SIMPLE_PREDICTOR_NOT_SUPPORTED` | EXP-022A/023 heterogeneity; EXP-024 panel | simple predictor not supported | 5.3/5.7 |
| C8 | mean-only signal is secondary | `SECONDARY_DESCRIPTIVE` | EXP-023 Split A | Split B null | 4.5 |
| C9 | general coordinate transport not tested | `NOT_TESTED` | none | no transport result | 5.4 |
| C10 | functional binding not tested | `NOT_TESTED` | none | no binding result | 5.4 |
| C11 | panel-bounded calibration benefit observed descriptively | `SUPPORTED_DESCRIPTIVELY` | EXP-024 10/10 G_eval positive | descriptive only | 4.6 |
| C12 | simple degradation-magnitude susceptibility prediction | `NOT_SUPPORTED` | EXP-024 rho=0.284, p=0.2115 | one panel, low resolution | 4.6/5.3/5.7 |


## 099C Revision Alignment

- Revised central claim is locked in `docs/paper/PAPER-A-FIRST-FULL-DRAFT.md`.
- Evidence statuses in this matrix are unchanged; Task-099C did not reanalyze
  or recalculate any experiment.
- The revised manuscript explicitly separates formal support from descriptive
  evidence for EXP-022A, EXP-023, and EXP-024.
- EXP-023 remains `NO_REPLICATION`.
- EXP-024 primary remains `NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`.
- Behavioral, functional-binding, and coordinate-transport boundaries remain
  unsupported and are not claimed.
