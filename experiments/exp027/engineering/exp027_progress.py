"""Outcome-blind EXP-027 formal-run progress and heartbeat helper.

This module is prospective engineering infrastructure. It may emit only
execution metadata and must not emit any prerelease scientific outcome before
the canonical result is published.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_STATE_KEYS = frozenset({
    "stage",
    "completed",
    "total",
    "percent",
    "elapsed",
    "last_update",
})

# These strings are deliberately forbidden from progress state and stdout
# lines until the canonical scientific result has been published.
FORBIDDEN_OUTCOME_FIELDS = frozenset({
    "rho",
    "sdi",
    "low_d",
    "low-d",
    "ci",
    "support",
    "route",
    "condition",
    "model_comparison",
    "comparison_outcome",
})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomically replace *path* with compact JSON and a trailing newline."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)


class OutcomeBlindProgress:
    """Emit human-monitorable progress without exposing scientific values."""

    def __init__(self, prefix: str = "[EXP027]", state_path: Path | str | None = None) -> None:
        self.prefix = prefix
        self.state_path = Path(state_path) if state_path is not None else None
        self._started_monotonic = time.monotonic()

    def _elapsed_seconds(self) -> float:
        return float(time.monotonic() - self._started_monotonic)

    def _percent(self, completed: int | None, total: int | None) -> float | None:
        if completed is None or not total:
            return None
        return round(100.0 * float(completed) / float(total), 1)

    def report(
        self,
        stage: str,
        completed: int | None = None,
        total: int | None = None,
        percent: float | None = None,
        eta_seconds: float | None = None,
        heartbeat: bool | None = None,
        publication_status: str | None = None,
    ) -> dict[str, Any]:
        """Print one outcome-blind progress line and optionally update state."""
        completed_value = None if completed is None else int(completed)
        total_value = None if total is None else int(total)
        if percent is None:
            percent_value = self._percent(completed_value, total_value)
        else:
            percent_value = round(float(percent), 1)

        parts = [f"stage={stage}"]
        if completed_value is not None:
            parts.append(f"completed={completed_value}")
        if total_value is not None:
            parts.append(f"total={total_value}")
        if percent_value is not None:
            parts.append(f"percent={percent_value}")
        parts.append(f"elapsed={round(self._elapsed_seconds(), 1)}")
        if eta_seconds is not None:
            parts.append(f"eta={round(float(eta_seconds), 1)}")
        if heartbeat is not None:
            parts.append(f"heartbeat={str(bool(heartbeat)).lower()}")
        if publication_status is not None:
            parts.append(f"publication_status={publication_status}")

        print(f"{self.prefix} " + " ".join(parts), flush=True)

        state = None
        if self.state_path is not None:
            state = self.write_state(stage, completed_value, total_value, percent_value)
        return state if state is not None else {}

    def write_state(
        self,
        stage: str,
        completed: int | None = None,
        total: int | None = None,
        percent: float | None = None,
    ) -> dict[str, Any]:
        """Write only the allowed execution-progress fields to an atomic file."""
        if percent is None:
            percent = self._percent(completed, total)
        state = {
            "stage": stage,
            "completed": completed,
            "total": total,
            "percent": percent,
            "elapsed": round(self._elapsed_seconds(), 1),
            "last_update": _utc_now_iso(),
        }
        self._validate_state(state)
        if self.state_path is not None:
            _atomic_write_json(self.state_path, state)
        return state

    @staticmethod
    def _validate_state(state: dict[str, Any]) -> None:
        if not set(state).issubset(ALLOWED_STATE_KEYS):
            raise ValueError(f"disallowed progress state keys: {sorted(set(state) - ALLOWED_STATE_KEYS)}")
        serialized = json.dumps(state, ensure_ascii=False, sort_keys=True).lower()
        for field in FORBIDDEN_OUTCOME_FIELDS:
            if field in serialized:
                raise ValueError(f"progress state contains forbidden scientific field: {field}")


def should_emit(completed: int, interval: int = 100) -> bool:
    """Low-volume deterministic bootstrap reporting policy."""
    return int(completed) % int(interval) == 0
