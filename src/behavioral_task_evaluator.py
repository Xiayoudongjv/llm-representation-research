"""Stable inference API for the frozen EXP-019 behavioral task evaluator.

The classifier estimates task-style identity from response text only.  It is
not a correctness, reasoning-quality, or semantic-validity evaluator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib


CLASS_ORDER = ("logic", "causality", "analogy", "definition")
# scikit-learn's LogisticRegression exposes its probability columns in this
# lexical label order.  Keep it explicit so downstream consumers never infer
# a different order from an arbitrary dataset.
SKLEARN_MODEL_CLASS_ORDER = ("analogy", "causality", "definition", "logic")
MODEL_COLUMN_BY_CLASS = {label: index for index, label in enumerate(SKLEARN_MODEL_CLASS_ORDER)}


def load_evaluator(path: str | Path):
    """Load the persisted TF-IDF plus logistic-regression pipeline."""
    return joblib.load(Path(path))


def predict_proba(evaluator, response_texts: Iterable[str]) -> list[dict[str, float]]:
    """Return probabilities keyed by the explicitly frozen class order."""
    texts = list(response_texts)
    probabilities = evaluator.predict_proba(texts)
    observed_order = tuple(evaluator.classes_)
    if observed_order != SKLEARN_MODEL_CLASS_ORDER:
        raise ValueError(f"Unexpected evaluator model class order: {observed_order}")
    return [{label: float(row[MODEL_COLUMN_BY_CLASS[label]]) for label in CLASS_ORDER} for row in probabilities]


def predict_task(evaluator, response_texts: Iterable[str]) -> list[str]:
    """Return predicted classes using the explicitly frozen class order."""
    probabilities = predict_proba(evaluator, response_texts)
    return [max(CLASS_ORDER, key=probability.__getitem__) for probability in probabilities]
