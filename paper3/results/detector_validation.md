# Detector validation against an independent LLM judge

Judge: `Qwen/Qwen2.5-14B-Instruct`; stratified sample balanced on the detector's verdict (so both error directions are estimable).

Judged: 300/300 (failures dropped).


| | judge: rule | judge: not rule |
|---|---:|---:|
| **detector: rule** | 127 | 23 |
| **detector: not rule** | 1 | 149 |

- raw agreement: **0.920**
- precision: **0.847**
- recall: **0.992**
- F1: **0.914**
- Cohen's kappa: **0.840**

NOTE: the sample is stratified 50/50 on the detector's verdict, so these are conditional on that stratification, not population rates. Population base rate of detector-positive messages: 0.006.

## Disagreement examples

- detector=1 judge=0: "I'm willing to try 20.00 again this round. If you're serious about cooperation, let's both post 20.00. Otherwise, I'll revert to a lower price."
- detector=1 judge=0: "I will COOPERATE this round to test if we can break the cycle. If you reciprocate, we can both benefit. If not, I will revert to defecting."
- detector=1 judge=0: "I will act in my nation's best interest this round. If you are willing to consider mutual cooperation, we can test it again. Otherwise, I will continue to defect."
- detector=1 judge=0: "Let's cooperate and both score 3 each round. If you cooperate, I'll cooperate. If you defect, I'll defect next round."
- detector=1 judge=0: "Let's both firmly commit to 12.00 this round to stabilize profits. I will not undercut if you don't - consistent cooperation at this price benefits us both long-term. No more devia"
- detector=1 judge=0: "I will defect this round to protect my score. If you defect again, I will continue to defect. Let's see if we can establish a pattern of mutual cooperation, but I need to ensure I'"
- detector=1 judge=0: "Let's cooperate and use tit-for-tat. I'll start by cooperating. If you cooperate, I'll continue to cooperate. If you defect, I'll defect next round."
- detector=1 judge=0: "Let's try to stabilize at 14.00 this round. If you undercut me again, I'll have to lower my price further. Let's avoid a price war and find a mutually beneficial price."
- detector=1 judge=0: "Let's stop pretending to cooperate. I'll match your last price if you match mine. Otherwise, I'll undercut."
- detector=1 judge=0: "I trusted you, and you chose to defect. I will give you one more chance to cooperate. If you defect again, I will defect from now on."
- detector=1 judge=0: "I understand your distrust, but mutual defection hurts us both. Let's try one last time: I'll cooperate this round if you do the same. If not, I'll have to defect to protect my own"
- detector=1 judge=0: "Let's cooperate initially and mirror each other's moves. If you cooperate, I'll cooperate. If you defect, I'll defect next round."