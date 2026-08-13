# EXP-020A Implementation Specification

## Status

This is an implementation-provenance record, not an EXP-020A runner or scientific result. The user-approved pre-outcome cluster-bootstrap rules resolve the prior statistical blocker. No formal FIT/EVAL inference was performed.

`EXP020_FORMAL_RUN_AUTHORIZED = false`
`EXP020_SCIENTIFIC_STATUS = NOT_STARTED`

## Scientific Protocol Authority

Scientific choices are controlled by the frozen EXP-020 configuration, its validator, and the preregistration. The model identity, revision, path, execution mode, block mapping, split, transitions, controls, beta, probe family, bootstrap seed/resample count, and primary gate are not changed here.

## Implementation Provenance Authority

For executable details absent from the EXP-020 freeze, the canonical source is `experiments/exp018/independent_validation.py` at commit `5bb6c45a89daf3a9768266c411162330e08d5cc8`, which is the offline-repair revision of the accepted EXP-018 runner. Its dependencies are `src/extraction.py`, `src/model_loader.py`, and `src/invariants.py` at the checked-out authority state.

## Authority and Conflict Rules

EXP-018 provenance can fill an undefined implementation detail only when it does not conflict with the EXP-020 freeze. Candidate interpretations and recommendations are not executable values. No conflict was found: EXP-018's offline representation perturbation is compatible with EXP-020A's representation-level protocol.

## Provenance Map

| Scientific operation | Source file | Exact function/class | Historical commit | Recovery status | Evidence |
| --- | --- | --- | --- | --- | --- |
| Prompt loading | `experiments/exp018/independent_validation.py` | `load_json`, `main` | `5bb6c45` | RECOVERED | Loads the frozen prompt path before config validation. |
| Prompt-field mapping/rendering | same | `_collect_model_representations` | `5bb6c45` | RECOVERED | Reads the record `text` field directly; no chat-template call exists. |
| Tokenizer invocation | same | `_collect_model_representations` | `5bb6c45` | PARTIALLY_RECOVERED | `tokenizer(prompt["text"], return_tensors="pt")` is exact; omitted tokenizer arguments are unresolved. |
| Representation extraction | `src/extraction.py` | `move_tokenized_inputs_to_device`, `get_model_input_device`, `extract_last_token_hidden_state`, `tensor_to_numpy_float32` | `5bb6c45` | RECOVERED | Historical source selects `[0, -1, :]`, then detach/CPU/float32/NumPy; current file is byte-for-byte unchanged relative to this historical source. |
| FIT routing | `experiments/exp018/independent_validation.py` | `route_split_items`, `_stack` | `5bb6c45` | RECOVERED | FIT and evaluation IDs are separately routed before fitting. |
| Centroids and task delta | same | `fit_group_centroids`, `construct_task_delta` | `5bb6c45` | RECOVERED | Per-group mean on axis 0; target centroid minus source centroid. |
| Offline intervention | same | `apply_steering` | `5bb6c45` | RECOVERED | Copies held-out representations and adds `beta * delta`; no model hook or downstream layer execution. |
| Matched random | same | `matched_random_delta` | `5bb6c45` | RECOVERED | `SeedSequence`, `default_rng`, standard normal, then exact L2 norm matching. |
| Opposite control | same | `opposite_delta` | `5bb6c45` | RECOVERED | Exact negation of the task delta. |
| Probe | same | `fit_linear_probe`, `evaluate_probe_items` | `5bb6c45` | RECOVERED | FIT-only scaler/classifier fit and EVAL transform/predict. |
| Probability mapping | same | `evaluate_probe_items` | `5bb6c45` | PARTIALLY_RECOVERED | Historical integer class indices follow frozen class order, but a future runner must map `classifier.classes_` explicitly. |
| Effects | EXP-020 frozen protocol | frozen effect definitions | `ea85fa5` authority ancestor | RECOVERED | The four paired effect formulas are explicitly frozen by EXP-020. |
| Bootstrap/statistics | EXP-020 frozen protocol; EXP-018 runner | frozen seed/count; no bootstrap function | `ea85fa5`; `5bb6c45` | NOT_RECOVERABLE | Seed/count are frozen, but the unit, CI method, percentiles, `ddof`, tie/zero handling, and RNG details are absent. |
| Aggregation | `experiments/exp018/independent_validation.py` | `aggregate_mean_metrics` | `5bb6c45` | PARTIALLY_RECOVERED | EXP-018 computes arithmetic means; EXP-020's required additional statistics remain unresolved. |

