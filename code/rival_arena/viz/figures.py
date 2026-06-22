"""Publication-quality static figures (experiments.md §2, A1/B1 demo notes).

The figure set is the fourth definition-of-done artifact (§5): a run is only
"done" once it emits >=1 figure. Everything here is computed from the metrics
layer's stable contracts — never from env/ or the LLM loop:

  * ``cell_summary`` dicts (metrics.report) — the PRIMARY input. Stable keys:
    cell_id, n_matches, channel, game, lockin_proportion, wilson_lo, wilson_hi,
    coop_endstate_mean, coop_ci_lo, coop_ci_hi, K_mean, K_ci_lo, K_ci_hi,
    refusal_rate, is_market_game.
  * ``MatchResult`` objects + the core series functions (coop_rate_series,
    collusion_index_series) for the round-by-round curves.
  * ``round.extra["prices"]`` = {seat: price} for the B1 price money-shot.

Design rules tied to the showcase: the headline figure is the A1 lock-in bar
("0/20 at L0, 15/20 at L3"); the on-stage money-shot is the B1 price trajectory
(two sellers climbing, competition "silently failing" below). Figures must be
clean, legible at projector distance, and saved as both PNG (deck) and SVG
(paper). Plotly variants are offered where an interactive/HTML export helps.

Each public function takes data + an output ``path`` and returns the written
path (the PNG). ``make_all`` regenerates the standard set for a saved run.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any, Optional, Sequence, Union

import matplotlib

matplotlib.use("Agg")  # headless: no display needed for file export
import matplotlib.pyplot as plt
import numpy as np

# --------------------------------------------------------------------------- #
# House style — one place so every figure is consistent and legible on stage.
# --------------------------------------------------------------------------- #
# Channel ladder order (A1) — used to sort/label rungs left-to-right L0->L3.
CHANNEL_ORDER = ["L0_none", "L1_signal", "L2_observed", "L3_private"]
CHANNEL_LABELS = {
    "L0_none": "L0\nnone",
    "L1_signal": "L1\nsignal",
    "L2_observed": "L2\nobserved",
    "L3_private": "L3\nprivate",
}
# A diverging-ish ramp: defection-grey -> cooperation-blue, so the bars *read*
# as "more channel -> more cooperation".
_RUNG_COLORS = {
    "L0_none": "#9aa0a6",
    "L1_signal": "#7ba6d6",
    "L2_observed": "#3b78c2",
    "L3_private": "#15487f",
}
_ACCENT = "#15487f"
_DANGER = "#c0392b"
_SAFE = "#2e8b57"

PALETTE = ["#15487f", "#c0392b", "#2e8b57", "#b8860b", "#7d3c98", "#16a085"]


def _apply_style() -> None:
    """Apply a clean, projector-legible rc context (idempotent)."""
    plt.rcParams.update(
        {
            "figure.dpi": 130,
            "savefig.dpi": 200,
            "font.size": 13,
            "axes.titlesize": 16,
            "axes.titleweight": "bold",
            "axes.labelsize": 13,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linestyle": "-",
            "legend.frameon": False,
            "figure.autolayout": True,
        }
    )


def _save(fig, path: Union[str, Path]) -> Path:
    """Write ``fig`` to ``path`` as PNG and a sibling SVG; return the PNG path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    png = path if path.suffix.lower() == ".png" else path.with_suffix(".png")
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(png.with_suffix(".svg"), bbox_inches="tight")
    plt.close(fig)
    return png


def _rung_key(cs: dict[str, Any]) -> int:
    ch = cs.get("channel")
    return CHANNEL_ORDER.index(ch) if ch in CHANNEL_ORDER else len(CHANNEL_ORDER)


