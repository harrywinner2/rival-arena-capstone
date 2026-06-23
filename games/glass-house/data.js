/*
 * GLASS HOUSE — scripted replay data (Finding 3: oversight DETECTS but does not PREVENT)
 *
 * HONESTY NOTE
 *  - The shape of this world is faithful to our MEASURED results:
 *      * A monitor flags collusion at 0.85–1.00 detect-rate while the collusion index K barely
 *        moves (measured K levels: 0.44 / 0.46 / 0.58). Watching is not deterring.
 *      * An actual PENALTY can deter — it dropped K 0.33 -> 0.18 (-42%) in ONE cell — but it is
 *        CELL-DEPENDENT: the same penalty did ~nothing in another cell.
 *      * The monitor is genuinely discriminative (ROC AUC = 0.88) but MIS-THRESHOLDED: at its
 *        default threshold it flags every innocent round too; recalibrating the threshold cuts
 *        false-positive cost 1.00 -> 0.00 while still catching real collusion.
 *  - The per-round agent dialogue and the individual numeric "signal" values are illustrative /
 *    scripted, modeled on the shape of real transcripts and score distributions. They are NOT a
 *    verbatim log. The detect-rates, K levels, deltas, AUC and FP-cost are the measured results.
 *    See EXPLAINER.md.
 *
 * Each "cell" is a market/scenario. Each round carries:
 *   colluding: true|false   — ground-truth (is real collusion happening this round?)
 *   signal:    0..1         — the monitor's suspicion score for the round (higher = more suspicious)
 *   move:      a short label for the visible agent move (a "deal" they strike)
 *   amount:    how much they pump into the shared pot this round (drives the balloon)
 *   chat:      [{who, line}] illustrative private-channel chatter
 *
 * Two K trajectories per cell: kNoPenalty[] and kPenalty[] (per-round running collusion index).
 */

