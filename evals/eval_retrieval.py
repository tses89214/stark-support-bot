"""Retrieval eval: `python -m evals.eval_retrieval [model ...]` prints hit@3 per embedding model plus the score range used to pick MIN_SCORE.
No LLM calls, so it is free. Each case is (question, doc that must be in the top 3)."""

import sys

from sentence_transformers import SentenceTransformer, util

from backend.build_index import DOCS_DIR, EMBED_MODEL
from evals.stats import wilson

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
    ("How do I place an order?", "guide_ordering_delivery"),
    ("My ship arrived damaged, what should I do?", "guide_ordering_delivery"),
    ("可以退貨嗎?要等多久才會到貨?", "guide_ordering_delivery"),
    ("The ship will not start, what should I check?", "guide_troubleshooting"),
    ("推進器飛行時一直震動怎麼辦?", "guide_troubleshooting"),
    ("導航 AI 方向不對要怎麼處理?", "guide_troubleshooting"),
    ("something in the engine area shakes when I fly", "guide_troubleshooting"),
    ("我想買船,第一步要做什麼?", "guide_ordering_delivery"),
    ("cheapest ship for one person who likes racing", "model_13"),
    ("全家出遊適合哪一款?", "model_4"),
    # added 2026-10-13: every doc now has at least 2 questions
    ("How often does the Stark 1's ion propulsion need maintenance?", "model_1"),
    ("How many passengers fit in the Stark 2?", "model_2"),
    ("Stark 2 的電漿護盾多久要換一次?", "model_2"),
    ("Which ship needs the oxygen recycling system checked on trips over 10 days?", "model_4"),
    ("How do I clean the gold-plated parts on the luxury model?", "model_6"),
    ("Which ship has adaptive landing gear?", "model_7"),
    ("Stark 7 的地形感測器需要校準嗎?", "model_7"),
    ("How often should I run energy core diagnostics?", "model_9"),
    ("Stark 9 是什麼顏色?", "model_9"),
    ("How many tons of cargo can the heavy hauler carry?", "model_12"),
    # added 2026-10-13 (round 2): every doc now has at least 5 questions
    ("最便宜的太空船是哪一款?", "model_1"),
    ("Which ship works with the Solar Power Booster?", "model_1"),
    ("Stark 1 的顏色是什麼?", "model_1"),
    ("Which ship has a Terrain Scanning System accessory?", "model_2"),
    ("Stark 2 的價格是多少?", "model_2"),
    ("How many meters long is the Stark 2?", "model_2"),
    ("What accessories are compatible with the Stark 3?", "model_3"),
    ("Stark 3 是什麼顏色?", "model_3"),
    ("What paint should I use on the speed model's exterior?", "model_3"),
    ("Stark 4 可以載多少人?", "model_4"),
    ("What is the price of the Stark 4?", "model_4"),
    ("Which ship has Extra Sleeping Pods?", "model_4"),
    ("How many tons of cargo can the Stark 5 hold?", "model_5"),
    ("Which ship uses Cargo Lifting Cranes?", "model_5"),
    ("Which ship has Galaxy View Windows?", "model_6"),
    ("Stark 6 的價格是多少?", "model_6"),
    ("哪一款是皇家金色的太空船?", "model_6"),
    ("Stark 7 載客幾人?", "model_7"),
    ("Which ship has Hazard Detection Systems?", "model_7"),
    ("Forest Green 的太空船是哪一款?", "model_7"),
    ("How often should the Stark 8 air filters be replaced?", "model_8"),
    ("Which ship has Life Support Expansion Modules?", "model_8"),
    ("Stark 8 多少錢?", "model_8"),
    ("Which ship comes with Research Modules and Energy Amplifiers?", "model_9"),
    ("Stark 9 的價格是多少?", "model_9"),
    ("Which ship is chrome with neon highlights?", "model_9"),
    ("Who may handle the anti-gravity stabilization unit during maintenance?", "model_10"),
    ("Stark 10 載客量是多少?", "model_10"),
    ("Which model has Multi-Dimensional Communication Systems?", "model_10"),
    ("How often must the observation deck glass be re-polarized?", "model_11"),
    ("Which ship has a Champagne Cooling Bar?", "model_11"),
    ("Stark 11 的價格是多少?", "model_11"),
    ("Stark 12 的顏色是什麼?", "model_12"),
    ("How should cargo be balanced before takeoff on the heavy hauler?", "model_12"),
    ("Which ship has Magnetic Container Locks?", "model_12"),
    ("How often does the racer's engine need a full inspection?", "model_13"),
    ("Stark 13 的價格是多少?", "model_13"),
    ("Which ship has a Telescope Array?", "model_14"),
    ("How should lab modules be prepared before each new mission?", "model_14"),
    ("Stark 14 載多少名研究員?", "model_14"),
    ("Which ship has a Rover Bay?", "model_15"),
    ("Stark 15 的價格是多少?", "model_15"),
    ("Which ship has All-Terrain Landing Skids?", "model_15"),
    ("What deposit percentage do I pay to confirm an order?", "guide_ordering_delivery"),
    ("艙壓警告出現時該怎麼辦?", "guide_troubleshooting"),
    # added 2026-10-21: the warranty policy had no question at all
    ("How long is the warranty?", "warranty_policy"),
    ("What does the warranty cover?", "warranty_policy"),
    ("保固期是多久?", "warranty_policy"),
    ("Is cosmetic wear covered by the warranty?", "warranty_policy"),
    ("跳過保養造成的損壞有保固嗎?", "warranty_policy"),
]
OFF_TOPIC = [
    "What's the capital of France?",
    "Write me a Python script to sort a list.",
    "Do you sell submarines?",
    "法國的首都是哪裡?",
    "今天天氣如何?",
]
MORE_OFF_TOPIC = [
    "How do I bake sourdough bread?",
    "What is the best way to learn guitar?",
    "Who won the last World Cup?",
    "Can you recommend a good laptop?",
    "Do you sell used cars?",
    "明天台北會下雨嗎?",
    "推薦一部好看的電影",
    "怎麼學英文比較快?",
    "你們有賣腳踏車嗎?",
    "幫我翻譯這句話成日文",
]
# (model, query prefix, passage prefix): e5 models need these prefixes, the others don't
MODELS = [
    ("sentence-transformers/all-MiniLM-L6-v2", "", ""),
    (EMBED_MODEL, "", ""),
    ("paraphrase-multilingual-MiniLM-L12-v2", "", ""),
    ("intfloat/multilingual-e5-small", "query: ", "passage: "),
    ("intfloat/multilingual-e5-base", "query: ", "passage: "),
    ("google/embeddinggemma-2", "task: search result | query: ", "title: none | text: "),
]  # needs transformers 5.x + newer torch: run in Docker, not on Intel Mac; prefixes match the model card (SearchQuery / Document)

