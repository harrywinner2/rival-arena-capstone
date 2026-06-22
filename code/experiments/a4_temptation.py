"""A4 — incentive-magnitude dose-response ("who breaks first").

IPD with the temptation gap scaled x0.5 / x1 / x2 / x4 (ipd's `temptation_scale`,
which widens (T-R) and (P-S) while keeping the ordinal social-dilemma structure).
A channel is left ON (L2_observed) so cooperation remains reachable and the only
thing moving is the incentive to defect — a clean dose-response (P-numbers: this
is the magnitude axis of H1).

We run TWO pairs by default (same_origin_cn and cross_origin) so each gets its own
slope: the steeper the fall of end-state C with temptation, the sooner that pair
"breaks". Origin is a confounded proxy here as in A3 (descriptive, P1/P2).
"""

from __future__ import annotations

from rival_arena.config import DEFAULT_HISTORY_WINDOW, DEFAULT_TOKEN_BUDGET
from rival_arena.harness.channel import default_epistemic
from rival_arena.schemas import ChannelLevel, GameSpec, MatchSpec

from .common import pair_players, resolve_pair, run_and_finalize

TEMPTATION_SCALES = [0.5, 1.0, 2.0, 4.0]
DEFAULT_PAIRS = ["same_origin_cn", "cross_origin"]


def build_specs(
    pairs=DEFAULT_PAIRS,
    seeds: int = 8,
    scales=TEMPTATION_SCALES,
    level: ChannelLevel = ChannelLevel.L2_OBSERVED,   # channel ON so coop is possible
    familiarity: str = "canonical",
    max_rounds: int = 20,
    continuation_prob: float = 0.97,
    token_budget: int = DEFAULT_TOKEN_BUDGET,
    framing: str = "neutral",
    seed_offset: int = 0,                 # disjoint range for confirmatory runs (P4)
) -> list[MatchSpec]:
    specs: list[MatchSpec] = []
    for pair in pairs:
        model_ids = resolve_pair(pair)
        pairname = pair if isinstance(pair, str) else "x".join(model_ids)
        for scale in scales:
            for s in range(seed_offset, seed_offset + seeds):
                specs.append(MatchSpec(
                    experiment_id="A4",
                    cell_id=f"A4/temptation_{scale}/{pairname}",
                    game=GameSpec("ipd", {"continuation_prob": continuation_prob,
                                          "max_rounds": max_rounds,
                                          "temptation_scale": scale},
                                  familiarity=familiarity),
                    channel=level,
                    epistemic=default_epistemic(level),
                    players=pair_players(model_ids, s),
                    seed=s,
                    token_budget=token_budget,
                    history_window=DEFAULT_HISTORY_WINDOW,
                    framing=framing,
                ))
    return specs


def figures(run_dir, summaries, results):
    from rival_arena.viz import figures as F
    out = []

    def _safe(fn, *a, **kw):
        try:
            out.append(fn(*a, **kw))
        except Exception as e:  # figures must never sink a completed run
            print(f"[A4] figure {getattr(fn, '__name__', fn)} failed: {e}")

    # dose-response: x = temptation scales, one line per pair (end-state C + CIs).
    try:
        def _scale_of(cell_id):
            return float(cell_id.split("/")[1].replace("temptation_", ""))

        def _pair_of(cell_id):
            return cell_id.split("/")[-1]

        xs = sorted({_scale_of(s["cell_id"]) for s in summaries})
        coop_means: dict[str, list[float]] = {}
        cis: dict[str, list[tuple]] = {}
        for pairname in sorted({_pair_of(s["cell_id"]) for s in summaries}):
            ys, ci = [], []
            for x in xs:
                hit = [s for s in summaries
                       if _pair_of(s["cell_id"]) == pairname
                       and abs(_scale_of(s["cell_id"]) - x) < 1e-9]
                m = hit[0].get("coop_endstate_mean") if hit else None
                ys.append(m if m is not None else 0.0)
                lo = hit[0].get("coop_ci_lo") if hit else None
                hi = hit[0].get("coop_ci_hi") if hit else None
                ci.append((lo if lo is not None else ys[-1],
                           hi if hi is not None else ys[-1]))
            coop_means[pairname] = ys
            cis[pairname] = ci
        if xs and coop_means:
            _safe(F.dose_response, xs, coop_means, cis,
                  run_dir / "a4_dose_response.png",
                  xlabel="Temptation scale (x canonical T-R gap)",
                  title="A4 temptation dose-response: who breaks first")
    except Exception as e:
        print(f"[A4] dose-response build failed: {e}")

    _safe(F.refusal_panel, summaries, run_dir / "a4_refusals.png")
    return out


def main(pairs=DEFAULT_PAIRS, seeds=8, mock=False, max_rounds=20, seed_offset=0,
         resume=True, **kw):
    specs = build_specs(pairs=pairs, seeds=seeds, max_rounds=max_rounds,
                        seed_offset=seed_offset, **kw)
    print(f"[A4] {len(specs)} matches: {len(pairs)} pairs x {len(TEMPTATION_SCALES)} "
          f"scales x {seeds} seeds, mock={mock}")
    return run_and_finalize(specs, "A4", mock=mock, figure_fn=figures, resume=resume)
