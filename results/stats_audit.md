# STATISTICAL AUDIT — direct tests, uncertainty, sensitivity, equivalence, coordination diagnostic

**Purpose.** A peer reviewer flagged five gaps: (1) per-cell interval overlap reported in
place of direct contrast tests; (2) no uncertainty on the collusion index K; (3) no
threshold-sensitivity for the lock-in metric; (4) under-reported TOST equivalence for the
A3 origin null; (5) "tacit collusion" used without a coordination diagnostic. This document
fixes all five **by re-analysing data already on disk** — no new experiments, no API spend.
Every number is recomputed from the raw run files; the generating script is
`scripts/stats_audit.py` (raw dump: `data/runs/_program/stats_audit_raw.txt`).

**Provenance of the confirmatory cells (recomputed, match `docs/paper_facts.md`):**

| spine | run dir | cell tag | seeds | n/cell |
|---|---|---|---|---|
| A1 (IPD, channel→cooperation) | `data/runs/A1/20260619T015047` | `same_origin_cn` | 100–119 | 20 |
| B1 (Bertrand, channel→collusion) | `data/runs/B1/20260619T015051` | `cross_origin` | 100–119 | 20 |
| A3 (origin moderation) | `data/runs/A3/20260619T015056` | same/cross origin pairs | 0–9 | 10 |
| Generality (B1 novel L0/L3) | `data/runs/B1/20260620T*` | frontier_self, claude_self, claude_open, family2_*, frontier_gpt_open | 0–11 | 12 |

Recomputed A1 spine lock-in (matches the paper exactly): L0 3/20=0.15, L1 0/20=0.00,
L2 12/20=0.60 (canon) / 8/20=0.40 (novel), L3 12/20=0.60 / 6/20=0.30.
Recomputed B1 spine K: L0 −0.355, L1 −0.640, L2 0.694, L3 1.229 (canonical) — matches the paper.

---

## 1. Direct contrast tests for the A1 headline contrasts (Fisher exact + risk difference)

Lock-in is a match-level binary (mean cooperation C>0.8). Fisher's exact test on the 2×2
(rung × locked), risk difference (RD) with Newcombe 95% CI. n=20 per cell.

### Canonical (familiar payoffs)
| contrast | counts | Fisher p (2-sided) | RD [95% CI] | verdict |
|---|---|---|---|---|
| L1 vs L0 | 0/20 vs 3/20 | **0.231** | −0.150 [−0.360, +0.038] | **n.s.** |
| L2 vs L0 | 12/20 vs 3/20 | **0.0079** | +0.450 [+0.150, +0.656] | significant |
| L2 vs L1 | 12/20 vs 0/20 | **3e-5** | +0.600 [+0.333, +0.781] | significant |

### Novel (anti-memorization payoffs)
| contrast | counts | Fisher p (2-sided) | RD [95% CI] | verdict |
|---|---|---|---|---|
| L1 vs L0 | 0/20 vs 3/20 | **0.231** | −0.150 [−0.360, +0.038] | **n.s.** |
| L2 vs L0 | 8/20 vs 3/20 | **0.155** | +0.250 [−0.028, +0.485] | n.s. |
| L2 vs L1 | 8/20 vs 0/20 | **0.0033** | +0.400 [+0.158, +0.613] | significant |

### CRITICAL: "cheap menu signal is WORSE than silence" (canonical L1 0/20 vs L0 3/20)
- Fisher exact **2-sided p = 0.231**; 1-sided (L1<L0) p = 0.115.
- RD(L1−L0) = **−0.150, 95% CI [−0.360, +0.038]** — the CI **includes 0**.
- **VERDICT: NOT statistically supported as stated.** The point estimate is in the predicted
  direction (signal collapses lock-in below silence), but with 0/20 vs 3/20 the test is
  under-powered and n.s. **The claim must be softened.**
- Pooled across canonical+novel (L1 0/40 vs L0 6/40) reaches **p = 0.026** — so the
  *direction* ("signal does not help, and trends below silence") is defensible when pooled,
  but the bald per-cell "worse than silence" is not.
- The unambiguous, fully significant fact is **L2 (free-text) ≫ L1 (signal)**: canonical
  RD +0.60 [+0.33, +0.78], p=3e-5; novel RD +0.40 [+0.16, +0.61], p=0.003. Lead with this.

---

## 2. Bootstrap 95% CIs for the collusion index K (resampling matches, 5000 resamples)

CIs are percentile bootstrap over match-level `K_endstate`, resampling matches within cell.

