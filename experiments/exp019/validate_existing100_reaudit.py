"""Build and validate the auditable EXP-019 existing-100 candidate pool.

The builder is deliberately deterministic: it reads the 100 response
paragraphs from the user-provided Word file, preserves the aligned source-card
metadata, and applies a documented, class-preserving audit decision map.  It
does not load models, train classifiers, or read EXP-017 outputs.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from xml.etree import ElementTree


DATA_DIR = Path(__file__).resolve().parent / "data"
WORD_SOURCE = Path(r"C:\Users\Xiayo\Desktop\新建 Microsoft Word 文档 (2).docx")
CARD_SOURCE = DATA_DIR / "source_cards_100_simple.csv"
AUDITED_PATH = DATA_DIR / "existing100_audited_pool.csv"
RETAINED_PATH = DATA_DIR / "existing100_retained_pool.csv"
HUMAN_REVIEW_PATH = DATA_DIR / "existing100_human_review.csv"
REJECTED_PATH = DATA_DIR / "existing100_rejected.csv"
PLAN_PATH = DATA_DIR / "final200_rebalancing_plan.json"

AUDITED_FIELDS = [
    "candidate_id",
    "task_class",
    "original_response",
    "normalized_response",
    "audit_status",
    "semantic_guard",
    "naturalness_status",
    "self_contained",
    "task_clarity",
    "lexical_shortcut_risk",
    "redundancy_risk",
    "length_tokens",
    "length_band",
    "topic_domain",
    "provenance",
    "source_reference",
    "audit_reason",
]
HUMAN_REVIEW_FIELDS = [
    "candidate_id",
    "task_class",
    "original_response",
    "audit_reason",
    "human_decision",
    "human_final_response",
]
REJECTED_FIELDS = [
    "candidate_id",
    "task_class",
    "original_response",
    "rejection_reason",
]
AUDIT_STATUSES = {
    "ACCEPT_AS_IS",
    "ACCEPT_SURFACE_NORMALIZED",
    "HUMAN_REVIEW",
    "REJECT",
}
TOKEN_PATTERN = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "both", "by", "can", "for", "from",
    "in", "is", "it", "of", "on", "or", "the", "that", "to", "while", "with",
}

# Only these entries receive automated wording changes.  Each one is a
# class-blind surface normalization of the original proposition.
NORMALIZATIONS = {
    "SRC-LOG-013": "Dry pores do not store groundwater.",
    "SRC-LOG-015": "Features without survival functions are not adaptations.",
    "SRC-CAU-008": "Chlorophyll absorbs light for photosynthesis.",
    "SRC-CAU-011": "Sunlight heats surface water, causing liquid water to evaporate.",
    "SRC-CAU-012": "Water vapor rises into cooler air and condenses to form cloud droplets.",
    "SRC-CAU-013": "Changes in the Moon's gravitational pull create tidal forces, causing the ocean to bulge.",
    "SRC-CAU-014": "Infiltration of precipitation can replenish groundwater.",
    "SRC-CAU-015": "Groundwater extraction faster than infiltration causes the groundwater level to drop.",
    "SRC-CAU-016": "When warm water vapor contacts a cold container, it condenses into liquid droplets.",
}
ACCEPT_AS_IS = {
    "SRC-LOG-006",
    "SRC-LOG-011",
    "SRC-LOG-012",
    "SRC-LOG-014",
    "SRC-LOG-018",
    "SRC-LOG-021",
    "SRC-CAU-001",
    "SRC-CAU-003",
    "SRC-CAU-004",
    "SRC-CAU-006",
    "SRC-CAU-007",
    "SRC-CAU-009",
    "SRC-CAU-010",
    "SRC-CAU-019",
    "SRC-CAU-020",
    "SRC-CAU-021",
    "SRC-CAU-022",
    "SRC-CAU-023",
    "SRC-CAU-025",
}
LOGIC_REJECTS = {"SRC-LOG-003", "SRC-LOG-025"}
CAUSALITY_HUMAN_REVIEW = {
    "SRC-CAU-002",
    "SRC-CAU-005",
    "SRC-CAU-017",
    "SRC-CAU-018",
    "SRC-CAU-024",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read an UTF-8 CSV artifact."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    """Write an UTF-8 CSV artifact with stable field order."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_docx_paragraphs(path: Path) -> list[str]:
    """Extract nonempty paragraph text from a DOCX without modifying it."""
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs = [
        "".join(text.text or "" for text in paragraph.findall(".//w:t", namespace)).strip()
        for paragraph in root.findall(".//w:body/w:p", namespace)
    ]
    return [paragraph for paragraph in paragraphs if paragraph]