## Input Rendering

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** raw record field `text` is passed directly to the tokenizer; no chat template is applied.
- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_FROZEN_RUNTIME:** under local-only Qwen3-4B revision `1cfa9a7208912126459214e8b04321603b3df60c` and Transformers 5.14.1, the effective defaults are documented in the JSON specification. They were measured only with the permitted neutral diagnostic sentence.

## Tokenization

The historical call is exactly `tokenizer(text, return_tensors="pt")`, one record at a time. For the frozen `Qwen2Tokenizer`, its effective values are: `add_special_tokens=True`, `padding=False`, no truncation, `max_length=None` (with `model_max_length=131072`), and an attention mask is returned. `padding_side` and `truncation_side` are both right. It has no BOS token, `add_bos_token=False`, `add_eos_token=False`, and zero special tokens are added for a single record. The neutral diagnostic confirms that the final sequence position is a text token rather than a special token and that no single-record padding occurs.

## Representation Definition

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** at historical commit `5bb6c45`, `tensor_to_numpy_float32(outputs.hidden_states[tuple_index][0, -1, :])`.
- It is the final sequence position in batch element zero; it is not attention-mask-aware and is not a pooled representation.
- Conversion is `detach() -> CPU -> float32 -> NumPy`.
- **IMPLEMENTATION_CORRECTNESS_REQUIREMENT:** a future runner must assert a nonempty rank-3 hidden-state tensor and map an EXP-020 block index to the specified tuple index before extracting it.

## Layer Mapping

- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** block 18 maps to `hidden_states[19]`; block 26 maps to `hidden_states[27]`.
- The tuple convention is embedding output at index 0 and post-block output at index `block + 1`.
- No model was loaded in this audit; the existing qualification artifact is the engineering evidence for this mapping.

## Direction Construction

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** route representations by frozen FIT IDs; cast each group matrix with `np.asarray(..., dtype=float)`; compute `matrix.mean(axis=0)`; set `delta = centroid[target] - centroid[source]`.
- The calculation is NumPy floating-point on CPU after extraction's float32 conversion; NumPy arithmetic promotes according to its normal dtype rules.
- **IMPLEMENTATION_CORRECTNESS_REQUIREMENT:** centroids, deltas, scaler fitting, and classifier fitting must receive FIT representations only. Synthetic tests exercise this separation.

## Intervention Semantics

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** EXP-018 applied an offline perturbation, `held_out_representations.copy() + beta * delta`, and evaluated the resulting array directly with the centroid metrics, probe, and RSM metrics.
- The tensor is not installed into a model module, no token positions inside an in-model forward are changed, and no downstream transformer computation executes after the addition.
- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** primary beta is 0.75; secondary descriptive beta is 0.50.

## Matched-Random Control

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** draw `standard_normal(task_delta.shape)` from `np.random.default_rng(np.random.SeedSequence([...]))`, then return `random * (||task_delta||₂ / ||random||₂)`.
- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** seed components are `[20260319, 2, block_index, split_index, source_group_index, target_group_index]`.
- `model_index`, block/layer, split, source group, and target group are all passed as 0-based code values. The generated vector is created once per such transition key and reused for every paired held-out item within that key.
- The project requirements pin NumPy to 2.4.6; `default_rng` is the recovered API. No alternative random generator is frozen here.

## Opposite Control

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** `opposite = -np.asarray(task_delta, dtype=float)` before the common beta multiplication. Its L2 norm equals the task-delta norm.

## Probe Pipeline

- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** FIT-only `StandardScaler` plus multinomial `LogisticRegression` with the frozen EXP-020 settings.
- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** scaler is fit-transformed on concatenated FIT matrices; classifier is fit on the same transformed FIT matrix; held-out representations use only `scaler.transform` and `classifier.predict_proba`/`predict`.
- Explicit historical constructor arguments are solver, penalty, `C`, `max_iter`, class weight, random state, and (when supported) `multi_class`. No EVAL tuning occurs.

## Probability Mapping

