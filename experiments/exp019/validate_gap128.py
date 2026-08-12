"""Validate the offline EXP-019 gap-candidate construction outputs."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
RAW = DATA / "gap128_raw_candidates.csv"
NORMALIZED = DATA / "gap128_normalized_candidates.csv"
AUDITED = DATA / "gap128_audited_candidates.csv"
EXCLUSION = DATA / "existing100_human_review_exclusion_log.csv"
STATUS = DATA / "final200_gap_status_after_exclusion.json"

CLASSES = ("logic", "causality", "analogy", "definition")
PROVENANCES = ("independent_external", "rule_composed", "ai_assisted_surface_normalized")
MARKERS = {
    "logic": ("therefore", "so", "implies", "entails", "must"),
    "causality": ("because", "causes", "leads", "results", "due"),
    "analogy": ("like", "as", "similar", "corresponds", "relation"),
    "definition": (" is ", "means", "refers", "defined", "describes"),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    raw = read_csv(RAW)
    normalized = read_csv(NORMALIZED)
    audited = read_csv(AUDITED)
    exclusions = read_csv(EXCLUSION)
    status = json.loads(STATUS.read_text(encoding="utf-8"))

    require(len(raw) == 128, f"raw rows: {len(raw)}")
    require(len(normalized) == 128, f"normalized rows: {len(normalized)}")
    require(len(audited) == 128, f"audited rows: {len(audited)}")
    require(len(exclusions) == 26, f"exclusion rows: {len(exclusions)}")
    ids = [row["candidate_id"] for row in raw]
    require(len(set(ids)) == 128, "duplicate raw candidate_id")
    require(set(ids) == {f"GAP-LOG-{i:03d}" for i in range(1, 43)} | {f"GAP-CAU-{i:03d}" for i in range(1, 31)} | {f"GAP-ANA-{i:03d}" for i in range(1, 27)} | {f"GAP-DEF-{i:03d}" for i in range(1, 31)}, "gap ID set mismatch")

    class_counts = Counter(row["task_class"] for row in raw)
    require(class_counts == Counter({"logic": 42, "causality": 30, "analogy": 26, "definition": 30}), f"class counts: {class_counts}")
    provenance_counts = Counter(row["provenance"] for row in raw)
    require(set(provenance_counts) == set(PROVENANCES), f"provenances: {provenance_counts}")
    require(max(provenance_counts.values()) / 128 <= 0.70, f"provenance exceeds 70%: {provenance_counts}")
    by_class_provenance = defaultdict(set)
    for row in raw:
        by_class_provenance[row["task_class"]].add(row["provenance"])
    require(all(len(values) >= 2 for values in by_class_provenance.values()), "a class maps to fewer than two provenances")
    external_sources = Counter(row["source_reference"] for row in raw if row["source_reference"] != "rule_composed://deterministic-construction")
    require(not external_sources or max(external_sources.values()) / sum(external_sources.values()) <= 0.15, f"external source exceeds 15%: {external_sources}")
    require(all(row["source_reference"] for row in raw), "missing source reference")
    require(all(row["topic_domain"] for row in raw), "missing topic domain")
    require(len({row["source_reference"] for row in raw}) >= 10, "fewer than ten source references")

    raw_by_id = {row["candidate_id"]: row for row in raw}
    norm_by_id = {row["candidate_id"]: row for row in normalized}
    audit_by_id = {row["candidate_id"]: row for row in audited}
    require(set(raw_by_id) == set(norm_by_id) == set(audit_by_id), "candidate IDs differ across files")
    require(all(set(row) == {"candidate_id", "raw_response", "normalized_response", "normalization_status", "semantic_guard", "normalization_notes"} for row in normalized), "normalized schema mismatch")
    require(all(row["normalization_status"] in {"PASS", "SURFACE_NORMALIZED", "REJECT_SEMANTICALLY_UNCLEAR", "REJECT_UNNATURAL_OR_FRAGMENTARY"} for row in normalized), "invalid normalization status")
    require(all(row["semantic_guard"] in {"UNCHANGED", "SURFACE_ONLY_UNCHANGED", "PRESERVED", "REJECTED"} for row in normalized), "invalid semantic guard")
    require(all(row["acceptance_status"] in {"ACCEPT_CANDIDATE", "REJECT_CANDIDATE"} for row in audited), "invalid acceptance status")
    require(all(1 <= int(row["length_tokens"]) <= 20 for row in audited), "length outside 1-20 tokens")
    require(all(row["length_band"] in {"short", "medium", "limited_long"} for row in audited), "invalid length band")
    require(all(raw_by_id[key]["raw_response"] == norm_by_id[key]["raw_response"] for key in raw_by_id), "raw text changed before normalization")
    require(all(audit_by_id[key]["normalized_response"] == norm_by_id[key]["normalized_response"] for key in raw_by_id), "audit/normalization mismatch")

    normalized_texts = [row["normalized_response"].strip().casefold() for row in normalized if row["normalization_status"] not in {"REJECT_SEMANTICALLY_UNCLEAR", "REJECT_UNNATURAL_OR_FRAGMENTARY"}]
    require(len(normalized_texts) == len(set(normalized_texts)), "duplicate normalized gap responses")
    marker_counts = {task_class: {marker: sum(marker in row["normalized_response"].casefold() for row in audited if row["task_class"] == task_class) for marker in markers} for task_class, markers in MARKERS.items()}

    require(status["remaining_total"] == 128, "status remaining_total mismatch")
    require(status["remaining_by_class"] == {"logic": 42, "causality": 30, "analogy": 26, "definition": 30}, "status class targets mismatch")
    require(all(row["new_status"] == "EXCLUDED_FROM_PRIMARY_POOL_FOR_EFFICIENCY_AND_AMBIGUITY" for row in exclusions), "invalid exclusion status")

    print("GAP128_VALIDATION_PASS")
    print("raw_rows:", len(raw))
    print("class_counts:", dict(class_counts))
    print("provenance_counts:", dict(provenance_counts))
    print("external_source_counts:", dict(external_sources))
    print("source_reference_count:", len({row["source_reference"] for row in raw}))
    print("normalization_counts:", dict(Counter(row["normalization_status"] for row in normalized)))
    print("acceptance_counts:", dict(Counter(row["acceptance_status"] for row in audited)))
    print("length_counts:", {task_class: dict(Counter(row["length_band"] for row in audited if row["task_class"] == task_class)) for task_class in CLASSES})
    print("lexical_marker_counts:", marker_counts)
    print("exclusion_rows:", len(exclusions))
    print("model_run: false")


if __name__ == "__main__":
    main()
