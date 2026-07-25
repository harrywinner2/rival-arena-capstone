#!/usr/bin/env python3
"""G0 — capability gate for the self-hosted model. Run this BEFORE P1/P3/P4.

The L4 work found no text effect at 1.5B and only a marginal one at 3B
(+0.175 [+0.0125, +0.300]). A predicate experiment on a model that does not respond to
readable communication measures nothing, so the whole GPU budget is gated here.

GATE (pre-registered, PROGRAM.md 12.4): the text-vs-none effect on IPD lock-in must have
a 95% CI excluding zero with a margin >= 0.15 (i.e. lower bound >= 0.15).

Usage:
    python3 paper3/src/g0_gate.py --mock --seeds 4
    python3 paper3/src/g0_gate.py --seeds 24 --pair self_local
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET  # noqa: E402
from rival_arena.harness.channel import default_epistemic  # noqa: E402
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec  # noqa: E402
from experiments.common import pair_players, resolve_pair, run_and_finalize  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
MARGIN = 0.15
LOCKIN_CUT = 0.8


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def newcombe(k1, n1, k2, n2):
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    return (p1 - p2,
            (p1 - p2) - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            (p1 - p2) + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def build_specs(pair: str, seeds: int, max_rounds: int, seed_offset: int):
    ids = resolve_pair(pair)
    name = pair if isinstance(pair, str) else "x".join(ids)
    specs = []
    for lvl in (ChannelLevel.L0_NONE, ChannelLevel.L2_OBSERVED):
        for s in range(seed_offset, seed_offset + seeds):
            specs.append(MatchSpec(
                experiment_id="G0",
                cell_id=f"G0/{lvl.value}/{name}",
                game=GameSpec("ipd", {"continuation_prob": 0.97,
                                      "max_rounds": max_rounds},
                              familiarity="canonical"),
                channel=lvl, epistemic=default_epistemic(lvl),
                players=pair_players(ids, s), seed=s,
                token_budget=DEFAULT_TOKEN_BUDGET,
                history_window=DEFAULT_HISTORY_WINDOW, framing="neutral",
            ))
    return specs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--pair", default="self_local")
    ap.add_argument("--seed-offset", type=int, default=200)
    ap.add_argument("--concurrency", type=int, default=16)
    args = ap.parse_args()

    specs = build_specs(args.pair, args.seeds, args.rounds, args.seed_offset)
    print(f"G0: {len(specs)} matches, pair={args.pair}, mock={args.mock}")
    run_dir = run_and_finalize(specs, "G0", mock=args.mock,
                               concurrency=args.concurrency)

    import pandas as pd
    df = pd.read_csv(Path(run_dir) / "rounds_long.csv", low_memory=False)
    if "refusal" in df.columns:
        df.loc[df.refusal == "api_error", "cooperative"] = np.nan
    m = df.groupby(["cell_id", "seed"]).cooperative.mean().reset_index()
    m["arm"] = m.cell_id.str.split("/").str[1]
    m["lockin"] = (m.cooperative > LOCKIN_CUT).astype(float)

    counts = {}
    lines = ["# G0 — self-hosted capability gate\n", f"Run: `{run_dir}`\n",
             "| arm | k/n | lock-in | Wilson 95% CI | mean C |", "|---|---|---:|---|---:|"]
    for a in ("L0_none", "L2_observed"):
        s = m[(m.arm == a) & m.lockin.notna()]
        if not len(s):
            continue
        k, n = int(s.lockin.sum()), len(s)
        counts[a] = (k, n)
        lo, hi = wilson(k, n)
        lines.append(f"| {a} | {k}/{n} | {k/n:.3f} | [{lo:.2f}, {hi:.2f}] | "
                     f"{s.cooperative.mean():.3f} |")

    verdict = "INDETERMINATE"
    if len(counts) == 2:
        rd, lo, hi = newcombe(*counts["L2_observed"], *counts["L0_none"])
        passed = lo >= MARGIN
        verdict = "PASS" if passed else "FAIL"
        lines += ["",
                  f"**text − none: {rd:+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]**",
                  f"\nGate requires lower bound >= {MARGIN}. -> **{verdict}**"]
        if not passed:
            lines.append(
                "\nPre-registered escalation: retry at 72B on 2xA100 and re-gate. If "
                "that also fails, the text program returns to OpenRouter and credits "
                "are bought for it. **Do not start P1/P3/P4 on this model.**")
        else:
            lines.append("\nProceed to P1, then P3 and P4 on this model.")

    OUT.mkdir(parents=True, exist_ok=True)
    txt = "\n".join(lines)
    (OUT / "g0_gate.md").write_text(txt)
    print("\n" + txt)
    sys.exit(0 if verdict == "PASS" else 1)


if __name__ == "__main__":
    main()
