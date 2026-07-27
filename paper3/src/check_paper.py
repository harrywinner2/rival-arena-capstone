#!/usr/bin/env python3
"""Structural checks on the paper package, without a TeX toolchain.

There is no LaTeX here, so a compile cannot be the check. These are the failures a
compile would catch (undefined references, missing inputs, missing figures, unbalanced
environments) plus two it would not: leftover \\pending markers, and stale references to
tables that a rewrite deleted.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

PAPER = Path(__file__).resolve().parents[1] / 'paper'


def strip_comments(t: str) -> str:
    return re.sub(r'(?<!\\)%.*', '', t)


def main() -> int:
    main_tex = (PAPER / 'main.tex').read_text()
    inputs = re.findall(r'\\input\{([^}]+)\}', main_tex)

    files, missing_inputs = [PAPER / 'main.tex'], []
    for i in inputs:
        f = PAPER / (i + ('' if i.endswith('.tex') else '.tex'))
        (files if f.exists() else missing_inputs).append(f if f.exists() else i)

    body = "\n".join(strip_comments(f.read_text()) for f in files)

    labels = Counter(re.findall(r'\\label\{([^}]+)\}', body))
    refs = set(re.findall(r'\\(?:ref|autoref|eqref)\{([^}]+)\}', body))
    cites = set()
    for grp in re.findall(r'\\cite[a-z]*\{([^}]+)\}', body):
        cites.update(c.strip() for c in grp.split(','))
    bibkeys = set(re.findall(r'@\w+\{([^,]+),', (PAPER / 'refs.bib').read_text()))
    figs = set(re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', body))

    problems = []
    for i in missing_inputs:
        problems.append(f'missing \\input target: {i}')
    for r in sorted(refs - set(labels)):
        problems.append(f'undefined reference: \\ref{{{r}}}')
    for l, n in sorted(labels.items()):
        if n > 1:
            problems.append(f'duplicate label: {l} ({n}x)')
    for c in sorted(cites - bibkeys):
        problems.append(f'citation not in refs.bib: {c}')
    for g in sorted(figs):
        if not (PAPER / g).exists() and not (PAPER / (g + '.pdf')).exists():
            problems.append(f'missing figure file: {g}')
    for f in files:
        t = f.read_text()
        if '\\pending{' in t:
            for m in re.findall(r'\\pending\{([^}]*)\}', t):
                problems.append(f'unresolved \\pending in {f.name}: {m}')

    # environment balance, per file
    for f in files:
        t = strip_comments(f.read_text())
        opens = re.findall(r'\\begin\{([^}]+)\}', t)
        closes = re.findall(r'\\end\{([^}]+)\}', t)
        d = Counter(opens) - Counter(closes)
        e = Counter(closes) - Counter(opens)
        for k, v in d.items():
            problems.append(f'{f.name}: {v} unclosed \\begin{{{k}}}')
        for k, v in e.items():
            problems.append(f'{f.name}: {v} unmatched \\end{{{k}}}')

    # tabular column counts vs declared spec
    for f in files:
        t = strip_comments(f.read_text())
        for spec, inner in re.findall(r'\\begin\{tabular\}\{([^}]*)\}(.*?)\\end\{tabular\}',
                                      t, re.S):
            ncol = len(re.findall(r'[lcrp]', re.sub(r'p\{[^}]*\}', 'p', spec)))
            for line in inner.split('\\\\'):
                line = line.strip()
                if (not line or line.startswith('\\') or 'multicolumn' in line
                        or '&' not in line):
                    continue
                got = line.count('&') + 1
                if got != ncol:
                    problems.append(
                        f'{f.name}: tabular row has {got} cells, spec declares {ncol}: '
                        f'{line[:58]}')

    unused = sorted(set(labels) - refs)

    print(f'files       : {len(files)} ({len(inputs)} inputs)')
    print(f'labels/refs : {len(labels)} labels, {len(refs)} refs')
    print(f'citations   : {len(cites)} used, {len(bibkeys)} in refs.bib')
    print(f'figures     : {len(figs)} referenced')
    print(f'words (body): ~{len(re.findall(r"[A-Za-z][A-Za-z-]+", body)):,}')
    if unused:
        print(f'\nunused labels ({len(unused)}, not an error): {", ".join(unused[:12])}'
              + (' ...' if len(unused) > 12 else ''))
    print()
    if problems:
        print(f'PROBLEMS ({len(problems)}):')
        for p in problems:
            print(f'  - {p}')
        return 1
    print('OK — no structural problems found.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
