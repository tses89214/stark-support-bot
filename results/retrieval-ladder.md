# Retrieval ladder: how the bot picks which documents to read

Question: as the document set grows (10, 20, 30 models; 27, 47, 67 files), which way of choosing documents keeps answers right without stuffing the whole library into the prompt?

- **R0** load every document into the prompt.
- **R1** embedding top-3 (bge-m3).
- **R2** top-3, or top-15 when an LLM scope check says the question is catalogue-wide.
- **R3** the LLM reads `INDEX.md` (one line per document) and names the files to open; invented paths are dropped.

Same model for every level and size: `nvidia/nemotron-3-ultra-550b-a55b:free` (reasoning off), 16 questions per run (one is graded on retrieval only, so accuracy is out of 15), **two runs per cell (cells show the mean)**. Per-question rows and traces are in MLflow (`retrieval-ladder` experiment).

| Level | n=10 acc / recall | n=20 acc / recall | n=30 acc / recall | prompt chars (n=10 → 30) | LLM calls | seconds (n=30) |
|---|---|---|---|---|---|---|
| R0 | 0.83 / 1.00 | 0.87 / 1.00 | 0.90 / 1.00 | 17,744 → 46,951 | 1 | 3.6 |
| R1 | 0.87 / 0.93 | 0.67 / 0.83 | 0.67 / 0.80 | 2,349 → 2,353 | 1 | 5.7 |
| R2 | 0.83 / 1.00 | 0.87 / 0.98 | 0.80 / 0.96 | 4,558 → 5,001 | 2 | 5.1 |
| R3 | 0.87 / 1.00 | 0.90 / 1.00 | 0.87 / 1.00 | 2,822 → 7,289 | 2 | 3.9 |

95% Wilson intervals for accuracy on 15 graded questions: 15/15 is 0.80–1.00, 14/15 is 0.70–0.99, 13/15 is 0.62–0.96, 11/15 is 0.48–0.89. **All of these intervals overlap each other**, so read the table as direction, not as a ranking.

What the numbers support, and what they do not:
- R0's prompt grows linearly with the library (about 2.6x from n=10 to n=30) and its accuracy (0.83 to 0.90) is no better than R3's (0.87 to 0.90) on this set, so loading everything buys nothing here except cost.
- R1's recall falls as documents are added (0.93 → 0.80) because near-duplicate manuals compete for three slots, and its accuracy falls with it (0.87 → 0.67).
- R2 and R3 keep recall at 0.96 and above; R3 reached 1.00 at all three sizes in both runs, with about 16% of R0's prompt at n=30, at the cost of a second LLM call per question. R3's accuracy (0.87 to 0.90) is 0.03 to 0.07 above R2's (0.80 to 0.87), which is one question or less and inside the run-to-run swing, so the R2-versus-R3 choice is still undecided and the app keeps R2.
- No evidence here that an R4 (R3 plus an embedding fallback) is needed; recall for R3 never dropped.
- Not tested: the 16 questions never ask about five of the 67 documents (contact and hours, ordering guide, troubleshooting guide, safety regulations, trade-in). A 21-question set that asks about each of them is in `evals/eval_retrieval_ladder.py` and is scheduled to be rerun; these tables come from the 16-question set.

Caveats: only two runs per cell on a free model; the manuals are templated on purpose (so catalogue questions have a computable answer); the question set is 16 questions written by the author; `llm_calls` counts calls the rate limiter refused as well, so it may read slightly high. Rerun: `python -m evals.gen_scaled_corpus N && python -m evals.eval_retrieval_ladder N` with `MLFLOW_TRACKING_URI=sqlite:///mlflow.db` (the generator wipes `data/stark_scaled/`, so never run two sizes at once).
