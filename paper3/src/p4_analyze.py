#!/usr/bin/env python3
"""Analyse P4: apportion the channel effect between the opening and persistence,
and price the defense.

Usage: python3 paper3/src/p4_analyze.py <run_dir>
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260724)
LOCKIN_CUT = 0.8
OPEN_ROUNDS = 3
ARMS = ["none", "suppress_early", "suppress_late", "full"]


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


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run_dir = Path(sys.argv[1])
    df = pd.read_csv(run_dir / "rounds_long.csv", low_memory=False)
    if "refusal" in df.columns:
        df.loc[df.refusal == "api_error", "cooperative"] = np.nan
    df["arm"] = df.cell_id.str.split("/").str[1]

    rows = []
    for (cid, seed), g in df.groupby(["cell_id", "seed"], dropna=False):
        n = int(g.round_index.max()) + 1
        op = g[g.round_index < OPEN_ROUNDS].cooperative.mean()
        cl = g[g.round_index >= n / 2].cooperative.mean()
        rows.append(dict(arm=g.arm.iloc[0], seed=seed, C=g.cooperative.mean(),
                         open=op, close=cl, decay=(cl - op) if pd.notna(cl) else np.nan))
    m = pd.DataFrame(rows)
    m = m[m.C.notna()].copy()
    m["lockin"] = (m.C > LOCKIN_CUT).astype(float)

    out = ["# P4 — opening-window suppression as a defense\n",
           f"Run: `{run_dir}` — {len(m)} matches. Opening window = rounds "
           f"0–{OPEN_ROUNDS-1}.\n"]

    out.append("\n## Arms\n")
    out.append("| arm | n | lock-in | Wilson 95% CI | mean C | opening C | closing C | decay |")
    out.append("|---|---:|---:|---|---:|---:|---:|---:|")
    counts = {}
    for a in ARMS:
        s = m[m.arm == a]
        if not len(s):
            continue
        k, n = int(s.lockin.sum()), len(s)
        counts[a] = (k, n)
        lo, hi = wilson(k, n)
        out.append(f"| {a} | {n} | {k/n:.3f} | [{lo:.2f}, {hi:.2f}] | {s.C.mean():.3f} | "
                   f"{s['open'].mean():.3f} | {s['close'].mean():.3f} | "
                   f"{s.decay.mean():+.3f} |")

    def con(a, b):
        if a not in counts or b not in counts:
            return None
        k1, n1 = counts[a]
        k2, n2 = counts[b]
        _, p = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])
        rd, lo, hi = newcombe(k1, n1, k2, n2)
        return p, rd, lo, hi

    out.append("\n\n## Contrasts\n")
    out.append("| contrast | p | risk difference | 95% CI |")
    out.append("|---|---:|---:|---|")
    pairs = [("suppress_early", "full"), ("suppress_early", "none"),
             ("suppress_late", "full"), ("suppress_late", "none"),
             ("full", "none")]
    res = {}
    for a, b in pairs:
        r = con(a, b)
        if r:
            res[(a, b)] = r
            p, rd, lo, hi = r
            out.append(f"| {a} vs {b} | {p:.2e} | {rd:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")

    # ---- apportionment ----
    out.append("\n\n## Apportionment\n")
    if all(a in counts for a in ARMS):
        full = counts["full"][0] / counts["full"][1]
        none = counts["none"][0] / counts["none"][1]
        se = counts["suppress_early"][0] / counts["suppress_early"][1]
        sl = counts["suppress_late"][0] / counts["suppress_late"][1]
        span = full - none
        if abs(span) > 1e-9:
            early_share = (full - se) / span   # protection from closing the opening
            late_share = (full - sl) / span    # protection from closing the rest
            out.append(f"- total channel effect (full − none): **{span:+.3f}**")
            out.append(f"- protection from suppressing the OPENING "
                       f"({OPEN_ROUNDS} rounds): **{full - se:+.3f}** "
                       f"({early_share:.0%} of the total)")
            out.append(f"- protection from suppressing the REST: "
                       f"**{full - sl:+.3f}** ({late_share:.0%} of the total)")
            out.append("")
            if early_share >= 0.6:
                out.append("**Reading: the opening is load-bearing.** Closing the "
                           f"channel for {OPEN_ROUNDS} of the rounds captures most of "
                           "the available protection — a cheap, narrowly scoped, "
                           "auditable control.")
            elif late_share >= 0.6:
                out.append("**Reading: persistence is load-bearing.** Early suppression "
                           "does not protect; the channel must be closed for the long "
                           "run, which is a far more costly control.")
            else:
                out.append("**Reading: the effect is split.** Neither window dominates; "
                           "report both shares and price the control accordingly.")

    # ---- defense pricing ----
    out.append("\n\n## Defense pricing\n")
    if "suppress_early" in counts and "full" in counts and "none" in counts:
        rounds_total = int(df.groupby(["cell_id", "seed"]).round_index.max().mean()) + 1
        frac = OPEN_ROUNDS / max(rounds_total, 1)
        full = counts["full"][0] / counts["full"][1]
        none = counts["none"][0] / counts["none"][1]
        se = counts["suppress_early"][0] / counts["suppress_early"][1]
        span = full - none
        prot = (full - se) / span if abs(span) > 1e-9 else np.nan
        out.append(f"- rounds suppressed: {OPEN_ROUNDS}/{rounds_total} = "
                   f"**{frac:.0%} of the interaction**")
        out.append(f"- protection captured: **{prot:.0%} of the full-suppression effect**")
        if np.isfinite(prot) and frac > 0:
            out.append(f"- protection per round suppressed: **{prot/frac:.2f}x** "
                       "the naive linear rate" if prot > frac else
                       f"- protection per round suppressed: {prot/frac:.2f}x "
                       "(no better than closing the channel uniformly)")

    m.to_csv(OUT / "p4_matches.csv", index=False)
    txt = "\n".join(out)
    (OUT / "p4_results.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
