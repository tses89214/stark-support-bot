# Embedding model comparison

Run 2026-10-13 with `python -m evals.eval_retrieval <models>` (local, no LLM calls, deterministic). 85 questions (51 English, 34 Chinese) over 17 docs, at least 5 questions per doc (the set grew 30 to 40 to 85 on the same day; every number here is from the 85-question set). A question passes when the right doc is in the top 3.

| Embedding model | hit@3 (95% interval) | English | Chinese | MRR@3 | Score gap (on-topic min vs off-topic max) |
|---|---|---|---|---|---|
| all-MiniLM-L6-v2 (small English-only default) | 57/85 (57%-76%) | 48/51 | 9/34 | 0.59 | 0.06 vs 0.34, overlaps |
| paraphrase-multilingual-MiniLM-L12-v2 | 66/85 (68%-85%) | 42/51 | 24/34 | 0.61 | 0.24 vs 0.33, overlaps |
| multilingual-e5-small | 78/85 (84%-96%) | 47/51 | 31/34 | 0.85 | 0.75 vs 0.80, overlaps |
| multilingual-e5-base | 79/85 (85%-97%) | 45/51 | 34/34 | 0.81 | 0.74 vs 0.78, overlaps |
| **bge-m3 (used by the bot)** | **81/85 (89%-98%)** | 47/51 | 34/34 | 0.87 | 0.42 vs 0.43, overlaps (barely) |
| embeddinggemma-2 (run in Docker) | 83/85 (92%-99%) | 49/51 | 34/34 | 0.89 | 0.60 vs 0.68, overlaps (off-topic scores higher) |

Examples (top 3 docs returned, correct doc in **bold**; `model_N` = Stark N, `guide_*` = process guides). Picked where the models disagree, including the questions bge-m3 misses; embeddinggemma-2 is not in this table because it runs only in Docker:

| Question | all-MiniLM-L6-v2 | multilingual-e5-small | multilingual-e5-base | bge-m3 |
|---|---|---|---|---|
| 我想買一艘貨船來做貿易 (I want a cargo ship for trading; answer model_5) | model_15, model_4, model_3: miss | guide_ordering_delivery, model_11, guide_troubleshooting: miss | model_12, model_11, **model_5** | **model_5**, model_12, model_1 |
| 有沒有單人座的賽艇? (a single-seat racing ship; answer model_13) | model_3, guide_ordering_delivery, model_1: miss | model_1, model_11, model_15: miss | model_8, **model_13**, model_1 | **model_13**, model_1, model_11 |
| Which model fits 30 passengers? (answer model_8) | **model_8**, model_3, model_6 | model_10, model_3, model_6: miss | model_10, model_6, model_3: miss | model_10, **model_8**, model_6 |
| Which ship needs the oxygen recycling system checked on trips over 10 days? (answer model_4) | **model_4**, guide_ordering_delivery, model_8 | guide_ordering_delivery, guide_troubleshooting, model_15: miss | guide_troubleshooting, model_8, model_11: miss | model_8, guide_ordering_delivery, guide_troubleshooting: miss |
| How often should I run energy core diagnostics? (answer model_9) | **model_9**, guide_troubleshooting, model_14 | guide_troubleshooting, **model_9**, model_13 | guide_troubleshooting, model_13, **model_9** | guide_troubleshooting, model_8, model_14: miss |
| Which ship has Life Support Expansion Modules? (answer model_8) | model_4, model_7, **model_8** | model_11, **model_8**, guide_troubleshooting | model_14, model_11, model_7: miss | model_14, model_11, model_7: miss |

The English-only model returns near-random ships for Chinese questions. e5-small finds some but ranks the right doc lower or misses (the cargo-ship question). The English rows show the other side: the English-only MiniLM finds all three English questions in this table that bge-m3 misses, so bge-m3 is not best everywhere, only best on Chinese. Wrong retrieval means the answer step never sees the right facts.

embeddinggemma-2 ran fine on this machine, in a Docker container (the repo's pinned torch 2.2.2 is too old for its transformers 5 requirement; the hardware is not the limit). On the 85-question set it is two questions ahead of bge-m3 (83/85, MRR 0.89 vs 81/85, 0.87) with overlapping intervals, so on accuracy it is a tie within noise, not a loss. It does not separate off-topic questions either (its off-topic scores are higher than its on-topic ones). The bot uses bge-m3 because the results are about the same and bge-m3 needs fewer resources: a smaller text-only model (about 2GB, versus a multimodal one of roughly 3GB in fp32). `embeddinggemma-300m` was not run (gated).

Intervals are Wilson 95% on 85 questions. embeddinggemma-2 (83/85), bge-m3 (81/85), e5-base (79/85) and e5-small (78/85) overlap on hit@3, so the top four are close; the gap to MiniLM (57/85, Chinese 9/34) is the only large one. MRR is 0.89, 0.87, 0.81 and 0.85.
