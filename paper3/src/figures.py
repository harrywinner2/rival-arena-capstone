"""Paper 3 figures.

F1  the predicate: lock-in by arm, ordered by whether the arm admits a joint proposal.
F2  cooperation trajectory by rung: opening displacement + decay.

Colour: Okabe-Ito categorical subset, validated (dataviz six checks). The adjacent
green/pink pair sits in the 6-8 CVD floor band, which is legal only with secondary
encoding, so every series also carries a distinct dash pattern AND a direct end-label;
identity is never colour-alone. Single-series figures carry no legend.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
from build_match_table import load  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK = "#1b1b1b"
MUTED = "#6b6b6b"
GRID = "#e3e3e0"
# fixed order, never cycled
CAT = ["#0072B2", "#E69F00", "#009E73", "#CC79A7"]
DASH = ["-", "--", "-.", ":"]

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 9,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def fig1(df: pd.DataFrame) -> None:
    """Lock-in by arm, grouped by whether the arm admits a joint proposal."""
    rows = pd.read_csv(Path(__file__).resolve().parents[1] / "results"
                       / "proposal_matches.csv")
    order = ["C1:restricted", "C1:selected", "L1_signal", "L0_none",
             "C1:free", "L2_observed", "L3_private"]
    label = {"L0_none": "L0 no channel", "L1_signal": "L1 fixed menu",
             "C1:selected": "C1 menu (selected)",
             "C1:restricted": "C1 free text,\nown intention only",
             "C1:free": "C1 free text", "L2_observed": "L2 free text",
             "L3_private": "L3 free text, private"}
    data = []
    for a in order:
        s = rows[rows.arm == a]
        if not len(s):
            continue
        k, n = int(s.lockin.sum()), len(s)
        lo, hi = wilson(k, n)
        data.append((label[a], k / n, lo, hi, s.proposal_frac.mean(), n))

    fig, ax = plt.subplots(figsize=(5.3, 3.0))
    y = np.arange(len(data))
    admits = np.array([d[4] for d in data]) > 0.5
    # magnitude by category -> bar. Two groups, so colour carries the grouping and
    # the group is ALSO named on the axis; identity is never colour-alone.
    colors = [CAT[0] if a else MUTED for a in admits]
    vals = [d[1] for d in data]
    err = np.array([[d[1] - d[2] for d in data], [d[3] - d[1] for d in data]])
    ax.barh(y, vals, height=0.6, color=colors, xerr=err,
            error_kw=dict(ecolor=MUTED, elinewidth=1.0, capsize=2.5), zorder=3)
    for i, d in enumerate(data):
        ax.text(d[1] + err[1][i] + 0.02, i, f"{d[1]:.2f}", va="center",
                ha="left", fontsize=7.5, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels([d[0] for d in data])
    ax.set_xlabel("cooperation lock-in proportion (Wilson 95% CI)")
    ax.set_xlim(0, 1.06)
    ax.axhline(3.5, color=MUTED, lw=0.8, ls=(0, (4, 3)))
    # group labels live in the right margin, so they cannot collide with the
    # value labels sitting just past each bar's error bar
    ax.text(1.03, 5.0, "admits a joint\nproposal", rotation=90, ha="center",
            va="center", fontsize=7.5, color=CAT[0], linespacing=1.25)
    ax.text(1.03, 1.5, "own intention\nonly", rotation=90, ha="center",
            va="center", fontsize=7.5, color=MUTED, linespacing=1.25)
    ax.xaxis.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    fig.savefig(FIG / "f1_predicate.pdf")
    fig.savefig(FIG / "f1_predicate.png")
    plt.close(fig)
    print("wrote f1_predicate")


def fig2(df: pd.DataFrame) -> None:
    """Mean cooperation by round and rung."""
    d = df[(df.game == "ipd") & df.cooperative.notna()]
    rungs = ["L0_none", "L1_signal", "L2_observed", "L3_private"]
    names = {"L0_none": "L0 none", "L1_signal": "L1 menu",
             "L2_observed": "L2 free text", "L3_private": "L3 private"}
    fig, ax = plt.subplots(figsize=(5.3, 2.9))
    maxr = 20
    for i, r in enumerate(rungs):
        s = d[d.channel == r]
        g = s.groupby("round_index").cooperative.mean()
        g = g[g.index < maxr]
        ax.plot(g.index, g.values, DASH[i], color=CAT[i], lw=1.8,
                solid_capstyle="round", zorder=3)
        # direct end-label: identity never colour-alone. Nudge off the axis when a
        # series ends at the floor so the label does not sit on the spine.
        ylab = max(g.values[-1], 0.035)
        ax.text(g.index[-1] + 0.25, ylab, names[r], color=CAT[i],
                fontsize=7.5, va="center", ha="left")
    ax.axvspan(-0.4, 2.4, color=CAT[0], alpha=0.06, zorder=0)
    ax.text(1.0, 0.04, "opening\nwindow", ha="center", va="bottom",
            fontsize=7, color=MUTED)
    ax.set_xlabel("round")
    ax.set_ylabel("mean cooperation")
    ax.set_xlim(-0.5, maxr + 5.2)
    ax.set_ylim(0, 1.0)
    ax.set_xticks([0, 5, 10, 15, 19])
    ax.yaxis.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    fig.savefig(FIG / "f2_trajectory.pdf")
    fig.savefig(FIG / "f2_trajectory.png")
    plt.close(fig)
    print("wrote f2_trajectory")


def main() -> None:
    df = load()
    fig1(df)
    fig2(df)


if __name__ == "__main__":
    main()
