# EXP-025 Formal Executor Specification

Classification: `GOVERNANCE_AND_IMPLEMENTATION_SPECIFICATION_ONLY`

This document specifies the frozen scientific/publication contract that the
future `_execute_formal_analysis` implementation must satisfy. It does not
implement `run_exp025.py`, does not create a formal authorization, and does not
execute formal science.

## Scope

The specification covers exactly the post-consumption formal execution path:

```text
run_formal
  -> authorization validation
  -> atomic authorization consumption
  -> _execute_formal_analysis
  -> canonical-result construction
  -> atomic publication boundary
```

Task 100D-D does not implement this path. The current implementation is the
fail-closed stub:

```text
_execute_formal_analysis raises
FORMAL_SCIENCE_NOT_AUTHORIZED_IN_100D_A
```

## Frozen Authorities

Primary EXP-025 frozen authorities:

| Authority | Path | SHA-256 |
| --- | --- | --- |
| Preregistration | `experiments/exp025/EXP-025-PREREGISTRATION.md` | `b83fd58ba36e55ab5c48577169e07a168d2a55df759d3131677cd86f2363e08e` |
| Frozen config | `experiments/exp025/exp025_frozen_config.json` | `2c9b1b8735378108c921a8ca99a1aab115b2a6669bf82e5ae0a9314dd4b62275` |
| Model selection | `experiments/exp025/EXP-025-MODEL-SELECTION.md` | `be28f7a2b1f460879e65f0ac911b01756d76b45069f8f438021412b76e954f80` |
| Checkpoint mapping | `experiments/exp025/EXP-025-CHECKPOINT-MAPPING.md` | `5f8c5df4aa849ceb7ee2ca8b1765aeeff46b96182426c97b81d320b3dda6a087` |
| Design validator | `experiments/exp025/validate_exp025_design.py` | `e87042535622e545c682a6f1019bf3703b4d0029d895e80c74269f7f1f26376d` |

Inherited EXP-024 scientific definitions:

- `docs/experiments/EXP-024-PREREGISTRATION.md`
- SHA-256: `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`

Inherited dataset/panel/schema identities:

| Authority | Path | SHA-256 |
| --- | --- | --- |
| Frozen dataset | `experiments/exp024/data/exp024_condition_panel_frozen.json` | `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404` |
| Condition panel | `experiments/exp024/condition_panel_spec.json` | `a3b8d565a94ef6041fbe6a29d73102ab4156cc19cfc07ccaeb06206d589f7954` |
| Data schema | `experiments/exp024/data_schema.json` | `e27c33c864c6305522aec0c92839634fb5885aeb50099372b9bf46da7f2fe3ec` |
| Freeze manifest | `experiments/exp024/exp024_frozen_manifest.json` | `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59` |

If any primary or inherited authority hash does not match before implementation,
the implementation gate is `BLOCKED_AUTHORITY_MISMATCH`.

## Global Scientific Invariants

The formal executor must preserve:

```text
EXP025_SCIENTIFIC_DESIGN_CHANGED = false
EXP025_FIT_DIAG_EVAL_FIREWALL = true
EXP025_MODEL_LOCKED = true
EXP025_CHECKPOINT_MAPPING_FROZEN = true
EXP025_GLOBAL_ROUTING_TABLE_FROZEN = true
EXP025_FORMAL_DATA_MODEL_INFERENCE_COUNT = 0 before consumption
```

Formal execution may use the frozen scientific dataset only after the
authorization is validated and atomically consumed.

## Endpoint 1: Frozen Dataset Loading and Identity Validation

Partition access: none for model inference.

Contract:

