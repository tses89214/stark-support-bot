# Results

Each page covers one question; they are independent, read the one you need.

| Page | Question | Produced by |
|---|---|---|
| [Full report (HTML)](https://tses89214.github.io/stark-support-bot/results/report.html) | All of the above as one tabbed page (Traditional Chinese), including the 對話順暢 tab: the conversation-flow design (server sessions, Focus, CLARIFY, pinned docs) and what is not yet measured. Open in a browser. | written by hand from these pages; same as the private Artifact |
| [Defense ladder](ladder.md) | How much does each defense (answer rules, input fence, classifier and routing, L0 to L3) add, from a deliberately defenseless bot? (Retrieval is measured on its own ladder below.) Scores, intervals, caveats. | `python -m evals.eval_ladder` (live LLM calls) |
| [Input classifier](guardrails.md) | How accurate is the 7-category input filter, and what does it get wrong? | `python -m evals.eval_guardrails` (live LLM calls) |
| [Ladder examples](ladder-examples.md) | What does the model actually receive at each level, and what does it reply to real attacks? | same run as the ladder |
| [Embedding models](embeddings.md) | Which embedding model retrieves the right doc, especially for Chinese questions? | `python -m evals.eval_retrieval` (local) |
| [Retrieval knobs](retrieval-knobs.md) | Is the score floor `MIN_SCORE = 0.4` and `TOP_K = 3` a good setting? | `python -m evals.eval_threshold` (local) |
| [Retrieval ladder](retrieval-ladder.md) | As the library grows from 10 to 30 models, which way of choosing documents (load all, embedding, scope check, LLM-read index) keeps answers right? 21 questions, 2 runs: at 30 models R3 0.93 (rerun 2026-10-23; 0.97 on 10-22), R0 0.95, R2 0.85, R1 0.75 (accuracy); R3 recall 1.00 in all runs but one (0.95), prompt 11% of R0's. | `python -m evals.eval_retrieval_ladder` (live LLM calls, MLflow) |
| [Review layer](review.md) | Does the final reviewer catch drafts that break one of its eight rules, and does it reject good drafts? Constructed drafts with a known verdict. 64/64 bad drafts rejected, 0/60 good drafts rejected (drafts are scripted, so the catch rate is optimistic). | `python -m evals.eval_review` (live LLM calls) |
| [Chunking, hybrid and rerank](hybrid.md) | If R1/R2 used the usual RAG techniques (sentence chunks, BM25 + vector fusion, cross-encoder rerank), how much would hit@3 on the 90 retrieval questions improve? vector 76/90, chunked 87, hybrid 81, rerank 86 (hit@1 85). | `python -m evals.eval_hybrid` (local, no LLM calls) |
| [Off-topic and follow-ups](followups.md) | With no score floor under R3, do the classifier and the document picker still stop off-topic messages, and does R3 or R2 find the right document for a follow-up in a chat? Off-topic: classifier 30/30 and picker 30/30; follow-ups: R2 16/16, R3 16/16 (small samples). | `python -m evals.eval_followups` (live LLM calls) |

Headline: attacks blocked rise from 16/28 (no defenses) to 28/28 (L3, with the classifier) without losing any normal question; answer rules, input fence and classifier each add a step, and neighbouring intervals overlap. The numbers are from the single model `nvidia/nemotron-3-ultra-550b-a55b:free` (reasoning off), 2 runs per level on a free tier, with small fixed question sets, so read the intervals on the ladder page before trusting a gap.
