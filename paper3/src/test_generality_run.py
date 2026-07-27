#!/usr/bin/env python3
"""Drive generality_run.py against a mock OpenAI-compatible server, with no GPU.

Every prior stage of this project lost a run to a bug that executing the code once would
have caught. The endpoint layer here is new code -- logprob parsing, option
renormalisation, seeded sampling, the ledger -- and it will next be pointed at a GPU that
costs money per hour, so it gets exercised first.

The mock reads the prompt the driver actually built: it locates the option letters, the
payoff table and any delivered message, and answers accordingly. So this checks that the
prompts are well-formed, not merely that the HTTP round-trip works.
"""

from __future__ import annotations

import json
import math
import random
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = 8731
KEY = "test-key"

PROPOSED = re.compile(r'[Ll]et us both choose (\w+)\.')
INTENT = re.compile(r'I will choose (\w+)\.')
ORDER = re.compile(r'Choose one of ([^.]+)\.')
DIAG = re.compile(r'you (\w+), they (\w+)\s+->\s+you (-?\d+), they (-?\d+)')
PRICEMAP = re.compile(r'Prices: (.+)')


def bert_profit(mine, theirs, cost=8, a=30):
    q = max(0, a - mine)
    if mine < theirs: return (mine - cost) * q
    if mine == theirs: return (mine - cost) * q / 2
    return 0.0


def _diag_from_prompt(user):
    diag = {a: float(v) for a, b, v, _ in DIAG.findall(user) if a == b}
    pm = PRICEMAP.search(user)
    if pm:
        price = {}
        for part in pm.group(1).split(','):
            lab, p = part.split('='); price[lab.strip()] = int(p)
        diag = {L: bert_profit(price[L], price[L]) for L in price}
    return diag


def _best_option(user, opts):
    d = _diag_from_prompt(user)
    return max(opts, key=lambda o: d.get(o, 0.0)) if d else opts[0]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        self._json({"data": [{"id": "mock"}]})

    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        req = json.loads(self.rfile.read(n))
        if self.headers.get('Authorization') != f'Bearer {KEY}':
            self.send_response(401); self.end_headers(); return
        user = req['messages'][-1]['content']
        SEEN.append(user)
        if req.get('max_tokens', 1) > 1:                       # message generation
            m = ORDER.search(user) or re.search(r'options are ([^.\n]+)', user)
            opts = [s.strip() for s in m.group(1).split(',')] if m else ['A']
            # Propose the mutually-best option, not whichever happens to be listed
            # first: a mock that names an arbitrary option gives the proposal arm
            # nothing to move, and the resulting null says nothing about the driver.
            best = _best_option(user, opts)
            txt = (f'Let us both choose {best}.' if 'proposing what BOTH' in user
                   else f'I will choose {best}.')
            return self._json({"choices": [{"message": {"content": txt}}]})

        # action: score options off the rendered payoff table, and follow a proposal
        diag = _diag_from_prompt(user)
        opts = [s.strip() for s in ORDER.search(user).group(1).split(',')]
        top = max(diag.values()) or 1.0
        prop = PROPOSED.search(user)
        logits = {}
        for o in opts:
            x = 2.5 * (diag.get(o, 0.0) / top)
            if prop and o == prop.group(1):
                x += 2.0
            logits[o] = x
        mx = max(logits.values())
        ex = {o: math.exp(v - mx) for o, v in logits.items()}
        s = sum(ex.values())
        lp = {o: math.log(max(ex[o] / s, 1e-9)) for o in opts}
        best = max(lp, key=lp.get)
        self._json({"choices": [{
            "message": {"content": best},
            "logprobs": {"content": [{"token": best, "top_logprobs":
                [{"token": o, "logprob": lp[o]} for o in opts]}]}}]})

    def _json(self, obj):
        b = json.dumps(obj).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)


SEEN: list = []


def main() -> int:
    srv = HTTPServer(('127.0.0.1', PORT), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(0.3)

    out = Path('/tmp/_generality_selftest')
    if out.exists():
        for f in out.glob('*.jsonl'):
            f.unlink()
    r = subprocess.run(
        [sys.executable, str(ROOT / 'src' / 'generality_run.py'),
         '--base', f'http://127.0.0.1:{PORT}', '--key', KEY, '--model', 'mock',
         '--tag', 'mock', '--seeds', '6', '--rounds', '4', '--out', str(out)],
        capture_output=True, text=True)
    print(r.stdout[-2600:])
    if r.returncode != 0:
        print('STDERR:', r.stderr[-2000:])
        return 1

    rows = [json.loads(l) for l in (out / 'mock.jsonl').open()]
    checks = []
    checks.append(('all units ran', len(rows) == 6 * 3 * 2))
    checks.append(('no refusals', sum(x.get('refusals', 0) for x in rows) == 0))
    checks.append(('bertrand K finite',
                   all(isinstance(x['value'], float) for x in rows if x['kind'] == 'bertrand')))
    checks.append(('ipd lockin is 0/1',
                   all(x['lockin'] in (0.0, 1.0) for x in rows if x['kind'] == 'ipd')))
    # the mock follows proposals, so the proposal arm must beat `none` in IPD
    g = lambda k, a: [x['lockin'] if k == 'ipd' else x['value']
                      for x in rows if x['kind'] == k and x['arm'] == a]
    checks.append(('proposal moves IPD vs none',
                   sum(g('ipd', 'text_proposal')) > sum(g('ipd', 'none'))))
    checks.append(('prompts carried the payoff table',
                   any('Payoffs this round' in p for p in SEEN)))
    checks.append(('prompts carried the Bertrand matrix',
                   any('YOUR profit' in p for p in SEEN)))
    checks.append(('a delivered message reached the receiver',
                   any('The other agent sent you' in p for p in SEEN)))

    # resumability: a second invocation must add nothing
    before = len(rows)
    subprocess.run(
        [sys.executable, str(ROOT / 'src' / 'generality_run.py'),
         '--base', f'http://127.0.0.1:{PORT}', '--key', KEY, '--model', 'mock',
         '--tag', 'mock', '--seeds', '6', '--rounds', '4', '--out', str(out)],
        capture_output=True, text=True)
    after = len(list((out / 'mock.jsonl').open()))
    checks.append(('resume skips completed units', after == before))

    print()
    ok = True
    for name, good in checks:
        print(f"  [{'pass' if good else 'FAIL'}] {name}")
        ok &= good
    print(f"\nDRIVER OK: {ok}")
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
