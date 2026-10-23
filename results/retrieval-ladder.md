# Retrieval ladder: how the bot picks which documents to read

Question: as the document set grows (10, 20, 30 models; 27, 47, 67 files), which way of choosing documents keeps answers right without stuffing the whole library into the prompt?

- **R0** load every document into the prompt.
- **R1** embedding top-3 (bge-m3).
- **R2** top-3, or every document when an LLM scope check says the question is catalogue-wide.
- **R3** the LLM reads `INDEX.md` (one line per document) and names the files to open; invented paths are dropped.

Same model for every level and size: `nvidia/nemotron-3-ultra-550b-a55b:free` (reasoning off), 21 questions per run (one is graded on retrieval only, so accuracy is out of 20), **two runs per cell, pooled (40 graded answers per cell)**, 0 failed calls in all 24 runs. Run 2026-10-22; **the R2 row (all three sizes) and the R3 n=30 cell were rerun on 2026-10-23** (two runs each; R2 after its catalogue-wide branch changed from top-15 to every document, R3 after the document-picker, classifier and answer prompts changed on 10-22), the other cells are still from 10-22. Per-question rows and traces are in MLflow (`retrieval-ladder` experiment).

| Level | n=10 acc / recall | n=20 acc / recall | n=30 acc / recall | prompt chars (n=10 ~ n=30) | LLM calls | seconds (n=30) |
|---|---|---|---|---|---|---|
| R0 | 0.93 / 1.00 | 0.93 / 1.00 | 0.95 / 1.00 | 17,744 ~ 46,951 | 1 | 4.4 |
| R1 | 0.95 / 0.95 | 0.80 / 0.87 | 0.75 / 0.85 | 2,215 ~ 2,268 | 1 | 3.4 |
| R2 | 0.93 / 1.00 | 0.93 / 1.00 | 0.98 / 1.00 | 4,868 ~ 11,780 | 2 | 8.4 |
| R3 | 0.95 / 1.00 | 0.93 / 1.00 | 0.93 / 0.98 | 2,263 ~ 5,240 | 2 | 10.0 |

95% Wilson intervals for accuracy at n=30 (40 graded answers per cell): R0 38/40 is 0.83–0.99, R1 30/40 is 0.60–0.86, R2 39/40 is 0.87–1.00, R3 37/40 is 0.80–0.97. At n=20: R0, R2 and R3 37/40 (0.80–0.97), R1 32/40 (0.65–0.90). R2 and R3 overlap at every size; R1 at n=30 is the only cell clearly below the others.

What the numbers support, and what they do not:
- R0's prompt grows linearly with the library (about 2.6x from n=10 to n=30) and its accuracy (0.93 to 0.95) is no better than R3's (0.93 to 0.95), so loading everything buys nothing except cost.
- R1's recall falls as documents are added (0.95 → 0.85) because near-duplicate manuals compete for three slots, and its accuracy falls with it (0.95 → 0.75).
- With "catalogue-wide question: read everything", R2 matches R3: accuracy 0.93, 0.93, 0.98 against R3's 0.95, 0.93, 0.93, and recall 1.00 in every run (R3 dropped to 0.95 once). The intervals overlap completely, so there is no measurable difference in accuracy. What differs is the prompt: at n=30 R2 sends 11.8k chars (25% of R0) and R3 5.2k (11%), because R2 reads all 30 sheets for every catalogue question. Both take two LLM calls per question. An earlier R2 variant that read the top 15 instead of everything scored 0.80 and 0.85 at n=20 and n=30: the cap of 15 cannot hold 30 models, so that gap came from the cap, not from the idea. The app's default was switched to R3 on 2026-10-21 by the owner's decision, based on how each fails (R2's top-3 path picks wrong documents and answers wrongly; R3 that picks too few asks the customer back); these numbers neither contradict nor separate the two.
- No evidence here that an R4 (R3 plus an embedding fallback) is needed; recall for R3 dropped once, to 0.95 in one of the 2026-10-23 reruns (one document missed), R2 never dropped; that is not enough to call for it.
- The 21 questions include one for each of the five documents the earlier 16-question set never asked about (contact and hours, ordering guide, troubleshooting guide, safety regulations, trade-in). Whether R1 and R2 miss those more than the others was not broken out per question; the rows are in MLflow.

Caveats: only two runs per cell on a free model; the manuals are templated on purpose (so catalogue questions have a computable answer); the question set is 21 questions written by the author; `llm_calls` counts calls the rate limiter refused as well, so it may read slightly high. Rerun: `python -m evals.gen_scaled_corpus N && python -m evals.eval_retrieval_ladder N` with `MLFLOW_TRACKING_URI=sqlite:///data/runtime/mlflow.db` (the generator wipes `data/stark_scaled/`, so never run two sizes at once; afterwards restore it with `python -m evals.gen_scaled_corpus 30`).

## A failure case from the live demo: what R2 and R3 do when the question cannot be resolved

One real conversation (2026-10-21, defense L4, 33 documents), six turns: a honeymoon couple asks for something special, says they like a small ship, picks the Stark 1, asks how to order, asks "Any warranty?" and then **"what color is it ?"**. The classifier left the last question as it was (the "it" was not replaced), so retrieval had no model to look for. The conversation state already held `Stark 1`; nothing used it.

I replayed that last turn with the stored history under both retrieval modes (R2 twice, R3 twice, same question `what color is it ?`):

| Mode | Documents chosen | What the customer saw |
|---|---|---|
| R2 (embedding, previous user turn prefixed) | `warranty_policy`, `model_3`, `model_10` (both runs) | "There is no mention of a Stark 1 in the available documents", a false statement, then details of the Stark 3 and Stark 10 |
| R3 (LLM reads the index) | none (both runs) | "I couldn't find that in our product documents. Please email customer_service@stark_spaceship.com" |

With the question already resolved (`What color is the Stark 1?`) both modes work: R2 returns `model_1, model_13, model_3`, R3 returns `model_1` alone.

What this shows, and what it does not:
- **Not** evidence that R3 answers better: on the unresolved question neither mode answered it. One conversation, two runs per mode, is an illustration, not a measurement; the ranking above (R2 .80-.85 vs R3 .93-.97 at n=20 and 30, overlapping intervals) points the same way.
- It does show a different **failure mode**. An embedding search always returns the nearest documents, so when the query is empty of meaning R2 fails open: wrong documents and a confident wrong sentence. R3 lets the model choose and it chose nothing, so it fails closed into the "ask a human" reply. For a support bot a refusal is cheaper than a false "there is no such model".
- Resolved, R3 reads one document where R2 reads three, so it also costs less prompt.

What was fixed in the bot (the failure was upstream of the retrieval choice): the conversation state is now a `Focus` object (`talking_about`, `interested_in`, `goal`) filled on every turn from the classifier and kept on the server; a follow-up that names no model gets the model from it (`what color is it ? (about Stark 1)`), and a model the question names is always read. The embedding query leaves the model name out, otherwise "does the Stark 1 have a warranty?" returned only model sheets and never the warranty policy. Replayed live after the fix: "what color is it ?" → `model_1` first, Metallic Silver; "Any warranty?" → `model_1, warranty_policy`, 3 years or 20,000 flight hours; "Stark 3 的保固期是幾年?" → `model_3, warranty_policy`. These live checks are single runs; the 16-question ladder above was **not** rerun with the new retrieval code (R1 and R2 here are the earlier implementation), so the table is still the evidence for R2 vs R3 and the choice is still open.