def token_count(text: str) -> int:
    """Count simple English tokens for the frozen EXP-019 length bands."""
    return len(TOKEN_PATTERN.findall(text))


def length_band(count: int) -> str:
    """Return the frozen EXP-019 length band for a token count."""
    if count <= 5:
        return "short"
    if count <= 12:
        return "medium"
    return "limited_long"


def infer_topic_domain(text: str) -> str:
    """Assign a descriptive broad topic label without changing task_class."""
    lowered = text.lower()
    technology_terms = (
        "satellite", "sensor", "gauge", "pump", "microscope", "telescope",
        "solar panel", "filter surface", "well is", "wells reaching",
    )
    biology_terms = (
        "algae", "camouflage", "adaptability", "adaptations", "photosynthesis",
        "chlorophyll", "stomata", "feather", "owl", "whale", "bale", "flippers",
        "immune", "chloroplast", "plant", "leaf", "mesophyll",
    )
    physics_terms = (
        "momentum", "force", "speed", "velocity", "acceleration", "collision",
        "elastic", "mass", "impulse", "energy", "heat",
    )
    earth_terms = (
        "water", "groundwater", "aquifer", "cloud", "vapor", "tide", "ocean",
        "precipitation", "rain", "atmosphere", "evaporation", "infiltration",
        "gravity", "moon", "sun", "rock", "reservoir",
    )
    if any(term in lowered for term in technology_terms):
        return "technology"
    if any(term in lowered for term in biology_terms):
        return "biology"
    if any(term in lowered for term in physics_terms):
        return "physics"
    if any(term in lowered for term in earth_terms):
        return "earth_science"
    return "general_science"


def audit_status(candidate_id: str) -> str:
    """Return the preregistered manual audit disposition for one candidate."""
    if candidate_id in ACCEPT_AS_IS:
        return "ACCEPT_AS_IS"
    if candidate_id in NORMALIZATIONS:
        return "ACCEPT_SURFACE_NORMALIZED"
    if candidate_id in LOGIC_REJECTS:
        return "REJECT"
    if candidate_id in CAUSALITY_HUMAN_REVIEW:
        return "HUMAN_REVIEW"
    if candidate_id.startswith("SRC-ANA-") or candidate_id.startswith("SRC-DEF-"):
        return "REJECT"
    return "HUMAN_REVIEW"


def audit_reason(candidate_id: str, status: str) -> str:
    """Explain the conservative decision without proposing any new response text."""
    if status == "ACCEPT_AS_IS":
        return "Task function is clear, the proposition is coherent and self-contained, and no substantive repair is needed."
    if status == "ACCEPT_SURFACE_NORMALIZED":
        return "Only grammar, wording, or terminology form was minimally normalized; the original proposition is unchanged."
    if candidate_id == "SRC-LOG-003":
        return "The factual and task-function claim is not reliable enough to retain; repair would require a new proposition."
    if candidate_id == "SRC-LOG-025":
        return "The statement is incomplete and its intended relation is unclear; substantive authorship would be required."
    if candidate_id.startswith("SRC-ANA-"):
        return "Original task_class is analogy, but this is a one-concept definition without a two-relation correspondence; a repair would add new content."
    if candidate_id.startswith("SRC-DEF-"):
        return "Original task_class is definition, but this compares two relations rather than defining one concept; a repair would add new content."
    if candidate_id == "SRC-CAU-002":
        return "The causal claim needs an unstated condition about force to be technically reliable; do not auto-rewrite."
    if candidate_id == "SRC-CAU-005":
        return "The relationship needs an unstated mass condition to be technically precise; do not auto-rewrite."
    if candidate_id == "SRC-CAU-017":
        return "Translation-like wording makes the factual relation unclear; naturalization would require substantive rewriting."
    if candidate_id == "SRC-CAU-018":
        return "The technical term and factual relation need human checking; correcting them would alter content."
    if candidate_id == "SRC-CAU-024":
        return "The sentence lacks a stated outcome, so it is not self-contained as a causal response."
    return "Dominant task function is not sufficiently clear for the original class without adding a premise or mechanism; human review is required."


