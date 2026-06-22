# Rival-Arena — per-track submission folders

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
