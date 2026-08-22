#!/usr/bin/env python3
"""Independent validator for an EXP-028 fresh-panel manifest."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

import exp028_panel_lib as panel_lib


def validate_panel_file(
    panel_path: Path,
    exclusion_index_path: Path | None = None,
    expected_sha256: str | None = None,
    *,
    allow_synthetic: bool = False,
) -> tuple[dict, list[str], str]:
    if not panel_path.exists():
        raise ValueError("EXP028_PANEL_MISSING")
    panel_sha256 = panel_lib.sha256_file(panel_path)
    if expected_sha256 and panel_sha256.casefold() != expected_sha256.casefold():
        raise ValueError("EXP028_PANEL_SHA256_MISMATCH")
    panel = panel_lib.read_json(panel_path)
    exclusion_index = None
    if exclusion_index_path is not None:
        if not exclusion_index_path.exists():
            raise ValueError("EXP028_EXCLUSION_INDEX_MISSING")
        exclusion_index = panel_lib.load_exclusion_index(exclusion_index_path)
    errors = panel_lib.validate_panel(
        panel,
        exclusion_index=exclusion_index,
        formal=not allow_synthetic,
    )
    return panel, errors, panel_sha256


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--panel", required=True)
    parser.add_argument("--exclusion-index", default=None)
    parser.add_argument("--expected-sha256", default=None)
    parser.add_argument("--allow-synthetic", action="store_true")
    args = parser.parse_args(argv)

    panel_path = Path(args.panel)
    exclusion_path = Path(args.exclusion_index) if args.exclusion_index else None
    panel, errors, panel_sha256 = validate_panel_file(
        panel_path,
        exclusion_index_path=exclusion_path,
        expected_sha256=args.expected_sha256,
        allow_synthetic=args.allow_synthetic,
    )
    if errors:
        print("EXP028_PANEL_VALIDATION=FAIL")
        for error in errors:
            print(f"ERROR={error}")
        return 1
    stats = panel_lib.panel_statistics(panel)
    print("EXP028_PANEL_VALIDATION=PASS")
    print(f"SHA256={panel_sha256}")
    print(f"ITEMS={stats['item_count']}")
    print(f"SPLITS={stats['split_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
