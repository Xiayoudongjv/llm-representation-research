# EXP-026 Layer Carrier Mapping

Status: `FROZEN_DESIGN_NOT_RUN`

## Carrier Semantics

The logical layer carrier is:

```text
output residual state of each Transformer decoder block,
after that block,
before the next decoder block,
and before any model-level final normalization
```

This is the clean post-decoder-block residual stream, not the embedding state,
not the LM-head logits, and not the post-final-model-normalization state.

`FULL_LAYER_EXTRACTION_FEASIBLE = true`.

Production extraction must use forward hooks on each decoder-layer module.
`output_hidden_states=True` may be used for oracle verification only; it is not
the production carrier authority.

## Forbidden Simplification

Do not blindly equate `transformers hidden_states tuple index` with logical
block output. The final tuple element may include final model normalization and
must not be used as a block27/Qwen or block15/OLMo pre-final carrier.

## All-Block Eligibility Rule

For each model, the primary depth set is all Transformer decoder blocks.

Exclude:

- embedding state;
- LM-head logits;
- post-LM-head state;
- any inconsistent final-normalized-only carrier.

Do not select sparse favorable layers. If architecture inspection proves an
all-block consistent carrier cannot be obtained, stop and report.

## Qwen3-1.7B Mapping

- Model class: `Qwen3ForCausalLM`
- Decoder module root: `model.model.layers`
- Number of decoder blocks: `28`
- Logical block indices: `0..27`
- Hidden size: `2048`
- Carrier location for logical layer `l`: output of `model.model.layers[l]`
- Normalization status: pre-final-model-RMSNorm
- Hook behavior: observational only; no mutation.

Qwen hidden-state oracle:

- `hidden_states[0]` is the embedding output and is excluded.
- For logical layers `0..26`, `hidden_states[l+1]` is the corresponding
  post-block output and may be used for hook-oracle verification.
- `hidden_states[28]` is the post-final-model-RMSNorm state and is excluded from
  the pre-final carrier set.
- Logical layer `27` must be captured by the `model.model.layers[27]` forward
  hook; it is not read from `hidden_states[28]`.

Mapping table for logical layers `0..27`:

| logical_layer_id | module_path | block_index | carrier_location | normalization_status | hidden_size |
| --- | --- | --- | --- | --- | --- |
| `qwen_block00_pre_final_rmsnorm` | `model.model.layers.0` | `0` | post-block residual output | pre-final-model-RMSNorm | `2048` |
| ... | `model.model.layers.l` | `l` | post-block residual output | pre-final-model-RMSNorm | `2048` |
| `qwen_block27_pre_final_rmsnorm` | `model.model.layers.27` | `27` | post-block residual output | pre-final-model-RMSNorm | `2048` |

All blocks `0..27` are eligible candidates for source rows; source usability is
determined separately by the DIAGNOSTIC floor.

## OLMo-2-0425-1B-Instruct Mapping

- Model class: `Olmo2ForCausalLM`
- Decoder module root: `model.model.layers`
- Number of decoder blocks: `16`
- Logical block indices: `0..15`
- Hidden size: `2048`
- Carrier location for logical layer `l`: output of `model.model.layers[l]`
- Normalization status: pre-final-model-RMSNorm
- Hook behavior: observational only; no mutation.

OLMo hidden-state oracle:

- `hidden_states[0]` is the embedding output and is excluded.
- Post-block outputs for logical layers are verified by forward hooks. The final
  tuple element, if it corresponds to `model.norm` output, is excluded from the
  pre-final carrier set.
- Logical layer `15` must be captured by the `model.model.layers[15]` forward
  hook; it is not read from a final-normalized-only state.

Mapping table for logical layers `0..15`:

| logical_layer_id | module_path | block_index | carrier_location | normalization_status | hidden_size |
| --- | --- | --- | --- | --- | --- |
| `olmo_block00_pre_final_rmsnorm` | `model.model.layers.0` | `0` | post-block residual output | pre-final-model-RMSNorm | `2048` |
| ... | `model.model.layers.l` | `l` | post-block residual output | pre-final-model-RMSNorm | `2048` |
| `olmo_block15_pre_final_rmsnorm` | `model.model.layers.15` | `15` | post-block residual output | pre-final-model-RMSNorm | `2048` |

## Normalized Depth

For each model with `L` eligible blocks and block index `l`:

```text
d(l) = l / (L - 1)
```

- Qwen: `l in 0..27`, `L=28`.
- OLMo: `l in 0..15`, `L=16`.

Equal normalized depth is not claimed to be functionally equivalent across
models.

## Carrier Identity Contract

Future engineering qualification must verify:

- each logical layer carrier is captured exactly once per forward pass;
- hooks are observational only and removed after capture;
- selected representation is the attention-mask-derived last valid token;
- selection occurs before CPU conversion;
- final analysis array is `float32`, shape `[hidden_size]`;
- no raw tensors are persisted in Git;
- Qwen and OLMo use the same logical carrier semantics.

No layer outcome may be inspected during mapping.
