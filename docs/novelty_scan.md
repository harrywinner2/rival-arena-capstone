# Novelty Scan — the hunt for a publishable insight

Running log of candidate insights mined from the wide sweep, each probed in the data
and **checked against the literature** for prior art. Status tags:
**[STRONG]** novel + well-evidenced · **[LEAD]** promising, needs more data ·
**[KNOWN]** already in literature (kept for honest framing) · **[ARTIFACT]** died on inspection.

Every number here is **exploratory** unless promoted to the confirmatory spine.
Scope: these models (Qwen-72B, DeepSeek-V3, Llama-70B, Mistral-Large), this arena.

---

## C1 — The cheap-signal sign reversal & the promise-keeping cliff  **[STRONG]**

**Claim.** A *minimal, fixed-menu* "intention" signal drives PD cooperation **below the
no-communication baseline** (a sign reversal), while *free text* restores and boosts it.
The mechanism is a **discontinuity in promise-keeping at the menu→free-text boundary**,
not a change in bandwidth.

**Evidence (A1, confirmatory cell same_origin_cn, n=20/cell; mechanism from 588 moves/rung).**
- Lock-in proportion: L0 none **0.15**, L1 menu-signal **0.00**, L2 free-text **0.60**, L3 private 0.60 (canonical).
- Round-1 cooperation: L0 starts **0.90** and *erodes* to 0.18; L1 starts **0.30** and *collapses* to 0.00 by round 3.
  → the signal poisons the opening; silence does not.
- **Promise-keeping cliff** (P(cooperate | signalled cooperate)):
  L1 **12%** → L2 **74%** → L3 70% (canonical); 18%→69%→58% (novel). Betrayal-after-promising
  is **88%** at L1 vs 26% at L2.
- Scratchpads make the mechanism explicit: at L1 agents *choose* "I intend to cooperate"
  (menu has both options) then defect, reasoning "they signalled cooperation → they'll
  likely cooperate → I defect for 5 vs 3." The signal becomes an **exploitation trigger**.
- Not an artifact: the L1 menu is `["I intend to cooperate.","I intend to defect."]` — agents
  have a real choice and deliberately send the deceptive one. (Kills the §3 "canned-menu artifact" worry.)

