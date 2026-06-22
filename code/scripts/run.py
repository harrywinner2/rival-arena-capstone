#!/usr/bin/env python3
"""Run an experiment from the command line.

Examples:
    # offline, zero-cost smoke of the whole spine (MockLLM):
    python3 scripts/run.py a1 --mock --seeds 3 --rounds 6

    # live A5 validity gate on a cheap model:
    python3 scripts/run.py a5 --model llama-8b --seeds 8

    # live B1 money-shot, cross-origin, full seeds:
    python3 scripts/run.py b1 --pair cross_origin --seeds 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rival_arena import config  # noqa: E402
from rival_arena.harness.runner import HardAPIError  # noqa: E402
from experiments import (  # noqa: E402
    a1_channel, a5_baseline, b1_pricing, c7_covert, d1_canary,
)


def main():
    ap = argparse.ArgumentParser(description="Rival-AI-Arena experiment runner")
    ap.add_argument("experiment", choices=["a1", "a5", "b1", "c7", "d1"])
    ap.add_argument("--mock", action="store_true",
                    help="use MockLLM (no API spend) for offline pipeline testing")
    ap.add_argument("--seeds", type=int, default=None)
    ap.add_argument("--rounds", type=int, default=None, help="max_rounds per match")
    ap.add_argument("--pair", default=None, help="named pair (a1/b1), e.g. cross_origin")
    ap.add_argument("--model", default=None, help="LLM model id (a5)")
    ap.add_argument("--seed-offset", type=int, default=0,
                    help="start seeds at this offset — use a disjoint range for "
                         "confirmatory runs so they don't reuse exploratory seeds (P4)")
    ap.add_argument("--fresh", action="store_true",
                    help="ignore any existing checkpoint and start over "
                         "(default: resume — completed matches are skipped)")
    args = ap.parse_args()

    # guard rails: live runs need a key
    if not args.mock and not (config.have_openrouter() or config.have_openai()):
        sys.exit("No API key found. Add OPENROUTER_API_KEY / OPENAI_API_KEY to .env, "
                 "or pass --mock for an offline run.")

    kw = {"mock": args.mock, "seed_offset": args.seed_offset, "resume": not args.fresh}
    if args.rounds is not None:
        kw["max_rounds"] = args.rounds

    try:
        if args.experiment == "a5":
            model = args.model or ("llama-8b" if args.mock else "qwen-72b")
            a5_baseline.main(model=model, seeds=args.seeds or (3 if args.mock else 8), **kw)
        elif args.experiment == "a1":
            pair = args.pair or ("smoke_pair" if args.mock else "same_origin_cn")
            a1_channel.main(pair=pair, seeds=args.seeds or (3 if args.mock else 20), **kw)
        elif args.experiment == "b1":
            pair = args.pair or ("smoke_pair" if args.mock else "cross_origin")
            b1_pricing.main(pair=pair, seeds=args.seeds or (3 if args.mock else 20), **kw)
        elif args.experiment == "c7":
            pair = args.pair or ("smoke_pair" if args.mock else "cross_origin")
            c7_covert.main(pair=pair, seeds=args.seeds or (2 if args.mock else 12), **kw)
        elif args.experiment == "d1":
            pair = args.pair or ("smoke_pair" if args.mock else "same_origin_cn")
            d1_canary.main(pair=pair, seeds=args.seeds or (2 if args.mock else 10), **kw)
    except HardAPIError as e:
        sys.exit(f"\n{e}\n\nNo data was written. Fix the key/credits and re-run.")


if __name__ == "__main__":
    main()
