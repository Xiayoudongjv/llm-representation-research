# EXP-022A Model / Tokenizer / Hook Engineering Qualification

THIS IS NOT AN EXP-022A SCIENTIFIC RESULT.

## Classification

- Classification: `ENGINEERING_MODEL_HOOK_QUALIFICATION_ONLY`
- Scientific result status: `NOT_RUN`
- Formal execution: `NOT AUTHORIZED`
- Formal data accessed: `false`
- Controlled prompt text accessed: `false`

## Model snapshot

- Model: `Qwen/Qwen3-1.7B`
- Snapshot identity: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Local-only execution: `true`
- Snapshot identity check: `PASS`

## Runtime identities

- Python: `3.11.9`
- PyTorch: `2.12.1+cu130`
- Transformers: `5.14.1`
- NumPy: `2.4.6`
- CUDA runtime: `13.0`
- GPU: `NVIDIA GeForce RTX 5060 Laptop GPU`
- Runtime dtype: `float16`
- Model class: `Qwen3ForCausalLM`
- Model type: `qwen3`
- Hidden size: `2048`
- Transformer blocks: `28`
- Model vocab size: `151936`
- Tokenizer class: `Qwen2Tokenizer`
- Tokenizer vocab size: `151669`
- Tokenizer padding side: `right`
- Tokenizer EOS token: `<|im_end|>`
- Tokenizer pad token: `<|endoftext|>`

## Tokenizer contract

- `return_tensors = "pt"`
- `padding = false`
- `truncation = false`
- `add_special_tokens = true`
- Tokenizer runtime identity: `PASS`
- Special-token runtime contract: `PASS`

## Neutral inputs

Two engineering-only neutral sentences were used. Only their SHA-256 hashes
are recorded here:

- `4784035b928a0165896d636aa29130b9a84519c93fd921024810d29f21d33834`
- `c1fba21d857d2154bdb2a08e46ce2ca05a7eb3e1cf4d65e85054c22a05460547`

No neutral text, token IDs, hidden vectors, hidden tensors, logits, formal
labels, or scientific predictions are stored in the qualification artifacts.

## Real hidden-state tuple

- Required hidden-state tuple length: `29`
- Observed hidden-state tuple length: `29`
- Result: `PASS`

## Hook oracles

- Block16 hook equals `hidden_states[17]`: `PASS`
- Block26 hook equals `hidden_states[27]`: `PASS`
- Block27 pre-final hook captures decoder-block output: `PASS`
- Block27 hook output is not block input: `PASS`
- Block27 hook output is not post-final RMSNorm: `PASS`
- Final RMSNorm relationship `final_norm(H_pre) ~= H_post`: `PASS`
- Primary pre/post RMSNorm distinction: `PASS`

## Hook safety

- Hook zero perturbation: `PASS`
- Hook cleanup after hooked forward: `PASS`
- No stale hook triggered after removal: `PASS`

## Production runtime helpers

- Last-valid-token runtime check: `PASS`
- Float32 analysis boundary check: `PASS`
- All checkpoint runtime shapes: `PASS`
- Frozen checkpoint mapping preserved: `true`

## Engineering artifact

- Artifact: `experiments/exp022a/engineering/model_hook_qualification.json`
- Artifact SHA-256:
  `5f2e82180ccb1381626513758209b060f43e3f70431d08c15a1e74af0fe4ffe2`

## Qualification verdict

- Overall qualification status: `MODEL_HOOK_ENGINEERING_QUALIFIED`
- Technical validity: `VALID`
- This qualification does not authorize formal EXP-022A execution.
