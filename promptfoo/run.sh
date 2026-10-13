#!/bin/sh
# Local-only promptfoo: no telemetry, no update check, no sharing, and generation by our own OpenRouter model, not promptfoo's server.
# Needs the bot running (uvicorn app:app --env-file .env) and OPENROUTER_API_KEY in the environment.
export PROMPTFOO_DISABLE_TELEMETRY=1 PROMPTFOO_DISABLE_UPDATE=1 PROMPTFOO_DISABLE_SHARING=1 PROMPTFOO_DISABLE_REDTEAM_REMOTE_GENERATION=true
cd "$(dirname "$0")" && exec npx --yes promptfoo@0.124.1 "$@"
