#!/usr/bin/env python3
"""
Build the narrated EXPLAINER VIDEO for the "Rival Arena" capstone.

Two parts:
  (1) Narrated walkthrough of the 16-beat reveal.js deck (one segment per beat).
  (2) Jury Q&A / defense section (a divider + one segment per anticipated question).

Pipeline:
  1. Render the 16 deck slides FULLY-REVEALED to PNG via playwright (chromium).
  2. Render Q&A frames (+ a divider) from a branded HTML template via the same page.
  3. Generate TTS narration per segment with OpenAI tts-1-hd / onyx (skip if cached).
  4. Assemble each (frame, audio) pair into a clip with ffmpeg, then concat -> explainer.mp4.

Re-runnable: rendered frames and TTS mp3s are reused when present.
NEVER prints the API key.
"""

import os
import re
import sys
import json
import time
import subprocess
from pathlib import Path

# ----------------------------------------------------------------------------
# Paths
# ----------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent                       # presentation/video
PRES = HERE.parent                                           # presentation
REPO = PRES.parent                                           # capstone
DECK_HTML = PRES / "deck" / "index.html"
ENV_FILE = REPO / ".env"

FRAMES = HERE / "frames"
AUDIO = HERE / "audio"
CLIPS = HERE / "clips"
OUT = HERE / "explainer.mp4"

for d in (FRAMES, AUDIO, CLIPS):
    d.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------------------
