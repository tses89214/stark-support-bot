# Chunking, hybrid search and reranking

Run 2026-10-22 with `python -m evals.eval_hybrid` (bge-m3 and `BAAI/bge-reranker-v2-m3`, local, no LLM calls). The same 90 retrieval questions as `eval_retrieval.py` (54 English, 36 Chinese) against the 33 product documents; a question is a hit when the right document is among the top 3.

| Method | What it does | hit@1 | hit@3 (95% interval) | hit@5 | English hit@3 | Chinese hit@3 | MRR |
|---|---|---|---|---|---|---|---|
| vector | bge-m3 against the whole document (what R1/R2 use) | 68/90 | 76/90 (76%–91%) | 82/90 | 41/54 | 35/36 | 0.82 |
| chunked | bge-m3 against each sentence with the document's title line; a document scores as its best sentence | 83/90 | **87/90 (91%–99%)** | 89/90 | 53/54 | 34/36 | 0.95 |
| bm25 | keyword score (Okapi BM25; Chinese split into character pairs) | 52/90 | 67/90 (65%–82%) | 77/90 | 46/54 | 21/36 | 0.68 |
| hybrid | vector + bm25 rankings merged by reciprocal rank fusion (1 / (60 + rank)) | 66/90 | 81/90 (82%–95%) | 83/90 | 50/54 | 31/36 | 0.83 |
| rerank | the hybrid top 10 re-ordered by a cross-encoder that reads question and document together | **85/90** | 86/90 (89%–98%) | 86/90 | 53/54 | 33/36 | 0.95 |

What the numbers say:
- **Chunking helped most** here (76 to 87 of 90, MRR 0.82 to 0.95). A document is a few facts packed into one vector; one sentence per vector keeps "Terrain Scanning System" or "Extra Sleeping Pods" from being averaged away. This works because the documents are tiny and each fact is one sentence; it is not a claim about long documents, where chunk size would have to be tuned.
- **Hybrid** repaired English wording problems that the vector missed (41 to 50 of 54 English) but lost some Chinese (35 to 31 of 36): BM25 on character pairs is noisy for short Chinese questions, and fusion carries that noise in. BM25 alone is weak (67/90) and fails almost every Chinese question that does not name a model.
- **Rerank** gives the best first place (hit@1 85/90 against 68/90 for vector), but it can only re-order what hybrid retrieved: the two Chinese warranty questions are missed because `warranty_policy` was not in the hybrid top 10, and the cross-encoder never saw it. Rerank is a precision tool; recall has to come from the stage before it.
- Misses left after chunking: "Which ship is the fastest?" (the right document never says "fastest"), the Chinese cargo-trade question, and "royal gold" (哪一款是皇家金色的太空船). Those are vocabulary gaps no ranking method here closes.

Caveats: one run per method (all deterministic, no sampling); the intervals overlap between chunked, rerank and hybrid, so only "chunked, rerank and hybrid beat vector and bm25" is supported, not an order among the three; the combination chunked + BM25 + rerank was not tried. The bot itself still chooses documents with R3 (the LLM reads the index); this page measures embedding-side techniques, which R1 and R2 would use. At 33 documents none of this is needed, which is why the product does not use it.
