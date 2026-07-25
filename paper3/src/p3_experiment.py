#!/usr/bin/env python3
"""P3 — the lever factorial (pre-registered: paper3/prereg/p3_levers.md).

"Communication is the DOMINANT attack surface" is a comparative claim the prior work
never tested comparatively. This crosses the three candidate levers in one design:

    expressiveness  intention_only | proposal_only | free
    throughput      once (round 0 only) | every round
    observability   observed (L2) | private (L3)

3 x 2 x 2 = 12 cells. Pre-registered ordinal prediction:
    eta2(expressiveness) > eta2(throughput) ~ eta2(observability),
    with expressiveness at least 3x the larger of the other two.

Usage:
    python3 paper3/src/p3_experiment.py --mock --seeds 2 --rounds 6
    python3 paper3/src/p3_experiment.py --seeds 24 --pair self_local
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(Path(__file__).parent))

from rival_arena import config  # noqa: E402
from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET  # noqa: E402
from rival_arena.harness.channel import default_epistemic  # noqa: E402
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec  # noqa: E402
from experiments.common import pair_players, resolve_pair, run_and_finalize  # noqa: E402

# registers own_intention_only / joint_proposal_only into the prompt table
import p1_experiment  # noqa: F401,E402

EXPRESSIVENESS = [
    ("intention", "own_intention_only"),
    ("proposal", "joint_proposal_only"),
    ("free", None),
]
# (label, channel_window). "once" = the channel is open only in round 0.
THROUGHPUT = [("once", (0, 0)), ("every", None)]
OBSERVABILITY = [("observed", ChannelLevel.L2_OBSERVED),
                 ("private", ChannelLevel.L3_PRIVATE)]


def build_specs(pair="self_local", seeds=24, max_rounds=20, seed_offset=700,
                continuation_prob=0.97):
    ids = resolve_pair(pair)
    name = pair if isinstance(pair, str) else "x".join(ids)
    specs = []
    for elab, restriction in EXPRESSIVENESS:
        for tlab, window in THROUGHPUT:
            for olab, lvl in OBSERVABILITY:
                for s in range(seed_offset, seed_offset + seeds):
                    specs.append(MatchSpec(
                        experiment_id="P3",
                        cell_id=f"P3/{elab}/{tlab}/{olab}/{name}",
                        game=GameSpec("ipd",
                                      {"continuation_prob": continuation_prob,
                                       "max_rounds": max_rounds},
                                      familiarity="canonical"),
                        channel=lvl, epistemic=default_epistemic(lvl),
                        players=pair_players(ids, s), seed=s,
                        token_budget=DEFAULT_TOKEN_BUDGET,
                        history_window=DEFAULT_HISTORY_WINDOW, framing="neutral",
                        message_restriction=restriction,
                        channel_window=window,
                    ))
    return specs


def main() -> None:
    ap = argparse.ArgumentParser(description="P3 lever factorial")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--pair", default="self_local")
    ap.add_argument("--seed-offset", type=int, default=700)
    ap.add_argument("--concurrency", type=int, default=16)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    if not args.mock and not (config.have_openrouter() or config.have_openai()):
        sys.exit("No API key / endpoint. Set OPENAI_API_BASE for vLLM, or --mock.")

    specs = build_specs(args.pair, args.seeds, args.rounds, args.seed_offset)
    print(f"P3: {len(specs)} matches — 3 expressiveness x 2 throughput x "
          f"2 observability x {args.seeds} seeds, pair={args.pair}")
    run_dir = run_and_finalize(specs, "P3", mock=args.mock,
                               concurrency=args.concurrency,
                               resume=not args.fresh)
    print(f"\nrun dir: {run_dir}")
    print(f"analyse: python3 paper3/src/p3_analyze.py {run_dir}")


if __name__ == "__main__":
    main()
