"""Two checks the retrieval ladder does not cover: `python -m evals.eval_followups [runs]` (default 2; live LLM calls, same env as app.py)
writes results/followups.md. `--dry` lists the cases, `--render` rebuilds the report from results/followups_raw.json, `--force` skips the quota check.

1. Off-topic messages under R3. R3 has no score floor, so two things stand between an off-topic message and the answer step: the input
   classifier (it should say OFF_TOPIC) and the document picker (it should name no file, which makes the bot say "not found").
   Measured separately, on the 15 off-topic messages the score-floor eval uses.
2. Follow-ups in a longer chat, R2 vs R3. The question is whether the retrieval still finds the right document when the message only makes
   sense with the earlier turns ("how much is it?"). Each case is a short history plus the last message and the documents it needs;
   the classifier first rewrites the message into a standalone question (as app.answer does), then each mode picks documents.
Scores are pooled over the runs with Wilson intervals; a failed call is retried, then counted and left out."""

import json
import sys
from datetime import date
from pathlib import Path

import requests

from backend import app
from evals.eval_retrieval import MORE_OFF_TOPIC, OFF_TOPIC
from evals.stats import wilson

RAW, OUT = Path("results/followups_raw.json"), Path("results/followups.md")
PART = Path(
    "results/followups_partial.json"
)  # every finished case is written here at once, so a crash or reboot loses at most one case
OFF_TOPIC_ALL = OFF_TOPIC + MORE_OFF_TOPIC  # 15 messages


def chat(*turns):
    """History from alternating (customer, bot) lines."""
    return [{"role": "user" if i % 2 == 0 else "assistant", "content": t} for i, t in enumerate(turns)]


# (name, history, last message, documents the answer needs). Document names are the file stems app.names uses.
FOLLOW_UPS = [
    (
        "it: price",
        chat("Tell me about the Stark 3.", "The Stark 3 is our speed model."),
        "How much is it?",
        {"model_3"},
    ),
    (
        "it: colour",
        chat("How many people fit in the Stark 8?", "The Stark 8 carries 30 passengers."),
        "What color is it?",
        {"model_8"},
    ),
    (
        "another model",
        chat("How much is the Stark 3?", "The Stark 3 costs $5,200,000."),
        "And the Stark 5?",
        {"model_5"},
    ),
    (
        "topic switch to a guide",
        chat("How much is the Stark 3?", "The Stark 3 costs $5,200,000.", "What color is it?", "It is Crimson."),
        "How do I place an order?",
        {"guide_ordering_delivery"},
    ),
    (
        "topic switch to the warranty",
        chat(
            "Tell me about the Stark 8.", "The Stark 8 is a large passenger ship.", "How many people?", "30 passengers."
        ),
        "How long is the warranty?",
        {"warranty_policy"},
    ),
    (
        "model plus policy",
        chat("I like the Stark 8.", "Good choice, it carries 30 passengers."),
        "Does it come with a warranty?",
        {"model_8", "warranty_policy"},
    ),
    ("Chinese follow-up", chat("Stark 4 適合家庭旅行嗎?", "適合，Stark 4 可以載一家人。"), "它多少錢?", {"model_4"}),
    (
        "troubleshooting after a model",
        chat("Tell me about the Stark 5.", "The Stark 5 is a cargo ship."),
        "It will not start, what should I check?",
        {"guide_troubleshooting"},
    ),
]
MODES = ["R2", "R3"]


def failed(reason):
    return reason.startswith("classifier failed")


def off_topic_case(message):
    """(classifier said OFF_TOPIC-or-blocked, picker named no file, failed): the classifier and the R3 picker are asked independently."""
    category, reason = app.classify(message)
    if failed(reason):
        return None
    try:
        picked = app.pick_by_index(message)
    except Exception as e:  # noqa: BLE001 - a failed call is counted, never scored
        print(f"pick failed: {e!r}", file=sys.stderr)
        return None
    return {"category": category, "picked": picked}


def follow_up_case(history, message, gold):
    """Per mode: did the picked documents include every document the answer needs. None when a call failed."""
    category, reason, question, _ = app.classify(message, history, full=True)
    if failed(reason) or category != "ANSWER":
        return None
    out = {"question": question}
    for mode in MODES:
        try:
            sources = app.select_docs(message, history, mode, question=question) or []
        except Exception as e:  # noqa: BLE001
            print(f"{mode} failed: {e!r}", file=sys.stderr)
            return None
        out[mode] = {"sources": sources, "hit": gold <= set(sources)}
    return out


def retry(fn, *args):
    for _ in range(3):
        result = fn(*args)
        if result is not None:
            return result
    return None


def done(key, fn, *args):
    """fn(*args) once per key: a result already in PART (from an interrupted run) is reused, a new one is saved before moving on."""
    saved = json.loads(PART.read_text()) if PART.exists() else {}
    if key not in saved:
        saved[key] = retry(fn, *args)
        PART.write_text(json.dumps(saved, ensure_ascii=False))
    return saved[key]


