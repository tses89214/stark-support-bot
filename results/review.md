# Review layer results

Generated 2026-10-23 by `python -m evals.eval_review 2` (model `nvidia/nemotron-3-ultra-550b-a55b:free`, 2 passes over 62 fixed cases).

The reviewer reads a question, a draft reply and the documents and says ok or not ok. Every draft here has a known right verdict:
bad drafts are a true answer broken in exactly one way (one way per review rule), good drafts are true answers or honest "I don't know" replies.
No LLM judges the judge.

| Rule broken by the draft | Catch rate (bad drafts rejected) |
|---|---|
| 1 invented fact | 8/8 (68% to 100%) |
| 2 wrong number | 8/8 (68% to 100%) |
| 3 promise (discount / refund) | 8/8 (68% to 100%) |
| 4 guess instead of 'unknown' | 8/8 (68% to 100%) |
| 5 listed item fails a condition | 8/8 (68% to 100%) |
| 6 names the AI model | 8/8 (68% to 100%) |
| 7 wrong support email | 8/8 (68% to 100%) |
| 8 'only' / 'cheapest' claim that another document contradicts | 8/8 (68% to 100%) |
| **all bad drafts** | **64/64 (94% to 100%)** |

**False rejects (good drafts the reviewer refused): 0/60 (-0% to 6%).** Each one costs a customer a good answer.

Failed reviewer calls (retried 3 times, then skipped from both scores): 0 distinct cases.

## Cases the reviewer got wrong

none

Caveats: the drafts are built by a script, so they are cleaner than real model mistakes and the catch rate is probably optimistic; 4 drafts per rule and
2 passes make every interval wide, so only large gaps mean anything; the reviewer was run once per pass at temperature 0.
