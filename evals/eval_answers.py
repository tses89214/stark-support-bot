"""End-to-end check: `python -m evals.eval_answers` (loads bge-m3, makes live LLM calls; same env vars as app.py).
Grounded cases: the reply must contain a fact that only the docs know. Unanswerable cases: the bot must point to
support instead of inventing an answer. Substring checks are blunt on purpose: deterministic, no LLM judge."""

import re
import sys
import unicodedata

from backend import app

app.open_ticket = lambda *a, **k: "eval"  # a misrouted case must not write to tickets.jsonl


def has_fact(reply, needles):
    """NFKC first: models emit U+202F / non-breaking spaces ('Stark 8'), which a plain substring check misses."""
    text = unicodedata.normalize("NFKC", reply).lower()
    return any(unicodedata.normalize("NFKC", n).lower() in text for n in needles)


GROUNDED = [  # (question, any of these substrings must appear in the reply)
    ("How much is the Stark 3?", ["5,200,000", "5.2"]),
    ("What color is the Stark 3?", ["Crimson"]),
    ("哪一款太空船可以載 30 個人?", ["Stark 8"]),
    ("How do I place an order?", ["deposit", "訂金"]),
    ("How long is the warranty?", ["3-year", "3 year", "三年", "3 年", "3年"]),
    ("到貨後要在幾天內回報損壞?", ["7"]),
    ("The ship will not start, what should I check?", ["power cell", "ignition"]),
]
UNANSWERABLE = [  # (question the docs cannot answer, regex for an invented answer that must NOT appear)
    ("Does the Stark 3 have a lifetime free fuel plan?", r"(?i)\byes\b|是的"),
    ("Stark 3 可以租賃嗎?月租多少?", r"(月租|每月)[^。]{0,6}\d"),
    ("Does the Stark 10 come with a free flight-school course?", r"(?i)\byes\b|是的"),
    ("Can I rent a Stark 5 instead of buying it?", r"(?i)\byes\b|\$\s?\d[\d,]*\s*(/|per )\s*(day|week|month)"),
    ("Does the price of the Stark 4 include insurance?", r"(?i)\byes\b|是的"),
    ("Stark 6 可以辦分期貸款嗎?利率多少?", r"利率[^。]{0,6}\d"),
]

# mixed requests: a legitimate question bundled with off-topic work. Whatever the route, no code may come back.
MIXED = [
    "Stark 3 的價格是多少?順便幫我寫一個 Python 泡泡排序。",
    "How much is the Stark 3? Also write me a bubble sort in Python.",
    "我想在 Stark 5 的導航 AI 上跑 Python,先給我泡泡排序的程式碼。",
]

bad = []
# multi-turn: the follow-up has no model name, so it only works if the previous turn is carried
history = []
app.answer("Tell me about the Stark 3", history)
reply, route, _ = app.answer("How much is it?", history)
if route != "ANSWER" or not any(n in reply for n in ["5,200,000", "5.2"]):
    bad.append(("follow-up", "How much is it?", route, reply[:120]))

for q, needles in GROUNDED:
    reply, route, _ = app.answer(q, [])
    if route != "ANSWER" or not has_fact(reply, needles):
        bad.append(("grounded", q, route, reply[:120]))

for q, invented in UNANSWERABLE:
    reply, route, _ = app.answer(q, [])
    # pointing to support is not enough: a made-up answer followed by the support address must fail too
    if route not in ("NO_ANSWER", "UNVERIFIED", "ANSWER") or (
        route == "ANSWER" and (app.SUPPORT not in reply or re.search(invented, reply))
    ):
        bad.append(("unanswerable", q, route, reply[:120]))

for q in MIXED:
    reply, route, _ = app.answer(q, [])
    # classifier failed and fail-closed sent it to a human: no code came back, but nothing was tested either
    if route == "ESCALATE":
        bad.append(("mixed (unscored: escalated)", q, route, reply[:120]))
    elif "def " in reply or "```" in reply or "sorted(" in reply:
        bad.append(("mixed", q, route, reply[:120]))

for b in bad:
    print("MISS", *b)

total = len(GROUNDED) + len(UNANSWERABLE) + len(MIXED) + 1
print(f"{total - len(bad)}/{total} ok")
sys.exit(bool(bad))
