"""A3 — origin moderation of the channel effect (H4).

Reuses the A1 IPD channel environment but SWEEPS THE PAIR across the origin
matrix (models.yaml): same-family / same-origin / cross-origin. Cells =
pair x channel x seeds; primary outcome is the same lock-in proportion (P17)
as A1, read *across* pairs at a fixed rung.

The point of A3 is moderation, not a main effect: does the L0->L3 lock-in slope
DIFFER across same- vs cross-origin pairs? Origin here is a confounded proxy
(size / quant / serving / tuning all travel with it), so this is a descriptive
case study of these specific models, reported as such — not a causal claim about
"nationality" of models (P1, P2).
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from .common import pair_players, resolve_pair, run_and_finalize

ALL_LEVELS = [ChannelLevel.L0_NONE, ChannelLevel.L1_SIGNAL,
              ChannelLevel.L2_OBSERVED, ChannelLevel.L3_PRIVATE]

DEFAULT_PAIRS = ["same_family", "same_origin_cn", "same_origin_west",
                 "cross_origin", "cross_origin_2"]


def build_specs(
    pairs=DEFAULT_PAIRS,
    seeds: int = 10,
    levels=ALL_LEVELS,
    familiarity: str = "canonical",
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,                 # disjoint range for confirmatory runs (P4)
) -> list[MatchSpec]:
    specs: list[MatchSpec] = []
    for pair in pairs:
        model_ids = resolve_pair(pair)
        pairname = pair if isinstance(pair, str) else "x".join(model_ids)
        for lvl in levels:
            for s in range(seed_offset, seed_offset + seeds):
                specs.append(MatchSpec(
                    experiment_id="A3",
                    cell_id=f"A3/{lvl.value}/{pairname}",
                    game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                          "max_rounds": max_rounds},
                                  familiarity=familiarity),
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

    def _safe(fn, *a, **kw):
        try:
            out.append(fn(*a, **kw))
        except Exception as e:  # figures must never sink a completed run
            print(f"[A3] figure {getattr(fn, '__name__', fn)} failed: {e}")

    # origin comparison at a FIXED channel: lock-in grouped by pair for each rung.
    channels = sorted({s.get("channel") for s in summaries},
                      key=lambda c: [lv.value for lv in ALL_LEVELS].index(c)
                      if c in [lv.value for lv in ALL_LEVELS] else 99)
    for ch in channels:
        cs = [s for s in summaries if s.get("channel") == ch]
        cs.sort(key=lambda s: s["cell_id"])
        if cs:
            _safe(F.lockin_bar, cs, run_dir / f"a3_lockin_{ch}.png",
                  title=f"A3 origin comparison — lock-in by pair ({ch})")

    # partial-eta panel (origin is second-order) if the data supports it; built
    # from a small {factor: eta2}-style mapping is brittle, so guard it.
    if hasattr(F, "origin_partial_eta"):
        try:
            import pandas as pd
            rows = [{"pair": s["cell_id"].split("/")[-1],
                     "channel": s.get("channel"),
                     "lockin": s.get("lockin_proportion")}
                    for s in summaries if s.get("lockin_proportion") is not None]
            if rows:
                df = pd.DataFrame(rows)
                # crude variance-share proxy by factor (descriptive only).
                shares = {}
                total = df["lockin"].var(ddof=0) or 0.0
                for fac in ("channel", "pair"):
                    grp = df.groupby(fac)["lockin"].mean()
                    shares[fac] = float(grp.var(ddof=0)) if len(grp) > 1 else 0.0
                _safe(F.origin_partial_eta, shares, run_dir / "a3_partial_eta.png",
                      title="A3 variance share: channel vs origin (descriptive)")
        except Exception as e:
            print(f"[A3] partial-eta panel skipped: {e}")

    _safe(F.refusal_panel, summaries, run_dir / "a3_refusals.png")
    return out


def main(pairs=DEFAULT_PAIRS, seeds=10, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pairs=pairs, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[A3] {len(specs)} matches: {len(pairs)} pairs x {len(ALL_LEVELS)} rungs "
          f"x {seeds} seeds, mock={mock}")
    return run_and_finalize(specs, "A3", mock=mock, figure_fn=figures, resume=resume)
