"""Statistical re-analysis / audit for the rival-arena paper.
Pure re-analysis of data already on disk. No experiments, no API spend.
Run: .venv/bin/python scripts/stats_audit.py
"""
import json, glob, os, math
import numpy as np
import pandas as pd
from scipy import stats as sps

np.random.seed(12345)
ROOT = "/home/ubuntu/capstone"

# Canonical TOST helper copied from rival_arena.metrics.stats (avoid heavy import)
def tost_equivalence(a, b, bound, alpha=0.05):
    a = [x for x in a if x is not None]; b = [x for x in b if x is not None]
    na, nb = len(a), len(b)
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    diff = ma - mb
    se = math.sqrt(va/na + vb/nb)
    if se == 0:
        eq = abs(diff) < bound
        return dict(equivalent=eq, p=0.0 if eq else 1.0, p_lower=0.0, p_upper=0.0,
                    mean_diff=diff, bound=bound, n_a=na, n_b=nb, se=0.0, df=na+nb-2)
    dfree = (va/na + vb/nb)**2 / ((va/na)**2/(na-1) + (vb/nb)**2/(nb-1))
    t_lower = (diff + bound)/se; p_lower = float(sps.t.sf(t_lower, dfree))
    t_upper = (diff - bound)/se; p_upper = float(sps.t.cdf(t_upper, dfree))
    p = max(p_lower, p_upper)
    return dict(equivalent=p < alpha, p=p, p_lower=p_lower, p_upper=p_upper,
                mean_diff=diff, bound=bound, n_a=na, n_b=nb, se=se, df=dfree)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k/n; den = 1 + z*z/n
    c = (p + z*z/(2*n))/den
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/den
    return (max(0, c-half), min(1, c+half))

def risk_diff_ci(k1, n1, k2, n2, z=1.96):
    """RD = p1 - p2 with Newcombe (Wilson-based) 95% CI."""
    p1, p2 = k1/n1, k2/n2
    rd = p1 - p2
    l1, u1 = wilson(k1, n1); l2, u2 = wilson(k2, n2)
    lo = rd - math.sqrt((p1-l1)**2 + (u2-p2)**2)
    hi = rd + math.sqrt((u1-p1)**2 + (p2-l2)**2)
    return rd, max(-1, lo), min(1, hi)

OUT = []
def w(s=""):
    OUT.append(s); print(s)

# ----------------------------------------------------------------------------
# Load metrics (pooled) and matches
# ----------------------------------------------------------------------------
def load_metrics(exp):
    rows = []
    for f in glob.glob(f"{ROOT}/data/runs/{exp}/2026*/metrics.csv"):
        df = pd.read_csv(f); df["__run"] = os.path.basename(os.path.dirname(f)); rows.append(df)
    return pd.concat(rows, ignore_index=True)

A1 = load_metrics("A1")
B1 = load_metrics("B1")
A3 = load_metrics("A3")

A1_SPINE_RUN = "20260619T015047"
B1_SPINE_RUN = "20260619T015051"
A3_SPINE_RUN = "20260619T015056"

w("="*80)
w("RUN PROVENANCE")
w("="*80)
w(f"A1 spine  (same_origin_cn, seeds 100-119, n=20): data/runs/A1/{A1_SPINE_RUN}")
w(f"B1 spine  (cross_origin,  seeds 100-119, n=20): data/runs/B1/{B1_SPINE_RUN}")
w(f"A3 origin (seeds 0-9 / 100-109, n=10/cell):     data/runs/A3/{A3_SPINE_RUN}")
w(f"Generality cells (n=12): data/runs/B1/20260620T* and A1/20260620T*")

# ============================================================================
# SECTION 1 — Direct contrast tests for A1 headline contrasts
# ============================================================================
w("\n" + "="*80)
w("SECTION 1 — A1 DIRECT CONTRAST TESTS (Fisher exact + risk difference)")
w("="*80)
a1 = A1[A1.__run == A1_SPINE_RUN]
def lockin_counts(fam, rung):
    g = a1[a1.cell_id == f"A1/{rung}/{fam}/same_origin_cn"]
    return int(g.locked_in.sum()), len(g)

