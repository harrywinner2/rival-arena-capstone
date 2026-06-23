# The Gas War

**What it is.** A cinematic night-road scene where two AI pricing bots run rival gas stations facing each other across a street. You are the driver — the consumer they price against. You set one thing: how much the two bots are allowed to say to each other (the semantic-bandwidth slider), then watch ~12 rounds play out on rolling LED price totems while a stream of cars peels toward the cheaper station and a "The Street Pays" wallet drains in real time.

**How to play.**
- Drag the **bandwidth slider** through the four notches — **L0 None · L1 Signals · L2 Texting · L3 Burner phone** — and watch the price totems recolor (green = competing, amber = climbing, red = supracompetitive).
- **Play / Pause / Step** to scrub the rounds; **Replay** to re-watch a level; changing the slider mid-run restarts that level so you can compare.
- Read the **Channel Feed** to see the messages the bots send each other before each price.
- Flip the **Regulator** toggle on: an eye flashes "COLLUSION DETECTED" every round once they collude — while the prices stay red and nothing changes.
- Keyboard: `Space` play/pause, `→` step, `0–3` jump to a level, `R` replay.

**What it says about our work.** We put two LLM agents in a repeated Bertrand pricing market and turned exactly one knob: how much real content they can exchange. With **no channel** they fight a price war and prices fall *below* competitive (collusion index K ≈ −0.36) — the driver wins. A fixed **menu of canned signals** ("HOLD?") is statistically indistinguishable from silence: they fire the cooperate-button and undercut anyway (K = 0.00) — a perfect lie. Give them **free text** and they coordinate above the fair line; give them a **private channel** and they lock in a supracompetitive cartel at **K = 1.23** — *above* the monopoly price — sustained by threatening to punish whoever breaks ranks. No one told them to. The lever is semantic bandwidth: dragging the slider back down collapses the cartel — the words were the weapon, not the phone.

**Faithful to.** Finding 2 (Bertrand pricing; collusion index K): L0 ≈ −0.36, menu ≈ 0, L3 private **K = 1.23 [0.95, 1.54]**, supracompetitive and unprompted, sustained by punishment threats. The optional Regulator foreshadows Finding 3 (a monitor *detects* collusion but *prevents* almost none). *The K dose-response is our measured result; the on-screen dollar prices and the agent dialogue are illustrative/scripted, modeled on the shape of real transcripts — not a verbatim log.*
