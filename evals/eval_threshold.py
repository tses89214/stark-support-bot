"""Retrieval knobs: `python -m evals.eval_threshold` (bge-m3, local, no LLM calls).
Part 1: MIN_SCORE sweep. A question is refused when its best doc score is below the threshold, so on-topic questions
refused = lost answers, off-topic questions let through = reach the answer step. Part 2: hit@k for TOP_K."""

from sentence_transformers import SentenceTransformer, util

from backend.build_index import DOCS_DIR, EMBED_MODEL
from evals.eval_retrieval import CASES, MORE_OFF_TOPIC, OFF_TOPIC

paths = sorted(DOCS_DIR.glob("*.txt"))
names, texts = [p.stem for p in paths], [p.read_text() for p in paths]
enc = SentenceTransformer(EMBED_MODEL)
docs = enc.encode(texts)


def search(qs, k):
    return util.semantic_search(enc.encode(qs), docs, top_k=k)


on = [h[0]["score"] for h in search([q for q, _ in CASES], 1)]
off = [h[0]["score"] for h in search(OFF_TOPIC + MORE_OFF_TOPIC, 1)]
print(
    f"{len(on)} on-topic, {len(off)} off-topic questions (on-topic min {min(on):.2f}, off-topic max {max(off):.2f})\n"
)
print("| MIN_SCORE | on-topic refused | off-topic let through |\n|---|---|---|")
for t in [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]:
    print(f"| {t:.2f} | {sum(s < t for s in on)}/{len(on)} | {sum(s >= t for s in off)}/{len(off)} |")

print("\n| TOP_K | hit@k |\n|---|---|")
for k in (1, 3, 5):
    hits = search([q for q, _ in CASES], k)
    print(
        f"| {k} | {sum(any(names[h['corpus_id']] == g for h in hit) for hit, (_, g) in zip(hits, CASES))}/{len(CASES)} |"
    )
