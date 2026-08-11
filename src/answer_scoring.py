"""Conservative normalization and matching for short-answer evaluation."""

from __future__ import annotations

import re
from collections.abc import Iterable


_PREFIX_PATTERN = re.compile(r"^(?:the answer is\s+|answer:\s*|it is\s+)")
_TRAILING_PUNCTUATION = ".,!?:;"


def normalize_answer(text: str) -> str:
    """Lowercase and lightly normalize an answer without semantic expansion."""
    normalized = " ".join(str(text).lower().strip().split())
    normalized = _PREFIX_PATTERN.sub("", normalized)
    return normalized.rstrip(_TRAILING_PUNCTUATION).strip()


def exact_normalized_match(model_answer: str, acceptable_answer: str) -> bool:
    """Return whether two answers are identical after conservative normalization."""
    return normalize_answer(model_answer) == normalize_answer(acceptable_answer)


def word_boundary_contains(model_answer: str, acceptable_answer: str) -> bool:
    """Match an acceptable answer only when it has token boundaries in a response."""
    normalized_model = normalize_answer(model_answer)
    normalized_acceptable = normalize_answer(acceptable_answer)
    if not normalized_acceptable:
        return False
    pattern = rf"(?<!\w){re.escape(normalized_acceptable)}(?!\w)"
    return re.search(pattern, normalized_model) is not None


def score_answer(
    model_answer: str,
    acceptable_answers: Iterable[str],
    scoring_rule: str = "boundary_aware",
) -> bool:
    """Score an answer using normalized, boundary-aware, or legacy matching.

    ``case_insensitive_contains`` is retained for reproducibility only. It is
    unsafe for short acceptable answers because a raw substring can occur inside
    an unrelated word.
    """
    normalized_model = normalize_answer(model_answer)
    for acceptable_answer in acceptable_answers:
        normalized_acceptable = normalize_answer(acceptable_answer)
        if scoring_rule == "normalized_exact":
            matched = normalized_model == normalized_acceptable
        elif scoring_rule == "boundary_aware":
            matched = (
                normalized_model == normalized_acceptable
                or word_boundary_contains(normalized_model, normalized_acceptable)
            )
        elif scoring_rule == "case_insensitive_contains":
            matched = normalized_acceptable in normalized_model
        else:
            raise ValueError(f"Unsupported scoring rule: {scoring_rule!r}")
        if matched:
            return True
    return False


def short_answer_substring_risk(answer: str) -> bool:
    """Return whether raw substring matching is especially unsafe for an answer."""
    normalized = normalize_answer(answer)
    return not normalized or (" " not in normalized and len(normalized) <= 2)
