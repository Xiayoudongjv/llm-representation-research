# Gemma 3 1B Local Smoke Test

## Model Metadata

- Model: `google/gemma-3-1b-it`
- Model class: `Gemma3ForCausalLM`
- Config class: `Gemma3TextConfig`
- Tokenizer class: `GemmaTokenizer`
- Model type: `gemma3_text`
- Parameters: 999,885,952
- Transformer blocks: 26
- Hidden size: 1152
- Declared dtype: bfloat16; runtime dtype: float16 on `cuda:0`

## Hidden-State Convention

A short no-grad forward pass returned a tuple of 27 hidden-state tensors. The
first and final shapes were both `[1, 16, 1152]`, confirming an embedding state
at index 0 followed by 26 transformer-block outputs. The final state is index
26.

## Relative-Depth Map

With `L = 26`, the proposed hidden-state indices are:

| Normalized depth | Gemma hidden-state index |
|---:|---:|
| 0.15 | 4 |
| 0.30 | 8 |
| 0.45 | 12 |
| 0.60 | 16 |
| 0.75 | 20 |
| 0.90 | 23 |
| 1.00 | 26 |

## Prompt Formatting Decision

The tokenizer has a chat template, but existing Qwen representation experiments
use raw plain-text prompts. Primary geometry replication should also use raw
plain-text prompts for comparability, unless a separately documented technical
reason requires a chat template.

## Compatibility and Resources

`src.extraction.extract_last_token_representation` ran unchanged and returned
a finite `float32[1152]` NumPy vector with L2 norm 120.43. The normalized vector
had norm 1.0, so `src.representation_metrics` accepts the result.

GPU allocated memory was 0 bytes before load, about 2.00 GB after load, and
about 2.04 GB after the short hidden-state forward. No OOM occurred. Batch size
1 is safe, and a sequential short-prompt geometry replication appears feasible.

The Gemma snapshot remains external to the repository. No weights, hidden
tensors, or result artifacts were written here.

## Implementation Note

The shared extraction and metrics utilities are architecture-compatible. For a
future offline replication runner, `src.model_loader.py` needs a small optional
local-path and `local_files_only` configuration because its current API resolves
only a model identifier through the default cache layout.
