"""The load-bearing test: does contingent-punishment content mediate the channel effect?

Three analyses, in increasing strictness:

1. DESCRIPTIVE      outcome by channel x rule-presence.
2. WITHIN-CHANNEL   among free-text matches only, rule vs no-rule, with the rival
                    mediator (message length) entered alongside. This is the test that
                    discriminates the expressiveness theory from a bandwidth theory:
                    bandwidth predicts length carries the effect, expressiveness predicts
                    rule content does.
3. TEMPORAL         rules observed in the OPENING rounds predicting cooperation in the
                    CLOSING half of the match. Observational mediation is vulnerable to
                    reverse causation (agents may threaten *because* things went badly);
                    ordering the mediator before the outcome blunts that.

Outcomes: lock-in (binary, IPD-family) and K (continuous, Bertrand).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from conditional import score_series  # noqa: E402
from build_match_table import load, BENCHMARKS, LOCKIN_CUT  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
RNG = np.random.default_rng(20260724)
NBOOT = 5000

FREE = ["L2_observed", "L3_private"]


# --- helpers ------------------------------------------------------------------

def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z**2 / n
    c = p + z**2 / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((c - h) / d, (c + h) / d)


def boot_diff(a: np.ndarray, b: np.ndarray, nboot: int = NBOOT) -> tuple[float, float, float]:
    """Bootstrap CI for mean(a) - mean(b)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    a, b = a[~np.isnan(a)], b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return (np.nan, np.nan, np.nan)
    obs = a.mean() - b.mean()
    d = np.empty(nboot)
    for i in range(nboot):
        d[i] = RNG.choice(a, len(a), replace=True).mean() - RNG.choice(b, len(b), replace=True).mean()
    return obs, float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))


def logit_fit(X: np.ndarray, y: np.ndarray, iters: int = 200) -> np.ndarray:
    """Newton-IRLS logistic regression with a small ridge for separation safety."""
    X = np.asarray(X, float)
    y = np.asarray(y, float)
    beta = np.zeros(X.shape[1])
    ridge = 1e-4
    for _ in range(iters):
        eta = np.clip(X @ beta, -30, 30)
        p = 1 / (1 + np.exp(-eta))
        W = np.clip(p * (1 - p), 1e-8, None)
        z = eta + (y - p) / W
        A = X.T @ (X * W[:, None]) + ridge * np.eye(X.shape[1])
        new = np.linalg.solve(A, X.T @ (W * z))
        if np.max(np.abs(new - beta)) < 1e-9:
            beta = new
            break
        beta = new
    return beta


def ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(np.asarray(X, float), np.asarray(y, float), rcond=None)[0]


