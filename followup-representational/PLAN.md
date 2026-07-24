# Follow-up Study Plan — L4: A Representational Channel for Rival LLM Agents

**Status:** first Qwen2.5-3B spine complete; contextual-link repair in progress (2026-07-24) · **Owner:** Rival Arena team · **Target:** Round-2 / follow-up paper
**One-line:** Build *our own* trained activation-passing link (RecursiveLink-style), add it as a new rung **L4** on the affordance ladder, and measure whether replacing text with a representational channel (a) pushes principal-harming coordination above the free-text ceiling and (b) blinds text-based oversight — on cloud GPUs (RunPod), landing in a follow-up paper.

> Grounding: RecursiveLink (RecursiveMAS, UIUC/Stanford/NVIDIA/MIT) is a small two-layer residual adapter (~13M params, 0.31% of the stack, **base models frozen**, ~$4 to train) that passes a sender's **last-layer hidden states** into a receiver's input-embedding space. The inter-agent channel is **non-interpretable continuous activations** with no text decoder and no monitoring. We re-implement the `outer` link ourselves so we control training and instrumentation.

---

## 2026-07-24 research checkpoint

The first complete 3B implementation and controlled arena spine are finished.
The trained link passes its original neutral Alpaca fidelity gate, but it does
not produce a representation-specific coordination advantage in the arena.

- The 8-seed pilot completed 96/96 matches with no parsing repairs.
- The frozen 40-seed IPD run completed 240/240 matches with no parsing repairs.
- End cooperation was 0.3425 with no channel, 0.5025 with text, 0.4600 with the
  trained link, and 0.5375 with the shuffled-link control.
- Pre-registered paired contrasts were trained-minus-text = -0.0425
  (95% paired bootstrap CI [-0.1025, 0.0175]) and
  trained-minus-shuffled = -0.0775 [-0.1400, -0.0175].

This is a negative result for the current adapter, not evidence that latent
semantic transfer improves coordination. The no-channel contrast is not
attributable to link content because zero, random, and shuffled injections also
raise cooperation.

The leading implementation diagnosis is a sender-distribution mismatch. Link
training and validation extract last-layer states from standalone neutral
messages under one fixed receiver context. Arena deployment extracts states from
tokens generated after long, strategic, history-dependent communication
prompts, then injects them after a different receiver prompt. The original gate
does not measure fidelity under that deployment distribution. Also, both the
trained and random-link intent probes scored 1.0, so that probe is
non-discriminative and cannot support a channel claim.

Before another arena run, add an arena-context fidelity gate comparing the
action distribution induced by readable text against trained, shuffled, random,
and zero representations on frozen arena snapshots. If it fails, train a
context-robust link on benign, context-randomized data and require it to beat
same-length controls under the new gate.

### Remaining bounded GPU schedule

Five sequential T4 runs are planned; a sixth is reserved only for one failed
training-gate repair.

1. Arena-context fidelity diagnostic: 20–40 minutes.
2. Context-randomized benign link tuning: 30–60 minutes.
3. Held-out neutral plus arena-context validation: 20–45 minutes.
4. Eight-seed controlled pilot: 50–80 minutes.
5. Fresh 40-seed confirmatory IPD run, only if trained beats shuffled in steps
   3 and 4: approximately 4 hours.
6. Optional single repair iteration: up to 60 minutes.

Expected core GPU time is about 6.5–7 hours. Reserve 8 hours including normal
Colab overhead, or 9 hours if preserving the one-repair contingency. These runs
are dependent and should not be launched in parallel.

---

## 0. The scientific headline (what the paper claims)

> **Is natural language a coordination *bottleneck* and a safety *crutch*?**
> When two *innocently-trained* rival agents talk in representations instead of text:
> 1. **Lever** — does collusion exceed the free-text plateau? (text result: L2≈L3≈0.60 lock-in; K up to 1.23)
> 2. **Oversight** — does our text monitor (AUC 0.88) collapse to chance, and can a *representational probe* restore it (and survive an arms race)?
> 3. **Guardrails** — do token-level safety behaviors (refuse explicit lie 0.00; launder ambient 0.71) transfer to the latent channel, or does it route around them?

**Either direction is publishable.** A null — "language is a sufficient statistic for strategic coordination; representation adds bits, not new coordination" — is a clean, reassuring result. We design for falsifiability.

### The methodological pillar (non-negotiable)
**We never train any link on the rival game.** If the link were trained on PD/Bertrand reward we would be manufacturing collusion. Links are trained only on (a) faithful transmission of neutral text, or (b) a *benign cooperative* benchmark — then frozen agents play the rival game *through* the channel. Any collusion is therefore **emergent**, not trained-in. This, plus the controls in §4, is what lets us attribute effects to *representation* rather than *bits* or *training distribution*.

