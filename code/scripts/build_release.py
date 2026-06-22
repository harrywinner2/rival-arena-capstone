#!/usr/bin/env python3
"""Assemble the reproducibility data release and zip it.
Output: release/rival-arena-data.zip  (curated data + code + figure scripts + docs).
Excludes secrets (.env), venv, caches, and the bulk raster match logs.
"""
from __future__ import annotations
import shutil, fnmatch
from pathlib import Path

ROOT = Path("/home/ubuntu/capstone")
REL  = ROOT/"release"/"rival_arena_data"
if REL.exists(): shutil.rmtree(REL)
REL.mkdir(parents=True)

def copy(src, dst_rel):
    s = ROOT/src
    if not s.exists(): print("  skip (missing):", src); return
    d = REL/dst_rel; d.parent.mkdir(parents=True, exist_ok=True)
    if s.is_dir(): shutil.copytree(s, d, ignore=shutil.ignore_patterns(
        "__pycache__","*.pyc",".pytest_cache","*.log"))
    else: shutil.copy2(s, d)
    print("  +", dst_rel)

# --- docs / methodology / locked numbers ---
for f in ["docs/paper_facts.md","docs/findings.md","docs/results_log.md",
          "docs/reanalysis_z2.md","docs/novelty_scan.md","docs/exhibits.md",
          "docs/hidden_language.md"]:
    copy(f, f)

# --- apparatus source code (the harness + experiments + tests) ---
for d in ["rival_arena","experiments","tests","configs"]:
    copy(d, "code/"+d)
for f in ["requirements.txt","pyproject.toml","README.md","CLAUDE.md",
          "scripts/paper_figures.py","scripts/figures.py","scripts/build_report.py",
          "scripts/run.py","scripts/run_program.py","scripts/build_release.py"]:
    copy(f, "code/"+f if f.startswith("scripts") else f)

# --- aggregate result tables for EVERY run (small, the quantitative backbone) ---
KEEP = {"summary.json","metrics.csv","rounds_long.csv","manifest.json"}
n_tab = 0
for p in (ROOT/"data"/"runs").rglob("*"):
    if p.is_file() and p.name in KEEP:
        rel = p.relative_to(ROOT)
        copy(str(rel), str(rel)); n_tab += 1
copy("data/SUMMARY.txt","data/SUMMARY.txt")
copy("data/FIGURES.txt","data/FIGURES.txt")
copy("data/master_long.csv","data/master_long.csv")   # tidy per-round aggregate

# --- qualitative evidence: ALL transcripts for the alignment runs (the novel bit) ---
ALIGN = ["E1_ESCALATE","E1_FULL/20260619T174838","S2/20260619T174644",
         "S2/20260619T190331","S1/20260619T174648","S1/20260619T191601",
         "E1/20260619T151025","C7/20260619T163929"]
n_tx = 0
for a in ALIGN:
    tdir = ROOT/"data"/"runs"/a/"transcripts"
    if tdir.exists():
        for t in tdir.glob("*.json"):
            rel = t.relative_to(ROOT); copy(str(rel), str(rel)); n_tx += 1

print(f"\naggregate tables: {n_tab} | alignment transcripts: {n_tx}")

# --- data dictionary / README ---
(REL/"README.md").write_text(f"""# Rival-Agent Arena — Data & Code Release

Reproducibility artifact for *Communication Affordances and Principal-Harming
Coordination among Rival LLM Agents* (Fezeu, Surana, Rossitter, Xia; Gauntlet AI).

## Layout
- `docs/paper_facts.md` — the locked, vetted numbers behind every figure/table (the
  single source of truth), with provenance and confirmatory[C]/exploratory[E] tier tags.
- `docs/findings.md`, `docs/results_log.md` (§V/§Z/§Z2/§Z3), `docs/reanalysis_z2.md`,
  `docs/novelty_scan.md`, `docs/exhibits.md`, `docs/hidden_language.md` — full record.
- `code/rival_arena/` — the apparatus (games, channel ladder, monitor, metrics, sandbox Lab).
- `code/experiments/` — experiment drivers (a1_channel, b1_pricing, a3_origin, e1_*, s1_*, s2_*, c7_covert, …).
- `code/tests/` — 163 offline tests. `code/configs/models.yaml` — model matrix & named pairs.
- `code/scripts/paper_figures.py` — regenerates every paper figure from the numbers/data.
- `data/runs/<EXP>/<timestamp>/` — per-run aggregate tables: `summary.json`,
  `metrics.csv`, `rounds_long.csv` (tidy per-round), `manifest.json`. Bulk raster match
  logs are omitted for size; `rounds_long.csv` is sufficient to reproduce all plots.
- `data/runs/{{E1_ESCALATE,E1_FULL,S2,S1,E1,C7}}/.../transcripts/*.json` — FULL transcripts
  + event logs for the alignment wave (the qualitative evidence; ground-truth scored).
- `data/master_long.csv` — tidy per-round table across experiments (figure source).
- `data/SUMMARY.txt` — per-cell summary across the program.

## Key conventions
- Primary cooperation outcome = match-level lock-in proportion (mean C>0.8) + Wilson 95% CI
  (matches are bimodal). Collusion = index K=(p-p_comp)/(p_monopoly-p_comp); K>1 = supra-monopoly.
- Two speeds: pre-registered confirmatory spine (A1/B1/A3) on fresh seeds (offset 100) vs
  exploratory catalog. Every number tier-tagged [C]/[E]. Refusals coded; API errors excluded.
- Alignment scenarios run in a sandboxed in-memory Lab; all tools mocked; nothing real leaves
  the process (`assert_contained()`).

## Regenerate figures
```
pip install -r requirements.txt
python code/scripts/paper_figures.py    # -> paper figures from locked numbers + master_long.csv
```

## Models
Qwen2.5-72B, DeepSeek-V3, Llama-3-70B, Mistral-Large + GPT-4o anchor, via LiteLLM→OpenRouter.
Hosted inference; quantization not pinnable (logged best-effort). Scope: these models, this arena.

NOTE: no API keys, prompts-with-secrets, or `.env` are included. Set `OPENROUTER_API_KEY`
to re-run live; `--mock` runs everything offline with a deterministic MockLLM.
""")
print("  + README.md (data dictionary)")

# --- zip it ---
out = ROOT/"release"/"rival-arena-data"
archive = shutil.make_archive(str(out), "zip", root_dir=REL.parent, base_dir=REL.name)
mb = Path(archive).stat().st_size/1e6
print(f"\nWROTE {archive}  ({mb:.1f} MB)")
