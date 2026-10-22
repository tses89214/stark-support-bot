# backend/

The serving path of the chatbot. Run from the repo root.

| File | What it does |
|---|---|
| `app.py` | FastAPI app, the whole request path: classify -> route/ticket -> retrieve -> answer -> review. LLM calls go to OpenRouter (`llm()`). `uvicorn backend.app:app` |
| `build_index.py` | Offline step: embeds `data/stark_spaceships/` with bge-m3into an index file. Re-run when the docs change. |
| `doc_tools.py` | Read-only document tools; every corpus access goes through them so reads show up as spans in MLflow. |
| `sessions.py` | Server-side conversations in a local SQLite file, so the browser cannot forge history. |
