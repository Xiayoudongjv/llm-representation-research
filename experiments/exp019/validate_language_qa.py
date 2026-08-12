"""Validate the first-50 candidate-response language QA artifacts.

This validator checks row structure and workflow safeguards only.  It does not
judge scientific content, generate text, or alter any QA artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


DATA_DIR = Path(__file__).resolve().parent / "data"
QA_PATH = DATA_DIR / "language_qa_first50.csv"
SUMMARY_PATH = DATA_DIR / "language_qa_first50_summary.json"
HUMAN_PATH = DATA_DIR / "language_qa_first50_for_human.csv"
SIMPLE_REVIEW_PATH = DATA_DIR / "language_qa_first50_review_simple.csv"
ATTENTION_ONLY_PATH = DATA_DIR / "language_qa_first50_attention_only.csv"
REWRITE_REQUIRED_PATH = DATA_DIR / "language_qa_first50_rewrite_required.csv"

QA_FIELDS = [
    "candidate_id",
    "task_class",
    "original_response",
    "review_status",
    "corrected_response",
    "reason",
    "semantic_change_guard",
    "human_approved",
]
HUMAN_FIELDS = [
    "candidate_id",
    "task_class",
    "original_response",
    "proposed_response",
    "review_status",
    "reason",
    "human_decision",
    "human_final_response",
]
REWRITE_FIELDS = [
    "candidate_id",
    "task_class",
    "original_response",
    "reason",
    "human_final_response",
    "human_decision",
]
ALLOWED_STATUSES = {
    "PASS",
    "MINOR_GRAMMAR_FIX",
    "MINOR_NATURALNESS_FIX",
    "HUMAN_REWRITE_REQUIRED",
}
REVIEW_ORDER = {
    "HUMAN_REWRITE_REQUIRED": 0,
    "MINOR_NATURALNESS_FIX": 1,
    "MINOR_GRAMMAR_FIX": 2,
    "PASS": 3,
}
FORBIDDEN_TERMS = (
    "exp-017",
    "exp017",
    "no_intervention",
    "task_real",
    "matched_random",
    "opposite",
    "hidden_state",
    "hidden-state",
    "activation",
    "tensor",
    "vector",
    "steering",
    "model_output",
)


def expected_candidate_classes() -> dict[str, str]:
    """Return the frozen first-50 candidate IDs and their task classes."""
    expected = {
        f"SRC-LOG-{index:03d}": "logic" for index in range(1, 26)
    }
    expected.update(
        {f"SRC-CAU-{index:03d}": "causality" for index in range(1, 26)}
    )
    return expected


def read_csv(path: Path) -> list[dict[str, str]]:
    """Read one UTF-8 CSV artifact."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write a UTF-8 CSV file using the supplied, explicit column order."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_review_packets() -> None:
    """Create deterministic human-review views without altering review content."""
    source_rows = read_csv(HUMAN_PATH)
    sorted_rows = sorted(
        source_rows,
        key=lambda item: REVIEW_ORDER[item["review_status"]],
    )

    simple_rows = [{field: row[field] for field in HUMAN_FIELDS} for row in sorted_rows]
    attention_rows = [
        row for row in simple_rows if row["review_status"] != "PASS"
    ]
    rewrite_rows = [
        {field: row[field] for field in REWRITE_FIELDS}
        for row in sorted_rows
        if row["review_status"] == "HUMAN_REWRITE_REQUIRED"
    ]

    write_csv(SIMPLE_REVIEW_PATH, HUMAN_FIELDS, simple_rows)
    write_csv(ATTENTION_ONLY_PATH, HUMAN_FIELDS, attention_rows)
    write_csv(REWRITE_REQUIRED_PATH, REWRITE_FIELDS, rewrite_rows)


def csv_fieldnames(path: Path) -> list[str] | None:
    """Read the UTF-8 header from one CSV artifact."""
    with path.open("r", encoding="utf-8", newline="") as handle:
        return csv.DictReader(handle).fieldnames


