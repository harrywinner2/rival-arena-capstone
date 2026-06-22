"""Metrics workstream — measures, message-structure / covert diagnostics, the
factorial statistics, and the definition-of-done assembler (experiments.md §2,
§5, §6.5).

Public entry points (the surface other workstreams import):
  * ``attach_metrics(result)``         — stash per-match metrics on result.metrics
  * ``save_run(results, exp_id)``      — write manifest + raw logs + metrics table
  * ``cell_summary(results)``          — the per-cell aggregate consumed by viz
  * ``summarize_match(result)``        — flat per-match metric dict
  * ``lockin_proportion(results)``     — k/n + Wilson CI for a cell (P17)
  * ``wilson_interval(k, n)``          — Wilson score CI (P17)
  * ``bootstrap_ci(values)``           — percentile bootstrap CI (§5)
  * ``factorial_anova(df, dv, fac)``   — partial-eta2 variance decomposition (§5)
  * ``tost_equivalence(a, b, bound)``  — powered origin null (P5)
"""

from __future__ import annotations

from .core import summarize_match
from .message import summarize_messages
from .report import attach_metrics, cell_summary, save_run
from .stats import (
    bootstrap_ci,
    factorial_anova,
    lockin_proportion,
    tost_equivalence,
    wilson_interval,
)

__all__ = [
    "attach_metrics",
    "save_run",
    "cell_summary",
    "summarize_match",
    "summarize_messages",
    "lockin_proportion",
    "wilson_interval",
    "bootstrap_ci",
    "factorial_anova",
    "tost_equivalence",
]
