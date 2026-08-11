"""Proxy relational-invariant metrics for representation transitions."""

from __future__ import annotations

import numpy as np
from scipy.stats import spearmanr


def representation_similarity_matrix(representations) -> np.ndarray:
    """Return a cosine similarity matrix for representations shaped [n, d]."""
    array = np.asarray(representations, dtype=float)
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    normalized = array / np.maximum(norms, 1e-12)
    return normalized @ normalized.T


def upper_triangle_values(matrix) -> np.ndarray:
    """Return upper-triangle values excluding the diagonal."""
    array = np.asarray(matrix, dtype=float)
    indices = np.triu_indices_from(array, k=1)
    return array[indices]


def rsm_correlation(before_matrix, after_matrix, method: str = "pearson") -> float:
    """Correlate upper-triangle RSM values using Pearson or Spearman correlation."""
    before = upper_triangle_values(before_matrix)
    after = upper_triangle_values(after_matrix)
    if before.size == 0 or np.std(before) < 1e-12 or np.std(after) < 1e-12:
        return 0.0
    if method == "pearson":
        correlation = np.corrcoef(before, after)[0, 1]
    elif method == "spearman":
        correlation = spearmanr(before, after).statistic
    else:
        raise ValueError("method must be 'pearson' or 'spearman'")
    return float(correlation) if np.isfinite(correlation) else 0.0


def invariant_violation_score(before_matrix, after_matrix) -> float:
    """Return 1 minus Pearson RSM correlation."""
    return float(1.0 - rsm_correlation(before_matrix, after_matrix, method="pearson"))


def rsm_frobenius_distance(before_matrix, after_matrix) -> float:
    """Return the Frobenius distance between two RSMs."""
    return float(np.linalg.norm(np.asarray(before_matrix) - np.asarray(after_matrix)))


def summarize_invariant_metrics(before_reps, after_reps) -> dict[str, float]:
    """Compute JSON-serializable RSM preservation metrics."""
    before_matrix = representation_similarity_matrix(before_reps)
    after_matrix = representation_similarity_matrix(after_reps)
    return {
        "rsm_pearson": rsm_correlation(before_matrix, after_matrix, method="pearson"),
        "rsm_spearman": rsm_correlation(before_matrix, after_matrix, method="spearman"),
        "invariant_violation_score": invariant_violation_score(before_matrix, after_matrix),
        "rsm_frobenius_distance": rsm_frobenius_distance(before_matrix, after_matrix),
    }
