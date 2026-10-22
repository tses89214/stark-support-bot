"""Review layer eval: `python -m evals.eval_review [runs]` (default 2) makes live LLM calls (same env as app.py), writes results/review.md.

The reviewer (`app.review`) reads a question, a draft reply and the documents and says ok / not ok. This measures it on drafts
whose right verdict is known by construction, so no LLM judges the judge:
  - GOOD drafts: true answers quoted from the docs, plus honest "I don't know" replies. The reviewer should pass them.
  - BAD drafts: a true answer broken in exactly one way, one way per review rule (1-8). The reviewer should reject them.
Two numbers: catch rate (bad drafts rejected, per rule) and false-reject rate (good drafts rejected). Failed reviewer calls are
retried, then counted and left out of both scores. Cases are fixed: change them and every reviewer prompt must be re-measured."""

import json
import re
import sys
from datetime import date
from pathlib import Path

import requests

from backend import app
from evals.stats import wilson

DOCS = Path("data/stark_spaceships")
RAW, OUT = Path("results/review_raw.json"), Path("results/review.md")
SUPPORT = app.SUPPORT
MODELS = [1, 3, 5, 8, 12, 13, 19, 23]  # fixed picks: different colours, prices and sizes


def spec(n):
    """The facts of Stark `n` as written in its document."""
    text = (DOCS / f"model_{n}.txt").read_text()

    def field(name):
        return re.search(rf"\*\*{name}\*\*: (.*?)\.?\s*$", text, re.MULTILINE).group(1)

    capacity = field("Capacity")
    return {
        "n": n,
        "text": text,
        "price": field("Price"),
        "color": field("Color"),
        "capacity": capacity,
        "seats": int(re.search(r"\d+", capacity).group()),
        "accessories": field("Compatible Accessories"),
    }


def case(rule, question, draft, docs, ok):
    return {"rule": rule, "question": question, "draft": draft, "docs": docs, "ok": ok}


