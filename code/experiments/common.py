"""Shared driver plumbing: spec builders, the bounded-concurrency run loop, and
the save+summarize+figure pipeline (definition of done, §5).
"""

from __future__ import annotations

import asyncio
import hashlib
import pickle
import time
from pathlib import Path
from typing import Iterable, Optional, Sequence

from rival_arena import config
from rival_arena.harness import LLMClient, MockLLM
from rival_arena.harness.monitor import Monitor, Paraphraser
from rival_arena.harness.runner import run_match
from rival_arena.metrics import attach_metrics, cell_summary, save_run
from rival_arena.registry import get_pair
from rival_arena.schemas import (
    ChannelLevel, EpistemicSpec, GameSpec, MatchSpec, PlayerKind, PlayerSpec,
)


def _ckpt_key(spec: MatchSpec) -> str:
    """Identifies one match for checkpoint dedup: cell + seed + horizon + budget,
    so a design change (e.g. different rounds) won't wrongly reuse old results."""
    return (f"{spec.experiment_id}|{spec.cell_id}|seed={spec.seed}"
            f"|r={spec.game.params.get('max_rounds')}|t={spec.token_budget}")


# --------------------------------------------------------------------------- #
# player / seat construction (player order randomized by seed, P)
# --------------------------------------------------------------------------- #
def pair_players(model_ids: Sequence[str], seed: int) -> list[PlayerSpec]:
    a, b = model_ids[0], model_ids[1]
    if seed % 2 == 1:                       # randomize seat assignment across seeds
        a, b = b, a
    return [PlayerSpec("A", PlayerKind.LLM, a), PlayerSpec("B", PlayerKind.LLM, b)]


def llm_vs_classical(model_id: str, strategy: str) -> list[PlayerSpec]:
    return [PlayerSpec("A", PlayerKind.LLM, model_id),
            PlayerSpec("B", PlayerKind.CLASSICAL, strategy)]


def resolve_pair(pair: str | Sequence[str]) -> list[str]:
    """Accept a named pair (models.yaml) or an explicit [id, id]."""
    if isinstance(pair, str):
        return get_pair(pair)
    return list(pair)


# --------------------------------------------------------------------------- #
# run loop
# --------------------------------------------------------------------------- #
async def _run_all(specs, client, monitor, paraphraser, concurrency, ckpt_dir):
    sem = asyncio.Semaphore(concurrency)

    async def _one(spec):
        async with sem:
            res = await run_match(spec, client, monitor=monitor, paraphraser=paraphraser)
            attach_metrics(res)
            if ckpt_dir is not None:                 # durable: persist the instant it lands
                fn = ckpt_dir / f"{hashlib.sha1(_ckpt_key(spec).encode()).hexdigest()}.pkl"
                with open(fn, "wb") as fh:
                    pickle.dump(res, fh)
            return res

    return await asyncio.gather(*[_one(s) for s in specs])


def _load_checkpoint(ckpt_dir: Path) -> dict[str, object]:
    done: dict[str, object] = {}
    if not ckpt_dir.exists():
        return done
    for p in ckpt_dir.glob("*.pkl"):
        try:
            with open(p, "rb") as fh:
                res = pickle.load(fh)
            done[_ckpt_key(res.spec)] = res
        except Exception:
            continue   # a half-written checkpoint from a hard kill is just skipped
    return done


