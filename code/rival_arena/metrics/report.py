"""Definition-of-Done assembler (experiments.md §5).

A run is "done" only when it emits (1) a parameter manifest, (2) raw logs, (3) a
metrics table with bootstrapped CIs, and (4) >=1 figure (§5). The figure is
viz/'s job; this module produces the first three:

  * ``attach_metrics`` — run summarize_match + summarize_messages and stash them
    on ``result.metrics`` (so the raw log carries its own metrics).
  * ``save_run`` — write ``manifest.json`` + ``matches.jsonl`` + ``metrics.csv``
    under ``data/runs/<exp_id>/<config_hash or timestamp>/``.
  * ``cell_summary`` — per-cell aggregate combining lock-in proportion + bootstrap
    CIs on coop end-state / K + mean refusal rate. **This dict is the contract
    consumed by viz** — its key set is stable (see ``cell_summary``).
"""

from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Any, Optional, Sequence

from .. import config
from ..schemas import MatchResult, to_jsonable
from .core import refusal_rates, summarize_match
from .message import summarize_messages
from .stats import bootstrap_ci, lockin_proportion
from .core import coop_endstate, collusion_endstate, _is_market_game


# --------------------------------------------------------------------------- #
# attach_metrics
# --------------------------------------------------------------------------- #
def attach_metrics(result: MatchResult) -> MatchResult:
    """Compute summarize_match + summarize_messages and store on result.metrics.

    Mutates and returns ``result`` (so it can be used in a pipeline). The message
    metrics are namespaced under flat keys so the whole dict is a single CSV row.
    """
    summary = summarize_match(result)
    summary.update(summarize_messages(result))
    result.metrics = summary
    return result


# --------------------------------------------------------------------------- #
# save_run
# --------------------------------------------------------------------------- #
# series-valued summarize_match keys excluded from the flat metrics.csv (they are
# preserved in matches.jsonl); keeping the CSV scalar makes it analysis-ready.
_SERIES_KEYS = ("coop_series", "welfare_series", "K_series")


def save_run(
    results: Sequence[MatchResult],
    exp_id: str,
    run_dir: Optional[Path] = None,
) -> Path:
    """Write the three definition-of-done artifacts for a run and return its dir.

    Layout: ``<RUNS_DIR>/<exp_id>/<config_hash or timestamp>/`` containing
      1. ``manifest.json`` — the param manifest, incl. model-comparability rows
         pulled from each match's ``result.manifest`` (§5).
      2. ``matches.jsonl`` — raw logs, one MatchResult per line via to_jsonable.
      3. ``metrics.csv`` — one row per match with all summarize_match (+message)
         scalar fields.

    ``attach_metrics`` is run on any match whose ``metrics`` is empty, so the CSV
    and the JSONL agree. ``run_dir`` overrides the auto-named directory.
    """
    results = list(results)

    # resolve the run directory
    if run_dir is None:
        if results:
            # config_hash identifies the *cell*; for a multi-cell run it still
            # gives a stable, content-addressed dir, else fall back to a stamp.
            try:
                sub = results[0].spec.config_hash()
            except Exception:
                sub = time.strftime("%Y%m%dT%H%M%S")
        else:
            sub = time.strftime("%Y%m%dT%H%M%S")
        run_dir = config.RUNS_DIR / exp_id / sub
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    # ensure metrics are attached
    for r in results:
        if not r.metrics:
            attach_metrics(r)

    # (1) manifest.json --------------------------------------------------------
    model_rows = _model_comparability_rows(results)
    manifest = {
        "experiment_id": exp_id,
        "saved_at": time.time(),
        "n_matches": len(results),
        "cells": sorted({r.spec.cell_id for r in results}),
        "config_hashes": sorted({_safe_hash(r) for r in results}),
        "model_comparability": model_rows,
        # carry through any env/build info attached to the first match's manifest
        "match_manifest_sample": to_jsonable(results[0].manifest) if results else {},
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, default=str))

    # (2) matches.jsonl --------------------------------------------------------
    with (run_dir / "matches.jsonl").open("w") as fh:
        for r in results:
            fh.write(json.dumps(to_jsonable(r), default=str))
            fh.write("\n")

    # (3) metrics.csv ----------------------------------------------------------
    _write_metrics_csv(run_dir / "metrics.csv", results)

    # (4) rounds_long.csv — tidy per-(match,round,seat) table for free-form plotting
    try:
        from .export import save_long_csv
        save_long_csv(results, run_dir / "rounds_long.csv")
    except Exception as e:  # never sink a completed run over an export
        print(f"[save_run] long export skipped: {e}")

    return run_dir


