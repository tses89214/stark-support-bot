# Results

Each page covers one question; they are independent, read the one you need.

| Page | Question | Produced by |
|---|---|---|
| [Defense ladder](results/ladder.md) | How much does each defense (answer rules, input fence, classifier, retrieval) add, from a deliberately defenseless bot to the real one? Scores, intervals, caveats. | `eval_ladder.py` (live LLM calls) |
| [Ladder examples](results/ladder-examples.md) | What does the model actually receive at each level, and what does it reply to real attacks? | same run as the ladder |
| [Embedding models](results/embeddings.md) | Which embedding model retrieves the right doc, especially for Chinese questions? | `eval_retrieval.py` (local) |
| [Retrieval knobs](results/retrieval-knobs.md) | Is the score floor `MIN_SCORE = 0.4` and `TOP_K = 3` a good setting? | `eval_threshold.py` (local) |

Headline: attacks blocked rise from 12/28 (no defenses) to 26.5/26.5 scored (2 mixed-request attacks excluded: the classifier model returns empty content for them) (the real bot) without losing any normal question; answer rules, input fence and classifier each add a step, and neighbouring intervals overlap. The numbers are from 2 runs on a free model with small fixed question sets, so read the intervals on the ladder page before trusting a gap.
