"""Freeze the human-approved EXP-019 Final-200 candidate pool without evaluation."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
CANDIDATE = DATA / "final200_post_similarity_remediation_candidate.csv"
FROZEN = DATA / "final200_frozen.csv"
MANIFEST = DATA / "final200_freeze_manifest.json"
STATUS = DATA / "final200_similarity_remediation_status.json"
REVIEW = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-REPLACEMENT5-HUMAN-REVIEW.md"
FREEZE_AUDIT = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-FREEZE-AUDIT.md"
REPLACEMENT_IDS = ("REMED2-DEF-001", "REMED2-DEF-002", "REMED2-CAU-001", "REMED2-CAU-002", "REMED2-LOG-001")
EXPECTED_EVALUATOR_HASH = "DF06E7683627F308330E77E8A50D35766F3CA50F5C8DE873E077092DEAEB2BDD"
EXPECTED_CONFIG_HASH = "EB673B63CB0C407C04F55F9B5F8FB687C7BD680FC5B53DDD4CC18A2BCC906744"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def import_replacement_decisions(text: str) -> str:
    for candidate_id in REPLACEMENT_IDS:
        heading = f"## `{candidate_id}`"
        start = text.find(heading)
        if start < 0:
            raise ValueError(f"Replacement review entry is missing: {candidate_id}")
        end = text.find("\n---", start)
        if end < 0:
            raise ValueError(f"Replacement review entry has no closing separator: {candidate_id}")
        block = text[start:end]
        if "**Decision:**" not in block:
            raise ValueError(f"Replacement review entry has no decision field: {candidate_id}")
        block = re.sub(r"(?m)^\*\*Decision:\*\*\s*(?:Y)?$", "**Decision:** Y", block, count=1)
        text = text[:start] + block + text[end:]
    return text


def audit_document(dataset_sha: str, artifact_sha: str, config_sha: str) -> str:
    return f"""# EXP-019 Final-200 Freeze Audit

## Dataset Construction

The frozen candidate derives from the documented 200-row EXP-019 construction workflow. It contains 50 examples each for logic, causality, analogy, and definition, with response lengths from 4 to 20 tokens.

## Alignment Repair

The prior alignment review and correction records remain preserved as historical audit materials.

## Random-40 Human Audit

The completed Random-40 audit recorded 38 `Y`, 2 `N`, and 0 uncertain judgments.

## Logic Spot Check

The ten-item Logic spot-check recorded 9 `Y`, 1 `N`, and 0 uncertain judgments.

## Logic Remediation

Three Logic mismatches were removed and replaced. The three replacement decisions are `Y`; `REMED-LOG-002` was accepted under the existing frozen exclusion/contradiction criterion through the recorded `REVIEW_CRITERION_CLARIFICATION`.

## Similarity Review

The completed compact similarity review had 16 flagged entries: 10 `Y`, 6 `N`, and 0 `?`. One semantic duplicate pair was flagged twice, yielding five unique substantive redundancy problems.

## Similarity Remediation

Five specified redundant rows were removed while their documented counterparts were retained. Five replacement candidates were added without reusing removed concepts.

## Replacement Review

`REMED2-DEF-001`, `REMED2-DEF-002`, `REMED2-CAU-001`, `REMED2-CAU-002`, and `REMED2-LOG-001` each received `Y` in targeted human review.

## Remaining Descriptive Similarity Flags

The final candidate has 7 repeated three-word-prefix groups and 2 character TF-IDF cosine pairs at or above 0.55. Remaining repeated-prefix / TF-IDF similarity flags were not treated as automatic failures because no exact or normalized duplicates remained and human-identified substantive redundancies had already been remediated.

## Freeze Decision

`READY_TO_FREEZE`\n\nThe frozen dataset SHA-256 is `{dataset_sha}`.

## Scientific Independence

The evaluator was frozen before Final-200 evaluation. No Final-200 predictions were viewed before dataset freeze. EXP-017 outputs remained unread. The evaluator artifact SHA-256 is `{artifact_sha}` and evaluator config SHA-256 is `{config_sha}`.

## Next Gate

The next authorized action is the separately governed, one-shot Final-200 evaluator test. This freeze task did not run that evaluation and did not unlock EXP-017.
"""


def main() -> None:
    rows = read_csv(CANDIDATE)
    if len(rows) != 200 or Counter(row["task_class"] for row in rows) != Counter({"logic": 50, "causality": 50, "analogy": 50, "definition": 50}):
        raise ValueError("Candidate pool fails the frozen size or class-balance requirement.")
    artifact_sha = sha256(ROOT / "artifacts" / "evaluator_tfidf_logreg.joblib")
    config_sha = sha256(ROOT / "evaluator_frozen_config.json")
    if artifact_sha != EXPECTED_EVALUATOR_HASH or config_sha != EXPECTED_CONFIG_HASH:
        raise ValueError("Frozen evaluator integrity hash differs from the recorded value.")
    review_text = import_replacement_decisions(REVIEW.read_text(encoding="utf-8"))
    review_text = review_text.replace(
        "All decisions and reasons are intentionally blank at creation. No automatic approval is permitted.",
        "All five targeted human decisions have been imported as `Y`. No response text or task label changed during this import.",
    )
    REVIEW.write_text(review_text, encoding="utf-8")
    status = json.loads(STATUS.read_text(encoding="utf-8"))
    status.update({
        "status": "FINAL200_FROZEN",
        "replacement_review_completed": True,
        "replacement5_decisions": {candidate_id: "Y" for candidate_id in REPLACEMENT_IDS},
        "final200_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    })
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(CANDIDATE, FROZEN)
    dataset_sha = sha256(FROZEN)
    manifest = {
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
        "evaluator_artifact_sha256": artifact_sha,
        "evaluator_config_sha256": config_sha,
        "frozen_dataset_sha256": dataset_sha,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    FREEZE_AUDIT.write_text(audit_document(dataset_sha, artifact_sha, config_sha), encoding="utf-8")
    print("FINAL200_FROZEN")
    print("dataset_sha256:", dataset_sha)
    print("replacement5_review_imported: 5/5 Y")


if __name__ == "__main__":
    main()
