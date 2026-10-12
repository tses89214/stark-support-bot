# Stark Spaceships customer-service chatbot

RAG chatbot over fake product docs (`data/stark_spaceships/`). Every message goes through
**classify → route/ticket → retrieve → answer**:

```
message ─► classifier (LLM) ─┬─ OFF_TOPIC / INJECTION ─► canned refusal
                             ├─ ABUSIVE / ESCALATE ────► ticket in tickets.jsonl + canned reply
                             └─ ANSWER ─► embed (bge-m3) ─► top-3 docs ─► LLM answers from them
                                          (best score < 0.4 ─► "no answer" reply)
```

The LLM is any free model on [OpenRouter](https://openrouter.ai); embeddings run locally.

## Run

```bash
python3 -m venv .venv && PIP_USER=0 .venv/bin/pip install -r requirements.txt
cp .env.example .env              # add your OpenRouter key, pick a :free model
.venv/bin/python build_index.py   # embeds the docs into index.npz (downloads bge-m3, ~2GB)
.venv/bin/python -m uvicorn app:app --env-file .env   # chat UI at http://localhost:8000
```

## Check it

| Command | What it checks | Cost |
|---|---|---|
| `python test_app.py` | retry and fail-closed behaviour | free, offline |
| `python eval_retrieval.py [model ...]` | hit@3 / MRR@3 per embedding model | free, local |
| `python eval_guardrails.py` | classifier accuracy on 15 labelled messages | free-tier LLM calls |
| `python eval_answers.py` | end to end: grounded answers contain doc facts, unanswerable ones point to support | free-tier LLM calls |

Free models are rate-limited: if the classifier fails it escalates to a human and prints
`classify failed` on stderr, so check stderr before trusting an eval score.

## Notes

- `demo.ipynb` (prompt stuffing vs RAG vs fine-tuning) is shelved and will be rewritten.
- `.claude/` holds progress and design decisions (`PROGRESS.md`, `DECISIONS.md`).
