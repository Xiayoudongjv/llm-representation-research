# EXP-025 Preoutcome Specification Clarification 001

Clarification ID: `EXP025_PREOUTCOME_SPECIFICATION_CLARIFICATION_001`

Classification: `PROSPECTIVE_PREOUTCOME_SPECIFICATION_CLARIFICATION`

## Prominent Status

This document:

- was created after the original EXP-025 Task-100A preregistration;
- was created after one technically invalid consumed formal authorization;
- was created before any DIAGNOSTIC/EVAL access or scientific outcome exposure;
- is motivated solely by the Task 100D-E0 implementation-specification audit;
- does not select a model, layer, dataset, endpoint, statistic, or threshold
  based on an observed outcome.

```text
EXP025_ORIGINAL_PREREGISTRATION_CHANGED = false
EXP025_PREOUTCOME_PROTOCOL_CLARIFICATION_ADDED = true
EXP025_PRIOR_SCIENTIFIC_OUTCOME_EXPOSURE = false
EXP025_PRIOR_DIAG_ACCESS = false
EXP025_PRIOR_EVAL_ACCESS = false
```

This clarification changes formerly unspecified scientific semantics. It does
not alter already specified hypotheses, model, dataset, layer, endpoint
family, or outcome-conditioned choices.

## Authority Search Summary

For each unresolved gap, the search order was:

1. frozen EXP-025 Task-100A authorities;
2. explicitly inherited EXP-024 / EXP-023 definitions;
3. pre-existing repository-wide scientific conventions;
4. pre-existing production helpers that clearly predate outcome exposure.

No candidate was sufficiently explicit to bind EXP-025 without a new additive
clarification. Therefore the five gaps are resolved below as
`PROSPECTIVE_PREOUTCOME_CLARIFICATION`.

## GAP-001: Spearman Tie Handling

Status: `PROSPECTIVE_PREOUTCOME_CLARIFICATION`

For the registered vectors:

```text
S = [S_diag(c)] for the fixed 10-condition order
G = [G_eval(c)] for the fixed 10-condition order
```

Compute:

1. Assign average ranks to tied values within `S`.
2. Assign average ranks to tied values within `G`.
3. Compute Pearson correlation between the two rank vectors.
4. Treat the result as the standard Spearman `rho` with average-rank ties.

Prohibited:

- breaking ties by condition order;
- random tie breaking;
- jittering values;
- ordinal/min/max ranks.

Scientific quantities affected: `rho_secondary`.

## GAP-002: Exact Permutation Test

Status: `PROSPECTIVE_PREOUTCOME_CLARIFICATION`

Observed statistic:

```text
rho_obs = rho_secondary from GAP-001
```

Null universe:

```text
all 10! = 3,628,800 permutations of the G vector across the fixed
10-condition order, including the observed labeling.
```

Direction:

```text
one-sided positive association: rho > 0
```

Extremeness convention:

```text
rho_perm is at least as extreme iff rho_perm >= rho_obs
```

Equality is included.

Complete enumeration p-value:

```text
p = count(rho_perm >= rho_obs) / N_permutations
```

No Monte-Carlo `+1` correction is added to a complete exact enumeration.

If the implementation uses only sampled permutations, the procedure is not
this registered exact test and must not be silently substituted.

Non-finite `rho` behavior:

- If `rho_obs` is non-finite, the secondary RQ3 analysis is
  `NOT_EVALUABLE`.
- If any `rho_perm` is non-finite, the secondary RQ3 analysis is
  `NOT_EVALUABLE`.
- `NOT_EVALUABLE` produces no RQ3 support classification.

Scientific quantities affected:

- exact permutation p-value;
- RQ3 support flag.

## GAP-004: Zero-Variance Scale Rule

Status: `PROSPECTIVE_PREOUTCOME_CLARIFICATION`

For any featurewise standardized term of the registered form:

```text
z_j = (x_j - mu_source,j) / sigma_source,j
```

use the deterministic, epsilon-free rule:

```text
if sigma_source,j > 0:
    z_j = (x_j - mu_source,j) / sigma_source,j

if sigma_source,j == 0:
    z_j = 0
```