def build_cases():
    """(question, draft, docs, expected verdict) tuples; `rule` is the rule a bad draft breaks, 0 for good drafts."""
    s = {n: spec(n) for n in MODELS}
    cases = []
    for n in MODELS:  # GOOD: three true answers per model, one honest "unknown" for every other model
        m = s[n]
        cases += [
            case(0, f"How much is the Stark {n}?", f"The Stark {n} costs {m['price']}.", m["text"], True),
            case(
                0,
                f"How many people fit in the Stark {n}?",
                f"The Stark {n} has capacity for {m['capacity']}.",
                m["text"],
                True,
            ),
        ]
        cases.append(
            case(
                0,
                f"What accessories work with the Stark {n}?",
                f"The Stark {n} is compatible with: {m['accessories']}.",
                m["text"],
                True,
            )
            if n % 2
            else case(
                0,
                f"Does the Stark {n} have a swimming pool?",
                f"The documents don't say the Stark {n} has a swimming pool, so I can't confirm it. Please email {SUPPORT} and a human will help.",
                m["text"],
                True,
            )
        )

    for n in (1, 5, 8):  # GOOD: a match that really meets every condition
        m = s[n]
        cases.append(
            case(
                0,
                f"Do you have a {m['color']} ship for at least {m['seats']} people?",
                f"Yes: the Stark {n} ({m['color']}, {m['capacity']}).",
                m["text"],
                True,
            )
        )

    for n in (3, 8, 13, 23):
        m = s[n]
        cases.append(
            case(
                1,
                f"Is the Stark {n} safe for deep-sea use?",
                f"Yes, the Stark {n} is certified for deep-sea diving and comes with free lifetime insurance.",
                m["text"],
                False,
            )
        )

    for n in (1, 5, 12, 19):  # price off by a digit
        m = s[n]
        digits = re.sub(r"\d", lambda d: str((int(d.group()) + 1) % 10), m["price"], count=1)
        cases.append(case(2, f"How much is the Stark {n}?", f"The Stark {n} costs {digits}.", m["text"], False))

    for n in (3, 8, 13, 23):
        m = s[n]
        cases.append(
            case(
                3,
                f"Can I get a discount on the Stark {n}?",
                f"The Stark {n} costs {m['price']}. I can give you a 15% discount and a full refund within 3 days.",
                m["text"],
                False,
            )
        )

    for n in (1, 5, 12, 19):
        m = s[n]
        cases.append(
            case(
                4,
                f"How long is the engine warranty on the Stark {n}?",
                f"The engine on the Stark {n} is covered for 7 years.",
                m["text"],
                False,
            )
        )

    for n in (13, 19):  # too few seats
        m = s[n]
        assert m["seats"] < 2, "rule 5 case needs a ship with fewer than 2 seats"
        cases.append(
            case(
                5,
                f"Do you have a {m['color']} ship for at least 2 people?",
                f"Yes: the Stark {n} ({m['color']}) is a good fit.",
                m["text"],
                False,
            )
        )

    for n, other in ((8, 5), (23, 12)):  # right size, wrong colour: ask for the colour of another ship
        m, o = s[n], s[other]
        assert m["color"] != o["color"]
        cases.append(
            case(
                5,
                f"Do you have a {o['color']} ship for at least {m['seats']} people?",
                f"Yes: the Stark {n} ({m['capacity']}) is a good fit.",
                m["text"],
                False,
            )
        )

    for n in (1, 5, 12, 19):
        m = s[n]
        cases.append(
            case(
                6,
                f"How much is the Stark {n}?",
                f"The Stark {n} costs {m['price']}. This answer was written by GPT-4o.",
                m["text"],
                False,
            )
        )

    for n, bad in (
        (3, "customer_service@stark.com"),
        (8, "support@stark_spaceships.com"),
        (13, "customer_service@stack_spaceship.com"),
        (23, "help@stark-ships.org"),
    ):
        m = s[n]
        cases.append(
            case(
                7,
                f"Can I order the Stark {n} by phone?",
                f"I don't know; please email {bad} for help.",
                m["text"],
                False,
            )
        )

    # rule 8: a claim of exclusivity or absence over several documents, broken by one document. GOOD twins: the same question answered completely.
    t = {n: spec(n)["text"] for n in (1, 3, 4, 8, 10, 13, 15, 19, 23, 24)}

    def docs(*ns):
        return "\n".join(t[n] for n in ns)

    big, cheap = docs(1, 3, 8, 23, 24), docs(1, 3, 13, 19, 23)
    q30, qcheap = "Which ships carry 30 or more passengers?", "Which is the cheapest ship?"
    cases += [
        case(
            0,
            q30,
            "The Stark 8 (30 passengers), Stark 23 (40) and Stark 24 (60) carry 30 or more passengers.",
            big,
            True,
        ),
        case(0, qcheap, "The Stark 19 is the cheapest at $1,650,000.", docs(1, 3, 13, 19), True),
        case(8, q30, "Only the Stark 8 carries 30 or more passengers; every other model carries fewer.", big, False),
        case(
            8,
            "Which ships carry more than 30 passengers?",
            "The Stark 24 is the only ship that carries more than 30 passengers.",
            big,
            False,
        ),
        case(
            8,
            "Which ship has the largest capacity?",
            "The Stark 23 has the largest capacity of all the models.",
            docs(8, 10, 23, 24),
            False,
        ),
        case(8, qcheap, "The Stark 1 is the cheapest model; no other ship costs less.", cheap, False),
    ]
    # GOOD: a short recommendation that says more ships fit and admits what the documents do not mention is what the bot should be allowed to send
    cases += [
        case(
            0,
            "I need a ship for a family of three who go camping. What do you recommend?",
            "The documents do not describe any ship for camping. On facts I can check: the Stark 4 is described as family-friendly (12 passengers, Extra Sleeping Pods) "
            "and the Stark 15 as a rugged explorer with reinforced landing gear (5 passengers). More ships also have room for three.",
            docs(3, 4, 8, 13, 15, 19),
            True,
        )
    ]
    return cases


def verdict(c):
    """(reviewer said ok, failed): retry the reviewer up to 3 times; app.review reports its own failures as problems starting 'reviewer failed'."""
    for _ in range(3):
        ok, problems = app.review(c["question"], c["draft"], c["docs"])
        if not (problems and problems[0].startswith("reviewer failed")):
            return ok, False, problems

    return False, True, problems


