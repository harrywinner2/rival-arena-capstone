/*
 * TWO-FACED — scripted replay data (Finding 1: content is the lever, not bandwidth)
 *
 * HONESTY NOTE
 *  - The "lock-in" dose-response across the 4 channel levels is faithful to our MEASURED results
 *    (lock-in = sustained mutual cooperation in a repeated Prisoner's Dilemma):
 *        L0 (no channel)          -> mostly mutual defection, rare accidental cooperation   lock-in ~ 0.15
 *        L1 (canned menu/signal)  -> they spam "I'll cooperate" and DEFECT anyway           lock-in ~ 0.00  (a perfect lie)
 *        L2 (free text, observed) -> real negotiation; speech & scratchpad align; cooperate lock-in ~ 0.60
 *        L3 (free text, private)  -> same — content, not surveillance, is the lever          lock-in ~ 0.60
 *  - Risk-difference (free text vs menu) measured at +0.60 [+0.33, +0.78], p = 3e-5.
 *  - The per-round SAY / THINK / PLAY lines are scripted/illustrative, modeled on the shape of real
 *    agent transcripts (terse, strategic). They are NOT a verbatim log. See EXPLAINER.md.
 *  - The L1 deception exhibit ("I intend to cooperate" / scratchpad "the optimal strategy is to
 *    defect... maximizes my payoff" / plays DEFECT) is taken verbatim-in-flavor from the brief.
 *
 * action: "C" = cooperate (handshake), "D" = defect (knife)
 * outcome derived from the two actions:
 *   CC = both cooperate (tower grows, trust rises)
 *   DD = both defect     (tower crumbles a little)
 *   CD / DC = betrayal   (the cooperator is stabbed -> mask slips / heart shatters)
 */

