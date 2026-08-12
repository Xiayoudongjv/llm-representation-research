"""Synthetic-only tests for the EXP-019 fast human-audit interaction."""

from __future__ import annotations

import csv
import sys
from pathlib import Path


EXP019 = Path(__file__).resolve().parents[1] / "experiments" / "exp019"
if str(EXP019) not in sys.path:
    sys.path.insert(0, str(EXP019))

from review_final200_human_audit import SIMILARITY_FIELDS, run_review, run_similarity_review, status


SAMPLE_FIELDS = ["candidate_id", "task_class", "response_text", "provenance", "topic_domain", "human_label_agreement", "human_naturalness", "human_self_contained", "human_ambiguity", "human_notes"]
LOCK_FIELDS = ["candidate_id", "task_class", "response_text", "provenance", "source_reference", "topic_domain", "length_tokens", "length_band"]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def inputs(values: list[str]):
    iterator = iter(values)
    return lambda _prompt: next(iterator)


def locked_rows() -> list[dict[str, str]]:
    return [
        {"candidate_id": "A", "task_class": "logic", "response_text": "A rule applies.", "provenance": "rule_composed", "source_reference": "test", "topic_domain": "test", "length_tokens": "3", "length_band": "short"},
        {"candidate_id": "B", "task_class": "causality", "response_text": "Heat changes wax.", "provenance": "rule_composed", "source_reference": "test", "topic_domain": "test", "length_tokens": "3", "length_band": "short"},
        {"candidate_id": "C", "task_class": "analogy", "response_text": "A map mirrors a guide.", "provenance": "rule_composed", "source_reference": "test", "topic_domain": "test", "length_tokens": "5", "length_band": "short"},
    ]


def blank_sample(locked: list[dict[str, str]]) -> list[dict[str, str]]:
    return [{"candidate_id": row["candidate_id"], "task_class": row["task_class"], "response_text": row["response_text"], "provenance": row["provenance"], "topic_domain": row["topic_domain"], "human_label_agreement": "", "human_naturalness": "", "human_self_contained": "", "human_ambiguity": "", "human_notes": ""} for row in locked]


def test_one_key_pass_and_resume_preserves_completed_rows(tmp_path: Path) -> None:
    locked, sample = tmp_path / "locked.csv", tmp_path / "sample.csv"
    source = locked_rows()
    write_csv(locked, LOCK_FIELDS, source)
    initial = blank_sample(source)
    initial[0].update({"human_label_agreement": "agree", "human_naturalness": "natural", "human_self_contained": "yes", "human_ambiguity": "clear", "human_notes": "already reviewed"})
    write_csv(sample, SAMPLE_FIELDS, initial)
    run_review(sample, locked, inputs(["y", "q"]), lambda *_: None)
    result = rows(sample)
    assert result[0]["human_notes"] == "already reviewed"
    assert result[1]["human_label_agreement"] == "agree"
    assert result[1]["human_naturalness"] == "acceptable"
    assert result[1]["human_self_contained"] == "yes"
    assert result[1]["human_ambiguity"] == "clear"
    assert not result[2]["human_label_agreement"]


def test_issue_language_branch_requires_confirmation(tmp_path: Path) -> None:
    locked, sample = tmp_path / "locked.csv", tmp_path / "sample.csv"
    source = locked_rows()[:1]
    write_csv(locked, LOCK_FIELDS, source)
    write_csv(sample, SAMPLE_FIELDS, blank_sample(source))
    run_review(sample, locked, inputs(["n", "2", "w", "n", "b", "note", "y"]), lambda *_: None)
    result = rows(sample)[0]
    assert result["human_label_agreement"] == "agree"
    assert result["human_naturalness"] == "awkward"
    assert result["human_self_contained"] == "no"
    assert result["human_ambiguity"] == "borderline"
    assert result["human_notes"] == "note"


def test_similarity_one_key_and_status(tmp_path: Path) -> None:
    locked, similarity, sample = tmp_path / "locked.csv", tmp_path / "similarity.csv", tmp_path / "sample.csv"
    source = locked_rows()
    write_csv(locked, LOCK_FIELDS, source)
    write_csv(sample, SAMPLE_FIELDS, blank_sample(source))
    write_csv(similarity, list(SIMILARITY_FIELDS), [
        {"candidate_id": "A", "task_class": "logic", "response_text": source[0]["response_text"], "flag_type": "prefix", "matched_candidate_id": "B", "similarity_value_if_available": "", "human_redundancy_decision": "", "human_notes": ""},
        {"candidate_id": "B", "task_class": "causality", "response_text": source[1]["response_text"], "flag_type": "tfidf", "matched_candidate_id": "C", "similarity_value_if_available": "0.6", "human_redundancy_decision": "", "human_notes": ""},
        {"candidate_id": "C", "task_class": "analogy", "response_text": source[2]["response_text"], "flag_type": "prefix", "matched_candidate_id": "A", "similarity_value_if_available": "", "human_redundancy_decision": "", "human_notes": ""},
    ])
    run_similarity_review(similarity, locked, inputs(["y", "n", "u"]), lambda *_: None)
    assert [row["human_redundancy_decision"] for row in rows(similarity)] == ["distinct_enough", "redundant", "uncertain"]
    lines: list[str] = []
    status(sample, similarity, lambda *value: lines.append(" ".join(map(str, value))))
    assert any("completed / total: 3/3" in line for line in lines)
