"""Tests for the metrics workstream (experiments.md §2, §5).

Synthetic MatchResults are built by hand from the schema dataclasses — no env/
or harness/ needed, no network. They exercise the per-match primitives, the
confirmatory statistics, and the definition-of-done save_run artifacts.
"""

from __future__ import annotations

import csv
import json
import math

import pytest

from rival_arena.config import END_STATE_K, LOCKIN_THRESHOLD
from rival_arena.metrics import (
    attach_metrics,
    bootstrap_ci,
    cell_summary,
    lockin_proportion,
    save_run,
    summarize_match,
    tost_equivalence,
    wilson_interval,
)
from rival_arena.metrics.core import (
    coop_endstate,
    coop_rate_series,
    collusion_endstate,
    convergence_tau,
    locked_in,
    promise_keeping_rate,
    refusal_rates,
    welfare_endstate,
)
from rival_arena.metrics.covert import (
    covert_surplus,
    mutual_information_bias_corrected,
    shuffled_baseline,
)
from rival_arena.metrics.stats import power_for_proportions
from rival_arena.schemas import (
    Action,
    AgentMove,
    ChannelLevel,
    EpistemicSpec,
    GameSpec,
    MatchResult,
    MatchSpec,
    PlayerKind,
    PlayerSpec,
    RefusalCode,
    RoundRecord,
)

# Canonical IPD payoffs (T=5, R=3, P=1, S=0); benchmarks per IPD.benchmarks().
IPD_BENCH = {"floor": 2.0, "social_optimum": 6.0, "T": 5.0, "R": 3.0, "P": 1.0, "S": 0.0}
MARKET_BENCH = {
    "floor": 0.0,
    "social_optimum": 100.0,
    "p_competitive": 10.0,
    "p_monopoly": 20.0,
}


# --------------------------------------------------------------------------- #
# builders
# --------------------------------------------------------------------------- #
def _coop() -> Action:
    return Action(label="COOPERATE", value=1.0, cooperative=True)


def _defect() -> Action:
    return Action(label="DEFECT", value=0.0, cooperative=False)


def _spec(game="ipd", channel=ChannelLevel.L3_PRIVATE, seed=0, cell_id="A1/L3/test") -> MatchSpec:
    return MatchSpec(
        experiment_id="A1",
        cell_id=cell_id,
        game=GameSpec(name=game, params={}, familiarity="canonical"),
        channel=channel,
        epistemic=EpistemicSpec(),
        players=[
            PlayerSpec(seat="A", kind=PlayerKind.LLM, ref="qwen"),
            PlayerSpec(seat="B", kind=PlayerKind.LLM, ref="llama"),
        ],
        seed=seed,
    )


def _ipd_round(i, a_coop, b_coop, *, a_msg=None, a_promise=None, refusal_a=RefusalCode.CLEAN):
    a = _coop() if a_coop else _defect()
    b = _coop() if b_coop else _defect()
    # canonical payoffs
    if a_coop and b_coop:
        pay = {"A": 3.0, "B": 3.0}
    elif a_coop and not b_coop:
        pay = {"A": 0.0, "B": 5.0}
    elif not a_coop and b_coop:
        pay = {"A": 5.0, "B": 0.0}
    else:
        pay = {"A": 1.0, "B": 1.0}
    moves = {
        "A": AgentMove(seat="A", action=a, message=a_msg, promise=a_promise, refusal=refusal_a),
        "B": AgentMove(seat="B", action=b),
    }
    return RoundRecord(round_index=i, moves=moves, payoffs=pay)


def _ipd_match(coop_pattern, bench=IPD_BENCH, **spec_kw):
    """coop_pattern: list of (a_coop, b_coop) tuples, one per round."""
    rounds = [_ipd_round(i, a, b) for i, (a, b) in enumerate(coop_pattern)]
    return MatchResult(spec=_spec(**spec_kw), rounds=rounds, manifest={"benchmarks": bench})


def _all_coop_match(n=10, **kw):
    return _ipd_match([(True, True)] * n, **kw)


def _all_defect_match(n=10, **kw):
    return _ipd_match([(False, False)] * n, **kw)


def _market_match(prices, bench=MARKET_BENCH):
    """prices: list of per-round mean prices (we put them in extra['prices'])."""
    rounds = []
    for i, p in enumerate(prices):
        moves = {
            "A": AgentMove(seat="A", action=Action(label="price", value=p)),
            "B": AgentMove(seat="B", action=Action(label="price", value=p)),
        }
        rounds.append(
            RoundRecord(
                round_index=i,
                moves=moves,
                payoffs={"A": p, "B": p},
                extra={"prices": {"A": p, "B": p}},
            )
        )
    spec = _spec(game="bertrand", cell_id="B1/L3/test")
    return MatchResult(spec=spec, rounds=rounds, manifest={"benchmarks": bench})


