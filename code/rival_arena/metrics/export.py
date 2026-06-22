"""Tidy long-format export — one row per (match × round × seat), with every field.

This is the "play with the graphs at the end" artifact: a single denormalized CSV
that pandas/plotly/seaborn can pivot any way (by channel, origin, regime, round,
seat, model, refusal code, ...) without touching the raw JSONL. Written next to
every saved run as ``rounds_long.csv`` (definition of done, enriched).

Keep it append-only in spirit: add columns, don't rename, so downstream notebooks
stay stable.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Sequence

from ..schemas import MatchResult

LONG_FIELDS = [
    # identity / factors
    "experiment_id", "cell_id", "config_hash", "seed",
    "game", "familiarity", "demand_spec", "channel", "framing",
    "pair", "seat", "model_id", "origin", "family", "opponent_seat", "opponent_model",
    # round
    "round_index", "n_rounds", "continued",
    # action
    "action_label", "action_value", "cooperative",
    # communication
    "message", "raw_message", "message_len", "scratchpad_len", "promise",
    # outcome / coding
    "refusal", "payoff", "payoff_other", "joint_payoff",
    "price", "price_other", "monitor_flag", "monitor_score",
    # cost
    "prompt_tokens", "completion_tokens", "latency_s",
]


def _row_for(result: MatchResult, rnd, seat, move) -> dict[str, Any]:
    spec = result.spec
    man = result.manifest or {}
    models = man.get("models", {}) or {}
    classical = man.get("classical", {}) or {}
    seats = list(rnd.moves.keys())
    other = next((s for s in seats if s != seat), None)
    mrow = models.get(seat, {})
    other_model = (models.get(other, {}) or {}).get("id") or classical.get(other)
    prices = (rnd.extra or {}).get("prices", {}) if rnd.extra else {}
    payoffs = rnd.payoffs or {}
    msg = move.message or ""
    scratch = move.scratchpad or ""
    act = move.action
    return {
        "experiment_id": spec.experiment_id,
        "cell_id": spec.cell_id,
        "config_hash": man.get("config_hash"),
        "seed": spec.seed,
        "game": spec.game.name,
        "familiarity": spec.game.familiarity,
        "demand_spec": spec.game.params.get("demand_spec"),
        "channel": spec.channel.value,
        "framing": spec.framing,
        "pair": "+".join(p.ref for p in spec.players),
        "seat": seat,
        "model_id": mrow.get("id") or classical.get(seat),
        "origin": mrow.get("origin") or ("classical" if seat in classical else None),
        "family": mrow.get("family"),
        "opponent_seat": other,
        "opponent_model": other_model,
        "round_index": rnd.round_index,
        "n_rounds": len(result.rounds),
        "continued": int(bool(rnd.continued)),
        "action_label": act.label if act else None,
        "action_value": act.value if act else None,
        "cooperative": (None if not act or act.cooperative is None else int(act.cooperative)),
        "message": msg,
        "raw_message": move.raw_message or "",
        "message_len": len(msg),
        "scratchpad_len": len(scratch),
        "promise": (None if move.promise is None else int(move.promise)),
        "refusal": move.refusal.value,
        "payoff": payoffs.get(seat),
        "payoff_other": payoffs.get(other),
        "joint_payoff": sum(payoffs.values()) if payoffs else None,
        "price": prices.get(seat),
        "price_other": prices.get(other),
        "monitor_flag": (None if rnd.monitor_flag is None else int(rnd.monitor_flag)),
        "monitor_score": rnd.monitor_score,
        "prompt_tokens": move.prompt_tokens,
        "completion_tokens": move.completion_tokens,
        "latency_s": round(move.latency_s, 3) if move.latency_s else 0.0,
    }


def rounds_long(results: Sequence[MatchResult]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for result in results:
        for rnd in result.rounds:
            for seat, move in rnd.moves.items():
                rows.append(_row_for(result, rnd, seat, move))
    return rows


def save_long_csv(results: Sequence[MatchResult], path: Path) -> Path:
    path = Path(path)
    rows = rounds_long(results)
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=LONG_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path
