# EXP-022A Runner Static and Synthetic Preflight

THIS IS NOT AN EXP-022A SCIENTIFIC RESULT.

## Frozen protocol identity

- Experiment: `EXP-022A 鈥?Clean-State Layerwise Readout Transport Diagnosis`
- Preregistration: `docs/experiments/EXP-022A-PREREGISTRATION.md`
- Preregistration SHA-256: `609aab2b3cc96f4ea316b45741b2ae427e682c72c7546c8a9520201f94547698`
- Freeze manifest: `docs/experiments/EXP-022A-FREEZE-MANIFEST.json`
- Protocol status: `FROZEN`
- Scientific result status: `NOT_RUN`

## Implemented components

- `experiments/exp022a/run_exp022a.py`
- CLI modes: `--static-preflight`, `--synthetic-preflight`, `--formal-run`
- Frozen-authority hash hard fail
- Split A/B text-free analysis contract
- Frozen checkpoint identities
- Attention-mask-derived last-valid-token extraction contract
- A0, A1, and A2 readout families
- StandardScaler and multiclass logistic regression contract
- Probability class mapping
- Balanced accuracy
- Exact primary tests
- Serial primary gate
- Secondary estimands
- Class-stratified item-resampling robustness intervals
- Cross-split synthesis
- Formal result schema validation
- Formal result finalization pipeline with single staging-path authority
- No-overwrite atomic canonical publication

## A0 semantics

A0 fits the reference scaler and classifier only on full FIT reference
representations at block16 / `hidden_states[17]`. Both components are then
applied unchanged to downstream EVAL checkpoints.

## A1 semantics

A1 fits a layer-specific `StandardScaler(with_mean=True, with_std=True)` on FIT
representations at each checkpoint, keeps the A0 reference classifier
unchanged, and evaluates that fixed classifier on layer-specific scaled EVAL
representations.

## A2 semantics

A2 fits a layer-specific scaler and the same preregistered same-family
multiclass linear classifier on FIT representations at each checkpoint, then
evaluates untouched EVAL representations at that checkpoint. A2 is interpreted
only as held-out performance of the preregistered layerwise linear readout
family.

## Primary gate implementation

- Primary score: balanced accuracy.
- Primary endpoint: block27 pre-final-RMSNorm.
- Primary reference: block16 pre-final-RMSNorm.
- `D_fixed = BA_final_A0 - BA_reference_A0`.
- `D_fixed` support requires `D_fixed < 0` and one-sided exact
  `P[Binomial(m, 0.5) >= favorable] <= 0.05`.
- `G_refit = BA_final_A2 - BA_final_A0`.
- `G_refit` support requires `D_fixed` support, `G_refit > 0`, and the exact
  one-sided p-value at or below 0.05.
- `G_refit` is always computed and reported. If the D-fixed gate is closed,
  `G_refit` is reported with `serial_gate = CLOSED_D_FIXED_NOT_SUPPORTED` and
  `supported = false`.

## Secondary robustness implementation

- `G_scale = BA_final_A1 - BA_final_A0`
- `G_noncal = BA_final_A2 - BA_final_A1`
- `R_refit = BA_final_A2 - BA_reference_A2`
- Post-final-RMSNorm checkpoint is stored and reported as descriptive.
- Bootstrap: 10,000 replicates, `numpy.random.PCG64(20260817)`, within split
  separately, class-stratified, three records sampled with replacement per
  class, all readout/checkpoint observations for a sampled record identity kept
  together.
- Quantile method: `"linear"`, 2.5th and 97.5th percentiles.
- Output terminology: `robustness_interval`.

## Deterministic bootstrap choice

The frozen protocol fixes the seed but does not uniquely specify stream
architecture. Task 094B chooses one fresh, named
`numpy.random.Generator(numpy.random.PCG64(20260817))` stream per bootstrap
call, with a fixed class-universe and split order. This makes repeated calls
deterministic and independent of earlier call ordering. The choice affects only
secondary robustness numbers and does not alter primary exact tests or
support gates.

## Synthetic fixture coverage

The synthetic preflight and focused tests cover:

- perfect stable readout / zero-effect behavior
- clear fixed-frame degradation with the exact test
- degradation plus A2 rescue
- A2 rescue prohibited when the D-fixed gate is closed
- A1-only and A2-beyond-A1 contrasts
- exact discordance cases
- missing FIT class
- unexpected classifier class
- non-finite representation
- non-finite probability
- classifier fitting exception
- convergence-warning-compatible finite output handling
- cross-split full concordance
- partial concordance including the exact-zero unsupported split case

