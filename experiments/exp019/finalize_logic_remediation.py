"""Finalize approved logic replacements and prepare the pending similarity gate.

This script never loads or retrains the evaluator, reads Final-200 predictions,
or accesses EXP-017. It does not modify the locked pre-human-audit pool.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
POOL = DATA / "final200_post_human_remediation_candidate.csv"
AUDIT = DATA / "final200_post_human_remediation_audit.json"
STATUS = DATA / "final200_logic_remediation_final_status.json"
PACKET = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-LOGIC-REPLACEMENT3-HUMAN-REVIEW.md"
SIMILARITY_PACKET = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-SIMILARITY-REVIEW.md"
FREEZE_AUDIT = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-FREEZE-AUDIT.md"

REPLACEMENTS = {
    "REMED-LOG-001": "If a number is divisible by four, it is even.",
    "REMED-LOG-002": "Nothing can be entirely north and entirely south of the same point.",
    "REMED-LOG-003": "If twelve equal shares are divided among three people, each person gets four shares.",
}
CLARIFICATION = (
    "Initial rejection used an overly narrow premise-conclusion criterion. "
    "The frozen operational definition also includes exclusion and contradiction, "
    "so this item is valid under the preregistered Logic definition."
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text.casefold())


def normalized(text: str) -> str:
    return " ".join(text.casefold().split())


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_similarity_flags(rows: list[dict[str, str]]) -> tuple[list[tuple[str, list[dict[str, str]]]], list[tuple[dict[str, str], dict[str, str], float]], float]:
    groups: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        prefix = " ".join(words(row["response_text"])[:3])
        if prefix:
            groups[prefix].append(row)
    prefix_flags = sorted((prefix, members) for prefix, members in groups.items() if len(members) > 1)

    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True)
    matrix = vectorizer.fit_transform([row["response_text"] for row in rows])
    similarity = cosine_similarity(matrix)
    high_pairs: list[tuple[dict[str, str], dict[str, str], float]] = []
    maximum = 0.0
    for left, left_row in enumerate(rows):
        for right in range(left + 1, len(rows)):
            value = float(similarity[left, right])
            maximum = max(maximum, value)
            if value >= 0.55:
                high_pairs.append((left_row, rows[right], value))
    return prefix_flags, high_pairs, maximum


def replacement_packet() -> str:
    blocks = []
    for candidate_id, text in REPLACEMENTS.items():
        reason = CLARIFICATION if candidate_id == "REMED-LOG-002" else "Approved under the frozen Logic operational definition."
        blocks.append(
            f"## `{candidate_id}`\n\n"
            f"**Response:** {text}\n\n"
            "**Decision:** Y\n\n"
            f"**Reason:** {reason}\n\n"
            "---\n"
        )
    return """# Logic Replacement Review

All three decisions are final under the frozen Logic operational definition.
No response text or task label was changed during this decision update.

""" + "\n".join(blocks)


def similarity_packet(prefix_flags: list[tuple[str, list[dict[str, str]]]], high_pairs: list[tuple[dict[str, str], dict[str, str], float]]) -> str:
    blocks = [
        "# EXP-019 Final-200 Similarity Review\n",
        "This compact packet contains only mechanically flagged pairs or repeated-prefix groups.\n",
        "`Y` = distinct enough; `N` = substantially redundant; `?` = uncertain.\n",
        "All Decision and Reason fields are intentionally blank.\n",
    ]
    index = 1
    for prefix, members in prefix_flags:
        for left, right in zip(members, members[1:]):
            blocks.append(
                f"## {index:02d} - repeated three-word prefix\n\n"
                f"**ID A:** `{left['candidate_id']}`\n\n**Text A:** {left['response_text']}\n\n"
                f"**ID B:** `{right['candidate_id']}`\n\n**Text B:** {right['response_text']}\n\n"
                f"**Flag type:** repeated three-word prefix (`{prefix}`)\n\n**Decision:**\n\n**Reason:**\n\n---\n"
            )
            index += 1
    for left, right, value in high_pairs:
        blocks.append(
            f"## {index:02d} - char TF-IDF similarity\n\n"
            f"**ID A:** `{left['candidate_id']}`\n\n**Text A:** {left['response_text']}\n\n"
            f"**ID B:** `{right['candidate_id']}`\n\n**Text B:** {right['response_text']}\n\n"
            f"**Flag type:** char TF-IDF cosine >= 0.55\n\n**Similarity score:** {value:.4f}\n\n"
            "**Decision:**\n\n**Reason:**\n\n---\n"
        )
        index += 1
    return "\n".join(blocks)


def freeze_audit_document(prefix_count: int, pair_count: int, maximum: float) -> str:
    return f"""# EXP-019 Final-200 Freeze Audit

