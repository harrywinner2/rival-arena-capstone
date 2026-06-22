"""Run many experiments in parallel through ONE shared concurrency pool.

Running experiments as separate processes would each open its own semaphore and
collectively blow the provider rate limit. Instead we collect every experiment's
MatchSpecs, run them all through a single bounded pool (so total in-flight calls
are controlled and throughput is maximised), checkpoint globally, then finalize
each experiment separately into its own run dir + figures.

Profiles:
  * ``spine`` — the confirmatory A1 + B1 at N=20 on fresh seeds (100+).
  * ``wide``  — spine + A2 (regime) + A3 (origin sweep) + A4 (temptation) +
                multi-model A5: the data-rich program for free-form analysis.
  * ``pilot`` — tiny seeds across everything (cheap signal / smoke).
"""

from __future__ import annotations

from rival_arena import config
from rival_arena.metrics import save_run

from . import (a1_channel, a2_regime, a3_origin, a4_temptation, a5_baseline,
               b1_pricing)
from .common import finalize, run_specs


# --------------------------------------------------------------------------- #
# profiles -> list of {exp, specs, fig}
# --------------------------------------------------------------------------- #
def _spine(seeds=20, rounds=20):
    return [
        dict(exp="A1", fig=a1_channel.figures, specs=a1_channel.build_specs(
            pair="same_origin_cn", seeds=seeds, seed_offset=100, max_rounds=rounds)),
        dict(exp="B1", fig=b1_pricing.figures, specs=b1_pricing.build_specs(
            pair="cross_origin", seeds=seeds, seed_offset=100, max_rounds=rounds)),
    ]


def _wide(seeds=None, rounds=20):
    items = _spine(seeds=seeds or 20, rounds=rounds)
    items += [
        # H4 origin moderation: 5 pairs x ladder — the cross-origin hook + null
        dict(exp="A3", fig=a3_origin.figures, specs=a3_origin.build_specs(
            seeds=10, max_rounds=rounds)),
        # H2 regime contrast
        dict(exp="A2", fig=a2_regime.figures, specs=a2_regime.build_specs(
            seeds=10, max_rounds=rounds)),
        # incentive dose-response (who breaks first), two pairs for per-family slope
        dict(exp="A4", fig=a4_temptation.figures, specs=a4_temptation.build_specs(
            seeds=8, max_rounds=rounds)),
        # B1 across origins too (does cross- vs same-origin change collusion?)
        dict(exp="B1o", fig=b1_pricing.figures, specs=b1_pricing.build_specs(
            pair="same_origin_cn", seeds=10, max_rounds=rounds)),
        # validity/comparability across the full model matrix
        dict(exp="A5", fig=a5_baseline.figures, specs=(
            a5_baseline.build_specs(model="qwen-72b", seeds=5, max_rounds=rounds)
            + a5_baseline.build_specs(model="deepseek-v3", seeds=5, max_rounds=rounds)
            + a5_baseline.build_specs(model="llama-70b", seeds=5, max_rounds=rounds)
            + a5_baseline.build_specs(model="mistral-large", seeds=5, max_rounds=rounds))),
    ]
    return items


def _pilot(seeds=3, rounds=8):
    return [
        dict(exp="A1", fig=a1_channel.figures, specs=a1_channel.build_specs(
            pair="same_origin_cn", seeds=seeds, max_rounds=rounds)),
        dict(exp="B1", fig=b1_pricing.figures, specs=b1_pricing.build_specs(
            pair="cross_origin", seeds=seeds, max_rounds=rounds)),
        dict(exp="A3", fig=a3_origin.figures, specs=a3_origin.build_specs(
            pairs=["same_origin_cn", "cross_origin"], seeds=seeds, max_rounds=rounds)),
    ]


PROFILES = {"spine": _spine, "wide": _wide, "pilot": _pilot}


# --------------------------------------------------------------------------- #
# runner
# --------------------------------------------------------------------------- #
def run_program(profile="spine", *, mock=False, concurrency=24, resume=True,
                seeds=None, rounds=20):
    builder = PROFILES[profile]
    items = builder(seeds=seeds, rounds=rounds) if profile != "pilot" else builder()
    all_specs = [s for it in items for s in it["specs"]]
    counts = ", ".join(f"{it['exp']}:{len(it['specs'])}" for it in items)
    print(f"[program:{profile}] {len(all_specs)} matches across {len(items)} experiments "
          f"({counts}); concurrency={concurrency}, mock={mock}")

    ckpt = config.RUNS_DIR / "_program" / f"{profile}_checkpoint"
    results = run_specs(all_specs, mock=mock, concurrency=concurrency,
                        checkpoint_dir=ckpt, resume=resume)

    # group results by experiment and finalize each into its own run dir
    by_exp: dict[str, list] = {}
    for r in results:
        by_exp.setdefault(r.spec.experiment_id, []).append(r)
    for it in items:
        rs = by_exp.get(it["exp"], [])
        if rs:
            finalize(rs, it["exp"], figure_fn=it["fig"])

    # clear the program checkpoint on a clean finish
    if ckpt.exists():
        for p in ckpt.glob("*.pkl"):
            p.unlink()
    print(f"[program:{profile}] done — {len(results)} matches over {len(by_exp)} experiments")
    return by_exp
