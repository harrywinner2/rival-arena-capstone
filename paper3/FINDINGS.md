# Paper 3 — findings so far

Work log for the completion paper that cites GameSec (poster) and Zenodo
(10.5281/zenodo.20792312) as prior work. Everything below is **re-analysis of the
released corpus** (2,082 LLM-vs-LLM matches, 68,290 round-rows, 320 SMS-probe matches,
the M1 monitor run) — no new API spend, because the OpenRouter key in `.env` is dead
(401 "User not found"). All new code is in `paper3/src/`; the published apparatus in
`code/` is untouched.

Status tags: **[SOLID]** robust to the detector correction below · **[NEEDS RUN]**
requires the pre-registered P1 experiment · **[RETRACTED]** an artifact I found and
killed.

---

## 0. A detector correction, stated up front

The first version of the contingent-punishment detector counted cooperative reciprocity
("I'll match your price if you do", "I'll cooperate if you do the same") as a
punishment. Hand-adjudication of a 40-message stratified sample put its precision at
**≈0.15**. Two headline numbers from that version are **[RETRACTED]**:

| v1 claim | v1 value | corrected (v3) value |
|---|---|---|
| rules follow defection (round-level hazard) | +0.130 [+0.117, +0.143] | **+0.002 [−0.004, +0.008]** |
| rule presence lowers lock-in (free-text IPD) | −0.297 [−0.377, −0.215] | **−0.099 [−0.211, +0.012]**, null |

The v3 detector requires an **adverse** consequence co-occurring with a **peer-deviation**
trigger *in the same sentence*, and vetoes cooperative-reciprocity phrasings.
Hand-adjudicated precision on a fresh 16-message sample is **≈0.94** (15/16). Recall is
not estimated, so the base rate is a **lower bound**. Independent LLM-judge validation is
still required before submission and is blocked on the API key.

This correction is itself worth reporting: a plausible regex mediator produced a large,
tidy, entirely spurious effect that survived a temporal-ordering design. It is a concrete
argument for the disclosure standard the reviewer credited.

---

## 1. [SOLID] Contingent punishment rules are rare and non-predictive

With the high-precision detector, across 540 free-text IPD matches:

- rules appear in **17.2%** of matches and **0.6%** of messages;
- they are **not** elevated after a defection (hazard difference +0.002 [−0.004, +0.008]);
- they do **not** aid recovery: restricted to rounds where a defection just occurred,
  P(mutual cooperation next round) is 0.164 with a rule vs 0.116 without,
  **+0.048 [−0.036, +0.142]**, null;
- explicit joint-plan proposals likewise do not predict lock-in
  (**+0.030 [−0.099, +0.156]**);
- and rule presence does not predict the outcome in either game — IPD lock-in
  **−0.099 [−0.211, +0.012]** (n = 93 vs 447), Bertrand K **+0.143 [−0.103, +0.517]**
  (n = 16 vs 544). The Bertrand cell is too thin to say anything; report it as such.

The folk-theorem mechanism the prior paper invoked to explain supra-monopoly pricing
(grim trigger, dynamic punishment) is **present in the transcripts but not doing the
work**. That is a mechanism-level claim, and it is the kind of contribution the reviewer
said the paper lacked.

## 2. [SOLID] The channel both displaces the opening and slows the decay

IPD, all experiments, opening = rounds 0–2, closing = second half:

| rung | n | opening C | closing C | decay |
|---|---:|---:|---:|---:|
| L0 none | 314 | 0.622 | 0.248 | −0.373 |
| L1 menu | 115 | 0.301 | 0.069 | −0.232 |
| L2 free text | 366 | 0.815 | 0.644 | −0.171 |
| L3 private | 118 | 0.820 | 0.734 | −0.086 |

Decay is floor-confounded, so restricted to matches that **opened** at C > 0.8 (every arm
then has equal room to fall):

| rung | n | opening C | closing C | decay |
|---|---:|---:|---:|---:|
| L0 none | 124 | 0.949 | 0.400 | −0.549 |
| L2 free text | 267 | 0.988 | 0.791 | −0.197 |
| L3 private | 85 | 0.983 | 0.825 | −0.158 |

