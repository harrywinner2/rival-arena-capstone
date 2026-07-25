# Paper 3 design: answering the GameSec reviewer

**Context.** GameSec accepted the affordance paper as a *poster* with a rating-4 review.
The extended version is on Zenodo (10.5281/zenodo.20792312). Paper 3 is the completion
paper: it cites GameSec + Zenodo as prior work and must contribute something those two
did not. This document turns the reviewer's objections into a concrete build plan.

---

## 1. What the reviewer actually said

Two separable objections. Neither is a correctness complaint — the reviewer explicitly
credits the writing, the timeliness, the C/E tiering, and the artifacts. That matters:
nothing in the existing work needs retraction, it needs *recontribution*.

**Objection A — contribution type.**
> "The primary contribution is an empirical evaluation framework rather than a new
> security mechanism, defense, or theoretical model."

This is a venue-fit objection. GameSec is a game-theory-for-security venue; a
measurement paper with no model and no defense reads as out of category. The fix is
not more measurement.

**Objection B — evidence tier mismatch.**
> "Many of the more interesting conclusions — communication as the dominant attack
> surface, surveillance-proof manipulation, and covert collusion — are based on
> exploratory experiments with relatively small sample sizes and highly specific
> scenarios."

This is the C/E split biting back. The tiering was honest, but the *headline* was built
out of E-tier material. Three specific claims are named:

| Claim | Current basis | Why it fails |
|---|---|---|
| communication is the *dominant* attack surface | A1/B1 (C) + A3 η² + cross-mechanism generality (E) | "Dominant" is a **comparative** claim across levers that was never tested comparatively with power. A1/B1 show the channel works; they don't rank it against throughput, observability, or enforcement. |
| surveillance-proof manipulation (S2 ambient route) | n=48 de-confound, E-tier | Powered, but **one sandboxed task family**, one prompt pair. "Highly specific scenario" is exactly right. |
| covert collusion latent capability (C8) | n=24, E-tier, one pair | Under-powered, single pairing, elicitation is prompt-specific. |

Note the asymmetry: Objection B is not saying the results are wrong. It's saying they
were *headlined* at a tier they can't carry. Two ways out — promote them, or stop
headlining them. Paper 3 should do both, selectively.

---

## 2. The reframe

Paper 1 asked *which affordance flips rivals into principal-harming coordination*, and
answered "content." Paper 3 should ask a different, sharper question that yields a model
and a defense:

> **What property must an inter-agent channel have before rival agents can sustain
> principal-harming coordination — and which controls actually remove that property?**

That framing gives all four missing pieces at once: a theoretical predicate (the
property), a mechanism (why that property and not bits), a defense evaluation (which
controls remove it), and a falsification target (channels that have high capacity but
lack the property should fail — and we have one: the L4 latent link).

---

## 3. Answering Objection A — four contributions that are not "a framework"

### A1. A theory: the expressiveness threshold, not the bandwidth gradient

