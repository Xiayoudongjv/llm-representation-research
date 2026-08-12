"""Mock-based tests for optional offline Hugging Face loading arguments."""

from pathlib import Path
from unittest.mock import patch

import torch

from src.model_loader import load_causal_lm, load_tokenizer


def test_tokenizer_forwards_cache_dir_and_local_only():
    with patch("src.model_loader.AutoTokenizer.from_pretrained") as mocked:
        load_tokenizer("org/model", cache_dir=Path("external-cache"), local_files_only=True)
    mocked.assert_called_once_with("org/model", cache_dir="external-cache", local_files_only=True)


def test_model_forwards_cache_dir_and_local_only():
    with patch("src.model_loader.AutoModelForCausalLM.from_pretrained") as mocked:
        load_causal_lm("org/model", cache_dir=Path("external-cache"), local_files_only=True)
    mocked.assert_called_once_with("org/model", dtype=torch.float16, device_map="auto", cache_dir="external-cache", local_files_only=True)


def test_default_loader_behavior_remains_compatible():
    with patch("src.model_loader.AutoTokenizer.from_pretrained") as tokenizer_mock, patch("src.model_loader.AutoModelForCausalLM.from_pretrained") as model_mock:
        load_tokenizer("org/model")
        load_causal_lm("org/model")
    tokenizer_mock.assert_called_once_with("org/model")
    model_mock.assert_called_once_with("org/model", dtype=torch.float16, device_map="auto")
