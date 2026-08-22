# EXP-028 Adversarial Test Specification

**Task:** `103C_EXP028_PREREGISTRATION_REREVIEW_AND_ENGINEERING_SPEC`
**Status:** `ADVERSARIAL_TEST_SPEC_ONLY`
**Implementation deferred to:** `103D_EXP028_RUNNER_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION`

The tests below are synthetic-only. They must pass before any real EXP-028
model inference or formal authorization is considered.

## Required synthetic tests

### LABEL_LEAKAGE_REJECTED

Verify T2 fitting and probe fitting cannot use class labels or EVAL labels.
Fixture uses randomized labels; the test fails if behavior differs.

### EVAL_OPERATOR_FIT_REJECTED

Verify the operator cannot be refit on EVAL. Fixture changes EVAL data; T2
coefficients must remain identical to FIT-only coefficients.

### DIAG_OPERATOR_TUNING_REJECTED

Verify DIAG cannot change operator family, endpoint, bootstrap, or threshold.
Fixture attempts a DIAG-driven operator change and expects rejection.

### OLD_PANEL_REUSE_REJECTED

Verify fresh-panel validation rejects any item whose normalized raw-text hash
collides with an enumerated prior-panel authority.

### DUPLICATE_SOURCE_FAMILY_REJECTED_WHEN_IDENTITY_AVAILABLE

Verify panel validation rejects reuse of a source-family ID when historical
source-family identity is available.

### ZERO_VARIANCE_RULE_EXACT

Verify zero target variance is exactly `TECHNICALLY_INVALID_MODEL`, with no
epsilon fallback.

### NONFINITE_RULE_EXACT

Verify NaN/Inf variance, covariance, or fitted coefficients produce
`TECHNICALLY_INVALID_MODEL`.

### T1_ORIENTATION_EXACT

Verify T1 maps target representation into the source measurement frame and does
not reverse the source/target mean/scale application.

### T2_ORIENTATION_EXACT

Verify T2 fits source as the dependent variable and target as the independent
variable under the registered paired orientation.

### PRIMARY_COMPARATOR_IS_T1

Verify primary contrast is `T2 - T1`, not `T2 - T0`.

### DELTA_RM_SIGN_EXACT

Verify `DELTA_RM = E(T1) - E(T2)`, with positive meaning paired contribution
improves representation matching.

### DELTA_RO_SIGN_EXACT

Verify `DELTA_RO = C(T2) - C(T1)`, with positive meaning paired contribution
improves fixed-readout recovery.

### BOOTSTRAP_PERCENTILE_SEMANTICS_EXACT

Verify support uses the 5th percentile one-sided lower bound and that the
`[5, 95]` interval is treated as central 90% descriptive, not a two-sided 95%
CI.

### SOURCE_FAMILY_CLUSTERING_EXACT

Verify resampling unit is source family, stratified by condition, with all rows
of a sampled source family included together.

### CONDITION_EQUAL_WEIGHTING_EXACT

Verify all 10 conditions are combined by arithmetic mean, equal weight.

### LAYER_PAIR_EQUAL_WEIGHTING_EXACT

Verify all ordered forward layer pairs `j > i` are combined by arithmetic mean,
equal weight.

### PAIR_BREAK_CANNOT_RESCUE

Verify a favorable pair-break result cannot change a failed primary result.

### LOW_RANK_OPERATOR_REJECTED

Verify the low-rank cross-coordinate operator family is rejected by the
capacity firewall.

### MLP_OPERATOR_REJECTED

Verify the MLP operator family is rejected by the capacity firewall.

### KAN_OPERATOR_REJECTED

Verify the KAN operator family is rejected by the capacity firewall.

### MAJORITY_ROUTE_REJECTED

Verify three-model routing never uses a 2/3 majority vote.

### INVALID_MODEL_DROP_REJECTED

Verify a technically invalid model produces `NOT_FULLY_ADJUDICATED` and is not
dropped to create a reduced-model claim.

### TRANSPORT_CLAIM_REJECTED

Verify the claim ceiling rejects any transport, invariant, Functional Binding,
or full Residual-Flow claim as beyond EXP-028 scope.

## Validator coverage

`validate_exp028_preregistration.py` must reject the pre-correction ambiguous
bootstrap form and accept only the corrected one-sided lower-bound form, plus
the corrected aggregation, pair-break, and freshness fields.
