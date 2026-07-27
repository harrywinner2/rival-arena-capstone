#!/usr/bin/env python3
"""Figures for the latent-transfer and model-generality results.

Style is inherited from figures.py: Okabe-Ito categorical hues in fixed order, thin
marks, recessive grid. Identity is never carried by colour alone -- every series is
also directly labelled, and the two panels of f3 are separated by position and axis
rather than by hue.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

FIG = Path(__file__).resolve().parents[1] / "paper" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#1b1b1b", "#6b6b6b", "#e3e3e0"
CAT = ["#0072B2", "#E69F00", "#009E73", "#CC79A7"]

plt.rcParams.update({
    "font.size": 8, "axes.labelsize": 8, "axes.titlesize": 9,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7.5,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})

# ---------------------------------------------------------------- f3: transfer
ARMS = [
    ("no channel",        0.585, 0.250, MUTED),
    ("text, proposal",    0.450, 0.650, CAT[0]),
    ("latent, proposal",  0.450, 0.650, CAT[1]),
    ("text, intention",   0.587, 0.225, CAT[0]),
    ("latent, intention", 0.588, 0.275, CAT[1]),
    ("latent, mismatched", 0.615, 0.075, CAT[3]),
    ("latent, shuffled",  0.557, 0.275, CAT[2]),
    ("latent, zero",      0.534, 0.175, CAT[2]),
]


def f3():
    # LNCS text width is 122mm = 4.8in. Drawing at 7in and scaling to \textwidth
    # shrank the tick fonts to ~5.5pt. Stack the panels instead so the figure is
    # natively column-width and the labels render at their true size.
    fig, axes = plt.subplots(2, 1, figsize=(4.75, 4.5))
    for ax, idx, title, xlab, ref in (
            (axes[0], 1, "Bertrand market  (collusion index $K$)", "$K$", 0.585),
            (axes[1], 2, "Prisoner's dilemma  (lock-in proportion)",
             "lock-in", 0.250)):
        y = np.arange(len(ARMS))[::-1]
        vals = [a[idx] for a in ARMS]
        cols = [a[3] for a in ARMS]
        ax.axvline(ref, color=MUTED, lw=1, ls=":", zorder=1)
        ax.barh(y, vals, height=0.62, color=cols, zorder=3)
        # 2px surface gap between bars is handled by height < 1
        for yi, v in zip(y, vals):
            ax.text(v + (0.012 if idx == 1 else 0.012), yi, f"{v:.3f}",
                    va="center", ha="left", fontsize=7, color=INK, zorder=4)
        ax.set_yticks(y)
        ax.set_yticklabels([a[0] for a in ARMS])
        ax.set_xlabel(xlab)
        ax.set_title(title, loc="left")
        ax.set_xlim(0, max(vals) * 1.52)
        ax.xaxis.grid(True, color=GRID, lw=0.7, zorder=0)
        ax.set_axisbelow(True)
        for s in ("top", "right", "left"):
            ax.spines[s].set_visible(False)
    # bracket the two coinciding bars, placed clear of the value labels rather than
    # on top of them
    for ax, x0 in ((axes[0], 0.585), (axes[1], 0.795)):
        ax.annotate("identical", xy=(x0, 5.5), xytext=(x0 + 0.075, 5.5),
                    fontsize=7.5, color=INK, va="center",
                    arrowprops=dict(arrowstyle="-[, widthB=1.35, lengthB=0.35",
                                    lw=0.9, color=INK))
    fig.text(0.5, -0.03, "dotted line = no channel", ha="center",
             fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(FIG / "f3_latent_transfer.pdf")
    plt.close(fig)
    print("wrote f3_latent_transfer.pdf")


# ---------------------------------------------------------- f5: generality
GEN = [
    ("Qwen2.5-14B",  -0.126, -0.203, -0.054),
    ("Llama-3.1-8B", -0.041, -0.061, -0.021),
    ("OLMo-2-13B",   -0.075, -0.125, -0.028),
]
POOLED = (-0.069, -0.113, -0.026)


def f5():
    fig, ax = plt.subplots(figsize=(4.4, 2.2))
    labels = [g[0] for g in GEN] + ["pooled (random effects)"]
    est = [g[1] for g in GEN] + [POOLED[0]]
    lo = [g[2] for g in GEN] + [POOLED[1]]
    hi = [g[3] for g in GEN] + [POOLED[2]]
    y = np.arange(len(labels))[::-1]
    ax.axvline(0, color=INK, lw=0.9, zorder=2)
    for i, (yi, e, l, h) in enumerate(zip(y, est, lo, hi)):
        pooled = i == len(labels) - 1
        c = INK if pooled else CAT[i]
        ax.plot([l, h], [yi, yi], color=c, lw=1.8, solid_capstyle="round", zorder=3)
        ax.plot([e], [yi], marker="D" if pooled else "o",
                ms=7 if pooled else 5.5, color=c, zorder=4,
                markeredgecolor="white", markeredgewidth=1.0)
        ax.text(h + 0.006, yi, f"{e:+.3f}", va="center", ha="left",
                fontsize=7, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlabel("proposal $-$ no channel  (collusion index $K$)")
    ax.set_xlim(-0.23, 0.10)
    ax.xaxis.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.set_title("A joint proposal is anti-collusive in every family", loc="left")
    fig.text(0.02, -0.10, "Negative = less collusion. 3/3 significant, same sign; "
             "$I^2=65\\%$, so pooling is random-effects.",
             fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(FIG / "f5_generality.pdf")
    plt.close(fig)
    print("wrote f5_generality.pdf")


if __name__ == "__main__":
    f3()
    f5()
