"""Per-match measurement primitives (experiments.md §2).

Everything here is computed from a single ``MatchResult`` and is deliberately
free of statistics over *multiple* matches (that lives in ``stats.py``). The
match — not the round — is the unit of analysis (P17).

Operational definitions, straight from §2:
  * Cooperation rate ``C`` — fraction of decision points where an LLM seat plays
    the cooperative action; reported as a series ``C(t)`` and an end-state mean
    over the last ``k`` rounds.
  * Normalized welfare ``W`` — joint payoff rescaled so ``W=0`` is mutual
    all-defect (the benchmark floor) and ``W=1`` is the social optimum.
  * Collusion index ``K`` — market only: ``(p - p_competitive)/(p_monopoly -
    p_competitive)`` (kept conceptually distinct from agent–agent cooperation, P7).
  * Convergence ``tau`` / stability ``sigma`` — rounds to a stable action
    distribution and the variance thereafter (the cleanest place an origin
    second-order effect can surface, H4).
  * Promise-keeping (P8) — a near-free content probe separating "promises" from
    "more bits".
  * Refusal coding (P19) — never silently dropped; the per-condition rate is
    itself a finding.

Benchmarks are read from ``result.manifest["benchmarks"]`` (the env's
``Game.benchmarks()`` payload), so metrics never import env/.
"""

from __future__ import annotations

from statistics import mean
from typing import Any, Optional

from ..config import END_STATE_K, LOCKIN_THRESHOLD
from ..schemas import MatchResult, RefusalCode, RoundRecord


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _llm_seats(result: MatchResult) -> list[str]:
    """Seats occupied by an LLM (classical-strategy seats are excluded from C
    so an Always-Defect anchor does not drag the cooperation rate, A5)."""
    seats: list[str] = []
    for p in result.spec.players:
        kind = getattr(p, "kind", None)
        kind_val = getattr(kind, "value", kind)
        if kind_val in (None, "llm"):
            seats.append(p.seat)
    return seats or [p.seat for p in result.spec.players]


def _coop_axis_defined(result: MatchResult) -> bool:
    """The C axis is undefined for pure zero-sum games (§A2). We infer it from
    whether any move carries a non-None ``cooperative`` flag."""
    for rnd in result.rounds:
        for move in rnd.moves.values():
            if move.action is not None and move.action.cooperative is not None:
                return True
    return False


def _benchmarks(result: MatchResult) -> dict[str, Any]:
    return dict(result.manifest.get("benchmarks", {}) or {})


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


# --------------------------------------------------------------------------- #
# Cooperation
# --------------------------------------------------------------------------- #
def coop_rate_series(result: MatchResult) -> list[float]:
    """Per-round mean cooperation over the LLM seats (§2 ``C(t)``).

    Skips zero-sum / undefined rounds: a seat contributes only when its action's
    ``cooperative`` flag is not None. A round with no scorable seat is omitted
    entirely (rather than reported as 0.0) so refusals/zero-sum don't bias C down.
    """
    seats = _llm_seats(result)
    series: list[float] = []
    for rnd in result.rounds:
        flags: list[float] = []
        for seat in seats:
            move = rnd.moves.get(seat)
            if move is None or move.action is None:
                continue
            if move.refusal == RefusalCode.API_ERROR:   # missing data, not a choice
                continue
            coop = move.action.cooperative
            if coop is None:
                continue
            flags.append(1.0 if coop else 0.0)
        if flags:
            series.append(mean(flags))
    return series


def coop_endstate(result: MatchResult, k: int = END_STATE_K) -> Optional[float]:
    """Mean cooperation over the last ``k`` scored rounds (§2 end-state ``C``)."""
    series = coop_rate_series(result)
    if not series:
        return None
    tail = series[-k:] if k > 0 else series
    return float(mean(tail))


def locked_in(result: MatchResult, k: int = END_STATE_K) -> Optional[bool]:
    """Did the match lock into cooperation? End-state ``C`` > LOCKIN_THRESHOLD
    (P17). None when the coop axis is undefined (zero-sum) or no rounds scored."""
    if not _coop_axis_defined(result):
        return None
    end = coop_endstate(result, k)
    if end is None:
        return None
    return end > LOCKIN_THRESHOLD


