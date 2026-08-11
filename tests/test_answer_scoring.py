"""Tests for conservative EXP-011 short-answer scoring."""

from src.answer_scoring import (
    exact_normalized_match,
    normalize_answer,
    score_answer,
    short_answer_substring_risk,
    word_boundary_contains,
)


def test_normalize_answer_removes_prefix_and_punctuation() -> None:
    assert normalize_answer("The answer is NO.") == "no"


def test_normalize_answer_collapses_whitespace() -> None:
    assert normalize_answer("  Wet   roads! ") == "wet roads"


def test_exact_normalized_match() -> None:
    assert exact_normalized_match("Evaporation.", "evaporation")


def test_boundary_match_for_no() -> None:
    assert word_boundary_contains("no", "no")


def test_boundary_match_for_prefixed_no() -> None:
    assert word_boundary_contains("The answer is no.", "no")


def test_boundary_match_rejects_known() -> None:
    assert not word_boundary_contains("known", "no")


def test_boundary_match_rejects_another() -> None:
    assert not word_boundary_contains("another", "no")


def test_boundary_match_rejects_not() -> None:
    assert not word_boundary_contains("not", "no")


def test_boundary_match_for_phrase() -> None:
    assert word_boundary_contains("wet roads", "wet roads")


def test_boundary_match_for_phrase_in_response() -> None:
    assert word_boundary_contains("The result is wet roads.", "wet roads")


def test_score_answer_accepts_multiple_answers() -> None:
    assert score_answer("The answer is a kennel.", ["kennel", "a kennel"])


def test_legacy_contains_is_available() -> None:
    assert score_answer("known", ["no"], scoring_rule="case_insensitive_contains")


def test_short_answer_risk_for_no() -> None:
    assert short_answer_substring_risk("no")


def test_short_answer_risk_for_yes() -> None:
    assert not short_answer_substring_risk("yes")


def test_short_answer_risk_for_evaporation() -> None:
    assert not short_answer_substring_risk("evaporation")