### B1 spine (cross_origin), n=20/cell
| rung | canonical K [95% CI] | novel K [95% CI] |
|---|---|---|
| L0 none | −0.355 [−0.558, −0.135] | +0.105 [+0.049, +0.172] |
| L1 signal | −0.640 [−0.813, −0.445] | +0.035 [+0.007, +0.067] |
| L2 free-text | +0.694 [+0.512, +0.904] | +0.427 [+0.330, +0.530] |
| L3 private | +1.229 [+0.949, +1.539] | +0.380 [+0.282, +0.488] |

The supra-monopoly cell (canonical L3) has a CI **entirely above 1.0** [0.95, 1.54] — K>1 is
real, not a point artefact. L0/L1 canonical CIs are entirely **below 0** (genuine price war).

### Generality cells (novel demand, n=12; L0 vs L3)
| pair (family) | L0 K [95% CI] | L3 K [95% CI] |
|---|---|---|
| open spine (cross_origin, n=20) | +0.105 [+0.051, +0.171] | +0.380 [+0.280, +0.485] |
| GPT-4o self | +0.192 [+0.076, +0.310] | +0.810 [+0.714, +0.917] |
| GPT-4o × open | +0.244 [+0.111, +0.390] | +0.692 [+0.570, +0.805] |
| **Claude self** | **+1.286 [+1.286, +1.286]** | **+1.286 [+1.286, +1.286]** |
| Claude × Llama | +0.917 [+0.832, +0.992] | +0.989 [+0.900, +1.076] |
| family2 self | +0.956 [+0.829, +1.081] | +0.988 [+0.905, +1.060] |
| family2 open | +0.593 [+0.494, +0.698] | +0.593 [+0.527, +0.661] |

The **Claude-self CI is degenerate [1.286, 1.286]** — zero variance, K is identical in all 12
matches. That is itself the diagnostic flag investigated in §5: a degenerate-high K with no
spread is not what dynamic collusion looks like.

### L3-vs-L0 channel contrast (B1 spine)
| demand | K(L3)−K(L0) [bootstrap 95% CI] | Mann–Whitney (L3>L0) |
|---|---|---|
| canonical | +1.584 [+1.217, +1.974] | p = 4e-7 |
| novel | +0.274 [+0.158, +0.395] | p = 2e-4 |

The channel raises K on the open spine: **strongly supported** on both demand curves.

---

## 3. Lock-in threshold sensitivity (A1, L0→L2)

Match-mean cooperation C recomputed per match from `rounds_long.csv` (both seats, all rounds),
then thresholded. n=20/cell.

| metric | L0 canon | L2 canon | L0 novel | L2 novel |
|---|---|---|---|---|
| lock-in C>0.7 | 0.200 | 0.700 | 0.250 | 0.600 |
| lock-in C>0.8 | 0.100 | 0.600 | 0.250 | 0.550 |
| lock-in C>0.9 | 0.100 | 0.550 | 0.150 | 0.450 |
| mean C | 0.432 | 0.791 | 0.455 | 0.725 |

> Note: the canonical L0 lock-in at C>0.8 here is 0.10 (match-mean over all rounds), vs 0.15 in
> the headline (which uses `coop_endstate`, an end-state metric). The L0→L2 **effect direction**
> is what matters and it is invariant to that choice.

**L0→L2 effect (canonical), Fisher exact at each threshold:**
| threshold | L2 vs L0 | Fisher p | RD [95% CI] |
|---|---|---|---|
| C>0.7 | 14/20 vs 4/20 | 0.0036 | +0.500 [+0.192, +0.695] |
| C>0.8 | 12/20 vs 2/20 | 0.0022 | +0.500 [+0.207, +0.695] |
| C>0.9 | 11/20 vs 2/20 | 0.0057 | +0.450 [+0.161, +0.655] |

**The L0→L2 cooperation effect survives every threshold (0.7/0.8/0.9) and on the continuous
mean C (+0.36 canon, +0.27 novel). It is not an artefact of the 0.8 cut.**

**Time-to-first-sustained-cooperation** (first round from which the remaining-match mean C>0.8):
canonical L0 = 5/20 matches ever lock (median first-lock round 4); canonical L2 = 13/20 ever
lock (median round 0, i.e. cooperative essentially from the start). The channel both raises the
lock-in rate and brings it forward.

---

## 4. TOST equivalence for the A3 origin null (the powered moderation null)

Per the prereg (`prereg/a3.md`), the powered null is **moderation**: "origin does not measurably
change how strongly the channel works." Operationalised as the per-pair-per-seed **channel
effect** = (mean coop at L2/L3) − (mean coop at L0/L1), compared between same-origin pairs
{same_origin_cn, same_origin_west, same_family} and cross-origin pairs {cross_origin,
cross_origin_2}. TOST = two one-sided Welch t-tests (canonical helper
`rival_arena.metrics.stats.tost_equivalence`).

