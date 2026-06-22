#!/usr/bin/env python3
"""Confirmatory + exploratory analysis for the wide program.

Reads the LATEST finalized run dir per experiment (data/runs/<EXP>/<ts>/metrics.csv)
and prints the labeled numbers that go into docs/findings.md:

  A1  (confirmatory, same_origin_cn, offset 100): lock-in ladder L0->L3 x {canonical,
       novel} + Wilson CIs; promise-keeping; refusals; the L1-collapse check.
  B1  (confirmatory, cross_origin, offset 100): collusion K ladder x {canonical,
       novel-demand} + supracompetitive proportion.
  B1o (exploratory, same_origin):  same, for the same- vs cross-origin contrast.
  A3  (H4 origin moderation): per-pair lock-in ladder; same- vs cross-origin channel
       slope; TOST equivalence + factorial partial-eta^2.  Wording locked (a3.md).
  A4  (exploratory): temptation dose-response slope per pair (who breaks first).
  A2  (exploratory): repeated vs one-shot collapse; zero-sum on a separate axis.

Run: .venv/bin/python scripts/analyze_findings.py
"""
from __future__ import annotations

import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from rival_arena.metrics.stats import (  # noqa: E402
    wilson_interval, bootstrap_ci, tost_equivalence, power_for_proportions,
    factorial_anova,
)

DATA = ROOT / "data"
CH_ORDER = ["L0_none", "L1_signal", "L2_observed", "L3_private"]
SAME_ORIGIN = {"same_family", "same_origin_cn", "same_origin_west"}
CROSS_ORIGIN = {"cross_origin", "cross_origin_2"}


def latest_metrics(exp: str) -> pd.DataFrame | None:
    """metrics.csv from the most-recently-modified finalized run dir for <exp>."""
    dirs = sorted(
        glob.glob(str(DATA / "runs" / exp / "*")),
        key=lambda p: Path(p).stat().st_mtime if Path(p).exists() else 0,
    )
    for d in reversed(dirs):
        f = Path(d) / "metrics.csv"
        if f.exists():
            df = pd.read_csv(f)
            df["__run"] = d
            return df
    return None


def ch_key(c: str) -> int:
    return CH_ORDER.index(c) if c in CH_ORDER else 99


def lockin_row(g: pd.DataFrame) -> tuple[int, int, float | None, float, float]:
    """k locked, n (coop-axis-defined), proportion, wilson lo/hi for a cell."""
    defined = g[g["coop_axis_defined"] == 1]
    n = len(defined)
    k = int((defined["locked_in"] == 1).sum())
    prop = (k / n) if n else None
    lo, hi = wilson_interval(k, n)
    return k, n, prop, lo, hi


def hdr(t: str) -> None:
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


# --------------------------------------------------------------------------- #
def analyze_a1() -> None:
    df = latest_metrics("A1")
    hdr("A1 — channel effect (CONFIRMATORY: same_origin_cn, seed-offset 100) [H1]")
    if df is None:
        print("  no A1 run found"); return
    print(f"  run: {df['__run'].iloc[0]}   n_matches={len(df)}")
    for fam in sorted(df["familiarity"].unique()):
        sub = df[df["familiarity"] == fam]
        print(f"\n  familiarity = {fam}")
        print(f"  {'rung':<13}{'lock-in':>10}{'  Wilson 95% CI':>20}"
              f"{'meanC':>8}{'promise':>9}{'refuse':>8}")
        for ch in sorted(sub["channel"].unique(), key=ch_key):
            g = sub[sub["channel"] == ch]
            k, n, prop, lo, hi = lockin_row(g)
            mc = g["coop_endstate"].mean()
            pk = g["promise_keeping_rate"].mean()
            rf = g["refusal_rate"].mean()
            ps = f"{prop:.2f}" if prop is not None else "  na"
            print(f"  {ch:<13}{k:>3}/{n:<3} {ps:>3}"
                  f"   [{lo:.2f},{hi:.2f}]   {mc:>6.2f}{pk:>9.2f}{rf:>8.2f}")


