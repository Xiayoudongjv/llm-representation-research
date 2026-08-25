# Paper A EXT-B Preregistration

Status: `FROZEN_PRE_DATA_PRE_MODEL_OUTCOME`

This is a new prospective study classified as
`POST_EXT_A_FEASIBILITY_PRE_MODEL_OUTCOME_NEW_PROSPECTIVE_STUDY`. It is not a
continuation, amendment, reduction, rescue, or temporal continuation of
EXT-A. EXT-A terminated before model inference because its prospectively
required four-task panel could not be completed. No EXT-B model outcome was
available at this freeze.

## Scientific question

Do the registered structural cross-depth operational-compatibility profiles
observed in the Paper-A core remain stable on a newly prospectively constructed
three-class external semantic panel? This tests panel/task robustness of the
registered structural profile summaries. It does not test absolute accuracy
equality, semantic equivalence, representation identity, architectural
causation, universal task invariance, directionality, CKA/SVCCA, or behavioral
control.

## Frozen panel

The model panel is exactly:

- `Qwen/Qwen3-1.7B` — normalized-depth denominator 27;
- `allenai/OLMo-2-0425-1B-Instruct` — denominator 15;
- `Meta-Llama-3.2-1B-Instruct` — denominator 15.

The task panel is exactly:

- `TF_SPATIAL` / `exta_tf_spatial`;
- `TF_QUANTITATIVE` / `exta_tf_quantitative`;
- `TF_MEREOLOGICAL` / `exta_tf_mereological`.

Temporal is excluded. No replacement fourth task or new model is allowed.
Each record has one global three-class label. `reference` and `realization` are
record roles; conditions are surface-realization conditions, not targets.

## Dataset construction

Each task contributes 220 source families and 440 records, with two records per
family. The three-task panel therefore contains 660 families and 1320 records
with exact class balance. Per task, the frozen split is:

| split | families | records |
|---|---:|---:|
| FIT | 60 | 120 |
| DIAGNOSTIC | 80 | 160 |
| EVAL | 80 | 160 |

The ten inherited conditions allocate 6, 8, and 8 families per task to FIT,
DIAGNOSTIC, and EVAL respectively. The condition identities are frozen in the
JSON protocol artifact.

Source policies are frozen before production:

- Spatial uses only allowed structured StepGame relation fields; stories,
  questions, answers, distractors, reasoning chains, and final benchmark text
  are forbidden.
- Quantitative uses deterministic programmatic numeric comparison, with no
  outcome-adaptive ranges or filtering.
- Mereological uses only WordNet 3.0 meronymy/holonymy structure, oriented as
  `ARG_A = part/member/substance` and `ARG_B = whole`; glosses, definitions,
  examples, and lexicographer prose are forbidden.

The construction order is source binding, structured-field extraction,
canonicalization, family/record construction, deterministic realizations,
deduplication/leakage checks, family split assignment, independent validation,
and hash binding. No model output may affect construction.

## Fail-closed 3-of-3 gate

Each task must independently pass this full chain:

`SOURCE_INPUT_VALID -> SOURCE_BANK_VALID -> DATASET_SHAPE_VALID ->
PAIRING_VALID -> SEMANTIC_VALID -> LEAKAGE_VALID -> SPLIT_VALID -> HASH_BOUND`

Only after all three chains pass may `EXT_B_DATA_PANEL_READY=true`. A failure
in any task is `EXT_B_SOURCE_OR_DATASET_FAILURE`; there is no two-task fallback,
task substitution, adaptive count/split change, temporal replacement, or
outcome-based filtering. Model inference is prohibited before the gate passes.

## Readout and metrics

The primary unit is exactly `MODEL_LEVEL_THREE_CLASS_EXTERNAL_PANEL_PROFILE`,
with three model-level profiles rather than nine task-level profiles. For each
model and source layer, fit one FIT-only global three-class readout over all
three classes: `StandardScaler(with_mean=true, with_std=true)` followed by
multinomial `LogisticRegression(solver=lbfgs, penalty=L2, C=1.0,
fit_intercept=true, tol=0.0001, max_iter=1000)`. No task-specific or one-vs-rest
primary classifiers are allowed.

For source layer `i`, target layer `j`, and condition `c`:

