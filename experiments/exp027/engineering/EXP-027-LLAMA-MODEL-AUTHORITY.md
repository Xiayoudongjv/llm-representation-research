# EXP-027 Llama Model Authority and Runtime Preparation

Status: `PROSPECTIVE_ENGINEERING_QUALIFICATION_ONLY`

Task: `102A-LQ_EXP027_LLAMA_MODEL_AUTHORITY_QUALIFICATION`

This document archives pre-scientific engineering evidence. It is not an
EXP-027 preregistration, authorization, or scientific result.

## Science Firewall

- Real EXP-024/026/027 FIT/DIAG/EVAL records: `NOT_ACCESSED`
- EXP-027 scientific compatibility matrix: `NOT_COMPUTED`
- SDI / LOW-D recovery / third-model classification: `NOT_COMPUTED`
- Formal authorization: `NOT_CREATED`
- Formal run: `NOT_PERFORMED`
- Scientific outcome: `NOT_OBSERVED`

## Selected Model Authority

- Selected model: `Meta-Llama-3.2-1B-Instruct`
- Source: `META_OFFICIAL_NATIVE_DISTRIBUTION`
- Native path: `D:\AI_Cache\llama_home\.llama\checkpoints\Llama3.2-1B-Instruct`
- Converted path: `D:\AI_Cache\llama_hf\Llama3.2-1B-Instruct-meta-converted-v4463-attempt3`
- `META_NATIVE_MD5_VERIFIED = true`
- `META_NATIVE_SHA256_CAPTURED = true`

Native SHA-256:

- `checklist.chk`: `EFEFC79FC47ECCE1C3E06A6AE77A4CDDC7E6078F822EFBA22E4FC7F9DA02400E`
- `consolidated.00.pth`: `FC17D497DF5E4175B3A8ACB4F5865B26F7FC1B009B25BEF814B95FDE10E8A1F3`
- `params.json`: `1D616A44F3CDAC29B9288CF14718B76EB1BED56ED38BE1F7E39B06ED139E3733`
- `tokenizer.model`: `82E9D31979E92AB929CD544440F129D9ECD797B69E327F80F17E1C50D5551B55`

Meta MD5:

- `consolidated.00.pth`: `5b6352294a545ebeb2e41d5638656a27`
- `params.json`: `69582ec3cc4a5f0bf8e2b1fcc04c3c6a`
- `tokenizer.model`: `08292403f8b173e7524d7fba7bbbd2d3`

## Conversion History

- Attempt 1: `FAILED_TOKENIZER_VOCAB_MISMATCH` (`tokenizer/config vocab 128002` vs native weights `128256`). Not reused.
- Attempt 2: `FAILED_MISSING_ACCELERATE_DEPENDENCY`. Not reused.
- Attempt 3: `PASS`.

Stable converter environment:

- `transformers = 4.46.3`
- `tokenizers = 0.20.3`
- `torch = 2.12.1+cpu`
- Accelerate installed

Converted `model.safetensors` SHA-256:

`1FF795FF6A07E6A68085D206FB84417DA2F083F68391C2843CD2B8AC6DF8538F`

## Converted Config

- Architecture: `LlamaForCausalLM`
- Hidden size: `2048`
- Intermediate size: `8192`
- Layers: `16`
- Attention heads: `32`
- KV heads: `8`
- Vocab size: `128256`
- Max position embeddings: `131072`
- Rope theta: `500000.0`
- Tied word embeddings: `true`
- Dtype: `bfloat16`

## Tokenizer Qualification

- Vocab: `128256`
- BOS: `<|begin_of_text|>` (`128000`)
- EOS: `<|end_of_text|>` (`128001`)
- EOT: `<|eot_id|>` (`128009`)
- Chat template used: `false`
- Input mode candidate: `RAW_TEXT` (must be frozen only in Task 102B)

## Project-Runtime Neutral Qualification