if __name__ == "__main__":
    paths = sorted(DOCS_DIR.glob("*.txt"))
    names, texts = [p.stem for p in paths], [p.read_text() for p in paths]
    wanted = sys.argv[1:]
    for model, qp, pp in [m for m in MODELS if not wanted or m[0] in wanted]:
        enc = SentenceTransformer(model)
        docs = enc.encode([pp + t for t in texts])

        def search(qs, enc=enc, qp=qp, docs=docs):
            return util.semantic_search(enc.encode([qp + q for q in qs]), docs, top_k=3)

        hits = search([q for q, _ in CASES])
        ok = [any(names[h["corpus_id"]] == gold for h in hit) for hit, (_, gold) in zip(hits, CASES)]
        en = [g for g, (q, _) in zip(ok, CASES) if q.isascii()]
        zh = [g for g, (q, _) in zip(ok, CASES) if not q.isascii()]
        mrr = sum(
            next((1 / r for r, h in enumerate(hit, 1) if names[h["corpus_id"]] == gold), 0)
            for hit, (_, gold) in zip(hits, CASES)
        ) / len(CASES)
        on = [hit[0]["score"] for hit in hits]
        off = [hit[0]["score"] for hit in search(OFF_TOPIC)]
        lo, hi = wilson(sum(ok), len(ok))
        print(
            f"{model}\n  hit@3 {sum(ok)}/{len(ok)} (95% {lo:.0%}-{hi:.0%})  (en {sum(en)}/{len(en)}, zh {sum(zh)}/{len(zh)}, MRR@3 {mrr:.2f})"
            f"\n  top score: on-topic min {min(on):.2f}, off-topic max {max(off):.2f}"
        )
        for (q, gold), good in zip(CASES, ok):
            if not good:
                print(f"  MISS {q!r} (want {gold})")
