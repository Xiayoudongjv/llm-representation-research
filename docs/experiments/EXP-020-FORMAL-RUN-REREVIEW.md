# EXP-020A Formal-Run Rereview

## Scope and exclusions

Task 082D independently reviewed commit
`d080cafd1e36c0daa3128fdff50010b86a02a570`.  This was review-only.  No
authorization artifact was created; no formal prompt/source text is reproduced;
no model was loaded; no formal FIT/EVAL inference, tokenization, probe fitting,
intervention, scientific effect calculation, gate calculation, or result
publication occurred.  Formal data access was LEVEL 1: paths, hashes, IDs,
counts, schema, split membership, clusters, and transition coverage only.

## Entry gate and authority integrity

HEAD was the required `d080cafd1e36c0daa3128fdff50010b86a02a570` on
`main...origin/main`, with a clean worktree.  Required ancestors were present.
The two tracked Task 082B artifacts exist and retain their required full hashes:

* `docs/experiments/EXP-020-FORMAL-RUN-REVIEW.md`:
  `9c91360513e4b7447e4ea82f0abbb04432c714680646a95dd09d6cde0e62a9af`
* `experiments/exp020/results/formal_run_review.json`:
  `6ed6a2a5e57c7cde1b42c8bf064454f0602830eac80f9f4ac66b134b4918eeee`

Both retain `FORMAL_RUN_REVIEW_BLOCKED_RUNNER_SEMANTIC_MISMATCH`.  The frozen
config, preregistration, implementation specification, validators, formal
prompt/source files, qualification artifacts, and preflight artifact remained
unchanged.

## Task 082C diff and semantic non-drift

The diff from `0f03d65e` to `d080caf` is confined to
`experiments/exp020/run_exp020a.py` and `tests/test_exp020_runner.py`.  It adds
authorization schema/integrity logic, canonical-result validation/publication,
and synthetic tests.  The frozen computational functions for prompt rendering,
tokenizer invocation, extraction, FIT/EVAL routing, centroids, directions,
controls, probe, probability mapping, paired effects, bootstrap, primary gate,
and secondary descriptive treatment were not altered.  No scientific-semantic
drift was found.

## Authorization schema and ordering

The authorization path is
`experiments/exp020/exp020_formal_run_authorization.json`, outside the canonical
result path and not itself a result artifact.  The parser uses a closed schema,
rejects duplicate keys, and requires schema version, `EXP-020A`, exact formal
FIT/EVAL plus atomic-publication scope, `single_use = true`, UUID, timestamp,
runner commit, and all required frozen-config, preregistration, prompt, source,
split/manifest, model, model-config, and tokenizer bindings.

Before formal source/model/output/RNG work, the actual flow checks authorization
existence and schema, checks the tracked worktree, independently derives frozen
expected bindings and current observed hashes, compares all authorization
bindings, then runs both frozen validators.  Static inspection and synthetic
tests support fail-closed rejection for missing, malformed, renamed/missing,
unknown, stale-commit, dirty-worktree, and individual binding-mismatch cases.
The implementation does not trust an authorization-supplied hash as authority.

## Authorization lifecycle: critical finding

`single_use` is validated as a true field but has no consumption record, lock,
or other durable use-state.  A valid authorization can be presented again after
a failure before publication, with retry semantics undefined.  After a
successful publication, canonical-result preexistence prevents another formal
run from reaching model inference, so duplicate final results are blocked; this
does not make the declared single-use rule operational for failed pre-publication
runs.  This is a critical lifecycle defect under Task 082D.

## Canonical result path and schema

The runner resolves the canonical final path as
`experiments/exp020/results/exp020a_results.json` for preexistence checks and
publication.  Engineering artifacts such as `runner_preflight.json`,
`formal_run_review.json`, and this rereview are not classified as final results.
The pre-publication validator requires nonempty primary and secondary comparison
sections, frozen coverage/counts, finite numeric values, primary gate inputs,
technical-validity separation, and extensive authorization/frozen/runtime/Git
provenance.  It contains no prompt/source-text result field.  Existing tests
reject missing/empty sections, duplicate-or-missing coverage, nonfinite values,
missing gate inputs, technical-invalid status, and authorization digest mismatch.

## Atomic publication: critical finding

The staging JSON is flushed and fsynced before a second `exists()` check, then
published with `os.replace(staging, output_path)`.  A competing process can
create the canonical output after that second check and before `os.replace`.
On the target platform, `os.replace` may overwrite that newly created final
artifact.  Therefore the implementation cannot establish the required
never-overwrite guarantee under this race.  Existing synthetic tests cover a
preexisting result, validation failure, and staging serialization failure, but
do not cover this check-to-replace race or cleanup failure.  This is an
independent critical publication defect.

If cleanup itself fails, the current handler can leave a clearly named staging
file and propagate the cleanup failure.  It cannot create a canonical final
result by that route; this is noncritical relative to the two blockers but
should be covered in a later engineering correction.

## Frozen input and model integrity

LEVEL 1 checks passed: prompt and source hashes, split/manifest hash, 24 unique
prompt IDs, six items in each of four groups, two complementary 12/12 FIT/EVAL
splits, 12 ordered transitions, 24 held-out source-item clusters, and 72
transition-item rows per replicate.  The canonical local model config hash,
`qwen3` architecture, 36 layers, hidden size 2560, tokenizer identity/revision,
and expected Torch/Transformers/CUDA/BF16 conditions match the freeze.  No model
load was performed.

## Validation

* Preregistration validator: PASS.
* Implementation-specification validator: PASS, including all readiness flags.
* Runner AST validation: PASS.
* Targeted synthetic suites: 75 passed; one non-failing scikit-learn deprecation warning.

## Findings and final status

Critical findings:

1. `single_use` is declarative rather than durably enforced; failed-run retry
   semantics are undefined.
2. Atomic publication can overwrite a concurrently-created canonical result
   between the final existence check and `os.replace`.

Noncritical finding:

* Cleanup failure of a staging file is not explicitly tested.  It cannot publish
  or overwrite the canonical result, but may leave a clearly named temporary
  artifact.

Final status: `FORMAL_RUN_REREVIEW_BLOCKED_AUTHORIZATION_LIFECYCLE`

## Experiment impact

* Evidence impact: no scientific evidence added.
* Reliability impact: determines whether authorization and publication safeguards are adequate for a later formal run.
* Interpretation boundary: no claim about behavioral control, reasoning improvement, scale invariance, task manifolds, or cognitive-space transformation.
* Publication impact: affects reproducibility and auditability only, not empirical strength.
* Next gate: user/ChatGPT analysis of the uncommitted rereview, followed by a separate archival commit task only if accepted.
