# EXP-020 Qwen3-4B Model Access Transfer Instructions

## Current Gate

The exact preregistered model is `Qwen/Qwen3-4B`. On this machine,
`hardware_feasibility = UNTESTED` because `model_access_status = BLOCKED`
before model configuration loading. This is a cache/network availability
problem, not an OOM or runtime finding. Do not substitute Qwen3.5 or another
4B checkpoint.

## Acquire the Exact Snapshot on a Networked Machine

Use a temporary external-cache root on a drive with sufficient space. Do not
use a project directory. First obtain metadata and pin the returned commit SHA;
then download that exact revision into the Hugging Face cache.

```python
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

cache_root = Path(r"E:\transfer_cache\huggingface")
info = HfApi().model_info("Qwen/Qwen3-4B")
print("resolved_revision:", info.sha)
snapshot = snapshot_download(
    repo_id="Qwen/Qwen3-4B",
    revision=info.sha,
    cache_dir=cache_root,
)
print("snapshot:", snapshot)
```

Record `info.sha` and the returned snapshot path. The snapshot directory name
must equal that commit SHA. Do not replace the revision with a branch name or
download a second model copy.

## Transfer Without Altering Snapshot Identity

Copy the complete cache-repository tree, including `blobs`, `refs`, and
`snapshots`, from:

```text
<cache_root>\hub\models--Qwen--Qwen3-4B
```

to this exact target:

```text
D:\AI_Cache\huggingface\hub\models--Qwen--Qwen3-4B
```

Preserve directory layout and symbolic-link relationships. An archive created
from the complete `models--Qwen--Qwen3-4B` tree is preferable to copying only
the snapshot directory. Do not place the model in the repository or on C:.

## Local Integrity Check on This Machine

After transfer, set the existing cache environment values and perform only a
local configuration/tokenizer check:

```python
from transformers import AutoConfig, AutoTokenizer

model_id = "Qwen/Qwen3-4B"
cache_dir = r"D:\AI_Cache\huggingface"
config = AutoConfig.from_pretrained(model_id, cache_dir=cache_dir, local_files_only=True)
tokenizer = AutoTokenizer.from_pretrained(model_id, cache_dir=cache_dir, local_files_only=True)
print(config._commit_hash, config.model_type, tokenizer.__class__.__name__)
```

Confirm that the snapshot includes `config.json`, tokenizer files, and all
weight shards before resuming hardware qualification. This check must not load
model weights, run prompts, calculate representation metrics, steer, or run
behavioral evaluation.

## Next Gate

Only after the local-only configuration and tokenizer checks pass is the state
`READY_TO_RESUME_HARDWARE_QUALIFICATION`. Resume the separately frozen neutral
hardware-qualification script; do not resume EXP-020 scientific execution.
