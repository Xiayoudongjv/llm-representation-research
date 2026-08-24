"""Read-only monitor for the offline-hybrid TEMP-V2 checkpoint."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


DEFAULT_CHECKPOINT = Path(__file__).resolve().parent / "data" / "temporal_source_v2_offline_runtime" / "offline_checkpoint.json"


def read_status(path: Path) -> dict:
    if not path.exists():
        return {"status": "NOT_STARTED", "checkpoint_exists": False}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "status": payload.get("status"),
        "phase": payload.get("phase"),
        "dump_path": payload.get("dump_path"),
        "structural_candidates_total": payload.get("structural_candidates_total", 0),
        "prior_identity_rejects": payload.get("prior_identity_rejects", 0),
        "fresh_structural_candidates": payload.get("fresh_structural_candidates", 0),
        "labels_collected": payload.get("labels_collected", 0),
        "hydrated": payload.get("hydrated", 0),
        "eligible": payload.get("eligible", 0),
        "updated_at": payload.get("updated_at"),
        "checkpoint_exists": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args(argv)
    print(json.dumps(read_status(args.checkpoint), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
