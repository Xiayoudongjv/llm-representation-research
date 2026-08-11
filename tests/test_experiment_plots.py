import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from src.experiment_plots import (
    save_bar_plot,
    save_heatmap,
    save_line_plot,
    save_scatter_plot,
)


def assert_nonempty(path):
    assert path.exists()
    assert path.stat().st_size > 0


def test_save_line_plot_creates_png(tmp_path):
    path = tmp_path / "nested" / "line.png"
    save_line_plot([0, 1], {"score": [1, 2]}, path)
    assert_nonempty(path)


def test_save_bar_plot_creates_png(tmp_path):
    path = tmp_path / "bar.png"
    save_bar_plot(["a", "b"], [1, 2], path)
    assert_nonempty(path)


def test_save_scatter_plot_creates_png(tmp_path):
    path = tmp_path / "scatter.png"
    save_scatter_plot([0, 1], [1, 2], path)
    assert_nonempty(path)


def test_save_scatter_plot_with_labels_creates_png(tmp_path):
    path = tmp_path / "labeled_scatter.png"
    save_scatter_plot([0, 1], [1, 2], path, labels=["a", "b"])
    assert_nonempty(path)


def test_save_heatmap_creates_png(tmp_path):
    path = tmp_path / "heatmap.png"
    save_heatmap(np.ones((2, 3)), ["r1", "r2"], ["c1", "c2", "c3"], path)
    assert_nonempty(path)


def test_save_bar_plot_rejects_mismatched_lengths(tmp_path):
    with pytest.raises(ValueError, match="same length"):
        save_bar_plot(["a"], [1, 2], tmp_path / "bar.png")


def test_save_heatmap_rejects_mismatched_row_labels(tmp_path):
    with pytest.raises(ValueError, match="same length"):
        save_heatmap(np.ones((2, 2)), ["r1"], ["c1", "c2"], tmp_path / "heatmap.png")


def test_save_heatmap_rejects_mismatched_col_labels(tmp_path):
    with pytest.raises(ValueError, match="same length"):
        save_heatmap(np.ones((2, 2)), ["r1", "r2"], ["c1"], tmp_path / "heatmap.png")
