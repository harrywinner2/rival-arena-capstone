#!/usr/bin/env python3
"""Assemble the clean, GitHub-ready deliverable repo and zip it.
Output: release/rival-arena-capstone/  (+ release/rival-arena-capstone.zip)
Curated: paper (3 venue folders) + presentation (deck/website/video) + code + results + docs.
Excludes working cruft (.venv, data/runs bulk, caches, logs, secrets).
"""
from __future__ import annotations
import shutil, subprocess
from pathlib import Path

ROOT = Path("/home/ubuntu/capstone")
DEST = ROOT / "release" / "rival-arena-capstone"
if DEST.exists():
    shutil.rmtree(DEST)
DEST.mkdir(parents=True)

IGN = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".pytest_cache",
                             "*.log", ".DS_Store", "*.aux", "*.fls", "*.fdb_latexmk",
                             "*.out", "*.blg", "*.synctex.gz")

def cptree(src, dst):
    s = ROOT / src
    if s.is_dir():
        shutil.copytree(s, DEST / dst, ignore=IGN)
        print("  dir +", dst)

def cp(src, dst):
    s = ROOT / src
    if s.exists():
        (DEST / dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(s, DEST / dst)
        print("  +", dst)

# --- paper: the three venue submission folders ---
for v in ["arxiv", "gamesec", "neurips_ws"]:
    src = ROOT / "release" / "submission_tracks" / v
    if src.is_dir():
        shutil.copytree(src, DEST / "paper" / v, ignore=IGN)
        print("  dir + paper/", v)
cp("release/submission_tracks/README.md", "paper/README.md")

# --- presentation ---
cptree("presentation/deck", "presentation/deck")
cptree("presentation/website", "presentation/website")
cp("presentation/SCRIPT.md", "presentation/SCRIPT.md")
(DEST / "presentation" / "video").mkdir(parents=True, exist_ok=True)
# prefer the compressed web video for the repo; keep the build script
cp("presentation/video/explainer_web.mp4", "presentation/video/explainer.mp4")
cp("presentation/video/build_video.py", "presentation/video/build_video.py")

# --- code (the apparatus + experiments) ---
for d in ["rival_arena", "experiments", "scripts", "tests", "configs"]:
    cptree(d, "code/" + d)
for f in ["requirements.txt", "pyproject.toml"]:
    cp(f, "code/" + f)

# --- results (curated; NOT the 250MB raw match logs) ---
KEEP = {"summary.json", "metrics.csv", "manifest.json"}
nt = 0
for p in (ROOT / "data" / "runs").rglob("*"):
    if p.is_file() and p.name in KEEP:
        rel = p.relative_to(ROOT)
        d = DEST / "results" / rel
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, d); nt += 1
print(f"  results: {nt} per-run summary tables")
cp("data/SUMMARY.txt", "results/SUMMARY.txt")
cp("data/master_long.csv", "results/master_long.csv")
# figures (vector PDFs + the PNGs)
(DEST / "results" / "figures").mkdir(parents=True, exist_ok=True)
for fp in (ROOT / "paper" / "figures").glob("f*.pdf"):
    shutil.copy2(fp, DEST / "results" / "figures" / fp.name)
cp("docs/stats_audit.md", "results/stats_audit.md")
cp("scripts/stats_audit.py", "results/stats_audit.py")

# --- docs ---
for f in ["paper_facts.md", "results_log.md", "stats_audit.md", "citation_audit.md",
          "findings.md", "novelty_scan.md", "reanalysis_z2.md"]:
    cp("docs/" + f, "docs/" + f)

# --- README + LICENSE + .gitignore ---
cp("REPO_README.md", "README.md")
(DEST / "LICENSE").write_text(
"""MIT License (code) / CC BY 4.0 (paper, figures, presentation)

Copyright (c) 2026 Harry Fezeu, Dhairya Surana, Thalia Rossitter, Tyler Xia (Gauntlet AI)

The CODE in this repository (code/, scripts) is released under the MIT License.
The PAPER, FIGURES, PRESENTATION, and TEXT are released under Creative Commons
Attribution 4.0 (CC BY 4.0). Full preprint + data: https://zenodo.org/records/20792312
""")
(DEST / ".gitignore").write_text(
"__pycache__/\n*.pyc\n.venv/\nvenv/\n.env\n.pytest_cache/\n*.aux\n*.log\n*.out\n*.fls\n*.fdb_latexmk\n*.blg\n.DS_Store\n")

# --- init git + first commit ---
def git(*a):
    subprocess.run(["git", *a], cwd=DEST, check=True,
                   capture_output=True)
git("init", "-q")
git("config", "user.email", "harry.fezeu@challenger.gauntletai.com")
git("config", "user.name", "Harry Fezeu")
git("add", "-A")
git("commit", "-q", "-m",
    "Rival Arena — capstone deliverable: paper (3 venues), presentation (deck/site/video), code, results")
print("  git: initialized + first commit")

# --- zip the whole repo (including .git so it's push-ready) ---
archive = shutil.make_archive(str(ROOT / "release" / "rival-arena-capstone"),
                              "zip", root_dir=DEST.parent, base_dir=DEST.name)
mb = Path(archive).stat().st_size / 1e6
total = sum(f.stat().st_size for f in DEST.rglob("*") if f.is_file()) / 1e6
print(f"\nrepo size (uncompressed): {total:.1f} MB")
print(f"WROTE {archive}  ({mb:.1f} MB)")
# biggest files (watch for >100MB GitHub limit)
big = sorted(((f.stat().st_size, f) for f in DEST.rglob("*") if f.is_file()),
             reverse=True)[:5]
print("largest files:")
for sz, f in big:
    print(f"  {sz/1e6:6.1f} MB  {f.relative_to(DEST)}")
