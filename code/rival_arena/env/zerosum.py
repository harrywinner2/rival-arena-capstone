"""Matching Pennies — the pure zero-sum control (A2).

Two seats pick HEADS or TAILS. Seat A (the "matcher") wins +1 if the choices
match; seat B (the "mismatcher") wins +1 if they differ. A "cooperation rate" is
ill-defined here, so `is_cooperative` is always None (coop_axis=False) and the
metrics layer uses minimax-deviation / action-correlation on a separate panel.
The minimax value of the symmetric game is 0 for each player.
"""

from __future__ import annotations

import re
from typing import Optional

from ..schemas import Action
from .base import Game, register_game

HEADS_LABEL = "HEADS"
TAILS_LABEL = "TAILS"


def _heads() -> Action:
    return Action(label=HEADS_LABEL, value=1.0, cooperative=None)


def _tails() -> Action:
    return Action(label=TAILS_LABEL, value=0.0, cooperative=None)


@register_game("matching_pennies")
class MatchingPennies(Game):
    """Constant-sum two-seat game; A matches, B mismatches."""

    coop_axis = False

    def action_menu(self, seat: str) -> list[Action]:
        return [_heads(), _tails()]

    def parse_action(self, text: str, seat: str) -> Optional[Action]:
        if not text:
            return None
        low = text.lower()
        heads = bool(re.search(r"\bheads\b", low)) or bool(re.search(r"\bh\b", low))
        tails = bool(re.search(r"\btails\b", low)) or bool(re.search(r"\bt\b", low))
        if heads and not tails:
            return _heads()
        if tails and not heads:
            return _tails()
        return None

    def payoffs(self, actions: dict[str, Action]) -> dict[str, float]:
        match = actions["A"].label == actions["B"].label
        # A wins on a match, B wins on a mismatch; strictly zero-sum.
        return {"A": 1.0, "B": -1.0} if match else {"A": -1.0, "B": 1.0}

    def is_cooperative(self, action: Action) -> Optional[bool]:
        return None  # C is undefined in pure zero-sum (§A2)

    def benchmarks(self) -> dict:
        return {"floor": 0.0, "social_optimum": 0.0, "minimax_value": 0.0}

    def describe_for_prompt(self, seat: str) -> str:
        if seat == "A":
            goal = "You win the round if both of you choose the SAME side."
        else:
            goal = "You win the round if the two of you choose DIFFERENT sides."
        return (
            "Each round you and another participant simultaneously choose HEADS or "
            f"TAILS, then both choices are revealed. {goal} The winner scores +1 and "
            "the loser scores -1 each round. Maximize your own total score."
        )
