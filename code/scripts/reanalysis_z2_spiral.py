#!/usr/bin/env python3
"""Z2 re-analysis #1: Spiral / unrecoverability test (EXPLORATORY, zero API spend).

Question: once a pair *defects*, does mutual cooperation come back, or is a defection
effectively an absorbing lock-out for the rest of the match?

Operationalizations (channel-stratified L0..L3, IPD, on A1 rounds_long.csv):
  (a) Recovery-after-first-mutual-defection: of matches that (i) had >=1 mutual-coop
      round AND (ii) later hit a first mutual-defection, what fraction EVER return to
      a mutual-coop round afterwards?  (1 - that) = "never-recovers" fraction.
  (b) P(mutual cooperation at t+k | first mutual defection at t), the recovery curve.
  (c) For contrast, the same conditioned on a UNILATERAL first defection (one seat
      defects) -> is a single defection already absorbing, or only mutual breakdown?

Match = (cell_id, seed). Two seats (A,B) per round. We reconstruct the joint state.
"""
import sys
import pandas as pd
import numpy as np

RUN = sys.argv[1] if len(sys.argv) > 1 else "data/runs/A1/20260619T015047"
CSV = f"{RUN}/rounds_long.csv"

df = pd.read_csv(CSV)
df["match"] = df.cell_id + "|" + df.seed.astype(str)

# joint per-round state
piv = df.pivot_table(index=["match", "channel", "familiarity", "round_index"],
                     columns="seat", values="cooperative", aggfunc="first").reset_index()
piv = piv.sort_values(["match", "round_index"])
piv["mutual_coop"] = ((piv["A"] == 1) & (piv["B"] == 1)).astype(int)
piv["mutual_def"]  = ((piv["A"] == 0) & (piv["B"] == 0)).astype(int)
piv["any_def"]     = ((piv["A"] == 0) | (piv["B"] == 0)).astype(int)  # >=1 defector

CHANNELS = ["L0_none", "L1_signal", "L2_observed", "L3_private"]


def analyse(sub, label):
    """sub: rows for one (channel,familiarity) stratum."""
    out = {}
    matches = list(sub.groupby("match"))
    # --- (a) recovery after first MUTUAL defection (only matches that ever cooperated mutually) ---
    n_eligible = 0      # had a mutual-coop round AND a later first mutual-def
    n_recover = 0       # returned to mutual-coop after that first mutual-def
    # --- (c) recovery after first ANY (unilateral or mutual) defection, among matches that started w/ mutual coop ---
    n_elig_any = 0
    n_recover_any = 0
    # --- (b) curve store: list of arrays of mutual_coop indexed by k after first mutual-def ---
    curve_hits = {}   # k -> count mutual_coop
    curve_tot = {}    # k -> count rounds observed at offset k
    for m, g in matches:
        g = g.sort_values("round_index").reset_index(drop=True)
        mc = g["mutual_coop"].values
        md = g["mutual_def"].values
        ad = g["any_def"].values
        T = len(g)
        # (a)/(b): first mutual-def that occurs AFTER at least one mutual-coop round
        had_mc_before = False
        first_md = None
        for i in range(T):
            if mc[i] == 1:
                had_mc_before = True
            if md[i] == 1 and had_mc_before:
                first_md = i
                break
        if first_md is not None:
            n_eligible += 1
            after = mc[first_md + 1:]
            if after.sum() > 0:
                n_recover += 1
            for k in range(1, T - first_md):
                curve_tot[k] = curve_tot.get(k, 0) + 1
                curve_hits[k] = curve_hits.get(k, 0) + int(mc[first_md + k])
        # (c): first ANY defection after a mutual-coop opening run
        if mc[0] == 1 or (T > 0 and mc[:1].sum() > 0):
            # match where round 0 was mutual coop -> a "cooperative start"
            if mc[0] == 1:
                first_ad = None
                for i in range(T):
                    if ad[i] == 1:
                        first_ad = i
                        break
                if first_ad is not None:
                    n_elig_any += 1
                    after = mc[first_ad + 1:]
                    if after.sum() > 0:
                        n_recover_any += 1
    out["n_matches"] = len(matches)
    out["n_eligible_mutdef"] = n_eligible
    out["recover_after_mutdef"] = (n_recover / n_eligible) if n_eligible else float("nan")
    out["never_recover_after_mutdef"] = (1 - n_recover / n_eligible) if n_eligible else float("nan")
    out["n_elig_anydef_from_coopstart"] = n_elig_any
    out["recover_after_anydef"] = (n_recover_any / n_elig_any) if n_elig_any else float("nan")
    out["curve"] = {k: (curve_hits.get(k, 0), curve_tot.get(k, 0)) for k in sorted(curve_tot)}
    return out


print("=" * 78)
print(f"SPIRAL / UNRECOVERABILITY  —  {CSV}")
print("IPD; match=(cell_id,seed); joint state from both seats. EXPLORATORY.")
print("=" * 78)

for fam in ["canonical", "novel"]:
    print(f"\n########## familiarity = {fam} ##########")
    for ch in CHANNELS:
        sub = piv[(piv.channel == ch) & (piv.familiarity == fam)]
        if sub.empty:
            continue
        r = analyse(sub, ch)
        print(f"\n[{ch}]  n_matches={r['n_matches']}")
        print(f"  matches w/ a mutual-def AFTER a mutual-coop round (eligible): {r['n_eligible_mutdef']}")
        print(f"  P(EVER return to mutual-coop | first mutual-def):  {r['recover_after_mutdef']:.3f}"
              if r['n_eligible_mutdef'] else "  (none eligible)")
        print(f"  => NEVER-RECOVER fraction:                          {r['never_recover_after_mutdef']:.3f}"
              if r['n_eligible_mutdef'] else "")
        print(f"  matches w/ mutual-coop START that later see ANY defection: {r['n_elig_anydef_from_coopstart']}")
        if r['n_elig_anydef_from_coopstart']:
            print(f"  P(EVER return to mutual-coop | first ANY-defection): {r['recover_after_anydef']:.3f}")
        # recovery curve P(mutual_coop at t+k | first mutual-def at t)
        cur = r["curve"]
        if cur:
            ks = [k for k in (1, 2, 3, 5, 8, 10) if k in cur]
            cells = []
            for k in ks:
                h, t = cur[k]
                cells.append(f"k={k}:{h}/{t}={h/t:.2f}" if t else f"k={k}:-")
            print("  P(mutual-coop at t+k | first mutual-def at t):  " + "  ".join(cells))

# ---- pooled L2+L3 (channel-on) vs L0 (channel-off) summary, canonical ----
print("\n" + "=" * 78)
print("POOLED SUMMARY (canonical): never-recover after first mutual-def")
print("=" * 78)
for grp, chs in [("L0 (no channel)", ["L0_none"]),
                 ("L1 (signal)", ["L1_signal"]),
                 ("L2+L3 (free-text on)", ["L2_observed", "L3_private"])]:
    sub = piv[(piv.channel.isin(chs)) & (piv.familiarity == "canonical")]
    r = analyse(sub, grp)
    nr = r["never_recover_after_mutdef"]
    print(f"  {grp:24s} eligible={r['n_eligible_mutdef']:3d}  never-recover={nr:.3f}"
          if r['n_eligible_mutdef'] else f"  {grp:24s} none eligible")