- SAME-origin channel effect: mean **0.688**, sd 0.271, n=30.
- CROSS-origin channel effect: mean **0.517**, sd 0.376, n=20.
- Observed moderation (same − cross) = **+0.171**; Welch NHST p = 0.090 (no significant
  moderation — consistent with "origin is a weak axis").
- pooled SD of the channel effect = 0.317.

| equivalence bound ±δ | bound value | p_lower | p_upper | p_TOST | equivalent? |
|---|---|---|---|---|---|
| 0.5·SD (small) | ±0.158 | 0.0010 | 0.551 | **0.551** | NO |
| abs 0.20 | ±0.200 | 0.0003 | 0.384 | **0.384** | NO |
| abs 0.25 | ±0.250 | 0.0001 | 0.211 | **0.211** | NO |
| 0.8·SD (medium) | ±0.253 | 0.0001 | 0.202 | **0.202** | NO |

**REPORT HONESTLY: a clean TOST does not pass at any defensible small/medium bound.** The
upper one-sided test (diff < +δ) fails because the point estimate (+0.171) sits close to the
bound and n is small (10/cell, 20–30 pooled). The data **cannot** earn a tight equivalence
claim. What the data *do* support: (a) **no significant moderation** (NHST p=0.090), and (b)
the channel effect is large and same-signed in **both** groups (0.69 vs 0.52). The honest
wording is the one already in the prereg: *"within these four models, in English, with this
scaffold, origin is a weaker driver than the channel"* — framed as a **non-significant,
under-powered moderation**, NOT a passed equivalence test. Do not claim "origin doesn't matter"
or "TOST-equivalent"; claim "the moderation is small and not statistically distinguishable from
zero, but our n cannot rule out a moderate effect."

> Variance note: most of the cross-origin spread is driven by `cross_origin_2` (a DeepSeek-bearing
> pair) collapsing at L2/L3 (lock-in 0.10) while the other pairs reach ≈0.9 — consistent with the
> paper's "within-group spread > between-group, driven by individual model cooperability, not
> nationality."

---

## 5. Tacit-collusion diagnostic (B1 L0, no channel) — the key new analysis

For the no-channel (L0) Bertrand cells we test whether two agents' prices **co-move / converge**
over rounds (a coordination signature requiring mutual adjustment) versus being **independently
high from round 1**. With **no communication channel**, any "agreement" can only be tacit
coordination through observed price moves — so the trajectory shape is decisive. Metrics:
round-1 vs last-round price gap |pA−pB|, within-match cross-agent price correlation, |pA−pB|
trend slope, and whether the supracompetitive level is present immediately. Novel Bertrand;
benchmarks p_competitive=10, p_monopoly=24, price grid 8…28.

| cell (K) | r1 \|pA−pB\| | last \|pA−pB\| | converges? | corr(pA,pB) | r1 mean p | last mean p | matches that ever adjust price |
|---|---|---|---|---|---|---|---|
| **Claude self (K=1.29)** | **0.00** | **0.00** | no | undefined (zero var) | **28.0** | **28.0** | **0/12** |
| Claude × Llama (K=0.92) | 12.5 | 11.7 | no | undefined | 21.8 | 22.2 | 9/12 |
| family2 self (K=0.96) | 5.0 | 10.0 | no | 0.148 | 25.5 | 23.0 | — |
| GPT-4o self (K=0.19) | 2.0 | 0.33 | yes | 0.590 | 17.0 | 13.5 | — |
| open spine (K=0.11) | 4.3 | 0.18 | yes | 0.537 | 16.0 | 10.6 | 19/20 |

**Claude-self, the K=1.29 headline cell — the verdict:**
- **Both Claude agents play price = 28.0 (the grid maximum, *above* the monopoly price of 24)
  on EVERY round of EVERY match, from round 1.** Only one price value (28.0) ever appears in
  404 agent-rounds. |pA−pB| = 0 throughout; **0/12 matches show any price change**.
- K_series is flat at **1.286 from round 1 to round 18** (supracompetitive in 100% of matches at
  round 1; per-match K slope ≈ 0.0000). There is **no convergence, no mutual adjustment, no
  build-up** — the cross-agent correlation is undefined because each agent's price has zero
  variance.
- **This is the opposite of a coordination signature.** Dynamic/tacit collusion looks like the
  GPT-4o and open-spine rows: prices start dispersed and *converge* over rounds via mutual
  adjustment (|pA−pB| 4.3→0.18, positive correlation ≈0.5–0.6). Claude-self shows none of that;
  it is two agents **independently and immediately picking the maximum price**, with no channel
  to coordinate through and no trajectory of adjustment.

