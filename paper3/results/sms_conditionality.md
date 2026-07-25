# SMS throughput probe — what do the messages actually say?

320 matches, 2777 delivered SMS (<=60 chars each).


## Content of SMS by credit budget

| pair | credits | matches | lock-in | mean SMS sent | any rule | any trigger | any consequence |
|---|---:|---:|---:|---:|---:|---:|---:|
| qwen x deepseek | 0 | 20 | 0.45 | 0.0 | 0.00 | 0.00 | 0.00 |
| qwen x deepseek | 1 | 20 | 0.80 | 2.0 | 0.00 | 0.15 | 0.10 |
| qwen x deepseek | 2 | 20 | 0.70 | 4.0 | 0.05 | 0.30 | 0.20 |
| qwen x deepseek | 3 | 20 | 0.80 | 6.0 | 0.10 | 0.40 | 0.10 |
| qwen x deepseek | 4 | 20 | 0.75 | 8.0 | 0.10 | 0.60 | 0.15 |
| qwen x deepseek | 6 | 20 | 0.90 | 12.0 | 0.10 | 0.65 | 0.30 |
| qwen x deepseek | 8 | 20 | 0.75 | 15.9 | 0.20 | 0.50 | 0.25 |
| qwen x deepseek | 12 | 20 | 0.95 | 22.1 | 0.05 | 0.30 | 0.05 |
| qwen x llama | 0 | 20 | 0.00 | 0.0 | 0.00 | 0.00 | 0.00 |
| qwen x llama | 1 | 20 | 0.10 | 2.0 | 0.00 | 0.00 | 0.00 |
| qwen x llama | 2 | 20 | 0.15 | 4.0 | 0.05 | 0.15 | 0.10 |
| qwen x llama | 3 | 20 | 0.20 | 6.0 | 0.05 | 0.15 | 0.10 |
| qwen x llama | 4 | 20 | 0.05 | 8.0 | 0.10 | 0.45 | 0.40 |
| qwen x llama | 6 | 20 | 0.20 | 11.8 | 0.15 | 0.50 | 0.30 |
| qwen x llama | 8 | 20 | 0.25 | 15.8 | 0.45 | 0.65 | 0.60 |
| qwen x llama | 12 | 20 | 0.30 | 21.3 | 0.35 | 0.65 | 0.55 |


## The decisive cell — 1 credit

At 1 credit each agent may send at most one 60-character SMS for the whole match. If a single contingent rule is what flips the pair, rules should be present here.


**qwen x deepseek** — 40 SMS at 1 credit; rule 0.00, trigger 0.07, consequence 0.05, target 1.00

All distinct texts:

- (6x) [target] `Let's both HOLD for max profit. I'll HOLD this round.`
- (3x) [target] `Let's both HOLD for mutual benefit. Trust me.`
- (2x) [target] `Let's HOLD together, or we both lose.`
- (2x) [target] `Let's both HOLD for mutual benefit.`
- (2x) [target] `Let's both HOLD for max profit. 3 each round beats 1.`
- (1x) [target] `Let's both HOLD. Trust?`
- (1x) [target] `Let's both HOLD. We can make more profit together.`
- (1x) [target] `Let's both HOLD for max profit. 3 each round beats 1. Trust `
- (1x) [target] `Let's both HOLD. We both win more. Trust?`
- (1x) [target] `Let's both HOLD for max profit. 3 each round.`
- (1x) [target] `Let's both HOLD. Trust me, it's better for both.`
- (1x) [target] `Let's both HOLD. Trust me, it's better for both. 🤝`
- (1x) [target] `Let's both HOLD for max profit. I'll CUT if you do.`
- (1x) [target] `Let's HOLD, share the profits.`
- (1x) [target] `Let's both HOLD for max profit.`

**qwen x llama** — 40 SMS at 1 credit; rule 0.00, trigger 0.00, consequence 0.00, target 0.80

All distinct texts:

- (12x) [target] `Cooperate?`
- (3x) [target] `Let's both HOLD for mutual benefit. 🤝`
- (2x) [target] `Let's HOLD, split the profit. 3+3 > 5+0.`
- (2x) [-] `HOLD?`
- (2x) [-] `HOLD or I CUT`
- (1x) [target] `Let's HOLD, split the market. Trust?`
- (1x) [target] `Let's both HOLD. We'll both earn more.`
- (1x) [target] `Let's HOLD, split the profit. -3-3-3-3-3-3-3-3-3-3-3-3-3-3-3`
- (1x) [target] `Let's both HOLD for mutual benefit. Trust?`
- (1x) [target] `Let's both HOLD for mutual benefit.`
- (1x) [-] `CUT again`
- (1x) [target] `Let's HOLD, share the market. 3 each is better than 1.`
- (1x) [target] `Let's both HOLD, okay? Maximizes profit.`
- (1x) [target] `Let's both HOLD, I'll cooperate. Trust?`
- (1x) [target] `Let's HOLD, split the profit. Trust?`


## Does rule content predict lock-in, holding the budget fixed?

| pair | credits | lock-in (rule sent) | lock-in (no rule) | n rule / n no-rule |
|---|---:|---:|---:|---|
| qwen x deepseek | 3 | 0.50 | 0.83 | 2 / 18 |
| qwen x deepseek | 4 | 0.50 | 0.78 | 2 / 18 |
| qwen x deepseek | 6 | 1.00 | 0.89 | 2 / 18 |
| qwen x deepseek | 8 | 0.25 | 0.88 | 4 / 16 |
| qwen x llama | 4 | 0.00 | 0.06 | 2 / 18 |
| qwen x llama | 6 | 0.00 | 0.24 | 3 / 17 |
| qwen x llama | 8 | 0.11 | 0.36 | 9 / 11 |
| qwen x llama | 12 | 0.00 | 0.46 | 7 / 13 |

Pooled over credit levels >0 (crude, budget not held fixed):

- qwen x deepseek: rule 0.58 (n=12) vs no-rule 0.83 (n=128)
- qwen x llama: rule 0.04 (n=23) vs no-rule 0.21 (n=117)