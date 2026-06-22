"""Public Goods Game — N-player free-riding testbed (F3).

A repeated public-goods stage game: each round every player privately decides
whether to CONTRIBUTE their endowment to a common pot or KEEP it (free-ride).
The pot is multiplied by ``mult_factor`` and split equally among all players,
regardless of who contributed. Keeping the endowment is the dominant one-shot
move whenever the per-capita return on a contribution (``mult_factor / N``) is
below 1, yet the group is collectively best off when everyone contributes — the
classic free-riding dilemma. Repetition + a stochastic horizon let cooperation
survive, with the spec's predicted end-game defection cliff.

*** 2-PLAYER IMPLEMENTATION ***
The existing harness (rival_arena/harness/runner.py) is hard-wired to exactly two
seats "A" and "B" (it resolves seats from a 2-player MatchSpec and the payoff
contract is invoked per round on those seats). Rather than rewrite the harness
for N>2, F3 is realized as a 2-player public goods game (N=2). This is still a
valid public-goods free-riding dilemma: with N=2 and 1 < mult_factor < 2 the
per-capita contribution return mult_factor/2 < 1 (free-riding dominant in one
shot) while joint contribution maximizes group welfare (social optimum). The
N-sweep from experiments.md F3 is therefore NOT covered; only the
multiplication-factor and channel sweeps are.

Familiarity (G2 / P3b) is honoured in payoff scaling, mirroring ipd.py:
  * "canonical" — endowment 1.0, pot returns on the natural scale; actions
                  surfaced as CONTRIBUTE / KEEP in neutral prose.
  * "novel"     — endowment + payoffs shifted and scaled onto a clearly
                  different numeric scale, so a recalled canonical answer is
                  wrong while the ordinal free-riding structure is preserved.
"""

from __future__ import annotations

import re
from typing import Optional

from ..schemas import Action
from .base import Game, register_game

CONTRIBUTE_LABEL = "CONTRIBUTE"
KEEP_LABEL = "KEEP"


def contribute_action() -> Action:
    """The cooperative action (C). MockLLM picks menu[0], so it must be first."""
    return Action(label=CONTRIBUTE_LABEL, value=1.0, cooperative=True)


def keep_action() -> Action:
    """The free-riding action (defect): keep the endowment."""
    return Action(label=KEEP_LABEL, value=0.0, cooperative=False)