# --------------------------------------------------------------------------- #
# 1. lockin_bar — THE headline A1 figure (P17)
# --------------------------------------------------------------------------- #
def lockin_bar(
    cell_summaries: Sequence[dict[str, Any]],
    path: Union[str, Path],
    title: str = "Cooperation lock-in vs communication channel",
) -> Path:
    """Bar chart of lock-in proportion per channel rung with Wilson CIs (A1).

    This is the money figure: "0/20 at L0, 15/20 at L3". Each bar is one cell's
    ``lockin_proportion`` (end-state C > 0.8 across the cell's matches), with
    asymmetric Wilson-CI error bars (``wilson_lo``/``wilson_hi``) and a
    "k/n matches locked in" annotation. Cells are ordered along the L0->L3
    ladder; any non-ladder cells are appended in input order.
    """
    _apply_style()
    cells = sorted(cell_summaries, key=_rung_key)
    n = len(cells)
    x = np.arange(n)

    props = [(c.get("lockin_proportion") or 0.0) for c in cells]
    lo = [(c.get("wilson_lo") or 0.0) for c in cells]
    hi = [(c.get("wilson_hi") or 0.0) for c in cells]
    yerr = np.array(
        [
            [max(0.0, p - l) for p, l in zip(props, lo)],
            [max(0.0, h - p) for p, h in zip(props, hi)],
        ]
    )
    colors = [_RUNG_COLORS.get(c.get("channel"), _ACCENT) for c in cells]

    fig, ax = plt.subplots(figsize=(max(6.5, 1.7 * n), 5.2))
    bars = ax.bar(x, props, width=0.62, color=colors, edgecolor="white", zorder=3)
    ax.errorbar(
        x, props, yerr=yerr, fmt="none", ecolor="#222", elinewidth=1.8,
        capsize=6, capthick=1.8, zorder=4,
    )

    # "k/n matches locked in" on each bar
    for xi, c, p, h in zip(x, cells, props, hi):
        k = c.get("k_locked")
        nn = c.get("n_matches") or c.get("n")
        if k is None:
            nn_eff = nn or 0
            k = int(round(p * nn_eff)) if nn_eff else 0
        label = f"{k}/{nn}" if nn is not None else f"{p:.0%}"
        ax.annotate(
            label,
            (xi, max(p, h) + 0.03),
            ha="center", va="bottom", fontsize=12, fontweight="bold", color="#222",
        )

    labels = [CHANNEL_LABELS.get(c.get("channel"), str(c.get("channel"))) for c in cells]
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.12)
    ax.set_yticks(np.linspace(0, 1, 6))
    ax.set_ylabel("Lock-in proportion\n(matches with end-state C > 0.8)")
    ax.set_xlabel("Communication channel (one affordance added per rung)")
    ax.set_title(title)
    ax.axhline(0, color="#222", lw=0.8)
    return _save(fig, path)


def lockin_bar_plotly(
    cell_summaries: Sequence[dict[str, Any]],
    path: Union[str, Path],
    title: str = "Cooperation lock-in vs communication channel",
) -> Path:
    """Interactive Plotly version of :func:`lockin_bar` (HTML; PNG via kaleido)."""
    import plotly.graph_objects as go

    cells = sorted(cell_summaries, key=_rung_key)
    props = [(c.get("lockin_proportion") or 0.0) for c in cells]
    lo = [(c.get("wilson_lo") or 0.0) for c in cells]
    hi = [(c.get("wilson_hi") or 0.0) for c in cells]
    labels = [str(c.get("channel")) for c in cells]
    text = []
    for c, p in zip(cells, props):
        nn = c.get("n_matches") or c.get("n")
        k = c.get("k_locked")
        if k is None and nn:
            k = int(round(p * nn))
        text.append(f"{k}/{nn}" if nn is not None else f"{p:.0%}")

    fig = go.Figure(
        go.Bar(
            x=labels, y=props, text=text, textposition="outside",
            marker_color=[_RUNG_COLORS.get(c.get("channel"), _ACCENT) for c in cells],
            error_y=dict(
                type="data", symmetric=False,
                array=[h - p for h, p in zip(hi, props)],
                arrayminus=[p - l for p, l in zip(props, lo)],
            ),
        )
    )
    fig.update_layout(
        title=title, yaxis_title="Lock-in proportion (end-state C > 0.8)",
        xaxis_title="Communication channel", yaxis_range=[0, 1.12],
        template="plotly_white", showlegend=False,
    )
    return _write_plotly(fig, path)


# --------------------------------------------------------------------------- #
# 2. price_trajectories — the B1 on-stage money-shot
# --------------------------------------------------------------------------- #
def _extract_price_series(result: Any) -> dict[str, list[float]]:
    """Pull per-seat price series from a MatchResult (or its jsonable dict)."""
    rounds = _rounds_of(result)
    seats: dict[str, list[float]] = {}
    for rnd in rounds:
        extra = _attr(rnd, "extra") or {}
        prices = extra.get("prices") if isinstance(extra, dict) else None
        if not isinstance(prices, dict):
            continue
        for seat, p in prices.items():
            if p is None:
                continue
            seats.setdefault(seat, []).append(float(p))
    return seats


def _benchmarks_of(result: Any) -> dict[str, Any]:
    man = _attr(result, "manifest") or {}
    if isinstance(man, dict):
        return dict(man.get("benchmarks", {}) or {})
    return {}


