"""Shared UTF-8 JSON/CSV and lightweight schema-validation helpers."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def ensure_dir(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    output = Path(path)
    output.mkdir(parents=True, exist_ok=True)
    return output


def save_json(data: Any, path: str | Path) -> None:
    """Save JSON as UTF-8 with readable indentation."""
    output = Path(path)
    ensure_dir(output.parent)
    with output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def load_json(path: str | Path) -> Any:
    """Load and parse a UTF-8 JSON file."""
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_csv_rows(fieldnames: list[str], rows: list[dict]) -> None:
    """Require every row to have exactly the declared CSV keys."""
    expected = set(fieldnames)
    for index, row in enumerate(rows):
        actual = set(row)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        if missing or extra:
            problems = []
            if missing:
                problems.append(f"missing keys: {missing}")
            if extra:
                problems.append(f"extra keys: {extra}")
            raise ValueError(f"CSV row {index} schema mismatch ({'; '.join(problems)}). Expected keys: {fieldnames}")


def write_csv(path: str | Path, fieldnames: list[str], rows: list[dict]) -> None:
    """Validate and write dictionaries as a UTF-8 CSV file."""
    validate_csv_rows(fieldnames, rows)
    output = Path(path)
    ensure_dir(output.parent)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file into a list of dictionaries."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def assert_required_columns(rows: list[dict], required_columns: list[str]) -> None:
    """Raise ValueError when rows do not contain all required columns."""
    if not rows:
        raise ValueError(f"CSV has no rows; required columns cannot be verified: {required_columns}")
    required = set(required_columns)
    for index, row in enumerate(rows):
        missing = sorted(required - set(row))
        if missing:
            raise ValueError(f"CSV row {index} is missing required columns: {missing}")


def safe_float(value: Any, default: float | None = None) -> float | None:
    """Convert a value to float, returning default for empty or invalid input."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
