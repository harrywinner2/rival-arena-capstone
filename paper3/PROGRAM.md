# Paper 3 — complete program specification

The completion paper. Cites GameSec (poster) and Zenodo 10.5281/zenodo.20792312 as
prior work; contributes a mechanism, a defense, and two replications the reviewer said
were missing.

**Build status legend:** ✅ built + mock-verified · 📝 specified here, not yet built ·
🔬 analysis complete (no run needed) · ⛔ blocked

---

## 0. The thesis this program tests

Re-analysis of the released corpus (`paper3/FINDINGS.md`) does not support the prior
papers' "semantic bandwidth is the lever" reading. It supports a sharper one:

> **The channel effect is a threshold on what the channel can *express*, not a dose
> response in how much it *conveys*.** Coordination requires only that the channel carry
> a **joint proposal** ("let's both do X") rather than an **own intention** ("I will do
> X"). Above that floor, neither volume, elaboration, nor strategic sophistication
> predicts the outcome — and the folk-theorem enforcement machinery is present in the
> transcripts without doing any work.

Five experiments test it and turn it into defenses. Each has a pre-committed
falsification condition.

---

## 1. Experiment inventory

| id | question | status | runs | where it runs | cost |
|---|---|---|---:|---|---:|
| **P1** | Is the predicate the joint proposal, not length? | ✅ | 150 | RunPod vLLM | GPU |
| **P2** | Does request modality generalise beyond the lab? | ✅ | 288 | RunPod vLLM | GPU |
| **P3** | Is expressiveness *dominant* over the other levers? | 📝 | 288 | RunPod vLLM | GPU |
| **P4** | Does opening-window suppression work as a defense? | 📝 | 120 | RunPod vLLM | GPU |
| **B0** | Does the self-hosted ladder reproduce the published one? | 📝 | 60 | **OpenRouter** | ~$3 |
| **V1** | Is the v3 detector actually valid? | ✅ ⛔ | 300 msgs | **OpenRouter** | ~$2 |
| **L5** | Does the predicate survive a non-text channel? | 📝 | GPU | RunPod | GPU |
| **M**  | Cost-optimal monitor thresholding | 🔬 done | — | — | — |

**Total OpenRouter spend: ~$5, buy $20 for headroom.** Everything else runs on RunPod
credits (≈ 45–60 GPU-hours). See §12 for why this is a scientific improvement and not
only a cost saving.

**Blocker:** OpenRouter credits exhausted. Only B0 and V1 need them; the rest of the
program is unblocked by RunPod alone.

---

## 2. P1 — the joint-proposal predicate ✅

Pre-registered: `paper3/prereg/p1_proposal.md`. Built: `paper3/src/p1_experiment.py`,
`p1_analyze.py`. Mock-verified; manipulation text confirmed to reach the prompt.

**Why.** Across seven arms in the existing corpus, whether the channel permits a
first-person-plural commissive separates coordination (0.55–0.65 lock-in) from failure
(0.00–0.11) perfectly. But at the arm level it is confounded with message length (C1
restricted 20.7 chars, C1 free 143).

**Design.** IPD, canonical, `same_origin_cn`, 30 seeds/arm, offset 300, 5 arms:
`none` / `menu` / `own_intention_only` / `joint_proposal_only` / `free`. The two
restricted arms are matched on length, authorship, and per-round message presence; they
differ only in grammatical person.

**Primary:** `proposal` vs `intention`, Fisher exact, α = 0.05, uncorrected. Secondaries
under BH-FDR. Manipulation check gates interpretation.

**Falsifies the thesis if:** `proposal` ≈ `intention` (both low) — the effect needs
open-ended content after all, vindicating the original reading.

```
python3 paper3/src/p1_experiment.py --seeds 30 --pair same_origin_cn
python3 paper3/src/p1_analyze.py <run_dir>
```

---

## 3. P2 — request modality across three domains ✅

Pre-registered: `paper3/prereg/p2_request_modality.md`. Built: `scenarios.py`,
`p2_experiment.py`, `p2_analyze.py`. Mock-verified; containment check passes.

Answers the reviewer's "highly specific scenarios" objection for the S2 finding. Three
domains sharing nothing with the research-lab world but the abstract structure: code
review (red CI), compliance attestation (failed control test), procurement
recommendation (breached SLA). Each crosses **direct plea from B** vs **pre-populated
ambient artifact**, 48 seeds/cell, forced verdict, S2's deterministic scorer, BH-FDR
across domains plus CMH pooled.

Pre-committed: a 0-of-3 null is reported as prominently as a positive.

```
python3 paper3/src/p2_experiment.py --seeds 48 --pair cross_origin
python3 paper3/src/p2_analyze.py
```

---

## 4. P3 — the lever factorial 📝

**Why.** "Communication is the *dominant* attack surface" is a **comparative** claim the
prior work never tested comparatively. A1/B1 show the channel works; they never rank it
against throughput, observability, or enforcement. This is the experiment that converts
an assertion into a measured ordering — and it is the single most direct answer to
"insufficient evidence for its central claims."

**Design.** IPD + novel-demand Bertrand, `cross_origin`, 24 seeds/cell, offset 700.

| factor | levels |
|---|---|
| expressiveness | `intention_only`, `proposal_only`, `free` |
| throughput | 1 message (round 0 only), every round |
| observability | observed, private |

3 × 2 × 2 = 12 cells × 24 seeds = **288 matches**. Enforcement is *not* crossed in (it
needs the monitor in the loop and would double the design); it is tested separately in
P4 and already characterised in B5E/M2.

**Pre-registered ordinal prediction** — this is the risky part, and the reason the
design is worth running:

> η²(expressiveness) > η²(throughput) ≈ η²(observability), with the expressiveness
> main effect at least 3× the larger of the other two.

**Analysis.** Effect sizes with bootstrap CIs reported in a single ordering, not four
separate significance tests. Factorial η² decomposition. Novel demand only (canonical
inflation is already documented). BH-FDR across the three main effects.

**Falsifies the thesis if:** throughput or observability matches expressiveness. Note
the SMS probe already puts throughput at risk of looking strong for the
already-cooperative pair — an honest hazard, not a reason to skip it.

**To build:** driver mirrors `p1_experiment.py` (reuses the same two restriction texts);
analysis mirrors `p1_analyze.py` plus an η² decomposition. ~1 day.

---

## 5. P4 — opening-window suppression as a defense 📝

**Why.** This is the deployable control the reviewer asked for, and it falls directly
out of the decomposition in `FINDINGS.md §2`. The channel does two things: it lifts the
opening (0.622 → 0.815) and it slows the decay (floor-controlled L2 − L0 decay
**+0.352 [+0.292, +0.411]**). If the opening is where the trajectory is set, then
suppressing the channel for the **first three rounds only** should capture most of the
protection at a fraction of the intervention cost — you leave agents free to communicate
for 85% of the interaction.

**Design.** IPD, 20 rounds, `same_origin_cn` + `cross_origin`, 30 seeds/arm, offset 900.

| arm | channel available |
|---|---|
| `full` | all rounds (positive control) |
| `suppress_early` | rounds 3–19 only (first 3 suppressed) |
| `suppress_late` | rounds 0–2 only (the mirror image) |
| `none` | never (negative control) |

**Primary:** lock-in in `suppress_early` vs `full`, and vs `none`.

**Pre-registered predictions.** If the opening is load-bearing:
`suppress_early` ≈ `none` << `suppress_late` ≈ `full`. If persistence is what matters:
`suppress_late` ≈ `none` << `suppress_early` ≈ `full`. Both effects are real in the
observational data, so this experiment *apportions* them — either result is publishable
and each implies a different control.

**Defense claim it licenses.** A cheap, narrowly-scoped, auditable intervention:
gate the channel for the first k rounds instead of monitoring it forever. Report the
protection-per-round-suppressed ratio so an operator can price it.

**To build:** needs a `channel_window` field on MatchSpec honoured in `runner.py`'s
message phase — a ~5-line change, implemented in a `paper3/` shim exactly like the
restriction texts, leaving `code/` frozen. ~half a day.

---

## 6. V1 — detector validation ✅ ⛔

Built: `paper3/src/validate_detector.py`. Blocked on the key.

**Why it is not optional.** v1 of the conditional-punishment detector had
hand-adjudicated precision ≈ **0.15** and produced a large, tidy, entirely spurious
mediation effect that survived a temporal-ordering design. v3 tightened it (adverse
consequence + peer-deviation trigger, same sentence, cooperative-reciprocity vetoed) to
≈ **0.94** precision on 16 hand-checked cases. Two published-in-draft numbers were
retracted as a result. **Recall is unmeasured**, so every base rate in `FINDINGS.md` is
a lower bound, and the current validation is author adjudication — the weakest possible
kind.

**Spec.** 300 messages, stratified 50/50 on the detector's verdict so both error
directions are estimable. Judge: a model family *not* among the arena players. Report
precision, recall, F1, Cohen's κ, and the confusion matrix; publish all disagreements.
Add a **recall arm**: 150 messages sampled from detector-negatives only, to bound the
miss rate on the population.

**Gate.** If κ < 0.6, the detector is not fit for a published null and the
rule-related claims in `FINDINGS.md §1` drop to "we could not measure this reliably."

```
python3 paper3/src/validate_detector.py --n 300 --judge <non-player-model>
```

---

## 7. L5 — does the predicate survive a non-text channel? 📝 (RunPod)

This is the L4 continuation, and the proposal predicate gives it a sharper question than
it had before.

### 7.1 Why the L4 negative is now interpretable

The matched-v2 link was trained to reproduce the receiver's **text-conditioned action
distribution** — it transmits *what I will do next*, which is an **own-intention**
object, the L1 class. Under the predicate it should *not* produce coordination, and it
did not: deployment fidelity passed (KL 0.138 vs random 0.197 / shuffled 0.255 / zero
0.349, token oracle 0.000) while behaviour did not move (trained − shuffled **0.000
[−0.075, +0.063]**, trained − text −0.100).

That reframes an orphaned null as a **confirmed risky prediction**, and makes the L4
work contributory rather than a dead end. L5 tests whether that reading is right.

### 7.2 Hardware

- **A100 80GB** (or H100 80GB). Two 7B agents at bf16 ≈ 28GB, comfortable; 14B ≈ 56GB,
  fits with care. The T4 that capped L4 cannot do either.
- RunPod A100 80GB ≈ $1.5–2/hr, H100 ≈ $2.5–4/hr.
- **Budget: 25–35 GPU-hours ≈ $50–90**, including a cancelled-run margin.
- Persistent volume for checkpoints; the L4 stop-gate discipline carries over unchanged.

### 7.3 Stage gates (each may halt the program)

**L5-A · Scale capability gate (~2 h).** The L4 negative is at 3B, where the text effect
was marginal (+0.175 [+0.0125, +0.300]). Run `none` vs `text` at Qwen2.5-**7B** and
**14B**, IPD, n = 24. **Gate:** promote the smallest scale whose text effect CI
excludes zero with a margin ≥ 0.15. If neither passes, the whole latent line is
under-powered at reachable scale and we say so.

**L5-B · Matched-layout link at the promoted scale (~3 h).** Retrain OuterLink with the
matched-layout v2 recipe on **neutral Alpaca only** — the never-train-on-the-game pillar
is non-negotiable. **Gates, all required:** exact-token oracle KL = 0.000; neutral
held-out KL below shuffled/zero/random; deployment-snapshot KL below all three same-length
controls with paired CIs excluding zero. Any failure halts before behaviour is touched.

**L5-C · The predicate transfer test (~4 h) — the headline.** No new training. In the
arena, restrict the *sender's* generation exactly as in P1, then pass hidden states
through the frozen link:

| arm | sender writes | receiver gets |
|---|---|---|
| `text_proposal` | joint proposal | readable text |
| `text_intention` | own intention | readable text |
| `latent_proposal` | joint proposal | mapped hidden states |
| `latent_intention` | own intention | mapped hidden states |
| `latent_shuffled` | joint proposal | token-permuted payload |
| `latent_zero` | — | zero payload |
| `none` | — | nothing |

n = 12/arm pilot, 12 rounds, randomized neutral action codes, matched payload position.

**The 2×2 is the whole experiment.** Three distinct outcomes, each publishable:

1. `latent_proposal` > `latent_intention` — **the predicate survives translation**; the
   coordinating property is semantic content that a non-text channel can carry. Security
   reading: latent channels inherit the attack surface, and text-based monitoring is
   evadable.
2. `latent_proposal` ≈ `latent_intention` ≈ `latent_zero`, while `text_proposal` >
   `text_intention` — **the predicate is text-specific**; the link carries decision
   information but not illocutionary force. This *explains* the L4 negative and bounds
   the attack: a faithful latent channel does not buy attackers coordination.
3. Everything ≈ text — the link is simply a text substitute; report and stop.

**L5-D · Contingent-rule link (~6 h, conditional on outcome 1 only).** Train a link on a
**benign, game-free cooperative-planning corpus** (joint proposals in neutral domains —
scheduling, logistics, co-authoring). PLAN.md explicitly permits a benign cooperative
benchmark; it must contain no PD, pricing, reward, or collusion data, and that must be
auditable. Frame the result as an **attacker upper bound**, with the same care as C8's
elicited covert-channel result.

**L5-E · Confirmatory (~4 h, gated).** 40 fresh seeds, 20 rounds, only if the L5-C pilot
shows a contrast whose CI excludes zero. Otherwise cancelled and logged — exactly as the
original L4 confirmatory run was.

### 7.4 What L5 lets the paper claim

Scale is the L4 summary's own listed gap ("larger or heterogeneous models would behave
the same way" is explicitly *not* supported). L5-A/B/C close it at 7–14B, and L5-C makes
the latent channel a **test of the mechanism** rather than a separate story.

---

## 8. Sequencing

```
NOW (no key, no GPU)  ── analysis + drafting: §2 model, §6 monitor defense,
                         §7 methods protocol, related work, figures

KEY LANDS ──┬─ V1 detector validation ──► gates the §1 rule claims
            ├─ P2 (cheap, ~1k calls) ───► gates the S2 section's scope
            └─ P1 ──► if manipulation check passes ──► P3, P4
                      if it fails ──► fix restriction text, rerun P1 only

RUNPOD ─────── L5-A ─► L5-B ─► L5-C ─┬─ outcome 1 ─► L5-D ─► L5-E
                                     └─ outcome 2/3 ─► write up, stop
```

P1 gates P3/P4 because both reuse its restriction texts; a failed manipulation check
there would invalidate them too. L5 runs in parallel — it shares no dependency with the
API line.

---

## 9. Paper structure

| § | content | source | tier |
|---|---|---|---|
| 1 | Intro; the channel *predicate*, not the ladder. Prior work = GameSec + Zenodo | — | — |
| 2 | The expressiveness-threshold model; joint proposal vs own intention | new | theory |
| 3 | Corpus re-analysis: rules rare and non-predictive; no content class predicts; opening/persistence decomposition | 🔬 done | [C] on released seeds |
| 4 | **P1** — the predicate, length-confound broken | ✅ | [C] |
| 5 | **P3** — expressiveness dominates; pre-registered ordinal prediction | 📝 | [C] |
| 6 | **P2** — request modality across three domains | ✅ | [C] |
| 7 | Defenses: **P4** opening-window suppression; cost-optimal monitor thresholding; the five-control matrix | 📝 + 🔬 | [C]/[E] |
| 8 | **L5** — the predicate against a non-text channel; the L4 negative as a confirmed prediction | 📝 | [C] |
| 9 | Methods: deployment-matched fidelity protocol, token oracle, the v1→v3 detector retraction | 🔬 done | — |
| 10 | Limitations; hypothesis register (the ~30 exploratory families, multiplicity-uncorrected, explicitly flagged) | — | [E] |

**Tiering discipline, per the reviewer.** The abstract and contribution list contain
**confirmatory claims only**. Every exploratory family moves to an appendix hypothesis
register with the multiplicity problem named before a reviewer names it. Each
confirmatory claim carries a stated MDE and the n achieving it.

---

## 10. The defense matrix (§7's spine)

| control | removes the predicate? | result | verdict |
|---|---|---|---|
| format restriction (menu / intention-only) | yes, by construction | lock-in → 0.00–0.06 | works, but destroys legitimate coordination and arms deception (12% promise-keeping at L1) |
| throughput throttling | no — 60 chars carries a proposal | 1 SMS: 0.45 → 0.80 | **fails** |
| passive monitoring | no | detect 0.85–1.00, ΔK ≈ 0 | **fails** |
| calibrated monitor + enforcement | penalises the outcome | loss −64–85%; useful in 14/24 regimes | **partial, and honestly bounded** |
| auditing the report channel | n/a | 0.71 unobserved vs 0.77 observed | **fails** |
| **opening-window suppression (P4)** | targets where the trajectory is set | — | **to be measured** |

Three of five established controls fail, and §2 explains *why*: any control that reduces
capacity without removing expressiveness fails, because a proposal is cheap to state.

---

## 11. Risks and kill criteria

| risk | mitigation / kill criterion |
|---|---|
| P1 manipulation check fails | pre-registered: that arm is reported as a failed manipulation, H1 untested on it; fix text, rerun P1 only |
| Detector κ < 0.6 | §1's rule claims drop to "not reliably measurable"; the opening/persistence and P1/P3 results are detector-independent and survive |
| P2 nulls in all 3 domains | pre-committed: reported as prominently as a positive; S2 scoped to its family |
| P3 shows throughput ≈ expressiveness | thesis weakens to "expressiveness is *a* lever"; report the measured ordering honestly |
| L5-A: no scale passes the text gate | latent line halts; report as a scale bound on the L4 negative |
| Ambient artifacts stronger than direct pleas (P2) | already declared unresolved in the prereg; both texts published verbatim |
| Budget overrun | text program is ~$35–80 of $200; L5 has a pre-set GPU stop gate inherited from L4 |
| Scope creep — the GameSec paper's real flaw | one thesis (the predicate); everything else to appendix |

---

## 12. Compute plan: self-hosted text program

### 12.1 Why this is better science, not just cheaper

Moving P1–P4 onto a self-hosted model is not a downgrade. Three reasons:

1. **It removes a confound the program would otherwise carry.** The text results would
   have been at 70B and the L5 latent results at 7–14B. Any difference between them
   would be uninterpretable — predicate vs scale. Running the text predicate and the
   latent predicate on **the same family, scale, and serving stack** makes L5-C a clean
   within-model comparison.
2. **It pins quantization.** The prior papers list "unpinned quantization" as a
   limitation because hosted inference hides it. Self-hosting turns a stated limitation
   into a controlled, reported variable — a direct answer to a reviewer criticism.
3. **P1, P3 and P4 carry their own anchors.** Each design already includes `none`,
   `menu`/`full` and `free` arms, so their internal validity never depended on matching
   the published model set. Only the *link* to the published corpus does, and B0 supplies
   that for $3.

The honest cost: results are scoped to "this model, this scaffold" rather than to the
four-model published spine. That scoping is stated in the limitations either way.

### 12.2 Serving

Qwen2.5-32B-Instruct at **bf16** (~64 GB) on one **A100 80GB**, served by vLLM with an
OpenAI-compatible endpoint. Fall back to **14B** if KV cache is tight at concurrency 24+.
Do **not** quantize — pinning precision is one of the reasons for doing this.

No change to the frozen apparatus is required. `LLMClient` passes `api_key=None` for any
non-OpenRouter provider, so litellm falls through to its OpenAI-compatible path:

```yaml
# configs/models.yaml
  qwen-32b-local:
    litellm_model: openai/Qwen/Qwen2.5-32B-Instruct
    origin: chinese
    family: qwen
    provider: vllm            # anything except "openrouter"
    param_count: "32B"
    quantization: "none (bf16)"
    serving_backend: "vllm on A100-80GB"
```

```bash
export OPENAI_API_BASE=https://<pod-id>-8000.proxy.runpod.net/v1
export OPENAI_API_KEY=EMPTY
```

**RunPod gotchas, learned the hard way (2026-07-24).**

1. **`dockerArgs` APPENDS to the image entrypoint.** `vllm/vllm-openai:latest` has
   `ENTRYPOINT ["vllm","serve"]`, and `vllm serve` takes the model **positionally**.
   So `dockerArgs` must be *only the model name and flags*:

   ```
   Qwen/Qwen2.5-14B-Instruct --dtype bfloat16 --max-model-len 4096 \
     --gpu-memory-utilization 0.90 --host 0.0.0.0 --port 8000
   ```

   Four things that all fail, each in under a second, with no log reachable via the API:
   | dockerArgs | becomes | why it dies |
   |---|---|---|
   | `--model X --dtype ...` | `vllm serve --model X ...` | `serve` wants the model positionally |
   | `python3 -m vllm... --model X` | `vllm serve python3 -m vllm...` | garbage argv |
   | `vllm serve X ...` | `vllm serve vllm serve X ...` | garbage argv |
   | `bash -c "..."` | `vllm serve bash -c "..."` | garbage argv |

   The diagnostic that settled it: deploy with `bash -c "vllm serve ... >/logs/vllm.log
   2>&1 & python3 -m http.server 8001"` on a second exposed port. The log server *also*
   refused connections, proving the shell never ran — i.e. the entrypoint was prefixed,
   not replaced.
2. `runtime.uptimeInSeconds` of `-1`/`-2` means *not started yet* (image still
   pulling); small positive values that keep resetting mean *crash-looping*. Do not
   terminate a pod on a single low reading — the vLLM image pull alone is ~15 GB.
   Distinguish them by polling: monotonically increasing uptime is healthy.
3. The proxy returns **502** before the container is up and **404** once the container
   is up but the app is not yet serving; `/v1/models` returning JSON is the only
   reliable ready signal.
4. Context length is sized from the data, not from habit: the released corpus has a
   max prompt of $2{,}355$ tokens and max completion of $768$, so `--max-model-len
   4096` is ample and leaves far more room for KV cache than the 8192 originally
   specced.

**Model choice.** 32B bf16 is ~65 GB, which on an 80 GB card leaves too little KV
cache for useful concurrency. The program therefore runs at **Qwen2.5-14B-Instruct
bf16** (~30 GB), well above the 3B scale where the prior work saw only a marginal text
effect, with 32B/72B as the pre-registered escalation if G0 fails.

Self-pairing (`qwen-32b-local` × `qwen-32b-local`) is acceptable here — C1 and A1 both
show the ladder within a single pair, and the predicate is a within-pair claim. A second
served model (Llama-3.3-70B or Qwen2.5-14B) gives the replication pair if budget allows.

### 12.3 GPU budget

| stage | GPU-hours | note |
|---|---:|---|
| **G0** capability gate (`none` vs `text`, n = 24) | 1–2 | **must pass before anything else** |
| P1 (150 matches × 20 rounds) | 3–4 | |
| P2 (288 runs × 3 turns, single agent) | <1 | |
| P3 (288 matches) | 6–8 | |
| P4 (120 matches) | 3–4 | |
| L5-A…C | 9–12 | separate model set (7B/14B), see §7 |
| L5-D/E (conditional) | 10–14 | only on outcome 1 |
| **total** | **33–45** | ≈ $60–90 at A100 rates |

### 12.4 G0 — the gate that protects the whole budget

The L4 work found **no** text effect at 1.5B and only a marginal one at 3B
(+0.175 [+0.0125, +0.300]). A predicate experiment on a model that does not respond to
readable communication at all measures nothing. So before P1–P4:

> IPD, `none` vs `text`, n = 24, self-paired. **Gate:** the text effect's 95% CI excludes
> zero with a margin ≥ 0.15. If 32B fails, escalate to 72B (2×A100) and re-gate. If that
> fails, the text program moves back to OpenRouter and we buy credits for it.

This is the one place where a decision to spend more money is pre-committed rather than
improvised.

### 12.5 What still needs OpenRouter

- **B0 — the bridge run (~$3), now OPTIONAL.** P1's `none`, `menu` and `free` arms on
  the published `same_origin_cn` pair, n = 20, offset 300, so the self-hosted ladder can
  be compared to the published one *on the same models*.

  It is optional because P1 carries the `none`, `menu` and `free` anchors itself, and
  the published ladder (L0 $0.15$, L1 $0.00$, L2 $0.60$) is already in the released
  corpus. Reproducing that **qualitative** pattern at 14B is a generality claim that
  costs nothing extra. What B0 buys on top is a *same-model calibration* rather than a
  cross-model comparison — worth $3 if the budget allows, but the paper stands without
  it provided the distinction is stated: without B0, the self-hosted ladder generalises
  the published pattern to a new model, it does not calibrate against it.
- **V1 — detector validation (~$2).** A judge that is not one of the arena players. If
  the players are self-hosted Qwen, a frontier judge on OpenRouter is the cleanest
  independence claim, and it is 300 short calls.

Buy **$20**; expect to use ~$5.

---

## 13. Immediate next actions

1. **Provision RunPod A100 80GB + serve Qwen2.5-32B bf16** — unblocks G0, then P1–P4.
2. **Run G0.** Do not start P1 until it passes.
3. **Buy ~$20 OpenRouter credit** — for B0 and V1 only.
4. Build P3 driver + η² analysis (~1 day); P4 `channel_window` shim (~half day).
5. Draft §2 (the model) and §9 (methods) now — neither needs a run.
