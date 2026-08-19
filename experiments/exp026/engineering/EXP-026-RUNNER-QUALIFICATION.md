# EXP-026 Runner Qualification

## Scope

- Classification: `ENGINEERING_MODEL_HOOK_QUALIFICATION_ONLY`
- Experiment: `EXP-026`
- Frozen implementation commit: `045873d31d65eeaed426177299bb4a9cf83b2747`
- Runner: `experiments/exp026/run_exp026.py`
- Runner SHA-256: `c9b4bf3c9244468f1cc572c54990d092c155cf430c78d3ace63b153e857b7188`
- Qualification JSON: `experiments/exp026/engineering/exp026_runner_qualification.json`

## Entry Gates

- `EXP026_DESIGN_VALIDATION = PASS`
- `EXP026_FROZEN_AUTHORITIES_MATCH = true`
- `EXP026_SPECIFICATION_GAPS = 0`
- Tracked tree before qualification was clean with expected historical untracked artifacts left untouched.

## Real Runtime Identity

| Model | Class | `model_type` | Layers | Hidden | Runtime dtype | Device |
| --- | --- | --- | ---: | ---: | --- | --- |
| `Q` | `Qwen3ForCausalLM` | `qwen3` | 28 | 2048 | `torch.bfloat16` | `cuda:0` |
| `O` | `Olmo2ForCausalLM` | `olmo2` | 16 | 2048 | `torch.bfloat16` | `cuda:0` |

GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`

## Neutral All-Layer Extraction

- `EXP026_QWEN_ALL_LAYER_EXTRACTION = PASS`
- `EXP026_OLMO_ALL_LAYER_EXTRACTION = PASS`
- `EXP026_QWEN_LOGICAL_LAYER_COUNT = 28`
- `EXP026_OLMO_LOGICAL_LAYER_COUNT = 16`
- Both models returned finite `float32` matrices with shape `[num_layers, hidden_size]`.
- Repeated neutral forward pass produced determinism `max_abs_diff = 0.0`.

## Boundary Checks

- Extraction uses registered last-valid-token selection from the actual attention mask.
- CUDA tensors are detached, moved to CPU, converted to `float32`, then converted to NumPy.
- No raw tensors are persisted.
- Formal dataset records were not read, tokenized, or forwarded.

## Non-Scientific Status

- `EXP026_REAL_FIT_ACCESSED = false`
- `EXP026_REAL_DIAG_ACCESSED = false`
- `EXP026_REAL_EVAL_ACCESSED = false`
- `EXP026_REAL_SCIENTIFIC_INFERENCE_PERFORMED = false`
- `EXP026_SCIENTIFIC_RESULT_CREATED = false`
- `EXP026_FORMAL_AUTHORIZATION_CREATED = false`

## Result

- `EXP026_ENGINEERING_QUALIFICATION = PASS`
- Next task: `101D_EXP026_ADVERSARIAL_RUNNER_REREVIEW`
