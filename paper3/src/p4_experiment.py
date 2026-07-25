#!/usr/bin/env python3
"""P4 — opening-window suppression as a deployable defense.

The channel does two things (paper3/FINDINGS.md 2): it lifts the opening
(0.622 -> 0.815) and it slows the decay (floor-controlled L2-L0 +0.352
[+0.292, +0.411]). Both are real in the observational data, so this experiment
APPORTIONS them by closing the channel in one window or the other.

    full             channel open every round          (positive control)
    suppress_early   open from round 3 onward          (first 3 rounds closed)
    suppress_late    open only rounds 0-2              (the mirror image)
    none             never open                        (negative control)

If the opening is load-bearing:  suppress_early ~ none  <<  suppress_late ~ full.
If persistence is what matters:  suppress_late  ~ none  <<  suppress_early ~ full.

Either result is publishable and each implies a different operator control. The
deployable claim is protection-per-round-suppressed: `suppress_early` closes the
channel for 15% of the interaction.

Usage:
    python3 paper3/src/p4_experiment.py --mock --seeds 2 --rounds 8
    python3 paper3/src/p4_experiment.py --seeds 30 --pair self_local
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from rival_arena import config  # noqa: E402
from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET  # noqa: E402
from rival_arena.harness.channel import default_epistemic  # noqa: E402
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec  # noqa: E402
from experiments.common import pair_players, resolve_pair, run_and_finalize  # noqa: E402

OPEN_ROUNDS = 3   # the "opening window" the decomposition identified

# (arm, channel level, channel_window)
def arms(max_rounds: int):
    big = max_rounds + 10
    return [
        ("full", ChannelLevel.L2_OBSERVED, None),
        ("suppress_early", ChannelLevel.L2_OBSERVED, (OPEN_ROUNDS, big)),
        ("suppress_late", ChannelLevel.L2_OBSERVED, (0, OPEN_ROUNDS - 1)),
        ("none", ChannelLevel.L0_NONE, None),
    ]


def build_specs(pair="self_local", seeds=30, max_rounds=20, seed_offset=900,
                continuation_prob=0.97):
    ids = resolve_pair(pair)
    name = pair if isinstance(pair, str) else "x".join(ids)
    specs = []
    for arm, lvl, window in arms(max_rounds):
        for s in range(seed_offset, seed_offset + seeds):
            specs.append(MatchSpec(
                experiment_id="P4",
                cell_id=f"P4/{arm}/{name}",
                game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                      "max_rounds": max_rounds},
                              familiarity="canonical"),
                channel=lvl, epistemic=default_epistemic(lvl),
                players=pair_players(ids, s), seed=s,
                token_budget=DEFAULT_TOKEN_BUDGET,
                history_window=DEFAULT_HISTORY_WINDOW, framing="neutral",
                channel_window=window,
            ))
    return specs


def main() -> None:
    ap = argparse.ArgumentParser(description="P4 opening-window suppression")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--pair", default="self_local")
    ap.add_argument("--seed-offset", type=int, default=900)
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    if not args.mock and not (config.have_openrouter() or config.have_openai()):
        sys.exit("No API key / endpoint. Set OPENAI_API_BASE for vLLM, or --mock.")

    specs = build_specs(args.pair, args.seeds, args.rounds, args.seed_offset)
    print(f"P4: {len(specs)} matches — 4 arms x {args.seeds} seeds, pair={args.pair}")
    run_dir = run_and_finalize(specs, "P4", mock=args.mock,
                               concurrency=args.concurrency,
                               resume=not args.fresh)
    print(f"\nrun dir: {run_dir}")
    print(f"analyse: python3 paper3/src/p4_analyze.py {run_dir}")


if __name__ == "__main__":
    main()
