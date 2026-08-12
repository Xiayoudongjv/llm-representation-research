"""Utilities for loading causal language models for representation experiments."""

from __future__ import annotations

from pathlib import Path

import torch
from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer


def get_torch_dtype(dtype: str) -> torch.dtype:
    supported = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}
    try:
        return supported[dtype.lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported dtype {dtype!r}. Choose from: {', '.join(supported)}.") from exc


def check_cuda_or_raise() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this experiment, but torch.cuda.is_available() is False.")


def _load_kwargs(cache_dir: str | Path | None, local_files_only: bool) -> dict:
    """Build optional Hugging Face loading arguments without changing defaults."""
    kwargs = {}
    if cache_dir is not None:
        kwargs["cache_dir"] = str(cache_dir)
    if local_files_only:
        kwargs["local_files_only"] = True
    return kwargs


def load_model_config(model_name: str, cache_dir: str | Path | None = None, local_files_only: bool = False):
    """Load a model configuration with optional explicit cache and offline mode."""
    return AutoConfig.from_pretrained(model_name, **_load_kwargs(cache_dir, local_files_only))


def load_tokenizer(model_name: str, cache_dir: str | Path | None = None, local_files_only: bool = False):
    """Load a tokenizer while preserving the previous default resolution behavior."""
    return AutoTokenizer.from_pretrained(model_name, **_load_kwargs(cache_dir, local_files_only))


def load_causal_lm(
    model_name: str,
    dtype: str = "float16",
    device_map: str = "auto",
    cache_dir: str | Path | None = None,
    local_files_only: bool = False,
):
    """Load a causal LM with optional explicit cache and fail-closed offline mode."""
    return AutoModelForCausalLM.from_pretrained(
        model_name, dtype=get_torch_dtype(dtype), device_map=device_map,
        **_load_kwargs(cache_dir, local_files_only),
    )


def print_model_info(model) -> None:
    config = getattr(model, "config", None)
    print(f"model_class: {model.__class__.__name__}")
    print(f"model_type: {getattr(config, 'model_type', 'unknown')}")
    print(f"num_hidden_layers: {getattr(config, 'num_hidden_layers', 'unknown')}")
    print(f"hidden_size: {getattr(config, 'hidden_size', 'unknown')}")
    try:
        device = model.device
    except (AttributeError, RuntimeError):
        device = "managed by device_map"
    print(f"model_device: {device}")
