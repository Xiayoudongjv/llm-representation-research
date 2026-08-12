"""Apply the five human-authorized EXP-019 similarity remediations.

The script writes a new candidate derivative only. It never modifies historical
audit files, trains or loads the evaluator, reads Final-200 predictions, or
accesses EXP-017.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SOURCE = DATA / "final200_post_human_remediation_candidate.csv"
OUTPUT = DATA / "final200_post_similarity_remediation_candidate.csv"
LOG = DATA / "final200_similarity_remediation_log.csv"
AUDIT = DATA / "final200_post_similarity_remediation_audit.json"
STATUS = DATA / "final200_similarity_remediation_status.json"
PACKET = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-REPLACEMENT5-HUMAN-REVIEW.md"
FREEZE_AUDIT = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-FREEZE-AUDIT.md"

REMOVALS = (
    {
        "removed_candidate_id": "GAP-DEF-025",
        "retained_counterpart_id": "SRC-DEF-002",
        "human_reason": "Near-duplicate definition of evaporation; only wording differs.",
    },
    {
        "removed_candidate_id": "GAP-CAU-014",
        "retained_counterpart_id": "SRC-CAU-006",
        "human_reason": "Near-duplicate photosynthesis energy-storage statement; only wording differs.",
    },
    {
        "removed_candidate_id": "GAP-CAU-023",
        "retained_counterpart_id": "SRC-CAU-009",
        "human_reason": "Near-duplicate stomata and water-loss statement; only wording differs.",
    },
    {
        "removed_candidate_id": "GAP-DEF-012",
        "retained_counterpart_id": "SRC-DEF-009",
        "human_reason": "Near-duplicate definition of force; only wording differs.",
    },
    {
        "removed_candidate_id": "GAP-LOG-033",
        "retained_counterpart_id": "GAP-CAU-017",
        "human_reason": "Semantic content is nearly identical and the cross-class task-function contrast is too weak; this was a human redundancy decision, not a classifier-driven decision.",
    },
)
REPLACEMENTS = (
    {
        "candidate_id": "REMED2-DEF-001",
        "task_class": "definition",
        "response_text": "A catalyst is a substance that speeds a chemical reaction without being consumed.",
        "provenance": "rule_composed",
        "topic_domain": "chemistry",
    },
    {
        "candidate_id": "REMED2-DEF-002",
        "task_class": "definition",
        "response_text": "An eclipse is an event in which one celestial body blocks light from another.",
        "provenance": "rule_composed",
        "topic_domain": "astronomy",
    },
    {
        "candidate_id": "REMED2-CAU-001",
        "task_class": "causality",
        "response_text": "Wind erodes bare soil by carrying loose particles away.",
        "provenance": "rule_composed",
        "topic_domain": "earth_science",
    },
    {
        "candidate_id": "REMED2-CAU-002",
        "task_class": "causality",
        "response_text": "Cooling magma causes it to solidify into igneous rock.",
        "provenance": "rule_composed",
        "topic_domain": "earth_science",
    },
    {
        "candidate_id": "REMED2-LOG-001",
        "task_class": "logic",
        "response_text": "If a quantity is greater than seven, it cannot be less than five.",
        "provenance": "rule_composed",
        "topic_domain": "quantitative_reasoning",
    },
)
EXPECTED_EVALUATOR_HASH = "DF06E7683627F308330E77E8A50D35766F3CA50F5C8DE873E077092DEAEB2BDD"
EXPECTED_CONFIG_HASH = "EB673B63CB0C407C04F55F9B5F8FB687C7BD680FC5B53DDD4CC18A2BCC906744"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text.casefold())


def normal(text: str) -> str:
    return " ".join(text.casefold().split())


def count_tokens(text: str) -> int:
    return len(words(text))


def length_band(count: int) -> str:
    if count <= 5:
        return "short"
    if count <= 12:
        return "medium"
    if count <= 20:
        return "limited_long"
    raise ValueError("Replacement exceeds frozen maximum length.")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def similarity(rows: list[dict[str, str]]) -> tuple[list[tuple[str, list[str]]], list[tuple[str, str, float]], float]:
    prefix_groups: defaultdict[str, list[str]] = defaultdict(list)
    for row in rows:
        prefix = " ".join(words(row["response_text"])[:3])
        if prefix:
            prefix_groups[prefix].append(row["candidate_id"])
    repeated = sorted((prefix, ids) for prefix, ids in prefix_groups.items() if len(ids) > 1)
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True)
    matrix = vectorizer.fit_transform([row["response_text"] for row in rows])
    values = cosine_similarity(matrix)
    pairs: list[tuple[str, str, float]] = []
    maximum = 0.0
    for left, row in enumerate(rows):
        for right in range(left + 1, len(rows)):
            value = float(values[left, right])
            maximum = max(maximum, value)
            if value >= 0.55:
                pairs.append((row["candidate_id"], rows[right]["candidate_id"], round(value, 4)))
    return repeated, pairs, round(maximum, 4)


def review_packet(rows: list[dict[str, str]]) -> str:
    items = []
    for row in rows:
        items.append(
            f"## `{row['candidate_id']}`\n\n"
            f"**Class:** {row['task_class']}\n\n"
            f"**Response:** {row['response_text']}\n\n"
            "**Decision:**\n\n"
            "**Reason:**\n\n"
            "---\n"
        )
    return """# EXP-019 Five Similarity-Remediation Replacements

