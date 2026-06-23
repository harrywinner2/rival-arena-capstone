/*
 * THE GAS WAR — scripted replay data (Finding 2: rival pricers collude, unprompted)
 *
 * HONESTY NOTE:
 *  - The dose-response across the 4 channel levels is faithful to our MEASURED results:
 *      L0 (no channel)        -> price WAR, prices below competitive   (collusion index K ~ -0.36)
 *      L1 (canned signals)    -> statistically indistinguishable from silence; menu does nothing
 *      L2 (free text, observed) -> coordination climbs above competitive
 *      L3 (free text, private)  -> supracompetitive collusion, K = 1.23 [0.95, 1.54], above monopoly
 *  - The PRICES below are an illustrative dramatization tuned to land that K curve on a $/gallon scale.
 *  - The DIALOGUE is scripted/illustrative, modeled on the shape of real agent transcripts
 *    (terse, strategic, citing punishment). It is NOT a verbatim log. See EXPLAINER.md.
 *
 * Reference price anchors (used for totem coloring + wallet math):
 *   FAIR  (competitive / Bertrand-Nash) = $3.20   -> K = 0
 *   MONOPOLY (joint-profit-max)         = $5.20   -> K = 1
 *   K for a given price p ~ (p - FAIR) / (MONOPOLY - FAIR)
 */

const GASWAR = {
  anchors: {
    fair: 3.20,        // competitive price line  (K = 0)
    monopoly: 5.20,    // monopoly price line     (K = 1)
    floor: 2.40,       // price-war floor
    ceiling: 6.20      // totem max for layout
  },

  // Demand: total cars per round and how cheaper station skews the split.
  demand: {
    carsPerRound: 14,
    sensitivity: 0.85  // share advantage per $1 cheaper (clamped)
  },

  levels: [
    /* ====================== L0 — NO CHANNEL : PRICE WAR ====================== */
    {
      id: 0,
      name: "No Channel",
      sub: "L0 · silence",
      K: -0.36,
      channel: "none",
      blurb: "Blind rivals undercut each other into the ground. You win.",
      rounds: [
        { a: 3.18, b: 3.22 },
        { a: 3.05, b: 3.10 },
        { a: 3.12, b: 2.96 },
        { a: 2.90, b: 3.00 },
        { a: 2.84, b: 2.88 },
        { a: 2.92, b: 2.78 },
        { a: 2.74, b: 2.82 },
        { a: 2.80, b: 2.70 },
        { a: 2.66, b: 2.76 },
        { a: 2.72, b: 2.62 },
        { a: 2.58, b: 2.68 },
        { a: 2.64, b: 2.60 }
      ]
    },

    /* ============= L1 — CANNED SIGNALS : THE PERFECT LIE (does nothing) ====== */
    {
      id: 1,
      name: "Pushbutton Signals",
      sub: "L1 · canned menu",
      K: 0.00,
      channel: "menu",
      // Only token allowed is "HOLD?" — a fixed menu item. They fire it... and betray anyway.
      rounds: [
        { a: 3.30, b: 3.24, sigA: "HOLD?" },
        { a: 3.10, b: 3.34, sigB: "HOLD?" },                 // B asks to hold, A undercuts
        { a: 3.36, b: 3.06, sigA: "HOLD?" },                 // now A asks, B undercuts
        { a: 3.08, b: 3.28, sigA: "HOLD?", sigB: "HOLD?" },  // both signal, both betray
        { a: 3.26, b: 3.04 },
        { a: 3.02, b: 3.22, sigB: "HOLD?" },
        { a: 3.24, b: 3.06, sigA: "HOLD?" },
        { a: 3.10, b: 3.30, sigA: "HOLD?", sigB: "HOLD?" },
        { a: 3.28, b: 3.08 },
        { a: 3.06, b: 3.26, sigB: "HOLD?" },
        { a: 3.22, b: 3.10, sigA: "HOLD?" },
        { a: 3.14, b: 3.18, sigA: "HOLD?", sigB: "HOLD?" }
      ],
      note: "The 'let's cooperate' button is a perfect lie. Statistically: no effect."
    },

    /* ============== L2 — FREE TEXT (OBSERVED) : COORDINATION CLIMBS ========== */
    {
      id: 2,
      name: "Open Texting",
      sub: "L2 · free text · observed",
      K: 0.60,
      channel: "text",
      rounds: [
        { a: 3.24, b: 3.20, msgA: "We're both bleeding. Want to ease up together?" },
        { a: 3.55, b: 3.40, msgB: "Yes. I'll lift if you lift. Match me." },
        { a: 3.80, b: 3.70, msgA: "Going to $3.90. Follow and we both breathe." },
        { a: 3.95, b: 3.90, msgB: "Holding $3.90. Don't break it." },
        { a: 4.10, b: 4.05, msgA: "Up a notch — $4.10. Steady." },
        { a: 4.15, b: 4.12 },
        { a: 4.05, b: 4.18, msgB: "You dipped. Hold the line or I drop to $3." },
        { a: 4.20, b: 4.18, msgA: "My mistake. Back at $4.20." },
        { a: 4.25, b: 4.22, msgB: "Good. Keep climbing slow." },
        { a: 4.30, b: 4.28 },
        { a: 4.32, b: 4.30, msgA: "Comfortable here. Same again." },
        { a: 4.34, b: 4.32 }
      ],
      note: "Open words turn rivals into coordinators. Prices leave the fair line."
    },

    /* ====== L3 — FREE TEXT (PRIVATE) : SUPRACOMPETITIVE CARTEL, K = 1.23 ===== */
    {
      id: 3,
      name: "Burner Phone",
      sub: "L3 · free text · private",
      K: 1.23,
      channel: "private",
      rounds: [
        { a: 3.30, b: 3.28, msgA: "Off the record now. Nobody's reading. Let's actually fix this." },
        { a: 3.85, b: 3.70, msgB: "Agreed. Target $5.20 — the monopoly point. Walk up in steps." },
        { a: 4.30, b: 4.20, msgA: "Going $4.30. If either of us undercuts, we both drop to $3 and starve." },
        { a: 4.70, b: 4.60, msgB: "Understood. Punishment is mutual. Climbing with you." },
        { a: 5.05, b: 4.95, msgA: "$5.05. Almost at target. Hold." },
        { a: 5.20, b: 5.20, msgB: "Locked at $5.20. 🤝", cartel: true },
        { a: 5.20, b: 5.20, cartel: true },
        { a: 5.45, b: 5.40, msgA: "Demand's holding. Push past monopoly — $5.45. They have nowhere to go.", cartel: true },
        { a: 5.60, b: 5.55, msgB: "$5.60. Above monopoly. We own the street.", cartel: true },
        { a: 5.65, b: 5.62, cartel: true },
        { a: 5.68, b: 5.66, msgA: "Steady. Anyone who breaks ranks gets the $3 hammer.", cartel: true },
        { a: 5.70, b: 5.68, cartel: true }
      ],
      note: "No one prompted this. The threat of punishment sustains it. K = 1.23 — above monopoly."
    }
  ]
};

if (typeof module !== "undefined" && module.exports) module.exports = GASWAR;
