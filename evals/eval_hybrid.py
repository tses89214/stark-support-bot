"""Hybrid retrieval on the retrieval questions: `python -m evals.eval_hybrid` (bge-m3 locally, no LLM calls, no quota).
Five ways to rank the documents for a question, same 90 cases as eval_retrieval.py:
  vector   bge-m3 cosine against the whole document (what the bot's R1/R2 use)
  chunked  bge-m3 against each sentence (with the document's title line), a document scores as its best sentence
  bm25     keyword score (Okapi BM25), so a model number or an exact word counts for more than "meaning"
  hybrid   vector and bm25 rankings merged with reciprocal rank fusion: score = sum over rankings of 1 / (60 + rank)
  rerank   the hybrid top-10 re-ordered by a cross-encoder (bge-reranker-v2-m3) that reads question and document together
Why: the vector misses questions worded unlike the document; BM25 misses synonyms; merging asks both; the cross-encoder then
judges each remaining candidate more carefully than a vector can (slower, so only for a short list).
This shows the technique and what it buys at this size; the bot itself still picks documents with R3 (see results/retrieval-ladder.md)."""

import math
import re
from collections import Counter

from sentence_transformers import CrossEncoder, SentenceTransformer, util

from backend.build_index import EMBED_MODEL
from evals.eval_retrieval import CASES, DOCS_DIR
from evals.stats import wilson

RERANKER, RERANK_TOP = "BAAI/bge-reranker-v2-m3", 10  # candidates the cross-encoder re-orders


def tokens(text):
    """Lower-case words, plus overlapping character pairs for Chinese (no spaces to split on)."""
    text = text.lower()
    words = re.findall(r"[a-z0-9]+", text)
    return words + [a + b for run in re.findall(r"[一-鿿]+", text) for a, b in zip(run, run[1:])]


def bm25_scores(query, docs, k1=1.5, b=0.75):
    """Okapi BM25 of every document for the query (docs: list of token lists)."""
    n, avg = len(docs), sum(map(len, docs)) / len(docs)
    df = Counter(t for d in docs for t in set(d))
    scores = []
    for d in docs:
        tf = Counter(d)
        scores.append(
            sum(
                math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                * tf[t]
                * (k1 + 1)
                / (tf[t] + k1 * (1 - b + b * len(d) / avg))
                for t in set(tokens(query))
                if t in tf
            )
        )

    return scores


def ranking(scores):
    """Document indices, best first."""
    return sorted(range(len(scores)), key=lambda i: -scores[i])


def fuse(*rankings, k=60):
    """Reciprocal rank fusion: documents ranked high by any list rise; one list's raw scores never need rescaling."""
    total = Counter()
    for r in rankings:
        for pos, i in enumerate(r, 1):
            total[i] += 1 / (k + pos)

    return sorted(total, key=lambda i: -total[i])


def chunks(text):
    """Sentences, each led by the document's first line (its title) so a chunk still says what it is about."""
    title, *_ = text.splitlines()
    parts = [p.strip() for p in re.split(r"(?<=[.!?。])\s+|\n+", text) if p.strip()]
    return [p if p == title.strip() else f"{title.strip()} {p}" for p in parts]


def selftest():
    """The two keyword rankings must agree on an obvious case, and fusion must lift a document both lists like."""
    docs = [
        tokens("The Stark 3 costs 5200000"),
        tokens("The Stark 8 carries 30 passengers"),
        tokens("warranty 3-year engine"),
    ]
    assert ranking(bm25_scores("how many passengers", docs))[0] == 1
    assert ranking(bm25_scores("你們的保固", [tokens("保固政策 三年"), tokens("訂單 運送")]))[0] == 0
    assert set(fuse([2, 0, 1], [0, 2, 1])[:2]) == {0, 2}  # both lists put these two first
    assert chunks("## Warranty\nThree years. Covers the hull.") == [
        "## Warranty",
        "## Warranty Three years.",
        "## Warranty Covers the hull.",
    ]
    assert fuse([0, 1, 2], [1, 0, 2])[:2] in ([0, 1], [1, 0]) and fuse([0, 1, 2], [0, 1, 2]) == [0, 1, 2]


if __name__ == "__main__":
    selftest()
    paths = sorted(DOCS_DIR.glob("*.txt"))
    names, texts = [p.stem for p in paths], [p.read_text() for p in paths]
    enc = SentenceTransformer(EMBED_MODEL)
    vectors = enc.encode(texts)
    toks = [tokens(t) for t in texts]
    pieces = [(i, c) for i, t in enumerate(texts) for c in chunks(t)]
    piece_vectors = enc.encode([c for _, c in pieces])
    reranker = CrossEncoder(RERANKER)
    results = {label: [] for label in ("vector", "chunked", "bm25", "hybrid", "rerank")}
    for q, gold in CASES:
        qv = enc.encode(q)
        v = ranking(util.cos_sim(qv, vectors)[0].tolist())
        best = [-1.0] * len(names)  # a document scores as its best sentence
        for (i, _), sc in zip(pieces, util.cos_sim(qv, piece_vectors)[0].tolist()):
            best[i] = max(best[i], sc)

        k = ranking(bm25_scores(q, toks))
        h = fuse(v, k)
        top = h[:RERANK_TOP]
        order = ranking(reranker.predict([(q, texts[i]) for i in top]).tolist())
        rr = [top[j] for j in order] + h[RERANK_TOP:]
        for label, rank in (("vector", v), ("chunked", ranking(best)), ("bm25", k), ("hybrid", h), ("rerank", rr)):
            results[label].append((q, gold, [names[i] for i in rank]))

    print(
        f"{len(CASES)} questions, {len(names)} documents ({sum(q.isascii() for q, _ in CASES)} English, {sum(not q.isascii() for q, _ in CASES)} Chinese)\n"
    )
    print(f"{'':8}{'hit@1':>8}{'hit@3':>8}{'hit@5':>8}{'  hit@3 en':>11}{'  hit@3 zh':>11}{'  MRR':>7}")
    for label, rows in results.items():
        at = lambda n, sel=lambda q: True: [g in r[:n] for q, g, r in rows if sel(q)]  # noqa: E731
        lo, hi = wilson(sum(at(3)), len(rows))
        mrr = sum(next((1 / p for p, d in enumerate(r, 1) if d == g), 0) for _, g, r in rows) / len(rows)
        en, zh = at(3, lambda q: q.isascii()), at(3, lambda q: not q.isascii())
        print(
            f"{label:8}{sum(at(1)):>5}/{len(rows)}{sum(at(3)):>5}/{len(rows)}{sum(at(5)):>5}/{len(rows)}{sum(en):>7}/{len(en)}{sum(zh):>7}/{len(zh)}{mrr:>7.2f}   hit@3 95% {lo:.0%}-{hi:.0%}"
        )

    print()
    for label in ("vector", "chunked", "bm25", "hybrid", "rerank"):
        print(f"{label} misses at top-3:")
        for q, g, r in results[label]:
            if g not in r[:3]:
                print(f"  {q!r} want {g}, got {r[:3]}")
