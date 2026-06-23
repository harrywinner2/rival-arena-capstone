# Rival Arena — Interactive Games · Shared Design Brief

**Read this fully before building. Every game must honor the facts, philosophy, brand, and tech rules here.**

---

## Mission
Build a small, beautiful, interactive **web game** that lets a live audience (a capstone jury + general public) *feel* one finding of the **Rival Arena** research. A juror should walk up, drag one control, watch two AI agents change behavior, see the consequence land on a human — and get the point in ~20 seconds, then want to replay at a different setting.

## The research in one paragraph
We put two LLM agents in repeated economic games and turned exactly **one knob at a time**. The dominant lever that flips rivals from *competing* into *coordinating* is **semantic bandwidth** — how much real content they can exchange. Free text flips rivals into cooperators/colluders; a fixed *menu* of canned signals does almost nothing (it is a perfect lie). In pricing markets this coordination becomes **supracompetitive collusion against the consumer, unprompted.** And a principal's defenses are weaker than they look: a monitor that *detects* collusion at near-ceiling rates *prevents* almost none of it; firm guardrails are *literal* — agents refuse a direct request to lie but launder a misleading fact handed to them indirectly.

## Unifying thesis (the feeling every game should leave)
The lever is **semantic bandwidth**. The principal's defenses — watching, auditing, a literal rule — are weaker and more literal than they look. **You**, by setting the channel, are making a safety decision, often blind.

---

## The faithful numbers (do NOT contradict these; label scripted dialogue honestly)

**The affordance ladder (the knob in most games):**
- **L0 — none:** no channel between the rivals.
- **L1 — menu / signal:** a fixed set of canned messages (a "I'll cooperate" button). *Statistically indistinguishable from silence.*
- **L2 — free text (observed):** open messaging the principal can read.
- **L3 — free text (private):** open messaging the principal CANNOT read.

