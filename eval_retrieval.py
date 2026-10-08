"""Retrieval eval: `python eval_retrieval.py [model ...]` prints hit@3 per embedding model plus the score range used to pick MIN_SCORE.
No LLM calls, so it is free. Each case is (question, doc that must be in the top 3)."""
import sys

from sentence_transformers import SentenceTransformer, util

from build_index import DOCS_DIR, EMBED_MODEL

CASES = [
    ("How much is the Stark 3?", "model_3"),
    ("Which model fits 30 passengers?", "model_8"),
    ("What color is the Stark 6?", "model_6"),
    ("I need a ship to haul cargo for trade missions", "model_5"),
    ("Which ship is the fastest?", "model_3"),
    ("What size screws go in the cargo hold of the Stark 5?", "model_5"),
    ("Which model is the flagship?", "model_10"),
    ("Is there a single-seat racing ship?", "model_13"),
    ("Can the Stark 12 carry passengers?", "model_12"),
    ("Which ship has a private chef module?", "model_11"),
    ("How often should I replace dust filters on the planetary explorer?", "model_15"),
    ("Which ship is built for scientific research in deep space?", "model_14"),
    ("哪一款太空船可以載 30 個人?", "model_8"),
    ("Stark 1 的價格是多少?", "model_1"),
    ("我想買一艘貨船來做貿易", "model_5"),
    ("有沒有單人座的賽艇?", "model_13"),
    ("豪華蜜月旅行適合哪一款?", "model_11"),
    ("哪一款適合在沙漠星球探險?", "model_15"),
    ("科學研究用的太空船有哪些?", "model_14"),
    ("最貴的旗艦機型是哪一款?", "model_10"),
]
OFF_TOPIC = ["What's the capital of France?", "Write me a Python script to sort a list.",
             "Do you sell submarines?", "法國的首都是哪裡?", "今天天氣如何?"]
# (model, query prefix, passage prefix): e5 models need these prefixes, the others don't
MODELS = [("sentence-transformers/all-MiniLM-L6-v2", "", ""), (EMBED_MODEL, "", ""), ("paraphrase-multilingual-MiniLM-L12-v2", "", ""),
          ("intfloat/multilingual-e5-small", "query: ", "passage: "), ("intfloat/multilingual-e5-base", "query: ", "passage: ")]

if __name__ == "__main__":
    paths = sorted(DOCS_DIR.glob("*.txt"))
    names, texts = [p.stem for p in paths], [p.read_text() for p in paths]
    wanted = sys.argv[1:]
    for model, qp, pp in [m for m in MODELS if not wanted or m[0] in wanted]:
        enc = SentenceTransformer(model)
        docs = enc.encode([pp + t for t in texts])
        search = lambda qs: util.semantic_search(enc.encode([qp + q for q in qs]), docs, top_k=3)
        hits = search([q for q, _ in CASES])
        ok = [any(names[h["corpus_id"]] == gold for h in hit) for hit, (_, gold) in zip(hits, CASES)]
        en, zh = ok[:12], ok[12:]
        on = [hit[0]["score"] for hit in hits]
        off = [hit[0]["score"] for hit in search(OFF_TOPIC)]
        print(f"{model}\n  hit@3 {sum(ok)}/{len(ok)}  (en {sum(en)}/{len(en)}, zh {sum(zh)}/{len(zh)})"
              f"\n  top score: on-topic min {min(on):.2f}, off-topic max {max(off):.2f}")
        for (q, gold), good in zip(CASES, ok):
            if not good:
                print(f"  MISS {q!r} (want {gold})")
