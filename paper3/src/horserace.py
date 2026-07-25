"""Mediator horse-race under a temporal design.

The naive mediation reversed sign because contingent-punishment rules are uttered
*after* trouble starts (78.6% of the time; hazard 0.173 vs 0.043). So we measure every
candidate mediator in the OPENING rounds only, and predict cooperation in the CLOSING
half, controlling for how the opening actually went. A mediator measured before the
outcome window cannot be a response to it.

Candidate content classes:
  threat        contingent punishment rule ("hold, or I undercut")   <- folk-theorem
  agreement     explicit joint plan ("let's both set 13.00")
  affirmation   appeal to shared history / trust / continuation
  solicitation  asking the peer to confirm or commit ("do you agree?")
  length        raw message length (the bandwidth account)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from conditional import score_series  # noqa: E402
from build_match_table import load, BENCHMARKS  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260724)
FREE = ["L2_observed", "L3_private"]
NB = 4000

LEX = {
    "agreement": [
        r"\blet'?s (?:both|all)\b", r"\bwe should both\b",
        r"\bboth (?:set|post|price|play|choose|hold|charge)\b",
        r"\blet'?s (?:agree|settle|stabili[sz]e|commit|stick)\b",
        r"\bagree(?:d)? (?:on|to)\b", r"\bstabili[sz]e at\b", r"\bcommit to\b",
        r"\bmutual(?:ly)? (?:benefit|agree|profit)\b", r"\bwe (?:can|could|will) both\b",
    ],
    "affirmation": [
        r"\b(?:our|the) cooperation\b", r"\bworking well\b", r"\bhas been\b",
        r"\btrust\b", r"\bconsisten", r"\bkeep (?:it |this )?(?:up|going)\b",
        r"\bcontinue\b", r"\bso far\b", r"\bproven\b", r"\bsuccess",
        r"\bmutual benefit\b", r"\bboth of us have\b", r"\bstable\b", r"\bmaintain\b",
    ],
    "solicitation": [
        r"\?\s*$", r"\bdo you agree\b", r"\bwhat do you think\b", r"\bare you (?:in|with)\b",
        r"\bwill you\b", r"\bcan (?:i|we) (?:count|rely)\b", r"\bconfirm\b",
        r"\bhow about\b", r"\bready\b", r"\bdeal\?",
    ],
}
RE = {k: re.compile("|".join(v), re.I) for k, v in LEX.items()}


def boot_ols(X, y, nb=1500):
    X = np.asarray(X, float); y = np.asarray(y, float)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    B = np.empty((nb, X.shape[1]))
    for i in range(nb):
        idx = RNG.integers(0, len(y), len(y))
        B[i] = np.linalg.lstsq(X[idx], y[idx], rcond=None)[0]
    return beta, np.percentile(B, [2.5, 97.5], axis=0)


def z(v):
    v = np.asarray(v, float)
    s = v.std()
    return (v - v.mean()) / s if s > 0 else v - v.mean()


def build() -> pd.DataFrame:
    df = load()
    sc = score_series(df["message"])
    df = pd.concat([df.reset_index(drop=True), sc.reset_index(drop=True)], axis=1)
    df = df.rename(columns={"rule": "threat"})
    for name, rgx in RE.items():
        df[name] = df["message"].map(
            lambda t, r=rgx: int(bool(r.search(t))) if isinstance(t, str) else 0)

    key = ["experiment_id", "cell_id", "seed"]
    rows = []
    for k, g in df[df.channel.isin(FREE)].groupby(key, dropna=False):
        g = g.sort_values("round_index")
        n = int(g.round_index.max()) + 1
        if n < 6:
            continue
        cut = min(3, n // 3)
        op = g[g.round_index < cut]
        cl = g[g.round_index >= n / 2]
        if op.empty or cl.empty:
            continue
        spec, game = g.spec.iloc[0], g.game.iloc[0]
        K = np.nan
        if game == "bertrand" and spec in BENCHMARKS:
            pm = cl.price.mean()
            if not np.isnan(pm):
                b = BENCHMARKS[spec]
                K = (pm - b["p_comp"]) / (b["p_mono"] - b["p_comp"])
        rows.append(dict(
            game=game, channel=g.channel.iloc[0], spec=spec, pair=g.pair.iloc[0],
            open_threat=int(op.threat.max()), open_agreement=int(op.agreement.max()),
            open_affirm=int(op.affirmation.max()), open_solicit=int(op.solicitation.max()),
            open_len=op.message_len.mean(),
            open_coop=op.cooperative.mean(), open_price=op.price.mean(),
            late_coop=cl.cooperative.mean(), late_K=K,
        ))
    return pd.DataFrame(rows)


def run(d: pd.DataFrame, ycol: str, label: str, out: list[str], control_open: str) -> None:
    d = d[d[ycol].notna() & d.open_len.notna()].copy()
    if len(d) < 40:
        out.append(f"\n### {label}: insufficient data (n={len(d)})")
        return
    terms = ["open_threat", "open_agreement", "open_affirm", "open_solicit"]
    cols = [np.ones(len(d))]
    names = ["intercept"]
    for t in terms:
        if d[t].std() > 0:
            cols.append(d[t].values.astype(float)); names.append(t)
    cols.append(z(d.open_len.values)); names.append("open_len(z)")
    if d[control_open].notna().any() and np.nanstd(d[control_open].values) > 0:
        c = d[control_open].values.astype(float)
        c = np.nan_to_num(c, nan=float(np.nanmean(c)))
        cols.append(z(c)); names.append(f"{control_open}(z)")
    cols.append((d.channel == "L3_private").values.astype(float)); names.append("private")
    if d.spec.nunique() > 1:
        cols.append((d.spec == "novel").values.astype(float)); names.append("novel_spec")

    beta, ci = boot_ols(np.column_stack(cols), d[ycol].values)
    out.append(f"\n### {label} — n={len(d)} free-text matches\n")
    out.append("| term | coef | 95% CI | base rate |")
    out.append("|---|---:|---|---:|")
    for j, nm in enumerate(names):
        lo, hi = ci[0, j], ci[1, j]
        star = " **" if (lo > 0 or hi < 0) else ""
        br = f"{d[nm].mean():.2f}" if nm in d.columns and set(d[nm].dropna().unique()) <= {0, 1} else ""
        out.append(f"| {nm}{star} | {beta[j]:+.3f} | [{lo:+.3f}, {hi:+.3f}] | {br} |")


def main() -> None:
    d = build()
    d.to_csv(OUT / "horserace_matches.csv", index=False)
    out = ["# Mediator horse-race (temporal design)\n",
           "Content classes measured in the OPENING rounds; outcome is the CLOSING half. "
           "Controls: how the opening actually went, private channel, demand spec.\n",
           f"Free-text matches with >=6 rounds: {len(d)}\n"]

    out.append("\n## Base rates of each content class in opening rounds\n")
    out.append("| class | IPD | Bertrand |")
    out.append("|---|---:|---:|")
    for t in ["open_threat", "open_agreement", "open_affirm", "open_solicit"]:
        i = d[d.game == "ipd"][t].mean()
        b = d[d.game == "bertrand"][t].mean()
        out.append(f"| {t} | {i:.3f} | {b:.3f} |")

    out.append("\n\n## IPD — closing-half cooperation")
    run(d[d.game == "ipd"], "late_coop", "IPD closing cooperation", out, "open_coop")
    out.append("\n\n## Bertrand — closing-half K")
    run(d[d.game == "bertrand"], "late_K", "Bertrand closing K", out, "open_price")

    txt = "\n".join(out)
    (OUT / "horserace.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
