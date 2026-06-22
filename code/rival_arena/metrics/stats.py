"""Factorial / confirmatory statistics (experiments.md §2, §5, §6).

This is the confirmatory machinery the spine (A1, B1, A3) leans on:
  * ``wilson_interval`` — Wilson score CI for the lock-in proportion (P17); the
    headline outcome is a proportion of matches, reported with this interval.
  * ``lockin_proportion`` — packages a cell's matches into k/n + Wilson CI.
  * ``bootstrap_ci`` — percentile bootstrap CI for any continuous statistic
    (coop end-state, K) — the §5 "bootstrapped CIs" definition-of-done item.
  * ``factorial_anova`` — OLS variance decomposition with partial eta-squared per
    factor (the channel / regime / origin decomposition, §5).
  * ``tost_equivalence`` — two one-sided t-tests for the *powered* origin null
    (P5); an unpowered null is "inconclusive", not evidence of absence.
  * ``power_for_proportions`` — n/group to rule out an effect bigger than the
    pre-registered equivalence bound (P5), so a null is earned.

These operate over *collections* of matches / per-match rows, unlike core.py.
"""

from __future__ import annotations

import math
from statistics import mean as _mean
from typing import Any, Callable, Optional, Sequence

import numpy as np
from scipy import stats as _sps

from .core import locked_in