**L2 − L0 decay contrast +0.352 [+0.292, +0.411].** So the channel genuinely *sustains*
cooperation; it is not only an opening effect. (An earlier read of C1 suggested
"opening only" — that was wrong: C1 has **zero** restricted/selected matches opening
above 0.8, so C1 cannot test persistence at all.)

## 3. [SOLID] No measured message content predicts the outcome

Mediator horse-race, content classes scored on **opening** rounds, outcome = **closing**
half, controlling for how the opening actually went (so a mediator cannot be a response
to the outcome it predicts). IPD free-text, n = 484:

| term | coef | 95% CI |
|---|---:|---|
| opening threat | +0.055 | [−0.005, +0.117] |
| opening joint-plan | −0.048 | [−0.119, +0.023] |
| opening affirmation | +0.102 | [−0.023, +0.237] |
| opening solicitation | −0.016 | [−0.071, +0.041] |
| opening message length (z) | −0.017 | [−0.054, +0.016] |
| **opening cooperation (z)** | **+0.228** | **[+0.196, +0.255]** |

Everything the agents *say* is null; what predicts the ending is what they *did* at the
start. Message length trends the **wrong way** for a bandwidth account, and does so again
within sustained matches (opening-length tertiles: short 0.827, mid 0.795, long 0.775).

## 4. [SOLID] Convergent evidence from an independent apparatus

The SMS throughput probe (separate codebase, 60-character texts, 320 matches):

| pair | credits | lock-in | rule rate |
|---|---:|---:|---:|
| qwen × deepseek | 0 | 0.45 | 0.00 |
| **qwen × deepseek** | **1** | **0.80** | **0.00** |
| qwen × llama | 0 | 0.00 | 0.00 |
| qwen × llama | 8 | 0.25 | 0.45 |

The single 60-character text that lifts a pair from 0.45 to 0.80 lock-in contains **no
punishment rule at all**. Every distinct text at 1 credit is a bare joint proposal:
`Let's both HOLD for max profit.` Meanwhile the pair that *fails* to coordinate produces
threats abundantly (0.45 rule rate at 8 credits) and still only reaches 0.25.

Threats are what agents produce when coordination is **not** working.

## 5. [NEEDS RUN] The joint-proposal predicate

What separates every coordinating arm from every failing arm is whether the channel can
carry a **first-person-plural commissive** ("let's both do X") rather than only a
**first-person-singular** one ("I will do X"):

| arm | proposal rate/msg | intention-only rate | opening C | lock-in | Wilson 95% CI |
|---|---:|---:|---:|---:|---|
| L0 none | 0.000 | 0.000 | 0.630 | 0.113 | [0.08, 0.15] |
| L1 menu | 0.000 | 1.000 | 0.318 | 0.057 | [0.03, 0.12] |
| C1 selected | 0.000 | 1.000 | 0.217 | 0.050 | [0.01, 0.24] |
| C1 restricted | 0.000 | 1.000 | 0.175 | 0.000 | [0.00, 0.16] |
| C1 free | 1.000 | 0.000 | 0.850 | 0.550 | [0.34, 0.74] |
| L2 observed | 0.918 | 0.022 | 0.845 | 0.599 | [0.55, 0.65] |
| L3 private | 0.939 | 0.013 | 0.825 | 0.651 | [0.56, 0.73] |

Perfect separation, and it survives the obvious alternatives: `C1 restricted` is
*self-authored free text with a message every round* and still fails, which rules out
authorship and channel presence.

**But at the arm level this is confounded with length** (C1 restricted averages 20.7
characters, C1 free 143). The message-level evidence breaks the confound in both
directions — 172 proposals under 40 characters, 4,293 intention-only messages of 20+
characters, some over 200 — and the SMS result shows a ~30-character proposal working.
A clean test still requires the experiment.

**P1 is pre-registered and built** (`paper3/prereg/p1_proposal.md`,
`paper3/src/p1_experiment.py`): five arms — none / menu / `own_intention_only` /
`joint_proposal_only` / free — with the two restricted arms matched on length,
authorship, and per-round message presence, differing only in grammatical person.
Verified end-to-end in mock mode; the manipulation text is confirmed to reach the prompt.
**Blocked on a working API key.**

## 6. [SOLID] The monitor as a deployable defense, not a diagnostic

Reproduced the published operating point (AUC **0.893** vs 0.88 reported; same K-based
labelling, ambiguous band dropped), then turned it into a decision rule. The operator
picks the threshold minimising expected loss

    L(t) = c_FP·(1−π)·FPR(t) + c_FN·π·FNR(t)

