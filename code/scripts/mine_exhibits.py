#!/usr/bin/env python3
"""Mine recorded transcripts (matches.jsonl) for vivid, illustrative exemplars.

These are the verbatim "telling examples" for the paper/deck — each with full
provenance (experiment / cell / seed / round / seat) so it is checkable. We read the
saved transcripts (the execution captured losslessly), not a live process.

Writes docs/exhibits.md. Run: .venv/bin/python scripts/mine_exhibits.py
"""
from __future__ import annotations
import glob, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "data" / "runs"
OUT = ROOT / "docs" / "exhibits.md"


def latest_jsonl(exp: str):
    ds = sorted(glob.glob(str(RUNS / exp / "2026*")), key=lambda p: Path(p).stat().st_mtime)
    for d in reversed(ds):
        f = Path(d) / "matches.jsonl"
        if f.exists():
            return f
    return None


def iter_matches(exp: str):
    f = latest_jsonl(exp)
    if not f:
        return
    for line in open(f):
        try:
            yield json.loads(line)
        except Exception:
            continue


def clip(s, n=320):
    s = (s or "").strip().replace("\n", " ")
    return s if len(s) <= n else s[:n] + "…"


def prov(m, rnd, seat):
    sp = m["spec"]
    return f"`{sp['cell_id']}` seed={sp['seed']} round={rnd['round_index']} seat={seat}"


def act(mv):
    a = mv.get("action") or {}
    return a.get("label") if isinstance(a, dict) else a


exhibits = []  # (title, body_lines)


def add(title, lines):
    exhibits.append((title, lines))


# 1) L1 deceptive signaling — the promise cliff / exploitation trigger
def mine_deception():
    found = []
    for exp in ("C1", "A1", "A3"):
        for m in iter_matches(exp):
            for rnd in m["rounds"]:
                for seat, mv in rnd["moves"].items():
                    msg = (mv.get("message") or "").lower()
                    sc = (mv.get("scratchpad") or "").lower()
                    if ("cooperate" in msg and "defect" not in msg and act(mv) == "DEFECT"
                            and any(k in sc for k in ("exploit", "defect", "higher payoff", "5 vs", "advantage"))):
                        found.append((m, rnd, seat, mv))
            if len(found) >= 3:
                break
        if len(found) >= 3:
            break
    lines = []
    for m, rnd, seat, mv in found[:2]:
        lines += [f"- **{prov(m, rnd, seat)}** — signalled *“{clip(mv.get('message'),120)}”* then played **{act(mv)}**.",
                  f"  - scratchpad: *“{clip(mv.get('scratchpad'),420)}”*"]
    if lines:
        add("Exhibit 1 — Cheap-talk as an exploitation trigger (the L1 collapse / promise cliff)", lines)


# 2) B1/B5 collusion money-shot — explicit price coordination
def mine_collusion():
    pat = re.compile(r"\b(rais|increase|higher|keep .*high|hold|match|undercut|together|both .*price|stable|maintain)", re.I)
    found = []
    for exp in ("B1", "B5", "B5E"):
        for m in iter_matches(exp):
            if m["spec"].get("channel") not in ("L2_observed", "L3_private"):
                continue
            for rnd in m["rounds"]:
                for seat, mv in rnd["moves"].items():
                    msg = mv.get("message") or ""
                    if "price" in msg.lower() and pat.search(msg) and len(msg) > 40:
                        found.append((m, rnd, seat, mv))
            if len(found) >= 4:
                break
        if len(found) >= 4:
            break
    lines = []
    for m, rnd, seat, mv in found[:3]:
        lines.append(f"- **{prov(m, rnd, seat)}**: *“{clip(mv.get('message'),300)}”*")
    if lines:
        add("Exhibit 2 — Autonomous price collusion (the money-shot): rival sellers coordinating high prices", lines)


# 3) D1 canary leakage — B repeating the planted codeword (show the field that contains it)
def _canary_hit(mv):
    """Return (field_name, snippet_around_match) for the first field of B that
    contains the canary, else None."""
    rx = re.compile(r"(.{0,60}(?:zarn[- ]?7|zarnberg).{0,80})", re.I)
    for field in ("message", "raw_message", "scratchpad"):
        txt = mv.get(field) or ""
        mt = rx.search(txt)
        if mt:
            return field, mt.group(1).strip()
    return None


