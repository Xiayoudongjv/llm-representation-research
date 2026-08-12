"""Validate the EXP-019 pre-human-audit lock without running a model."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCK = DATA / "final200_pre_human_audit_locked.csv"
MANIFEST = DATA / "final200_pre_human_audit_lock_manifest.json"
SAMPLE = DATA / "final200_human_audit_sample.csv"
EXCLUDED = DATA / "existing100_human_review_exclusion_log.csv"
REJECTED = DATA / "existing100_corrected_rejected.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    rows = read_csv(LOCK)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    sample = read_csv(SAMPLE)
    require(len(rows) == 200, "lock row count is not 200")
    require(Counter(row["task_class"] for row in rows) == Counter({c: 50 for c in ("logic", "causality", "analogy", "definition")}), "class balance mismatch")
    require(len({row["candidate_id"] for row in rows}) == 200, "duplicate candidate IDs")
    require(all(1 <= len(row["response_text"].split()) <= 20 for row in rows), "response outside 1-20 whitespace tokens")
    normalized = [" ".join(row["response_text"].casefold().split()) for row in rows]
    require(len(normalized) == len(set(normalized)), "normalized duplicate response")
    excluded = {row["candidate_id"] for row in read_csv(EXCLUDED)}
    rejected = {row["candidate_id"] for row in read_csv(REJECTED)}
    ids = {row["candidate_id"] for row in rows}
    require(not ids & excluded, "excluded human-review candidate present")
    require(not ids & rejected, "rejected original candidate present")
    forbidden = ("classifier", "probability", "steering", "intervention", "hidden", "vector", "EXP017")
    require(not any(any(term.lower() in key.lower() for term in forbidden) for row in rows for key in row), "forbidden metadata field present")
    human_fields = ("human_label_agreement", "human_naturalness", "human_self_contained", "human_ambiguity", "human_notes")
    require(all(not row[field] for row in sample for field in human_fields), "human audit fields are not blank")
    require(manifest["dataset_size"] == 200 and manifest["length_violations"] == 0, "manifest count mismatch")
    require(manifest["human_audit_completed"] is False and manifest["evaluator_trained"] is False and manifest["EXP017_outputs_accessed"] is False, "manifest safety flags mismatch")
    print("PRE_HUMAN_AUDIT_LOCK_VALIDATION_PASS")
    print("rows:", len(rows))
    print("class_counts:", dict(Counter(row["task_class"] for row in rows)))
    print("length_min_max:", manifest["length_min"], manifest["length_max"])
    print("human_audit_completed: false")
    print("evaluator_trained: false")
    print("EXP017_outputs_accessed: false")


if __name__ == "__main__":
    main()
