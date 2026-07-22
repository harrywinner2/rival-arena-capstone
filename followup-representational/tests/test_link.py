import sys
from pathlib import Path

import pytest
import torch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from l4_arena.link import OuterLink


def test_same_dimension_shape_and_gradient():
    link = OuterLink(8, 8, hidden_dim=12)
    value = torch.randn(2, 5, 8)
    output = link(value)
    assert output.shape == value.shape
    output.square().mean().backward()
    assert all(parameter.grad is not None for parameter in link.parameters())


def test_cross_dimension_and_bottleneck():
    link = OuterLink(8, 6, bottleneck_dim=3)
    assert link(torch.randn(1, 4, 8)).shape == (1, 4, 6)


def test_bad_shape_is_rejected():
    link = OuterLink(8, 8)
    with pytest.raises(ValueError):
        link(torch.randn(4, 7))