- `C0(i,j,c)` is direct EVAL balanced accuracy;
- `Cself(i,c) = C0(i,i,c)`;
- `D(i,j,c) = Cself(i,c) - C0(i,j,c)`;
- `Ccal(i,j,c)` is the EVAL result after frozen FIT-only `A_mu_sigma`
  calibration;
- `R(i,j,c) = Ccal(i,j,c) - C0(i,j,c)`.

Balanced accuracy is the macro-average of per-class recall over the three
frozen labels. Distance support is `POSITIVE_SUPPORTED` only when Spearman rho
between pooled off-diagonal `Dbar` and absolute normalized depth distance, with
average-rank ties, has a positive estimate and a positive one-sided 95% cluster
bootstrap lower bound. SDI is
`(SOURCE_VARIANCE-TARGET_VARIANCE)/(SOURCE_VARIANCE+TARGET_VARIANCE)` using
population variance (`ddof=0`); source/target dominance requires the matching
sign and a one-sided interval excluding zero. LOW-D is the frozen diagnostic
off-diagonal `Dbar <= 0` mask, with support requiring a positive point estimate
and positive one-sided lower bound for the EVAL `R` estimand.

The carrier is the observational output of each decoder block before final
model normalization. Normalized depth is `block_index/(num_blocks-1)`, with
all logical decoder blocks eligible. LOW-D selection uses DIAGNOSTIC quantities
only and is frozen before EVAL recovery aggregation.

## Profile matching and routing

Each model profile has exactly three components: distance-degradation state,
SDI/source-target dominance state, and LOW-D recovery support state. The frozen
core references are:

| model | distance | SDI | LOW-D recovery |
|---|---|---|---|
| Qwen | `POSITIVE_SUPPORTED` | `TARGET_DOMINANT` | `NOT_SUPPORTED` |
| OLMo | `POSITIVE_SUPPORTED` | `SOURCE_DOMINANT` | `SUPPORTED` |
| Llama | `POSITIVE_SUPPORTED` | `TARGET_DOMINANT` | `SUPPORTED` |

`MATCH_m=1` only when all three components exactly match the corresponding
reference. Partial matches are retained and reported, but do not count as
replication. Weighted similarity, majority rescue, favorable-component
selection, tolerance, and near-match relabeling are forbidden.

Let `K = MATCH_Qwen + MATCH_OLMo + MATCH_Llama`. The exhaustive routing is:

- `B0_MEASUREMENT_INVALID_OR_INCONCLUSIVE` if a required primary measurement
  is technically invalid or scientifically undefined;
- `B1_BROAD_EXTERNAL_PANEL_STABILITY` for `K=3`;
- `B2_MOSTLY_STABLE_WITH_MODEL_SPECIFIC_CHANGE` for `K=2`;
- `B3_LIMITED_EXTERNAL_PANEL_STABILITY` for `K=1`;
- `B4_BROAD_EXTERNAL_PANEL_PROFILE_CHANGE` for `K=0`.

Because the core and EXT-B have different class counts, raw `C0`, `Cself`,
`Ccal`, `D`, `R`, distance-rho, SDI, and LOW-D magnitudes are
`STRUCTURALLY_COMPARABLE_ONLY`. They are not numerically equivalent balanced
accuracy quantities across panels. The categorical three-component profile is
the preregistered cross-panel comparison.

Task-stratified outputs are secondary diagnostics from the same global
readout. They may localize class contributions, but cannot change a model
match, `K`, or routing. The permitted interpretation is: “Task-stratified
diagnostics localize which semantic classes contributed to the aggregate
external-panel result.”

## Dependence, bootstrap, and stop rule

Use 5000 source-family cluster bootstrap replicates with seed `20260819`,
`numpy.random.PCG64`, condition/task-class stratification, and preservation of
family, condition, and three-class balance. Layer pairs, records, and tasks are
not IID population observations; no inference over all possible tasks is
claimed.

After one technically valid EXT-B result, the study enters the final manuscript
phase. No new task, replacement task, temporal rescue, fourth model, primary
metric, profile component, or outcome-adaptive rescue experiment is permitted.
Technical recovery is allowed only when it leaves scientific semantics
unchanged.

## EXT-A and temporal disclosure

