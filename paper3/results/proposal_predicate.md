# The joint-proposal predicate

Does the arm permit a first-person-plural commissive proposal ("let's both do X"), or only a first-person-singular intention ("I will do X")?


## Arm-level: does the arm permit proposals, and does it coordinate?

| arm | n | mean proposal rate per message | intention-only rate | opening C | lock-in | Wilson 95% CI |
|---|---:|---:|---:|---:|---:|---|
| L0_none | 354 | 0.000 | 0.000 | 0.630 | 0.113 | [0.08, 0.15] |
| L1_signal | 106 | 0.000 | 1.000 | 0.318 | 0.057 | [0.03, 0.12] |
| C1:selected | 20 | 0.000 | 1.000 | 0.217 | 0.050 | [0.01, 0.24] |
| C1:restricted | 20 | 0.000 | 1.000 | 0.175 | 0.000 | [-0.00, 0.16] |
| C1:free | 20 | 1.000 | 0.000 | 0.850 | 0.550 | [0.34, 0.74] |
| L2_observed | 374 | 0.918 | 0.022 | 0.845 | 0.599 | [0.55, 0.65] |
| L3_private | 126 | 0.939 | 0.013 | 0.825 | 0.651 | [0.56, 0.73] |

The ordering of the lock-in column follows the proposal-rate column, not message length and not the presence of threats. `C1:restricted` is self-authored free text with a real message every round; it carries intentions, not proposals, and it behaves like the fixed menu.


## Threshold, not dose: within free text, proposal rate does not grade the outcome

| proposal-rate quartile | n | lock-in | 95% CI |
|---|---:|---:|---|
| (0.124, 0.925] | 134 | 0.284 | [0.21, 0.37] |
| (0.925, 1.0] | 386 | 0.723 | [0.68, 0.77] |

Base rate: 0.926 of free-text messages carry a proposal, and 96.9% of free-text matches are above 0.5 -- the floor is cleared almost everywhere, so there is little room left for a dose effect.

## Length is not the predicate

- messages that are a proposal in under 40 characters: 172
- messages that are an intention-only announcement of 20+ characters: 4293

Examples of short proposals:

- `Let's start by cooperating.` (27 chars)
- `Let's continue cooperating, shall we?` (37 chars)
- `Let's continue cooperating as agreed.` (37 chars)
- `Let's cooperate for mutual benefit.` (35 chars)
- `Let's start by cooperating. 🤝` (29 chars)
- `Let's work together for mutual benefit.` (39 chars)

Examples of longer intention-only messages:

- `I intend to cooperate.` (22 chars)
- `Despite multiple chances, you continue to defect. I will not be exploited further. I will choose DEFECT this round.` (115 chars)
- `Given your consistent pattern of defection, I will not be exploited further. I will choose DEFECT this round.` (109 chars)
- `I remain committed to protecting my interests due to your past actions. I will choose DEFECT this round. If you genuinely want to rebuild trust, show it through consistent cooperation.` (184 chars)
- `I've noticed a consistent pattern of you defecting after promising to cooperate. To protect my score, I will defect this round. However, if you genuinely want to rebuild trust, show it by cooperating this round.` (211 chars)
- `I've given you multiple chances to show genuine cooperation, but you've consistently defected. To protect my score, I will defect this round. However, if you truly want to rebuild trust, show it by cooperating this round.` (221 chars)