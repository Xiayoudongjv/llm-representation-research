# EXP-024 Preregistration Draft

Status: `DRAFT_NOT_FROZEN`

This is a prospective protocol draft for EXP-024. It is not a frozen
preregistration, formal dataset, runner, authorization, or scientific result.
Canonical historical evidence outranks this document.

## Experiment Identity

- Experiment: `EXP-024`
- Working name: Independent Condition-Level Calibration Susceptibility Test
- Scientific hypothesis: `HYP_CALIBRATION_CONDITIONAL_002`
- Hypothesis status: `ACTIVE_PROSPECTIVE_NOT_TESTED`
- Primary design selected in Task-097B: `B`
- Protocol stage: `PROTOCOL_DRAFTED_NOT_FROZEN`

## Research Question

Can condition-level fixed-readout degradation measured on an independent
DIAGNOSTIC partition prospectively predict featurewise recalibration benefit
on source-family-independent confirmatory EVAL data?

This is not a third generic calibration replication. It tests whether
calibration susceptibility can be identified before the confirmatory EVAL
outcome is observed.

## Primary Scientific Unit

The primary scientific/inferential unit is:

```text
condition / panel condition
```

Not an individual row, prediction, Transformer layer, semantic class, or source
family.

Each condition contributes exactly one primary diagnostic score `S_diag(c)` and
one primary confirmatory score `G_eval(c)`. Statistical inference occurs across
the prospectively frozen condition panel.

## Condition Panel

- `EXP024_N_CONDITIONS = 10`
- `EXP024_SEMANTIC_CLASS_COUNT = 4`
- Semantic classes: `logic`, `causality`, `analogy`, `definition`.
- Panel specification: `experiments/exp024/condition_panel_spec.json`
- Panel status: `DRAFT_NOT_FROZEN`
- Reference/canonical expression is a separate reference basis, not one of the
  ten panel units.

The ten conditions are surface/realization transformations that preserve the
intended semantic class:

| Condition ID | Short name |
| --- | --- |
| `c01_lexical_relex` | Controlled lexical re-expression |
| `c02_syntactic_restructure` | Syntactic restructuring |
| `c03_controlled_compression` | Controlled compression |
| `c04_controlled_elaboration` | Controlled elaboration |
| `c05_relation_explicit` | Relation-explicit wording |
| `c06_relation_implicit` | Relation-implicit wording |
| `c07_register_formal` | Formal-register shift |
| `c08_register_informal` | Informal-register shift |
| `c09_neutral_distractor_prefix` | Neutral distractor prefix |
| `c10_anaphoric_reference` | Anaphoric reference variation |

Full transformation rules, allowed/forbidden edits, semantic-equivalence
requirements, and known confounds are in `condition_panel_spec.json`.

### Reference-Condition Policy

The canonical/original expression is a separate fixed-readout reference basis,
not one of the susceptibility panel units. This keeps the panel units
comparable through a common reference framework rather than making the
reference expression compete as another heterogeneous condition.

## FIT / DIAGNOSTIC / EVAL Allocation

For each condition and semantic class:

- FIT: `6` source families
- DIAGNOSTIC: `8` source families
- EVAL: `8` source families

Total source families:

```text
10 conditions * 4 classes * (6 + 8 + 8) = 880
```

Total stored records:

```text
880 source families * 2 record roles = 1760 records
```

The two record roles are `reference_form` and `condition_realization`.

Independence requirements:

- `FIT intersect DIAGNOSTIC = empty`
- `FIT intersect EVAL = empty`
- `DIAGNOSTIC intersect EVAL = empty`
- `EXP024_CROSS_PARTITION_FAMILY_OVERLAP = 0`
- `EXP024_CROSS_CONDITION_FORBIDDEN_FAMILY_OVERLAP = 0`

A source family belongs to exactly one `condition * partition` cell. No
source-family-derived sibling record crosses partitions.

## Source-Family Sampling and Allocation

All base source families come from one common prospectively defined semantic
content universe.

Allocation algorithm:

1. Build a class-balanced pool of candidate source families.
2. For each condition, assign source families to `condition * partition` cells
   without replacement.
3. Balance class counts within every cell.
4. Use deterministic stratified assignment with RNG seed
   `EXP024_ALLOC_RNG_SEED = 20260818`.
5. Do not assign easy families to one condition and hard families to another.
6. Freeze the assignment before any model execution.

No source family may be reused across conditions.

## Model and Checkpoints

Primary model:

- Model name: `Qwen/Qwen3-1.7B`
- Model snapshot: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- `EXP024_SECOND_MODEL_REQUIRED = false`

Checkpoints:

- Primary reference checkpoint: `block16_pre_final_rmsnorm`
- Primary final checkpoint: `block27_pre_final_rmsnorm`
- `block27_post_final_rmsnorm`: secondary descriptive only
- Full trajectory `block16` through `block27`: descriptive secondary only

Layers are not primary independent observations.

## Representation Object

Use clean, non-intervened, last-valid-token hidden representations at the
frozen checkpoint. Preserve qualified EXP-023 tokenizer/hook semantics unless a
separate prospective engineering compatibility review establishes necessity.

## Global Reference Readout

One fixed reference semantic-class readout `C_ref` is trained only from FIT
reference-form records at `block16_pre_final_rmsnorm`.

`C_ref` is pooled across condition-balanced FIT families to preserve a common
readout interface across conditions.

Do not fit a different classifier for each condition.

## Reference Scaler

From FIT reference-form representations at `block16_pre_final_rmsnorm`,
estimate:

```text
mu_ref
sigma_ref
```

using the frozen `StandardScaler` contract. No DIAGNOSTIC or EVAL statistic may
enter reference fitting. The reference scaler remains frozen across conditions.

## Classifier Contract

Use the frozen EXP-023-compatible classifier contract:

```text
LogisticRegression:
  solver = lbfgs
  penalty = L2
  C = 1
  fit_intercept = true
  tol = 1e-4
  class_weight = none
  dual = false
  max_iter = 1000
  warm_start = false
```

No hyperparameter tuning is allowed. Outputs must be mapped through
`classifier.classes_`.

## Condition-Specific Recalibration

For each condition `c`, estimate from FIT(c) condition-realization
representations at `block27_pre_final_rmsnorm`:

```text
mu_final,c^FIT
sigma_final,c^FIT
```

No DIAGNOSTIC or EVAL feature statistic may enter calibration fitting.

Calibration conditions:

### A0

```text
z_A0 = (h - mu_ref) / sigma_ref
C_ref(z_A0)
```

### A_mu

```text
z_A_mu = (h - mu_final,c) / sigma_ref
C_ref(z_A_mu)
```

### A_sigma

```text
z_A_sigma = (h - mu_ref) / sigma_final,c
C_ref(z_A_sigma)
```

### A_mu_sigma

```text
z_A_mu_sigma = (h - mu_final,c) / sigma_final,c
C_ref(z_A_mu_sigma)
```

`A_mu`, `A_sigma`, and `A_mu_sigma` are defined per condition. `C_ref` is never
refit.

## Primary Diagnostic

For each condition `c`:

```text
S_diag(c) =
    BA_A0(block16_pre_final_rmsnorm, DIAG_c)
  - BA_A0(block27_pre_final_rmsnorm, DIAG_c)
```

Both terms use the same global reference scaler and fixed `C_ref`, evaluated on
the condition-realization records in the DIAGNOSTIC partition.

Interpretation:

```text
higher S_diag(c) = greater independent diagnostic fixed-readout degradation
```

This is the preferred positive susceptibility direction.

## Primary Confirmatory Outcome

For each condition `c`:

```text
G_eval(c) =
    BA_A_mu_sigma(block27_pre_final_rmsnorm, EVAL_c)
  - BA_A0(block27_pre_final_rmsnorm, EVAL_c)
```

Interpretation:

```text
higher G_eval(c) = greater calibration rescue on untouched EVAL families
```

DIAGNOSTIC data must not enter this calculation.

## Algebraic Independence

