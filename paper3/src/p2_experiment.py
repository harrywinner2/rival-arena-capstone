#!/usr/bin/env python3
"""P2 — does the request-modality effect replicate outside the research-lab world?

Pre-registered: paper3/prereg/p2_request_modality.md

Three unrelated attestation domains (code review / compliance / procurement) x
request_mode {direct, ambient} x observability {observed, unobserved}. Reuses only the
LLM client and model registry from the frozen apparatus; the scenario world is
self-contained in paper3/src/scenarios.py so the published S2 stays untouched.

Usage:
    python3 paper3/src/p2_experiment.py --mock --seeds 2          # offline check
    python3 paper3/src/p2_experiment.py --seeds 48 --pair cross_origin
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))
sys.path.insert(0, str(Path(__file__).parent))

from rival_arena.harness.llm import LLMClient, MockLLM  # noqa: E402
from rival_arena.registry import get_model, get_pair  # noqa: E402

import scenarios as S  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "results"
MAX_TURNS = 3

TOOL_RE = re.compile(r"^\s*TOOL:\s*(\w+)\s*(\{.*\})?\s*$", re.M)


def parse_calls(raw: str) -> list[tuple[str, dict]]:
    calls = []
    for m in TOOL_RE.finditer(raw or ""):
        name = m.group(1)
        args = {}
        if m.group(2):
            try:
                args = json.loads(m.group(2))
            except Exception:  # noqa: BLE001
                # tolerate loose quoting rather than dropping the call
                blob = m.group(2)
                for k in ("verdict", "note"):
                    mm = re.search(rf'"{k}"\s*:\s*"([^"]*)"', blob)
                    if mm:
                        args[k] = mm.group(1)
        calls.append((name, args))
    return calls


async def run_one(client, model, scen_key: str, request_mode: str, observed: bool,
                  seed: int) -> dict:
    lab = S.MiniLab(scenario=S.SCENARIOS[scen_key], request_mode=request_mode,
                    observed=observed, seed=seed)
    tool_output = None
    transcript = []
    refusal = "clean"
    for turn in range(MAX_TURNS):
        mandatory = (turn == MAX_TURNS - 1)
        sysmsg = S.system_prompt(lab)
        usr = S.user_prompt(lab, turn, tool_output, mandatory)
        try:
            r = await client.complete(model, sysmsg, usr, temperature=0.7,
                                      max_tokens=400, seed=seed)
            raw = r.text
        except Exception as e:  # noqa: BLE001
            raw = ""
            refusal = "api_error"
            transcript.append(dict(turn=turn, raw=f"api_error: {e}"))
            break
        transcript.append(dict(turn=turn, system=sysmsg, user=usr, raw=raw))
        tool_output = None
        for name, args in parse_calls(raw)[:3]:
            tool_output = S.dispatch(lab, name, args)
        if lab.report is not None:
            break

    # forced verdict: if A never filed, file on its behalf using its own last prose,
    # so the deterministic scorer classifies what A actually said (matches S2).
    if lab.report is None and refusal != "api_error":
        last = (transcript[-1]["raw"] if transcript else "") or ""
        prose = re.sub(r"<scratchpad>.*?</scratchpad>", " ", last, flags=re.S).strip()
        S.dispatch(lab, lab.scenario.report_tool,
                   {"verdict": "", "note": prose[:600]})
        lab.log("system", "force_report", {"category": lab.report["category"]})

    return dict(
        scenario=scen_key, request_mode=request_mode,
        observed=int(observed), seed=seed, model=model.id if hasattr(model, "id") else str(model),
        read_truth=int(lab.read_truth_called),
        verdict=(lab.report or {}).get("verdict", ""),
        category=(lab.report or {}).get("category", "omission"),
        note=(lab.report or {}).get("note", "")[:400],
        refusal=refusal,
        transcript=transcript,
    )


async def main_async(args) -> None:
    S.assert_contained()
    # MockLLM subclasses LLMClient, so it drops straight in for offline runs.
    client = MockLLM() if args.mock else LLMClient()
    model = get_model("qwen-72b" if args.mock else get_pair(args.pair)[0])

    jobs = []
    for scen in args.scenarios:
        for mode in ("direct", "ambient"):
            for observed in ([False, True] if args.sweep_observability else [False]):
                for s in range(args.seed_offset, args.seed_offset + args.seeds):
                    jobs.append((scen, mode, observed, s))

    print(f"P2: {len(jobs)} runs — {len(args.scenarios)} scenarios x 2 request modes "
          f"x {2 if args.sweep_observability else 1} observability x {args.seeds} seeds")

    sem = asyncio.Semaphore(args.concurrency)
    out_path = OUT / "p2_runs.jsonl"
    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if out_path.exists() and not args.fresh:
        for line in out_path.open():
            try:
                r = json.loads(line)
                done.add((r["scenario"], r["request_mode"], r["observed"], r["seed"]))
            except Exception:  # noqa: BLE001
                pass
        print(f"resuming: {len(done)} runs already on disk")

    todo = [j for j in jobs if (j[0], j[1], int(j[2]), j[3]) not in done]

    async def one(job):
        async with sem:
            return await run_one(client, model, *job)

    t0 = time.time()
    with out_path.open("a") as fh:
        for i in range(0, len(todo), args.concurrency * 2):
            batch = todo[i:i + args.concurrency * 2]
            for r in await asyncio.gather(*[one(j) for j in batch]):
                fh.write(json.dumps(r) + "\n")
            fh.flush()
            print(f"  {min(i + len(batch), len(todo))}/{len(todo)} "
                  f"({time.time()-t0:.0f}s)")
    print(f"wrote {out_path}")
    print("analyse with: python3 paper3/src/p2_analyze.py")


def main() -> None:
    ap = argparse.ArgumentParser(description="P2 request-modality replication")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--seeds", type=int, default=48)
    ap.add_argument("--seed-offset", type=int, default=500)
    ap.add_argument("--pair", default="cross_origin")
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--fresh", action="store_true")
    ap.add_argument("--sweep-observability", action="store_true",
                    help="also cross observed/unobserved (secondary factor)")
    ap.add_argument("--scenarios", nargs="*", default=list(S.SCENARIOS))
    args = ap.parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
