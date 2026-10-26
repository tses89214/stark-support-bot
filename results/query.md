# Condition extraction (plan_query -> find_models)

Generated 2026-10-26 by `python -m evals.eval_query 2` (model `nvidia/nemotron-3-ultra-550b-a55b:free`). 24 questions x 2 runs. A plan passes when the models code finds with it equal those found with the hand-written conditions (empty expected = the plan must be empty).

- Questions with an exact condition: **34/34** (95% interval 90% to 100%)
- Questions with nothing exact to look up: **14/14** (95% interval 78% to 100%)

| Question | Passed |
|---|---|
| 哪一款太空船可以載 30 個人? | 2/2 |
| Which ships carry at least 20 passengers? | 2/2 |
| 價格低於 600 萬的有哪些？ | 2/2 |
| 預算一千萬以內、至少載 10 人的船 | 2/2 |
| Any ship under $2 million? | 2/2 |
| Which ships cost less than $2.5M? | 2/2 |
| 兩千萬以上的有哪些？ | 2/2 |
| 有黃色的船嗎？ | 2/2 |
| Which ones are red? | 2/2 |
| 藍色而且不超過 800 萬的 | 2/2 |
| Which ships are longer than 40 meters? | 2/2 |
| 長度至少 30 公尺的有哪些？ | 2/2 |
| Which ships weigh more than 100 metric tons? | 2/2 |
| 重量不到 20 噸的船 | 2/2 |
| Which can carry more than 30 people? | 2/2 |
| Which ships fit 8 people? | 2/2 |
| I need at least 5 seats and a price under 6 million | 2/2 |
| 最便宜的是哪一款？ | 2/2 |
| 適合露營的船有哪些？ | 2/2 |
| 哪款比較大？ | 2/2 |
| 保固多久？ | 2/2 |
| 推薦一台適合家庭的 | 2/2 |
| Which is the longest ship? | 2/2 |
| Tell me about the Stark 3. | 2/2 |

## Failed plans

none
