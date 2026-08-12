"""Tiny technical check of the frozen EXP-017 Qwen generation-hook semantics.

This script is intentionally not a behavioral experiment.  It uses one short
synthetic prompt, a zero vector, and a deterministic synthetic diagnostic
vector.  It never writes model outputs, hidden states, or result files.
"""

from __future__ import annotations

import argparse
import gc
import sys
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import torch

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.extraction import get_model_input_device, move_tokenized_inputs_to_device
from src.model_loader import check_cuda_or_raise, load_causal_lm, load_tokenizer


MODEL_NAME = "Qwen/Qwen3-1.7B"
TARGET_LAYER = 16
PROMPT = "Answer with one word: Is water wet?"


@dataclass
class HookEvent:
    """One post-block hook observation, retaining scalar diagnostics only."""

    output_type: str
    hidden_state_location: str
    sequence_length: int
    modified_token_index: int
    activation_norm_before: float
    perturbation_norm: float
    activation_norm_after: float
    earlier_positions_unchanged: bool
    last_token_changed: bool
    device: str
    dtype: str
    explicit_delta_shape: tuple[int, int, int]


def _replace_tensor_at_path(value: Any, path: tuple[int, ...], tensor: torch.Tensor) -> Any:
    """Return ``value`` with the tensor at an index-only tuple/list path replaced."""
    if not path:
        return tensor
    index, *remaining = path
    if isinstance(value, tuple):
        items = list(value)
        items[index] = _replace_tensor_at_path(items[index], tuple(remaining), tensor)
        return tuple(items)
    if isinstance(value, list):
        items = list(value)
        items[index] = _replace_tensor_at_path(items[index], tuple(remaining), tensor)
        return items
    raise TypeError(f"Cannot replace tensor at {path!r} inside {type(value).__name__}.")


def locate_hidden_state_output(output: Any) -> tuple[torch.Tensor, str, Callable[[torch.Tensor], Any]]:
    """Locate the sole [batch, sequence, hidden] tensor in a layer output.

    Qwen decoder-layer implementations may return a bare tensor or a tuple.
    Rather than assuming a tuple layout, this accepts either and rejects
    ambiguous structures.  It deliberately supports only tuple/list nesting,
    which covers the block output forms needed for this diagnostic.
    """
    if isinstance(output, torch.Tensor):
        if output.ndim != 3:
            raise ValueError(f"A direct layer tensor must be rank 3, got {tuple(output.shape)}.")
        return output, "output", lambda replacement: replacement

    matches: list[tuple[tuple[int, ...], torch.Tensor]] = []

    def visit(value: Any, path: tuple[int, ...]) -> None:
        if isinstance(value, torch.Tensor) and value.ndim == 3:
            matches.append((path, value))
        elif isinstance(value, (tuple, list)):
            for index, item in enumerate(value):
                visit(item, path + (index,))

    visit(output, ())
    if len(matches) != 1:
        raise ValueError(
            "Expected exactly one rank-3 hidden-state tensor in layer output; "
            f"found {len(matches)} in {type(output).__name__}."
        )
    path, hidden_states = matches[0]
    location = "output" + "".join(f"[{index}]" for index in path)
    return hidden_states, location, lambda replacement: _replace_tensor_at_path(output, path, replacement)