def zscore(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    s = v.std()
    return (v - v.mean()) / s if s > 0 else v - v.mean()


# --- round-level mediator with temporal ordering -------------------------------

def build_round_level() -> pd.DataFrame:
    df = load()
    scores = score_series(df["message"])
    df = pd.concat([df.reset_index(drop=True), scores.reset_index(drop=True)], axis=1)

    key = ["experiment_id", "cell_id", "seed"]
    rows = []
    for k, g in df.groupby(key, dropna=False):
        n_rounds = int(g["round_index"].max()) + 1
        if n_rounds < 6:
            continue  # need an opening and a closing half
        open_cut = min(3, n_rounds // 3)
        opening = g[g["round_index"] < open_cut]
        closing = g[g["round_index"] >= n_rounds / 2]
        spec = g["spec"].iloc[0]
        game = g["game"].iloc[0]
        price_late = closing["price"].mean()
        K_late = np.nan
        if game == "bertrand" and spec in BENCHMARKS and not np.isnan(price_late):
            b = BENCHMARKS[spec]
            K_late = (price_late - b["p_comp"]) / (b["p_mono"] - b["p_comp"])
        rows.append(dict(
            experiment_id=k[0], cell_id=k[1], seed=k[2],
            game=game, channel=g["channel"].iloc[0], spec=spec,
            pair=g["pair"].iloc[0], n_rounds=n_rounds,
            open_rule=int(opening["rule"].max()) if len(opening) else 0,
            open_msg_len=opening["message_len"].mean(),
            open_coop=opening["cooperative"].mean(),
            late_coop=closing["cooperative"].mean(),
            late_lockin=float(closing["cooperative"].mean() > LOCKIN_CUT)
            if closing["cooperative"].notna().any() else np.nan,
            late_K=K_late,
        ))
    return pd.DataFrame(rows)


# --- analyses -----------------------------------------------------------------

def descriptive(m: pd.DataFrame, out: list[str]) -> None:
    out.append("## 1. Descriptive: outcome by channel x rule presence\n")
    for game, ycol, label in [("ipd", "lockin", "lock-in"), ("bertrand", "K", "K")]:
        g = m[m.game == game]
        out.append(f"\n### {game} ({label})\n")
        out.append("| channel | rule present | n | mean | Wilson/bootstrap 95% CI |")
        out.append("|---|---|---:|---:|---|")
        for ch in ["L0_none", "L1_signal", "L2_observed", "L3_private"]:
            sub = g[g.channel == ch]
            if not len(sub):
                continue
            groups = [(0, sub[sub.any_rule == 0]), (1, sub[sub.any_rule == 1])]
            if ch in ("L0_none", "L1_signal"):
                groups = [("n/a", sub)]
            for tag, s in groups:
                y = s[ycol].dropna()
                if not len(y):
                    continue
                if ycol == "lockin":
                    k, n = int(y.sum()), len(y)
                    lo, hi = wilson(k, n)
                    out.append(f"| {ch} | {tag} | {n} | {y.mean():.3f} | [{lo:.2f}, {hi:.2f}] |")
                else:
                    bs = [RNG.choice(y.values, len(y), replace=True).mean() for _ in range(2000)]
                    out.append(f"| {ch} | {tag} | {len(y)} | {y.mean():.3f} | "
                               f"[{np.percentile(bs,2.5):.2f}, {np.percentile(bs,97.5):.2f}] |")


def within_channel(m: pd.DataFrame, out: list[str]) -> None:
    out.append("\n\n## 2. Within free-text: rule content vs message length as rival mediators\n")
    out.append("Restricted to L2/L3 matches, so the channel affordance is held constant. "
               "A bandwidth account predicts message length carries the effect; the "
               "expressiveness account predicts rule content does.\n")
    for game, ycol, label in [("ipd", "lockin", "lock-in"), ("bertrand", "K", "K")]:
        g = m[(m.game == game) & (m.channel.isin(FREE))].copy()
        g = g[g[ycol].notna() & g.msg_len.notna()]
        if len(g) < 20:
            continue
        yes = g[g.any_rule == 1][ycol].values
        no = g[g.any_rule == 0][ycol].values
        obs, lo, hi = boot_diff(yes, no)
        out.append(f"\n### {game} ({label}), n={len(g)} free-text matches\n")
        out.append(f"- rule present n={len(yes)}, mean {yes.mean():.3f}; "
                   f"absent n={len(no)}, mean {no.mean():.3f}")
        out.append(f"- **difference {obs:+.3f}, bootstrap 95% CI [{lo:+.3f}, {hi:+.3f}]**")

        # head-to-head regression: rule vs length (both standardised), + private-channel
        # and demand-spec controls
        X = np.column_stack([
            np.ones(len(g)),
            g.any_rule.values.astype(float),
            zscore(g.msg_len.values),
            (g.channel == "L3_private").values.astype(float),
            (g.spec == "novel").values.astype(float),
        ])
        names = ["intercept", "rule(any)", "msg_len(z)", "private", "novel_spec"]
        y = g[ycol].values.astype(float)
        if ycol == "lockin":
            beta = logit_fit(X, y)
            # bootstrap CIs
            B = np.empty((NBOOT // 5, X.shape[1]))
            for i in range(len(B)):
                idx = RNG.integers(0, len(g), len(g))
                B[i] = logit_fit(X[idx], y[idx])
            out.append("\n| term | logit coef | 95% CI |")
        else:
            beta = ols(X, y)
            B = np.empty((NBOOT // 5, X.shape[1]))
            for i in range(len(B)):
                idx = RNG.integers(0, len(g), len(g))
                B[i] = ols(X[idx], y[idx])
            out.append("\n| term | OLS coef | 95% CI |")
        out.append("|---|---:|---|")
        for j, nm in enumerate(names):
            lo_, hi_ = np.percentile(B[:, j], [2.5, 97.5])
            star = " **" if (lo_ > 0 or hi_ < 0) else ""
            out.append(f"| {nm}{star} | {beta[j]:+.3f} | [{lo_:+.3f}, {hi_:+.3f}] |")


def mediation_effect(m: pd.DataFrame, out: list[str]) -> None:
    out.append("\n\n## 3. Formal mediation: channel -> rule content -> outcome\n")
    out.append("Total effect = free-text vs no-channel. Indirect = through rule presence "
               "(product of coefficients, nonparametric bootstrap).\n")
    for game, ycol, label in [("ipd", "lockin", "lock-in"), ("bertrand", "K", "K")]:
        g = m[(m.game == game) & (m.channel.isin(FREE + ["L0_none"]))].copy()
        g = g[g[ycol].notna()]
        if len(g) < 30:
            continue
        g["X"] = (g.channel != "L0_none").astype(float)
        g["M"] = g.any_rule.astype(float)

        def paths(d: pd.DataFrame):
            a = d.groupby("X").M.mean()
            a_path = a.get(1.0, 0.0) - a.get(0.0, 0.0)
            Xd = np.column_stack([np.ones(len(d)), d.X.values, d.M.values])
            yv = d[ycol].values.astype(float)
            b = ols(Xd, yv)  # linear probability / linear model for decomposability
            total = ols(np.column_stack([np.ones(len(d)), d.X.values]), yv)[1]
            return a_path, b[2], b[1], total

        a_p, b_p, direct, total = paths(g)
        ind = a_p * b_p
        Bs = np.empty((NBOOT // 5, 4))
        for i in range(len(Bs)):
            d = g.sample(len(g), replace=True, random_state=int(RNG.integers(1e9)))
            ap, bp, dr, tt = paths(d)
            Bs[i] = [ap, bp, ap * bp, dr]
        lo_i, hi_i = np.percentile(Bs[:, 2], [2.5, 97.5])
        lo_d, hi_d = np.percentile(Bs[:, 3], [2.5, 97.5])
        prop = ind / total if total else np.nan
        out.append(f"\n### {game} ({label}), n={len(g)}\n")
        out.append(f"- a-path (channel -> P(rule)): {a_p:+.3f}")
        out.append(f"- b-path (rule -> outcome | channel): {b_p:+.3f}")
        out.append(f"- **total effect {total:+.3f}**")
        out.append(f"- **indirect (mediated) {ind:+.3f}, 95% CI [{lo_i:+.3f}, {hi_i:+.3f}]**")
        out.append(f"- direct (unmediated) {direct:+.3f}, 95% CI [{lo_d:+.3f}, {hi_d:+.3f}]")
        out.append(f"- proportion mediated: {prop:.1%}")


def temporal(r: pd.DataFrame, out: list[str]) -> None:
    out.append("\n\n## 4. Temporal ordering: opening-round rules -> closing-half outcome\n")
    out.append("Mediator measured strictly before the outcome window, so a rule cannot be "
               "a *response* to the outcome it predicts.\n")
    for game, ycol, label in [("ipd", "late_lockin", "closing lock-in"),
                              ("ipd", "late_coop", "closing cooperation"),
                              ("bertrand", "late_K", "closing K")]:
        g = r[(r.game == game) & (r.channel.isin(FREE))].copy()
        g = g[g[ycol].notna() & g.open_msg_len.notna()]
        if len(g) < 20:
            continue
        yes = g[g.open_rule == 1][ycol].values
        no = g[g.open_rule == 0][ycol].values
        if len(yes) < 5 or len(no) < 5:
            out.append(f"\n### {game} ({label}) — insufficient cells "
                       f"(rule n={len(yes)}, no-rule n={len(no)})")
            continue
        obs, lo, hi = boot_diff(yes, no)
        out.append(f"\n### {game} ({label}), n={len(g)}\n")
        out.append(f"- opening rule n={len(yes)}, mean {yes.mean():.3f}; "
                   f"no opening rule n={len(no)}, mean {no.mean():.3f}")
        out.append(f"- **difference {obs:+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}]**")
        # control for opening behaviour (where defined) and opening message length
        cols = [np.ones(len(g)), g.open_rule.values.astype(float)]
        names = ["intercept", "opening rule"]
        if g.open_coop.notna().any():
            oc = g.open_coop.values.astype(float)
            oc = np.nan_to_num(oc, nan=float(np.nanmean(oc)))
            if oc.std() > 0:
                cols.append(zscore(oc))
                names.append("opening coop(z)")
        cols.append(zscore(g.open_msg_len.values))
        names.append("opening msg_len(z)")
        X = np.column_stack(cols)
        y = g[ycol].values.astype(float)
        beta = ols(X, y)
        B = np.empty((1000, X.shape[1]))
        for i in range(1000):
            idx = RNG.integers(0, len(g), len(g))
            B[i] = ols(X[idx], y[idx])
        out.append("\n| term | coef | 95% CI |")
        out.append("|---|---:|---|")
        for j, nm in enumerate(names):
            lo_, hi_ = np.percentile(B[:, j], [2.5, 97.5])
            star = " **" if (lo_ > 0 or hi_ < 0) else ""
            out.append(f"| {nm}{star} | {beta[j]:+.3f} | [{lo_:+.3f}, {hi_:+.3f}] |")


def main() -> None:
    m = pd.read_csv(OUT / "matches.csv")
    r = build_round_level()
    r.to_csv(OUT / "matches_temporal.csv", index=False)

    out: list[str] = ["# Mediation analysis — does contingent-punishment content carry "
                      "the channel effect?\n",
                      f"Source: `results/master_long.csv`; {len(m)} LLM-vs-LLM matches "
                      f"(smoke pairs and classical opponents excluded).\n",
                      "Detector: `paper3/src/conditional.py` (regex, deterministic).\n"]
    descriptive(m, out)
    within_channel(m, out)
    mediation_effect(m, out)
    temporal(r, out)

    txt = "\n".join(out)
    (OUT / "mediation.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
