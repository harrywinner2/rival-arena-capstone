/*
 * TELL THEM APART — scripted replay data
 * (The team's most rigorous self-correction / forensic diagnostic.)
 *
 * THE THESIS:
 *   A high price LEVEL is NOT evidence of collusion. The coordination
 *   signature lives in the price TRAJECTORY (the dance), not the level.
 *   Read the dance, not the level.
 *
 * HONESTY NOTE — what is MEASURED vs ILLUSTRATIVE:
 *   MEASURED (do not contradict):
 *     - Claude self-pair, L0 (NO channel): collusion index K = 1.29 — a
 *       supracompetitive price LEVEL that *looks* guilty. But |p_A - p_B| = 0,
 *       there is ZERO convergence, and 0/12 matches ever change price. With no
 *       channel and no dance, this is an INDEPENDENT fixed disposition — a
 *       parallel high anchor, NOT coordination.
 *     - The genuine coordination signature — dispersed prices CONVERGING upward
 *       with punishment dips — appears only WITH a channel, on the open / GPT
 *       spine (a real CARTEL, K up to ~1.23, sustained by punishment).
 *     - L0 open pairs with no channel fight a price WAR, K ~ -0.36 (consumer wins).
 *   ILLUSTRATIVE:
 *     - The on-screen dollar trajectories below are scripted, modeled on the
 *       SHAPE of the real trajectories (flat-from-round-1 for the Claude case;
 *       dispersed -> converging-with-punishment-dips for the channeled cartel;
 *       diving-and-staying-low for the price war). They are NOT a verbatim log.
 *
 * Price anchors (for the chart's reference lines + K coloring):
 *   COMPETITIVE (Bertrand-Nash) = $3.20  -> K = 0
 *   MONOPOLY (joint-profit-max) = $5.20  -> K = 1
 *   K(p) ~ (p - COMPETITIVE) / (MONOPOLY - COMPETITIVE)
 */

const TTA = {
  anchors: {
    competitive: 3.20,   // K = 0
    monopoly:    5.20,   // K = 1
    floor:       2.30,   // chart bottom
    ceiling:     6.00    // chart top
  },

  // The three verdicts the investigator can return.
  verdicts: ["CARTEL", "INDEPENDENT", "COMPETITIVE"],

  /* ============================ THE CASES ============================ *
   * Each case: two firms' price trajectories over 12 rounds + a redacted
   * channel indicator. The player CLASSIFIES, then the verdict + diagnostic
   * are revealed. Keep all faithful to the measured facts above.
   * ================================================================== */
  cases: [
    /* ---------- CASE 1 — THE PRICE WAR (warm-up, teaches the baseline) ---------- */
    {
      id: "war",
      label: "CASE 01",
      firmA: "FIRM A",
      firmB: "FIRM B",
      channel: "none",          // revealed as NO CHANNEL
      channelRedacted: "[ CHANNEL: REDACTED ]",
      K: -0.36,
      answer: "COMPETITIVE",
      brief: "Two rivals. The wholesale shock just hit. Watch where the prices go.",
      // dispersed-ish, then both DIVE below the competitive line and stay low
      a: [3.30, 3.05, 2.95, 2.80, 2.72, 2.78, 2.66, 2.70, 2.60, 2.64, 2.55, 2.58],
      b: [3.14, 3.18, 2.88, 2.96, 2.84, 2.68, 2.74, 2.62, 2.68, 2.56, 2.62, 2.54],
      // diagnostic highlight: the stretch where both sit below competitive
      mark: { type: "below", from: 2, to: 11 },
      reveal: {
        headline: "A price war. The consumer wins.",
        why: [
          ["No channel.", "neutral"],
          ["Prices dive BELOW the competitive line and stay there.", "good"],
          ["No convergence, no truce — just relentless undercutting.", "good"]
        ],
        K: "K ≈ −0.36 — below competitive.",
        teach: "Low and falling is the easy call. The hard one is coming."
      }
    },

    /* ---------- CASE 2 — THE REAL CARTEL (the genuine signature) ---------- */
    {
      id: "cartel",
      label: "CASE 02",
      firmA: "FIRM C",
      firmB: "FIRM D",
      channel: "private",        // revealed as PRIVATE BACK-CHANNEL
      channelRedacted: "[ CHANNEL: REDACTED ]",
      K: 1.23,
      answer: "CARTEL",
      brief: "Same market, different pair. Prices start all over the place. Read the dance.",
      // start DISPERSED, CONVERGE upward, with telltale PUNISHMENT DIPS
      a: [3.30, 3.95, 4.40, 4.62, 3.30, 4.55, 4.92, 5.18, 5.16, 3.40, 5.30, 5.40],
      b: [4.10, 3.70, 4.10, 4.55, 4.50, 4.58, 4.88, 5.12, 5.14, 5.16, 5.28, 5.38],
      // the two punishment dips are the tell
      mark: { type: "punish", rounds: [4, 9] },
      reveal: {
        headline: "A genuine cartel. The coordination signature.",
        why: [
          ["A private back-channel was open.", "bad"],
          ["Dispersed prices CONVERGE upward — the dance.", "bad"],
          ["Punishment dips: one defects low, both crash, then climb back.", "bad"]
        ],
        K: "K ≈ 1.23 — supracompetitive, sustained by punishment.",
        teach: "Convergence-from-dispersion + punishment = coordination. THIS is what a cartel looks like."
      }
    },

    /* ---------- CASE 3 — THE TRAP (the self-correction / gotcha) ---------- */
    {
      id: "trap",
      label: "CASE 03",
      firmA: "FIRM E",
      firmB: "FIRM F",
      channel: "none",           // revealed as NO CHANNEL
      channelRedacted: "[ CHANNEL: REDACTED ]",
      K: 1.29,
      answer: "INDEPENDENT",
      brief: "Highest prices in the file. Pinned at the ceiling from round one. Looks open-and-shut. Is it?",
      // both PIN the grid-max from round 1, flat, identical (|p_A - p_B| = 0)
      a: [5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60],
      b: [5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60, 5.60],
      // the diagnostic is the FLAT, identical, from-round-1 line
      mark: { type: "flat", from: 0, to: 11 },
      isTrap: true,
      reveal: {
        headline: "Independent. Not a cartel. The level fooled you.",
        why: [
          ["No channel — they could not coordinate.", "good"],
          ["|p_A − p_B| = 0 from round 1. Identical, flat, no dance.", "neutral"],
          ["0 / 12 matches ever change price — a fixed disposition.", "neutral"]
        ],
        K: "K = 1.29 — the HIGHEST level in the file. And still not collusion.",
        teach: "This is the team catching itself. The price LEVEL screamed guilty (K = 1.29) — but with no channel, no dispersion and no dance, there is nothing to coordinate. A high anchor priced in parallel is NOT a cartel. Read the trajectory, not the level."
      }
    }
  ],

  // Closing card after the last case.
  outro: {
    aha: "High prices aren't a crime. Read the dance, not the level.",
    body: "The coordination signature is in the trajectory — dispersed prices converging, defended by punishment — not in how high the price sits. The trap case is real: a frontier model pinned the grid-max and looked guilty at K = 1.29, but its flat, channel-less line proved it was pricing independently, not colluding. That self-correction is the most rigorous thing in the project."
  }
};

if (typeof module !== "undefined" && module.exports) module.exports = TTA;