# --------------------------------------------------------------------------- #
# cooperation / lock-in
# --------------------------------------------------------------------------- #
def test_coop_series_all_cooperate():
    m = _all_coop_match(8)
    assert coop_rate_series(m) == [1.0] * 8


def test_coop_endstate_and_locked_in_true():
    m = _all_coop_match(10)
    assert coop_endstate(m) == 1.0
    assert coop_endstate(m) > LOCKIN_THRESHOLD
    assert locked_in(m) is True


def test_coop_endstate_and_locked_in_false():
    m = _all_defect_match(10)
    assert coop_endstate(m) == 0.0
    assert locked_in(m) is False


def test_locked_in_uses_endstate_window():
    # defect early, cooperate in the last END_STATE_K rounds -> locked in
    pattern = [(False, False)] * 6 + [(True, True)] * END_STATE_K
    m = _ipd_match(pattern)
    assert coop_endstate(m) == 1.0
    assert locked_in(m) is True


def test_coop_endstate_partial():
    # one seat cooperates, the other defects -> 0.5 each round
    m = _ipd_match([(True, False)] * 6)
    assert coop_endstate(m) == 0.5
    assert locked_in(m) is False  # 0.5 < 0.8


def test_locked_in_none_when_axis_undefined():
    # zero-sum: actions carry cooperative=None
    rounds = [
        RoundRecord(
            round_index=i,
            moves={
                "A": AgentMove(seat="A", action=Action(label="H", value=0.0, cooperative=None)),
                "B": AgentMove(seat="B", action=Action(label="T", value=1.0, cooperative=None)),
            },
            payoffs={"A": 1.0, "B": -1.0},
        )
        for i in range(5)
    ]
    m = MatchResult(spec=_spec(game="matching_pennies"), rounds=rounds, manifest={})
    assert locked_in(m) is None
    assert coop_endstate(m) is None


# --------------------------------------------------------------------------- #
# welfare normalization
# --------------------------------------------------------------------------- #
def test_welfare_mutual_coop_is_one():
    # joint = 6, floor = 2, opt = 6 -> W = (6-2)/(6-2) = 1.0
    m = _all_coop_match(5)
    assert welfare_endstate(m) == pytest.approx(1.0)


def test_welfare_mutual_defect_is_zero():
    # joint = 2 = floor -> W = 0.0
    m = _all_defect_match(5)
    assert welfare_endstate(m) == pytest.approx(0.0)


def test_welfare_intermediate_and_clip():
    # one coop one defect: joint = 0+5 = 5 -> W = (5-2)/(6-2) = 0.75
    m = _ipd_match([(True, False)] * 5)
    assert welfare_endstate(m) == pytest.approx(0.75)


def test_welfare_none_without_benchmarks():
    m = _all_coop_match(5, bench={})
    assert welfare_endstate(m) is None


# --------------------------------------------------------------------------- #
# collusion index K
# --------------------------------------------------------------------------- #
def test_K_competitive_is_zero():
    # price == p_competitive (10) -> K = 0
    m = _market_match([10.0] * 6)
    assert collusion_endstate(m) == pytest.approx(0.0)


def test_K_monopoly_is_one():
    # price == p_monopoly (20) -> K = 1
    m = _market_match([20.0] * 6)
    assert collusion_endstate(m) == pytest.approx(1.0)


def test_K_halfway():
    # price 15 -> K = (15-10)/(20-10) = 0.5
    m = _market_match([15.0] * 6)
    assert collusion_endstate(m) == pytest.approx(0.5)


def test_K_none_for_non_market_game():
    m = _all_coop_match(5)  # ipd, no market benchmarks
    assert collusion_endstate(m) is None


# --------------------------------------------------------------------------- #
# convergence / promises / refusals
# --------------------------------------------------------------------------- #
def test_convergence_tau_stable_series():
    series = [0.0, 0.5, 1.0, 1.0, 1.0, 1.0]
    tau = convergence_tau(series, eps=0.1, window=3)
    assert tau == 2  # window [1.0,1.0,1.0] starting at index 2


def test_convergence_tau_never():
    series = [0.0, 1.0, 0.0, 1.0, 0.0, 1.0]
    assert convergence_tau(series, eps=0.1, window=3) is None