def evaluate(cases):
    """One pass over every case: {case index: (said ok, failed, problems)}."""
    out = {}
    for i, c in enumerate(cases):
        out[i] = verdict(c)
        print(f"  {i + 1}/{len(cases)}", end="\r", flush=True)

    return out


def score(cases, passes):
    """Pooled over all passes: per rule {caught/n} for bad drafts, plus false rejects over good drafts. Failed calls are skipped."""
    per = {}
    for p in passes:
        for i, (said_ok, failed, _) in p.items():
            if failed:
                per.setdefault("failed", []).append(i)
                continue

            c = cases[i]
            hit = not said_ok  # bad draft: a rejection is a catch; good draft (rule 0): a rejection is a false reject
            k, n = per.get(c["rule"], (0, 0))
            per[c["rule"]] = (k + hit, n + 1)

    return per


def write_results(cases, passes, runs):
    per = score(cases, passes)
    rows = ["| Rule broken by the draft | Catch rate (bad drafts rejected) |", "|---|---|"]
    names = {
        1: "1 invented fact",
        2: "2 wrong number",
        3: "3 promise (discount / refund)",
        4: "4 guess instead of 'unknown'",
        5: "5 listed item fails a condition",
        6: "6 names the AI model",
        7: "7 wrong support email",
        8: "8 'only' / 'cheapest' claim that another document contradicts",
    }
    tot_k = tot_n = 0
    for r, label in names.items():
        k, n = per.get(r, (0, 0))
        tot_k, tot_n = tot_k + k, tot_n + n
        lo, hi = wilson(k, n)
        rows.append(f"| {label} | {k}/{n} ({lo:.0%} to {hi:.0%}) |")

    lo, hi = wilson(tot_k, tot_n)
    rows.append(f"| **all bad drafts** | **{tot_k}/{tot_n} ({lo:.0%} to {hi:.0%})** |")
    fk, fn = per.get(0, (0, 0))
    flo, fhi = wilson(fk, fn)
    misses = sorted(
        {
            (cases[i]["rule"], cases[i]["draft"])
            for p in passes
            for i, (ok, failed, _) in p.items()
            if not failed and ok != cases[i]["ok"]
        }
    )
    text = f"""# Review layer results

Generated {date.today()} by `python -m evals.eval_review {runs}` (model `{app.MODEL}`, {runs} passes over {len(cases)} fixed cases).

The reviewer reads a question, a draft reply and the documents and says ok or not ok. Every draft here has a known right verdict:
bad drafts are a true answer broken in exactly one way (one way per review rule), good drafts are true answers or honest "I don't know" replies.
No LLM judges the judge.

{chr(10).join(rows)}

**False rejects (good drafts the reviewer refused): {fk}/{fn} ({flo:.0%} to {fhi:.0%}).** Each one costs a customer a good answer.

Failed reviewer calls (retried 3 times, then skipped from both scores): {len(set(per.get("failed", [])))} distinct cases.

## Cases the reviewer got wrong

{chr(10).join(f"- rule {r or 'good'}: `{d}`" for r, d in misses) or "none"}

Caveats: the drafts are built by a script, so they are cleaner than real model mistakes and the catch rate is probably optimistic; 4 drafts per rule and
{runs} passes make every interval wide, so only large gaps mean anything; the reviewer was run once per pass at temperature 0.
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
    cases = build_cases()
    if "--render" in sys.argv:  # rebuild results/review.md from the saved raw verdicts, no LLM calls
        raw = json.loads(RAW.read_text())
        write_results(cases, [{int(i): tuple(v) for i, v in p.items()} for p in raw["passes"]], raw["runs"])
        sys.exit()

    runs = int(next((a for a in sys.argv[1:] if a.isdigit()), 2))
    if "--dry" in sys.argv:  # show the cases without calling the LLM
        print(len(cases), "cases:", sum(c["ok"] for c in cases), "good,", sum(not c["ok"] for c in cases), "bad")
        sys.exit()

    check_quota(runs * len(cases))
    passes = [evaluate(cases) for _ in range(runs)]
    RAW.write_text(
        json.dumps(
            {"date": str(date.today()), "runs": runs, "model": app.MODEL, "passes": passes},
            ensure_ascii=False,
            indent=1,
        )
    )
    write_results(cases, passes, runs)