- Load `experiments/exp024/data/exp024_condition_panel_frozen.json`.
- Verify SHA-256:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`.
- Require record count `1760`, source-family count `880`, condition count `10`,
  semantic-class count `4`, and the frozen condition order.
- Require FIT/DIAGNOSTIC/EVAL source-family intersections to be empty.
- FIT `6`, DIAGNOSTIC `8`, EVAL `8` source families per condition and semantic
  class.
- Do not use record text for model inference before authorization consumption.

Status: `NOT_IMPLEMENTED`

## Endpoint 2: OLMo Tokenizer/Model Identity

Partition access: none.

Contract:

- Model ID: `allenai/OLMo-2-0425-1B-Instruct`.
- Exact revision: `48d788eca847d4d7548f375ad03d3c9312f6139e`.
- Local snapshot:
  `D:/AI_Cache/huggingface/hub/models--allenai--OLMo-2-0425-1B-Instruct/snapshots/48d788eca847d4d7548f375ad03d3c9312f6139e`.
- Load offline with `local_files_only=true`, `HF_HUB_OFFLINE=1`,
  `TRANSFORMERS_OFFLINE=1`.
- Expected `Olmo2ForCausalLM`, `model_type=olmo2`, `num_hidden_layers=16`,
  `hidden_size=2048`.
- Runtime dtype is `torch.bfloat16` on the available CUDA device.
- Tokenizer is the exact OLMo tokenizer; do not automatically apply the chat
  template.
- Tokenization contract:
  `tokenizer(text, return_tensors="pt")`, with `padding=false`,
  `truncation=false`, and the frozen special-token policy.

Status: `NOT_IMPLEMENTED`

## Endpoint 3: Reference-Checkpoint Representation Extraction

Partition access: FIT reference-form records only during formal execution.

Contract:

- Checkpoint: `block9_pre_final_rmsnorm`.
- Capture the OLMo decoder-layer output at layer index `9` before the final
  `model.norm`.
- Select the attention-mask-derived last valid non-padding token.
- Perform selection on the representation tensor device before CPU conversion.
- Convert with:
  `tensor.detach().cpu().to(torch.float32).numpy()`.
- Require final analysis representation dtype `float32` and shape `[2048]`.
- Hooks must be observational, non-mutating, and removed after use.

Status: `NOT_IMPLEMENTED`

## Endpoint 4: Final-Checkpoint Representation Extraction

Partition access: FIT, DIAGNOSTIC, or EVAL record text only in the respective
registered computation, and only after consumption.

Contract:

- Pre-final checkpoint: `block15_pre_final_rmsnorm`.
- Capture the OLMo decoder-layer output at layer index `15` before the final
  `model.norm`.
- Post-final descriptive checkpoint: `block15_post_final_rmsnorm`.
- Compute the post-final checkpoint as `model.model.norm(block15_pre_final_rmsnorm)`.
- Apply the same last-valid-token, device-bound selection, detach/CPU/float32
  conversion, and shape `[2048]` contract.
- Do not alias `block15_pre_final_rmsnorm` to
  `block15_post_final_rmsnorm`.

Status: `NOT_IMPLEMENTED`

## Endpoint 5: FIT-Only Reference Classifier Training

Partition access: FIT only.

Contract:

- Use FIT reference-form records at `block9_pre_final_rmsnorm`.
- Estimate `mu_ref` and `sigma_ref` from those representations using the frozen
  `StandardScaler` contract.
- Fit one global `C_ref_OLMo` using the frozen `LogisticRegression` contract:

```text
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

- Do not tune hyperparameters.
- Do not fit a different classifier for each condition.
- Do not use DIAGNOSTIC or EVAL records.
- Compute FIT reference balanced accuracy only for the frozen technical
  usability floor `0.75`; this floor is not a scientific outcome.

Status: `NOT_IMPLEMENTED`

## Endpoint 6: DIAGNOSTIC Fixed-Readout Evaluation

Partition access: DIAGNOSTIC only.

Contract:

- For each condition `c`, use DIAGNOSTIC condition-realization records.
- Compute `BA_A0(block9_pre_final_rmsnorm, DIAG_c)`.
- Compute `BA_A0(block15_pre_final_rmsnorm, DIAG_c)`.
- Both terms use the same global reference scaler and fixed `C_ref_OLMo`.
- Do not fit calibration parameters on DIAGNOSTIC.
- Do not use EVAL records.

Status: `NOT_IMPLEMENTED`

## Endpoint 7: S_diag(c)

Partition access: DIAGNOSTIC only.

Contract:

```text
S_diag(c) =
    BA_A0(block9_pre_final_rmsnorm, DIAG_c)
  - BA_A0(block15_pre_final_rmsnorm, DIAG_c)
```

`S_diag(c)` is one value per frozen condition. Higher values indicate greater
independent diagnostic fixed-readout degradation.

Status: `NOT_IMPLEMENTED`

## Endpoint 8: EVAL A0

Partition access: FIT for calibration statistics; EVAL for evaluation.

Contract:

For each condition `c`, evaluate EVAL condition-realization records at
`block15_pre_final_rmsnorm` with:

```text
z_A0 = (h - mu_ref) / sigma_ref
C_ref_OLMo(z_A0)
```

Compute `BA_A0(block15_pre_final_rmsnorm, EVAL_c)`.

