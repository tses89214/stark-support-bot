# Results

Each page covers one question; they are independent, read the one you need.

| Page | Question | Produced by |
|---|---|---|
| [Defense ladder](ladder.md) | How much does each defense (answer rules, input fence, classifier, retrieval) add, from a deliberately defenseless bot to the real one? Scores, intervals, caveats. | `python -m evals.eval_ladder` (live LLM calls) |
| [Input classifier](guardrails.md) | How accurate is the 7-category input filter, and what does it get wrong? | `python -m evals.eval_guardrails` (live LLM calls) |
| [Ladder examples](ladder-examples.md) | What does the model actually receive at each level, and what does it reply to real attacks? | same run as the ladder |
| [Embedding models](embeddings.md) | Which embedding model retrieves the right doc, especially for Chinese questions? | `python -m evals.eval_retrieval` (local) |
| [Retrieval knobs](retrieval-knobs.md) | Is the score floor `MIN_SCORE = 0.4` and `TOP_K = 3` a good setting? | `python -m evals.eval_threshold` (local) |
| [Retrieval ladder](retrieval-ladder.md) | As the library grows from 10 to 30 models, which way of choosing documents (load all, embedding, scope check, LLM-read index) keeps answers right? | `python -m evals.eval_retrieval_ladder` (live LLM calls, MLflow) |

Headline: attacks blocked rise from 17/28 (no defenses) to 28/28 (the real bot) without losing any normal question; answer rules, input fence and classifier each add a step, and neighbouring intervals overlap. The numbers are from the single model `nvidia/nemotron-3-ultra-550b-a55b:free` (reasoning off), 2 runs per level on a free tier, with small fixed question sets, so read the intervals on the ladder page before trusting a gap.
