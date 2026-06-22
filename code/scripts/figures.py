#!/usr/bin/env python3
"""Regenerate the standard figure set for a saved run directory.

Run: python3 scripts/figures.py data/runs/A1/<timestamp>
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rival_arena.viz import make_all  # noqa: E402


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python3 scripts/figures.py <run_dir>")
    run_dir = Path(sys.argv[1])
    if not run_dir.exists():
        sys.exit(f"no such run dir: {run_dir}")
    paths = make_all(run_dir)
    for p in paths:
        print(f"figure: {p}")


if __name__ == "__main__":
    main()
