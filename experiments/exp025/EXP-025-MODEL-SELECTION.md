# EXP-025 Model Selection

Status: `FROZEN_DESIGN_NOT_RUN`

## Primary Model

- Model ID: `allenai/OLMo-2-0425-1B-Instruct`
- Exact immutable revision: `48d788eca847d4d7548f375ad03d3c9312f6139e`
- Model family: `OLMo2`
- Architecture: `Olmo2ForCausalLM`
- `model_type`: `olmo2`
- License: `apache-2.0`
- Reported BF16 parameter count: `1484916736`

## Frozen Config Identity

- `config.json` SHA-256:
  `0d15ebb6cb8d998513b46ef337214176a6fd59fe5f16b30387c70d5f87795a9c`
- `tokenizer_config.json` SHA-256:
  `50c412c57d832057a3d5db42064c741f751e570f7c8788f037bfb0d2dd6e5f49`
- `special_tokens_map.json` SHA-256:
  `78afb564e81264029b25f9caf24bda2521d5bdaeff5cd3fdbc01d3da2e8ce2f2`

These identities are bound to the exact revision and must be verified again
before model access in Task 100B.

## Architecture Metadata

- `num_hidden_layers`: `16`
- `hidden_size`: `2048`
- `num_attention_heads`: `16`
- `num_key_value_heads`: `16`
- `intermediate_size`: `8192`
- `hidden_act`: `silu`
- `max_position_embeddings`: `4096`
- `vocab_size`: `100352`
- `torch_dtype`: `bfloat16`
- `tie_word_embeddings`: `false`
- `use_cache`: `false`
- `rope_theta`: `500000`
- `rms_norm_eps`: `1e-06`
- `pad_token_id`: `100277`
- `eos_token_id`: `100257`
- `attention_bias`: `false`
- `attention_dropout`: `0.0`

## Tokenizer Identity

- Tokenizer class: `GPT2Tokenizer`
- `bos_token`: `<|endoftext|>`
- `eos_token`: `<|endoftext|>`
- `unk_token`: `<|endoftext|>`
- `pad_token`: `<|pad|>`
- Special/control tokens relevant to qualification:
  - `<|endoftext|>`: special
  - `<|pad|>`: special
  - `<|endofprompt|>`: special
  - `<|im_start|>`: special
  - `<|im_end|>`: special
  - `<|fim_prefix|>`, `<|fim_middle|>`, `<|fim_suffix|>`: special
  - `<|extra_id_0|>` through `<|extra_id_10|>`: non-special added tokens
- `add_prefix_space`: `false`
- `clean_up_tokenization_spaces`: `false`

The model has a chat template, but EXP-025 does not automatically apply it to
the scientific records. Tokenizer behavior must be verified in Task 100B.

## Selection Reason

The primary model is selected for these non-benchmark reasons:

1. Independent model family from the EXP-024 Qwen3-1.7B anchor.
2. Small enough for the current RTX 5060 Laptop GPU with about 8GB VRAM.
3. Post-trained conversational model consistent with the Paper-A phenomenon
   context.
4. Open and reproducible model assets under an Apache-2.0 license.
5. Engineering compatibility with Transformers causal-language-model
   representation extraction.

Benchmark performance is not a selection reason.

## Fallback Rule

Technical fallback candidate:

```text
google/gemma-3-1b-it
```

The fallback may be activated only before any EXP-025 semantic scientific
outcome is observed, and only for a technical failure:

- OLMo cannot be downloaded
- OLMo cannot be loaded
- unsupported runtime
- hidden-state extraction impossible
- hard VRAM incompatibility

Forbidden fallback reasons:

- OLMo semantic separability poor
- OLMo degradation absent
- OLMo recalibration weak

Those are scientific or qualification outcomes, not technical fallback
reasons.

## Model Shopping Prohibition

Once OLMo semantic measurement qualification begins:

```text
MODEL_LOCKED = true
```

After that:

- no Llama
- no Gemma
- no Phi
- no third model

until EXP-025 scientific status is formally interpreted.

## Hardware Feasibility

- Expected GPU: CUDA-capable RTX 5060 Laptop GPU, about 8GB VRAM.
- OLMo-2-0425-1B-Instruct is about 1.49B parameters, comparable to the Qwen3
  anchor in footprint.
- Prefer BF16/FP16 loading.
- Use conservative batch sizes and streaming extraction.
- Do not store large raw hidden-state tensor artifacts.

## Local Runtime Note

The installed local Transformers version is `5.14.1`, while the model config
records `transformers_version = 4.50.0`.

This is a compatibility fact to verify, not a model-shopping reason. If the
exact revision cannot be loaded in local offline mode with correct OLMo2 hook
semantics, report a technical qualification failure and apply the fallback rule
only if no semantic outcome has been observed.
