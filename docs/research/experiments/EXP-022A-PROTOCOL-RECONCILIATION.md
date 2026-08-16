# EXP-022A Protocol Reconciliation

## General status

EXP-022A is a new clean-state mechanism-diagnosis experiment.

It is not:

- an EXP-021 retry;
- Stage-P;
- an intervention-propagation experiment;
- a functional-binding experiment.

Current core question:

Does late clean-state fixed source-class readout degradation reflect:

1. featurewise calibration drift;
2. readout-coordinate remapping;
3. held-out source-class linear decodability decline;
4. mixed / split-heterogeneous behavior;
5. indeterminate evidence?

## Authority Extraction A - Label Semantics

- `STATUS = EXP022A_091A_LABEL_SEMANTICS_RESOLVED`
- Class universe: `logic`, `causality`, `analogy`, `definition`
- Stage-Q `y_true = SOURCE_SEMANTIC_CLASS`
- Stage-Q predicted-class role: `SOURCE_SEMANTIC_CLASS`
- `source class = intrinsic source-item semantic identity`
- `target class = directed intervention destination`
- `source_class == y_true = PROVED_EQUIVALENT`
- `target_class == y_true = PROVED_DISTINCT`
- `EXP-018 target_probability target vs Stage-Q y_true = DISTINCT_ROLE`
- `original/paraphrase y_true semantic class = INVARIANT`
- Do not infer source-family identity from this invariance.

## Authority Extraction B - Intervention and State Semantics

- `STATUS = EXP022A_091B_INTERVENTION_SEMANTICS_RESOLVED`
- Historical intervention direction: `delta_task = centroid_target_FIT - centroid_source_FIT`
- Direction uses split-specific FIT centroids.
- Historical TASK intervention: `h' = h + beta * delta_(s->t)`
- `EXP-018 / EXP-020A intervention = offline held-out representation manipulation`
- `EXP-021 Stage-Q = NO INTERVENTION`
- `Stage-Q X = BASELINE_SOURCE_STATE`
- `Stage-Q states = clean unmodified forward representations`
- `Stage-Q measurement role = SOURCE_CLASS_READOUT_ON_NONINTERVENED_STATES`
- `target acquisition = NOT OBSERVABLE`
- `Stage-Q baseline availability = BASELINE_ONLY`
- `EXP-021 relation to EXP-018/020 intervention object = different operational measurement construct`

Clarification: different operational construct does not mean unrelated broader
research question.

## Corrected EXP-021 / 090Z interpretation

- `EXP021 Q3 = QUALIFICATION_FAILED`
- Result SHA-256: `833002c8e8bf47883bbab2063c4dfe7d91346a1c055ac5df4d50357cb061b851`
- Consumption SHA-256: `eb1fd673569c914e1a23386df021476f6c155a17b3fa7fc7b3df9e06f1abb96a`

Directly measured:

- clean-state fixed source-semantic-class readout degradation across depth

Not directly measured:

- intervention propagation
- target acquisition
- perturbation transport
- coordinate-remapping mechanism
- information disappearance
- functional binding

Status classification:

- `DIRECTLY_MEASURED`: fixed source-class readout degradation
- `CONSISTENT_BUT_NOT_IDENTIFIED`: source-class linear decodability change, readout-coordinate remapping, representation/statistical change
- `NOT_MEASURED`: target acquisition, intervention perturbation transport, functional binding

090Z is not described as intervention propagation.

## Authority Extraction C - Source-Family Mapping

- `EXP022A_091C_SOURCE_FAMILY_MAPPING_BLOCKED`
- Controlled artifact: `experiments/exp003/prompts_controlled.json`
- Controlled artifact SHA-256: `72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`
- Fields: `id`, `group`, `variant_type`, `text`
- Explicit pair/base/source-family field: `none`
- Pairing classification: `ID_GRAMMAR_ONLY`
- ID grammar authority: `false`
- Historical production treats original/paraphrase as explicit class-balanced FIT/EVAL ID sets, not authoritative paired source families.
- Complementary split relation: `CLASS_BALANCED_BUT_NOT_FAMILY_SWAP`
- Historical source-family cluster: `NOT_SUPPORTED`
- Derived historical family manifest eligibility: `false`

Do NOT treat `*_orig_01` and `*_para_01` as the same source family without a
future new frozen authority.

## Statistical consequence of 091C

Retired design candidate:

```text
SOURCE-FAMILY SUPER-CLUSTER BOOTSTRAP = REJECTED FOR CURRENT HISTORICAL DATA
```

