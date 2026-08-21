# EXP-027 Pre-Model Neutral Engineering Audit

Status: `PROSPECTIVE_ENGINEERING_PREPARATION_ONLY`

Task: `102A-PRE_EXP027_THIRD_MODEL_NEUTRAL_ENGINEERING_PREPARATION`

This is not a frozen scientific preregistration, not a model selection, not an
authorization, and not a scientific result.

## Science Firewall

- Real EXP-024/026/027 FIT/DIAG/EVAL records: `NOT_ACCESSED`
- Frozen 10-condition scientific panel: `NOT_RUN`
- TinyLlama scientific compatibility matrices / SDI / LOW-D recovery: `NOT_COMPUTED`
- TinyLlama vs Qwen/OLMo scientific comparison: `NOT_PERFORMED`
- EXP-027 model selection: `NOT_FROZEN`
- EXP-027 formal authorization: `NOT_CREATED`
- EXP-027 scientific result: `NOT_CREATED`

## Model-Selection Rule

- Primary third-model candidate: `meta-llama/Llama-3.2-1B-Instruct`
- Predefined fallback: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Fallback revision: `fe8a4ea1ffedaf415f4da2f062534de366a451e6`
- Fallback activation rule:
  `PRE_OUTCOME_TECHNICAL_OR_ACCESS_FAILURE_ONLY`

Fallback may activate only for a pre-outcome technical/access failure such as
access denial, download failure, incompatible local framework support,
ambiguous carrier mapping, BF16/local hardware failure, or tokenizer/input
semantic incompatibility. It may not activate because a preliminary Llama
result is weak, inconvenient, `NOT_SUPPORTED`, or because TinyLlama appears
more interesting.

No scientific panel may be used before model selection is frozen.

## TinyLlama Neutral Qualification

### Identity

- Model ID: `TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- Exact revision: `fe8a4ea1ffedaf415f4da2f062534de366a451e6`
- Snapshot:
  `D:\AI_Cache\huggingface\hub\models--TinyLlama--TinyLlama-1.1B-Chat-v1.0\snapshots\fe8a4ea1ffedaf415f4da2f062534de366a451e6`
- Model class: `LlamaForCausalLM`
- `model_type`: `llama`
- Hidden size: `2048`
- Decoder block count: `22`
- Runtime dtype: `torch.bfloat16`
- Device: `cuda:0`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`

### Qualification Results

- `TINYLLAMA_NEUTRAL_LOAD = PASS`
- `TINYLLAMA_BF16_CUDA = PASS`
- `TINYLLAMA_HIDDEN_SIZE = 2048`
- `TINYLLAMA_LAYER_COUNT = 22`
- `TINYLLAMA_CARRIER_MAPPING = VERIFIED`
- `TINYLLAMA_LAST_TOKEN_EXTRACTION = PASS`
- `TINYLLAMA_REAL_PANEL_ACCESSED = false`

Carrier verification:

- `model.model.layers` length equals `22`.
- Module identities are unique.
- Carrier list excludes `embed_tokens` and model-level `norm`.
- Each of the 22 forward hooks captured exactly one decoder-block output.
- Last-token extraction yielded 22 selected arrays, each shape `[2048]`.
- All selected arrays were finite and converted through
  `BF16 -> detach -> CPU -> float32 -> NumPy`.
- VRAM peak reserved: `2332033024` bytes.
- VRAM peak allocated: `2238022656` bytes.

Qualification artifact:
`experiments/exp027/engineering/tinyllama_neutral_carrier_qualification.json`

Helper:
`experiments/exp027/engineering/tinyllama_neutral_carrier_qualification.py`

## TinyLlama Tokenizer / Input-Semantics Review

- Tokenizer class: `LlamaTokenizer`
- BOS: `<s>` (`id = 1`)
- EOS: `</s>` (`id = 2`)
- PAD: `</s>` (`id = 2`)
- UNK: `<unk>` (`id = 0`)
- Chat template available: `true`
- Default raw-text tokenization adds BOS but not EOS for a single non-chat
  string.
- `add_special_tokens=false` omits BOS/EOS.
- Chat template uses `<|user|>`, `<|system|>`, `<|assistant|>`, and appends EOS.

For future EXP-027, prefer a prospectively frozen raw-text/tokenizer rule
rather than choosing a chat template based on observed outcomes. The final
Llama-3.2 rule must be verified against the actual downloaded snapshot.

## Llama-3.2 Adapter Preparation

Do not assume TinyLlama and Llama-3.2 are implementation-identical. Separate:

- `GENERIC_LLAMA_FAMILY_ENGINEERING`
  - decoder-block discovery
  - carrier validation
  - last-token extraction
  - BF16-to-float32 analysis conversion
  - model identity/provenance capture
