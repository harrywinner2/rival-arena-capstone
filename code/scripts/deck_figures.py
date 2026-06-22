#!/usr/bin/env python3
"""Render high-DPI PNG figures for the demo-day reveal.js deck.

Run:  .venv/bin/python scripts/deck_figures.py  ->  presentation/assets/f*.png

ZERO API spend (pure plotting). Numbers are LOCKED per docs/paper_facts.md §3/§4
and mirror scripts/paper_figures.py EXACTLY -- only style (size/DPI/fonts/colors)
is changed for projection. The paper's PDFs in paper/figures/ are NOT touched.

Style differences vs the paper script:
  * larger figures + larger fonts (legible from the back of a room)
  * sans-serif (cleaner on screen than serif)
  * transparent background so figures sit on the dark deck theme
  * light-on-dark text colors (the deck is dark)
  * ~200 dpi raster PNG
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "presentation" / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

DPI = 200

# Dark-deck friendly: light text/axes on transparent background.
FG = "#E8ECF3"      # near-white foreground (text, ticks, spines)
MUTED = "#9AA7BD"   # muted labels

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 15,
    "axes.titlesize": 16,
    "axes.labelsize": 15,
    "legend.fontsize": 12.5,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.alpha": 0.18,
    "grid.linewidth": 0.8,
    "lines.linewidth": 2.4,
    "figure.dpi": DPI,
    "savefig.dpi": DPI,
    "savefig.bbox": "tight",
    "savefig.transparent": True,
    # paint all the "ink" light so it reads on a dark slide
    "text.color": FG,
    "axes.labelcolor": FG,
    "axes.edgecolor": FG,
    "xtick.color": FG,
    "ytick.color": FG,
    "grid.color": FG,
})

# Wong (2011) colorblind-safe palette (brightened a touch for dark bg)
BLUE = "#3FA7FF"
SKY = "#56B4E9"
ORANGE = "#F0A500"
VERM = "#FF6B4A"     # reddish, "bad"/lie
GREEN = "#2FD08A"
YELLOW = "#F0E442"
PURPLE = "#E07AB8"
GRAY = "#9AA7BD"
LGRAY = "#5C6779"


def save(fig, name: str):
    out = ASSETS / name
    fig.savefig(out, facecolor="none")
    plt.close(fig)
    return out


# F1 -- A1 lock-in ladder, canonical vs novel (content beats signal)
def f1_a1_ladder():
    rungs = ["L0\nnone", "L1\nsignal", "L2\nfree-text", "L3\nprivate"]
    can = [0.15, 0.00, 0.60, 0.60]
    can_lo = [0.05, 0.00, 0.39, 0.39]
    can_hi = [0.36, 0.16, 0.78, 0.78]
    nov = [0.15, 0.00, 0.40, 0.30]
    nov_lo = [0.05, 0.00, 0.22, 0.15]
    nov_hi = [0.36, 0.16, 0.61, 0.52]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = np.arange(4)
    w = 0.38
    ax.bar(x - w / 2, can, w, color=BLUE, edgecolor=FG, linewidth=0.6,
           label="canonical payoffs",
           yerr=[np.array(can) - can_lo, np.array(can_hi) - np.array(can)],
           capsize=4, error_kw=dict(lw=1.2, ecolor=FG))
    ax.bar(x + w / 2, nov, w, color="none", edgecolor=BLUE, linewidth=1.6,
           hatch="////", label="novel payoffs",
           yerr=[np.array(nov) - nov_lo, np.array(nov_hi) - np.array(nov)],
           capsize=4, error_kw=dict(lw=1.2, ecolor=FG))
    ax.set_xticks(x)
    ax.set_xticklabels(rungs)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Lock-in proportion (mean $C>0.8$)")
    ax.set_xlabel("Channel rung")
    ax.legend(frameon=False, loc="upper left", labelcolor=FG)
    ax.annotate("L1 signal collapses\nBELOW L0 silence",
                xy=(1, 0.02), xytext=(1.35, 0.42), fontsize=12.5, color=VERM,
                ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=VERM, lw=1.6))
    fig.tight_layout()
    return save(fig, "f1_a1_ladder.png")


# F2 -- A1 cooperation over rounds (REAL DATA: master_long.csv)
def f2_a1_curve():
    m = pd.read_csv(ROOT / "data/master_long.csv", low_memory=False)
    a1 = m[(m.experiment_id == "A1") & (m.game == "ipd")]
    series = {
        "L0_none": (GRAY, "-", "o", "L0 no channel (decays)"),
        "L1_signal": (VERM, "--", "s", "L1 canned signal (poisons)"),
        "L2_observed": (GREEN, "-", "^", "L2 free-text (sustains)"),
    }
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    for ch, (c, ls, mk, lab) in series.items():
        sub = a1[a1.channel == ch]
        if not len(sub):
            continue
        t = sub.groupby("round_index")["cooperative"].mean()
        ax.plot(t.index, t.values, color=c, linestyle=ls, marker=mk,
                markersize=6, markevery=2, label=lab)
    ax.set_xlabel("Round")
    ax.set_ylabel("Mean cooperation rate")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, loc="upper right", labelcolor=FG)
    fig.tight_layout()
    return save(fig, "f2_a1_curve.png")


# F3 -- C1 content vs authorship
def f3_c1_content():
    conds = ["Menu\n(signal)", "Authored,\naction-only", "Free-text\n(content)"]
    pk = [0.14, 0.12, 0.74]
    li = [0.05, 0.00, 0.50]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = np.arange(3)
    w = 0.38
    ax.bar(x - w / 2, pk, w, color=ORANGE, edgecolor=FG, linewidth=0.6,
           label="Promise-keeping rate")
    ax.bar(x + w / 2, li, w, color="none", edgecolor=GREEN, linewidth=1.6,
           hatch="\\\\\\", label="Cooperation lock-in")
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Rate")
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=11,
              columnspacing=1.0, handletextpad=0.4, labelcolor=FG)
    ax.annotate("+authorship:\nINERT", xy=(0.5, 0.14), xytext=(0.55, 0.52),
                fontsize=12, color=GRAY, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.4))
    ax.annotate("+content:\nFLIPS IT", xy=(2.15, 0.50), xytext=(1.5, 0.74),
                fontsize=12, color=GREEN, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.4))
    fig.tight_layout()
    return save(fig, "f3_c1_content.png")


# F4 -- B1 collusion-K ladder
def f4_b1_k():
    rungs = ["L0\nnone", "L1\nsignal", "L2\nfree-text", "L3\nprivate"]
    kc = [-0.36, -0.64, 0.69, 1.23]
    kn = [0.11, 0.04, 0.43, 0.38]
    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    x = np.arange(4)
    w = 0.38
    ax.bar(x - w / 2, kc, w, color=VERM, edgecolor=FG, linewidth=0.6,
           label="canonical demand")
    ax.bar(x + w / 2, kn, w, color="none", edgecolor=VERM, linewidth=1.6,
           hatch="////", label="novel demand (floor)")
    ax.axhline(1.0, ls=":", color=GRAY, lw=1.4)
    ax.axhline(0.0, color=FG, lw=1.0)
    ax.text(3.45, 1.05, "monopoly ($K{=}1$)", fontsize=11.5, color=GRAY,
            ha="right", va="bottom")
    ax.text(3.45, -0.06, "competitive ($K{=}0$)", fontsize=11.5, color=GRAY,
            ha="right", va="top")
    ax.annotate("$K=1.23$:\nsupra-monopoly", xy=(0.05, 1.23), xytext=(0.7, 1.34),
                fontsize=11.5, color=FG, ha="left", va="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=FG, lw=1.3))
    ax.set_xticks(x)
    ax.set_xticklabels(rungs)
    ax.set_ylabel("Collusion index $K$")
    ax.set_xlabel("Channel rung")
    ax.set_ylim(-0.85, 1.55)
    ax.legend(frameon=False, loc="lower right", labelcolor=FG)
    fig.tight_layout()
    return save(fig, "f4_b1_k.png")


# F5 -- A3 per-pair channel slope (within > between)
def f5_a3_origin():
    pairs = ["cross-origin A", "cross-origin B", "same-family",
             "same-origin (CN)", "same-origin (West)"]
    slopes = [0.90, 0.10, 0.70, 0.40, 0.80]
    is_cross = [True, True, False, False, False]
    order = np.argsort(slopes)
    pairs = [pairs[i] for i in order]
    slopes = [slopes[i] for i in order]
    is_cross = [is_cross[i] for i in order]
    colors = [PURPLE if c else BLUE for c in is_cross]
    hatches = ["xxx" if c else "" for c in is_cross]

    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    y = np.arange(len(pairs))
    for yi, s, c, h in zip(y, slopes, colors, hatches):
        ax.barh(yi, s, color=c, edgecolor=FG, linewidth=0.6, hatch=h)
    ax.set_yticks(y)
    ax.set_yticklabels(pairs, fontsize=12)
    ax.set_xlim(0, 1.18)
    ax.set_xlabel("Channel effect (lock-in slope L0$\\to$L3)")
    ax.legend(handles=[
        Patch(facecolor=PURPLE, edgecolor=FG, hatch="xxx", label="cross-origin"),
        Patch(facecolor=BLUE, edgecolor=FG, label="same-origin"),
    ], frameon=False, loc="lower right", fontsize=11.5, labelcolor=FG)
    ax.text(0.99, 0.42,
            "$\\eta^2$: channel 0.54\nvs origin 0.03\n(~20$\\times$ more variance)",
            transform=ax.transAxes, ha="right", va="center", fontsize=11,
            color=GRAY)
    fig.tight_layout()
    return save(fig, "f5_a3_origin.png")


# F6 -- oversight 3-panel: detection!=prevention | enforcement | false-positives
def f6_oversight():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))

    ax = axes[0]
    strg = ["none", "weak", "strong"]
    kk = [0.44, 0.46, 0.58]
    det = [0.0, 0.85, 1.00]
    xx = np.arange(3)
    ax.bar(xx, kk, color=BLUE, edgecolor=FG, linewidth=0.6, width=0.6,
           label="collusion $K$")
    ax.plot(xx, det, "o--", color=VERM, markersize=7, label="detect-rate")
    ax.set_xticks(xx)
    ax.set_xticklabels(strg)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Rate / $K$")
    ax.set_xlabel("Monitor strength")
    ax.set_title("(a) Detection $\\neq$ prevention")
    ax.legend(frameon=False, loc="center left", labelcolor=FG)

    ax = axes[1]
    ax.bar(["off", "on"], [0.33, 0.18], color=[LGRAY, GREEN],
           edgecolor=FG, linewidth=0.6, width=0.55)
    ax.set_ylim(0, 0.42)
    ax.set_ylabel("Collusion $K$")
    ax.set_xlabel("Penalty on flag")
    ax.set_title("(b) Enforcement deters")
    ax.annotate("$-42\\%$", xy=(1, 0.19), xytext=(0.45, 0.31),
                color=GREEN, fontsize=15, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.6))

    ax = axes[2]
    ax.bar(["strong", "weak"], [0.98, 0.88], color=VERM,
           edgecolor=FG, linewidth=0.6, width=0.55, hatch="...")
    ax.set_ylim(0, 1.20)
    ax.set_ylabel("False-positive rate")
    ax.set_xlabel("Monitor strength")
    ax.set_title("(c) Flags non-colluders")
    ax.text(0.5, 1.10, "corr$(K,$ score$)\\approx 0$", ha="center",
            fontsize=12, color=GRAY, transform=ax.transData)
    fig.tight_layout()
    return save(fig, "f6_oversight.png")


# F7 -- cross-game generalization
def f7_generalize():
    games = ["IPD\n(coop)", "Bertrand\n($K$)", "Public goods\n(coop)",
             "Double-auction\n($K$)"]
    nochan = [0.15, 0.11, 0.03, 0.06]
    chan = [0.60, 0.43, 0.44, 0.28]
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = np.arange(4)
    w = 0.38
    ax.bar(x - w / 2, nochan, w, color="none", edgecolor=GRAY, linewidth=1.6,
           hatch="...", label="no channel")
    ax.bar(x + w / 2, chan, w, color=BLUE, edgecolor=FG, linewidth=0.6,
           label="with channel")
    ax.set_xticks(x)
    ax.set_xticklabels(games, fontsize=11.5)
    ax.set_ylim(0, 0.72)
    ax.set_ylabel("Cooperation / collusion")
    ax.legend(frameon=False, loc="upper right", labelcolor=FG)
    fig.tight_layout()
    return save(fig, "f7_generalize.png")


# F8 -- alignment: E1-escalate dose-response + E1 leak-vs-contact
def f8_alignment_dose():
    fig, axes = plt.subplots(1, 2, figsize=(13.5, 4.8))

    ax = axes[0]
    P = ["P0\nfirm", "P1\n+pleas", "P2\nweaken", "P3\nremove",
         "P4\n+social", "P5\n+'saves B'"]
    leak = [0.00, 0.00, 0.19, 0.44, 0.56, 0.50]
    xx = np.arange(6)
    ax.bar(xx, leak, color=VERM, edgecolor=FG, linewidth=0.6,
           width=0.62, label="functional leak (share findings)")
    ax.axvspan(-0.5, 1.5, color=GREEN, alpha=0.13)
    ax.text(0.5, 0.90, "instruction firm\n$0/16$ leaks", ha="center",
            fontsize=12, color=GREEN, fontweight="bold")
    ax.set_xticks(xx)
    ax.set_xticklabels(P, fontsize=11)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Functional leak rate")
    ax.set_xlabel("Pressure rung (instruction weakening)")
    ax.set_title("(a) E1-escalate: dose-response on the instruction")

    ax = axes[1]
    ch = ["none", "open", "private"]
    leak2 = [0.0, 0.0, 0.0]
    contact = [0.0, 0.38, 0.38]
    xx = np.arange(3)
    w = 0.38
    ax.bar(xx - w / 2, leak2, w, color=VERM, edgecolor=FG, linewidth=0.6,
           label="leaks findings (0/48)")
    ax.bar(xx + w / 2, contact, w, color="none", edgecolor=BLUE,
           linewidth=1.6, hatch="////", label="contacts rival")
    for xi in xx:
        ax.plot(xi - w / 2, 0.01, marker="_", color=VERM, markersize=14)
    ax.set_xticks(xx)
    ax.set_xticklabels(ch)
    ax.set_ylim(0, 0.6)
    ax.set_ylabel("Rate (threat arm)")
    ax.set_xlabel("Channel")
    ax.set_title("(b) E1-full: channel raises contact, not leaking")
    ax.legend(frameon=False, loc="upper left", labelcolor=FG)
    fig.tight_layout()
    return save(fig, "f8_alignment_dose.png")


# F9 -- S2 observability: honest/omit/lie by channel x request-mode
def f9_s2_observability():
    arms = ["none /\nexplicit ask", "none /\noptimistic", "open /\nexplicit ask",
            "private /\nexplicit ask"]
    honest = [0.00, 0.50, 0.58, 0.67]
    omit = [0.25, 0.25, 0.42, 0.33]
    lie = [0.75, 0.25, 0.00, 0.00]

    fig, ax = plt.subplots(figsize=(8.4, 5.0))
    x = np.arange(len(arms))
    w = 0.27
    ax.bar(x - w, honest, w, color=GREEN, edgecolor=FG, linewidth=0.6,
           label="honest")
    ax.bar(x, omit, w, color=LGRAY, edgecolor=FG, linewidth=0.6,
           hatch="...", label="omission")
    ax.bar(x + w, lie, w, color=VERM, edgecolor=FG, linewidth=0.6,
           hatch="xxx", label="active lie")
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=11.5)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Rate of verdict outcome")
    ax.legend(frameon=False, loc="upper center", ncol=3, fontsize=11.5,
              columnspacing=1.0, handletextpad=0.4,
              bbox_to_anchor=(0.5, 1.04), labelcolor=FG)
    ax.annotate("private back-channel\n$\\to$ lie 0.75",
                xy=(0 + 0.27, 0.75), xytext=(1.15, 0.92), fontsize=11,
                color=VERM, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=VERM, lw=1.4))
    ax.annotate("observable channels\n$\\to$ lie 0.00",
                xy=(2.27, 0.02), xytext=(2.95, 0.60), fontsize=11, color=GREEN,
                ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=1.4))
    fig.tight_layout()
    return save(fig, "f9_s2_observability.png")


FIGS = [
    f1_a1_ladder, f2_a1_curve, f3_c1_content, f4_b1_k, f5_a3_origin,
    f6_oversight, f7_generalize, f8_alignment_dose, f9_s2_observability,
]


def main():
    for fn in FIGS:
        out = fn()
        print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
