"""Small filesystem and serialization helpers."""

from __future__ import annotations

import json
from pathlib import Path


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def save_json(data, path: str) -> None:
    output_path = Path(path)
    ensure_dir(str(output_path.parent))
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