def price_trajectories(
    result_or_results: Union[Any, Sequence[Any]],
    path: Union[str, Path],
    benchmarks: Optional[dict[str, Any]] = None,
    title: str = "Autonomous price collusion: two rivals climbing together",
) -> Path:
    """B1 money-shot — two sellers' prices over rounds vs the benchmarks.

    Draws each seller's price line, dashed horizontals at ``p_competitive`` and
    ``p_monopoly``, and shades the *supracompetitive* region between them (where
    "competition has silently failed"). If given many results, plots the
    per-seat mean with a min-max/SE band so the climb reads as a population
    effect, not one lucky seed.

    ``benchmarks`` overrides what is read from the match manifest (so a caller
    can pass spec-derived p_competitive/p_monopoly directly).
    """
    _apply_style()
    results = _as_list(result_or_results)
    if not results:
        raise ValueError("price_trajectories: no results given")

    bm = dict(benchmarks or {})
    if not bm:
        bm = _benchmarks_of(results[0])
    p_comp = bm.get("p_competitive")
    p_mono = bm.get("p_monopoly")

    # collect per-seat series across all results
    per_seat_runs: dict[str, list[list[float]]] = {}
    for res in results:
        for seat, series in _extract_price_series(res).items():
            per_seat_runs.setdefault(seat, []).append(series)

    if not per_seat_runs:
        raise ValueError("price_trajectories: no per-round prices in extra['prices']")

    fig, ax = plt.subplots(figsize=(9.5, 5.6))

    # shade the supracompetitive band first (sits behind the lines)
    if p_comp is not None and p_mono is not None and p_mono > p_comp:
        ax.axhspan(
            p_comp, p_mono, color=_DANGER, alpha=0.07, zorder=0,
            label="supracompetitive region",
        )

    seat_colors = {}
    for i, (seat, runs) in enumerate(sorted(per_seat_runs.items())):
        color = PALETTE[i % len(PALETTE)]
        seat_colors[seat] = color
        T = max(len(r) for r in runs)
        # align ragged runs by padding with NaN, then nanmean
        mat = np.full((len(runs), T), np.nan)
        for r_i, r in enumerate(runs):
            mat[r_i, : len(r)] = r
        x = np.arange(1, T + 1)
        m = np.nanmean(mat, axis=0)
        ax.plot(x, m, color=color, lw=3.0, marker="o", ms=4,
                label=f"seat {seat}" + (" (mean)" if len(runs) > 1 else ""), zorder=5)
        if len(runs) > 1:
            sd = np.nanstd(mat, axis=0)
            ax.fill_between(x, m - sd, m + sd, color=color, alpha=0.18, zorder=2)

    if p_comp is not None:
        ax.axhline(p_comp, ls="--", lw=2, color=_SAFE, zorder=3)
        ax.annotate(
            f"competition silently failing  (p={p_comp:g})",
            (0.015, p_comp), xycoords=("axes fraction", "data"),
            ha="left", va="bottom", color=_SAFE, fontweight="bold", fontsize=11,
        )
    if p_mono is not None:
        ax.axhline(p_mono, ls="--", lw=2, color=_DANGER, zorder=3)
        ax.annotate(
            f"monopoly / cartel ceiling  (p={p_mono:g})",
            (0.015, p_mono), xycoords=("axes fraction", "data"),
            ha="left", va="top", color=_DANGER, fontweight="bold", fontsize=11,
        )

    ax.set_xlabel("Round")
    ax.set_ylabel("Price")
    ax.set_title(title)
    # headroom above monopoly so the climb + labels are not clipped
    if p_mono is not None:
        ax.set_ylim(top=p_mono * 1.12)
    ax.legend(loc="upper left", fontsize=11, ncol=2)
    ax.margins(x=0.01)
    return _save(fig, path)


def price_trajectories_plotly(
    result_or_results: Union[Any, Sequence[Any]],
    path: Union[str, Path],
    benchmarks: Optional[dict[str, Any]] = None,
    title: str = "Autonomous price collusion",
) -> Path:
    """Interactive Plotly version of :func:`price_trajectories`."""
    import plotly.graph_objects as go

    results = _as_list(result_or_results)
    bm = dict(benchmarks or {}) or _benchmarks_of(results[0])
    p_comp, p_mono = bm.get("p_competitive"), bm.get("p_monopoly")

    per_seat_runs: dict[str, list[list[float]]] = {}
    for res in results:
        for seat, s in _extract_price_series(res).items():
            per_seat_runs.setdefault(seat, []).append(s)

    fig = go.Figure()
    if p_comp is not None and p_mono is not None and p_mono > p_comp:
        fig.add_hrect(y0=p_comp, y1=p_mono, fillcolor=_DANGER, opacity=0.07, line_width=0)
    for i, (seat, runs) in enumerate(sorted(per_seat_runs.items())):
        T = max(len(r) for r in runs)
        mat = np.full((len(runs), T), np.nan)
        for r_i, r in enumerate(runs):
            mat[r_i, : len(r)] = r
        m = np.nanmean(mat, axis=0)
        fig.add_trace(go.Scatter(
            x=list(range(1, T + 1)), y=m, mode="lines+markers", name=f"seat {seat}",
            line=dict(width=3, color=PALETTE[i % len(PALETTE)]),
        ))
    if p_comp is not None:
        fig.add_hline(y=p_comp, line_dash="dash", line_color=_SAFE,
                      annotation_text="competitive")
    if p_mono is not None:
        fig.add_hline(y=p_mono, line_dash="dash", line_color=_DANGER,
                      annotation_text="monopoly")
    fig.update_layout(title=title, xaxis_title="Round", yaxis_title="Price",
                      template="plotly_white")
    return _write_plotly(fig, path)


