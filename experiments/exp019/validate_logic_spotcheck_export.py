"""Validate the blinded, deterministic EXP-019 logic-only spot-check export."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SAMPLE = DATA / "final200_human_audit_sample.csv"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
SPOTCHECK = DATA / "final200_logic_spotcheck10_template.csv"
MANIFEST = DATA / "final200_logic_spotcheck10_manifest.json"
FAILED = {"GAP-LOG-036", "GAP-LOG-005"}
SEED = 20260812


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    sample = read_csv(SAMPLE)
    locked = {row["candidate_id"]: row for row in read_csv(LOCKED)}
    spotcheck = read_csv(SPOTCHECK)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    reviewed_logic = {row["candidate_id"] for row in sample if row["task_class"] == "logic"}
    require(len(spotcheck) == 10 and len({row["candidate_id"] for row in spotcheck}) == 10, "spot-check is not exactly ten unique rows")
    require(manifest["seed"] == SEED, "deterministic seed mismatch")
    require(manifest["selected_candidate_ids"] == [row["candidate_id"] for row in spotcheck], "manifest/CSV selection mismatch")
    for row in spotcheck:
        candidate_id = row["candidate_id"]
        authoritative = locked.get(candidate_id)
        require(authoritative is not None, f"spot-check candidate missing from locked pool: {candidate_id}")
        require(authoritative["task_class"] == "logic", f"spot-check candidate is not logic: {candidate_id}")
        require(candidate_id not in FAILED, f"explicit failure appears in spot-check: {candidate_id}")
        require(candidate_id not in reviewed_logic, f"already reviewed random logic candidate appears in spot-check: {candidate_id}")
        require(row["response_text"] == authoritative["response_text"], f"response mismatch with locked pool: {candidate_id}")
        require(not row["human_decision"] and not row["human_reason"], f"human decision prefilled: {candidate_id}")
    print("LOGIC_SPOTCHECK_EXPORT_VALIDATION_PASS")
    print("spotcheck_rows:", len(spotcheck))
    print("reviewed_logic_overlap: 0")
    print("decisions_blank: true")
    print("seed:", SEED)


if __name__ == "__main__":
    main()
