# EXP-021 Pre-Run Reconciliation and Amendment 01 Draft

Status: `NON_EXECUTABLE_AMENDMENT_DRAFT_READY_FOR_REREVIEW`

Amendment status: `EXECUTABLE_PROTOCOL_DRAFT_READY_FOR_FINAL_REREVIEW`
Overall status: `EXP021_AMENDMENT_READY_FOR_TARGETED_FINAL_REREVIEW`

Hook-oracle protocol status: `FROZEN`

Hook-oracle runtime qualification status: `NOT_RUN`

`EXP021_HOOK_ORACLE_RUNTIME_QUALIFIED = false`

`stage_q_authorizable = false`; `stage_p_authorizable = false`

This document is a scientific-review draft only. It does not authorize an
EXP-021 run, create an evaluator, load a model, access formal data, or create
scientific results. The original preregistration remains unchanged.

## Authority and provenance

The existing file `docs/experiments/EXP-021-PREREGISTRATION.md` is the
historical authority. It is byte-identical to the entry version:

- SHA-256: `2ea9c54a49c41b3c1c8e6c39b029dc333d3ee6753ae0608603d6365ae063301a`
- Git blob: `c17c24ea9562708f14d703f120c1c29928496757`
- last commit: `c95cd270cf84c06c8cee4db506cc949b9ecd4b5a`
- commit time: `2026-08-13T01:46:38Z`
- commit message: `Preregister EXP-020 and EXP-021`

The EXP-021/EXP-020 overlap is a genuine scientific overlap, not merely a
numbering collision: both protocols concern downstream persistence of a
representation intervention. This draft therefore reconciles the existing
commitments instead of replacing the original document.

## Current status

- Primary model: Qwen/Qwen3-1.7B.
- Qwen3-4B is a pre-specified optional conditional replication branch. The
  supplied Task 087B context says that the EXP-020 gate and runtime condition
  were met; this draft does not independently inspect EXP-020 row-level data.
- The conditional branch cannot rescue or replace the primary model.
- Historical identity recovery remains `UNRECOVERED` and byte identity with
  earlier runs remains `UNPROVEN`. A complete local snapshot has instead been
  prospectively frozen for EXP-021 by a content manifest. The manifest, not a
  recovered Hugging Face revision, is the immutable execution identity.
- EXP-021 remains `NOT_STARTED`.
- Formal execution is not authorized.
- Stage Q measurement qualification is not authorized.

## Two-stage execution boundary

The draft now defines two future stages. Neither stage is executable from this
document.

### Stage Q: FIT-only measurement qualification

Stage Q is a technical measurement qualification, not a persistence result.
It requires its own future explicit authorization and its own qualification
report. It may access only frozen FIT IDs and clean, unmodified forward
representations. It may not access EVAL data, apply interventions, generate
behavior, or consume/create an EXP-021 formal EVAL authorization.

For each original split, Stage Q performs leave-one-FIT-item-out validation at
the intervention representation. Each fold fits the frozen
`StandardScaler` plus multinomial `LogisticRegression` only on the remaining
intervention-layer FIT representations, then applies that same estimator
without refitting at the intervention checkpoint and every downstream
checkpoint. `classifier.classes_` must be explicitly mapped to the frozen
semantic class order. Raw hidden states are not persisted.

For every split and checkpoint, the qualification records leave-one-item-out
balanced accuracy, correct count out of 12, and the exact two-sided 95%
Clopper–Pearson lower bound. The nominal four-class chance level is 0.25. A
checkpoint passes only if at least 7 of 12 are correct, the exact lower bound
is strictly greater than 0.25, all four classes are represented in the
ground-truth and predicted accounting, all probabilities are finite, and the
intervention checkpoint itself passes. The threshold calculation is:

`BetaInv(0.025; 7, 12 - 7 + 1) = 0.276669685682 > 0.25`.

The global Stage-Q gate passes only when every checkpoint passes in both
original splits. Allowed outcomes are
`CROSS_LAYER_READOUT_QUALIFIED`,
`CROSS_LAYER_READOUT_NOT_QUALIFIED`, and
`CROSS_LAYER_READOUT_TECHNICALLY_INVALID`.

