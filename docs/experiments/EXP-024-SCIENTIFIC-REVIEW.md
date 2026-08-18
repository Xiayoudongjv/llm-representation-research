# EXP-024 Scientific Review

Review type: `INDEPENDENT_POST_HOC_SCIENTIFIC_REVIEW`

Review timestamp: `2026-08-18T16:05:12+00:00`

Formal verdict: `EXP024_098F_SCIENTIFIC_REVIEW_COMPLETE`

## Formal Result Identity

- Execution repository commit: `68add3dbffe14a6b9cd28f9f4b6e8577821cf6f1`
- Authorization ID: `ca17270d-8621-4b65-9f61-be78a3bcf6d8`
- Authorization SHA-256: `5a37e5f0b75c236b6c50774b335cdc0651fe7871f1358ce6a089007d7070afb7`
- Consumption SHA-256: `015bce9ff4b5dba079e80a038f22bcbf7339b7c7441938a6038dbd7fc77abff8`
- Run attempt ID: `1bd3b938-9c63-4cdb-9854-21f3f34474e1`
- Runner SHA-256: `6416e278bb6836b8751967e619bf7e8b3d2b3a3180dce814ec068b50c386615f`
- Qualification SHA-256: `72e7f48d68a022819cfed5045061af5b0d6d84de659a49e056487b9d20da8d8f`
- Canonical result: `experiments/exp024/results/exp024_results.json`
- Result SHA-256: `50a6ea72dbb9c33ae8ec15d0e2ad31b32ebe0cf299679875fe7b34fb6cabcb69`

Verified:

- `FORMAL_RUN_LAUNCH_COUNT = 1`
- Authorization consumed exactly once.
- Result schema validation: `PASS`
- Result provenance validation: `PASS`
- Technical validity: `VALID`
- Formal analysis complete: `true`

## Primary Outcome

- Primary scientific unit: `condition`
- `N = 10`
- Primary diagnostic: `S_diag(c)`
- Primary confirmatory outcome: `G_eval(c)`
- Primary statistic: `Spearman_rho`
- Observed rho: `0.28401877872187725`
- Exact one-sided permutation p: `0.2115079365079365`
- Registered support rule: `rho > 0 AND p <= 0.05`
- Registered primary support: `false`

The primary directional association was positive but did not meet the registered
support criterion.

## Primary Hypothesis Disposition

`HYP_CALIBRATION_CONDITIONAL_002 = NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`

EXP-024 does not support the proposition that, across the frozen 10-condition
panel, independently measured fixed-readout degradation magnitude prospectively
ranks independent EVAL calibration benefit magnitude under the registered
one-sided exact test.

This negative primary result must not be expanded to mean:

- calibration does not work;
- degradation and calibration are unrelated in general;
- the descriptive panel-level calibration benefit is absent.

## Two Scientific Questions

- `QUESTION A`: Does fixed-readout degradation occur, and does FIT-only
  calibration improve final-layer readout? EXP-024 provides descriptive
  panel-level evidence relevant to Question A, but its primary test is not a
  confirmatory test of Question A.
- `QUESTION B`: Does condition-level independent degradation magnitude predict
  condition-level calibration benefit magnitude? EXP-024 directly tests
  Question B and returns `NOT_SUPPORTED` under the frozen primary test.

## Condition-Level Direct Observations

Canonical condition order:

`c01_lexical_relex`, `c02_syntactic_restructure`, `c03_controlled_compression`,
`c04_controlled_elaboration`, `c05_relation_explicit`, `c06_relation_implicit`,
`c07_register_formal`, `c08_register_informal`,
`c09_neutral_distractor_prefix`, `c10_anaphoric_reference`

`S_diag` values:

`[0.5, 0.4375, 0.3125, 0.3125, 0.5, 0.4375, 0.3125, 0.34375, 0.4375, 0.3125]`

`G_eval` values:

`[0.40625, 0.46875, 0.34375, 0.5, 0.4375, 0.375, 0.34375, 0.46875, 0.46875, 0.3125]`

Direct descriptive checks:

- `S_diag > 0`: `10 / 10` conditions
- `G_eval > 0`: `10 / 10` conditions

This is descriptive panel evidence only. It is not a new confirmatory
cross-condition positivity test.

## Post-Result Descriptive Summary

```text
POST-RESULT DESCRIPTIVE SUMMARY
NOT A NEW PREREGISTERED TEST
```

`S_diag`:

- mean: `0.390625`
- median: `0.390625`
- range: `0.3125` to `0.5`
- unique values: `4`
- ties: substantial; most values are `0.3125`, `0.4375`, or `0.5`

`G_eval`:

- mean: `0.4125`
- median: `0.421875`
- range: `0.3125` to `0.5`
- unique values: `7`

These summaries describe measurement shape only. They do not create a
significance test, replace the primary endpoint, or generate a new support
verdict.

## Measurement-Resolution Limitation

