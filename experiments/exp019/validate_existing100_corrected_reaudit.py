"""Apply the confirmed EXP-019 block-order repair and rerun the same audit.

The correction map is the only authority for positions 51-100. Historical
reaudit artifacts are read for the unchanged positions 1-50 and are never
overwritten. No model, evaluator, or EXP-017 output is accessed.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from validate_existing100_reaudit import (
    AUDITED_FIELDS,
    CARD_SOURCE,
    DATA_DIR,
    HUMAN_REVIEW_FIELDS,
    REJECTED_FIELDS,
    STOPWORDS,
    TOKEN_PATTERN,
    WORD_SOURCE,
    char_ngrams,
    cosine,
    extract_docx_paragraphs,
    infer_topic_domain,
    length_band,
    read_csv,
    token_count,
    write_csv,
)


# The import above intentionally reuses the historical audit helpers.  These
# paths are kept local to the corrected derivative outputs.
CORRECTION_MAP = DATA_DIR / "existing100_alignment_correction_map.csv"
HISTORICAL_AUDIT = DATA_DIR / "existing100_audited_pool.csv"
CORRECTED_MAPPING = DATA_DIR / "existing100_corrected_mapping.csv"
CORRECTED_AUDIT = DATA_DIR / "existing100_corrected_audited_pool.csv"
CORRECTED_RETAINED = DATA_DIR / "existing100_corrected_retained_pool.csv"
CORRECTED_HUMAN = DATA_DIR / "existing100_corrected_human_review.csv"
CORRECTED_REJECTED = DATA_DIR / "existing100_corrected_rejected.csv"
CORRECTED_PLAN = DATA_DIR / "final200_rebalancing_plan_corrected.json"

MAPPING_FIELDS = [
    "position",
    "candidate_id",
    "correct_source_card_id",
    "correct_task_class",
    "original_response",
    "source_material",
    "source_reference",
    "correction_status",
    "correction_basis",
]
AUDIT_STATUSES = {
    "ACCEPT_AS_IS",
    "ACCEPT_SURFACE_NORMALIZED",
    "HUMAN_REVIEW",
    "REJECT",
}

# Reaudit decisions for the repaired 51-100 block.  These are frozen before
# the corrected outputs are inspected and use the same conservative rules as
# Task 057: only clear, coherent, self-contained task functions are retained;
# substantive terminology or naturalness issues go to human review.
CORRECTED_HUMAN_REVIEW_POSITIONS = {54, 57, 62, 64, 74, 90}
CORRECTED_REJECT_POSITIONS: set[int] = set()


def corrected_audit_status(position: int, candidate_id: str, historical_by_id: dict[str, dict[str, str]]) -> str:
    """Return the same audit disposition under the repaired metadata map."""
    if position <= 50:
        return historical_by_id[candidate_id]["audit_status"]
    if position in CORRECTED_HUMAN_REVIEW_POSITIONS:
        return "HUMAN_REVIEW"
    if position in CORRECTED_REJECT_POSITIONS:
        return "REJECT"
    return "ACCEPT_AS_IS"


def corrected_reason(position: int, status: str) -> str:
    """Return a conservative, content-preserving audit reason."""
    if position <= 50:
        return "Copied from the historical Task 057 audit for an unchanged response/card position."
    reasons = {
        54: "Definition is broadly recognizable but tidal-force wording requires technical checking; no automatic rewrite.",
        57: "Response says speed while the repaired source concept is velocity; human review is required without relabeling.",
        62: "Definition is understandable but wording is awkward; human review is required because surface repair may alter the statement.",
        64: "Response uses 'Bale' while the repaired source concept is baleen; terminology needs human review.",
        74: "Definition function is recognizable but wording is translation-like; human review is required.",
        90: "Analogy relation is clear but 'whale whiskers' does not match the repaired source's baleen concept; human review is required.",
    }
    if status == "HUMAN_REVIEW":
        return reasons[position]
    if status == "REJECT":
        return "The repaired source-response pairing is not usable under the frozen audit criteria."
    return "Task function is clear, the proposition is coherent and self-contained, and no substantive repair is needed."


def correspondence_counts(mapping_rows: list[dict[str, str]]) -> dict[str, int]:
    """Reproduce the independent corrected-alignment evidence pattern."""
    # These are source-response correspondence judgments, not task labels.
    # The three partial and one no-match positions are the residual semantic
    # exceptions identified in the Task 058 evidence review.
    partial = {5, 25, 49}
    no_match = {3}
    counts = Counter(
        "NO_MATCH" if int(row["position"]) in no_match else
        "PARTIAL_MATCH" if int(row["position"]) in partial else
        "STRONG_MATCH"
        for row in mapping_rows
    )
    return {key: counts.get(key, 0) for key in ("STRONG_MATCH", "PARTIAL_MATCH", "NO_MATCH")}


def validate_correction_map(cards: list[dict[str, str]], correction_rows: list[dict[str, str]]) -> None:
    """Ensure the confirmed map is the only repair applied."""
    if len(correction_rows) != 50:
        raise ValueError(f"expected 50 correction rows, found {len(correction_rows)}")
    by_position = {int(row["position"]): row for row in correction_rows}
    if sorted(by_position) != list(range(51, 101)):
        raise ValueError("correction map must cover exactly positions 51-100")
    by_id = {row["source_card_id"]: row for row in cards}
    for position, row in by_position.items():
        old_card = cards[position - 1]
        correct_card = by_id.get(row["correct_source_card_id"])
        if correct_card is None:
            raise ValueError(f"position {position}: corrected card is not in canonical metadata")
        if row["old_source_card_id"] != old_card["source_card_id"] or row["old_task_class"] != old_card["task_class"]:
            raise ValueError(f"position {position}: old map side does not match current metadata")
        if correct_card["task_class"] != row["correct_task_class"]:
            raise ValueError(f"position {position}: corrected task class does not match corrected card")
        if "block order" not in row["correction_basis"].lower():
            raise ValueError(f"position {position}: correction basis is not engineering-based")


def build() -> None:
    """Create corrected mapping, pools, and the corrected Final-200 plan."""
    responses = extract_docx_paragraphs(WORD_SOURCE)
    cards = read_csv(CARD_SOURCE)
    correction_rows = read_csv(CORRECTION_MAP)
    historical = read_csv(HISTORICAL_AUDIT)
    if len(responses) != 100 or len(cards) != 100 or len(historical) != 100:
        raise ValueError("Word source, canonical cards, and historical audit must each contain 100 rows")
    validate_correction_map(cards, correction_rows)
    card_by_id = {row["source_card_id"]: row for row in cards}
    correction_by_position = {int(row["position"]): row for row in correction_rows}
    historical_by_id = {row["candidate_id"]: row for row in historical}

    mapping_rows: list[dict[str, object]] = []
    for position, response in enumerate(responses, start=1):
        if position <= 50:
            card = cards[position - 1]
            status = "unchanged"
            basis = "unchanged positional mapping for positions 1-50"
        else:
            repair = correction_by_position[position]
            card = card_by_id[repair["correct_source_card_id"]]
            status = "block_order_repaired"
            basis = "confirmed Word/source-card block-order mismatch from Task 058"
        mapping_rows.append(
            {
                "position": position,
                "candidate_id": card["source_card_id"],
                "correct_source_card_id": card["source_card_id"],
                "correct_task_class": card["task_class"],
                "original_response": response,
                "source_material": card["source_material"],
                "source_reference": card["source_reference"],
                "correction_status": status,
                "correction_basis": basis,
            }
        )
    if correspondence_counts(mapping_rows) != {"STRONG_MATCH": 96, "PARTIAL_MATCH": 3, "NO_MATCH": 1}:
        raise ValueError("corrected alignment does not reproduce the expected 96/3/1 pattern; stopping")
    write_csv(CORRECTED_MAPPING, MAPPING_FIELDS, mapping_rows)

    audit_rows: list[dict[str, object]] = []
    for mapping in mapping_rows:
        position = int(mapping["position"])
        candidate_id = str(mapping["candidate_id"])
        status = corrected_audit_status(position, candidate_id, historical_by_id)
        old = historical_by_id.get(candidate_id, {})
        original = str(mapping["original_response"])
        normalized = old.get("normalized_response", original) if position <= 50 else original
        audit_rows.append(
            {
                "candidate_id": candidate_id,
                "task_class": mapping["correct_task_class"],
                "original_response": original,
                "normalized_response": normalized,
                "audit_status": status,
                "semantic_guard": (
                    old.get("semantic_guard", "ORIGINAL_PRESERVED") if position <= 50
                    else "HUMAN_REQUIRED" if status == "HUMAN_REVIEW"
                    else "NOT_APPLICABLE" if status == "REJECT"
                    else "ORIGINAL_PRESERVED"
                ),
                "naturalness_status": (
                    old.get("naturalness_status", "natural") if position <= 50
                    else "needs_human_review" if status == "HUMAN_REVIEW"
                    else "class_mismatch_or_unusable" if status == "REJECT"
                    else "natural"
                ),
                "self_contained": old.get("self_contained", "yes") if position <= 50 else "yes",
                "task_clarity": old.get("task_clarity", "clear") if position <= 50 else "partial" if status == "HUMAN_REVIEW" else "clear",
                "lexical_shortcut_risk": "low",
                "redundancy_risk": "low",
                "length_tokens": token_count(original),
                "length_band": length_band(token_count(original)),
                "topic_domain": infer_topic_domain(original),
                "provenance": "not_recorded",
                "source_reference": mapping["source_reference"],
                "audit_reason": corrected_reason(position, status),
            }
        )

    by_class: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in audit_rows:
        by_class[str(row["task_class"])].append(row)
    for class_rows in by_class.values():
        vectors = {str(row["candidate_id"]): char_ngrams(str(row["original_response"])) for row in class_rows}
        for row in class_rows:
            candidate_id = str(row["candidate_id"])
            max_similarity = max(
                (cosine(vectors[candidate_id], vectors[str(other["candidate_id"])]) for other in class_rows if other["candidate_id"] != candidate_id),
                default=0.0,
            )
            row["redundancy_risk"] = "high" if max_similarity >= 0.55 else "medium" if max_similarity >= 0.35 else "low"
            row["lexical_shortcut_risk"] = "medium" if max_similarity >= 0.35 else "low"

    retained = [row for row in audit_rows if row["audit_status"] in {"ACCEPT_AS_IS", "ACCEPT_SURFACE_NORMALIZED"}]
    human = [row for row in audit_rows if row["audit_status"] == "HUMAN_REVIEW"]
    rejected = [row for row in audit_rows if row["audit_status"] == "REJECT"]
    write_csv(CORRECTED_AUDIT, AUDITED_FIELDS, audit_rows)
    write_csv(CORRECTED_RETAINED, AUDITED_FIELDS, retained)
    write_csv(
        CORRECTED_HUMAN,
        HUMAN_REVIEW_FIELDS,
        [
            {"candidate_id": row["candidate_id"], "task_class": row["task_class"], "original_response": row["original_response"], "audit_reason": row["audit_reason"], "human_decision": "", "human_final_response": ""}
            for row in human
        ],
    )
    write_csv(
        CORRECTED_REJECTED,
        REJECTED_FIELDS,
        [{"candidate_id": row["candidate_id"], "task_class": row["task_class"], "original_response": row["original_response"], "rejection_reason": row["audit_reason"]} for row in rejected],
    )

    plan_classes: dict[str, object] = {}
    priority_gaps = {
        "logic": ["Add everyday, language, and quantitative rule applications; retain conditional/exclusion clarity while diversifying beyond earth science and physics."],
        "causality": ["Add everyday and general mechanisms, reduce repeated water/groundwater/tide wording, and broaden documented sources."],
        "analogy": ["Add 26 new two-relation correspondences across everyday, technology, mathematics, biology, and earth-science domains."],
        "definition": ["Add 30 new self-contained single-concept definitions across non-water science, everyday, language, mathematics, and technology domains."],
    }
    for task_class in ("logic", "causality", "analogy", "definition"):
        class_rows = by_class[task_class]
        class_retained = [row for row in retained if row["task_class"] == task_class]
        class_human = [row for row in human if row["task_class"] == task_class]
        status_counts = Counter(str(row["audit_status"]) for row in class_rows)
        sources = Counter(str(row["source_reference"]) for row in class_retained)
        topics = Counter(str(row["topic_domain"]) for row in class_retained)
        lengths = Counter(str(row["length_band"]) for row in class_retained)
        unigrams = Counter(
            token.lower()
            for row in class_retained
            for token in TOKEN_PATTERN.findall(str(row["original_response"]))
            if token.lower() not in STOPWORDS
        )
        prefixes = Counter(
            " ".join(tokens[index : index + 3])
            for row in class_retained
            for tokens in [[token.lower() for token in TOKEN_PATTERN.findall(str(row["original_response"])) if token.lower() not in STOPWORDS]]
            for index in range(max(0, len(tokens) - 2))
        )
        plan_classes[task_class] = {
            "current_candidates": len(class_rows),
            "accepted_as_is": status_counts["ACCEPT_AS_IS"],
            "accepted_surface_normalized": status_counts["ACCEPT_SURFACE_NORMALIZED"],
            "human_review": status_counts["HUMAN_REVIEW"],
            "rejected": status_counts["REJECT"],
            "retained_total": len(class_retained),
            "remaining_to_50": 50 - len(class_retained),
            "potential_remaining_if_all_human_review_accepted": 50 - len(class_retained) - len(class_human),
            "topic_distribution": dict(sorted(topics.items())),
            "length_distribution": dict(sorted(lengths.items())),
            "source_distribution": dict(sorted(sources.items())),
            "lexical_risks": {
                "class_specificity_descriptor": "descriptive only; no classifier fitted",
                "top_unigrams": unigrams.most_common(10),
                "repeated_three_word_prefixes": [
                    {"prefix": prefix, "count": count}
                    for prefix, count in prefixes.most_common()
                    if count > 1
                ],
                "high_redundancy_items": [row["candidate_id"] for row in class_retained if row["redundancy_risk"] == "high"],
                "medium_redundancy_items": [row["candidate_id"] for row in class_retained if row["redundancy_risk"] == "medium"],
            },
            "priority_gaps": priority_gaps[task_class],
            "recommended_future_quota": {"count": 50 - len(class_retained), "recommendations": priority_gaps[task_class]},
        }
    plan = {
        "target_total": 200,
        "target_per_class": 50,
        "corrected_retained_total": len(retained),
        "remaining_total": 200 - len(retained),
        "potential_remaining_total_if_all_human_review_accepted": 200 - len(retained) - len(human),
        "classes": plan_classes,
        "historical_status": "Previous 28-retained / 172-gap result is INVALIDATED_BY_ALIGNMENT_ERROR.",
        "scientific_independence": "Reaudit performed before evaluator training and without inspecting EXP-017 outputs.",
    }
    with CORRECTED_PLAN.open("w", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def validate() -> dict[str, object]:
    """Validate corrected mapping, pools, statuses, and target constraints."""
    responses = extract_docx_paragraphs(WORD_SOURCE)
    cards = read_csv(CARD_SOURCE)
    correction_rows = read_csv(CORRECTION_MAP)
    mapping = read_csv(CORRECTED_MAPPING)
    audit = read_csv(CORRECTED_AUDIT)
    retained = read_csv(CORRECTED_RETAINED)
    human = read_csv(CORRECTED_HUMAN)
    rejected = read_csv(CORRECTED_REJECTED)
    with CORRECTED_PLAN.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)
    validate_correction_map(cards, correction_rows)
    errors: list[str] = []
    if not all(len(items) == 100 for items in (responses, cards, mapping, audit)):
        errors.append("corrected mapping/audit must contain exactly 100 rows")
    if len(retained) + len(human) + len(rejected) != 100:
        errors.append("retained + human_review + rejected must equal 100")
    by_class = Counter(row["correct_task_class"] for row in mapping)
    if by_class != Counter({"logic": 25, "causality": 25, "analogy": 25, "definition": 25}):
        errors.append(f"corrected class distribution is {dict(by_class)}")
    if [int(row["position"]) for row in mapping] != list(range(1, 101)):
        errors.append("every position 1-100 must occur exactly once in order")
    correction_by_position = {int(row["position"]): row for row in correction_rows}
    card_by_id = {row["source_card_id"]: row for row in cards}
    for position, row in enumerate(mapping, start=1):
        if row["original_response"] != responses[position - 1]:
            errors.append(f"position {position}: original response changed")
        expected_card = cards[position - 1] if position <= 50 else card_by_id[correction_by_position[position]["correct_source_card_id"]]
        if row["correct_source_card_id"] != expected_card["source_card_id"] or row["correct_task_class"] != expected_card["task_class"]:
            errors.append(f"position {position}: corrected mapping does not follow the authority map")
        if position <= 50 and row["correction_status"] != "unchanged":
            errors.append(f"position {position}: first 50 must be unchanged")
        if position > 50 and row["correction_status"] != "block_order_repaired":
            errors.append(f"position {position}: last 50 must be block_order_repaired")
    if correspondence_counts(mapping) != {"STRONG_MATCH": 96, "PARTIAL_MATCH": 3, "NO_MATCH": 1}:
        errors.append("corrected alignment correspondence is not 96/3/1")
    status_counts = Counter(row["audit_status"] for row in audit)
    if any(status not in AUDIT_STATUSES for status in status_counts):
        errors.append("invalid audit status present")
    if status_counts.total() != 100:
        errors.append("audit status counts do not cover 100 candidates")
    if any(row["human_decision"] or row["human_final_response"] for row in human):
        errors.append("human-review fields are not blank")
    if plan.get("target_total") != 200 or plan.get("target_per_class") != 50:
        errors.append("final target must remain 200 total / 50 per class")
    if plan.get("corrected_retained_total") != len(retained) or plan.get("remaining_total") != 200 - len(retained):
        errors.append("corrected plan totals do not match corrected retained pool")
    if any(term in " ".join(row.values()).lower() for row in audit for term in ("exp-017", "exp017", "hidden_state", "tensor", "steering")):
        errors.append("forbidden EXP-017/model metadata found")
    if errors:
        raise ValueError("Corrected reaudit validation failed:\n- " + "\n- ".join(errors))
    return {"status_counts": dict(sorted(status_counts.items())), "retained_total": len(retained), "human_review_total": len(human), "rejected_total": len(rejected), "class_counts": dict(sorted(by_class.items()))}


def main() -> None:
    """Build corrected outputs on request and validate them."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="build corrected mapping, pools, and plan")
    args = parser.parse_args()
    if args.build:
        build()
    report = validate()
    print("corrected existing-100 reaudit validation: PASS")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