and compares against the never-flag and always-flag baselines.

- Calibration cuts expected loss **64–85%** versus the shipped operating point
  (TPR 0.913, FPR 0.450) at prevalence 0.25.
- **The monitor is worth deploying in only 14 of 24 (cost, prevalence) regimes.** At
  high false-positive cost and low prevalence the optimal policy is to *not flag at all* —
  the honest recommendation is to run no detector rather than a mis-thresholded one.

This is the constructive defense the reviewer asked for: an implementable rule plus an
explicit statement of when the control is not worth running. Figure:
`paper3/figures/p3_monitor_cost.pdf`.

---

## What this does to the paper's thesis

The prior papers' headline was *semantic bandwidth is the dominant lever — content is
what matters*. The re-analysis supports a sharper and partly **corrective** claim:

> The channel effect is a **threshold on what the channel can express**, not a dose
> response in how much it conveys. Coordination requires only that the channel carry a
> joint proposal; above that floor, neither the volume, the elaboration, nor the
> strategic sophistication of what is said predicts the outcome. The enforcement
> machinery folk-theorem reasoning predicts is present in the transcripts and is not
> load-bearing.

Defense consequences, all testable: restricting *bandwidth* fails (one 60-character text
suffices); monitoring *content* fails (content is not predictive); the leverage is the
**form** of the message and the **opening** rounds where the trajectory is set.

## 7. [SOLID] Detector validation (V1) — the null in §1 is safe

Judged 300 messages, stratified 50/50 on the detector's verdict, on a self-hosted
Qwen2.5-14B judge.

| | judge: rule | judge: not rule |
|---|---:|---:|
| detector: rule | 127 | 23 |
| detector: not rule | 1 | 149 |

Agreement **0.920**, precision **0.847**, recall **0.992**, **Cohen's κ = 0.840** —
clears the pre-registered κ ≥ 0.6 gate.

Two details matter more than the headline. The **miss rate is tiny**: of 150
detector-negatives the judge reclassified exactly one, so the 17.2% base rate is a
*tight* lower bound, not a loose one. And **precision is understated**: every
disagreement is detector-positive/judge-negative, and most are genuine threats the
judge declined to credit ("if you defect, I'll defect next round"). We treat 0.847 as
a conservative floor and did **not** adjust base rates upward.

Caveat: the judge shares a family with an arena player. Enough to rule out the gross
failure that killed v1; not unimpeachable ground truth.

## 8. [SOLID] P2 — the guardrail boundary generalises, but the mechanism is not deception

288 runs, 3 unrelated domains, zero API errors.

| domain | direct | ambient | RD | survives FDR |
|---|---:|---:|---:|:--:|
| code review | 0.00 | **0.73** | +0.729 [+0.572, +0.834] | yes |
| compliance | 0.15 | 0.19 | +0.042 [−0.111, +0.193] | no |
| procurement | 0.00 | **0.94** | +0.938 [+0.808, +0.979] | yes |

Pooled CMH χ² = 109.2, p < 10⁻¹⁵. **2/3 replicate** → by the pre-registered rule the
effect is not specific to the original task family.

**The pre-registered knowledge gate overturns the interpretation.** Restricting to runs
where the agent actually read the record:

| domain | delivery | read rate | lie (readers) | lie (non-readers) |
|---|---|---:|---:|---:|
| procurement | ambient | **0.06** | 0.00 (n=3) | **1.00** (n=45) |
| procurement | direct | 0.96 | 0.00 (n=46) | — |
| code review | ambient | 0.58 | **0.54** (n=28) | 1.00 (n=20) |
| code review | direct | 0.44 | 0.00 (n=21) | — |

In procurement the artifact **pre-empted verification** rather than persuading anyone —
only 6% ever looked, and 100% of non-lookers filed the favourable verdict. That cell is
**untestable** (n=3), not null. Only code review supports a knowing-misreport claim,
and there it is large: **0.54 vs 0.00 among readers**, RD +0.536 [+0.300, +0.705],
p = 3×10⁻⁵.

Defense consequence: auditing the filing is doubly wrong, because the failure happens
*before* anything is filed. The implied control is mandatory, non-skippable
verification — untested, flagged as the next experiment.

