"""Does the SMS throughput probe support the expressiveness reading?

The throughput probe found that one pair (Qwen x DeepSeek) jumps from 0.45 to 0.80
lock-in on a SINGLE 60-character SMS, while another (Qwen x Llama) needs 8+ credits.
The original reading was "coordination is cheap for some pairs". Two competing
mechanisms:

  expressiveness  the single text carries a contingent rule, which is enough to select
                  an equilibrium the pair was already close to;
  presence        the text carries nothing strategically specific -- what matters is
                  that a message-exchange turn happened at all.

We score every delivered SMS with the same detector used on the main arena, and ask
what the messages at low credit budgets actually say.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from conditional import score_message  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "results"
FILES = {
    "qwen x llama": ROOT / "followup-throughput/results/sms_matches.jsonl",
    "qwen x deepseek": ROOT / "followup-throughput/results/sms_matches_qwen_deepseek.jsonl",
}


def main() -> None:
    rows, msgs = [], []
    for label, path in FILES.items():
        if not path.exists():
            continue
        for line in path.open():
            r = json.loads(line)
            sent = []
            for rd in r.get("rounds", []):
                for seat, txt in (rd.get("sms_delivered") or {}).items():
                    if txt:
                        sc = score_message(txt)
                        sent.append(sc)
                        msgs.append(dict(pair=label, credits=r["credits"], seed=r["seed"],
                                         t=rd["t"], seat=seat, text=txt, **sc))
            rows.append(dict(
                pair=label, credits=r["credits"], seed=r["seed"],
                lock_in=int(bool(r["lock_in"])), hold=r["mutual_hold_rate"],
                n_sms=len(sent),
                rule_any=int(any(s["rule"] for s in sent)),
                target_any=int(any(s["target"] for s in sent)),
                trigger_any=int(any(s["trigger"] for s in sent)),
                conseq_any=int(any(s["consequence"] for s in sent)),
            ))
    d = pd.DataFrame(rows)
    m = pd.DataFrame(msgs)
    if d.empty:
        sys.exit("no SMS data found")

    out = ["# SMS throughput probe — what do the messages actually say?\n",
           f"{len(d)} matches, {len(m)} delivered SMS (<=60 chars each).\n"]

    out.append("\n## Content of SMS by credit budget\n")
    out.append("| pair | credits | matches | lock-in | mean SMS sent | "
               "any rule | any trigger | any consequence |")
    out.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for (p, c), g in d.groupby(["pair", "credits"]):
        out.append(f"| {p} | {c} | {len(g)} | {g.lock_in.mean():.2f} | {g.n_sms.mean():.1f} | "
                   f"{g.rule_any.mean():.2f} | {g.trigger_any.mean():.2f} | "
                   f"{g.conseq_any.mean():.2f} |")

    out.append("\n\n## The decisive cell — 1 credit\n")
    out.append("At 1 credit each agent may send at most one 60-character SMS for the whole "
               "match. If a single contingent rule is what flips the pair, rules should be "
               "present here.\n")
    one = m[m.credits == 1]
    for p, g in one.groupby("pair"):
        out.append(f"\n**{p}** — {len(g)} SMS at 1 credit; "
                   f"rule {g.rule.mean():.2f}, trigger {g.trigger.mean():.2f}, "
                   f"consequence {g.consequence.mean():.2f}, target {g.target.mean():.2f}")
        out.append("\nAll distinct texts:\n")
        for txt, n in Counter(g.text).most_common(15):
            sc = score_message(txt)
            tag = "RULE" if sc["rule"] else ("target" if sc["target"] else "-")
            out.append(f"- ({n}x) [{tag}] `{txt}`")

    # does rule presence predict lock-in, holding credits fixed?
    out.append("\n\n## Does rule content predict lock-in, holding the budget fixed?\n")
    out.append("| pair | credits | lock-in (rule sent) | lock-in (no rule) | n rule / n no-rule |")
    out.append("|---|---:|---:|---:|---|")
    for (p, c), g in d[d.credits > 0].groupby(["pair", "credits"]):
        a, b = g[g.rule_any == 1], g[g.rule_any == 0]
        if len(a) < 2 or len(b) < 2:
            continue
        out.append(f"| {p} | {c} | {a.lock_in.mean():.2f} | {b.lock_in.mean():.2f} | "
                   f"{len(a)} / {len(b)} |")
    # pooled across credit levels within pair
    out.append("\nPooled over credit levels >0 (crude, budget not held fixed):\n")
    for p, g in d[d.credits > 0].groupby("pair"):
        a, b = g[g.rule_any == 1], g[g.rule_any == 0]
        if len(a) >= 3 and len(b) >= 3:
            out.append(f"- {p}: rule {a.lock_in.mean():.2f} (n={len(a)}) vs "
                       f"no-rule {b.lock_in.mean():.2f} (n={len(b)})")

    m.to_csv(OUT / "sms_messages_scored.csv", index=False)
    d.to_csv(OUT / "sms_matches_scored.csv", index=False)
    txt = "\n".join(out)
    (OUT / "sms_conditionality.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
