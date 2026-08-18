# EXP-024 Model / Tokenizer / Checkpoint-Hook Qualification

Status: `QUALIFICATION_PASSED`

## Qualification Identity

- Experiment: `EXP-024`
- Qualification type: `NON_FORMAL_MODEL_TOKENIZER_HOOK`
- Schema version: `1.0.0`
- Qualified runner source commit:
  `5ced3f707d6ea7cf0699262e7ea8755e29fbd6d7`
- Qualified runner SHA-256:
  `07fd3dd2b9980a69f2e35a07245240b8ca7b61a50ca944392922499500239379`
- Fresh qualification artifact path:
  `experiments/exp024/engineering/model_hook_qualification.json`
- Fresh qualification artifact SHA-256:
  `133c62aa2c00e37c0b5dbf52e53999fa40cc7e0ff3ef372f1c3649c4d73e303f`

## Qualified Runner

- CLI entrypoint: `python experiments/exp024/run_exp024.py --model-hook-qualification`
- Exit code: `0`
- Runner remained byte-identical during qualification.
- Static preflight: `PASS`
- Focused runner tests: `48 passed`

## Frozen Authority Binding

- Frozen dataset:
  `46c832b68b6ac95704bf5143badc1431627d7f935648842a78971491b13ee404`
- Final preregistration:
  `55f9604d904fd389da28c6214082028faca081f7e3a0c87c8ba8d961f792d810`
- Frozen manifest:
  `1409a33e300463067ffc060afa58ceb238fda8d6dc2479563c886a8474748f59`

## Local Model / Revision

- Model identity: `Qwen/Qwen3-1.7B`
- Revision: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Local snapshot:
  `D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-1.7B\snapshots\70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Model class: `Qwen3ForCausalLM`
- Model type: `qwen3`
- Transformer blocks: `28`
- Hidden size: `2048`
- Device: `cuda:0`
- Runtime dtype: `float16`
- Evaluation mode: `true`

## Tokenizer Result

- Tokenizer class: `Qwen2Tokenizer`
- Qualification input count: `4`
- Token counts: `9`, `15`, `14`, `18`
- Attention-mask shapes: `[1,9]`, `[1,15]`, `[1,14]`, `[1,18]`
- Last token ID for all inputs: `13`
- Last token special status: `false`
- No unregistered padding, truncation, chat template, or prompt wrapping was
  applied.

## Reference Checkpoint Result

- Checkpoint: `block16_pre_final_rmsnorm`
- Registered hidden-state equivalent: `hidden_states[17]`
- Status: `QUALIFIED`
- Shape: `[2048]`
- Output dtype: `float32`
- Finite: `true`
- Reference extraction was reached for all four neutral inputs.

## Final Checkpoint Result

- Checkpoint: `block27_pre_final_rmsnorm`
- Production hook target: `model.model.layers[27]`
- Status: `QUALIFIED`
- Shape: `[2048]`
- Output dtype: `float32`
- Finite: `true`
- The post-final `block27_post_final_rmsnorm` path was also captured as
  secondary metadata and remained finite.

## Hook Cardinality / Cleanup

- Hook firing counts: `1, 1, 1, 1`
- EXP-024-owned hooks remaining: `0`
- Foreign hooks remaining after forward: `1` per pass
- Cleanup criterion: `EXP024_OWNED_HANDLES_REMOVED`
- Total-module-zero criterion: not required
- Hook cleanup: `PASS`

The remaining foreign hook is Transformers' internal output-capturing hook and
is not EXP-024 state.

## Repeatability

- Procedure: two identical eval-mode forward passes on the first fixed neutral
  input.
- Tolerance: `1e-6`
- Observed maximum absolute difference: `0.0`
- Repeatability: `PASS`

## Formal-Data Firewall

- Frozen dataset hash verified: `true`
- Formal record content used: `false`
- Formal dataset text tokenized: `false`

## Scientific-Access Audit

- Formal classifier fit performed: `false`
- Formal recalibration performed: `false`
- Balanced accuracy computed: `false`
- `S_diag` computed: `false`
- `G_eval` computed: `false`
- Primary Spearman computed: `false`
- Primary permutation test performed: `false`
- Formal authorization created: `false`
- Formal authorization consumed: `false`
- Formal result created: `false`
- Scientific outcome observed: `false`

## Historical Failed Qualification

The prior qualification attempt belongs to old runner
`f28c2fde1abad184ee38105c4e31da7aa1aff42df2704624bb2f40724afa0eca`
and source commit
`c9c72047b8d3f35e23ba08a46c862aeb37e89a76`.

It failed because the old cleanup criterion required zero total module hooks,
which incorrectly treated a Transformers internal output-capturing hook as an
EXP-024 qualification leak.

Historical artifact SHA-256:
`b46e9b78a7ae8f8725d86f52f0dc4fae61be6fce8025de1d661954e6d469f0c8`

Authorization eligibility:
`false`

## Final Technical Verdict

`EXP024_098B_R2_MODEL_TOKENIZER_HOOK_QUALIFICATION_COMPLETE`

`EXP024_QUALIFICATION_STATUS = QUALIFICATION_PASSED`

`EXP024_QUALIFICATION_GATE = READY_FOR_SINGLE_USE_FORMAL_AUTHORIZATION`