**Finding 1 — Content is the lever (repeated Prisoner's Dilemma, "lock-in" = sustained mutual cooperation):**
- Lock-in by rung: **L0 = 0.15 · L1 = 0.00 · L2 = 0.60 · L3 = 0.60.**
- Free text ≫ menu: risk-difference **+0.60 [+0.33, +0.78], p = 3×10⁻⁵.** The menu does *nothing*.
- *Why the menu fails — the deception exhibit (verbatim flavor):* agent **says** "I intend to cooperate"; private **scratchpad** "the optimal strategy is to defect… maximizes my payoff"; **plays DEFECT.**

**Finding 2 — Rival pricers collude, unprompted (Bertrand pricing; collusion index K: K=0 competitive, K=1 monopoly):**
- **L0 → price war**, prices *below* competitive (K ≈ −0.36).
- **L3 private → K = 1.23 [0.95, 1.54]** — *above* the monopoly point (supracompetitive). Sustained by threatening to *punish* anyone who breaks ranks. No one prompted it. Survives a brand-new demand curve.
- Replicates on a frontier model (GPT-4o): K **0.19 → 0.81** with a channel.

**Finding 3 — Oversight detects ≠ prevents:**
- A monitor flags collusion at **0.85–1.00** detect-rate while K barely moves (**0.44 / 0.46 / 0.58**). Watching ≠ deterring.
- An actual **penalty** can deter — dropped K **0.33 → 0.18** (−42%) in one cell — but it's **cell-dependent** (elsewhere the same penalty did nothing).
- The monitor is genuinely discriminative (**ROC AUC 0.88**) but **mis-thresholded**: at its default it flags every innocent round; recalibrating the threshold cuts false-positive cost **1.00 → 0.00.**

**Finding 4 — The guardrail is literal (exploratory; a sandboxed "lab" scenario):**
- **0/16 leaks** of a proprietary secret under a firm "do not share" instruction — even under a desperate rival's pleas. Misalignment tracks the *instruction*, not the rival's emotion.
- Dose-response as the instruction weakens (P0→P5): **0 / 0 / 0.19 / 0.19 / 0.50 / 0.50.**
- Ask the agent to lie → **refused (0.00).** Hand it the *same* misleading status as **ambient context** → **laundered (~0.71).** Making it auditable does **not** fix it (~0.71 unobserved vs ~0.77 observed). Surveillance is not the lever.
- Covert collusion is a **latent capability:** left alone agents don't hide it; *elicited*, detection drops **0.97 → 0.32** while K rises **0.31 → 0.96.**

> Honesty rule: the **numbers** above are our measured results — keep them accurate. Agent **dialogue** in a game is illustrative/scripted (modeled on real transcripts); say so in one line in the EXPLAINER. Never present a scripted number that contradicts the table above.

---

## Design philosophy (non-negotiable)
1. **Show the world, not the metric.** Never make a bare number ("collusion index = 1.23") the payload. Render what it *means*: prices on a sign, a draining wallet, a trapped crowd, a backstab, a mushroom cloud, a fraying leash. A small honest metric readout is fine as secondary HUD — never the star.
2. **Every agent decision = a visible event.** A message sent = an animated bubble/thread between agents. A price chosen = a sign flips and recolors. A defection = a backstab. The viewer must *see* the causation.
3. **The knob is the star.** The player sets communication bandwidth (the L0→L3 ladder) and the outcome visibly changes. That is the core interaction. Make dragging it feel consequential.
4. **One "aha".** Each game lands a single surprising beat (e.g., "the menu button did nothing," "the alarm blares but the crime continues," "no one told them to," "you got peace by losing control").
5. **Cinematic, not infographic.** Anticipation → action → payoff. Easing, particles, sound-optional. It should feel like a game.

## Brand / visual system
- Background near-black `#0a0a0a` (radial vignettes welcome). Ink `#f4f1ea`. Muted `#9a948a`.
- Accents: gold `#c09e5a`, cyan `#00d4ff`, coral `#ff6b6b`, good-green `#2fd08a`.
- Fonts via Google Fonts with **system fallbacks** (must still look good offline): "Space Grotesk" (display), "Inter" (body), "JetBrains Mono" (numbers / agent text).
- Mood: premium, dark, quietly tense — a sleek war-room / trading-floor / lab. Generous spacing, restrained palette, purposeful motion.

## Tech constraints
- Self-contained `games/<slug>/`. Entry `index.html`. **Vanilla** HTML/CSS/JS — no build step. Canvas2D and/or SVG for animation. Tiny CDN helpers allowed only if they degrade gracefully offline; prefer **zero** dependencies.
- Must run via a static server (`python3 -m http.server`) and tolerate `file://`. Works fully **offline** at runtime (Google Fonts optional; system-font fallback required).
- **Replay/scripted data** lives in the folder (`data.js`/`data.json`), faithful to the numbers above. **Never put the OpenRouter key in client code.** An optional "live" mode is allowed ONLY via a local proxy server (key from env), OFF by default and documented — but replay must be the fully self-sufficient default.
- Smooth animation via `requestAnimationFrame`; honor `prefers-reduced-motion`. Responsive 1280×800 → 1920×1080. Keyboard-operable controls + aria labels + good contrast.

## Deliverables (every game)
1. `games/<slug>/index.html` (+ any css/js/assets in the folder).
2. `games/<slug>/EXPLAINER.md` — **short**: *What it is* (2–3 sentences) · *How to play* (3–5 bullets) · *What it says about our work* (the finding + thesis, 3–4 sentences) · *Faithful to* (which finding/numbers + the one-line dialogue-is-illustrative note).
3. **Self-verify before finishing:** serve it, drive it with headless Chromium (Puppeteer is installed at `/tmp/pdfgen` — `cd /tmp/pdfgen && node` with `require('puppeteer')`), screenshot key states, confirm **no console errors** and that it renders and animates. Iterate until it looks genuinely good, not a first draft.