- `MODEL_SPECIFIC_FROZEN_MAPPING`
  - final model ID/revision
  - exact block class names
  - exact logical block count
  - tokenizer/chat-template rule
  - frozen carrier mapping

The final Llama-3.2 mapping must be verified against the actual downloaded
exact snapshot after access approval.

## Bootstrap Performance Debt

Observed EXP-026 debt: 5000 cluster-bootstrap replicates repeatedly recomputed
`C0`, `Ccal`, `D`, `R`, condition pooling, and registered summaries inside the
replicate loop, causing multi-hour / approximately single-core execution.

The EXP-026 canonical result and frozen runner history remain unmodified.

## Prospective Optimized Implementation

Prototype:
`experiments/exp027/engineering/exp027_bootstrap_optimized_prototype.py`

Optimization preserves:

- source-family cluster resampling unit
- condition stratification
- replicate count
- RNG algorithm and seed semantics
- sample-with-replacement behavior
- non-evaluable replicate handling
- `C0`, `Ccal`, `D`, and `R` definitions
- condition pooling
- distance association, SDI, and LOW-D recovery
- quantile method and CI endpoints
- routing inputs

The prototype precomputes classwise additive counts for `C0` and `Ccal` per
family cluster. Balanced accuracy is reconstructed from exact classwise
positive/correct counts rather than repeatedly materializing matrices and
calling `predict` inside every replicate.

## Equivalence Tests

Test file:
`tests/test_exp027_bootstrap_optimized_prototype.py`

Result: `9 passed`

Verified:

- Registered bootstrap CI endpoints match the reference path exactly
  (`equal_nan=true` where applicable).
- Reference and optimized paths consume the RNG draw sequence identically.
- Support classification matches the reference `_support_classes`.
- Routing inputs match the reference `classify_route`.
- Equivalence holds on a fixture with ties and class imbalance.

## Performance Benchmark

Synthetic-only benchmark, `1000` replicates, 4-layer fixture:

- Reference bootstrap runtime: `48.9951` seconds
- Optimized bootstrap runtime: `6.4418` seconds
- Synthetic speedup ratio: `7.6059x`

This is engineering planning only, not a scientific gate.

## Required Flags

- `EXP027_102A_PRE_COMPLETE = true`
- `TINYLLAMA_EXACT_REVISION = fe8a4ea1ffedaf415f4da2f062534de366a451e6`
- `TINYLLAMA_NEUTRAL_LOAD = PASS`
- `TINYLLAMA_BF16_CUDA = PASS`
- `TINYLLAMA_HIDDEN_SIZE = 2048`
- `TINYLLAMA_LAYER_COUNT = 22`
- `TINYLLAMA_CARRIER_MAPPING = VERIFIED`
- `TINYLLAMA_LAST_TOKEN_EXTRACTION = PASS`
- `TINYLLAMA_REAL_PANEL_ACCESSED = false`
- `EXP027_PRIMARY_MODEL_CANDIDATE = meta-llama/Llama-3.2-1B-Instruct`
- `EXP027_FALLBACK_MODEL_CANDIDATE = TinyLlama/TinyLlama-1.1B-Chat-v1.0`
- `EXP027_FALLBACK_ACTIVATION_RULE = PRE_OUTCOME_TECHNICAL_OR_ACCESS_FAILURE_ONLY`
- `BOOTSTRAP_REFERENCE_IMPLEMENTATION_PRESERVED = true`
- `BOOTSTRAP_OPTIMIZED_PROTOTYPE = AVAILABLE`
- `BOOTSTRAP_DRAW_SEQUENCE_EQUIVALENCE = PASS`
- `BOOTSTRAP_REGISTERED_STATISTIC_EQUIVALENCE = PASS`
- `BOOTSTRAP_CLASSIFICATION_EQUIVALENCE = PASS`
- `BOOTSTRAP_ROUTING_EQUIVALENCE = PASS`
- `BOOTSTRAP_SYNTHETIC_SPEEDUP = 7.6059x`
- `EXP027_MODEL_SELECTED = false`
- `EXP027_PREREGISTRATION_FROZEN = false`
- `EXP027_FORMAL_AUTHORIZATION_CREATED = false`
- `EXP027_REAL_FIT_ACCESSED = false`
- `EXP027_REAL_DIAG_ACCESSED = false`
- `EXP027_REAL_EVAL_ACCESSED = false`

## Next Task

`EXP027_NEXT_TASK = 102A_EXP027_FINAL_MODEL_SELECTION_AFTER_LLAMA_ACCESS`

Wait for Llama-3.2 access approval before the final model-selection audit. Do
not freeze EXP-027 or authorize a formal run in this task.