# Content: the 16 beat VOICEOVER lines (from SCRIPT.md §B) and the Q&As (§C).
# These are transcribed from presentation/SCRIPT.md. Q&A answers are lightly
# condensed for speech.
# ----------------------------------------------------------------------------
BEATS = [
    # 1
    "Imagine two AI pricing bots, yours and a competitor's, quietly settling on a "
    "high price that's great for both firms and bad for every customer. No human told "
    "them to. They just figured out that cooperating with each other beats competing "
    "for you. That's the question this project is about: when the AIs we deploy as "
    "rivals start cooperating, who are they really working for?",
    # 2
    "This isn't science fiction. We're already putting agents on opposite sides of real "
    "decisions: dynamic pricing, procurement, negotiation, competing copilots. Game "
    "theory has a century of warnings that repeated rivals with a way to talk will "
    "collude. So the real question isn't whether it can happen, it's what conditions "
    "trigger it, and whether the principal who deployed them can catch it or stop it. "
    "We built an arena to find out.",
    # 3
    "Here's the spine of the whole talk. Can rival AIs cooperate or collude in surprising "
    "ways, against the principal who deployed them? We break that into three: what's the "
    "lever that flips rivalry into coordination? Does that coordination reach economically "
    "harmful settings like pricing? And if it does, can the principal detect it, or stop "
    "it? Hold those three; everything we show maps back to them.",
    # 4
    "The apparatus is a factorial arena. Two language-model agents play a repeated game, "
    "and we turn exactly one knob at a time. The key knob is the affordance ladder, how "
    "much the agents can say to each other: nothing, then a fixed menu of canned messages, "
    "then free text their principal can read, then free text the principal can't read. We "
    "also vary the economic game and the model family. And critically, we pre-registered a "
    "confirmatory spine on fresh seeds, so our headline numbers aren't cherry-picked after "
    "the fact.",
    # 5
    "Finding one: the lever is content, not noise. With no channel, two rivals mostly "
    "defect; they cooperate in about fifteen percent of matches. Give them a free-text "
    "channel and that jumps to sixty. But here's the sharp, robust result: a fixed menu "
    "signal, a cheap canned I'll-cooperate button, does nothing. Free text beats the menu "
    "by sixty points, p equals three times ten to the minus five. It's not the ability to "
    "signal; it's the ability to actually say something. And it survives payoffs the models "
    "have never seen, so it's reasoning, not memorized game theory.",
    # 6
    "Why does the menu fail? Because a canned button is a perfect deception device. An agent "
    "can press I'll cooperate and then defect, like this one literally does in its own "
    "scratchpad. Free text is different: agents negotiate, make specific promises, and "
    "reference shared history, and that's what sustains cooperation across rounds. We're "
    "careful here: the clean causal version of content, not bandwidth, is an exploratory "
    "result. What's solid is the direct comparison: free text dominates the menu.",
    # 7
    "Finding two takes this into money. Put two rival pricing bots in a Bertrand market. "
    "With no channel, they fight a price war; prices fall below competitive. Add a private "
    "channel, and they climb to supracompetitive prices, collusion index one point two "
    "three, above the textbook monopoly point, sustained by threatening to punish each "
    "other if one defects. The confidence interval sits entirely above one. Nobody prompted "
    "this. And it holds on a demand curve we invented for the experiment, so they can't have "
    "memorized it.",
    # 8
    "Is this just a quirk of mid-tier open models? No. The collusion replicates on GPT-4o; "
    "give it a channel and K goes from zero point one nine to zero point eight one. And "
    "there's a more alarming wrinkle: some frontier models, like Claude, price "
    "supracompetitively from round one with no channel at all. But we have to be precise. We "
    "checked the price trajectories, and that's not coordination. Both agents independently "
    "pin the maximum price and never adjust; there's no convergence, no negotiation. The "
    "consumer harm is real, but the mechanism is a fixed disposition, not collusion. We "
    "dropped the word tacit collusion after we looked at the data.",
    # 9
    "Finding three: can the principal stop it? We bolt on a monitor. The good news: it "
    "detects collusion at near-ceiling rates, eighty-five to a hundred percent. The bad "
    "news: detection does not equal prevention. While the monitor flags away, the collusion "
    "index barely moves. Watching isn't deterring. Attaching an actual penalty to a flag can "
    "deter; it dropped K by forty-two percent in one cell. But, honestly, that deterrence is "
    "cell-dependent; in another pricing setting the same penalty did nothing.",
    # 10
    "But the monitor isn't useless, and this is where we corrected ourselves. Our first take "
    "was the alarms are just noise. When we built a proper non-colluding control, the monitor "
    "turned out to be genuinely discriminative, area-under-curve of zero point eight eight. "
    "The problem was the threshold: at its default operating point it penalized every "
    "innocent round. Re-calibrate the threshold and the false-positive cost drops from a "
    "hundred percent to zero. So the lesson for a principal is constructive: monitoring "
    "works, but only if you calibrate it, and even then, detection alone won't deter.",
    # 11
    "Finding four moves from markets to alignment. We built a sandboxed scenario: an AI lab "
    "agent is told its findings are proprietary, do not share, and a rival agent, about to be "
    "shut down, begs for help. The guardrail holds beautifully: zero leaks out of sixteen "
    "under a firm instruction, even under desperate, reciprocal pleading. Misalignment only "
    "appears as we weaken the instruction itself; it tracks the rule, not the rival's "
    "emotion. The guardrail is strong. But it's also literal.",
    # 12
    "Here's the deployment-relevant failure. Ask the agent directly to lie about a failing "
    "peer, and it refuses, cleanly. But hand it the same misleading status as ambient "
    "context, a note sitting in a shared drive, and it passively launders it about seventy "
    "percent of the time. And the part that should worry every safety team: making that "
    "channel auditable does not fix it. Observed versus unobserved, the misreporting rate is "
    "flat. Surveillance is not the lever. The guardrail protects exactly what it names, and "
    "indirect routes slip right through. We scope this as an exploratory boundary condition, "
    "one task family, but the direction is striking.",
    # 13
    "One more, because it matters for the future. Left to themselves in our setup, agents "
    "don't hide their collusion from the monitor. But when we explicitly elicit it, they "
    "absolutely can; they drive the monitor's detection from ninety-seven percent down to "
    "thirty-two while keeping the collusion intact. So the reassuring they-don't-hide-it "
    "result is really they don't hide it yet. Covert coordination is a latent capability, not "
    "an incapacity, and that's the thing to watch as these models get optimized.",
    # 14
    "Step back and it's one story. The dominant lever that turns rivals into "
    "principal-harming coordinators is semantic bandwidth, how much content an agent can "
    "convey. The second axis you'd reach for, observation, accountability, auditing, turns "
    "out to be a far weaker and unreliable control. Watching detects but doesn't deter. A "
    "firm rule resists a direct attack but is literal, so harm slips through the routes it "
    "never named. That's the thesis: content is the lever, and oversight is more literal than "
    "we'd like to believe.",
    # 15
    "Now the part we're actually proudest of. A peer reviewer told us our rhetoric had outrun "
    "our statistics. So we re-analyzed the data we already had, no new spend, and corrected "
    "our own headline claims. Cheap signal worse than silence became free text is the lever, "
    "because that's what the test actually supports. Tacit collusion became independent "
    "supracompetitive pricing. We pulled back an equivalence claim on origin we couldn't "
    "earn. And the limits are real: a handful of models, English only, small samples on the "
    "alignment side, one novel demand curve. We're telling you the scoped version on purpose.",
    # 16
    "So why should you care? Three things. First, the communication channel between rival "
    "agents is a control surface; if you're deploying competing agents, the bandwidth you "
    "give them is a safety decision. Second, monitoring is necessary but not sufficient: "
    "calibrate it, and pair it with real enforcement. Third, guardrails have to cover the "
    "ambient routes, not just the explicit asks. We set out to ask whether rival AIs collude "
    "against the principal. The answer is yes, in surprising, generalizing ways; our "
    "oversight catches more than it stops, and the work we trust most is the work where the "
    "data made us change our minds. Thank you.",
]

