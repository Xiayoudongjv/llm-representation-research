"""Apply only the three human-authorized EXP-019 logic replacements.

This creates a post-human-remediation candidate derivative. It never modifies
the locked source pool, trains/loads the evaluator, or reads EXP-017 outputs.
"""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from review_final200_human_audit import prepare_similarity_review


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
OUTPUT = DATA / "final200_post_human_remediation_candidate.csv"
LOG = DATA / "final200_logic_remediation_log.csv"
AUDIT = DATA / "final200_post_human_remediation_audit.json"
SIMILARITY = DATA / "final200_similarity_review_post_remediation.csv"
PACKET = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-LOGIC-REPLACEMENT3-HUMAN-REVIEW.md"
DOC = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-MINOR-REMEDIATION.md"
FAILED = ("GAP-LOG-036", "GAP-LOG-005", "GAP-LOG-003")
REPLACEMENTS = (
    {
        "candidate_id": "REMED-LOG-001",
        "task_class": "logic",
        "response_text": "If a number is divisible by four, it is even.",
        "provenance": "rule_composed",
        "source_reference": "rule_composed://human-audit-remediation",
        "topic_domain": "mathematics",
        "reasoning_structure": "conditional implication",
    },
    {
        "candidate_id": "REMED-LOG-002",
        "task_class": "logic",
        "response_text": "Nothing can be entirely north and entirely south of the same point.",
        "provenance": "rule_composed",
        "source_reference": "rule_composed://human-audit-remediation",
        "topic_domain": "spatial_reasoning",
        "reasoning_structure": "exclusion / contradiction",
    },
    {
        "candidate_id": "REMED-LOG-003",
        "task_class": "logic",
        "response_text": "If twelve equal shares are divided among three people, each person gets four shares.",
        "provenance": "rule_composed",
        "source_reference": "rule_composed://human-audit-remediation",
        "topic_domain": "mathematics",
        "reasoning_structure": "quantitative rule application",
    },
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text))


def length_band(count: int) -> str:
    if count <= 5:
        return "short"
    if count <= 12:
        return "medium"
    if count <= 20:
        return "limited_long"
    raise ValueError(f"Candidate length outside frozen policy: {count}")


def replacement_rows() -> list[dict[str, str]]:
    rows = []
    for source in REPLACEMENTS:
        count = token_count(source["response_text"])
        rows.append({
            "candidate_id": source["candidate_id"],
            "task_class": source["task_class"],
            "response_text": source["response_text"],
            "provenance": source["provenance"],
            "source_reference": source["source_reference"],
            "topic_domain": source["topic_domain"],
            "length_tokens": str(count),
            "length_band": length_band(count),
        })
    return rows


def review_packet(rows: list[dict[str, str]]) -> str:
    items = []
    for row in rows:
        items.append(
            f"## `{row['candidate_id']}`\n\n"
            f"**Response:** {row['response_text']}\n\n"
            "**Decision:**\n\n"
            "**Reason:**\n\n"
            "---\n"
        )
    return """# Logic Replacement Review

`Y` = valid Logic replacement
`N` = not valid
`?` = uncertain

For each response, judge only: **Does this response clearly perform Logic rather than merely state a fact?**

""" + "\n".join(items)