- **IMPLEMENTATION_CORRECTNESS_REQUIREMENT / IMPLEMENTATION_CORRECTNESS_REQUIREMENT:** map the fitted classifier's `classes_` values back to the frozen semantic class order before selecting source and target probability columns. Do not assume a probability-column order.
- This is a deterministic label-to-column safeguard, not a new scientific label choice. The synthetic test uses deliberately non-alphabetical scientific ordering.

## Effect Computation

- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** effects are paired by the same held-out item: task minus baseline target probability; matched-random minus baseline; opposite minus baseline; then task-minus-random and task-minus-opposite contrasts.
- **IMPLEMENTATION_CORRECTNESS_REQUIREMENT:** pairing must retain model, block, split, transition, and evaluation-item identity; no unpaired group averaging may replace the frozen formulas.

## Statistics and Bootstrap

All rules in this section are **USER_APPROVED_PRE_OUTCOME_IMPLEMENTATION_SPEC**, not recovered from EXP-018. A cluster is `(split_id, held_out_source_item_id)` and contains its three fixed directed-target-transition rows. Bootstrap separately samples 12 clusters with replacement within each of the two complementary splits, then concatenates the samples into 24 cluster instances and 72 rows. It uses one `np.random.Generator(np.random.PCG64(20260812))`, split-index/evaluation-ID traversal ordering, replicate order `0..9999`, and the same resample plan for `task_effect`, `D_random`, and `D_opposite`.

The statistic is the arithmetic mean over 72 resampled rows. The CI is the percentile bootstrap at 2.5% and 97.5% using `np.quantile(..., [0.025, 0.975], method="linear")`. Observed summaries use arithmetic mean, NumPy median, sample SD (`ddof=1`), and `mean(value > 0)`; zero is not positive. Degenerate replicates are retained, identical observed values produce `[c, c]`, and any nonfinite value/statistic or invalid frozen cluster structure is technical invalidity.

Bootstrap uncertainty is cluster-resampling uncertainty for the frozen held-out source-item sample, stratified across the two complementary splits. Directed task transitions are fixed design factors.

The 72 transition-item observations are not 72 independent prompts. They are generated from 24 held-out source-item clusters, with three fixed target-transition rows per cluster.

## Primary Gate

- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** only primary block 18 at beta 0.75 can satisfy the gate. All five frozen requirements must hold: positive mean task effect and positive-excluding CI; positive mean random contrast and positive-excluding CI; and positive mean opposite contrast.
- **IMPLEMENTATION_CORRECTNESS_REQUIREMENT:** technical invalidity is reported as `REPRESENTATION_REPLICATION_INVALID`, separately from scientific non-support; secondary results cannot rescue primary failure.

## Secondary Analysis

- **AUTHORITATIVE_RECOVERED_VALUE / RECOVERED_FROM_EXP018:** the canonical runner iterates each layer independently and fits that layer's own FIT centroids/deltas before applying steering. Therefore the descriptive block-26 analysis uses an independent block-26 FIT delta, not the primary-layer delta.
- **AUTHORITATIVE_RECOVERED_VALUE / ALREADY_FROZEN_EXP020:** secondary block 26 and beta 0.50 are descriptive only and cannot alter primary-gate status.

## Environment Policy

The qualification environment is pinned by project requirements and the qualification artifact: Transformers 5.14.1, Torch 2.12.1+cu130, native BF16, `cuda:0`, and MODE_A_NATIVE. Any material version or execution-mode drift is a stop-before-formal-run event requiring explicit review; no fallback to FP16, CPU offload, quantization, or another device is authorized.

## Data Access Boundary

This audit used LEVEL 0 source/history inspection and LEVEL 1 existing-validator integrity validation only. No formal prompt/source content is reproduced here. No model inference, representation extraction, or outcome inspection was performed.

## Synthetic-Test Boundary

Tests use only fabricated vectors, labels, IDs, and temporary paths. They do not import a formal runner, load formal prompts, access EXP-017/EXP-019 artifacts, or load a model.

## Formal-Run Boundary

This specification neither implements nor authorizes an EXP-020A runner. `EXP020_FORMAL_RUN_AUTHORIZED` remains false until a later explicit task resolves the listed primary-critical statistical choices and separately authorizes implementation.

## Remaining Decisions

No unresolved executable semantic remains. `PRIMARY_READY = true`, `SECONDARY_READY = true`, and `FULL_READY = true`. This records implementation readiness only; a later explicit task is still required for runner implementation and any formal execution.