def task_clarity(status: str) -> str:
    """Map audit disposition to a transparent task-clarity descriptor."""
    if status.startswith("ACCEPT"):
        return "clear"
    if status == "HUMAN_REVIEW":
        return "partial"
    return "mismatched"


def naturalness_status(status: str) -> str:
    """Map audit disposition to a descriptive language-quality state."""
    if status == "ACCEPT_AS_IS":
        return "natural"
    if status == "ACCEPT_SURFACE_NORMALIZED":
        return "surface_normalized"
    if status == "HUMAN_REVIEW":
        return "needs_human_review"
    return "class_mismatch_or_unusable"


def char_ngrams(text: str) -> Counter[str]:
    """Build character 3-5 gram counts for descriptive similarity only."""
    compact = re.sub(r"\s+", " ", text.lower()).strip()
    grams: Counter[str] = Counter()
    for size in (3, 4, 5):
        grams.update(compact[index : index + size] for index in range(max(0, len(compact) - size + 1)))
    return grams


def cosine(left: Counter[str], right: Counter[str]) -> float:
    """Compute cosine similarity over sparse character n-gram counts."""
    dot_product = sum(value * right.get(key, 0) for key, value in left.items())
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    return dot_product / (left_norm * right_norm) if left_norm and right_norm else 0.0


def lexical_summary(rows: list[dict[str, object]]) -> dict[str, object]:
    """Compute descriptive lexical/template indicators without fitting a classifier."""
    token_lists = {
        row["candidate_id"]: [token.lower() for token in TOKEN_PATTERN.findall(str(row["original_response"]))]
        for row in rows
    }
    by_class: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        by_class[str(row["task_class"])].append(row)

    class_presence: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        class_presence[str(row["task_class"])].update(
            token for token in token_lists[str(row["candidate_id"])] if token not in STOPWORDS
        )

    output: dict[str, object] = {}
    for task_class, class_rows in sorted(by_class.items()):
        unigrams: Counter[str] = Counter()
        bigrams: Counter[str] = Counter()
        prefixes: Counter[str] = Counter()
        for row in class_rows:
            tokens = [token for token in token_lists[str(row["candidate_id"])] if token not in STOPWORDS]
            unigrams.update(tokens)
            bigrams.update(" ".join(tokens[index : index + 2]) for index in range(max(0, len(tokens) - 1)))
            if len(tokens) >= 3:
                prefixes[" ".join(tokens[:3])] += 1

        concentrated = [
            token
            for token, frequency in unigrams.most_common()
            if frequency >= 2 and sum(token in words for words in class_presence.values()) == 1
        ][:10]
        grams = {row["candidate_id"]: char_ngrams(str(row["original_response"])) for row in class_rows}
        similarities: list[dict[str, object]] = []
        for index, left in enumerate(class_rows):
            for right in class_rows[index + 1 :]:
                score = cosine(grams[left["candidate_id"]], grams[right["candidate_id"]])
                if score >= 0.35:
                    similarities.append(
                        {
                            "left": left["candidate_id"],
                            "right": right["candidate_id"],
                            "character_ngram_cosine": round(score, 4),
                        }
                    )
        similarities.sort(key=lambda item: item["character_ngram_cosine"], reverse=True)
        output[task_class] = {
            "top_unigrams": unigrams.most_common(10),
            "top_bigrams": bigrams.most_common(10),
            "highly_class_concentrated_words": concentrated,
            "repeated_three_word_prefixes": [
                {"prefix": prefix, "count": count}
                for prefix, count in prefixes.most_common()
                if count > 1
            ],
            "repeated_syntactic_frame_proxies": [
                {"frame": prefix, "count": count}
                for prefix, count in prefixes.most_common(5)
            ],
            "high_character_ngram_similarity_pairs": similarities[:10],
        }
    return output