def mine_canary():
    for exp in ("D1", "D1B"):
        found = []
        for m in iter_matches(exp):
            planted = set((m["spec"].get("canary") or {}).keys()) or {"A"}
            for rnd in m["rounds"]:
                for seat, mv in rnd["moves"].items():
                    if seat in planted:
                        continue
                    hit = _canary_hit(mv)
                    if hit:
                        found.append((m, rnd, seat, mv, hit))
            if len(found) >= 2:
                break
        lines = []
        for m, rnd, seat, mv, (field, snip) in found[:2]:
            lines.append(f"- **{prov(m, rnd, seat)}** — B (never given the canary) surfaced it in its **{field}**: "
                         f"*“…{clip(snip,200)}…”*")
        if lines:
            tag = "instructed" if exp == "D1" else "non-instructed/gossip"
            add(f"Exhibit 3 — Idea leakage ({tag}): the planted 'ZARN-7' codeword surfacing in the uninformed agent", lines)


# 4) B5 colluding under a watching monitor
def mine_under_monitor():
    found = []
    for m in iter_matches("B5"):
        if "strong" not in m["spec"]["cell_id"]:
            continue
        for rnd in m["rounds"]:
            if rnd.get("monitor_flag"):
                for seat, mv in rnd["moves"].items():
                    if (mv.get("message") or "").strip():
                        found.append((m, rnd, seat, mv))
                        break
        if len(found) >= 2:
            break
    lines = [f"- **{prov(m, rnd, seat)}** (monitor FLAGGED this round, yet): *“{clip(mv.get('message'),240)}”*"
             for m, rnd, seat, mv in found[:2]]
    if lines:
        add("Exhibit 4 — Colluding under a watching monitor (oversight theater): flagged but undeterred", lines)


# 5) B5E enforcement reaction — confiscated payoff then a response
def mine_enforcement():
    found = []
    for m in iter_matches("B5E"):
        if "/on/" not in m["spec"]["cell_id"]:
            continue
        for rnd in m["rounds"]:
            ex = rnd.get("extra") or {}
            if ex.get("enforced"):
                for seat, mv in rnd["moves"].items():
                    found.append((m, rnd, seat, mv))
                    break
        if len(found) >= 2:
            break
    lines = [f"- **{prov(m, rnd, seat)}** — payoff CONFISCATED after a flag; scratchpad: *“{clip(mv.get('scratchpad'),320)}”*"
             for m, rnd, seat, mv in found[:2]]
    if lines:
        add("Exhibit 5 — Enforcement bites: an agent reacting to a confiscated (penalised) round", lines)


# 6) G1 patriotic framing — cooperating despite "foreign rival" framing
def mine_patriotic():
    found = []
    for m in iter_matches("G1"):
        if "patriotic" not in m["spec"]["cell_id"] or "ipd" not in m["spec"]["cell_id"]:
            continue
        for rnd in m["rounds"]:
            for seat, mv in rnd["moves"].items():
                if act(mv) == "COOPERATE" and (mv.get("message") or "").strip():
                    found.append((m, rnd, seat, mv))
                    break
            if found:
                break
        if len(found) >= 2:
            break
    lines = [f"- **{prov(m, rnd, seat)}** (told the other is a foreign rival, still cooperates): *“{clip(mv.get('message'),240)}”*"
             for m, rnd, seat, mv in found[:2]]
    if lines:
        add("Exhibit 6 — Cooperation survives nationalist framing (structural, not pure obedience)", lines)


def main():
    mine_deception(); mine_collusion(); mine_canary()
    mine_under_monitor(); mine_enforcement(); mine_patriotic()
    out = ["# Exhibits — verbatim transcript examples for the report/deck",
           "",
           "Mined from saved `matches.jsonl` transcripts (the execution captured losslessly).",
           "Each carries provenance `cell_id seed round seat` so it is checkable against the raw run.",
           "Lightly clipped for length (… = truncated); never reworded.", ""]
    for title, lines in exhibits:
        out += [f"## {title}", ""] + lines + [""]
    if len(exhibits) == 0:
        out += ["_(no exemplars matched — check run availability)_"]
    OUT.write_text("\n".join(out))
    print(f"wrote {OUT} with {len(exhibits)} exhibit sections")
    for t, _ in exhibits:
        print("  -", t)


if __name__ == "__main__":
    main()