def one_pass(i):
    off = {m: done(f"{i}|off|{m}", off_topic_case, m) for m in OFF_TOPIC_ALL}
    fol = {name: done(f"{i}|fol|{name}", follow_up_case, h, m, g) for name, h, m, g in FOLLOW_UPS}
    return {"off_topic": off, "follow_ups": fol}


def write_results(passes, runs):
    off = [r for p in passes for r in p["off_topic"].values() if r]
    lost_off = len([1 for p in passes for r in p["off_topic"].values() if not r])
    caught = sum(r["category"] != "ANSWER" for r in off)  # any route but ANSWER stops the message before retrieval
    quiet = sum(not r["picked"] for r in off)
    both = sum(r["category"] != "ANSWER" or not r["picked"] for r in off)  # stopped by at least one of the two

    def fmt(k, n):
        lo, hi = wilson(k, n)
        return f"{k}/{n} ({lo:.0%} to {hi:.0%})"

    rows = ["| Mode | Follow-ups where every needed document was picked |", "|---|---|"]
    detail = []
    for mode in MODES:
        res = [(name, p["follow_ups"][name][mode]) for p in passes for name in p["follow_ups"] if p["follow_ups"][name]]
        rows.append(f"| {mode} | {fmt(sum(r['hit'] for _, r in res), len(res))} |")
        for name, r in res:
            if not r["hit"]:
                detail.append(f"- {mode} missed `{name}`: picked {r['sources']}")
    lost_fol = len([1 for p in passes for r in p["follow_ups"].values() if not r])
    text = f"""# Off-topic messages and follow-ups

Generated {date.today()} by `python -m evals.eval_followups {runs}` (model `{app.MODEL}`, {runs} passes).

## 1. Off-topic messages under R3 (no score floor)

{len(OFF_TOPIC_ALL)} off-topic messages per pass. Two independent lines of defence:

| Line | Stops the message |
|---|---|
| Input classifier says something other than ANSWER | {fmt(caught, len(off))} |
| R3 picker names no file ("not found") | {fmt(quiet, len(off))} |
| At least one of the two | {fmt(both, len(off))} |

An off-topic message reaches the answer step only when both lines miss it. Calls that failed after 3 tries and were left out: {lost_off}.

## 2. Follow-ups in a chat, R2 vs R3

{len(FOLLOW_UPS)} cases per pass: a short history, a last message that needs it, and the documents the answer needs. The classifier rewrites the
message into a standalone question first (as `app.answer` does); both modes see the same rewrite. R2 = scope check, then vector top-3
or top-15; R3 = the LLM reads the document index.

{chr(10).join(rows)}

{chr(10).join(detail) or "No misses."}

Cases dropped because a call failed after 3 tries: {lost_fol}. Caveats: 8 hand-written cases, so every interval is wide; histories are two to four turns, so
this says nothing about chats of twenty turns; the classifier only sees the last 4 messages.
"""
    OUT.write_text(text)
    print(text)


def check_quota(need):
    """The free tier counts requests per account and day; refuse to start when the counters are short (`--force` overrides)."""
    left = sum(
        requests.get("https://openrouter.ai/api/v1/key", headers={"Authorization": f"Bearer {k}"}, timeout=30).json()[
            "data"
        ]["free_model_daily_requests"]["remaining"]
        for k in app.KEYS
    )
    print(f"free-model requests left today: {left}, this run needs up to {need}", flush=True)
    if left < need and "--force" not in sys.argv:
        sys.exit(f"not enough quota ({left} < {need}); wait for the UTC reset (08:00 Taipei)")


if __name__ == "__main__":
    runs = int(next((a for a in sys.argv[1:] if a.isdigit()), 2))
    if "--render" in sys.argv:  # rebuild results/followups.md from the saved raw results, no LLM calls
        raw = json.loads(RAW.read_text())
        write_results(raw["passes"], raw["runs"])
        sys.exit()
    if "--dry" in sys.argv:  # show the cases without calling the LLM
        print(len(OFF_TOPIC_ALL), "off-topic messages,", len(FOLLOW_UPS), "follow-up cases")
        for name, history, message, gold in FOLLOW_UPS:
            print(f"  {name}: {len(history)} history lines, {message!r} -> {sorted(gold)}")
            assert all(g in app.names for g in gold), f"{name}: gold names a document that does not exist"
        sys.exit()
    # per pass: off-topic = classify + pick (2 calls each); follow-up = classify + R2 scope check + R3 pick (3 calls each); retries not counted
    check_quota(runs * (2 * len(OFF_TOPIC_ALL) + 3 * len(FOLLOW_UPS)))
    passes = [
        one_pass(i) for i in range(runs)
    ]  # rerun the same command after an interruption: finished cases are skipped
    RAW.write_text(
        json.dumps(
            {"date": str(date.today()), "runs": runs, "model": app.MODEL, "passes": passes},
            ensure_ascii=False,
            indent=1,
        )
    )
    PART.unlink(missing_ok=True)
    write_results(passes, runs)
