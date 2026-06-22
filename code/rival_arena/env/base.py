"""Game interface — the contract between env/ and harness/.

A `Game` is a repeated stage game. It is essentially stateless: the runner owns
the match history and hands the game the actions for one round to score. This
keeps games trivial to test and reuse across the channel/regime/origin factors.

Two registries (`GAME_REGISTRY`, `STRATEGY_REGISTRY`) are populated by the
concrete modules (ipd, market, zerosum, classical) at import time.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from typing import Optional

from ..schemas import Action

GAME_REGISTRY: dict[str, type["Game"]] = {}
STRATEGY_REGISTRY: dict[str, type["ClassicalStrategy"]] = {}


def register_game(name: str):
    def deco(cls):
        cls.name = name
        GAME_REGISTRY[name] = cls
        return cls

    return deco


def register_strategy(name: str):
    def deco(cls):
        cls.name = name
        STRATEGY_REGISTRY[name] = cls
        return cls

    return deco


class Game(ABC):
    """A repeated stage game over a fixed set of seats ('A', 'B', ...)."""

    name: str = "base"
    coop_axis: bool = True   # False for pure zero-sum (C is ill-defined there, §A2)

    def __init__(self, params: dict, familiarity: str = "canonical"):
        self.params = params or {}
        self.familiarity = familiarity  # "canonical" | "relabeled" | "novel" (G2)

    # --- horizon ---
    @property
    def continuation_prob(self) -> float:
        """delta: probability the match continues after each round (P: no backward
        induction at fixed length). Default ~0.97 per A1."""
        return float(self.params.get("continuation_prob", 0.97))

    @property
    def max_rounds(self) -> int:
        """Hard cap so a run's cost is bounded even with high delta."""
        return int(self.params.get("max_rounds", 30))

    def continues(self, round_index: int, rng: random.Random) -> bool:
        if round_index + 1 >= self.max_rounds:
            return False
        return rng.random() < self.continuation_prob

    # --- actions ---
    @abstractmethod
    def action_menu(self, seat: str) -> list[Action]:
        """The legal actions for this seat (the menu shown to the agent)."""

    @abstractmethod
    def parse_action(self, text: str, seat: str) -> Optional[Action]:
        """Map raw model text onto a legal Action, or None if unparseable
        (the runner then applies the refusal-repair policy)."""

    @abstractmethod
    def payoffs(self, actions: dict[str, Action]) -> dict[str, float]:
        """Stage payoff per seat given everyone's action this round."""

    def is_cooperative(self, action: Action) -> Optional[bool]:
        """Map an action onto the C axis. None when undefined (zero-sum)."""
        return action.cooperative

    # --- prompting helpers ---
    @abstractmethod
    def describe_for_prompt(self, seat: str) -> str:
        """Natural-language rules + payoffs, honouring `familiarity` (G2:
        canonical names / relabeled / novel payoffs)."""

    def signal_menu(self) -> list[str]:
        """Canned signals for the L1 rung (tiny menu, ~no bandwidth)."""
        return ["I intend to cooperate.", "I intend to defect.", "(no signal)"]

    # --- benchmarks (anchor every number) ---
    @abstractmethod
    def benchmarks(self) -> dict:
        """Reference points for normalization. Mixed-motive games return at least
        {'floor': joint all-defect payoff, 'social_optimum': joint best}.
        Market games additionally return {'p_competitive', 'p_monopoly', ...}."""


class ClassicalStrategy(ABC):
    """A non-LLM Axelrod-style strategy occupying a seat (A5 anchor)."""

    name: str = "base"

    def reset(self) -> None:
        pass

    @abstractmethod
    def act(self, history: list[dict[str, Action]], seat: str, rng: random.Random) -> Action:
        """Choose an action given the full action history (list of {seat: Action})."""
