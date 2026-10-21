#!/bin/bash
# One-off: full re-run of the guardrail and ladder evals on nemotron-3-ultra (no-think), because nemotron-super:free is down.
# Not comparable with the earlier nemotron-super numbers; results are copied to *-ultra files afterwards.
cd /Users/po.cx.jian/github/llm-rag-tuning || exit 1
# cron has no shell profile: the corporate proxy must be set here or every request times out (HTTP 000)
export HTTP_PROXY=http://itt-fpx01.benq.corp.com:3128 HTTPS_PROXY=http://itt-fpx01.benq.corp.com:3128 NO_PROXY=localhost,127.0.0.1
set -a; . ./.env; set +a
unset LLM_BASE_URL LLM_API_KEY
export CHAT_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free LLM_NO_THINK=1 HF_HUB_OFFLINE=1
echo "running ultra since $(date)" > /tmp/rerun_status.log
.venv/bin/python -m evals.eval_guardrails > /tmp/ultra_guardrails.log 2>&1
.venv/bin/python -m evals.eval_ladder 2 > /tmp/ultra_ladder.log 2>&1
echo "done ultra $(date)" > /tmp/rerun_status.log
