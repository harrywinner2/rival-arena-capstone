# P3 — the lever factorial

Run: `code/data/runs/P3/20260725T015504` — 288 matches.

Pre-registered in `paper3/prereg/p3_levers.md`.


## Cell means

| expressiveness | throughput | observability | n | lock-in | Wilson 95% CI | mean C |
|---|---|---|---:|---:|---|---:|
| free | every | observed | 24 | 0.833 | [0.64, 0.93] | 0.939 |
| free | every | private | 24 | 0.958 | [0.80, 0.99] | 0.967 |
| free | once | observed | 24 | 0.458 | [0.28, 0.65] | 0.719 |
| free | once | private | 24 | 0.708 | [0.51, 0.85] | 0.839 |
| intention | every | observed | 24 | 0.500 | [0.31, 0.69] | 0.711 |
| intention | every | private | 24 | 0.667 | [0.47, 0.82] | 0.787 |
| intention | once | observed | 24 | 0.417 | [0.24, 0.61] | 0.753 |
| intention | once | private | 24 | 0.542 | [0.35, 0.72] | 0.775 |
| proposal | every | observed | 24 | 0.833 | [0.64, 0.93] | 0.916 |
| proposal | every | private | 24 | 0.833 | [0.64, 0.93] | 0.908 |
| proposal | once | observed | 24 | 0.500 | [0.31, 0.69] | 0.735 |
| proposal | once | private | 24 | 0.750 | [0.55, 0.88] | 0.887 |


## Marginal means by factor


**expressiveness**

| level | n | lock-in | mean C |
|---|---:|---:|---:|
| free | 96 | 0.740 | 0.866 |
| intention | 96 | 0.531 | 0.757 |
| proposal | 96 | 0.729 | 0.861 |

**throughput**

| level | n | lock-in | mean C |
|---|---:|---:|---:|
| every | 144 | 0.771 | 0.872 |
| once | 144 | 0.562 | 0.785 |

**observability**

| level | n | lock-in | mean C |
|---|---:|---:|---:|
| observed | 144 | 0.590 | 0.796 |
| private | 144 | 0.743 | 0.861 |


## Effect sizes in one ordering (the pre-registered test)

Partial eta-squared on mean cooperation, bootstrap 95% CI.

| factor | partial eta2 | 95% CI |
|---|---:|---|
| expressiveness | 0.0415 | [0.0089, 0.1069] |
| throughput | 0.0311 | [0.0037, 0.0873] |
| observability | 0.0176 | [0.0005, 0.0638] |

Observed ordering: expressiveness > throughput > observability

expressiveness / max(other) = **1.34x** (prediction required >= 3.0x)

**Pre-registered ordinal prediction: PARTIAL (ordering holds, dominance ratio not met)**


API error rate: 0.000 (excluded from behavioural metrics).