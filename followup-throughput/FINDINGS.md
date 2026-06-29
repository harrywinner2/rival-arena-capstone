# Findings — Collusion vs communication throughput (SMS probe)

*Exploratory probe run to seed the "coming next" slide. Two model pairings, one
game (repeated pricing duopoly), 20 seeds × 8 throughput levels = 160 matches each.
Throughput = SMS credits per agent (each SMS ≤60 chars); 0 credits = no channel,
12 = can text every round. Collusion = sustained mutual HOLD (high price) against
the buyer. Pair = Qwen-2.5-72B × {Llama-3.3-70B, DeepSeek-V3}.*

## The result in one line
**Collusion rises with communication throughput — but the *price* of collusion is
set by who's talking. A pair already inclined to collude needs just ONE 60-character
text to jump from 45% → 80% lock-in; a competitive pair needs a sustained channel
(8+ texts) before collusion moves at all.**

## The three findings

**1. The continuous knob works, and collusion grades up with it.**
Unlike the Paper-1 ladder (none / menu / free-text — three discrete points), the SMS
credit budget turns throughput as a *continuous* dial, and collusion tracks it in
**both** pairings (Spearman ρ > 0 in both; same sign for *allowed* and *used*
throughput). The discrete ladder couldn't show a dose-response; this can.

| Throughput (SMS credits) | 0 | 1 | 2 | 3 | 4 | 6 | 8 | 12 |
|---|---|---|---|---|---|---|---|---|
| **Qwen×Llama** lock-in | 0.00 | 0.10 | 0.15 | 0.20 | 0.05 | 0.20 | 0.25 | **0.30** |
| **Qwen×Llama** mutual-HOLD | 0.20 | 0.21 | 0.25 | 0.34 | 0.21 | 0.42 | 0.40 | **0.45** |
| **Qwen×DeepSeek** lock-in | 0.45 | 0.80 | 0.70 | 0.80 | 0.75 | 0.90 | 0.75 | **0.95** |
| **Qwen×DeepSeek** mutual-HOLD | 0.54 | 0.80 | 0.72 | 0.83 | 0.76 | 0.88 | 0.82 | **0.91** |

*(n=20/cell, Wilson CIs in `results/summary.json`. ρ: Qwen×Llama +0.14 (marginal,
p≈0.08); Qwen×DeepSeek +0.23 (p≈0.003).)*

**2. The headline: how *much* throughput collusion needs is pair-dependent.**
- **Qwen×DeepSeek — coordination is cheap.** Already 45% locked in with *no* channel;
  a **single SMS nearly doubles it (0.45 → 0.80)**, significant at **1 credit** (Fisher
  p<0.05). Then it saturates near the ceiling. For this pair you *cannot throttle your
  way to safety* — one text is enough.
- **Qwen×Llama — coordination is expensive.** Starts at **0** collusion (they compete);
  throughput has to climb to **8+ SMS** before collusion rises significantly (Fisher
  p=0.047), and even a full channel only reaches ~0.30 lock-in / 0.45 HOLD.

So the question we'd been asking — *"is coordination cheap?"* — has **no single
answer**: it's gated by the pair's baseline disposition to collude. A throttle is a
strong safety lever for one pair and nearly useless for another.

**3. Allowed vs used: agents value the channel — they spend almost all of it.**
*Used* throughput tracks *allowed* almost 1:1 up to ~8 credits (agents send on nearly
every credit they're given), and only ration mildly at large budgets (≈21–22 of 24
possible SMS at 12 credits). They don't treat texts as free spam to dump, nor as
precious to hoard — they use a scarce channel nearly fully. Because used ≈ allowed,
the used-throughput collusion curve mirrors the allowed one (`f2_used_throughput.png`).

## Figures (`figures/`)
- `f1_allowed_throughput.png` — collusion vs allowed throughput, both pairings (the slide).
- `f2_used_throughput.png` — collusion vs the throughput agents actually used.
- `f3_allowed_vs_used.png` — the rationing gap (used vs allowed).

## Honesty / scope
Exploratory: 2 pairings, 1 game, 1 scaffold, n=20/cell, hosted open models. The
binary lock-in metric is noisy (Qwen×Llama's curve is non-monotonic from sampling
noise; the continuous HOLD rate is cleaner). The Qwen×Llama gradient is *weak/marginal*;
the Qwen×DeepSeek effect is strong. Agent SMS text is real model output; the dollar
payoffs are the scripted game. **We did not hunt for pairings that show the effect** —
we ran a competitive pair and a cooperative pair and report both. This is the **text**
throughput curve, which confounds bits with message content; the clean, continuous,
non-confounded version (a representational channel throttled to *k* latent dimensions)
is the planned **Paper 2** headline (`../followup-representational/PLAN.md`, RQ2).

## For the deck — the "coming next" slide
> **Title:** *Next: how much communication does collusion actually need?*
> **Visual:** `f1_allowed_throughput.png` (the two-pair throughput curve).
> **Beat 1:** We gave each rival agent a phone — one 60-char SMS per round, a finite
> budget of texts. Turning that budget is a *continuous throughput knob* the on/off
> ladder never had.
> **Beat 2:** Collusion rises with throughput. But the price is pair-dependent — one
> pair locks in collusion with a **single text**; another needs a **sustained channel**.
> **Beat 3 (the hook):** So "just rate-limit the bots" is not a reliable safety lever.
> The next paper turns this knob cleanly — throughput = latent dimensions of a
> representational channel — to map the full collusion-vs-capacity curve.
