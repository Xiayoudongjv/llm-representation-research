# EXP-020 Native Model-Load Stability Qualification

## Scope and Exclusions

Task 083B is an engineering-only qualification after the consumed, technically invalid Task 083A formal attempt. It did not access formal prompt/source data, execute formal mode, run FIT/EVAL inference, create scientific results, alter the consumed authorization, or modify runner code, tests, authority files, environment versions, or model files.

## Preserved Incident Identity

- Incident authorization SHA-256: `070d2e2ccaf8857c2a3d439ea6c87420784f6029c9340ccf2d042399f7ecfd01`
- Consumption-record SHA-256: `0a39e6a214512ffac928620768100ac9a5c20e1a1fbd8c72c44f76413f6864cc`
- Consumed run-attempt ID: `0f2cff46-61c5-499f-af3c-8aef0701ee96`
- Preserved historical status: `EXP020A_FORMAL_RUN_TECHNICALLY_INVALID_AUTHORIZATION_CONSUMED_NATIVE_CRASH`

The authorization and consumption record hashes matched. The canonical EXP-020A result and formal staging files remain absent.

## Loader-Path Comparison

Formal and neutral paths both use the same local canonical snapshot, `local_files_only=True`, `AutoTokenizer`, `AutoModelForCausalLM`, BF16, `device_map={"": 0}`, no quantization, no offload, no trust-remote-code setting, and call `eval()` before their respective forward paths.

The neutral path explicitly passes `low_cpu_mem_usage=True` to `from_pretrained`; the formal path calls the shared loader without that explicit argument. This is potentially resource-affecting before formal data access. Therefore the paths are not materially identical for a load-stability qualification, and the hard stop applies. No neutral cycles were run.

## Model-Snapshot Integrity

The canonical snapshot is `D:\Qwen3-4B-transfer`. Its frozen `config.json` SHA-256 matched: `8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a`.

Read-only metadata matched the frozen identity: Qwen3 / `Qwen3ForCausalLM`, 36 transformer blocks, hidden size 2560, vocabulary 151936, and BF16 expectation. The snapshot contains 13 files totaling 8,060,926,626 bytes, three readable safetensors shards, a safetensors index, and tokenizer files. No symlink resolution issue was observed. Existing qualification evidence does not freeze authoritative per-weight SHA-256 values, so none were invented or recomputed as a new baseline.

## System and Crash Evidence

- Python: `D:\python311\python.exe`, 3.11.9
- PyTorch / CUDA metadata: 2.12.1+cu130 / 13.0
- Transformers: 5.14.1; safetensors: 0.8.0; Accelerate: 1.14.0
- GPU: NVIDIA GeForce RTX 5060 Laptop GPU; driver 610.62; 8151 MiB total and 0 MiB currently used.
- Physical memory: 16,890,322,944 bytes total; 6,284,267,520 bytes free.
- Virtual memory: 32,459,579,392 bytes total; 11,047,931,904 bytes free.
- Pagefile: 14,848 MiB allocated; 2,424 MiB current use; 2,562 MiB peak use.
- D: free space: 190,675,660,800 bytes.

The narrow 23:26--23:30 local Windows Application/System log queries found no matching Application Error, Windows Error Reporting, Display, nvlddmkm, WHEA, or resource-exhaustion event. This is absence of event evidence, not proof that no native fault occurred. The remaining Python processes are pre-existing Jupyter support/kernel processes and were not terminated.

## Cycle Results and Resource Pattern

No neutral cycle was launched. The completed-cycle count, normal-exit count, and reproduced-native-crash count are all zero. This follows the required hard stop; a neutral process with explicit `low_cpu_mem_usage=True` would not qualify the formal loader path that omitted it.

## Unresolved Root-Cause Candidates

1. Resource-affecting divergence in `low_cpu_mem_usage` between neutral and formal loading paths.
2. Native failure during safetensors/model-load processing, as Task 083A ended during weight-loading progress.
3. Load-time host-memory/pagefile pressure remains a possible but unproven contributor.
4. No Windows fault-module/event evidence was available in the queried window.

## Qualification Decision

`NATIVE_LOAD_QUALIFICATION_BLOCKED_LOADER_PATH_DIVERGENCE`

This engineering blocker does not alter the Task 083A historical technical-invalid status, does not authorize a new formal authorization, and adds no scientific evidence.
