"""Synthetic fail-closed offline and atomic-publication tests for EXP-018."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from experiments.exp018 import independent_validation as runner


def test_resolve_cache_root_uses_hf_home(monkeypatch, tmp_path):
    monkeypatch.setenv("HF_HOME", str(tmp_path))
    assert runner.resolve_cache_root() == tmp_path.resolve()


def test_missing_cache_root_fails_before_scientific_execution(monkeypatch):
    monkeypatch.delenv("HF_HOME", raising=False)
    with pytest.raises(RuntimeError, match="HF_HOME"):
        runner.resolve_cache_root()


def test_model_cache_resolution_supports_root_and_hub_layouts(tmp_path):
    (tmp_path / "models--google--gemma-3-1b-it").mkdir()
    (tmp_path / "hub" / "models--Qwen--Qwen3-1.7B").mkdir(parents=True)
    assert runner.resolve_model_cache_dir("google/gemma-3-1b-it", tmp_path) == tmp_path
    assert runner.resolve_model_cache_dir("Qwen/Qwen3-1.7B", tmp_path) == tmp_path / "hub"


def test_preflight_forwards_local_only_to_every_loader(tmp_path):
    config = {"models": [{"name": "org/model"}]}
    (tmp_path / "models--org--model").mkdir()
    with patch("src.model_loader.check_cuda_or_raise"), patch("src.model_loader.load_model_config") as config_loader, patch("src.model_loader.load_tokenizer") as tokenizer_loader, patch("src.model_loader.load_causal_lm") as model_loader, patch("torch.cuda.empty_cache"):
        resolved = runner.preflight_model_resources(config, tmp_path, "float16")
    assert resolved == {"org/model": tmp_path}
    for mocked in (config_loader, tokenizer_loader, model_loader):
        assert mocked.call_args.kwargs["cache_dir"] == tmp_path
        assert mocked.call_args.kwargs["local_files_only"] is True


def test_preflight_failure_prevents_scientific_run(tmp_path):
    config, prompts = {"models": []}, []
    with patch.object(runner, "preflight_model_resources", side_effect=RuntimeError("missing local artifact")), patch.object(runner, "run_validation") as scientific_run:
        with pytest.raises(RuntimeError, match="missing local artifact"):
            runner.execute_official_validation(config, prompts, "float16", tmp_path)
    scientific_run.assert_not_called()


def test_atomic_publication_does_not_expose_final_directory_on_staging_failure(tmp_path):
    output_dir = tmp_path / "results" / "exp018"
    config = runner.load_frozen_config()
    with patch.object(runner, "write_csv", side_effect=RuntimeError("write failed")):
        with pytest.raises(RuntimeError, match="write failed"):
            runner.publish_outputs_atomically([], [], [], [], config, output_dir)
    assert not output_dir.exists()


def test_atomic_publication_publishes_all_six_files_together(tmp_path):
    output_dir = tmp_path / "results" / "exp018"
    config = runner.load_frozen_config()
    transition = [{field: 0 for field in runner.TRANSITION_FIELDS}]
    probe = [{field: 0 for field in runner.PROBE_FIELDS}]
    invariant = [{field: 0 for field in runner.INVARIANT_FIELDS}]
    pair = [{field: 0 for field in runner.PAIR_SUMMARY_FIELDS}]
    runner.publish_outputs_atomically(transition, probe, invariant, pair, config, output_dir)
    assert {path.name for path in output_dir.iterdir()} == {
        "transition_metrics.csv", "probe_metrics.csv", "invariant_metrics.csv",
        "pair_summary.csv", "validation_summary.json", "split_metadata.json",
    }
