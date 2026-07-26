#!/usr/bin/env python3
"""Execute the L6 notebook's scaffold cells against stub models, with no GPU.

The first Colab run of L6 failed its own self-test for two reasons that had nothing to
do with the model: the Bertrand test asked for max(PRICES) (a price that is dominated
both jointly and individually, so a correct model refuses it), and the order-bias
statistic assumed two options and flagged a four-option game where random choice already
scores 0.50. Both would have been caught by running the cell once.

The stub models here READ THE RENDERED PROMPT -- they parse the payoff block, the
delivered message and the presentation order out of the string `action_prompt` built.
So this exercises the actual plumbing, not a mock of it.

A check that cannot fail is not a check: `sensitive` must PASS and each broken stub must
fail on ITS OWN named check.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import types
from pathlib import Path

NB_SRC = Path(__file__).resolve().parent / "make_l6_notebook.py"

PAYOFF_BASE = {('C', 'C'): (3, 3), ('C', 'D'): (0, 5),
               ('D', 'C'): (5, 0), ('D', 'D'): (1, 1)}
PRICES = [8, 12, 19, 24]


class _Vec(list):
    def argmax(self):
        return int(max(range(len(self)), key=lambda i: self[i]))

    def max(self):
        return max(self)


def _softmax(xs):
    m = max(xs)
    e = [pow(2.718281828459045, x - m) for x in xs]
    s = sum(e)
    return _Vec([v / s for v in e])


# ---------------------------------------------------------------- prompt parsing
DIAG_IPD = re.compile(r"you (\w+), they (\w+)\s+->\s+you (-?\d+), they (-?\d+)")
ROW_BERT = re.compile(r"(\w+): price (\d+)\s+->\s+you earn (\d+)")
PROPOSED = re.compile(r"[Ll]et us both choose (\w+)\.")
ORDER = re.compile(r"Choose one of ([^.]+)\.")


def read_prompt(prompt, letters):
    """Recover what a real model would have to read off the rendered prompt."""
    diag = {}
    for a, b, mine, _ in DIAG_IPD.findall(prompt):
        if a == b:
            diag[a] = float(mine)
    price = {}
    for lab, p, earn in ROW_BERT.findall(prompt):
        diag[lab] = float(earn)
        price[lab] = int(p)
    m = PROPOSED.search(prompt)
    order = [s.strip() for s in ORDER.search(prompt).group(1).split(',')]
    return dict(diag={k: diag.get(k, 0.0) for k in letters},
                price=price, proposed=m.group(1) if m else None, order=order,
                adverse="No rounds have been played yet." not in prompt)


def make_code_probs(mode):
    """code_probs(prompt, code_ids) -> (probs over code_ids, logits).

    sensitive    : scores options by the payoff the prompt states, follows a proposal,
                   ignores presentation order. This is what a usable model looks like.
    msg_blind    : reads payoffs, ignores the message entirely.
    order_driven : picks whatever is shown first.
    payoff_blind : follows the message but cannot read the table.
    """
    def _fn(prompt, code_ids, embeds=False):
        letters = [chr(c) for c in code_ids]
        r = read_prompt(prompt, letters)
        top = max(r['diag'].values()) or 1.0
        logits = []
        for L in letters:
            if mode == 'order_driven':
                x = 3.0 if L == r['order'][0] else 0.0
            elif mode == 'payoff_blind':
                x = 0.0
            else:
                x = 3.0 * (r['diag'][L] / top)
                if r['adverse'] and r['diag'][L] == top:
                    x -= 0.8          # exploited last round -> less willing to hold
            if mode not in ('msg_blind', 'order_driven') and L == r['proposed']:
                x += 2.0
            logits.append(x)
        return _softmax(logits), logits
    return _fn


# ---------------------------------------------------------------- stub GPU surface
class _Tok:
    eos_token_id = 0

    def encode(self, s, add_special_tokens=True):
        return [ord(s[0])]

    def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True):
        return "\n".join(m["content"] for m in msgs)


def _torch():
    t = types.ModuleType("torch")

    def no_grad():
        def deco(fn):
            return fn
        return deco
    t.no_grad = no_grad
    t.bfloat16, t.float16 = "bf16", "fp16"
    t.cuda = types.SimpleNamespace(is_available=lambda: True,
                                   is_bf16_supported=lambda: True)
    return t


def notebook_cells():
    """Build the notebook in-process and return its code cells, so the test always
    reflects the generator rather than a stale committed .ipynb."""
    src = NB_SRC.read_text()
    g = {"__name__": "_l6gen", "__file__": str(NB_SRC)}
    exec(compile(src.split('if __name__')[0], str(NB_SRC), 'exec'), g)
    return [(kind, body) for kind, body in g["cells"] if kind == "code"]


def run(mode):
    torch = _torch()
    sys.modules["torch"] = torch
    g = {
        "__name__": "__main__", "torch": torch, "hashlib": hashlib, "json": json,
        "R_TOK": _Tok(), "S_TOK": _Tok(), "S_MODEL": object(), "R_MODEL": object(),
        "PAYOFF": dict(PAYOFF_BASE), "PRICES": list(PRICES),
        "COST": 8, "DEMAND_A": 30, "P_COMP": 8, "P_MONO": 19, "CONT_PROB": 0.97,
    }
    import collections
    g["collections"] = collections

    out, verdict = [], None
    for _, body in notebook_cells():
        title = next((l for l in body.splitlines() if "#@title" in l), "")
        if not re.match(r"#@title 5b? ", title):
            continue
        code = "\n".join(l for l in body.splitlines()
                         if not l.lstrip().startswith("#@"))
        if "5b" in title:
            g["code_probs"] = make_code_probs(mode)   # override the real one
            code = code.replace("raise SystemExit(", "raise RuntimeError(")
        buf = []
        _p = g.get("print")
        g["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
        try:
            exec(compile(code, title.strip(), "exec"), g)
            status = "ok"
        except RuntimeError as e:
            status = "selftest-failed"
        except Exception as e:
            status = f"*** {type(e).__name__}: {e}"
        finally:
            g["print"] = _p
        out += buf
        if "5b" in title:
            verdict = status
    return verdict, out


EXPECT = {
    'sensitive':    None,
    'msg_blind':    'MESSAGE-BLIND',
    'order_driven': 'presentation order dominates',
    'payoff_blind': 'near-random',
}


def main() -> int:
    ok = True
    for mode, want in EXPECT.items():
        verdict, lines = run(mode)
        body = "\n".join(lines)
        fault = verdict is not None and verdict.startswith("***")
        if mode == 'sensitive':
            good = verdict == "ok"
        else:
            good = verdict == "selftest-failed" and want in body
        ok &= good and not fault
        print(f"--- {mode} ---")
        for l in lines:
            print("   ", l)
        print(f"    => {verdict}  [{'PASS' if good else 'FAIL'}]"
              f"{'' if want is None else f'  expected: {want}'}\n")
    print(f"DISCRIMINATES: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
