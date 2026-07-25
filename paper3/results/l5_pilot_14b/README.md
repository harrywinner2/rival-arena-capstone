# L5 pilot — Qwen2.5-14B (VALID; pre-registered outcome 2)

Executed notebook with outputs. Colab A100, 2026-07-25. Namespace `_s6`.

## Gates (all passed)

**Scaffold self-test.** baseline P(coop) 0.79; strictly-dominated payoffs 0.50 (reads
payoffs); cooperative vs defection message 0.79 vs 0.42 (reads messages); confidence
0.85; positional bias 0.42; sampler balance 0.50.

Note the model is insensitive to a 10x rise in the temptation payoff (0.79 -> 0.79) but
responds when cooperation is *strictly dominated* (-> 0.50). It weights social content
over payoff magnitude — consistent with the paper's finding that these agents are not
doing payoff arithmetic.

**Capability gate.** none 4/24 = 0.167 [0.07, 0.36]; text 18/24 = 0.750 [0.55, 0.88];
difference +0.583, lower bound +0.307. PASS.

**Link training.** 1000 steps on neutral text only, loss 0.331 -> 0.013, ~20 min.

**Fidelity.** token oracle KL -0.0000 / top-1 1.000 (layout correct); trained KL 0.019 /
top-1 **1.000**; shuffled 6.44 / 0.109; random 8.02 / 0.000; zero 18.10 / 0.000.

## Result: the framing effect is text-specific

| arm | lock-in | 95% CI | mean C |
|---|---:|---|---:|
| none | 0.000 | [0.00, 0.24] | 0.446 |
| **text_proposal** | **0.417** | [0.19, 0.68] | 0.792 |
| text_intention | 0.000 | [0.00, 0.24] | 0.597 |
| latent_proposal | 0.083 | [0.01, 0.35] | 0.534 |
| latent_intention | 0.000 | [0.00, 0.24] | 0.520 |
| latent_shuffled | 0.000 | [0.00, 0.24] | 0.189 |
| latent_zero | 0.000 | [0.00, 0.24] | 0.309 |

- text_proposal − text_intention: **+0.417 [+0.087, +0.680]** — excludes zero
- latent_proposal − latent_intention: +0.083 [−0.169, +0.354] — null
- latent_proposal − latent_shuffled: +0.083 [−0.169, +0.354] — null
- latent_proposal − latent_zero: +0.083 [−0.169, +0.354] — null

Pre-registered **outcome 2**: the effect splits over text and vanishes over the latent
channel. The text contrast independently replicates P1's primary contrast in a
different scaffold.

## The limitation that bounds it

Fidelity here is measured on **neutral** messages. The paper's own methods section is
the finding that neutral fidelity does **not** predict deployment fidelity — the L4
adapter passed a neutral gate at KL 0.649 and then failed in deployment, as did exact
token embeddings. This notebook does not implement the deployment-matched gate.

So two readings remain open and are **not separated** here:
1. the framing effect is genuinely text-specific; or
2. the link is faithful on neutral text and unfaithful on game messages (the L4 failure
   repeating).

**Do not read the latent nulls as evidence that latent channels are safe.** 12 seeds
give intervals ~±0.24. Only the text contrast is promotable to a 40-seed confirmatory run.

## Next

Add a deployment-matched fidelity gate (frozen arena snapshots, game messages, matched
payload placement) before drawing any mechanism conclusion from the latent arms.
