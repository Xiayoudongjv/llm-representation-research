"""EXP-001: compute a representation geometry baseline."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

import numpy as np
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.model_loader import load_causal_lm, load_tokenizer, print_model_info
from src.plotting import plot_pca_2d
from src.representation_metrics import cosine_similarity_matrix, pca_2d


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model_name", default="Qwen/Qwen3-1.7B")
    parser.add_argument("--fallback_model_name", default="TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    parser.add_argument("--use_fallback", action="store_true")
    parser.add_argument("--dtype", choices=["float16", "bfloat16", "float32"], default="float16")
    parser.add_argument("--layer", type=int, default=-1)
    parser.add_argument("--prompts_path", default="experiments/exp001/prompts.json")
    parser.add_argument("--output_dir", default="results/exp001")
    return parser.parse_args()


def _write_csv(path: Path, rows: list[list], header: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    model_name = args.fallback_model_name if args.use_fallback else args.model_name
    prompts_path = PROJECT_ROOT / args.prompts_path
    output_dir = PROJECT_ROOT / args.output_dir
    prompts = json.loads(prompts_path.read_text(encoding="utf-8"))
    prompt_ids = [item["id"] for item in prompts]
    groups = [item["group"] for item in prompts]

    print(f"Loading model: {model_name}")
    tokenizer = load_tokenizer(model_name)
    model = load_causal_lm(model_name, dtype=args.dtype)
    print_model_info(model)
    device = next(model.parameters()).device
    representations = []
    selected_layer = args.layer
    with torch.no_grad():
        for item in prompts:
            inputs = tokenizer(item["text"], return_tensors="pt")
            inputs = {name: value.to(device) for name, value in inputs.items()}
            outputs = model(**inputs, output_hidden_states=True, return_dict=True)
            hidden_states = outputs.hidden_states
            layer_index = args.layer if args.layer >= 0 else len(hidden_states) + args.layer
            if not 0 <= layer_index < len(hidden_states):
                raise ValueError(f"Layer {args.layer} is out of range for {len(hidden_states)} hidden-state tensors.")
            selected_layer = layer_index
            representations.append(hidden_states[layer_index][0, -1, :].detach().cpu().float().numpy())

    matrix = np.stack(representations).astype(np.float32)
    cosine = cosine_similarity_matrix(matrix)
    coords, explained = pca_2d(matrix)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "model_name": model_name,
        "selected_layer": selected_layer,
        "num_prompts": len(prompts),
        "hidden_size": int(matrix.shape[1]),
        "prompt_ids": prompt_ids,
        "groups": groups,
        "pca_explained_variance_ratio": explained.tolist(),
    }
    (output_dir / "representations_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    _write_csv(output_dir / "cosine_similarity.csv", cosine.tolist(), ["id"] + prompt_ids)
    cosine_path = output_dir / "cosine_similarity.csv"
    lines = cosine_path.read_text(encoding="utf-8").splitlines()
    cosine_path.write_text("\n".join([lines[0]] + [f"{prompt_ids[i]},{lines[i + 1]}" for i in range(len(prompt_ids))]) + "\n", encoding="utf-8")
    _write_csv(output_dir / "pca_coords.csv", [[item["id"], item["group"], coords[i, 0], coords[i, 1]] for i, item in enumerate(prompts)], ["id", "group", "x", "y"])
    plot_pca_2d(coords, prompt_ids, str(output_dir / "pca_plot.png"), f"EXP-001 PCA: {model_name}, layer {selected_layer}")
    print(f"saved_outputs: {output_dir}")


if __name__ == "__main__":
    main()
