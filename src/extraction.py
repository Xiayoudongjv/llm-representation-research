"""Shared helpers for extracting last-token hidden-state representations."""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import torch


def validate_layer_index(layer: int, num_layers: int) -> int:
    """Normalize a Python-style layer index and reject out-of-range values."""
    if num_layers <= 0:
        raise IndexError(f"Cannot index a hidden-state sequence with {num_layers} layers.")
    normalized = num_layers + layer if layer < 0 else layer
    if not 0 <= normalized < num_layers:
        raise IndexError(f"Layer {layer} is out of range for {num_layers} layers.")
    return normalized


def move_tokenized_inputs_to_device(inputs: Mapping, device: torch.device | str) -> dict:
    """Move tensor values in tokenizer outputs to device and preserve other values."""
    return {
        name: value.to(device) if isinstance(value, torch.Tensor) else value
        for name, value in inputs.items()
    }


def get_model_input_device(model) -> torch.device:
    """Return the first parameter device, with CPU fallback for parameterless models.

    Models loaded with ``device_map="auto"`` or model parallelism may require
    more careful input-device handling in a future implementation.
    """
    try:
        return next(model.parameters()).device
    except StopIteration:
        return torch.device("cpu")


def extract_last_token_hidden_state(hidden_states, layer: int) -> torch.Tensor:
    """Return batch-zero's last-token state from a validated hidden-state layer."""
    layer_index = validate_layer_index(layer, len(hidden_states))
    selected = hidden_states[layer_index]
    if selected.ndim != 3:
        raise ValueError("Hidden-state tensors must have shape [batch, seq_len, hidden_size].")
    if selected.shape[0] < 1:
        raise ValueError("Hidden-state batch size must be at least 1.")
    if selected.shape[1] < 1:
        raise ValueError("Hidden-state sequence length must be at least 1.")
    return selected[0, -1, :]


def tensor_to_numpy_float32(tensor: torch.Tensor) -> np.ndarray:
    """Detach a tensor, move it to CPU, convert to float32, and return NumPy data."""
    return tensor.detach().to(device="cpu", dtype=torch.float32).numpy()


def extract_last_token_representation(model, tokenizer, prompt: str, layer: int) -> np.ndarray:
    """Run a no-grad forward pass and return one last-token float32 representation."""
    device = get_model_input_device(model)
    tokenized = tokenizer(prompt, return_tensors="pt")
    inputs = move_tokenized_inputs_to_device(tokenized, device)
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, return_dict=True)
    hidden_state = extract_last_token_hidden_state(outputs.hidden_states, layer)
    return tensor_to_numpy_float32(hidden_state)
