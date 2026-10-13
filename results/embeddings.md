# Embedding model comparison

Run 2026-10-13 with `python eval_retrieval.py <models>` (local, no LLM calls, deterministic). 85 questions (51 English, 34 Chinese) over 17 docs, at least 5 questions per doc (the set grew 30 to 40 to 85 on the same day; every number here is from the 85-question set). A question passes when the right doc is in the top 3.

| Embedding model | hit@3 (95% interval) | English | Chinese | MRR@3 | Score gap (on-topic min vs off-topic max) |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 (small English-only default) | 57/85 (57%-76%) | 48/51 | 9/34 | 0.59 | 0.06 vs 0.34, overlaps |
| paraphrase-multilingual-MiniLM-L12-v2 | 66/85 (68%-85%) | 42/51 | 24/34 | 0.61 | 0.24 vs 0.33, overlaps |
| multilingual-e5-small | 78/85 (84%-96%) | 47/51 | 31/34 | 0.85 | 0.75 vs 0.80, overlaps |
| multilingual-e5-base | 79/85 (85%-97%) | 45/51 | 34/34 | 0.81 | 0.74 vs 0.78, overlaps |
| **bge-m3 (used by the bot)** | **81/85 (89%-98%)** | 47/51 | 34/34 | 0.87 | 0.42 vs 0.43, overlaps (barely) |
| embeddinggemma-2 (run in Docker) | 83/85 (92%-99%) | 49/51 | 34/34 | 0.89 | 0.60 vs 0.68, overlaps (off-topic scores higher) |

Examples (top 3 docs returned, correct doc in **bold**; `model_N` = Stark N, `guide_*` = process guides):

| Question | all-MiniLM-L6-v2 | multilingual-e5-small | bge-m3 |
|---|---|---|---|
| 哪一款太空船可以載 30 個人? (which ship carries 30 people; answer Stark 8) | model_15, model_6, model_1: miss | model_1, **model_8**, model_10 | **model_8**, model_4, model_1 |
| 我想買一艘貨船來做貿易 (I want a cargo ship for trading; answer Stark 5) | model_15, model_4, model_3: miss | guide_ordering_delivery, model_11, guide_troubleshooting: miss | **model_5**, model_12, model_1 |
| 可以退貨嗎?要等多久才會到貨? (returns and delivery time) | model_6, model_2, model_8: miss | **guide_ordering_delivery**, model_12, model_15 | **guide_ordering_delivery**, guide_troubleshooting, model_7 |

The English-only model returns near-random ships for Chinese questions. e5-small finds some but ranks the right doc lower or misses (the cargo-ship question). Wrong retrieval means the answer step never sees the right facts.

embeddinggemma-2 ran fine on this machine, in a Docker container (the repo's pinned torch 2.2.2 is too old for its transformers 5 requirement; the hardware is not the limit). On the 85-question set it is two questions ahead of bge-m3 (83/85, MRR 0.89 vs 81/85, 0.87) with overlapping intervals, so on accuracy it is a tie within noise, not a loss. It does not separate off-topic questions either (its off-topic scores are higher than its on-topic ones). The bot uses bge-m3 because the results are about the same and bge-m3 needs fewer resources: a smaller text-only model (about 2GB, versus a multimodal one of roughly 3GB in fp32). `embeddinggemma-300m` was not run (gated).

Intervals are Wilson 95% on 85 questions. embeddinggemma-2 (83/85), bge-m3 (81/85), e5-base (79/85) and e5-small (78/85) overlap on hit@3, so the top four are close; the gap to MiniLM (57/85, Chinese 9/34) is the only large one. MRR is 0.89, 0.87, 0.81 and 0.85.
