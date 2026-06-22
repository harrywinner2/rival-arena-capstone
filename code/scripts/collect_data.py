#!/usr/bin/env python3
"""Collate every experiment's outputs into master artifacts for final analysis.

Pure pandas over the per-run CSVs (no rehydration) — robust to run anytime.
Writes into data/:
  master_long.csv  — every rounds_long.csv concatenated (the play-with-graphs table)
  SUMMARY.txt      — the per-cell summary tables (grepped from data/wide.log)
  FIGURES.txt      — index of every generated figure

Run: python3 scripts/collect_data.py
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main():
    longs = sorted(glob.glob(str(DATA / "runs" / "**" / "rounds_long.csv"), recursive=True))
    frames = []
    for p in longs:
        try:
            df = pd.read_csv(p)
            df["__src"] = p
            frames.append(df)
        except Exception as e:
            print(f"  skip {p}: {e}")
    if frames:
        master = pd.concat(frames, ignore_index=True)
        out = DATA / "master_long.csv"
        master.to_csv(out, index=False)
        exps = master["experiment_id"].nunique() if "experiment_id" in master else "?"
        print(f"master_long.csv: {len(master)} rows across {exps} experiments -> {out}")
    else:
        print("no rounds_long.csv found yet")

    figs = sorted(glob.glob(str(DATA / "runs" / "**" / "*.png"), recursive=True))
    (DATA / "FIGURES.txt").write_text("\n".join(figs))
    print(f"FIGURES.txt: {len(figs)} figures")

    wlog = DATA / "wide.log"
    if wlog.exists():
        lines = wlog.read_text(errors="ignore").splitlines()
        keep = [l for l in lines
                if "per-cell summary" in l
                or l.strip()[:3] in ("A1/", "A2/", "A3/", "A4/", "A5/", "B1/")]
        (DATA / "SUMMARY.txt").write_text("\n".join(keep))
        print(f"SUMMARY.txt: {len(keep)} summary lines")


if __name__ == "__main__":
    main()
