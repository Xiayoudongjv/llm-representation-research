# EXP-020 Safetensors and Tensor-Boundary Diagnostic

## Scope and boundary

This diagnostic localizes the native loading incident without a complete model load. It did not access formal EXP-020 data, run either EXP-020 runner, create an authorization or consumption record, perform a forward pass, use GPU tensors, or create a scientific result.

`TECHNICALLY_INVALID` refers only to the consumed prior EXP-020A formal attempt, which crashed during model loading. No formal FIT/EVAL inference or scientific observation was produced. Task 083D is diagnostic-only and produces no scientific outcome.

## Entry integrity

- Reviewed commit: `90a5bf12e020bc84f87496bc60c24e23e531fec5` on `main...origin/main`.
- The only tracked modifications at entry were the permitted 083C files: `experiments/exp020/run_exp020a.py` (`7958410af11ecf45b7520c568fe3f4af805bdc506acd5d7812d2bae4f211e564`) and `tests/test_exp020_runner.py` (`3b712a0dbdb804f69e6c6d3dee3e82a4560254f860a4d350fbfefc66b87afc98`).
- The runner retains explicit `low_cpu_mem_usage=True` for the formal loader.
- The prior authorization and its single consumption record matched their frozen SHA-256 values: `070d2e2ccaf8857c2a3d439ea6c87420784f6029c9340ccf2d042399f7ecfd01` and `0a39e6a214512ffac928620768100ac9a5c20e1a1fbd8c72c44f76413f6864cc`.
- The 083B and 083C report pairs matched their required hashes. No canonical result, staging result, new consumption record, or staged file existed at entry.

## Snapshot and structural check

The inspected local snapshot is `D:\Qwen3-4B-transfer`, revision `1cfa9a7208912126459214e8b04321603b3df60c`. Its `config.json` SHA-256 is `8ba006f74fecfaaeb392872a60f4a480e7ec9860153d2e1b769ec81f9a147f8a`; the safetensors index SHA-256 is `6dc0981b8829fead746441f68f38f24c5ca4a3a66351f652c26c6df0efc43ab2`. The config identifies `Qwen3ForCausalLM` / `qwen3`, BF16, 36 blocks, and hidden size 2560.

A temporary standard-library-only Python process parsed every safetensors header before any tensor materialization. It verified all 398 index entries against the three shard headers, offsets, shapes, dtype byte sizes, non-overlap, bounds, and declared byte totals.

| Shard | Tensors | File bytes | SHA-256 |
| --- | ---: | ---: | --- |
| `model-00001-of-00003.safetensors` | 174 | 3,957,900,840 | `328a91d3122359d5547f9d79521205bc0a46e1f79a792dfe650e99fc2d651223` |
| `model-00002-of-00003.safetensors` | 219 | 3,987,450,520 | `6cd087b316306a68c562436b5492edbcf6e16c6dba3a1308279caa5a58e21ca5` |
| `model-00003-of-00003.safetensors` | 5 | 99,630,640 | `e4bf436957184f4eeb86a80e9db394503f1f56446b2e6b7edeac5b81470f4ca1` |

All three data regions were fully covered by declared non-overlapping tensor ranges. The index metadata total was 8,044,936,192 tensor bytes, equal to the shard-declared tensor total. The direct snapshot has no symlink resolution issue.

The Hugging Face cache snapshot has an identical index and third-shard content hash. The cache contains zero-byte incomplete markers for the first two direct-shard hash names, not complete authoritative blob files. Consequently, all three direct-snapshot hashes are recorded as descriptive integrity evidence; this diagnostic does not invent a complete historical authoritative blob-hash baseline.

## Progress mapping proof

Installed Transformers source (`core_model_loading.py`) defines the `Loading weights` bar as an iteration over `param_name_to_load`, built after a natural sort of checkpoint state-dict keys. A separate CPU/meta-only subprocess built `Qwen3ForCausalLM` under `accelerate.init_empty_weights()` and applied the same key-renaming logic without opening any shard.

- 398 checkpoint keys produced exactly 398 progress entries.
- Every checkpoint key was included by an identity mapping.
- No source conversion pattern was used, and no duplicate target key was produced.
- `lm_head.weight` is the sole model-state key absent from the checkpoint because it is shared/tied; it does not create a progress item.

Therefore the positions are unique. The incident window maps to:

| Position | Tensor | Shard |
| ---: | --- | --- |
| 156 | `model.layers.14.input_layernorm.weight` | 1 |
| 157 | `model.layers.14.mlp.down_proj.weight` | 1 |
| 158 | `model.layers.14.mlp.gate_proj.weight` | 1 |
| 159 | `model.layers.14.mlp.up_proj.weight` | 1 |

The nearby shard boundary is between positions 166 (`model.layers.14.self_attn.v_proj.weight`, shard 1) and 167 (`model.layers.15.input_layernorm.weight`, shard 2).

## Bounded CPU-only reads

Before Phase 2, available physical memory was 4.625 GiB. The largest selected tensor was 49,807,360 bytes; the prescribed threshold was 1.093 GiB (`2 × tensor bytes + 1 GiB`), so the bounded-read gate passed.

Using PyTorch 2.12.1+cu130 and safetensors 0.8.0, six fresh child processes each executed exactly one `safe_open(..., framework="pt", device="cpu").get_tensor(name)` call. All exited zero and reported CPU BF16 tensors with the header-declared shape and byte count. The selected tensors were positions 156–159 and the boundary positions 166–167. No tensor values were printed or persisted, and no GPU was made visible to these processes.

## Result and limitation

Final diagnostic status: `TARGETED_TENSOR_BOUNDARY_READS_PASS`.

The evidence rules out malformed safetensors headers/index mappings and a deterministic failure when individually materializing the six bounded CPU tensors around the observed progress window and one shard boundary. It does not identify a single root cause for the prior `torch_cpu.dll` access violation: the failed full loader involved substantially different lifetime, asynchronous materialization, and device-placement behavior. No claim is made that the full load is now safe, and no formal rerun is authorized.

```text
EXP020_FORMAL_RUN_AUTHORIZED = false
EXP020_SCIENTIFIC_STATUS = NOT_STARTED
FORMAL_FIT_EVAL_INFERENCE_PERFORMED = false
FORMAL_SCIENTIFIC_RESULTS_CREATED = false
EVIDENCE_CHANGED = false
SCIENTIFIC_CONCLUSION_CHANGED = false
```
