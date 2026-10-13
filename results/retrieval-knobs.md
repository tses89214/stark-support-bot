# Retrieval knobs: `MIN_SCORE` and `TOP_K`

Run 2026-10-13 with `python eval_threshold.py` (bge-m3, local, no LLM calls): the same 85 on-topic questions and 15 off-topic ones (5 from `eval_retrieval.py` plus 10 added by hand: unrelated chat, shopping, Chinese and English). A question is refused when its best doc score is below `MIN_SCORE`.

| MIN_SCORE | on-topic refused (lost answers) | off-topic let through |
|---|---|---|
| 0.30 | 0/85 | 14/15 |
| 0.35 | 0/85 | 10/15 |
| **0.40 (current)** | 0/85 | 5/15 |
| 0.45 | 4/85 | 1/15 |
| 0.50 | 21/85 | 0/15 |
| 0.55 | 35/85 | 0/15 |
| 0.60 | 55/85 | 0/15 |

The current 0.40 refuses no real question but lets a third of the off-topic ones reach the answer step; the classifier is what stops them. 0.45 trades 4 lost answers of 85 (5%) for one leak of 15; 0.50 already loses a quarter of the real questions. The lowest on-topic score is now 0.42, just under the best off-topic score (0.43 in the retrieval set, 0.46 here), so no threshold separates the two sets cleanly. It is not changed here: the ladder's L4 numbers were measured at 0.40, so a change means re-running the ladder. With 15 off-topic questions the leak column is coarse.

| TOP_K | hit@k |
|---|---|
| 1 | 68/85 |
| 3 (current) | 81/85 |
| 5 | 84/85 |

On the 85-question set top-3 misses 4 questions, top-5 misses 1 and top-1 misses 17, so `TOP_K = 3` is a prompt-size trade (about 1.6k chars at 3, more at 5), not free. Not changed, because the ladder's L4 was measured at 3.
