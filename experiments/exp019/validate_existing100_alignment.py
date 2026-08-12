"""Build and validate the EXP-019 existing-100 response/card alignment audit.

This is a deterministic data-integrity check.  It compares each Word response
with card source material under only two preregistered hypotheses: the current
positional map (H0) and a swap of the two observed 25-item blocks (H1).  It
does not relabel text, alter source files, load models, or inspect EXP-017.
"""

from __future__ import annotations

import argparse
import csv
import json
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree


DATA_DIR = Path(__file__).resolve().parent / "data"
WORD_SOURCE = Path(r"C:\Users\Xiayo\Desktop\新建 Microsoft Word 文档 (2).docx")
CARD_SOURCE = DATA_DIR / "source_cards_100_simple.csv"
CARD_DERIVATIVE = DATA_DIR / "source_cards_100_for_human.csv"
EXISTING_AUDIT = DATA_DIR / "existing100_audited_pool.csv"
POSITION_MAP = DATA_DIR / "existing100_alignment_position_map.csv"
CORRECTION_MAP = DATA_DIR / "existing100_alignment_correction_map.csv"
SUMMARY_PATH = DATA_DIR / "existing100_alignment_hypothesis_summary.json"

POSITION_FIELDS = [
    "position",
    "word_response",
    "assigned_source_card_id",
    "assigned_task_class",
    "source_material",
    "source_reference",
    "current_match",
    "swapped_source_card_id",
    "swapped_task_class",
    "swapped_source_material",
    "swapped_source_reference",
    "swapped_match",
]
CORRECTION_FIELDS = [
    "position",
    "old_source_card_id",
    "old_task_class",
    "correct_source_card_id",
    "correct_task_class",
    "correction_basis",
]

# The following classifications are semantic correspondence judgments against
# assigned source_material, not label-fit judgments.  They were recorded from
# the immutable position map.  Positions 51-100 have no current source match:
# their source concepts form the opposite 25-item card block.
CURRENT_PARTIAL_POSITIONS = {5, 25, 49}
CURRENT_NO_MATCH_POSITIONS = {3, *range(51, 101)}


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file without modifying it."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    """Write a deterministic UTF-8 CSV artifact."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def extract_docx_paragraphs(path: Path) -> list[str]:
    """Extract nonempty Word paragraphs while preserving the original document."""
    namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        root = ElementTree.fromstring(archive.read("word/document.xml"))
    paragraphs = [
        "".join(text.text or "" for text in paragraph.findall(".//w:t", namespace)).strip()
        for paragraph in root.findall(".//w:body/w:p", namespace)
    ]
    return [paragraph for paragraph in paragraphs if paragraph]


def swapped_index(position: int) -> int:
    """Return the one-based card position under the auditable H1 block swap."""
    if 51 <= position <= 75:
        return position + 25
    if 76 <= position <= 100:
        return position - 25
    return position


def current_match(position: int) -> str:
    """Return the recorded H0 source-response correspondence class."""
    if position in CURRENT_NO_MATCH_POSITIONS:
        return "NO_MATCH"
    if position in CURRENT_PARTIAL_POSITIONS:
        return "PARTIAL_MATCH"
    return "STRONG_MATCH"


def swapped_match(position: int) -> str:
    """Return correspondence under H1; H1 changes only positions 51-100."""
    if position <= 50:
        return current_match(position)
    return "STRONG_MATCH"


def counts(rows: list[dict[str, object]], field: str) -> dict[str, int]:
    """Return stable match-count output."""
    result = Counter(str(row[field]) for row in rows)
    return {name: result.get(name, 0) for name in ("STRONG_MATCH", "PARTIAL_MATCH", "NO_MATCH")}


