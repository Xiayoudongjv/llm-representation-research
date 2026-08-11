"""Metrics for comparing model representations."""

from __future__ import annotations

import numpy as np
import torch
from sklearn.decomposition import PCA


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
    pca = PCA(n_components=2)
    coords = pca.fit_transform(array)
    return coords, pca.explained_variance_ratio_
