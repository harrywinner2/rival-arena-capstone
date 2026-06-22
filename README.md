# Rival Arena

### Communication Affordances and Principal-Harming Coordination among Rival LLM Agents

> **The core question:** *Can the AIs we deploy as **rivals** — pricing bots on the same marketplace, negotiating agents on opposite sides of a deal, competing copilots — cooperate or collude against the **principal** who deployed them?*

**Authors:** Harry Fezeu ([ORCID 0000-0002-8632-1459](https://orcid.org/0000-0002-8632-1459)), Dhairya Surana, Thalia Rossitter, Tyler Xia — **Gauntlet AI**.

We built a factorial "rival arena": two LLM agents play repeated economic games, and we turn exactly one knob at a time — communication **bandwidth**, incentive **regime**, model **family** — to find what flips rivalry into coordination *against the operator*, and whether that operator can catch it or stop it.

---

## TL;DR — Key findings

We label every claim **[C] confirmatory** (pre-registered spine, fresh held-out seeds, offset 100) or **[E] exploratory** (the wider catalog and the alignment wave). **After a peer review flagged that our rhetoric had outrun our statistics, we re-analyzed the existing data — zero new API spend — and corrected our own headline claims.** Those corrections are baked into the table below and are, frankly, the part of this project we trust most.

| # | Finding | Numbers | Tier |
|---|---------|---------|------|
| 1 | **Free text is the lever.** A free-text channel flips rivals from defection to cooperation; a fixed *menu* signal does not help. The robust, direct contrast is free-text ≫ menu. | lock-in **0.15 → 0.60** (L0 → L2); free-text vs menu **RD +0.60 [+0.33, +0.78], p = 3e-5**; effect holds on novel payoffs and at lock-in cuts C>0.7/0.8/0.9 | **[C]** |
| 2 | **Rival pricers collude, unprompted.** With a channel, two Bertrand agents climb to supracompetitive prices via dynamic punishment — no one told them to. | collusion index **K up to 1.23 [0.95, 1.54]** (supra-monopoly, CI above 1); survives a **novel demand curve**; **replicates on GPT-4o (K 0.19 → 0.81)** | **[C]** |
| 3 | **Some frontier models price high with no channel — but that's *independent* pricing, not coordination.** Claude self-pairs pin the grid-max price from round 1. We checked the trajectories: no convergence, no negotiation. The harm is real; the mechanism is a fixed disposition. | Claude self **K = 1.29 at L0**; \|p_A−p_B\|=0, 0/12 matches show any price change; genuine coordination signature (dispersed→converging) appears only on the open/GPT spine *with* a channel | **[E]** |
| 4 | **Oversight detects but does not prevent.** A monitor flags collusion at near-ceiling rates while K barely moves. It is discriminative but was mis-thresholded; calibration fixes the false alarms; enforcement deters only sometimes. | detect-rate **0.85–1.00** with K flat; monitor **AUC 0.88** but FPR 0.48 at default threshold; **calibration cuts false-positive cost 100% → 0%**; penalty deters in one cell (K 0.33 → 0.18) but not another (ΔK ≈ 0) | **[E]** |
| 5 | **The guardrail is literal.** Agents refuse a *direct* request to lie about a failing peer, but passively launder a misleading status delivered as *ambient* context — and making the channel auditable does **not** fix it. Surveillance is not the lever. | refuses explicit "lie for me" (**0.00**); launders ambient misleading status (**~0.71**); de-confounded n=48: unobserved **0.71** vs observed/accountable **0.77** (flat) | **[E]** |
| 6 | **Covert collusion is a latent capability.** Left alone, agents don't hide collusion from the monitor. Elicited, they clearly can — so "they don't hide it" really means "they don't hide it *yet*." | spontaneous null (C7); when elicited, detection **0.97 → 0.32** while **K 0.31 → 0.96** (C8) | **[E]** |

**Unifying thesis:** the dominant lever that turns rivals into principal-harming coordinators is **semantic bandwidth** — how much *content* an agent can convey (menu → free text). The second axis you'd reach for — observation, accountability, auditing — is a far weaker and more *literal* control: watching detects but doesn't deter, and a firm rule protects exactly what it names while indirect/ambient routes slip through.

**Honesty notes.** Confirmatory claims rest on the pre-registered spine (A1, B1, A3) on fresh seeds; everything else is exploratory and labeled so. We do **not** claim "origin doesn't matter" (the equivalence test fails — it is non-significant and under-powered). We dropped "tacit collusion" for the frontier no-channel cells (it is independent supracompetitive pricing). The alignment results are exploratory boundary conditions from a single sandboxed task family. Scope every claim to **"these models, this arena."**

---

## What's in this repo

```
.
├── README.md  ·  LICENSE
├── paper/                # the three venue versions (each: PDF + LaTeX + refs.bib + main.bbl + figures/ + SUBMISSION_NOTES.md)
│   ├── arxiv/            #   the SUPERSET (everything) — cs.MA primary
│   ├── gamesec/          #   GameSec 2026 — Springer LNCS (security framing)
│   ├── neurips_ws/       #   NeurIPS workshop — safety framing
│   └── README.md         #   per-track submission guide
│
├── presentation/
│   ├── deck/             # Gauntlet-branded reveal.js slide deck — open index.html
│   ├── website/          # interactive findings website — open index.html (+ PRESENTER_GUIDE.md)
│   ├── video/            # narrated explainer video — explainer.mp4 (+ build_video.py)
│   └── SCRIPT.md         # the master narrative (deck + video voiceover + website copy + jury Q&A)
│
├── code/                 # the experiment apparatus
│   ├── rival_arena/      #   env/ (games + classical baselines), harness/ (two-model loop, channel
│   │                     #     ladder, monitor, LLM client), metrics/ (C/W/K/τ/σ, covert MI, stats),
│   │                     #     labs/ (sandboxed alignment Lab), viz/
│   ├── experiments/      #   ~30 drivers: a1_channel, b1_pricing, a3_origin, c7/c8_covert, e1/s1/s2, m1/m2, …
│   ├── scripts/          #   run.py · run_program.py · smoke_test.py · stats_audit.py · paper_figures.py
│   ├── tests/            #   unit tests (env, metrics, labs, ROC, S1/S2, LLM failover)
│   ├── configs/          #   models.yaml — the model matrix + named pairs
│   └── requirements.txt
│
├── results/
│   ├── figures/          # f1–f12 vector PDFs
│   ├── data/runs/        # per-run summary tables (summary.json, metrics.csv) — curated, not the raw bulk
│   ├── master_long.csv   # tidy per-round table (the figure source)
│   ├── stats_audit.md/.py# the reviewer-driven statistical audit (direct tests, bootstrap CIs, diagnostics)
│   └── SUMMARY.txt
│
└── docs/                 # paper_facts.md (source of truth) · results_log.md · stats_audit.md
                          #   · citation_audit.md · findings.md · novelty_scan.md
```

Each venue directory (`paper/arxiv/`, `paper/gamesec/`, `paper/neurips_ws/`) is self-contained: a compiled **PDF**, the **LaTeX source**, `refs.bib` (44 vetted entries), a pre-built `main.bbl`, a `figures/` folder, and a `SUBMISSION_NOTES.md`. The `arxiv/` version is the superset; `gamesec/` leads with the security framing (collusion generality, a monitor-calibration defense), and `neurips_ws/` leads with the safety framing (latent covert capability, the ambient-context manipulation route).

---

## How to use each artifact

| I want to… | Do this |
|---|---|
| **Read the paper** | Open `paper/arxiv/main.pdf` (full version) — or `paper/gamesec/main.pdf` / `paper/neurips_ws/main.pdf` for the venue cuts. |
| **See the slides** | Open `presentation/deck/index.html` in any browser (self-contained reveal.js deck). |
| **Explore the findings interactively** | Open `presentation/website/index.html` in a browser. See `presentation/website/PRESENTER_GUIDE.md`. |
| **Watch the explainer** | Play `presentation/video/explainer.mp4` — a 17-min narrated walkthrough + a jury-Q&A defense section. |
| **Check the numbers** | Read `docs/paper_facts.md` (authoritative source of truth), `docs/stats_audit.md`, and `docs/results_log.md`. |
| **Reproduce results** | See below. |

---

## Reproduce the experiments

```bash
cd code            # the apparatus + scripts live here

# 1. Environment
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Offline smoke test — verifies the whole pipeline end-to-end, ZERO API spend
python scripts/smoke_test.py

# 3. A confirmatory-spine experiment, live (needs OPENROUTER_API_KEY in .env)
python scripts/run.py a1 --pair cross_origin --seeds 20

# 4. The same experiment offline, with a deterministic MockLLM — no spend
python scripts/run.py a1 --pair cross_origin --seeds 20 --mock
```

**No API spend by default.** `scripts/smoke_test.py` and `--mock` run a deterministic `MockLLM`, so you can develop and demo the entire apparatus offline. Live runs route through **LiteLLM → OpenRouter** (Qwen2.5-72B, DeepSeek-V3, Llama-3-70B, Mistral-Large, plus GPT-4o / Claude frontier anchors) and require `OPENROUTER_API_KEY`.

**Containment.** Every alignment scenario (E1 / S1 / S2) runs on a **sandboxed in-memory Lab** (`code/rival_arena/labs/`): all tools are mocked and `assert_contained()` is enforced — nothing real ever leaves the process.

**Protocol.** ~30 experiment families under a deliberate **two-speed protocol**: only the pre-registered spine (A1, B1, A3) gets *confirmatory* statistics on fresh held-out seeds (offset 100, Wilson CIs, bootstrap K, the `prereg/` specs); the wider catalog runs *exploratory* and is labeled as such. Runs are checkpointed — a kill/sleep costs only in-flight matches; re-run the same command to resume.

---

## Data & preprint

- **Full preprint + reproducibility data:** **Zenodo — https://zenodo.org/records/20792312** (paper PDFs, LaTeX, prompts, model ids, seeds, manifests, raw tables, and figure scripts).
- **Submitted to:** **GameSec 2026** (Conference on Decision and Game Theory for Security).
- **Scope statement:** all claims are scoped to *these models, this arena* — four open models plus three frontier families, English-only, one scaffold, hosted inference with unpinned quantization.

---

## License

- **Code** (`rival_arena/`, `experiments/`, `scripts/`, `tests/`, `configs/`): **MIT**.
- **Paper, figures, and slides**: **CC BY 4.0**.

---

## Citation

```bibtex
@misc{fezeu2026rivalarena,
  title        = {Communication Affordances and Principal-Harming Coordination
                  among Rival LLM Agents},
  author       = {Fezeu, Harry and Surana, Dhairya and Rossitter, Thalia and Xia, Tyler},
  year         = {2026},
  howpublished = {Preprint, Zenodo},
  doi          = {10.5281/zenodo.20792312},
  url          = {https://zenodo.org/records/20792312},
  note         = {Submitted to GameSec 2026. Gauntlet AI.}
}
```