class LastTokenHook:
    """Add a checked vector only to the final sequence position of a layer output."""

    def __init__(self, delta: torch.Tensor):
        if delta.ndim != 1:
            raise ValueError(f"delta must have shape [hidden_size], got {tuple(delta.shape)}.")
        self.delta = delta
        self.events: list[HookEvent] = []

    def __call__(self, _module, _inputs, output):
        hidden_states, location, replace = locate_hidden_state_output(output)
        if hidden_states.shape[-1] != self.delta.numel():
            raise ValueError(
                f"delta dimension {self.delta.numel()} does not match hidden size {hidden_states.shape[-1]}."
            )
        if self.delta.device != hidden_states.device or self.delta.dtype != hidden_states.dtype:
            raise ValueError(
                "delta must already match the activation device and dtype; "
                f"got delta={self.delta.device}/{self.delta.dtype}, "
                f"activation={hidden_states.device}/{hidden_states.dtype}."
            )

        before = hidden_states.detach().clone()
        explicit_delta = self.delta.view(1, 1, -1)
        modified = hidden_states.clone()
        modified[:, -1, :] = modified[:, -1, :] + explicit_delta[:, 0, :]
        unchanged = bool(
            torch.equal(before[:, :-1, :], modified[:, :-1, :]) if hidden_states.shape[1] > 1 else True
        )
        last_token_changed = not torch.equal(before[:, -1, :], modified[:, -1, :])
        self.events.append(
            HookEvent(
                output_type=type(output).__name__,
                hidden_state_location=location,
                sequence_length=int(hidden_states.shape[1]),
                modified_token_index=int(hidden_states.shape[1] - 1),
                activation_norm_before=float(torch.linalg.vector_norm(before[:, -1, :]).item()),
                perturbation_norm=float(torch.linalg.vector_norm(explicit_delta).item()),
                activation_norm_after=float(torch.linalg.vector_norm(modified[:, -1, :]).item()),
                earlier_positions_unchanged=unchanged,
                last_token_changed=last_token_changed,
                device=str(hidden_states.device),
                dtype=str(hidden_states.dtype).replace("torch.", ""),
                explicit_delta_shape=tuple(int(item) for item in explicit_delta.shape),
            )
        )
        return replace(modified)


def generate_ids(model, tokenizer, prompt: str) -> tuple[torch.Tensor, str, int]:
    """Generate a short deterministic continuation and return IDs, text, prompt length."""
    inputs = move_tokenized_inputs_to_device(tokenizer(prompt, return_tensors="pt"), get_model_input_device(model))
    prompt_length = int(inputs["input_ids"].shape[1])
    with torch.no_grad():
        generated = model.generate(**inputs, do_sample=False, max_new_tokens=4, use_cache=True)
    text = tokenizer.decode(generated[0], skip_special_tokens=True)
    return generated.detach().cpu(), text, prompt_length


def resolve_cache_dir(cache_root: Path) -> Path:
    """Resolve a standard Hugging Face cache root to the Qwen repository parent."""
    repository = "models--Qwen--Qwen3-1.7B"
    for candidate in (cache_root, cache_root / "hub"):
        if (candidate / repository).is_dir():
            return candidate
    raise RuntimeError(
        f"Offline cache does not contain {MODEL_NAME!r} beneath {cache_root} or {cache_root / 'hub'}."
    )


def assert_zero_vector_equivalence(model, tokenizer, layer) -> tuple[bool, dict[str, Any]]:
    """Require bit-identical deterministic output with no hook and a zero hook."""
    baseline_ids, baseline_text, prompt_length = generate_ids(model, tokenizer, PROMPT)
    device = get_model_input_device(model)
    zero_hook = LastTokenHook(torch.zeros(model.config.hidden_size, device=device, dtype=next(model.parameters()).dtype))
    handle = layer.register_forward_hook(zero_hook)
    try:
        hooked_ids, hooked_text, _ = generate_ids(model, tokenizer, PROMPT)
    finally:
        handle.remove()
    equal = torch.equal(baseline_ids, hooked_ids) and baseline_text == hooked_text
    return equal, {
        "prompt_token_count": prompt_length,
        "baseline_text": baseline_text,
        "zero_hook_text": hooked_text,
        "baseline_token_ids": baseline_ids.tolist(),
        "zero_hook_token_ids": hooked_ids.tolist(),
        "zero_hook_events": [asdict(event) for event in zero_hook.events],
    }