---

## 1. What we build — our own link

### 1.1 Architecture (the `outer` link)
A 2-layer residual adapter mapping sender hidden states `h ∈ R^{d_src}` into the receiver's embedding space `R^{d_tgt}`:

```python
class OuterLink(nn.Module):
    def __init__(self, d_src, d_tgt, d_hidden=None):
        super().__init__()
        d_hidden = d_hidden or d_src
        self.W1 = nn.Linear(d_src, d_hidden, bias=False)
        self.W2 = nn.Linear(d_hidden, d_tgt, bias=False)
        self.W3 = nn.Linear(d_src, d_tgt, bias=False)   # cross-dim residual map
        nn.init.zeros_(self.W2.weight)                  # start as a near-linear pipe
    def forward(self, h):                               # h: [B, T, d_src]
        return self.W3(h) + self.W2(F.gelu(self.W1(h)))
```
- **Homogeneous (same model both seats):** `d_src == d_tgt`, `W3` initialized to identity — start as an honest pipe.
- **Heterogeneous (RQ5):** `d_src != d_tgt`, `W3` is the learned cross-architecture projection.
- **Throttled (RQ2 dose-response):** insert a `k`-dim bottleneck (`d_src → k → d_tgt`) for `k ∈ {1,4,16,64,full}`.
- (Optional later) an `inner` link for multi-step latent "thought streaming" before exchange; start with a **single exchange per round** for simplicity.

### 1.2 Three training regimes (this *is* the independent variable)
| Link | Objective | Data | What it tests |
|------|-----------|------|---------------|
| **L4-faithful** | Receiver, given only the context + injected latents, predicts the sender's next-token distribution. Loss = `KL(p_sender ‖ p_receiver)` (distillation). | Neutral instruct text (e.g., a slice of open instruction data) | An **honest pipe** — does *emergent* collusion appear through a channel never optimized for the game? |
| **L4-collab** | Maximize joint task accuracy, RecursiveMAS-style. Loss = NLL of the final answer. | A **cooperative** benchmark (math/code QA) | The **realistic deployment** link — does a channel trained for legit teamwork *transfer* to rivalrous collusion? |
| **L4-throttled(k)** | Same as L4-faithful with a `k`-dim bottleneck | same | The **dose-response** in representational capacity |

Only link params train (≤~15M); base models frozen. Per the source, this is **hours on one GPU, tens of dollars**.

### 1.3 The signal-carrying gate (before any arena compute)
After training, verify the channel actually carries strategic content: train a small **decode probe** to recover the sender's intended action / message from the *received* latent. **Go/no-go:** probe recovery must beat chance by a pre-set margin (e.g., balanced acc ≥ 0.70 on intent). If a link is a dead pipe, fix the objective before spending arena GPU-hours. (This probe is reused as the **representational monitor** in RQ3.)

---

## 2. Models (RunPod-friendly, open weights, activation access)

The headline study used 70B-class models via OpenRouter (no activations). L4 **requires last-layer hidden states**, so we self-host smaller open weights and **scope-note** it.

| Tier | Pair | d_model | GPU |
|------|------|---------|-----|
| Primary (homogeneous self-play) | Qwen2.5-7B-Instruct × 2 | 3584 | 1× A100/H100 80GB |
| Mid | Llama-3.1-8B-Instruct × 2 | 4096 | 1× 80GB |
| Cross-arch (RQ5) | Qwen2.5-7B ↔ Llama-3.1-8B | 3584↔4096 | 1–2× 80GB |
| Scale robustness (1 cell) | Qwen2.5-32B × 2 | 5120 | 2× 80GB |

Rationale: cheap, fast, and we already use these families. **Honesty caveat to carry in the paper:** L4 results are scoped to 7–32B open models; hosted frontier models (Claude/Gemini/GPT-4o) cannot be wired this way (no weights) — same scoping discipline as Round 1.

---

## 3. The L4 channel protocol (reuses every game + metric)

Only the **inter-agent message medium** changes. The **action stays observable**: agents still emit a discrete action token (cooperate/defect, or a price) and an optional readable scratchpad — so C / W / K / covert-MI and the monitor all keep working. The latent is the *chat*, not the move.

Per round:
1. **State:** each agent gets the game-state prompt (text).
2. **Comm phase (latent at L4):** agent A runs forward with `output_hidden_states=True`; take last-layer hidden states over a fixed comm span `H_A` (m≈16–80 steps, ablate). Map `Ĥ_A = OuterLink(H_A)` and feed B via `inputs_embeds = concat(embed(B_prompt), Ĥ_A)`. Symmetric for B. (1 exchange to start; ablate 2.)
3. **Action phase:** each agent emits its action token(s) + private scratchpad as **text** (logged, readable).
4. **Log:** action, scratchpad, **and the raw/received latents** (for probing, decoding, covert-MI).

