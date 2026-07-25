#!/usr/bin/env python3
"""Analyse a P1 run exactly as pre-registered (paper3/prereg/p1_proposal.md).

Runs the manipulation check first; H1 is only interpreted on arms that pass it.
Primary contrast: proposal vs intention (Fisher exact, two-sided, alpha 0.05,
uncorrected). Secondary contrasts under Benjamini-Hochberg FDR at 0.05.

Usage: python3 paper3/src/p1_analyze.py <run_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import fisher_exact

sys.path.insert(0, str(Path(__file__).parent))
from proposal_predicate import classify  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
LOCKIN_CUT = 0.8
ARM_ORDER = ["none", "menu", "intention", "proposal", "free"]

PRIMARY = ("proposal", "intention")
SECONDARY = [("proposal", "free"), ("intention", "none"), ("free", "none"),
             ("menu", "none")]


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def newcombe_rd(k1, n1, k2, n2):
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    p1, p2 = k1 / n1, k2 / n2
    lo = (p1 - p2) - np.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = (p1 - p2) + np.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return p1 - p2, lo, hi


def bh(pvals, alpha=0.05):
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    crit = alpha * (np.arange(1, m + 1)) / m
    passed = p[order] <= crit
    kmax = np.max(np.where(passed)[0]) + 1 if passed.any() else 0
    out = np.zeros(m, bool)
    out[order[:kmax]] = True
    return out


def load_rounds(run_dir: Path) -> pd.DataFrame:
    f = run_dir / "rounds_long.csv"
    if not f.exists():
        sys.exit(f"no rounds_long.csv in {run_dir}")
    df = pd.read_csv(f, low_memory=False)
    df["arm"] = df.cell_id.str.split("/").str[1]
    return df


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    run_dir = Path(sys.argv[1])
    df = load_rounds(run_dir)

    cls = pd.DataFrame([classify(t) for t in df.get("message", pd.Series(dtype=object))])
    df = pd.concat([df.reset_index(drop=True), cls], axis=1)
    if "refusal" in df.columns:
        df["is_api_error"] = (df["refusal"] == "api_error").astype(float)
        df.loc[df.is_api_error == 1, "cooperative"] = np.nan
    else:
        df["is_api_error"] = 0.0

    key = ["cell_id", "seed"]
    m = df.groupby(key, dropna=False).agg(
        arm=("arm", "first"),
        coop=("cooperative", "mean"),
        msgs=("has_msg", "sum"),
        proposal=("proposal", "sum"),
        intention_only=("intention_only", "sum"),
        msg_len=("message_len", "mean"),
        api_err=("is_api_error", "mean"),
    ).reset_index()
    m["lockin"] = (m.coop > LOCKIN_CUT).astype(float)
    m.loc[m.coop.isna(), "lockin"] = np.nan

    out = ["# P1 — the joint-proposal predicate\n",
           f"Run: `{run_dir}`\n",
           "Pre-registered in `paper3/prereg/p1_proposal.md`.\n"]

    # ---------- manipulation check ----------
    out.append("\n## Manipulation check (gates H1)\n")
    out.append("| arm | n | proposal rate/msg | intention-only rate/msg | mean msg chars |")
    out.append("|---|---:|---:|---:|---:|")
    rates = {}
    for a in ARM_ORDER:
        s = m[m.arm == a]
        if not len(s):
            continue
        tot = s.msgs.sum()
        pr = s.proposal.sum() / tot if tot else 0.0
        ir = s.intention_only.sum() / tot if tot else 0.0
        rates[a] = (pr, ir, s.msg_len.mean())
        out.append(f"| {a} | {len(s)} | {pr:.3f} | {ir:.3f} | {s.msg_len.mean():.0f} |")

    ok = True
    notes = []
    if "proposal" in rates:
        pr, ir, _ = rates["proposal"]
        if pr < 0.80 or ir > 0.20:
            ok = False
            notes.append(f"proposal arm FAILED (proposal {pr:.2f}, intention-only {ir:.2f})")
    if "intention" in rates:
        pr, ir, _ = rates["intention"]
        if ir < 0.80 or pr > 0.20:
            ok = False
            notes.append(f"intention arm FAILED (intention-only {ir:.2f}, proposal {pr:.2f})")
    if "proposal" in rates and "intention" in rates:
        lp, li = rates["proposal"][2], rates["intention"][2]
        if lp and li and not (1 / 1.5 <= lp / li <= 1.5):
            ok = False
            notes.append(f"length match FAILED ({lp:.0f} vs {li:.0f} chars)")
    out.append("\n**PASS**" if ok else "\n**FAIL** — " + "; ".join(notes))
    if not ok:
        out.append("\nH1 is not interpreted on a failed arm (pre-registered rule).")

    # ---------- primary outcome ----------
    out.append("\n\n## Primary outcome: lock-in proportion\n")
    out.append("| arm | k/n | lock-in | Wilson 95% CI | mean C | api_error_rate |")
    out.append("|---|---|---:|---|---:|---:|")
    counts = {}
    for a in ARM_ORDER:
        s = m[(m.arm == a) & m.lockin.notna()]
        if not len(s):
            continue
        k, n = int(s.lockin.sum()), len(s)
        counts[a] = (k, n)
        lo, hi = wilson(k, n)
        out.append(f"| {a} | {k}/{n} | {k/n:.3f} | [{lo:.2f}, {hi:.2f}] | "
                   f"{s.coop.mean():.3f} | {s.api_err.mean():.3f} |")

    def contrast(a, b):
        if a not in counts or b not in counts:
            return None
        k1, n1 = counts[a]
        k2, n2 = counts[b]
        _, p = fisher_exact([[k1, n1 - k1], [k2, n2 - k2]])
        rd, lo, hi = newcombe_rd(k1, n1, k2, n2)
        return p, rd, lo, hi

    out.append("\n\n## Pre-registered contrasts\n")
    r = contrast(*PRIMARY)
    if r:
        p, rd, lo, hi = r
        verdict = "SUPPORTED" if (p < 0.05 and rd > 0) else "NOT SUPPORTED"
        out.append(f"**Primary — {PRIMARY[0]} vs {PRIMARY[1]}** (Fisher exact, two-sided, "
                   f"alpha 0.05, uncorrected): p = {p:.2e}, "
                   f"RD {rd:+.3f} [{lo:+.3f}, {hi:+.3f}] -> **H1 {verdict}**\n")

    rows, ps = [], []
    for a, b in SECONDARY:
        rr = contrast(a, b)
        if rr:
            rows.append((a, b) + rr)
            ps.append(rr[0])
    if rows:
        flags = bh(ps)
        out.append("\nSecondary contrasts (Benjamini-Hochberg FDR 0.05):\n")
        out.append("| contrast | p | RD | 95% CI | survives FDR |")
        out.append("|---|---:|---:|---|:--:|")
        for (a, b, p, rd, lo, hi), f in zip(rows, flags):
            out.append(f"| {a} vs {b} | {p:.2e} | {rd:+.3f} | [{lo:+.3f}, {hi:+.3f}] | "
                       f"{'yes' if f else 'no'} |")

    out.append("\n\n## Interpretation guide (pre-registered)\n")
    out.append("- `proposal` >> `intention` and `proposal` ~ `free`: the coordinating "
               "predicate is the joint proposal, not open-ended content or bandwidth.\n"
               "- `proposal` ~ `intention` (both low): the predicate is wrong; the effect "
               "requires open-ended content, supporting the original reading.\n"
               "- A non-significant `proposal` vs `free` contrast is reported as "
               "under-powered, NOT as equivalence.")

    m.to_csv(OUT / "p1_matches.csv", index=False)
    txt = "\n".join(out)
    (OUT / "p1_results.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
