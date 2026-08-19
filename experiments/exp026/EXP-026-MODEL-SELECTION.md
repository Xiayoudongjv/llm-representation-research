# EXP-026 Model Selection

Status: `FROZEN_DESIGN_NOT_RUN`

## Model Scope

- Design: `FULL_SOURCE_TARGET_COMPATIBILITY_MATRIX`
- Scope: `TWO_MODEL_COMPARATIVE_PROFILE`
- Primary model count: exactly `2`
- Floating revisions: prohibited

## Frozen Primary Models

### Model Q

- Model ID: `Qwen/Qwen3-1.7B`
- Exact immutable revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Model family: `Qwen3`
- Model class: `Qwen3ForCausalLM`
- `model_type`: `qwen3`
- Transformer decoder blocks: `28`
- Logical eligible block indices: `0..27`
- Hidden size: `2048`
- Local snapshot:
  `D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-1.7B\snapshots\70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`

### Model O

- Model ID: `allenai/OLMo-2-0425-1B-Instruct`
- Exact immutable revision: `48d788eca847d4d7548f375ad03d3c9312f6139e`
- Model family: `OLMo2`
- Model class: `Olmo2ForCausalLM`
- `model_type`: `olmo2`
- Transformer decoder blocks: `16`
- Logical eligible block indices: `0..15`
- Hidden size: `2048`
- Local snapshot:
  `D:\AI_Cache\huggingface\hub\models--allenai--OLMo-2-0425-1B-Instruct\snapshots\48d788eca847d4d7548f375ad03d3c9312f6139e`

## Selection Reason

The two models are selected for non-benchmark scientific reasons:

1. They are the two models behind the already observed `D+ / G+` vs `D- / G+`
   contrast.
2. They are independent model families with similar scale and existing local
   engineering infrastructure.
3. They are small enough for the current RTX 5060 Laptop GPU.
4. Both have open/reproducible model assets.
5. Both support causal-language-model hidden-state extraction.

Benchmark performance is not a selection reason.

## Claim Language

EXP-026 may establish `MODEL-DEPENDENT COMPATIBILITY ORGANIZATION`, i.e.
differences between the two frozen models.

It cannot attribute those differences specifically to architecture, training
recipe, tokenizer, model family, or scale without additional controls.

Do not use `ARCHITECTURE-DEPENDENT`, `FAMILY-DEPENDENT`, or `FAMILY CAUSAL`
language for EXP-026 scientific claims.

## Model Shopping Prohibition

Once EXP-026 semantic measurement qualification begins:

```text
MODEL_SET_LOCKED = true
```

After that, no third model, no fallback model, and no alternate snapshot may be
used for EXP-026. A technical failure must stop and report; it does not trigger
model shopping.

## Excluded Models

The following are not part of EXP-026:

- Llama
- Qwen3-4B
- Gemma
- any fallback model

## Llama Future Gate

Llama is explicitly deferred as a potential independent third-model validation
experiment.

`EXP026_LLAMA_FUTURE_GATE_DEFINED = true`.

`P3` in `experiments/exp026/EXP-026-ROUTING-RULES.md` is the only route that may
make a third-model validation scientifically useful.

If `P3` triggers later:

- Candidate third model may be `Llama-3.2-1B-Instruct`.
- Do not use the previous 8B Llama as an automatic next model.
- Audit a roughly 1B Llama-family model first to reduce scale confounding.
- A separate third-model experiment must be designed and frozen; it is not part
  of EXP-026.

## Runtime Identity Notes

- Qwen3-1.7B previously qualified as `Qwen3ForCausalLM`, `model_type=qwen3`,
  `28` blocks, hidden size `2048`, `float16` runtime.
- OLMo-2-0425-1B-Instruct previously qualified as `Olmo2ForCausalLM`,
  `model_type=olmo2`, `16` blocks, hidden size `2048`, `bfloat16` runtime.
- Actual observed runtime identity remains authoritative in the future
  engineering qualification; any critical structural mismatch fails closed.
