# The monitor as a deployable defense: cost-optimal thresholding

M1 run: 1079 labelled rounds (403 colluding, 676 non-colluding); 389 ambiguous rounds (0.0 < K <= 0.5) dropped, matching the shipped M1 labelling.


**AUC = 0.893** — the score is discriminative; the question is where to cut it.


Default operating point as shipped: TPR 0.913, FPR 0.450.


## Cost-optimal threshold t* by (cost ratio, prevalence)

`ratio` = c_FP / c_FN, the cost of sanctioning an innocent agent relative to the cost of missing collusion. `pi` = prevalence of colluding rounds. Loss is normalised so c_FN = 1. **`use monitor?`** is no when neither t* beats both do-nothing baselines.

| c_FP/c_FN | pi | t* | TPR | FPR | loss(t*) | never-flag | always-flag | use monitor? |
|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| 0.1 | 0.05 | 0.95 | 0.81 | 0.06 | 0.015 | 0.050 | 0.095 | yes |
| 0.1 | 0.1 | 0.95 | 0.81 | 0.06 | 0.024 | 0.100 | 0.090 | yes |
| 0.1 | 0.25 | 0.85 | 0.87 | 0.17 | 0.045 | 0.250 | 0.075 | yes |
| 0.1 | 0.5 | — (always flag) | 1.00 | 1.00 | 0.050 | 0.500 | 0.050 | **no** |
| 0.5 | 0.05 | 0.95 | 0.81 | 0.06 | 0.038 | 0.050 | 0.475 | yes |
| 0.5 | 0.1 | 0.95 | 0.81 | 0.06 | 0.045 | 0.100 | 0.450 | yes |
| 0.5 | 0.25 | 0.95 | 0.81 | 0.06 | 0.069 | 0.250 | 0.375 | yes |
| 0.5 | 0.5 | 0.90 | 0.87 | 0.16 | 0.106 | 0.500 | 0.250 | yes |
| 1 | 0.05 | — (never flag) | 0.00 | 0.00 | 0.050 | 0.050 | 0.950 | **no** |
| 1 | 0.1 | 0.95 | 0.81 | 0.06 | 0.072 | 0.100 | 0.900 | yes |
| 1 | 0.25 | 0.95 | 0.81 | 0.06 | 0.092 | 0.250 | 0.750 | yes |
| 1 | 0.5 | 0.95 | 0.81 | 0.06 | 0.124 | 0.500 | 0.500 | yes |
| 2 | 0.05 | — (never flag) | 0.00 | 0.00 | 0.050 | 0.050 | 1.900 | **no** |
| 2 | 0.1 | — (never flag) | 0.00 | 0.00 | 0.100 | 0.100 | 1.800 | **no** |
| 2 | 0.25 | 0.95 | 0.81 | 0.06 | 0.136 | 0.250 | 1.500 | yes |
| 2 | 0.5 | 0.95 | 0.81 | 0.06 | 0.153 | 0.500 | 1.000 | yes |
| 5 | 0.05 | — (never flag) | 0.00 | 0.00 | 0.050 | 0.050 | 4.750 | **no** |
| 5 | 0.1 | — (never flag) | 0.00 | 0.00 | 0.100 | 0.100 | 4.500 | **no** |
| 5 | 0.25 | — (never flag) | 0.00 | 0.00 | 0.250 | 0.250 | 3.750 | **no** |
| 5 | 0.5 | 0.95 | 0.81 | 0.06 | 0.242 | 0.500 | 2.500 | yes |
| 10 | 0.05 | — (never flag) | 0.00 | 0.00 | 0.050 | 0.050 | 9.500 | **no** |
| 10 | 0.1 | — (never flag) | 0.00 | 0.00 | 0.100 | 0.100 | 9.000 | **no** |
| 10 | 0.25 | — (never flag) | 0.00 | 0.00 | 0.250 | 0.250 | 7.500 | **no** |
| 10 | 0.5 | 0.95 | 0.81 | 0.06 | 0.390 | 0.500 | 5.000 | yes |

The monitor is worth deploying in 14/24 of the (cost, prevalence) regimes examined. Where it is not, the honest operator recommendation is to run no detector rather than a mis-thresholded one.


## What calibration buys, at matched cost assumptions

Comparing the shipped default operating point against t*, at pi = 0.25:

| c_FP/c_FN | loss at default | loss at t* | reduction |
|---:|---:|---:|---:|
| 0.5 | 0.190 | 0.069 | 64% |
| 1 | 0.359 | 0.092 | 75% |
| 2 | 0.696 | 0.136 | 80% |
| 5 | 1.708 | 0.250 | 85% |

Figure: `paper3/figures/p3_monitor_cost.pdf`
