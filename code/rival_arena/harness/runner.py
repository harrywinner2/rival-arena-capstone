"""Match runner — the two-model loop.

Move structure (A1): simultaneous and lockstep. When a channel is on, each round
is two phases — both send messages, messages are revealed, then both choose
actions, actions are revealed. An action never leaks before the other commits
(the two seats' calls in each phase run concurrently). With no channel, only the
action phase runs. Every rung gets a private scratchpad (parity, P8).

History is a rolling window, identical across conditions (P22). Continuation is
stochastic (delta) so cooperation can't unravel by backward induction.

Definition of done is enforced downstream (metrics/report); the runner's job is a
faithful, fully-logged MatchResult.
"""

from __future__ import annotations

import asyncio
import random
import time

from .. import __version__, config
from ..env import get_game, get_strategy
from ..registry import comparability_row, get_model
from ..schemas import (
    Action, AgentMove, ChannelLevel, MatchResult, MatchSpec, PlayerKind,
    RefusalCode, RoundRecord, to_jsonable,
)
from .channel import channel_config
from .llm import LLMClient, code_refusal, is_hard_error, parse_tags
from .monitor import Monitor, Paraphraser
from .prompts import action_prompt, detect_promise, message_prompt, system_prompt


class HardAPIError(RuntimeError):
    """Non-retryable API failure (bad key / no credits) — aborts the sweep."""


def _guard(r, model):
    if r.error and is_hard_error(r.error):
        raise HardAPIError(
            f"Aborting run — non-retryable API error for {model.id}: {r.error}")


async def _llm_move_message(client, model, spec, game, seat, history):
    sys = system_prompt(spec, game, seat)
    usr = message_prompt(spec, game, seat, history)
    r = await client.complete(model, sys, usr, temperature=spec.temperature,
                              max_tokens=spec.max_tokens, seed=spec.seed)
    _guard(r, model)
    tags = parse_tags(r.text)
    return tags.get("message"), tags.get("scratchpad"), r


async def _llm_move_action(client, model, spec, game, seat, history, current_messages):
    sys = system_prompt(spec, game, seat)
    usr = action_prompt(spec, game, seat, history, current_messages)
    r = await client.complete(model, sys, usr, temperature=spec.temperature,
                              max_tokens=spec.max_tokens, seed=spec.seed)
    _guard(r, model)
    tags = parse_tags(r.text)
    action_text = tags.get("action")
    model_action = game.parse_action(action_text, seat) if action_text else None
    repaired = False
    if model_action is None:                         # loose recovery over whole text
        model_action = game.parse_action(r.text, seat)
        repaired = model_action is not None
    if r.error:                                      # transient infra failure, not behaviour
        refusal = RefusalCode.API_ERROR
    else:
        refusal = code_refusal(r.text, model_action is not None, repaired)
    final = model_action if model_action is not None else game.action_menu(seat)[-1]
    return final, tags.get("scratchpad"), refusal, r


