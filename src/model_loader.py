"""Utilities for loading causal language models for representation experiments."""

from __future__ import annotations

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def get_torch_dtype(dtype: str) -> torch.dtype:
    supported = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}
    try:
        return supported[dtype.lower()]
    except KeyError as exc:
        raise ValueError(f"Unsupported dtype {dtype!r}. Choose from: {', '.join(supported)}.") from exc


def check_cuda_or_raise() -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for this experiment, but torch.cuda.is_available() is False.")


def load_tokenizer(model_name: str):
    return AutoTokenizer.from_pretrained(model_name)


def load_causal_lm(model_name: str, dtype: str = "float16", device_map: str = "auto"):
    return AutoModelForCausalLM.from_pretrained(
        model_name, dtype=get_torch_dtype(dtype), device_map=device_map
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
