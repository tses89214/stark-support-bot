"""Review LLM-drafted test messages by hand: `python -m evals.review_candidates [file]` (default eval_candidates.jsonl).
For each unreviewed row: Enter = the intended category is right, 1-5 = it is really ANSWER/OFF_TOPIC/ABUSIVE/ESCALATE/INJECTION,
d = drop (bad message), s = skip, q = quit. Progress is saved after every row. `--export` prints accepted rows as
eval_guardrails.py CASES lines. Only rows you accepted may be graded against the classifier."""

import json
import sys
from pathlib import Path

LABELS = ["ANSWER", "OFF_TOPIC", "ABUSIVE", "ESCALATE", "INJECTION"]
path = next((a for a in sys.argv[1:] if not a.startswith("--")), "evals/eval_candidates.jsonl")
rows = [json.loads(line) for line in Path(path).read_text().splitlines()]


def save():
    Path(path).write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))


if "--export" in sys.argv:
    for r in rows:
        if r["status"] == "reviewed":
            print(f'    ({json.dumps(r["message"], ensure_ascii=False)}, "{r["intended_category"]}"),')

    sys.exit()

todo = [r for r in rows if r["status"] == "unreviewed"]
for i, r in enumerate(todo, 1):
    print(
        f"\n[{i}/{len(todo)}] {r['message']}\n  intended: {r['intended_category']}  ({r.get('style') or r.get('plugin', '')})"
    )
    key = input("  Enter=ok  1-5=" + "/".join(LABELS) + "  d=drop  s=skip  q=quit > ").strip().lower()
    if key == "q":
        break

    if key == "s":
        continue

    if key == "d":
        r["status"] = "dropped"
    else:
        if key in "12345" and key:
            r["intended_category"] = LABELS[int(key) - 1]

        r["status"] = "reviewed"

    save()

save()
print({s: sum(r["status"] == s for r in rows) for s in ("unreviewed", "reviewed", "dropped")})
