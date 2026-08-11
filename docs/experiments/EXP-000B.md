# EXP-000B: Reproducible Hidden State Extraction

## Goal

Build a reproducible GPU pipeline that loads an open-source causal language
model and extracts hidden states for a single prompt.

## Hypothesis

The model's layer-by-layer hidden states can be extracted in shape and
structure without generating text or storing full tensor artifacts.

## Model

Primary: `Qwen/Qwen3-1.7B`  
Fallback: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`

## Method

Check CUDA, load the tokenizer and causal LM, tokenize one prompt, run a
forward pass with `output_hidden_states=True` and `return_dict=True`, print a
per-layer summary, and save JSON metadata only.

## Expected Output

The console reports the number of hidden-state tensors and each tensor's layer
index, shape, dtype, and device. Metadata is saved under
`results/exp000/hidden_states_metadata.json`.

## Result

Placeholder: run the experiment locally and record the observed model,
environment, and metadata here.

## Failure Cases

- CUDA unavailable: use a CUDA-enabled PyTorch environment.
- CUDA out of memory: use the fallback model or a smaller dtype.
- Hugging Face download failure: check the model name, cache, network, or `HF_ENDPOINT`.

## Next Step

Validate extraction on both models, then use the resulting representations as
the input baseline for later task-conditioned representation experiments.