# --------------------------------------------------------------------------- #
# Wilson score interval (P17)
# --------------------------------------------------------------------------- #
def wilson_interval(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score confidence interval for a binomial proportion (P17).

    The lock-in proportion is small-N and often near 0 or 1, where the normal
    approximation breaks; the Wilson interval stays inside [0,1] and is the §2
    prescribed interval. Implemented directly from the closed form.

    Returns ``(lo, hi)``; for ``n == 0`` returns ``(0.0, 1.0)`` (total ignorance).
    """
    if n <= 0:
        return (0.0, 1.0)
    phat = successes / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (phat + z2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(phat * (1 - phat) / n + z2 / (4 * n * n))
    lo = max(0.0, center - half)
    hi = min(1.0, center + half)
    return (lo, hi)


def lockin_proportion(results: Sequence[Any], z: float = 1.96) -> dict[str, Any]:
    """Lock-in proportion for one cell of matches (P17).

    Matches whose coop axis is undefined (locked_in is None, e.g. zero-sum) are
    excluded from the denominator. Returns
    ``{n, k_locked, proportion, wilson_lo, wilson_hi}``.
    """
    flags = [locked_in(r) for r in results]
    flags = [f for f in flags if f is not None]
    n = len(flags)
    k = sum(1 for f in flags if f)
    prop = (k / n) if n else None
    lo, hi = wilson_interval(k, n, z)
    return {
        "n": n,
        "k_locked": k,
        "proportion": prop,
        "wilson_lo": lo,
        "wilson_hi": hi,
    }


# --------------------------------------------------------------------------- #
# Percentile bootstrap
# --------------------------------------------------------------------------- #
def bootstrap_ci(
    values: Sequence[float],
    statfn: Callable[[Sequence[float]], float] = _mean,
    n: int = 10000,
    alpha: float = 0.05,
    seed: int = 0,
) -> tuple[Optional[float], Optional[float]]:
    """Percentile bootstrap CI for ``statfn`` over ``values`` (§5 bootstrapped CIs).

    Resamples ``values`` with replacement ``n`` times and returns the
    ``[alpha/2, 1-alpha/2]`` percentiles of the statistic. Returns ``(None, None)``
    for empty input. With a single value the interval collapses to that value.
    """
    clean = [v for v in values if v is not None]
    if not clean:
        return (None, None)
    if len(clean) == 1:
        v = float(statfn(clean))
        return (v, v)
    rng = np.random.default_rng(seed)
    arr = np.asarray(clean, dtype=float)
    idx = rng.integers(0, len(arr), size=(n, len(arr)))
    samples = np.array([statfn(arr[row]) for row in idx], dtype=float)
    lo = float(np.percentile(samples, 100 * alpha / 2))
    hi = float(np.percentile(samples, 100 * (1 - alpha / 2)))
    return (lo, hi)


# --------------------------------------------------------------------------- #
# Factorial ANOVA with partial eta-squared (§5)
# --------------------------------------------------------------------------- #
def factorial_anova(df, dv: str, factors: Sequence[str]):
    """OLS factorial ANOVA with partial eta-squared per factor (§5).

    Fits ``dv ~ C(f1) + C(f2) + ...`` (main effects) via statsmodels, runs a
    Type-II ANOVA, and appends ``partial_eta_sq = SS_effect / (SS_effect +
    SS_resid)`` — the channel / regime / origin variance decomposition. ``df`` is
    a pandas DataFrame of per-match rows (e.g. from ``metrics.csv``).

    Returns the ANOVA table (a pandas DataFrame) with an added
    ``partial_eta_sq`` column. Rows with a NaN ``dv`` are dropped first.
    """
    import pandas as pd  # local import: pandas only needed for the stats layer
    import statsmodels.api as sm
    from statsmodels.formula.api import ols

    data = df.dropna(subset=[dv]).copy()
    if data.empty:
        raise ValueError(f"no rows with a non-null {dv!r}")

    terms = " + ".join(f"C({f})" for f in factors)
    formula = f"Q('{dv}') ~ {terms}" if terms else f"Q('{dv}') ~ 1"
    model = ols(formula, data=data).fit()
    table = sm.stats.anova_lm(model, typ=2)

    ss_resid = table.loc["Residual", "sum_sq"] if "Residual" in table.index else float("nan")
    eta = []
    for idx in table.index:
        if idx == "Residual":
            eta.append(float("nan"))
            continue
        ss_effect = table.loc[idx, "sum_sq"]
        denom = ss_effect + ss_resid
        eta.append(ss_effect / denom if denom and not math.isnan(denom) else float("nan"))
    table["partial_eta_sq"] = eta
    return table


# --------------------------------------------------------------------------- #
# TOST equivalence (P5 — the powered origin null)
# --------------------------------------------------------------------------- #
def tost_equivalence(
    a: Sequence[float], b: Sequence[float], bound: float, alpha: float = 0.05
) -> dict[str, Any]:
    """Two one-sided t-tests for equivalence of two means within +-``bound`` (P5).

    Used for the origin null (A3): before claiming "origin does not move the
    effect" we pre-specify an equivalence bound and test that the mean
    difference lies inside +-bound. Equivalence is declared when *both* one-sided
    tests reject at ``alpha`` (i.e. the larger of the two p-values < alpha).

    Returns ``{equivalent, p, p_lower, p_upper, mean_diff, bound, n_a, n_b}``.
    """
    a = [x for x in a if x is not None]
    b = [x for x in b if x is not None]
    na, nb = len(a), len(b)
    if na < 2 or nb < 2:
        return {
            "equivalent": False,
            "p": 1.0,
            "p_lower": 1.0,
            "p_upper": 1.0,
            "mean_diff": (float(_mean(a)) - float(_mean(b))) if (a and b) else None,
            "bound": bound,
            "n_a": na,
            "n_b": nb,
        }
    ma, mb = float(np.mean(a)), float(np.mean(b))
    va, vb = float(np.var(a, ddof=1)), float(np.var(b, ddof=1))
    diff = ma - mb
    se = math.sqrt(va / na + vb / nb)
    if se == 0:
        equivalent = abs(diff) < bound
        p = 0.0 if equivalent else 1.0
        return {
            "equivalent": equivalent,
            "p": p, "p_lower": p, "p_upper": p,
            "mean_diff": diff, "bound": bound, "n_a": na, "n_b": nb,
        }
    # Welch–Satterthwaite df
    dfree = (va / na + vb / nb) ** 2 / (
        (va / na) ** 2 / (na - 1) + (vb / nb) ** 2 / (nb - 1)
    )
    # H0_lower: diff <= -bound  -> upper-tail test
    t_lower = (diff + bound) / se
    p_lower = float(_sps.t.sf(t_lower, dfree))
    # H0_upper: diff >= +bound  -> lower-tail test
    t_upper = (diff - bound) / se
    p_upper = float(_sps.t.cdf(t_upper, dfree))
    p = max(p_lower, p_upper)
    return {
        "equivalent": p < alpha,
        "p": p,
        "p_lower": p_lower,
        "p_upper": p_upper,
        "mean_diff": diff,
        "bound": bound,
        "n_a": na,
        "n_b": nb,
    }


# --------------------------------------------------------------------------- #
# Power for two proportions (P5)
# --------------------------------------------------------------------------- #
def power_for_proportions(
    p1: float, p2: float, alpha: float = 0.05, power: float = 0.8
) -> int:
    """Sample size per group for a two-sided two-proportion test (P5).

    Lets us show the design can *rule out* an effect bigger than the
    equivalence bound: if ``|p1 - p2|`` is the smallest difference we want to
    detect, this returns the per-cell match count needed at ``alpha`` / ``power``.
    Uses the standard normal-approximation formula (pooled & unpooled averaged
    via the conventional ``(zα·√(2p̄q̄) + zβ·√(p1q1+p2q2))²`` numerator).
    """
    if p1 == p2:
        return 0
    z_alpha = _sps.norm.ppf(1 - alpha / 2)
    z_beta = _sps.norm.ppf(power)
    pbar = (p1 + p2) / 2
    qbar = 1 - pbar
    q1, q2 = 1 - p1, 1 - p2
    num = (z_alpha * math.sqrt(2 * pbar * qbar) + z_beta * math.sqrt(p1 * q1 + p2 * q2)) ** 2
    n = num / ((p1 - p2) ** 2)
    return int(math.ceil(n))
