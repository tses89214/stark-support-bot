# backend/

The serving path of the chatbot. Run from the repo root.

| File | What it does |
|---|---|
| `app.py` | FastAPI app, the whole request path: classify -> route/ticket -> retrieve -> answer -> review. LLM calls go to OpenRouter (`llm()`). `uvicorn backend.app:app` |
| `build_index.py` | Offline step: embeds `data/stark_spaceships/` with bge-m3 into an index file. Re-run when the docs change. |
| `doc_tools.py` | MLflow tracing helpers (no-ops unless `MLFLOW_TRACKING_URI` is set) and read-only document tools over `data/stark_scaled/`. The chatbot itself only uses the tracing helpers; the document tools are used by `evals/eval_retrieval_ladder.py`. |
| `sessions.py` | Server-side conversations in a local SQLite file, so the browser cannot forge history. |