Engineering note: this is a **Transformers-based custom loop** (`output_hidden_states`, `inputs_embeds`) — *not* vLLM/OpenRouter, which don't expose/inject activations. New module: `code/rival_arena/harness/local_activation_runner.py` + an `L4` channel object alongside the existing text channel; game logic, payoffs, and metrics unchanged.

---

## 4. Experiment matrix

**Games:** A1 (repeated PD → lock-in `C`, Wilson CI) and B1 (Bertrand → `K`, bootstrap CI). Two-speed protocol: confirmatory spine = A1/B1 with fresh seeds (offset 200, new wave); exploratory = the rest.

**Channel rungs (the dose):** `L0 none · L1 menu · L2 observed-text · L3 private-text · L4-faithful · L4-collab · L4-throttled(k)`.

**Pre-registered primary contrast:** `L4-faithful vs L3` risk-difference on lock-in (PD) and ΔK (Bertrand). Secondary: `L4-collab vs L3`, `L4 vs L4-throttled` dose curve.

**The controls that make the claim (each isolates a confound):**
| Control | Isolates |
|---------|----------|
| **Bandwidth-matched text** (very long text messages) | *bits* vs *representation* — if long text matches L4, the effect is bandwidth, not "neuralese" |
| **Text-bottleneck latent** (activation → decode-to-text → re-encode) | the **non-linguistic** contribution specifically |
| **Strategic-info ablation** (zero / shuffle the received latent) | proves coordination rides the channel, not the link's prior or the prompt |
| **Observable-to-us latent** (a link we *can* decode) vs not | decouples "representational" from "unmonitorable" |

**Metrics:** lock-in proportion + Wilson CI; K + bootstrap CI; covert mutual information; **text-monitor AUC** (→ chance on L4 by construction) vs **representational-probe AUC**; leak/honesty rate for the RQ4 lab scenario.

**Power:** reuse the text-experiment per-cell SDs to size n for the L4-vs-L3 risk-difference (target detect ≥ the L2-vs-L1 effect size we already saw, RD≈0.60, at 80% power → small n; budget for ≥ that with margin, e.g. 30–60 seeds/cell on the spine).

### Mapping to the RQs from the prior discussion
- **RQ1 (new rung/plateau):** L4-faithful vs L3 primary contrast + the three controls.
- **RQ2 (continuity):** L4-throttled(k) dose curve; place L1/L2 on the same effective-bits axis.
- **RQ3 (oversight collapse + probe arms race):** text-monitor AUC on L4 (expect ≈0.5) vs representational-probe AUC; then elicit/fine-tune the link to evade the probe and re-measure.
- **RQ4 (guardrail transfer):** rerun the lab leak/honesty scenario delivering the payload via explicit-text / ambient-text / **latent**; compare leak rates (expect latent ≥ ambient ≫ explicit if safety is token-level).
- **RQ5 (heterogeneous bridging):** cross-arch link on pairs that floored in text; does latent lift them off 0.00?
- **RQ6 (emergent code):** decode received latents to nearest tokens per round; track text-decodability vs covert-MI over time.

---

## 5. RunPod infrastructure & runbook

- **GPU:** start 1× A100 80GB (community/spot ~$1.5–2.5/hr); 2× for cross-arch/32B. H100 if throughput-bound.
- **Image:** PyTorch 2.x + Transformers + accelerate + our repo; pin CUDA. A `Dockerfile` in this folder (to author in Phase 0) for reproducibility.
- **Persistent volume:** model weights (HF cache), link checkpoints, transcripts + saved activations, results. Keep raw activations only for sampled matches (storage).
- **Skeleton commands:**
  ```bash
  # Phase 0 smoke (tiny): prove extract+inject works through a RANDOM link
  python -m rival_arena.harness.local_activation_runner --smoke --model Qwen2.5-7B-Instruct
  # Phase 1: train a link (only link params), then gate on the probe
  python scripts/train_link.py --regime faithful --model Qwen2.5-7B-Instruct --steps 2000
  python scripts/probe_link.py --link ckpts/faithful.pt   # go/no-go: intent recovery
  # Phase 2: run the arena at a rung
  python scripts/run.py a1 --pair qwen7b_self --channel L4 --link ckpts/faithful.pt --seeds 40 --seed-offset 200
  python scripts/run.py b1 --pair qwen7b_self --channel L4 --link ckpts/faithful.pt --seeds 40 --seed-offset 200
  ```
