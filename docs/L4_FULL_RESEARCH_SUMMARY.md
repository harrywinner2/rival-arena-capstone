# Beyond Text in Rival Arena: Full L4 Research Summary

**Project:** Gauntlet capstone follow-up  
**Research period:** July 22–24, 2026  
**Repository branch:** `l4-colab`  
**Primary model:** `Qwen/Qwen2.5-3B-Instruct`  
**Compute:** Google Colab Pro, NVIDIA Tesla T4, standard RAM  
**Status:** Experiment program complete; GPU stop gate reached

## Executive summary

This study asked whether two frozen language-model agents coordinate more
effectively when they communicate through learned continuous representations
rather than human-readable text.

We built and trained an `OuterLink` adapter that maps a sender model's
last-layer hidden states into the receiver model's input-embedding space. The
base language model remained frozen throughout. Link training used only neutral
Alpaca assistance examples—never Prisoner's Dilemma, pricing, rival-game
histories, actions, rewards, collusion labels, or monitoring data.

The final result is a scoped negative:

> A learned continuous channel can faithfully reproduce text-conditioned action
> distributions, but that fidelity did not produce greater sequential
> cooperation than readable text, shuffled representations, or even
> content-free controls in Qwen2.5-3B self-play.

This conclusion rests on two distinct findings:

1. **Channel capability succeeded.** After repairing a deployment-layout
   confound, the trained representation reproduced held-out text-conditioned
   action distributions substantially better than random, shuffled, or zero
   representations.
2. **Behavioral transfer failed.** In a fresh controlled IPD pilot, the trained
   channel did not increase cooperation. It equaled shuffled representations at
   the endpoint, trailed readable text, and was no better than no communication.

The project also produced an important methodological result: a link can pass a
standard neutral continuation-fidelity test while failing in its actual
multi-agent deployment context. Exact token embeddings themselves failed until
text and latent payloads were placed after the same receiver prompt. Therefore,
future latent-communication studies need a deployment-specific oracle control
and matched payload placement before interpreting behavior.

## Research question

The original Rival Arena capstone established that richer natural-language
channels can increase cooperation in repeated social dilemmas and raise prices
in competitive markets. The L4 follow-up tested a new rung:

- **L0:** no communication;
- **text:** human-readable free-form communication;
- **L4 trained:** sender hidden states mapped into receiver embedding space;
- **random:** same architecture with an untrained map;
- **zero:** correctly shaped all-zero payload;
- **shuffled:** trained payload with token order permuted.

The primary question was whether the learned non-text channel exceeded the
coordination attainable through text. The attribution question was whether any
effect depended on semantic information rather than payload length, position,
or distribution shift.

## System built

### Adapter

`OuterLink` is an 8.39-million-parameter residual mapping:

- a linear residual projection;
- a two-layer GELU update path;
- a learned gate;
- output LayerNorm.

For the primary 3B runs, source and target dimensions were identical because
both agents used Qwen2.5-3B. Only adapter parameters were trainable.

### Training objective

The teacher receiver read a benign collaborator message as text. The student
receiver saw only mapped sender states. Training minimized KL divergence between
teacher and student continuation distributions. The base model was always
frozen.

The experiment eventually used three adapter lineages:

1. **Original faithful link:** standalone sender messages and a fixed neutral
   receiver context.
2. **Contextual v1 link:** sender states extracted after benign contextual
   prefixes, but teacher text and latent payload still occupied different
   receiver layouts.
3. **Matched v2 link:** contextual sender extraction, with teacher text-token
   embeddings and student mapped states appended after the exact same receiver
   prefix.

### Games

- **Iterated Prisoner's Dilemma (IPD):** primary behavioral test.
- **Novel-demand Bertrand pricing:** used during early pilots to test
  supracompetitive pricing.

### Action measurement

Early generated-action parsing was replaced with normalized continuation
likelihood over randomized neutral action codes. For every game, seed, round,
and seat, the mapping between codes such as `A`/`B` and legal actions was
randomized deterministically. This removed semantic label priors and eliminated
parser repairs.

## Complete experiment chronology

## 1. Plumbing smoke test

**Model:** Qwen2.5-0.5B-Instruct  
**Purpose:** prove hidden-state extraction, mapping, and embedding injection on
a T4.

