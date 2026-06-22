#!/usr/bin/env python3
"""Run a whole program of experiments in parallel (one shared pool).

Examples:
    # offline smoke of the parallel orchestrator:
    python3 scripts/run_program.py pilot --mock

    # the confirmatory spine, high concurrency:
    python3 scripts/run_program.py spine --concurrency 24

    # the full data-rich program (spine + A2/A3/A4/A5 + B1-origin):
    python3 scripts/run_program.py wide --concurrency 24
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rival_arena import config  # noqa: E402
from rival_arena.harness.runner import HardAPIError  # noqa: E402
from experiments.program import PROFILES, run_program  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Rival-AI-Arena parallel program runner")
    ap.add_argument("profile", choices=list(PROFILES))
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--concurrency", type=int, default=24)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--seeds", type=int, default=None, help="override per-experiment seeds")
    ap.add_argument("--fresh", action="store_true", help="ignore checkpoint, start over")
    args = ap.parse_args()

    if not args.mock and not (config.have_openrouter() or config.have_openai()):
        sys.exit("No API key found. Add OPENROUTER_API_KEY to .env or pass --mock.")

    try:
        run_program(args.profile, mock=args.mock, concurrency=args.concurrency,
                    resume=not args.fresh, seeds=args.seeds, rounds=args.rounds)
    except HardAPIError as e:
        sys.exit(f"\n{e}\n\nCompleted matches are checkpointed; fix the key/credits "
                 f"and re-run the same command to resume.")


if __name__ == "__main__":
    main()
