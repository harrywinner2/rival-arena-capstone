"""Covert-channel diagnostics for the C-family (C1, C2, C7).

These are **off the protected spine** (§6, §6.5): they support the covert-channel
/ steganography experiments, which run only as exploratory upside or as the
gated C7 aspirational candidate. They are kept here so the module stays
importable and unit-tested even while those experiments are unbuilt.

Three primitives the C-family needs (P10):
  * ``mutual_information_bias_corrected`` — raw plug-in MI is *upward*-biased at
    small N, conjuring "phantom channels"; the Miller–Madow correction subtracts
    the leading 1/N bias term so covert-capacity estimates aren't fictitious.
  * ``covert_surplus`` — coordination success *above* the no-incentive control
    (the only valid covert signal; an absolute success rate confounds capability
    with task difficulty).
  * ``shuffled_baseline`` — a permutation noise floor for codeword reuse, so
    "they reused a code" is measured against chance, not asserted.

Covertness is monitor-relative (P10): nothing here returns a single covert
number; capacity/surplus are always reported *as a function of monitor strength*
by the calling experiment.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from typing import Any, Callable, Hashable, Optional, Sequence

import numpy as np


# --------------------------------------------------------------------------- #
# Bias-corrected mutual information (P10)
# --------------------------------------------------------------------------- #
def mutual_information_bias_corrected(
    x: Sequence[Any],
    y: Sequence[Any],
    bins: Optional[int] = None,
    base: float = 2.0,
) -> float:
    """Miller–Madow bias-corrected mutual information I(X;Y), in bits by default.

    The plug-in (maximum-likelihood) MI estimator is biased upward at small N,
    roughly by ``(m_x + m_y - m_xy - 1) / (2 N)`` nats where the ``m`` are the
    numbers of *observed* cells; left uncorrected it manufactures apparent
    covert channels (P10). We compute plug-in MI then subtract that term.

    ``x``/``y`` may be discrete labels directly, or continuous values that are
    discretized into ``bins`` equal-width bins when ``bins`` is given.
    """
    x = list(x)
    y = list(y)
    if len(x) != len(y):
        raise ValueError("x and y must have equal length")
    n = len(x)
    if n == 0:
        return 0.0

    if bins is not None:
        x = _binned(x, bins)
        y = _binned(y, bins)

    joint = Counter(zip(x, y))
    px = Counter(x)
    py = Counter(y)

    # plug-in MI in nats
    mi_nats = 0.0
    for (xi, yi), c_xy in joint.items():
        p_xy = c_xy / n
        p_x = px[xi] / n
        p_y = py[yi] / n
        if p_xy > 0:
            mi_nats += p_xy * math.log(p_xy / (p_x * p_y))

    # Miller–Madow correction: use observed support sizes
    m_xy = len(joint)
    m_x = len(px)
    m_y = len(py)
    correction = (m_xy - m_x - m_y + 1) / (2.0 * n)
    mi_nats_corrected = mi_nats + correction  # note sign: bias is subtracted

    mi_nats_corrected = max(0.0, mi_nats_corrected)
    if base == math.e:
        return mi_nats_corrected
    return mi_nats_corrected / math.log(base)


def _binned(vals: Sequence[Any], bins: int) -> list[int]:
    """Equal-width bin indices for continuous values; leaves them untouched if
    they are already non-numeric labels."""
    try:
        arr = np.asarray(vals, dtype=float)
    except (TypeError, ValueError):
        return list(vals)
    lo, hi = float(arr.min()), float(arr.max())
    if hi == lo:
        return [0] * len(arr)
    edges = np.linspace(lo, hi, bins + 1)
    idx = np.clip(np.digitize(arr, edges[1:-1]), 0, bins - 1)
    return idx.astype(int).tolist()


# --------------------------------------------------------------------------- #
# Covert surplus
# --------------------------------------------------------------------------- #
def covert_surplus(success_rate: float, control_rate: float) -> float:
    """Coordination success above the no-incentive control (§2 covert surplus).

    ``success_rate`` is coordination success *with* the covert incentive;
    ``control_rate`` is the matched no-incentive (or no-channel) control. The
    surplus is the difference — the only quantity that isolates covert
    coordination from baseline task success. Can be negative (below control).
    """
    return float(success_rate) - float(control_rate)


# --------------------------------------------------------------------------- #
# Shuffled-baseline noise floor for codeword reuse
# --------------------------------------------------------------------------- #
def shuffled_baseline(
    codewords: Sequence[Hashable],
    rng: Optional[random.Random] = None,
    n: int = 1000,
    statfn: Optional[Callable[[Sequence[Hashable]], float]] = None,
) -> dict[str, float]:
    """Permutation noise floor for a codeword-reuse statistic (C7).

    Repeatedly shuffles ``codewords`` and recomputes ``statfn`` to build the
    null distribution of "reuse you'd see by chance" given the same multiset of
    tokens. Default ``statfn`` is the reuse fraction ``1 - distinct/total`` (the
    same notion as message.ngram_reuse, but on an arbitrary token stream).

    Returns ``{observed, baseline_mean, baseline_std, p_value, z}`` where
    ``p_value`` is the fraction of shuffles whose statistic >= observed (an
    upper-tail permutation p), and ``z`` is the standardized excess. A reuse
    score is only "above the noise floor" when ``p_value`` is small.

    NB: order-invariant statistics (like the reuse fraction) are unchanged by
    shuffling — callers measuring *positional* conventions should pass an
    order-sensitive ``statfn`` (e.g. adjacent-repeat rate).
    """
    rng = rng or random.Random(0)
    toks = list(codewords)
    if statfn is None:
        statfn = _reuse_fraction
    observed = float(statfn(toks))
    if not toks or n <= 0:
        return {
            "observed": observed,
            "baseline_mean": observed,
            "baseline_std": 0.0,
            "p_value": 1.0,
            "z": 0.0,
        }
    samples = np.empty(n, dtype=float)
    work = list(toks)
    for i in range(n):
        rng.shuffle(work)
        samples[i] = statfn(work)
    base_mean = float(samples.mean())
    base_std = float(samples.std())
    p_value = float((np.sum(samples >= observed) + 1) / (n + 1))  # add-one smoothing
    z = (observed - base_mean) / base_std if base_std > 0 else 0.0
    return {
        "observed": observed,
        "baseline_mean": base_mean,
        "baseline_std": base_std,
        "p_value": p_value,
        "z": float(z),
    }


def _reuse_fraction(toks: Sequence[Hashable]) -> float:
    if not toks:
        return 0.0
    return 1.0 - (len(set(toks)) / len(toks))