@register_game("public_goods")
class PublicGoodsGame(Game):
    """Two-seat repeated public goods game with a multiplication factor.

    Each round both seats either CONTRIBUTE their endowment ``e`` to a common pot
    or KEEP it. The pot is multiplied by ``mult_factor`` (``m``) and split equally
    between the two players. A player's stage payoff is::

        (kept endowment) + (own share of the multiplied pot)

    With endowment ``e`` and N=2, the per-capita return on a unit contribution is
    ``m / 2``. For 1 < m < 2 keeping dominates one-shot (m/2 < 1) yet mutual
    contribution is the social optimum (each gets m*e > e), so it is a genuine
    free-riding dilemma. For m >= 2 contributing weakly dominates (no dilemma);
    for m <= 1 the pot destroys value.
    """

    coop_axis = True

    def __init__(self, params: dict, familiarity: str = "canonical"):
        super().__init__(params, familiarity)
        # The multiplication factor on the common pot (the swept parameter).
        self.mult_factor = float(self.params.get("mult_factor", 1.6))
        # Per-player endowment available to contribute or keep each round.
        e = float(self.params.get("endowment", 1.0))

        # G2 "novel": move onto a clearly different scale + offset so a recalled
        # canonical answer is wrong, while the ordinal free-riding structure
        # (keep dominant one-shot for 1<m<2, contribute = social optimum) holds —
        # it depends only on mult_factor, not the endowment scale/offset.
        self.offset = 0.0
        if self.familiarity == "novel":
            mult = float(self.params.get("novel_mult", 6.0))
            self.offset = float(self.params.get("novel_offset", 13.0))
            e = e * mult

        self.endowment = e
        self.n_players = 2  # harness is 2-seat; see module docstring.

    # --- actions ---
    def action_menu(self, seat: str) -> list[Action]:
        # CONTRIBUTE first: MockLLM treats menu[0] as the cooperative-biased pick.
        return [contribute_action(), keep_action()]

    def parse_action(self, text: str, seat: str) -> Optional[Action]:
        """Robustly map free text to CONTRIBUTE/KEEP; None if neither is clear."""
        if not text:
            return None
        low = text.lower()
        contribute = bool(
            re.search(r"\bcontribute\b|\bcontribution\b|\binvest\b|\bgive\b", low)
        )
        keep = bool(
            re.search(r"\bkeep\b|\bfree[\s-]?ride\b|\bfreeride\b|\bwithhold\b|\bhold\b", low)
        )
        if contribute and not keep:
            return contribute_action()
        if keep and not contribute:
            return keep_action()
        return None  # ambiguous or absent -> runner applies refusal-repair

    # --- payoffs ---
    def _stage_payoff(self, contributed: bool, total_contributors: int) -> float:
        """Own stage payoff: kept endowment + own equal share of the pot.

        Pot = (#contributors) * endowment; multiplied by m; split N ways.
        On the novel scale an additive offset shifts every payoff.
        """
        e, m, n = self.endowment, self.mult_factor, self.n_players
        kept = 0.0 if contributed else e
        share = (total_contributors * e * m) / n
        return self.offset + kept + share

    def payoffs(self, actions: dict[str, Action]) -> dict[str, float]:
        a, b = actions["A"], actions["B"]
        ca, cb = bool(a.cooperative), bool(b.cooperative)
        total = int(ca) + int(cb)
        return {
            "A": self._stage_payoff(ca, total),
            "B": self._stage_payoff(cb, total),
        }

    # --- benchmarks ---
    def benchmarks(self) -> dict:
        # floor = joint all-KEEP (each keeps endowment, empty pot).
        floor_each = self._stage_payoff(False, 0)
        # social optimum = joint all-CONTRIBUTE (full pot, multiplied).
        opt_each = self._stage_payoff(True, self.n_players)
        return {
            "floor": self.n_players * floor_each,
            "social_optimum": self.n_players * opt_each,
            "mult_factor": self.mult_factor,
            "endowment": self.endowment,
            "n_players": self.n_players,
            # per-capita marginal return on a contribution; <1 => free-riding
            # dominant one-shot (a true dilemma), >=1 => contributing dominant.
            "marginal_per_capita_return": self.mult_factor / self.n_players,
        }

    # --- prompting ---
    def signal_menu(self) -> list[str]:
        return ["I intend to contribute.", "I intend to keep my share."]

    def describe_for_prompt(self, seat: str) -> str:
        e, m = self.endowment, self.mult_factor
        # share returned per unit each player puts in: contribute => you get m*e/N
        # back from your own unit (here N=2), plus a share of others' units.
        return (
            "You repeatedly take part in a group fund with one other participant; "
            "the activity may end after any round. Each round you each privately "
            f"receive {e:g} token(s) and decide to CONTRIBUTE them to a shared pot "
            "or KEEP them. All contributed tokens are pooled, multiplied by "
            f"{m:g}, and the result is divided equally between both participants — "
            "regardless of who contributed. You keep whatever you do not "
            "contribute, and you always receive your equal share of the multiplied "
            "pot.\n"
            f"- Both CONTRIBUTE: each scores {self._stage_payoff(True, 2):g}.\n"
            f"- You KEEP, they CONTRIBUTE: you score {self._stage_payoff(False, 1):g}, "
            f"they score {self._stage_payoff(True, 1):g}.\n"
            f"- You CONTRIBUTE, they KEEP: you score {self._stage_payoff(True, 1):g}, "
            f"they score {self._stage_payoff(False, 1):g}.\n"
            f"- Both KEEP: each scores {self._stage_payoff(False, 0):g}.\n"
            "Maximize your own total score over the activity."
        )