- Checkpoint/resume like the rest of the apparatus; a kill/sleep costs only in-flight matches.

---

## 6. Budget (ranged)

| Item | Estimate |
|------|----------|
| Link training (3 regimes × a few model pairs, hours each on 1 GPU) | **$20–80** |
| Phase-0/1 dev + debugging GPU time | **$80–200** |
| Arena matrix (spine + controls + exploratory, many short forward passes) | **$300–800** |
| Storage (persistent volume, weeks) | **$20–60** |
| **Total** | **≈ $500–1,200** (contingency to $1,500) |

The adapter is cheap; the cost is **local serving for the arena**, controlled with the two-speed protocol (small powered spine; cheap exploratory catalog).

---

## 7. Timeline & go/no-go gates

| Phase | Days | Work | Gate |
|-------|------|------|------|
| **0 — Plumbing** | 2–3 | Transformers two-agent loop; `output_hidden_states` + `inputs_embeds` injection; one PD match through a *random* link | Pipeline runs end-to-end, no NaNs, action tokens still emitted |
| **1 — Train + verify links** | 3–5 | Train L4-faithful & L4-collab (+ throttled); run the decode probe | **Probe recovers intent > chance** (else fix objective) |
| **2 — Run the arena** | 5–8 | Full rung × game × control matrix on the spine; exploratory extras; RQ4 lab scenario | Cells complete; refusal/API-error rates acceptable; primary contrast estimable |
| **3 — Analyze + write** | 5–8 | Reuse `stats_audit` pipeline; figures; draft the follow-up paper | Pre-registered contrasts reported with CIs; controls attribute the effect |

≈ **3–4 weeks part-time.**

---

## 8. Risks & kill criteria

- **Injection off-distribution derails the receiver** → normalize/scale injected embeddings to match the receiver's embedding statistics; cap exchange length; match LayerNorm; ablate inject position. *Kill:* if receivers can't generate coherently with injected latents after Phase 0, fall back to "text-bottleneck latent" as the floor channel and reframe.
- **`inputs_embeds` semantics differ per model** (positions, attention mask, BOS handling) → per-model adapter shims; caught in Phase 0.
- **Link transmits nothing strategic** (esp. L4-faithful) → the probe gate catches it; if needed add a distillation target that guarantees content. A genuine null *with a passing probe* is a real (publishable) result, not a failure.
- **Compute overrun** → strict two-speed protocol; cap seeds; spot instances with checkpointing.
- **Over-claiming** → never report L4-vs-L3 without the bandwidth-matched-text and text-bottleneck controls. Scope every claim to "these open models, this arena," as in Round 1.
- **Ethical/safety framing** → this studies *covert coordination and oversight evasion*; keep it defensive/measurement-focused, sandbox the lab scenarios (`assert_contained()`), release link checkpoints with a clear "for safety research" note.

---

## 9. Deliverables & the follow-up paper

- **Code:** `local_activation_runner.py`, `OuterLink`, `train_link.py`, `probe_link.py`, an `L4` channel object, a RunPod `Dockerfile` — all in the repo.
- **Artifacts:** trained link checkpoints, configs, seeds, transcripts + sampled activations → Zenodo + GitLab.
- **Paper (working title):** *"Beyond Language: A Representational Channel for Rival LLM Agents — Does Removing the Linguistic Bottleneck Create Collusion Text-Based Oversight Can't See?"*
  - Contributions: (1) the L4 rung + our open, instrumented link; (2) emergent-collusion result (either direction) with the bits/representation decomposition; (3) oversight-collapse + representational-probe arms race; (4) guardrail-transfer test; (5) disciplined scope.
  - Venue: arXiv superset + a NeurIPS/ICLR **safety or multi-agent workshop** (matches our existing track strategy); apparatus + games reuse is a selling point.
  - Honesty: confirmatory spine vs exploratory labeling preserved; the null is reported as a result, not buried.

---

## 10. Open decisions for Harry
1. **Green-light local hosting?** (the one gating decision — moves us off OpenRouter for this study).
2. **Budget ceiling** on RunPod ($500 lean / $1,200 full / $1,500 with contingency)?
3. **Model tier:** 7–8B primary only, or include the 32B robustness cell?
4. **Scope of v1 paper:** lead with RQ1+RQ3 (lever + oversight) and hold RQ4/RQ5/RQ6 for a longer version, or go comprehensive in one shot?
5. Want me to **scaffold Phase 0** now (the Transformers two-agent loop + `OuterLink` + a smoke test) so it's ready to `git clone` onto a RunPod box?