async def run_match(
    spec: MatchSpec,
    client: LLMClient,
    monitor: Monitor | None = None,
    paraphraser: Paraphraser | None = None,
) -> MatchResult:
    config.ensure_dirs()
    rng = random.Random(spec.seed)
    game = get_game(spec.game.name, spec.game.params, spec.game.familiarity)
    cfg = channel_config(spec.channel)

    # resolve players
    seats = spec.players_seats()
    llm_models = {}
    classical = {}
    for p in spec.players:
        if p.kind == PlayerKind.LLM:
            llm_models[p.seat] = get_model(p.ref)
        else:
            strat = get_strategy(p.ref)
            strat.reset()
            classical[p.seat] = strat

    rounds: list[RoundRecord] = []
    action_history: list[dict[str, Action]] = []     # for classical strategies
    refusal_counts: dict[str, int] = {s: 0 for s in seats}

    round_index = 0
    while True:
        # ---------- message phase ----------
        messages: dict[str, str] = {}
        raw_messages: dict[str, str] = {}
        msg_scratch: dict[str, str] = {}
        if cfg.has_message_phase:
            tasks = {s: _llm_move_message(client, llm_models[s], spec, game, s, rounds)
                     for s in llm_models}
            results = await asyncio.gather(*tasks.values())
            for s, (msg, scr, _r) in zip(tasks.keys(), results):
                authored = msg or ""
                raw_messages[s] = authored
                delivered = authored
                if paraphraser and cfg.free_text and authored:
                    delivered = await paraphraser.rewrite(authored)
                messages[s] = delivered
                msg_scratch[s] = scr or ""

        monitor_flag = monitor_score = None
        if monitor and messages:
            monitor_flag, monitor_score = await monitor.assess(messages)

        # ---------- action phase ----------
        actions: dict[str, Action] = {}
        moves: dict[str, AgentMove] = {}

        async def _llm_seat(s):
            return s, await _llm_move_action(
                client, llm_models[s], spec, game, s, rounds, messages or None)

        llm_results = await asyncio.gather(*[_llm_seat(s) for s in llm_models])
        for s, (act, scr, refusal, r) in llm_results:
            actions[s] = act
            if refusal != RefusalCode.CLEAN:
                refusal_counts[s] += 1
            moves[s] = AgentMove(
                seat=s, action=act, message=messages.get(s),
                raw_message=raw_messages.get(s), scratchpad=scr or msg_scratch.get(s),
                promise=detect_promise(messages.get(s)), refusal=refusal,
                prompt_tokens=r.prompt_tokens, completion_tokens=r.completion_tokens,
                latency_s=r.latency_s, raw_response=r.text, error=r.error,
            )

        for s, strat in classical.items():
            act = strat.act(action_history, s, rng)
            actions[s] = act
            moves[s] = AgentMove(seat=s, action=act, message=None,
                                 scratchpad=None, refusal=RefusalCode.CLEAN)

        payoffs = game.payoffs(actions)
        action_history.append(dict(actions))
        cont = game.continues(round_index, rng)
        extra = game_round_extra(game, actions)
        # --- B5E enforcement hook (backward-compatible; gated on a free-form game
        # param so schemas.py is untouched and the default path is unchanged). When
        # enforcement is ON and the monitor flagged this round as collusive, the
        # round's payoffs are penalised (default: confiscated -> 0) BEFORE the record
        # is built. Because prompts._format_history shows each seat its own
        # `payoffs[seat]`, the penalty is visible in the next round's history, so the
        # *shadow of enforcement* can shape later price choices (the only way the
        # price-based collusion index K can move). The realized prices in
        # extra["prices"] are left untouched (K is read from prices, not payoffs), so
        # K reflects what agents CHOSE — exactly the behaviour we want to test.
        enforcement = enforcement_config(spec.game.params)
        enforced = bool(enforcement["on"] and monitor_flag)
        if enforced:
            factor = enforcement["retained_fraction"]
            payoffs = {s: v * factor for s, v in payoffs.items()}
            extra = dict(extra)
            extra["enforced"] = True
            extra["enforcement_retained_fraction"] = factor
        rounds.append(RoundRecord(
            round_index=round_index, moves=moves, payoffs=payoffs, continued=cont,
            monitor_flag=monitor_flag, monitor_score=monitor_score,
            extra=extra,
        ))
        round_index += 1
        if not cont:
            break

    manifest = {
        "code_version": __version__,
        "config_hash": spec.config_hash(),
        "experiment_id": spec.experiment_id,
        "cell_id": spec.cell_id,
        "channel": spec.channel.value,
        "game": to_jsonable(spec.game),
        "epistemic": to_jsonable(spec.epistemic),
        "seed": spec.seed,
        "temperature": spec.temperature,
        "token_budget": spec.token_budget,
        "history_window": spec.history_window,
        "framing": spec.framing,
        "paraphrase": bool(paraphraser),
        "monitor": bool(monitor),
        "n_rounds": len(rounds),
        "benchmarks": game.benchmarks(),
        "models": {s: comparability_row(llm_models[s].id) for s in llm_models},
        "classical": {s: classical[s].name for s in classical},
        "players": to_jsonable(spec.players),
    }
    return MatchResult(
        spec=spec, rounds=rounds, manifest=manifest, refusal_counts=refusal_counts,
        finished_at=time.time(),
    )


def enforcement_config(game_params: dict | None) -> dict:
    """Parse the optional B5E enforcement settings out of the free-form game params.

    Backward-compatible: with no ``enforcement`` key (the default for every existing
    spec) this returns ``{"on": False, ...}`` and the runner's behaviour is byte-for-
    byte identical to before. ``enforcement`` may be a bool (True -> confiscate the
    flagged round's payoffs) or a dict that additionally sets
    ``retained_fraction`` (the share of payoff a seller KEEPS on a flagged round;
    0.0 = full confiscation, the default).
    """
    params = game_params or {}
    enf = params.get("enforcement", False)
    if isinstance(enf, dict):
        on = bool(enf.get("on", True))
        retained = float(enf.get("retained_fraction", 0.0))
    else:
        on = bool(enf)
        retained = 0.0
    return {"on": on, "retained_fraction": retained}


def game_round_extra(game, actions: dict[str, Action]) -> dict:
    """Game-specific per-round fields (e.g. realized prices for the market K)."""
    extra = {}
    if game.name in ("bertrand", "cournot", "double_auction"):
        extra["prices"] = {s: a.value for s, a in actions.items() if a.value is not None}
    return extra


def run_match_sync(spec: MatchSpec, client: LLMClient | None = None, **kw) -> MatchResult:
    client = client or LLMClient()
    return asyncio.run(run_match(spec, client, **kw))
