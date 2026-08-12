# EXP-017 Hook Semantics Diagnostic

## Scope

This technical diagnostic verifies the frozen EXP-017 intervention location on
Qwen/Qwen3-1.7B with one synthetic prompt. It is not a behavioral evaluation,
does not use the 80-item benchmark, and makes no task-conversion claim.

## Frozen Target Semantics

The diagnostic attaches a forward hook to `model.model.layers[16]`. It locates
the returned rank-3 hidden-state tensor without assuming that a decoder layer
returns a particular tuple layout, then replaces only its final sequence
position with `hidden_states[:, -1, :] + delta`.

The script checks a zero vector before a small synthetic nonzero vector. It
records scalar diagnostics only to standard output; no hidden states, vectors,
model weights, or result files are written.

## Recorded Run

The local-only Qwen run passed on 2026-08-12. The target was
`Qwen3ForCausalLM.model.layers[16]`, a `Qwen3DecoderLayer`; its forward output
was directly a rank-3 `Tensor` at `output` rather than a tuple. The synthetic
prompt contained 9 tokens. With four deterministic new tokens, the hook fired
once during prefill (sequence length 9, final index 8) and three times during
cached decode (sequence length 1, index 0).

The zero-vector hook produced exactly the baseline token IDs and text. The
nonzero synthetic vector had explicit shape `[1, 1, 2048]`, dtype `float16`,
and device `cuda:0`, matching the activation. Earlier positions were exactly
unchanged for every call; the final position changed on every call. Removing
the hook restored the original deterministic baseline. The hook returns a new
current block-output tensor, so it does not mutate previously stored cache
entries; the cached decode observations are therefore consistent with the
frozen semantics.

## Pass Criteria

`HOOK_DIAGNOSTIC_PASS` requires exact deterministic no-hook/zero-hook output
equality, one prompt-prefill call, one hook call per cached decode forward,
last-token-only modification, matching tensor device/dtype/shape, and baseline
restoration after hook removal. The official EXP-017 behavioral pilot remains
separately governed by its unchanged preregistration.