For each replacement, judge only:

1. Is the frozen task function correct?
2. Is the response not substantially redundant with the retained set?

`Y` = valid and sufficiently distinct; `N` = invalid or substantially redundant; `?` = uncertain.

All decisions and reasons are intentionally blank at creation. No automatic approval is permitted.

""" + "\n".join(items)


def freeze_audit_document(audit: dict[str, object]) -> str:
    return f"""# EXP-019 Final-200 Freeze Audit

## Human Audit History

The completed Random-40 audit recorded 38 `Y`, 2 `N`, and 0 uncertain judgments. The Logic spot-check recorded 9 `Y` and 1 `N`. Three approved Logic replacements were then added under the frozen operational definition.

## Human Similarity Review

Six of sixteen flagged entries were judged `N`; because one semantic duplicate was flagged twice, this yielded five unique human-identified redundancy problems. The five specified rows were removed while their stated counterparts were retained. `GAP-LOG-033` was removed because its semantic content was nearly identical to `GAP-CAU-017` and the cross-class task-function contrast was too weak. This was not classifier-driven.

## Five Replacement Candidates

`REMED2-DEF-001`, `REMED2-DEF-002`, `REMED2-CAU-001`, `REMED2-CAU-002`, and `REMED2-LOG-001` are new rule-composed candidates for targeted human review. They do not reuse the removed concepts.

## Mechanical Audit

The new 200-row candidate has {audit['exact_duplicates']} exact duplicates, {audit['normalized_duplicates']} normalized duplicates, {audit['repeated_three_word_prefix_group_count']} repeated three-word-prefix groups, and {audit['high_similarity_pair_count']} character TF-IDF pairs at or above 0.55. Maximum nearest-neighbor similarity is {audit['maximum_nearest_neighbor_similarity']:.4f}.

## Stop Rule

If all five replacements receive `Y` and no exact or normalized duplicate exists, the status becomes `READY_TO_FREEZE_PENDING_FINAL_VALIDATION`. If any replacement receives `N` or `?`, replace only that specific item. Do not start another Random-40 audit or reopen accepted items unless a new exact or normalized duplicate is introduced.

## Current Freeze Status

`REPLACEMENT5_REVIEW_PENDING`

## Scientific Independence

