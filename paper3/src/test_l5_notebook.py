#!/usr/bin/env python3
"""Execute the L5 notebook's logic cells against a stub model.

Written after five Colab runs were spent discovering NameErrors and scaffold bugs that
executing the code once would have caught. Syntax-checking is not enough: it does not
bind names, does not exercise control flow, and does not notice that a variable
referenced in one patch was never introduced by another.

This runs the pure-logic cells (game, self-test, results) with torch/transformers
stubbed, so it can run anywhere with no GPU. It cannot validate model behaviour -- only
that the code paths execute and every name resolves.
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "notebooks" / "L5_latent_predicate.ipynb"


class _FakeTensor(list):
    def __init__(self, vals):
        super().__init__(vals)

    def argmax(self):
        return int(max(range(len(self)), key=lambda i: self[i]))

    def max(self):
        return max(self)

    def cuda(self):
        return self

    @property
    def shape(self):
        return (1, len(self))


def _stub_env():
    """Minimal stand-ins for the GPU/model surface the logic cells touch."""
    torch = types.ModuleType("torch")

    def no_grad():
        def deco(fn):
            return fn
        return deco
    torch.no_grad = no_grad
    torch.bfloat16 = "bf16"
    torch.float16 = "fp16"
    torch.cuda = types.SimpleNamespace(
        is_available=lambda: True, get_device_name=lambda i: "stub",
        is_bf16_supported=lambda: True)
    torch.__version__ = "stub"

    class _Tok:
        eos_token_id = 0

        def __call__(self, text, return_tensors=None):
            return types.SimpleNamespace(input_ids=_FakeTensor([1, 2, 3]))

        def encode(self, s, add_special_tokens=True):
            return [ord(s[0])]

        def decode(self, ids, skip_special_tokens=True):
            return "Let us both choose A."

        def apply_chat_template(self, msgs, tokenize=False, add_generation_prompt=True):
            return "\n".join(m["content"] for m in msgs) + "\n<assistant>"

    # deterministic, payoff-blind stub: always prefers the FIRST code id
    def _action_logprobs(prefix_ids, code_ids):
        return _FakeTensor([0.7, 0.3])

    return torch, _Tok(), _action_logprobs


def main() -> None:
    nb = json.loads(NB.read_text())
    cells = [c for c in nb["cells"] if c["cell_type"] == "code"]

    torch, tok, action_logprobs = _stub_env()
    sys.modules["torch"] = torch

    g: dict = {
        "__name__": "__main__", "torch": torch, "TOK": tok,
        "MODEL": types.SimpleNamespace(config=types.SimpleNamespace(hidden_size=1536)),
        "PAYOFF": {('C', 'C'): (3, 3), ('C', 'D'): (0, 5),
                   ('D', 'C'): (5, 0), ('D', 'D'): (1, 1)},
        "CONT_PROB": 0.97, "SEED_OFFSET": 1000, "GATE_SEEDS": 4, "PILOT_SEEDS": 2,
        "ROUNDS": 3, "MODEL_ID": "Qwen/Qwen2.5-14B-Instruct",
        "WORK": Path("/tmp/_l5_selftest_work"),
        "LINK": lambda h: h, "OuterLink": object,
    }
    (g["WORK"] / "results").mkdir(parents=True, exist_ok=True)

    # cells whose bodies are pure logic (no real model / no Drive / no training)
    WANT = ["5 · The game", "5b · Scaffold self-test", "3 · Checkpoint"]
    ran = []
    for c in cells:
        src = "".join(c["source"])
        title = next((l for l in src.splitlines() if "#@title" in l), "")
        if not any(w in title for w in WANT):
            continue
        body = "\n".join(l for l in src.splitlines()
                         if not l.lstrip().startswith("#@"))
        # the self-test needs the stubbed scorer and must not exit the harness
        body = body.replace("raise SystemExit(", "raise RuntimeError(")
        g["action_logprobs"] = action_logprobs
        try:
            exec(compile(body, title.strip() or "cell", "exec"), g)
            ran.append((title.strip(), "ok"))
        except RuntimeError as e:            # a self-test verdict, not a code fault
            ran.append((title.strip(), f"verdict: {str(e)[:60]}"))
        except Exception as e:               # a real code fault
            ran.append((title.strip(), f"*** {type(e).__name__}: {e}"))

    print("=== L5 notebook logic execution ===")
    bad = 0
    for title, status in ran:
        flag = "FAIL" if status.startswith("***") else "pass"
        if flag == "FAIL":
            bad += 1
        print(f"  [{flag}] {title[:52]:52s} {status}")
    print(f"\n{len(ran)} logic cells executed, {bad} with code faults")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
