# Multi-turn conversations

Generated 2026-10-25 by `python -m evals.eval_conversations 4` (model `nvidia/nemotron-3-ultra-550b-a55b:free`). 14 scripted chats through `app.chat`, 4 runs each; every turn is judged by code (route, required and forbidden text, reply language).

**56/56 chats passed in full** (95% interval 94% to 100%); 92/92 single turns passed.

| Chat | Turns | Passed |
|---|---|---|
| greeting | 1 | 4/4 |
| order status goes to a human | 1 | 4/4 |
| damaged order goes to a human | 1 | 4/4 |
| price then colour of 'it' | 2 | 4/4 |
| Chinese follow-up | 2 | 4/4 |
| off-topic turn does not lose the focus | 3 | 4/4 |
| injection in the middle of a chat | 3 | 4/4 |
| catalogue question lists every match | 1 | 4/4 |
| cheapest, asked in English, answered in English | 1 | 4/4 |
| colour, asked in Chinese, answered in Chinese | 1 | 4/4 |
| named model: no clarifying question | 1 | 4/4 |
| ship search: asks first, then recommends | 2 | 4/4 |
| asks at most twice, then recommends anyway | 3 | 4/4 |
| 'just list them' skips the question | 1 | 4/4 |

## Failed turns

none

Caveats: the chats are written by the author and there are few of them, so a pass rate here is a smoke test of known behaviours, not an estimate for real customers; the checks are substrings and a regex, so a reply that is wrong in a way they do not look for passes.
