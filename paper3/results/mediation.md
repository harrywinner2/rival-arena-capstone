# Mediation analysis — does contingent-punishment content carry the channel effect?

Source: `results/master_long.csv`; 2082 LLM-vs-LLM matches (smoke pairs and classical opponents excluded).

Detector: `paper3/src/conditional.py` (regex, deterministic).

## 1. Descriptive: outcome by channel x rule presence


### ipd (lock-in)

| channel | rule present | n | mean | Wilson/bootstrap 95% CI |
|---|---|---:|---:|---|
| L0_none | n/a | 354 | 0.113 | [0.08, 0.15] |
| L1_signal | n/a | 126 | 0.056 | [0.03, 0.11] |
| L2_observed | 0 | 352 | 0.585 | [0.53, 0.64] |
| L2_observed | 1 | 62 | 0.468 | [0.35, 0.59] |
| L3_private | 0 | 95 | 0.674 | [0.57, 0.76] |
| L3_private | 1 | 31 | 0.581 | [0.41, 0.74] |

### bertrand (K)

| channel | rule present | n | mean | Wilson/bootstrap 95% CI |
|---|---|---:|---:|---|
| L0_none | n/a | 244 | 0.046 | [0.01, 0.08] |
| L1_signal | n/a | 66 | -0.102 | [-0.21, 0.00] |
| L2_observed | 0 | 363 | 0.373 | [0.34, 0.40] |
| L2_observed | 1 | 8 | 0.390 | [0.25, 0.52] |
| L3_private | 0 | 181 | 0.441 | [0.38, 0.50] |
| L3_private | 1 | 8 | 0.688 | [0.25, 1.41] |


## 2. Within free-text: rule content vs message length as rival mediators

Restricted to L2/L3 matches, so the channel affordance is held constant. A bandwidth account predicts message length carries the effect; the expressiveness account predicts rule content does.


### ipd (lock-in), n=540 free-text matches

- rule present n=93, mean 0.505; absent n=447, mean 0.604
- **difference -0.099, bootstrap 95% CI [-0.211, +0.012]**

| term | logit coef | 95% CI |
|---|---:|---|
| intercept ** | +0.359 | [+0.158, +0.582] |
| rule(any) | -0.434 | [-0.909, +0.030] |
| msg_len(z) | -0.141 | [-0.362, +0.037] |
| private ** | +0.541 | [+0.138, +0.975] |
| novel_spec | -0.596 | [-1.305, +0.059] |

### bertrand (K), n=560 free-text matches

- rule present n=16, mean 0.539; absent n=544, mean 0.396
- **difference +0.143, bootstrap 95% CI [-0.103, +0.517]**

| term | OLS coef | 95% CI |
|---|---:|---|
| intercept ** | +0.614 | [+0.468, +0.771] |
| rule(any) | +0.155 | [-0.057, +0.484] |
| msg_len(z) ** | -0.059 | [-0.086, -0.026] |
| private ** | +0.070 | [+0.004, +0.128] |
| novel_spec ** | -0.287 | [-0.445, -0.139] |


## 3. Formal mediation: channel -> rule content -> outcome

Total effect = free-text vs no-channel. Indirect = through rule presence (product of coefficients, nonparametric bootstrap).


### ipd (lock-in), n=894

- a-path (channel -> P(rule)): +0.172
- b-path (rule -> outcome | channel): -0.099
- **total effect +0.474**
- **indirect (mediated) -0.017, 95% CI [-0.037, +0.002]**
- direct (unmediated) +0.491, 95% CI [+0.434, +0.548]
- proportion mediated: -3.6%

### bertrand (K), n=804

- a-path (channel -> P(rule)): +0.029
- b-path (rule -> outcome | channel): +0.143
- **total effect +0.354**
- **indirect (mediated) +0.004, 95% CI [-0.003, +0.015]**
- direct (unmediated) +0.350, 95% CI [+0.303, +0.397]
- proportion mediated: 1.2%


## 4. Temporal ordering: opening-round rules -> closing-half outcome

Mediator measured strictly before the outcome window, so a rule cannot be a *response* to the outcome it predicts.


### ipd (closing lock-in), n=484

- opening rule n=60, mean 0.583; no opening rule n=424, mean 0.533
- **difference +0.050, 95% CI [-0.083, +0.181]**

| term | coef | 95% CI |
|---|---:|---|
| intercept ** | +0.532 | [+0.487, +0.573] |
| opening rule | +0.056 | [-0.054, +0.170] |
| opening coop(z) ** | +0.224 | [+0.195, +0.256] |
| opening msg_len(z) | -0.012 | [-0.047, +0.024] |

### ipd (closing cooperation), n=484

- opening rule n=60, mean 0.712; no opening rule n=424, mean 0.660
- **difference +0.052, 95% CI [-0.046, +0.143]**

| term | coef | 95% CI |
|---|---:|---|
| intercept ** | +0.660 | [+0.629, +0.688] |
| opening rule | +0.052 | [-0.008, +0.117] |
| opening coop(z) ** | +0.233 | [+0.208, +0.256] |
| opening msg_len(z) | +0.001 | [-0.023, +0.025] |

### bertrand (closing K) — insufficient cells (rule n=1, no-rule n=499)