# Multi-turn conversations

Generated 2026-10-24 by `python -m evals.eval_conversations 2` (model `nvidia/nemotron-3-ultra-550b-a55b:free`). 14 scripted chats through `app.chat`, 2 runs each; every turn is judged by code (route, required and forbidden text, reply language).

**28/28 chats passed in full** (95% interval 88% to 100%); 46/46 single turns passed.

| Chat | Turns | Passed |
|---|---|---|
| greeting | 1 | 2/2 |
| order status goes to a human | 1 | 2/2 |
| damaged order goes to a human | 1 | 2/2 |
| price then colour of 'it' | 2 | 2/2 |
| Chinese follow-up | 2 | 2/2 |
| off-topic turn does not lose the focus | 3 | 2/2 |
| injection in the middle of a chat | 3 | 2/2 |
| catalogue question lists every match | 1 | 2/2 |
| cheapest, asked in English, answered in English | 1 | 2/2 |
| colour, asked in Chinese, answered in Chinese | 1 | 2/2 |
| named model: no clarifying question | 1 | 2/2 |
| ship search: asks first, then recommends | 2 | 2/2 |
| asks at most twice, then recommends anyway | 3 | 2/2 |
| 'just list them' skips the question | 1 | 2/2 |

## Failed turns

none

Caveats: the chats are written by the author and there are few of them, so a pass rate here is a smoke test of known behaviours, not an estimate for real customers; the checks are substrings and a regex, so a reply that is wrong in a way they do not look for passes.
