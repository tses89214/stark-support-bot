# Stark Support Bot

A RAG customer-service chatbot with guardrails (off-topic filtering, prompt-injection refusal, hand-off to human agents) and a minimal web UI, plus a notebook comparing prompt stuffing, RAG and fine-tuning.
This is a small proof-of-concept for learning and demonstration, not a production system.

> All data (Stark Spaceships, prices, the support email address) is **fictional**.

## The scenario

A customer-service chatbot for **Stark Spaceships**, a fake line of consumer-level spaceships (models 1–15) that differ in size, color, price and target customer. Product data lives in `data/stark_spaceships/`.

## The chatbot

Two parts, one command each:

| Part | File | Run | What it does |
|---|---|---|---|
| Embedding (offline) | `build_index.py` | `python build_index.py` | Embeds every doc with `BAAI/bge-m3` (multilingual; chosen with `eval_retrieval.py`) and saves `index.npz`. Re-run when the docs change. |
| Serving (online) | `app.py` + `static/index.html` | `uvicorn app:app` | FastAPI server and a one-page chat UI at http://localhost:8000. |

What happens to each message in `app.py`:

1. **Classify** — an LLM labels it `ANSWER`, `OFF_TOPIC`, `ABUSIVE`, `ESCALATE` or `INJECTION` (fails closed to `ESCALATE`).
2. **Route** — off-topic and injection get a fixed refusal. Abusive and escalation cases open a ticket for a human agent (written to `tickets.jsonl`, a stand-in for a helpdesk API) and reply with the ticket number.
3. **Retrieve** — for `ANSWER`, embed the question (plus the previous user turn, for follow-ups) and take the top-3 docs by cosine similarity. If the best score is under `MIN_SCORE`, reply "not in our documents".
4. **Answer** — send the docs to the chat model with a prompt that says to answer only from them.

The chat history lives in the browser and is sent with each request, so the server keeps no state. The UI shows the route and source docs under each reply.

`python eval_guardrails.py` runs the classifier on 15 labeled messages (English and Chinese). `python eval_retrieval.py` compares embedding models by hit@3 on 20 labeled questions (free, no LLM calls); bge-m3 scored 20/20 vs 11/20 for MiniLM, which found no Chinese questions.

## Three methods, one notebook

All code and results are in [`demo.ipynb`](demo.ipynb), with outputs kept so you can read it without running it.

```
Method 1: Prompt          Method 2: RAG                      Method 3: Fine-tuning
all 10 docs ─► system     query ─► embed ─► cosine top-N     JSONL examples ─► OpenAI
prompt ─► GPT-4o          docs ◄───────────┘                 fine-tune job ─► custom
                          top docs + query ─► GPT-4o         gpt-4o-mini ─► reply
```

| | 1. Prompt | 2. RAG | 3. Fine-tuning |
|---|---|---|---|
| How | Paste all docs into the prompt | Embed docs (`all-MiniLM-L6-v2`), retrieve top match, pass to GPT-4o | Train `gpt-4o-mini` on Q&A pairs (`data/fine-tuning-job-example.jsonl`) |
| Good for | Small corpus, quick start | Larger / frequently changing knowledge | Consistent tone and output format |
| Limits | Context window, token cost, latency | Retrieval quality; no chunking or reranking here | Poor at injecting new facts; needs data and training cost |
| Knowledge updates | Instant | Re-embed docs | Retrain |

## Example results

- **Prompt** — asked for a family of 6 (2 kids, wife, her parents): recommends *Stark 4* (12 seats, $8M) with a matching accessory list.
- **RAG** — "reliable for adventurers, extra fuel tanks": retrieves `model 2` and answers from that document only.
- **Fine-tuning** — "I received the wrong model!": replies with an apology and directs the customer to the support email, in the trained tone.

## Run it

```bash
pip install -r requirements.txt
export OPENAI_API_KEY=...        # paid API; fine-tuning (Method 3) also incurs training cost
# chatbot.py works with any OpenAI-compatible endpoint, e.g. a LiteLLM gateway serving Claude:
# export OPENAI_BASE_URL=https://<your-gateway>/v1 CHAT_MODEL=<model-name>
python build_index.py            # once, and after docs change
uvicorn app:app                  # chatbot at http://localhost:8000 (run from the repo root)
jupyter notebook demo.ipynb      # the method comparison
```

## Known simplifications

- The chatbot has no chunking (one file = one doc), vector database, reranking or query rewriting; no streaming or authentication; tickets go to a local file.
- The only evaluation is the 15-case classifier check; retrieval and answer quality are untested, and `MIN_SCORE` is a rough guess.
- Training set is only 20 examples, enough to show the workflow, not to measure improvement.
- No automated tests or retrieval/answer quality metrics.
