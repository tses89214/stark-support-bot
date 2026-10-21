#!/bin/bash
# Hourly cron probe: once the free super model answers 200, run classifier eval then the 2-run defense ladder, once.
# Does not change docs; results land in results/ladder*.md, ladder_raw.json and /tmp/rerun_*.log. Same model as before, never another one.
cd /Users/po.cx.jian/github/llm-rag-tuning || exit 1
grep -qE '^(done|running)' /tmp/rerun_status.log 2>/dev/null && exit 0
set -a; . ./.env; set +a
unset LLM_BASE_URL LLM_API_KEY LLM_NO_THINK
export CHAT_MODEL=nvidia/nemotron-3-super-120b-a12b:free HF_HUB_OFFLINE=1
code=$(curl -s -o /dev/null -w '%{http_code}' https://openrouter.ai/api/v1/chat/completions -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"'"$CHAT_MODEL"'","messages":[{"role":"user","content":"hi"}],"max_tokens":10}')
if [ "$code" != "200" ]; then echo "model still unavailable (HTTP $code), nothing run" > /tmp/rerun_status.log; exit 1; fi
echo "running since $(date)" > /tmp/rerun_status.log
.venv/bin/python -m evals.eval_guardrails > /tmp/rerun_guardrails.log 2>&1
.venv/bin/python -m evals.eval_ladder 2 > /tmp/rerun_ladder.log 2>&1
echo "done $(date)" > /tmp/rerun_status.log