## Random-40 Audit

The completed random audit recorded 38 `Y`, 2 `N`, and 0 uncertain judgments. Both Random-40 mismatches were in Logic.

## Logic Spot Check

The ten-item Logic spot-check recorded 9 `Y` and 1 `N`, identifying one additional Logic mismatch.

## Logic Remediation

`GAP-LOG-036`, `GAP-LOG-005`, and `GAP-LOG-003` were replaced only in the post-human-remediation candidate pool by `REMED-LOG-001`, `REMED-LOG-002`, and `REMED-LOG-003`. All three replacements are approved `Y`.

## REVIEW_CRITERION_CLARIFICATION

`REMED-LOG-002` was initially rejected using an overly narrow premise-conclusion criterion. The frozen Logic operational definition already includes exclusion and contradiction, so the item is valid under the preregistered Logic definition. This records a criterion clarification, not a post-hoc label relaxation.

## Final Mechanical Similarity Audit

The remediated 200-row pool has {prefix_count} repeated three-word-prefix groups, {pair_count} character TF-IDF cosine pairs at or above 0.55, and maximum nearest-neighbor character TF-IDF cosine {maximum:.4f}. The compact human review packet contains only those flags.

## Freeze Decision

`SIMILARITY_REVIEW_PENDING`

No similarity judgments have been entered in the compact review packet. Final-200 must not be frozen until that review is complete and does not identify a systematic redundancy problem.

## Scientific Independence

The evaluator remains frozen and unchanged. Final-200 predictions were not viewed. EXP-017 remains unread and locked.
"""


def main() -> None:
    rows = read_csv(POOL)
    by_id = {row["candidate_id"]: row for row in rows}
    if len(rows) != 200 or set(REPLACEMENTS) - set(by_id):
        raise ValueError("Post-remediation pool is absent or does not contain all replacements.")
    if any(by_id[candidate_id]["response_text"] != text for candidate_id, text in REPLACEMENTS.items()):
        raise ValueError("A replacement response text has changed.")
    prefix_flags, high_pairs, maximum = build_similarity_flags(rows)
    exact_texts = [row["response_text"] for row in rows]
    normalized_texts = [normalized(text) for text in exact_texts]
    audit = {
        "dataset_size": len(rows),
        "class_counts": dict(Counter(row["task_class"] for row in rows)),
        "length_min": min(int(row["length_tokens"]) for row in rows),
        "length_max": max(int(row["length_tokens"]) for row in rows),
        "exact_duplicates": len(exact_texts) - len(set(exact_texts)),
        "normalized_duplicates": len(normalized_texts) - len(set(normalized_texts)),
        "repeated_three_word_prefix_group_count": len(prefix_flags),
        "high_similarity_pair_count": len(high_pairs),
        "maximum_nearest_neighbor_similarity": round(maximum, 4),
        "similarity_review_status": "SIMILARITY_REVIEW_PENDING",
        "evaluator_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    }
    status = {
        "logic_remediation_status": "COMPLETE",
        "replacement_decisions": {candidate_id: "Y" for candidate_id in REPLACEMENTS},
        "REVIEW_CRITERION_CLARIFICATION": CLARIFICATION,
        "similarity_review_status": "SIMILARITY_REVIEW_PENDING",
        "evaluator_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    }
    write_json(AUDIT, audit)
    write_json(STATUS, status)
    PACKET.write_text(replacement_packet(), encoding="utf-8")
    SIMILARITY_PACKET.write_text(similarity_packet(prefix_flags, high_pairs), encoding="utf-8")
    FREEZE_AUDIT.write_text(freeze_audit_document(len(prefix_flags), len(high_pairs), maximum), encoding="utf-8")
    print("LOGIC_REMEDIATION_FINALIZED")
    print("replacement_decisions: REMED-LOG-001=Y, REMED-LOG-002=Y, REMED-LOG-003=Y")
    print("repeated_prefix_groups:", len(prefix_flags))
    print("high_similarity_pairs:", len(high_pairs))
    print("maximum_nearest_neighbor_similarity:", f"{maximum:.4f}")
    print("freeze_status: SIMILARITY_REVIEW_PENDING")


if __name__ == "__main__":
    main()
