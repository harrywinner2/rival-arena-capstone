"""B4 — prompt-phrasing sensitivity of collusion.

B1's Bertrand pricing game, with the PAIR and CHANNEL held fixed. We sweep only
the SELLER-GOAL INSTRUCTION PHRASING across a graded set (innocuous -> suggestive)
to find which innocuous wording raises the collusion index K — replicating and
extending Fish et al.: innocuous phrasing is load-bearing [R1].

Channel is fixed at L2_observed (free text, told observed) so that ONLY phrasing
varies, never bandwidth. Demand spec is fixed to the novel floor (P3): canonical
collusion might be recalled rather than discovered, so we test the conservative
case. Each variant substitutes exactly one sentence — the seller-goal line — via
the prompts.py phrasing hook (spec.prompt_variant); variant=None reproduces the
neutral mainline verbatim. The exact strings live in
``rival_arena.harness.prompts.PROMPT_VARIANTS`` (single source of truth).

Primary measure: collusion index K as a function of prompt phrasing — the
phrasing -> K ranking is printed per cell.
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.harness.prompts import PROMPT_VARIANTS
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from rival_arena import config
from .common import finalize, pair_players, resolve_pair, run_specs

# Graded phrasing set, innocuous -> suggestive. Keys index PROMPT_VARIANTS, which
# holds the EXACT instruction text substituted for the seller-goal line. "profit"
# is the mainline-equivalent control.
VARIANTS = ("profit", "longrun", "savvy", "avoid_price_wars")

# Hold the channel fixed: this experiment varies phrasing, not bandwidth.
FIXED_CHANNEL = ChannelLevel.L2_OBSERVED


def build_specs(
    pair="cross_origin",
    seeds: int = 8,
    variants=VARIANTS,
    demand_specs=("novel",),              # novel = the defensible floor (P3)
    channel: ChannelLevel = FIXED_CHANNEL,
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    n_prices: int = 11,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    seed_offset: int = 0,                 # disjoint range for confirmatory runs (P4)
) -> list[MatchSpec]:
    model_ids = resolve_pair(pair)
    pairname = pair if isinstance(pair, str) else "x".join(model_ids)
    specs: list[MatchSpec] = []
    for demand in demand_specs:
        for variant in variants:
            for s in range(seed_offset, seed_offset + seeds):
                specs.append(MatchSpec(
                    experiment_id="B4",
                    cell_id=f"B4/{variant}/{channel.value}/{pairname}",
                    game=GameSpec("bertrand", {
                        "demand_spec": demand, "n_prices": n_prices,
                        "continuation_prob": continuation_prob, "max_rounds": max_rounds,
                    }),
                    channel=channel,
                    epistemic=default_epistemic(channel),
                    players=pair_players(model_ids, s),
                    seed=s,
                    token_budget=token_budget,
                    history_window=DEFAULT_HISTORY_WINDOW,
                    prompt_variant=variant,          # B4 phrasing hook
                    notes=f"B4 phrasing variant={variant}",
                ))
    return specs


def figures(run_dir, summaries, results):
    out = []
    try:
        from rival_arena.viz import figures as F
        out.append(F.refusal_panel(summaries, run_dir / "b4_refusals.png"))
    except Exception as e:  # figures must never sink a completed run
        print(f"[B4] figure generation skipped: {e}")
    return out


def _print_k_ranking(results):
    """Phrasing -> K ranking: K_mean per variant, sorted ascending so the wording
    that most raises collusion lands at the bottom (the headline of B4)."""
    from rival_arena.metrics import cell_summary
    by_variant: dict[str, list] = {}
    for r in results:
        v = getattr(r.spec, "prompt_variant", None) or "default"
        by_variant.setdefault(v, []).append(r)
    rows = []
    for v, rs in by_variant.items():
        rows.append((v, cell_summary(rs, cell_id=f"B4/{v}")))
    rows.sort(key=lambda kv: (kv[1]["K_mean"] is None, kv[1]["K_mean"] or 0.0))
    print("\n===== B4: phrasing -> K ranking (K_mean per variant, ascending) =====")
    for v, s in rows:
        km = s["K_mean"]
        kstr = f"{km:.3f}" if isinstance(km, (int, float)) else "  n/a"
        print(f"  {v:<18} n={s['n_matches']:>3}  K_mean={kstr}  "
              f"refusal={s.get('refusal_rate')}")
    return rows


def main(pair="cross_origin", seeds=8, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pair=pair, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[B4] {len(specs)} matches: {len(VARIANTS)} phrasing variants "
          f"x 1 channel ({FIXED_CHANNEL.value}) x {seeds} seeds, pair={pair}, "
          f"mock={mock}")
    ckpt_dir = config.RUNS_DIR / "B4" / "_checkpoint"
    results = run_specs(specs, mock=mock, checkpoint_dir=ckpt_dir, resume=resume)
    run_dir = finalize(results, "B4", figure_fn=figures)
    if ckpt_dir.exists():
        for p in ckpt_dir.glob("*.pkl"):
            p.unlink()
    _print_k_ranking(results)
    return run_dir