The main authority-level history is that EXT-A required four task families,
including temporal; temporal construction failed before the canonical panel was
completed; no EXT-A model inference occurred; and EXT-A was terminated rather
than reduced post hoc. EXT-B was conceived afterward as a new three-class
prospective study. The TEMP-V2 QLever runtime chain and TEMP-FEAS-002R V8
feasibility chain remain distinct; their counts are not combined here.

## Freeze boundary and next action

At this freeze: no dataset was generated, no model was loaded, no model
inference or scientific result exists, and no formal authorization was created
or consumed. The next lifecycle action is **`EXT_B_DATASET_CONSTRUCTION`**, not
model authorization.

## Authority files and hashes

The four machine-readable authorities are:

- `experiments/paper_a_ext_b/paper_a_ext_b_preregistration.json`
- `experiments/paper_a_ext_b/paper_a_ext_b_frozen_protocol.json`
- `experiments/paper_a_ext_b/paper_a_ext_b_outcome_routing.json`
- `experiments/paper_a_ext_b/paper_a_ext_b_authority_manifest.json`

The raw SHA-256 identities of the three machine-readable protocol authorities
at freeze are:

```text
paper_a_ext_b_preregistration.json = 8069439f96db96649a7bbbff3413b2ec6dda37a72d5bbb98a72934349c3e42f8
paper_a_ext_b_frozen_protocol.json = c67e8786f93d593dfd8ae70c1e1348758997baf097aed4e5393a4e30641a40ac
paper_a_ext_b_outcome_routing.json = 6e0ad230664e10b26849ef284fae11174093d2adf4d36eb79dc37201ab29e7f0
```

The authority manifest binds the exact raw SHA-256 of those three files, this
reviewer-facing document, and the inherited EXP-026 metric/result authorities,
EXP-027 design/result/manifest, EXT-A V3 content/source policies and
validators, the StepGame revision, the WordNet 3.0 archive, and the frozen
quantitative construction identity. The manifest's own raw SHA-256 is reported
in the final archive record; it is not embedded in itself or in this document,
avoiding a self-referential hash.

## Final flags

```text
EXT_B_PREREGISTRATION_CREATED = true
EXT_B_PROTOCOL_FROZEN = true
EXT_B_OUTCOME_ROUTING_FROZEN = true
EXT_B_AUTHORITY_MANIFEST_CREATED = true
EXT_B_CLASSIFICATION = POST_EXT_A_FEASIBILITY_PRE_MODEL_OUTCOME_NEW_PROSPECTIVE_STUDY
EXT_B_PRIMARY_UNIT = MODEL_LEVEL_THREE_CLASS_EXTERNAL_PANEL_PROFILE
EXT_B_PRIMARY_PROFILE_COUNT = 3
EXT_B_GLOBAL_THREE_CLASS_READOUT_VALID = true
EXT_B_RAW_BA_DIRECTLY_COMPARABLE_TO_CORE = false
EXT_B_STRUCTURAL_PROFILE_COMPARABLE_TO_CORE = true
EXT_B_EXACT_PROFILE_MATCH_FROZEN = true
EXT_B_ROUTING_FROZEN = true
EXT_B_BOOTSTRAP_FROZEN = true
EXT_B_3_OF_3_GATE_FROZEN = true
EXT_B_TASK_STRATIFIED_PRIMARY = false
EXT_B_TEMPORAL_INCLUDED = false
EXT_B_REPLACEMENT_TASK_ALLOWED = false
EXT_B_NEW_MODEL_ALLOWED = false
EXT_B_HARD_STOP_AFTER_FIRST_VALID_RESULT = true
EXT_B_MODEL_OUTCOMES_OBSERVED_AT_FREEZE = false
EXT_B_DATASETS_CREATED_AT_FREEZE = false
EXT_B_FREEZE_VALIDATION_PASS = true
EXT_B_NEXT_LIFECYCLE_ACTION = EXT_B_DATASET_CONSTRUCTION
DATASET_GENERATED = false
MODEL_INFERENCE_RUN = false
SCIENTIFIC_RESULT_CREATED = false
AUTHORIZATION_CREATED_OR_CONSUMED = false
TEMPORAL_RUNTIME_EXECUTED = false
CORE_CANONICAL_RESULT_MODIFIED = false
```
