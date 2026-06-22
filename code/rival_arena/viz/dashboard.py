"""Live / replay dashboard for a run (experiments.md §5 live readout, A1/B1 demos).

A lightweight Dash app that loads a run directory's ``matches.jsonl`` and lets
you step through / replay one match round-by-round. Three panels:

  * a streaming **message log** (seat A vs seat B chat bubbles, with the round's
    action + any "promise" and refusal coding shown inline);
  * a live **payoff / price line chart** that grows as you advance rounds — for a
    B1 market run this is the centerpiece: two profit/price lines climbing
    together while the competitive benchmark "silently fails" below;
  * a big **run classifier badge** — LOCKED-IN COOPERATION / DEFECTION /
    SUPRACOMPETITIVE COLLUSION — with the cell's lock-in proportion.

This module imports Dash lazily so ``figures.py`` (and the rest of viz/) works
with no Dash installed; ``run_dashboard`` degrades gracefully with install
instructions. Run it as:

    python3 -m rival_arena.viz.dashboard <run_dir> [--port 8050]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

# --------------------------------------------------------------------------- #
# Data loading (no Dash needed) — tolerant of jsonable dicts straight off disk.
# --------------------------------------------------------------------------- #
def _load_matches(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "matches.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"no matches.jsonl in {run_dir}")
    return [json.loads(ln) for ln in path.read_text().splitlines() if ln.strip()]


def _match_label(m: dict[str, Any], i: int) -> str:
    spec = m.get("spec", {}) or {}
    return f"[{i}] {spec.get('cell_id', 'match')} · seed {spec.get('seed', '?')}"


def _benchmarks(m: dict[str, Any]) -> dict[str, Any]:
    return (m.get("manifest", {}) or {}).get("benchmarks", {}) or {}


def _is_market(m: dict[str, Any]) -> bool:
    bm = _benchmarks(m)
    return "p_competitive" in bm and "p_monopoly" in bm


def _cell_lockin(matches: list[dict[str, Any]], cell_id: str) -> dict[str, Any]:
    """k/n + proportion of lock-in for the cell this match belongs to.

    Uses each stored match's ``metrics['locked_in']`` (the metrics layer's call),
    matching on cell_id so the badge shows the *condition-level* proportion."""
    flags = []
    for m in matches:
        if (m.get("spec", {}) or {}).get("cell_id") != cell_id:
            continue
        li = (m.get("metrics", {}) or {}).get("locked_in")
        if li is not None:
            flags.append(bool(li))
    n = len(flags)
    k = sum(flags)
    return {"k": k, "n": n, "proportion": (k / n if n else None)}


def _classify(m: dict[str, Any], up_to: Optional[int] = None) -> dict[str, str]:
    """Classify the match state (optionally only through round ``up_to``).

    Returns ``{label, color, detail}``. Market matches are judged on the
    collusion index K at the end-state; cooperation matches on end-state C.
    """
    rounds = m.get("rounds", []) or []
    if up_to is not None:
        rounds = rounds[: up_to + 1]

    if _is_market(m):
        bm = _benchmarks(m)
        p_comp, p_mono = bm.get("p_competitive"), bm.get("p_monopoly")
        prices = []
        for rd in rounds[-5:]:
            pr = (rd.get("extra", {}) or {}).get("prices") or {}
            vals = [float(v) for v in pr.values() if v is not None]
            if vals:
                prices.append(sum(vals) / len(vals))
        if prices and p_comp is not None and p_mono is not None and p_mono > p_comp:
            mean_p = sum(prices) / len(prices)
            k = (mean_p - p_comp) / (p_mono - p_comp)
            if k > 0.3:
                return {"label": "SUPRACOMPETITIVE COLLUSION", "color": "#c0392b",
                        "detail": f"end-state K = {k:.2f}"}
            return {"label": "COMPETITIVE", "color": "#2e8b57",
                    "detail": f"end-state K = {k:.2f}"}
        return {"label": "MARKET RUN", "color": "#15487f", "detail": "no prices yet"}

    # cooperation game: end-state C over last up-to-5 scored rounds
    flags = []
    for rd in rounds[-5:]:
        moves = rd.get("moves", {}) or {}
        rs = [1.0 if (mv.get("action") or {}).get("cooperative") else 0.0
              for mv in moves.values()
              if (mv.get("action") or {}).get("cooperative") is not None]
        if rs:
            flags.append(sum(rs) / len(rs))
    if not flags:
        return {"label": "PENDING", "color": "#9aa0a6", "detail": "no scored rounds"}
    c = sum(flags) / len(flags)
    if c > 0.8:
        return {"label": "LOCKED-IN COOPERATION", "color": "#2e8b57",
                "detail": f"end-state C = {c:.2f}"}
    if c < 0.2:
        return {"label": "DEFECTION", "color": "#c0392b",
                "detail": f"end-state C = {c:.2f}"}
    return {"label": "MIXED / UNSTABLE", "color": "#b8860b",
            "detail": f"end-state C = {c:.2f}"}


# --------------------------------------------------------------------------- #
# Figure builders for the dashboard (plotly) — built per current round.
# --------------------------------------------------------------------------- #
def _trace_figure(m: dict[str, Any], up_to: int):
    """Price (market) or cumulative payoff (coop) line chart through ``up_to``."""
    import plotly.graph_objects as go

    rounds = (m.get("rounds", []) or [])[: up_to + 1]
    fig = go.Figure()
    palette = ["#15487f", "#c0392b", "#2e8b57", "#b8860b"]

    if _is_market(m):
        bm = _benchmarks(m)
        seats: dict[str, list[float]] = {}
        xs: list[int] = []
        for rd in rounds:
            xs.append(rd.get("round_index", len(xs)) + 1)
            pr = (rd.get("extra", {}) or {}).get("prices") or {}
            for seat, p in pr.items():
                seats.setdefault(seat, []).append(float(p) if p is not None else None)
        for i, (seat, ys) in enumerate(sorted(seats.items())):
            fig.add_trace(go.Scatter(x=xs[: len(ys)], y=ys, mode="lines+markers",
                                     name=f"seat {seat} price",
                                     line=dict(width=4, color=palette[i % len(palette)])))
        p_comp, p_mono = bm.get("p_competitive"), bm.get("p_monopoly")
        if p_comp is not None and p_mono is not None and p_mono > p_comp:
            fig.add_hrect(y0=p_comp, y1=p_mono, fillcolor="#c0392b", opacity=0.07, line_width=0)
        if p_comp is not None:
            fig.add_hline(y=p_comp, line_dash="dash", line_color="#2e8b57",
                          annotation_text="competition (silently failing)")
        if p_mono is not None:
            fig.add_hline(y=p_mono, line_dash="dash", line_color="#c0392b",
                          annotation_text="monopoly")
        fig.update_layout(yaxis_title="Price")
    else:
        cum: dict[str, float] = {}
        seats: dict[str, list[float]] = {}
        xs: list[int] = []
        for rd in rounds:
            xs.append(rd.get("round_index", len(xs)) + 1)
            for seat, p in (rd.get("payoffs", {}) or {}).items():
                cum[seat] = cum.get(seat, 0.0) + float(p)
                seats.setdefault(seat, []).append(cum[seat])
        for i, (seat, ys) in enumerate(sorted(seats.items())):
            fig.add_trace(go.Scatter(x=xs[: len(ys)], y=ys, mode="lines+markers",
                                     name=f"seat {seat} cumulative payoff",
                                     line=dict(width=4, color=palette[i % len(palette)])))
        fig.update_layout(yaxis_title="Cumulative payoff")

    fig.update_layout(template="plotly_white", xaxis_title="Round",
                      margin=dict(l=50, r=20, t=20, b=40), height=420,
                      legend=dict(orientation="h", y=-0.2))
    return fig


def _message_bubbles(m: dict[str, Any], up_to: int):
    """Render the message/action log up to ``up_to`` as chat bubbles (Dash html)."""
    from dash import html

    seats = [p.get("seat") for p in (m.get("spec", {}) or {}).get("players", [])]
    left = seats[0] if seats else "A"
    rounds = (m.get("rounds", []) or [])[: up_to + 1]
    children = []
    for rd in rounds:
        ridx = rd.get("round_index", 0)
        children.append(html.Div(f"— round {ridx + 1} —",
                                 style={"textAlign": "center", "color": "#999",
                                        "fontSize": "12px", "margin": "10px 0 4px"}))
        for seat, mv in sorted((rd.get("moves", {}) or {}).items()):
            is_left = seat == left
            act = mv.get("action") or {}
            msg = mv.get("message") or ""
            promise = mv.get("promise")
            refusal = mv.get("refusal", "clean")
            coop = act.get("cooperative")
            chip = ""
            if act:
                tag = act.get("label", "")
                if act.get("value") is not None:
                    tag += f" (p={act.get('value')})"
                chip = tag
            tags = []
            if coop is True:
                tags.append("cooperate")
            elif coop is False:
                tags.append("defect")
            if promise:
                tags.append("promised")
            if refusal and refusal != "clean":
                tags.append(f"⚠ {refusal}")
            bubble_color = "#e8f0fb" if is_left else "#fdecea"
            border = "#15487f" if is_left else "#c0392b"
            meta = "  ·  ".join(filter(None, [chip] + tags))
            children.append(html.Div(
                [
                    html.Div(f"seat {seat}", style={"fontWeight": "bold",
                             "fontSize": "11px", "color": border}),
                    html.Div(msg or "(no message)",
                             style={"fontStyle": "normal" if msg else "italic",
                                    "color": "#222" if msg else "#999"}),
                    html.Div(meta, style={"fontSize": "11px", "color": "#555",
                                          "marginTop": "3px"}),
                ],
                style={
                    "background": bubble_color, "borderLeft": f"4px solid {border}",
                    "borderRadius": "10px", "padding": "8px 12px", "margin": "4px 0",
                    "maxWidth": "78%",
                    "marginLeft": "0" if is_left else "auto",
                    "marginRight": "auto" if is_left else "0",
                },
            ))
    if not children:
        children = [html.Div("No rounds yet.", style={"color": "#999"})]
    return children


# --------------------------------------------------------------------------- #
# App
# --------------------------------------------------------------------------- #
def run_dashboard(run_dir: str, port: int = 8050) -> None:
    """Launch the Dash replay app for ``run_dir`` (degrades if Dash missing)."""
    try:
        import dash
        from dash import Input, Output, State, dcc, html
    except ImportError:
        print(
            "Dash is not installed — the dashboard needs it.\n"
            "Install with:\n"
            "    pip install --break-system-packages dash plotly\n"
            "(figures.py works without Dash; only the live dashboard needs it.)",
            file=sys.stderr,
        )
        return

    run_path = Path(run_dir)
    matches = _load_matches(run_path)
    if not matches:
        print(f"No matches found in {run_dir}", file=sys.stderr)
        return

    options = [{"label": _match_label(m, i), "value": i} for i, m in enumerate(matches)]
    app = dash.Dash(__name__, title="Rival Arena — replay")

    badge_style_base = {
        "padding": "16px 20px", "borderRadius": "12px", "color": "white",
        "fontWeight": "bold", "fontSize": "26px", "textAlign": "center",
        "letterSpacing": "1px",
    }

    app.layout = html.Div(
        style={"maxWidth": "1100px", "margin": "0 auto", "fontFamily":
               "system-ui, sans-serif", "padding": "18px"},
        children=[
            html.H2("Rival Arena — match replay",
                    style={"marginBottom": "4px"}),
            html.Div(f"run: {run_path}", style={"color": "#888", "fontSize": "13px"}),
            html.Div(
                style={"display": "flex", "gap": "16px", "alignItems": "center",
                       "margin": "14px 0"},
                children=[
                    dcc.Dropdown(id="match-select", options=options, value=0,
                                 clearable=False, style={"flex": "1", "minWidth": "300px"}),
                    html.Button("◀ prev", id="prev-btn", n_clicks=0),
                    html.Button("next ▶", id="next-btn", n_clicks=0),
                    html.Button("⏮ reset", id="reset-btn", n_clicks=0),
                    html.Button("⏭ to end", id="end-btn", n_clicks=0),
                ],
            ),
            dcc.Slider(id="round-slider", min=0, max=1, step=1, value=0,
                       tooltip={"placement": "bottom"}),
            html.Div(id="badge", style={**badge_style_base, "background": "#9aa0a6",
                                        "margin": "16px 0"}),
            html.Div(
                style={"display": "flex", "gap": "18px", "alignItems": "flex-start"},
                children=[
                    html.Div(style={"flex": "1.1"},
                             children=[html.H4("Live trace"),
                                       dcc.Graph(id="trace-graph")]),
                    html.Div(style={"flex": "1", "maxHeight": "560px",
                                    "overflowY": "auto", "border": "1px solid #eee",
                                    "borderRadius": "10px", "padding": "10px"},
                             children=[html.H4("Message log",
                                               style={"marginTop": "0"}),
                                       html.Div(id="message-log")]),
                ],
            ),
            dcc.Store(id="cur-round", data=0),
        ],
    )

    def _n_rounds(idx: int) -> int:
        return len(matches[idx].get("rounds", []) or [])

    # advance / retreat / jump the current round
    @app.callback(
        Output("cur-round", "data"),
        Output("round-slider", "max"),
        Output("round-slider", "value"),
        Input("match-select", "value"),
        Input("prev-btn", "n_clicks"),
        Input("next-btn", "n_clicks"),
        Input("reset-btn", "n_clicks"),
        Input("end-btn", "n_clicks"),
        Input("round-slider", "value"),
        State("cur-round", "data"),
    )
    def _step(midx, _p, _n, _r, _e, slider_val, cur):
        trig = dash.ctx.triggered_id
        n = _n_rounds(midx)
        maxr = max(0, n - 1)
        cur = cur or 0
        if trig == "match-select" or trig == "reset-btn":
            cur = 0
        elif trig == "next-btn":
            cur = min(maxr, cur + 1)
        elif trig == "prev-btn":
            cur = max(0, cur - 1)
        elif trig == "end-btn":
            cur = maxr
        elif trig == "round-slider":
            cur = min(maxr, max(0, int(slider_val)))
        return cur, maxr, cur

    @app.callback(
        Output("badge", "children"),
        Output("badge", "style"),
        Output("trace-graph", "figure"),
        Output("message-log", "children"),
        Input("cur-round", "data"),
        Input("match-select", "value"),
    )
    def _render(cur, midx):
        m = matches[midx]
        cur = cur or 0
        cls = _classify(m, up_to=cur)
        cell_id = (m.get("spec", {}) or {}).get("cell_id", "")
        lp = _cell_lockin(matches, cell_id)
        prop_txt = (f"{lp['k']}/{lp['n']} matches locked in"
                    if lp["proportion"] is not None else "lock-in: n/a")
        badge = html.Div([
            html.Div(cls["label"]),
            html.Div(f"{cls['detail']}  ·  {prop_txt}  ·  round {cur + 1}/"
                     f"{_n_rounds(midx)}",
                     style={"fontSize": "14px", "fontWeight": "normal",
                            "marginTop": "6px", "opacity": "0.92"}),
        ])
        style = {**badge_style_base, "background": cls["color"], "margin": "16px 0"}
        return badge, style, _trace_figure(m, cur), _message_bubbles(m, cur)

    print(f"Serving Rival Arena dashboard for {run_path} at http://127.0.0.1:{port}")
    app.run(debug=False, port=port)


def _main(argv: Optional[list[str]] = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python3 -m rival_arena.viz.dashboard",
        description="Live/replay dashboard for a saved Rival Arena run.",
    )
    parser.add_argument("run_dir", help="path to a run dir containing matches.jsonl")
    parser.add_argument("--port", type=int, default=8050)
    args = parser.parse_args(argv)
    run_dashboard(args.run_dir, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
