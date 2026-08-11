"""Static representation-space steering helpers."""

from __future__ import annotations

import numpy as np


def compute_group_centroids(representations: np.ndarray, groups: list[str]) -> dict[str, np.ndarray]:
    """Compute one mean representation vector for each group."""
    array = np.asarray(representations, dtype=float)
    labels = list(groups)
    return {
        group: array[[label == group for label in labels]].mean(axis=0)
        for group in dict.fromkeys(labels)
    }


def compute_steering_vector(source_centroid, target_centroid, normalize: bool = True) -> np.ndarray:
    """Return the target-minus-source centroid direction."""
    vector = np.asarray(target_centroid, dtype=float) - np.asarray(source_centroid, dtype=float)
    norm = float(np.linalg.norm(vector))
    if normalize:
        if norm < 1e-12:
            raise ValueError("Cannot normalize a near-zero steering vector.")
        vector = vector / norm
    return vector


def apply_static_steering(representations, steering_vector, alpha: float) -> np.ndarray:
    """Apply h' = h + alpha * v to one or more representations."""
    return np.asarray(representations, dtype=float) + float(alpha) * np.asarray(steering_vector, dtype=float)


def cosine_to_centroids(representations, centroids) -> dict[str, list[float]]:
    """Return cosine similarities from each representation to each centroid."""
    array = np.asarray(representations, dtype=float)
    array_norms = np.linalg.norm(array, axis=1, keepdims=True)
    normalized = array / np.maximum(array_norms, 1e-12)
    result = {}
    for group, centroid in centroids.items():
        centroid_array = np.asarray(centroid, dtype=float)
        centroid_norm = np.linalg.norm(centroid_array)
        if centroid_norm < 1e-12:
            raise ValueError(f"Centroid for group {group!r} has near-zero norm.")
        result[group] = (normalized @ (centroid_array / centroid_norm)).astype(float).tolist()
    return result


def nearest_centroid_labels(representations, centroids) -> tuple[list[str], list[float]]:
    """Assign each representation to its nearest centroid by cosine similarity."""
    similarities = cosine_to_centroids(representations, centroids)
    groups = list(centroids)
    matrix = np.asarray([similarities[group] for group in groups], dtype=float).T
    indices = np.argmax(matrix, axis=1)
    return [groups[index] for index in indices], matrix[np.arange(len(indices)), indices].astype(float).tolist()
