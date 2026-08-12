"""Validate the immutable EXP-019 Final-200 freeze boundary."""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CANDIDATE = DATA / "final200_post_similarity_remediation_candidate.csv"
FROZEN = DATA / "final200_frozen.csv"
MANIFEST = DATA / "final200_freeze_manifest.json"
STATUS = DATA / "final200_similarity_remediation_status.json"
REVIEW = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-REPLACEMENT5-HUMAN-REVIEW.md"
REMOVED = {"GAP-LOG-036", "GAP-LOG-005", "GAP-LOG-003", "GAP-DEF-025", "GAP-CAU-014", "GAP-CAU-023", "GAP-DEF-012", "GAP-LOG-033"}
APPROVED = {"REMED-LOG-001", "REMED-LOG-002", "REMED-LOG-003", "REMED2-DEF-001", "REMED2-DEF-002", "REMED2-CAU-001", "REMED2-CAU-002", "REMED2-LOG-001"}
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
    if not FROZEN.exists() or not MANIFEST.exists():
        print("FREEZE_NOT_READY")
        print("reason: final200_frozen.csv and/or final200_freeze_manifest.json is absent")
        return
    candidate = read_csv(CANDIDATE)
    frozen = read_csv(FROZEN)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    require(FROZEN.read_bytes() == CANDIDATE.read_bytes(), "frozen dataset bytes differ from validated candidate")
    require(frozen == candidate and len(frozen) == 200, "frozen dataset content mismatch or count mismatch")
    require(len({row["candidate_id"] for row in frozen}) == 200, "candidate IDs are not unique")
    require(Counter(row["task_class"] for row in frozen) == Counter({"logic": 50, "causality": 50, "analogy": 50, "definition": 50}), "class balance mismatch")
    require(all(4 <= tokens(row["response_text"]) <= 20 for row in frozen), "response length is outside 4-20")
    exact = [row["response_text"] for row in frozen]
    normalized_texts = [normalized(text) for text in exact]
    require(len(exact) == len(set(exact)), "exact duplicate found")
    require(len(normalized_texts) == len(set(normalized_texts)), "normalized duplicate found")
    identifiers = {row["candidate_id"] for row in frozen}
    require(not (REMOVED & identifiers), "documented removed candidate is still present")
    require(APPROVED <= identifiers, "an approved replacement is absent")
    expected_manifest = {
        "dataset_size": 200,
        "class_counts": {"logic": 50, "causality": 50, "analogy": 50, "definition": 50},
        "length_min": 4,
        "length_max": 20,
        "exact_duplicates": 0,
        "normalized_duplicates": 0,
        "random40_human_audit_completed": True,
        "logic_spotcheck_completed": True,
        "logic_remediation_completed": True,
        "similarity_human_review_completed": True,
        "similarity_remediation_completed": True,
        "replacement5_review_completed": True,
        "remaining_repeated_prefix_groups": 7,
        "remaining_char_tfidf_pairs_ge_0_55": 2,
        "remaining_similarity_flags_are_descriptive": True,
        "freeze_decision": "READY_TO_FREEZE",
        "evaluator_frozen_before_final200_test": True,
        "evaluator_retrained_after_freeze": False,
        "final200_predictions_seen_before_freeze": False,
        "EXP017_outputs_accessed_before_freeze": False,
        "random_seed": 20260812,
    }
    require(all(manifest.get(key) == value for key, value in expected_manifest.items()), "freeze manifest is internally inconsistent")
    require(manifest["frozen_dataset_sha256"] == sha256(FROZEN), "frozen dataset hash mismatch")
    require(manifest["evaluator_artifact_sha256"] == EXPECTED_EVALUATOR_HASH, "evaluator artifact hash changed")
    require(manifest["evaluator_config_sha256"] == EXPECTED_CONFIG_HASH, "evaluator config hash changed")
    require(sha256(ROOT / "artifacts" / "evaluator_tfidf_logreg.joblib") == EXPECTED_EVALUATOR_HASH, "evaluator artifact differs on disk")
    require(sha256(ROOT / "evaluator_frozen_config.json") == EXPECTED_CONFIG_HASH, "evaluator config differs on disk")
    require(status["status"] == "FINAL200_FROZEN" and status["replacement_review_completed"] is True, "freeze status is not final")
    review_text = REVIEW.read_text(encoding="utf-8")
    require(review_text.count("**Decision:** Y") == 5, "all five replacement decisions must be Y")
    print("FINAL200_FREEZE_VALIDATION_PASS")
    print("dataset_sha256:", manifest["frozen_dataset_sha256"])
    print("class_counts:", manifest["class_counts"])
    print("freeze_decision: READY_TO_FREEZE")


if __name__ == "__main__":
    main()
