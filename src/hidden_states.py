"""Forward-pass helpers for extracting model hidden states."""

from __future__ import annotations

import torch


def tokenize_prompt(tokenizer, prompt: str, device):
    inputs = tokenizer(prompt, return_tensors="pt")
    return {name: value.to(device) for name, value in inputs.items()}


def run_forward_with_hidden_states(model, tokenizer, prompt: str):
    device = next(model.parameters()).device
    inputs = tokenize_prompt(tokenizer, prompt, device)
    with torch.no_grad():
        outputs = model(**inputs, output_hidden_states=True, return_dict=True)
    return outputs.hidden_states


def summarize_hidden_states(hidden_states) -> None:
    print(f"hidden_state_count: {len(hidden_states)}")
    for index, tensor in enumerate(hidden_states):
        print(f"layer={index} shape={tuple(tensor.shape)} dtype={tensor.dtype} device={tensor.device}")


def hidden_states_metadata(hidden_states) -> list[dict]:
    return [
        {"layer": index, "shape": list(tensor.shape), "dtype": str(tensor.dtype), "device": str(tensor.device)}
        for index, tensor in enumerate(hidden_states)
    ]
