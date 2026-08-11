"""Shared matplotlib helpers for compact experiment figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def _ensure_parent_dir(output_path: str | Path) -> Path:
    """Create the output parent directory and return the output Path."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    return output


def _validate_same_length(a, b, name_a: str = "a", name_b: str = "b") -> None:
    """Raise ValueError unless two sequences have equal lengths."""
    if len(a) != len(b):
        raise ValueError(f"{name_a} and {name_b} must have the same length; got {len(a)} and {len(b)}.")


def save_line_plot(x, series, output_path, title=None, xlabel=None, ylabel=None) -> None:
    """Save one default-style line for each named series."""
    for name, values in series.items():
        _validate_same_length(x, values, "x", name)
    output = _ensure_parent_dir(output_path)
    figure, axis = plt.subplots()
    for name, values in series.items():
        axis.plot(x, values, marker="o", label=name)
    if title is not None:
        axis.set_title(title)
    if xlabel is not None:
        axis.set_xlabel(xlabel)
    if ylabel is not None:
        axis.set_ylabel(ylabel)
    if series:
        axis.legend()
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def save_bar_plot(labels, values, output_path, title=None, xlabel=None, ylabel=None) -> None:
    """Save a default-style bar chart after validating labels and values."""
    _validate_same_length(labels, values, "labels", "values")
    output = _ensure_parent_dir(output_path)
    figure, axis = plt.subplots()
    axis.bar(labels, values)
    if title is not None:
        axis.set_title(title)
    if xlabel is not None:
        axis.set_xlabel(xlabel)
    if ylabel is not None:
        axis.set_ylabel(ylabel)
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def save_scatter_plot(x, y, output_path, title=None, xlabel=None, ylabel=None, labels=None) -> None:
    """Save a scatter plot and optionally annotate each point."""
    _validate_same_length(x, y, "x", "y")
    if labels is not None:
        _validate_same_length(x, labels, "x", "labels")
    output = _ensure_parent_dir(output_path)
    figure, axis = plt.subplots()
    axis.scatter(x, y)
    if labels is not None:
        for x_value, y_value, label in zip(x, y, labels):
            axis.annotate(label, (x_value, y_value))
    if title is not None:
        axis.set_title(title)
    if xlabel is not None:
        axis.set_xlabel(xlabel)
    if ylabel is not None:
        axis.set_ylabel(ylabel)
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)


def save_heatmap(matrix, row_labels, col_labels, output_path, title=None, colorbar_label=None) -> None:
    """Save a matrix with row and column labels using matplotlib imshow."""
    array = np.asarray(matrix)
    if array.ndim != 2:
        raise ValueError(f"matrix must be two-dimensional; got shape {array.shape}.")
    _validate_same_length(row_labels, array, "row_labels", "matrix rows")
    _validate_same_length(col_labels, array.T, "col_labels", "matrix columns")
    output = _ensure_parent_dir(output_path)
    figure, axis = plt.subplots()
    image = axis.imshow(array, aspect="auto")
    axis.set_xticks(range(len(col_labels)), col_labels)
    axis.set_yticks(range(len(row_labels)), row_labels)
    if title is not None:
        axis.set_title(title)
    if colorbar_label is not None:
        figure.colorbar(image, ax=axis, label=colorbar_label)
    figure.tight_layout()
    figure.savefig(output)
    plt.close(figure)
