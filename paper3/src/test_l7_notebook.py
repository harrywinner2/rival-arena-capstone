#!/usr/bin/env python3
"""Run L7's probe cells on synthetic states with a KNOWN answer, on CPU.

The probe's job is to tell a recoverable representation from an unrecoverable one. So it
is tested against three layers whose answers are known in advance:

  layer 0  the embeddings themselves      -> must score ~1.0 (this is the notebook's own
                                             positive control; if it fails, the probe is
                                             broken, not the model)
  layer 2  embeddings under a rotation    -> a linear map EXISTS, so must score high
  layer 4  noise independent of the text  -> nothing to recover, so must score ~0

A probe that cannot fail on layer 4 would rubber-stamp any hidden state handed to it, and
its verdict on the real model would be worthless.
"""

from __future__ import annotations

import json
import random
import sys
import types
from pathlib import Path

import torch

NB = Path(__file__).resolve().parents[1] / "notebooks" / "L7_channel_probe.ipynb"

V, D, N_MSG, TOK_PER = 600, 64, 240, 12


def synth():
    g = torch.Generator().manual_seed(0)
    E = torch.randn(V, D, generator=g)
    E = torch.nn.functional.normalize(E, dim=-1) * 1.4
    tokens = torch.randint(0, V, (N_MSG * TOK_PER,), generator=g)
    owner = torch.arange(N_MSG).repeat_interleave(TOK_PER)
    R = torch.linalg.qr(torch.randn(D, D, generator=g))[0]      # invertible rotation
    neutral = {
        0: E[tokens],                                            # exact
        2: E[tokens] @ R + 0.05 * torch.randn(len(tokens), D, generator=g),
        4: torch.randn(len(tokens), D, generator=g),             # unrecoverable
    }
    labels = torch.randint(0, 4, (N_MSG,), generator=g)
    centres = torch.randn(4, D, generator=g) * 3
    game = {
        0: centres[labels] + 0.4 * torch.randn(N_MSG, D, generator=g),
        2: centres[labels] @ R + 0.4 * torch.randn(N_MSG, D, generator=g),
        4: torch.randn(N_MSG, D, generator=g),
    }
    return dict(layers=[0, 2, 4], neutral={k: v.half() for k, v in neutral.items()},
                tokens=tokens, owner=owner, game={k: v.half() for k, v in game.items()},
                labels=labels, emb=E.half())


def cells_of(nb):
    return [''.join(c['source']) for c in nb['cells'] if c['cell_type'] == 'code']


def main() -> int:
    torch.Tensor.cuda = lambda self, *a, **k: self          # CPU stand-in
    nb = json.loads(NB.read_text())
    g = {"__name__": "__main__", "torch": torch, "json": json, "random": random,
         "BLOB": synth(), "OPTIONS": ['A', 'B', 'C', 'D'],
         "WORK": Path("/tmp/_l7_selftest"), "collections": __import__('collections')}
    g["WORK"].mkdir(parents=True, exist_ok=True)
    g["LAYERS"] = g["BLOB"]["layers"]

    out = []
    for src in cells_of(nb):
        title = next((l for l in src.splitlines() if "#@title" in l), "")
        if not any(title.startswith(f"#@title {n} ") for n in (5, 6, 7, 8)):
            continue
        body = "\n".join(l for l in src.splitlines() if not l.lstrip().startswith("#@"))
        buf = []
        g["print"] = lambda *a, **k: buf.append(" ".join(str(x) for x in a))
        try:
            exec(compile(body, title.strip(), "exec"), g)
            st = "ok"
        except Exception as e:
            st = f"*** {type(e).__name__}: {e}"
        finally:
            g.pop("print", None)
        out.append((title.strip()[:44], st, buf))

    faults = 0
    for title, st, buf in out:
        print(f'--- {title}  [{st}]')
        for l in buf:
            print('   ', l)
        if st.startswith("***"):
            faults += 1
    if faults:
        print(f'\n{faults} code faults — probe did not run')
        return 1

    A, B = g.get("A_RES", {}), g.get("B_RES", {})
    checks = [
        ("A layer0 (control) ~1.0", A.get(0, {}).get('top1', 0) > 0.95),
        ("A layer2 (rotation) high", A.get(2, {}).get('top1', 0) > 0.80),
        ("A layer4 (noise) ~0", A.get(4, {}).get('top1', 1) < 0.05),
        ("B layer2 (separable) high", B.get(2, 0) > 0.90),
        ("B layer4 (noise) ~chance", B.get(4, 1) < 0.45),
    ]
    print()
    ok = True
    for name, good in checks:
        print(f"  [{'pass' if good else 'FAIL'}] {name}")
        ok &= good
    print(f"\nDISCRIMINATES: {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
