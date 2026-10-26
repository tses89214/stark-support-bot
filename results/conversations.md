# Multi-turn conversations

Generated 2026-10-26 by `python -m evals.eval_conversations 4` (model `nvidia/nemotron-3-ultra-550b-a55b:free`). 14 scripted chats through `app.chat`, 4 runs each; every turn is judged by code (route, required and forbidden text, reply language).

**55/56 chats passed in full** (95% interval 91% to 100%); 91/92 single turns passed.

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
| ship search: asks first, then recommends | 2 | 3/4 |
| asks at most twice, then recommends anyway | 3 | 4/4 |
| 'just list them' skips the question | 1 | 4/4 |

## Failed turns

- **ship search: asks first, then recommends** / `三人小家庭、日常家庭旅行偶爾露營` -> ANSWER: forbidden text '唯一'
  > '為三人小家庭的日常旅行與偶爾露營需求，文件中能確認的資訊僅限於各型號的**載客人數**、**尺寸**、**價格**與**標配配件**；沒有任何型號在文件中提及露營相關功能（如帳篷艙、野外電源、全地形著陸腳等）。\n\n以下是載客 **≥ 3 人** 且較符合家庭出遊基本條件的三款機型（依文件描述排序）：\n\n| 型號 | 載客 | 尺寸/重量 | 價格 | 標配配件（文件列出） | 文件定位 |\n|------|------|-----------|------|---------'

Caveats: the chats are written by the author and there are few of them, so a pass rate here is a smoke test of known behaviours, not an estimate for real customers; the checks are substrings and a regex, so a reply that is wrong in a way they do not look for passes.
