# EXP-020A Formal-Run Readiness Review

## Scope and exclusions

Task 082B was an independent, fail-closed review of the committed EXP-020A
runner at `0f03d65ec8328691f46405538cc8d7b9a3ecd83d`.  No active authorization
artifact was created; no formal FIT/EVAL inference, tokenization, probe
fitting, intervention, scientific-effect calculation, or result publication
was performed.  Formal data access was limited to LEVEL 1 hashes, schema,
identifier, split, and count checks.  No formal prompt or source text is
reproduced here.

## Authority chain and entry state

Scientific authority was reviewed in the required order: the frozen config and
qualification artifacts, preregistration validator, preregistration, then
handoff context.  Executable-semantics authority was reviewed in the required
order: implementation specification, its validator, implementation-spec
document, committed tests, runner, and committed preflight evidence.

Entry HEAD was `0f03d65ec8328691f46405538cc8d7b9a3ecd83d` on
`main...origin/main`, with a clean worktree.  Required ancestors
`bec0233ff047389dce38a81e62f2914ced8a1ebd` and
`18579a1074d2c5f7a3873f2890f223b3653a94e9` are ancestors of HEAD.  No active
authorization file, no formal result artifact, and neither Task 082B report
existed at entry.

All checked frozen authority files were clean relative to HEAD.  The
preregistration validator passed, including the frozen prompt hash
`72dab733e6a1639dfc80d186f3af1dbce5c6d70da4905e6d6d422cf47064c472`, source
conditions hash, split/transition manifest, model revision, and local model
config hash.  The implementation-specification validator passed and reported
`PRIMARY_READY = true`, `SECONDARY_READY = true`, `FULL_READY = true`, and
`READY_FOR_EXP020_RUNNER_IMPLEMENTATION`.

## Runner control-flow audit

* No mode: argparse rejects execution before runner action.
* `--static-preflight`: invokes both validators and performs metadata/runtime
  checks without formal prompt text or weights, but its CLI path unconditionally
  writes the committed `experiments/exp020/results/runner_preflight.json`.
  It was therefore not run in this review.
* `--neutral-model-preflight`: first runs static preflight, then loads the
  local model with only the committed neutral diagnostic sentence and discards
  transient tensors.  It also writes `runner_preflight.json`; the previously
  committed engineering evidence was reviewed rather than rerun.
* `--formal-run`: starts with `validate_formal_authorization()` before formal
  prompt loading, model initialization, tokenizer invocation, result guard,
  probe fitting, inference, or formal RNG use.

The no-mode and missing-authorization tests pass.  Synthetic temporary-file
checks additionally showed missing authorization is blocked, malformed JSON
stops with `JSONDecodeError` before any later formal action, and mismatched
required values are blocked.  These are fail-closed for the tested cases.

## Authorization-boundary audit

The committed authorization path is
`experiments/exp020/exp020_formal_run_authorization.json`.  The implementation
requires `experiment = EXP-020A`, `formal_run_authorized = true`, the fixed
protocol and implementation-specification commit values, and `runner_commit`
equal to current HEAD.  It is consequently bound to EXP-020A and the runner
commit.

However, it does not bind authorization to the frozen config hash, prompt hash,
source-conditions hash, split/transition-manifest hash, or model-config hash.
It also does not make an independently structured FIT/EVAL scope declaration.
Further, after authorization the formal path does not run either frozen
validator or equivalent hash checks before opening the formal prompt file.
Thus a locally changed prompt/config/manifest authority set is not rejected by
the formal path itself.  This conflicts with the frozen pre-run sanity checks
and does not establish a fail-closed boundary for the complete frozen authority
set.

## Computation and bootstrap audit

