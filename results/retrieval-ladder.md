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

## A failure case from the live demo: what R2 and R3 do when the question cannot be resolved

One real conversation (2026-10-21, defense L4, 33 documents), six turns: a honeymoon couple asks for something special, says they like a small ship, picks the Stark 1, asks how to order, asks "Any warranty?" and then **"what color is it ?"**. The classifier left the last question as it was (the "it" was not replaced), so retrieval had no model to look for. The conversation state already held `Stark 1`; nothing used it.

I replayed that last turn with the stored history under both retrieval modes (R2 twice, R3 twice, same question `what color is it ?`):

| Mode | Documents chosen | What the customer saw |
|---|---|---|
| R2 (embedding, previous user turn prefixed) | `warranty_policy`, `model_3`, `model_10` (both runs) | "There is no mention of a Stark 1 in the available documents", a false statement, then details of the Stark 3 and Stark 10 |
| R3 (LLM reads the index) | none (both runs) | "I couldn't find that in our product documents. Please email customer_service@stack_spaceship.com" |

With the question already resolved (`What color is the Stark 1?`) both modes work: R2 returns `model_1, model_13, model_3`, R3 returns `model_1` alone.

What this shows, and what it does not:
- **Not** evidence that R3 answers better: on the unresolved question neither mode answered it. One conversation, two runs per mode, is an illustration, not a measurement; the ranking above (R2 .80-.87 vs R3 .87-.90, overlapping intervals) is unchanged.
- It does show a different **failure mode**. An embedding search always returns the nearest documents, so when the query is empty of meaning R2 fails open: wrong documents and a confident wrong sentence. R3 lets the model choose and it chose nothing, so it fails closed into the "ask a human" reply. For a support bot a refusal is cheaper than a false "there is no such model".
- Resolved, R3 reads one document where R2 reads three, so it also costs less prompt.

What was fixed in the bot (the failure was upstream of the retrieval choice): the conversation state is now a `Focus` object (`talking_about`, `interested_in`, `goal`) filled on every turn from the classifier and kept on the server; a follow-up that names no model gets the model from it (`what color is it ? (about Stark 1)`), and a model the question names is always read. The embedding query leaves the model name out, otherwise "does the Stark 1 have a warranty?" returned only model sheets and never the warranty policy. Replayed live after the fix: "what color is it ?" → `model_1` first, Metallic Silver; "Any warranty?" → `model_1, warranty_policy`, 3 years or 20,000 flight hours; "Stark 3 的保固期是幾年?" → `model_3, warranty_policy`. These live checks are single runs; the 16-question ladder above was **not** rerun with the new retrieval code (R1 and R2 here are the earlier implementation), so the table is still the evidence for R2 vs R3 and the choice is still open.

