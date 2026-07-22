from __future__ import annotations

import hashlib
import json
import os
import random
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch


@dataclass(frozen=True)
class TrainConfig:
    model: str
    dataset: str
    dataset_split: str
    steps: int
    learning_rate: float
    weight_decay: float
    grad_accumulation: int
    max_message_tokens: int
    max_target_tokens: int
    checkpoint_every: int
    seed: int

    def fingerprint(self) -> str:
        encoded = json.dumps(asdict(self), sort_keys=True).encode()
        return hashlib.sha256(encoded).hexdigest()[:16]


def choose_cuda_dtype() -> torch.dtype:
    """Use bf16 only on hardware with native bf16 tensor-core support."""
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required")
    major, _minor = torch.cuda.get_device_capability(0)
    return torch.bfloat16 if major >= 8 and torch.cuda.is_bf16_supported() else torch.float16


def seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def capture_rng_state() -> dict[str, Any]:
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch": torch.get_rng_state(),
        "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else [],
    }


def restore_rng_state(state: dict[str, Any]) -> None:
    random.setstate(state["python"])
    np.random.set_state(state["numpy"])
    torch.set_rng_state(state["torch"])
    if torch.cuda.is_available() and state.get("cuda"):
        torch.cuda.set_rng_state_all(state["cuda"])


def save_checkpoint_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        torch.save(payload, temporary)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def load_checkpoint(path: Path, expected_fingerprint: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = torch.load(path, map_location="cpu", weights_only=False)
    actual = payload.get("config_fingerprint")
    if actual != expected_fingerprint:
        raise ValueError(
            f"checkpoint config mismatch: expected {expected_fingerprint}, found {actual}"
        )
    return payload


def extract_alpaca_example(row: dict[str, Any]) -> tuple[str, str] | None:
    instruction = str(row.get("instruction", "")).strip()
    extra_input = str(row.get("input", "")).strip()
    target = str(row.get("output", "")).strip()
    if not instruction or not target:
        return None
    message = instruction if not extra_input else f"{instruction}\n\nInput:\n{extra_input}"
    return message, target

