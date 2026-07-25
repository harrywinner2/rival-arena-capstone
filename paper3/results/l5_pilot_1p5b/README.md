# L5 pilot attempt — Qwen2.5-1.5B (behavioural test VOID)

Executed notebook with outputs, run on Colab T4, 2026-07-25.

## Outcome

**The capability gate FAILED and the run continued anyway** (a notebook bug, since fixed).
The behavioural result is therefore **not interpretable** and must not be cited.

### Salvageable: channel fidelity replicates

| payload | KL | top-1 |
|---|---:|---:|
| token oracle | -0.00008 | 1.000 |
| trained | **0.032** | 0.922 |
| shuffled | 2.189 | 0.031 |
| zero | 11.152 | 0.000 |
| random | 7.008 | 0.000 |

The exact-token oracle passes, so the matched receiver layout is correct, and the trained
link beats every same-length control by two orders of magnitude. The adapter transmits
faithfully at 1.5B.

### Void: the behavioural 2x2

Gate: `none` 0/24 = 0.000, `text` 0/24 = 0.000; text - none = +0.000, lower bound -0.138.
Qwen2.5-1.5B never locks in under ANY condition, matching the prior L4 finding of no text
effect at this scale. Every L5-C arm returned 0.000 lock-in and every contrast
+0.000 [-0.243, +0.243]. That is a **floor effect, not a null**.

Mean cooperation did vary (latent arms 0.29-0.40, `latent_zero` highest at 0.404, text
0.05-0.07, none 0.02). A content-free payload scoring highest is the payload-position
artefact identified in L4; with lock-in pinned at zero we draw nothing from it.

## Bugs this run exposed (both fixed)

1. The gate printed FAIL without halting. It now raises `SystemExit`.
2. Ledger keys were `arm|seed` with no model tag, so raising `MODEL_ID` would have
   SKIPPED these 84 units and reported 1.5B numbers under a larger model's name — a
   silent wrong answer. Ledgers and stage markers are now namespaced by model.

## To get a real result

Set `MODEL_ID` to `Qwen/Qwen2.5-7B-Instruct` or `-14B-Instruct` (needs an A100, not a T4)
and run from cell 2. The gate will stop you if that scale also fails.