for fam in ["canonical", "novel"]:
    w(f"\n--- {fam} ---")
    rungs = {"L0": "L0_none", "L1": "L1_signal", "L2": "L2_observed"}
    cnt = {k: lockin_counts(fam, v) for k, v in rungs.items()}
    for k, (kk, nn) in cnt.items():
        w(f"  {k}: {kk}/{nn}  lock-in={kk/nn:.3f}  Wilson95=[{wilson(kk,nn)[0]:.3f},{wilson(kk,nn)[1]:.3f}]")
    for hi, lo in [("L1","L0"), ("L2","L0"), ("L2","L1")]:
        kh, nh = cnt[hi]; kl, nl = cnt[lo]
        # 2x2: rows = rung, cols = [locked, not]
        table = [[kh, nh-kh], [kl, nl-kl]]
        odds, p = sps.fisher_exact(table)
        rd, rlo, rhi = risk_diff_ci(kh, nh, kl, nl)
        w(f"  {hi} vs {lo}: {kh}/{nh} vs {kl}/{nl}  Fisher p={p:.4f}  RD={rd:+.3f} [{rlo:+.3f},{rhi:+.3f}]")

# The critical claim: L1 (cheap signal) WORSE than L0 (silence), canonical
w("\n--- CRITICAL: 'cheap menu signal WORSE than silence' (canonical L1 0/20 vs L0 3/20) ---")
kl1, nl1 = lockin_counts("canonical", "L1_signal")
kl0, nl0 = lockin_counts("canonical", "L0_none")
table = [[kl1, nl1-kl1], [kl0, nl0-kl0]]
odds, p_2s = sps.fisher_exact(table)
odds, p_1s = sps.fisher_exact(table, alternative="less")  # L1 < L0
rd, rlo, rhi = risk_diff_ci(kl1, nl1, kl0, nl0)
w(f"  Fisher 2-sided p={p_2s:.4f}; 1-sided (L1<L0) p={p_1s:.4f}")
w(f"  RD(L1-L0) = {rd:+.3f} [{rlo:+.3f},{rhi:+.3f}]  -> CI includes 0: {rlo<=0<=rhi}")
w(f"  VERDICT: difference is {'SIGNIFICANT' if p_2s<0.05 else 'NOT SIGNIFICANT (n.s.)'} at alpha=.05")
# also pooled L1 vs L0 across canonical+novel for power
kl1p = sum(lockin_counts(f,'L1_signal')[0] for f in ['canonical','novel'])
kl0p = sum(lockin_counts(f,'L0_none')[0]  for f in ['canonical','novel'])
np_ = 40
odds, p_pool = sps.fisher_exact([[kl1p,np_-kl1p],[kl0p,np_-kl0p]])
w(f"  Pooled (canon+novel) L1 {kl1p}/40 vs L0 {kl0p}/40: Fisher 2-sided p={p_pool:.4f}")

# ============================================================================
# SECTION 2 — Bootstrap 95% CI for collusion index K (resample matches)
# ============================================================================
w("\n" + "="*80)
w("SECTION 2 — BOOTSTRAP 95% CI FOR COLLUSION INDEX K (>=2000 resamples)")
w("="*80)
NB = 5000
def boot_ci_mean(vals, nb=NB):
    vals = np.asarray(vals, float)
    n = len(vals)
    idx = np.random.randint(0, n, size=(nb, n))
    bs = vals[idx].mean(axis=1)
    return float(vals.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5)), n

def k_vals(df, run, cell):
    g = df[(df.__run == run) & (df.cell_id == cell)]
    return g.K_endstate.dropna().values

w("\n-- B1 SPINE (cross_origin, n=20/cell) --")
spine_K = {}
for rung in ["L0_none","L1_signal","L2_observed","L3_private"]:
    for fam in ["canonical","novel"]:
        cell = f"B1/{rung}/{fam}/cross_origin"
        v = k_vals(B1, B1_SPINE_RUN, cell)
        m, lo, hi, n = boot_ci_mean(v)
        spine_K[(rung,fam)] = (m,lo,hi,n)
        w(f"  {rung:11s} {fam:9s} K={m:+.3f} [{lo:+.3f},{hi:+.3f}] (n={n})")