def test_promise_keeping_rate():
    # round0: promise + cooperated (kept); round1: promise + defected (broken)
    rounds = [
        _ipd_round(0, True, True, a_promise=True),
        _ipd_round(1, False, True, a_promise=True),
        _ipd_round(2, True, True, a_promise=None),  # no promise -> ignored
    ]
    m = MatchResult(spec=_spec(), rounds=rounds, manifest={"benchmarks": IPD_BENCH})
    assert promise_keeping_rate(m) == pytest.approx(0.5)


def test_promise_keeping_none_without_promises():
    m = _all_coop_match(5)
    assert promise_keeping_rate(m) is None


def test_refusal_rates():
    rounds = [
        _ipd_round(0, True, True, refusal_a=RefusalCode.CLEAN),
        _ipd_round(1, True, True, refusal_a=RefusalCode.REFUSAL),
        _ipd_round(2, True, True, refusal_a=RefusalCode.REPAIRED),
        _ipd_round(3, True, True, refusal_a=RefusalCode.OFF_TASK),
    ]
    m = MatchResult(spec=_spec(), rounds=rounds, manifest={"benchmarks": IPD_BENCH})
    rr = refusal_rates(m)
    # 8 responses (4 rounds x 2 seats); seat A has 3 of 4 in the refusal family
    assert rr["n_responses"] == 8
    assert rr["overall"] == pytest.approx(3 / 8)
    assert rr["refusal_only"] == pytest.approx(1 / 8)
    assert rr["per_seat"]["A"]["overall"] == pytest.approx(3 / 4)
    assert rr["per_seat"]["A"]["refusal_only"] == pytest.approx(1 / 4)
    assert rr["per_seat"]["B"]["overall"] == 0.0


# --------------------------------------------------------------------------- #
# Wilson interval (known values) and lock-in proportion
# --------------------------------------------------------------------------- #
def test_wilson_interval_15_of_20():
    # 15/20 = 0.75; Wilson 95% CI (z=1.96) is approx (0.5313, 0.8881),
    # matching scipy.stats.binomtest(...).proportion_ci(method="wilson").
    lo, hi = wilson_interval(15, 20, z=1.96)
    assert lo == pytest.approx(0.5313, abs=1e-3)
    assert hi == pytest.approx(0.8881, abs=1e-3)


def test_wilson_interval_bounds():
    assert wilson_interval(0, 0) == (0.0, 1.0)
    lo, hi = wilson_interval(0, 20)
    assert lo == 0.0
    lo, hi = wilson_interval(20, 20)
    assert hi == 1.0


def test_lockin_proportion():
    locked = [_all_coop_match(8) for _ in range(15)]
    not_locked = [_all_defect_match(8) for _ in range(5)]
    lp = lockin_proportion(locked + not_locked)
    assert lp["n"] == 20
    assert lp["k_locked"] == 15
    assert lp["proportion"] == pytest.approx(0.75)
    assert lp["wilson_lo"] == pytest.approx(0.5313, abs=1e-3)
    assert lp["wilson_hi"] == pytest.approx(0.8881, abs=1e-3)


# --------------------------------------------------------------------------- #
# bootstrap / tost / power
# --------------------------------------------------------------------------- #
def test_bootstrap_ci_brackets_mean():
    vals = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    lo, hi = bootstrap_ci(vals, n=2000, seed=1)
    assert lo < sum(vals) / len(vals) < hi


def test_tost_equivalence_equivalent():
    a = [0.50, 0.52, 0.48, 0.51, 0.49, 0.50]
    b = [0.50, 0.49, 0.51, 0.50, 0.52, 0.48]
    res = tost_equivalence(a, b, bound=0.1)
    assert res["equivalent"] is True
    assert res["bound"] == 0.1


def test_tost_equivalence_not_equivalent():
    a = [0.90, 0.92, 0.88, 0.91]
    b = [0.10, 0.12, 0.08, 0.11]
    res = tost_equivalence(a, b, bound=0.1)
    assert res["equivalent"] is False


def test_power_for_proportions():
    n = power_for_proportions(0.0, 0.5, alpha=0.05, power=0.8)
    assert isinstance(n, int) and 0 < n < 40


# --------------------------------------------------------------------------- #
# covert diagnostics
# --------------------------------------------------------------------------- #
def test_mi_independent_near_zero():
    rng = __import__("random").Random(0)
    x = [rng.randint(0, 1) for _ in range(200)]
    y = [rng.randint(0, 1) for _ in range(200)]
    mi = mutual_information_bias_corrected(x, y)
    assert mi < 0.1  # bias-corrected -> near zero for independent streams