This is a design correction, not a scientific result.

Replacement current statistical candidate:

```text
SPLIT-WISE EVAL-ITEM CLUSTERING
```

For each split separately:

- cluster unit candidate = held-out EVAL record identity
- all repeated measurements for that record stay together
- all layers stay together
- all readout conditions stay together

Class stratification candidate:

- 3 logic
- 3 causality
- 3 analogy
- 3 definition

Do NOT yet freeze:

- bootstrap replicate count
- RNG seed
- CI method

## A/B split relation

- `A/B source-family independence = UNRESOLVED`

Therefore prohibit in current design:

- treating A+B as 24 independent observations
- source-family paired A/B bootstrap
- claims that A/B are exact paired family swaps

Current inferential candidate:

- analyze A separately
- analyze B separately
- use cross-split concordance/heterogeneity as a replication diagnostic

Do NOT define exact concordance threshold yet.

## Current EXP-022A design candidate

Record as `NEW_FREEZE_PENDING`:

- clean-state only
- readout ladder:
  - `A0 Fixed`
  - `A1 Featurewise-Affine Recalibration`
  - `A2 Layer-wise Linear Refit`
- Reference: `block16 / hidden_states[17]`
- Candidate primary final endpoint: `final block pre-final-RMSNorm`
- Full L16-L27 trajectory: `secondary`
- post-final-RMSNorm: `secondary mechanistic endpoint`

Primary candidate estimands:

```text
G_scale  = BA_recal - BA_fixed
G_refit  = BA_refit - BA_fixed
G_noncal = BA_refit - BA_recal
R_refit  = BA_refit_final - BA_refit_reference
```

All remain `NOT YET FROZEN`.

## Reconciliation matrix

- semantic universe: `REUSE_FROZEN`
- source label semantics: `RESOLVED / REUSE_FROZEN`
- target label semantics: `RESOLVED / DISTINCT ROLE`
- Stage-Q clean-state semantics: `RESOLVED / REUSE_FROZEN`
- historical intervention semantics: `RESOLVED / REUSE_FROZEN FOR HISTORICAL CONTEXT`
- historical source-family mapping: `BLOCKED / NOT AVAILABLE`
- source-family bootstrap: `NOT SUPPORTED FOR CURRENT DATA`
- split-wise held-out-item clustering: `RECONCILE_THEN_FREEZE`
- qualification-rule portability: `RESOLVED / PARTIALLY_PORTABLE`
- Fixed readout: `RECONCILE_THEN_FREEZE`
- Featurewise recalibration: `NEW_FREEZE_PENDING`
- Layer-wise refit: `NEW_FREEZE_PENDING`
- structured alignment: `OUT_OF_SCOPE_022A`
- perturbation transport: `OUT_OF_SCOPE_022A`
- functional binding: `OUT_OF_SCOPE_022A`

## Frozen authority references

- EXP-021 preregistration SHA-256: `2ea9c54a49c41b3c1c8e6c39b029dc333d3ee6753ae0608603d6365ae063301a`
- EXP-021 amendment SHA-256: `c026587c90b74d75e9f395001f94732d41f3b550c22247e5613cc6d3cc880635`
- EXP-021 reconciliation SHA-256: `4630a253db1454c9b6cb0850bf6f99cf61781d44e48e37994cba8e1c6d47da95`
- EXP-018 validation conditions SHA-256: `4ce4ebb1af318e7c25725980680c0dc62762e20790adcb7abf2026130f0d4169`
- EXP-020A frozen config SHA-256: `f760f781b4b744a10938eb4de032e0cc345a021706821ecf0ca8523f5d57e667`


## Authority Extraction D - Qualification-Rule Portability

- `EXP022A_091D_QUALIFICATION_RULE_PORTABILITY_RESOLVED`
- Overall Stage-Q ruleset portability: `PARTIALLY_PORTABLE`

Portability results:

- `TRUE_CLASS_SUPPORT = PORTABLE_AS_STRUCTURAL_CHECK`
- `CLASS_MAPPING = PORTABLE_AS_TECHNICAL_VALIDITY`
- `PREDICTED_CLASS_COVERAGE = PORTABLE_AS_SECONDARY_HISTORICAL_BENCHMARK`
- `CORRECT_COUNT_THRESHOLD = PORTABLE_AS_SECONDARY_HISTORICAL_BENCHMARK`
- `CP_LOWER_BOUND = PORTABLE_AS_SECONDARY_HISTORICAL_BENCHMARK`
- `CHECKPOINT_ROLE_PORTABILITY = PARTIAL`
- `GLOBAL_GATE = NOT_PORTABLE_STAGE_Q_SPECIFIC_GATE`
- `NO_EVAL_RULE = NOT_PORTABLE_OUT_OF_SCOPE`
- `NO_INTERVENTION_CONSTRUCT = COMPATIBLE_CLEAN_STATE_CONSTRUCT`
- `CONTRAST_BASED_PREREGISTRATION = AVAILABLE`

## Historical Stage-Q benchmarks

`HISTORICAL_STAGE_Q_BENCHMARK_ONLY`
`NOT_EXP022A_PRIMARY_GATE`

- checkpoint correct threshold: `>= 7 / 12`
- historical equivalent accuracy: `>= 0.583333...`
- Clopper-Pearson: `95%` two-sided lower bound, strictly `> 0.25`
- predicted-class coverage: all four frozen predicted classes present
- Stage-Q checkpoint pass: coverage AND correct-count/CP rule
- Stage-Q global qualification: all required split/checkpoint cells pass

## Do-not-migrate rules

The following must NOT become EXP-022A primary scientific gates:

- `correct >= 7 / 12`
- `CP lower bound > 0.25`
- `predicted-class coverage pass`
- `all-required-checkpoints pass`
- `joint A/B Stage-Q qualification gate`
- `FIT-only / no-EVAL scope`

Using them as EXP-022A primary scientific gates would conflate the
measurement-qualification estimand with the new held-out mechanism estimand.

## Reusable structural/technical requirements

- frozen four-class universe/order
- complete expected class support
- `classifier.classes_` integrity
- explicit probability-column mapping
- probability width = 4
- finite probabilities
- valid probability normalization
- one complete prediction row per required `split x EVAL item x layer x readout condition`
- identity/provenance consistency

Historical rules remain separate from future NEW_FREEZE additions.

## Authority-gate closure summary

- `091A LABEL SEMANTICS = RESOLVED`
- `091B STATE / INTERVENTION SEMANTICS = RESOLVED`
- `091C HISTORICAL SOURCE-FAMILY MAPPING = BLOCKED / NOT AVAILABLE`
- `091D QUALIFICATION-RULE PORTABILITY = RESOLVED`

`HISTORICAL_AUTHORITY_EXTRACTION_PHASE = COMPLETE`

091C BLOCKED is itself the final resolved historical conclusion: the historical
dataset does not provide authoritative source-family pairing.


## Current EXP-022A design boundary

Scientific object:

- clean, non-intervened hidden states

Measurement target:

- `SOURCE_SEMANTIC_CLASS`

Historical source-family pairing:

- `NOT AVAILABLE`

Current inferential unit candidate:

- held-out EVAL record within each split

A/B relationship:

- do not treat as 24 independent observations
- analyze separately unless future preregistration supplies another authority-supported treatment

Current readout ladder candidates:

- `A0 Fixed Frame`
- `A1 Featurewise-Affine Recalibration`
- `A2 Layer-wise Linear Refit`

All remain `NEW_FREEZE_PENDING`.

## Primary scientific route

EXP-022A should be preregistered around held-out paired contrasts, not around
Stage-Q qualification pass/fail.

Candidate contrasts, explicitly still `NOT FROZEN`:

```text
G_scale  = BA_recal - BA_fixed
G_refit  = BA_refit - BA_fixed
G_noncal = BA_refit - BA_recal
R_refit  = BA_refit_final - BA_refit_reference
```

`CONTRAST_BASED_PREREGISTRATION_AVAILABLE`

Do not select CI thresholds or significance criteria here.

## NEW_FREEZE_REQUIRED checklist

- exact EXP-022A FIT and EVAL record identities
- exact per-split EVAL balance
- reference-layer fitting procedure
- exact Fixed definition
- exact Featurewise-Affine Recalibration definition
- exact Layer-wise Refit definition
- depth/checkpoint set
- primary endpoint
- secondary endpoints
- balanced-accuracy definition
- paired estimands
- split-wise statistical procedure
- bootstrap or alternative inference method
- RNG seed if applicable
- replicate count if applicable
- CI method
- multiplicity policy
- split-concordance interpretation
- scientific outcome categories
- technical-validity gate
- result schema
- stopping rule
- authorization lifecycle

Do not fill these values in Task-091DP.