The smoke test produced finite tensors:

- hidden shape: `[1, 8, 896]`;
- mapped shape: `[1, 8, 896]`;
- GPU: Tesla T4;
- dtype: fp16/bf16 handling verified.

This established that the basic activation path worked.

## 2. Qwen2.5-0.5B faithful-link training

**Training:** 300 steps, 1,200 neutral examples, 219 seconds.

- Initial loss: 7.396
- Best loss: 0.365
- Final loss: 0.701

Held-out neutral validation, n=512:

| Representation | Mean KL | Top-1 agreement |
|---|---:|---:|
| trained | **0.786** | **0.639** |
| shuffled | 1.252 | 0.593 |
| zero | 2.732 | 0.424 |
| random | 6.864 | 0.058 |

The adapter clearly learned a neutral transmission channel.

### Why the 0.5B arena was not a scientific result

The first arena driver generated action text and repaired malformed outputs.
Repair rates reached approximately 45–91%, making the measurements invalid.

A second driver scored semantic action labels directly. Qwen0.5B exhibited
extreme label priors and ceiling behavior:

- IPD cooperation was 1.0 in nearly every condition;
- no-communication Bertrand K was already 0.714;
- trained and shuffled conditions were often identical.

These values are retained as engineering history but excluded from substantive
claims. They motivated randomized neutral action codes.

## 3. Qwen2.5-1.5B scaling run

**Training:** 600 steps, 2,400 examples, 525 seconds.

- Initial loss: 10.280
- Best loss: 0.298
- Final loss: 0.488

Held-out neutral validation, n=512:

| Representation | Mean KL | Top-1 agreement |
|---|---:|---:|
| trained | **0.667** | **0.684** |
| shuffled | 1.456 | 0.578 |
| zero | 4.915 | 0.233 |
| random | 10.761 | 0.010 |

The neutral channel again learned successfully.

### 1.5B neutral-code pilot

The v3 pilot used randomized neutral codes, 8 seeds per cell, 12 rounds, both
games, and all six controls. It completed 96 matches with no meaningful parser
problem.

IPD end cooperation:

| Condition | End cooperation |
|---|---:|
| none | 0.475 |
| text | 0.475 |
| trained | 0.538 |
| random | 0.563 |
| zero | 0.525 |
| shuffled | 0.563 |

Bertrand collusion index K:

| Condition | K |
|---|---:|
| none | 0.505 |
| text | 0.505 |
| trained | 0.539 |
| random | 0.513 |
| zero | 0.689 |
| shuffled | 0.507 |

The critical problem was capability: readable text itself did not change
behavior relative to no communication. Without a text effect, the model could
not support a meaningful test of whether representations exceeded text.
Qwen1.5B was therefore not promoted.

## 4. Qwen2.5-3B capability gate

Before training another link, we required the base model to respond to readable
communication.

**Design:** n=8 per condition, 12 rounds, `none` versus `text`.

IPD:

- none end cooperation: 0.350;
- text end cooperation: 0.525;
- paired difference: +0.175;
- paired bootstrap 95% CI: [+0.0125, +0.300].

Bertrand:

- none K: 0.538;
- text K: 0.511;
- difference: -0.027;
- CI: [-0.079, +0.029].

Qwen3B passed the IPD capability floor: readable communication altered
cooperative behavior. Bertrand did not show a text-induced collusion lift, so
later confirmatory work focused on IPD.

## 5. Qwen2.5-3B original faithful link

**Training:** 800 steps, 3,200 neutral examples, approximately 14.5 minutes.

- Initial loss: 10.075
- Best loss: 0.227
- Final loss: 0.631
- Trainable parameters: 8.39M

Held-out neutral validation, n=512:

| Representation | Mean KL | Top-1 agreement |
|---|---:|---:|
| trained | **0.649** | **0.701** |
| shuffled | 1.569 | 0.580 |
| zero | 3.128 | 0.420 |
| random | 9.132 | 0.007 |

The neutral fidelity gate passed strongly.

### Invalid intent-probe result

The strategic-intent diagnostic reported 1.0 accuracy/AUROC for both the trained
and random link. The labels were already linearly recoverable from random
high-dimensional features, so this probe was non-discriminative. It is retained
in the artifacts but is not evidence for the trained channel.

## 6. Original 3B v3 pilot

