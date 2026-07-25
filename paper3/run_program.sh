#!/usr/bin/env bash
# Paper 3 experiment program, in dependency order, against a self-hosted endpoint.
#
#   bash paper3/run_program.sh https://<pod>-8000.proxy.runpod.net/v1 Qwen/Qwen2.5-14B-Instruct
#
# G0 gates everything: if the model does not respond to readable communication, the
# predicate experiments measure nothing, so a G0 failure aborts the run.
# Each stage is resumable (the harness checkpoints per match), so re-running after an
# interruption costs only the in-flight matches.

set -uo pipefail

BASE="${1:?usage: run_program.sh <openai-base-url> [model-id]}"
MODEL="${2:-Qwen/Qwen2.5-14B-Instruct}"
LOG=paper3/results/program.log

export OPENAI_API_BASE="$BASE"
export OPENAI_API_KEY=EMPTY

cd "$(dirname "$0")/.." || exit 1
mkdir -p paper3/results
: > "$LOG"

say() { echo -e "\n=== $* ===" | tee -a "$LOG"; }
run() { echo "+ $*" | tee -a "$LOG"; "$@" 2>&1 | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }

say "endpoint check"
curl -s -m 30 "$BASE/models" | head -c 200 | tee -a "$LOG"; echo

# ---------------------------------------------------------------- G0 (the gate)
say "G0 capability gate (48 matches)"
if ! run python3 paper3/src/g0_gate.py --seeds 24 --pair self_local_14 --concurrency 24; then
  say "G0 FAILED — the model does not clear the text-effect floor."
  say "Pre-registered escalation: re-provision at 32B/72B and re-gate. NOT running P1-P4."
  exit 1
fi
say "G0 PASSED"

# ---------------------------------------------------------------- V1 (cheap, parallel-safe)
say "V1 detector validation (300 messages)"
run python3 paper3/src/validate_detector.py --n 300 --judge "$MODEL" \
    --base-url "$BASE" --concurrency 16

# ---------------------------------------------------------------- P2 (cheapest experiment)
say "P2 request modality, 3 domains (288 runs)"
run python3 paper3/src/p2_experiment.py --seeds 48 --pair self_local_14 --concurrency 24
run python3 paper3/src/p2_analyze.py

# ---------------------------------------------------------------- P1 (gates P3/P4)
say "P1 joint-proposal predicate (150 matches)"
run python3 paper3/src/p1_experiment.py --seeds 30 --pair self_local_14 --concurrency 24
P1DIR=$(ls -td code/data/runs/P1/*/ | grep -v _checkpoint | head -1)
run python3 paper3/src/p1_analyze.py "$P1DIR"

# ---------------------------------------------------------------- P4 (cheap defense)
say "P4 opening-window suppression (120 matches)"
run python3 paper3/src/p4_experiment.py --seeds 30 --pair self_local_14 --concurrency 24
P4DIR=$(ls -td code/data/runs/P4/*/ | grep -v _checkpoint | head -1)
run python3 paper3/src/p4_analyze.py "$P4DIR"

# ---------------------------------------------------------------- P3 (largest)
say "P3 lever factorial (288 matches)"
run python3 paper3/src/p3_experiment.py --seeds 24 --pair self_local_14 --concurrency 24
P3DIR=$(ls -td code/data/runs/P3/*/ | grep -v _checkpoint | head -1)
run python3 paper3/src/p3_analyze.py "$P3DIR"

say "regenerating figures"
run python3 paper3/src/figures.py

say "PROGRAM COMPLETE — results in paper3/results/"
ls -la paper3/results/*.md | tee -a "$LOG"
