"""EXP-000B: reproducibly extract hidden-state metadata from one prompt."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.hidden_states import hidden_states_metadata, run_forward_with_hidden_states, summarize_hidden_states
from src.model_loader import check_cuda_or_raise, load_causal_lm, load_tokenizer, print_model_info
from src.utils import save_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--fallback_model_name", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    parser.add_argument("--prompt", default="Explain briefly why logical reasoning requires preserving relationships between concepts.")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--use_fallback", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_name = args.fallback_model_name if args.use_fallback else args.model_name
    print(f"Loading model: {model_name}")
    check_cuda_or_raise()
    tokenizer = load_tokenizer(model_name)
    model = load_causal_lm(model_name, dtype=args.dtype)
    print_model_info(model)
    hidden_states = run_forward_with_hidden_states(model, tokenizer, args.prompt)
    summarize_hidden_states(hidden_states)
    output_path = PROJECT_ROOT / "results" / "exp000" / "hidden_states_metadata.json"
    save_json(hidden_states_metadata(hidden_states), str(output_path))
    print(f"saved_metadata: {output_path}")


if __name__ == "__main__":
    try:
        main()
    except (torch.cuda.OutOfMemoryError, RuntimeError) as exc:
        if isinstance(exc, torch.cuda.OutOfMemoryError) or "out of memory" in str(exc).lower():
            print("CUDA out of memory. Try --use_fallback or a smaller dtype such as --dtype float16.", file=sys.stderr)
        else:
            print(f"Experiment failed during CUDA/model execution: {exc}", file=sys.stderr)
        raise
    except OSError as exc:
        print("Hugging Face download/cache error. Set HF_ENDPOINT if needed or check the model name and local Hugging Face cache.", file=sys.stderr)
        raise
    except Exception as exc:
        print(f"Experiment failed unexpectedly: {exc}", file=sys.stderr)
        raise
