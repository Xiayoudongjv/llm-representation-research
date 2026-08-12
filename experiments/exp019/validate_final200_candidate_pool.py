"""Validate the assembled 200-row EXP-019 pre-human-audit candidate pool."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
POOL = DATA / "final200_candidate_pool_pre_human_audit.csv"
SAMPLE = DATA / "final200_human_audit_sample.csv"
RETAINED = DATA / "existing100_corrected_retained_pool.csv"
GAP = DATA / "gap128_audited_candidates.csv"
CLASSES = ("logic", "causality", "analogy", "definition")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    pool = read_csv(POOL)
    sample = read_csv(SAMPLE)
    retained = read_csv(RETAINED)
    gap = read_csv(GAP)
    require(len(pool) == 200, f"pool rows: {len(pool)}")
    require(Counter(row["task_class"] for row in pool) == Counter({task_class: 50 for task_class in CLASSES}), "pool class balance mismatch")
    require(len({row["candidate_id"] for row in pool}) == 200, "duplicate pool IDs")
    require(set(row["candidate_id"] for row in pool) == {row["candidate_id"] for row in retained} | {row["candidate_id"] for row in gap if row["acceptance_status"] == "ACCEPT_CANDIDATE"}, "pool does not equal retained plus accepted gap")
    response_texts = [row["response_text"].strip().casefold() for row in pool]
    require(len(response_texts) == len(set(response_texts)), "duplicate normalized response_text in pool")
    require(all(row["response_text"].strip() for row in pool), "empty response_text")
    gap_ids = {row["candidate_id"] for row in gap}
    gap_rows = [row for row in pool if row["candidate_id"] in gap_ids]
    require(all(1 <= int(row["length_tokens"]) <= 20 for row in gap_rows), "gap length outside 1-20")
    require(all(row["length_band"] in {"short", "medium", "limited_long"} for row in gap_rows), "invalid gap length band")
    require(len(sample) == 40, f"human sample rows: {len(sample)}")
    require(len({row["candidate_id"] for row in sample}) == 40, "duplicate human sample IDs")
    require(set(row["candidate_id"] for row in sample) <= {row["candidate_id"] for row in pool}, "human sample contains unknown ID")
    human_fields = ("human_label_agreement", "human_naturalness", "human_self_contained", "human_ambiguity", "human_notes")
    require(all(not row[field] for row in sample for field in human_fields), "human audit fields are not blank")
    require(all("intervention" not in key.lower() and "hidden" not in key.lower() and "vector" not in key.lower() for row in pool for key in row), "intervention/hidden/vector field found")

    print("FINAL200_POOL_VALIDATION_PASS")
    print("pool_rows:", len(pool))
    print("class_counts:", dict(Counter(row["task_class"] for row in pool)))
    print("provenance_counts:", dict(Counter(row["provenance"] for row in pool)))
    print("gap_length_counts:", {task_class: dict(Counter(row["length_band"] for row in gap_rows if row["task_class"] == task_class)) for task_class in CLASSES})
    print("retained_rows_outside_gap_length_policy:", sum(not (1 <= int(row["length_tokens"]) <= 20) for row in pool if row["candidate_id"] not in gap_ids))
    print("human_sample_rows:", len(sample))
    print("human_fields_blank: true")


if __name__ == "__main__":
    main()
