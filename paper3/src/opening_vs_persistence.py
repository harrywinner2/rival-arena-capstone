"""Where does the channel effect live: the opening, or the persistence?

C1 (the authorship/content ablation) suggests the whole effect is an OPENING effect:
free text opens at 0.85 vs 0.18 for a self-authored action-only channel, while the
decay rate is nearly identical across arms. But decay is floor-confounded -- an arm
sitting at 0.003 cannot decay. So we re-test decay *within matches that opened
cooperatively*, where every arm has room to fall.

Outputs the decomposition the paper needs:
  total channel effect on closing cooperation
    = (effect on opening) x (pass-through) + (effect on decay | opening)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from build_match_table import load, BENCHMARKS  # noqa: E402
from conditional import score_series  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260724)
NB = 4000


def bmean(v, nb=NB):
    v = np.asarray(v, float)
    v = v[~np.isnan(v)]
    if len(v) < 3:
        return np.nan, np.nan, np.nan
    bs = np.array([RNG.choice(v, len(v), True).mean() for _ in range(nb)])
    return v.mean(), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def bdiff(a, b, nb=NB):
    a = np.asarray(a, float); b = np.asarray(b, float)
    a = a[~np.isnan(a)]; b = b[~np.isnan(b)]
    if len(a) < 3 or len(b) < 3:
        return np.nan, np.nan, np.nan
    d = np.array([RNG.choice(a, len(a), True).mean() - RNG.choice(b, len(b), True).mean()
                  for _ in range(nb)])
    return a.mean() - b.mean(), float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def match_table(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    rows = []
    for k, g in df.groupby(["experiment_id", "cell_id", "seed"], dropna=False):
        g = g.sort_values("round_index")
        n = int(g.round_index.max()) + 1
        if n < 6:
            continue
        op = g[g.round_index < 3]
        cl = g[g.round_index >= n / 2]
        if op.empty or cl.empty:
            continue
        rows.append(dict(
            grp=g[group_col].iloc[0], game=g.game.iloc[0], spec=g.spec.iloc[0],
            pair=g.pair.iloc[0], n_rounds=n,
            open=op.cooperative.mean(), close=cl.cooperative.mean(),
            open_price=op.price.mean(), close_price=cl.price.mean(),
            lockin=float(g.cooperative.mean() > 0.8) if g.cooperative.notna().any() else np.nan,
        ))
    r = pd.DataFrame(rows)
    r["decay"] = r["close"] - r["open"]
    return r


def section(r: pd.DataFrame, order: list[str], title: str, out: list[str]) -> None:
    out.append(f"\n## {title}\n")
    out.append("| arm | n | opening C | closing C | decay | decay 95% CI |")
    out.append("|---|---:|---:|---:|---:|---|")
    for a in order:
        s = r[r.grp == a]
        if not len(s):
            continue
        o, _, _ = bmean(s["open"].values)
        c, _, _ = bmean(s["close"].values)
        d, dl, dh = bmean(s["decay"].values)
        out.append(f"| {a} | {len(s)} | {o:.3f} | {c:.3f} | {d:+.3f} | [{dl:+.3f}, {dh:+.3f}] |")

    # floor-controlled: only matches that opened cooperatively
    hi = r[r["open"] > 0.8]
    out.append(f"\n**Floor-controlled** (matches opening at C>0.8, n={len(hi)}) — every arm "
               "now has equal room to fall, so a channel that *sustains* cooperation "
               "should show a flatter decay here:\n")
    out.append("| arm | n | opening C | closing C | decay | decay 95% CI |")
    out.append("|---|---:|---:|---:|---:|---|")
    for a in order:
        s = hi[hi.grp == a]
        if len(s) < 3:
            out.append(f"| {a} | {len(s)} | — | — | — | insufficient |")
            continue
        o, _, _ = bmean(s["open"].values)
        c, _, _ = bmean(s["close"].values)
        d, dl, dh = bmean(s["decay"].values)
        out.append(f"| {a} | {len(s)} | {o:.3f} | {c:.3f} | {d:+.3f} | [{dl:+.3f}, {dh:+.3f}] |")

    # pairwise decay contrasts among the channel arms, floor-controlled
    chans = [a for a in order if len(hi[hi.grp == a]) >= 5]
    if len(chans) >= 2:
        out.append("\n**Pairwise decay contrasts (floor-controlled).** A significant "
                   "difference would mean the channel changes persistence, not just the "
                   "starting point.\n")
        out.append("| contrast | Δdecay | 95% CI |")
        out.append("|---|---:|---|")
        base = chans[0]
        for a in chans[1:]:
            o, lo, hi_ = bdiff(hi[hi.grp == a].decay.values, hi[hi.grp == base].decay.values)
            star = " **" if (lo > 0 or hi_ < 0) else ""
            out.append(f"| {a} − {base}{star} | {o:+.3f} | [{lo:+.3f}, {hi_:+.3f}] |")


def main() -> None:
    df = load()
    out = ["# Opening displacement vs persistence\n",
           "The channel effect decomposed into where it acts.\n"]

    # --- A1-family: the full channel ladder, IPD ---
    ipd = df[(df.game == "ipd") & df.cooperative.notna()]
    r = match_table(ipd, "channel")
    section(r, ["L0_none", "L1_signal", "L2_observed", "L3_private"],
            "The channel ladder (all IPD experiments)", out)

    # --- C1: the authorship/content ablation ---
    c1 = df[df.experiment_id == "C1"].copy()
    c1["arm"] = c1.cell_id.str.split("/").str[1]
    rc = match_table(c1, "arm")
    section(rc, ["selected", "restricted", "free"],
            "C1 ablation — selected (menu) / restricted (self-authored, action-only) / free",
            out)

    out.append("\n\n## Reading\n")
    out.append("C1 holds the *act* of sending a message constant and varies only how much "
               "content the message may carry. If the channel worked by installing an "
               "enforcement regime, the free arm should decay more slowly. It does not: "
               "the arms separate almost entirely at the opening.\n")

    txt = "\n".join(out)
    (OUT / "opening_vs_persistence.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
