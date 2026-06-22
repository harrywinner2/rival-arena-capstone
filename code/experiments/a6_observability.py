"""A6 — action-observability / monitoring structure (content-vs-observation).

Separates two things normally bundled into "the channel effect": (a) a *message*
channel, vs (b) whether each agent simply *observes the other's past actions*
(the folk-theorem ingredient). This is a WITHIN-DESIGN validation: all three
conditions run on the SAME pairs and SAME seeds in one driver, so the contrast
is apples-to-apples (no borrowing cells from a separate A1 run).

Three comparable conditions per pair/seed:

    none : channel=L0_NONE, observe_actions=False
           (no messages, and the other's past moves are hidden)
    obs  : channel=L0_NONE, observe_actions=True
           (no messages, but each seat observes the other's past actions —
            the pure folk-theorem ingredient)
    msg  : channel=L2_OBSERVED (observe_actions=True, its natural default)
           (full message channel)

The contrast none -> obs isolates mere observability; obs -> msg isolates the
*content* of messages on top of observability. If most of the channel effect is
content rather than observability, obs sits near none and msg jumps above both.

ipd, canonical; runs both pairs (same_origin_cn, cross_origin). cell_id is
``A6/<cond>/<pair>`` with cond in {none, obs, msg} (§ experiments.md A6).
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from .common import pair_players, resolve_pair, run_and_finalize

# (cond label, channel, observe_actions) — the three comparable conditions
CONDITIONS = [
    ("none", ChannelLevel.L0_NONE, False),     # no obs, no messages
    ("obs", ChannelLevel.L0_NONE, True),       # observe past actions, no messages
    ("msg", ChannelLevel.L2_OBSERVED, True),   # full message channel
]
PAIRS = ("same_origin_cn", "cross_origin")


def build_specs(
    pairs=PAIRS,
    seeds: int = 20,
    conditions=CONDITIONS,
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,
) -> list[MatchSpec]:
    specs: list[MatchSpec] = []
    for pair in pairs:
        model_ids = resolve_pair(pair)
        pairname = pair if isinstance(pair, str) else "x".join(model_ids)
        for cond, channel, observe in conditions:
            for s in range(seed_offset, seed_offset + seeds):
                specs.append(MatchSpec(
                    experiment_id="A6",
                    cell_id=f"A6/{cond}/{pairname}",
                    game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                          "max_rounds": max_rounds}),
                    channel=channel,
                    epistemic=default_epistemic(channel),
                    players=pair_players(model_ids, s),
                    seed=s,
                    token_budget=token_budget,
                    history_window=DEFAULT_HISTORY_WINDOW,
                    framing=framing,
                    observe_actions=observe,          # A6 history hook
                    state_observability=None,         # unstated (control cell count)
                ))
    return specs


def figures(run_dir, summaries, results):
    from rival_arena.viz import figures as F
    out = []
    try:
        cs = sorted(summaries, key=lambda s: s["cell_id"])
        if cs:
            out.append(F.lockin_bar(cs, run_dir / "a6_lockin.png",
                                    title="A6 content-vs-observation — IPD (none/obs/msg)"))
    except Exception as e:
        print(f"[A6] lockin_bar skipped: {e}")
    try:
        out.append(F.refusal_panel(summaries, run_dir / "a6_refusals.png"))
    except Exception as e:
        print(f"[A6] refusal_panel skipped: {e}")
    return out


def _print_content_table(run_dir, summaries, results):
    """Per-pair none/obs/msg lock-in + mean-C table (the key contrast)."""
    by_cell = {s["cell_id"]: s for s in summaries}
    cond_labels = [c[0] for c in CONDITIONS]

    def _f(v):
        return format(v, ".2f") if isinstance(v, (int, float)) else " n/a"

    print("\n===== A6: content-vs-observation (none vs obs vs msg) =====")
    for pair in PAIRS:
        model_ids = resolve_pair(pair)
        pairname = pair if isinstance(pair, str) else "x".join(model_ids)
        print(f"\n  pair = {pairname}")
        print(f"    {'cond':<6} {'n':>3}  {'lock-in':>8}  {'mean-C':>7}")
        for cond in cond_labels:
            s = by_cell.get(f"A6/{cond}/{pairname}")
            if s is None:
                print(f"    {cond:<6} (missing)")
                continue
            print(f"    {cond:<6} {s['n_matches']:>3}  "
                  f"{_f(s.get('lockin_proportion')):>8}  "
                  f"{_f(s.get('coop_endstate_mean')):>7}")
    return []


def main(pairs=PAIRS, seeds=20, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    if isinstance(pairs, str):
        pairs = (pairs,)
    specs = build_specs(pairs=pairs, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    n_cells = len(CONDITIONS) * len(pairs)
    print(f"[A6] {len(specs)} matches: {len(CONDITIONS)} conditions (none/obs/msg) x "
          f"{len(pairs)} pairs ({n_cells} cells) x {seeds} seeds "
          f"(offset {seed_offset}), ipd, mock={mock}")

    def _figs(run_dir, summaries, results):
        _print_content_table(run_dir, summaries, results)
        return figures(run_dir, summaries, results)

    return run_and_finalize(specs, "A6", mock=mock, figure_fn=_figs, resume=resume)
