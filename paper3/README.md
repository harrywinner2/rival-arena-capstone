# Paper 3 — the coordinating predicate

The completion paper for the Rival Arena program. Cites the GameSec poster and the
Zenodo extended report as prior work, and contributes the mechanism, two defenses, and
two replications that those papers lacked.

**Start here:** [`FINDINGS.md`](FINDINGS.md) (what the data says) ·
[`PROGRAM.md`](PROGRAM.md) (the full experiment program and compute plan) ·
[`paper/main.tex`](paper/main.tex) (the draft).

---

## The claim in one paragraph

The prior papers concluded that *semantic bandwidth* drives principal-harming
coordination between rival LLM agents. Re-analysis of the released corpus (2,082
matches, 68,290 round-records) does not support that. Contingent punishment rules are
rare and predict nothing; no measured content class predicts the outcome once opening
behaviour is controlled; message length trends the wrong way. What separates every
coordinating arm from every failing one is whether the channel admits a **joint
proposal** ("let's both do X") rather than only an **own intention** ("I will do X").
Above that floor, what is said stops mattering.

## Status

| component | state |
|---|---|
| corpus re-analysis (§3 of the paper) | **complete** |
| monitor cost-curve defense (§7.2) | **complete** |
| L4 latent-channel reinterpretation (§8) | **complete** |
| methods + detector retraction (§9) | **complete** |
| P1 predicate experiment | built, mock-verified, **not yet run** |
| P2 request modality, 3 domains | built, mock-verified, **not yet run** |
| P3 lever factorial | built, mock-verified, **not yet run** |
| P4 opening-window defense | built, mock-verified, **not yet run** |
| V1 detector validation | built, **not yet run** |
| L5 latent predicate transfer | specified only |

The paper carries `\pending{}` markers wherever a result is missing. **None may remain
at submission.** Count them with `grep -c 'pending{' paper/main.tex`.

## Layout

```
paper3/
├── FINDINGS.md        what the completed analysis shows, with retractions
├── PROGRAM.md         all experiments, compute plan, sequencing, risks
├── README.md          this file
├── prereg/            pre-registrations, locked before the corresponding seeds run
│   ├── p1_proposal.md
│   └── p2_request_modality.md
├── paper/             main.tex · refs.bib · figures/
├── runpod/setup.sh    vLLM serving for the self-hosted program
├── run_program.sh     the whole program in dependency order
├── src/               analysis + experiment drivers (see below)
├── results/           generated markdown + csv (regenerable)
└── figures/           generated PDFs (regenerable)
```

## Reproducing the analysis (no inference, no cost)

```bash
python3 src/build_match_table.py        # per-match table from master_long.csv
python3 src/diagnose_rule_timing.py     # rule timing, hazard, recovery
python3 src/horserace.py                # mediator horse-race, temporal design
python3 src/opening_vs_persistence.py   # opening displacement vs persistence
python3 src/proposal_predicate.py       # the predicate across seven arms
python3 src/sms_conditionality.py       # independent-apparatus convergent evidence
python3 src/monitor_defense.py          # cost-optimal thresholding + figure
python3 src/figures.py                  # F1, F2
```

The detector (`src/conditional.py`) is pure regex — no model call — so these are
bit-reproducible.

## Running the experiments

Serve a model, then run the program:

```bash
bash runpod/setup.sh serve                      # or any OpenAI-compatible endpoint
export OPENAI_API_BASE=https://<host>/v1 OPENAI_API_KEY=EMPTY
python3 src/smoke_endpoint.py qwen-14b-local    # verify the stack in one call
bash run_program.sh "$OPENAI_API_BASE" Qwen/Qwen2.5-14B-Instruct
```

`run_program.sh` runs G0 → V1 → P2 → P1 → P4 → P3. **G0 gates the rest**: if the served
model does not respond to readable communication, the predicate experiments measure
nothing and the script aborts. Every stage is checkpointed, so an interruption costs
only the in-flight matches.

## Two things to know before trusting a number here

1. **A detector of ours was wrong and we caught it.** v1 of the contingent-punishment
   detector counted cooperative reciprocity as punishment (precision ≈ 0.15) and
   produced a large, clean, entirely spurious effect that survived a temporal-ordering
   design. v3 (precision ≈ 0.94 by hand-adjudication) reduces both headline v1 numbers
   to null. See `FINDINGS.md §0`. Recall is still unmeasured, so rule base rates are
   **lower bounds** until V1 runs.
2. **The predicate is observational until P1 runs.** At the arm level the proposal form
   is confounded with message length. The message-level evidence breaks the confound in
   both directions, but the causal claim rests on P1.
