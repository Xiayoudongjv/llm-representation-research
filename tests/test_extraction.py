import numpy as np
import pytest
import torch

from src.extraction import (
    extract_last_token_hidden_state,
    get_model_input_device,
    move_tokenized_inputs_to_device,
    tensor_to_numpy_float32,
    validate_layer_index,
)


def test_validate_layer_index_accepts_positive_and_negative_indices():
    assert validate_layer_index(0, 29) == 0
    assert validate_layer_index(28, 29) == 28
    assert validate_layer_index(-1, 29) == 28
    assert validate_layer_index(-2, 29) == 27


def test_validate_layer_index_rejects_out_of_range_indices():
    with pytest.raises(IndexError):
        validate_layer_index(29, 29)
    with pytest.raises(IndexError):
        validate_layer_index(-30, 29)


def test_move_tokenized_inputs_to_device_moves_tensors_and_preserves_other_values():
    marker = object()
    inputs = {"input_ids": torch.tensor([[1, 2]]), "metadata": marker}
    moved = move_tokenized_inputs_to_device(inputs, torch.device("cpu"))
    assert moved["input_ids"].device == torch.device("cpu")
    assert moved["metadata"] is marker


def test_extract_last_token_hidden_state_selects_layer_and_last_token():
    hidden_states = (
        torch.tensor([[[1.0, 2.0], [3.0, 4.0]]]),
        torch.tensor([[[5.0, 6.0], [7.0, 8.0]]]),
    )
    assert torch.equal(extract_last_token_hidden_state(hidden_states, 1), torch.tensor([7.0, 8.0]))
    assert torch.equal(extract_last_token_hidden_state(hidden_states, -1), torch.tensor([7.0, 8.0]))


def test_tensor_to_numpy_float32_converts_and_preserves_shape():
    result = tensor_to_numpy_float32(torch.ones((2, 3), dtype=torch.float64))
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (2, 3)


def test_get_model_input_device_returns_cpu_for_tiny_model():
    model = torch.nn.Linear(2, 2)
    assert get_model_input_device(model) == torch.device("cpu")