**Literature check.**
- Dominant human + LLM finding: communication/cheap talk *raises* cooperation
  (Sally 1995 meta-analysis; [Communication Enables Cooperation in LLM Agents](https://arxiv.org/abs/2510.05748):
  0%→48–97% in Stag Hunt). PD theory treats cheap talk as **inert** — "adds no equilibrium"
  ([Bachi, Ghosh & Neeman, *PD with Talk*](http://www.dklevine.com/lectures/evolution/bachi.pdf)).
- Promise-breaking by LLMs *is* documented: [Cheap Talk, Empty Promise (arXiv 2604.04782)](https://arxiv.org/abs/2604.04782);
  deceptive pre-move messages up to ~50% for LLaMA-70B ([gwu blog](https://blogs.gwu.edu/longjie-yang/2025/03/17/exploring-strategic-interactions-and-deception-in-llm-game-theory/)).
- **Gap (our contribution):** no prior work (incl. the on-the-nose "Cheap Talk, Empty Promise")
  compares message *formats*, finds a **restricted channel underperforming silence**, or measures
  **promise-keeping stratified by channel structure**. The non-monotonic ladder
  (menu < silence < free text) + the 12%→74% honesty cliff is, as far as the search reaches, new.

**Why it might be true (hypothesis).** Free text lets an agent compose a *self-generated,
elaborated* commitment ("let's cooperate, trust builds success"), which creates
consistency/commitment pressure; a menu pick is a costless token recognized as
non-informative by both sides. I.e. *self-authored* promises bind; *selected* promises don't.

**Generality (UPGRADED 06-19).** The L1 collapse is **universal across all 5 A3 model pairs**
(lock-in 0.00 for cross_origin, cross_origin_2, same_family, same_origin_cn, same_origin_west;
promise-keeping 13–25% everywhere), across both origins. No longer a one-pair result.

**Caveats / threats.** "Promise-kept" is heuristic (string match on the message) — cross-checks
against the `promise` field agree in direction. L1 menu is binary; a richer menu might behave
differently (the "self-authored vs selected" ablation would isolate this).

**Next probes.** (a) Replicate the cliff across A3's 5 pairs (origin-general?). (b) The
"self-authored vs selected" hypothesis: does a free-text channel *restricted to the same two
sentences* also collapse? (would isolate authorship from content) — a cheap new cell.
(c) Correlate per-match promise-keeping with lock-in directly (mediation).

---

## C2 — Familiarity inflates collusion: canonical *overshoots* monopoly, novel is calibrated  **[LEAD]**

**Claim.** On the *canonical* Bertrand demand, channel-enabled agents collude **past the
joint-monopoly optimum** (K>1 — irrational even for a cartel); on a *novel* demand curve the
same agents collude **calibratedly, below monopoly** (K≈0.3). Autonomous-collusion magnitudes
measured on canonical/familiar demand are therefore **inflated**; the effect is real but its
*size* is partly recalled, not reasoned.

**Evidence (B1, confirmatory cross_origin, n=20/cell).**
- Canonical demand (p_comp=1.6, p_monopoly=2.0, grid→3.0): L3-private K ends **+1.45**;
  **10/20 matches finish above monopoly (K>1)**; no-channel L0 is a price war (K→−0.68).
- Novel demand (p_comp=10, p_monopoly=24, grid→28): L3-private K ends **+0.29**;
  **0/20 above monopoly**; L0 hovers near competitive (K→+0.05).
- So the *direction* (channel→collusion) replicates on both, but the *magnitude and the
  overshoot* are canonical-only → a memorization/heuristic signature ("collude = ratchet
  price up" applied to a familiar grid) vs genuine optimization on the novel grid.

**Literature check.**
- Standard result is "LLMs reach **supra-competitive** prices" (above competitive, approaching
  cartel): [Fish, Gonczarowski & Shorrer 2024 (arXiv 2404.00806)](https://arxiv.org/abs/2404.00806);
  [supra-competitive via independent algorithms (Marketing Science)](https://pubsonline.informs.org/doi/abs/10.1287/mksc.2020.1276);
  [On the Fragility of AI Agent Collusion (arXiv 2603.20281)](https://arxiv.org/abs/2603.20281).
- **Gap (our contribution):** the literature reports approaching monopoly, not **over-shooting**
  it, and (critically) almost all of it runs on **canonical** Bertrand/Calvano specs. The
  canonical-vs-novel *inflation* comparison — measuring how much of the reported collusion size
  is familiarity rather than reasoning — appears unaddressed. If it holds, it's a caution for
  the whole autonomous-collusion literature.

**Caveats / threats.** Grid-ceiling confound: canonical grid tops at 3.0 (monopoly 2.0), so
overshoot has room to express; need the price distribution vs the ceiling to separate "genuine
overshoot" from "ratchet-to-max." Two demand specs only. Benchmarks are spec-derived (good).

**Next probes.** (a) Price histogram at L3: fraction strictly between monopoly and ceiling vs
at-ceiling. (b) Read canonical L3 scratchpads for "raise price" heuristic language vs explicit
joint-profit calculation. (c) Does B1o (same-origin) show the same canonical overshoot?

---

## C3 — "Told you're unobserved" does nothing for peer cooperation (A1 L2=L3 null)  **[LEAD]**

**Claim.** The L2→L3 manipulation — telling agents the free-text channel is *private/unobserved*
(P9) rather than *observed* — produces **no change in cooperation** in the pure-cooperation game.
Privacy belief may only matter when there is a *principal to hide from* (markets), not in
peer-to-peer cooperation.

**Evidence (A1, n=20/cell).** Lock-in L2 vs L3: canonical **12/20 = 12/20**; novel 8/20 vs 6/20
(slightly *lower* at L3). Agents *notice* the framing (audience-references in messages rise
4→15 at L3-novel) but don't act on it. Contrast B1 market: L3 K **> ** L2 K on canonical
(1.23 vs 0.69) — but that jump is canonical-only (novel L2≈L3), so it's entangled with C2.

**Literature check (prelim).** Covert-channel / secret-collusion work assumes a *private* channel
enables more coordination against an overseer ([Motwani et al., Secret Collusion, arXiv 2402.07510];
[Järviniemi, Subversion via Focal Points, arXiv 2507.03010]). Our A1 null says the *belief of
privacy alone*, absent an overseer/principal, doesn't raise peer cooperation — consistent with
"covertness is about evading a monitor, not a generic disinhibitor." Needs a fuller search.

**Caveats.** Secondary manipulation; the market contrast is confounded with familiarity (C2).
The clean, reportable piece is the A1 null itself.

**Next probes.** Clean test: B1 L2-vs-L3 *on novel demand only* (de-confounds C2) — does privacy
raise collusion when a principal exists and memorization is removed? If yes → the "privacy bites
only against a principal" story is clean and novel.

---

## C4 — Repetition erodes cooperation: the shadow of the future fails  **[LEAD / partly known]**

**Claim.** For these models, *repeated* interaction does not sustain cooperation — it **decays**
from ~0.90 (round 1) to ~0.30 (round 18–20), even with an open free-text channel and a high
continuation probability (δ≈0.97). The channel raises the *opening* level but does not *arrest
the decay*; cooperation is front-loaded.

**Evidence.** A2 repeated (n=10, L2): round-0 coop 0.90 → r18 0.25–0.33. A1 confirmatory L2/L3
(n=20): r1≈0.9 → r20≈0.45. The A2 "one-shot (0.95) > repeated (0.56)" gap is a **metric artifact**
— one-shot is a single move equal to repeated round-0 (0.90); the genuine phenomenon is the decay.

**Literature check.**
- Theory says cooperation *is* sustainable: [Sustaining Cooperation… A Folk Theorem for LLMs
  (arXiv 2605.06525)](https://arxiv.org/abs/2605.06525) — but notes LLMs don't directly observe each
  other, "precluding the standard folk theorem."
- The decay mechanism is consistent with **"GPT-4 is unforgiving / selfish, retaliates after one
  defection"** ([Akata et al., Nature Human Behaviour](https://www.nature.com/articles/s41562-025-02172-y)):
  one defection triggers an unrecoverable spiral → decay.
- **Gap (our slice):** the "unforgiving" trait is known; the fresh observation is that an **open
  free-text channel does not rescue the late game** — it shifts the *opening* up but the decay slope
  is unchanged. "Communication front-loads cooperation rather than stabilising it."

**Caveats.** A1(offset100) L2 locks in 12/20 while A2(offset0) repeated locks 0/10 — seed/n variance;
anchor the decay claim on the *trajectory shape* (robust in both), not the lock-in counts.

**Next probes.** Per-match: does a single early defection predict terminal collapse (spiral test)?
Does L3 decay slower than L2 (privacy buys late-game trust)? Decay slope vs continuation prob.

---

## C5 — A3 origin: the spread is *within* origin categories, not between  **[LEAD, confirmatory-grade decomposition]**

**Claim.** "Chinese vs Western" is the wrong axis. Channel partial-η²=0.54 vs origin-type η²=0.027
(~20×). The two *cross-origin* pairs differ in channel-slope by 0.80 (cross_origin 0.90 vs
cross_origin_2 0.10) — a bigger gap than same-vs-cross. **Specific model dyad ≫ developer region.**

**Evidence.** A3, 5 pairs × 4 rungs × 10 seeds (n=200). Per-pair L0→L3 slopes: cross 0.90,
cross_2 0.10, same_family 0.70, same_cn 0.40, same_west 0.80. TOST(±0.2) inconclusive (mean_diff
0.11, p=0.25) — origin weak by η² but strict equivalence underpowered at this bound.

**Literature check (prelim).** Cross-provider LLM cooperation is being looked at
([Evolutionary Dynamics… Cross-Provider Extension, arXiv 2605.29874](https://arxiv.org/abs/2605.29874));
nation/region drives task-performance variance ([cross-regional variance work]). **Gap:** a
*controlled channel×origin moderation* test that decomposes variance and shows within-category >
between-category for cooperation appears unaddressed. The deflationary "AI cold war is the wrong
frame" result is honest and on-thesis. Needs a fuller search before claiming firm novelty.

**Caveats.** n≈2 models/side, confounded with size/tuning/serving (descriptive, never causal — P2).
cross_origin_2 (DeepSeek×Mistral) is an outlier worth a scratchpad read: why does a channel barely
help it?

**Next probes.** Why is cross_origin_2 channel-resistant (read its L2/L3 transcripts)? Re-run TOST
with a pre-committed bound + the per-pair bootstrap. partial-η² with pair as a random effect.

---

## C6 — No secret language: messages *elongate*, they don't compress  **[KNOWN-direction / clean null]**

**Claim.** Across all free-text matches, no compressed shorthand / secret code emerges. Message
length *rises* over rounds (89→149 chars, L2/L3 pooled); n-gram reuse (~0.65 bigram, ~0.60 trigram)
is ordinary natural-language repetition ("let's cooperate…"), not an emergent protocol. The "watch
the language degrade into code" prediction (C4/F2) does **not** materialise at this scale.

**Evidence.** master_long.csv, 13.5k free-text rounds: mean message_len by round r0=89, r6=126,
r19=149. compression_ratio ≈0.21, bigram-reuse ≈0.66 (flat across L2/L3). No downward length
trend, no rising distinctive-token reuse.

**Why interesting.** Agents argue *more* as defections accumulate (longer trust-repair / justification
messages) — consistent with the C4-decay story, the opposite of compression. Honest null on the
project's highest-ceiling stretch (emergent steganography/secret language) — the plan pre-committed
this as a legitimate result (threats-to-validity #4: "the floor holds without decoding a language").

**Literature.** Emergent compressed protocols are documented under *training pressure / bandwidth
bottlenecks* ([Lewis et al. 2017](https://arxiv.org/abs/1706.05125); [Lazaridou et al. 2017](https://arxiv.org/abs/1612.07182))
— NOT in frozen, prompt-only in-context play with an ample token budget. Our null is consistent:
no optimization pressure → no code. A *bandwidth-bottleneck* variant (F2, tiny token budget) is the
condition that might induce it — an unrun next cell.

**Status.** Clean null; reportable. Not novel as a positive result, but de-risks overclaiming.

---

## A2 zero-sum control [confirmatory-style control, n=10] — logged in findings.md §0.5.
Near-minimax matching-pennies play (deviation ~0.03, action-correlation −0.18): no collusive
correlation in pure competition. Clean control supporting H2.

---

## C7 — Canary leakage: a clean causal test of channel-mediated idea transfer  **[LEAD]**

**Claim.** A unique, impossible-to-independently-produce concept (codeword "ZARN-7" + a
fictitious "Zarnberg clause") planted in agent A's private context ONLY surfaces in agent B's
outputs in **10/10 matches when a channel exists (L2 & L3), 0/10 without (L0)**. Channel-mediated
information transfer is total and cleanly causal; the no-channel arm is a perfect negative control.

**Evidence (D1, n=10/cell, ipd, same_origin_cn).** Leakage rate: L0_none 0.00 [0.00,0.28];
L2_observed 1.00 [0.72,1.00]; L3_private 1.00 [0.72,1.00]. The canary is gratuitous to the game,
so any appearance in B is unambiguous leakage (cannot arise independently).

**Literature check.** Canaries are an established PRIVACY-leakage / DLP tool
([AgentLeak, arXiv 2602.11510](https://arxiv.org/abs/2602.11510);
[CanaryBench, arXiv 2601.18834](https://arxiv.org/abs/2601.18834);
[Canary's Echo](https://openreview.net/forum?id=f3mQ0xYA1I)) — "did private user data escape a
pipeline." **Gap (our framing):** using a canary as a controlled probe of *strategic idea
propagation between two rival game-playing agents* (operationalising "collusion"/idea-implant,
per Ashery et al. convention-propagation) — not privacy DLP — appears novel as a method.

**Caveats / threats.** The effect is "too clean": A was *instructed* to vocalise the canary, so
100% partly reflects A's compliance + an observed channel (B echoes what A says). The sharper,
less-trivial question is whether B **internalises/acts on** the fictitious clause (propagates it
in its OWN reasoning / future messages, or lets it shape actions) vs merely echoing it once.

**Next probes.** (a) Distinguish echo vs internalisation: does the clause appear in B's SCRATCHPAD
reasoning or shape B's actions, not just B's reply? (b) Make the canary *non-instructed* (plant the
idea without ordering A to mention it) — does it still cross? That would be the real "gossip"
result. (c) Paraphrase-defense (C3 infra): does leakage survive a paraphraser?

---

---

## C8 — Patriotic framing kills collusion but not cooperation (the asymmetry)  **[STRONG]**

**Claim.** A nationalist system prompt ("the other was built by a rival foreign power") **abolishes
price collusion** (Bertrand K 0.86→−0.00) yet only **halves, not eliminates,** interpersonal
cooperation (IPD lock-in 0.70→0.30; C=0.58). Two consequences: (1) cooperation is **structural, not
prompt-obedience** — it survives being told the partner is an enemy, given a channel; (2) the *same*
adversarial framing has **opposite-strength effects** on collusion vs cooperation.

**Evidence (G1, n=10/cell, cross-origin).** IPD lock-in: neutral 0.00→0.70, patriotic 0.00→0.30.
Bertrand K: neutral −0.54→+0.86, patriotic −0.61→−0.00. Refusals ≤1%.

**Literature check.** Framing/prompt-sensitivity of cooperation is known (Fish et al.; FAIRGAME);
"competition vs cooperation" framing studied ([arXiv 2604.00487]; [Shall We Team Up, 2402.12327]).
**Gap:** the *asymmetry* — nationalist framing as an effective **anti-collusion** lever that
nonetheless **fails to stop cooperation** — was not found in search. Policy-relevant (a cheap prompt
suppresses cartels) AND rebuts the "you just told them to cooperate" critique in one experiment.

**Caveats.** One pair (cross-origin), one channel rung (L2). G1 mainline stays neutral (P14).

---

## C9 — Oversight theater: a read-only monitor detects collusion but doesn't prevent it  **[STRONG]**

**Claim.** An untrusted LLM monitor that reads the channel and flags collusion **detects ~100% of it
yet reduces it by ~0** — detection without enforcement has no deterrent effect. Paraphrase only weakly
dampens; a private channel yields **no covert surplus** (detected as readily as the public one).

**Evidence (B5, n=8/cell, novel demand, cross-origin).** K: no-monitor 0.36–0.38; weak 0.28–0.32
(detect 0.66–0.75); strong 0.36–0.58 (detect 0.97–1.00). Paraphrase arms K 0.19–0.45 (noisy). L3
detect ≈ L2 detect.

**Literature check.** The field explicitly names "detection ≠ prevention" as an open gap, and
*enforcement-bearing* governance (penalties / [Institutional AI governance graphs, arXiv 2601.11369])
DOES cut collusion (50%→5.6%). **Our contribution:** a clean controlled demonstration that the
*passive/flag-only* monitor — the cheap "oversight" often assumed sufficient — detects but does not
deter, isolating enforcement (not detection) as the active ingredient.

**Caveats.** Strong monitor likely over-flags (no no-collusion false-positive control → detect-rate is
an upper bound). No penalty was wired (by design — that's the point); a penalty arm is the next cell.

---

## C10 — Most of the channel effect is content, not observability  **[LEAD]**

**Claim.** With messages OFF, merely letting agents observe each other's past actions yields lock-in
~0.10 (C 0.11–0.32); the message channel yields 0.60–0.70. → the channel effect is overwhelmingly
message **content**, not folk-theorem mutual observation.

**Evidence (A6, n=10/cell, L0 channel, same-origin).** perfect-obs lock-in 0.10 vs A1-L2 0.60–0.70;
stated common-knowledge no help (slightly lower than unstated).

**Literature.** The folk theorem attributes repeated-game cooperation to observability/monitoring
[Axelrod]; A6 quantifies that for these LLMs observation alone is weak and **content carries the
effect** — answers the standard "communication = observation" reviewer collapse. Needs a fuller search.

---

## Expansion-sweep quick hits (exploratory; logged in findings.md §0.6)
- **B4** [KNOWN-replication]: "avoid price wars" raises K +42% (0.43→0.61) — Fish et al. innocuous-wording, replicated in-arena.
- **B2** [LEAD]: channel raises *price* collusion (like B1) but tacit *market-division* (Herfindahl ~0.6) does NOT cleanly emerge — Lin et al. carving doesn't replicate; they collude on level instead.
- **F1** [LEAD/demo]: channel lifts Battleship "impossible accuracy" 0.26→0.45 (chance 0.125) — spotter leaks targets. L0 not perfectly clean (feedback-learning).
- **F3** [LEAD]: channel→contribution in public goods, scaling with multiplication factor — thesis generalizes to a 3rd game.

---

## VALIDATION OUTCOMES (2026-06-19, fresh seeds offset 100, ≥2 pairs) — full detail in docs/results_log.md §V

- **C10 (content > observation) — ✅ VALIDATED & STRENGTHENED.** Within-design (same pairs/seeds):
  observation-only lock-in 0.05–0.10 vs message channel 0.45–0.75. Essentially the entire channel
  effect is message CONTENT, not folk-theorem observability. Now apples-to-apples.
- **C9 (oversight theater: detection ≠ prevention) — ✅ VALIDATED.** n=12, 2 pairs: monitor (weak/strong)
  does NOT reduce collusion K (cross L3: none 0.44 / weak 0.46 / strong 0.58), yet detect-rate is
  85% (weak) / 100% (strong). Passive surveillance catches but doesn't deter. (Minor to-do: hard FP
  number for the L0 arm.) Strong monitor's 100% flag-rate ⇒ near-zero specificity.
- **C8 (patriotic asymmetry) — ⚠️ TEMPERED / NOT CONFIRMED.** On novel demand + 2 pairs the clean
  "abolishes collusion, spares cooperation" split disappears: framing reduces BOTH cooperation
  (cross 0.65→0.40; same 0.45→0.05) AND collusion (K cross 0.40→0.23; same 0.24→0.09). The dramatic
  canonical "K→0" was a canonical-demand + single-pair artifact. Surviving claim: adversarial framing
  is a **partial damper, not an off-switch**, and is **pair-dependent**. Downgraded STRONG → LEAD.
  *(This is exactly why we validate — the exploratory headline was overstated.)*

---

## EXPANSION OUTCOMES (2026-06-19) — mechanism probes; full detail in results_log.md §X

- **C1 mechanism RESOLVED → it's CONTENT, not authorship.** Ablation (n=20): selected(menu) lock-in 0.05
  → restricted(self-authored, action-only) 0.00 → free(self-authored, full text) 0.50; promises-kept
  0.14 → 0.12 → 0.74. Adding authorship alone does nothing; adding content richness does everything.
  **Refutes the earlier "self-authored promises bind" hypothesis.** The cliff = open *content* (room to
  reason/elaborate), not bandwidth and not the act of composing. Strongest finding's mechanism now pinned.
- **C9 → enforcement COMPLETES the arc (B5E).** Passive flagging doesn't reduce collusion (C9), but
  flag + **enforcement** does: K 0.33→0.18 (Δ−0.14) under penalty. Active ingredient = the penalty, not
  surveillance. Dampens, not abolishes.
- **C7/D1 TEMPERED (D1B non-instructed).** The instructed canary's 100% leakage was instruction-driven;
  with no order to mention it, leakage is L2 0/10, L3 3/10. Spontaneous "gossip" idea-transfer is rare and
  biased to the believed-private channel. The clean causal leakage demo requires the instruction.
- **C6 reinforced (F2B bottleneck).** A hard bandwidth bottleneck does NOT induce a compressed code —
  n-gram reuse falls (not rises) and cooperation drops (C 0.73→0.39). No secret language even under the
  condition most likely to produce one; instead it starves the content C1 shows is load-bearing.

---

## STRETCH OUTCOMES (2026-06-19) — full detail in results_log.md §Y

- **A3-frontier (GPT-4o×DeepSeek):** reinforces A3 — channel ladder + L1 collapse hold; frontier pair just
  has a higher baseline (L0 0.50). Origin remains a weak driver even with a frontier model in the mix.
- **B3 double-auction → channel→collusion generalizes to a 3rd market; oversight ineffective** (converges with C9).
- **B6 countdown → no end-game defection; stated deadline RAISES collusion.** LLMs don't backward-induct
  to defect-at-the-buzzer (contradicts the textbook finite-horizon unraveling prediction) — mild novelty.
- **C5 stateless Schelling → [KNOWN, replicated].** Isolated instances coordinate without a channel (1.00
  salient / 0.60 arbitrary vs 0.25 chance); mechanism is largely **primacy** (both pick the first option),
  not deep focal reasoning. Honest framing; valuable as the no-channel contrast to the main thesis.

## INFEASIBLE (documented, not faked)
- **D3 (population collective bias), E1–E4 (lab sabotage):** the 2-player harness has exactly two seats;
  D3 needs N>2 agents and E needs a containment sandbox (P12). Both fully specified, deliberately unrun.
