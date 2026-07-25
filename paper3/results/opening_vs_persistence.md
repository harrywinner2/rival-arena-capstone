# Opening displacement vs persistence

The channel effect decomposed into where it acts.


## The channel ladder (all IPD experiments)

| arm | n | opening C | closing C | decay | decay 95% CI |
|---|---:|---:|---:|---:|---|
| L0_none | 314 | 0.622 | 0.248 | -0.373 | [-0.406, -0.340] |
| L1_signal | 115 | 0.301 | 0.069 | -0.232 | [-0.278, -0.189] |
| L2_observed | 366 | 0.815 | 0.644 | -0.171 | [-0.199, -0.142] |
| L3_private | 118 | 0.820 | 0.734 | -0.086 | [-0.142, -0.030] |

**Floor-controlled** (matches opening at C>0.8, n=490) — every arm now has equal room to fall, so a channel that *sustains* cooperation should show a flatter decay here:

| arm | n | opening C | closing C | decay | decay 95% CI |
|---|---:|---:|---:|---:|---|
| L0_none | 124 | 0.949 | 0.400 | -0.549 | [-0.598, -0.498] |
| L1_signal | 14 | 0.964 | 0.374 | -0.590 | [-0.780, -0.402] |
| L2_observed | 267 | 0.988 | 0.791 | -0.197 | [-0.228, -0.166] |
| L3_private | 85 | 0.983 | 0.825 | -0.158 | [-0.216, -0.106] |

**Pairwise decay contrasts (floor-controlled).** A significant difference would mean the channel changes persistence, not just the starting point.

| contrast | Δdecay | 95% CI |
|---|---:|---|
| L1_signal − L0_none | -0.042 | [-0.237, +0.164] |
| L2_observed − L0_none ** | +0.352 | [+0.292, +0.411] |
| L3_private − L0_none ** | +0.391 | [+0.316, +0.464] |

## C1 ablation — selected (menu) / restricted (self-authored, action-only) / free

| arm | n | opening C | closing C | decay | decay 95% CI |
|---|---:|---:|---:|---:|---|
| selected | 17 | 0.196 | 0.003 | -0.193 | [-0.269, -0.122] |
| restricted | 17 | 0.167 | 0.003 | -0.164 | [-0.253, -0.085] |
| free | 17 | 0.931 | 0.711 | -0.220 | [-0.354, -0.099] |

**Floor-controlled** (matches opening at C>0.8, n=15) — every arm now has equal room to fall, so a channel that *sustains* cooperation should show a flatter decay here:

| arm | n | opening C | closing C | decay | decay 95% CI |
|---|---:|---:|---:|---:|---|
| selected | 0 | — | — | — | insufficient |
| restricted | 0 | — | — | — | insufficient |
| free | 15 | 0.978 | 0.779 | -0.198 | [-0.340, -0.071] |


## Reading

C1 holds the *act* of sending a message constant and varies only how much content the message may carry. If the channel worked by installing an enforcement regime, the free arm should decay more slowly. It does not: the arms separate almost entirely at the opening.
