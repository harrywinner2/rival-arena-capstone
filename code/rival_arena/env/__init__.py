"""Game environments + classical baselines.

Public surface:
    get_game(name, params, familiarity) -> Game
    get_strategy(name) -> ClassicalStrategy
"""

from __future__ import annotations

from .base import ClassicalStrategy, Game

# Concrete games/strategies are registered on import.
from . import ipd, market, zerosum, classical, public_goods, multi_commodity, battleship, double_auction, schelling, research_race  # noqa: E402,F401
from .base import GAME_REGISTRY, STRATEGY_REGISTRY  # noqa: E402


def get_game(name: str, params: dict | None = None, familiarity: str = "canonical") -> Game:
    if name not in GAME_REGISTRY:
        raise KeyError(f"Unknown game {name!r}. Known: {sorted(GAME_REGISTRY)}")
    return GAME_REGISTRY[name](params or {}, familiarity)


def get_strategy(name: str) -> ClassicalStrategy:
    if name not in STRATEGY_REGISTRY:
        raise KeyError(f"Unknown strategy {name!r}. Known: {sorted(STRATEGY_REGISTRY)}")
    return STRATEGY_REGISTRY[name]()


__all__ = ["Game", "ClassicalStrategy", "get_game", "get_strategy"]
