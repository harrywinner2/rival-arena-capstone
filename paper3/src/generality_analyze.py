#!/usr/bin/env python3
"""Pool the model-generality runs and report whether the predicate effect replicates.

Three families, matched seeds, matched prompts. The question is not "is the effect
significant somewhere" but "does it hold across models", so this reports a per-model
table, a random-effects pooled estimate, and the heterogeneity -- pooling three
disparate estimates under a fixed-effects model would understate the uncertainty and
overstate the generality claim.

IPD is reported separately and mostly as a capability result: two of the three models
never reach cooperation lock-in under ANY arm, so their flat contrasts are floors, not
refutations, and they are excluded from pooling rather than counted as zeros.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / 'results' / 'generality'
ORDER = ['qwen25-14b', 'llama31-8b', 'olmo2-13b']
NICE = {'qwen25-14b': 'Qwen2.5-14B', 'llama31-8b': 'Llama-3.1-8B',
        'olmo2-13b': 'OLMo-2-13B'}


def boot(v, nb=6000, seed=0):
    if len(v) < 3:
        return float('nan'), float('nan')
    rng = random.Random(seed); n = len(v)
    b = sorted(sum(rng.choices(v, k=n)) / n for _ in range(nb))
    return b[int(.025 * nb)], b[int(.975 * nb)]


def load(tag):
    p = RES / f'{tag}.jsonl'
    return [json.loads(l) for l in p.open()] if p.exists() else []


def arms(rows, kind, field):
    d = {}
    for r in rows:
        if r['kind'] == kind:
            d.setdefault(r['arm'], []).append(r[field])
    return d


def contrast(d, a, b):
    x, y = d.get(a, []), d.get(b, [])
    if len(x) < 3 or len(y) < 3:
        return None
    diff = [p - q for p, q in zip(x, y)]
    lo, hi = boot(diff)
    return sum(diff) / len(diff), lo, hi


def dersimonian_laird(est, se):
    """Random-effects pool. Fixed effects would treat between-model variation as noise,
    which is precisely the thing being measured here."""
    w = [1 / (s * s) for s in se]
    fe = sum(wi * e for wi, e in zip(w, est)) / sum(w)
    Q = sum(wi * (e - fe) ** 2 for wi, e in zip(w, est))
    df = len(est) - 1
    C = sum(w) - sum(wi * wi for wi in w) / sum(w)
    tau2 = max(0.0, (Q - df) / C) if C > 0 else 0.0
    wr = [1 / (s * s + tau2) for s in se]
    re = sum(wi * e for wi, e in zip(wr, est)) / sum(wr)
    se_re = math.sqrt(1 / sum(wr))
    I2 = max(0.0, (Q - df) / Q) * 100 if Q > 0 else 0.0
    return re, se_re, Q, df, I2, tau2


def main():
    print('=' * 78)
    print('MODEL GENERALITY — the predicate contrast across three families')
    print('matched seeds (11000+), prompts execed from the L6 notebook, 20 seeds/arm')
    print('=' * 78)

    summary = {}
    for kind, field, label in (('bertrand', 'value', 'collusion index K'),
                               ('ipd', 'lockin', 'cooperation lock-in')):
        print(f'\n### {kind.upper()} — {label}\n')
        print(f"{'model':16s} {'none':>8s} {'proposal':>10s} {'intention':>10s}"
              f"  {'prop-none':>22s}  {'prop-intent':>22s}")
        rowsout = []
        for tag in ORDER:
            rows = load(tag)
            if not rows: continue
            d = arms(rows, kind, field)
            if not d: continue
            floor = (kind == 'ipd' and
                     not any(r['lockin'] == 1.0 for r in rows if r['kind'] == 'ipd'))
            m = lambda a: sum(d[a]) / len(d[a])
            cn, ci = contrast(d, 'text_proposal', 'none'), contrast(d, 'text_proposal',
                                                                    'text_intention')
            f1 = f'{cn[0]:+.3f} [{cn[1]:+.3f},{cn[2]:+.3f}]' if cn else '-'
            f2 = f'{ci[0]:+.3f} [{ci[1]:+.3f},{ci[2]:+.3f}]' if ci else '-'
            flag = '  <- FLOOR' if floor else ''
            print(f'{NICE[tag]:16s} {m("none"):8.3f} {m("text_proposal"):10.3f} '
                  f'{m("text_intention"):10.3f}  {f1:>22s}  {f2:>22s}{flag}')
            if not floor and cn and ci:
                rowsout.append((tag, cn, ci))
        summary[kind] = rowsout

        if kind == 'ipd':
            n_floor = sum(1 for tag in ORDER
                          if load(tag) and not any(r['lockin'] == 1.0
                                                   for r in load(tag) if r['kind'] == 'ipd'))
            print(f'\n  {n_floor}/{len(ORDER)} models never reach lock-in under ANY arm. '
                  f'Their contrasts are\n  capability floors, not refutations, and are '
                  f'excluded from pooling rather than\n  counted as zeros -- averaging a '
                  f'floor into a generality claim would be a\n  straightforward way to '
                  f'manufacture a null.')

        if len(rowsout) >= 2:
            for nm, idx in (('proposal - none', 1), ('proposal - intention', 2)):
                est = [r[idx][0] for r in rowsout]
                se = [max((r[idx][2] - r[idx][1]) / 3.92, 1e-6) for r in rowsout]
                re, se_re, Q, df, I2, tau2 = dersimonian_laird(est, se)
                lo, hi = re - 1.96 * se_re, re + 1.96 * se_re
                same = all(e < 0 for e in est) or all(e > 0 for e in est)
                print(f'\n  POOLED {nm:22s} {re:+.3f} [{lo:+.3f}, {hi:+.3f}]  '
                      f'(random effects, k={len(est)})')
                print(f'         heterogeneity Q={Q:.2f} df={df} I2={I2:.0f}% '
                      f'tau2={tau2:.5f}; all same sign: {same}')
        elif rowsout:
            print(f'\n  Only {len(rowsout)} model has an interpretable contrast here; '
                  f'no pooling.')

    print('\n' + '=' * 78)
    b = summary.get('bertrand', [])
    if len(b) >= 2:
        signs = [r[1][0] < 0 for r in b]
        sig = [not (r[1][1] <= 0 <= r[1][2]) for r in b]
        print(f'Bertrand: {sum(sig)}/{len(b)} families significant, '
              f'{"all" if all(signs) else "not all"} in the same direction.')
    print('IPD: measurable only where the model can sustain cooperation at all.')
    print('=' * 78)


if __name__ == '__main__':
    main()
