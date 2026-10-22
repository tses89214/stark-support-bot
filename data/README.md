# data/

| Folder | What it is |
|---|---|
| `stark_spaceships/` | The product docs the bot answers from: one `.txt` per model (`model_1` .. `model_30`) plus a warranty policy and two guides. Indexed by `backend/build_index.py`. |
| `stark_scaled/` | A bigger, hierarchical corpus (`brand/`, `general/`, `models/`, `manuals/`, plus `INDEX.md`) for the retrieval ladder only (`evals/eval_retrieval_ladder.py`); the chatbot does not read it. Generated deterministically by `evals/gen_scaled_corpus.py`; `gold.json` holds the per-model facts that define the correct answers. |
