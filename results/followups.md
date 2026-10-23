# Off-topic messages and follow-ups

Generated 2026-10-22 by `python -m evals.eval_followups 2` (model `nvidia/nemotron-3-ultra-550b-a55b:free`, 2 passes).

## 1. Off-topic messages under R3 (no score floor)

15 off-topic messages per pass. Two independent lines of defence:

| Line | Stops the message |
|---|---|
| Input classifier says something other than ANSWER | 30/30 (89% to 100%) |
| R3 picker names no file ("not found") | 30/30 (89% to 100%) |
| At least one of the two | 30/30 (89% to 100%) |

An off-topic message reaches the answer step only when both lines miss it. Calls that failed after 3 tries and were left out: 0.

## 2. Follow-ups in a chat, R2 vs R3

8 cases per pass: a short history, a last message that needs it, and the documents the answer needs. The classifier rewrites the
message into a standalone question first (as `app.answer` does); both modes see the same rewrite. R2 = scope check, then vector top-3,
or every model sheet when the question is catalogue-wide; R3 = the LLM reads the document index.

| Mode | Follow-ups where every needed document was picked |
|---|---|
| R2 | 16/16 (81% to 100%) |
| R3 | 16/16 (81% to 100%) |

No misses.

Cases dropped because a call failed after 3 tries: 0. Caveats: 8 hand-written cases, so every interval is wide; histories are two to four turns, so
this says nothing about chats of twenty turns; the classifier only sees the last 4 messages.
