#!/usr/bin/env python3
"""One-call smoke test of the full stack before launching the program.

registry -> LLMClient -> litellm(openai/...) -> OPENAI_API_BASE -> vLLM

Catches routing/auth problems in seconds instead of after 900 matches have failed.

    OPENAI_API_BASE=https://<pod>-8000.proxy.runpod.net/v1 OPENAI_API_KEY=EMPTY \
      python3 paper3/src/smoke_endpoint.py qwen-14b-local
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from rival_arena.harness.llm import LLMClient  # noqa: E402
from rival_arena.registry import get_model  # noqa: E402


async def main() -> None:
    mid = sys.argv[1] if len(sys.argv) > 1 else "qwen-14b-local"
    base = os.environ.get("OPENAI_API_BASE")
    print(f"model={mid}  OPENAI_API_BASE={base}")
    if not base:
        sys.exit("OPENAI_API_BASE not set")

    m = get_model(mid)
    print(f"litellm_model={m.litellm_model}  provider={m.provider}")
    client = LLMClient()
    r = await client.complete(
        m,
        "You are terse.",
        "Reply with exactly the word OK and nothing else.",
        temperature=0.0, max_tokens=16,
    )
    print(f"text={r.text!r}")
    print(f"prompt_tokens={r.prompt_tokens} completion_tokens={r.completion_tokens} "
          f"latency={r.latency_s:.2f}s")
    if not r.text.strip():
        sys.exit("EMPTY RESPONSE — routing reached the server but produced nothing")
    print("SMOKE OK")


if __name__ == "__main__":
    asyncio.run(main())
