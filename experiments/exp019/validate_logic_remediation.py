"""Validate the human-authorized three-row EXP-019 logic remediation."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
REMEDIATED = DATA / "final200_post_human_remediation_candidate.csv"
LOG = DATA / "final200_logic_remediation_log.csv"
PACKET = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-LOGIC-REPLACEMENT3-HUMAN-REVIEW.md"
STATUS = DATA / "final200_logic_remediation_final_status.json"
FAILED = {"GAP-LOG-036", "GAP-LOG-005", "GAP-LOG-003"}
NEW = {"REMED-LOG-001", "REMED-LOG-002", "REMED-LOG-003"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text))


def main() -> None:
    locked = read_csv(LOCKED)
    remediated = read_csv(REMEDIATED)
    log = read_csv(LOG)
    locked_by_id = {row["candidate_id"]: row for row in locked}
    remediated_by_id = {row["candidate_id"]: row for row in remediated}
    require(len(locked) == 200 and len(remediated) == 200, "source/derivative row count is not 200")
    require(set(locked_by_id) - set(remediated_by_id) == FAILED, "incorrect removed candidate set")
    require(set(remediated_by_id) - set(locked_by_id) == NEW, "incorrect replacement candidate set")
    require(Counter(row["task_class"] for row in remediated) == Counter({"logic": 50, "causality": 50, "analogy": 50, "definition": 50}), "class balance mismatch")
    require(all(remediated_by_id[candidate_id]["task_class"] == "logic" for candidate_id in NEW), "new candidates are not logic")
    for candidate_id in set(locked_by_id) & set(remediated_by_id):
        require(locked_by_id[candidate_id] == remediated_by_id[candidate_id], f"unrelated row changed: {candidate_id}")
    require(all(1 <= tokens(row["response_text"]) <= 20 for row in remediated), "response outside frozen 1-20 token policy")
    normalized = [" ".join(row["response_text"].casefold().split()) for row in remediated]
    require(len(normalized) == len(set(normalized)), "exact or normalized duplicate found")
    require(len(log) == 3 and {row["removed_candidate_id"] for row in log} == FAILED, "remediation log mismatch")
    require(all(row["human_reason"] == "HUMAN_LABEL_FUNCTION_MISMATCH" and row["remediation_status"] == "REPLACE" for row in log), "remediation log status mismatch")
    fields = set(remediated[0])
    require(not any("evaluator" in field.casefold() or "exp017" in field.casefold() or "prediction" in field.casefold() for field in fields), "forbidden evaluator/EXP-017 field found")
    packet = PACKET.read_text(encoding="utf-8")
    for candidate_id in NEW:
        require(f"## `{candidate_id}`" in packet, f"replacement missing from human packet: {candidate_id}")
        require(f"## `{candidate_id}`" in packet and "**Decision:** Y" in packet, f"replacement is not approved: {candidate_id}")
    require("REVIEW_CRITERION_CLARIFICATION" in json.loads(STATUS.read_text(encoding="utf-8")), "criterion clarification missing from remediation status")
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    require(status["replacement_decisions"] == {candidate_id: "Y" for candidate_id in sorted(NEW)}, "replacement decisions are not all Y")
    require(status["similarity_review_status"] == "SIMILARITY_REVIEW_PENDING", "unexpected similarity review status")
    print("LOGIC_REMEDIATION_VALIDATION_PASS")
    print("removed_count: 3")
    print("replacement_count: 3")
    print("unchanged_other_rows: 197")
    print("class_counts:", dict(Counter(row["task_class"] for row in remediated)))
    print("replacement_decisions: all_Y")
    print("similarity_review_status: SIMILARITY_REVIEW_PENDING")


if __name__ == "__main__":
    main()