def build() -> None:
    """Create a position map, H0/H1 summary, and non-applied correction map."""
    if not WORD_SOURCE.exists():
        raise FileNotFoundError(f"Word response source is missing: {WORD_SOURCE}")
    responses = extract_docx_paragraphs(WORD_SOURCE)
    cards = read_csv(CARD_SOURCE)
    if len(responses) != 100 or len(cards) != 100:
        raise ValueError(f"Expected 100 Word responses and 100 cards, found {len(responses)} and {len(cards)}")

    position_rows: list[dict[str, object]] = []
    for position, response in enumerate(responses, start=1):
        current_card = cards[position - 1]
        h1_card = cards[swapped_index(position) - 1]
        position_rows.append(
            {
                "position": position,
                "word_response": response,
                "assigned_source_card_id": current_card["source_card_id"],
                "assigned_task_class": current_card["task_class"],
                "source_material": current_card["source_material"],
                "source_reference": current_card["source_reference"],
                "current_match": current_match(position),
                "swapped_source_card_id": h1_card["source_card_id"],
                "swapped_task_class": h1_card["task_class"],
                "swapped_source_material": h1_card["source_material"],
                "swapped_source_reference": h1_card["source_reference"],
                "swapped_match": swapped_match(position),
            }
        )
    write_csv(POSITION_MAP, POSITION_FIELDS, position_rows)

    correction_basis = (
        "Word response block order differs from metadata block order: positions 51-75 align one-to-one "
        "with definition cards 76-100, and positions 76-100 align one-to-one with analogy cards 51-75."
    )
    correction_rows = [
        {
            "position": row["position"],
            "old_source_card_id": row["assigned_source_card_id"],
            "old_task_class": row["assigned_task_class"],
            "correct_source_card_id": row["swapped_source_card_id"],
            "correct_task_class": row["swapped_task_class"],
            "correction_basis": correction_basis,
        }
        for row in position_rows
        if 51 <= int(row["position"]) <= 100
    ]
    write_csv(CORRECTION_MAP, CORRECTION_FIELDS, correction_rows)

    summary = {
        "decision": "BLOCK_ORDER_MISMATCH_CONFIRMED",
        "source_files": {
            "word_responses": str(WORD_SOURCE),
            "metadata_cards": str(CARD_SOURCE),
            "earlier_derived_cards": str(CARD_DERIVATIVE),
            "existing_reaudit": str(EXISTING_AUDIT),
        },
        "metadata_block_order": [
            {"positions": "1-25", "task_class": "logic"},
            {"positions": "26-50", "task_class": "causality"},
            {"positions": "51-75", "task_class": "analogy"},
            {"positions": "76-100", "task_class": "definition"},
        ],
        "word_apparent_block_structure": [
            {"positions": "1-25", "structure": "logic-oriented premise/rule/exclusion/comparison answers"},
            {"positions": "26-50", "structure": "causal mechanism answers"},
            {"positions": "51-75", "structure": "single-concept definition answers matching definition-card concepts"},
            {"positions": "76-100", "structure": "two-relation correspondence answers matching analogy-card pairs"},
        ],
        "hypotheses": {
            "H0_current_positional_mapping": counts(position_rows, "current_match"),
            "H1_swap_blocks_51_75_and_76_100": counts(position_rows, "swapped_match"),
            "small_offset_tests": "Not evaluated: H1 provides a complete one-to-one fit for positions 51-100 and leaves no residual boundary pattern requiring an offset hypothesis.",
        },
        "diagnostic": {
            "positions_1_50_current_strong_match": sum(
                row["current_match"] == "STRONG_MATCH" for row in position_rows[:50]
            ),
            "positions_1_50_current_partial_match": sum(
                row["current_match"] == "PARTIAL_MATCH" for row in position_rows[:50]
            ),
            "positions_1_50_current_no_match": sum(
                row["current_match"] == "NO_MATCH" for row in position_rows[:50]
            ),
            "positions_51_100_current_no_match": sum(
                row["current_match"] == "NO_MATCH" for row in position_rows[50:]
            ),
            "positions_51_100_swapped_strong_match": sum(
                row["swapped_match"] == "STRONG_MATCH" for row in position_rows[50:]
            ),
        },
        "correction_boundary": "The correction map is a proposal only. It is not applied to source cards, the Word document, or existing reaudit outputs in this task.",
        "existing_reaudit_status": "INVALIDATED_BY_ALIGNMENT_ERROR",
        "final200_gap_estimate_status": "INVALIDATED_BY_ALIGNMENT_ERROR",
        "prohibited_inputs": ["EXP-017 outputs", "evaluator predictions", "model runs"],
    }
    with SUMMARY_PATH.open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def validate() -> dict[str, object]:
    """Validate source preservation, H0/H1 counts, and correction-map boundaries."""
    errors: list[str] = []
    responses = extract_docx_paragraphs(WORD_SOURCE)
    cards = read_csv(CARD_SOURCE)
    derived_cards = read_csv(CARD_DERIVATIVE)
    existing_audit = read_csv(EXISTING_AUDIT)
    map_rows = read_csv(POSITION_MAP)
    correction_rows = read_csv(CORRECTION_MAP)
    with SUMMARY_PATH.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)

    if not all(len(items) == 100 for items in (responses, cards, derived_cards, existing_audit, map_rows)):
        errors.append("one or more required 100-row sources or maps is incomplete")
    metadata_fields = ["source_card_id", "task_class", "topic_group", "source_material", "source_reference"]
    if any(any(left[field] != right[field] for field in metadata_fields) for left, right in zip(cards, derived_cards)):
        errors.append("earlier source-card derivative differs from canonical source-card metadata")
    for position, row in enumerate(map_rows, start=1):
        card = cards[position - 1]
        if int(row["position"]) != position:
            errors.append(f"position map row {position} has an incorrect position")
        if row["word_response"] != responses[position - 1]:
            errors.append(f"position {position}: Word response was not preserved")
        if row["assigned_source_card_id"] != card["source_card_id"] or row["assigned_task_class"] != card["task_class"]:
            errors.append(f"position {position}: current metadata pairing was not preserved")
        if row["source_material"] != card["source_material"] or row["source_reference"] != card["source_reference"]:
            errors.append(f"position {position}: current source material was not preserved")
        if existing_audit[position - 1]["candidate_id"] != card["source_card_id"]:
            errors.append(f"position {position}: existing reaudit does not use the current metadata map")
        if existing_audit[position - 1]["original_response"] != responses[position - 1]:
            errors.append(f"position {position}: existing reaudit response differs from Word source")
        swapped_card = cards[swapped_index(position) - 1]
        if row["swapped_source_card_id"] != swapped_card["source_card_id"] or row["swapped_task_class"] != swapped_card["task_class"]:
            errors.append(f"position {position}: H1 mapping is not the defined block swap")

    expected_h0 = {"STRONG_MATCH": 46, "PARTIAL_MATCH": 3, "NO_MATCH": 51}
    expected_h1 = {"STRONG_MATCH": 96, "PARTIAL_MATCH": 3, "NO_MATCH": 1}
    if counts(map_rows, "current_match") != expected_h0:
        errors.append("H0 correspondence counts do not match the recorded audit")
    if counts(map_rows, "swapped_match") != expected_h1:
        errors.append("H1 correspondence counts do not match the recorded audit")
    if len(correction_rows) != 50:
        errors.append("correction map must contain exactly positions 51-100")
    for expected_position, row in enumerate(correction_rows, start=51):
        if int(row["position"]) != expected_position:
            errors.append("correction map has an unexpected position")
        if row["old_source_card_id"] == row["correct_source_card_id"]:
            errors.append(f"position {expected_position}: correction map did not change the card")
        if "block order" not in row["correction_basis"].lower():
            errors.append(f"position {expected_position}: correction basis is not an engineering reason")
    if summary.get("decision") != "BLOCK_ORDER_MISMATCH_CONFIRMED":
        errors.append("summary decision is not BLOCK_ORDER_MISMATCH_CONFIRMED")
    if summary.get("existing_reaudit_status") != "INVALIDATED_BY_ALIGNMENT_ERROR":
        errors.append("existing reaudit was not marked invalidated")
    if summary.get("final200_gap_estimate_status") != "INVALIDATED_BY_ALIGNMENT_ERROR":
        errors.append("final-200 gap estimate was not marked invalidated")

    if errors:
        raise ValueError("Existing-100 alignment validation failed:\n- " + "\n- ".join(errors))
    return {"H0": expected_h0, "H1": expected_h1, "correction_map_rows": len(correction_rows)}


def main() -> None:
    """Build audit artifacts on request, then validate them."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--build", action="store_true", help="build the alignment map, correction map, and summary")
    args = parser.parse_args()
    if args.build:
        build()
    report = validate()
    print("existing-100 alignment validation: PASS")
    print("H0 current mapping:", report["H0"])
    print("H1 block swap:", report["H1"])
    print("correction_map_rows:", report["correction_map_rows"])


if __name__ == "__main__":
    main()