Status: `NOT_IMPLEMENTED`

## Endpoint 9: EVAL A_mu

Partition access: FIT for calibration statistics; EVAL for evaluation.

Contract:

For each condition `c`, estimate `mu_final,c^FIT` from FIT condition-realization
representations at `block15_pre_final_rmsnorm`. Evaluate:

```text
z_A_mu = (h - mu_final,c) / sigma_ref
C_ref_OLMo(z_A_mu)
```

`sigma_ref` is retained. No EVAL statistic enters calibration fitting.

Status: `NOT_IMPLEMENTED`

## Endpoint 10: EVAL A_sigma

Partition access: FIT for calibration statistics; EVAL for evaluation.

Contract:

For each condition `c`, estimate `sigma_final,c^FIT` from FIT condition-realization
representations at `block15_pre_final_rmsnorm`. Evaluate:

```text
z_A_sigma = (h - mu_ref) / sigma_final,c
C_ref_OLMo(z_A_sigma)
```

`mu_ref` is retained. No EVAL statistic enters calibration fitting.

Status: `NOT_IMPLEMENTED`

## Endpoint 11: EVAL A_mu_sigma and G_eval(c)

Partition access: FIT for calibration statistics; EVAL for evaluation.

Contract:

For each condition `c`, estimate both `mu_final,c^FIT` and
`sigma_final,c^FIT` from FIT condition-realization representations at
`block15_pre_final_rmsnorm`. Evaluate:

```text
z_A_mu_sigma = (h - mu_final,c) / sigma_final,c
C_ref_OLMo(z_A_mu_sigma)
```

Compute:

```text
G_eval(c) =
    BA_A_mu_sigma(block15_pre_final_rmsnorm, EVAL_c)
  - BA_A0(block15_pre_final_rmsnorm, EVAL_c)
```

Higher `G_eval(c)` indicates greater calibration rescue on untouched EVAL
families. `C_ref_OLMo` is never refit.

Status: `NOT_IMPLEMENTED`

## Endpoint 12: Secondary Spearman/Permutation, Routing, Provenance, Publication

Partition access: post-analysis only.

Contract:

- Build frozen condition-order arrays of `S_diag(c)` and `G_eval(c)`.
- Compute the secondary statistic:

```text
rho_secondary = Spearman(S_diag(c), G_eval(c))
```

- Enumerate all `10! = 3,628,800` condition pairings.
- Compute the exact one-sided permutation p-value under `rho > 0`.
- Secondary support rule:

```text
rho_secondary > 0 AND exact_one_sided_p <= 0.05
```

- Compute `D+`/`D-` and `G+`/`G-` from condition-level `S_diag(c)` and
  `G_eval(c)` using the frozen exact one-sided binomial rule.
- Apply the frozen routing table:

```text
D+/G+  -> Paper A breadth STRENGTHENED; operator/mechanism HIGH PRIORITY CANDIDATE
D+/G-  -> degradation breadth STRENGTHENED; generic calibration breadth WEAKENED
D-/G+  -> general fixed-readout degradation NOT CROSS-MODEL REPLICATED
D-/G-  -> general fixed-readout degradation NOT CROSS-MODEL REPLICATED
technical/measurement invalid -> NO SCIENTIFIC ROUTING
```

- Construct the canonical result object with provenance, then validate and
  atomically publish it according to the publication contract below.

Status: `NOT_IMPLEMENTED`

## Numerical Contract

The implementation must use the following frozen boundaries:

### Tensor extraction

```text
device tensor
  -> detach
  -> CPU
  -> float32
  -> NumPy
```

The formal path must not call generic `np.asarray` directly on a CUDA tensor.

### Classifier class/probability mapping

Predictions and probabilities must be ordered through `classifier.classes_`.
The four frozen classes are `logic`, `causality`, `analogy`, `definition`.

### Condition ordering

All arrays and serialized condition-level outputs must use the frozen
EXP-024/EXP-025 condition order:

```text
c01_lexical_relex
c02_syntactic_restructure
c03_controlled_compression
c04_controlled_elaboration
c05_relation_explicit
c06_relation_implicit
c07_register_formal
c08_register_informal
c09_neutral_distractor_prefix
c10_anaphoric_reference
```

### One-sided directions

- `S_diag` positive direction means degradation.
- `G_eval` positive direction means recovery.
- Binomial p-value direction is one-sided upper-tail for positive evidence.
- Permutation p-value direction is one-sided under `rho > 0`.

