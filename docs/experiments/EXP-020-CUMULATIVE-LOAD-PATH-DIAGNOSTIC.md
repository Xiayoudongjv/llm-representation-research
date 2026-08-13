# EXP-020 Cumulative Load and CPU/GPU Path-Separation Diagnostic

## Scope and status separation

Task 083E is an engineering diagnostic at formal-data access level 0. It did not open formal FIT/EVAL data, execute a formal runner, create or consume an authorization, perform model inference, or generate a scientific result.

```text
PRIOR_EXP020A_ATTEMPT_STATUS = TECHNICALLY_INVALID
EXP020_SCIENTIFIC_RESULT_STATUS = UNOBSERVED
TASK_083E_OUTCOME_TYPE = ENGINEERING_DIAGNOSTIC_ONLY
```

The prior attempt remains a consumed, technically invalid model-loading crash. This task produced no scientific outcome.

## Entry and Task 083D normalization

Entry HEAD was `90a5bf12e020bc84f87496bc60c24e23e531fec5` on `main...origin/main`; only the permitted 083C runner and test files were tracked modifications, and nothing was staged. The consumed authorization, its single consumption record, and all 083B/083C report hashes matched their frozen values. There was no canonical result, staging result, second authorization, new consumption record, or formal retry.

Task 083D was normalized only at the status level:

- `STATIC_INTEGRITY_PASS_TARGETED_READ_PASS` became `TARGETED_TENSOR_BOUNDARY_READS_PASS` in both reports.
- JSON gained `task_083d_outcome_type: ENGINEERING_DIAGNOSTIC_ONLY`.
- The required Markdown clarification gained the mandated backticks around `TECHNICALLY_INVALID`.

No mapping, tensor identity, observation, count, interpretation, or other evidence changed.

| 083D report | Entry SHA-256 | Normalized SHA-256 |
| --- | --- | --- |
| Markdown | `937f7b6922cc78daf6aa57223b4fc5810b1b90d93d8fce392a2dbce95d358d4c` | `28e5dcb0a778ce9b01713f6bfb6bd16432580b4af8fd518424bd064ae44a4738` |
| JSON | `e185f8d824f2b586da8fb27e3b4a45a22c68be75aa35f067bb9de53a0c055390` | `49503c6076b18d8074639d5d5c206227e131089309499bf1c7c274792262f8dc` |

## Cumulative byte reconstruction

Using only the validated 083D identity mapping, Transformers natural key ordering, the safetensors index, and safetensors headers, the 398 progress units total 8,044,936,192 raw tensor bytes (7.493 GiB). No tensor values were read in this reconstruction.

| Position | Tensor | Shard | Tensor bytes | Cumulative bytes | Tensor-count fraction | Weight-byte fraction |
| ---: | --- | --- | ---: | ---: | ---: | ---: |
| 156 | `model.layers.14.input_layernorm.weight` | 1 | 5,120 | 3,603,980,288 | 39.196% | 44.798% |
| 157 | `model.layers.14.mlp.down_proj.weight` | 1 | 49,807,360 | 3,653,787,648 | 39.447% | 45.417% |
| 158 | `model.layers.14.mlp.gate_proj.weight` | 1 | 49,807,360 | 3,703,595,008 | 39.698% | 46.036% |
| 159 | `model.layers.14.mlp.up_proj.weight` | 1 | 49,807,360 | 3,753,402,368 | 39.950% | 46.655% |
| 166 | `model.layers.14.self_attn.v_proj.weight` | 1 | 5,242,880 | 3,805,836,800 | 41.709% | 47.307% |
| 167 | `model.layers.15.input_layernorm.weight` | 2 | 5,120 | 3,805,841,920 | 41.960% | 47.307% |
| 398 | `model.norm.weight` | 3 | 5,120 | 8,044,936,192 | 100.000% | 100.000% |

Positions 157–158 are at about 40% of progress-unit count, but 45–46% of raw weight bytes. Each is 49,807,360 bytes (0.619% of total raw bytes), so neither is unusually large relative to this model. Both are in shard 1, do not begin or end a progress shard boundary, and are 1,918,986,240 and 1,869,178,880 bytes respectively from their closest physical shard boundary. The repeated incident location is therefore associated with count progress, not a shard boundary or a uniquely large tensor; this association is not causal evidence.

## Clean-state and resource baseline

The system boot time was 2026-08-13 05:13:52 UTC, earlier than the Task 083D report completion time. Therefore `CLEAN_RESTART_NOT_CONFIRMED` was recorded. No process was terminated.

At the immediately preceding baseline:

- Physical RAM: 15.73 GiB total; 3.90 GiB free.
- Committed memory: 21.72 GiB of 30.23 GiB; 8.51 GiB available commit.
- Pagefile: 14,848 MiB allocated; 1,583 MiB in use; 2,562 MiB peak.
- Required CPU gate: `W + 2 GiB` = 10,192,419,840 bytes (9.493 GiB).
- GPU: NVIDIA GeForce RTX 5060 Laptop GPU, driver 610.62, 8,151 MiB total and 7,899 MiB free dedicated memory.
- Runtime: Python 3.11.9; PyTorch 2.12.1+cu130; Transformers 5.14.1; Accelerate 1.14.0; safetensors 0.8.0; CUDA runtime 13.0.
- Material background use included ChatGPT Classic (about 1.99 GiB working set) and several VS Code processes. They were observed only.

Both required CPU resource conditions failed: free physical RAM (3.90 GiB) and available commit (8.51 GiB) were each below 9.493 GiB.

## Load-path result

The CPU resource gate failed before any complete-load child process could be safely launched. Consequently:

- CPU-only complete model-load launches: 0.
- GPU neutral-load launches: 0.
- No monitor, stdout/stderr capture, telemetry, model process, forward pass, or GPU dispatch was created.
- The GPU prelaunch gate was not evaluated, because CPU-only complete loading did not pass.

The post-boot Windows event scan showed the already documented Python / `torch_cpu.dll` access violation (`0xc0000005`, report ID `a676528a-5782-4c06-ab51-47df4b270caf`). No new diagnostic launch occurred, and no Display/nvlddmkm or WHEA event was observed for this task.

## Interpretation

Supported eliminations remain limited to Task 083D: malformed safetensors structure/index mapping and deterministic individual CPU reads for six local tensors were not observed. This task cannot distinguish cumulative CPU materialization from CPU-to-GPU dispatch because its mandatory host-resource gate blocked complete loading. Remaining candidates include insufficient current host-memory/commit headroom, background-process state, cumulative native materialization behavior, virtual-memory/pagefile state, and other intermittent native interactions. Root cause is not proven.

Final diagnostic status: `CUMULATIVE_LOAD_DIAGNOSTIC_BLOCKED_CPU_RESOURCE_GATE`.

```text
EXP020_FORMAL_RUN_AUTHORIZED = false
PRIOR_AUTHORIZATION_CONSUMED = true
PRIOR_EXP020A_ATTEMPT_STATUS = TECHNICALLY_INVALID
EXP020_SCIENTIFIC_RESULT_STATUS = UNOBSERVED
TASK_083E_OUTCOME_TYPE = ENGINEERING_DIAGNOSTIC_ONLY
CPU_COMPLETE_MODEL_LOAD_COUNT = 0
GPU_NEUTRAL_MODEL_LOAD_COUNT = 0
FORMAL_FIT_EVAL_INFERENCE_PERFORMED = false
FORMAL_SCIENTIFIC_RESULTS_CREATED = false
ROOT_CAUSE_PROVEN = false
RETRY_PERFORMED = false
COMMIT_PERFORMED = false
PUSH_PERFORMED = false
```
