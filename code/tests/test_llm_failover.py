"""Automatic OpenRouter API-key failover (zero API spend).

Every test drives the real ``LLMClient.complete`` retry/failover loop but with a
fake ``litellm`` object injected onto the client, so no network call is ever
made and no credits are ever spent. We assert:

  (a) a 402 / "insufficient credits" error makes the client switch to the BACKUP
      key and retry the SAME call (and STAY on backup for later calls);
  (b) a 429 (rate limit) does NOT switch keys;
  (c) neither key VALUE is ever emitted to stderr/stdout/logs.
"""

from __future__ import annotations

import asyncio

import pytest

from rival_arena.harness import llm as llmmod
from rival_arena.harness.llm import LLMClient
from rival_arena.schemas import ModelSpec, Origin

PRIMARY = "sk-or-PRIMARYsecret-aaaaaaaaaaaaaaaaaaaaaaaaaaaa"
BACKUP = "sk-or-BACKUPsecret-bbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def _model() -> ModelSpec:
    return ModelSpec(
        id="test-model",
        litellm_model="openrouter/qwen/qwen-2.5-7b-instruct",
        origin=Origin.CHINESE,
        family="qwen",
        provider="openrouter",
    )


class _FakeResp:
    """Minimal litellm response shape (resp.choices[0].message.content + usage)."""

    class _Usage:
        prompt_tokens = 3
        completion_tokens = 4

    def __init__(self):
        msg = type("M", (), {"content":
                   "<scratchpad>ok</scratchpad><action>C</action>"})()
        choice = type("C", (), {"message": msg})()
        self.choices = [choice]
        self.usage = _FakeResp._Usage()


class _CreditError(Exception):
    """OpenRouter-style 402 / insufficient-credits error."""
    status_code = 402

    def __str__(self):
        return ("litellm.APIError: OpenRouterException - {\"error\":{\"code\":402,"
                "\"message\":\"This request requires more credits, or fewer "
                "max_tokens. You requested up to ... but your balance is "
                "insufficient credits.\"}}")


class _RateLimitError(Exception):
    """OpenRouter-style 429 rate-limit error."""
    status_code = 429

    def __str__(self):
        return ("litellm.RateLimitError: OpenRouterException - rate limit "
                "exceeded, please slow down (429)")


class _FakeLitellm:
    """Records which api_key each acompletion call was made with, and replays a
    scripted sequence of outcomes (exception classes or None=success)."""

    def __init__(self, script):
        self._script = list(script)
        self.keys_used: list[str | None] = []
        self.calls = 0

    async def acompletion(self, *, model, messages, temperature, max_tokens,
                          seed, extra_headers, api_key):
        self.keys_used.append(api_key)
        outcome = self._script[self.calls] if self.calls < len(self._script) \
            else self._script[-1]
        self.calls += 1
        if outcome is None:
            return _FakeResp()
        raise outcome()


@pytest.fixture(autouse=True)
def _isolate(monkeypatch):
    """Fresh failover state + known keys for every test, and no real backoff."""
    monkeypatch.setenv("OPENROUTER_API_KEY", PRIMARY)
    monkeypatch.setenv("OPENROUTER_API_KEY_BACKUP", BACKUP)
    llmmod._reset_failover_state()
    # make asyncio.sleep instant so the 429 backoff path doesn't slow the suite
    real_sleep = asyncio.sleep

    async def _fast_sleep(_s):
        await real_sleep(0)

    monkeypatch.setattr(llmmod.asyncio, "sleep", _fast_sleep)
    yield
    llmmod._reset_failover_state()


def _client_with(script):
    c = LLMClient(max_retries=4)
    c._litellm = _FakeLitellm(script)
    return c