def run_specs(
    specs: Sequence[MatchSpec],
    *,
    mock: bool = False,
    client: Optional[LLMClient] = None,
    monitor: Optional[Monitor] = None,
    paraphraser: Optional[Paraphraser] = None,
    concurrency: Optional[int] = None,
    checkpoint_dir: Optional[Path] = None,
    resume: bool = True,
):
    """Run MatchSpecs with bounded concurrency; metrics attached.

    If ``checkpoint_dir`` is set, every completed match is pickled there the
    instant it finishes, and (when ``resume``) already-completed matches are
    loaded and skipped — so a machine sleep / kill costs only the in-flight
    matches, never the whole run. This makes the pipeline host-agnostic.
    """
    client = client or (MockLLM() if mock else LLMClient())
    concurrency = concurrency or config.MAX_CONCURRENCY

    done: dict[str, object] = {}
    if checkpoint_dir is not None:
        checkpoint_dir = Path(checkpoint_dir)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        if resume:
            done = _load_checkpoint(checkpoint_dir)

    todo = [s for s in specs if _ckpt_key(s) not in done]
    if done:
        print(f"[resume] {len(done)} matches already done; running {len(todo)} more "
              f"(of {len(specs)} total)")
    new = asyncio.run(_run_all(todo, client, monitor, paraphraser, concurrency,
                               checkpoint_dir)) if todo else []
    return list(done.values()) + list(new)


def run_and_finalize(specs, exp_id, *, mock=False, figure_fn=None, resume=True,
                     clear_checkpoint=True, **run_kw):
    """Checkpointed run + definition-of-done finalize, in one call.

    The checkpoint lives at ``RUNS_DIR/<exp_id>/_checkpoint``; on a clean finish
    it is cleared (so the next, differently-configured run starts fresh). Pass
    ``resume=False`` to ignore an existing checkpoint, or ``clear_checkpoint=
    False`` to keep it.
    """
    ckpt_dir = config.RUNS_DIR / exp_id / "_checkpoint"
    results = run_specs(specs, mock=mock, checkpoint_dir=ckpt_dir, resume=resume,
                        **run_kw)
    run_dir = finalize(results, exp_id, figure_fn=figure_fn)
    if clear_checkpoint and ckpt_dir.exists():
        for p in ckpt_dir.glob("*.pkl"):
            p.unlink()
    return run_dir


# --------------------------------------------------------------------------- #
# save + summarize + figures (definition of done)
# --------------------------------------------------------------------------- #
def finalize(results, exp_id: str, figure_fn=None) -> Path:
    """Write manifest+logs+metrics, print per-cell summaries, render figures."""
    stamp = time.strftime("%Y%m%dT%H%M%S")
    run_dir = config.RUNS_DIR / exp_id / stamp
    save_run(results, exp_id, run_dir=run_dir)

    # per-cell summaries (grouped by cell_id)
    by_cell: dict[str, list] = {}
    for r in results:
        by_cell.setdefault(r.spec.cell_id, []).append(r)
    summaries = [cell_summary(rs, cell_id=cid) for cid, rs in sorted(by_cell.items())]
    _print_summaries(exp_id, summaries)

    fig_paths = []
    if figure_fn is not None:
        try:
            fig_paths = figure_fn(run_dir, summaries, results) or []
        except Exception as e:  # figures must never sink a completed run
            print(f"[finalize] figure generation failed: {e}")
    print(f"\n[finalize] run saved to: {run_dir}")
    for p in fig_paths:
        print(f"[finalize] figure: {p}")
    return run_dir


def _fmt(v, spec=".2f"):
    return format(v, spec) if isinstance(v, (int, float)) else "  n/a"


def _print_summaries(exp_id, summaries):
    print(f"\n===== {exp_id}: per-cell summary =====")
    for s in summaries:
        line = f"  {s['cell_id']:<40} n={s['n_matches']:>3}"
        if s.get("lockin_proportion") is not None:
            line += (f" lock-in={_fmt(s['lockin_proportion'])} "
                     f"[{_fmt(s['wilson_lo'])},{_fmt(s['wilson_hi'])}]")
        if s.get("coop_endstate_mean") is not None:
            line += f"  C={_fmt(s['coop_endstate_mean'])}"
        if s.get("K_mean") is not None:
            line += f"  K={_fmt(s['K_mean'])}"
        line += f"  refusal={_fmt(s.get('refusal_rate'))}"
        print(line)