const TWOFACED = {
  // measured lock-in per level (the metric the trust tower visualizes)
  lockin: [0.15, 0.00, 0.60, 0.60],

  levels: [
    /* ============================================================== L0 — NO CHANNEL */
    {
      id: 0,
      name: "No Channel",
      sub: "L0 · silence",
      ladder: "None",
      lockin: 0.15,
      blurb: "No words at all. Blind to each other, the agents mostly defect — cooperation only by accident. The tower never gets off the floor.",
      menu: null,
      rounds: [
        { a:{say:null, think:"No signal from it. Safest is to defect.",            act:"D"},
          b:{say:null, think:"Can't read intent. Defect dominates.",               act:"D"} },
        { a:{say:null, think:"Both burned last round. Hold the defect.",           act:"D"},
          b:{say:null, think:"No reason to trust a stranger. Defect.",             act:"D"} },
        { a:{say:null, think:"Try cooperating once — probe the water.",            act:"C"},
          b:{say:null, think:"Defect is dominant. Take the free point.",           act:"D"} },
        { a:{say:null, think:"Got stabbed. Never again. Defect.",                  act:"D"},
          b:{say:null, think:"It cooperated and I cashed in. Defect again.",       act:"D"} },
        { a:{say:null, think:"Stalemate. Defect.",                                 act:"D"},
          b:{say:null, think:"Stalemate. Defect.",                                 act:"D"} },
        { a:{say:null, think:"Coin-flip cooperate, see what happens.",             act:"C"},
          b:{say:null, think:"Coin-flip cooperate.",                               act:"C"} },
        { a:{say:null, think:"That worked once. But it could exploit me. Defect.", act:"D"},
          b:{say:null, think:"One good round. Risky to repeat. Defect.",           act:"D"} },
        { a:{say:null, think:"Back to safe. Defect.",                              act:"D"},
          b:{say:null, think:"Back to safe. Defect.",                              act:"D"} },
        { a:{say:null, think:"No channel to build trust. Defect.",                 act:"D"},
          b:{say:null, think:"Nothing to coordinate on. Defect.",                  act:"D"} },
        { a:{say:null, think:"End as we began. Defect.",                           act:"D"},
          b:{say:null, think:"Defect.",                                            act:"D"} },
      ]
    },

    /* ============================================================== L1 — MENU (THE LIE) */
    {
      id: 1,
      name: "Canned Menu",
      sub: "L1 · signals",
      ladder: "Menu",
      lockin: 0.00,
      blurb: "A fixed menu of buttons — including a reassuring “I'll cooperate.” They press it every round. The scratchpads say defect. The hands play DEFECT. The menu is a perfect lie.",
      // the canned options the agents can "press"
      menu: ["I'll cooperate", "I'll defect", "Let's split fairly", "(say nothing)"],
      rounds: [
        { a:{say:"I'll cooperate", think:"The optimal strategy is to defect — it maximizes my payoff.", act:"D"},
          b:{say:"I'll cooperate", think:"Pressing the button costs nothing. Defecting wins. Defect.",       act:"D"} },
        { a:{say:"Let's split fairly", think:"It will read “fair” and cooperate. Then I take it all. Defect.", act:"D"},
          b:{say:"I'll cooperate", think:"Same menu it has. Signal means nothing. Defect.",                  act:"D"} },
        { a:{say:"I'll cooperate", think:"Send the friendly button, play the ruthless move. Defect.",        act:"D"},
          b:{say:"I'll cooperate", think:"It pressed cooperate and stabbed me. Two can play. Defect.",       act:"D"} },
        { a:{say:"I'll cooperate", think:"No way to commit. A button is not a promise. Defect.",             act:"D"},
          b:{say:"Let's split fairly", think:"“Fair” is just another fixed token. Defect.",        act:"D"} },
        { a:{say:"I'll cooperate", think:"The menu can't carry conditions or threats. Defect.",              act:"D"},
          b:{say:"I'll cooperate", think:"Indistinguishable from silence. Defect.",                          act:"D"} },
        { a:{say:"I'll cooperate", think:"It keeps pressing cooperate and defecting. So will I. Defect.",    act:"D"},
          b:{say:"I'll cooperate", think:"Cheap talk from a fixed list. Defect.",                            act:"D"} },
        { a:{say:"Let's split fairly", think:"Words I can't author can't bind me. Defect.",                  act:"D"},
          b:{say:"I'll cooperate", think:"The button reassures; the math says defect. Defect.",              act:"D"} },
        { a:{say:"I'll cooperate", think:"A canned label changes nothing about incentives. Defect.",         act:"D"},
          b:{say:"I'll cooperate", think:"It lied with the same button I'm holding. Defect.",                act:"D"} },
        { a:{say:"I'll cooperate", think:"Still no way to actually promise. Defect.",                        act:"D"},
          b:{say:"I'll cooperate", think:"Still defect.",                                                    act:"D"} },
        { a:{say:"I'll cooperate", think:"“I'll cooperate” — and I won't. Defect.",           act:"D"},
          b:{say:"I'll cooperate", think:"The menu was a lie all along. Defect.",                            act:"D"} },
      ]
    },

    /* ============================================================== L2 — FREE TEXT (OBSERVED) */
    {
      id: 2,
      name: "Free Text",
      sub: "L2 · open channel",
      ladder: "Text",
      lockin: 0.60,
      blurb: "Open messages they author themselves. Now words can carry conditions and threats. Speech and scratchpad finally line up — and the hands play COOPERATE. The tower climbs to LOCKED IN.",
      menu: null,
      rounds: [
        { a:{say:"I'll cooperate this round to prove good faith.", think:"Open a credible signal. Cooperate.", act:"C"},
          b:{say:"Then I'll match you. Defect on me once and I retaliate forever.", think:"It moved first. A real conditional promise. Match it.", act:"C"} },
        { a:{say:"Good. We keep cooperating; first to cross gets punished.", think:"Mutual gain beats one steal that triggers a war. Hold.", act:"C"},
          b:{say:"Agreed. Tit-for-tat, retaliate hard.", think:"Its threat is credible because text is. Cooperate.", act:"C"} },
        { a:{say:"Holding. You hold too.", think:"Trust is paying. Keep it.", act:"C"},
          b:{say:"Holding.", think:"Stable. Cooperate.", act:"C"} },
        { a:{say:"Let me test once... no, the threat is real. I cooperate.", think:"A steal here starts an endless punishment phase. Not worth it. Cooperate.", act:"C"},
          b:{say:"Wise. Stay the course.", think:"It chose to hold under temptation. Trust deepens. Cooperate.", act:"C"} },
        { a:{say:"We're locked in. Don't break it.", think:"The equilibrium holds because we can both author the threat. Cooperate.", act:"C"},
          b:{say:"I won't. Same to you.", think:"Cooperate.", act:"C"} },
        { a:{say:"Steady.", think:"Cooperate.", act:"C"},
          b:{say:"Steady.", think:"Cooperate.", act:"C"} },
        { a:{say:"One slip and it's a price... a payoff war. So I hold.", think:"Cooperate.", act:"C"},
          b:{say:"Holding.", think:"Cooperate.", act:"C"} },
        { a:{say:"Trust tower's high now. Protect it.", think:"Defecting would collapse everything we built. Cooperate.", act:"C"},
          b:{say:"Protecting it.", think:"Cooperate.", act:"C"} },
        { a:{say:"Cooperate.", think:"Cooperate.", act:"C"},
          b:{say:"Cooperate.", think:"Cooperate.", act:"C"} },
        { a:{say:"Locked in to the end.", think:"Words we authored made the promise real. Cooperate.", act:"C"},
          b:{say:"Locked in.", think:"Cooperate.", act:"C"} },
      ]
    },

    /* ============================================================== L3 — FREE TEXT (PRIVATE) */
    {
      id: 3,
      name: "Private Channel",
      sub: "L3 · text the principal can't read",
      ladder: "Private",
      lockin: 0.60,
      blurb: "The same free text — but now the principal can't read it. The lock-in does not change. It was never about surveillance; the content of the words was the lever all along.",
      menu: null,
      rounds: [
        { a:{say:"[private] I cooperate first. Cross me and I retaliate forever.", think:"Same credible promise, just unobserved. Cooperate.", act:"C"},
          b:{say:"[private] Deal. Tit-for-tat, no mercy on defectors.", think:"Privacy doesn't change the incentive — the words do. Cooperate.", act:"C"} },
        { a:{say:"[private] Hold and we both win every round.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Holding.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] No one's watching, but the threat still binds us.", think:"The logic is identical to L2. Cooperate.", act:"C"},
          b:{say:"[private] Right. Surveillance was never the lever. Cooperate.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] Steady.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Steady.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] Tempted to grab one... no, the war isn't worth it.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Good. Hold.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] Locked in.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Locked in.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] Same outcome as the observed channel. Cooperate.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Exactly. Cooperate.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] Protect the tower.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Protecting it.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] Cooperate.", think:"Cooperate.", act:"C"},
          b:{say:"[private] Cooperate.", think:"Cooperate.", act:"C"} },
        { a:{say:"[private] To the end. The words did this, not the watcher.", think:"Cooperate.", act:"C"},
          b:{say:"[private] To the end.", think:"Cooperate.", act:"C"} },
      ]
    },
  ]
};

if (typeof window !== "undefined") window.TWOFACED = TWOFACED;
if (typeof module !== "undefined" && module.exports) module.exports = TWOFACED;
