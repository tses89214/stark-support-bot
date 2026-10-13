# Retrieval knobs: `MIN_SCORE` and `TOP_K`

Run 2026-10-13 with `python eval_threshold.py` (bge-m3, local, no LLM calls): the same 40 on-topic questions and 15 off-topic ones (5 from `eval_retrieval.py` plus 10 added by hand: unrelated chat, shopping, Chinese and English). A question is refused when its best doc score is below `MIN_SCORE`.

| MIN_SCORE | on-topic refused (lost answers) | off-topic let through |
|---|---|---|
| 0.30 | 0/40 | 14/15 |
| 0.35 | 0/40 | 10/15 |
| **0.40 (current)** | 0/40 | 5/15 |
| 0.45 | 1/40 | 1/15 |
| 0.50 | 6/40 | 0/15 |
| 0.55 | 14/40 | 0/15 |
| 0.60 | 27/40 | 0/15 |

The current 0.40 refuses no real question but lets a third of the off-topic ones reach the answer step; the classifier is what stops them. 0.45 looks like the better trade (one lost answer of 40, one leak of 15); 0.50 already loses 6 answers. It is not changed here: the ladder's L4 numbers were measured at 0.40, so a change means re-running the ladder. With 15 off-topic questions the curve is coarse.

| TOP_K | hit@k |
|---|---|
| 1 | 34/40 |
| 3 (current) | 38/40 |
| 5 | 40/40 |

On the 40-question set top-3 misses two questions that top-5 finds, so `TOP_K = 3` is a prompt-size trade (about 1.6k chars at 3, more at 5), not free; the earlier 30-question set could not show this. Not changed, because the ladder's L4 was measured at 3.