Do not silently switch to two-sided inference.

## Specification Gaps

The following required behaviors are not fully explicit in the frozen EXP-025
authority. Task 100D-D records them as `SPECIFICATION_GAP`. They must be
resolved by an explicit frozen authority or binding governance decision before
implementation if they could affect the scientific result.

### GAP-001: Spearman tie-handling

Status: `UNRESOLVED_D`

`EXP-025-PREREGISTRATION.md` defines the secondary statistic as
`Spearman(S_diag(c), G_eval(c))` but does not restate the tie-handling rule.
EXP-024 states standard average ranks for the EXP-024 primary test, but the
frozen EXP-025 text does not explicitly bind its secondary RQ3 to that rule.

### GAP-002: Exact permutation tie/zero semantics

Status: `UNRESOLVED_D`

The exact one-sided permutation p-value is not specified at the implementation
level for ties in permuted `rho` values, exact zero permutation correlations,
or whether the count includes `rho_perm >= rho_observed`.

### GAP-003: Canonical JSON schema and serialization precision

Status: `RESOLVED_C`

The result object schema, serialization precision, key ordering, newline, and
pre-publication hashing behavior are pure publication/provenance details. They
are resolved from the pre-existing repository JSON/atomic-publication
conventions, without changing any scientific quantity.

### GAP-004: Zero-variance/scaling edge behavior

Status: `UNRESOLVED_D`

The formal behavior of `A_sigma` and `A_mu_sigma` when a fitted scale is zero
or near zero is not explicitly frozen for EXP-025.

### GAP-005: Effective sample size zero for D/G

Status: `UNRESOLVED_D`

The D/G inference rule drops exact zero values, but the authority does not
define behavior when the effective nonzero sample size is `0`. The binomial
formula is undefined for that case.

### GAP-006: Balanced-accuracy definition

Status: `UNRESOLVED_D`

The authority uses `BA` in the primary estimands and a balanced-accuracy
technical floor, but does not explicitly freeze the exact multi-class
balanced-accuracy formula or its equivalence to
`sklearn.metrics.balanced_accuracy_score`.

## Implementation Gate

The executor may not be implemented or authorized for formal science until the
specification gaps are resolved and the end-to-end qualification standard is
met. Task 100D-E0 classifies five of the six gaps as scientifically
consequential and unresolved. The current gate result is:

```text
EXP025_FORMAL_EXECUTOR_SPEC_COMPLETE = true
EXP025_SPECIFICATION_GAPS = 5
EXP025_IMPLEMENTATION_COVERAGE_BASELINE = 0/12
EXP025_FIT_DIAG_EVAL_FIREWALL_SPECIFIED = true
EXP025_PUBLICATION_CONTRACT_SPECIFIED = true
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = false
EXP025_NEXT_TASK = 100D_E1_PROSPECTIVE_SPECIFICATION_CLARIFICATION_REVIEW
```

`EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = false` means implementation
must remain blocked until the five unresolved scientific gaps are explicitly
resolved through a separately governed prospective clarification.

## Publication Contract

The formal executor must implement atomic canonical publication with:

- no pre-existing canonical result collision;
- write to a temporary path;
- full schema/provenance/validation before promotion;
- atomic/exclusive promotion;
- no overwrite of an existing canonical result;
- result SHA-256 computed after final serialization;
- bound authorization identity;
- bound consumption identity;
- bound run-attempt identity;
- repository commit;
- runner hash;
- frozen authority hashes;
- model ID and revision;
- dataset/panel identities.

Publication failure must fail closed and must not fabricate a valid result.

## Required Flags

```text
EXP025_FORMAL_EXECUTOR_SPEC_COMPLETE = true
EXP025_SPECIFICATION_GAPS = 5
EXP025_IMPLEMENTATION_COVERAGE_BASELINE = 0/12
EXP025_FIT_DIAG_EVAL_FIREWALL_SPECIFIED = true
EXP025_PUBLICATION_CONTRACT_SPECIFIED = true
EXP025_SCIENTIFIC_DESIGN_CHANGED = false
EXP025_FORMAL_RUN_EXECUTED = false
EXP025_RECOVERY_AUTHORIZATION_CREATED = false
EXP025_READY_FOR_FORMAL_EXECUTOR_IMPLEMENTATION = false
EXP025_NEXT_TASK = 100D_E1_PROSPECTIVE_SPECIFICATION_CLARIFICATION_REVIEW
```