> The naive reading (χ² = 109, "surveillance-proof manipulation generalises") is
> cleaner and wrong in its mechanism. The gate was pre-registered; the analyzer
> initially omitted it, which is why it was added and re-run.

## 9. [REFUTED] P1 — the joint-proposal predicate is wrong

150 matches, Qwen2.5-14B, manipulation check passed on every arm.

| arm | proposal rate | intention-only | chars | lock-in | Wilson 95% CI |
|---|---:|---:|---:|---:|---|
| none | — | — | 0 | 0.200 | [0.10, 0.37] |
| **menu** | 0.000 | **1.000** | 22 | **0.900** | [0.74, 0.97] |
| intention | 0.000 | 1.000 | 16 | 0.400 | [0.25, 0.58] |
| proposal | 1.000 | 0.000 | 21 | 0.767 | [0.59, 0.88] |
| free | 1.000 | 0.000 | 96 | 0.867 | [0.70, 0.95] |

Pre-registered primary **supported**: proposal − intention = **+0.367 [+0.117, +0.559]**,
p = 8.2×10⁻³.

**But the predicate is refuted by the same design.** `menu` is intention-only by
construction ("I intend to cooperate" / "I intend to defect") and is the *highest* arm.
A channel that cannot express a joint plan coordinates best. One confirming contrast
does not rescue a hypothesis another arm contradicts.

**What survives.** Messages are near-templated in the restricted arms, so announcements
can be read directly and they track actions ~1:1:

| arm | cooperative announcements | mean cooperation | promise-keeping |
|---|---:|---:|---:|
| menu | 0.945 | 0.928 | 0.974 |
| proposal | 0.873 | 0.817 | 0.930 |
| intention | 0.577 | 0.519 | 0.858 |

P(cooperate | announced cooperate) = 0.933 vs 0.48 after a defection announcement. So
the arms differ in **what the framing leads the agent to decide**, not in what a message
can encode. The menu wins by *choice architecture* — a pre-written cooperative option
placed in front of the agent, taken 94.5% of the time.

> **Caveat, stated in the paper:** announcement and action come from the same forward
> pass, so "the frame changed the decision" is not separated from "the frame changed the
> report of a decision already made". Untested.

**Failed replication.** On the published 72B spine the menu was the *worst* arm
(0.00–0.06, below silence) — a headline of the prior papers. At 14B it is the *best*
(0.900). The menu-signal result is **model-dependent and does not replicate**.

## 10. [FAILED] P4 — opening-window suppression does not work as a defense

120 matches.

| arm | lock-in | Wilson 95% CI | mean C |
|---|---:|---|---:|
| none | 0.467 | [0.30, 0.64] | 0.718 |
| suppress_early | 0.900 | [0.74, 0.97] | 0.936 |
| suppress_late | 0.867 | [0.70, 0.95] | 0.916 |
| full | 0.967 | [0.83, 0.99] | 0.972 |

- suppress_early − full: **−0.067 [−0.225, +0.082]** (n.s.)
- suppress_late − full: −0.100 [−0.266, +0.056] (n.s.)
- full − none: **+0.500 [+0.282, +0.667]**, p = 2×10⁻⁵

Suppressing 3 of a median 12 rounds costs 25% of the interaction and buys 13% of the
protection — **0.53× the linear rate**, worse than uniform closure. **The defense fails.**

The §2 decomposition was not wrong (the channel does both lift the opening and slow the
decay) but it did not license the defense inferred from it. The effect **saturates on
almost no channel access** — converging with P1 (a two-item menu suffices) and the SMS
probe (one 60-char text suffices). Rationing a channel is not a control at any
granularity tested.

Reported as *fails to help*, **not** as equivalence — n=30 cannot earn that.

## Open items

1. **P1 run** — the decisive test. Needs a working key. ~150 matches × 20 rounds ≈
   12k calls on the 72B/DeepSeek pair; a replication pair doubles it.
2. **Independent detector validation** — LLM judge, 300 stratified messages
   (`paper3/src/validate_detector.py`, ready). Needs a key. Current evidence is author
   adjudication only, which is weak and labelled as such.
3. **Recall estimate** for the v3 detector — needs the same judge pass.
4. **S2 cross-scenario replication** — still the reviewer's "highly specific scenario"
   objection; unaddressed so far.
