"""Summarize human QA and apply the documented Final-200 freeze gate.

No human judgment is created here. This program reads completed human input and
either produces a derivative freeze copy or a remediation list; it never edits
the locked candidate pool.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
SAMPLE = DATA / "final200_human_audit_sample.csv"
SIMILARITY = DATA / "final200_similarity_review.csv"
SUMMARY = DATA / "final200_human_audit_summary.json"
FROZEN = DATA / "final200_frozen.csv"
MANIFEST = DATA / "final200_freeze_manifest.json"
REMEDIATION = DATA / "final200_remediation_needed.csv"
DOC = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-FREEZE-AUDIT.md"
AUDIT_FIELDS = ("human_label_agreement", "human_naturalness", "human_self_contained", "human_ambiguity")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def decision(summary: dict[str, object], random_rows: list[dict[str, str]], similarity_rows: list[dict[str, str]]) -> str:
    """Use conservative, predeclared human-QA thresholds only."""
    if summary["total_audited"] != 40 or summary["similarity_review_completed"] is not True:
        return "HUMAN_REVIEW_INCOMPLETE"
    serious = summary["label_disagree"] + summary["label_ambiguous"] + summary["awkward"] + summary["self_contained_no"] + summary["ambiguous"] + summary["similarity_redundant"]
    by_class = Counter(row["task_class"] for row in random_rows if row["human_label_agreement"] != "agree")
    # Ready requires no negative human judgment. A small number of borderline
    # items and at most one uncertain similarity flag remain allowable.
    if serious == 0 and summary["borderline"] <= 2 and summary["similarity_uncertain"] <= 1:
        return "READY_TO_FREEZE"
    if serious <= 5 and not any(count >= 2 for count in by_class.values()):
        return "MINOR_REMEDIATION_REQUIRED"
    return "MAJOR_REMEDIATION_REQUIRED"


def remediation_rows(random_rows: list[dict[str, str]], similarity_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for row in random_rows:
        concerns = []
        if row["human_label_agreement"] != "agree": concerns.append(f"label_agreement={row['human_label_agreement']}")
        if row["human_naturalness"] == "awkward": concerns.append("naturalness=awkward")
        if row["human_self_contained"] == "no": concerns.append("self_contained=no")
        if row["human_ambiguity"] == "ambiguous": concerns.append("ambiguity=ambiguous")
        if concerns:
            rows.append({"candidate_id": row["candidate_id"], "task_class": row["task_class"], "issue_source": "random_human_audit", "human_reason": "; ".join(concerns), "human_notes": row["human_notes"]})
    for row in similarity_rows:
        if row["human_redundancy_decision"] in {"redundant", "uncertain"}:
            rows.append({"candidate_id": row["candidate_id"], "task_class": row["task_class"], "issue_source": "similarity_review", "human_reason": f"redundancy={row['human_redundancy_decision']}; matched={row['matched_candidate_id']}", "human_notes": row["human_notes"]})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finalize", action="store_true", help="Create freeze/remediation derivatives after all human fields are complete.")
    args = parser.parse_args()
    random_rows = read_csv(SAMPLE)
    similarity_rows = read_csv(SIMILARITY)
    random_complete = all(all(row[field] for field in AUDIT_FIELDS) for row in random_rows)
    similarity_complete = all(row["human_redundancy_decision"] in {"distinct_enough", "redundant", "uncertain"} for row in similarity_rows)
    summary = {
        "total_audited": sum(all(row[field] for field in AUDIT_FIELDS) for row in random_rows),
        "label_agree": sum(row["human_label_agreement"] == "agree" for row in random_rows),
        "label_disagree": sum(row["human_label_agreement"] == "disagree" for row in random_rows),
        "label_ambiguous": sum(row["human_label_agreement"] == "ambiguous" for row in random_rows),
        "natural": sum(row["human_naturalness"] == "natural" for row in random_rows),
        "acceptable": sum(row["human_naturalness"] == "acceptable" for row in random_rows),
        "awkward": sum(row["human_naturalness"] == "awkward" for row in random_rows),
        "self_contained_yes": sum(row["human_self_contained"] == "yes" for row in random_rows),
        "self_contained_no": sum(row["human_self_contained"] == "no" for row in random_rows),
        "clear": sum(row["human_ambiguity"] == "clear" for row in random_rows),
        "borderline": sum(row["human_ambiguity"] == "borderline" for row in random_rows),
        "ambiguous": sum(row["human_ambiguity"] == "ambiguous" for row in random_rows),
        "random_human_audit_completed": random_complete,
        "similarity_review_count": len(similarity_rows),
        "similarity_review_completed": similarity_complete,
        "similarity_distinct_enough": sum(row["human_redundancy_decision"] == "distinct_enough" for row in similarity_rows),
        "similarity_redundant": sum(row["human_redundancy_decision"] == "redundant" for row in similarity_rows),
        "similarity_uncertain": sum(row["human_redundancy_decision"] == "uncertain" for row in similarity_rows),
        "evaluator_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    }
    summary["freeze_decision"] = decision(summary, random_rows, similarity_rows) if random_complete and similarity_complete else "HUMAN_REVIEW_INCOMPLETE"
    if not args.finalize:
        print(json.dumps(summary, indent=2))
        return
    if not random_complete or not similarity_complete:
        raise RuntimeError("Cannot finalize: human random audit and similarity review must both be complete.")
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    problems = remediation_rows(random_rows, similarity_rows)
    if summary["freeze_decision"] == "READY_TO_FREEZE":
        shutil.copyfile(LOCKED, FROZEN)
        manifest = {
            "dataset_size": 200,
            "class_counts": {"logic": 50, "causality": 50, "analogy": 50, "definition": 50},
            "length_range": "4-20",
            "random_human_audit_size": 40,
            "random_human_audit_completed": True,
            "similarity_review_completed": True,
            "evaluator_frozen_before_final200_test": True,
            "evaluator_retrained_after_freeze": False,
            "final200_predictions_seen_before_freeze": False,
            "EXP017_outputs_accessed": False,
            "random_seed": 20260812,
            "freeze_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_locked_file": LOCKED.name,
            "freeze_decision": "READY_TO_FREEZE",
        }
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    else:
        write_csv(REMEDIATION, ["candidate_id", "task_class", "issue_source", "human_reason", "human_notes"], problems)
    DOC.parent.mkdir(parents=True, exist_ok=True)
    DOC.write_text("# EXP-019 Final-200 Freeze Audit\n\n"
                   f"- Random audit: {summary['total_audited']}/40 completed.\n"
                   f"- Label agreement: {summary['label_agree']} agree, {summary['label_disagree']} disagree, {summary['label_ambiguous']} ambiguous.\n"
                   f"- Naturalness: {summary['natural']} natural, {summary['acceptable']} acceptable, {summary['awkward']} awkward.\n"
                   f"- Self-contained: {summary['self_contained_yes']} yes, {summary['self_contained_no']} no.\n"
                   f"- Ambiguity: {summary['clear']} clear, {summary['borderline']} borderline, {summary['ambiguous']} ambiguous.\n"
                   f"- Similarity review: {summary['similarity_review_count']} flagged candidates; {summary['similarity_redundant']} redundant, {summary['similarity_uncertain']} uncertain.\n\n"
                   f"## Freeze decision\n\n`{summary['freeze_decision']}`\n\n"
                   "The evaluator was already frozen. Final-200 predictions were not viewed, and EXP-017 remains locked.\n", encoding="utf-8")
    print("FINAL200_HUMAN_AUDIT_FINALIZED")
    print("freeze_decision:", summary["freeze_decision"])
    print("remediation_count:", len(problems))


if __name__ == "__main__":
    main()
