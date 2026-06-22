#!/usr/bin/env python3
"""F2-bottleneck probe: does bandwidth PRESSURE induce compressed shorthand?

C4 found no secret-language emergence at the normal token budget (messages elongate).
The condition most likely to induce a code is a hard bandwidth bottleneck. Re-run the
A1 IPD free-text channel (L2) at a TIGHT message budget vs a NORMAL one, on the same
pair/seeds, and compare compression_ratio / n-gram reuse / message length.
"""
from __future__ import annotations
import dataclasses, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from rival_arena.schemas import ChannelLevel  # noqa: E402
from experiments import a1_channel            # noqa: E402
from experiments.common import run_and_finalize  # noqa: E402

BUDGETS = {"tight": 12, "normal": 256}   # ~3 words vs ~64 words per message


def build():
    specs = []
    for name, bt in BUDGETS.items():
        base = a1_channel.build_specs(
            pair="same_origin_cn", seeds=10, familiarities=("canonical",),
            levels=[ChannelLevel.L2_OBSERVED], max_rounds=20, token_budget=bt,
            seed_offset=300)
        for s in base:
            specs.append(dataclasses.replace(
                s, experiment_id="F2B", token_budget=bt,
                cell_id=f"F2B/budget_{name}/{s.channel.value}/same_origin_cn"))
    return specs


def figures(run_dir, summaries, results):
    return []


if __name__ == "__main__":
    specs = build()
    print(f"[F2B] {len(specs)} matches: {len(BUDGETS)} budgets x 1 rung x 10 seeds")
    run_and_finalize(specs, "F2B", mock=False, figure_fn=figures)
