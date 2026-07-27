#!/usr/bin/env python3
"""Split the monolithic main.tex into a venue-adaptable package.

Produces paper/ with:
  main.tex        venue-neutral driver; ONE block to edit to retarget a venue
  preamble.tex    packages + macros, shared by every venue
  sections/*.tex  one file per section, venue-independent
  refs.bib, figures/

The body files contain no venue-specific markup, so switching venues means editing
main.tex only.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "main.tex"
OUT = ROOT / "paper"

SLUGS = {
    "Related Work": "related_work",
    "The Expressiveness Threshold": "model",
    "The Content Account Does Not Survive Re-analysis": "reanalysis",
    "P1: The Predicate, With Length Held Constant": "p1_predicate",
    "P3: Ranking the Levers Against Each Other": "p3_levers",
    "P2: The Guardrail Boundary, Across Three Domains": "p2_modality",
    "Defenses": "defenses",
    "The Effect Crosses a Channel": "latent",
    "Does It Hold Beyond One Checkpoint": "generality",
    "Methods, and a Retraction": "methods",
    "Limitations": "limitations",
    "Conclusion": "conclusion",
    "Introduction": "intro",
}


def slug_for(title: str, n: int) -> str:
    flat = re.sub(r"\\[a-zA-Z]+|[{}\\$]", "", title).strip()
    for k, v in SLUGS.items():
        if flat.startswith(k) or k in flat:
            return f"{n:02d}_{v}"
    return f"{n:02d}_" + re.sub(r"[^a-z0-9]+", "_", flat.lower())[:28].strip("_")


def main() -> None:
    tex = SRC.read_text()

    pre_start = tex.index("\\usepackage[T1]{fontenc}")
    pre_end = tex.index("\\begin{document}")
    preamble = tex[pre_start:pre_end].strip()

    body_start = tex.index("\\begin{abstract}")
    body_end = tex.index("\\bibliographystyle")
    body = tex[body_start:body_end]

    abstract = body[body.index("\\begin{abstract}"):body.index("\\end{abstract}") + len("\\end{abstract}")]
    rest = body[body.index("\\end{abstract}") + len("\\end{abstract}"):]

    # split on top-level \section / \appendix
    parts, cur, title = [], [], "Front"
    for line in rest.splitlines():
        m = re.match(r"\\section\{(.+?)\}\s*$", line.strip())
        if m or line.strip() == "\\appendix":
            if cur:
                parts.append((title, "\n".join(cur).strip()))
            cur = [line]
            title = m.group(1) if m else "Appendix"
        else:
            cur.append(line)
    if cur:
        parts.append((title, "\n".join(cur).strip()))

    sec_dir = OUT / "sections"
    if sec_dir.exists():
        shutil.rmtree(sec_dir)
    sec_dir.mkdir(parents=True)

    (OUT / "preamble.tex").write_text(
        "% Shared preamble: packages and macros used by every venue target.\n"
        "% Venue-specific settings (documentclass, author block) live in main.tex.\n\n"
        + preamble + "\n")
    (sec_dir / "00_abstract.tex").write_text(abstract + "\n")

    inputs, appendix_at = [], None
    n = 1
    for title, content in parts:
        if title == "Appendix":
            appendix_at = len(inputs)
        slug = slug_for(title, n)
        (sec_dir / f"{slug}.tex").write_text(content + "\n")
        inputs.append(slug)
        n += 1

    lines = []
    for i, s in enumerate(inputs):
        if appendix_at is not None and i == appendix_at:
            pass  # \appendix already sits at the top of that file
        lines.append(f"\\input{{sections/{s}}}")
    body_inputs = "\n".join(lines)

    main_tex = r"""%%%===================================================================
%%%  What Must a Channel Express?
%%%  The Coordinating Predicate in Multi-Agent LLM Deployments
%%%
%%%  VENUE-ADAPTABLE DRIVER.
%%%  Everything venue-specific is in THIS FILE. sections/ and preamble.tex
%%%  are venue-independent -- retarget by editing only the block below.
%%%  See README.md for per-venue recipes (LNCS / ACM / IEEE / NeurIPS / arXiv).
%%%===================================================================

%%% ---- VENUE BLOCK : EDIT THIS ------------------------------------
\documentclass[runningheads]{llncs}          % Springer LNCS (GameSec, ESORICS...)
% \documentclass[sigconf,anonymous=false]{acmart}   % ACM (CCS, AsiaCCS...)
% \documentclass[conference]{IEEEtran}             % IEEE (S&P, EuroS&P...)
% \documentclass{article}                          % arXiv / NeurIPS-style
\newcommand{\VenueIsLNCS}{1}   % comment out for non-LNCS classes
%%% -----------------------------------------------------------------

\input{preamble}

\begin{document}

\title{What Must a Channel Express?\\
The Coordinating Predicate in Multi-Agent LLM Deployments}
\titlerunning{What Must a Channel Express?}

\author{Harry Fezeu\orcidID{0000-0002-8632-1459} \and Dhairya Surana \and
Thalia Rossitter \and Tyler Xia}
\authorrunning{H. Fezeu et al.}
\institute{Gauntlet AI\\
\email{\{harry.fezeu, thalia.rossitter, tyler.xia\}@challenger.gauntletai.com}\\
\email{dhairya.surana@gfachallenger.gauntletai.com}}

\maketitle

\input{sections/00_abstract}

""" + body_inputs + r"""

\bibliographystyle{splncs04}
\bibliography{refs}

\end{document}
"""
    (OUT / "main.tex").write_text(main_tex)

    print(f"preamble.tex + {len(inputs) + 1} section files")
    for s in ["00_abstract"] + inputs:
        print(f"  sections/{s}.tex")


if __name__ == "__main__":
    main()
