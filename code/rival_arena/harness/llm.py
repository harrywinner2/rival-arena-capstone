"""LLM client over LiteLLM (OpenRouter + OpenAI direct), plus a MockLLM for
offline, zero-cost end-to-end testing.

The client returns raw text + token accounting + latency; tag parsing and
refusal coding live alongside (parse_tags / code_refusal) so the runner stays
thin. Concurrency is the caller's job (the runner gathers the two seats; the
experiment driver bounds total in-flight calls with a semaphore).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import re
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional

from ..schemas import ModelSpec, RefusalCode

_TAG = lambda name, text: (m.group(1).strip() if (m := re.search(  # noqa: E731
    rf"<{name}>(.*?)</{name}>", text, re.DOTALL | re.IGNORECASE)) else None)

_REFUSAL_MARKERS = (
    "i can't", "i cannot", "i won't", "i will not", "i'm not able", "i am not able",
    "i refuse", "as an ai", "i'm sorry", "i am sorry", "cannot assist", "not appropriate",
    "i must decline", "unethical", "i won't collude", "against my", "illegal",
)


_HARD_ERROR_MARKERS = (
    "insufficient credits", "402", "invalid api key", "no auth credentials",
    "401", "authenticationerror", "incorrect api key", "user not found",
)


def is_hard_error(msg: str | None) -> bool:
    """A non-retryable error that should abort the whole sweep (bad/empty key,
    no credits) rather than silently fill the run with empty rounds.

    Credit-exhaustion phrasings count as hard too: if we reach the runner with a
    credit error it means failover is already spent (no backup, or the backup is
    also out), so aborting cleanly is the right move."""
    if not msg:
        return False
    low = msg.lower()
    return (any(mk in low for mk in _HARD_ERROR_MARKERS)
            or any(mk in low for mk in _CREDIT_EXHAUSTION_MARKERS))


# Credit-exhaustion signatures. These are the OpenRouter / LiteLLM errors that
# mean "this key has no money left" — as opposed to a bad/missing key (auth) or a
# transient rate limit (429). On these, and ONLY these, we fail over to the
# backup key. Matched case-insensitively against str(exception).
_CREDIT_EXHAUSTION_MARKERS = (
    "insufficient credits",
    "insufficient_credits",
    "negative balance",
    "requires more credits",
    "more credits are required",
    "exceeded your",            # "exceeded your ... limit" / "...credit limit"
    "out of credits",
    "credit limit",
    "payment required",
)


def _http_status(exc: BaseException) -> Optional[int]:
    """Best-effort HTTP status extraction from a LiteLLM/openai-style exception."""
    for attr in ("status_code", "http_status", "code"):
        val = getattr(exc, attr, None)
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
    return None


def is_credit_exhaustion(exc: BaseException) -> bool:
    """True iff ``exc`` looks like the active OpenRouter key has run out of credits.

    Triggers on HTTP 402 (Payment Required) or on the credit-specific message
    signatures. Deliberately does NOT trigger on 429 (rate limit) or on auth
    errors (401/403/invalid key) — those are not "out of money" and must not burn
    the failover."""
    status = _http_status(exc)
    if status == 429:                 # rate limit — same key, back off & retry
        return False
    if status == 402:                 # Payment Required — out of credits
        return True
    low = str(exc).lower()
    # A bare "402" can appear in a message even when status isn't parseable.
    if " 402" in low or "error code: 402" in low or "status 402" in low:
        return True
    return any(mk in low for mk in _CREDIT_EXHAUSTION_MARKERS)


# --------------------------------------------------------------------------- #
# Active OpenRouter key + automatic failover to the backup key.
#
# litellm reads OPENROUTER_API_KEY from the environment, but to fail over we must
# choose the key per-call. We keep a module-level "active key" that every
# OpenRouter call passes explicitly. When the primary key is exhausted we switch
# the active key to the backup ONCE and stay there for the rest of the process —
# we never go back to hammering the dead primary. Key VALUES are never logged.
# --------------------------------------------------------------------------- #
_KEY_LOCK = threading.Lock()
_ON_BACKUP = False                    # have we already failed over?
_FAILOVER_LOGGED = False


def _primary_key() -> Optional[str]:
    return os.getenv("OPENROUTER_API_KEY") or None


def _backup_key() -> Optional[str]:
    return os.getenv("OPENROUTER_API_KEY_BACKUP") or None


def active_openrouter_key() -> Optional[str]:
    """The OpenRouter key the client should use right now (primary until failover,
    backup afterwards). Returns None if no key is configured."""
    with _KEY_LOCK:
        if _ON_BACKUP:
            return _backup_key()
        return _primary_key()


def on_backup_key() -> bool:
    """Test/diagnostic helper: are we currently on the backup key?"""
    with _KEY_LOCK:
        return _ON_BACKUP


def _switch_to_backup() -> bool:
    """Flip the active key to the backup, exactly once. Returns True only when we
    JUST switched (so the caller should retry the same call on the backup key).
    Returns False when there is nothing to switch to — either no distinct backup
    is configured, or we are ALREADY on the backup and it too is exhausted — in
    which case the caller should surface the hard error rather than loop on a
    dead key."""
    global _ON_BACKUP, _FAILOVER_LOGGED
    with _KEY_LOCK:
        if _ON_BACKUP:
            return False              # already on backup; it also failed -> give up
        backup = _backup_key()
        if not backup or backup == _primary_key():
            return False              # no distinct backup configured
        _ON_BACKUP = True
        should_log = not _FAILOVER_LOGGED
        _FAILOVER_LOGGED = True
    if should_log:
        # ONE line, to STDERR. Never the key value (not even a prefix).
        print("[keyfailover] primary key exhausted; switched to backup key",
              file=sys.stderr, flush=True)
    return True


def _reset_failover_state() -> None:
    """Test hook: restore the module to its initial (primary) state."""
    global _ON_BACKUP, _FAILOVER_LOGGED
    with _KEY_LOCK:
        _ON_BACKUP = False
        _FAILOVER_LOGGED = False


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    error: Optional[str] = None


def parse_tags(text: str) -> dict[str, Optional[str]]:
    """Extract <scratchpad>/<message>/<action> blocks."""
    return {
        "scratchpad": _TAG("scratchpad", text),
        "message": _TAG("message", text),
        "action": _TAG("action", text),
    }


def code_refusal(text: str, parsed_action_ok: bool, repaired: bool) -> RefusalCode:
    """Classify a response (P19). Order matters: a clean action wins; otherwise we
    distinguish a substantive refusal from generic off-task output."""
    if parsed_action_ok:
        return RefusalCode.REPAIRED if repaired else RefusalCode.CLEAN
    low = (text or "").lower()
    if any(mk in low for mk in _REFUSAL_MARKERS):
        return RefusalCode.REFUSAL
    return RefusalCode.OFF_TASK


class LLMClient:
    """Async LiteLLM wrapper with retry/backoff."""

    def __init__(self, max_retries: int = 4):
        self.max_retries = max_retries
        self._litellm = None

    def _lazy(self):
        if self._litellm is None:
            import litellm  # imported lazily so offline/mock runs need no dep
            litellm.drop_params = True   # silently drop unsupported params (e.g. seed)
            litellm.suppress_debug_info = True
            self._litellm = litellm
        return self._litellm

    async def complete(
        self, model: ModelSpec, system: str, user: str,
        temperature: float = 0.7, max_tokens: int = 256, seed: Optional[int] = None,
    ) -> LLMResponse:
        litellm = self._lazy()
        headers = {}
        if model.provider == "openrouter":
            headers = {
                "HTTP-Referer": os.getenv("OPENROUTER_APP_URL", ""),
                "X-Title": os.getenv("OPENROUTER_APP_TITLE", "Rival-AI-Arena"),
            }
        messages = [{"role": "system", "content": system},
                    {"role": "user", "content": user}]
        start = time.time()
        last_err = None
        for attempt in range(self.max_retries):
            # For OpenRouter, pass the *active* key explicitly so failover can
            # swap primary -> backup per call. None lets litellm fall back to its
            # own env lookup (and keeps non-openrouter providers untouched).
            api_key = active_openrouter_key() if model.provider == "openrouter" else None
            try:
                resp = await litellm.acompletion(
                    model=model.litellm_model, messages=messages,
                    temperature=temperature, max_tokens=max_tokens,
                    seed=seed, extra_headers=headers or None,
                    api_key=api_key,
                )
                txt = resp.choices[0].message.content or ""
                usage = getattr(resp, "usage", None)
                return LLMResponse(
                    text=txt,
                    prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
                    completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
                    latency_s=time.time() - start,
                )
            except Exception as e:  # noqa: BLE001 — surface as a coded error, don't crash the sweep
                last_err = str(e)
                # Credit exhaustion on an OpenRouter key: try to fail over to the
                # backup key and retry the SAME call immediately (no backoff —
                # the primary is dead, not throttled). If we switch, stay on the
                # backup for all future calls. 429s / auth errors fall through to
                # the normal backoff path on the same key.
                if model.provider == "openrouter" and is_credit_exhaustion(e):
                    if _switch_to_backup():
                        continue       # retry now on the backup key
                    # No backup to fail over to (or backup also exhausted) ->
                    # surface as a hard error so the runner aborts cleanly.
                    break
                await asyncio.sleep(min(2 ** attempt, 20))
        return LLMResponse(text="", latency_s=time.time() - start, error=last_err)


class MockLLM(LLMClient):
    """Deterministic, dependency-free stand-in. Parses the action menu out of the
    prompt and picks an action, so the full env+harness+metrics+viz pipeline can be
    exercised end-to-end with zero API spend. Cooperation-leaning so smoke runs
    produce non-degenerate metrics.
    """

    def __init__(self, coop_bias: float = 0.75):
        super().__init__()
        self.coop_bias = coop_bias

    async def complete(  # type: ignore[override]
        self, model: ModelSpec, system: str, user: str,
        temperature: float = 0.7, max_tokens: int = 256, seed: Optional[int] = None,
    ) -> LLMResponse:
        h = int(hashlib.sha1(f"{model.id}|{seed}|{len(user)}|{user[-80:]}".encode())
                .hexdigest(), 16)
        if "<message>" in user:  # message phase
            menu = re.findall(r"^\s*-\s*(.+)$", user, re.MULTILINE)
            if "menu" in user.lower() and menu:        # L1 canned signal
                pick = menu[0] if (h % 100) / 100 < self.coop_bias else menu[min(1, len(menu) - 1)]
                msg = pick
            else:
                msg = "I intend to cooperate; let's both keep our payoffs high."
            return LLMResponse(text=f"<scratchpad>mock</scratchpad><message>{msg}</message>")
        # action phase: parse the menu, pick cooperatively-biased
        menu = re.findall(r"^\s*-\s*(.+)$", user, re.MULTILINE)
        if not menu:
            return LLMResponse(text="<scratchpad>mock</scratchpad><action>?</action>")
        idx = 0 if (h % 100) / 100 < self.coop_bias else (len(menu) - 1)
        return LLMResponse(
            text=f"<scratchpad>mock reasoning</scratchpad><action>{menu[idx]}</action>"
        )
