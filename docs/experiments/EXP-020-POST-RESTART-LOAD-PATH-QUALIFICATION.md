# EXP-020 Post-Restart Load-Path Qualification

## Final status

`POST_RESTART_CPU_RESOURCE_GATE_FAILED_LOCAL_HARDWARE_NOT_QUALIFIED`

Task 083G is an engineering qualification only. It did not access formal FIT/EVAL data, start the formal runner, create or consume an authorization, load a model, run a forward pass, or produce a scientific result.

```text
PRIOR_EXP020A_ATTEMPT_STATUS = TECHNICALLY_INVALID
EXP020_SCIENTIFIC_RESULT_STATUS = UNOBSERVED
TASK_083G_OUTCOME_TYPE = ENGINEERING_QUALIFICATION_ONLY
```

## Entry and restart evidence

- HEAD: `90a5bf12e020bc84f87496bc60c24e23e531fec5`; branch: `main...origin/main`; staging area: empty.
- The only tracked modifications were the preserved 083C files `experiments/exp020/run_exp020a.py` and `tests/test_exp020_runner.py`.
- Their SHA-256 values remained `7958410af11ecf45b7520c568fe3f4af805bdc506acd5d7812d2bae4f211e564` and `3b712a0dbdb804f69e6c6d3dee3e82a4560254f860a4d350fbfefc66b87afc98`.
- Windows boot time was 2026-08-13 17:04:17 UTC, after the 083F report time of 2026-08-13 17:00:33 UTC. The clean restart was independently confirmed.
- All observed Python processes began after this boot. No pre-restart Task 083A–083E Python/model process remained.
- The prior authorization and its sole consumption record, 083B/083C reports, normalized 083D reports, 083E reports, and 083F reports matched their required hashes. Task 083D retained `TARGETED_TENSOR_BOUNDARY_READS_PASS`.
- No canonical result, staging result, second authorization, or second consumption record exists.

## Validation

The prescribed non-model validation completed before resource gating:

- EXP-020 preregistration validator: pass.
- EXP-020 implementation-specification validator: pass.
- Runner AST syntax validation: pass.
- Targeted tests: 94 passed, 1 existing non-failing sklearn `FutureWarning` about the deprecated `penalty` parameter.

`PYTHONDONTWRITEBYTECODE=1` and pytest `-p no:cacheprovider` were used.

## Pre-CPU resource gate

The frozen raw model-weight size is 8,044,936,192 bytes. The threshold for both physical memory and available commit space is 10,192,419,840 bytes (9.493 GiB).

| Measurement | Value | Gate |
| --- | ---: | --- |
| Total physical memory | 16,890,322,944 bytes (15.73 GiB) | informational |
| Available physical memory | 4,782,518,272 bytes (4.45 GiB) | **fail** |
| Commit limit | 32,996,450,304 bytes (30.73 GiB) | informational |
| Current committed memory | 18,652,688,384 bytes (17.37 GiB) | informational |
| Available commit space | 14,343,761,920 bytes (13.36 GiB) | pass |
| Pagefile | 15,360 MiB allocated; 70 MiB used | informational |
| GPU | RTX 5060 Laptop, driver 610.62; 7,805 MiB free of 8,151 MiB | not reached |

Because physical-memory headroom failed, the required dual CPU gate failed. No waiting, process termination, pagefile modification, loader alteration, quantization, offloading, or retry was used to seek a pass.

## Load-path outcome

- CPU complete-load attempts: 0.
- GPU neutral cycles: 0.
- Native crash reproduced: no; no model child process was launched.
- GPU gate: not evaluated, because the CPU gate did not pass.
- Windows event evidence: no 083G child existed, therefore no task-generated native or GPU event window exists.
- Operational qualification: false. The local Qwen3-4B BF16 runtime is not qualified under the observed post-restart physical-memory envelope.

Another local complete-load attempt is not recommended until a separate decision evaluates greater physical/commit-memory hardware, an independently qualified runtime, or a separately reviewed implementation/environment change. This is a resource-gate observation, not proof of the cause of the earlier crash.

## Final filesystem state

Only this Markdown report and its ignored JSON companion were newly created. No formal data, scientific result, model cache, weight, tensor, authorization, consumption record, canonical result, or staging result was created. Nothing was staged, committed, or pushed.

```text
EXP020_FORMAL_RUN_AUTHORIZED = false
PRIOR_AUTHORIZATION_CONSUMED = true
PRIOR_EXP020A_ATTEMPT_STATUS = TECHNICALLY_INVALID
EXP020_SCIENTIFIC_RESULT_STATUS = UNOBSERVED
TASK_083G_OUTCOME_TYPE = ENGINEERING_QUALIFICATION_ONLY
CPU_COMPLETE_MODEL_LOAD_COUNT = 0
GPU_NEUTRAL_MODEL_CYCLE_COUNT = 0
GPU_NEUTRAL_MODEL_CYCLE_PASS_COUNT = 0
FORMAL_FIT_EVAL_INFERENCE_PERFORMED = false
FORMAL_SCIENTIFIC_RESULTS_CREATED = false
ROOT_CAUSE_PROVEN = false
RETRY_PERFORMED = false
COMMIT_PERFORMED = false
PUSH_PERFORMED = false
```
