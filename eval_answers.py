"""End-to-end check: `python eval_answers.py` (loads bge-m3, makes live LLM calls; same env vars as app.py).
Grounded cases: the reply must contain a fact that only the docs know. Unanswerable cases: the bot must point to
support instead of inventing an answer. Substring checks are blunt on purpose: deterministic, no LLM judge."""
import sys

import app

app.open_ticket = lambda *a, **k: "eval"  # a misrouted case must not write to tickets.jsonl

GROUNDED = [  # (question, any of these substrings must appear in the reply)
    ("How much is the Stark 3?", ["5,200,000", "5.2"]),
    ("What color is the Stark 3?", ["Crimson"]),
    ("哪一款太空船可以載 30 個人?", ["Stark 8"]),
    ("How do I place an order?", ["deposit", "訂金"]),
    ("到貨後要在幾天內回報損壞?", ["7"]),
    ("The ship will not start, what should I check?", ["power cell", "ignition"]),
]
UNANSWERABLE = [
    "What is the warranty period of the Stark 3?",
    "Stark 3 的保固期是幾年?",
    "Does the Stark 10 come with a free flight-school course?",
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
    if route != "ANSWER" or not any(n.lower() in reply.lower() for n in needles):
        bad.append(("grounded", q, route, reply[:120]))
for q in UNANSWERABLE:
    reply, route, _ = app.answer(q, [])
    if route not in ("NO_ANSWER", "ANSWER") or (route == "ANSWER" and app.SUPPORT not in reply):
        bad.append(("unanswerable", q, route, reply[:120]))
for b in bad:
    print("MISS", *b)
total = len(GROUNDED) + len(UNANSWERABLE) + 1
print(f"{total - len(bad)}/{total} ok")
sys.exit(bool(bad))
