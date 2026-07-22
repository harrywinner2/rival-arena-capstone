import pytest

from l4_arena.arena import ArenaConfig, cell_id, summarize_bertrand, summarize_ipd


def ipd_round(a, b):
    return {
        "A": {"action": a, "action_value": 1 if a == "COOPERATE" else 0},
        "B": {"action": b, "action_value": 1 if b == "COOPERATE" else 0},
    }


def test_ipd_summary_and_cell_validation():
    rounds = [ipd_round("COOPERATE", "COOPERATE") for _ in range(5)]
    assert summarize_ipd(rounds)["lock_in"] is True
    assert cell_id("ipd", "trained", 4) == "ipd/trained/seed-4"
    with pytest.raises(ValueError):
        cell_id("bad", "trained", 4)


def test_bertrand_summary():
    rounds = [
        {
            "A": {"action": "PRICE", "action_value": 18.0},
            "B": {"action": "PRICE", "action_value": 18.0},
        }
        for _ in range(5)
    ]
    result = summarize_bertrand(rounds, p_competitive=10.0, p_monopoly=20.0)
    assert result["collusion_index"] == pytest.approx(0.8)
    assert result["supracompetitive"] is True


def test_arena_config_fingerprint_is_stable():
    config = ArenaConfig("m", 2, 3, 4, ("none",), ("ipd",), 5, 6)
    assert config.fingerprint() == config.fingerprint()
