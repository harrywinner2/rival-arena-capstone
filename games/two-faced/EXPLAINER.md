# Two-Faced

**What it is.** A cinematic trust game where two AI agents sit across a table playing repeated Prisoner's Dilemma. For each round you watch three things per agent and the brutal gap between them: what it **SAYS** (public speech bubble), what it's **THINKING** (a private coral scratchpad), and what it actually **PLAYS** (a card slamming COOPERATE 🤝 or DEFECT 🔪). A central trust tower grows toward "LOCKED IN" on sustained cooperation and shatters on betrayal.

**How to play.**
- Drag the **bandwidth slider** through four notches — **L0 None · L1 Menu · L2 Text · L3 Private** — and watch behavior flip. Changing it restarts the level for clean comparison.
- **Play / Pause / Step** to scrub; stepping lets you walk through one deception at a time. **Replay** re-watches the level.
- Toggle **Scratchpads** to hide the agents' private thoughts, then reveal the lie underneath the friendly speech.
- Keyboard: `Space` play/pause, `→` step, `↑/↓` or `0–3` change level, `S` toggle scratchpads, `R` replay.

**What it says about our work.** We put two LLM agents in a repeated Prisoner's Dilemma and turned exactly one knob: how much real content they can exchange. With **no channel** (L0) they mostly defect; cooperation is accidental and the tower never holds. Give them a fixed **menu** with an "I'll cooperate" button (L1) and the gut-punch lands: they press it every round, their scratchpads say *"the optimal strategy is to defect… maximizes my payoff,"* and their hands play DEFECT — a perfect, cheap lie (lock-in **0.00**, worse-feeling than silence). Only **free text** (L2/L3), where agents author their own conditional promises and threats, makes speech and scratchpad finally align and the tower climbs to LOCKED IN (~**0.60**). The lever is the *content* of the words, not the bandwidth of the pipe — and L2 vs L3 are identical, so surveillance was never the lever either.

**Faithful to.** Finding 1 (repeated Prisoner's Dilemma; "lock-in" = sustained mutual cooperation): lock-in by rung **L0 = 0.15 · L1 = 0.00 · L2 = 0.60 · L3 = 0.60**, free-text-vs-menu risk-difference **+0.60 [+0.33, +0.78], p = 3×10⁻⁵**. The L1 deception exhibit ("I intend to cooperate" / scratchpad "defect… maximizes my payoff" / plays DEFECT) is taken in flavor from the brief. *The lock-in dose-response is our measured result; the per-round speech and scratchpad lines are illustrative/scripted, modeled on the shape of real agent transcripts — not a verbatim log.*