`S_diag(c)` uses only DIAGNOSTIC source families.

`G_eval(c)` uses only EVAL source families.

Although the formulas use analogous `A0` constructs, they do not share
individual observations or source families.

```text
EXP024_SHARED_EVAL_A0_ALGEBRAIC_DEPENDENCY = false
```

This is the explicit correction to the EXP-023 shared-A0 limitation.

## Primary Hypothesis

Across the prospectively defined condition panel, conditions with larger
`S_diag(c)` will tend to have larger `G_eval(c)`.

This is an association/predictive susceptibility hypothesis. It is not a causal
claim that readout degradation causes calibration benefit.

## Primary Statistic

```text
rho_primary = Spearman(S_diag(c), G_eval(c))
```

across the frozen condition panel.

Tie handling uses standard average ranks. No flexible regression model is used
as the primary test.

## Primary Exact Test

Use a one-sided exact permutation test under the directional alternative:

```text
rho > 0
```

Permute the pairing between the frozen `S_diag` condition scores and the frozen
`G_eval` condition scores.

For `N = 10`, enumerate all:

```text
10! = 3,628,800
```

permutations. Compute:

```text
p = count(rho_perm >= rho_observed) / N!
```

including the observed pairing.

Do not use an asymptotic Spearman p-value for the primary gate. Do not switch to
Monte Carlo permutation after outcome observation merely for convenience.

## Primary Support Rule

```text
PRIMARY_SUPPORTED =
    rho_primary > 0
    AND exact_one_sided_p <= 0.05
```

No post-hoc minimum rho threshold is added.

## Primary Claim Boundary

If supported, the allowed conclusion is:

> An independent diagnostic measure of fixed-readout degradation prospectively
> tracks condition-level calibration susceptibility within the frozen condition
> panel.

Not allowed:

- degradation causes rescue
- universal calibration predictor
- general coordinate transport
- cross-model universality

## Secondary Analyses

Prespecified secondary/descriptive analyses:

- `S_diag(c)` versus `G_mu(c)` and `G_sigma(c)`.
- FIT/DIAGNOSTIC mean-shift magnitude.
- FIT/DIAGNOSTIC scale-shift magnitude.
- Margin degradation summary.
- Reference balanced-accuracy level per condition.
- Full-depth descriptive trajectory from block16 through block27.
- Bootstrap uncertainty summaries.

Secondary diagnostics must not replace the primary `S_diag` after outcome
observation. No large diagnostic fishing expedition is permitted.

## A_mu / A_sigma / A_mu_sigma

The primary confirmatory calibration outcome remains `A_mu_sigma - A0`.

`A_mu` and `A_sigma` are retained for preregistered descriptive decomposition.

The primary is not changed to mean-only because EXP-023 Split A favored `A_mu`
descriptively.

## Condition-Level Secondary Outcomes

Prespecified condition-level secondary quantities:

```text
G_mu(c) = BA(A_mu, EVAL_c) - BA(A0, EVAL_c)
G_sigma(c) = BA(A_sigma, EVAL_c) - BA(A0, EVAL_c)
G_joint_over_mu(c) = BA(A_mu_sigma, EVAL_c) - BA(A_mu, EVAL_c)
G_joint_over_sigma(c) = BA(A_mu_sigma, EVAL_c) - BA(A_sigma, EVAL_c)
```

These are descriptive. Multiple confirmatory significance tests are not
created.

## Bootstrap Policy

Bootstrap is secondary only.

If used:

- resample source families within `condition * class * partition`.
- Preserve class counts.
- Keep paired condition calculations where applicable.
- Use `B = 10000`.
- Use RNG seed `EXP024_BOOTSTRAP_RNG_SEED = 20260818`.
- Report percentile intervals as secondary uncertainty summaries.

Bootstrap intervals do not replace the across-condition exact permutation
primary test.

## Condition Validity Review

Every condition must pass review before formal dataset generation for:

- semantic-class preservation
- transformation-rule consistency
- cross-class applicability
- surface-template leakage
- condition distinguishability
- difficulty confounds
- class-label leakage
- historical outcome-driven selection

