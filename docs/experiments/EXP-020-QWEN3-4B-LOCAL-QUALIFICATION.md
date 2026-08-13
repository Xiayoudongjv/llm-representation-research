# EXP-020 Qwen3-4B Local Snapshot Qualification

## Scope and Boundary

This is an infrastructure qualification only. It used the exact local
candidate for `Qwen/Qwen3-4B` and neutral diagnostic text, with
`local_files_only=True`. It did not open formal EXP-020 prompts, calculate
representation outcomes, inspect EXP-017, or access EXP-019.

## Canonical Snapshot and Integrity

The canonical model path is `D:\Qwen3-4B-transfer`. Download metadata records
revision `1cfa9a7208912126459214e8b04321603b3df60c`. The snapshot contains
`config.json`, tokenizer files, `generation_config.json`, and the three shards
referenced by `model.safetensors.index.json`; no referenced shard is missing
and there are no zero-byte required files.

Local-only loading identified `Qwen3Config` / `Qwen3ForCausalLM`, model type
`qwen3`, hidden size 2560, 36 transformer blocks, vocabulary size 151936, and
BF16 configuration metadata. `Qwen2Tokenizer` encoded and decoded a neutral
sentence successfully.

The candidate's weight shards total 8,044,982,000 bytes. Across the candidate
and relevant D: Hugging Face cache locations, six large model files were
hashed. There were zero exact duplicate large files, zero exact duplicate
bytes, no same-filename/different-hash groups, and no hardlink or symlink
duplicates. Duplicate cleanup status is `SAFE_TO_KEEP_ALL`.

There are partial-download residues outside the completed shard set, including
768,079,002 bytes under the candidate download metadata directory and older
residues in the Qwen3-1.7B/TinyLlama cache. They are not complete snapshots or
duplicate model bytes. They are recorded for later cleanup review only; this
task did not delete, move, or modify them.

## Frozen Hardware Qualification

The prescribed order was MODE A native BF16, then CPU offload only after a
native memory failure, then deterministic 4-bit only if offload failed or was
impractical. MODE A succeeded practically, so MODE B and MODE C were not
attempted.

An earlier invocation exited during native weight loading before it could
write a result. Its cleanup path was hardened so a CUDA cleanup error cannot
mask a loading outcome; the subsequent no-download rerun completed MODE A.
The unrecorded invocation is not treated as a separate qualification outcome.

- GPU: NVIDIA GeForce RTX 5060 Laptop GPU (7.9595 GiB); BF16 supported.
- MODE A: native BF16 on `cuda:0`.
- Allocated GPU memory after load: 7.4984 GiB.
- Forward peak GPU allocation: 7.5339 GiB.
- Forward latency: 1.2065 s; two-token generation latency: 0.3401 s.
- Hidden states: 37 tensors; final diagnostic shape `[1, 7, 2560]`.
- Frozen normalized-depth hook indices: primary 18 and secondary 26.
- Two-token deterministic generation: successful.
- Zero-intervention hook equivalence: `ZERO_HOOK_EQUIVALENCE_PASS`, maximum
  logit difference 0.0 at `rtol=0.001`, `atol=0.001`.

## Resulting Gate

Hardware qualification status is `READY_FOR_EXP020_PREREGISTRATION_REVIEW`.
The selected execution mode is `MODE_A_NATIVE`; no offload or quantized
comparison was made. This unlocks only preregistration review of the planned
EXP-020 execution. EXP-020 scientific status remains `NOT_STARTED`.
