#!/usr/bin/env bash
# RunPod setup for the Paper 3 text program.
#
# Serves Qwen2.5-32B-Instruct at bf16 on one A100 80GB via vLLM, exposing an
# OpenAI-compatible endpoint. The frozen apparatus needs NO code change: LLMClient
# passes api_key=None for any provider other than "openrouter", so litellm falls
# through to its OpenAI-compatible path and reads OPENAI_API_BASE from the env.
#
# Usage on the pod (interactive shell):
#   bash paper3/runpod/setup.sh serve      # start vLLM (foreground; use tmux)
#   bash paper3/runpod/setup.sh check      # verify the endpoint answers
#
# IF DEPLOYING VIA THE RUNPOD API INSTEAD OF A SHELL: `dockerArgs` is APPENDED to the
# image ENTRYPOINT, and vllm/vllm-openai has ENTRYPOINT ["vllm","serve"], which takes
# the model POSITIONALLY. So dockerArgs must be only the model plus flags:
#
#   Qwen/Qwen2.5-14B-Instruct --dtype bfloat16 --max-model-len 4096 \
#     --gpu-memory-utilization 0.90 --host 0.0.0.0 --port 8000
#
# Passing `--model X`, `vllm serve X`, or a `bash -c` wrapper all produce invalid argv
# and the container dies in under a second with no log retrievable through the API.
# See PROGRAM.md section 12.2.
#
# Then, from wherever the experiments run:
#   export OPENAI_API_BASE=http://<pod-host>:8000/v1
#   export OPENAI_API_KEY=EMPTY

set -euo pipefail

MODEL="${MODEL:-Qwen/Qwen2.5-32B-Instruct}"
PORT="${PORT:-8000}"
MAXLEN="${MAXLEN:-8192}"
# Leave headroom for KV cache at concurrency ~24. Drop to 0.85 or fall back to
# Qwen2.5-14B-Instruct if you see preemption warnings under load.
UTIL="${UTIL:-0.90}"

case "${1:-serve}" in
  install)
    pip install -q "vllm>=0.6" "litellm>=1.40" pandas numpy scipy matplotlib
    ;;
  serve)
    echo "serving $MODEL at bf16 on port $PORT (max_len=$MAXLEN, util=$UTIL)"
    # --dtype bfloat16 is deliberate: quantization is NOT used, so precision is a
    # pinned, reported variable rather than the unknown it was in the hosted runs.
    exec vllm serve "$MODEL" \
      --dtype bfloat16 \
      --max-model-len "$MAXLEN" \
      --gpu-memory-utilization "$UTIL" \
      --port "$PORT" \
      --disable-log-requests
    ;;
  check)
    BASE="${OPENAI_API_BASE:-http://localhost:$PORT/v1}"
    echo "probing $BASE"
    curl -s "$BASE/models" | head -c 400; echo
    curl -s "$BASE/chat/completions" \
      -H 'Content-Type: application/json' \
      -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"reply with the single word OK\"}],\"max_tokens\":8}" \
      | head -c 400; echo
    ;;
  *)
    echo "usage: $0 {install|serve|check}" >&2; exit 2
    ;;
esac