The in-memory arithmetic implementation matches several frozen mechanics:
plain raw text routing, hidden-state indices 19 and 27 for blocks 18 and 26,
last-token extraction through `[0, -1, :]`, detach/CPU/float32/NumPy transfer,
FIT-only centroids and probe fitting, `target - source`, norm-matched random
directions, opposite directions, explicit `classifier.classes_` probability
mapping, paired effects, and primary-only gating.  The secondary path is
configured as block 26, beta 0.5, descriptive only.

The bootstrap implementation is consistent with the frozen manifest-derived
order: two complementary strata, 12 source-item clusters per stratum, three
target transitions per cluster, shared PCG64(20260812) resampling, 10,000
resamples, arithmetic means, linear percentile endpoints, sample SD (`ddof=1`),
strict positivity, and retained degenerate samples.  The implementation-spec
tests confirm ordering invariance, cluster grouping, shared plans, nonfinite
technical invalidity, insufficient-cluster invalidity, and that the secondary
layer cannot rescue the primary gate.  The documentation correctly treats 72
transition-item observations as clustered observations, not 72 independent
prompts.

Nevertheless, the missing runtime frozen-authority revalidation described
above is a computation-path semantic mismatch: formal data can be opened after
commit-bound authorization without first verifying the frozen input/hash set.

## Result-publication audit

Raw hidden states are not serialized, and the implementation stages under a
sibling temporary directory then atomically renames the completed directory.
The tested staging failure does not publish the target output directory.

This is not sufficient for formal readiness.  The runner's result guard looks
for the preregistered CSV/JSON filenames, whereas `_atomic_publish` writes
`effect_rows.json`, `probe_rows.json`, `transition_rows.json`, `pair_rows.json`,
and `representation_summary.json`.  Therefore an existing prior publication in
that actual JSON shape is not detected by `_require_no_formal_results()` before
model inference.  The publication also accepts empty probe/transition/pair row
lists and does not emit the expected validation summary or metadata binding
results to frozen hashes, model revision/config, runtime, runner commit, and
formal authorization.  Technical-invalidity provenance cannot be serialized in
the required result contract.  These are result-publication risks, not merely
formatting differences.

## Formal input and model integrity audit

At LEVEL 1, the prompt/source hashes passed, the prompt schema contained 24
unique IDs with six items in each of four task groups, the two frozen splits
were complementary (12 FIT and 12 evaluation IDs each), all referenced IDs
existed, and the design had 12 valid ordered transitions, 24 source-item
clusters, and 72 transition-item rows per bootstrap replicate.

The local canonical model path exists.  Its config hash matches the frozen
value and reports `Qwen3ForCausalLM`/`qwen3`, 36 transformer blocks, hidden
size 2560, and vocabulary size 151936; tokenizer files and the safetensors
index are present.  The runtime versions and CUDA BF16 availability match the
frozen expectation.  No model was loaded in this review.

## Validation results

* `validate_exp020_preregistration.py`: PASS.
* `validate_exp020_implementation_spec.py`: PASS with all three readiness
  flags true.
* AST syntax validation of `run_exp020a.py`: PASS.
* Targeted implementation-specification and runner tests: 49 passed (one
  non-failing scikit-learn deprecation warning).

## Unresolved critical findings

1. Formal authorization is not bound to the complete frozen authority/hash
   set, and formal mode does not rerun equivalent validation before formal
   source access.
2. Formal output guarding and actual atomic-publication schema differ; the
   publication lacks required provenance/validation metadata and permits empty
   result sections.

## Final readiness status

`FORMAL_RUN_REVIEW_BLOCKED_RUNNER_SEMANTIC_MISMATCH`

The publication risk is independently critical.  No repair was made in this
review, and no authorization, commit, or push is permitted under the blocking
status.

## Experiment-impact statement

* Evidence impact: no new scientific evidence; only runner/readiness assurance.
* Interpretation boundary: no claim about behavioral control, reasoning improvement, scale invariance, task manifolds, or cognitive-space transformation.
* Publication impact: may improve reproducibility and internal validity, but does not increase empirical result strength.
* Next gate: a separate explicit user decision on formal-run authorization.
