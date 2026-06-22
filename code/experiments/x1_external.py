"""X1 — EXTERNAL-VALIDITY replication of the load-bearing results.

A thin wrapper (NO new apparatus) that drives the EXISTING experiment drivers on a
chosen ``--pair`` to replicate the minimal load-bearing set that carries the paper,
so we can claim the findings generalize **beyond the original 4-model set** to (a) a
FRONTIER model (GPT-4o) and (b) a 2nd distinct model family (Gemini).

The four load-bearing cells (see ``docs/paper_facts.md`` §3–4):
  1. A1 channel -> cooperation : L0 vs L2  (content-not-bandwidth; IPD).
  2. B1 channel -> collusion   : L0 vs L3 on NOVEL demand (supracompetitive).
  3. S2 de-confound            : threat x {obsF, obsT}, force_report=True,
                                 b_modes=('explicit_ask',), channels=('none',).
  4. E1-escalate               : P0 vs P3 (instruction-is-load-bearing); the driver
                                 sweeps the full P0..P5 ladder, of which P0 & P3 are
                                 the load-bearing endpoints.

This file ONLY orchestrates the existing drivers with their public ``main()`` /
``build_specs()`` entry points + a ``pair`` argument. It adds no new game, metric,
or model. Run one cell with ``--only {a1,b1,s2,e1}`` or all four (default).

Examples
--------
    # offline wiring check (zero API spend), frontier self-pair:
    .venv/bin/python -m experiments.x1_external --pair frontier_self --mock --seeds 2

    # LIVE frontier replication, 12 seeds:
    .venv/bin/python -m experiments.x1_external --pair frontier_self --seeds 12 --concurrency 24
"""

from __future__ import annotations

import argparse

from rival_arena.schemas import ChannelLevel

from . import a1_channel, b1_pricing, e1_escalate, s2_cover

# Load-bearing channel restrictions (keep the spend on the cells that carry the paper).
A1_LEVELS = [ChannelLevel.L0_NONE, ChannelLevel.L2_OBSERVED]      # content-not-bandwidth
B1_LEVELS = [ChannelLevel.L0_NONE, ChannelLevel.L3_PRIVATE]       # supracompetitive


def run_a1(pair: str, seeds: int, mock: bool, concurrency: int | None,
           seed_offset: int, max_rounds: int):
    """A1 L0 vs L2, both familiarities (novel = anti-memorization)."""
    return a1_channel.main(
        pair=pair, seeds=seeds, mock=mock, max_rounds=max_rounds,
        seed_offset=seed_offset, levels=A1_LEVELS,
        familiarities=("canonical", "novel"),
    )


def run_b1(pair: str, seeds: int, mock: bool, concurrency: int | None,
           seed_offset: int, max_rounds: int):
    """B1 L0 vs L3 on NOVEL demand (the supracompetitive floor)."""
    return b1_pricing.main(
        pair=pair, seeds=seeds, mock=mock, max_rounds=max_rounds,
        seed_offset=seed_offset, levels=B1_LEVELS, demand_specs=("novel",),
    )


def run_s2(pair: str, seeds: int, mock: bool, concurrency: int | None,
           seed_offset: int, **_):
    """S2 de-confound: threat x {obsF,obsT}, delivery held fixed at the drive route."""
    return s2_cover.main(
        pair=pair, seeds=seeds, mock=mock, seed_offset=seed_offset,
        concurrency=concurrency or 8, force_report=True,
        b_modes=("explicit_ask",), channels=("none",), pi_observes=(True, False),
    )


def run_e1(pair: str, seeds: int, mock: bool, concurrency: int | None,
           seed_offset: int, **_):
    """E1-escalate P0..P5 ladder (P0 vs P3 are the load-bearing endpoints)."""
    return e1_escalate.main(
        pair=pair, seeds=seeds, mock=mock, seed_offset=seed_offset,
        concurrency=concurrency or 8,
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pair", required=True,
                    help="named pair from configs/models.yaml, e.g. frontier_self, "
                         "frontier_gpt_open, family2_self, family2_open")
    ap.add_argument("--only", choices=["a1", "b1", "s2", "e1"], default=None,
                    help="run a single load-bearing cell (default: all four)")
    ap.add_argument("--seeds", type=int, default=12,
                    help="seeds per cell (10-12 recommended for a credible replication)")
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--max-rounds", type=int, default=20, help="A1/B1 horizon")
    ap.add_argument("--concurrency", type=int, default=24)
    ap.add_argument("--mock", action="store_true",
                    help="MockLLM, zero API spend — wiring check only")
    a = ap.parse_args()

    cells = {"a1": run_a1, "b1": run_b1, "s2": run_s2, "e1": run_e1}
    todo = [a.only] if a.only else list(cells)
    print(f"[X1] external-validity replication: pair={a.pair} seeds={a.seeds} "
          f"cells={todo} mock={a.mock}")
    for name in todo:
        print(f"\n========== X1 :: {name.upper()} :: pair={a.pair} ==========")
        cells[name](a.pair, a.seeds, a.mock, a.concurrency, a.seed_offset,
                    max_rounds=a.max_rounds)


if __name__ == "__main__":
    main()
