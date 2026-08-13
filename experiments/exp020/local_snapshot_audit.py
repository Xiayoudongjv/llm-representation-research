"""Audit the local Qwen3-4B snapshot without network access or model loading."""

from __future__ import annotations

import hashlib
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from transformers import AutoConfig, AutoTokenizer


MODEL_ID = "Qwen/Qwen3-4B"
CANDIDATE = Path(r"D:\Qwen3-4B-transfer")
HF_HUB = Path(r"D:\AI_Cache\huggingface\hub")
HF_TRANSFORMERS = Path(r"D:\AI_Cache\huggingface\transformers")
RESULT = Path(__file__).resolve().parent / "results" / "qwen3_4b_local_integrity_and_duplicate_audit.json"
NEUTRAL_TEXT = "The river passes quietly through the valley."
WEIGHT_SUFFIXES = {".safetensors", ".bin", ".pt", ".pth", ".npy", ".npz", ".gguf"}
LARGE_FILE_BYTES = 1_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path):
    if root.exists():
        yield from (path for path in root.rglob("*") if path.is_file())


def file_record(path: Path, digest: str | None = None) -> dict[str, object]:
    stat = path.stat()
    return {
        "absolute_path": str(path),
        "filename": path.name,
        "size_bytes": stat.st_size,
        "extension": path.suffix.lower(),
        "sha256": digest,
        "st_nlink": stat.st_nlink,
        "is_symlink": path.is_symlink(),
    }


def metadata_revision() -> str | None:
    metadata = CANDIDATE / ".cache" / "huggingface" / "download" / "config.json.metadata"
    if not metadata.exists():
        return None
    lines = metadata.read_text(encoding="utf-8").splitlines()
    return lines[0] if lines else None


def main() -> None:
    if not CANDIDATE.is_dir():
        raise FileNotFoundError(f"Canonical candidate path is absent: {CANDIDATE}")

    candidate_files = list(iter_files(CANDIDATE))
    cache_files = list(iter_files(HF_HUB)) + list(iter_files(HF_TRANSFORMERS))
    weight_paths = [
        path
        for path in candidate_files + cache_files
        if path.suffix.lower() in WEIGHT_SUFFIXES and path.stat().st_size >= LARGE_FILE_BYTES
    ]
    records = [file_record(path, sha256(path)) for path in weight_paths]
    by_hash: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        by_hash[str(record["sha256"])].append(record)
    exact_duplicate_groups = [group for group in by_hash.values() if len(group) > 1]
    exact_duplicate_bytes = sum(int(group[0]["size_bytes"]) * (len(group) - 1) for group in exact_duplicate_groups)

    by_name: dict[str, list[dict[str, object]]] = defaultdict(list)
    for record in records:
        by_name[str(record["filename"])].append(record)
    same_name_different_hash = [
        group for group in by_name.values() if len(group) > 1 and len({item["sha256"] for item in group}) > 1
    ]
    partials = [
        file_record(path)
        for path in candidate_files + cache_files
        if path.name.endswith((".incomplete", ".part"))
    ]
    candidate_partial_bytes = sum(int(record["size_bytes"]) for record in partials if str(record["absolute_path"]).startswith(str(CANDIDATE)))
    total_partial_bytes = sum(int(record["size_bytes"]) for record in partials)
    locks = [file_record(path) for path in candidate_files + cache_files if path.name.endswith(".lock")]
    metadata_only_cache_files = [
        file_record(path)
        for path in candidate_files
        if ".cache" in path.parts and path.name.endswith(".metadata")
    ]

    required = ["config.json", "tokenizer.json", "tokenizer_config.json", "model.safetensors.index.json"]
    required_present = {name: (CANDIDATE / name).is_file() for name in required}
    index = json.loads((CANDIDATE / "model.safetensors.index.json").read_text(encoding="utf-8"))
    referenced_shards = sorted(set(index["weight_map"].values()))
    shard_checks = [
        {"filename": name, "exists": (CANDIDATE / name).is_file(), "size_bytes": (CANDIDATE / name).stat().st_size if (CANDIDATE / name).is_file() else None}
        for name in referenced_shards
    ]
    zero_byte_files = [str(path) for path in candidate_files if path.stat().st_size == 0 and not path.name.endswith((".incomplete", ".part", ".lock"))]

    config = AutoConfig.from_pretrained(CANDIDATE, local_files_only=True)
    tokenizer = AutoTokenizer.from_pretrained(CANDIDATE, local_files_only=True)
    encoded = tokenizer(NEUTRAL_TEXT, return_tensors="pt")
    decoded = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True)
    identity_ok = config.model_type == "qwen3" and "Qwen3ForCausalLM" in list(config.architectures or []) and config.hidden_size == 2560 and config.num_hidden_layers == 36
    integrity_ok = all(required_present.values()) and all(item["exists"] and item["size_bytes"] for item in shard_checks) and not zero_byte_files

    result = {
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "requested_model_id": MODEL_ID,
        "canonical_model_path": str(CANDIDATE),
        "local_files_only": True,
        "source_revision_from_download_metadata": metadata_revision(),
        "candidate_model_storage_bytes": sum(path.stat().st_size for path in candidate_files),
        "candidate_weight_storage_bytes": sum(path.stat().st_size for path in candidate_files if path.suffix.lower() in WEIGHT_SUFFIXES),
        "apparent_model_storage_bytes": sum(int(record["size_bytes"]) for record in records),
        "large_model_files": records,
        "exact_duplicate_large_file_groups": exact_duplicate_groups,
        "exact_duplicate_large_file_count": sum(len(group) - 1 for group in exact_duplicate_groups),
        "exact_duplicate_bytes": exact_duplicate_bytes,
        "candidate_partial_download_residue_bytes": candidate_partial_bytes,
        "total_partial_download_residue_bytes": total_partial_bytes,
        "potential_recoverable_storage_bytes": exact_duplicate_bytes + total_partial_bytes,
        "same_filename_different_hash_groups": same_name_different_hash,
        "incomplete_or_partial_files": partials,
        "lock_files": locks,
        "metadata_only_cache_files": metadata_only_cache_files,
        "duplicate_cleanup_status": "SAFE_TO_KEEP_ALL",
        "potential_duplicates_for_later_cleanup": exact_duplicate_groups,
        "required_file_presence": required_present,
        "generation_config_present": (CANDIDATE / "generation_config.json").is_file(),
        "referenced_weight_shards": shard_checks,
        "zero_byte_non_partial_files": zero_byte_files,
        "identity": {
            "identity_consistent_with_qwen3_4b": identity_ok,
            "model_type": config.model_type,
            "architectures": list(config.architectures or []),
            "hidden_size": config.hidden_size,
            "num_hidden_layers": config.num_hidden_layers,
            "vocab_size": config.vocab_size,
            "torch_dtype": str(config.torch_dtype),
            "tokenizer_class": tokenizer.__class__.__name__,
            "tokenizer_local_only_success": True,
            "neutral_token_count": int(encoded["input_ids"].shape[-1]),
            "neutral_decoded_text": decoded,
        },
        "integrity_status": "PASS" if integrity_ok and identity_ok else "FAIL",
        "exp020_scientific_results_created": False,
        "exp017_accessed": False,
        "exp019_accessed": False,
    }
    RESULT.parent.mkdir(parents=True, exist_ok=True)
    RESULT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("LOCAL_SNAPSHOT_AUDIT_" + result["integrity_status"])
    print("large_model_files:", len(records))
    print("exact_duplicate_bytes:", exact_duplicate_bytes)
    print("canonical_model_path:", CANDIDATE)


if __name__ == "__main__":
    main()