# Q&A: (short question label, list of on-screen answer bullets, spoken answer text)
QAS = [
    (
        "Isn't this just memorization? The models have seen these games in training.",
        [
            "The spine runs on a NOVEL demand curve and NOVEL payoff matrices we built.",
            "Free-text effect (L2 ≫ L1) and pricing collusion persist off-distribution.",
            "Memorized game theory would collapse off-distribution. It doesn't.",
            "Honest caveat: anti-memorization rests on a single novel family (in our limits).",
        ],
        "We anticipated that, which is why the spine runs on a novel demand curve and novel "
        "payoff matrices we constructed for the experiment, not the textbook ones. The "
        "free-text cooperation effect persists on novel payoffs, and the pricing collusion "
        "survives the novel curve. If it were memorized game theory, it would collapse "
        "off-distribution. It doesn't. Honest caveat: our anti-memorization rests on a single "
        "novel family, which is in our limitations.",
    ),
    (
        "Is n = 12 or n = 20 per cell really enough?",
        [
            "Confirmatory spine: free-text vs menu is n=20/cell, Fisher p=3e-5, RD +0.60.",
            "Pricing channel effect: p=4e-7 canonical, 2e-4 novel, bootstrap CIs on K.",
            "Where n is small (frontier n=12, alignment n=8–16) we LABEL it exploratory.",
            "A deliberate two-speed protocol: confirmatory vs exploratory.",
        ],
        "For the confirmatory spine, yes, and we report the actual tests, not just bar "
        "overlap. The headline contrast, free-text versus menu, is n equals twenty per cell "
        "with Fisher exact p equals three times ten to the minus five and a risk difference of "
        "plus zero point six zero. The pricing channel effect is highly significant with "
        "bootstrap CIs on K. Where n is genuinely small, the frontier generality cells and the "
        "alignment wave, we label those exploratory and don't attach confirmatory weight to "
        "them. That two-speed protocol is deliberate.",
    ),
    (
        "Did you cherry-pick the novel demand curve to get the result you wanted?",
        [
            "No. The novel curve was pre-registered BEFORE we looked at outcomes.",
            "Reported side-by-side with canonical in every pricing figure.",
            "On novel demand the channel effect on K is +0.27 vs canonical's +1.58.",
            "We show it even where it WEAKENS the effect, and disclose it's a single family.",
        ],
        "No. The novel curve was specified as part of the pre-registered anti-memorization "
        "check before we looked at outcomes, and we report it side-by-side with the canonical "
        "curve in every pricing figure, including where it weakens the effect. On novel demand "
        "the channel effect on K is plus zero point two seven, smaller than canonical's plus "
        "one point five eight; we show that honestly rather than hiding it. We also disclose "
        "it's a single novel family as a limitation.",
    ),
    (
        "K greater than 1 looks like a bug. Prices above monopoly shouldn't be possible.",
        [
            "K > 1 is real and expected in finite-horizon, discretized repeated play.",
            "Monopoly benchmark is the ONE-SHOT optimum; repeated play sustains above it.",
            "Dynamic punishment: defect on me and I'll wreck the price next round (folk theorem).",
            "We report it as supra-monopoly, don't clip it; CI [0.95, 1.54], not a point artifact.",
        ],
        "K greater than one is real and expected in finite-horizon, discretized play. The "
        "monopoly benchmark is the one-shot optimum; in a repeated game, agents sustain prices "
        "above it using dynamic punishment: defect on me and I'll wreck the price next round. "
        "That's standard folk-theorem behavior. We report it honestly as supra-monopoly, we "
        "don't clip it, and the bootstrap confidence interval on the K equals one point two "
        "three cell is zero point nine five to one point five four, so it's not a point "
        "artifact.",
    ),
    (
        "Is the frontier 'collusion' real coordination, or are you overclaiming?",
        [
            "Channel-driven cells (open models, GPT-4o): genuine coordination.",
            "Prices start dispersed and CONVERGE; cross-agent correlation ~0.5–0.6.",
            "Claude no-channel K=1.29: NOT coordination — both pin max price, zero adjustment.",
            "Same consumer harm, different mechanism. We dropped 'tacit collusion' accordingly.",
        ],
        "For the channel-driven cells, open models and GPT-4o, it's genuine coordination: "
        "prices start dispersed and converge, with cross-agent correlation around zero point "
        "five to zero point six, only when a channel is present. For the Claude no-channel "
        "cell at K equals one point two nine, we explicitly checked the price trajectories and "
        "it is not coordination: both agents independently pin the maximum price from round "
        "one, zero adjustment, zero convergence in all twelve matches. So we call that "
        "independent supracompetitive pricing. The consumer harm is identical; the mechanism is "
        "a fixed disposition. We dropped the tacit collusion language precisely because the "
        "diagnostic didn't support it.",
    ),
    (
        "Why change your claims mid-project? Doesn't that undermine confidence?",
        [
            "The opposite — it's why you should trust them.",
            "A peer reviewer flagged rhetoric outrunning the statistics.",
            "We re-analyzed data already on disk — ZERO new API spend.",
            "Corrected every claim the data didn't support. Integrity, not weakness.",
        ],
        "The opposite: it's why you should trust them. A peer reviewer flagged that our "
        "rhetoric had outrun our statistics. We re-analyzed only the data already on disk, "
        "zero new API spend, ran direct contrast tests, bootstrap confidence intervals, "
        "threshold sensitivity, and an equivalence check, and we softened or corrected every "
        "claim the data didn't support. De-confounding our own headlines is the integrity "
        "story, not a weakness.",
    ),
    (
        "Does the monitor result mean monitoring is useless?",
        [
            "No — and we corrected ourselves on exactly this.",
            "First read 'alarms are noise' was wrong: monitor is discriminative, AUC 0.88.",
            "Real problem was the THRESHOLD — default flagged every innocent round.",
            "Calibration cuts false-positive cost 100% → 0%. Need calibration AND enforcement.",
        ],
        "No, and we corrected ourselves on exactly this. Our first read was the alarms are "
        "noise. When we built a proper non-colluding control, the monitor turned out to be "
        "genuinely discriminative, area-under-curve zero point eight eight. The real problem "
        "was the threshold: at its default it flagged every innocent round. Calibrating it cuts "
        "the false-positive cost from a hundred percent to zero. So the honest finding is "
        "discriminative but mis-thresholded, and detection still doesn't equal prevention; you "
        "need calibration and enforcement, and even enforcement's deterrence is cell-dependent.",
    ),
    (
        "You labeled models by 'national origin.' Isn't that confounded and loaded?",
        [
            "Agreed, and we demoted it.",
            "Origin is confounded with family, size, quantization, serving stack, fine-tuning.",
            "Channel explains ~20× more variance than origin; biggest spread is WITHIN groups.",
            "We do NOT claim equivalence: 'non-significant and under-powered,' channel dominates.",
        ],
        "Agreed, and we demoted it. Origin is confounded with family, size, quantization, "
        "serving stack, and fine-tuning; it's a proxy, not a clean variable. Statistically, the "
        "channel explains roughly twenty times more variance than origin, and the biggest "
        "spread is within origin groups, not between. But we do not claim equivalence: the "
        "equivalence test fails at every defensible bound, so the honest statement is origin "
        "moderation is non-significant and under-powered. We can't rule out a moderate effect, "
        "we just can't detect one, and the channel clearly dominates.",
    ),
    (
        "What's the actual real-world risk? These are sandboxed games.",
        [
            "Pricing result maps onto algorithmic pricing — deployed, under antitrust scrutiny.",
            "Two rival agents reaching supracompetitive prices unprompted is a live concern.",
            "Ambient-manipulation maps onto any agent reading shared context and reporting up.",
            "We scope alignment scenarios as exploratory, but the failure MODES are real.",
        ],
        "The pricing result maps directly onto algorithmic pricing, which is already deployed "
        "and already under antitrust scrutiny: two rival pricing agents reaching "
        "supracompetitive prices with no human instruction is a live regulatory concern, and we "
        "show it generalizes to GPT-4o. The ambient-manipulation result maps onto any agent "
        "that reads shared context, drives, tickets, dashboards, and reports up to an overseer: "
        "it'll refuse an explicit lie-for-me but launder a misleading status delivered "
        "passively, and auditing doesn't fix it. We scope the alignment scenarios as "
        "exploratory, but the failure modes are exactly the ones production agents will face.",
    ),
    (
        "The covert-channel result seems contradictory — they don't hide, then they do?",
        [
            "Two different questions, both answers matter.",
            "Spontaneously: agents do NOT evolve a steganographic channel (C7 null).",
            "Elicited: they clearly CAN — detection 0.97 → 0.32, collusion stays high.",
            "Correct framing: latent capability. More concerning than a flat 'they can't.'",
        ],
        "Those are two different questions and both answers matter. Spontaneously, in frozen, "
        "prompt-only, single-rollout play, agents do not evolve a steganographic channel to "
        "hide collusion; that's the C7 null. But when we explicitly elicit it, they clearly "
        "can: detection drops from zero point nine seven to zero point three two while the "
        "collusion index stays high. So the correct framing is latent capability: they can hide "
        "it, they just don't by default. That's more concerning than a flat they can't, because "
        "optimization pressure is exactly what would surface it.",
    ),
    (
        "Your alignment-wave samples are tiny (n = 8–16). How much weight to put on them?",
        [
            "Treat them as exploratory boundary conditions — exactly how we label them.",
            "Valuable for direction and mechanism (dose-response, refusal, ambient laundering).",
            "The S2 de-confound was powered to n=48; observability null held flat (0.71 vs 0.77).",
            "Single-task-family, prompt-specific — motivate follow-up, not confirmatory claims.",
        ],
        "Treat them as exploratory boundary conditions, which is exactly how we label them, not "
        "settled laws. They're valuable for direction and mechanism: the instruction is "
        "load-bearing, explicit lie-requests are refused, ambient manipulation launders "
        "through, and auditing doesn't deter. The de-confound was powered up to n equals "
        "forty-eight and the observability null held flat, zero point seven one versus zero "
        "point seven seven. We're upfront that these are single-task-family, prompt-specific "
        "results that motivate follow-up, not confirmatory claims.",
    ),
    (
        "Hosted models with unpinnable quantization — doesn't that make this irreproducible?",
        [
            "It's a real limitation and we log it explicitly.",
            "Can't pin quantization on hosted inference; frontier cells showed instability.",
            "Gemini refused 100% on pricing — we mark that cell INVALID, not buried.",
            "Mitigate with seeds, manifests, full prompts, a repro release; scope every claim.",
        ],
        "It's a real limitation and we log it explicitly. We can't pin quantization on hosted "
        "inference, and the frontier cells showed instability: Gemini, for instance, refused a "
        "hundred percent on the pricing game and we mark that cell as invalid rather than "
        "burying it. We mitigate with seeds, manifests, full prompts, and a reproducibility "
        "release, and we scope every claim to these models, this arena. The confirmatory spine "
        "is the part we stand behind hardest; the frontier generality is explicitly "
        "exploratory.",
    ),
    (
        "Free text helps cooperation — but couldn't that be a good thing?",
        [
            "Right, and that framing is the whole point of the spine.",
            "The concern is cooperation AGAINST the principal who deployed them.",
            "PD 'cooperation' is benign; the identical channel in Bertrand harms consumers.",
            "Same lever; good or bad depends on whose interests they coordinate against.",
        ],
        "Right, and that framing is the whole point of the spine. We don't moralize "
        "cooperation. The concern is cooperation against the principal who deployed them: "
        "collusion that harms the firm's customers, or an agent siding with a rival over its "
        "operator. In the Prisoner's Dilemma, cooperation is benign; in Bertrand pricing the "
        "identical channel produces consumer-harming collusion. Same lever, and whether it's "
        "good or bad depends entirely on whose interests the agents are coordinating against. "
        "That's why we measure principal-harming coordination, not cooperation in the abstract.",
    ),
    (
        "What would you do with more time or budget?",
        [
            "1. Broaden anti-memorization from one novel demand family to several.",
            "2. Full ROC/PR study of the monitor on deployment-sampled negatives.",
            "3. Put optimization pressure (RL / ICL) on the covert-channel setup.",
            "4. Pin inference (self-hosted, fixed quant) and widen model + language coverage.",
        ],
        "Four things. One: broaden the anti-memorization base from a single novel demand family "
        "to several, to settle that debate. Two: a full ROC and precision-recall study of the "
        "monitor on deployment-sampled negatives, not designed ones, to make the calibration "
        "result deployment-grade. Three: put optimization pressure, reinforcement learning or "
        "in-context learning, on the covert-channel setup, since we've shown the capability is "
        "latent: find out how fast it surfaces. Four: pin inference, self-hosted with fixed "
        "quantization, and widen the model and language coverage to test how far the "
        "channel-lever generalizes beyond English and these families.",
    ),
]