The condition-level predictor has limited resolution and substantial ties:

`DESCRIPTIVE_MEASUREMENT_LIMITATION: LIMITED_CONDITION_LEVEL_DIAGNOSTIC_RESOLUTION`

This limitation does not override the registered primary result. The current
registered diagnostic did not provide sufficient prospective ranking evidence
in this panel. It is not appropriate to reinterpret `p = 0.2115` as a trend or
power-adjusted support.

## Design Improvement Preserved

EXP-024 separates `S_diag` from the confirmatory `G_eval` by using independent
DIAGNOSTIC and EVAL source families. Unlike EXP-023, the predictor and outcome
do not share EVAL `A0` observations.

This design improvement is retained as a methodological strength even though
the primary hypothesis was not supported.

## Relation to EXP-023

EXP-023 registered outcome: `NO_REPLICATION`.

- Split A showed substantial degradation and calibration rescue.
- Split B showed little degradation and no calibration benefit.
- EXP-023 exposed condition/split-dependent heterogeneity.

EXP-024 shows that in a new 10-condition panel:

- fixed-readout degradation was descriptively positive in all conditions;
- calibration benefit was descriptively positive in all conditions;
- degradation magnitude did not significantly predict calibration-benefit
  magnitude.

Therefore EXP-024 neither replicates `HYP_CALIBRATION_CONDITIONAL_002` nor
contradicts all calibration evidence.

## Relation to EXP-022A

EXP-022A established:

- fixed-frame degradation: partial and split-dependent;
- featurewise recalibration: descriptive high-value signal;
- same-family refit rescue: not supported;
- coordinate transport: not tested.

EXP-024 extends the descriptive calibration signal to a broader
preregistered condition panel, but rejects the simple independent
susceptibility predictor.

## Evidence Chain

- EXP-018: held-out local representational manipulability.
- EXP-017: task-specific behavioral correctness control not supported.
- EXP-019: independent evaluator failed generalization; behavioral targetness
  unresolved.
- EXP-020A: larger-model representation-level replication supported.
- EXP-021: fixed cross-depth readout qualification degraded; measurement
  framework failed to remain qualified.
- EXP-022A: split-dependent fixed-readout degradation; descriptive calibration
  rescue signal.
- EXP-023: independent preregistered general calibration replication returned
  `NO_REPLICATION`; localized strong signal preserved.
- EXP-024: valid preregistered condition-panel test; simple independent
  degradation-magnitude predictor not supported; broad positive panel-level
  calibration benefit observed descriptively.

## Scientific Taxonomy

- `OBSERVATION`: all registered `S_diag` and `G_eval` values are positive.
- `OPERATIONAL RESULT`: the primary Spearman exact test failed the registered
  support criterion.
- `INTERPRETATION`: simple degradation magnitude is insufficient as a
  prospective ranking predictor in this panel.
- `SPECULATION`: other aspects of frame mismatch may govern calibration
  susceptibility; this remains a future mechanism idea, not an EXP-024 finding.

## Paper-A Contribution Assessment

- Readout-degradation evidence: enhanced descriptively.
- Calibration-utility evidence: enhanced descriptively within the panel.
- Simple prospective susceptibility prediction: not supported.
- Methodological credibility: enhanced by preregistration and independent
  DIAGNOSTIC/EVAL separation.
- Cross-model generality: not addressed.

## Recommended Paper-A Core Story

```text
Fixed semantic readouts can lose compatibility across Transformer depth even
when task-associated information remains manipulable. Low-capacity FIT-only
featurewise recalibration can substantially restore readout performance under
multiple held-out conditions, but this benefit is not uniformly explained by a
simple independent measure of fixed-readout degradation magnitude.
```

Forbidden wording remains: universal, invariant representation transport,
causal cognitive transformation, general reasoning control, true task axis, or
general cognitive space.

## Research-State Updates

- `HYP_CALIBRATION_CONDITIONAL_002`: `NOT_SUPPORTED_BY_EXP024_PRIMARY_TEST`
- `PANEL_BOUNDED_FEATUREWISE_CALIBRATION_BENEFIT`: `OBSERVED_IN_EXP024`
- `GENERAL_CALIBRATION_REPLICATION`: `NOT_ESTABLISHED`
- `GENERAL_COORDINATE_TRANSPORT`: `NOT_TESTED`
- `FUNCTIONAL_BINDING`: `NOT_TESTED`
- `BEHAVIORAL_CONTROL`: `NOT_ESTABLISHED_BY_EXP024`

No new confirmatory follow-up hypothesis is created solely to chase
significance. The default next step is `PRESERVE_MECHANISM_GAP` and
`NO_IMMEDIATE_CONFIRMATORY_FOLLOWUP`.

## Next Step

Proceed to Paper-A full prose drafting with the bounded story above. Do not
automatically create EXP-025, do not create a replacement authorization, and
do not rerun EXP-024.