w("\n-- GENERALITY cells (novel demand, n=12; L0 and L3) --")
gen_cells = {
 "open spine (cross_origin)":  ("cross_origin",   B1_SPINE_RUN, B1_SPINE_RUN),
 "GPT-4o self (frontier_self)":("frontier_self",  "20260620T132236","20260620T132236"),
 "GPT-4o x open (frontier_gpt_open)":("frontier_gpt_open","20260620T200544","20260620T200544"),
 "Claude self (claude_self)":  ("claude_self",    "20260620T213527","20260620T213527"),
 "Claude x Llama (claude_open)":("claude_open",    "20260620T214122","20260620T214122"),
 "family2 self":               ("family2_self",   "20260620T134841","20260620T134841"),
 "family2 open":               ("family2_open",   "20260620T201530","20260620T201530"),
}
gen_K = {}
for label,(tag,run0,run3) in gen_cells.items():
    v0 = k_vals(B1, run0, f"B1/L0_none/novel/{tag}")
    v3 = k_vals(B1, run3, f"B1/L3_private/novel/{tag}")
    m0,l0,h0,n0 = boot_ci_mean(v0); m3,l3,h3,n3 = boot_ci_mean(v3)
    gen_K[label] = (m0,l0,h0,n0,m3,l3,h3,n3)
    w(f"  {label:34s} L0 K={m0:+.3f}[{l0:+.3f},{h0:+.3f}](n={n0})  L3 K={m3:+.3f}[{l3:+.3f},{h3:+.3f}](n={n3})")

# L3 vs L0 channel contrast on the B1 spine (novel; the principal-harming contrast)
w("\n-- L3 vs L0 channel contrast (B1 spine, paired by seed; perm + bootstrap) --")
for fam in ["canonical","novel"]:
    v0 = k_vals(B1, B1_SPINE_RUN, f"B1/L0_none/{fam}/cross_origin")
    v3 = k_vals(B1, B1_SPINE_RUN, f"B1/L3_private/{fam}/cross_origin")
    # bootstrap of the difference of means (independent resample)
    n0,n3=len(v0),len(v3)
    bs = np.random.choice(v3,(NB,n3)).mean(1) - np.random.choice(v0,(NB,n0)).mean(1)
    d = v3.mean()-v0.mean()
    lo,hi = np.percentile(bs,[2.5,97.5])
    u,pmw = sps.mannwhitneyu(v3,v0,alternative="greater")
    w(f"  {fam}: K(L3)-K(L0)={d:+.3f} boot95=[{lo:+.3f},{hi:+.3f}]  Mann-Whitney(L3>L0) p={pmw:.4f}")

# ============================================================================
# SECTION 3 — Lock-in threshold sensitivity (A1, L0 -> L2)
# ============================================================================
w("\n" + "="*80)
w("SECTION 3 — A1 LOCK-IN THRESHOLD SENSITIVITY (L0 -> L2)")
w("="*80)
# Need per-match mean cooperation. metrics.coop_endstate is end-state; we want match mean C.
# Compute match-mean cooperation from rounds_long of the spine run.
rl = pd.read_csv(f"{ROOT}/data/runs/A1/{A1_SPINE_RUN}/rounds_long.csv")
rl = rl[rl.cell_id.str.contains("same_origin_cn")]
# cooperative is per seat per round; match mean coop = mean over both seats & rounds
def match_meanC(cell):
    g = rl[rl.cell_id == cell]
    # mean cooperative per (seed) across all rows
    return g.groupby("seed")["cooperative"].mean()

w("\nMatch-mean cooperation C per match -> lock-in under thresholds:")
w(f"{'metric':<22}{'L0 canon':>12}{'L2 canon':>12}{'L0 novel':>12}{'L2 novel':>12}")
res = {}
for thr_label, thr in [("C>0.7",0.7),("C>0.8",0.8),("C>0.9",0.9)]:
    row = [thr_label]
    for fam in ["canonical","novel"]:
        c0 = match_meanC(f"A1/L0_none/{fam}/same_origin_cn")
        c2 = match_meanC(f"A1/L2_observed/{fam}/same_origin_cn")
        p0 = (c0 > thr).mean(); p2 = (c2 > thr).mean()
        res[(thr_label,fam)] = (p0,p2,len(c0),len(c2))
    w(f"{thr_label:<22}{res[(thr_label,'canonical')][0]:>12.3f}{res[(thr_label,'canonical')][1]:>12.3f}{res[(thr_label,'novel')][0]:>12.3f}{res[(thr_label,'novel')][1]:>12.3f}")
