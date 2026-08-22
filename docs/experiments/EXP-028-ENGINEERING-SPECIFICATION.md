# EXP-028 Engineering Specification

**Task:** `103C_EXP028_PREREGISTRATION_REREVIEW_AND_ENGINEERING_SPEC`
**Status:** `ENGINEERING_SPECIFICATION_ONLY`
**Runner implementation deferred to:** `103D_EXP028_RUNNER_IMPLEMENTATION_AND_SYNTHETIC_QUALIFICATION`

This document specifies the future EXP-028 production runner. It does not
implement, run, or authorize EXP-028.

## Hard boundaries

- No real FIT, DIAG, or EVAL data is read in this task.
- No formal authorization is created.
- No scientific result is created.
- The runner must not alter the frozen preregistration or panel.
- Scientific computation occurs only after a single-use formal authorization is
  consumed.

## Module specification

### 1. Model authority verification

`verify_model_authorities(config, binding)`

- Verify Qwen, OLMo, and Llama identity, revision/source, model class, hidden
  size, decoder block count, tokenizer class, and registered layer indices.
- Verify local snapshot/converted checkpoint hashes where registered.
- Fail closed on authority mismatch, missing authority, or unregistered runtime
  dtype/device ambiguity.
- Do not modify weights, tokenizer files, or checkpoint files.

### 2. Fresh panel validation

`load_and_validate_fresh_panel(panel_path, prior_authorities)`

- Validate schema, 10 conditions, four semantic classes, and FIT/DIAG/EVAL
  allocation.
- Compute normalized raw-text SHA-256 and compare against all enumerated prior
  panel authorities.
- Reject prior source-family reuse where source-family identity exists.
- Reject paraphrase-family leakage where such identity exists.
- Freeze the panel before any real hidden-state extraction begins.

### 3. Representation extraction

`extract_layer_representations(model, tokenizer, panel)`

- Use `FORWARD_HOOK_DECODER_BLOCK_OUTPUT` at `model.model.layers[l]`.
- Extract post-decoder-block residual before next block and before model final
  norm.
- Forbid `outputs.hidden_states[-1]`.
- Use last valid token rule `attention_mask_sum_minus_one`.
- Convert with `tensor.detach().cpu().to(torch.float32).numpy()`.

### 4. Source FIT probe

`fit_source_probe(source_repr, labels)`

- Fit `StandardScaler` and frozen `LogisticRegression` only on FIT source-layer
  representations.
- Use the frozen class order `logic`, `causality`, `analogy`, `definition`.
- Never fit on DIAG or EVAL.

### 5. T0 identity

`apply_T0(target_repr)`

- Return target representation unchanged: `T0(h_j) = h_j`.
- Use as baseline/descriptive context, never as primary comparator.

### 6. T1 moment recalibration

`apply_T1(target_repr, source_repr)`

- Compute `mu_j`, `sigma_j`, `mu_i`, `sigma_i` from FIT paired representations
  only, with `ddof=0`.
- Apply
  `T_mu_sigma(h_j)_k = ((h_j,k - mu_j,k) / sigma_j,k) * sigma_i,k + mu_i,k`.
- Orientation is target representation to source measurement frame.

### 7. T2 paired diagonal OLS

`apply_T2(target_repr, source_repr)`

- Fit one affine coefficient pair `(a_k, b_k)` per coordinate by closed-form OLS
  on FIT paired representations.
- Mapping is `T_pair_diag(h_j)_k = a_k * h_j,k + b_k`.
- No cross-coordinate mixing, no label use, no hyperparameter search, no
  task-loss optimization, and no optimization against `DELTA_RO`.

### 8. Numerical-degeneracy handling

`apply_numerical_edge_rules(value)`

- Frozen `epsilon = 0.0`; population variance `ddof=0`.
- Zero target variance: `TECHNICALLY_INVALID_MODEL`.
- Near-zero positive variance: compute without epsilon and invalidate if
  non-finite.
- Non-finite variance, covariance, or fitted coefficient:
  `TECHNICALLY_INVALID_MODEL`.
- Source denominator `sigma <= 0` or non-finite:
  `TECHNICALLY_INVALID_MODEL`.
- No tunable epsilon and no post-outcome tuning.

### 9. DIAG technical qualification

`run_diag_qualification(artifacts)`

- DIAG is technical only.
- May check probe qualification, finite operator coefficients, required
  layer/source coverage, normalized depth span, class integrity, and
  source-family integrity.
- Must not select favorable layer pairs/models, change operator family,
  endpoint, bootstrap, or threshold, or determine whether EVAL is worth
  running.
- Enforce source floor `0.75` on DIAGNOSTIC and coverage minima `(8, 0.5,
  depth span 0.5)`.

