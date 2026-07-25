# Raw run records — Paper 3 experiments

One directory per experiment, each the verbatim output of the harness.

| dir | experiment | matches |
|---|---|---|
| `G0` | capability gate (none vs text) | 48 |
| `P1` | joint-proposal predicate | 150 |
| `P3` | lever factorial | 288 |
| `P4` | opening-window suppression | 120 |

Files per run:
- `manifest.json`   — config hash, model IDs, seeds, timestamps
- `metrics.csv`     — per-match summary metrics
- `rounds_long.csv` — the tidy per-round table every analysis reads
- `matches.jsonl.gz` — full per-match records including message text (gzipped)

P2 is scenario-based rather than match-based; its records are in
`paper3/results/p2_runs.jsonl`. V1's judged sample is
`paper3/results/detector_validation_sample.csv`.

All runs: Qwen2.5-14B-Instruct, bf16, vLLM on a single A100 80GB, `max_model_len` 4096.
API error rate 0.000 throughout.
