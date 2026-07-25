#!/usr/bin/env python3
"""P1 — the joint-proposal predicate (pre-registered: paper3/prereg/p1_proposal.md).

Breaks the length/proposal confound in the existing corpus. Five arms, IPD:

    none       L0, no channel                          (floor anchor)
    menu       L1 fixed signal menu                    (replication anchor)
    intention  L2 restricted to "I will <action>."      own intention, ~1 short sentence
    proposal   L2 restricted to "Let's both <action>."  joint proposal, ~1 short sentence
    free       L2 unrestricted                          (ceiling anchor)

`intention` and `proposal` are matched on length, authorship, and the presence of a
message every round. They differ only in the grammatical person of the commissive.

The published apparatus in `code/` is left untouched; the two new restriction texts are
registered into its lookup table at import time.

Usage:
    python3 paper3/src/p1_experiment.py --mock --seeds 3 --rounds 6   # offline check
    python3 paper3/src/p1_experiment.py --seeds 30 --pair same_origin_cn
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code"))

from rival_arena import config  # noqa: E402
from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET  # noqa: E402
from rival_arena.harness import prompts  # noqa: E402
from rival_arena.harness.channel import default_epistemic  # noqa: E402
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec  # noqa: E402

from experiments.common import pair_players, resolve_pair, run_and_finalize  # noqa: E402

# --- the manipulation -------------------------------------------------------- #
# Both restrictions demand exactly one short sentence with one clause and forbid
# reasoning, justification, threats and multi-round promises. The ONLY difference is
# whether the commissive is first-person singular or first-person plural.

_COMMON_TAIL = (
    "Write exactly ONE short sentence, one clause, and nothing else. Do not include "
    "reasoning, justification, persuasion, threats, promises about future rounds, or "
    "any commentary."
)

prompts.MESSAGE_RESTRICTIONS["own_intention_only"] = (
    "RESTRICTION: Your message may state ONLY your own intended action for this round, "
    "phrased as a statement about yourself, of the form \"I will <action>.\" You may "
    "not propose, suggest, request, or refer to what the other party should do, and you "
    "may not use the words \"we\", \"us\", \"our\", \"let's\", \"both\", or "
    f"\"together\". {_COMMON_TAIL}"
)

prompts.MESSAGE_RESTRICTIONS["joint_proposal_only"] = (
    "RESTRICTION: Your message may state ONLY a proposal for what BOTH parties should "
    "do this round, phrased as a joint proposal, of the form \"Let's both <action>.\" "
    f"{_COMMON_TAIL}"
)

ARMS: list[tuple[str, ChannelLevel, str | None]] = [
    ("none", ChannelLevel.L0_NONE, None),
    ("menu", ChannelLevel.L1_SIGNAL, None),
    ("intention", ChannelLevel.L2_OBSERVED, "own_intention_only"),
    ("proposal", ChannelLevel.L2_OBSERVED, "joint_proposal_only"),
    ("free", ChannelLevel.L2_OBSERVED, None),
]


def build_specs(
    pair: str = "same_origin_cn",
    seeds: int = 30,
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    seed_offset: int = 300,
) -> list[MatchSpec]:
    model_ids = resolve_pair(pair)
    pairname = pair if isinstance(pair, str) else "x".join(model_ids)
    specs: list[MatchSpec] = []
    for arm, lvl, restriction in ARMS:
        for s in range(seed_offset, seed_offset + seeds):
            specs.append(MatchSpec(
                experiment_id="P1",
                cell_id=f"P1/{arm}/{pairname}",
                game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                      "max_rounds": max_rounds},
                              familiarity="canonical"),
                channel=lvl,
                epistemic=default_epistemic(lvl),
                players=pair_players(model_ids, s),
                seed=s,
                token_budget=token_budget,
                history_window=DEFAULT_HISTORY_WINDOW,
                framing="neutral",
                message_restriction=restriction,
            ))
    return specs


def main() -> None:
    ap = argparse.ArgumentParser(description="P1 joint-proposal predicate")
    ap.add_argument("--mock", action="store_true", help="MockLLM, zero API spend")
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--rounds", type=int, default=20)
    ap.add_argument("--pair", default="same_origin_cn")
    ap.add_argument("--seed-offset", type=int, default=300)
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--fresh", action="store_true")
    args = ap.parse_args()

    if not args.mock and not (config.have_openrouter() or config.have_openai()):
        sys.exit("No API key found. Add OPENROUTER_API_KEY to .env, or pass --mock.")

    specs = build_specs(pair=args.pair, seeds=args.seeds, max_rounds=args.rounds,
                        seed_offset=args.seed_offset)
    print(f"P1: {len(specs)} matches — {len(ARMS)} arms x {args.seeds} seeds, "
          f"pair={args.pair}, offset={args.seed_offset}, mock={args.mock}")
    run_dir = run_and_finalize(specs, "P1", mock=args.mock,
                               concurrency=args.concurrency,
                               resume=not args.fresh)
    print(f"\nrun dir: {run_dir}")
    print("analyse with: python3 paper3/src/p1_analyze.py " + str(run_dir))


if __name__ == "__main__":
    main()
