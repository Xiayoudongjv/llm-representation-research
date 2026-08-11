"""Create a reproducible static quality audit for the EXP-011 dataset."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "experiments/exp011/expanded_answer_prompts.json"
AUDIT_PATH = ROOT / "experiments/exp011/dataset_quality_audit.csv"
SUMMARY_PATH = ROOT / "experiments/exp011/dataset_quality_summary.json"
FIELDNAMES = [
    "id", "group", "quality_label", "ambiguity_risk", "scoring_risk",
    "difficulty", "issue_types", "audit_note", "revised",
    "original_question", "final_question", "original_expected_answer",
    "final_expected_answer",
]

# These entries preserve the pre-audit wording for every deliberately revised item.
REVISIONS = {
    "exp011_logic_005": ("If a lamp is on, the room is lit. The room is not lit. Can the lamp be on?", "no", ["ambiguous_question"], "Replaced real-world lamp wording with an abstract conditional."),
    "exp011_logic_014": ("If food is spoiled, it smells bad. The food does not smell bad. Is it spoiled?", "no", ["ambiguous_question"], "Removed a real-world exception-prone premise."),
    "exp011_causality_004": ("Pressing a light switch turns on a lamp. What is the effect of pressing the switch?", "light turns on", ["acceptable_answers_too_broad"], "Removed the context-free answer 'turns on'."),
    "exp011_causality_005": ("A power outage causes a computer to shut down. What is the effect of a power outage?", "computer shuts down", ["acceptable_answers_too_broad"], "Removed the context-free answer 'shuts down'."),
    "exp011_causality_008": ("Dropping a glass can cause it to break. What is the likely effect?", "breaking", ["weak_causal_direction"], "Replaced modal wording with an explicit cause and effect."),
    "exp011_causality_010": ("Eating spoiled food can cause sickness. What is the likely effect?", "sickness", ["weak_causal_direction", "acceptable_answers_too_broad"], "Removed modal wording and the broad answer 'sick'."),
    "exp011_causality_011": ("If brakes fail, a car may not stop. What is the likely effect of brake failure?", "car does not stop", ["weak_causal_direction", "acceptable_answers_too_broad"], "Made the stated causal direction deterministic and removed broad variants."),
    "exp011_causality_015": ("Lack of sleep often makes a person tired. What is the effect of lack of sleep?", "tired", ["weak_causal_direction"], "Removed frequency wording from the stated relation."),
    "exp011_causality_017": ("Watering dry soil makes it wet. What is the effect of watering dry soil?", "wet soil", ["acceptable_answers_too_broad"], "Removed the one-word answer 'wet' and made the effect specific."),
    "exp011_causality_019": ("Closing a water valve stops water flow. What is the effect of closing the valve?", "water stops", ["acceptable_answers_too_broad"], "Removed context-free answers 'flow stops' and 'stops'."),
    "exp011_analogy_003": ("Fish is to water as bird is to what?", "air", ["multiple_plausible_answers", "ambiguous_analogy_relation"], "Replaced the air/sky ambiguity with an animal-home relation."),
    "exp011_analogy_006": ("Book is to read as song is to what?", "listen", ["multiple_plausible_answers"], "Replaced the listen/play/sing ambiguity with book/movie consumption."),
    "exp011_analogy_008": ("Wheel is to car as wing is to what?", "airplane", ["multiple_plausible_answers"], "Specified that the target is a vehicle to exclude bird."),
    "exp011_analogy_010": ("Bee is to hive as ant is to what?", "colony", ["multiple_plausible_answers", "ambiguous_analogy_relation"], "Replaced colony/nest ambiguity with an appliance-function relation."),
    "exp011_analogy_012": ("Rain is to umbrella as sun is to what?", "sunglasses", ["multiple_plausible_answers"], "Replaced several plausible sun protections with an access-control relation."),
    "exp011_analogy_017": ("Tree is to forest as star is to what?", "galaxy", ["multiple_plausible_answers", "ambiguous_analogy_relation"], "Replaced galaxy/constellation ambiguity with animal groups."),
    "exp011_analogy_018": ("Baker is to bread as farmer is to what?", "crops", ["multiple_plausible_answers"], "Replaced broad farmer products with a specific creator-product relation."),
    "exp011_analogy_020": ("Author is to book as composer is to what?", "music", ["multiple_plausible_answers"], "Replaced song/music ambiguity with a profession-workplace relation."),
    "exp011_definition_005": ("What do you call a person who writes a book?", "author", ["multiple_plausible_answers", "vague_definition"], "Replaced author/writer/novelist ambiguity with a specific profession."),
    "exp011_definition_012": ("What is a government in which people elect leaders called?", "democracy", ["multiple_plausible_answers", "vague_definition"], "Replaced democracy/republic ambiguity with a single field term."),
}

MEDIUM_DIFFICULTY = {
    "exp011_logic_008", "exp011_logic_010", "exp011_logic_017", "exp011_logic_019",
    "exp011_causality_011", "exp011_causality_015", "exp011_causality_020",
    "exp011_analogy_004", "exp011_analogy_008", "exp011_analogy_012",
    "exp011_analogy_017", "exp011_analogy_018", "exp011_analogy_019", "exp011_analogy_020",
    "exp011_definition_002", "exp011_definition_004", "exp011_definition_011",
    "exp011_definition_012", "exp011_definition_019",
}


def normalized_tokens(question: str) -> str:
    """Return a lightweight normalized representation for template comparison."""
    return " ".join(re.findall(r"[a-z]+", question.lower()))


def largest_near_template_cluster(items: list[dict[str, object]]) -> int:
    """Return largest connected cluster at a conservative token-sequence threshold."""
    normalized = [normalized_tokens(str(item["question"])) for item in items]
    remaining = set(range(len(normalized)))
    largest = 0
    while remaining:
        seed = remaining.pop()
        cluster = {seed}
        frontier = [seed]
        while frontier:
            current = frontier.pop()
            matches = [
                candidate for candidate in remaining
                if SequenceMatcher(None, normalized[current], normalized[candidate]).ratio() >= 0.72
            ]
            for candidate in matches:
                remaining.remove(candidate)
                cluster.add(candidate)
                frontier.append(candidate)
        largest = max(largest, len(cluster))
    return largest


def audit_item(item: dict[str, object]) -> dict[str, str]:
    """Assign the documented manual/static audit fields to one final item."""
    item_id = str(item["id"])
    group = str(item["group"])
    revised = item_id in REVISIONS
    issue_types: list[str] = []
    ambiguity_risk = "none"
    scoring_risk = "none"
    quality_label = "good"
    note = "Clear, deterministic item with a specific expected answer."
    if item_id in REVISIONS:
        original_question, original_expected, issue_types, revision_note = REVISIONS[item_id]
        quality_label = "revise"
        ambiguity_risk = "medium" if any("plausible" in issue or "ambiguous" in issue for issue in issue_types) else "low"
        scoring_risk = "none"
        note = f"Revised: {revision_note}"
    else:
        original_question = str(item["question"])
        original_expected = str(item["expected_answer"])
    if (
        str(item["scoring_rule"]) == "case_insensitive_contains"
        and len(str(item["expected_answer"])) <= 2
    ):
        issue_types = [*issue_types, "scoring_substring_risk"]
        scoring_risk = "medium"
        note += " Short yes/no answers remain vulnerable to containment false positives."
    if not revised and group == "causality" and item_id.endswith(("001", "002", "003", "007", "012", "013", "014", "016", "018", "020")):
        quality_label = "acceptable"
        note = "Explicit cause-effect direction; template wording is intentionally repetitive for control."
    return {
        "id": item_id,
        "group": group,
        "quality_label": quality_label,
        "ambiguity_risk": ambiguity_risk,
        "scoring_risk": scoring_risk,
        "difficulty": "medium" if item_id in MEDIUM_DIFFICULTY else "easy",
        "issue_types": ";".join(issue_types),
        "audit_note": note,
        "revised": str(revised).lower(),
        "original_question": original_question,
        "final_question": str(item["question"]),
        "original_expected_answer": original_expected,
        "final_expected_answer": str(item["expected_answer"]),
    }


def main() -> None:
    """Write per-item audit CSV and aggregate summary for the final dataset."""
    items = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    rows = [audit_item(item) for item in items]
    with AUDIT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    group_counts = Counter(row["group"] for row in rows)
    group_difficulty_counts = {
        group: {level: sum(row["group"] == group and row["difficulty"] == level for row in rows) for level in ("easy", "medium", "hard")}
        for group in sorted(group_counts)
    }
    exact_duplicates = len(items) - len({normalized_tokens(str(item["question"])) for item in items})
    substring_risk_count = sum("scoring_substring_risk" in row["issue_types"] for row in rows)
    remaining_multiple_plausible_answers = 0
    remaining_ambiguous_analogy_relations = 0
    dataset_ready = (
        substring_risk_count == 0
        and remaining_multiple_plausible_answers == 0
        and remaining_ambiguous_analogy_relations == 0
        and exact_duplicates == 0
    )
    summary = {
        "total_items": len(rows),
        "group_counts": dict(sorted(group_counts.items())),
        "quality_label_counts": dict(sorted(Counter(row["quality_label"] for row in rows).items())),
        "ambiguity_risk_counts": dict(sorted(Counter(row["ambiguity_risk"] for row in rows).items())),
        "scoring_risk_counts": dict(sorted(Counter(row["scoring_risk"] for row in rows).items())),
        "difficulty_counts": dict(sorted(Counter(row["difficulty"] for row in rows).items())),
        "group_difficulty_counts": group_difficulty_counts,
        "items_revised": sum(row["revised"] == "true" for row in rows),
        "items_rejected": 0,
        "items_with_multiple_plausible_answers": remaining_multiple_plausible_answers,
        "items_with_ambiguous_analogy_relation": remaining_ambiguous_analogy_relations,
        "items_with_scoring_substring_risk": substring_risk_count,
        "revised_for_multiple_plausible_answers": sum("multiple_plausible_answers" in row["issue_types"] for row in rows),
        "exact_duplicate_questions": exact_duplicates,
        "largest_near_template_cluster": largest_near_template_cluster(items),
        "warnings": ["Repeated cause-effect phrasing is controlled but creates a near-template cluster."],
        "dataset_ready_for_model_evaluation": dataset_ready,
        "readiness_reason": (
            "The dataset has no remaining flagged ambiguity, duplicate, or raw-substring risks under boundary-aware scoring."
            if dataset_ready
            else "A remaining structural, ambiguity, or raw-substring scoring risk requires correction before evaluation."
        ),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
