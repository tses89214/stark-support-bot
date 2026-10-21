# Retrieval ladder: how the bot picks which documents to read

Question: as the document set grows (10, 20, 30 models; 27, 47, 67 files), which way of choosing documents keeps answers right without stuffing the whole library into the prompt?

- **R0** load every document into the prompt.
- **R1** embedding top-3 (bge-m3).
- **R2** top-3, or top-15 when an LLM scope check says the question is catalogue-wide.
- **R3** the LLM reads `INDEX.md` (one line per document) and names the files to open; invented paths are dropped.

Same model for every level and size: `nvidia/nemotron-3-super-120b-a12b:free`, 16 questions per run (one is graded on retrieval only, so accuracy is out of 15), **two runs per cell (cells show the mean)**. Per-question rows and traces are in MLflow (`retrieval-ladder` experiment).

| Level | n=10 acc / recall | n=20 acc / recall | n=30 acc / recall | prompt chars (n=10 → 30) | LLM calls | seconds (n=30) |
|---|---|---|---|---|---|---|
| R0 | 0.97 / 1.00 | 1.00 / 1.00 | 0.93 / 1.00 | 17,744 → 46,951 | 1 | 11.1 |
| R1 | 0.93 / 0.93 | 0.73 / 0.83 | 0.73 / 0.80 | 2,349 → 2,353 | 1 | 9.7 |
| R2 | 1.00 / 1.00 | 0.83 / 0.98 | 0.93 / 0.96 | 5,138 → 6,551 | 2 | 13.7 |
| R3 | 0.97 / 1.00 | 0.97 / 1.00 | 0.97 / 1.00 | 3,268 → 7,289 | 2 | 14.4 |

95% Wilson intervals for accuracy on 15 graded questions: 15/15 is 0.80–1.00, 14/15 is 0.70–0.99, 13/15 is 0.62–0.96, 11/15 is 0.48–0.89. **All of these intervals overlap each other**, so read the table as direction, not as a ranking.

What the numbers support, and what they do not:
- R0's prompt grows linearly with the library (about 2.6x from n=10 to n=30). Its accuracy did not fall in a way this sample can distinguish from one lost question.
- R1's recall falls as documents are added (0.93 → 0.80) because near-duplicate manuals compete for three slots.
- R2 and R3 keep recall at 0.96 and above. R3 accuracy was 0.93 → 1.00 (n=30) and 1.00 → 0.93 (n=20) between the two runs, so the run-to-run swing is as big as the R2/R3 gap; the R2-vs-R3 choice is still undecided. R3 reached 1.00 recall at all three sizes in both runs with about 16% of R0's prompt at n=30, at the cost of a second LLM call per question.
- No evidence here that an R4 (R3 plus an embedding fallback) is needed; recall for R3 never dropped.

Caveats: only two runs per cell on a free model; the manuals are templated on purpose (so catalogue questions have a computable answer); the question set is 16 questions written by the author; `llm_calls` counts calls the rate limiter refused as well, so it may read slightly high. Rerun: `python -m evals.gen_scaled_corpus N && python -m evals.eval_retrieval_ladder N` with `MLFLOW_TRACKING_URI=sqlite:///mlflow.db` (the generator wipes `data/stark_scaled/`, so never run two sizes at once).
