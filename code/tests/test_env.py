"""Offline, deterministic tests for the env/ workstream (no network).

Covers: IPD payoff cells + benchmarks + parse robustness + familiarity/scaling,
Bertrand benchmark sanity + K computability, Matching Pennies zero-sum, and the
classical Axelrod strategies over scripted histories.
"""

from __future__ import annotations

import random

import pytest

from rival_arena.env import get_game, get_strategy
from rival_arena.env.base import GAME_REGISTRY, STRATEGY_REGISTRY
from rival_arena.env.ipd import coop_action, defect_action


# --------------------------------------------------------------------------- #
# Registration
# --------------------------------------------------------------------------- #
def test_games_registered():
    assert {"ipd", "bertrand", "matching_pennies"} <= set(GAME_REGISTRY)


def test_strategies_registered():
    assert {
        "tit_for_tat", "grim", "pavlov", "random",
        "always_defect", "always_cooperate",
    } <= set(STRATEGY_REGISTRY)


# --------------------------------------------------------------------------- #
# IPD payoffs — all four cells
# --------------------------------------------------------------------------- #
def test_ipd_all_four_cells():
    g = get_game("ipd")
    C, D = coop_action(), defect_action()
    # T=5, R=3, P=1, S=0
    assert g.payoffs({"A": C, "B": C}) == {"A": 3.0, "B": 3.0}
    assert g.payoffs({"A": D, "B": C}) == {"A": 5.0, "B": 0.0}
    assert g.payoffs({"A": C, "B": D}) == {"A": 0.0, "B": 5.0}
    assert g.payoffs({"A": D, "B": D}) == {"A": 1.0, "B": 1.0}


def test_ipd_cooperate_is_first_in_menu():
    g = get_game("ipd")
    menu = g.action_menu("A")
    assert menu[0].cooperative is True  # MockLLM picks menu[0] as cooperative


def test_ipd_benchmarks():
    b = get_game("ipd").benchmarks()
    assert b["floor"] == 2.0          # 2*P
    assert b["social_optimum"] == 6.0  # 2*R
    assert b["floor"] < b["social_optimum"]


def test_ipd_temptation_scale_keeps_dilemma():
    for scale in (0.5, 1.0, 2.0, 4.0):
        b = get_game("ipd", {"temptation_scale": scale}).benchmarks()
        T, R, P, S = b["T"], b["R"], b["P"], b["S"]
        assert T > R > P > S            # ordinal social dilemma
        assert 2 * R > T + S            # mutual coop beats alternating exploit


def test_ipd_temptation_scale_widens_gap():
    g1 = get_game("ipd", {"temptation_scale": 1.0}).benchmarks()
    g4 = get_game("ipd", {"temptation_scale": 4.0}).benchmarks()
    assert (g4["T"] - g4["R"]) > (g1["T"] - g1["R"])


def test_ipd_novel_is_different_scale_but_still_dilemma():
    can = get_game("ipd", {}, "canonical").benchmarks()
    nov = get_game("ipd", {}, "novel").benchmarks()
    assert (nov["T"], nov["R"], nov["P"], nov["S"]) != (
        can["T"], can["R"], can["P"], can["S"]
    )
    assert nov["T"] > nov["R"] > nov["P"] > nov["S"]
    assert 2 * nov["R"] > nov["T"] + nov["S"]


def test_ipd_describe_honours_familiarity():
    canonical = get_game("ipd", {}, "canonical").describe_for_prompt("A")
    relabeled = get_game("ipd", {}, "relabeled").describe_for_prompt("A")
    assert "Prisoner" not in canonical and "prisoner" not in canonical
    assert "Option X" in relabeled


# --------------------------------------------------------------------------- #
# IPD parse_action — robustness incl. junk
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "text, expect_coop",
    [
        ("I will cooperate this round.", True),
        ("COOPERATE", True),
        ("My move: C", True),
        ("Let's defect.", False),
        ("D", False),
        ("I choose to DEFECT now", False),
    ],
)
def test_ipd_parse_clear(text, expect_coop):
    g = get_game("ipd")
    action = g.parse_action(text, "A")
    assert action is not None
    assert action.cooperative is expect_coop


@pytest.mark.parametrize(
    "junk",
    ["", "asdf qwerty", "I am not sure what to do", "cooperate or defect?"],
)
def test_ipd_parse_junk_returns_none(junk):
    assert get_game("ipd").parse_action(junk, "A") is None


def test_ipd_relabeled_parse_maps_back():
    g = get_game("ipd", {}, "relabeled")
    assert g.parse_action("I pick Option X", "A").cooperative is True
    assert g.parse_action("I pick Option Y", "A").cooperative is False


# --------------------------------------------------------------------------- #
# Bertrand — benchmarks + K computability (both specs)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("spec", ["canonical", "novel"])
def test_bertrand_benchmarks_ordered(spec):
    b = get_game("bertrand", {"demand_spec": spec}).benchmarks()
    assert b["p_monopoly"] > b["p_competitive"] >= b["marginal_cost"]
    assert b["p_competitive"] in b["price_grid"]
    assert b["p_monopoly"] in b["price_grid"]