def analyze_b1(exp: str, label: str, pair: str | None = None) -> None:
    # B1 and B1o share experiment_id "B1" -> both land in the B1 run dir; split on the
    # pair segment of the cell_id (B1/<rung>/<demand>/<pair>).
    df = latest_metrics("B1")
    hdr(f"{exp} — autonomous collusion ({label}) [H3]")
    if df is None:
        print(f"  no B1 run found"); return
    if pair is not None:
        df = df[df["cell_id"].str.endswith(pair)].copy()
        if df.empty:
            print(f"  no rows for pair={pair}"); return
    print(f"  run: {df['__run'].iloc[0]}   pair={pair}   n_matches={len(df)}")
    # B1 encodes the demand spec in the cell_id (B1/<rung>/<demand>/<pair>), NOT in
    # the familiarity column (which stays 'canonical'); split on it — the novel-demand
    # arm is the anti-memorization floor (P3).
    df = df.copy()
    df["demand"] = df["cell_id"].map(
        lambda c: c.split("/")[2] if len(c.split("/")) > 3 else c.split("/")[-1])
    for fam in sorted(df["demand"].unique()):
        sub = df[df["demand"] == fam]
        print(f"\n  demand = {fam}")
        print(f"  {'rung':<13}{'meanK':>8}{'  K bootstrap CI':>20}"
              f"{'K>0 prop':>10}{'refuse':>8}{'n':>5}")
        for ch in sorted(sub["channel"].unique(), key=ch_key):
            g = sub[sub["channel"] == ch]
            kv = g["K_endstate"].dropna().tolist()
            n = len(kv)
            mk = float(np.mean(kv)) if kv else float("nan")
            lo, hi = bootstrap_ci(kv) if kv else (None, None)
            supra = sum(1 for x in kv if x > 0)
            sp = supra / n if n else float("nan")
            slo, shi = wilson_interval(supra, n)
            rf = g["refusal_rate"].mean()
            cis = f"[{lo:.2f},{hi:.2f}]" if lo is not None else "  na"
            print(f"  {ch:<13}{mk:>8.2f}{cis:>20}"
                  f"   {sp:.2f} [{slo:.2f},{shi:.2f}]{rf:>8.2f}{n:>5}")


def _pair_of(cell_id: str) -> str:
    return cell_id.split("/")[-1]


def analyze_a3() -> None:
    df = latest_metrics("A3")
    hdr("A3 — origin moderation of the channel effect [H4]  (a3.md wording LOCKED)")
    if df is None:
        print("  no A3 run found"); return
    print(f"  run: {df['__run'].iloc[0]}   n_matches={len(df)}")
    df = df.copy()
    df["pair"] = df["cell_id"].map(_pair_of)
    df["origin_type"] = df["pair"].map(
        lambda p: "same" if p in SAME_ORIGIN else ("cross" if p in CROSS_ORIGIN else "other"))

    # per-pair lock-in ladder + L0->L3 channel slope
    print("\n  per-pair lock-in ladder (proportion):")
    print(f"  {'pair':<18}{'origin':<7}" + "".join(f"{c.split('_')[0]:>8}" for c in CH_ORDER)
          + f"{'L0->L3':>9}")
    pair_slopes = {}
    for pair in sorted(df["pair"].unique()):
        g = df[df["pair"] == pair]
        ot = g["origin_type"].iloc[0]
        props = {}
        for ch in CH_ORDER:
            cg = g[g["channel"] == ch]
            _, n, prop, _, _ = lockin_row(cg)
            props[ch] = prop
        slope = (props.get("L3_private") or 0) - (props.get("L0_none") or 0)
        pair_slopes[pair] = (ot, slope)
        cells = "".join(f"{(props[c] if props[c] is not None else float('nan')):>8.2f}"
                        for c in CH_ORDER)
        print(f"  {pair:<18}{ot:<7}{cells}{slope:>9.2f}")

    # TOST: per-(pair,seed) coop_endstate slope L3-L0, grouped same vs cross
    def seed_slopes(origin: str) -> list[float]:
        out = []
        sub = df[df["origin_type"] == origin]
        for pair in sub["pair"].unique():
            pg = sub[sub["pair"] == pair]
            for seed in pg["seed"].unique():
                sg = pg[pg["seed"] == seed]
                l0 = sg[sg["channel"] == "L0_none"]["coop_endstate"]
                l3 = sg[sg["channel"] == "L3_private"]["coop_endstate"]
                if len(l0) and len(l3):
                    out.append(float(l3.mean() - l0.mean()))
        return out

    same_s, cross_s = seed_slopes("same"), seed_slopes("cross")
    BOUND = 0.20  # equivalence bound on the channel-slope difference (coop scale 0-1)
    tost = tost_equivalence(same_s, cross_s, bound=BOUND)
    print(f"\n  channel-slope (coop L3-L0), per seed:")
    print(f"    same-origin  : mean={np.mean(same_s):.3f}  n={len(same_s)}")
    print(f"    cross-origin : mean={np.mean(cross_s):.3f}  n={len(cross_s)}")
    print(f"  TOST equivalence (bound +/-{BOUND} on coop scale):")
    print(f"    mean_diff={tost['mean_diff']:.3f}  p={tost['p']:.4f}  "
          f"equivalent={tost['equivalent']}  (p_lower={tost['p_lower']:.3f}, "
          f"p_upper={tost['p_upper']:.3f})")

    # factorial partial-eta^2: channel vs origin_type on coop_endstate
    try:
        fdf = df[df["origin_type"].isin(["same", "cross"]) & (df["coop_axis_defined"] == 1)]
        tbl = factorial_anova(fdf, "coop_endstate", ["channel", "origin_type"])
        print("\n  partial eta^2 (coop_endstate ~ channel + origin_type):")
        for idx in tbl.index:
            if idx == "Residual":
                continue
            print(f"    {idx:<18} partial_eta_sq={tbl.loc[idx, 'partial_eta_sq']:.4f}  "
                  f"p={tbl.loc[idx, 'PR(>F)']:.4g}")
    except Exception as e:
        print(f"  [anova skipped: {e}]")

    # power: smallest lock-in proportion gap detectable at the per-pair n
    n_per = int(df.groupby(["pair", "channel"]).size().median())
    for gap in (0.3, 0.4, 0.5):
        need = power_for_proportions(0.2, 0.2 + gap)
        print(f"    power: detecting a {gap:.1f} lock-in gap needs ~{need}/cell "
              f"(have ~{n_per}/cell)")