# --------------------------------------------------------------------------- #
# 3. coop_curves — round-by-round C(t) per cell with CI bands
# --------------------------------------------------------------------------- #
def coop_curves(
    results_by_cell: dict[str, Sequence[Any]],
    path: Union[str, Path],
    title: str = "Cooperation trajectory C(t) by condition",
) -> Path:
    """Mean cooperation C(t) per cell with bootstrap-style CI bands (§2 secondary).

    ``results_by_cell`` maps a label -> a sequence of MatchResults (or jsonable
    dicts). Each match's per-round coop series is recomputed via the metrics
    layer (``coop_rate_series``) when given a live MatchResult, or read from the
    stored ``metrics['coop_series']`` when given a jsonable dict. Curves are the
    cross-match mean per round with a +-1.96 SE band.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(9, 5.4))

    for i, (label, results) in enumerate(results_by_cell.items()):
        color = PALETTE[i % len(PALETTE)]
        series_list = [_coop_series_of(r) for r in results]
        series_list = [s for s in series_list if s]
        if not series_list:
            continue
        T = max(len(s) for s in series_list)
        mat = np.full((len(series_list), T), np.nan)
        for r_i, s in enumerate(series_list):
            mat[r_i, : len(s)] = s
        x = np.arange(1, T + 1)
        m = np.nanmean(mat, axis=0)
        cnt = np.sum(~np.isnan(mat), axis=0)
        sd = np.nanstd(mat, axis=0)
        se = np.divide(sd, np.sqrt(np.maximum(cnt, 1)))
        ax.plot(x, m, color=color, lw=2.6, label=label, zorder=4)
        ax.fill_between(x, np.clip(m - 1.96 * se, 0, 1), np.clip(m + 1.96 * se, 0, 1),
                        color=color, alpha=0.18, zorder=2)

    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel("Round")
    ax.set_ylabel("Mean cooperation rate C(t)")
    ax.set_title(title)
    ax.axhline(0.8, ls=":", color="#555", lw=1.4)
    ax.annotate("lock-in threshold (0.8)", (0.01, 0.81),
                xycoords=("axes fraction", "data"), fontsize=10, color="#555")
    ax.legend(loc="best", fontsize=11)
    return _save(fig, path)


# --------------------------------------------------------------------------- #
# 4. dose_response — A4 temptation curve (slope per family)
# --------------------------------------------------------------------------- #
def dose_response(
    x_vals: Sequence[float],
    coop_means: Union[Sequence[float], dict[str, Sequence[float]]],
    cis: Optional[Union[Sequence[tuple], dict[str, Sequence[tuple]]]],
    path: Union[str, Path],
    xlabel: str = "Temptation gap (T - R)",
    title: str = "Temptation dose-response: who breaks first",
) -> Path:
    """A4 dose-response — cooperation vs temptation, one slope per family.

    ``coop_means`` is either a single sequence (one curve) or a mapping
    ``family -> sequence`` (one curve per family, the "who breaks first" chart).
    ``cis`` mirrors that shape: a sequence of ``(lo, hi)`` per x, or a mapping
    of the same; pass ``None`` to omit error bars.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    x = np.asarray(list(x_vals), dtype=float)

    if isinstance(coop_means, dict):
        series_items = list(coop_means.items())
        ci_map = cis if isinstance(cis, dict) else {}
    else:
        series_items = [("cooperation", coop_means)]
        ci_map = {"cooperation": cis} if cis is not None else {}

    for i, (fam, ys) in enumerate(series_items):
        color = PALETTE[i % len(PALETTE)]
        y = np.asarray(list(ys), dtype=float)
        yerr = None
        fam_cis = ci_map.get(fam)
        if fam_cis is not None:
            lo = np.array([c[0] for c in fam_cis], dtype=float)
            hi = np.array([c[1] for c in fam_cis], dtype=float)
            yerr = np.array([y - lo, hi - y])
        ax.errorbar(x, y, yerr=yerr, color=color, lw=2.6, marker="o", ms=7,
                    capsize=5, label=str(fam), zorder=4)
        # annotate the OLS slope (the "who breaks first" number)
        if len(x) >= 2:
            slope = np.polyfit(x, y, 1)[0]
            ax.annotate(f"slope={slope:+.3f}", (x[-1], y[-1]),
                        textcoords="offset points", xytext=(8, 0),
                        color=color, fontsize=10, fontweight="bold", va="center")

    ax.set_ylim(-0.02, 1.05)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("End-state cooperation C")
    ax.set_title(title)
    if len(series_items) > 1:
        ax.legend(loc="best", fontsize=11, title="family")
    return _save(fig, path)


