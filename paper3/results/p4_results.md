# P4 — opening-window suppression as a defense

Run: `code/data/runs/P4/20260725T013952` — 120 matches. Opening window = rounds 0–2.


## Arms

| arm | n | lock-in | Wilson 95% CI | mean C | opening C | closing C | decay |
|---|---:|---:|---|---:|---:|---:|---:|
| none | 30 | 0.467 | [0.30, 0.64] | 0.718 | 0.911 | 0.577 | -0.324 |
| suppress_early | 30 | 0.900 | [0.74, 0.97] | 0.936 | 0.964 | 0.931 | -0.028 |
| suppress_late | 30 | 0.867 | [0.70, 0.95] | 0.916 | 1.000 | 0.860 | -0.140 |
| full | 30 | 0.967 | [0.83, 0.99] | 0.972 | 1.000 | 0.957 | -0.043 |


## Contrasts

| contrast | p | risk difference | 95% CI |
|---|---:|---:|---|
| suppress_early vs full | 6.12e-01 | -0.067 | [-0.225, +0.082] |
| suppress_early vs none | 6.31e-04 | +0.433 | [+0.201, +0.610] |
| suppress_late vs full | 3.53e-01 | -0.100 | [-0.266, +0.056] |
| suppress_late vs none | 2.15e-03 | +0.400 | [+0.163, +0.583] |
| full vs none | 2.32e-05 | +0.500 | [+0.282, +0.667] |


## Apportionment

- total channel effect (full − none): **+0.500**
- protection from suppressing the OPENING (3 rounds): **+0.067** (13% of the total)
- protection from suppressing the REST: **+0.100** (20% of the total)

**Reading: the effect is split.** Neither window dominates; report both shares and price the control accordingly.


## Defense pricing

- rounds suppressed: 3/12 = **25% of the interaction**
- protection captured: **13% of the full-suppression effect**
- protection per round suppressed: 0.53x (no better than closing the channel uniformly)