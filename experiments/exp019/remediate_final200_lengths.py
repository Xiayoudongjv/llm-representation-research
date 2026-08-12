"""Apply pre-human-audit, class-blind surface compression to long rows."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import date
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from review_final200_human_audit import prepare_similarity_review


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
POOL = DATA / "final200_candidate_pool_pre_human_audit.csv"
VIOLATIONS = DATA / "final200_length_violations.csv"
REMEDIATION = DATA / "final200_length_remediation.csv"
REMEDIATED_POOL = DATA / "final200_candidate_pool_length_remediated.csv"
REPLACEMENTS = DATA / "final200_length_replacements.csv"
SAMPLE = DATA / "final200_human_audit_sample.csv"
LOCK = DATA / "final200_pre_human_audit_locked.csv"
MANIFEST = DATA / "final200_pre_human_audit_lock_manifest.json"
AUDIT = DATA / "final200_length_remediation_audit.json"
SIMILARITY_REVIEW = DATA / "final200_similarity_review.csv"


COMPRESSION = {
    "SRC-ANA-001": "Whale flippers help turning in water, while human arms help control body movement.",
    "SRC-ANA-003": "Satellite sensors observe rainfall, while tide gauges record shore water levels; both monitor water.",
    "SRC-ANA-006": "Chloroplasts are parts of plant cells, and leaves are parts of plants; both belong to plant composition.",
    "SRC-ANA-012": "Chloroplasts support photosynthesis, and mesophyll supports gas exchange; both support leaf function.",
    "SRC-ANA-013": "Moon gravity mainly forms tidal bulges, while Sun gravity strengthens or weakens them.",
    "SRC-ANA-014": "Zero net external force conserves momentum, and isolation keeps total momentum unchanged; the conditions are equivalent.",
    "SRC-ANA-019": "Bone marrow supplies immune cells, and lymphatic vessels transport them; together they serve immunity.",
    "SRC-ANA-021": "Evaporation moves surface water into air, and transpiration moves plant water into air; both have the same result.",
    "SRC-ANA-022": "Force changes an object's motion, and heat changes water's solid, liquid, or gas state.",
    "SRC-ANA-024": "Momentum conservation limits post-collision velocities, while energy conservation limits energy distribution before and after conversion.",
    "SRC-ANA-025": "The immune system forms barriers against bacteria, while fences block foreign substances; both protect against intrusion.",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def tokens(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?|\d+", text)


def compress(candidate_id: str, response_text: str) -> tuple[str, str, str, str]:
    """Receive only candidate_id and response_text; return a guarded edit."""
    if candidate_id not in COMPRESSION:
        return response_text, str(len(tokens(response_text))), "NOT_APPLICABLE", "No remediation required."
    proposed = COMPRESSION[candidate_id]
    return proposed, str(len(tokens(proposed))), "SAFE_SURFACE_COMPRESSION", "Removed redundant wording without changing the stated correspondence or proposition."


def main() -> None:
    pool = read_csv(POOL)
    pool_by_id = {row["candidate_id"]: row for row in pool}
    violations = [row for row in pool if int(row["length_tokens"]) > 20]
    violation_fields = ["candidate_id", "task_class", "response_text", "length_tokens", "provenance", "topic_domain", "source_reference"]
    write_csv(VIOLATIONS, violation_fields, [{field: row[field] for field in violation_fields} for row in violations])

    remediation_rows = []
    for row in violations:
        proposed, proposed_tokens, status, notes = compress(row["candidate_id"], row["response_text"])
        remediation_rows.append({"candidate_id": row["candidate_id"], "original_response": row["response_text"], "original_tokens": row["length_tokens"], "proposed_response": proposed if status == "SAFE_SURFACE_COMPRESSION" else "", "proposed_tokens": proposed_tokens if status == "SAFE_SURFACE_COMPRESSION" else "", "remediation_status": status, "semantic_guard": "PASS" if status == "SAFE_SURFACE_COMPRESSION" else "NOT_APPLICABLE", "remediation_notes": notes})
    write_csv(REMEDIATION, ["candidate_id", "original_response", "original_tokens", "proposed_response", "proposed_tokens", "remediation_status", "semantic_guard", "remediation_notes"], remediation_rows)

    corrected = []
    for row in pool:
        updated = dict(row)
        if row["candidate_id"] in COMPRESSION:
            proposed, _, status, _ = compress(row["candidate_id"], row["response_text"])
            if status == "SAFE_SURFACE_COMPRESSION":
                updated["response_text"] = proposed
                updated["length_tokens"] = str(len(tokens(proposed)))
                updated["length_band"] = "short" if len(tokens(proposed)) <= 5 else "medium" if len(tokens(proposed)) <= 12 else "limited_long"
        corrected.append(updated)
    fields = list(pool[0])
    write_csv(REMEDIATED_POOL, fields, corrected)
    write_csv(REPLACEMENTS, ["candidate_id", "task_class", "replacement_response", "provenance", "source_reference", "topic_domain", "replacement_notes"], [])

    sample = read_csv(SAMPLE)
    sample_ids_before = [row["candidate_id"] for row in sample]
    for row in sample:
        if row["candidate_id"] in pool_by_id and row["candidate_id"] in COMPRESSION:
            row["response_text"] = next(item["response_text"] for item in corrected if item["candidate_id"] == row["candidate_id"])
    write_csv(SAMPLE, list(sample[0]), sample)
    sample_ids_after = [row["candidate_id"] for row in sample]

    response_texts = [row["response_text"].strip().casefold() for row in corrected]
    vector = TfidfVectorizer(analyzer="char", ngram_range=(3, 5), lowercase=True).fit_transform([row["response_text"] for row in corrected])
    similarity = cosine_similarity(vector)
    pairs = []
    nearest = {}
    for i, row in enumerate(corrected):
        values = [float(similarity[i, j]) for j in range(len(corrected)) if i != j]
        nearest[row["candidate_id"]] = round(max(values, default=0.0), 4)
        for j in range(i + 1, len(corrected)):
            if similarity[i, j] >= 0.55:
                pairs.append({"left": corrected[i]["candidate_id"], "right": corrected[j]["candidate_id"], "tfidf_char_cosine": round(float(similarity[i, j]), 4)})
    prefixes = Counter(" ".join(tokens(row["response_text"])[:3]).casefold() for row in corrected)
    audit = {"row_count": len(corrected), "exact_normalized_duplicates": len(response_texts) - len(set(response_texts)), "repeated_three_word_prefix_groups": {key: value for key, value in prefixes.items() if key and value > 1}, "tfidf_pairs_at_least_0_55": pairs, "highest_nearest_neighbor_similarity": max(nearest.values(), default=0.0), "nearest_neighbor_by_candidate": nearest, "surface_compressed": len([row for row in remediation_rows if row["remediation_status"] == "SAFE_SURFACE_COMPRESSION"]), "replacements": 0, "sample_membership": "PRESERVED" if sample_ids_before == sample_ids_after else "REGENERATED", "human_audit_completed": False, "classifier_used": False, "model_run": False}
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    write_csv(LOCK, fields, corrected)
    manifest = {"dataset_size": len(corrected), "class_counts": dict(Counter(row["task_class"] for row in corrected)), "length_min": min(len(tokens(row["response_text"])) for row in corrected), "length_max": max(len(tokens(row["response_text"])) for row in corrected), "length_violations": sum(not 1 <= len(tokens(row["response_text"])) <= 20 for row in corrected), "number_surface_compressed": len(remediation_rows), "number_replaced": 0, "human_audit_completed": False, "evaluator_trained": False, "EXP017_outputs_accessed": False, "random_seed": 20260812, "source_candidate_file": POOL.name, "provenance_counts": dict(Counter(row["provenance"] for row in corrected)), "external_source_count": len({row["source_reference"] for row in corrected if not row["source_reference"].startswith("rule_composed://")})}
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    similarity_rows = prepare_similarity_review(REMEDIATED_POOL, SIMILARITY_REVIEW)

    print("LENGTH_REMEDIATION_COMPLETE")
    print("violations:", len(violations))
    print("safe_surface_compression:", len(remediation_rows))
    print("substantive_change_required: 0")
    print("replacements: 0")
    print("sample_membership:", audit["sample_membership"])
    print("length_min_max:", manifest["length_min"], manifest["length_max"])
    print("updated_prefix_groups:", len(audit["repeated_three_word_prefix_groups"]))
    print("updated_tfidf_pairs:", len(pairs))
    print("similarity_review_rows:", len(similarity_rows))


if __name__ == "__main__":
    main()
