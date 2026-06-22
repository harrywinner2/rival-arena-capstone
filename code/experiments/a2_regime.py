"""A2 — strategic-regime sweep (H2).

Holds the channel fixed (L2_observed) and a single pair, and swaps the GAME's
strategic regime:

  * "repeated"  — IPD, continuation_prob=0.97 (a long shadow of the future).
  * "oneshot"   — IPD, continuation_prob=0.0, max_rounds=1 (no future to leverage).
  * "zerosum"   — matching pennies, a pure-conflict control.

H2: cooperation should ride the regime — high under "repeated", collapsing under
"oneshot". The zero-sum cell is a CONTROL on a separate axis: cooperation rate C
is only defined for the mixed-motive (ipd) cells, so the matching-pennies cell's
C is None by design (matching_pennies has coop_axis=False and the metrics layer
already handles that), and it is read via minimax-deviation, not C.
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from .common import pair_players, resolve_pair, run_and_finalize

REGIMES = ["repeated", "oneshot", "zerosum"]


def _game_for(regime: str, max_rounds: int, continuation_prob: float) -> GameSpec:
    if regime == "repeated":
        return GameSpec("ipd", {"continuation_prob": continuation_prob,
                                "max_rounds": max_rounds}, familiarity="canonical")
    if regime == "oneshot":
        return GameSpec("ipd", {"continuation_prob": 0.0, "max_rounds": 1},
                        familiarity="canonical")
    if regime == "zerosum":
        return GameSpec("matching_pennies", {"max_rounds": max_rounds,
                                             "continuation_prob": continuation_prob})
    raise ValueError(f"unknown regime: {regime}")


def build_specs(
    pair="same_origin_cn",
    seeds: int = 10,
    regimes=REGIMES,
    level: ChannelLevel = ChannelLevel.L2_OBSERVED,
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,                 # disjoint range for confirmatory runs (P4)
) -> list[MatchSpec]:
    model_ids = resolve_pair(pair)
    pairname = pair if isinstance(pair, str) else "x".join(model_ids)
    specs: list[MatchSpec] = []
    for regime in regimes:
        for s in range(seed_offset, seed_offset + seeds):
            specs.append(MatchSpec(
                experiment_id="A2",
                cell_id=f"A2/{regime}/{pairname}",
                game=_game_for(regime, max_rounds, continuation_prob),
                channel=level,
                epistemic=default_epistemic(level),
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

    def _safe(fn, *a, **kw):
        try:
            out.append(fn(*a, **kw))
        except Exception as e:  # figures must never sink a completed run
            print(f"[A2] figure {getattr(fn, '__name__', fn)} failed: {e}")

    # the clean contrast: repeated vs oneshot (the mixed-motive cells where C is
    # defined). lockin_bar reads lock-in proportion per cell.
    coop_cells = [s for s in summaries
                  if "/repeated/" in s["cell_id"] or "/oneshot/" in s["cell_id"]]
    coop_cells.sort(key=lambda s: s["cell_id"])
    if coop_cells:
        _safe(F.lockin_bar, coop_cells, run_dir / "a2_lockin_regime.png",
              title="A2 regime contrast — lock-in (repeated vs one-shot)")

    _safe(F.refusal_panel, summaries, run_dir / "a2_refusals.png")
    return out


def main(pair="same_origin_cn", seeds=10, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pair=pair, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[A2] {len(specs)} matches: {len(REGIMES)} regimes x {seeds} seeds, "
          f"pair={pair}, mock={mock}")
    return run_and_finalize(specs, "A2", mock=mock, figure_fn=figures, resume=resume)
