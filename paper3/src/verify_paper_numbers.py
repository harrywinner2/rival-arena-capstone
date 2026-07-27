#!/usr/bin/env python3
"""Check the paper's headline numbers against the raw result files.

A structural check (check_paper.py) catches what a compile would. This catches what a
compile would not: a number transcribed wrongly from a run into a table. Every value it
checks is re-derived from the ledgers rather than copied.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / 'results' / 'generality'
MODELS = (('qwen25-14b', 'Qwen2.5-14B'), ('llama31-8b', 'Llama-3.1-8B'),
          ('olmo2-13b', 'OLMo-2-13B'))


def main() -> int:
    tex = (ROOT / 'paper' / 'sections' / '10b_generality.tex').read_text()
    ok, checked = True, 0
    print(f"{'quantity':40s} {'ledger':>9s} {'paper':>9s}")
    for tag, nice in MODELS:
        f = GEN / f'{tag}.jsonl'
        if not f.exists():
            print(f'  (missing {f.name}, skipped)'); continue
        rows = [json.loads(l) for l in f.open()]
        by = {}
        for r in rows:
            if r['kind'] == 'bertrand':
                by.setdefault(r['arm'], []).append(r['value'])
        mean = lambda k: sum(by[k]) / len(by[k])
        pair = lambda a, b: sum(p - q for p, q in zip(by[a], by[b])) / len(by[a])
        row = [l for l in tex.splitlines() if l.startswith(nice) and '&' in l][0]
        cells = [c.strip() for c in row.split('&')]
        num = lambda c: float(re.search(r'\$(-?\d\.\d+)\$', c).group(1))
        for label, a, b in (
                (f'{nice} no-channel K', mean('none'), num(cells[1])),
                (f'{nice} proposal-none', pair('text_proposal', 'none'), num(cells[2])),
                (f'{nice} proposal-intention',
                 pair('text_proposal', 'text_intention'), num(cells[3]))):
            good = abs(a - b) < 0.0015
            ok &= good; checked += 1
            print(f'{label:40s} {a:9.3f} {b:9.3f}  {"ok" if good else "MISMATCH"}')
    print(f'\n{checked} quantities checked. VERIFIED: {ok}')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