A Stage-Q pass supports only the claim that the fixed intervention-layer
classifier retains minimal semantic discriminability on held-out FIT items at
the predeclared checkpoints. It does not establish intervention persistence,
probability calibration equivalence, behavioral relevance, Functional
Binding, or causal model use.

### Stage P: formal downstream persistence

Stage P remains inaccessible unless Stage Q is technically valid, every
checkpoint passes, the Stage-Q report is independently reviewed, and a
separate Stage-P authorization is created. Stage P would preserve the original
four conditions and fixed-probe `P_target` definition, reporting task,
random, opposite, `D_random`, and `D_opposite` effects descriptively. It has
no binary scientific success gate. No checkpoint may be selected after
observation, and a failed checkpoint cannot be rescued by another layer,
model, beta, or probe.

If Stage Q is `CROSS_LAYER_READOUT_NOT_QUALIFIED`, EVAL access and Stage P stop;
no per-layer probe rescue or persistence/attenuation claim is permitted. If
Stage Q is technically invalid, no automatic retry is permitted; incident
review and a separate authorization decision are required. Geometry-only work
would require a separately named transparent amendment.

## Prospective primary identity and checkpoint mapping

Historical identity recovery is not claimed. The following complete local
snapshot is prospectively frozen as the EXP-021 execution identity:

- model: `Qwen/Qwen3-1.7B`
- architecture: `Qwen3ForCausalLM`
- model type: `qwen3`
- transformer blocks: 28
- hidden size: 2048
- vocabulary size: 151936
- config-declared dtype: `bfloat16`
- EXP-021 execution dtype: `float16`
- device: `cuda:0`
- `local_files_only=true`, network access prohibited, `model.eval()`,
  gradients disabled, `use_cache=false`
- tokenizer class: `Qwen2Tokenizer`
- tokenizer authority: the tokenizer files in the same manifest
- model and tokenizer repository revisions:
  `UNRECOVERED_NOT_USED_AS_EXECUTION_IDENTITY`
