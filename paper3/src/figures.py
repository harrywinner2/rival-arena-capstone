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


# --------------------------------------------------------------------------- #
# F3 / F4 — added after the L5 pilot and the full experiment program completed.
# --------------------------------------------------------------------------- #

L5_FID = [("token oracle", -0.0000, 1.000), ("trained", 0.019, 1.000),
          ("shuffled", 6.440, 0.109), ("random", 8.019, 0.000),
          ("zero", 18.101, 0.000)]
L5_BEH = [("none", 0, 12), ("text\nproposal", 5, 12), ("text\nintent.", 0, 12),
          ("latent\nproposal", 1, 12), ("latent\nintent.", 0, 12),
          ("latent\nshuffled", 0, 12), ("latent\nzero", 0, 12)]


def fig3_latent() -> None:
    """Token-level fidelity is near-perfect; the behavioural effect does not transfer."""
    fig, ax = plt.subplots(1, 2, figsize=(6.6, 2.8),
                           gridspec_kw={"width_ratios": [1, 1.35]})

    names = [n for n, _, _ in L5_FID]
    top1 = [t for _, _, t in L5_FID]
    y = np.arange(len(names))[::-1]
    cols = [CAT[2] if n in ("token oracle", "trained") else MUTED for n in names]
    ax[0].barh(y, top1, height=0.6, color=cols, zorder=3)
    for i, (n, kl, t) in enumerate(L5_FID):
        ax[0].text(t + 0.03, y[i], f"{t:.2f}", va="center", fontsize=7, color=INK)
    ax[0].set_yticks(y); ax[0].set_yticklabels(names)
    ax[0].set_xlim(0, 1.28); ax[0].set_xlabel("top-1 agreement with text")
    ax[0].set_title("channel fidelity", fontsize=8.5)
    ax[0].xaxis.grid(True, color=GRID, lw=0.7, zorder=0); ax[0].set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax[0].spines[sp].set_visible(False)

    labs = [n for n, _, _ in L5_BEH]
    x = np.arange(len(labs))
    props = [k / n for _, k, n in L5_BEH]
    err = np.array([[p - wilson(k, n)[0] for p, (_, k, n) in zip(props, L5_BEH)],
                    [wilson(k, n)[1] - p for p, (_, k, n) in zip(props, L5_BEH)]])
    bcols = [CAT[0] if l.startswith("text") else (MUTED if l == "none" else CAT[1])
             for l in labs]
    ax[1].bar(x, props, width=0.62, color=bcols, yerr=err,
              error_kw=dict(ecolor=MUTED, elinewidth=1.0, capsize=2.5), zorder=3)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(labs, fontsize=6.2, rotation=32, ha="right",
                          rotation_mode="anchor")
    ax[1].set_ylabel("lock-in (Wilson 95% CI)"); ax[1].set_ylim(0, 0.78)
    ax[1].set_title("behavioural transfer", fontsize=8.5)
    ax[1].yaxis.grid(True, color=GRID, lw=0.7, zorder=0); ax[1].set_axisbelow(True)
    for sp in ("top", "right"):
        ax[1].spines[sp].set_visible(False)
    ax[1].annotate("effect appears\nover text", xy=(1, 0.417), xytext=(1.75, 0.66),
                   fontsize=6.8, color=CAT[0], ha="left",
                   arrowprops=dict(arrowstyle="->", color=CAT[0], lw=0.9))
    ax[1].annotate("and not over the link", xy=(3, 0.083), xytext=(3.1, 0.42),
                   fontsize=6.8, color=CAT[1], ha="left",
                   arrowprops=dict(arrowstyle="->", color=CAT[1], lw=0.9))
    fig.tight_layout()
    fig.savefig(FIG / "f3_latent_transfer.pdf"); fig.savefig(FIG / "f3_latent_transfer.png")
    plt.close(fig); print("wrote f3_latent_transfer")


LEDGER = [
    ("G0", "model responds to readable communication", "held", "+0.583 [lb +0.307]"),
    ("V1", "detector agreement $\\kappa \\geq 0.6$", "held", "0.840"),
    ("P1", "joint proposal $>$ own intention", "held", "+0.367 [+0.117, +0.559]"),
    ("P1", "a menu channel cannot coordinate", "refuted", "menu 0.900, highest arm"),
    ("P1", "menu-signal result replicates", "refuted", "0.00 at 72B, 0.900 at 14B"),
    ("P2", "modality effect in $\\geq$2 of 3 domains", "held", "2/3, CMH p<1e-15"),
    ("P2", "the mechanism is deception", "refuted", "pre-empted verification"),
    ("P3", "expressiveness ranks first", "held", "$\\eta^2$ .042 > .031 > .018"),
    ("P3", "expressiveness dominates ($\\geq 3\\times$)", "refuted", "1.34$\\times$"),
    ("P4", "opening-window suppression protects", "refuted", "0.53$\\times$ linear"),
    ("L5", "framing survives a latent channel", "refuted", "+0.083 [-0.169, +0.354]"),
]


def fig4_ledger() -> None:
    """Every pre-registered prediction and its outcome, including the falsified ones."""
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    n = len(LEDGER)
    for i, (exp, claim, status, ev) in enumerate(LEDGER):
        y = n - i
        held = status == "held"
        c = CAT[2] if held else CAT[3]
        ax.scatter([0], [y], s=42, marker="o" if held else "X", color=c, zorder=3)
        ax.text(0.055, y, f"{exp}  {claim}", va="center", fontsize=7.4, color=INK)
        ax.text(0.995, y, ev, va="center", ha="right", fontsize=6.8, color=MUTED)
        ax.text(0.052, y - 0.34, "", fontsize=1)
    ax.set_xlim(-0.03, 1.02); ax.set_ylim(-0.35, n + 0.9)
    ax.axis("off")
    ax.text(0, n + 0.65, "pre-registered prediction", fontsize=7.6, color=INK,
            fontweight="bold")
    ax.text(0.995, n + 0.65, "outcome", fontsize=7.6, color=INK, ha="right",
            fontweight="bold")
    ax.scatter([0.28], [-0.1], s=42, marker="o", color=CAT[2])
    ax.text(0.305, -0.1, "held", fontsize=7.2, va="center", color=INK)
    ax.scatter([0.42], [-0.1], s=42, marker="X", color=CAT[3])
    ax.text(0.445, -0.1, "refuted by our own data", fontsize=7.2, va="center", color=INK)
    fig.tight_layout()
    fig.savefig(FIG / "f4_prereg_ledger.pdf"); fig.savefig(FIG / "f4_prereg_ledger.png")
    plt.close(fig); print("wrote f4_prereg_ledger")


if __name__ != "__main__":
    pass
