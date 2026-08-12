"""Validate the blank Markdown and CSV export of the locked random-40 review."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
SAMPLE = DATA / "final200_human_audit_sample.csv"
LOCKED = DATA / "final200_pre_human_audit_locked.csv"
TEMPLATE = DATA / "final200_random40_human_review_template.csv"
MARKDOWN = ROOT.parents[1] / "docs" / "experiments" / "EXP-019-FINAL200-RANDOM40-HUMAN-REVIEW.md"
TEMPLATE_FIELDS = ["review_index", "candidate_id", "task_class", "response_text", "human_decision", "human_reason"]
SECTION = re.compile(
    r"^## (?P<index>\d{2})\n\n\*\*ID:\*\* `(?P<candidate_id>[^`]+)`\n\n\*\*Class:\*\* `(?P<task_class>[^`]+)`\n\n\*\*Response:\*\* (?P<response>.*?)\n\n\*\*Decision:\*\*\n\n\*\*Reason:\*\*\n\n---$",
    re.MULTILINE,
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    sample = read_csv(SAMPLE)
    locked = {row["candidate_id"]: row for row in read_csv(LOCKED)}
    template = read_csv(TEMPLATE)
    markdown = MARKDOWN.read_text(encoding="utf-8")
    sections = list(SECTION.finditer(markdown))
    require(len(sample) == 40 and len({row["candidate_id"] for row in sample}) == 40, "input sample is not exactly 40 unique IDs")
    require(len(sections) == 40, f"Markdown contains {len(sections)} candidate sections, not 40")
    require(len(template) == 40 and len({row["candidate_id"] for row in template}) == 40, "template is not exactly 40 unique rows")
    require(list(template[0]) == TEMPLATE_FIELDS, "template CSV schema mismatch")
    for index, (sample_row, section, template_row) in enumerate(zip(sample, sections, template, strict=True), start=1):
        candidate_id = sample_row["candidate_id"]
        authoritative = locked.get(candidate_id)
        require(authoritative is not None, f"sample candidate missing from locked pool: {candidate_id}")
        require(sample_row["task_class"] == authoritative["task_class"], f"sample class mismatch: {candidate_id}")
        require(section.group("index") == f"{index:02d}", f"Markdown sequence mismatch at {candidate_id}")
        require(section.group("candidate_id") == candidate_id, f"Markdown ID mismatch: {candidate_id}")
        require(section.group("task_class") == authoritative["task_class"], f"Markdown class mismatch: {candidate_id}")
        require(section.group("response") == authoritative["response_text"], f"Markdown response differs from locked pool: {candidate_id}")
        require(template_row["review_index"] == str(index), f"template index mismatch: {candidate_id}")
        require(template_row["candidate_id"] == candidate_id and template_row["task_class"] == authoritative["task_class"], f"template metadata mismatch: {candidate_id}")
        require(template_row["response_text"] == authoritative["response_text"], f"template response mismatch: {candidate_id}")
        require(not template_row["human_decision"] and not template_row["human_reason"], f"template judgment is prefilled: {candidate_id}")
    require("**Probability:**" not in markdown and "**Prediction:**" not in markdown and "EXP-017" not in markdown, "forbidden evaluator or EXP-017 content in Markdown")
    print("RANDOM40_REVIEW_EXPORT_VALIDATION_PASS")
    print("markdown_sections:", len(sections))
    print("template_rows:", len(template))
    print("decisions_blank: true")
    print("reasons_blank: true")
    print("locked_text_authoritative: true")


if __name__ == "__main__":
    main()