The evaluator remains frozen and unchanged. Final-200 predictions were not viewed. EXP-017 remains unread and locked.
"""


def main() -> None:
    source_rows = read_csv(SOURCE)
    source_by_id = {row["candidate_id"]: row for row in source_rows}
    removal_ids = {entry["removed_candidate_id"] for entry in REMOVALS}
    if len(source_rows) != 200 or removal_ids - set(source_by_id):
        raise ValueError("Source pool is missing an authorized redundancy removal.")
    expected_classes = {"GAP-DEF-025": "definition", "GAP-CAU-014": "causality", "GAP-CAU-023": "causality", "GAP-DEF-012": "definition", "GAP-LOG-033": "logic"}
    if any(source_by_id[candidate_id]["task_class"] != task_class for candidate_id, task_class in expected_classes.items()):
        raise ValueError("Removal class does not match the authorized plan.")
    retained_texts = {normal(row["response_text"]) for row in source_rows if row["candidate_id"] not in removal_ids}
    replacement_rows = []
    for item in REPLACEMENTS:
        token_total = count_tokens(item["response_text"])
        if not 4 <= token_total <= 20 or normal(item["response_text"]) in retained_texts:
            raise ValueError("Replacement violates length or duplicate rules.")
        replacement_rows.append({
            "candidate_id": item["candidate_id"],
            "task_class": item["task_class"],
            "response_text": item["response_text"],
            "provenance": item["provenance"],
            "source_reference": "rule_composed://similarity-remediation",
            "topic_domain": item["topic_domain"],
            "length_tokens": str(token_total),
            "length_band": length_band(token_total),
        })
    if len({normal(row["response_text"]) for row in replacement_rows}) != len(replacement_rows):
        raise ValueError("Replacement-to-replacement duplicate detected.")
    rows = [dict(row) for row in source_rows if row["candidate_id"] not in removal_ids] + replacement_rows
    fields = list(source_rows[0])
    write_csv(OUTPUT, fields, rows)
    log_rows = [{
        "removed_candidate_id": entry["removed_candidate_id"],
        "retained_counterpart_id": entry["retained_counterpart_id"],
        "task_class": source_by_id[entry["removed_candidate_id"]]["task_class"],
        "removed_response_text": source_by_id[entry["removed_candidate_id"]]["response_text"],
        "human_reason": entry["human_reason"],
        "remediation_status": "REPLACE",
    } for entry in REMOVALS]
    write_csv(LOG, list(log_rows[0]), log_rows)
    repeated, pairs, maximum = similarity(rows)
    exact_texts = [row["response_text"] for row in rows]
    normalized_texts = [normal(text) for text in exact_texts]
    evaluator_hash = sha256(ROOT / "artifacts" / "evaluator_tfidf_logreg.joblib")
    config_hash = sha256(ROOT / "evaluator_frozen_config.json")
    audit = {
        "dataset_size": len(rows),
        "class_counts": dict(Counter(row["task_class"] for row in rows)),
        "length_min": min(int(row["length_tokens"]) for row in rows),
        "length_max": max(int(row["length_tokens"]) for row in rows),
        "exact_duplicates": len(exact_texts) - len(set(exact_texts)),
        "normalized_duplicates": len(normalized_texts) - len(set(normalized_texts)),
        "repeated_three_word_prefix_group_count": len(repeated),
        "high_similarity_pair_count": len(pairs),
        "maximum_nearest_neighbor_similarity": maximum,
        "evaluator_artifact_sha256": evaluator_hash,
        "evaluator_config_sha256": config_hash,
        "evaluator_unchanged": evaluator_hash == EXPECTED_EVALUATOR_HASH and config_hash == EXPECTED_CONFIG_HASH,
        "final200_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    }
    status = {
        "status": "REPLACEMENT5_REVIEW_PENDING",
        "stop_rule": "All five replacements Y plus no exact/normalized duplicates -> READY_TO_FREEZE_PENDING_FINAL_VALIDATION; any N/? -> replace only that item.",
        "replacement_review_completed": False,
        "evaluator_unchanged": audit["evaluator_unchanged"],
        "final200_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    PACKET.write_text(review_packet(replacement_rows), encoding="utf-8")
    FREEZE_AUDIT.write_text(freeze_audit_document(audit), encoding="utf-8")
    print("SIMILARITY_REMEDIATION_CREATED")
    print("removed:", ",".join(sorted(removal_ids)))
    print("replacements:", ",".join(row["candidate_id"] for row in replacement_rows))
    print("class_counts:", dict(Counter(row["task_class"] for row in rows)))
    print("length_min_max:", audit["length_min"], audit["length_max"])
    print("repeated_prefix_groups:", len(repeated))
    print("high_similarity_pairs:", len(pairs))
    print("maximum_nearest_neighbor_similarity:", maximum)
    print("freeze_status:", status["status"])


if __name__ == "__main__":
    main()
