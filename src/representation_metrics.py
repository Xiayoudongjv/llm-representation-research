"""Metrics for comparing model representations."""

from __future__ import annotations

import numpy as np
import torch
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score


def l2_normalize(x: torch.Tensor | np.ndarray):
    """Normalize a vector or matrix along its final dimension."""
    if isinstance(x, torch.Tensor):
        return x / torch.linalg.vector_norm(x, dim=-1, keepdim=True).clamp_min(torch.finfo(x.dtype).eps)
    array = np.asarray(x)
    norms = np.linalg.norm(array, axis=-1, keepdims=True)
    return array / np.maximum(norms, np.finfo(array.dtype if np.issubdtype(array.dtype, np.floating) else np.float64).eps)


def cosine_similarity_matrix(representations: torch.Tensor | np.ndarray) -> np.ndarray:
    """Return pairwise cosine similarities for representations shaped [n, d]."""
    normalized = np.asarray(l2_normalize(representations), dtype=np.float64)
    return normalized @ normalized.T


def pca_2d(representations: torch.Tensor | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Project representations to two dimensions with sklearn PCA."""
    array = np.asarray(representations.detach().cpu() if isinstance(representations, torch.Tensor) else representations)
    if np.allclose(np.var(array, axis=0), 0.0):
        return np.zeros((array.shape[0], 2), dtype=float), np.zeros(2, dtype=float)
    pca = PCA(n_components=2)
    coords = pca.fit_transform(array)
    return coords, pca.explained_variance_ratio_


def mean_within_group_similarity(similarity_matrix, groups) -> tuple[float, dict[str, float]]:
    """Return overall and per-group mean similarities, excluding diagonals."""
    similarity = np.asarray(similarity_matrix, dtype=float)
    labels = list(groups)
    per_group = {}
    within_values = []
    for group in dict.fromkeys(labels):
        indices = [index for index, label in enumerate(labels) if label == group]
        values = [similarity[i, j] for position, i in enumerate(indices) for j in indices[position + 1:]]
        per_group[group] = float(np.mean(values)) if values else float("nan")
        within_values.extend(values)
    return (float(np.mean(within_values)) if within_values else float("nan")), per_group


def mean_between_group_similarity(similarity_matrix, groups) -> float:
    """Return the mean similarity for pairs from different groups."""
    similarity = np.asarray(similarity_matrix, dtype=float)
    labels = list(groups)
    values = [similarity[i, j] for i in range(len(labels)) for j in range(i + 1, len(labels)) if labels[i] != labels[j]]
    return float(np.mean(values)) if values else float("nan")


def separation_score(within_mean: float, between_mean: float) -> float:
    """Compute within-group similarity minus between-group similarity."""
    return float(within_mean - between_mean)


def compute_silhouette(representations, groups) -> float:
    """Compute a cosine-distance silhouette score."""
    array = np.asarray(representations.detach().cpu() if isinstance(representations, torch.Tensor) else representations)
    return float(silhouette_score(array, list(groups), metric="cosine"))


def group_centroid_distances(representations, groups) -> dict[str, dict[str, float]]:
    """Return pairwise cosine distances between group centroids."""
    array = np.asarray(representations.detach().cpu() if isinstance(representations, torch.Tensor) else representations, dtype=float)
    labels = list(groups)
    unique_groups = list(dict.fromkeys(labels))
    centroids = {group: array[[label == group for label in labels]].mean(axis=0) for group in unique_groups}
    normalized = {group: l2_normalize(centroid) for group, centroid in centroids.items()}
    distances = {}
    for group_a in unique_groups:
        distances[group_a] = {}
        for group_b in unique_groups:
            distances[group_a][group_b] = float(1.0 - np.dot(normalized[group_a], normalized[group_b]))
    return distances
