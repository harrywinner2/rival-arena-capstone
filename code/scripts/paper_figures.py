#!/usr/bin/env python3
"""Regenerate all publication-grade vector (PDF) figures for the paper.

Run:  .venv/bin/python scripts/paper_figures.py   ->  paper/figures/*.pdf

ZERO API spend (pure plotting). Numbers are LOCKED per docs/paper_facts.md §3/§4.
Only F2 (cooperation-over-rounds) is drawn from real per-round data
(data/master_long.csv); everything else uses the vetted facts-sheet constants.

Style: serif body font (LaTeX-match), font.size 9, vector PDF, colorblind-safe
AND grayscale-legible (series distinguished by hatch / linestyle / marker, not
colour alone), tight bounding box, no chart-junk.
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
FIGDIR = ROOT / "paper" / "figures"
FIGDIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------- #
# Publication style.  Wong colorblind-safe palette + hatching/linestyle for B/W.
# ----------------------------------------------------------------------------- #
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Nimbus Roman", "Liberation Serif",
                   "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 9,
    "axes.titlesize": 9,
    "axes.labelsize": 9,
    "legend.fontsize": 7.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.alpha": 0.30,
    "grid.linewidth": 0.5,
    "lines.linewidth": 1.4,
    "pdf.fonttype": 42,   # embed TrueType (editable text in the PDF)
    "ps.fonttype": 42,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
})

# Wong (2011) colorblind-safe palette
BLUE = "#0072B2"
SKY = "#56B4E9"
ORANGE = "#E69F00"
VERM = "#D55E00"     # reddish, "bad"/lie
GREEN = "#009E73"
YELLOW = "#F0E442"
PURPLE = "#CC79A7"
GRAY = "#666666"
LGRAY = "#BBBBBB"

COL = "single"   # ~3.3in width markers in the manifest
FULL = "full"


def save(fig, name: str):
    out = FIGDIR / name
    fig.savefig(out)
    plt.close(fig)
    return out


# ============================================================================= #
# F1 — A1 lock-in ladder, canonical vs novel, Wilson CIs (content beats signal)
# ============================================================================= #
def f1_a1_ladder():
    rungs = ["L0\nnone", "L1\nsignal", "L2\nfree-text", "L3\nprivate"]
    can = [0.15, 0.00, 0.60, 0.60]
    can_lo = [0.05, 0.00, 0.39, 0.39]
    can_hi = [0.36, 0.16, 0.78, 0.78]
    nov = [0.15, 0.00, 0.40, 0.30]
    nov_lo = [0.05, 0.00, 0.22, 0.15]
    nov_hi = [0.36, 0.16, 0.61, 0.52]

    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    x = np.arange(4)
    w = 0.38
    ax.bar(x - w / 2, can, w, color=BLUE, edgecolor="black", linewidth=0.5,
           label="canonical payoffs",
           yerr=[np.array(can) - can_lo, np.array(can_hi) - np.array(can)],
           capsize=2, error_kw=dict(lw=0.8, ecolor="black"))
    ax.bar(x + w / 2, nov, w, color="white", edgecolor=BLUE, linewidth=0.8,
           hatch="////", label="novel payoffs",
           yerr=[np.array(nov) - nov_lo, np.array(nov_hi) - np.array(nov)],
           capsize=2, error_kw=dict(lw=0.8, ecolor="black"))
    ax.set_xticks(x)
    ax.set_xticklabels(rungs)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Lock-in proportion (mean $C>0.8$)")
    ax.set_xlabel("Channel rung")
    ax.legend(frameon=False, loc="upper left")
    ax.annotate("L1 signal collapses\nbelow L0 silence",
                xy=(1, 0.02), xytext=(1.25, 0.40), fontsize=7, color=VERM,
                ha="center",
                arrowprops=dict(arrowstyle="->", color=VERM, lw=0.8))
    fig.tight_layout()
    return save(fig, "f1_a1_ladder.pdf")


# ============================================================================= #
# F2 — A1 cooperation over rounds, L0/L1/L2 (REAL DATA: master_long.csv)
# ============================================================================= #
def f2_a1_curve():
    m = pd.read_csv(ROOT / "data/master_long.csv", low_memory=False)
    a1 = m[(m.experiment_id == "A1") & (m.game == "ipd")]
    series = {
        "L0_none": (GRAY, "-", "o", "L0 no channel (decays)"),
        "L1_signal": (VERM, "--", "s", "L1 canned signal (poisons)"),
        "L2_observed": (GREEN, "-", "^", "L2 free-text (sustains)"),
    }
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    for ch, (c, ls, mk, lab) in series.items():
        sub = a1[a1.channel == ch]
        if not len(sub):
            continue
        t = sub.groupby("round_index")["cooperative"].mean()
        ax.plot(t.index, t.values, color=c, linestyle=ls, marker=mk,
                markersize=3, markevery=2, label=lab)
    ax.set_xlabel("Round")
    ax.set_ylabel("Mean cooperation rate")
    ax.set_ylim(0, 1.02)
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    return save(fig, "f2_a1_curve.pdf")


# ============================================================================= #
# F3 — C1 content vs authorship (promise-keeping & lock-in bars)
# ============================================================================= #
def f3_c1_content():
    conds = ["Menu\n(signal)", "Authored,\naction-only", "Free-text\n(full content)"]
    pk = [0.14, 0.12, 0.74]
    li = [0.05, 0.00, 0.50]
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    x = np.arange(3)
    w = 0.38
    ax.bar(x - w / 2, pk, w, color=ORANGE, edgecolor="black", linewidth=0.5,
           label="Promise-keeping rate")
    ax.bar(x + w / 2, li, w, color="white", edgecolor=GREEN, linewidth=0.8,
           hatch="\\\\\\", label="Cooperation lock-in")
    ax.set_xticks(x)
    ax.set_xticklabels(conds)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Rate")
    ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=6.8,
              columnspacing=1.0, handletextpad=0.4)
    ax.set_ylim(0, 1.05)
    ax.annotate("+authorship:\ninert", xy=(0.5, 0.14), xytext=(0.55, 0.48),
                fontsize=7, color=GRAY, ha="center",
                arrowprops=dict(arrowstyle="->", color=GRAY, lw=0.8))
    ax.annotate("+content:\nflips it", xy=(2.15, 0.50), xytext=(1.55, 0.66),
                fontsize=7, color=GREEN, ha="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))
    fig.tight_layout()
    return save(fig, "f3_c1_content.pdf")


# ============================================================================= #
# F4 — B1 collusion-K ladder, canonical vs novel (+ monopoly/competitive lines)
# ============================================================================= #
def f4_b1_k():
    # B1 spine K with bootstrap 95% CIs (percentile, 5000 resamples over matches).
    # Source: docs/stats_audit.md §2, "B1 spine (cross_origin), n=20/cell".
    rungs = ["L0\nnone", "L1\nsignal", "L2\nfree-text", "L3\nprivate"]
    # canonical: point, [lo, hi]
    kc = [-0.355, -0.640, 0.694, 1.229]
    kc_lo = [-0.558, -0.813, 0.512, 0.949]
    kc_hi = [-0.135, -0.445, 0.904, 1.539]
    # novel demand
    kn = [0.105, 0.035, 0.427, 0.380]
    kn_lo = [0.049, 0.007, 0.330, 0.282]
    kn_hi = [0.172, 0.067, 0.530, 0.488]

    fig, ax = plt.subplots(figsize=(3.3, 2.8))
    x = np.arange(4)
    w = 0.38
    ax.bar(x - w / 2, kc, w, color=VERM, edgecolor="black", linewidth=0.5,
           label="canonical demand",
           yerr=[np.array(kc) - kc_lo, np.array(kc_hi) - np.array(kc)],
           capsize=2, error_kw=dict(lw=0.8, ecolor="black"))
    ax.bar(x + w / 2, kn, w, color="white", edgecolor=VERM, linewidth=0.8,
           hatch="////", label="novel demand (floor)",
           yerr=[np.array(kn) - kn_lo, np.array(kn_hi) - np.array(kn)],
           capsize=2, error_kw=dict(lw=0.8, ecolor=VERM))
    ax.axhline(1.0, ls=":", color=GRAY, lw=1.0)
    ax.axhline(0.0, color="black", lw=0.7)
    ax.text(3.45, 1.03, "monopoly ($K{=}1$)", fontsize=6.5, color=GRAY,
            ha="right", va="bottom")
    ax.text(3.45, -0.05, "competitive ($K{=}0$)", fontsize=6.5, color=GRAY,
            ha="right", va="top")
    ax.annotate("$K>1$, CI $[0.95,1.54]$:\nsupra-monopoly", xy=(2.81, 1.18),
                xytext=(1.25, 1.42), fontsize=6.3, color="black", ha="left",
                va="center",
                arrowprops=dict(arrowstyle="->", color="black", lw=0.7))
    ax.set_xticks(x)
    ax.set_xticklabels(rungs)
    ax.set_ylabel("Collusion index $K$")
    ax.set_xlabel("Channel rung")
    ax.set_ylim(-0.95, 1.7)
    ax.legend(frameon=False, loc="lower right", fontsize=6.8)
    ax.text(0.0, -0.90, "error bars: bootstrap 95% CI ($n{=}20$/cell, 5000 resamples)",
            fontsize=5.6, color=GRAY, ha="left", va="bottom")
    fig.tight_layout()
    return save(fig, "f4_b1_k.pdf")


# ============================================================================= #
# F5 — A3 per-pair channel slope, colored by origin (within > between)
# ============================================================================= #
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

    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    y = np.arange(len(pairs))
    for yi, s, c, h in zip(y, slopes, colors, hatches):
        ax.barh(yi, s, color=c, edgecolor="black", linewidth=0.5, hatch=h)
    ax.set_yticks(y)
    ax.set_yticklabels(pairs, fontsize=7.5)
    ax.set_xlim(0, 1.18)
    ax.set_xlabel("Channel effect (lock-in slope L0$\\to$L3)")
    ax.legend(handles=[
        Patch(facecolor=PURPLE, edgecolor="black", hatch="xxx",
              label="cross-origin"),
        Patch(facecolor=BLUE, edgecolor="black", label="same-origin"),
    ], frameon=False, loc="lower right", fontsize=7)
    ax.text(0.99, 0.45,
            "$\\eta^2$: channel 0.54\nvs origin 0.03\n(spread is within,\nnot between)",
            transform=ax.transAxes, ha="right", va="center", fontsize=6.3,
            color=GRAY)
    fig.tight_layout()
    return save(fig, "f5_a3_origin.pdf")


# ============================================================================= #
# F6 — oversight 3-panel: detection != prevention | enforcement | false-positives
# ============================================================================= #
def f6_oversight():
    fig, axes = plt.subplots(1, 3, figsize=(6.8, 2.5))

    # panel 1: detection != prevention
    ax = axes[0]
    strg = ["none", "weak", "strong"]
    kk = [0.44, 0.46, 0.58]
    det = [0.0, 0.85, 1.00]
    xx = np.arange(3)
    ax.bar(xx, kk, color=BLUE, edgecolor="black", linewidth=0.5, width=0.6,
           label="collusion $K$")
    ax.plot(xx, det, "o--", color=VERM, markersize=4, label="detect-rate")
    ax.set_xticks(xx)
    ax.set_xticklabels(strg)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Rate / $K$")
    ax.set_xlabel("Monitor strength")
    ax.set_title("(a) Detection $\\neq$ prevention")
    ax.legend(frameon=False, loc="center left")

    # panel 2: enforcement deters
    ax = axes[1]
    ax.bar(["off", "on"], [0.33, 0.18], color=[LGRAY, GREEN],
           edgecolor="black", linewidth=0.5, width=0.55)
    ax.set_ylim(0, 0.42)
    ax.set_ylabel("Collusion $K$")
    ax.set_xlabel("Penalty on flag")
    ax.set_title("(b) Enforcement deters")
    ax.annotate("$-42\\%$", xy=(1, 0.19), xytext=(0.45, 0.30),
                color=GREEN, fontsize=8.5,
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9))

    # panel 3: false positives
    ax = axes[2]
    ax.bar(["strong", "weak"], [0.98, 0.88], color=VERM,
           edgecolor="black", linewidth=0.5, width=0.55, hatch="...")
    ax.set_ylim(0, 1.20)
    ax.set_ylabel("False-positive rate")
    ax.set_xlabel("Monitor strength")
    ax.set_title("(c) Flags non-colluders")
    ax.text(0.5, 1.10, "corr$(K,$ score$)\\approx 0$", ha="center",
            fontsize=6.8, color=GRAY, transform=ax.transData)
    fig.tight_layout()
    return save(fig, "f6_oversight.pdf")


# ============================================================================= #
# F7 — cross-game generalization: no-channel vs channel
# ============================================================================= #
def f7_generalize():
    games = ["IPD\n(coop)", "Bertrand\n($K$)", "Public goods\n(coop)",
             "Double-auction\n($K$)"]
    nochan = [0.15, 0.11, 0.03, 0.06]
    chan = [0.60, 0.43, 0.44, 0.28]
    fig, ax = plt.subplots(figsize=(3.3, 2.7))
    x = np.arange(4)
    w = 0.38
    ax.bar(x - w / 2, nochan, w, color="white", edgecolor=GRAY, linewidth=0.8,
           hatch="...", label="no channel")
    ax.bar(x + w / 2, chan, w, color=BLUE, edgecolor="black", linewidth=0.5,
           label="with channel")
    ax.set_xticks(x)
    ax.set_xticklabels(games, fontsize=7)
    ax.set_ylim(0, 0.72)
    ax.set_ylabel("Cooperation / collusion")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    return save(fig, "f7_generalize.pdf")


# ============================================================================= #
# F8 — alignment: E1-escalate dose-response (P0-P5) + E1 leak-vs-contact
# ============================================================================= #
def f8_alignment_dose():
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.8))

    ax = axes[0]
    P = ["P0\nfirm", "P1\n+pleas", "P2\nweaken", "P3\nremove",
         "P4\n+social", "P5\n+'saves B'"]
    leak = [0.00, 0.00, 0.19, 0.44, 0.56, 0.50]
    xx = np.arange(6)
    bars = ax.bar(xx, leak, color=VERM, edgecolor="black", linewidth=0.5,
                  width=0.62, label="functional leak (share findings)")
    # shade the "instruction holds" region
    ax.axvspan(-0.5, 1.5, color=GREEN, alpha=0.10)
    ax.text(0.5, 0.90, "instruction firm\n$0/16$ leaks", ha="center",
            fontsize=6.5, color=GREEN)
    ax.set_xticks(xx)
    ax.set_xticklabels(P, fontsize=6.5)
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
    ax.bar(xx - w / 2, leak2, w, color=VERM, edgecolor="black", linewidth=0.5,
           label="leaks findings (0/48)")
    ax.bar(xx + w / 2, contact, w, color="white", edgecolor=BLUE,
           linewidth=0.8, hatch="////", label="contacts rival")
    # mark the zero-leak bars
    for xi in xx:
        ax.plot(xi - w / 2, 0.01, marker="_", color=VERM, markersize=8)
    ax.set_xticks(xx)
    ax.set_xticklabels(ch)
    ax.set_ylim(0, 0.6)
    ax.set_ylabel("Rate (threat arm)")
    ax.set_xlabel("Channel")
    ax.set_title("(b) E1-full: channel raises contact, not leaking")
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout()
    return save(fig, "f8_alignment_dose.pdf")


# ============================================================================= #
# F9 — S2 observability: honest/omit/lie by channel x request-mode
# ============================================================================= #
def f9_s2_observability():
    # facts §4: arms with verdicts honest/omit/lie
    arms = ["none /\nexplicit ask", "none /\noptimistic", "open /\nexplicit ask",
            "private /\nexplicit ask"]
    honest = [0.00, 0.50, 0.58, 0.67]
    omit = [0.25, 0.25, 0.42, 0.33]
    lie = [0.75, 0.25, 0.00, 0.00]

    fig, ax = plt.subplots(figsize=(3.3, 3.0))
    x = np.arange(len(arms))
    w = 0.27
    ax.bar(x - w, honest, w, color=GREEN, edgecolor="black", linewidth=0.5,
           label="honest")
    ax.bar(x, omit, w, color=LGRAY, edgecolor="black", linewidth=0.5,
           hatch="...", label="omission")
    ax.bar(x + w, lie, w, color=VERM, edgecolor="black", linewidth=0.5,
           hatch="xxx", label="active lie")
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=6.5)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("Rate of verdict outcome")
    ax.legend(frameon=False, loc="upper center", ncol=3, fontsize=6.8,
              columnspacing=1.0, handletextpad=0.4,
              bbox_to_anchor=(0.5, 1.02))
    ax.annotate("private back-channel\n$\\to$ lie 0.75",
                xy=(0 + 0.27, 0.75), xytext=(1.15, 0.88), fontsize=6.3,
                color=VERM, ha="center",
                arrowprops=dict(arrowstyle="->", color=VERM, lw=0.8))
    ax.annotate("observable channels\n$\\to$ lie 0.00",
                xy=(2.27, 0.02), xytext=(2.9, 0.62), fontsize=6.3, color=GREEN,
                ha="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))
    fig.tight_layout()
    return save(fig, "f9_s2_observability.pdf")


# ============================================================================= #
# ROUND 2 — generality, monitor ROC, governance (docs/paper_facts.md §10)
# ============================================================================= #
M1_DIR = ROOT / "data/runs/M1/20260620T143225"


# ============================================================================= #
# F10 — generality: B1 collusion K at L0 vs L3 across 4 model families (§10a)
#       + small A1 cooperation-lock-in panel (cooperation is model-specific)
# ============================================================================= #
def f10_generality():
    # §10a B1 channel->collusion (novel demand, K, n=12/cell except open spine
    # n=20). Points: docs/paper_facts.md §10a. Bootstrap 95% CIs (percentile,
    # 5000 resamples over matches): docs/stats_audit.md §2 "Generality cells".
    # Gemini-2.5 self is INVALID (100% refusal on B1) — shown explicitly, not
    # omitted. Raw: data/runs/B1/20260620T* (gemini cell 20260620T134841).
    fams = ["open\nspine", "GPT-4o\n(self)", "Claude-3.7\n(self)",
            "Claude\n$\\times$Llama", "Gemini-2.5\n(self)"]
    # L0 / L3 point estimates and their bootstrap [lo, hi]
    l0 = [0.105, 0.192, 1.286, 0.917]
    l0_lo = [0.051, 0.076, 1.286, 0.832]
    l0_hi = [0.171, 0.310, 1.286, 0.992]
    l3 = [0.380, 0.810, 1.286, 0.989]
    l3_lo = [0.280, 0.714, 1.286, 0.900]
    l3_hi = [0.485, 0.917, 1.286, 1.076]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.0),
                             gridspec_kw={"width_ratios": [2.25, 1.0]})

    # ---- panel (a): the headline grouped bars ----
    ax = axes[0]
    nvalid = len(fams) - 1            # last family (Gemini) is the invalid cell
    x = np.arange(len(fams))
    w = 0.38
    xv = x[:nvalid]
    ax.bar(xv - w / 2, l0, w, color="white", edgecolor=GRAY, linewidth=0.9,
           hatch="...", label="L0  no channel",
           yerr=[np.array(l0) - l0_lo, np.array(l0_hi) - np.array(l0)],
           capsize=2, error_kw=dict(lw=0.8, ecolor=GRAY))
    ax.bar(xv + w / 2, l3, w, color=BLUE, edgecolor="black", linewidth=0.5,
           label="L3  private channel",
           yerr=[np.array(l3) - l3_lo, np.array(l3_hi) - np.array(l3)],
           capsize=2, error_kw=dict(lw=0.8, ecolor="black"))

    # Gemini: 100%-refusal INVALID cell — explicit hatched marker, not a value.
    gx = x[-1]
    ax.bar(gx, 1.55, 2 * w + 0.04, color="white", edgecolor=VERM, linewidth=1.0,
           hatch="xxxx", zorder=0)
    ax.text(gx, 0.78, "INVALID\n100% refusal\n(no usable $K$)", ha="center",
            va="center", fontsize=6.0, color=VERM, rotation=0)

    # reference regimes
    ax.axhline(1.0, ls=":", color=GRAY, lw=1.0)
    ax.axhline(0.0, color="black", lw=0.7)
    ax.text(3.42, 1.02, "monopoly ($K{=}1$)", fontsize=6.3, color=GRAY,
            ha="right", va="bottom")
    ax.text(-0.48, 0.015, "competitive ($K{=}0$)", fontsize=6.3, color=GRAY,
            ha="left", va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(fams, fontsize=7.0)
    ax.set_ylim(0, 1.62)
    ax.set_ylabel("Collusion index $K$ (novel demand)")
    ax.legend(frameon=False, loc="upper left", fontsize=7)
    # regime annotations (DESCRIPTIVE — no editorializing)
    ax.annotate("channel raises $K$\n(open, GPT-4o)", xy=(1 + w / 2, 0.81),
                xytext=(0.50, 0.55), fontsize=6.4, color=BLUE, ha="center",
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=0.8))
    ax.annotate("Claude L0: supracompetitive\nwithout a channel; prices do\n"
                "not co-move (independent,\nnot coordinated)",
                xy=(2 - w / 2 - 0.02, 1.286), xytext=(2.35, 0.42),
                fontsize=5.7, color=VERM, ha="center", va="center",
                arrowprops=dict(arrowstyle="->", color=VERM, lw=0.8))
    ax.set_title("(a) Collusion index $K$ by family, L0 vs L3 "
                 "(error bars: bootstrap 95% CI)", fontsize=7.0)

    # ---- panel (b): A1 cooperation lock-in is model-specific ----
    ax = axes[1]
    fams2 = ["open", "GPT-4o", "Claude\n$\\times$Llama"]
    c_l0 = [0.15, 1.00, 0.00]
    c_l3 = [0.60, 1.00, 0.00]
    x2 = np.arange(len(fams2))
    ax.bar(x2 - w / 2, c_l0, w, color="white", edgecolor=GREEN, linewidth=0.9,
           hatch="\\\\\\", label="L0")
    ax.bar(x2 + w / 2, c_l3, w, color=GREEN, edgecolor="black", linewidth=0.5,
           label="L3")
    ax.set_xticks(x2)
    ax.set_xticklabels(fams2, fontsize=6.8)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("A1 cooperation lock-in")
    ax.legend(frameon=False, loc="lower left", fontsize=6.5,
              handletextpad=0.4, ncol=1, columnspacing=0.8,
              bbox_to_anchor=(0.0, 0.30))
    ax.text(1.0, 0.93, "1.00 (all rungs)", ha="center", fontsize=5.8,
            color=GREEN)
    ax.text(2.0, 0.05, "0.00 (all rungs)", ha="center", fontsize=5.8,
            color=VERM)
    ax.set_title("(b) A1 cooperation\nlock-in by family", fontsize=7.5)

    fig.tight_layout()
    return save(fig, "f10_generality.pdf")


# ============================================================================= #
# F11 — M1 detector ROC (AUC=0.88), REAL DATA (data/runs/M1/.../roc_points.csv)
#       + PR/precision inset; default & calibrated operating points marked
# ============================================================================= #
def f11_monitor_roc():
    import json
    roc = pd.read_csv(M1_DIR / "roc_points.csv")
    pr = pd.read_csv(M1_DIR / "pr_points.csv")
    summary = json.loads((M1_DIR / "summary.json").read_text())
    auc = summary["auc_roc"]

    # finite, sorted ROC for the curve
    rc = roc[np.isfinite(roc["threshold"])].sort_values("fpr")

    fig, ax = plt.subplots(figsize=(3.4, 3.0))
    ax.plot([0, 1], [0, 1], ls=":", color=LGRAY, lw=0.9, label="chance")
    ax.plot(rc["fpr"], rc["tpr"], color=BLUE, lw=1.6, marker="o",
            markersize=2.6, label=f"M1 monitor (AUC$={auc:.2f}$)")

    # default operating point (flag threshold 0.5): FPR 0.484 / TPR 0.945
    op = summary["operating_point_at_flag_threshold"]
    ax.plot(op["fpr"], op["tpr"], marker="X", color=VERM, markersize=8,
            markeredgecolor="black", markeredgewidth=0.5, zorder=5,
            linestyle="none", label="default ($\\tau{=}0.5$)")
    ax.annotate(f"default: FPR$={op['fpr']:.2f}$\nflags everything",
                xy=(op["fpr"], op["tpr"]), xytext=(0.50, 0.55),
                fontsize=6.3, color=VERM, ha="left",
                arrowprops=dict(arrowstyle="->", color=VERM, lw=0.8))

    # calibrated point: top budget, score_threshold 0.95 (~15% budget -> use 0.10/0.25)
    # take the 0.95 row from roc_points (FPR 0.113 / TPR 0.833) as the calibrated tau=0.95
    cal = rc[np.isclose(rc["threshold"], 0.95)].iloc[0]
    ax.plot(cal["fpr"], cal["tpr"], marker="D", color=GREEN, markersize=7,
            markeredgecolor="black", markeredgewidth=0.5, zorder=5,
            linestyle="none", label="calibrated ($\\tau{=}0.95$)")
    ax.annotate(f"calibrated\nFPR$={cal['fpr']:.2f}$, TPR$={cal['tpr']:.2f}$",
                xy=(cal["fpr"], cal["tpr"]), xytext=(0.015, 0.66),
                fontsize=6.3, color=GREEN, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.8))

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1.02)
    ax.set_xlabel("False-positive rate")
    ax.set_ylabel("True-positive rate")
    ax.set_title("M1 monitor: discriminative, mis-thresholded")
    ax.legend(frameon=False, loc="lower right", fontsize=6.3)

    # ---- precision-recall inset ----
    iax = ax.inset_axes([0.135, 0.135, 0.36, 0.36])
    prs = pr.sort_values("recall")
    iax.plot(prs["recall"], prs["precision"], color=PURPLE, lw=1.2,
             marker="s", markersize=2.2)
    iax.axhline(summary["calibration"]["base_rate"], ls="--", color=LGRAY,
                lw=0.8)
    iax.set_xlim(0, 1)
    iax.set_ylim(0, 1.0)
    iax.set_xlabel("recall", fontsize=5.5, labelpad=1)
    iax.set_ylabel("precision", fontsize=5.5, labelpad=1)
    iax.tick_params(labelsize=5)
    iax.set_title("PR (base rate $-\\!-$)", fontsize=5.5, pad=2)
    iax.grid(alpha=0.25, lw=0.4)

    fig.tight_layout()
    return save(fig, "f11_monitor_roc.pdf")


# ============================================================================= #
# F12 — M2 governance: per-arm K (flat deterrence) + FP-cost collapse (§10d)
# ============================================================================= #
def f12_m2_governance():
    arms = ["none", "default", "calibrated"]
    K = [0.538, 0.525, 0.564]          # deterrence ~flat
    fp = [None, 1.00, 0.00]            # FP cost: default 1.00 -> calibrated 0.00

    fig, axes = plt.subplots(1, 2, figsize=(6.0, 2.8),
                             gridspec_kw={"width_ratios": [1.0, 1.0]})

    # ---- panel (a): FP-cost collapse (the headline) ----
    ax = axes[0]
    xb = [0, 1]
    ax.bar(xb, [1.00, 0.00], color=[VERM, GREEN], edgecolor="black",
           linewidth=0.5, width=0.55, hatch="xxx")
    ax.set_xticks(xb)
    ax.set_xticklabels(["default\nthreshold", "calibrated\nthreshold"],
                       fontsize=7.5)
    ax.set_ylim(0, 1.18)
    ax.set_ylabel("False-positive cost\n(innocent rounds penalized)")
    ax.set_title("(a) Calibration kills false positives")
    ax.annotate("$1.00 \\to 0.00$\n(27/27 $\\to$ 0/27)", xy=(1, 0.04),
                xytext=(0.5, 0.62), fontsize=7, color=GREEN, ha="center",
                arrowprops=dict(arrowstyle="->", color=GREEN, lw=0.9))

    # ---- panel (b): deterrence ~flat across arms ----
    ax = axes[1]
    x = np.arange(len(arms))
    ax.bar(x, K, color=BLUE, edgecolor="black", linewidth=0.5, width=0.6)
    ax.axhline(np.mean(K), ls="--", color=GRAY, lw=0.9)
    for xi, k in zip(x, K):
        ax.text(xi, k + 0.02, f"{k:.3f}", ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels(arms, fontsize=7.5)
    ax.set_ylim(0, 0.72)
    ax.set_ylabel("Collusion index $K$")
    ax.set_xlabel("Enforcement arm")
    ax.set_title("(b) Deterrence flat ($\\Delta K\\approx 0$)")
    ax.text(1.0, 0.66, "enforcement did NOT deter\n(cell-dependent, cf. B5E)",
            ha="center", fontsize=6.2, color=GRAY)

    fig.tight_layout()
    return save(fig, "f12_m2_governance.pdf")


FIGS = [
    f1_a1_ladder, f2_a1_curve, f3_c1_content, f4_b1_k, f5_a3_origin,
    f6_oversight, f7_generalize, f8_alignment_dose, f9_s2_observability,
    f10_generality, f11_monitor_roc, f12_m2_governance,
]

# venues that also receive a copy of every figure
VENUE_FIGDIRS = [
    ROOT / "gamesec" / "figures",
    ROOT / "arxiv" / "figures",
    ROOT / "neurips_ws" / "figures",
]


def main():
    import shutil
    for fn in FIGS:
        out = fn()
        print(f"wrote {out.relative_to(ROOT)}")
    # mirror the Round-2 figures + the reviewer-revised f4 into each venue dir
    mirrored = ["f4_b1_k.pdf", "f10_generality.pdf", "f11_monitor_roc.pdf",
                "f12_m2_governance.pdf"]
    for vdir in VENUE_FIGDIRS:
        vdir.mkdir(parents=True, exist_ok=True)
        for name in mirrored:
            shutil.copy2(FIGDIR / name, vdir / name)
            print(f"copied {name} -> {(vdir / name).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
