"""Runtime configuration: paths, .env loading, and global knobs.

Importing this module loads `.env` (if present) so API keys land in the
environment before any litellm call. No secrets are ever hard-coded here.
"""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # dotenv is optional at import time (offline/mock runs)
    def load_dotenv(*_a, **_k):  # type: ignore
        return False

# --- paths ---
ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "configs"
PREREG_DIR = ROOT / "prereg"
DATA_DIR = ROOT / "data"
RUNS_DIR = DATA_DIR / "runs"
CACHE_DIR = DATA_DIR / "cache"

# load .env from repo root
load_dotenv(ROOT / ".env")

# --- knobs ---
MAX_CONCURRENCY = int(os.getenv("RIVAL_ARENA_MAX_CONCURRENCY", "8"))
MAINLINE_TEMPERATURE = 0.7          # P11
DEFAULT_TOKEN_BUDGET = 256          # message-length guidance (bandwidth control)
DEFAULT_MAX_TOKENS = 768            # completion cap; reasoning + action must fit (P8 parity)
DEFAULT_HISTORY_WINDOW = 10         # P22
LOCKIN_THRESHOLD = 0.8              # end-state C > 0.8 counts as cooperative lock-in (P17)
END_STATE_K = 5                     # rounds averaged for end-state means


def have_openrouter() -> bool:
    return bool(os.getenv("OPENROUTER_API_KEY"))


def have_openrouter_backup() -> bool:
    """True iff a backup OpenRouter key is configured for credit-exhaustion
    failover (see harness/llm.py)."""
    return bool(os.getenv("OPENROUTER_API_KEY_BACKUP"))


def have_openai() -> bool:
    return bool(os.getenv("OPENAI_API_KEY"))


def ensure_dirs() -> None:
    for d in (DATA_DIR, RUNS_DIR, CACHE_DIR):
        d.mkdir(parents=True, exist_ok=True)
