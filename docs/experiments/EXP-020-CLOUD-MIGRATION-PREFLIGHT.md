# EXP-020 Cloud Migration Preflight

## Scope and status

This document records a source-side, file-identity preflight for moving the
unchanged EXP-020A package to a domestic container-GPU service. It does not
create a cloud resource, upload any file, load a model, authorize a formal
run, or create scientific results.

`SOURCE_PREFLIGHT_COMPLETE = true`

`EXP020_FORMAL_RUN_AUTHORIZED = false`

`EXP020_SCIENTIFIC_STATUS = NOT_STARTED`

`FORMAL_FIT_EVAL_INFERENCE_PERFORMED = false`

`FORMAL_SCIENTIFIC_RESULTS_CREATED = false`

The previous formal authorization is a consumed, non-reusable provenance
record. It is not transferable authority for a cloud run.

## Frozen source identity

- Repository commit: `7865727284d633b7d7d174773d8d7ecf5ef35869`
- Repository source root: `D:\Research\llm-representation-research`
- Model source root: `D:\Qwen3-4B-transfer`
- Model: `Qwen/Qwen3-4B`, revision `1cfa9a7208912126459214e8b04321603b3df60c`
- Architecture: `Qwen3ForCausalLM` / `qwen3`; 36 blocks; hidden size 2560;
  native BF16 target mode.
- Model config SHA-256:
  `8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a`
- Safetensors index SHA-256:
  `6dc0981b8829fead746441f68f38f24c5ca4a3a66351f652c26c6df0efc43ab2`
- Index structure: 398 tensors; raw tensor bytes `8044936192`; three indexed
  shards.

The machine-verifiable registry is
[`cloud_migration_manifest.json`](../../experiments/exp020/cloud_migration_manifest.json).
It contains every required relative path, byte size, SHA-256 digest, schema
summary, and the source/target bindings. The manifest is the authoritative
transfer checklist; this document does not duplicate controlled prompt text.

## Intended target (unverified)

The following is an engineering target selected before outcome observation, not
a verified cloud configuration:

- Provider class: `DOMESTIC_CONTAINER_GPU_SERVICE`; region: `天津一区`.
- One `MANUAL`, non-preemptible node with one requested `NVIDIA GeForce RTX
  5090` (32 GB VRAM), 26 CPU cores, 63 GB host memory, and no multi-container
  execution.
- Persistent volume: 100 GB mounted at `/workspace/persist`.
- Expected container identity: repository `pytorch/pytorch`, tag
  `2.12.1-cuda13.0-cudnn9-devel`, platform `linux/amd64`; expected digest
  `sha256:ac63aaae09996612bdaf12bbf6d5fe840af6bed3100d6dc15fcb5fd1f4f957c4`.

No cloud account, region availability, image digest, GPU model, CUDA stack,
filesystem, or runtime property was inspected during this task. All such
fields remain unverified.

## Task 084B schema correction

The independent review found that the original manifest used noncanonical
hardware aliases and did not close every validation-relevant nested object.
Task 084C corrects the migration-schema representation only:

- hardware fields now use `requested_vram_gb`, `requested_cpu_cores`,
  `requested_host_memory_gb`, `scaling_mode`, `persistent_volume_gb`, and
  `persistent_mount`; the former aliases are absent;
- the target container separately records repository, tag, expected platform,
  expected manifest digest, a null actual target digest, and false verification;
- the validator now enforces exact key sets for all relevant manifest objects,
  roots/bindings, artifact entries, authorization provenance, readiness, and
  prohibited operations;
- synthetic regression tests cover same-size and changed-size integrity
  failures, duplicate logical roles, and non-disclosure of a synthetic formal
  content sentinel.

Previous Task 084A source observations, all source file identities, and the
scientific protocol are unchanged. Cloud target qualification was not
performed, and the target remains unready for formal execution.

## Task 084E Git-binding lifecycle correction

The historical/scientific execution base is
`7865727284d633b7d7d174773d8d7ecf5ef35869`. It is the reviewed baseline for
scientific code and authority files, not the only permissible live checkout.

