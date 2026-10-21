#!/bin/bash
# One command for the demo: chat at :8000 and MLflow traces at :5001. Ctrl-C stops both.
# Needs .env (see .env.example) and `pip install -r requirements-eval.txt` for the MLflow side.
cd "$(dirname "$0")" || exit 1
[ -f .env ] || { echo "missing .env: copy .env.example and fill it in"; exit 1; }
[ -f data/runtime/index.npz ] || .venv/bin/python -m backend.build_index
for port in 8000 5001; do
  lsof -ti tcp:$port >/dev/null && { echo "port $port is already in use (old demo still running? lsof -ti tcp:$port | xargs kill)"; exit 1; }
done

export CHAT_MODEL=nvidia/nemotron-3-ultra-550b-a55b:free LLM_NO_THINK=1  # fixed for the demo; overrides .env
export MLFLOW_TRACKING_URI=sqlite:///data/runtime/mlflow.db MLFLOW_EXPERIMENT_NAME=chatbot-demo MLFLOW_DISABLE_AGENT_HINT=1
trap 'kill $(jobs -p) 2>/dev/null' EXIT
.venv/bin/mlflow ui --backend-store-uri "$MLFLOW_TRACKING_URI" --port 5001 >/dev/null 2>&1 &
.venv/bin/uvicorn backend.app:app --env-file .env &

until curl -s -o /dev/null localhost:8000/; do sleep 2; done  # bge-m3 takes a while to load
echo "chat:   http://localhost:8000"
echo "traces: http://localhost:5001  (experiment chatbot-demo -> Traces)"
command -v open >/dev/null && open http://localhost:8000 http://localhost:5001
wait