def _safe_hash(r: MatchResult) -> str:
    try:
        return r.spec.config_hash()
    except Exception:
        return "unknown"


def _model_comparability_rows(results: Sequence[MatchResult]) -> list[dict[str, Any]]:
    """Collect the model-comparability sheet rows (§5) from match manifests.

    Each match may carry ``manifest['models']`` (a list of model-spec dicts) or
    ``manifest['model_comparability']``; we de-duplicate by model id."""
    rows: dict[str, dict[str, Any]] = {}
    for r in results:
        man = r.manifest or {}
        candidates = man.get("models") or man.get("model_comparability") or []
        if isinstance(candidates, dict):
            candidates = list(candidates.values())
        for row in candidates:
            if isinstance(row, dict):
                key = str(row.get("id") or row.get("litellm_model") or len(rows))
                rows[key] = to_jsonable(row)
    return list(rows.values())


def _write_metrics_csv(path: Path, results: Sequence[MatchResult]) -> None:
    # union of scalar keys across all rows (excluding series), stable order
    field_order: list[str] = []
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for r in results:
        scalar = {k: v for k, v in r.metrics.items() if k not in _SERIES_KEYS}
        rows.append(scalar)
        for k in scalar:
            if k not in seen:
                seen.add(k)
                field_order.append(k)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=field_order, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _csv_scalar(row.get(k)) for k in field_order})


def _csv_scalar(v: Any) -> Any:
    if isinstance(v, bool):
        return int(v)
    if v is None:
        return ""
    return v


# --------------------------------------------------------------------------- #
# cell_summary — the viz contract
# --------------------------------------------------------------------------- #
def cell_summary(
    results: Sequence[MatchResult], cell_id: Optional[str] = None
) -> dict[str, Any]:
    """Per-cell aggregate — **the contract consumed by viz** (§5).

    Combines the lock-in proportion (+Wilson CI), bootstrap CIs on coop
    end-state and collusion ``K``, and the mean refusal rate, for one factor cell
    (a set of matches sharing a cell_id). Key set is STABLE:

        cell_id, n_matches, channel, game,
        lockin_proportion, wilson_lo, wilson_hi,
        coop_endstate_mean, coop_ci_lo, coop_ci_hi,
        K_mean, K_ci_lo, K_ci_hi,
        refusal_rate, is_market_game

    Values that don't apply (e.g. K for a non-market game) are None.
    """
    results = list(results)
    cid = cell_id
    if cid is None and results:
        cid = results[0].spec.cell_id
    channel = results[0].spec.channel.value if results else None
    game = results[0].spec.game.name if results else None

    lp = lockin_proportion(results)

    coop_vals = [c for c in (coop_endstate(r) for r in results) if c is not None]
    coop_mean = float(sum(coop_vals) / len(coop_vals)) if coop_vals else None
    coop_lo, coop_hi = bootstrap_ci(coop_vals) if coop_vals else (None, None)

    is_market = any(_is_market_game(r) for r in results)
    k_vals = [k for k in (collusion_endstate(r) for r in results) if k is not None]
    k_mean = float(sum(k_vals) / len(k_vals)) if k_vals else None
    k_lo, k_hi = bootstrap_ci(k_vals) if k_vals else (None, None)

    ref_vals = [refusal_rates(r)["overall"] for r in results]
    ref_mean = float(sum(ref_vals) / len(ref_vals)) if ref_vals else None

    return {
        "cell_id": cid,
        "n_matches": len(results),
        "channel": channel,
        "game": game,
        "lockin_proportion": lp["proportion"],
        "wilson_lo": lp["wilson_lo"],
        "wilson_hi": lp["wilson_hi"],
        "coop_endstate_mean": coop_mean,
        "coop_ci_lo": coop_lo,
        "coop_ci_hi": coop_hi,
        "K_mean": k_mean,
        "K_ci_lo": k_lo,
        "K_ci_hi": k_hi,
        "refusal_rate": ref_mean,
        "is_market_game": is_market,
    }
