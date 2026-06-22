"""Classical Axelrod strategies for the IPD (A5 — the validity anchor).

Each strategy occupies a seat and best-responds to the *action history* (a list
of per-round dicts {seat: Action}), returning COOPERATE/DEFECT Actions built from
ipd's constructors so labels and cooperative flags match the LLM seat exactly.

`history` is the list of completed rounds; the strategy is choosing the action
for the next round. `seat` is the strategy's own seat ("A"/"B"); the opponent is
the other seat present in each round dict.
"""

from __future__ import annotations

import random
from typing import Optional

from ..schemas import Action
from .base import ClassicalStrategy, register_strategy
from .ipd import coop_action, defect_action


def _opponent_seat(round_actions: dict[str, Action], seat: str) -> Optional[str]:
    for s in round_actions:
        if s != seat:
            return s
    return None


def _was_cooperative(action: Optional[Action]) -> Optional[bool]:
    return None if action is None else bool(action.cooperative)


@register_strategy("always_cooperate")
class AlwaysCooperate(ClassicalStrategy):
    def act(self, history, seat, rng):
        return coop_action()


@register_strategy("always_defect")
class AlwaysDefect(ClassicalStrategy):
    def act(self, history, seat, rng):
        return defect_action()


@register_strategy("random")
class RandomStrategy(ClassicalStrategy):
    """50/50 via the supplied rng (deterministic given the seed)."""

    def act(self, history, seat, rng: random.Random):
        return coop_action() if rng.random() < 0.5 else defect_action()


@register_strategy("tit_for_tat")
class TitForTat(ClassicalStrategy):
    """Cooperate first, then copy the opponent's last action."""

    def act(self, history, seat, rng):
        if not history:
            return coop_action()
        last = history[-1]
        opp = _opponent_seat(last, seat)
        return coop_action() if _was_cooperative(last.get(opp)) else defect_action()


@register_strategy("grim")
class Grim(ClassicalStrategy):
    """Cooperate until the opponent ever defects, then defect forever."""

    def act(self, history, seat, rng):
        for rnd in history:
            opp = _opponent_seat(rnd, seat)
            if _was_cooperative(rnd.get(opp)) is False:
                return defect_action()
        return coop_action()


@register_strategy("pavlov")
class Pavlov(ClassicalStrategy):
    """Win-stay / lose-shift on the last round's outcome.

    A "win" is a mutual outcome (both cooperated or both defected); then repeat
    own last move. A "loss" is a mismatched outcome (got tempted or suckered);
    then switch. Cooperate on the first move.
    """

    def act(self, history, seat, rng):
        if not history:
            return coop_action()
        last = history[-1]
        opp = _opponent_seat(last, seat)
        own_coop = _was_cooperative(last.get(seat))
        opp_coop = _was_cooperative(last.get(opp))
        if own_coop is None:
            return coop_action()
        win = own_coop == opp_coop  # both-C or both-D => stay
        if win:
            return coop_action() if own_coop else defect_action()
        return defect_action() if own_coop else coop_action()  # shift
