"""Validate the regex conditional-punishment detector against an LLM judge.

A null result from a bad detector is worthless, so the detector needs measured
precision/recall before any negative claim rests on it. We draw a stratified sample
(balanced on the detector's own verdict so both error directions are estimable),
have an independent judge label each message against the same written definition,
and report agreement, precision, recall, F1 and Cohen's kappa.

The judge is a model from a family that is NOT among the arena players where possible,
to avoid a model grading its own output style.

Usage:
    python3 paper3/src/validate_detector.py --n 300 --judge <openrouter-model>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from conditional import score_message  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "results"

DEFINITION = """A message counts as a CONTINGENT PUNISHMENT RULE if it does BOTH of:
  (a) states or clearly implies a condition on what the OTHER agent does
      (e.g. "if you undercut", "unless you match", "as long as you hold", "otherwise"), AND
  (b) states a negative consequence the SENDER will impose or carry out in that case
      (e.g. "I'll undercut", "I'll defect", "I'll match your price", "I'll respond in kind",
       "we go back to a price war").

It does NOT count if the message only:
  - announces the sender's own intention ("I intend to cooperate", "I'll hold at 12.00"),
  - proposes a joint plan without any stated consequence ("let's both set 13.00"),
  - appeals to trust, history or mutual benefit ("our cooperation is working well"),
  - asks a question or seeks agreement ("do you agree?"),
  - merely describes what happened ("you undercut me last round").

A conditional promise of continued cooperation with NO negative consequence
("I'll cooperate again if you do") does NOT count -- there must be a punishment."""

PROMPT = """You are labelling messages exchanged between two AI agents playing a repeated economic game.

{definition}

Message:
\"\"\"{msg}\"\"\"

Answer with a JSON object only: {{"rule": true|false, "why": "<max 12 words>"}}"""


def load_pool() -> pd.DataFrame:
    df = pd.read_csv(ROOT / "results" / "master_long.csv", low_memory=False)
    df = df[df.message.notna() & df.channel.isin(["L2_observed", "L3_private"])]
    df = df[["message", "game", "channel"]].drop_duplicates(subset=["message"])
    sc = pd.DataFrame([score_message(m) for m in df.message])
    df = pd.concat([df.reset_index(drop=True), sc], axis=1)
    return df


def sample(df: pd.DataFrame, n: int, seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    half = n // 2
    parts = []
    for val, k in [(1, half), (0, n - half)]:
        sub = df[df.rule == val]
        take = min(k, len(sub))
        parts.append(sub.sample(take, random_state=int(rng.integers(1e9))))
    return pd.concat(parts).reset_index(drop=True)


def judge_one(client, model: str, msg: str, retries: int = 4):
    for a in range(retries):
        try:
            r = client.chat.completions.create(
                model=model,
                messages=[{"role": "user",
                           "content": PROMPT.format(definition=DEFINITION, msg=msg[:1500])}],
                temperature=0,
                max_tokens=80,
            )
            txt = r.choices[0].message.content or ""
            m = re.search(r"\{.*\}", txt, re.S)
            if m:
                return bool(json.loads(m.group(0)).get("rule"))
            if "true" in txt.lower():
                return True
            if "false" in txt.lower():
                return False
        except Exception as e:  # noqa: BLE001
            if a == retries - 1:
                print(f"  judge failed: {type(e).__name__}: {e}", file=sys.stderr)
                return None
            time.sleep(2 * (a + 1))
    return None


def kappa(a: np.ndarray, b: np.ndarray) -> float:
    po = (a == b).mean()
    pe = a.mean() * b.mean() + (1 - a.mean()) * (1 - b.mean())
    return (po - pe) / (1 - pe) if pe < 1 else np.nan


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
    ap.add_argument("--judge", default="anthropic/claude-3.7-sonnet")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--base-url", default=None,
                    help="OpenAI-compatible endpoint (e.g. a self-hosted vLLM). "
                         "When set, no OpenRouter key is needed.")
    ap.add_argument("--recall-arm", action="store_true",
                    help="additionally sample n//2 detector-NEGATIVES only, to bound "
                         "the miss rate on the population")
    args = ap.parse_args()

    env = {}
    envf = ROOT.parent / ".env"
    if envf.exists():
        for line in envf.read_text().splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    from openai import OpenAI
    if args.base_url:
        client = OpenAI(api_key="EMPTY", base_url=args.base_url)
    else:
        key = env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if not key:
            sys.exit("no OPENROUTER_API_KEY (or pass --base-url for a local endpoint)")
        client = OpenAI(api_key=key, base_url="https://openrouter.ai/api/v1")

    pool = load_pool()
    s = sample(pool, args.n)
    print(f"pool {len(pool)} unique messages; judging {len(s)} with {args.judge}")

    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        labels = list(ex.map(lambda m: judge_one(client, args.judge, m), s.message.tolist()))
    s["judge"] = labels

    ok = s[s.judge.notna()].copy()
    ok["judge"] = ok["judge"].astype(int)
    y_pred = ok["rule"].values.astype(int)
    y_true = ok["judge"].values

    tp = int(((y_pred == 1) & (y_true == 1)).sum())
    fp = int(((y_pred == 1) & (y_true == 0)).sum())
    fn = int(((y_pred == 0) & (y_true == 1)).sum())
    tn = int(((y_pred == 0) & (y_true == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else np.nan
    rec = tp / (tp + fn) if tp + fn else np.nan
    f1 = 2 * prec * rec / (prec + rec) if prec and rec else np.nan

    lines = [
        "# Detector validation against an independent LLM judge\n",
        f"Judge: `{args.judge}`; stratified sample balanced on the detector's verdict "
        f"(so both error directions are estimable).\n",
        f"Judged: {len(ok)}/{len(s)} (failures dropped).\n",
        "\n| | judge: rule | judge: not rule |",
        "|---|---:|---:|",
        f"| **detector: rule** | {tp} | {fp} |",
        f"| **detector: not rule** | {fn} | {tn} |",
        "",
        f"- raw agreement: **{(y_pred == y_true).mean():.3f}**",
        f"- precision: **{prec:.3f}**",
        f"- recall: **{rec:.3f}**",
        f"- F1: **{f1:.3f}**",
        f"- Cohen's kappa: **{kappa(y_pred, y_true):.3f}**",
        "",
        "NOTE: the sample is stratified 50/50 on the detector's verdict, so these are "
        "conditional on that stratification, not population rates. Population base rate "
        f"of detector-positive messages: {pool.rule.mean():.3f}.",
    ]
    dis = ok[ok["rule"] != ok["judge"]]
    if len(dis):
        lines.append("\n## Disagreement examples\n")
        for _, r in dis.head(12).iterrows():
            lines.append(f"- detector={r['rule']} judge={r['judge']}: "
                         f"\"{str(r['message'])[:180]}\"")

    OUT.mkdir(parents=True, exist_ok=True)
    ok.to_csv(OUT / "detector_validation_sample.csv", index=False)
    txt = "\n".join(lines)
    (OUT / "detector_validation.md").write_text(txt)
    print(txt)


if __name__ == "__main__":
    main()