## Formal-run fail-closed behavior

`python experiments/exp022a/run_exp022a.py --formal-run` exits nonzero with
`FORMAL_RUN_NOT_AUTHORIZED` before prompt/data loading, tokenizer loading, model
loading, CUDA initialization, representation extraction, FIT/EVAL, bootstrap,
or scientific gate calculation. No authorization artifact is created.

## Task-094C-P publication engineering patch

Task-094C independently rereviewed the runner as scientifically faithful but
identified three publication/collision engineering defects:

- formal-result validation was not reachable from a production publication path;
- atomic publication was not reachable from a production publication path;
- collision checking used a stale `.tmp` path while the atomic writer used
  `.staging`, so an existing actual staging file could be overwritten.

Patch resolution:

- single staging-path authority via `staging_path_for`;
- collision checking and atomic writing both use `exp022a_results.json.staging`;
- staging creation uses exclusive `open("x")` semantics;
- canonical publication uses `os.link`, so an existing result is never replaced;
- `finalize_formal_result` explicitly orders schema validation, collision
  validation, and atomic publication;
- `run_formal` exposes the intended post-authorization finalization call graph
  while the authorization gate remains fail-closed;
- A0/A1/A2 object-reuse, EVAL-leakage, collision, and publication tests were added.

Scientific implementation semantics are unchanged. Model qualification has not
been performed and formal execution remains unauthorized.

## Known non-scientific implementation choices

- JSON serialization uses UTF-8, two-space indentation, and sorted keys for
  deterministic engineering artifacts.
- Bootstrap uses the independent fresh-stream choice documented above.
- Temporary atomic publication files are derived only through
  `staging_path_for` and use the canonical filename plus `.staging`.
- Warnings are serialized as strings in the result warnings list.

These choices do not change scientific hypotheses or primary gates.

## Test results

- Focused: `pytest -q tests/test_exp022a_runner.py` 鈥?`35 passed`
- Full: `pytest -q` with repository root on `PYTHONPATH` 鈥?`602 passed, 2 skipped`
- Warnings: seven existing scikit-learn `FutureWarning` items related to
  `penalty` deprecation; no new scientific warning was suppressed.

## Task-094D runtime qualification blocker

Task-094D was blocked before model/tokenizer load because the production
representation helpers were NumPy-only and the block27 hook was a placeholder.

- Classification: `ENGINEERING_RUNTIME_INTEGRATION_GAP`
- Not a scientific failure.
- Not a model failure.
- Not an EXP-022A failure.
- Not-yet-executed runtime qualification checks remain `NOT_OBSERVED`,
  `NOT_EVALUATED`, or `BLOCKED_BY_RUNTIME_INTEGRATION`.

## Task-094D-P torch runtime patch

Engineering-only patch that adds the production PyTorch/CUDA-compatible
representation-runtime bridge:

- torch import with no CUDA initialization on module import;
- torch-aware `last_valid_token_indices` that stays on-device;
- torch-aware `select_last_valid_token` and
  `select_last_valid_token_at_indices`;
- `to_float32_analysis_array` using `detach -> CPU -> NumPy -> float32`;
- finite-value validation at the analysis conversion boundary;
- decoder-block output normalization for tensor and tuple/list outputs;
- explicit `ForwardHookCapture` container with missing/multiple detection;
- non-mutating forward-hook factory and lifecycle context manager with cleanup;
- checkpoint extraction from `hidden_states[17]` through `hidden_states[28]`
  plus the captured block27 pre-final output;
- same-index last-token extraction across all checkpoints.

Static and synthetic preflight remain non-runtime. The formal-run gate remains
fail-closed before any new runtime helper is reachable.

- Model runtime qualification: `NOT YET COMPLETED`
- Formal EXP-022A execution: `NOT AUTHORIZED`
- Scientific implementation semantics: `UNCHANGED`

Focused test result: `pytest -q tests/test_exp022a_runner.py` -> `54 passed`.

Full test result: `PYTHONPATH=. pytest -q` -> `621 passed, 2 skipped`.

## Remaining qualification steps

- Targeted independent rereview of the Task-094D-P runtime-integration patch.
- Future Task-094D model/tokenizer/hook engineering qualification under
  separate authorization.
- Future formal execution authorization.

No model, tokenizer, controlled prompt text, formal FIT/EVAL data, formal
hidden states, or formal scientific result was accessed or created by Task
094B.