- canonical and resolved snapshot path:
  `D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-1.7B\snapshots\70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

The frozen content manifest is:

| File | Bytes | SHA-256 |
| --- | ---: | --- |
| `config.json` | 726 | `1ddb5b89ebc90dcb417a45c213d818577e65976454d29385c8f6140771d95197` |
| `tokenizer_config.json` | 9732 | `d5d09f07b48c3086c508b30d1c9114bd1189145b74e982a265350c923acd8101` |
| `tokenizer.json` | 11422654 | `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4` |
| `model.safetensors.index.json` | 25605 | `0d660e94b165eb912669a5249dff44b83188c4777a07ddb9611fb78d91b0578d` |
| `generation_config.json` | 239 | `2325da0f15bb848e018c5ae071b7943332e9f871d6b60e2ed22ca97d4cb993d2` |
| `model-00001-of-00002.safetensors` | 3441185608 | `169ad53ec313c3a34b06c0809216e4fc072cce444a5d4ff2b59690d064130ed5` |
| `model-00002-of-00002.safetensors` | 622329984 | `912becff8d60672aa8628ef08c05898d9adf17c2ad4ae3caf99b065622fdeff9` |

The index references exactly the two complete shards and declares
`total_size=4063479808`. Static safetensors header checks passed without
materializing tensor payloads. The stale `.incomplete` files elsewhere in the
model cache are outside this canonical snapshot; the snapshot contains and
resolves only the complete verified files above, so they do not invalidate this
prospective manifest.

Using `round(fraction * (num_blocks - 1))` with 28 blocks and the existing
historical L16/beta-0.75 operating point gives:

| Checkpoint | Block index | Hidden-state index | Role |
| --- | ---: | ---: | --- |
| Intervention | 16 | 17 | Frozen intervention, beta 0.75 |
| Normalized 0.625 | 17 | 18 | Stage-Q checkpoint |
| Normalized 0.75 | 20 | 21 | Stage-Q checkpoint |
| Normalized 0.875 | 24 | 25 | Stage-Q checkpoint |
| Final block, pre-final RMSNorm | 27 | not exposed as tuple index 28 | Primary final checkpoint via block hook |
| Final normalized state | 27 | 28 | Descriptive only |

The final block output and `hidden_states[28]` are not treated as identical.
Static Qwen3 source shows that indices 1–27 are decoder-block outputs before
the final RMSNorm, while the capture decorator replaces the final tuple entry
with the post-RMSNorm `last_hidden_state`. The pre-final-RMSNorm block-27
output is therefore primary for the final-block interpretation; index 28 is
descriptive only.

## Token, forward, and numerical semantics

The proposed pre-run execution semantics are: one prompt at a time, padding
disabled, truncation disabled unless separately frozen before implementation,
unchanged attention mask, no generation, `use_cache=False`, `model.eval()`,
`torch.no_grad()`, separate independent forward passes for each condition, no
shared KV cache, exactly one intervention application, and finally-style hook
removal. With one unpadded prompt, the final tensor position is the last valid
prompt token, and attention-mask last-valid-token logic must agree with that
position. Disagreement is a technical failure. Only that selected residual
vector may change; all other positions must be exactly unchanged and weights
must remain unchanged.

The exact active-hook construction oracle is frozen: for every intervention
forward, capture the unmodified output tensor of block 16, clone that exact
tensor to construct `expected`, and cast the frozen intervention vector to the
captured tensor's dtype and device. In the frozen production order compute
`expected[:, selected_token_index, :] += beta * delta_cast`, apply the
production hook, and require `torch.equal(actual_hook_output, expected)`.
Shape, dtype, device, every non-target token position, and exactly one hook
invocation must also match. No cache may be created or reused. No low-precision
subtraction against a higher-precision delta and no broad `allclose` tolerance
may replace this construction oracle.

An inactive hook must return the original tensor object or exact value without
cloning or mutation. Future deterministic neutral qualification must establish
exact no-hook versus inactive-hook equality; failure is technical invalidity
and may not be rescued by an approximate tolerance. Downstream values need
only be finite; exact equality is required at the hook boundary, not after
nonlinear downstream computation.

## Neutral hook-oracle runtime qualification gate

The hook oracle is protocol-frozen but has not been runtime-qualified:
`hook_oracle_protocol_status = FROZEN`,
`hook_oracle_runtime_qualification_status = NOT_RUN`, and
`EXP021_HOOK_ORACLE_RUNTIME_QUALIFIED = false`. R20 remains resolved because
the oracle is operationally specified; that resolution does not imply that a
production hook implementation has passed. A separate neutral engineering
qualification is required before Stage Q and before Stage P. Until it passes,
`stage_q_authorizable = false` and `stage_p_authorizable = false`.

The neutral qualification may use only one or more predeclared semantically
neutral diagnostic sentences. It must not access EXP-021 FIT or EVAL items,
calculate a persistence outcome, or create scientific evidence. It may load the
prospectively frozen seven-file model only under a separate engineering
authorization, using `float16` on `cuda:0`, `local_files_only=True`, eval mode,
disabled gradients, `use_cache=False`, one unpadded prompt per forward, the
last valid token, and block 16.

The qualification must pass every required check. For the inactive-hook check,
run deterministic no-hook and inactive-hook neutral forwards, require exact
equality for the relevant captured block output and, if declared part of the
oracle, downstream logits, require zero hook-side mutation, and confirm no
FIT/EVAL access. For the active check, capture the unmodified block-16 output,
clone it as `expected`, cast the diagnostic delta to the captured dtype/device,
apply `expected[:, selected_token_index, :] += beta * delta_cast`, and require
`torch.equal(actual_hook_output, expected)`, exact non-target-token equality,
exactly one invocation, unchanged shape/dtype/device, the last-valid-token
selection, and `use_cache=False`.

The qualification report must bind its schema version, attempt ID, repository
commit, production implementation file hashes, seven-file model manifest,
runtime versions and device identities, hook block/token rule, beta and
diagnostic-vector identity, timestamps, every check result, FIT/EVAL access,
and scientific-result status. A qualification becomes invalid before Stage Q
or Stage P if production hook/runner bytes, the model manifest, dtype/device,
block or token semantics, beta/intervention construction, torch or
transformers version, cache semantics, or checkpoint mapping changes. A session
restart alone is not drift when all bound identities remain unchanged.

The required lifecycle is: amendment archived; Stage-Q implementation created
and independently reviewed; neutral qualification separately authorized and
passed; Stage-Q separately authorized and run once; Stage-Q independently
reviewed; Stage-P reviewed, separately authorized, and run once only if Stage Q
passes. A consumed neutral qualification authorization is single-use. Failure
or technical invalidity permits no automatic retry; retry requires a new
explicit authorization and incident review. This gate authorizes no future
action by itself.

## Bootstrap and descriptive mechanism metrics

The EXP-020 bootstrap is adopted as a transparent pre-run amendment: source-
item clusters, two split strata, one shared PCG64 resample plan across
checkpoints and conditions, seed 20260812, 10,000 resamples, linear
percentile intervals, `ddof=1`, and preservation of each complete layer
trajectory within a resampled source-item cluster. All checkpoint intervals
are reported. No multiplicity-adjusted binary inference is required because
EXP-021 remains descriptive, and no checkpoint can rescue another checkpoint.

Common-coordinate projection, displacement norm, norm retention, cosine with
the original direction, and layer-specific FIT centroid relations remain
explicitly descriptive. Norm survival measures generic perturbation survival;
original-direction projection measures coordinate-specific retention; and
fixed-probe `P_target` is target-associated readout only after Stage-Q
qualification. None establishes behavioral use.

## Reconciliation classifications

The following IDs and classifications are mirrored exactly in
`experiments/exp021/exp021_preregistration_reconciliation.json`.

| ID | Topic | Classification | Reconciled position |
| --- | --- | --- | --- |
| R01 | primary model | ORIGINAL_FROZEN_COMMITMENT | Keep Qwen3-1.7B primary. |
| R02 | optional Qwen3-4B branch | PRE_SPECIFIED_CONDITIONAL_BRANCH_NOW_TRIGGERED | Conditional replication only; no rescue. |
| R03 | conditions | ORIGINAL_FROZEN_COMMITMENT | BASELINE, TASK, MATCHED_RANDOM, OPPOSITE. |
| R04 | checkpoints | ORIGINAL_FROZEN_COMMITMENT | Deterministic normalized checkpoints; no trajectory selection. |
| R05 | hidden-state tuple | NON_SUBSTANTIVE_CLARIFICATION | Index 0 is embedding; index k+1 is block k output. |
| R06 | numeric intervention site and beta | OPEN_DESIGN_DECISION | Candidate block 16/index 17/beta 0.75 requires explicit pre-run confirmation. |
| R07 | last-token hook | NON_SUBSTANTIVE_CLARIFICATION | Last valid token at the selected residual/block output. |
| R08 | direction and controls | ORIGINAL_FROZEN_COMMITMENT | FIT-only delta with matched-random and opposite controls. |
| R09 | tokenization and mask | OPEN_DESIGN_DECISION | Freeze raw-text, mask, padding, and last-token semantics. |
| R10 | probe strategy | ORIGINAL_FROZEN_COMMITMENT | Reuse frozen machinery; no per-layer separability-maximizing probes. |
| R11 | common-coordinate transport | TRANSPARENT_PRE_RUN_AMENDMENT | Recommended primary persistence measurement if valid. |
| R12 | final endpoint and gate | OPEN_DESIGN_DECISION | Original is descriptive and has no binary gate; decide only before execution. |
| R13 | bootstrap | OPEN_DESIGN_DECISION | Freeze exact resampling rules before execution. |
| R14 | labels and EXP-022 | ORIGINAL_FROZEN_COMMITMENT | Retain descriptive labels; EXP-022 remains conditional. |
| R15 | technical validity | NON_SUBSTANTIVE_CLARIFICATION | Add finite-output, hook, cleanup, and coverage checks. |
| R16 | interpretation boundaries | ORIGINAL_FROZEN_COMMITMENT | No behavioral, reasoning, or universal claims. |
| R17 | runtime identity | OPEN_DESIGN_DECISION | Historically unrecovered; prospectively frozen by the complete content manifest, with no invented repository revision. |
| R18 | cross-layer coordinate validity | OPEN_DESIGN_DECISION | Validate before claiming cross-layer persistence. |
| R19 | independent probe availability | OPEN_DESIGN_DECISION | Verify a valid independently frozen instrument; stop if unavailable. |
| R20 | numeric tolerances | OPEN_DESIGN_DECISION | Exact construction-based hook oracle and inactive-hook equality are frozen. |
| R21 | forward computation sharing | OPEN_DESIGN_DECISION | Decide separate-forward semantics before execution. |
| R22 | cluster adequacy | OPEN_DESIGN_DECISION | Predeclare the small-cluster uncertainty limitation. |
| R23 | final normalization | OPEN_DESIGN_DECISION | Resolve final checkpoint normalization semantics. |
| R24 | conditional model namespace | NON_SUBSTANTIVE_CLARIFICATION | Separate authorization and result namespaces. |
| R25 | per-layer probe as primary | REJECTED_AS_POST_OUTCOME_OR_RESCUE_CHANGE | Do not adopt it as confirmatory primary. |
| R26 | Qwen3-4B rescue | REJECTED_AS_POST_OUTCOME_OR_RESCUE_CHANGE | Cannot rescue Qwen3-1.7B. |
| R27 | behavior or EXP-022 now | REJECTED_AS_POST_OUTCOME_OR_RESCUE_CHANGE | Not part of EXP-021. |
| R28 | post-hoc threshold/layer selection | REJECTED_AS_POST_OUTCOME_OR_RESCUE_CHANGE | No post-outcome rescue rules. |

## Task 087C/087D open-decision statuses

These statuses are mirrored in the JSON field `open_decision_statuses`.

| ID | Status |
| --- | --- |
| R06 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R09 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R12 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R13 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R17 | RESOLVED_BY_TRANSPARENT_PROSPECTIVE_PRE_RUN_AMENDMENT |
| R18 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R19 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R20 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R21 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |
| R22 | REMAINS_OPEN_NONBLOCKING |
| R23 | RESOLVED_BY_TRANSPARENT_PRE_RUN_AMENDMENT |

R17 is resolved prospectively, not historically: the complete content
manifest is the execution identity and no repository revision is invented.
R20 is resolved through the exact construction oracle rather than an empirical
tolerance. R22 remains nonblocking but limits the interpretation of
uncertainty and generality.

## Measurement strategy review

Five strategies were considered explicitly:

1. **A — fixed injection-layer probe.** Suitable only as a secondary or
   conditional descriptive measurement after calibration validity is shown.
2. **B — separate FIT probe per checkpoint.** Rejected as the confirmatory
   primary because it can maximize checkpoint separability and conflicts with
   the original prohibition.
3. **C — common residual-coordinate transport.** Retained as descriptive
   geometry only. Projection onto the original direction does not establish
   semantic coordinate invariance and does not replace Stage-Q fixed-probe
   qualification.
4. **D — layer-specific centroid reference without a probe.** Acceptable only
   as a secondary descriptive geometric reference; it does not establish task
   probability or persistence by itself.
5. **E — pooled cross-layer probe.** Not adopted silently. It changes the
   measurement instrument and needs an independently justified pre-run
   specification.

The recommendation is therefore not to silently adopt Task 087A's per-layer
probe design. If common-coordinate validity cannot be established, the safe
outcome is to document the limitation or retain only the originally specified
descriptive endpoint; it is not to fit a more favorable downstream classifier.

## Recommended minimum design

The following is a review recommendation, not an executable authorization.

- Keep Qwen3-1.7B as primary. Treat Qwen3-4B as conditional replication only.
- Reuse the original four conditions and the existing controlled task/split
  identity without outcome-based prompt filtering.
- Map normalized checkpoints with
  `round(fraction * (num_blocks - 1))` for intervention, 0.625, 0.75, 0.875,
  and the final block. Checkpoints are not selected from observed trajectories.
- The transparent pre-run amendment freezes Qwen3-1.7B block 16, corresponding
  to hidden-state index 17, at beta 0.75. Qwen3-4B's block 18 must not be
  remapped into the 1.7B protocol.
- Use only the last valid token at the selected residual/block output. Do not
  alter weights, KV cache, or generation behavior.
- Fit the target-minus-source direction on FIT representations only. Use
  matched-random and opposite controls.
- Use the Stage-Q-qualified fixed intervention-layer probe for `P_target`.
  Common residual-coordinate transport and layer-specific centroid relations
  remain descriptive only. A new per-layer classifier is not a confirmatory
  primary instrument.

For a representation `h_k`, the intervention is conceptually

`h'_k = h_k + beta * delta`,