The manifest now has a versioned `git_binding` with an ordered, exact registry
of the four migration-infrastructure paths in this package. It supports two
explicit states:

- `source-draft`: live HEAD equals the execution base and exactly those four
  paths are untracked; and
- `archived-checkout`: live HEAD is a strict descendant whose complete delta
  from the execution base is exactly those four paths, with a clean worktree.

An archived checkout reports its observed live commit during validation. That
commit is not serialized as a supposedly final value in the source manifest.
The cloud must later check out an exact archived commit rather than a floating
branch; the exact checkout, execution base, delta paths, and validation status
belong in a future target-qualification report.

Accepting this exact migration-only descendant does not alter scientific
semantics. Arbitrary descendants, and any descendant that changes a runner,
frozen authority, input, model identity, result schema, or unrelated path, are
rejected. A new single-use authorization remains required for any future formal
execution; the prior consumed authorization can never be reused.

## Task 084F target checkout policy

The migration manifest freezes a Linux target checkout policy in the closed
`git_binding.target_checkout_policy` object. The policy requires
`core.autocrlf=false`, `core.eol=lf`, configuration before checkout, and a
detached exact-commit checkout; floating branches are prohibited.

The target procedure is equivalent to:

```bash
git clone --no-checkout <REPOSITORY_URL> /workspace/persist/repository
git -C /workspace/persist/repository config core.autocrlf false
git -C /workspace/persist/repository config core.eol lf
git -C /workspace/persist/repository checkout --detach <EXACT_ARCHIVE_COMMIT>
```

Neither a repository URL nor a future archive commit is serialized here. Both
are external deployment inputs. The archived-checkout validator reports the
runtime-observed checkout commit; a target-side prospective validation may add
`--verify-target-checkout` to verify the repository-local EOL configuration
and detached HEAD. For every repository artifact, the manifest records both
the Windows source-worktree identity and the exact execution-base Git-blob
identity. Source-draft validation checks the former plus the latter;
archived-checkout validation checks the Git objects; and target-checkout
verification additionally requires checked-out bytes to equal the Git blobs.
This preserves frozen source records even when Windows line-ending conversion
changes their working-tree bytes. The Windows source checkout need not change
its global Git configuration.

## Transfer layout and procedure

The target persistent roots are:

- Repository: `/workspace/persist/llm-representation-research`
- Model snapshot: `/workspace/persist/models/qwen3-4b`

A cloud engineer must transfer only the manifest-listed files, preserving their
relative paths under the corresponding root. Do not use a model download,
change revisions, substitute tokenizer files, or use an archive as a
verification substitute. The model snapshot must include the indexed model
configuration, all three declared safetensors shards, and all four declared
tokenizer files.

Before archival, from the source-draft repository root, run:

```powershell
python experiments/exp020/validate_cloud_migration_manifest.py `
  --manifest experiments/exp020/cloud_migration_manifest.json `
  --repo-root D:\Research\llm-representation-research `
  --model-root D:\Qwen3-4B-transfer `
  --mode source-draft
```

For a future archived checkout, substitute the transferred Linux roots and use
`--mode archived-checkout`; it additionally proves that the exact committed
delta equals the frozen four-path registry. Both modes check bytes, SHA-256
values, index-to-shard closure, controlled input schemas/IDs/counts, no formal
result, and consumed-authorization provenance. Neither mode loads a model or
authorizes EXP-020A.

## Required next gates

1. Confirm the model snapshot and repository transfer with the manifest
   validator.
2. Separately qualify the actual cloud hardware, image digest, CUDA/runtime,
   and local-only load path under a new engineering task.
3. Review any resulting qualification evidence without changing this manifest.
4. Obtain a new, explicit, single-use formal-run authorization before any
   formal FIT/EVAL inference.

Until all of these occur, the formal runner remains prohibited. No result path
may be created or replaced.

## Source-side result

The source validator was run only against the existing local repository and
snapshot. It returned `CLOUD_MIGRATION_SOURCE_PREFLIGHT_READY`. No model,
GPU, formal input text, or formal scientific result was accessed or produced.
