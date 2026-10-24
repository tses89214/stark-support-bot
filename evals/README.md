# evals/

Run from the repo root as `python -m evals.<name>`. Each script's docstring has the details; results are written to `results/` (index: `results/README.md`). Live LLM calls hit the OpenRouter free tier, which is rate-limited.

| Script | Measures | LLM calls |
|---|---|---|
| `eval_ladder` | Defense ladder L0..L3: attacks blocked, questions answered | yes |
| `eval_guardrails` | Input classifier accuracy and confusion matrix | yes |
| `eval_review` | The reviewer layer on constructed good/bad drafts | yes |
| `eval_conversations` | 14 scripted multi-turn chats through `app.chat`, judged by code | yes |
| `eval_followups` | Off-topic messages and follow-up questions in a chat | yes |
| `eval_answers` | End to end: grounded answers contain doc facts, unanswerable ones point to support | yes |
| `eval_retrieval` | hit@3 / MRR per embedding model | no |
| `eval_threshold` | `MIN_SCORE` sweep and `TOP_K` hit@k | no |
| `eval_hybrid` | Chunking, BM25 + vector fusion, rerank vs plain vector search | no |
| `eval_retrieval_ladder` | How the bot picks documents at two corpus sizes (uses `data/stark_scaled/`) | yes (`--dry` builds the questions only) |

Test-case data and helpers:

- `eval_candidates.jsonl`, `eval_candidates_attacks.jsonl`: labelled classifier messages (hand-written, or LLM-drafted then hand-reviewed).
- `gen_candidates.py` drafts new messages with an LLM; `review_candidates.py` is the hand-review loop.
- `gen_scaled_corpus.py` builds `data/stark_scaled/`; `stats.py` computes the Wilson 95% intervals.
