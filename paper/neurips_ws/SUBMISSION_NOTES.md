# NeurIPS 2026 workshop submission — The Guardrail Only Protects What It Names

**AI-safety / multi-agent workshop version (non-archival, condensed ~9 pp).**

## How to submit
- Target: a NeurIPS 2026 safety / multi-agent / agents workshop. Workshops are announced in late summer;
  their paper CfPs typically open ~September with deadlines ~late Sept/Oct for the Dec conference.
- **Non-archival** — this won't conflict with the GameSec/arXiv submissions.
- **Action needed once the workshop is announced:** swap the `\documentclass`/title block to the official
  workshop style file (often the NeurIPS or ICLR template). The body, figures, and refs port unchanged
  (the preamble has a comment noting this). Current length ~9 pp at 10pt single-column.
- Authors + ORCID (Harry Fezeu 0000-0002-8632-1459) in the source.
- Files: `main.tex`, `refs.bib`, `main.bbl`, `figures/`, `main.pdf`.

## Build
`latexmk -pdf main.tex`