def main() -> None:
    locked = read_csv(LOCKED)
    locked_by_id = {row["candidate_id"]: row for row in locked}
    if set(FAILED) - set(locked_by_id):
        raise ValueError("An authorized removal ID is absent from the locked pool.")
    if any(locked_by_id[candidate_id]["task_class"] != "logic" for candidate_id in FAILED):
        raise ValueError("Authorized removals must all be logic rows.")
    replacements = replacement_rows()
    existing_normalized = {" ".join(row["response_text"].casefold().split()) for row in locked if row["candidate_id"] not in FAILED}
    replacement_normalized = [" ".join(row["response_text"].casefold().split()) for row in replacements]
    if len(set(replacement_normalized)) != 3 or any(text in existing_normalized for text in replacement_normalized):
        raise ValueError("Replacement exact/normalized duplication detected.")

    fields = list(locked[0])
    remediated = [dict(row) for row in locked if row["candidate_id"] not in FAILED] + replacements
    write_csv(OUTPUT, fields, remediated)
    write_csv(LOG, ["removed_candidate_id", "task_class", "response_text", "human_audit_source", "human_reason", "remediation_status"], [
        {"removed_candidate_id": candidate_id, "task_class": "logic", "response_text": locked_by_id[candidate_id]["response_text"], "human_audit_source": "Random-40 audit" if candidate_id in {"GAP-LOG-036", "GAP-LOG-005"} else "Logic-only spot-check", "human_reason": "HUMAN_LABEL_FUNCTION_MISMATCH", "remediation_status": "REPLACE"}
        for candidate_id in FAILED
    ])

    vector = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True)
    matrix = vector.fit_transform([row["response_text"] for row in remediated])
    similarity = cosine_similarity(matrix)
    prefixes = Counter(" ".join(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", row["response_text"].casefold())[:3]) for row in remediated)
    pairs, nearest = [], {}
    for left, row in enumerate(remediated):
        nearest[row["candidate_id"]] = round(max((float(similarity[left, right]) for right in range(len(remediated)) if right != left), default=0.0), 4)
        for right in range(left + 1, len(remediated)):
            if similarity[left, right] >= 0.55:
                pairs.append({"left": row["candidate_id"], "right": remediated[right]["candidate_id"], "tfidf_char_cosine": round(float(similarity[left, right]), 4)})
    texts = [" ".join(row["response_text"].casefold().split()) for row in remediated]
    audit = {
        "dataset_size": len(remediated),
        "class_counts": dict(Counter(row["task_class"] for row in remediated)),
        "length_min": min(int(row["length_tokens"]) for row in remediated),
        "length_max": max(int(row["length_tokens"]) for row in remediated),
        "exact_duplicates": len(texts) - len(set(texts)),
        "normalized_duplicates": len(texts) - len(set(texts)),
        "repeated_three_word_prefix_groups": {prefix: count for prefix, count in prefixes.items() if prefix and count > 1},
        "tfidf_char_similarity_pairs_at_least_0_55": pairs,
        "nearest_neighbor_maximum": max(nearest.values(), default=0.0),
        "evaluator_predictions_accessed": False,
        "exp017_outputs_accessed": False,
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    prepare_similarity_review(OUTPUT, SIMILARITY)
    PACKET.parent.mkdir(parents=True, exist_ok=True)
    PACKET.write_text(review_packet(replacements), encoding="utf-8")
    DOC.write_text("# EXP-019 Final-200 Minor Remediation\n\n"
                   "## Human Audit Finding\n\nThe Random-40 audit found two logic label-function mismatches.\n\n"
                   "## Logic Spot Check\n\nThe ten-item spot-check found one additional logic mismatch.\n\n"
                   "## Frozen Interpretation\n\n`LIKELY_ISOLATED_WITH_MINOR_RISK`\n\n"
                   "## Three Removed Candidates\n\n`GAP-LOG-036`, `GAP-LOG-005`, and `GAP-LOG-003` were removed only from the post-remediation candidate derivative.\n\n"
                   "## Replacement Construction Rules\n\nThree rule-composed logic responses use conditional implication, exclusion/contradiction, and quantitative rule application. Each is 4 to 20 tokens and receives no automatic approval.\n\n"
                   "## Replacement Review Requirement\n\nAll three replacements require targeted human review before any freeze.\n\n"
                   "## Updated Similarity Audit\n\nMechanical duplicate, prefix, and character-TF-IDF similarity checks were recomputed on the new derivative.\n\n"
                   "## Scientific Independence\n\nNo evaluator predictions were viewed. The evaluator was not retrained. EXP-017 remained locked.\n\n"
                   "## Freeze Status\n\n`MINOR_REMEDIATION_PENDING_REPLACEMENT_REVIEW`\n", encoding="utf-8")
    print("LOGIC_MINOR_REMEDIATION_COMPLETE")
    print("removed:", ",".join(FAILED))
    print("replacements:", ",".join(row["candidate_id"] for row in replacements))
    print("class_counts:", dict(Counter(row["task_class"] for row in remediated)))
    print("length_min_max:", audit["length_min"], audit["length_max"])
    print("prefix_groups:", len(audit["repeated_three_word_prefix_groups"]))
    print("tfidf_pairs:", len(pairs))


if __name__ == "__main__":
    main()