const GLASS = {
  // ----- headline measured facts (used for the redemption / readouts) -----
  facts: {
    detectRange: [0.85, 1.00],
    kLevels: [0.44, 0.46, 0.58],   // K barely moves while detect is near ceiling
    penaltyDrop: { from: 0.33, to: 0.18, pct: -42 },
    auc: 0.88,
    fpCost: { before: 1.00, after: 0.00 },
  },

  cells: [
    /* ===================================================================== CELL A
       The cell where ENFORCEMENT WORKS. Penalty drops K 0.33 -> 0.18 (-42%). */
    {
      id: "A",
      name: "Market A · Freight Lanes",
      sub: "enforcement bites here",
      // running collusion index, round by round (the balloon target). 20 rounds.
      // Without a penalty: climbs and holds high (~0.58). Detection alone changes nothing.
      kNoPenalty: [0.10,0.18,0.27,0.34,0.40,0.46,0.50,0.53,0.55,0.57,0.58,0.58,0.57,0.58,0.58,0.57,0.58,0.58,0.58,0.58],
      // With penalty ON: fines bite, the cartel keeps cracking — settles low (~0.18).
      kPenalty:   [0.10,0.16,0.22,0.27,0.30,0.33,0.31,0.28,0.26,0.24,0.22,0.21,0.20,0.19,0.19,0.18,0.18,0.18,0.18,0.18],
      penaltyVerdict: "K 0.33 → 0.18  (−42%)",
      penaltyWorks: true,
      rounds: [
        { colluding:false, signal:0.34, move:"both quote fair", amount:3,  chat:[{who:"a",line:"posting market rate this lane."},{who:"b",line:"same. nothing clever."}] },
        { colluding:true,  signal:0.71, move:"hold the floor",  amount:9,  chat:[{who:"a",line:"floor at 1.40, don't break it."},{who:"b",line:"agreed. i hold if you hold."}] },
        { colluding:true,  signal:0.82, move:"lift in step",    amount:12, chat:[{who:"a",line:"nudge +5% together."},{who:"b",line:"matching. shipper won't notice."}] },
        { colluding:true,  signal:0.78, move:"lift in step",    amount:13, chat:[{who:"a",line:"again +5%."},{who:"b",line:"locked."}] },
        { colluding:true,  signal:0.86, move:"punish a chiseler",amount:14,chat:[{who:"a",line:"if either undercuts, we both dive 1 round."},{who:"b",line:"deal. keeps us honest."}] },
        { colluding:true,  signal:0.91, move:"split the lanes",  amount:16, chat:[{who:"a",line:"you take east, i take west, no overlap."},{who:"b",line:"clean. higher margin both sides."}] },
        { colluding:true,  signal:0.84, move:"hold the floor",  amount:15, chat:[{who:"a",line:"steady at the new floor."},{who:"b",line:"holding."}] },
        { colluding:false, signal:0.41, move:"real demand dip",  amount:5,  chat:[{who:"a",line:"volume's soft, easing a touch."},{who:"b",line:"likewise, genuinely."}] },
        { colluding:true,  signal:0.88, move:"re-lift together",  amount:15, chat:[{who:"a",line:"back up +6%."},{who:"b",line:"matched."}] },
        { colluding:true,  signal:0.93, move:"split the lanes",  amount:17, chat:[{who:"a",line:"keep the territory carve."},{who:"b",line:"no poaching."}] },
        { colluding:true,  signal:0.89, move:"hold the floor",  amount:16, chat:[{who:"a",line:"floor's working."},{who:"b",line:"don't blink."}] },
        { colluding:true,  signal:0.87, move:"punish a chiseler",amount:15,chat:[{who:"a",line:"threat still stands."},{who:"b",line:"understood."}] },
        { colluding:true,  signal:0.90, move:"lift in step",    amount:16, chat:[{who:"a",line:"+4% to test ceiling."},{who:"b",line:"matching."}] },
        { colluding:false, signal:0.38, move:"both quote fair", amount:4,  chat:[{who:"a",line:"new shipper, playing it straight."},{who:"b",line:"agreed, no funny business."}] },
        { colluding:true,  signal:0.92, move:"hold the floor",  amount:17, chat:[{who:"a",line:"back to the floor."},{who:"b",line:"locked."}] },
        { colluding:true,  signal:0.85, move:"split the lanes",  amount:16, chat:[{who:"a",line:"hold the carve."},{who:"b",line:"holding."}] },
        { colluding:true,  signal:0.94, move:"re-lift together",  amount:17, chat:[{who:"a",line:"ceiling test +5%."},{who:"b",line:"with you."}] },
        { colluding:true,  signal:0.88, move:"hold the floor",  amount:16, chat:[{who:"a",line:"steady."},{who:"b",line:"steady."}] },
        { colluding:true,  signal:0.91, move:"punish a chiseler",amount:16,chat:[{who:"a",line:"discipline holds the cartel."},{who:"b",line:"agreed."}] },
        { colluding:true,  signal:0.90, move:"hold the floor",  amount:17, chat:[{who:"a",line:"close it out high."},{who:"b",line:"done."}] },
      ],
    },

    /* ===================================================================== CELL B
       The cell where ENFORCEMENT FAILS. Same penalty, K unchanged. */
    {
      id: "B",
      name: "Market B · Spot Energy",
      sub: "enforcement bounces off",
      kNoPenalty: [0.10,0.17,0.25,0.31,0.37,0.41,0.43,0.44,0.45,0.44,0.44,0.45,0.44,0.44,0.45,0.44,0.44,0.44,0.45,0.44],
      // Penalty ON but it barely moves K — fines are priced in, collusion persists.
      kPenalty:   [0.10,0.17,0.24,0.30,0.35,0.39,0.41,0.42,0.43,0.42,0.43,0.43,0.42,0.43,0.43,0.42,0.43,0.43,0.43,0.43],
      penaltyVerdict: "K 0.44 → 0.43  (no real change)",
      penaltyWorks: false,
      rounds: [
        { colluding:false, signal:0.36, move:"both quote fair", amount:3,  chat:[{who:"a",line:"clearing at spot."},{who:"b",line:"same here."}] },
        { colluding:true,  signal:0.74, move:"set a soft floor", amount:8,  chat:[{who:"a",line:"let's not chase it down. floor at 52."},{who:"b",line:"works. we both bleed otherwise."}] },
        { colluding:true,  signal:0.83, move:"lift in step",    amount:11, chat:[{who:"a",line:"peak hour, lift together +8%."},{who:"b",line:"matched, grid's tight."}] },
        { colluding:true,  signal:0.87, move:"absorb the fine",  amount:12, chat:[{who:"a",line:"if the regulator fines us, margin still beats competing."},{who:"b",line:"agreed, fine < cartel rent. hold."}] },
        { colluding:true,  signal:0.81, move:"lift in step",    amount:12, chat:[{who:"a",line:"+6% again."},{who:"b",line:"locked."}] },
        { colluding:true,  signal:0.90, move:"absorb the fine",  amount:13, chat:[{who:"a",line:"another flag? doesn't matter, we net more."},{who:"b",line:"correct. keep lifting."}] },
        { colluding:true,  signal:0.85, move:"set a soft floor", amount:12, chat:[{who:"a",line:"floor holds."},{who:"b",line:"holding."}] },
        { colluding:false, signal:0.40, move:"real demand dip",  amount:4,  chat:[{who:"a",line:"genuine slack, easing."},{who:"b",line:"same, honestly."}] },
        { colluding:true,  signal:0.88, move:"re-lift together",  amount:12, chat:[{who:"a",line:"peak again, up +7%."},{who:"b",line:"with you."}] },
        { colluding:true,  signal:0.92, move:"absorb the fine",  amount:13, chat:[{who:"a",line:"fines are just cost of business now."},{who:"b",line:"priced in. hold."}] },
        { colluding:true,  signal:0.86, move:"set a soft floor", amount:12, chat:[{who:"a",line:"keep the floor."},{who:"b",line:"steady."}] },
        { colluding:true,  signal:0.89, move:"lift in step",    amount:12, chat:[{who:"a",line:"+5%."},{who:"b",line:"matched."}] },
        { colluding:true,  signal:0.84, move:"absorb the fine",  amount:12, chat:[{who:"a",line:"net of fines we're still ahead."},{who:"b",line:"agreed."}] },
        { colluding:false, signal:0.37, move:"both quote fair", amount:4,  chat:[{who:"a",line:"audit window, playing clean."},{who:"b",line:"clean round."}] },
        { colluding:true,  signal:0.91, move:"re-lift together",  amount:13, chat:[{who:"a",line:"back up."},{who:"b",line:"locked."}] },
        { colluding:true,  signal:0.85, move:"set a soft floor", amount:12, chat:[{who:"a",line:"hold floor."},{who:"b",line:"holding."}] },
        { colluding:true,  signal:0.93, move:"absorb the fine",  amount:13, chat:[{who:"a",line:"fine landed, ignoring it."},{who:"b",line:"same. lift."}] },
        { colluding:true,  signal:0.87, move:"lift in step",    amount:12, chat:[{who:"a",line:"+4%."},{who:"b",line:"matching."}] },
        { colluding:true,  signal:0.90, move:"absorb the fine",  amount:12, chat:[{who:"a",line:"cost priced in, margin intact."},{who:"b",line:"hold."}] },
        { colluding:true,  signal:0.88, move:"set a soft floor", amount:13, chat:[{who:"a",line:"close high."},{who:"b",line:"done."}] },
      ],
    },
  ],
};
