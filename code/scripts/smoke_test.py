#!/usr/bin/env python3
"""Offline end-to-end smoke test (zero API spend, MockLLM).

Exercises env + harness + metrics + report + figures for all three MPU
experiments at tiny scale, and asserts the definition-of-done artifacts exist.
Run: python3 scripts/smoke_test.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from experiments import a1_channel, a5_baseline, b1_pricing  # noqa: E402


def _check(run_dir: Path):
    for name in ("manifest.json", "matches.jsonl", "metrics.csv"):
        p = run_dir / name
        assert p.exists() and p.stat().st_size > 0, f"missing/empty: {p}"
    figs = list(run_dir.glob("*.png"))
    assert figs, f"no figures produced in {run_dir}"
    print(f"  OK: {run_dir}  ({len(figs)} figures)")


def main():
    print("== A5 (mock) ==")
    _check(a5_baseline.main(model="llama-8b", seeds=2, mock=True, max_rounds=5))
    print("== A1 (mock) ==")
    _check(a1_channel.main(pair="smoke_pair", seeds=2, mock=True, max_rounds=5))
    print("== B1 (mock) ==")
    _check(b1_pricing.main(pair="smoke_pair", seeds=2, mock=True, max_rounds=5))
    print("\nSMOKE TEST PASSED — full pipeline green end-to-end (offline).")


if __name__ == "__main__":
    main()