# mean cooperation
mc = {}
for fam in ["canonical","novel"]:
    c0 = match_meanC(f"A1/L0_none/{fam}/same_origin_cn"); c2 = match_meanC(f"A1/L2_observed/{fam}/same_origin_cn")
    mc[fam]=(c0.mean(),c2.mean())
w(f"{'mean C':<22}{mc['canonical'][0]:>12.3f}{mc['canonical'][1]:>12.3f}{mc['novel'][0]:>12.3f}{mc['novel'][1]:>12.3f}")

# direction + test at each threshold (canonical, Fisher)
w("\nL0->L2 effect (canonical) Fisher exact + risk diff at each threshold:")
for thr_label,thr in [("C>0.7",0.7),("C>0.8",0.8),("C>0.9",0.9)]:
    c0 = match_meanC("A1/L0_none/canonical/same_origin_cn"); c2 = match_meanC("A1/L2_observed/canonical/same_origin_cn")
    k0=int((c0>thr).sum()); k2=int((c2>thr).sum()); n0=len(c0); n2=len(c2)
    odds,p = sps.fisher_exact([[k2,n2-k2],[k0,n0-k0]])
    rd,rlo,rhi=risk_diff_ci(k2,n2,k0,n0)
    w(f"  {thr_label}: L2 {k2}/{n2} vs L0 {k0}/{n0}  Fisher p={p:.4f}  RD={rd:+.3f}[{rlo:+.3f},{rhi:+.3f}]")

# time-to-first-lock-in: first round at which a 3-round trailing mean coop > 0.8 sustained
w("\nTime-to-first-sustained-cooperation (first round where remaining-match mean C>0.8), canonical:")
def time_to_lock(cell):
    g = rl[rl.cell_id==cell]
    times=[]
    for seed,sg in g.groupby("seed"):
        # per-round mean coop across both seats
        per = sg.groupby("round_index")["cooperative"].mean().sort_index()
        t=np.nan
        rounds=per.index.tolist()
        for i,r in enumerate(rounds):
            if per.iloc[i:].mean()>0.8:
                t=r; break
        times.append(t)
    times=pd.Series(times)
    return times
for fam in ["canonical","novel"]:
    for rung in ["L0_none","L2_observed"]:
        t=time_to_lock(f"A1/{rung}/{fam}/same_origin_cn")
        locked=t.notna().sum()
        med = np.nanmedian(t.values) if locked>0 else float('nan')
        w(f"  {fam:9s} {rung:11s}: {locked}/{len(t)} matches ever lock; median first-lock round={med}")

# ============================================================================
# SECTION 4 — TOST equivalence for A3 origin null
# ============================================================================
w("\n" + "="*80)
w("SECTION 4 — A3 ORIGIN NULL: TOST EQUIVALENCE (channel-effect-slope difference)")
w("="*80)
a3 = A3[A3.__run == A3_SPINE_RUN]
# Define groups: same-origin = {same_origin_cn, same_origin_west, same_family}; cross-origin = {cross_origin, cross_origin_2}
SAME = ["same_origin_cn","same_origin_west","same_family"]
CROSS = ["cross_origin","cross_origin_2"]
# Channel effect = per-match coop_endstate at channel rung minus the group-mean at L0 (the slope).
# Cleaner powered null per prereg: difference in the CHANNEL EFFECT (L2/L3 lock-in or coop minus L0)
# We compute, per pair-cell, the channel effect = mean coop at {L2,L3} - mean coop at {L0,L1}, then
# TOST the SAME vs CROSS distributions of that per-pair-per-seed channel effect.
def channel_effect_series(pairtag):
    """per-seed channel effect = mean coop_endstate over high rungs (L2,L3) minus low rungs (L0,L1)."""
    g = a3[a3.cell_id.str.contains(f"/{pairtag}$")]
    hi = g[g.cell_id.str.contains("L2_observed|L3_private")].groupby("seed")["coop_endstate"].mean()
    lo = g[g.cell_id.str.contains("L0_none|L1_signal")].groupby("seed")["coop_endstate"].mean()
    j = (hi - lo).dropna()
    return j

