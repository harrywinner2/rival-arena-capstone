#!/usr/bin/env python3
"""Assemble per-publishing-track submission folders, each self-contained for upload,
then zip them. Output: release/rival-arena-submission-tracks.zip with one folder per track.
"""
from __future__ import annotations
import shutil
from pathlib import Path

ROOT = Path("/home/ubuntu/capstone")
OUT = ROOT / "release" / "submission_tracks"
if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)

# (src dir under capstone, track folder name, venue note)
TRACKS = {
    "arxiv": "arxiv",
    "gamesec": "gamesec",
    "neurips_ws": "neurips_ws",
}

NOTES = {
"arxiv": """# arXiv submission — Communication Affordances and Principal-Harming Coordination among Rival LLM Agents

**This is the comprehensive SUPERSET version (all findings, all caveats).**

## How to submit
- Upload the SOURCE (arXiv compiles it; it runs pdflatex/latex but NOT bibtex, so `main.bbl` is included).
- Files in this folder: `main.tex`, `sections/`, `refs.bib`, **`main.bbl`** (required — arXiv won't run bibtex),
  `figures/` (vector PDFs), and the compiled `main.pdf` for reference.
- Categories: **primary cs.MA** (Multiagent Systems); cross-list **cs.GT** and **cs.AI**.
- License: CC BY 4.0 recommended (it's a reproducibility release).
- No anonymization; authors + ORCID (Harry Fezeu 0000-0002-8632-1459) are in the source.
- No page limit. Compiled length ~26 pp.

## Tip
Test locally with: `latexmk -pdf main.tex` (regenerates main.bbl). Then `tar czf arxiv-src.tgz main.tex sections refs.bib main.bbl figures`.
""",
"gamesec": """# GameSec 2026 submission — Communication Affordances as an Attack Surface

**Springer LNCS, security/game-theory venue. 19 pp (hard limit 20, incl. refs + appendix).**

## How to submit
- Venue: GameSec 2026 (Conf. on Game Theory and AI for Security), Ann Arbor, Oct 26–28, 2026.
- **Deadline: June 26, 2026, 23:59 AoE**, via **OpenReview** (gamesec-conf.org).
- Anonymization is OPTIONAL — this is the authored version (with ORCID). If you prefer blind, strip the
  `\\author`/`\\institute`/`\\orcidID` block.
- Upload the compiled `main.pdf`; if source is requested, this folder is self-contained
  (`main.tex`, `refs.bib`, `main.bbl`, `figures/`).
- Format: Springer LNCS (`llncs` class, `splncs04` bib) — already conforming.
- On acceptance: a Springer copyright form + camera-ready (camera-ready deadline Aug 7, 2026).

## Build
`latexmk -pdf main.tex`
""",
"neurips_ws": """# NeurIPS 2026 workshop submission — The Guardrail Only Protects What It Names

**AI-safety / multi-agent workshop version (non-archival, condensed ~9 pp).**

## How to submit
- Target: a NeurIPS 2026 safety / multi-agent / agents workshop. Workshops are announced in late summer;
  their paper CfPs typically open ~September with deadlines ~late Sept/Oct for the Dec conference.
- **Non-archival** — this won't conflict with the GameSec/arXiv submissions.
- **Action needed once the workshop is announced:** swap the `\\documentclass`/title block to the official
  workshop style file (often the NeurIPS or ICLR template). The body, figures, and refs port unchanged
  (the preamble has a comment noting this). Current length ~9 pp at 10pt single-column.
- Authors + ORCID (Harry Fezeu 0000-0002-8632-1459) in the source.
- Files: `main.tex`, `refs.bib`, `main.bbl`, `figures/`, `main.pdf`.

## Build
`latexmk -pdf main.tex`
""",
}

for src, name in TRACKS.items():
    s = ROOT / src
    d = OUT / name
    d.mkdir(parents=True)
    # core source
    for f in ["main.tex", "refs.bib", "main.bbl", "main.pdf"]:
        if (s / f).exists():
            shutil.copy2(s / f, d / f)
    # sections/ and figures/
    for sub in ["sections", "figures"]:
        if (s / sub).is_dir():
            shutil.copytree(s / sub, d / sub,
                            ignore=shutil.ignore_patterns("*.aux", "*.log"))
    (d / "SUBMISSION_NOTES.md").write_text(NOTES[name])
    n_fig = len(list((d / "figures").glob("*.pdf"))) if (d / "figures").is_dir() else 0
    print(f"  {name}: main.pdf + main.tex + {'sections/ ' if (d/'sections').is_dir() else ''}refs.bib + main.bbl + {n_fig} figures + notes")

# top-level README
(OUT / "README.md").write_text(
"""# Rival-Arena — per-track submission folders

Communication Affordances and Principal-Harming Coordination among Rival LLM Agents.
Fezeu, Surana, Rossitter, Xia — Gauntlet AI. (Harry Fezeu ORCID 0000-0002-8632-1459.)

One folder per publishing track, each self-contained for submission (PDF + LaTeX source +
`refs.bib` + pre-built `main.bbl` + `figures/` + venue-specific SUBMISSION_NOTES.md):

- **arxiv/**       — the comprehensive SUPERSET (everything). cs.MA primary. ~26 pp.
- **gamesec/**     — GameSec 2026, Springer LNCS, security-scoped. 19 pp (≤20 limit). Deadline Jun 26.
- **neurips_ws/**  — a NeurIPS 2026 safety workshop, condensed ~9 pp, non-archival (swap the template on announcement).

All three share one source of truth and were revised to address a peer review: confirmatory-first
abstracts, direct contrast tests + bootstrap CIs, and corrected/scoped claims (free-text-is-the-lever
not "worse than silence"; "independent supracompetitive pricing" not "tacit collusion"; A3 under-powered
not "equivalence"; enforcement cell-dependent; S2 an exploratory boundary condition). Full statistical
backing: `docs/stats_audit.md` in the main repo. Each builds with `latexmk -pdf main.tex`.
""")
print("  README.md (top-level)")

archive = shutil.make_archive(str(ROOT/"release"/"rival-arena-submission-tracks"),
                              "zip", root_dir=OUT.parent, base_dir=OUT.name)
mb = Path(archive).stat().st_size/1e6
print(f"\nWROTE {archive}  ({mb:.1f} MB)")
