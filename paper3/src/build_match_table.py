"""Build the per-match analysis table from master_long.csv.

One row per match (experiment_id, cell_id, seed) with:
  - design factors (game, channel, demand_spec, pair, experiment)
  - outcome: lock-in (IPD/PD-like) and K (Bertrand)
  - mediator: conditional-punishment content measured on that match's messages
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from conditional import score_series, CHANNEL_CAPACITY  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "results" / "master_long.csv"
OUT = Path(__file__).resolve().parents[1] / "results"

# Bertrand K normalisation benchmarks, per demand spec (from the game definitions).
BENCHMARKS = {
    "canonical": dict(p_comp=1.6, p_mono=2.0),
    "novel": dict(p_comp=10.0, p_mono=24.0),
}

# Pairs that are scaffolding, not experimental subjects.
SMOKE_PAIRS = {"llama-8b+qwen-7b", "qwen-7b+llama-8b"}
# Classical (non-LLM) opponents used for the A5 validity gate.
CLASSICAL = {"tit_for_tat", "grim", "pavlov", "always_defect", "always_cooperate", "random"}

LOCKIN_CUT = 0.8


def _is_llm_pair(p: str) -> bool:
    if not isinstance(p, str) or p in SMOKE_PAIRS:
        return False
    return not any(c in p.split("+") for c in CLASSICAL)


def load() -> pd.DataFrame:
    df = pd.read_csv(MASTER, low_memory=False)
    df = df[df.pair.map(_is_llm_pair)].copy()
    # Bertrand's real demand axis is demand_spec; `familiarity` is not populated for it.
    df["spec"] = df["demand_spec"].fillna(df["familiarity"])
    # Repo convention: refusals are coded as outcomes; API/transport errors are
    # excluded from behavioural metrics and tracked separately.
    df["is_refusal"] = (df["refusal"] == "refusal").astype(float)
    df["is_api_error"] = (df["refusal"] == "api_error").astype(float)
    df.loc[df["is_api_error"] == 1, ["cooperative", "price"]] = np.nan
    return df


def build(df: pd.DataFrame) -> pd.DataFrame:
    scores = score_series(df["message"])
    df = pd.concat([df, scores], axis=1)

    key = ["experiment_id", "cell_id", "seed"]

    agg = df.groupby(key, dropna=False).agg(
        game=("game", "first"),
        channel=("channel", "first"),
        spec=("spec", "first"),
        pair=("pair", "first"),
        framing=("framing", "first"),
        n_rows=("round_index", "size"),
        n_rounds=("round_index", lambda s: int(s.max()) + 1),
        coop_mean=("cooperative", "mean"),
        price_mean=("price", "mean"),
        price_last=("price", lambda s: s.dropna().iloc[-1] if s.notna().any() else np.nan),
        refusal_rate=("is_refusal", "mean"),
        api_error_rate=("is_api_error", "mean"),
        # mediator: fraction of this match's messages carrying each component
        msgs=("has_message", "sum"),
        rule_frac=("rule", "mean"),
        full_rule_frac=("full_rule", "mean"),
        trigger_frac=("trigger", "mean"),
        conseq_frac=("consequence", "mean"),
        target_frac=("target", "mean"),
        intention_frac=("intention", "mean"),
        msg_len=("message_len", "mean"),
    ).reset_index()

    # message-fraction columns are over ALL rows; renormalise to rows that had a message
    n_msg = df.groupby(key, dropna=False)["has_message"].sum().reset_index(name="_nmsg")
    agg = agg.merge(n_msg, on=key, how="left")
    for c in ["rule_frac", "full_rule_frac", "trigger_frac", "conseq_frac",
              "target_frac", "intention_frac"]:
        agg[c] = np.where(agg["_nmsg"] > 0, agg[c] * agg["n_rows"] / agg["_nmsg"], 0.0)
    agg = agg.drop(columns=["_nmsg"])

    # any-rule: did this match contain at least one contingent punishment rule?
    any_rule = df.groupby(key, dropna=False)["rule"].max().reset_index(name="any_rule")
    agg = agg.merge(any_rule, on=key, how="left")

    agg["lockin"] = (agg["coop_mean"] > LOCKIN_CUT).astype(float)
    agg.loc[agg["coop_mean"].isna(), "lockin"] = np.nan

    # Bertrand collusion index
    def kval(row):
        if row["game"] != "bertrand" or pd.isna(row["price_mean"]):
            return np.nan
        b = BENCHMARKS.get(row["spec"])
        if b is None:
            return np.nan
        return (row["price_mean"] - b["p_comp"]) / (b["p_mono"] - b["p_comp"])

    agg["K"] = agg.apply(kval, axis=1)
    agg["capacity"] = agg["channel"].map(CHANNEL_CAPACITY)
    agg["has_channel"] = (agg["channel"] != "L0_none").astype(int)
    agg["free_text"] = agg["channel"].isin(["L2_observed", "L3_private"]).astype(int)
    return agg


def main() -> None:
    df = load()
    agg = build(df)
    OUT.mkdir(parents=True, exist_ok=True)
    agg.to_csv(OUT / "matches.csv", index=False)
    print(f"wrote {OUT / 'matches.csv'}  ({len(agg)} matches)")
    print()
    print(agg.groupby("channel")[["lockin", "K", "rule_frac", "any_rule"]].mean())
    print()
    print("matches per game:")
    print(agg.game.value_counts())


if __name__ == "__main__":
    main()