def distribution(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    """Return a stable count distribution for a selected audit field."""
    return dict(sorted(Counter(str(row[field]) for row in rows).items()))


def build() -> None:
    """Create audited derivative pools and the final-200 rebalancing plan."""
    if not WORD_SOURCE.exists():
        raise FileNotFoundError(f"Canonical Word response source is missing: {WORD_SOURCE}")
    responses = extract_docx_paragraphs(WORD_SOURCE)
    cards = read_csv(CARD_SOURCE)
    if len(responses) != 100 or len(cards) != 100:
        raise ValueError(f"Expected 100 responses and 100 source cards, found {len(responses)} and {len(cards)}")

    provisional: list[dict[str, object]] = []
    for response, card in zip(responses, cards, strict=True):
        candidate_id = card["source_card_id"]
        status = audit_status(candidate_id)
        normalized = NORMALIZATIONS.get(candidate_id, response)
        token_total = token_count(response)
        provisional.append(
            {
                "candidate_id": candidate_id,
                "task_class": card["task_class"],
                "original_response": response,
                "normalized_response": normalized,
                "audit_status": status,
                "semantic_guard": (
                    "ORIGINAL_PRESERVED" if status == "ACCEPT_AS_IS"
                    else "SURFACE_ONLY_UNCHANGED" if status == "ACCEPT_SURFACE_NORMALIZED"
                    else "HUMAN_REQUIRED" if status == "HUMAN_REVIEW"
                    else "NOT_APPLICABLE"
                ),
                "naturalness_status": naturalness_status(status),
                "self_contained": "no" if candidate_id in {"SRC-LOG-025", "SRC-CAU-024"} else "yes",
                "task_clarity": task_clarity(status),
                "length_tokens": token_total,
                "length_band": length_band(token_total),
                "topic_domain": infer_topic_domain(response),
                "provenance": "not_recorded",
                "source_reference": card["source_reference"],
                "audit_reason": audit_reason(candidate_id, status),
            }
        )

    by_class: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in provisional:
        by_class[str(row["task_class"])].append(row)
    for class_rows in by_class.values():
        gram_vectors = {row["candidate_id"]: char_ngrams(str(row["original_response"])) for row in class_rows}
        for row in class_rows:
            score = max(
                (
                    cosine(gram_vectors[row["candidate_id"]], gram_vectors[other["candidate_id"]])
                    for other in class_rows
                    if other["candidate_id"] != row["candidate_id"]
                ),
                default=0.0,
            )
            row["redundancy_risk"] = "high" if score >= 0.55 else "medium" if score >= 0.35 else "low"
            row["lexical_shortcut_risk"] = (
                "high" if str(row["task_class"]) in {"analogy", "definition"}
                else "medium" if score >= 0.35 else "low"
            )

    write_csv(AUDITED_PATH, AUDITED_FIELDS, provisional)
    retained = [
        row for row in provisional
        if row["audit_status"] in {"ACCEPT_AS_IS", "ACCEPT_SURFACE_NORMALIZED"}
    ]
    human_review = [row for row in provisional if row["audit_status"] == "HUMAN_REVIEW"]
    rejected = [row for row in provisional if row["audit_status"] == "REJECT"]
    write_csv(RETAINED_PATH, AUDITED_FIELDS, retained)
    write_csv(
        HUMAN_REVIEW_PATH,
        HUMAN_REVIEW_FIELDS,
        [
            {
                "candidate_id": row["candidate_id"],
                "task_class": row["task_class"],
                "original_response": row["original_response"],
                "audit_reason": row["audit_reason"],
                "human_decision": "",
                "human_final_response": "",
            }
            for row in human_review
        ],
    )
    write_csv(
        REJECTED_PATH,
        REJECTED_FIELDS,
        [
            {
                "candidate_id": row["candidate_id"],
                "task_class": row["task_class"],
                "original_response": row["original_response"],
                "rejection_reason": row["audit_reason"],
            }
            for row in rejected
        ],
    )

    lexical = lexical_summary(provisional)
    class_guidance = {
        "logic": [
            "Add everyday-life, language, and quantitative rule-application responses; retained material is concentrated in physics, earth science, and biology.",
            "Prefer explicit conditional, exclusion, comparison, or deduction functions over bare factual statements.",
            "Use more medium-length responses and avoid repeated short 'X is not Y' skeletons.",
            "Record provenance and broaden sources beyond the current small source-card set.",
        ],
        "causality": [
            "Retain the broad physics/biology/earth/technology coverage, but add non-science everyday and social/general mechanisms with documented sources.",
            "Reduce repeated water-vapor, groundwater, and tidal phrasing; use different causal structures and outcome statements.",
            "Add medium-length mechanisms while retaining some concise causal answers.",
            "Record provenance for every new example and avoid a single source dominating a class.",
        ],
        "analogy": [
            "Collect 50 new, self-contained two-relation correspondences; no current item can be retained under the frozen analogy label.",
            "Cover everyday tools, language, technology, mathematics, biology, and earth science rather than single-concept descriptions.",
            "Use varied correspondence phrasing and documented, diverse sources/provenance.",
        ],
        "definition": [
            "Collect 50 new, self-contained single-concept definitions; no current relation-comparison item can be retained under the frozen definition label.",
            "Cover non-science and non-water concepts alongside science, with varied definitional properties and length bands.",
            "Use documented, diverse sources/provenance and avoid repeated 'both' comparison frames.",
        ],
    }
    plan_classes: dict[str, object] = {}
    for task_class in ("logic", "causality", "analogy", "definition"):
        class_rows = by_class[task_class]
        retained_rows = [row for row in class_rows if row in retained]
        status_counts = Counter(str(row["audit_status"]) for row in class_rows)
        source_distribution = distribution(retained_rows, "source_reference")
        plan_classes[task_class] = {
            "current_candidates": len(class_rows),
            "accepted_as_is": status_counts["ACCEPT_AS_IS"],
            "accepted_surface_normalized": status_counts["ACCEPT_SURFACE_NORMALIZED"],
            "human_review": status_counts["HUMAN_REVIEW"],
            "rejected": status_counts["REJECT"],
            "retained_total": len(retained_rows),
            "remaining_to_50": 50 - len(retained_rows),
            "candidate_topic_distribution": distribution(class_rows, "topic_domain"),
            "topic_distribution": distribution(retained_rows, "topic_domain"),
            "length_distribution": distribution(retained_rows, "length_band"),
            "provenance_distribution": distribution(retained_rows, "provenance"),
            "source_distribution": source_distribution,
            "source_concentration": (
                max(source_distribution.values()) / len(retained_rows) if retained_rows else None
            ),
            "lexical_risks": lexical[task_class],
            "priority_gaps": class_guidance[task_class],
            "recommended_future_quota": {
                "count": 50 - len(retained_rows),
                "principle": "Fill only with candidates that meet task clarity, naturalness, semantic validity, and documented diversity requirements; do not optimize for evaluator performance.",
                "recommendations": class_guidance[task_class],
            },
        }

    plan = {
        "source_of_truth": {
            "response_text": str(WORD_SOURCE),
            "aligned_metadata": str(CARD_SOURCE),
            "mapping_rule": "The 100 nonempty Word paragraphs map in order to the 100 source-card rows; no files were merged.",
        },
        "target_total": 200,
        "target_per_class": 50,
        "current_retained_total": len(retained),
        "remaining_total": 200 - len(retained),
        "audit_status_counts": dict(sorted(Counter(row["audit_status"] for row in provisional).items())),
        "classes": plan_classes,
        "overall_notes": [
            "This is a candidate retained pool, not a frozen final dataset.",
            "Topic labels are descriptive and never change task_class.",
            "Provenance was not recorded in the source cards and is therefore reported as not_recorded rather than inferred.",
            "Rebalancing occurred before evaluator training and without accessing EXP-017 steering outputs.",
        ],
    }
    with PLAN_PATH.open("w", encoding="utf-8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def validate() -> dict[str, int]:
    """Validate audit completeness, preservation rules, and final-target constraints."""
    errors: list[str] = []
    audited = read_csv(AUDITED_PATH)
    retained = read_csv(RETAINED_PATH)
    human_review = read_csv(HUMAN_REVIEW_PATH)
    rejected = read_csv(REJECTED_PATH)
    cards = read_csv(CARD_SOURCE)
    responses = extract_docx_paragraphs(WORD_SOURCE)

    if len(audited) != 100:
        errors.append(f"expected exactly 100 audited rows, found {len(audited)}")
    if len(cards) != 100 or len(responses) != 100:
        errors.append("canonical source no longer contains exactly 100 aligned entries")
    expected_ids = [card["source_card_id"] for card in cards]
    audited_ids = [row["candidate_id"] for row in audited]
    if audited_ids != expected_ids:
        errors.append("audited candidate IDs do not preserve source-card order and coverage")
    if len(set(audited_ids)) != len(audited_ids):
        errors.append("audited candidate IDs are not unique")

    for index, row in enumerate(audited):
        candidate_id = row["candidate_id"]
        if row["task_class"] != cards[index]["task_class"]:
            errors.append(f"{candidate_id}: task_class changed from source metadata")
        if row["original_response"] != responses[index]:
            errors.append(f"{candidate_id}: original_response differs from the Word source")
        if row["audit_status"] not in AUDIT_STATUSES:
            errors.append(f"{candidate_id}: invalid audit_status")
        if row["audit_status"] == "ACCEPT_AS_IS":
            if row["normalized_response"] != row["original_response"] or row["semantic_guard"] != "ORIGINAL_PRESERVED":
                errors.append(f"{candidate_id}: ACCEPT_AS_IS must preserve original text")
        elif row["audit_status"] == "ACCEPT_SURFACE_NORMALIZED":
            if candidate_id not in NORMALIZATIONS or row["normalized_response"] != NORMALIZATIONS[candidate_id]:
                errors.append(f"{candidate_id}: surface normalization is not in the frozen audit map")
            if row["semantic_guard"] != "SURFACE_ONLY_UNCHANGED":
                errors.append(f"{candidate_id}: surface normalization lacks semantic guard")
        elif row["normalized_response"] != row["original_response"]:
            errors.append(f"{candidate_id}: non-retained row must not receive new wording")
        if any(term in " ".join(row.values()).lower() for term in ("exp-017", "exp017", "hidden_state", "tensor", "steering")):
            errors.append(f"{candidate_id}: forbidden EXP-017/model metadata found")

    status_counts = Counter(row["audit_status"] for row in audited)
    if len(retained) + len(human_review) + len(rejected) != 100:
        errors.append("retained + human_review + rejected does not equal 100")
    if len(retained) != status_counts["ACCEPT_AS_IS"] + status_counts["ACCEPT_SURFACE_NORMALIZED"]:
        errors.append("retained-pool count does not match accepted statuses")
    if len(human_review) != status_counts["HUMAN_REVIEW"]:
        errors.append("human-review count does not match HUMAN_REVIEW status")
    if len(rejected) != status_counts["REJECT"]:
        errors.append("rejected count does not match REJECT status")
    if any(row["human_decision"] or row["human_final_response"] for row in human_review):
        errors.append("human-review pool contains auto-filled human fields")

    with PLAN_PATH.open("r", encoding="utf-8") as handle:
        plan = json.load(handle)
    if plan.get("target_total") != 200 or plan.get("target_per_class") != 50:
        errors.append("final target constraint is not 200 total / 50 per class")
    if plan.get("current_retained_total") != len(retained):
        errors.append("plan retained total does not match retained-pool count")
    if plan.get("remaining_total") != 200 - len(retained):
        errors.append("plan remaining total does not match retained-pool count")

    if errors:
        raise ValueError("Existing-100 reaudit validation failed:\n- " + "\n- ".join(errors))
    return {
        "audited": len(audited),
        "accepted_as_is": status_counts["ACCEPT_AS_IS"],
        "accepted_surface_normalized": status_counts["ACCEPT_SURFACE_NORMALIZED"],
        "human_review": status_counts["HUMAN_REVIEW"],
        "rejected": status_counts["REJECT"],
        "retained": len(retained),
    }


def main() -> None:
    """Build on request, then validate and print a concise report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="build all audited derivative artifacts before validation")
    args = parser.parse_args()
    if args.build:
        build()
    report = validate()
    print("existing-100 reaudit validation: PASS")
    for name, value in report.items():
        print(f"{name}: {value}")


if __name__ == "__main__":
    main()
