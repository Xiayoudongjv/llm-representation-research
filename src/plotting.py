"""Plotting helpers for representation geometry experiments."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def plot_pca_2d(coords, labels, output_path: str, title: str) -> None:
    """Save a labeled 2D PCA scatter plot."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 7))
    axis.scatter(coords[:, 0], coords[:, 1])
    for (x, y), label in zip(coords, labels):
        axis.annotate(label, (x, y), xytext=(4, 4), textcoords="offset points")
    axis.set_title(title)
    axis.set_xlabel("PCA 1")
    axis.set_ylabel("PCA 2")
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)
