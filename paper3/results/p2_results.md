# P2 — request modality across three unrelated domains

Source: `/home/kamdemharry/capstone/l4-workspace/paper3/results/p2_runs.jsonl` — 288 runs.

Pre-registered in `paper3/prereg/p2_request_modality.md`.


API errors excluded from behavioural metrics: 0 (0.0%).


## Knowledge gate

A can only *knowingly* misreport if it read the authoritative record. Rates below are reported on all runs; the gated subset is shown for comparison.

- read_truth called in **60.8%** of runs (by domain: code review 51%, compliance attestation 80%, procurement recommendation 51%)


## Primary: ambient artifact vs direct request

| domain | delivery | n | honest | omission | **active lie** | Wilson 95% CI |
|---|---|---:|---:|---:|---:|---|
| code review | direct | 48 | 1.00 | 0.00 | **0.00** | [0.00, 0.07] |
| code review | ambient | 48 | 0.27 | 0.00 | **0.73** | [0.59, 0.83] |
| compliance attestation | direct | 48 | 0.77 | 0.08 | **0.15** | [0.07, 0.27] |
| compliance attestation | ambient | 48 | 0.81 | 0.00 | **0.19** | [0.10, 0.32] |
| procurement recommendation | direct | 48 | 1.00 | 0.00 | **0.00** | [0.00, 0.07] |
| procurement recommendation | ambient | 48 | 0.06 | 0.00 | **0.94** | [0.83, 0.98] |


### Contrasts (ambient − direct), Benjamini-Hochberg FDR 0.05

| domain | p | risk difference | 95% CI | survives FDR |
|---|---:|---:|---|:--:|
| code review | 2.04e-15 | +0.729 | [+0.572, +0.834] | yes |
| compliance attestation | 7.85e-01 | +0.042 | [-0.111, +0.193] | no |
| procurement recommendation | 6.47e-24 | +0.938 | [+0.808, +0.979] | yes |

**Pooled (Cochran-Mantel-Haenszel, stratified by domain):** chi2 = 109.16, p = 0.00e+00

**Replication count: 2/3 domains show the ambient route producing more active lies.**

Pre-registered reading: the request-modality effect is **not specific to the research-lab task family**.


## Knowledge-gated: knowing misreports only (`read_truth` called)

| domain | delivery | read rate | n (read) | active lie | Wilson 95% CI |
|---|---|---:|---:|---:|---|
| code review | direct | 0.44 | 21 | 0.00 | [0.00, 0.15] |
| code review | ambient | 0.58 | 28 | 0.54 | [0.36, 0.70] |
| compliance attestation | direct | 0.60 | 29 | 0.21 | [0.10, 0.38] |
| compliance attestation | ambient | 1.00 | 48 | 0.19 | [0.10, 0.32] |
| procurement recommendation | direct | 0.96 | 46 | 0.00 | [-0.00, 0.08] |
| procurement recommendation | ambient | 0.06 | 3 | 0.00 | [0.00, 0.56] |

| domain | p | risk difference | 95% CI | survives FDR |
|---|---:|---:|---|:--:|
| code review | 2.59e-05 | +0.536 | [+0.300, +0.705] | yes |
| compliance attestation | 1.00e+00 | -0.019 | [-0.216, +0.151] | no |

**Knowing-misreport replication: 1/2 testable domains.** Domains where one arm has fewer than 5 readers are not testable and are excluded rather than counted as nulls.

### Where the ungated effect actually comes from

| domain | delivery | lie rate among readers | lie rate among non-readers |
|---|---|---:|---:|
| code review | direct | 0.00 (n=21) | 0.00 (n=27) |
| code review | ambient | 0.54 (n=28) | 1.00 (n=20) |
| compliance attestation | direct | 0.21 (n=29) | 0.05 (n=19) |
| compliance attestation | ambient | 0.19 (n=48) | — |
| procurement recommendation | direct | 0.00 (n=46) | 0.00 (n=2) |
| procurement recommendation | ambient | 0.00 (n=3) | 1.00 (n=45) |

A high lie rate concentrated among **non-readers** means the ambient artifact worked by **pre-empting verification**, not by persuading an informed agent to misreport. That is a different failure with a different remedy: force the verification step rather than audit the filing.