**Design:** 96 matches, 8 seeds/cell, 12 rounds, IPD and Bertrand, all six
conditions, neutral action codes.

IPD:

| Condition | Overall cooperation | End cooperation |
|---|---:|---:|
| none | 0.375 | 0.350 |
| text | 0.438 | 0.525 |
| trained | 0.500 | 0.550 |
| random | 0.490 | 0.525 |
| zero | 0.484 | 0.525 |
| shuffled | 0.453 | 0.500 |

Paired IPD endpoint contrasts:

- text − none: +0.175, CI [+0.0125, +0.300];
- trained − none: +0.200, CI [+0.100, +0.300];
- trained − text: +0.025, CI [-0.063, +0.125];
- trained − shuffled: +0.050, CI [-0.075, +0.200].

Bertrand showed no stable representation-specific effect.

The trained condition looked promising against no communication, but random,
zero, and shuffled controls moved behavior similarly. The pilot did not
attribute the effect to semantic content.

## 7. Original 3B frozen confirmatory IPD run

The pilot fixed the following design before execution:

- IPD only;
- 40 matched seeds;
- 20 rounds;
- all six controls;
- end cooperation as the primary metric;
- primary contrasts: trained − text and trained − shuffled.

**Integrity:** 240/240 unique matches, zero parse repairs, 3h48m runtime.

| Condition | Overall cooperation | End cooperation | Lock-in |
|---|---:|---:|---:|
| none | 0.3838 | 0.3425 | 0.000 |
| text | 0.4775 | 0.5025 | 0.025 |
| trained | 0.4869 | 0.4600 | 0.000 |
| random | 0.5000 | 0.4900 | 0.000 |
| zero | 0.4950 | 0.4900 | 0.000 |
| shuffled | 0.5031 | 0.5375 | 0.075 |

Paired endpoint contrasts:

| Contrast | Difference | 95% paired bootstrap CI |
|---|---:|---:|
| trained − text | -0.0425 | [-0.1025, +0.0175] |
| trained − shuffled | **-0.0775** | **[-0.1400, -0.0175]** |
| trained − none | +0.1175 | [+0.0475, +0.1850] |
| text − none | +0.1600 | [+0.0900, +0.2275] |
| shuffled − none | +0.1950 | [+0.1275, +0.2625] |
| trained − zero | -0.0300 | [-0.0925, +0.0325] |
| trained − random | -0.0300 | [-0.0925, +0.0325] |

The current link failed the representation-specific hypothesis. It did not beat
text and was significantly worse than shuffled representations.

## 8. Arena-context deployment diagnostic

Code inspection revealed that neutral validation did not reproduce arena
deployment:

- training extracted hidden states from standalone messages;
- the arena extracted hidden states from messages generated after long
  strategic/history prompts;
- readable text was inserted inside the action prompt;
- latent payloads were appended after a different prompt.

We froze 256 arena snapshots and compared the text-conditioned two-action
distribution against each representation.

Legacy-layout results:

| Representation | Action KL | Top-1 agreement | Total variation |
|---|---:|---:|---:|
| trained | 0.269 | 0.695 | 0.232 |
| shuffled | **0.184** | **0.742** | **0.200** |
| random | 0.295 | 0.516 | 0.314 |
| zero | 0.313 | 0.520 | 0.273 |
| exact text-token embeddings | 0.413 | 0.594 | 0.290 |

The trained link failed. More importantly, exact token embeddings also failed.
This proved that receiver-layout differences—not just adapter quality—changed
decisions.

## 9. Contextual v1 repair

The first repair trained sender states after four benign contextual templates
and placed student latents after a receiver instruction.

**Training:** 1,000 steps, 4,000 neutral examples, 18.5 minutes.

- Initial batch loss: 2.695
- Best batch loss: 0.148
- Final batch loss: 0.537
- Mean first 50 steps: 1.323
- Mean last 50 steps: 0.648

Neutral fidelity remained acceptable:

- trained KL 0.941;
- shuffled 1.275;
- zero 3.099;
- random 9.019.

However, on 384 deployment snapshots disjoint from the diagnostic set:

| Representation | Action KL | Top-1 agreement |
|---|---:|---:|
| trained | 0.283 | 0.659 |
| shuffled | **0.216** | **0.729** |
| random | 0.282 | 0.576 |
| zero | 0.296 | 0.576 |
| exact token embeddings | 0.423 | 0.602 |