def test_mi_perfectly_dependent_positive():
    x = [i % 2 for i in range(200)]
    y = list(x)
    mi = mutual_information_bias_corrected(x, y)
    assert mi > 0.9  # ~1 bit for a balanced copied binary variable


def test_covert_surplus():
    assert covert_surplus(0.8, 0.3) == pytest.approx(0.5)


def test_shuffled_baseline_keys():
    import random as _r

    res = shuffled_baseline(["a", "a", "b", "c", "a", "b"], rng=_r.Random(0), n=200)
    assert set(res) == {"observed", "baseline_mean", "baseline_std", "p_value", "z"}
    assert 0.0 <= res["p_value"] <= 1.0


# --------------------------------------------------------------------------- #
# summarize_match / attach_metrics
# --------------------------------------------------------------------------- #
def test_summarize_match_keys_and_values():
    m = _all_coop_match(10)
    s = summarize_match(m)
    assert s["coop_endstate"] == 1.0
    assert s["locked_in"] is True
    assert s["welfare_endstate"] == pytest.approx(1.0)
    assert s["K_endstate"] is None
    assert s["channel"] == "L3_private"
    assert json.dumps(s, default=str)  # JSON-serializable


def test_attach_metrics_populates_result():
    m = _all_coop_match(10)
    attach_metrics(m)
    assert m.metrics["coop_endstate"] == 1.0
    assert "compression_ratio" in m.metrics  # message metrics merged in


# --------------------------------------------------------------------------- #
# cell_summary contract
# --------------------------------------------------------------------------- #
CELL_SUMMARY_KEYS = {
    "cell_id",
    "n_matches",
    "channel",
    "game",
    "lockin_proportion",
    "wilson_lo",
    "wilson_hi",
    "coop_endstate_mean",
    "coop_ci_lo",
    "coop_ci_hi",
    "K_mean",
    "K_ci_lo",
    "K_ci_hi",
    "refusal_rate",
    "is_market_game",
}


def test_cell_summary_key_contract():
    results = [_all_coop_match(8) for _ in range(10)]
    cs = cell_summary(results)
    assert set(cs) == CELL_SUMMARY_KEYS
    assert cs["n_matches"] == 10
    assert cs["lockin_proportion"] == pytest.approx(1.0)
    assert cs["coop_endstate_mean"] == pytest.approx(1.0)
    assert cs["K_mean"] is None  # ipd, not a market game
    assert cs["is_market_game"] is False


def test_cell_summary_market():
    results = [_market_match([15.0] * 8) for _ in range(8)]
    cs = cell_summary(results)
    assert cs["is_market_game"] is True
    assert cs["K_mean"] == pytest.approx(0.5)
    assert cs["K_ci_lo"] is not None


# --------------------------------------------------------------------------- #
# save_run definition-of-done
# --------------------------------------------------------------------------- #
def test_save_run_writes_three_files(tmp_path):
    results = [_all_coop_match(8, seed=i) for i in range(5)]
    # attach a model-comparability row so the manifest carries it (§5)
    for r in results:
        r.manifest["models"] = [
            {"id": "qwen", "origin": "chinese", "param_count": "72B"},
            {"id": "llama", "origin": "western", "param_count": "70B"},
        ]
    run_dir = save_run(results, exp_id="A1", run_dir=tmp_path / "run")

    manifest_p = run_dir / "manifest.json"
    matches_p = run_dir / "matches.jsonl"
    metrics_p = run_dir / "metrics.csv"
    assert manifest_p.exists() and matches_p.exists() and metrics_p.exists()

    manifest = json.loads(manifest_p.read_text())
    assert manifest["n_matches"] == 5
    assert len(manifest["model_comparability"]) == 2

    lines = matches_p.read_text().strip().splitlines()
    assert len(lines) == 5
    first = json.loads(lines[0])
    assert first["spec"]["experiment_id"] == "A1"

    with metrics_p.open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 5
    assert rows[0]["coop_endstate"] == "1.0"
    assert rows[0]["locked_in"] == "1"  # bool serialized as int


def test_save_run_auto_dir(tmp_path, monkeypatch):
    import rival_arena.config as cfg

    monkeypatch.setattr(cfg, "RUNS_DIR", tmp_path / "runs")
    results = [_all_coop_match(8, seed=i) for i in range(3)]
    run_dir = save_run(results, exp_id="A1")
    assert run_dir.exists()
    assert (run_dir / "metrics.csv").exists()
    assert run_dir.parent.parent.name == "runs"