# --------------------------------------------------------------------------- #
# Welfare
# --------------------------------------------------------------------------- #
def welfare_series(result: MatchResult) -> list[Optional[float]]:
    """Normalized joint welfare per round, ``W=(joint - floor)/(opt - floor)``,
    clipped to [0,1] (§2). None per round if benchmarks are missing/degenerate."""
    bm = _benchmarks(result)
    floor = bm.get("floor")
    opt = bm.get("social_optimum")
    series: list[Optional[float]] = []
    for rnd in result.rounds:
        if floor is None or opt is None or opt == floor:
            series.append(None)
            continue
        joint = sum(rnd.payoffs.values())
        series.append(_clip01((joint - floor) / (opt - floor)))
    return series


def welfare_endstate(result: MatchResult, k: int = END_STATE_K) -> Optional[float]:
    """Mean normalized welfare over the last ``k`` rounds; None if undefined."""
    series = [w for w in welfare_series(result) if w is not None]
    if not series:
        return None
    tail = series[-k:] if k > 0 else series
    return float(mean(tail))


# --------------------------------------------------------------------------- #
# Collusion index K (market games only)
# --------------------------------------------------------------------------- #
def _round_mean_price(rnd: RoundRecord) -> Optional[float]:
    """Mean price across sellers for one round, read from ``extra['prices']``.

    Accepts either a {seat: price} mapping or a flat list of prices."""
    prices = rnd.extra.get("prices") if rnd.extra else None
    if prices is None:
        return None
    if isinstance(prices, dict):
        vals = [float(v) for v in prices.values() if v is not None]
    else:
        vals = [float(v) for v in prices if v is not None]
    if not vals:
        return None
    return mean(vals)


def _is_market_game(result: MatchResult) -> bool:
    bm = _benchmarks(result)
    return "p_competitive" in bm and "p_monopoly" in bm


def collusion_index_series(result: MatchResult) -> Optional[list[float]]:
    """Per-round market collusion index ``K`` (§2). None if not a market game.

    ``K = (mean_price - p_competitive)/(p_monopoly - p_competitive)``: K=0 is the
    competitive (Bertrand/Nash) benchmark, K=1 is full monopoly/cartel [R1, R4].
    Not clipped — supracompetitive prices above monopoly (K>1) are informative.
    """
    if not _is_market_game(result):
        return None
    bm = _benchmarks(result)
    p_comp = float(bm["p_competitive"])
    p_mono = float(bm["p_monopoly"])
    if p_mono == p_comp:
        return None
    series: list[float] = []
    for rnd in result.rounds:
        p = _round_mean_price(rnd)
        if p is None:
            continue
        series.append((p - p_comp) / (p_mono - p_comp))
    return series


def collusion_endstate(result: MatchResult, k: int = END_STATE_K) -> Optional[float]:
    """Mean ``K`` over the last ``k`` priced rounds; None if not a market game."""
    series = collusion_index_series(result)
    if not series:
        return None
    tail = series[-k:] if k > 0 else series
    return float(mean(tail))


# --------------------------------------------------------------------------- #
# Convergence tau / stability sigma
# --------------------------------------------------------------------------- #
def convergence_tau(
    series: list[float], eps: float = 0.1, window: int = 3
) -> Optional[int]:
    """First round index after which the action distribution is stable (§2 ``tau``).

    "Stable" = the series moves by < ``eps`` over a sliding window of length
    ``window`` (max-min within the window). Returns the round index at the start
    of the first such stable window, or None if it never stabilizes.
    """
    n = len(series)
    if n == 0 or window <= 0:
        return None
    if n < window:
        return None
    for start in range(0, n - window + 1):
        chunk = series[start : start + window]
        if (max(chunk) - min(chunk)) < eps:
            return start
    return None


def stability_sigma(series: list[float], tau: Optional[int]) -> Optional[float]:
    """Variance of the action distribution after convergence (§2 ``sigma``).

    Population variance of the series from ``tau`` onward. None if the match
    never converged or there is < 1 post-tau point."""
    if tau is None:
        return None
    tail = series[tau:]
    if not tail:
        return None
    m = mean(tail)
    return float(sum((x - m) ** 2 for x in tail) / len(tail))


# --------------------------------------------------------------------------- #
# Promise-keeping (P8)
# --------------------------------------------------------------------------- #
def promise_keeping_rate(result: MatchResult) -> Optional[float]:
    """Among (seat, round) pairs where a seat *stated* it would cooperate
    (``move.promise is True``), the fraction where that seat then played the
    cooperative action (P8). None if no promises were made.

    This separates "promises change behaviour" from "more bits" — a near-free
    content probe on top of the channel ladder.
    """
    kept = 0
    total = 0
    for rnd in result.rounds:
        for move in rnd.moves.values():
            if move.promise is True:
                total += 1
                if move.action is not None and move.action.cooperative is True:
                    kept += 1
    if total == 0:
        return None
    return kept / total