def _run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------------------- #
# (a) credit exhaustion -> switch to backup + retry; then STAY on backup
# --------------------------------------------------------------------------- #
def test_402_fails_over_to_backup_and_retries():
    # 1st call: credit error on primary. 2nd call: success on backup.
    c = _client_with([_CreditError, None])
    r = _run(c.complete(_model(), "sys", "user"))

    assert r.error is None, f"expected success after failover, got {r.error!r}"
    assert "<action>" in r.text
    fake = c._litellm
    assert fake.keys_used == [PRIMARY, BACKUP], fake.keys_used
    assert llmmod.on_backup_key() is True

    # Subsequent calls STAY on backup (never re-hit the dead primary).
    c2 = _client_with([None])
    _run(c2.complete(_model(), "sys", "user"))
    assert c2._litellm.keys_used == [BACKUP]


def test_402_message_variants_all_fail_over():
    for marker in ("insufficient credits", "negative balance",
                   "requires more credits", "exceeded your credit limit"):
        llmmod._reset_failover_state()

        class _E(Exception):
            def __str__(self, _m=marker):
                return f"litellm.APIError: OpenRouterException - {_m}"

        c = _client_with([_E, None])
        r = _run(c.complete(_model(), "sys", "user"))
        assert r.error is None, marker
        assert c._litellm.keys_used == [PRIMARY, BACKUP], marker


def test_backup_also_exhausted_surfaces_hard_error():
    from rival_arena.harness.llm import is_hard_error
    # primary 402 -> switch to backup -> backup 402 -> give up (no infinite loop).
    c = _client_with([_CreditError, _CreditError, _CreditError, _CreditError])
    r = _run(c.complete(_model(), "sys", "user"))
    assert r.error is not None
    assert is_hard_error(r.error) is True
    # exactly two calls: one primary, one backup — no looping on the dead key.
    assert c._litellm.keys_used == [PRIMARY, BACKUP]


def test_no_backup_configured_does_not_switch(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY_BACKUP", "")
    llmmod._reset_failover_state()
    c = _client_with([_CreditError, _CreditError, _CreditError, _CreditError])
    r = _run(c.complete(_model(), "sys", "user"))
    assert r.error is not None
    assert llmmod.on_backup_key() is False
    assert set(c._litellm.keys_used) == {PRIMARY}


# --------------------------------------------------------------------------- #
# (b) rate limit (429) -> do NOT switch; retry/backoff on the SAME key
# --------------------------------------------------------------------------- #
def test_429_does_not_fail_over():
    # 429 on first attempt, then success — must stay on PRIMARY throughout.
    c = _client_with([_RateLimitError, None])
    r = _run(c.complete(_model(), "sys", "user"))
    assert r.error is None
    assert c._litellm.keys_used == [PRIMARY, PRIMARY]
    assert llmmod.on_backup_key() is False


def test_429_exhausting_retries_stays_on_primary():
    c = _client_with([_RateLimitError] * 8)  # always rate-limited
    r = _run(c.complete(_model(), "sys", "user"))
    assert r.error is not None
    assert llmmod.on_backup_key() is False
    assert set(c._litellm.keys_used) == {PRIMARY}


# --------------------------------------------------------------------------- #
# (c) key VALUES are never logged / printed
# --------------------------------------------------------------------------- #
def test_failover_never_prints_key_values(capsys):
    c = _client_with([_CreditError, None])
    _run(c.complete(_model(), "sys", "user"))
    out = capsys.readouterr()
    blob = out.out + out.err
    assert "[keyfailover]" in out.err            # the one-line notice did fire
    for secret in (PRIMARY, BACKUP):
        assert secret not in blob
        # not even a long identifying prefix
        assert secret[:16] not in blob
    # the literal env values must never appear, only the marker line
    assert "switched to backup key" in out.err


def test_mock_paths_unaffected():
    """--mock uses MockLLM, which never touches litellm or the key machinery."""
    from rival_arena.harness.llm import MockLLM
    m = MockLLM()
    r = _run(m.complete(_model(), "<message>", "Choose:\n- C\n- D"))
    assert r.error is None
    assert llmmod.on_backup_key() is False