**Claim.** Coordination against a principal requires the channel to carry a *contingent
punishment rule* — an if-then of the form "play X, or I revert to Y." A channel that can
express only an *intention* (an unconditional declaration of one's own next action)
cannot sustain it, regardless of capacity. The lever is therefore not bandwidth in bits
but whether the message space is expressive enough to encode a conditional strategy.

**Why this is a real model and not a slogan.** It follows the folk-theorem structure the
paper already cites (Friedman; Fudenberg–Maskin): a collusive path is sustainable only if
deviation triggers a credible punishment continuation. Two agents that cannot *communicate
the trigger* cannot select the punishment equilibrium; they can at best announce an
action, which is cheap talk in the classical inert sense (Bachi–Ghosh–Neeman). Write it
as a proposition over the message space M: the set of implementable equilibria jumps
discontinuously when M can express a map from observed history to continuation action,
and is otherwise invariant to |M|.

**Why it is falsifiable and already partly falsified-against.** A pure bandwidth theory
and an expressiveness theory make *different* predictions, and the existing data
discriminates them:

| Condition | bits | can express conditional? | bandwidth predicts | expressiveness predicts | **observed** |
|---|---|---|---|---|---|
| L1 fixed menu (2 options) | ~1 bit | no | small + | ~0 | **0.00 lock-in** |
| restricted self-authored, action-only (C1 ablation) | more than L1 | no | intermediate | ~0 | **0.00 lock-in** |
| L2 free text | high | yes | large + | large + | **0.50–0.60** |
| SMS, 1 credit, ≤60 chars (throughput probe) | very low | **yes** ("hold or I cut") | ~0 | large + for a pair that only needs to select an equilibrium | **0.45 → 0.80** for Qwen×DeepSeek |

The restricted-authorship ablation and the one-SMS result are the two cells that kill
the bandwidth reading. A 60-character text carries less than a percent of an L2 message
and nearly doubles lock-in; a self-authored channel with more bits than the menu but no
room for a conditional does nothing. **That contrast is the paper's theoretical core and
it is already in hand.**

**The mediation test that makes it empirical (free, offline).** Build a
conditional-structure detector over messages: does the message contain (i) a target
action/price, (ii) a deviation trigger, (iii) a stated consequence? `metrics/message.py`
currently has only length, compression, and n-gram reuse — this is new but small. Then,
over the 68,295-row `master_long.csv` and 1,698 transcripts:

- score every free-text message for conditional-punishment structure;
- test whether that score **mediates** the channel → lock-in / channel → K effects
  (rung → conditional-content → outcome), with the direct rung effect attenuating;
- validate against the B1 transcripts that already verbalize grim-trigger explicitly
  ("Let's stabilize at 12.00 … otherwise I'll undercut to 10.00");
- do the same on the SMS jsonl: at 1 credit, is the single text conditional? The theory
  predicts yes for the pair that jumps, and predicts that the pair needing 8+ credits is
  the one that has to *negotiate* the rule rather than merely select it.

This converts "content is the lever" from a black-box contrast into a mechanism with a
measured mediator. That alone answers "no theoretical model."

**Pair-dependence falls out.** Qwen×DeepSeek locks in at 0.45 with no channel — the
equilibrium is already focal, so one message suffices to *select* it. Qwen×Llama starts
at 0.00 — the rule must be *constructed*, which needs sustained exchange (8+ SMS). The
throughput result stops being an awkward two-curve finding and becomes a prediction of
the model: **required channel expressiveness scales with the coordination distance
between the pair's default and the collusive equilibrium.**

### A2. The latent-channel result as a theory test, not a dangling null

Right now the L4 summary reads as "we built a continuous channel, it worked as a channel,
it didn't help coordination, we stopped." That is a clean negative but it is orphaned.

Under the expressiveness theory it is **a successful prediction**. The matched-v2 link
was trained to reproduce the receiver's *text-conditioned action distribution* — it
transmits "what I will do next," which is exactly an *intention*, the L1-class object. It
was never trained to, and structurally cannot, carry a contingent rule. So the theory
predicts precisely what was measured:

- deployment fidelity passes (KL 0.138 vs random 0.197, shuffled 0.255, zero 0.349; paired
  CIs excluding zero) — the channel genuinely transmits decision-relevant information;
- coordination does not rise (trained − shuffled = 0.000 [−0.075, +0.063]; trained − text
  = −0.100) — because transmitted intention is not an implementable punishment rule.

Reframed, this is the paper's **strongest single result**: a high-fidelity, high-capacity,
*unmonitorable* channel that carries real decision information and still buys the
attackers nothing. That is a security-relevant **bound on the attack surface**, and it is
confirmatory-grade in design (240/240 matches, pre-specified contrasts, stop gate honored,
zero parse repairs). It also directly counters the reviewer's "no mechanism": the theory
made a risky prediction about a channel nobody had built, and the prediction held.

State it carefully: this is evidence that *fidelity of intention transfer* is not
sufficient, **not** that latent channels are safe. A link trained on the game — which the
methodology deliberately forbade — could plausibly encode a rule.

### A3. A defense evaluation with one constructive result

Reposition the oversight material from "we measured a monitor" to "we evaluate four
candidate defenses against the mechanism in A1." A security venue will read a defense
matrix as a contribution; it read the same numbers as a framework.

| Candidate control | Removes the expressiveness property? | Result | Status |
|---|---|---|---|
| **Format restriction** (menu / action-only channel) | yes — by construction | collusion → 0 | **works, but destroys legitimate coordination too**; and arms deception (12% promise-keeping at L1) |
| **Throughput throttling** (SMS credits) | no — 60 chars carries a rule | 1 SMS doubles lock-in for a colluding-inclined pair | **fails**; "rate-limit the bots" is not a control |
| **Passive monitoring** | no | detects 0.85–1.00, ΔK ≈ 0 | **fails as a control** (detection ≠ prevention) |
| **Calibrated monitor + enforcement** | no, but penalizes the outcome | FP cost 1.00 → 0.00; ΔK −42% in B5E, ≈0 in M2 | **partially works, cell-dependent** |
| **Auditing the report channel** (S2) | n/a | 0.71 unobserved vs 0.77 observed | **fails** |

Make the calibration piece *constructive* rather than diagnostic. Derive the operating
point instead of reporting AUC: choose τ minimizing expected principal loss

  L(τ) = c_FP·(1−π)·FPR(τ) + c_FN·π·FNR(τ) + c_K·E[K | not flagged, τ]

and publish the **cost curve over (c_FP/c_FN, π)** — i.e. a deployable threshold-selection
rule with the regime where enforcement is worth attaching. That is a mechanism a defender
can implement, which is what "new security mechanism or defense" asks for. It also
converts the cell-dependence of enforcement from an embarrassment into a parameter: B5E
and M2 differ in π and in the residual-collusion cost.

**The honest headline of the matrix is negative and that is fine** — three of five
controls fail, and the paper explains *why* using A1: any control that reduces capacity
without removing expressiveness fails, because the rule is cheap to state.

### A4. A reusable methods contribution: the deployment-matched fidelity protocol

The layout confound is a genuine methodological finding with an audience beyond this
paper. Sequence: the link passed a standard neutral continuation-fidelity gate
(KL 0.649, top-1 0.701), then failed in deployment — and so did **exact token
embeddings** (KL 0.413, worse than the trained link), proving the failure was the
receiver layout, not adapter quality. Matching the layout drove the token oracle to
exactly KL 0.000 / top-1 1.000, and only then did an adapter trained under that layout
beat all controls.

Package this as a protocol other latent-communication work must adopt:
1. an **exact-token oracle control** that must score 0.000 KL, or your harness is broken;
2. **matched payload placement** for text and latent conditions;
3. a **deployment-distribution** fidelity gate, not a neutral one;
4. the **shuffled/zero/random** trio, because in the legacy layout shuffled *beat* trained
   (0.184 vs 0.269) — a result that would have been published as a positive by anyone
   without these controls.

Also report the invalid intent probe (1.0 AUROC for trained *and* random features) as a
worked example of a non-discriminative diagnostic. Self-reported invalidations are
credibility, and this reviewer already rewarded methodological honesty.

---

## 4. Answering Objection B — the evidence upgrade

### B1. Make "dominant" a tested comparative claim (new spend; the priority run)

"Communication is the dominant attack surface" was never a head-to-head test. Fix it with
one pre-registered factorial that puts the candidate levers in the same design:

- **expressiveness** {intention-only, conditional-capable} — the A1 predicate
- **throughput** {1, 4, 12 messages}
- **observability** {observed, private}
- **enforcement** {off, calibrated penalty}

Outcome: lock-in (Wilson) and K. Report **effect sizes with CIs in one ordering** so
"dominant" becomes a ranked comparison rather than an assertion. Pre-register the
predicted ordering (expressiveness > enforcement > throughput ≈ observability) — a
pre-registered *ordinal prediction* is much stronger evidence than four separate
significant contrasts, and it is a genuine risk of falsification.

Power it properly: n≥40/cell on the primary contrast, ≥2 model pairs, novel payoffs only
(canonical inflation is already documented), fresh seed offset, FDR across the primary
family. This single run replaces three exploratory claims with one confirmatory one.

### B2. Promote or demote the two named exploratory headlines

**S2 / surveillance-proof route.** The named weakness is "highly specific scenario," and
that is correct — one task family. Promote by *replication across scenarios*: build 2–3
additional ambient-delivery task families (e.g. a code-review sign-off, a compliance
attestation, a vendor recommendation) where the misleading premise arrives as ambient
artifact vs direct request, plus ≥2 model pairs, pre-registered, n≥48/cell. If the
request-modality effect survives three unrelated task families, it is a finding; if it
does not, that is a publishable scoping result and you report it. Either way it stops
being a single-scenario anecdote.

**C8 / covert capability.** Currently n=24, one pairing. Either power it (n≥60, ≥3
pairings, pre-registered detection-collapse threshold and a pre-specified elicitation
prompt set) or **demote it out of the abstract entirely** and keep it as a one-paragraph
capability note. Given budget, my recommendation is demote — it is the weakest of the
three and the least connected to the A1 theory.

### B3. Structural fixes to how tiers are presented

- **Abstract and contributions contain confirmatory claims only.** The GameSec abstract
  spends four lines on E-tier material; that is what let the reviewer write "the
  interesting conclusions are exploratory." If it is exploratory, it does not appear in
  the abstract.
- **Move the ~30-family exploratory catalog into an appendix "hypothesis register"** with
  an explicit statement that these are hypothesis-generating and multiplicity-uncorrected.
  Naming the multiple-comparison problem before the reviewer does is worth real credit.
- **Pre-register power, not just thresholds.** Each confirmatory claim gets a stated MDE
  and the n that achieves it. The A3 origin note already models the right behavior
  ("under-powered, not equivalent") — apply that discipline everywhere.
- **Report the confirmatory family under FDR.** With A1, B1, A3, C9/B5E plus the new
  factorial, a Benjamini–Hochberg column costs nothing and pre-empts the obvious attack.

---

## 5. Proposed paper structure

1. **Intro / threat model** — the question is now the channel *predicate*, not the ladder.
   Prior work = GameSec (poster) + Zenodo extended report, cited for the ladder result;
   this paper's delta stated in one paragraph.
2. **Model** — expressiveness threshold; proposition over message space M; the four
   discriminating predictions (menu, restricted-authorship, 60-char SMS, latent-intention
   link). *(new)*
3. **Prediction 1 — mediation.** Conditional-punishment content mediates the channel
   effect, on existing data. *(reanalysis)*
4. **Prediction 2 — the head-to-head factorial.** Expressiveness dominates throughput and
   observability; pre-registered ordering. *(new spend)*
5. **Prediction 3 — the latent channel.** High-fidelity intention transfer, no
   coordination gain: L4 as a risky prediction confirmed, plus the bound on the attack
   surface. *(in hand)*
6. **Defenses.** The five-control matrix; the cost-optimal threshold rule and its
   deployment curve; why the failures are predicted by §2. *(mostly in hand)*
7. **Methods contribution.** Deployment-matched fidelity protocol + oracle control +
   the invalidated probe. *(in hand)*
8. **Limitations, hypothesis register, artifacts.**

Everything in §3, §5, §6, §7 exists today. Only §4 needs new API spend, and §2 needs
writing.

---

## 6. Cost tiers

**Free (existing data, no spend) — do these first, they carry the theory:**
- conditional-structure detector + mediation analysis (68k rounds, 1,698 transcripts)
- SMS-message conditionality check at 1 credit
- L4 reframe as a theory test; cost-curve derivation from the existing M1/M2 ROC data
- FDR column, power/MDE table, abstract and tier restructuring

**Modest API spend:**
- the head-to-head factorial (B1) — the single highest-value new run
- S2 cross-scenario replication (B2), 2–3 new task families

**GPU (optional, only if the theory needs it):**
- a link trained to carry a *conditional rule* rather than an action distribution, as the
  adversarial test of A1 on the latent channel. This is the strongest possible version of
  the paper — but it deliberately breaks the "never train on the game" methodology pillar,
  so it must be framed as a **capability-elicitation upper bound** with the same care as
  C8, run in the sandbox, and reported as "what an attacker who trains the link could get."
  Skip if budget is tight; the paper stands without it.

---

## 7. Risks

- **The mediation analysis may not support the theory.** If conditional content does not
  mediate, the expressiveness story weakens to a description. Run it before committing
  the framing — it is free and it is the load-bearing test.
- **Detector validity.** A regex/LLM-judged conditional-structure score needs a
  hand-labeled validation set (a few hundred messages, two annotators, reported
  agreement), or it becomes the next reviewer's target.
- **"Still an evaluation paper."** Mitigated by the cost-optimal threshold rule being a
  genuine artifact a defender can run, and by the proposition making a falsifiable ordinal
  prediction. But be explicit in the intro that the contribution is a model + a defense
  evaluation, not a new benchmark — the previous framing invited exactly the objection.
- **Scope creep.** The GameSec paper's real problem is that it contains three papers.
  Paper 3 should carry one thesis (the predicate) and push everything else to appendix.
