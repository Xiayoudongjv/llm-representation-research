# EXP-020 Load-Path Correction Qualification

## Context and Scope

Task 083C follows Task 083A's consumed, technically invalid formal attempt and Task 083B's loader-path divergence finding. It made one engineering-only loader correction, used no formal prompt/source data, did not execute formal mode, did not create an authorization or scientific result, and did not alter the consumed incident artifacts.

## Exact Correction

The formal Qwen3-4B construction now directly calls `AutoModelForCausalLM.from_pretrained` with the already used canonical path, `local_files_only=True`, `dtype=torch.bfloat16`, `device_map={"": 0}`, and explicit `low_cpu_mem_usage=True`.

This replaces the formal use of a shared wrapper that did not expose that explicit argument. It does not alter model identity, tokenizer behavior, extraction, formal-data ordering, representations, intervention arithmetic, controls, probe, statistics, bootstrap, gate, authorization lifecycle, result schema, or publication behavior.

## Loader-Path Equivalence

After correction, formal and neutral paths have equivalent resource-affecting model-loading semantics: identical local snapshot, local-only behavior, `AutoModelForCausalLM`, BF16, `device_map={"": 0}`, explicit `low_cpu_mem_usage=True`, no quantization, no offload, no alternate attention implementation, no trust-remote-code setting, and `eval()` before forward computation. Both use `AutoTokenizer` with local-only behavior; the neutral path's additional `AutoConfig` metadata read is operationally irrelevant to weight loading/device placement.

## Regression and Semantic Audit

- Preregistration validator: pass.
- Implementation-specification validator: pass.
- Runner AST validation: pass.
- Targeted synthetic tests: 94 passed.

New mock tests capture formal and neutral loader kwargs without loading the real model or accessing formal data. The code diff contains only the explicit formal loader alignment and these tests. Protected scientific computation, result schema, authorization lifecycle, and atomic publication functions were unchanged.

## System State Before Cycle

- Qwen3-4B frozen config hash matched the local snapshot.
- CUDA/BF16 static validation passed.
- GPU: RTX 5060 Laptop GPU, driver 610.62, 8151 MiB total, 0 MiB used before the cycle.
- Before cycle: 5,021,310,976 free physical bytes; 10,375,008,256 free virtual bytes; 0 MiB GPU memory used.

## Neutral Stability Cycles

Only cycle 1 ran. The temporary diagnostic invoked the committed neutral loader/forward function directly, bypassing solely the preflight authorization-artifact absence check because the preserved consumed authorization makes that unrelated check necessarily fail. Loader and forward semantics were otherwise unchanged, and only the frozen neutral input was available to the process.

| Cycle | Start UTC | End UTC | Exit | Model load | Neutral forward | Hidden-state checks | Shutdown |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-08-13T15:51:39.2473589Z | 2026-08-13T15:52:18.2253804Z | -1073741819 | incomplete | not reached | not reached | native crash |

The last safe load-progress line reached 158 of 398 weight-loading units. Standard output was empty; no hidden states or model outputs were persisted. The GPU returned to 0 MiB used after process exit. Post-cycle free physical and virtual memory were 7,877,619,712 and 21,868,830,720 bytes respectively.

## Native Crash Evidence

Windows Application Error event 1000 at local 23:51:55 identified `python.exe` faulting in `torch_cpu.dll`, exception `0xc0000005`, offset `0x0000000008e8b949`, and process ID `0x8668` (34408). Windows Error Reporting event 1001 recorded the same APPCRASH report ID `a676528a-5782-4c06-ab51-47df4b270caf`. No matching System Display, nvlddmkm, WHEA, or resource-exhaustion event was found in the cycle window.

The correction did not prevent a native load-time crash. It does not prove that `low_cpu_mem_usage` caused the earlier crash, nor does it isolate a root cause. Remaining candidates include a native `torch_cpu.dll` failure during safetensors/model loading and unobserved host-resource interactions.

## Qualification Decision

`CORRECTED_NATIVE_LOAD_STABILITY_NOT_QUALIFIED`

The Task 083A formal attempt remains technically invalid with its authorization consumed. This result adds no scientific evidence and does not authorize a new formal authorization or another formal run.