def run_diagnostic(cache_dir: Path) -> int:
    """Run the bounded diagnostic and print evidence required by the task."""
    check_cuda_or_raise()
    cache_dir = resolve_cache_dir(cache_dir)
    tokenizer = load_tokenizer(MODEL_NAME, cache_dir=cache_dir, local_files_only=True)
    model = load_causal_lm(MODEL_NAME, dtype="float16", device_map="auto", cache_dir=cache_dir, local_files_only=True)
    model.eval()
    try:
        layers = model.model.layers
        layer = layers[TARGET_LAYER]
        zero_ok, zero_report = assert_zero_vector_equivalence(model, tokenizer, layer)
        if not zero_ok:
            print("HOOK_DIAGNOSTIC_FAIL: zero-vector hook changed deterministic generation.")
            return 1

        activation_device = get_model_input_device(model)
        activation_dtype = next(model.parameters()).dtype
        diagnostic_delta = torch.zeros(model.config.hidden_size, device=activation_device, dtype=activation_dtype)
        diagnostic_delta[0] = torch.tensor(1.0, device=activation_device, dtype=activation_dtype)
        diagnostic_hook = LastTokenHook(diagnostic_delta)
        handle = layer.register_forward_hook(diagnostic_hook)
        try:
            nonzero_ids, nonzero_text, _ = generate_ids(model, tokenizer, PROMPT)
        finally:
            handle.remove()
        restored_ids, restored_text, _ = generate_ids(model, tokenizer, PROMPT)

        events = diagnostic_hook.events
        prefill_events = [event for event in events if event.sequence_length > 1]
        decode_events = [event for event in events if event.sequence_length == 1]
        expected_decode_events = int(nonzero_ids.shape[1] - zero_report["prompt_token_count"] - 1)
        semantics_ok = (
            len(prefill_events) == 1
            and len(decode_events) == expected_decode_events
            and all(event.modified_token_index == event.sequence_length - 1 for event in events)
            and all(event.earlier_positions_unchanged for event in events)
            and all(event.last_token_changed for event in events)
            and all(event.device == str(diagnostic_delta.device) for event in events)
            and all(event.dtype == str(diagnostic_delta.dtype).replace("torch.", "") for event in events)
            and torch.equal(restored_ids, torch.tensor(zero_report["baseline_token_ids"]))
            and restored_text == zero_report["baseline_text"]
        )

        print(f"model_class: {model.__class__.__name__}")
        print(f"target_module: model.model.layers[{TARGET_LAYER}]")
        print(f"module_class: {layer.__class__.__name__}")
        print(f"prompt_token_count: {zero_report['prompt_token_count']}")
        print(f"zero_vector_exact_equivalence: {zero_ok}")
        print(f"zero_hook_invocations: {len(zero_report['zero_hook_events'])}")
        print(f"nonzero_hook_invocations: {len(events)}")
        print(f"prefill_hook_invocations: {len(prefill_events)}")
        print(f"cached_decode_hook_invocations: {len(decode_events)}")
        print(f"expected_cached_decode_invocations: {expected_decode_events}")
        print(f"nonzero_generated_token_ids: {nonzero_ids.tolist()}")
        print(f"nonzero_output_text: {nonzero_text}")
        print(f"hook_removal_restores_baseline: {torch.equal(restored_ids, torch.tensor(zero_report['baseline_token_ids'])) and restored_text == zero_report['baseline_text']}")
        print("hook_events:")
        for index, event in enumerate(events, start=1):
            print(f"  {index}: {asdict(event)}")
        print("cached_past_states: not mutated by this hook; the hook replaces only the current post-block hidden-state output.")
        print("HOOK_DIAGNOSTIC_PASS" if semantics_ok else "HOOK_DIAGNOSTIC_FAIL")
        return 0 if semantics_ok else 1
    finally:
        del model
        gc.collect()
        torch.cuda.empty_cache()


def main() -> int:
    """Parse the external cache location and execute the technical diagnostic."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=Path(r"D:\AI_Cache\huggingface"))
    args = parser.parse_args()
    return run_diagnostic(args.cache_dir)


if __name__ == "__main__":
    raise SystemExit(main())