def analyze_a4() -> None:
    df = latest_metrics("A4")
    hdr("A4 — temptation dose-response (EXPLORATORY): who breaks first")
    if df is None:
        print("  no A4 run found"); return
    print(f"  run: {df['__run'].iloc[0]}   n_matches={len(df)}")
    df = df.copy()

    def temptation(cid: str) -> float:
        for seg in cid.split("/"):
            if seg.startswith("temptation_"):
                return float(seg.split("_")[1])
        return float("nan")

    df["temptation"] = df["cell_id"].map(temptation)
    df["pair"] = df["cell_id"].map(_pair_of)
    for pair in sorted(df["pair"].unique()):
        g = df[df["pair"] == pair]
        pts = g.groupby("temptation")["coop_endstate"].mean().sort_index()
        if len(pts) >= 2:
            slope = float(np.polyfit(pts.index.values, pts.values, 1)[0])
        else:
            slope = float("nan")
        curve = "  ".join(f"{t:g}:{v:.2f}" for t, v in pts.items())
        print(f"  {pair:<16} slope={slope:+.3f}   {curve}")


def analyze_a2() -> None:
    df = latest_metrics("A2")
    hdr("A2 — regime contrast (EXPLORATORY): repeated vs one-shot; zero-sum separate")
    if df is None:
        print("  no A2 run found"); return
    print(f"  run: {df['__run'].iloc[0]}   n_matches={len(df)}")
    df = df.copy()
    df["regime"] = df["cell_id"].map(lambda c: c.split("/")[1] if "/" in c else c)
    for reg in sorted(df["regime"].unique()):
        g = df[df["regime"] == reg]
        defined = g[g["coop_axis_defined"] == 1]
        if len(defined):
            k, n, prop, lo, hi = lockin_row(g)
            mc = defined["coop_endstate"].mean()
            print(f"  {reg:<22} lock-in={k}/{n} ({(prop or 0):.2f}) "
                  f"[{lo:.2f},{hi:.2f}]  meanC={mc:.2f}")
        else:
            # zero-sum / undefined coop axis — separate panel
            mk = g["K_endstate"].dropna().mean() if "K_endstate" in g else float("nan")
            print(f"  {reg:<22} [coop axis undefined: zero-sum control]  "
                  f"meanK={mk:.2f}  n={len(g)}")


if __name__ == "__main__":
    analyze_a1()
    analyze_b1("B1", "CONFIRMATORY: cross_origin, seed-offset 100", pair="cross_origin")
    analyze_b1("B1o", "EXPLORATORY: same_origin_cn", pair="same_origin_cn")
    analyze_a3()
    analyze_a4()
    analyze_a2()
    print("\n" + "=" * 78)