def validate_review_packets() -> dict[str, int]:
    """Validate review order, counts, exact field copying, and blank human fields."""
    errors: list[str] = []
    source_rows = read_csv(HUMAN_PATH)
    sorted_rows = sorted(source_rows, key=lambda item: REVIEW_ORDER[item["review_status"]])
    simple_rows = read_csv(SIMPLE_REVIEW_PATH)
    attention_rows = read_csv(ATTENTION_ONLY_PATH)
    rewrite_rows = read_csv(REWRITE_REQUIRED_PATH)

    for path, expected_fields in (
        (SIMPLE_REVIEW_PATH, HUMAN_FIELDS),
        (ATTENTION_ONLY_PATH, HUMAN_FIELDS),
        (REWRITE_REQUIRED_PATH, REWRITE_FIELDS),
    ):
        if csv_fieldnames(path) != expected_fields:
            errors.append(f"{path.name}: header does not match the required schema")

    expected_simple = [{field: row[field] for field in HUMAN_FIELDS} for row in sorted_rows]
    expected_attention = [
        row for row in expected_simple if row["review_status"] != "PASS"
    ]
    expected_rewrite = [
        {field: row[field] for field in REWRITE_FIELDS}
        for row in sorted_rows
        if row["review_status"] == "HUMAN_REWRITE_REQUIRED"
    ]
    if simple_rows != expected_simple:
        errors.append("simple review does not exactly copy and sort the source review rows")
    if attention_rows != expected_attention:
        errors.append("attention-only review does not exactly copy the non-PASS rows")
    if rewrite_rows != expected_rewrite:
        errors.append("rewrite-required review does not exactly copy the required rows")

    for label, rows in (
        ("simple review", simple_rows),
        ("attention-only review", attention_rows),
        ("rewrite-required review", rewrite_rows),
    ):
        for row_number, row in enumerate(rows, start=2):
            if row.get("human_decision", "") or row.get("human_final_response", ""):
                errors.append(f"{label} row {row_number}: human fields must remain blank")

    if len(simple_rows) != 50:
        errors.append(f"expected 50 simple-review rows, found {len(simple_rows)}")
    if len(attention_rows) != 31:
        errors.append(f"expected 31 attention-only rows, found {len(attention_rows)}")
    if len(rewrite_rows) != 16:
        errors.append(f"expected 16 rewrite-required rows, found {len(rewrite_rows)}")

    if errors:
        raise ValueError("Human review packet validation failed:\n- " + "\n- ".join(errors))
    return {
        "simple_review_rows": len(simple_rows),
        "attention_only_rows": len(attention_rows),
        "rewrite_required_rows": len(rewrite_rows),
    }


