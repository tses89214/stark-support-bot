# Retrieval knobs: `MIN_SCORE` and `TOP_K`

Run 2026-10-13 with `python -m evals.eval_threshold` (bge-m3, local, no LLM calls): the same 85 on-topic questions (90 after the 2026-10-21 re-run, see below) and 15 off-topic ones (5 from `eval_retrieval.py` plus 10 added by hand: unrelated chat, shopping, Chinese and English). A question is refused when its best doc score is below `MIN_SCORE`.

| MIN_SCORE | on-topic refused (lost answers) | off-topic let through |
|---|---|---|
| 0.30 | 0/85 | 15/15 |
| 0.35 | 0/85 | 10/15 |
| **0.40 (current)** | 0/85 | 6/15 |
| 0.45 | 3/85 | 2/15 |
| 0.50 | 18/85 | 0/15 |
| 0.55 | 34/85 | 0/15 |
| 0.60 | 53/85 | 0/15 |

Re-run 2026-10-21 on the grown corpus (30 models, 33 files; the numbers above and below are from this run, the first version of this page was 15 models). The current 0.40 refuses no real question but lets 6 of 15 off-topic ones reach the answer step; the classifier is what stops them. 0.45 trades 3 lost answers of 85 for 4 fewer leaks; 0.50 already loses a fifth of the real questions. The lowest on-topic score is 0.42 and the highest off-topic score is 0.47, so no threshold separates the two sets cleanly. `MIN_SCORE` is left at 0.40 until the ladder is re-run. With 15 off-topic questions the leak column is coarse.

| TOP_K | hit@k |
|---|---|
| 1 | 63/85 |
| 3 (current) | 71/85 |
| 5 | 77/85 |

On the 85-question set top-3 misses 14 questions, top-5 misses 8 and top-1 misses 22 (it was 4, 1 and 17 when the corpus had 15 models). `TOP_K = 3` is a prompt-size trade (about 1.6k chars at 3, more at 5), not free. Not changed.

Re-run 2026-10-21 after five warranty questions (en 3, zh 2; `warranty_policy` had none) were added to `eval_retrieval.py`: 90 on-topic questions, same 15 off-topic. All five warranty questions hit at top-3. The on-topic min (0.42) and off-topic max (0.47) did not change, so the conclusions above hold.

| MIN_SCORE | on-topic refused | off-topic let through |
|---|---|---|
| 0.35 | 0/90 | 10/15 |
| 0.40 (current) | 0/90 | 6/15 |
| 0.45 | 3/90 | 2/15 |
| 0.50 | 18/90 | 0/15 |

| TOP_K | hit@k (90 questions) |
|---|---|
| 1 | 68/90 |
| 3 (current) | 76/90 |
| 5 | 82/90 |
