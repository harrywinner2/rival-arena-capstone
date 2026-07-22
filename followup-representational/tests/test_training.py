import random
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from l4_arena.link import OuterLink
from l4_arena.training import (
    TrainConfig,
    extract_alpaca_example,
    load_checkpoint,
    save_checkpoint_atomic,
)


def config() -> TrainConfig:
    return TrainConfig("m", "d", "train", 2, 1e-3, 0.0, 1, 8, 4, 1, 7)


def test_extract_alpaca_example():
    assert extract_alpaca_example({"instruction": "Do X", "input": "Y", "output": "Z"}) == (
        "Do X\n\nInput:\nY",
        "Z",
    )
    assert extract_alpaca_example({"instruction": "", "output": "Z"}) is None


def test_checkpoint_round_trip_and_fingerprint_guard(tmp_path):
    link = OuterLink(4, 4)
    optimizer = torch.optim.AdamW(link.parameters())
    path = tmp_path / "checkpoint.pt"
    payload = {
        "config_fingerprint": config().fingerprint(),
        "link": link.state_dict(),
        "optimizer": optimizer.state_dict(),
    }
    save_checkpoint_atomic(path, payload)
    loaded = load_checkpoint(path, config().fingerprint())
    assert loaded is not None
    assert loaded["config_fingerprint"] == config().fingerprint()
    with pytest.raises(ValueError):
        load_checkpoint(path, "different")