# --------------------------------------------------------------------------- #
# Refusal coding (P19)
# --------------------------------------------------------------------------- #
_REFUSAL_FAMILY = {RefusalCode.REPAIRED, RefusalCode.REFUSAL, RefusalCode.OFF_TASK}


def refusal_rates(result: MatchResult) -> dict[str, Any]:
    """Per-seat and overall refusal rates (P19 — reported, never dropped).

    Returns:
      * ``overall`` — fraction of (seat, round) responses coded REPAIRED /
        REFUSAL / OFF_TASK (the "not a clean action" family).
      * ``refusal_only`` — fraction coded *substantive* REFUSAL specifically.
      * ``per_seat`` — {seat: {"overall": f, "refusal_only": f}}.
      * ``by_code`` — raw counts per RefusalCode value.
      * ``n_responses`` — denominator.
    """
    per_seat: dict[str, dict[str, float]] = {}
    counts: dict[str, dict[str, int]] = {}
    by_code: dict[str, int] = {c.value: 0 for c in RefusalCode}
    total = 0          # behavioural responses (API errors excluded — infra, not behaviour)
    fam_total = 0
    ref_total = 0
    api_err_total = 0
    for rnd in result.rounds:
        for seat, move in rnd.moves.items():
            code = move.refusal
            by_code[code.value] = by_code.get(code.value, 0) + 1
            if code == RefusalCode.API_ERROR:   # missing data, not a behavioural choice
                api_err_total += 1
                continue
            counts.setdefault(seat, {"n": 0, "fam": 0, "ref": 0})
            counts[seat]["n"] += 1
            total += 1
            if code in _REFUSAL_FAMILY:
                counts[seat]["fam"] += 1
                fam_total += 1
            if code == RefusalCode.REFUSAL:
                counts[seat]["ref"] += 1
                ref_total += 1
    for seat, c in counts.items():
        n = c["n"] or 1
        per_seat[seat] = {
            "overall": c["fam"] / n,
            "refusal_only": c["ref"] / n,
        }
    n_all = total + api_err_total
    return {
        "overall": (fam_total / total) if total else 0.0,
        "refusal_only": (ref_total / total) if total else 0.0,
        "api_error_rate": (api_err_total / n_all) if n_all else 0.0,
        "per_seat": per_seat,
        "by_code": by_code,
        "n_responses": total,
    }


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #
def summarize_match(result: MatchResult, k: int = END_STATE_K) -> dict[str, Any]:
    """Assemble all per-match primitives into a flat, JSON-serializable dict.

    This is what gets attached to ``MatchResult.metrics`` and what becomes one
    row of ``metrics.csv``. Keys are stable; viz / stats depend on them.
    """
    coop_series = coop_rate_series(result)
    k_series = collusion_index_series(result)
    w_series = [w for w in welfare_series(result) if w is not None]

    coop_tau = convergence_tau(coop_series) if coop_series else None
    coop_sigma = stability_sigma(coop_series, coop_tau) if coop_series else None

    refusals = refusal_rates(result)

    summary: dict[str, Any] = {
        # identity (so the metrics table is self-describing)
        "experiment_id": result.spec.experiment_id,
        "cell_id": result.spec.cell_id,
        "channel": result.spec.channel.value,
        "game": result.spec.game.name,
        "familiarity": result.spec.game.familiarity,
        "seed": result.spec.seed,
        "n_rounds": len(result.rounds),
        # cooperation
        "coop_endstate": coop_endstate(result, k),
        "locked_in": locked_in(result, k),
        "coop_axis_defined": _coop_axis_defined(result),
        # welfare
        "welfare_endstate": welfare_endstate(result, k),
        # collusion (market only; None otherwise)
        "K_endstate": collusion_endstate(result, k),
        "is_market_game": _is_market_game(result),
        # dynamics
        "convergence_tau": coop_tau,
        "stability_sigma": coop_sigma,
        # content probe
        "promise_keeping_rate": promise_keeping_rate(result),
        # refusals (P19)
        "refusal_rate": refusals["overall"],
        "refusal_only_rate": refusals["refusal_only"],
        # series (kept for viz / re-aggregation; small)
        "coop_series": coop_series,
        "welfare_series": w_series,
        "K_series": k_series,
    }
    return summary
