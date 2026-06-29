#!/usr/bin/env python3
"""Analyze the SMS-throughput sweep: the two curves the question asks for,
across however many model pairings are present in results/.

  (1) collusion vs ALLOWED throughput  — lock-in / mutual-HOLD vs SMS credits granted
  (2) collusion vs USED   throughput   — lock-in vs SMS the agents actually sent
  (3) rationing                        — used vs allowed

Plus the headline test: WHERE does collusion turn on, and does the gradient
replicate across pairings? Reads every results/sms_matches*.jsonl; writes
figures/*.png and results/summary.json.
"""
from __future__ import annotations
import json, math, glob
from pathlib import Path
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from scipy.optimize import curve_fit

HERE = Path(__file__).resolve().parent
GOLD, CYAN, CORAL, GREEN, INK, BG = "#c09e5a", "#00d4ff", "#ff6b6b", "#2fd08a", "#f4f1ea", "#0a0a0a"
PAIR_COLORS = [GOLD, CYAN, GREEN, CORAL]


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"),) * 3
    p = k / n
    d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d
    h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return p, max(0, c-h), min(1, c+h)


def load(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def analyze_pair(rows):
    by_c = defaultdict(list)
    for r in rows:
        by_c[r["credits"]].append(r)
    credits = sorted(by_c)
    curve = []
    for c in credits:
        ms = by_c[c]; n = len(ms)
        k = sum(1 for m in ms if m["lock_in"])
        p, lo, hi = wilson(k, n)
        hold = float(np.mean([m["mutual_hold_rate"] for m in ms]))
        used = float(np.mean([m["used_sms"]["A"] + m["used_sms"]["B"] for m in ms]))
        curve.append(dict(credits=c, n=n, k=k, lock_in=p, lo=lo, hi=hi, hold=hold, used=used))
    # turn-on: first credit level significant vs credits==0
    k0 = sum(m["lock_in"] for m in by_c.get(0, []))
    n0 = len(by_c.get(0, []))
    turn_on, fishers = None, []
    for c in credits:
        if c == 0:
            continue
        kc, nc = sum(m["lock_in"] for m in by_c[c]), len(by_c[c])
        _, pval = stats.fisher_exact([[kc, nc-kc], [k0, n0-k0]]) if (n0 and nc) else (0, 1.0)
        fishers.append(dict(credits=c, lock_in=kc/nc, p=pval))
        if turn_on is None and pval < 0.05:
            turn_on = c
    # used-throughput logistic + binned
    used_tot = np.array([r["used_sms"]["A"] + r["used_sms"]["B"] for r in rows], float)
    lock = np.array([1.0 if r["lock_in"] else 0.0 for r in rows])
    def logistic(x, b0, b1):
        return 1.0 / (1.0 + np.exp(-(b0 + b1 * x)))
    try:
        popt, _ = curve_fit(logistic, used_tot, lock, p0=[-2, 0.3], maxfev=10000); fit = list(map(float, popt))
    except Exception:
        fit = None
    edges = [0, 1, 3, 6, 10, 16, 100]; usedc = []
    for a, b in zip(edges[:-1], edges[1:]):
        idx = (used_tot >= a) & (used_tot < b); n = int(idx.sum())
        if n:
            k = int(lock[idx].sum()); p, lo, hi = wilson(k, n)
            usedc.append(dict(mid=float(used_tot[idx].mean()), n=n, lock_in=p, lo=lo, hi=hi))
    # rank correlation: collusion vs throughput (per-match)
    cr = np.array([r["credits"] for r in rows], float)
    rho_allowed = float(stats.spearmanr(cr, [r["mutual_hold_rate"] for r in rows]).correlation)
    rho_used = float(stats.spearmanr(used_tot, [r["mutual_hold_rate"] for r in rows]).correlation)
    return dict(pair=rows[0]["model"], n=len(rows), curve=curve, turn_on=turn_on,
                fishers=fishers, baseline=k0/max(n0, 1), used_curve=usedc,
                logistic=fit, rho_allowed=rho_allowed, rho_used=rho_used,
                used_tot=used_tot.tolist(), lock=lock.tolist())


def main():
    files = sorted(glob.glob(str(HERE / "results" / "sms_matches*.jsonl")))
    pairs = [analyze_pair(load(f)) for f in files]
    print(f"analyzed {len(pairs)} pairing(s)\n")
    for P in pairs:
        print(f"=== {P['pair']}  (n={P['n']}) ===")
        print(f"{'credits':>8}{'lock-in':>9}{'95% CI':>15}{'hold':>7}{'used':>7}")
        for c in P["curve"]:
            print(f"{c['credits']:>8}{c['lock_in']:>9.2f}  [{c['lo']:.2f},{c['hi']:.2f}]{c['hold']:>7.2f}{c['used']:>7.1f}")
        print(f"  turn-on (first sig vs 0 credits): "
              f"{P['turn_on'] if P['turn_on'] else 'never (n.s. at all levels)'}")
        print(f"  Spearman collusion~allowed: rho={P['rho_allowed']:+.2f} | "
              f"collusion~used: rho={P['rho_used']:+.2f}\n")

    plt.rcParams.update({"figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG,
                         "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
                         "ytick.color": INK, "axes.edgecolor": "#444", "font.size": 12})

    def short(name):  # "qwen-72b x llama-70b" -> "Qwen×Llama"
        a, _, b = name.partition(" x ")
        sm = {"qwen-72b": "Qwen", "llama-70b": "Llama", "deepseek-v3": "DeepSeek",
              "mistral-large": "Mistral", "gpt-4o": "GPT-4o"}
        return f"{sm.get(a, a)}×{sm.get(b, b)}"

    # Fig 1: collusion (mutual-HOLD) vs ALLOWED throughput — overlay pairings
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    for i, P in enumerate(pairs):
        col = PAIR_COLORS[i % len(PAIR_COLORS)]
        xs = [c["credits"] for c in P["curve"]]
        ax.plot(xs, [c["hold"] for c in P["curve"]], "-o", color=col, lw=2.4, ms=6,
                label=f"{short(P['pair'])}  (ρ={P['rho_allowed']:+.2f})")
        ax.plot(xs, [c["lock_in"] for c in P["curve"]], ":", color=col, lw=1.3, alpha=0.7)
    ax.plot([], [], "k:", color="#888", label="(dotted = strict lock-in)")
    ax.set_xlabel("ALLOWED throughput  —  SMS credits per agent  (each ≤60 chars)")
    ax.set_ylabel("collusion  (mutual-HOLD rate)")
    ax.set_title("Collusion rises with communication throughput\nrepeated pricing duopoly · per-pair Spearman ρ",
                 fontsize=12)
    ax.set_ylim(-0.03, 1.03); ax.grid(alpha=0.12)
    ax.legend(facecolor="#161616", edgecolor="#333", labelcolor=INK, fontsize=10)
    fig.tight_layout(); fig.savefig(HERE / "figures" / "f1_allowed_throughput.png", dpi=150)

    # Fig 2: collusion vs USED throughput — overlay binned curves
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    for i, P in enumerate(pairs):
        col = PAIR_COLORS[i % len(PAIR_COLORS)]
        uc = P["used_curve"]
        if uc:
            ux = [u["mid"] for u in uc]; uy = [u["lock_in"] for u in uc]
            ulo = [u["lo"] for u in uc]; uhi = [u["hi"] for u in uc]
            ax.errorbar(ux, uy, yerr=[np.array(uy)-np.array(ulo), np.array(uhi)-np.array(uy)],
                        fmt="-o", color=col, ms=7, lw=1.8, capsize=3, label=short(P["pair"]))
    ax.set_xlabel("USED throughput  —  SMS the agents actually sent (both, per match)")
    ax.set_ylabel("collusion  (lock-in, Wilson CI)")
    ax.set_title("Collusion vs the throughput agents actually use", fontsize=12)
    ax.set_ylim(-0.05, 1.05); ax.grid(alpha=0.12)
    ax.legend(facecolor="#161616", edgecolor="#333", labelcolor=INK, fontsize=10)
    fig.tight_layout(); fig.savefig(HERE / "figures" / "f2_used_throughput.png", dpi=150)

    # Fig 3: rationing — used vs allowed
    fig, ax = plt.subplots(figsize=(7.6, 4.8))
    mx = max(c["credits"] for P in pairs for c in P["curve"])
    ax.plot([0, mx], [0, 2*mx], ":", color="#666", label="if every credit were spent")
    for i, P in enumerate(pairs):
        col = PAIR_COLORS[i % len(PAIR_COLORS)]
        xs = [c["credits"] for c in P["curve"]]
        ax.plot(xs, [c["used"] for c in P["curve"]], "-o", color=col, lw=2.2, ms=6, label=short(P["pair"]))
    ax.set_xlabel("ALLOWED throughput (credits per agent)")
    ax.set_ylabel("USED throughput (SMS sent, both agents)")
    ax.set_title("Agents ration the channel: used vs allowed", fontsize=12)
    ax.grid(alpha=0.12); ax.legend(facecolor="#161616", edgecolor="#333", labelcolor=INK, fontsize=10)
    fig.tight_layout(); fig.savefig(HERE / "figures" / "f3_allowed_vs_used.png", dpi=150)

    for P in pairs:  # drop bulky raw arrays from the summary
        P.pop("used_tot", None); P.pop("lock", None)
    (HERE / "results" / "summary.json").write_text(json.dumps(dict(pairings=pairs), indent=2))
    print("wrote figures/f1_allowed_throughput.png, f2_used_throughput.png, "
          "f3_allowed_vs_used.png and results/summary.json")


if __name__ == "__main__":
    main()
