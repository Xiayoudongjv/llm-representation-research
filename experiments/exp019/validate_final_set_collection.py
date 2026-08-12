"""Validate progress or final-freeze conditions for the EXP-019 collection packet."""

from __future__ import annotations

import argparse
import csv
import re
from collections import Counter
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
PACKET_PATH = DATA_DIR / "final_set_collection_packet.csv"
PROCEDURAL_PATH = DATA_DIR / "behavioral_targetness_dataset.csv"

FIELDS = [
    "candidate_id", "task_class", "target_provenance", "response_text",
    "source_family", "source_reference", "author_id", "length_tokens",
    "length_band", "self_contained", "naturalness", "label_quality",
    "lexical_giveaway", "notes", "collection_status",
]
CLASSES = ("logic", "causality", "analogy", "definition")
PROVENANCE = ("human_authored", "manually_adapted_external")
BANDS = {"short": (1, 5), "medium": (6, 12), "limited_long": (13, 20)}
FORBIDDEN_TERMS = (
    "NO_INTERVENTION", "TASK_REAL", "MATCHED_RANDOM", "OPPOSITE",
    "hidden_state", "steering_vector", "intervention_condition",
)


def load_rows() -> list[dict[str, str]]:
    """Load the collection packet and enforce its frozen header."""
    with PACKET_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != FIELDS:
            raise ValueError(f"unexpected packet header: {reader.fieldnames}")
        return list(reader)


def token_count(text: str) -> int:
    """Count simple whitespace-separated response tokens."""
    return len(text.split())


def normalized(text: str) -> str:
    """Normalize text for duplicate comparison."""
    return re.sub(r"\s+", " ", text.casefold()).strip()


def prefix_three(text: str) -> str:
    """Return a normalized three-word prefix for overlap reporting."""
    return " ".join(re.findall(r"[A-Za-z0-9]+", text.casefold())[:3])


def procedural_texts() -> tuple[set[str], set[str], set[str]]:
    """Load procedural text keys for mechanical independence checks only."""
    with PROCEDURAL_PATH.open(encoding="utf-8", newline="") as handle:
        texts = [row["response_text"] for row in csv.DictReader(handle)]
    return set(texts), {normalized(text) for text in texts}, {prefix_three(text) for text in texts}


def report_progress(rows: list[dict[str, str]]) -> None:
    """Print collection progress without requiring any response text."""
    completed = [row for row in rows if row["collection_status"] == "accepted"]
    missing = len(rows) - len(completed)
    class_counts = Counter(row["task_class"] for row in completed)
    provenance_counts = Counter(row["target_provenance"] for row in completed)
    bands = Counter(row["length_band"] for row in completed if row["length_band"])
    source_counts = Counter(row["source_family"] for row in completed if row["source_family"])
    missing_sources = sum(
        not row["source_family"] or not row["source_reference"]
        for row in completed
        if row["target_provenance"] == "manually_adapted_external"
    )
    quality = Counter(row["label_quality"] for row in completed if row["label_quality"])
    print(f"completed_rows={len(completed)}")
    print(f"missing_rows={missing}")
    print(f"class_counts={dict(class_counts)}")
    print(f"provenance_counts={dict(provenance_counts)}")
    print(f"length_distributions={dict(bands)}")
    print(f"source_family_counts={dict(source_counts)}")
    print(f"missing_external_source_references={missing_sources}")
    print(f"label_quality_counts={dict(quality)}")


def require(condition: bool, message: str) -> None:
    """Raise a readable validation error when a final condition fails."""
    if not condition:
        raise ValueError(message)


def validate_final(rows: list[dict[str, str]]) -> None:
    """Require all frozen structural conditions for final-set freeze."""
    require(len(rows) == 200, f"expected 200 rows, got {len(rows)}")
    require(all(row["collection_status"] == "accepted" for row in rows), "all rows must be accepted")
    require(all(row["label_quality"] == "clear" for row in rows), "all rows must be clear")
    require(Counter(row["task_class"] for row in rows) == Counter({c: 50 for c in CLASSES}), "class quota failure")
    require(Counter(row["target_provenance"] for row in rows) == Counter({p: 100 for p in PROVENANCE}), "provenance quota failure")
    for cls in CLASSES:
        require(
            Counter(row["target_provenance"] for row in rows if row["task_class"] == cls)
            == Counter({p: 25 for p in PROVENANCE}),
            f"class provenance quota failure: {cls}",
        )
    external = [row for row in rows if row["target_provenance"] == "manually_adapted_external"]
    source_counts = Counter(row["source_family"] for row in external)
    require(all(row["source_family"] and row["source_reference"] for row in external), "external source metadata missing")
    require(all(count <= 20 for count in source_counts.values()), "external source family exceeds 20")
    require(all(row["response_text"].strip() for row in rows), "empty response")
    require(all(row["self_contained"].casefold() == "yes" for row in rows), "not self-contained")
    require(all(row["length_band"] in BANDS for row in rows), "invalid length band")
    for row in rows:
        try:
            length = int(row["length_tokens"])
        except ValueError as exc:
            raise ValueError("invalid length_tokens") from exc
        require(1 <= length <= 20, "length outside 1-20")
        lo, hi = BANDS[row["length_band"]]
        require(lo <= length <= hi, "length range mismatch")
    texts = [row["response_text"] for row in rows]
    require(len(texts) == len(set(texts)), "exact duplicate response")
    normalized_texts = [normalized(text) for text in texts]
    require(len(normalized_texts) == len(set(normalized_texts)), "normalized duplicate response")
    exact, normalized_set, prefixes = procedural_texts()
    require(not set(texts) & exact, "exact procedural overlap")
    require(not set(normalized_texts) & normalized_set, "normalized procedural overlap")
    packet_prefixes = {prefix_three(text) for text in texts if prefix_three(text)}
    print(f"procedural_three_word_prefix_overlap={len(packet_prefixes & prefixes)}")
    values = " ".join(" ".join(row.values()) for row in rows).casefold()
    require(not any(term.casefold() in values for term in FORBIDDEN_TERMS), "forbidden intervention metadata")
    print("final_validation=passed")


def main() -> None:
    """Run progress or final validation mode."""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--progress", action="store_true")
    group.add_argument("--final", dest="final_mode", action="store_true")
    args = parser.parse_args()
    rows = load_rows()
    if args.progress:
        require(len(rows) == 200, f"collection packet must contain 200 rows, got {len(rows)}")
        report_progress(rows)
    else:
        validate_final(rows)


if __name__ == "__main__":
    main()
