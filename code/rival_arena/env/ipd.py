"""Iterated Prisoner's Dilemma — the core cooperation testbed (A1, A2, A4).

Canonical Axelrod payoffs (T=5, R=3, P=1, S=0). The game is a stage game; the
runner owns the horizon (continuation_prob / max_rounds in base.Game). Two seats
"A" and "B" each pick COOPERATE or DEFECT.

Familiarity (G2 / P3b) is honoured in `describe_for_prompt`:
  * "canonical"  — payoff matrix in neutral prose (never named "Prisoner's
                   Dilemma"); actions called COOPERATE / DEFECT.
  * "relabeled"  — identical payoffs, actions surfaced as "Option X" / "Option Y"
                   (X==COOPERATE internally) so memorized label heuristics misfire.
  * "novel"      — scaled + shifted payoffs on a different scale (still an ordinal
                   social dilemma T>R>P>S and 2R>T+S), so a recalled numeric answer
                   would mislead.

`temptation_scale` (A4) widens the (T-R) and (P-S) gaps about R and P while
keeping the ordinal social-dilemma structure, letting payoffs scale x0.5/x1/x2/x4.
"""

from __future__ import annotations

import re
from typing import Optional

from ..schemas import Action
from .base import Game, register_game

# --- canonical action constructors -----------------------------------------
# Exposed at module level so classical.py builds *identical* Actions (matching
# labels + cooperative flags), keeping payoff lookups consistent everywhere.

COOPERATE_LABEL = "COOPERATE"
DEFECT_LABEL = "DEFECT"


def coop_action() -> Action:
    """The cooperative action (C). MockLLM picks menu[0], so it must be first."""
    return Action(label=COOPERATE_LABEL, value=1.0, cooperative=True)


def defect_action() -> Action:
    """The defecting action (D)."""
    return Action(label=DEFECT_LABEL, value=0.0, cooperative=False)


@register_game("ipd")
class IteratedPrisonersDilemma(Game):
    """Two-seat repeated PD with Axelrod payoffs (params may override)."""

    coop_axis = True

    def __init__(self, params: dict, familiarity: str = "canonical"):
        super().__init__(params, familiarity)
        # Base (canonical) payoffs; params override the bare values.
        T = float(self.params.get("T", 5.0))
        R = float(self.params.get("R", 3.0))
        P = float(self.params.get("P", 1.0))
        S = float(self.params.get("S", 0.0))

        # A4: scale the temptation gap (T-R) and sucker penalty gap (P-S) about
        # the cooperative anchors, then lift the cooperative reward R so the
        # social-dilemma efficiency constraint 2R > T+S survives large scales
        # (otherwise widening the gaps alone breaks it at x2+). Ordinal structure
        # T>R>P>S and the PD constraint both hold for any scale >= 1.
        scale = float(self.params.get("temptation_scale", 1.0))
        t_gap = (T - R) * scale
        s_gap = (P - S) * scale
        # extra spread injected beyond the canonical gaps, shared into R's margin
        # (only when widening; shrinking gaps keep the constraint on their own).
        extra = max(0.0, (t_gap - (T - R)) + (s_gap - (P - S)))
        R = R + extra
        T = R + t_gap
        S = P - s_gap

        # G2 "novel": move onto a clearly different scale + offset so a recalled
        # canonical answer is wrong, while keeping T>R>P>S and 2R>T+S.
        if self.familiarity == "novel":
            mult = float(self.params.get("novel_mult", 7.0))
            offset = float(self.params.get("novel_offset", 11.0))
            T, R, P, S = (offset + mult * x for x in (T, R, P, S))

        self.T, self.R, self.P, self.S = T, R, P, S

    # --- actions ---
    def action_menu(self, seat: str) -> list[Action]:
        # COOPERATE first: MockLLM treats menu[0] as the cooperative-biased pick.
        return [coop_action(), defect_action()]

    def parse_action(self, text: str, seat: str) -> Optional[Action]:
        """Robustly map free text to C/D; None if neither is clearly present."""
        if not text:
            return None
        low = text.lower()
        # Relabeled surface forms map back to the internal C/D.
        coop = bool(re.search(r"\bcooperate\b|\boption\s*x\b", low)) or bool(
            re.search(r"\bc\b", low)
        )
        defect = bool(re.search(r"\bdefect\b|\boption\s*y\b", low)) or bool(
            re.search(r"\bd\b", low)
        )
        if coop and not defect:
            return coop_action()
        if defect and not coop:
            return defect_action()
        return None  # ambiguous or absent -> runner applies refusal-repair

    # --- payoffs ---
    def payoffs(self, actions: dict[str, Action]) -> dict[str, float]:
        a, b = actions["A"], actions["B"]
        ca, cb = bool(a.cooperative), bool(b.cooperative)
        T, R, P, S = self.T, self.R, self.P, self.S
        if ca and cb:
            return {"A": R, "B": R}
        if ca and not cb:
            return {"A": S, "B": T}
        if not ca and cb:
            return {"A": T, "B": S}
        return {"A": P, "B": P}

    # --- benchmarks ---
    def benchmarks(self) -> dict:
        return {
            "floor": 2.0 * self.P,            # joint all-defect
            "social_optimum": 2.0 * self.R,   # joint mutual-cooperation
            "T": self.T,
            "R": self.R,
            "P": self.P,
            "S": self.S,
        }

    # --- prompting ---
    def signal_menu(self) -> list[str]:
        return ["I intend to cooperate.", "I intend to defect."]

    def describe_for_prompt(self, seat: str) -> str:
        T, R, P, S = self.T, self.R, self.P, self.S
        if self.familiarity == "relabeled":
            ca, cb = "Option X", "Option Y"
            return (
                "You repeatedly play a two-choice game against another participant; "
                "the match may end after any round. Each round you both pick "
                f"{ca} or {ca[-1]}/{cb} simultaneously, then results are revealed.\n"
                f"- Both pick {ca}: each scores {R:g}.\n"
                f"- You pick {cb}, they pick {ca}: you score {T:g}, they score {S:g}.\n"
                f"- You pick {ca}, they pick {cb}: you score {S:g}, they score {T:g}.\n"
                f"- Both pick {cb}: each scores {P:g}.\n"
                "Maximize your own total score over the match."
            )
        # canonical / novel: same structure, neutral wording, no game name.
        return (
            "You repeatedly interact with another participant; the match may end "
            "after any round. Each round you each privately choose to COOPERATE or "
            "DEFECT, then both choices are revealed.\n"
            f"- Both COOPERATE: each scores {R:g}.\n"
            f"- You DEFECT, they COOPERATE: you score {T:g}, they score {S:g}.\n"
            f"- You COOPERATE, they DEFECT: you score {S:g}, they score {T:g}.\n"
            f"- Both DEFECT: each scores {P:g}.\n"
            "Maximize your own total score over the match."
        )
