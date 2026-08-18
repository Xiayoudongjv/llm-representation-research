# EXP-024 Model / Tokenizer / Checkpoint-Hook Qualification

Status: `PATCHED_RUNNER_REAL_QUALIFICATION_PASSED`

## Current Authorization-Eligible Qualification (Task 098B-R4)

This is the only qualification evidence eligible for the current patched
EXP-024 runner.

- Patched runner commit:
  `1f5082e0d8246432157cb43832430ac3214e846a`
- Patched runner SHA-256:
  `709572c77110eab497d3851f0e998a0c330b5422e8e7cdea5ec9195fae99da76`
- Fresh qualification artifact path:
  `experiments/exp024/engineering/model_hook_qualification.json`
- Fresh qualification artifact SHA-256:
  `be1388b8a8e8b73f0589984e0da2cad1c17cc08c93cad7427446469089ec7463`
- Qualification status: `QUALIFICATION_PASSED`
- CLI exit code: `0`
- Frozen authority validation: `PASS`
- Focused runner tests: `86 passed`
- Standalone qualification validator: `PASS`
- Production qualification consumer: `PASS`
- Formal authorization dry verification: `PASS`
- Formal result present: `false`
- Formal authorization present: `false`

Runtime identity observed by this fresh real qualification:

- Model: `Qwen/Qwen3-1.7B`
- Model snapshot: `70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`
- Model class: `Qwen3ForCausalLM`
- Model type: `qwen3`
- Transformer blocks: `28`
- Hidden size: `2048`
- Device: `cuda:0`
- Runtime dtype: `float16`
- Tokenizer class: `Qwen2Tokenizer`

Required checkpoint/hook checks all `PASS`:

- Reference checkpoint: `block16_pre_final_rmsnorm`
- Final checkpoint: `block27_pre_final_rmsnorm`
- Hook firing cardinality: `PASS`
- EXP-024-owned hook cleanup: `PASS`
- Owned hooks remaining: `0`
- Repeatability: `PASS` with max absolute difference `0.0`
- Representation finite check: `PASS`
- Representation output dtype: `float32`

Formal/scientific firewall:

- Formal dataset hash verified: `true`
- Formal dataset record content used: `false`
- Formal dataset text tokenized: `false`
- Classifier fit: `false`
- Recalibration: `false`
- Balanced accuracy: `false`
- `S_diag` computed: `false`
- `G_eval` computed: `false`
- Primary Spearman computed: `false`
- Primary permutation test performed: `false`
- Formal authorization created/consumed: `false`
- Formal result created: `false`
- Scientific outcome observed: `false`

## Chronology

1. Historical failed real qualification: false-positive total-hook-count
   cleanup criterion.
2. Historical successful qualification: old runner
   `07fd3dd2b9980a69f2e35a07245240b8ca7b61a50ca944392922499500239379`.
3. R3 qualification: runner
   `4690115d2a322e8d89bfb3a21fa32e2c5ca758a26fa5e07c40df88af8648885e`,
   runtime `QUALIFICATION_PASSED`, but blocked by the consumer model-binding
   field-location defect.
4. Current R4 qualification: patched runner
   `709572c77110eab497d3851f0e998a0c330b5422e8e7cdea5ec9195fae99da76`,
   full runtime and production consumer verification passed.

Only item 4 is authorization-eligible for the current patched runner.

### Historical R3 Blocked Qualification

- R3 artifact SHA:
  `ea29a6b1a2841a98e2f9559731d7f418cbfa13eaab3253967faad86c364429aa`
- Archived path:
  `experiments/exp024/engineering/qualification_history/model_hook_qualification_0c9162c_4690115d_passed_consumer_blocked.json`
- R4 authorization eligibility: `false`
- Defect corrected in R4: the production consumer now reads
  `model.model_name` and `model.model_snapshot` and fail-closes when the
  nested model object is missing.

## Historical Successful Qualification (Task 098B-R2)

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

## Final Technical Verdict (Historical Task 098B-R2)

`EXP024_098B_R2_MODEL_TOKENIZER_HOOK_QUALIFICATION_COMPLETE`

`EXP024_QUALIFICATION_STATUS = QUALIFICATION_PASSED`

`EXP024_QUALIFICATION_GATE = READY_FOR_SINGLE_USE_FORMAL_AUTHORIZATION`