# --------------------------------------------------------------------------- #
# 5. refusal_panel — P19, refusals are their own finding
# --------------------------------------------------------------------------- #
def refusal_panel(
    cell_summaries: Sequence[dict[str, Any]],
    path: Union[str, Path],
    title: str = "Refusal rate by condition (reported, never dropped)",
) -> Path:
    """Refusal rate per condition (P19) — its own finding, not a dropped run.

    Bars are each cell's ``refusal_rate`` (the REPAIRED/REFUSAL/OFF_TASK family
    share). Ordered along the channel ladder when applicable; the cell_id is the
    x label otherwise.
    """
    _apply_style()
    cells = sorted(cell_summaries, key=_rung_key)
    rates = [(c.get("refusal_rate") or 0.0) for c in cells]
    labels = [
        CHANNEL_LABELS.get(c.get("channel"), str(c.get("cell_id") or c.get("channel")))
        for c in cells
    ]
    x = np.arange(len(cells))
    colors = [_RUNG_COLORS.get(c.get("channel"), _DANGER) for c in cells]

    fig, ax = plt.subplots(figsize=(max(6.5, 1.6 * len(cells)), 5.0))
    ax.bar(x, rates, width=0.6, color=colors, edgecolor="white", zorder=3)
    for xi, r in zip(x, rates):
        ax.annotate(f"{r:.0%}", (xi, r + 0.005), ha="center", va="bottom",
                    fontsize=11, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    top = max(0.1, max(rates) * 1.25 if rates else 0.1)
    ax.set_ylim(0, top)
    ax.set_ylabel("Refusal rate\n(repaired / refusal / off-task)")
    ax.set_xlabel("Condition")
    ax.set_title(title)
    return _save(fig, path)


# --------------------------------------------------------------------------- #
# 6. origin_partial_eta — A3, origin is second-order
# --------------------------------------------------------------------------- #
def origin_partial_eta(
    anova_df: Any,
    path: Union[str, Path],
    title: str = "Variance explained: channel vs regime vs origin",
) -> Path:
    """Partial-eta^2 per factor (A3) — shows origin is second-order.

    ``anova_df`` is either the table returned by ``metrics.factorial_anova``
    (a DataFrame with a ``partial_eta_sq`` column, indexed by ``C(factor)``) or
    a plain ``{factor_label: partial_eta2}`` mapping. The "Residual" row is
    dropped. Bars are sorted descending so the channel dominance reads at once.
    """
    _apply_style()
    # normalize to {label: eta2}
    if isinstance(anova_df, dict):
        items = dict(anova_df)
    else:
        items = {}
        col = anova_df["partial_eta_sq"]
        for idx in anova_df.index:
            if str(idx) == "Residual":
                continue
            label = str(idx)
            if label.startswith("C(") and label.endswith(")"):
                label = label[2:-1]
            val = col.loc[idx]
            if val == val:  # not NaN
                items[label] = float(val)

    pairs = sorted(items.items(), key=lambda kv: kv[1], reverse=True)
    labels = [k for k, _ in pairs]
    vals = [v for _, v in pairs]
    x = np.arange(len(pairs))
    colors = [_ACCENT if i == 0 else "#9aa0a6" for i in range(len(pairs))]

    fig, ax = plt.subplots(figsize=(max(6, 1.6 * len(pairs)), 5.0))
    ax.bar(x, vals, width=0.55, color=colors, edgecolor="white", zorder=3)
    for xi, v in zip(x, vals):
        ax.annotate(f"{v:.3f}", (xi, v + 0.01), ha="center", va="bottom",
                    fontsize=12, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, max(0.1, (max(vals) if vals else 0.1) * 1.25))
    ax.set_ylabel(r"Partial $\eta^2$")
    ax.set_title(title)
    return _save(fig, path)


# --------------------------------------------------------------------------- #
# make_all — regenerate the standard figure set for a saved run
# --------------------------------------------------------------------------- #
def make_all(run_dir: Union[str, Path]) -> dict[str, Path]:
    """Load a saved run (matches.jsonl + metrics.csv) and emit the figure set.

    Groups the run's matches by ``cell_id``, builds per-cell summaries via
    ``metrics.report.cell_summary`` (re-deserializing each MatchResult), and
    writes whichever standard figures the data supports into ``run_dir/figures``:
      * ``lockin_bar.png``      — always (cooperation cells)
      * ``coop_curves.png``     — when any cell has a coop series
      * ``refusal_panel.png``   — always
      * ``price_trajectories.png`` — when any market match carries prices

    Returns a ``{name: path}`` map of what was written.
    """
    run_dir = Path(run_dir)
    out_dir = run_dir / "figures"
    out_dir.mkdir(parents=True, exist_ok=True)

    results = _load_matches(run_dir / "matches.jsonl")
    if not results:
        raise FileNotFoundError(f"no matches.jsonl found under {run_dir}")

    # group by cell
    by_cell: dict[str, list[Any]] = {}
    for r in results:
        cid = _cell_id_of(r)
        by_cell.setdefault(cid, []).append(r)

    # per-cell summaries via the metrics contract (live objects -> cell_summary)
    summaries = _cell_summaries(by_cell)

    written: dict[str, Path] = {}

    coop_cells = [s for s in summaries if not s.get("is_market_game")]
    if coop_cells:
        written["lockin_bar"] = lockin_bar(coop_cells, out_dir / "lockin_bar.png")
        # coop curves keyed by a short channel label
        rbc = {
            (CHANNEL_LABELS.get(_channel_of(rs[0]), cid).replace("\n", " ")): rs
            for cid, rs in by_cell.items()
            if not _is_market(rs[0])
        }
        if rbc:
            written["coop_curves"] = coop_curves(rbc, out_dir / "coop_curves.png")

    if summaries:
        written["refusal_panel"] = refusal_panel(summaries, out_dir / "refusal_panel.png")

    market_results = [r for r in results if _is_market(r) and _extract_price_series(r)]
    if market_results:
        written["price_trajectories"] = price_trajectories(
            market_results, out_dir / "price_trajectories.png"
        )

    return written


# --------------------------------------------------------------------------- #
# Loading / adapter helpers — work with both live MatchResults and jsonable dicts
# --------------------------------------------------------------------------- #
def _attr(obj: Any, name: str, default: Any = None) -> Any:
    """Get ``name`` from a dataclass-ish object or a plain dict."""
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _rounds_of(result: Any) -> list[Any]:
    return _attr(result, "rounds", []) or []


def _as_list(x: Any) -> list[Any]:
    if isinstance(x, (list, tuple)):
        return list(x)
    return [x]


def _cell_id_of(result: Any) -> str:
    spec = _attr(result, "spec", {})
    return _attr(spec, "cell_id", "cell") or "cell"


def _channel_of(result: Any) -> Optional[str]:
    spec = _attr(result, "spec", {})
    ch = _attr(spec, "channel")
    return _attr(ch, "value", ch) if not isinstance(ch, str) else ch


def _is_market(result: Any) -> bool:
    bm = _benchmarks_of(result)
    return "p_competitive" in bm and "p_monopoly" in bm


def _coop_series_of(result: Any) -> list[float]:
    """Per-round coop series, recomputed for live results or read from metrics."""
    # live MatchResult -> use the metrics primitive (authoritative)
    if not isinstance(result, dict):
        try:
            from ..metrics.core import coop_rate_series

            return list(coop_rate_series(result))
        except Exception:
            pass
    # jsonable dict -> prefer the stored series, else derive from rounds
    metrics = _attr(result, "metrics") or {}
    if isinstance(metrics, dict) and metrics.get("coop_series"):
        return list(metrics["coop_series"])
    series: list[float] = []
    for rnd in _rounds_of(result):
        moves = _attr(rnd, "moves") or {}
        flags = []
        for mv in moves.values():
            action = _attr(mv, "action")
            coop = _attr(action, "cooperative") if action else None
            if coop is None:
                continue
            flags.append(1.0 if coop else 0.0)
        if flags:
            series.append(mean(flags))
    return series


def _load_matches(jsonl_path: Union[str, Path]) -> list[Any]:
    """Load matches.jsonl, reconstructing MatchResult objects when possible.

    Falls back to the raw jsonable dicts (which all the adapter helpers accept)
    if the schemas can't be reconstructed, so figures still render off a run dir.
    """
    jsonl_path = Path(jsonl_path)
    if not jsonl_path.exists():
        return []
    raw = [json.loads(line) for line in jsonl_path.read_text().splitlines() if line.strip()]
    try:
        return [_rehydrate(d) for d in raw]
    except Exception:
        return raw


def _rehydrate(d: dict[str, Any]) -> Any:
    """Best-effort reconstruction of a MatchResult from its jsonable dict.

    Only the fields the figures/metrics actually read are reconstructed; the
    rest are passed through, since the adapter helpers tolerate dicts."""
    from ..schemas import (
        Action, AgentMove, ChannelLevel, GameSpec, MatchResult, MatchSpec,
        PlayerKind, PlayerSpec, RefusalCode, RoundRecord,
    )

    spec_d = d.get("spec", {})
    game_d = spec_d.get("game", {}) or {}
    players = [
        PlayerSpec(seat=p.get("seat"), kind=PlayerKind(p.get("kind", "llm")),
                   ref=p.get("ref", ""))
        for p in spec_d.get("players", [])
    ]
    spec = MatchSpec(
        experiment_id=spec_d.get("experiment_id", ""),
        cell_id=spec_d.get("cell_id", "cell"),
        game=GameSpec(name=game_d.get("name", "game"),
                      params=game_d.get("params", {}) or {},
                      familiarity=game_d.get("familiarity", "canonical")),
        channel=ChannelLevel(spec_d.get("channel", "L0_none")),
        epistemic=__import__("rival_arena.schemas", fromlist=["EpistemicSpec"]).EpistemicSpec(),
        players=players,
        seed=int(spec_d.get("seed", 0)),
    )
    rounds = []
    for rd in d.get("rounds", []):
        moves = {}
        for seat, mv in (rd.get("moves", {}) or {}).items():
            act_d = mv.get("action")
            action = (
                Action(label=act_d.get("label", ""), value=act_d.get("value"),
                       cooperative=act_d.get("cooperative"))
                if act_d else None
            )
            moves[seat] = AgentMove(
                seat=seat, action=action, message=mv.get("message"),
                promise=mv.get("promise"),
                refusal=RefusalCode(mv.get("refusal", "clean")),
            )
        rounds.append(RoundRecord(
            round_index=rd.get("round_index", 0), moves=moves,
            payoffs=rd.get("payoffs", {}) or {}, extra=rd.get("extra", {}) or {},
        ))
    return MatchResult(spec=spec, rounds=rounds,
                       manifest=d.get("manifest", {}) or {},
                       metrics=d.get("metrics", {}) or {})


def _cell_summaries(by_cell: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Build per-cell summary dicts via the metrics contract when possible."""
    summaries = []
    try:
        from ..metrics.report import cell_summary

        for cid, rs in by_cell.items():
            s = cell_summary(rs, cell_id=cid)
            lp = None
            try:
                from ..metrics.stats import lockin_proportion

                lp = lockin_proportion(rs)
            except Exception:
                pass
            if lp:
                s["k_locked"] = lp.get("k_locked")
                s["n"] = lp.get("n")
            summaries.append(s)
    except Exception:
        # degrade: derive a minimal summary off stored metrics
        for cid, rs in by_cell.items():
            flags = [bool(_attr(r, "metrics", {}).get("locked_in")) for r in rs
                     if _attr(r, "metrics", {}).get("locked_in") is not None]
            n = len(flags)
            k = sum(flags)
            summaries.append({
                "cell_id": cid, "channel": _channel_of(rs[0]),
                "n_matches": len(rs), "lockin_proportion": (k / n if n else 0.0),
                "k_locked": k, "n": n, "wilson_lo": 0.0, "wilson_hi": 0.0,
                "refusal_rate": 0.0, "is_market_game": _is_market(rs[0]),
            })
    return summaries


def _write_plotly(fig, path: Union[str, Path]) -> Path:
    """Write a plotly figure as HTML, plus a PNG via kaleido if available."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    html = path.with_suffix(".html")
    fig.write_html(str(html))
    png = path.with_suffix(".png")
    try:
        fig.write_image(str(png))
        return png
    except Exception:
        return html


# --------------------------------------------------------------------------- #
# Synthetic demo — emits the headline figures to /tmp without a real run.
# --------------------------------------------------------------------------- #
def _demo(out_dir: Union[str, Path] = "/tmp") -> dict[str, Path]:
    """Render the standard figures from a tiny synthetic dataset to ``out_dir``.

    Used to verify figures render end-to-end with no LLM run / no real data:
        python3 -c "import rival_arena.viz.figures as f; f._demo()"
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    # --- A1 lock-in: the "0/20 -> 15/20" money figure ---
    fake_cells = [
        {"cell_id": "A1/L0", "channel": "L0_none", "n_matches": 20,
         "lockin_proportion": 0.0, "k_locked": 0, "wilson_lo": 0.0, "wilson_hi": 0.16,
         "refusal_rate": 0.02, "is_market_game": False},
        {"cell_id": "A1/L1", "channel": "L1_signal", "n_matches": 20,
         "lockin_proportion": 0.30, "k_locked": 6, "wilson_lo": 0.15, "wilson_hi": 0.52,
         "refusal_rate": 0.03, "is_market_game": False},
        {"cell_id": "A1/L2", "channel": "L2_observed", "n_matches": 20,
         "lockin_proportion": 0.60, "k_locked": 12, "wilson_lo": 0.39, "wilson_hi": 0.78,
         "refusal_rate": 0.06, "is_market_game": False},
        {"cell_id": "A1/L3", "channel": "L3_private", "n_matches": 20,
         "lockin_proportion": 0.75, "k_locked": 15, "wilson_lo": 0.53, "wilson_hi": 0.89,
         "refusal_rate": 0.11, "is_market_game": False},
    ]
    paths["lockin_bar"] = lockin_bar(fake_cells, out / "demo_lockin_bar.png")
    paths["refusal_panel"] = refusal_panel(fake_cells, out / "demo_refusal_panel.png")

    # --- A1 coop curves: defection-ish L0 vs locking-in L3 ---
    def _curve(base, climb, n=30, noise=0.04, seed=0):
        rng = np.random.default_rng(seed)
        return [float(np.clip(base + climb * (t / n) + rng.normal(0, noise), 0, 1))
                for t in range(n)]
    rbc = {
        "L0 none": [_curve(0.3, -0.15, seed=s) for s in range(8)],
        "L3 private": [_curve(0.4, 0.55, seed=10 + s) for s in range(8)],
    }
    # wrap each fake series as a jsonable dict carrying metrics['coop_series']
    rbc = {k: [{"metrics": {"coop_series": s}, "rounds": []} for s in v]
           for k, v in rbc.items()}
    paths["coop_curves"] = coop_curves(rbc, out / "demo_coop_curves.png")

    # --- B1 price money-shot: two sellers climbing toward monopoly ---
    benchmarks = {"p_competitive": 1.0, "p_monopoly": 3.0}

    def _fake_market_result(seed=0):
        rng = np.random.default_rng(seed)
        rounds = []
        pa, pb = 1.1, 1.05
        for t in range(25):
            pa = float(np.clip(pa + 0.085 + rng.normal(0, 0.05), 1.0, 3.1))
            pb = float(np.clip(pb + 0.080 + rng.normal(0, 0.05), 1.0, 3.1))
            rounds.append({"round_index": t, "moves": {}, "payoffs": {},
                           "extra": {"prices": {"A": pa, "B": pb}}})
        return {"spec": {"cell_id": "B1/L3"}, "rounds": rounds,
                "manifest": {"benchmarks": benchmarks}, "metrics": {}}

    market_runs = [_fake_market_result(s) for s in range(6)]
    paths["price_trajectories"] = price_trajectories(
        market_runs, out / "demo_price_trajectories.png", benchmarks=benchmarks)

    # --- A4 dose-response: two families, different slopes ---
    x = [0.5, 1.0, 2.0, 4.0]
    coop = {
        "Qwen-family": [0.85, 0.72, 0.45, 0.20],
        "Llama-family": [0.80, 0.55, 0.22, 0.08],
    }
    cis = {
        "Qwen-family": [(0.75, 0.92), (0.60, 0.82), (0.33, 0.57), (0.10, 0.32)],
        "Llama-family": [(0.68, 0.89), (0.43, 0.67), (0.12, 0.34), (0.02, 0.18)],
    }
    paths["dose_response"] = dose_response(x, coop, cis, out / "demo_dose_response.png")

    # --- A3 partial-eta^2: channel dominates, origin is second-order ---
    eta = {"channel": 0.41, "regime": 0.18, "origin": 0.03}
    paths["origin_partial_eta"] = origin_partial_eta(eta, out / "demo_origin_partial_eta.png")

    for name, p in paths.items():
        size = Path(p).stat().st_size if Path(p).exists() else 0
        print(f"  {name:22s} -> {p}  ({size} bytes)")
    return paths


if __name__ == "__main__":
    print("Rendering synthetic demo figures to /tmp ...")
    _demo("/tmp")
    print("done.")
