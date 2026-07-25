# P1 — the joint-proposal predicate

Run: `code/data/runs/P1/20260725T013304`

Pre-registered in `paper3/prereg/p1_proposal.md`.


## Manipulation check (gates H1)

| arm | n | proposal rate/msg | intention-only rate/msg | mean msg chars |
|---|---:|---:|---:|---:|
| none | 30 | 0.000 | 0.000 | 0 |
| menu | 30 | 0.000 | 1.000 | 22 |
| intention | 30 | 0.000 | 1.000 | 16 |
| proposal | 30 | 1.000 | 0.000 | 21 |
| free | 30 | 1.000 | 0.000 | 96 |

**PASS**


## Primary outcome: lock-in proportion

| arm | k/n | lock-in | Wilson 95% CI | mean C | api_error_rate |
|---|---|---:|---|---:|---:|
| none | 6/30 | 0.200 | [0.10, 0.37] | 0.582 | 0.000 |
| menu | 27/30 | 0.900 | [0.74, 0.97] | 0.931 | 0.000 |
| intention | 12/30 | 0.400 | [0.25, 0.58] | 0.575 | 0.000 |
| proposal | 23/30 | 0.767 | [0.59, 0.88] | 0.847 | 0.000 |
| free | 26/30 | 0.867 | [0.70, 0.95] | 0.930 | 0.000 |


## Pre-registered contrasts

**Primary — proposal vs intention** (Fisher exact, two-sided, alpha 0.05, uncorrected): p = 8.21e-03, RD +0.367 [+0.117, +0.559] -> **H1 SUPPORTED**


Secondary contrasts (Benjamini-Hochberg FDR 0.05):

| contrast | p | RD | 95% CI | survives FDR |
|---|---:|---:|---|:--:|
| proposal vs free | 5.06e-01 | -0.100 | [-0.293, +0.100] | no |
| intention vs none | 1.58e-01 | +0.200 | [-0.032, +0.406] | no |
| free vs none | 3.25e-07 | +0.667 | [+0.429, +0.799] | yes |
| menu vs none | 5.62e-08 | +0.700 | [+0.467, +0.824] | yes |


## Interpretation guide (pre-registered)

- `proposal` >> `intention` and `proposal` ~ `free`: the coordinating predicate is the joint proposal, not open-ended content or bandwidth.
- `proposal` ~ `intention` (both low): the predicate is wrong; the effect requires open-ended content, supporting the original reading.
- A non-significant `proposal` vs `free` contrast is reported as under-powered, NOT as equivalence.