def validate() -> dict[str, int]:
    """Validate QA rows, the review sheet, and the summary artifact."""
    errors: list[str] = []
    qa_rows = read_csv(QA_PATH)
    human_rows = read_csv(HUMAN_PATH)

    with QA_PATH.open("r", encoding="utf-8", newline="") as handle:
        if csv.DictReader(handle).fieldnames != QA_FIELDS:
            errors.append("language QA CSV header does not match the required schema")
    with HUMAN_PATH.open("r", encoding="utf-8", newline="") as handle:
        if csv.DictReader(handle).fieldnames != HUMAN_FIELDS:
            errors.append("human-review CSV header does not match the required schema")

    expected = expected_candidate_classes()
    if len(qa_rows) != 50:
        errors.append(f"expected exactly 50 QA rows, found {len(qa_rows)}")
    if len(human_rows) != 50:
        errors.append(f"expected exactly 50 human-review rows, found {len(human_rows)}")

    identifiers = [row.get("candidate_id", "") for row in qa_rows]
    if len(set(identifiers)) != len(identifiers):
        errors.append("candidate_id values are not unique")
    if set(identifiers) != set(expected):
        errors.append("candidate IDs do not match the frozen first-50 set")

    for row_number, row in enumerate(qa_rows, start=2):
        candidate_id = row.get("candidate_id", "")
        status = row.get("review_status", "")
        corrected = row.get("corrected_response", "")
        original = row.get("original_response", "")
        guard = row.get("semantic_change_guard", "")

        if row.get("task_class") != expected.get(candidate_id):
            errors.append(f"row {row_number}: task_class differs from frozen candidate mapping")
        if not original:
            errors.append(f"row {row_number}: original_response is empty")
        if not row.get("reason"):
            errors.append(f"row {row_number}: reason is empty")
        if status not in ALLOWED_STATUSES:
            errors.append(f"row {row_number}: unsupported review_status {status!r}")
        if row.get("human_approved", ""):
            errors.append(f"row {row_number}: human_approved must remain blank")

        if status == "PASS":
            if corrected != original:
                errors.append(f"row {row_number}: PASS must preserve original_response")
            if guard != "PASS":
                errors.append(f"row {row_number}: PASS requires semantic guard PASS")
        elif status == "HUMAN_REWRITE_REQUIRED":
            if corrected:
                errors.append(f"row {row_number}: human rewrite rows must have blank corrections")
            if guard != "HUMAN_REQUIRED":
                errors.append(f"row {row_number}: human rewrite rows require HUMAN_REQUIRED guard")
        else:
            if not corrected:
                errors.append(f"row {row_number}: minor fix requires a proposed correction")
            if guard != "UNCHANGED":
                errors.append(f"row {row_number}: minor fix requires UNCHANGED guard")

        searchable = " ".join(row.values()).lower()
        for term in FORBIDDEN_TERMS:
            if term in searchable:
                errors.append(f"row {row_number}: forbidden metadata term {term!r} found")

    human_by_id = {row.get("candidate_id", ""): row for row in human_rows}
    if set(human_by_id) != set(expected):
        errors.append("human-review candidate IDs do not match the frozen first-50 set")
    for candidate_id, qa_row in {row["candidate_id"]: row for row in qa_rows}.items():
        human_row = human_by_id.get(candidate_id, {})
        for field in ("task_class", "original_response", "review_status", "reason"):
            source_field = "corrected_response" if field == "proposed_response" else field
            if field in human_row and field != "proposed_response":
                if human_row[field] != qa_row[source_field]:
                    errors.append(f"human-review row {candidate_id}: {field} differs from QA row")
        if human_row.get("proposed_response", "") != qa_row["corrected_response"]:
            errors.append(f"human-review row {candidate_id}: proposed_response differs from QA correction")
        if human_row.get("human_decision", "") or human_row.get("human_final_response", ""):
            errors.append(f"human-review row {candidate_id}: human fields must remain blank")

    with SUMMARY_PATH.open("r", encoding="utf-8") as handle:
        summary = json.load(handle)
    counts = Counter(row["review_status"] for row in qa_rows)
    expected_summary = {
        "total_rows": len(qa_rows),
        "pass_count": counts["PASS"],
        "minor_grammar_fix_count": counts["MINOR_GRAMMAR_FIX"],
        "minor_naturalness_fix_count": counts["MINOR_NATURALNESS_FIX"],
        "human_rewrite_required_count": counts["HUMAN_REWRITE_REQUIRED"],
        "human_approved_count": 0,
    }
    for key, value in expected_summary.items():
        if summary.get(key) != value:
            errors.append(f"summary field {key!r} is {summary.get(key)!r}, expected {value!r}")
    if summary.get("semantic_guard_failures") != 0:
        errors.append("summary semantic_guard_failures must be zero")

    if errors:
        raise ValueError("Language QA validation failed:\n- " + "\n- ".join(errors))
    return dict(counts)


def main() -> None:
    """Run validation and optionally create deterministic human-review views."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--write-review-packets",
        action="store_true",
        help="create the three derived human-review CSVs, then validate them",
    )
    args = parser.parse_args()
    counts = validate()
    if args.write_review_packets:
        build_review_packets()
    print("language QA validation: PASS")
    print("total_rows: 50")
    for status in sorted(ALLOWED_STATUSES):
        print(f"{status}: {counts.get(status, 0)}")
    print("human_approved_count: 0")
    if args.write_review_packets:
        packet_counts = validate_review_packets()
        for name, value in packet_counts.items():
            print(f"{name}: {value}")


if __name__ == "__main__":
    main()
