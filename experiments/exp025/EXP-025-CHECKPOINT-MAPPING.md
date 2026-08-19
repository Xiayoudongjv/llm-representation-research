# EXP-025 Checkpoint Mapping

Status: `FROZEN_DESIGN_NOT_RUN`

This file freezes the logical residual-stream checkpoint mapping from the
EXP-024 Qwen3-1.7B construct to the EXP-025 OLMo-2-0425-1B-Instruct
architecture.

## Principle

The mapping is:

```text
logical checkpoint equivalence
```

not:

```text
module-name equivalence
```

We do not mechanically copy a Qwen RMSNorm hook name into OLMo. We first state
the representation state that EXP-024 intended to measure, then map that state
to the equivalent OLMo residual-stream carrier.

## EXP-024 Logical Construct

EXP-024 measured:

1. A reference checkpoint: a clean post-block residual-stream state, before the
   final model RMSNorm, used for fixed reference readout fitting.
2. A final checkpoint: the deepest pre-final-model-RMSNorm residual-stream
   state, used for degradation and recalibration.
3. A post-final checkpoint: the final RMSNorm output, used only descriptively.

For Qwen3-1.7B, the frozen identities are:

- `block16_pre_final_rmsnorm`
- `block27_pre_final_rmsnorm`
- `block27_post_final_rmsnorm`

## OLMo2 Architecture Anchors

Local Transformers source confirms OLMo2 `Olmo2DecoderLayer` returns the
post-attention/post-MLP residual stream after its internal post-attention and
post-feedforward RMSNorm operations:

```text
residual = hidden_states
hidden_states = self_attn(hidden_states)
hidden_states = post_attention_layernorm(hidden_states)
hidden_states = residual + hidden_states

residual = hidden_states
hidden_states = mlp(hidden_states)
hidden_states = post_feedforward_layernorm(hidden_states)
hidden_states = residual + hidden_states
return hidden_states
```

The OLMo `Olmo2Model` then applies the final `model.norm` once after all
decoder layers.

Therefore:

- Post-decoder-layer output is the pre-final-model-RMSNorm residual stream.
- `model.norm(post-decoder-layer output)` is the post-final-model-RMSNorm state.

This is the correct logical analog to the Qwen pre/post final checkpoint
distinction.

## Normalized Depth Mapping

Qwen authority:

- `num_hidden_layers = 28`
- Valid layer indices: `0..27`
- Reference block index: `16`
- Final block index: `27`

OLMo authority:

- `num_hidden_layers = 16`
- Valid layer indices: `0..15`

Mapping rule:

```text
normalized_depth = block_index / (num_hidden_layers - 1)
OLMo candidate = round(normalized_depth * (OLMo_num_hidden_layers - 1))
```

Block indices are `0-based`.

## Frozen Derivation

Reference checkpoint:

```text
Qwen normalized_depth = 16 / 27 = 0.5925925926
OLMo candidate = round(0.5925925926 * 15) = round(8.8888888889) = 9
```

Final checkpoint:

```text
Qwen normalized_depth = 27 / 27 = 1.0
OLMo candidate = round(1.0 * 15) = 15
```

Post-final checkpoint:

```text
OLMo block15 output after model.norm
```

## Frozen Checkpoint Identities

| Role | Qwen identity | OLMo identity |
| --- | --- | --- |
| Reference pre-final | `block16_pre_final_rmsnorm` | `block9_pre_final_rmsnorm` |
| Primary final pre-final | `block27_pre_final_rmsnorm` | `block15_pre_final_rmsnorm` |
| Final post-final descriptive | `block27_post_final_rmsnorm` | `block15_post_final_rmsnorm` |

## Hook Contract

Task 100B must verify, without formal scientific data:

- Hooking the OLMo decoder-layer output for layer index `9` captures
  `block9_pre_final_rmsnorm`.
- Hooking the OLMo decoder-layer output for layer index `15` captures
  `block15_pre_final_rmsnorm`.
- Applying the actual final `model.norm` to the captured
  `block15_pre_final_rmsnorm` state reproduces `block15_post_final_rmsnorm`.
- The selected representation is the attention-mask-derived last valid token,
  before CPU conversion, in float32 for analysis.
- Hooks are observational only and are removed after capture.

## Forbidden Alternatives

The following are forbidden after the design freeze:

- choosing layer 10 or 11 because a pre-qualification signal looks stronger
- using the second-to-last OLMo layer for the final checkpoint
- replacing the frozen mapping based on DIAGNOSTIC/EVAL outcomes
- any layer sweep
- reusing a Qwen classifier directly on OLMo states