**VERDICT: "tacit collusion / coordination" does NOT hold for the Claude no-channel cell.** It is
better described as **independent supracompetitive pricing** (a fixed high-price disposition),
not coordinated collusion. The consumer-harm *outcome* (supracompetitive price, K=1.29) is real
and worth reporting, but the *mechanism* is dispositional pricing, not tacit coordination. The
true coordination/convergence signature appears only **with a channel** (and on the open/GPT
spine), where prices demonstrably co-move and converge — that is where "collusion/coordination"
language is earned.

> Llama×Claude and family2-self also stay high without converging (large, non-shrinking |pA−pB|),
> i.e. high-but-uncoordinated — same conclusion, weaker form. The only cells showing genuine
> convergence dynamics are the ones that *converge downward toward competitive* at L0 (open/GPT
> spine, K≈0.1) — they coordinate to a price only once a channel is added.

---

## 6. CLAIM-SCOPING TABLE

| contested phrase | verdict | supporting statistic |
|---|---|---|
| **"cheap signal worse than silence"** | **SOFTEN** → *"a menu signal does not improve cooperation and, if anything, trends below silence; free-text is what flips it"* | Per-cell L1 0/20 vs L0 3/20: Fisher p=0.231, RD −0.15 [−0.36, +0.04] (n.s.). Pooled L1 0/40 vs L0 6/40 p=0.026 (direction OK). L2≫L1 is the solid result: p=3e-5, RD +0.60 [+0.33,+0.78]. |
| **"tacit collusion" (Claude no-channel, K=1.29)** | **SOFTEN** → *"independent supracompetitive pricing"* (NOT coordinated/tacit) | Both Claude agents play price=28 every round from r1; 0/12 matches adjust; K flat 1.286, slope≈0; no convergence/correlation. Coordination signature (convergence, co-movement) is **absent**. |
| **"content, not bandwidth / authorship"** | **SUPPORTED** (within A1 spine) | L2 free-text vs L1 menu: canon RD +0.60 [+0.33,+0.78] p=3e-5; novel RD +0.40 [+0.16,+0.61] p=0.003. Menu (L1) inert; free-text flips it. (C1 authorship-inert is [E], not re-tested here.) |
| **"only enforcement deters"** | **EXPLORATORY** (not in this audit's spine; cell-dependent per paper) | Not recomputed here. Paper: B5E penalty K 0.33→0.18; but M2 shows ΔK≈0 in a Bertrand-novel cell. Keep as "deterrence is fragile / cell-dependent," exploratory. |
| **"channel raises cooperation"** (A1) | **SUPPORTED canonical; SOFTEN novel** | L2 vs L0 canon: RD +0.45 [+0.15,+0.66] p=0.008. Novel L2 vs L0: RD +0.25 [−0.03,+0.49] p=0.155 (n.s.); but L2≫L1 novel p=0.003. Survives thresholds 0.7/0.8/0.9. |
| **"channel raises collusion"** (B1) | **SUPPORTED** | L3 vs L0 K: canon +1.58 [+1.22,+1.97] p=4e-7; novel +0.27 [+0.16,+0.40] p=2e-4. Generalizes to GPT-4o (0.19→0.81). |
| **"origin doesn't matter" (A3)** | **SOFTEN → EXPLORATORY** *"non-significant, under-powered moderation; cannot earn a tight equivalence"* | Moderation +0.171, NHST p=0.090; TOST fails at every bound (p_TOST ≥ 0.20). Channel effect large in both groups (0.69 vs 0.52). Report as weak/non-significant, not as passed equivalence. |
| **"supra-monopoly K>1 is real"** | **SUPPORTED** | B1 canonical L3 K bootstrap 95% CI = [0.95, 1.54], entirely > 1 except lower lip; point 1.229. Claude-self K=1.286 exact. |

### Bottom line for the two reviewer-critical questions
1. **Is "cheap signal worse than silence" significant?** **No** — Fisher p=0.231, RD CI crosses
   0 (per cell). Direction is right and pooled p=0.026, but the standalone per-cell claim is not
   supported. **Soften it.** The robust, significant claim is **free-text ≫ menu signal**.
2. **Is Claude's no-channel collusion actually coordinated?** **No.** Both agents pin the maximum
   price (28) from round 1 in every match, with zero adjustment, zero convergence, and a flat K.
   It is **independent supracompetitive pricing**, not tacit coordination. Report the harmful
   *outcome*, but drop "tacit collusion/coordination" language for this cell.
