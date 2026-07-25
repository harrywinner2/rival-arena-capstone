#!/usr/bin/env python3
"""Analyse P3 as pre-registered: effect sizes in ONE ordering, not four separate tests.

Reports partial eta-squared for each factor from a three-way ANOVA on mean cooperation
(continuous, so eta2 is well behaved), plus lock-in with Wilson intervals, plus the
pre-registered ordinal prediction verdict.

Usage: python3 paper3/src/p3_analyze.py <run_dir>
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260724)
LOCKIN_CUT = 0.8
FACTORS = ["expressiveness", "throughput", "observability"]
DOMINANCE_RATIO = 3.0


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def partial_eta2(df: pd.DataFrame, y: str, factors: list[str]) -> dict[str, float]:
    """Type-II-ish partial eta^2 via sums of squares from full vs reduced group means."""
    yv = df[y].values.astype(float)
    grand = yv.mean()
    ss_total = ((yv - grand) ** 2).sum()
    out = {}
    for f in factors:
        ss_f = 0.0
        for lev, g in df.groupby(f, observed=True):
            ss_f += len(g) * (g[y].mean() - grand) ** 2
        # residual after removing all factor main effects
        pred = np.full(len(df), grand)
        for ff in factors:
            adj = df.groupby(ff, observed=True)[y].transform("mean") - grand
            pred = pred + adj.values
        ss_err = ((yv - pred) ** 2).sum()
        out[f] = ss_f / (ss_f + ss_err) if (ss_f + ss_err) > 0 else np.nan
    return out


def boot_eta2(df, y, factors, nb=2000):
    keys = {f: [] for f in factors}
    for _ in range(nb):
        d = df.sample(len(df), replace=True, random_state=int(RNG.integers(1e9)))
        e = partial_eta2(d, y, factors)
        for f in factors:
            keys[f].append(e[f])
    return {f: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
            for f, v in keys.items()}


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run_dir = Path(sys.argv[1])
    df = pd.read_csv(run_dir / "rounds_long.csv", low_memory=False)
    if "refusal" in df.columns:
        df["api_err"] = (df.refusal == "api_error").astype(float)
        df.loc[df.api_err == 1, "cooperative"] = np.nan
    else:
        df["api_err"] = 0.0

    parts = df.cell_id.str.split("/", expand=True)
    df["expressiveness"] = parts[1]
    df["throughput"] = parts[2]
    df["observability"] = parts[3]

    m = df.groupby(["cell_id", "seed"], dropna=False).agg(
        expressiveness=("expressiveness", "first"),
        throughput=("throughput", "first"),
        observability=("observability", "first"),
        C=("cooperative", "mean"),
        api_err=("api_err", "mean"),
    ).reset_index()
    m = m[m.C.notna()].copy()
    m["lockin"] = (m.C > LOCKIN_CUT).astype(float)

    out = ["# P3 — the lever factorial\n", f"Run: `{run_dir}` — {len(m)} matches.\n",
           "Pre-registered in `paper3/prereg/p3_levers.md`.\n"]

    out.append("\n## Cell means\n")
    out.append("| expressiveness | throughput | observability | n | lock-in | "
               "Wilson 95% CI | mean C |")
    out.append("|---|---|---|---:|---:|---|---:|")
    for (e, t, o), g in m.groupby(FACTORS, observed=True):
        k, n = int(g.lockin.sum()), len(g)
        lo, hi = wilson(k, n)
        out.append(f"| {e} | {t} | {o} | {n} | {k/n:.3f} | [{lo:.2f}, {hi:.2f}] | "
                   f"{g.C.mean():.3f} |")

    out.append("\n\n## Marginal means by factor\n")
    for f in FACTORS:
        out.append(f"\n**{f}**\n")
        out.append("| level | n | lock-in | mean C |")
        out.append("|---|---:|---:|---:|")
        for lev, g in m.groupby(f, observed=True):
            out.append(f"| {lev} | {len(g)} | {g.lockin.mean():.3f} | {g.C.mean():.3f} |")

    # ---- the pre-registered ordering ----
    e2 = partial_eta2(m, "C", FACTORS)
    ci = boot_eta2(m, "C", FACTORS)
    out.append("\n\n## Effect sizes in one ordering (the pre-registered test)\n")
    out.append("Partial eta-squared on mean cooperation, bootstrap 95% CI.\n")
    out.append("| factor | partial eta2 | 95% CI |")
    out.append("|---|---:|---|")
    for f, v in sorted(e2.items(), key=lambda kv: -kv[1]):
        out.append(f"| {f} | {v:.4f} | [{ci[f][0]:.4f}, {ci[f][1]:.4f}] |")

    expr = e2["expressiveness"]
    other = max(e2["throughput"], e2["observability"])
    ratio = expr / other if other > 0 else np.inf
    ranked = sorted(e2, key=lambda f: -e2[f])
    ordering_ok = ranked[0] == "expressiveness"
    dominance_ok = ratio >= DOMINANCE_RATIO
    verdict = ("SUPPORTED" if (ordering_ok and dominance_ok)
               else "PARTIAL (ordering holds, dominance ratio not met)"
               if ordering_ok else "NOT SUPPORTED")
    out.append(f"\nObserved ordering: {' > '.join(ranked)}")
    out.append(f"\nexpressiveness / max(other) = **{ratio:.2f}x** "
               f"(prediction required >= {DOMINANCE_RATIO}x)")
    out.append(f"\n**Pre-registered ordinal prediction: {verdict}**")

    out.append(f"\n\nAPI error rate: {m.api_err.mean():.3f} "
               "(excluded from behavioural metrics).")

    m.to_csv(OUT / "p3_matches.csv", index=False)
    txt = "\n".join(out)
    (OUT / "p3_results.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
