"""viz workstream — publishable static figures + a live/replay dashboard.

``figures`` has no Dash dependency (it only needs matplotlib/numpy, with
optional plotly for interactive variants), so importing this package never
requires Dash. ``run_dashboard`` imports Dash lazily and degrades gracefully if
it is not installed.
"""

from __future__ import annotations

from .figures import (
    coop_curves,
    dose_response,
    lockin_bar,
    make_all,
    origin_partial_eta,
    price_trajectories,
    refusal_panel,
)


def run_dashboard(run_dir: str, port: int = 8050) -> None:
    """Launch the Dash replay app (lazy import so viz works without Dash)."""
    from .dashboard import run_dashboard as _run

    return _run(run_dir, port=port)


__all__ = [
    "lockin_bar",
    "price_trajectories",
    "coop_curves",
    "dose_response",
    "refusal_panel",
    "origin_partial_eta",
    "make_all",
    "run_dashboard",
]
