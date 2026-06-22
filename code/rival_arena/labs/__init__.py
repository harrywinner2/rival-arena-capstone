"""FULL E1 agentic research-lab harness: a sandboxed in-memory ``Lab`` world,
mocked+logged tools, the agentic loop with a rapport->threat arc, and a
containment guard. See ``sandbox.py`` for the safety guarantees.
"""

from .sandbox import Lab, assert_contained, dispatch, tools_for  # noqa: F401
from .loop import (  # noqa: F401
    LLMAgent, LoopResult, ScriptedAgent, build_prompt, fake_always_share,
    fake_never_share, parse_turn, run_lab_match,
)

__all__ = [
    "Lab", "assert_contained", "dispatch", "tools_for",
    "LLMAgent", "LoopResult", "ScriptedAgent", "build_prompt",
    "fake_always_share", "fake_never_share", "parse_turn", "run_lab_match",
]