same_eff=[]; cross_eff=[]
for t in SAME: same_eff.extend(channel_effect_series(t).values)
for t in CROSS: cross_eff.extend(channel_effect_series(t).values)
same_eff=np.array(same_eff); cross_eff=np.array(cross_eff)
w(f"\nPer-pair-per-seed channel effect (mean coop L2/L3 - L0/L1):")
w(f"  SAME-origin pairs ({'+'.join(SAME)}): mean={same_eff.mean():.3f} sd={same_eff.std(ddof=1):.3f} n={len(same_eff)}")
w(f"  CROSS-origin pairs ({'+'.join(CROSS)}): mean={cross_eff.mean():.3f} sd={cross_eff.std(ddof=1):.3f} n={len(cross_eff)}")
diff = same_eff.mean()-cross_eff.mean()
# Welch t for the difference (the moderation effect)
tt = sps.ttest_ind(same_eff, cross_eff, equal_var=False)
w(f"  Observed moderation (same-cross) = {diff:+.3f}; Welch t p={tt.pvalue:.4f} (NHST: any difference?)")
# pooled SD for bound choice
pooled_sd = math.sqrt(((len(same_eff)-1)*same_eff.var(ddof=1)+(len(cross_eff)-1)*cross_eff.var(ddof=1))/(len(same_eff)+len(cross_eff)-2))
w(f"  pooled SD of channel-effect = {pooled_sd:.3f}")
for d_label,bound in [("0.5*SD (small)",0.5*pooled_sd),("0.8*SD (medium)",0.8*pooled_sd),("abs 0.20",0.20),("abs 0.25",0.25)]:
    r = tost_equivalence(same_eff, cross_eff, bound)
    w(f"  TOST bound=±{bound:.3f} [{d_label}]: mean_diff={r['mean_diff']:+.3f} p_lower={r['p_lower']:.4f} p_upper={r['p_upper']:.4f} p_TOST={r['p']:.4f} -> EQUIVALENT={r['equivalent']}")

# Power: with this n, what min detectable difference would TOST rule out? report achieved n
w(f"\n  n_same={len(same_eff)}, n_cross={len(cross_eff)}. Equivalence declared iff p_TOST<0.05 at the bound.")

# ============================================================================
# SECTION 5 — Tacit-collusion diagnostic (B1 L0 NO-channel cells)
# ============================================================================
w("\n" + "="*80)
w("SECTION 5 — TACIT-COLLUSION DIAGNOSTIC (B1 L0, no channel)")
w("="*80)
# For each L0 no-channel cell: cross-agent price co-movement, convergence of |pA-pB|, immediate vs emergent.
def price_panel(run, cell):
    g = pd.read_csv(f"{ROOT}/data/runs/{run}").pipe(lambda d:d) if False else None
def load_rounds(run):
    return pd.read_csv(f"{ROOT}/data/runs/B1/{run}/rounds_long.csv")

cells_to_test = {
 "Claude self (K=1.29)": ("20260620T213527","B1/L0_none/novel/claude_self"),
 "Claude x Llama (K=0.92)": ("20260620T214122","B1/L0_none/novel/claude_open"),
 "GPT-4o self (K=0.19)": ("20260620T132236","B1/L0_none/novel/frontier_self"),
 "open spine (K=0.11)": (B1_SPINE_RUN,"B1/L0_none/novel/cross_origin"),
 "family2 self (K=0.96)": ("20260620T134841","B1/L0_none/novel/family2_self"),
}
# competitive & monopoly price benchmarks: read from matches.jsonl benchmarks if present
def get_benchmarks(run, cell):
    path=f"{ROOT}/data/runs/B1/{run}/matches.jsonl"
    for line in open(path):
        m=json.loads(line)
        if m["spec"]["cell_id"]==cell:
            return m["spec"].get("game",{}), m.get("manifest",{}).get("benchmarks") or m["manifest"].get("benchmarks") if isinstance(m.get("manifest"),dict) else None
    return None,None

