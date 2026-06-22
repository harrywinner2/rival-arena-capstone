"""A1 — channel effect in the IPD (the confirmatory spine).

Ladder L0->L3 (one affordance per rung, P6) x familiarity {canonical, novel}
(G2 / P3b) x a fixed pair x seeds. Primary outcome = lock-in proportion (P17).

This driver runs both the exploratory pilot and the confirmatory run; which it is
is a labeling/analysis decision (prereg/a1.md), not a code difference.
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from .common import pair_players, resolve_pair, run_and_finalize

ALL_LEVELS = [ChannelLevel.L0_NONE, ChannelLevel.L1_SIGNAL,
              ChannelLevel.L2_OBSERVED, ChannelLevel.L3_PRIVATE]


def build_specs(
    pair="same_origin_cn",
    seeds: int = 20,
    familiarities=("canonical", "novel"),
    levels=ALL_LEVELS,
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,                 # use a disjoint range for confirmatory runs (P4)
) -> list[MatchSpec]:
    model_ids = resolve_pair(pair)
    pairname = pair if isinstance(pair, str) else "x".join(model_ids)
    specs: list[MatchSpec] = []
    for fam in familiarities:
        for lvl in levels:
            for s in range(seed_offset, seed_offset + seeds):
                specs.append(MatchSpec(
                    experiment_id="A1",
                    cell_id=f"A1/{lvl.value}/{fam}/{pairname}",
                    game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                          "max_rounds": max_rounds}, familiarity=fam),
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
    fams = sorted({r.spec.game.familiarity for r in results})
    for fam in fams:
        cs = [s for s in summaries if f"/{fam}/" in s["cell_id"]]
        cs.sort(key=lambda s: s["channel"])
        if cs:
            out.append(F.lockin_bar(cs, run_dir / f"a1_lockin_{fam}.png",
                                    title=f"A1 channel ladder — IPD ({fam})"))
    out.append(F.coop_curves(by_cell, run_dir / "a1_coop_curves.png"))
    out.append(F.refusal_panel(summaries, run_dir / "a1_refusals.png"))
    return out


def main(pair="same_origin_cn", seeds=20, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pair=pair, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[A1] {len(specs)} matches: {len(ALL_LEVELS)} rungs x 2 familiarities "
          f"x {seeds} seeds, pair={pair}, mock={mock}")
    return run_and_finalize(specs, "A1", mock=mock, figure_fn=figures, resume=resume)
