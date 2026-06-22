"""C1 — authorship vs content ablation in the IPD (the promise-keeping cliff).

The project's strongest result is the "promise-keeping cliff": a fixed-MENU
intention signal (L1) collapses cooperation, while FREE-TEXT (L2) restores it.
Open question — what is the active ingredient?

  (a) AUTHORSHIP: the agent composing its own promise creates commitment, or
  (b) CONTENT:    free text simply carries more than a menu token.

We isolate the two with a clean 3-point ladder (IPD canonical, same_origin_cn,
matching A1's pair, continuation_prob 0.97):

  * selected   = L1_SIGNAL: pick "I intend to cooperate."/"I intend to defect."
                 from the menu.            [authored = NO , content = low ]
  * restricted = L2_OBSERVED + message_restriction="action_only": free text, but
                 the agent may state ONLY its own intended action this round, in
                 its own words, nothing else. [authored = YES, content = low ]
  * free       = L2_OBSERVED, normal free text. [authored = YES, content = high]

Logic:
  selected -> restricted isolates AUTHORSHIP (content held low).
  restricted -> free      isolates CONTENT   (authorship held constant).

If `restricted` behaves like `free` (cooperation recovers, promises kept) ->
AUTHORSHIP is the lever. If it behaves like `selected` (collapse) -> CONTENT is
the lever. The promise-keeping contrast across the 3 conditions is the key output.
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.metrics.stats import wilson_interval
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from rival_arena import config

from .common import finalize, pair_players, resolve_pair, run_specs

# (condition name, channel, message_restriction) — the 3-point ladder.
CONDITIONS: list[tuple[str, ChannelLevel, str | None]] = [
    ("selected", ChannelLevel.L1_SIGNAL, None),       # authored=NO , content=low
    ("restricted", ChannelLevel.L2_OBSERVED, "action_only"),  # authored=YES, content=low
    ("free", ChannelLevel.L2_OBSERVED, None),         # authored=YES, content=high
]


def build_specs(
    pair="same_origin_cn",
    seeds: int = 20,
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,                 # use a disjoint range for confirmatory runs (P4)
) -> list[MatchSpec]:
    model_ids = resolve_pair(pair)
    pairname = pair if isinstance(pair, str) else "x".join(model_ids)
    specs: list[MatchSpec] = []
    for cond, lvl, restriction in CONDITIONS:
        for s in range(seed_offset, seed_offset + seeds):
            specs.append(MatchSpec(
                experiment_id="C1",
                cell_id=f"C1/{cond}/{pairname}",
                game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                      "max_rounds": max_rounds}, familiarity="canonical"),
                channel=lvl,
                epistemic=default_epistemic(lvl),
                players=pair_players(model_ids, s),
                seed=s,
                token_budget=token_budget,
                history_window=DEFAULT_HISTORY_WINDOW,
                framing=framing,
                message_restriction=restriction,
            ))
    return specs


def _cond_of(cell_id: str) -> str:
    # cell_id == "C1/<cond>/<pair>"
    parts = cell_id.split("/")
    return parts[1] if len(parts) > 1 else cell_id


def _order_key(cond: str) -> int:
    order = {name: i for i, (name, _, _) in enumerate(CONDITIONS)}
    return order.get(cond, len(order))


def _condition_stats(results) -> dict[str, dict]:
    """Aggregate per-condition: lock-in (k/n + Wilson CI), mean coop end-state,
    and promise-keeping rate (mean over matches with a defined rate)."""
    from rival_arena.metrics.core import (
        coop_endstate, locked_in, promise_keeping_rate,
    )
    by_cond: dict[str, list] = {}
    for r in results:
        by_cond.setdefault(_cond_of(r.spec.cell_id), []).append(r)

    out: dict[str, dict] = {}
    for cond, rs in by_cond.items():
        flags = [f for f in (locked_in(r) for r in rs) if f is not None]
        n = len(flags)
        k = sum(1 for f in flags if f)
        prop = (k / n) if n else None
        lo, hi = wilson_interval(k, n)

        coop_vals = [c for c in (coop_endstate(r) for r in rs) if c is not None]
        coop_mean = (sum(coop_vals) / len(coop_vals)) if coop_vals else None

        pk_vals = [p for p in (promise_keeping_rate(r) for r in rs) if p is not None]
        pk_mean = (sum(pk_vals) / len(pk_vals)) if pk_vals else None

        out[cond] = {
            "n": n, "k_locked": k, "lockin": prop, "wilson_lo": lo, "wilson_hi": hi,
            "coop_mean": coop_mean, "n_matches": len(rs),
            "promise_keeping_rate": pk_mean, "n_promise_matches": len(pk_vals),
        }
    return out


def _fmt(v, spec=".2f"):
    return format(v, spec) if isinstance(v, (int, float)) else " n/a"


def _print_ablation_table(stats: dict[str, dict]) -> None:
    print("\n===== C1: authorship vs content ablation (IPD) =====")
    header = (f"  {'condition':<12} {'authored/content':<18} "
              f"{'lock-in [Wilson CI]':<26} {'mean C':>7}  {'promises kept':>14}")
    print(header)
    print("  " + "-" * (len(header) - 2))
    labels = {
        "selected": "no / low",
        "restricted": "yes / low",
        "free": "yes / high",
    }
    for cond in sorted(stats, key=_order_key):
        s = stats[cond]
        lockin = (f"{_fmt(s['lockin'])} "
                  f"[{_fmt(s['wilson_lo'])},{_fmt(s['wilson_hi'])}] "
                  f"(k={s['k_locked']}/{s['n']})")
        pk = (f"{_fmt(s['promise_keeping_rate'])} "
              f"(m={s['n_promise_matches']})")
        print(f"  {cond:<12} {labels.get(cond, ''):<18} "
              f"{lockin:<26} {_fmt(s['coop_mean']):>7}  {pk:>14}")
    print("\n  Read: selected->restricted isolates AUTHORSHIP; "
          "restricted->free isolates CONTENT.")


def figures(run_dir, summaries, results):
    try:
        from rival_arena.viz import figures as F
        cs = list(summaries)
        cs.sort(key=lambda s: _order_key(_cond_of(s["cell_id"])))
        out = []
        if cs:
            out.append(F.lockin_bar(cs, run_dir / "c1_lockin.png",
                                    title="C1 authorship vs content — IPD"))
        return out
    except Exception as e:  # figures must never sink a completed run
        print(f"[C1] figure generation failed: {e}")
        return []


def main(pair="same_origin_cn", seeds=20, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pair=pair, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[C1] {len(specs)} matches: {len(CONDITIONS)} conditions x {seeds} seeds, "
          f"pair={pair}, seed_offset={seed_offset}, mock={mock}")

    # checkpointed run (host-agnostic resume), then finalize — same pipeline as
    # run_and_finalize, but we keep `results` for the per-condition ablation table.
    ckpt_dir = config.RUNS_DIR / "C1" / "_checkpoint"
    results = run_specs(specs, mock=mock, checkpoint_dir=ckpt_dir, resume=resume)
    run_dir = finalize(results, "C1", figure_fn=figures)
    if ckpt_dir.exists():
        for p in ckpt_dir.glob("*.pkl"):
            p.unlink()

    stats = _condition_stats(results)
    _print_ablation_table(stats)
    return run_dir
