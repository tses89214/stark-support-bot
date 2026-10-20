#!/bin/bash
# Scheduled once by cron after the OpenRouter free quota reset (08:00 Taipei): classifier eval, then the 2-run defense ladder.
# Does not change docs; results land in results/ladder*.md, ladder_raw.json and /tmp/rerun_*.log. Same model as before, never another one.
cd /Users/po.cx.jian/github/llm-rag-tuning || exit 1
set -a; . ./.env; set +a
unset LLM_BASE_URL LLM_API_KEY LLM_NO_THINK
export CHAT_MODEL=nvidia/nemotron-3-super-120b-a12b:free HF_HUB_OFFLINE=1
code=$(curl -s -o /dev/null -w '%{http_code}' https://openrouter.ai/api/v1/chat/completions -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"'"$CHAT_MODEL"'","messages":[{"role":"user","content":"hi"}],"max_tokens":10}')
if [ "$code" != "200" ]; then echo "model still unavailable (HTTP $code), nothing run" > /tmp/rerun_status.log; exit 1; fi
.venv/bin/python eval_guardrails.py > /tmp/rerun_guardrails.log 2>&1
.venv/bin/python eval_ladder.py 2 > /tmp/rerun_ladder.log 2>&1
echo "done $(date)" > /tmp/rerun_status.log
