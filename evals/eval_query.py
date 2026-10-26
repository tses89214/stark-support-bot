"""Condition-extraction eval: `python -m evals.eval_query [runs]` (default 2) makes live LLM calls (same env as app.py), writes results/query.md.

`app.plan_query` turns a catalogue question into conditions for `app.find_models`. Each case in eval_query_cases.jsonl gives the conditions a
careful reader would write (an empty list = nothing exact to look up: "the cheapest", "good for camping"). A plan passes when the models code
finds with it are the same as with the expected conditions, so wording does not matter, only the numbers, fields and operators; for an
empty expectation the plan must be empty too. No LLM judges anything."""

import json
import sys
from datetime import date
from pathlib import Path

from backend import app
from evals.stats import wilson

CASES = Path("evals/eval_query_cases.jsonl")
OUT = Path("results/query.md")


def passes(plan, expected):
    if not expected:
        return plan == []

    return bool(plan) and set(app.find_models(plan)) == set(app.find_models(expected))


if __name__ == "__main__":
    runs = next((int(a) for a in sys.argv[1:] if a.isdigit()), 2)
    cases = [json.loads(line) for line in CASES.read_text().splitlines()]
    for c in cases:  # a case whose expected list selects nothing, or every model, would pass a useless plan
        found = app.find_models(c["where"]) if c["where"] else None
        assert found is None or 0 < len(found) < 30, c["question"]

    rows, bad = [], []
    for c in cases:
        ok = 0
        for _ in range(runs):
            plan = app.plan_query(c["question"])
            if passes(plan, c["where"]):
                ok += 1
            else:
                bad.append((c["question"], c["where"], plan))

        rows.append((c["question"], bool(c["where"]), ok))
        print(f"{ok}/{runs}  {c['question']}", flush=True)

    def tally(look):
        k = sum(ok for _, w, ok in rows if w == look)
        n = sum(runs for _, w, _ in rows if w == look)
        return k, n, wilson(k, n)

    lines = [
        "# Condition extraction (plan_query -> find_models)",
        "",
        (
            f"Generated {date.today()} by `python -m evals.eval_query {runs}` (model `{app.MODEL}`). {len(cases)} questions x {runs} runs. "
            "A plan passes when the models code finds with it equal those found with the hand-written conditions (empty expected = the plan must be empty)."
        ),
        "",
    ]
    for label, look in (("Questions with an exact condition", True), ("Questions with nothing exact to look up", False)):
        k, n, (lo, hi) = tally(look)
        lines.append(f"- {label}: **{k}/{n}** (95% interval {lo:.0%} to {hi:.0%})")

    lines += ["", "| Question | Passed |", "|---|---|", *(f"| {q} | {ok}/{runs} |" for q, _, ok in rows), "", "## Failed plans", ""]
    lines += [f"- {q}: expected `{json.dumps(w, ensure_ascii=False)}`, got `{json.dumps(p, ensure_ascii=False)}`" for q, w, p in bad] or ["none"]
    OUT.write_text("\n".join(lines) + "\n")