with `delta = centroid_target(FIT) - centroid_source(FIT)`. Report task,
matched-random, and opposite effects using the same paired evaluation units,
including the task-versus-random and task-versus-opposite contrasts. Useful
descriptive diagnostics include signed target projections, norm retention, and
cosine similarity, but they must not become multiple unannounced rescue
endpoints.

## Confirmatory versus descriptive status

The original EXP-021 preregistration is explicitly descriptive/causal-
mechanistic and does **not** freeze a binary confirmatory gate or a numerical
success threshold. Its labels (`PERSISTS`, `ATTENUATES`, `DISAPPEARS`,
`REVERSES`, `MIXED`) remain descriptive. A positive-confidence terminal gate,
if later desired, is a transparent pre-run amendment and cannot be described
as an original commitment or selected after observing results.

The original does require bootstrap 95% confidence intervals but does not
fully specify the resampling unit and numerical rules. This draft adopts the
EXP-020 cluster rule as a transparent pre-run amendment: clusters by split and
held-out source item, PCG64 seed 20260812, 10,000 resamples, shared plans over
the complete trajectories, linear percentile intervals, and `ddof=1`. This
does not create a binary scientific gate.

## Open design decisions

R17 and R20 are resolved prospectively by the transparent amendments above;
R22 remains an open, nonblocking interpretation limitation. The prospective
manifest does not claim historical byte identity, and the exact hook oracle
does not depend on an empirical tolerance.