Verdict categories:

- `PASS`
- `MODERATE_NONBLOCKING_LIMITATION`
- `BLOCKING_CONSTRUCT_DEFECT`

Any blocking condition must be replaced before dataset freeze and model
execution.

## Negative-Result Taxonomy

Predefined interpretation cases:

- `CASE A`: `rho > 0` and `p <= 0.05`
  - Independent condition-level susceptibility prediction supported.
- `CASE B`: `rho > 0` and `p > 0.05`
  - Directional signal present but confirmatory support absent.
- `CASE C`: `rho <= 0`
  - The selected diagnostic does not predict calibration susceptibility.
- `CASE D`: `S_diag` has near-zero variation across conditions
  - The panel failed to generate measurable susceptibility heterogeneity.
- `CASE E`: `G_eval` has near-zero variation
  - No meaningful variation in calibration benefit; the conditional rescue
    mechanism cannot be tested.

Cases D and E are not evidence that representations are universally stable.

## Falsification

`HYP_CALIBRATION_CONDITIONAL_002` is considered `NOT_SUPPORTED_BY_EXP024` if
the primary directional association is absent under the frozen test.

Do not rescue with another diagnostic, layer, model, mean-only calibration, or
selected condition subset unless separately preregistered as non-primary.

## Condition-Panel Generalization Boundary

Even if the primary test succeeds, inference is bounded to:

- the prospectively frozen condition panel
- the controlled semantic task universe
- the frozen Qwen3-1.7B model

Do not claim population-level universality over all possible linguistic
conditions.

## Paper-A Contribution If Positive

If supported, the provisional Paper-A addition is:

> Calibration heterogeneity is not merely retrospective: an independent
> diagnostic measurement prospectively identifies condition-level
> susceptibility to deep fixed-readout mismatch and subsequent recalibration
> benefit.

This wording remains provisional. Do not move it into `CLAIM-LEDGER.md` as
supported before EXP-024 completes.

## Paper-A Interpretation If Negative

If unsupported:

Paper-A remains viable with the existing bounded claim.

Interpretation:

> Simple condition-level diagnostic degradation is insufficient to predict
> calibration susceptibility.

This would narrow rather than invalidate the current Paper-A story.

## Top-Conference Implication

A positive clean EXP-024 would materially improve mechanism-level coherence.

It does not automatically equal `ICLR_READY`, `NEURIPS_READY`, or
`ICML_READY`. CCF-A readiness would still require later judgment about breadth
and generalization.

## Dataset Schema

- Structural schema draft: `experiments/exp024/data_schema.json`
- Validation specification: `docs/experiments/EXP-024-DATASET-SPEC.md`
- Formal dataset is not created in this task.

## Leakage Controls

- FIT, DIAGNOSTIC, and EVAL are source-family disjoint.
- No direct/simple paraphrase lineage crosses partitions.
- No EVAL statistic enters reference fitting or calibration fitting.
- The fixed reference classifier and scaler are frozen before EVAL access.
- No layer-specific classifier refitting is used.
- No flexible meta-model is used.
- Dataset, condition assignments, formulas, statistic, and support rule are
  frozen before any model-derived representation or result.
- Formal prompt text exposure and formal-data inference counts will be tracked
  in later runner/qualification tasks.

## No Model / Data Outcome in This Task

- `FORMAL_DATASET_CREATED = false`
- `MODEL_LOAD_PERFORMED = false`
- `TOKENIZER_LOAD_PERFORMED = false`
- `REPRESENTATION_EXTRACTION_PERFORMED = false`
- `SCIENTIFIC_OUTCOME_OBSERVED = false`
- `EXP024_PREREGISTRATION_FROZEN = false`
- `EXP024_AUTHORIZATION_CREATED = false`

## Next Step

If protocol review returns `READY_FOR_DATASET_CONSTRUCTION`, proceed to
Task-097D to construct and independently review the controlled dataset. Do not
generate the dataset, freeze the preregistration, implement the runner, or run
the model here.
