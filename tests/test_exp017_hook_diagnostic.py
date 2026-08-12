"""Unit tests for the output-structure handling used by the hook diagnostic."""

import pytest
import torch

from experiments.exp017.hook_diagnostic import LastTokenHook, locate_hidden_state_output


def test_locate_hidden_state_output_handles_direct_tensor():
    tensor = torch.zeros(1, 3, 4)
    found, location, replace = locate_hidden_state_output(tensor)
    assert found is tensor
    assert location == "output"
    assert torch.equal(replace(torch.ones_like(tensor)), torch.ones_like(tensor))


def test_last_token_hook_replaces_tuple_hidden_state_only_at_last_position():
    hidden = torch.zeros(1, 3, 4)
    marker = torch.ones(1, 2)
    hook = LastTokenHook(torch.tensor([1.0, 0.0, 0.0, 0.0]))
    result = hook(None, (), (hidden, marker))
    assert torch.equal(result[0][:, :-1, :], hidden[:, :-1, :])
    assert torch.equal(result[0][0, -1], torch.tensor([1.0, 0.0, 0.0, 0.0]))
    assert result[1] is marker
    assert hook.events[0].hidden_state_location == "output[0]"


def test_locate_hidden_state_output_rejects_ambiguous_tuple():
    with pytest.raises(ValueError, match="exactly one"):
        locate_hidden_state_output((torch.zeros(1, 1, 2), torch.zeros(1, 1, 2)))
