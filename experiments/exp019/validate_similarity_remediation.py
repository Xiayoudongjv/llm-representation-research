"""Validate the bounded five-row EXP-019 similarity remediation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SOURCE = DATA / "final200_post_human_remediation_candidate.csv"
OUTPUT = DATA / "final200_post_similarity_remediation_candidate.csv"
LOG = DATA / "final200_similarity_remediation_log.csv"
AUDIT = DATA / "final200_post_similarity_remediation_audit.json"
STATUS = DATA / "final200_similarity_remediation_status.json"
PACKET = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-REPLACEMENT5-HUMAN-REVIEW.md"
REMOVED = {"GAP-DEF-025", "GAP-CAU-014", "GAP-CAU-023", "GAP-DEF-012", "GAP-LOG-033"}
ADDED = {"REMED2-DEF-001", "REMED2-DEF-002", "REMED2-CAU-001", "REMED2-CAU-002", "REMED2-LOG-001"}
EXPECTED_EVALUATOR_HASH = "DF06E7683627F308330E77E8A50D35766F3CA50F5C8DE873E077092DEAEB2BDD"
EXPECTED_CONFIG_HASH = "EB673B63CB0C407C04F55F9B5F8FB687C7BD680FC5B53DDD4CC18A2BCC906744"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def tokens(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text))


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main() -> None:
    source = read_csv(SOURCE)
    output = read_csv(OUTPUT)
    log = read_csv(LOG)
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    source_by_id = {row["candidate_id"]: row for row in source}
    output_by_id = {row["candidate_id"]: row for row in output}
    require(len(source) == 200 and len(output) == 200, "source or remediated candidate count is not 200")
    require(set(source_by_id) - set(output_by_id) == REMOVED, "removed ID set is not exactly authorized")
    require(set(output_by_id) - set(source_by_id) == ADDED, "added ID set is not exactly authorized")
    require(Counter(row["task_class"] for row in output) == Counter({"logic": 50, "causality": 50, "analogy": 50, "definition": 50}), "class balance mismatch")
    for candidate_id in set(source_by_id) & set(output_by_id):
        require(source_by_id[candidate_id] == output_by_id[candidate_id], f"unrelated row changed: {candidate_id}")
    require(all(4 <= tokens(row["response_text"]) <= 20 for row in output), "response length outside 4-20")
    exact = [row["response_text"] for row in output]
    normalized_texts = [normalized(text) for text in exact]
    require(len(exact) == len(set(exact)), "exact duplicate found")
    require(len(normalized_texts) == len(set(normalized_texts)), "normalized duplicate found")
    require(len(log) == 5 and {row["removed_candidate_id"] for row in log} == REMOVED, "remediation log is incomplete")
    require({row["retained_counterpart_id"] for row in log} == {"SRC-DEF-002", "SRC-CAU-006", "SRC-CAU-009", "SRC-DEF-009", "GAP-CAU-017"}, "retained counterparts differ from human record")
    fields = set(output[0])
    require(not any(token in field.casefold() for field in fields for token in ("evaluator", "prediction", "exp017", "hidden", "vector")), "forbidden metadata column found")
    require(audit["evaluator_unchanged"] is True, "evaluator integrity marker is false")
    require(audit["evaluator_artifact_sha256"] == EXPECTED_EVALUATOR_HASH, "evaluator artifact hash changed")
    require(audit["evaluator_config_sha256"] == EXPECTED_CONFIG_HASH, "evaluator config hash changed")
    require(audit["final200_predictions_accessed"] is False and audit["exp017_outputs_accessed"] is False, "scientific-independence status is false")
    require(status["status"] == "REPLACEMENT5_REVIEW_PENDING", "unexpected freeze status")
    require(status["replacement_review_completed"] is False, "replacement review should be pending")
    packet = PACKET.read_text(encoding="utf-8")
    for candidate_id in ADDED:
        require(f"## `{candidate_id}`" in packet, f"replacement absent from review packet: {candidate_id}")
    require(packet.count("**Decision:**\n\n**Reason:**") == 5, "replacement review fields must be blank")
    print("SIMILARITY_REMEDIATION_VALIDATION_PASS")
    print("removed_count: 5")
    print("added_count: 5")
    print("unchanged_other_rows: 195")
    print("class_counts:", dict(Counter(row["task_class"] for row in output)))
    print("freeze_status: REPLACEMENT5_REVIEW_PENDING")


if __name__ == "__main__":
    main()