w("\nPer-cell price-coordination signatures (novel Bertrand, n matches):")
w(f"{'cell':<26}{'r1 |pA-pB|':>12}{'rLast|pA-pB|':>13}{'converge?':>11}{'corr(pA,pB)':>13}{'r1 mean p':>11}{'rLast mean p':>13}")
sec5_rows={}
for label,(run,cell) in cells_to_test.items():
    rl5 = load_rounds(run)
    g = rl5[rl5.cell_id==cell].copy()
    # pivot price by seat per seed per round
    # rows have seat A/B with price + price_other; use 'price' per seat
    piv = g.pivot_table(index=["seed","round_index"], columns="seat", values="price")
    piv = piv.dropna()
    piv["absdiff"]=(piv["A"]-piv["B"]).abs()
    # within-match across-round correlation of pA,pB, averaged over matches
    corrs=[]
    slopes=[]  # trend of |pA-pB| over rounds (negative => convergence)
    for seed,sg in g.groupby("seed"):
        p=sg.pivot_table(index="round_index",columns="seat",values="price").dropna()
        if len(p)>=3 and p["A"].std()>0 and p["B"].std()>0:
            corrs.append(np.corrcoef(p["A"],p["B"])[0,1])
        if len(p)>=3:
            ad=(p["A"]-p["B"]).abs().values
            x=np.arange(len(ad))
            sl=np.polyfit(x,ad,1)[0]
            slopes.append(sl)
    # round-1 vs last-round stats across matches
    r1 = piv.xs(0, level="round_index") if 0 in piv.index.get_level_values("round_index") else piv[piv.index.get_level_values("round_index")==piv.index.get_level_values("round_index").min()]
    maxr = g.round_index.max()
    rL = piv[piv.index.get_level_values("round_index")==maxr]
    r1_absdiff = r1["absdiff"].mean()
    rL_absdiff = rL["absdiff"].mean()
    r1_meanp = (r1["A"].mean()+r1["B"].mean())/2
    rL_meanp = (rL["A"].mean()+rL["B"].mean())/2
    mean_corr = np.nanmean(corrs) if corrs else float('nan')
    mean_slope = np.nanmean(slopes) if slopes else float('nan')
    converge = "yes" if (rL_absdiff < r1_absdiff and mean_slope < 0) else "no"
    sec5_rows[label]=dict(r1_absdiff=r1_absdiff,rL_absdiff=rL_absdiff,mean_corr=mean_corr,
                          mean_slope=mean_slope,r1_meanp=r1_meanp,rL_meanp=rL_meanp,
                          nmatch=g.seed.nunique())
    w(f"{label:<26}{r1_absdiff:>12.2f}{rL_absdiff:>13.2f}{converge:>11}{mean_corr:>13.3f}{r1_meanp:>11.2f}{rL_meanp:>13.2f}")

# For Claude self specifically: immediate-vs-emergent. Compare K_series round-1 region to end.
w("\nClaude-self detail (the K=1.29 cell): is supracompetitive price present from round 1?")
run,cell="20260620T213527","B1/L0_none/novel/claude_self"
# competitive & monopoly: derive from K_endstate and price. K=(p-pc)/(pm-pc). We have K_series in matches.
path=f"{ROOT}/data/runs/B1/{run}/matches.jsonl"
kser=[]
for line in open(path):
    m=json.loads(line)
    if m["spec"]["cell_id"]==cell:
        ks=m["metrics"].get("K_series")
        if ks: kser.append(ks)
if kser:
    L=min(len(k) for k in kser)
    arr=np.array([k[:L] for k in kser])
    w(f"  n matches with K_series={len(kser)}, rounds={L}")
    w(f"  mean K by round: r1={arr[:,0].mean():+.3f}  r2={arr[:,1].mean():+.3f}  r_mid={arr[:,L//2].mean():+.3f}  r_last={arr[:,-1].mean():+.3f}")
    w(f"  -> supracompetitive (K>0) at round 1 in {(arr[:,0]>0).mean()*100:.0f}% of matches; at last round {(arr[:,-1]>0).mean()*100:.0f}%")
    # trend test: does K rise over rounds (emergent coordination) or flat-high (immediate)?
    slopes=[np.polyfit(np.arange(L),row,1)[0] for row in arr]
    w(f"  per-match K slope over rounds: mean={np.mean(slopes):+.4f} (positive=>builds up; ~0=>immediate)")
    ts=sps.wilcoxon(slopes) if len(slopes)>1 else None
    if ts: w(f"  Wilcoxon slope!=0: p={ts.pvalue:.4f}")

w("\nINTERPRETATION KEY:")
w("  coordination signature = (a) high cross-agent price corr AND (b) convergence (|pA-pB| shrinks) AND/OR (c) K rises over rounds.")
w("  independent supracompetitive = high price from r1, no convergence trend, low/!+ correlation.")

# ----------------------------------------------------------------------------
# write raw text dump for reference
with open(f"{ROOT}/data/runs/_program/stats_audit_raw.txt","w") as f:
    f.write("\n".join(OUT))
print("\n[done]")
