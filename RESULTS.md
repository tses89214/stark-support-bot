# Results

Each page covers one question; they are independent, read the one you need.

| Page | Question | Produced by |
|---|---|---|
| [Defense ladder](results/ladder.md) | How much does each defense (answer rules, input fence, classifier, retrieval) add, from a deliberately defenseless bot to the real one? Includes what the model is sent and real example replies. | `eval_ladder.py` (live LLM calls) |
| [Embedding models](results/embeddings.md) | Which embedding model retrieves the right doc, especially for Chinese questions? | `eval_retrieval.py` (local) |
| [Retrieval knobs](results/retrieval-knobs.md) | Is the score floor `MIN_SCORE = 0.4` and `TOP_K = 3` a good setting? | `eval_threshold.py` (local) |

Headline: attacks blocked rise from 7/14 (no defenses) to 14/14 (the real bot) without losing any normal question, and the biggest single step is the input fence. The numbers are from 2 runs on a free model with small fixed question sets, so read the intervals on the ladder page before trusting a gap.
