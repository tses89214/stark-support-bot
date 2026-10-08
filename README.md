# llm-rag-tuning

A **customer-service chatbot that answers questions from product documents** (RAG), plus a notebook comparing it with two alternatives: prompt stuffing and fine-tuning.
This is a small proof-of-concept for learning and demonstration, not a production system.

> All data (Stark Spaceships, prices, the support email address) is **fictional**.

## The scenario

A customer-service chatbot for **Stark Spaceships**, a fake line of consumer-level spaceships (models 1–10) that differ in size, color, price and target customer. Product data lives in `data/stark_spaceships/`.

## The chatbot

[`chatbot.py`](chatbot.py) is a command-line chat loop:

1. Embed the question and retrieve the top-3 matching product docs (`all-MiniLM-L6-v2`, cosine similarity).
2. Send them to the chat model (default `gpt-4o`) with a system prompt that says to answer **only** from those docs, or admit it doesn't know and point to support.
3. Keep chat history for follow-up questions, and print which docs each answer came from.

```bash
python chatbot.py
You: Which ship fits two kids and grandparents?
```

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
python chatbot.py                # the chatbot, run from the repo root
jupyter notebook demo.ipynb      # the method comparison
```

## Known simplifications

- The chatbot has no chunking (one file = one doc), vector database, reranking, query rewriting or evaluation; the notebook RAG returns only top-1.
- Training set is only 20 examples, enough to show the workflow, not to measure improvement.
- No automated tests or retrieval/answer quality metrics.