The repair failed because the teacher and student still occupied different
receiver layouts.

## 10. Matched-layout oracle experiment

We changed the diagnostic so readable text-token embeddings and every
continuous payload appeared immediately after one identical receiver prompt.

The token oracle then achieved exactly:

- KL: 0.000;
- top-1 agreement: 1.000;
- total variation: 0.000.

This validated the corrected layout.

On the same 256 snapshots:

| Adapter/control | Action KL | Top-1 agreement |
|---|---:|---:|
| original trained | 0.208 | 0.699 |
| original shuffled | 0.227 | 0.715 |
| contextual trained | 0.234 | 0.734 |
| contextual shuffled | 0.248 | 0.703 |
| random | **0.185** | **0.816** |
| zero | 0.287 | 0.820 |
| token oracle | **0.000** | **1.000** |

Neither existing adapter beat random. The layout was now valid, but the training
objective was not aligned with it.

## 11. Matched v2 reserved repair

The final permitted repair used:

- contextual sender extraction;
- one identical benign receiver prefix;
- teacher message-token embeddings appended after that prefix;
- student mapped states appended at the same position;
- frozen Qwen3B;
- original faithful adapter initialization;
- no arena data.

**Training:** 1,000 steps, 4,000 examples, 18.4 minutes.

- Mean loss, first 50 steps: 0.722
- Mean loss, last 50 steps: 0.488
- Best batch loss: 0.125 at step 999
- Final batch loss: 0.619

### Fresh matched-layout validation

Neutral held-out validation, n=256:

| Representation | Mean KL | Top-1 agreement |
|---|---:|---:|
| trained | **0.425** | **0.777** |
| shuffled | 1.425 | 0.625 |
| zero | 3.099 | 0.420 |
| random | 9.019 | 0.008 |

Matched deployment validation used 384 snapshots excluding all 256 prior
matched-layout comparison snapshots:

| Representation | Action KL | Top-1 agreement | Total variation |
|---|---:|---:|---:|
| trained | **0.138** | 0.758 | **0.173** |
| random | 0.197 | 0.776 | 0.226 |
| shuffled | 0.255 | 0.693 | 0.236 |
| zero | 0.349 | 0.773 | 0.232 |
| token oracle | **0.000** | **1.000** | **0.000** |

Paired uncertainty:

- trained − random KL: -0.059, CI [-0.088, -0.031];
- trained − shuffled KL: -0.117, CI [-0.161, -0.077];
- trained − zero KL: -0.211, CI [-0.269, -0.158];
- trained − random total variation: -0.053, CI [-0.073, -0.033];
- trained − shuffled total variation: -0.063, CI [-0.085, -0.042].

This was the first adapter to pass both neutral and actual deployment fidelity
gates with uncertainty intervals excluding zero.

## 12. Final repaired v4 pilot

**Design:**

- Qwen2.5-3B homogeneous self-play;
- IPD only;
- fresh seeds 800–807;
- n=8 per condition;
- 12 rounds;
- all six controls;
- randomized neutral action codes;
- readable text tokens and all latent payloads at the exact same receiver
  position;
- no parse repairs.

**Integrity:** 48/48 unique matches, 28.0 minutes.

| Condition | Overall cooperation | End cooperation | Lock-in |
|---|---:|---:|---:|
| none | 0.401 | 0.425 | 0.000 |
| text | 0.484 | 0.538 | 0.000 |
| trained | 0.422 | 0.438 | 0.000 |
| random | 0.490 | 0.550 | 0.000 |
| zero | 0.500 | 0.550 | 0.000 |
| shuffled | 0.464 | 0.438 | 0.000 |

Paired endpoint contrasts:

| Contrast | Difference | 95% CI |
|---|---:|---:|
| trained − text | -0.100 | [-0.238, +0.050] |
| trained − shuffled | 0.000 | [-0.075, +0.063] |
| trained − random | -0.113 | [-0.225, +0.012] |
| trained − zero | -0.113 | [-0.225, +0.012] |
| trained − none | +0.013 | [-0.113, +0.137] |
| text − none | +0.113 | [-0.025, +0.238] |

Across all rounds:

- trained − random cooperation: -0.068, CI [-0.125, -0.005];
- trained − zero cooperation: -0.078, CI [-0.130, -0.026].

Random and zero action paths agreed on 190/192 decisions (99.0%), demonstrating
that their behavior was dominated by the shared payload-position/context effect,
not random semantic content.

## Final interpretation

### What succeeded

1. We implemented a fully frozen-base continuous inter-agent channel.
2. The adapter learned neutral message transmission at 0.5B, 1.5B, and 3B.
3. The final matched adapter reproduced text-conditioned action distributions
   better than shuffled, random, and zero controls on fresh deployment
   snapshots.
4. The experiment eliminated parser dependence and semantic action-label bias.
5. The exact-token oracle exposed and then verified removal of a receiver-layout
   confound.
6. All final behavioral runs were checkpointed, manifest-locked, and completed
   with zero repairs.

### What did not succeed

1. Learned representations did not raise sequential cooperation above text.
2. They did not outperform shuffled representations in the final pilot.
3. A standard neutral fidelity test did not predict behavioral deployment
   fidelity.
4. The original strategic-intent probe was invalid because random features
   achieved the same perfect score.
5. The tested 3B model did not exhibit stable IPD lock-in under any condition.
6. Bertrand pricing did not show a reliable readable-text capability lift at
   3B, so it was not promoted to the repaired spine.

### Scientific claim supported

For frozen Qwen2.5-3B agents in this scaffold:

> Faithfully transmitting a peer's text-conditioned decision signal through a
> learned continuous representation is not sufficient to increase repeated-game
> coordination. Individual-decision fidelity and emergent sequential
> coordination are distinct capabilities.

### Claims not supported

The experiments do **not** show that:

- continuous channels can never increase coordination;
- larger or heterogeneous models would behave the same way;
- reinforcement-learned or jointly trained agents would fail;
- latent channels are inherently safe or monitorable;
- the result generalizes beyond English, Qwen2.5, T4/fp16 inference, IPD, or this
  arena scaffold.

## Why the final confirmatory run was cancelled

The bounded plan allowed one repair iteration and required a pilot signal before
spending approximately four additional GPU hours on a fresh confirmatory run.
The final pilot showed:

- trained − shuffled endpoint difference exactly 0.000;
- trained below text by 0.100;
- trained no better than no communication;
- trained significantly below random and zero across all rounds.

The stop rule was therefore met. Running a larger confirmatory matrix would
have violated the pre-specified compute gate without a supporting pilot signal.
The negative result and cancellation were logged rather than hidden.

## Reproducibility map

### Core implementation

- `followup-representational/src/l4_arena/link.py`
- `followup-representational/scripts/train_link.py`
- `followup-representational/scripts/train_context_link.py`
- `followup-representational/scripts/validate_link.py`
- `followup-representational/scripts/diagnose_arena_fidelity.py`
- `followup-representational/scripts/run_arena.py`

### Colab notebooks

- `00_plumbing_smoke.ipynb`
- `05_capability_gate_3b.ipynb`
- `10`–`12`: link training at 0.5B, 1.5B, and 3B
- `20`–`22`: neutral validation
- `30`–`32`: early arenas
- `33`: original 3B confirmatory IPD
- `34`: arena-context diagnostic
- `35`: contextual v1 training
- `36`: contextual v1 validation
- `37`: matched-layout adapter comparison
- `38`: matched v2 repair training
- `39`: fresh matched v2 validation
- `40`: final repaired pilot

### Detailed provenance

- `docs/results_log.md` contains the append-only experimental record.
- `followup-representational/PLAN.md` contains the evolving scientific contract
  and stop decisions.
- `docs/L4_EXECUTION_PLAN.md` in the parent workspace contains the operational
  inventory and compute plan.

Raw imported artifacts and model checkpoints are intentionally gitignored
because they are large. Every imported archive used in the final reasoning has
a SHA-256 digest recorded in `docs/results_log.md`.

## Bottom line

The most valuable outcome was not a positive coordination result. It was a
clean separation between:

1. **representation fidelity**—which the final adapter demonstrably achieved;
2. **behavioral influence at one decision**—which it approximated; and
3. **emergent sequential coordination**—which did not improve.

That separation is the defensible contribution of this follow-up.
