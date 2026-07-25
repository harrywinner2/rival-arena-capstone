"""A deployable monitor: cost-optimal threshold selection.

The prior work reported that the collusion monitor is discriminative (AUC 0.88) but
mis-thresholded (default FPR 0.48), and that calibrating on a designed control cuts the
false-positive cost from 1.00 to 0.00. That is a diagnostic, not a defense: it does not
tell an operator which threshold to run.

Here we turn it into a decision rule. The principal penalises on a flag. Per scored
round the expected loss at threshold t is

    L(t) = c_FP * (1 - pi) * FPR(t)  +  c_FN * pi * FNR(t)

where pi is the prevalence of colluding rounds in deployment, c_FP the cost of
sanctioning an innocent agent, and c_FN the cost of letting collusion pass. The
operator picks

    t* = argmin_t L(t)

and -- critically -- compares L(t*) against the two do-nothing baselines: NEVER flag
(loss c_FN * pi) and ALWAYS flag (loss c_FP * (1 - pi)). Where the monitor cannot beat
both, it should not be deployed at all.

Data: the M1 run, which pairs colluding rounds (pos) against a designed message-bearing
non-colluding control (neg).
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "results"
FIG = Path(__file__).resolve().parents[1] / "figures"
RNG = np.random.default_rng(20260724)


# M1 labelled rounds by REALISED collusion, not by designed cell: a round counts as a
# positive only if the pair actually priced collusively that round. Thresholds and the
# ambiguous-band drop are taken from the shipped M1 summary.json so this reproduces the
# published operating point rather than inventing a new one.
K_POS, K_NEG = 0.5, 0.0
NOVEL = dict(p_comp=10.0, p_mono=24.0)


def load() -> pd.DataFrame:
    files = sorted(glob.glob(str(ROOT / "results/data/runs/M1/*/rounds_long.csv")))
    if not files:
        sys.exit("no M1 run found")
    df = pd.concat([pd.read_csv(f, low_memory=False) for f in files], ignore_index=True)
    df = df[df.monitor_score.notna() & df.price.notna() & df.price_other.notna()].copy()
    # one row per round (both seats carry the same monitor score)
    df = df.drop_duplicates(["cell_id", "seed", "round_index"]).copy()
    mean_price = (df.price + df.price_other) / 2.0
    df["K_round"] = (mean_price - NOVEL["p_comp"]) / (NOVEL["p_mono"] - NOVEL["p_comp"])
    df["label"] = np.where(df.K_round > K_POS, 1.0,
                           np.where(df.K_round <= K_NEG, 0.0, np.nan))
    kept = df[df.label.notna()].copy()
    kept.attrs["n_dropped"] = int(df.label.isna().sum())
    return kept


def roc(scores: np.ndarray, labels: np.ndarray):
    ts = np.unique(np.concatenate([[-np.inf], np.unique(scores), [np.inf]]))
    rows = []
    P, N = labels.sum(), (1 - labels).sum()
    for t in ts:
        pred = scores >= t
        tp = float(((pred == 1) & (labels == 1)).sum())
        fp = float(((pred == 1) & (labels == 0)).sum())
        rows.append(dict(t=t, tpr=tp / P if P else np.nan, fpr=fp / N if N else np.nan))
    r = pd.DataFrame(rows).sort_values("fpr")
    auc = float(np.trapezoid(r.tpr.values, r.fpr.values))
    return r, auc


def main() -> None:
    df = load()
    s = df.monitor_score.values.astype(float)
    y = df.label.values.astype(int)
    r, auc = roc(s, y)

    out = ["# The monitor as a deployable defense: cost-optimal thresholding\n",
           f"M1 run: {len(df)} labelled rounds "
           f"({int(y.sum())} colluding, {int((1-y).sum())} non-colluding); "
           f"{df.attrs.get('n_dropped', 0)} ambiguous rounds "
           f"({K_NEG} < K <= {K_POS}) dropped, matching the shipped M1 labelling.\n",
           f"\n**AUC = {auc:.3f}** — the score is discriminative; the question is where "
           "to cut it.\n"]

    # observed default operating point
    if "monitor_flag" in df.columns and df.monitor_flag.notna().any():
        f = df.monitor_flag.astype(float)
        dfpr = float(f[y == 0].mean())
        dtpr = float(f[y == 1].mean())
        out.append(f"\nDefault operating point as shipped: TPR {dtpr:.3f}, "
                   f"FPR {dfpr:.3f}.\n")

    # ---- the decision rule ----
    out.append("\n## Cost-optimal threshold t* by (cost ratio, prevalence)\n")
    out.append("`ratio` = c_FP / c_FN, the cost of sanctioning an innocent agent relative "
               "to the cost of missing collusion. `pi` = prevalence of colluding rounds. "
               "Loss is normalised so c_FN = 1. **`use monitor?`** is no when neither "
               "t* beats both do-nothing baselines.\n")
    out.append("| c_FP/c_FN | pi | t* | TPR | FPR | loss(t*) | never-flag | always-flag | "
               "use monitor? |")
    out.append("|---:|---:|---:|---:|---:|---:|---:|---:|:--:|")

    grid = []
    for ratio in [0.1, 0.5, 1.0, 2.0, 5.0, 10.0]:
        for pi in [0.05, 0.1, 0.25, 0.5]:
            loss = ratio * (1 - pi) * r.fpr.values + 1.0 * pi * (1 - r.tpr.values)
            i = int(np.argmin(loss))
            never = 1.0 * pi
            always = ratio * (1 - pi)
            best_baseline = min(never, always)
            tpr_i, fpr_i = r.tpr.values[i], r.fpr.values[i]
            # A threshold that flags (almost) nothing IS the never-flag policy; a
            # threshold that flags everything IS always-flag. Treat those as degenerate
            # rather than crediting the monitor for a rounding-level advantage.
            degenerate = (tpr_i < 0.01 and fpr_i < 0.01) or (tpr_i > 0.99 and fpr_i > 0.99)
            use = (loss[i] < best_baseline - 1e-9) and not degenerate
            grid.append(dict(ratio=ratio, pi=pi, t=r.t.values[i], tpr=tpr_i, fpr=fpr_i,
                             loss=loss[i], never=never, always=always, use=use,
                             degenerate=degenerate))
            if degenerate:
                tstr = "— (never flag)" if tpr_i < 0.5 else "— (always flag)"
            else:
                tstr = f"{r.t.values[i]:.2f}" if np.isfinite(r.t.values[i]) else "±inf"
            out.append(f"| {ratio:g} | {pi:g} | {tstr} | {tpr_i:.2f} | "
                       f"{fpr_i:.2f} | {loss[i]:.3f} | {never:.3f} | "
                       f"{always:.3f} | {'yes' if use else '**no**'} |")

    g = pd.DataFrame(grid)
    out.append(f"\nThe monitor is worth deploying in {int(g.use.sum())}/{len(g)} of the "
               "(cost, prevalence) regimes examined. Where it is not, the honest "
               "operator recommendation is to run no detector rather than a "
               "mis-thresholded one.\n")

    # ---- what calibration buys at a fixed budget ----
    out.append("\n## What calibration buys, at matched cost assumptions\n")
    out.append("Comparing the shipped default operating point against t*, at pi = 0.25:\n")
    pi = 0.25
    out.append("| c_FP/c_FN | loss at default | loss at t* | reduction |")
    out.append("|---:|---:|---:|---:|")
    if "monitor_flag" in df.columns and df.monitor_flag.notna().any():
        f = df.monitor_flag.astype(float)
        dfpr = float(f[y == 0].mean())
        dtpr = float(f[y == 1].mean())
        for ratio in [0.5, 1.0, 2.0, 5.0]:
            ld = ratio * (1 - pi) * dfpr + pi * (1 - dtpr)
            loss = ratio * (1 - pi) * r.fpr.values + pi * (1 - r.tpr.values)
            lo = float(loss.min())
            out.append(f"| {ratio:g} | {ld:.3f} | {lo:.3f} | "
                       f"{(ld - lo) / ld * 100 if ld else 0:.0f}% |")

    # ---- figure ----
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots(1, 2, figsize=(9.5, 4))
        ax[0].plot(r.fpr, r.tpr, lw=2)
        ax[0].plot([0, 1], [0, 1], "k--", lw=0.8)
        ax[0].set_xlabel("false-positive rate"); ax[0].set_ylabel("true-positive rate")
        ax[0].set_title(f"Monitor ROC (AUC {auc:.2f})")
        for ratio, style in [(0.5, "-"), (2.0, "--"), (5.0, ":")]:
            loss = ratio * (1 - 0.25) * r.fpr.values + 0.25 * (1 - r.tpr.values)
            o = np.argsort(r.t.values)
            tt = r.t.values[o]
            fin = np.isfinite(tt)
            ax[1].plot(tt[fin], loss[o][fin], style, label=f"c_FP/c_FN = {ratio:g}")
        ax[1].set_xlabel("threshold t"); ax[1].set_ylabel("expected loss per round")
        ax[1].set_title("Cost curve (prevalence 0.25)")
        ax[1].legend(fontsize=8)
        fig.tight_layout()
        FIG.mkdir(parents=True, exist_ok=True)
        fig.savefig(FIG / "p3_monitor_cost.pdf")
        fig.savefig(FIG / "p3_monitor_cost.png", dpi=150)
        out.append(f"\nFigure: `paper3/figures/p3_monitor_cost.pdf`\n")
    except Exception as e:  # noqa: BLE001
        out.append(f"\n(figure skipped: {e})\n")

    g.to_csv(OUT / "monitor_cost_grid.csv", index=False)
    r.to_csv(OUT / "monitor_roc.csv", index=False)
    txt = "\n".join(out)
    (OUT / "monitor_defense.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