@pytest.mark.parametrize("spec", ["canonical", "novel"])
def test_bertrand_K_computable(spec):
    g = get_game("bertrand", {"demand_spec": spec})
    b = g.benchmarks()
    p_comp, p_mono = b["p_competitive"], b["p_monopoly"]
    K = (p_mono - p_comp) / (p_mono - p_comp)  # full-monopoly price -> K == 1
    assert K == pytest.approx(1.0)
    # competitive price -> K == 0
    assert (p_comp - p_comp) / (p_mono - p_comp) == pytest.approx(0.0)


def test_bertrand_parse_snaps_to_grid():
    g = get_game("bertrand", {"demand_spec": "canonical"})
    a = g.parse_action("I'll set a price of 2.47 dollars", "A")
    assert a is not None and a.value in g.grid
    assert g.parse_action("no number here", "A") is None


def test_bertrand_lower_price_sells_more():
    g = get_game("bertrand", {"demand_spec": "novel"})
    grid = g.grid
    lo, hi = grid[1], grid[-1]
    a_low = next(x for x in g.action_menu("A") if x.value == lo)
    b_high = next(x for x in g.action_menu("B") if x.value == hi)
    pay = g.payoffs({"A": a_low, "B": b_high})
    assert pay["A"] > pay["B"]  # undercutter captures the market


# --------------------------------------------------------------------------- #
# Matching Pennies — zero-sum
# --------------------------------------------------------------------------- #
def test_matching_pennies_zero_sum():
    g = get_game("matching_pennies")
    H, T = g.action_menu("A")
    for a in (H, T):
        for b in (H, T):
            pay = g.payoffs({"A": a, "B": b})
            assert pay["A"] + pay["B"] == 0.0
    # A (matcher) wins on a match
    assert g.payoffs({"A": H, "B": H})["A"] == 1.0
    assert g.payoffs({"A": H, "B": T})["A"] == -1.0


def test_matching_pennies_no_coop_axis():
    g = get_game("matching_pennies")
    assert g.coop_axis is False
    assert g.is_cooperative(g.action_menu("A")[0]) is None
    b = g.benchmarks()
    assert b["floor"] == 0.0 and b["social_optimum"] == 0.0


# --------------------------------------------------------------------------- #
# Classical strategies over scripted histories
# --------------------------------------------------------------------------- #
def _round(a_coop: bool, b_coop: bool) -> dict:
    mk = lambda c: coop_action() if c else defect_action()
    return {"A": mk(a_coop), "B": mk(b_coop)}


def test_always_defect_and_cooperate():
    rng = random.Random(0)
    assert get_strategy("always_defect").act([], "A", rng).cooperative is False
    assert get_strategy("always_cooperate").act([], "A", rng).cooperative is True


def test_tit_for_tat():
    s = get_strategy("tit_for_tat")
    rng = random.Random(0)
    assert s.act([], "A", rng).cooperative is True  # cooperate first
    # opponent (B) defected last round -> TfT (A) defects
    assert s.act([_round(True, False)], "A", rng).cooperative is False
    # opponent cooperated last round -> TfT cooperates
    assert s.act([_round(False, True)], "A", rng).cooperative is True


def test_grim_triggers_forever():
    s = get_strategy("grim")
    rng = random.Random(0)
    assert s.act([], "A", rng).cooperative is True
    assert s.act([_round(True, True)], "A", rng).cooperative is True
    # once B defected, grim defects forever after
    hist = [_round(True, True), _round(True, False), _round(False, True)]
    assert s.act(hist, "A", rng).cooperative is False


def test_pavlov_win_stay_lose_shift():
    s = get_strategy("pavlov")
    rng = random.Random(0)
    assert s.act([], "A", rng).cooperative is True            # first move C
    # both cooperated (win) -> stay (cooperate)
    assert s.act([_round(True, True)], "A", rng).cooperative is True
    # both defected (mutual outcome = "win" in WSLS) -> stay (defect)
    assert s.act([_round(False, False)], "A", rng).cooperative is False
    # A cooperated, B defected (got suckered, lose) -> shift to defect
    assert s.act([_round(True, False)], "A", rng).cooperative is False
    # A defected, B cooperated (got temptation but mismatch, lose) -> shift to coop
    assert s.act([_round(False, True)], "A", rng).cooperative is True


def test_random_is_deterministic_given_seed():
    s = get_strategy("random")
    seq1 = [s.act([], "A", random.Random(42)).cooperative for _ in range(1)]
    seq2 = [s.act([], "A", random.Random(42)).cooperative for _ in range(1)]
    assert seq1 == seq2
    # over many draws with one rng, both actions appear
    rng = random.Random(7)
    draws = {s.act([], "A", rng).cooperative for _ in range(50)}
    assert draws == {True, False}
