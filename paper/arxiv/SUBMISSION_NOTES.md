# arXiv submission — Communication Affordances and Principal-Harming Coordination among Rival LLM Agents

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