Applied to the registered variants:

```text
A0:
    z_A0,j = (h_j - mu_ref,j) / sigma_ref,j
    if sigma_ref,j == 0: z_A0,j = 0

A_mu:
    z_A_mu,j = (h_j - mu_final,c,j) / sigma_ref,j
    if sigma_ref,j == 0: z_A_mu,j = 0

A_sigma:
    z_A_sigma,j = (h_j - mu_ref,j) / sigma_final,c,j
    if sigma_final,c,j == 0: z_A_sigma,j = 0

A_mu_sigma:
    z_A_mu_sigma,j = (h_j - mu_final,c,j) / sigma_final,c,j
    if sigma_final,c,j == 0: z_A_mu_sigma,j = 0
```

Requirements:

- no epsilon;
- no learned fallback;
- no dropping dimensions;
- no DIAGNOSTIC/EVAL decision logic.

The rule is algebraically compatible with the frozen `A0`, `A_mu`,
`A_sigma`, and `A_mu_sigma` equations: a zero source scale produces a zero
normalized contribution without arbitrary scale inflation.

Scientific quantities affected:

- `A_sigma`;
- `A_mu_sigma`;
- `G_eval`;
- downstream routing.

## GAP-005: Effective Sample Size Zero

Status: `PROSPECTIVE_PREOUTCOME_CLARIFICATION`

For the registered D/G exact binomial-support rule:

```text
if effective_n == 0:
    BINOMIAL_RULE_STATUS = NOT_EVALUABLE
    effective_successes = 0
    exact_one_sided_p = UNDEFINED
    support = NOT_EVALUABLE
```

`NOT_EVALUABLE` is not:

- `PASS`;
- `FAIL`;
- `0 successes out of 0`;
- `p = 1` interpreted as failure;
- `p = 0`;
- automatic support;
- automatic non-support.

The result artifact must preserve:

```text
effective_n = 0
effective_successes = 0
status = NOT_EVALUABLE
```

Any higher-level routing rule that requires the D/G binomial result must
propagate the indeterminate state. For EXP-025 routing, `D` or `G`
`NOT_EVALUABLE` maps to `NO SCIENTIFIC ROUTING`; it is not treated as
degradation present or absent.

Scientific quantities affected:

- D/G support classification;
- downstream routing.

## GAP-006: Multiclass Balanced Accuracy

Status: `PROSPECTIVE_PREOUTCOME_CLARIFICATION`

For the four registered semantic classes:

```text
logic, causality, analogy, definition
```

Define balanced accuracy as unadjusted macro-average recall:

```text
BA = (1 / 4) * sum_{c in registered classes} (TP_c / N_c)
```

Requirements:

- equal class weight;
- no frequency weighting;
- no adjusted balanced accuracy;
- fixed four-class registry;
- deterministic class ordering only for serialization, not weighting.

If a registered evaluation subset unexpectedly contains zero examples for a
registered class, the formal path must
`STOP_AND_REPORT_PROTOCOL_INTEGRITY_ERROR` rather than silently dropping the
class.

Scientific quantities affected:

- all `BA`-derived quantities, including `S_diag` and `G_eval`;
- downstream routing.

## Scientific Consequence Ledger

```text
GAP-001 -> rho_secondary
GAP-002 -> exact permutation p-value and RQ3 support flag
GAP-004 -> A_sigma, A_mu_sigma, G_eval, downstream routing
GAP-005 -> D/G support classification and routing
GAP-006 -> all BA-derived quantities including S_diag and G_eval
```

## Result-Conditioned Justification

This clarification does not reference:

- actual OLMo `S_diag` values;
- actual OLMo `G_eval` values;
- actual `rho`;
- actual p-values;
- replication strength;
- Paper-A favorability.

No such outcome has been observed.

## Binding

The SHA-256 values for this Markdown file, the JSON companion, and the
validator are computed after final content is frozen. Future executor
qualification and recovery authorization must bind these hashes in addition to
the original Task-100A authority hashes.
