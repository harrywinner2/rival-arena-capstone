# P3 — the lever factorial

Run: `code/data/runs/P3/20260724T193817` — 24 matches.

Pre-registered in `paper3/prereg/p3_levers.md`.


## Cell means

| expressiveness | throughput | observability | n | lock-in | Wilson 95% CI | mean C |
|---|---|---|---:|---:|---|---:|
| free | every | observed | 2 | 0.000 | [0.00, 0.66] | 0.667 |
| free | every | private | 2 | 0.000 | [0.00, 0.66] | 0.667 |
| free | once | observed | 2 | 0.000 | [0.00, 0.66] | 0.500 |
| free | once | private | 2 | 0.000 | [0.00, 0.66] | 0.500 |
| intention | every | observed | 2 | 0.000 | [0.00, 0.66] | 0.667 |
| intention | every | private | 2 | 0.000 | [0.00, 0.66] | 0.667 |
| intention | once | observed | 2 | 0.000 | [0.00, 0.66] | 0.500 |
| intention | once | private | 2 | 0.000 | [0.00, 0.66] | 0.500 |
| proposal | every | observed | 2 | 0.000 | [0.00, 0.66] | 0.667 |
| proposal | every | private | 2 | 0.000 | [0.00, 0.66] | 0.667 |
| proposal | once | observed | 2 | 0.000 | [0.00, 0.66] | 0.500 |
| proposal | once | private | 2 | 0.000 | [0.00, 0.66] | 0.500 |


## Marginal means by factor


**expressiveness**

| level | n | lock-in | mean C |
|---|---:|---:|---:|
| free | 8 | 0.000 | 0.583 |
| intention | 8 | 0.000 | 0.583 |
| proposal | 8 | 0.000 | 0.583 |

**throughput**

| level | n | lock-in | mean C |
|---|---:|---:|---:|
| every | 12 | 0.000 | 0.667 |
| once | 12 | 0.000 | 0.500 |

**observability**

| level | n | lock-in | mean C |
|---|---:|---:|---:|
| observed | 12 | 0.000 | 0.583 |
| private | 12 | 0.000 | 0.583 |


## Effect sizes in one ordering (the pre-registered test)

Partial eta-squared on mean cooperation, bootstrap 95% CI.

| factor | partial eta2 | 95% CI |
|---|---:|---|
| throughput | 0.3333 | [nan, nan] |
| expressiveness | 0.0000 | [nan, nan] |
| observability | 0.0000 | [0.0000, 0.2739] |

Observed ordering: throughput > expressiveness > observability

expressiveness / max(other) = **0.00x** (prediction required >= 3.0x)

**Pre-registered ordinal prediction: NOT SUPPORTED**


API error rate: 0.000 (excluded from behavioural metrics).