### 10. Frozen EVAL execution

`run_frozen_eval(probe, transformed_target_repr)`

- Apply the frozen probe to fresh EVAL transformed target representations for
  T0, T1, and T2.
- Compute registered endpoint inputs without refitting probe or operator.

### 11. DELTA_RM

`compute_delta_rm(eval_artifacts)`

- `DELTA_RM = E(T_mu_sigma) - E(T_pair_diag)`.
- `E(T) = mean over fresh EVAL item and coordinate of
  ((T(h_j)_k - h_i,k) / sigma_i,k^FIT)^2`.
- Equivalent to `RM(T_pair_diag) - RM(T_mu_sigma)` where `RM(T) = -E(T)`.
- Positive means paired contribution improves direct representation matching.

### 12. DELTA_RO

`compute_delta_ro(eval_artifacts)`

- `DELTA_RO = C_pair - C_mu_sigma`.
- `C_pair` and `C_mu_sigma` are balanced accuracies of the frozen source probe
  on T2- and T1-transformed fresh EVAL target representations.
- Balanced accuracy is macro-average per-class recall over the four classes.
- Positive means paired contribution improves fixed-readout recovery.

### 13. Source-family bootstrap

`bootstrap_primary_support(delta_rm, delta_ro, panel_metadata)`

- Use condition-stratified source-family cluster bootstrap.
- Resample source families, using all records of each sampled family.
- Use `numpy.random.Generator(numpy.random.PCG64(20260819))`, 5000 replicates.
- Quantile method: `numpy.percentile_method_linear`.
- Skip replicates that do not preserve all four classes.
- No operator refit and no probe refit inside EVAL bootstrap.
- Primary support uses the 5th percentile one-sided lower bound compared with
  `0`.
- The 5th-to-95th percentile interval is descriptive only.

### 14. Model-level registered state

`route_model_state(rm_supported, ro_supported)`

- `(RM+, RO+)` -> `JOINT_ALIGNMENT_CONTRIBUTION`
- `(RM+, RO-)` -> `REPRESENTATION_ONLY`
- `(RM-, RO+)` -> `READOUT_ONLY_ARTIFACT_RISK`
- `(RM-, RO-)` -> `NO_PAIRED_COORDINATE_CONTRIBUTION`

### 15. Three-model routing

`route_three_models(model_states)`

- Exact state matching only.
- Any technical invalidity -> `NOT_FULLY_ADJUDICATED`.
- All three joint -> `THREE_MODEL_JOINT_COORDINATEWISE_COMPONENT`.
- All three share another exact state -> `THREE_MODEL_COMMON_STATE`.
- Otherwise -> `MODEL_DEPENDENT_ALIGNMENT_STATE`.
- No majority vote, no endpoint voting, no nearest-profile routing, no post-hoc
  grouping, and no dropping an invalid model.

### 16. Pair-break secondary control

`run_pair_break_control(fit_artifacts)`

- Status `SECONDARY_ONLY`.
- Within FIT, per condition, per layer pair, sort source-family IDs
  lexicographically and assign target sequence by deterministic cyclic shift of
  one.
- Preserve source marginals, target marginals, sample count, and coordinates.
- Use the same coordinatewise OLS family.
- Cannot rescue a failed primary endpoint.

### 17. Result schema

`exp028_result_schema.json`

- Include model identity/authority status, technical qualification status,
  endpoint aggregates, bootstrap bounds, model states, three-model route,
  pair-break secondary state, and non-claim routing.
- Never expose FIT/DIAG/EVAL item text or labels in progress reports.
- Scientific values are written only by the formal execution path.

### 18. Atomic publication

`publish_canonical_result(result)`

- Write to a temporary file in the same filesystem, flush/fsync, then atomic
  rename to `experiments/exp028/results/exp028_results.json`.
- Create canonical result only after registered result validation passes.
- Do not partially publish or overwrite an existing canonical result.

### 19. Authorization lifecycle

`consume_authorization(authorization)`

- Exactly one single-use formal authorization per formal run.
- Verify authorization SHA-256, bound HEAD, runner SHA-256, and unconsumed
  status before starting scientific compute.
- Record consumption atomically before model inference.
- Forbid re-run, rescue run, and post-hoc replacement.

### 20. Outcome-blind progress reporting

`report_progress(stage)`

- Report only stage names, lifecycle status, and non-scientific technical
  checks.
- Do not report DIAG or EVAL outcome values before final result validation.
- Do not expose scientific outcome in logs or progress messages.

## Implementation gate

The runner may be implemented only in `103D`. It must first pass the synthetic
test specification in `EXP-028-ADVERSARIAL-TEST-SPEC.md` without accessing real
FIT/DIAG/EVAL data.
