# Embedding model comparison

Run 2026-10-13 with `python eval_retrieval.py <models>` (local, no LLM calls, deterministic). 40 questions (24 English, 16 Chinese) over 17 docs, at least 2 questions per doc; a question passes when the right doc is in the top 3. The set grew from 30 to 40 questions on 2026-10-13, so all rows except embeddinggemma-2 were re-run; that row is from the 30-question set.

| Embedding model | hit@3 (95% interval) | English | Chinese | MRR@3 | Score gap (on-topic min vs off-topic max) |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 (small English-only default) | 25/40 (47%-76%) | 23/24 | 2/16 | 0.54 | 0.06 vs 0.34, overlaps |
| paraphrase-multilingual-MiniLM-L12-v2 | 31/40 (62%-88%) | 20/24 | 11/16 | 0.64 | 0.27 vs 0.33, overlaps |
| multilingual-e5-small | 36/40 (77%-96%) | 22/24 | 14/16 | 0.81 | 0.75 vs 0.80, overlaps |
| multilingual-e5-base | 38/40 (83%-99%) | 22/24 | 16/16 | 0.77 | 0.77 vs 0.78, overlaps |
| **bge-m3 (used by the bot)** | **38/40 (83%-99%)** | 22/24 | 16/16 | **0.90** | 0.45 vs 0.43, barely separates |
| embeddinggemma-2 (earlier 30-question set, not re-run: needs Docker) | 29/30 (83%-99%) | 16/17 | 13/13 | 0.93 | 0.60 vs 0.68, overlaps (off-topic scores higher) |

Examples (top 3 docs returned, correct doc in **bold**; `model_N` = Stark N, `guide_*` = process guides):

| Question | all-MiniLM-L6-v2 | multilingual-e5-small | bge-m3 |
|---|---|---|---|
| 哪一款太空船可以載 30 個人? (which ship carries 30 people; answer Stark 8) | model_15, model_6, model_1: miss | model_1, **model_8**, model_10 | **model_8**, model_4, model_1 |
| 我想買一艘貨船來做貿易 (I want a cargo ship for trading; answer Stark 5) | model_15, model_4, model_3: miss | guide_ordering_delivery, model_11, guide_troubleshooting: miss | **model_5**, model_12, model_1 |
| 可以退貨嗎?要等多久才會到貨? (returns and delivery time) | model_6, model_2, model_8: miss | **guide_ordering_delivery**, model_12, model_15 | **guide_ordering_delivery**, guide_troubleshooting, model_7 |

The English-only model returns near-random ships for Chinese questions. e5-small finds some but ranks the right doc lower or misses (the cargo-ship question). Wrong retrieval means the answer step never sees the right facts.

embeddinggemma-2 (run in Docker, since it needs a newer torch than this Intel Mac has) was within one question of bge-m3 on the 30-question set and does not separate off-topic questions either, so the bot keeps bge-m3. `embeddinggemma-300m` was not run (gated).

Intervals are Wilson 95% on 40 questions (gemma-2: 30), so they are wide and overlap: bge-m3, e5-base and e5-small are not separable on hit@3; MRR and the Chinese split are what set bge-m3 apart, and even those are one or two questions.
