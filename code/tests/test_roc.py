"""Tests for the M1 detector-evaluation helper (rival_arena/metrics/roc.py).

Pure-stdlib, no network: exercises AUC (perfect / chance / single-class), PR/AP,
the operating point, FPR-at-budget, and the calibration curve on synthetic
(score, label) data.
"""

from __future__ import annotations

import math

from rival_arena.metrics.roc import (
    auc_roc,
    average_precision,
    calibration_curve,
    evaluate_detector,
    fpr_at_budget,
    operating_point,
    operating_point_from_preds,
    roc_curve,
)


def test_auc_perfect_separator():
    s = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    y = [0, 0, 0, 1, 1, 1]
    assert auc_roc(s, y) == 1.0


def test_auc_reversed_is_zero():
    # scores anti-correlated with labels -> AUC 0
    s = [0.9, 0.8, 0.7, 0.3, 0.2, 0.1]
    y = [0, 0, 0, 1, 1, 1]
    assert auc_roc(s, y) == 0.0


def test_auc_ties_handled():
    # all identical scores -> pure chance, AUC 0.5
    s = [0.5, 0.5, 0.5, 0.5]
    y = [0, 1, 0, 1]
    assert abs(auc_roc(s, y) - 0.5) < 1e-9


def test_auc_single_class_none():
    assert auc_roc([0.1, 0.2, 0.3], [1, 1, 1]) is None
    assert auc_roc([0.1, 0.2, 0.3], [0, 0, 0]) is None


def test_roc_curve_endpoints():
    s = [0.1, 0.9, 0.4, 0.6]
    y = [0, 1, 0, 1]
    pts = roc_curve(s, y)
    # starts at (0,0), ends at (1,1)
    assert pts[0]["fpr"] == 0.0 and pts[0]["tpr"] == 0.0
    assert pts[-1]["fpr"] == 1.0 and pts[-1]["tpr"] == 1.0


def test_pr_and_ap_perfect():
    s = [0.1, 0.2, 0.8, 0.9]
    y = [0, 0, 1, 1]
    assert abs(average_precision(s, y) - 1.0) < 1e-9


def test_operating_point():
    s = [0.1, 0.4, 0.6, 0.9]
    y = [0, 0, 1, 1]
    op = operating_point(s, y, 0.5)
    assert op["tp"] == 2 and op["fp"] == 0 and op["tn"] == 2 and op["fn"] == 0
    assert op["tpr"] == 1.0 and op["fpr"] == 0.0 and op["specificity"] == 1.0


def test_operating_point_from_preds():
    preds = [1, 1, 0, 0]
    y = [1, 0, 0, 1]
    op = operating_point_from_preds(preds, y)
    assert op["tp"] == 1 and op["fp"] == 1 and op["tn"] == 1 and op["fn"] == 1


def test_fpr_at_budget():
    s = [0.1, 0.2, 0.3, 0.95]
    y = [0, 0, 1, 1]
    r = fpr_at_budget(s, y, 0.25)  # top 1 of 4 -> the 0.95 round (a positive)
    assert r["k"] == 1
    assert r["tpr"] == 0.5 and r["fpr"] == 0.0 and r["precision"] == 1.0


def test_calibration_perfectly_calibrated():
    # scores equal empirical rate per bin -> ECE ~ 0
    s = [0.05] * 20 + [0.95] * 20
    y = [0] * 19 + [1] + [1] * 19 + [0]  # 1/20 positive in low bin, 19/20 in high
    cal = calibration_curve(s, y, n_bins=10)
    assert cal["ece"] < 0.1
    assert 0.0 <= cal["brier"] <= 1.0


def test_evaluate_detector_bundle():
    s = [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]
    y = [0, 0, 0, 1, 1, 1]
    ev = evaluate_detector(s, y, flag_threshold=0.5, preds=[0, 0, 0, 1, 1, 1])
    assert ev["auc_roc"] == 1.0
    assert ev["n_pos"] == 3 and ev["n_neg"] == 3
    assert ev["operating_point_monitor_flags"]["tpr"] == 1.0
    assert ev["operating_point_monitor_flags"]["fpr"] == 0.0
    assert len(ev["roc_curve"]) >= 2
    assert math.isfinite(ev["calibration"]["brier"])