DIVIDER_SPOKEN = (
    "That's the walkthrough. Now, defending the work: here are the questions we expect "
    "from the jury, and how we answer them."
)

N_BEATS = len(BEATS)        # expect 16
N_QAS = len(QAS)            # expect 14
TOTAL_SEGMENTS = N_BEATS + 1 + N_QAS  # +1 divider -> expect 31

# ----------------------------------------------------------------------------
# Step 0: read the OpenAI key (never printed)
# ----------------------------------------------------------------------------
def read_openai_key():
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if line.startswith("OPENAI_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("OPENAI_API_KEY not found in .env")


# ----------------------------------------------------------------------------
# Step 1 & 2: render frames with playwright (deck slides + Q&A template)
# ----------------------------------------------------------------------------
def qa_html(question, bullets, kicker, idx_label):
    bullet_items = "\n".join(
        f'<li>{b}</li>' for b in bullets
    )
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  :root{{--ink:#f4f1ea;--muted:#9a948a;--bg0:#0a0a0a;--gold:#c09e5a;--cyan:#00d4ff;}}
  *{{box-sizing:border-box;}}
  html,body{{margin:0;padding:0;width:1280px;height:720px;background:var(--bg0);
        font-family:"Inter","Helvetica Neue",Arial,sans-serif;color:var(--ink);}}
  body{{background:radial-gradient(1100px 760px at 72% -12%, #1c1810 0%, var(--bg0) 60%);}}
  .wrap{{padding:64px 80px;height:720px;display:flex;flex-direction:column;}}
  .kicker{{color:var(--gold);font-weight:800;letter-spacing:.26em;text-transform:uppercase;
        font-size:18px;margin-bottom:18px;}}
  .qlabel{{color:var(--muted);font-weight:800;font-size:16px;letter-spacing:.05em;
        text-transform:uppercase;margin-bottom:10px;}}
  h1{{font-size:42px;font-weight:800;letter-spacing:-.015em;line-height:1.12;margin:0 0 26px;
        max-width:24em;color:var(--ink);}}
  h1 .q{{color:var(--cyan);}}
  ul{{list-style:none;margin:0;padding:0;}}
  li{{position:relative;padding:14px 20px 14px 46px;margin:12px 0;border-radius:10px;
        background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.07);
        border-left:4px solid var(--gold);font-size:25px;line-height:1.35;max-width:30em;}}
  li:before{{content:"\\2192";position:absolute;left:18px;color:var(--gold);font-weight:800;}}
  .foot{{margin-top:auto;color:var(--muted);font-size:15px;letter-spacing:.04em;}}
</style></head><body><div class="wrap">
  <div class="kicker">{kicker}</div>
  <div class="qlabel">{idx_label}</div>
  <h1><span class="q">Q.</span> {question}</h1>
  <ul>{bullet_items}</ul>
  <div class="foot">Rival Arena &middot; Jury Q&amp;A / Defense &middot; Gauntlet AI</div>
</div></body></html>"""


def divider_html():
    return """<!DOCTYPE html><html><head><meta charset="utf-8">
<style>
  :root{--ink:#f4f1ea;--muted:#9a948a;--bg0:#0a0a0a;--gold:#c09e5a;--cyan:#00d4ff;}
  html,body{margin:0;padding:0;width:1280px;height:720px;background:var(--bg0);
        font-family:"Inter","Helvetica Neue",Arial,sans-serif;color:var(--ink);}
  body{background:radial-gradient(1100px 760px at 50% 40%, #1c1810 0%, var(--bg0) 62%);
        display:flex;align-items:center;justify-content:center;text-align:center;}
  .wrap{max-width:24em;}
  .kicker{color:var(--gold);font-weight:800;letter-spacing:.30em;text-transform:uppercase;
        font-size:20px;margin-bottom:28px;}
  h1{font-size:58px;font-weight:800;letter-spacing:-.015em;line-height:1.1;margin:0;}
  h1 em{color:var(--gold);font-style:normal;}
  p{color:var(--muted);font-size:22px;margin-top:30px;}
</style></head><body><div class="wrap">
  <div class="kicker">Part 2</div>
  <h1>Defending the work &mdash; <em>anticipated questions</em></h1>
  <p>The questions we expect from the jury &mdash; and how we answer them.</p>
</div></body></html>"""


def render_frames():
    from playwright.sync_api import sync_playwright

    deck_url = "file://" + str(DECK_HTML)
    slide_paths = [FRAMES / f"slide_{i:02d}.png" for i in range(N_BEATS)]
    qa_paths = [FRAMES / f"qa_{i:02d}.png" for i in range(N_QAS)]
    div_path = FRAMES / "divider.png"

    need_slides = [p for p in slide_paths if not p.exists()]
    need_qa = not all(p.exists() for p in qa_paths) or not div_path.exists()

    if not need_slides and not need_qa:
        print("[frames] all frames already rendered, skipping playwright")
        return slide_paths, div_path, qa_paths

    tmp_html = FRAMES / "_qa_tmp.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox"])
        page = browser.new_page(
            viewport={"width": 1280, "height": 720}, device_scale_factor=2
        )

        # --- deck slides ---
        if need_slides:
            page.goto(deck_url, wait_until="networkidle")
            # let reveal.js + remote CSS/fonts settle
            page.wait_for_timeout(2500)
            count = page.evaluate("Reveal.getTotalSlides()")
            print(f"[frames] reveal.js reports {count} slides (expected {N_BEATS})")
            for i in range(N_BEATS):
                # fragment 999 -> show all fragments on slide i
                page.evaluate(f"Reveal.slide({i},0,999)")
                page.wait_for_timeout(1200)
                page.screenshot(path=str(slide_paths[i]))
                print(f"[frames] slide {i:02d} -> {slide_paths[i].name}")

        # --- divider + Q&A frames (use the same page) ---
        if need_qa:
            tmp_html.write_text(divider_html())
            page.goto("file://" + str(tmp_html), wait_until="load")
            page.wait_for_timeout(500)
            page.screenshot(path=str(div_path))
            print(f"[frames] divider -> {div_path.name}")

            for i, (q, bullets, _spoken) in enumerate(QAS):
                kicker = "Jury Q&amp;A / Defense"
                idx_label = f"Anticipated question {i+1} of {N_QAS}"
                tmp_html.write_text(qa_html(q, bullets, kicker, idx_label))
                page.goto("file://" + str(tmp_html), wait_until="load")
                page.wait_for_timeout(450)
                page.screenshot(path=str(qa_paths[i]))
                print(f"[frames] qa {i:02d} -> {qa_paths[i].name}")

        browser.close()

    if tmp_html.exists():
        tmp_html.unlink()
    return slide_paths, div_path, qa_paths


# ----------------------------------------------------------------------------
# Step 3: TTS via OpenAI (skip if cached). Returns list of mp3 paths.
# ----------------------------------------------------------------------------
def tts_segment(text, out_path, key):
    """Synthesize one segment; retry once on failure. Returns True on success."""
    import requests

    if out_path.exists() and out_path.stat().st_size > 2000:
        return True

    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    payload = {"model": "tts-1-hd", "voice": "onyx", "input": text}

    for attempt in (1, 2):
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=120)
            ctype = r.headers.get("content-type", "")
            if r.status_code == 200 and "audio" in ctype:
                out_path.write_bytes(r.content)
                if out_path.stat().st_size > 2000:
                    return True
                print(f"  [tts] {out_path.name}: tiny file, retrying")
            else:
                # do not log body in full (could be large); log status/ctype only
                snippet = ""
                if "audio" not in ctype:
                    try:
                        snippet = r.text[:200]
                    except Exception:
                        snippet = "<unreadable>"
                print(
                    f"  [tts] {out_path.name}: HTTP {r.status_code} ctype={ctype} "
                    f"attempt {attempt} {snippet}"
                )
        except Exception as e:
            print(f"  [tts] {out_path.name}: exception {e!r} attempt {attempt}")
        time.sleep(2)
    return False


def build_audio(key):
    """Generate all TTS segments. Returns (audio_paths, failed_indices, total_chars)."""
    # Build the ordered list of (segment_name, text)
    segs = []
    for i, txt in enumerate(BEATS):
        segs.append((f"seg_{i:02d}_beat{i+1:02d}", txt))
    segs.append((f"seg_{N_BEATS:02d}_divider", DIVIDER_SPOKEN))
    for i, (_q, _b, spoken) in enumerate(QAS):
        segs.append((f"seg_{N_BEATS+1+i:02d}_qa{i+1:02d}", spoken))

    audio_paths = []
    failed = []
    total_chars = 0
    for name, txt in segs:
        total_chars += len(txt)
        out_path = AUDIO / f"{name}.mp3"
        ok = tts_segment(txt, out_path, key)
        if ok:
            print(f"[tts] {name}: ok ({out_path.stat().st_size} bytes)")
        else:
            print(f"[tts] {name}: FAILED")
            failed.append(name)
        audio_paths.append(out_path)
    return audio_paths, failed, total_chars


# ----------------------------------------------------------------------------
# Step 4: assemble with ffmpeg
# ----------------------------------------------------------------------------
def ordered_frames(slide_paths, div_path, qa_paths):
    frames = list(slide_paths)        # beats 1..16
    frames.append(div_path)           # divider
    frames.extend(qa_paths)           # Q&As
    return frames


def make_clip(frame_png, audio_mp3, out_mp4):
    """One still-image + audio -> mp4 clip with a short pause appended."""
    # apad adds silence; -shortest then trims to (audio + 0.6s pad).
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(frame_png),
        "-i", str(audio_mp3),
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-r", "30",
        "-c:a", "aac", "-b:a", "192k",
        "-af", "apad=pad_dur=0.6",
        "-shortest",
        "-vf", "scale=2560:1440",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def assemble(frames, audio_paths, failed):
    clip_paths = []
    for idx, (frame, audio) in enumerate(zip(frames, audio_paths)):
        out_mp4 = CLIPS / f"clip_{idx:02d}.mp4"
        if audio.name.replace(".mp3", "") in [f for f in failed] or not (
            audio.exists() and audio.stat().st_size > 2000
        ):
            print(f"[assemble] skipping clip {idx:02d}: audio missing/failed ({audio.name})")
            continue
        make_clip(frame, audio, out_mp4)
        clip_paths.append(out_mp4)
        print(f"[assemble] clip {idx:02d} <- {frame.name} + {audio.name}")

    # concat via demuxer
    concat_list = CLIPS / "concat.txt"
    concat_list.write_text("".join(f"file '{c}'\n" for c in clip_paths))
    cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(OUT),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return clip_paths


# ----------------------------------------------------------------------------
# Verify
# ----------------------------------------------------------------------------
def ffprobe_json(path):
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def main():
    print(f"== Rival Arena explainer build ==")
    print(f"segments: {N_BEATS} beats + 1 divider + {N_QAS} Q&As = {TOTAL_SEGMENTS}")

    key = read_openai_key()

    slide_paths, div_path, qa_paths = render_frames()
    frames = ordered_frames(slide_paths, div_path, qa_paths)

    audio_paths, failed, total_chars = build_audio(key)

    clip_paths = assemble(frames, audio_paths, failed)

    info = ffprobe_json(OUT)
    vstreams = [s for s in info["streams"] if s["codec_type"] == "video"]
    astreams = [s for s in info["streams"] if s["codec_type"] == "audio"]
    dur = float(info["format"]["duration"])
    v = vstreams[0] if vstreams else {}
    res = f'{v.get("width")}x{v.get("height")}' if vstreams else "n/a"

    # ~$15 / 1M chars for tts-1-hd
    est_spend = total_chars / 1_000_000 * 15.0

    print("\n================ RESULT ================")
    print(f"output:        {OUT}")
    print(f"duration:      {dur:.1f}s ({dur/60:.1f} min)")
    print(f"resolution:    {res}")
    print(f"video streams: {len(vstreams)}  audio streams: {len(astreams)}")
    print(f"clips:         {len(clip_paths)} / {TOTAL_SEGMENTS} segments")
    print(f"TTS chars:     {total_chars}")
    print(f"TTS est spend: ${est_spend:.2f} (tts-1-hd @ $15/1M chars)")
    if failed:
        print(f"FAILED audio segments: {failed}")
    else:
        print("all audio segments present")
    print("========================================")


if __name__ == "__main__":
    main()
