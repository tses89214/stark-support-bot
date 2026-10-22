#!/bin/bash
# One-off for 2026-10-22 08:10 Taipei (after the free-model quota reset): retrieval ladder n=10/20/30, 2 runs each (21 questions, ~760 requests), on nemotron-3-ultra (no-think).
# Skips itself if the quota is too low; results are in results/retrieval-ladder.md and /tmp/ultra_retrieval.log. Does not update docs.
cd /Users/po.cx.jian/github/llm-rag-tuning || exit 1
# cron has no shell profile: the corporate proxy must be set here or every request times out
export HTTP_PROXY=http://itt-fpx01.benq.corp.com:3128 HTTPS_PROXY=http://itt-fpx01.benq.corp.com:3128 NO_PROXY=localhost,127.0.0.1
set -a; . ./.env; set +a
unset LLM_BASE_URL LLM_API_KEY
export CHAT_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free LLM_NO_THINK=1 HF_HUB_OFFLINE=1 MLFLOW_TRACKING_URI=sqlite:///data/runtime/mlflow.db MLFLOW_DISABLE_AGENT_HINT=1
left=$(curl -s https://openrouter.ai/api/v1/key -H "Authorization: Bearer $OPENROUTER_API_KEY" | .venv/bin/python -c "import sys,json;print(json.load(sys.stdin)['data']['free_model_daily_requests']['remaining'])")
echo "retrieval ladder: $left requests left at $(date)" > /tmp/ultra_retrieval_status.log
[ "${left:-0}" -ge 800 ] || { echo "not enough quota ($left < 800), nothing run" >> /tmp/ultra_retrieval_status.log; exit 1; }
for n in 10 20 30; do
  .venv/bin/python -m evals.gen_scaled_corpus $n >> /tmp/ultra_retrieval.log 2>&1
  for pass in 1 2; do .venv/bin/python -m evals.eval_retrieval_ladder $n >> /tmp/ultra_retrieval.log 2>&1; done  # one run per call, MLflow keeps both
done
echo "done $(date)" >> /tmp/ultra_retrieval_status.log
