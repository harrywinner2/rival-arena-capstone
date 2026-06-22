"""F3 — Public Goods Game / free-riding (extends the dyadic results to a pot).

Repeated public goods game: each round both seats CONTRIBUTE their endowment to
a common pot (multiplied by ``mult_factor`` and split equally) or KEEP it and
free-ride. We sweep the multiplication factor x channel and watch contribution
dynamics + end-game defection (the spec's predicted decaying-contribution curve
with an end-game cliff).

*** 2-PLAYER (N=2) ***
The harness is hard-wired to two seats (A, B), so F3 is run as a 2-player public
goods game. This still yields a genuine free-riding dilemma (see below); it does
NOT cover the N-sweep from experiments.md F3.

Multiplication-factor choice (N=2). With endowment 1 and N players, contributing
one unit returns ``m/N`` per capita while costing 1, so the per-capita marginal
return is ``m/2`` here. Keeping is the dominant one-shot move exactly when
``m/2 < 1`` (i.e. ``m < 2``), yet mutual contribution maximizes group welfare
whenever ``m > 1`` (the pot creates value). The swept factors straddle this:
  * m = 1.2 — strong dilemma: per-capita return 0.60; free-riding heavily
              dominant, contribution only marginally raises the social optimum
              (2.4 vs floor 2). Expect rapid collapse to KEEP.
  * m = 1.6 — moderate dilemma: per-capita return 0.80; free-riding still
              dominant one-shot but the cooperative surplus is large (social
              optimum 3.2 vs floor 2). The interesting cell.
  * m = 2.0 — boundary / no dilemma: per-capita return 1.00; contributing is
              (weakly) dominant, so this is the cooperative-control end of the
              sweep (social optimum 4.0). Free-riding has no one-shot edge.
So 1.2 and 1.6 are true free-riding dilemmas (Nash = all-KEEP, social optimum =
all-CONTRIBUTE) and 2.0 is the non-dilemma control where the incentive to
free-ride vanishes — letting us attribute any defection at m<2 to the dilemma
rather than to model behaviour.

Cooperative action = CONTRIBUTE, so the existing C / lock-in / welfare metrics
pick it up unchanged.
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from .common import pair_players, resolve_pair, run_and_finalize

# L0 (no channel) vs L2 (observed free text): does a channel sustain the pot?
LEVELS = [ChannelLevel.L0_NONE, ChannelLevel.L2_OBSERVED]

# Multiplication factors straddling the N=2 free-riding boundary m/2 = 1 (m=2):
#   1.2, 1.6 = genuine dilemmas; 2.0 = non-dilemma cooperative control.
MULT_FACTORS = (1.2, 1.6, 2.0)


def build_specs(
    pair="same_origin_cn",
    seeds: int = 8,
    mult_factors=MULT_FACTORS,
    levels=LEVELS,
    familiarity: str = "canonical",
    max_rounds: int = 15,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,
) -> list[MatchSpec]:
    model_ids = resolve_pair(pair)
    pairname = pair if isinstance(pair, str) else "x".join(model_ids)
    specs: list[MatchSpec] = []
    for mf in mult_factors:
        for lvl in levels:
            for s in range(seed_offset, seed_offset + seeds):
                specs.append(MatchSpec(
                    experiment_id="F3",
                    cell_id=f"F3/mult_{mf:g}/{lvl.value}/{pairname}",
                    game=GameSpec(
                        "public_goods",
                        {"mult_factor": mf,
                         "continuation_prob": continuation_prob,
                         "max_rounds": max_rounds},
                        familiarity=familiarity,
                    ),
                    channel=lvl,
                    epistemic=default_epistemic(lvl),
                    players=pair_players(model_ids, s),
                    seed=s,
                    token_budget=token_budget,
                    history_window=DEFAULT_HISTORY_WINDOW,
                    framing=framing,
                ))
    return specs


def figures(run_dir, summaries, results):
    from rival_arena.viz import figures as F
    out = []
    by_cell = {}
    for r in results:
        by_cell.setdefault(r.spec.cell_id, []).append(r)
    try:
        out.append(F.coop_curves(by_cell, run_dir / "f3_contribution_curves.png"))
    except Exception as e:
        print(f"[F3] contribution curves skipped: {e}")
    try:
        out.append(F.refusal_panel(summaries, run_dir / "f3_refusals.png"))
    except Exception as e:
        print(f"[F3] refusal panel skipped: {e}")
    return out


def main(pair="same_origin_cn", seeds=8, mock=False, max_rounds=15, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pair=pair, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[F3] {len(specs)} matches: {len(MULT_FACTORS)} mult-factors x "
          f"{len(LEVELS)} channels x {seeds} seeds, pair={pair}, mock={mock}")
    return run_and_finalize(specs, "F3", mock=mock, figure_fn=figures, resume=resume)