- **R22 — nonblocking:** report the small source-item cluster count as a
  limitation and do not claim broad generality.

## Rejected changes and claim limits

Rejected as post-outcome or rescue changes are: per-layer probes as the
confirmatory primary; using Qwen3-4B or an intermediate layer to rescue the
primary; adding behavior or EXP-022 now; post-hoc thresholds, layer or beta
selection; and reading formal outcomes to choose a measurement design.

Even if a later approved run shows persistence, allowed claims are limited to
descriptive downstream persistence or attenuation under the frozen protocol.
The study cannot establish behavioral control, reasoning improvement,
cognitive-space transformation, true task manifolds, scale invariance, or
universal cross-family replication.

## Execution boundary and required fields

No model was loaded. No formal prompt/source text, EXP-020 row-level outcome,
EXP-017 material, or EXP-019 material was accessed or modified for this draft.
No inference, authorization, result, runner, validator, or test file was
created. EXP-020 remains untouched.

```text
EXP021_FORMAL_RUN_AUTHORIZED = false
EXP021_MEASUREMENT_QUALIFICATION_AUTHORIZED = false
EXP021_SCIENTIFIC_STATUS = NOT_STARTED
EXP021_SNAPSHOT_IDENTITY_STATUS = PROSPECTIVELY_FROZEN_FOR_EXP021
EXP021_HISTORICAL_BYTE_IDENTITY_EQUIVALENCE = UNPROVEN
EXP021_R17_RESOLVED = true
EXP021_R20_RESOLVED = true
EXP021_HOOK_ORACLE_PROTOCOL_STATUS = FROZEN
EXP021_HOOK_ORACLE_RUNTIME_QUALIFICATION_STATUS = NOT_RUN
EXP021_HOOK_ORACLE_RUNTIME_QUALIFIED = false
EXP021_STAGE_Q_AUTHORIZABLE = false
EXP021_STAGE_P_AUTHORIZABLE = false
EXP021_ORIGINAL_PREREGISTRATION_MODIFIED = false
EXP021_AMENDMENT_STATUS = EXECUTABLE_PROTOCOL_DRAFT_READY_FOR_FINAL_REREVIEW
MODEL_LOAD_PERFORMED = false
TOKENIZER_LOAD_PERFORMED = false
NETWORK_ACCESS_PERFORMED = false
FORMAL_DATA_ACCESSED = false
FORMAL_INFERENCE_PERFORMED = false
SCIENTIFIC_RESULTS_CREATED = false
COMMIT_PERFORMED = false
PUSH_PERFORMED = false
```
