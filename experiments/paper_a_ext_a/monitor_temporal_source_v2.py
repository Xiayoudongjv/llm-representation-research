"""Read-only PowerShell-friendly TEMP-V2 checkpoint monitor."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_CHECKPOINT = Path(__file__).resolve().parent / "data" / "temporal_source_v2_runtime" / "checkpoint.json"


def render(checkpoint: dict) -> str:
    timestamp = checkpoint.get("retrieval_timestamp", "")
    if timestamp:
        try:
            timestamp = datetime.fromisoformat(timestamp).astimezone(timezone.utc).isoformat()
        except ValueError:
            pass
    values = [
        ("Time", timestamp),
        ("Candidates", checkpoint.get("fresh_candidates_discovered", 0)),
        ("RootValid", checkpoint.get("event_root_valid", 0)),
        ("TimeValid", checkpoint.get("time_valid", 0)),
        ("LeakagePass", checkpoint.get("surface_leakage_pass", 0)),
        ("Eligible", checkpoint.get("final_eligible_events", 0)),
        ("P580", checkpoint.get("p580_used", 0)),
        ("P585", checkpoint.get("p585_fallback_used", 0)),
        ("Families", checkpoint.get("families_count", 0)),
        ("Status", checkpoint.get("status", "UNKNOWN")),
    ]
    return "\n".join(f"{key}={value}" for key, value in values)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args()
    if not args.checkpoint.exists():
        print("Status=NO_CHECKPOINT")
        return 0
    print(render(json.loads(args.checkpoint.read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