- `transformers = 5.15.0`
- `torch = 2.12.1+cu130`
- CUDA load: `PASS`
- Runtime dtype: `torch.bfloat16`
- Model class: `LlamaForCausalLM`
- Logical blocks: `16`
- Hidden size: `2048`
- Device: `cuda:0`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`
- Peak VRAM: approximately `2393.5 MB`
- Neutral logits shape: `(1, N, 128256)`

## Carrier Semantics

- `EXP027_FINAL_HIDDEN_STATE_SEMANTICS = POST_FINAL_NORM_CONFIRMED`
- `EXP027_CARRIER_API = FORWARD_HOOK_DECODER_BLOCK_OUTPUT`
- `EXP027_CARRIER_MAPPING = VERIFIED`
- Logical layer `l` maps to `model.model.layers[l]`.
- Extraction path: hook output -> last valid token -> detach -> CPU -> float32 -> NumPy.
- Final hidden state is after model-level final norm; decoder-block hooks are pre-final-norm for block 15.

## Native-to-Converted Provenance

Artifact: `experiments/exp027/engineering/llama32_native_converted_provenance.json`

- Native tensors: `147`
- Converted safetensors tensors: `146`
- `output.weight` is tied to `tok_embeddings.weight`; no separate `lm_head.weight` is stored.
- Direct mapped tensors match exactly.
- Q/K require the official Meta-to-HF permutation; reconstructed Q/K tensors match exactly with zero failures.
- `EXP027_NATIVE_CONVERTED_PROVENANCE = PASS`
- `EXP027_MODEL_AUTHORITY_QUALIFIED = true`

## Bootstrap Equivalence Engineering

- EXP-026 reference implementation is preserved and not rewritten.
- Optimized prototype: `experiments/exp027/engineering/exp027_bootstrap_optimized_prototype.py`
- Tests: `tests/test_exp027_bootstrap_optimized_prototype.py`
- Focused test result: `9 passed`
- Draw sequence equivalence: `PASS`
- Registered statistic equivalence: `PASS`
- Classification equivalence: `PASS`
- Routing equivalence: `PASS`
- Synthetic speedup: `7.6059x` on the recorded synthetic benchmark.

## Outcome-Blind Progress Design

- Helper: `experiments/exp027/engineering/exp027_progress.py`
- Tests: `tests/test_exp027_progress.py`
- `EXP027_OUTCOME_BLIND_PROGRESS = IMPLEMENTED`
- `EXP027_PROGRESS_CONTAINS_SCIENTIFIC_VALUES = false`
- Allowed: timestamp, stage, completed, total, percentage, elapsed, optional ETA, heartbeat, publication status.
- Forbidden before publication: rho, SDI, LOW-D recovery, CI, support, route, condition-specific scientific values, model-comparison outcomes.
- Preferred bootstrap policy: every 100 replicates or approximately once per minute.
- Optional state file uses atomic replacement and contains only execution-progress fields.
- Console output is plain stdout, compatible with VSCode PowerShell `Tee-Object`.

## Required Flags

- `EXP027_102A_LQ_COMPLETE = true`
- `EXP027_SELECTED_MODEL = Meta-Llama-3.2-1B-Instruct`
- `EXP027_MODEL_SOURCE = META_OFFICIAL_NATIVE_DISTRIBUTION`
- `EXP027_NATIVE_CONVERTED_PROVENANCE = PASS`
- `EXP027_MODEL_AUTHORITY_QUALIFIED = true`
- `EXP027_BOOTSTRAP_REFERENCE_PRESERVED = true`
- `EXP027_BOOTSTRAP_OPTIMIZED_IMPLEMENTATION = AVAILABLE`
- `EXP027_BOOTSTRAP_DRAW_EQUIVALENCE = PASS`
- `EXP027_BOOTSTRAP_STATISTIC_EQUIVALENCE = PASS`
- `EXP027_BOOTSTRAP_CLASSIFICATION_EQUIVALENCE = PASS`
- `EXP027_BOOTSTRAP_ROUTING_EQUIVALENCE = PASS`
- `EXP027_REAL_FIT_ACCESSED = false`
- `EXP027_REAL_DIAG_ACCESSED = false`
- `EXP027_REAL_EVAL_ACCESSED = false`
- `EXP027_SCIENTIFIC_MATRIX_COMPUTED = false`
- `EXP027_PREREGISTRATION_FROZEN = false`
- `EXP027_FORMAL_AUTHORIZATION_CREATED = false`
- `EXP027_FORMAL_RUN_PERFORMED = false`

## Next Task

`EXP027_NEXT_TASK = 102B_EXP027_PREREGISTRATION_AND_FROZEN_DESIGN`
